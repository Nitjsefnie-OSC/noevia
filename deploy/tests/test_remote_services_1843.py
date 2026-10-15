"""#1843: services assigned to another Inference machine (preflight, restart alert, compose defaults).

curl, docker and notify are PATH shims; nothing leaves the machine and no real host is probed.
"""
import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / 'deploy/tools/remote-services.sh'
ALERT = ROOT / 'deploy/tools/sidecar-restart-alert.sh'
UP = ROOT / 'deploy/preflight/up.sh'


class Sandbox:
    def __init__(self, test):
        self.tmp = tempfile.TemporaryDirectory()
        test.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'calls.log'
        self.answers = self.root / 'answers'  # url substring -> http code, or "fail"
        self.answers.mkdir()
        self.shim('curl', '''#!/bin/bash
echo "curl $*" >> "$QA_LOG"
url="${@: -1}"
for f in "$QA_ANSWERS"/*; do
  [ -f "$f" ] || continue
  if [[ "$url" == *"$(basename "$f")"* ]]; then
    a="$(cat "$f")"; [ "$a" = fail ] && exit 28; printf '%s' "$a"; exit 0
  fi
done
exit 7
''')
        self.shim('notify', '#!/bin/bash\necho "notify $*" >> "$QA_LOG"\n')
        self.shim('docker', '''#!/bin/bash
echo "docker $*" >> "$QA_LOG"
case " $* " in
  *" config --services"*) cat "$QA_SERVICES" 2>/dev/null ;;
  *" config "*) printf '{"services":{"web":{}}}' ;;
  *" ps "*) : ;;
esac
''')
        self.shim('php', '#!/bin/bash\ncat >/dev/null\n')
        (self.root / 'services').write_text('web\nllama\n')

    def shim(self, name, body):
        path = self.bin / name
        path.write_text(body)
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def answer(self, key, value):
        (self.answers / key).write_text(value)

    def env(self, **extra):
        env = {k: v for k, v in os.environ.items()
               if not k.startswith('NOEVIA_REMOTE') and k != 'COWORK_PROJECT_DIR'}
        env.update(PATH=f'{self.bin}{os.pathsep}{env["PATH"]}', QA_LOG=str(self.log),
                   QA_ANSWERS=str(self.answers), QA_SERVICES=str(self.root / 'services'))
        env.update(extra)
        return env

    def run(self, args, **extra):
        return subprocess.run(args, env=self.env(**extra), cwd=self.root, capture_output=True, text=True, timeout=60)

    def calls(self):
        return self.log.read_text() if self.log.exists() else ''


