"""#1980: remote health probes that need a key, and role names for the remote services.

A local stub HTTP server on 127.0.0.1 stands in for a remote service; curl is the real one behind a PATH
wrapper that records its argv. docker and notify are shims. Nothing leaves the machine. The key is a
synthetic random value made per test.
"""
import secrets
import shutil
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # also when run by path, not only by discover
from test_remote_services_1843 import ALERT, LIB, ROOT, UP, Sandbox  # noqa: E402

REAL_CURL = shutil.which('curl')


class StubService:
    """/open: 200. /auth and /auth403: 200 with the right bearer, else 401 / 403. /down: 503.

    While a request is open it scans every /proc/*/cmdline for the key, so a key on any command line
    during the probe (curl's or a shell's) is caught, not only the wrapper's view of curl's argv.
    """

    def __init__(self, test, key):
        self.key = key
        self.seen = []        # Authorization header per request ('' when none)
        self.cmdline_hits = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                auth = self.headers.get('Authorization') or ''
                stub.seen.append(auth)
                stub.scan_cmdlines()
                good = auth == f'Bearer {stub.key}'
                path = self.path.split('?')[0]
                code = {'/open': 200, '/down': 503,
                        '/auth': 200 if good else 401, '/auth403': 200 if good else 403}.get(path, 404)
                self.send_response(code)
                self.send_header('Content-Length', '0')
                self.end_headers()

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.port = self.server.server_address[1]
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        test.addCleanup(self.server.server_close)
        test.addCleanup(self.server.shutdown)

    def url(self, path):
        return f'http://127.0.0.1:{self.port}{path}'

    def scan_cmdlines(self):
        proc = Path('/proc')
        if not proc.is_dir():
            return
        needle = self.key.encode()
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                cmd = (entry / 'cmdline').read_bytes()
            except OSError:
                continue
            if needle in cmd:
                self.cmdline_hits.append(entry.name)


@unittest.skipUnless(REAL_CURL, 'curl is not installed')
class AuthProbeTests(unittest.TestCase):
    def setUp(self):
        self.key = 'synthetic-' + secrets.token_hex(16)
        self.stub = StubService(self, self.key)
        self.sb = Sandbox(self)
        self.argv_log = self.sb.root / 'curl-argv.log'
        # The real curl, behind a wrapper that records its exact argv (NUL separated, one run per line).
        self.sb.shim('curl', f'''#!/bin/bash
{{ for a in "$@"; do printf '%s\\0' "$a"; done; printf '\\n'; }} >> "{self.argv_log}"
exec "{REAL_CURL}" "$@"
''')
        self.outputs = []

    def tearDown(self):
        # Every run of every test: the key never reaches output, curl's argv or any command line.
        everything = '\n'.join(self.outputs) + self.sb.calls()
        if self.argv_log.exists():
            everything += self.argv_log.read_bytes().decode(errors='replace')
        self.assertNotIn(self.key, everything)
        self.assertEqual(self.stub.cmdline_hits, [], 'the key appeared on a process command line during a probe')

    def key_file(self, name='decision.hdr', value=None, mode=0o600, text=None):
        path = self.sb.root / name
        path.write_text(text if text is not None else f'Authorization: Bearer {value or self.key}\n')
        path.chmod(mode)
        return path

    def run_lib(self, *args, **env):
        result = self.sb.run(['bash', str(LIB), *args], NOEVIA_REMOTE_PROBE_TIMEOUT='5', **env)
        self.outputs += [result.stdout, result.stderr]
        return result

    def probe(self, path, auth_file=None, **extra):
        env = dict(NOEVIA_REMOTE_SERVICES='decision', NOEVIA_REMOTE_DECISION_HEALTH_URL=self.stub.url(path))
        if auth_file is not None:
            env['NOEVIA_REMOTE_DECISION_AUTH_FILE'] = str(auth_file)
        env.update(extra)
        return self.run_lib('--probe', **env)

    def curl_runs(self):
        if not self.argv_log.exists():
            return []
        return [line.split('\0')[:-1] for line in self.argv_log.read_bytes().decode().splitlines() if line]

    def test_401_or_403_without_a_key_is_up_and_needs_auth(self):
        result = self.probe('/auth')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'PASS: decision runs on machine remote (HTTP 401 (needs auth))')
        self.assertEqual(result.stderr, '')
        self.assertIn('PASS: decision runs on machine remote (HTTP 403 (needs auth))', self.probe('/auth403').stdout)
        self.assertEqual(self.stub.seen, ['', ''], 'no key is sent when none is configured')
        self.assertNotIn('-H', self.curl_runs()[0])

    def test_the_right_key_file_is_sent_from_the_file_and_healthy(self):
        path = self.key_file()
        result = self.probe('/auth', path)
        self.assertEqual(result.stdout.strip(), 'PASS: decision runs on machine remote (HTTP 200)', result.stderr)
        self.assertEqual(self.stub.seen, [f'Bearer {self.key}'])
        argv = self.curl_runs()[0]
        self.assertIn(f'@{path}', argv)
        self.assertEqual(argv[argv.index(f'@{path}') - 1], '-H')
        self.assertEqual(argv[-1], self.stub.url('/auth'), 'the URL stays the last argument')
        # A stricter mode is accepted too.
        path.chmod(0o400)
        self.assertIn('(HTTP 200)', self.probe('/auth', path).stdout)

    def test_a_refused_key_is_unhealthy(self):
        wrong = self.key_file(value='synthetic-wrong-' + secrets.token_hex(8))
        self.assertEqual(self.probe('/auth', wrong).stdout.strip(),
                         'WARN: decision on machine remote is unhealthy (HTTP 401 (key refused))')
        self.assertIn('unhealthy (HTTP 403 (key refused))', self.probe('/auth403', wrong).stdout)
        self.assertIn('unhealthy (HTTP 503)', self.probe('/down', wrong).stdout)

    def test_an_unsafe_or_malformed_key_file_is_ignored_with_a_warning(self):
        good = self.key_file('good.hdr')
        link = self.sb.root / 'link.hdr'
        link.symlink_to(good)
        cases = {
            'mode': [self.key_file('loose644.hdr', mode=0o644), self.key_file('loose640.hdr', mode=0o640),
                     self.key_file('loose604.hdr', mode=0o604), self.key_file('exec700.hdr', mode=0o700)],
            'readable regular file': [link, self.sb.root / 'missing.hdr', self.sb.root],
            'header line': [self.key_file('bare.hdr', text=f'{self.key}\n'),
                            self.key_file('mixed.hdr', text=f'Authorization: Bearer {self.key}\n{self.key}\n'),
                            self.key_file('empty.hdr', text='')],
        }
        for reason, paths in cases.items():
            for path in paths:
                with self.subTest(path=path.name):
                    before = len(self.stub.seen)
                    result = self.probe('/auth', path)
                    self.assertIn('NOEVIA_REMOTE_DECISION_AUTH_FILE', result.stderr)
                    self.assertIn(reason, result.stderr)
                    self.assertIn('ignored, probing without a key', result.stderr)
                    self.assertNotIn(str(path), result.stderr + result.stdout, 'the path is an .env value: not printed')
                    self.assertIn('PASS: decision runs on machine remote (HTTP 401 (needs auth))', result.stdout)
                    self.assertEqual(self.stub.seen[before:], [''], 'an ignored file sends nothing')
        for argv in self.curl_runs():
            self.assertNotIn('-H', argv)

    def test_earlier_names_still_probe_with_their_key_and_print_only_roles(self):
        path = self.key_file()
        result = self.run_lib('--probe', NOEVIA_REMOTE_SERVICES='kev,laya,embed,rerank',
                              NOEVIA_REMOTE_KEV_HEALTH_URL=self.stub.url('/auth'),
                              NOEVIA_REMOTE_KEV_AUTH_FILE=str(path),
                              NOEVIA_REMOTE_KEV_MACHINE='box1',
                              NOEVIA_REMOTE_LAYA_HEALTH_URL=self.stub.url('/auth'),
                              NOEVIA_REMOTE_EMBED_HEALTH_URL=self.stub.url('/open'),
                              NOEVIA_REMOTE_RERANK_HEALTH_URL=self.stub.url('/down'))
        self.assertEqual(result.stdout.splitlines(), [
            'PASS: decision runs on machine box1 (HTTP 200)',
            'PASS: sensitivity runs on machine remote (HTTP 401 (needs auth))',
            'PASS: embedding runs on machine remote (HTTP 200)',
            'WARN: reranker on machine remote is unhealthy (HTTP 503)',
        ])
        self.assertEqual(result.stderr, '')
        for name in ('kev', 'laya', 'embed ', 'rerank '):
            self.assertNotIn(name, result.stdout.lower() + ' ')
        listed = self.run_lib('--list', NOEVIA_REMOTE_SERVICES='kev, laya,decision')
        self.assertEqual(listed.stdout.split(), ['decision', 'sensitivity'])

    def test_the_role_variable_wins_over_the_earlier_one(self):
        result = self.run_lib('--probe', NOEVIA_REMOTE_SERVICES='decision',
                              NOEVIA_REMOTE_DECISION_HEALTH_URL=self.stub.url('/open'),
                              NOEVIA_REMOTE_KEV_HEALTH_URL=self.stub.url('/down'),
                              NOEVIA_REMOTE_KEV_AUTH_FILE=str(self.key_file(mode=0o644)))
        self.assertEqual(result.stdout.strip(), 'PASS: decision runs on machine remote (HTTP 200)')
        self.assertIn('NOEVIA_REMOTE_DECISION_AUTH_FILE must have mode 0600', result.stderr,
                      'warnings name the role variable even when the earlier one was set')

    def test_earlier_names_in_the_env_file(self):
        path = self.key_file()
        env_file = self.sb.root / 'config.env'
        env_file.write_text(f'NOEVIA_REMOTE_SERVICES=kev\nNOEVIA_REMOTE_KEV_HEALTH_URL={self.stub.url("/auth")}\n'
                            f'NOEVIA_REMOTE_KEV_AUTH_FILE="{path}"\n')
        result = self.run_lib('--probe', NOEVIA_REMOTE_ENV_FILE=str(env_file))
        self.assertEqual(result.stdout.strip(), 'PASS: decision runs on machine remote (HTTP 200)', result.stderr)

    def alert(self, state, *args, **env):
        result = self.sb.run(['bash', str(ALERT), '--state', str(state), *args], NOEVIA_REMOTE_PROBE_TIMEOUT='5', **env)
        self.outputs += [result.stdout, result.stderr]
        return result

    def notifications(self):
        return [l for l in self.sb.calls().splitlines() if l.startswith('notify')]

    def test_restart_alert_needs_auth_is_quiet_and_a_refused_key_alerts(self):
        state = self.sb.root / 'state.tsv'
        env = dict(NOEVIA_REMOTE_SERVICES='decision', NOEVIA_REMOTE_DECISION_HEALTH_URL=self.stub.url('/auth'),
                   NOEVIA_REMOTE_FAIL_THRESHOLD='1')
        for _ in range(3):
            self.alert(state, **env)
        self.assertEqual(self.notifications(), [], 'a 401 with no key sent is not an outage (#1980)')
        self.assertIn('decision\thealthy\t0\t0', Path(str(state) + '.remote').read_text())
        wrong = self.key_file(value='synthetic-wrong-' + secrets.token_hex(8))
        self.alert(state, NOEVIA_REMOTE_DECISION_AUTH_FILE=str(wrong), **env)
        notes = self.notifications()
        self.assertEqual(len(notes), 1)
        self.assertIn('decision down on remote', notes[0])
        self.assertIn('HTTP 401 (key refused)', notes[0])
        self.alert(state, NOEVIA_REMOTE_DECISION_AUTH_FILE=str(self.key_file()), **env)
        notes = self.notifications()
        self.assertEqual(len(notes), 2)
        self.assertIn('decision recovered on remote', notes[1])

    def test_restart_alert_carries_over_state_written_under_the_earlier_name(self):
        state = self.sb.root / 'state.tsv'
        remote_state = Path(str(state) + '.remote')
        remote_state.write_text('kev\tunreachable\t4\t1\nembed\thealthy\t0\t0\n')
        self.alert(state, NOEVIA_REMOTE_SERVICES='kev', NOEVIA_REMOTE_KEV_HEALTH_URL=self.stub.url('/open'))
        notes = self.notifications()
        self.assertEqual(len(notes), 1, 'the alert raised under the earlier name still gets its recovery notice')
        self.assertIn('decision recovered on remote', notes[0])
        self.assertEqual(remote_state.read_text(), 'decision\thealthy\t0\t0\n')