REMOTE = dict(NOEVIA_REMOTE_SERVICES='embed,rerank',
              NOEVIA_REMOTE_EMBED_HEALTH_URL='http://pi5.lan:8080/health',
              NOEVIA_REMOTE_EMBED_MACHINE='pi5',
              NOEVIA_REMOTE_RERANK_HEALTH_URL='http://100.64.0.7:8080/health')


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.sb = Sandbox(self)

    def probe(self, **extra):
        return self.sb.run(['bash', str(LIB), '--probe'], **extra)

    def test_nothing_configured_is_silent_and_never_calls_curl(self):
        result = self.probe()
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        self.assertEqual(self.sb.calls(), '')

    def test_healthy_unhealthy_and_unreachable_are_distinguished(self):
        self.sb.answer('pi5.lan', '200')
        self.sb.answer('100.64.0.7', '503')
        out = self.probe(**REMOTE).stdout
        self.assertIn('PASS: embed runs on machine pi5 (HTTP 200)', out)
        self.assertIn('WARN: rerank on machine remote is unhealthy (HTTP 503)', out)
        self.sb.answer('pi5.lan', 'fail')
        self.assertIn('WARN: embed on machine pi5 is unreachable', self.probe(**REMOTE).stdout)

    def test_probe_is_bounded_and_never_follows_redirects_or_proxies(self):
        self.sb.answer('pi5.lan', '200')
        self.probe(**{**REMOTE, 'NOEVIA_REMOTE_PROBE_TIMEOUT': '2'})
        line = [l for l in self.sb.calls().splitlines() if 'pi5.lan' in l][0]
        self.assertIn('--max-time 2', line)
        self.assertIn('--connect-timeout 2', line)
        self.assertIn("--noproxy *", line)
        self.assertNotIn(' -L', line)
        self.probe(**{**REMOTE, 'NOEVIA_REMOTE_PROBE_TIMEOUT': '9999'})
        self.assertIn('--max-time 3', self.sb.calls().splitlines()[-1])

    def test_only_lan_or_tailscale_hosts_are_contacted(self):
        refused = ['http://example.com/health', 'http://8.8.8.8/health', 'http://172.32.0.1/health',
                   'http://100.128.0.1/health', 'http://user:pw@pi5.lan/health', 'ftp://pi5.lan/x',
                   'http://pi5.lan.evil.com/health', 'http://[2001:db8::1]/health', 'pi5.lan/health']
        for url in refused:
            with self.subTest(url=url):
                out = self.probe(NOEVIA_REMOTE_SERVICES='embed', NOEVIA_REMOTE_EMBED_HEALTH_URL=url).stdout
                self.assertIn('is refused', out)
                self.assertNotIn('pw', out)
        self.assertEqual(self.sb.calls(), '')
        self.sb.answer('x', '200')
        for url in ['http://10.1.2.3/h', 'http://172.16.0.9:81/h', 'http://192.168.1.5/h', 'http://100.101.102.103/h',
                    'http://pi5/h', 'http://pi.tail1234.ts.net:8080/h', 'http://box.local/h', 'http://[fd00::5]:8080/h',
                    'http://127.0.0.1:9/h']:
            with self.subTest(url=url):
                out = self.probe(NOEVIA_REMOTE_SERVICES='kev', NOEVIA_REMOTE_KEV_HEALTH_URL=url).stdout
                self.assertNotIn('is refused', out)

    def test_unknown_and_duplicate_names_and_missing_url(self):
        result = self.probe(NOEVIA_REMOTE_SERVICES=' Embed, bogus ,embed')
        self.assertIn("unknown service 'bogus'", result.stderr)
        self.assertEqual(result.stdout.count('embed'), 1)
        self.assertIn('INFO: embed is assigned to machine remote', result.stdout)
        self.assertEqual(self.sb.calls(), '')

    def test_env_file_reads_only_remote_keys_and_never_executes(self):
        marker = self.sb.root / 'pwned'
        env_file = self.sb.root / 'config.env'
        env_file.write_text(
            f'MODEL_LOADER_TOKEN=secret-should-not-load\nNOEVIA_REMOTE_SERVICES="embed"\n'
            f'NOEVIA_REMOTE_EMBED_HEALTH_URL=http://pi5.lan/health $(touch {marker})\n')
        self.sb.answer('pi5.lan', '200')
        result = self.sb.run(['bash', str(LIB), '--probe'], NOEVIA_REMOTE_ENV_FILE=str(env_file))
        self.assertIn('embed', result.stdout)
        self.assertFalse(marker.exists())
        self.assertNotIn('secret-should-not-load', result.stdout + result.stderr + self.sb.calls())
        # An explicit environment variable wins over the file.
        result = self.sb.run(['bash', str(LIB), '--list'], NOEVIA_REMOTE_ENV_FILE=str(env_file), NOEVIA_REMOTE_SERVICES='rerank')
        self.assertEqual(result.stdout.strip(), 'rerank')


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.sb = Sandbox(self)

    def up(self, **extra):
        return self.sb.run(['bash', str(UP), '--', '-d'], COWORK_PROJECT_DIR=str(self.sb.root),
                           SIDECAR_ALERT_ACK='0', **extra)

    def test_unconfigured_never_probes_and_prints_nothing_extra(self):
        result = self.up()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('curl', self.sb.calls())
        self.assertNotIn('--services', self.sb.calls())
        self.assertNotIn('remote', (result.stdout + result.stderr).lower())

    def test_stopped_local_sidecar_never_fails_and_remote_is_reported(self):
        self.sb.answer('pi5.lan', '200')
        self.sb.answer('100.64.0.7', 'fail')
        result = self.up(**REMOTE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('PASS: embed runs on machine pi5', result.stdout)
        self.assertIn('WARN: rerank on machine remote is unreachable', result.stdout)
        self.assertIn('up -d', self.sb.calls())  # up still ran

    def test_warns_when_assigned_service_would_still_start_locally(self):
        (self.sb.root / 'services').write_text('web\nembed\n')
        self.sb.answer('pi5.lan', '200')
        result = self.up(**REMOTE)
        self.assertEqual(result.returncode, 0)
        self.assertRegex(result.stderr, r'WARN: embed is assigned to another machine but is still enabled')
        self.assertNotIn('WARN: rerank is assigned', result.stderr)

    def test_missing_library_warns_but_still_starts(self):
        lone = self.sb.root / 'lone'
        lone.mkdir()
        for name in ('up.sh', 'diary-image-guard.sh'):
            (lone / name).write_text((ROOT / 'deploy/preflight' / name).read_text())
        result = self.sb.run(['bash', str(lone / 'up.sh'), '--', '-d'], COWORK_PROJECT_DIR=str(self.sb.root),
                             SIDECAR_ALERT_ACK='0', **REMOTE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('remote-services.sh was not found', result.stderr)
        self.assertNotIn('curl', self.sb.calls())


class AlertTests(unittest.TestCase):
    def setUp(self):
        self.sb = Sandbox(self)
        self.state = self.sb.root / 'state.tsv'

    def alert(self, *args, **extra):
        return self.sb.run(['bash', str(ALERT), '--state', str(self.state), *args], **extra)

    def notifications(self):
        return [l for l in self.sb.calls().splitlines() if l.startswith('notify')]

    def test_unconfigured_writes_no_remote_state_and_probes_nothing(self):
        result = self.alert()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(Path(str(self.state) + '.remote').exists())
        self.assertNotIn('curl', self.sb.calls())

    def test_down_alerts_once_after_threshold_and_recovery_notifies_once(self):
        self.sb.answer('pi5.lan', '200')
        self.sb.answer('100.64.0.7', '200')
        self.alert(**REMOTE)  # first run: baseline only
        self.assertEqual(self.notifications(), [])
        self.sb.answer('pi5.lan', 'fail')
        self.alert(**REMOTE)
        self.assertEqual(self.notifications(), [], 'one failure is below the default threshold of 2')
        self.alert(**REMOTE)
        notes = self.notifications()
        self.assertEqual(len(notes), 1)
        self.assertIn('embed down on pi5', notes[0])
        self.assertIn('-i alert', notes[0])
        self.alert(**REMOTE)
        self.assertEqual(len(self.notifications()), 1, 'not re-alerted while still down')
        self.sb.answer('pi5.lan', '200')
        self.alert(**REMOTE)
        notes = self.notifications()
        self.assertEqual(len(notes), 2)
        self.assertIn('embed recovered on pi5', notes[1])
        self.assertIn('-i normal', notes[1])
        self.alert(**REMOTE)
        self.assertEqual(len(self.notifications()), 2)

    def test_threshold_override_and_dry_run_and_ack(self):
        self.sb.answer('pi5.lan', '200')
        self.sb.answer('100.64.0.7', '200')
        self.alert(**REMOTE)
        remote_state = Path(str(self.state) + '.remote')
        before = remote_state.read_text()
        self.sb.answer('pi5.lan', '500')
        dry = self.alert('--dry-run', NOEVIA_REMOTE_FAIL_THRESHOLD='1', **REMOTE)
        self.assertIn('embed down on pi5', dry.stdout)
        self.assertEqual(remote_state.read_text(), before, '--dry-run never moves the baseline')
        self.assertEqual(self.notifications(), [])
        self.alert('--ack', NOEVIA_REMOTE_FAIL_THRESHOLD='1', **REMOTE)
        self.assertEqual(self.notifications(), [], '--ack silences a service that is already down')
        self.alert(NOEVIA_REMOTE_FAIL_THRESHOLD='1', **REMOTE)
        self.assertEqual(self.notifications(), [])

    def test_failed_notify_retries_next_run(self):
        self.sb.answer('pi5.lan', '200')
        self.sb.answer('100.64.0.7', '200')
        self.alert(**REMOTE)
        self.sb.answer('pi5.lan', 'fail')
        self.sb.shim('notify', '#!/bin/bash\necho "notify $*" >> "$QA_LOG"\nexit 1\n')
        env = dict(NOEVIA_REMOTE_FAIL_THRESHOLD='1', **REMOTE)
        self.alert(**env)
        self.assertEqual(len(self.notifications()), 1)
        self.sb.shim('notify', '#!/bin/bash\necho "notify $*" >> "$QA_LOG"\n')
        self.alert(**env)
        self.assertEqual(len(self.notifications()), 2)
        self.alert(**env)
        self.assertEqual(len(self.notifications()), 2)

    def test_no_secret_in_logs_or_notifications(self):
        self.sb.answer('pi5.lan', 'fail')
        env = dict(REMOTE, NOEVIA_REMOTE_FAIL_THRESHOLD='1', NOEVIA_REMOTE_EMBED_HEALTH_URL='http://pi5.lan/health?k=SECRETVALUE')
        self.alert(**env)
        result = self.alert(**env)
        self.assertNotIn('SECRETVALUE', result.stdout + result.stderr + '\n'.join(self.notifications()))


class DefaultsUnchangedTests(unittest.TestCase):
    def test_compose_files_do_not_mention_remote_services(self):
        for name in ['compose.yaml', 'compose.embed.yaml', 'compose.rerank.yaml', 'compose.llamacpp.yaml']:
            self.assertNotIn('NOEVIA_REMOTE', (ROOT / name).read_text(), name)

    def test_laya_stays_behind_its_profile_and_overlays_are_not_default(self):
        compose = (ROOT / 'compose.yaml').read_text()
        self.assertRegex(compose, r'(?m)^  laya:\n    profiles: \[laya\]')

    def test_docs_state_remote_services_are_outside_the_budget(self):
        text = (ROOT / 'docs/deployment.md').read_text()
        self.assertIn('## Services on other Inference machines (#1843)', text)
        self.assertRegex(text, r'not counted against this host.s budget')
        self.assertIn('is outside this budget too', text)


if __name__ == '__main__':
    unittest.main()