class PreflightRoleTests(unittest.TestCase):
    def test_each_role_warns_about_its_own_local_service(self):
        sb = Sandbox(self)
        (sb.root / 'services').write_text('web\nlaya\nrerank\n')
        result = sb.run(['bash', str(UP), '--', '-d'], COWORK_PROJECT_DIR=str(sb.root), SIDECAR_ALERT_ACK='0',
                        NOEVIA_REMOTE_SERVICES='sensitivity,embedding,decision')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('WARN: sensitivity is assigned to another machine but its local sidecar is still enabled',
                      result.stderr)
        self.assertNotIn('WARN: embedding is assigned', result.stderr)
        self.assertNotIn('WARN: decision is assigned', result.stderr)
        self.assertNotIn('laya', result.stderr + result.stdout)


class DocsTests(unittest.TestCase):
    def test_docs_describe_roles_earlier_names_and_the_auth_file(self):
        text = (ROOT / 'docs/deployment.md').read_text()
        self.assertIn('NOEVIA_REMOTE_<ROLE>_AUTH_FILE', text)
        self.assertIn('HTTP 401 (needs auth)', text)
        for row in ('| `decision` | `kev` |', '| `sensitivity` | `laya` |', '| `embedding` | `embed` |',
                    '| `reranker` | `rerank` |'):
            self.assertIn(row, text)
        lib = LIB.read_text()
        self.assertIn('remote_known_services="decision sensitivity embedding reranker"', lib)


if __name__ == '__main__':
    unittest.main()
