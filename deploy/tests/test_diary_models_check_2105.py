"""#2105: the release preflight refuses a cutover when the diary's configured chat or aux model id
(or the explicit fallback the diary would use instead) is not served by the chat router.

Everything here is synthetic: env files are written to a temp directory and the router is a stub HTTP
server on the loopback interface that records each request. The check must make exactly one read-only
GET of the model list, fail closed on every other outcome, and never print a value from the env file.
"""
import json
import os
import pathlib
import re
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[2]
CHECK = ROOT / 'deploy/preflight/diary-models-check.sh'
OVERLAY = ROOT / 'deploy/examples/overlay-release.sh'
DIARY = ROOT / 'deploy/examples/diary-overlay.sh'

CHAT = 'synthetic-chat-a'
AUX = 'synthetic-aux-b'
OTHER = 'synthetic-other-c'
KEY = 'synthetic-api-key-0123456789'


def listing(*ids, flags=None):
    """A /v1/models body. flags maps an id to router launch args (a router section's status.args)."""
    data = []
    for model_id in ids:
        item = {'id': model_id, 'object': 'model'}
        if flags and model_id in flags:
            item['status'] = {'value': 'unloaded', 'args': flags[model_id]}
        data.append(item)
    return json.dumps({'object': 'list', 'data': data}).encode()


class Router:
    """A stub router. `answers` maps a path to (status, headers, body); anything else is a 404."""

    def __init__(self, models=None, status=200, headers=None, body=None):
        self.requests = []
        self.auth = []
        answer = (status, headers or {}, body if body is not None else listing(*(models or [])))
        self.answers = {'/v1/models': answer}
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def respond(self):
                outer.requests.append((self.command, self.path))
                outer.auth.append(self.headers.get('Authorization'))
                code, hdrs, payload = outer.answers.get(self.path, (404, {}, b'{}'))
                self.send_response(code)
                for name, value in hdrs.items():
                    self.send_header(name, value)
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST = do_PUT = do_DELETE = respond

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.url = f'http://127.0.0.1:{self.server.server_address[1]}/v1'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)


class CheckTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = pathlib.Path(tempfile.mkdtemp(prefix='noevia-models-check-'))
        self.addCleanup(lambda: __import__('shutil').rmtree(self.temp, ignore_errors=True))

    def env_file(self, **keys):
        path = self.temp / 'cutover.env'
        path.write_text(''.join(f'{k}={v}\n' for k, v in keys.items() if v is not None))
        return path

    def run_check(self, env_path, bash_flags=()):
        return subprocess.run(['bash', *bash_flags, str(CHECK), '--env-file', str(env_path)],
                              capture_output=True, text=True, timeout=60)

    def assert_refused(self, result, *needles):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('REFUSED', result.stderr)
        for needle in needles:
            self.assertIn(needle, result.stderr)

    def assert_no_values(self, result, *values):
        for value in values:
            self.assertNotIn(value, result.stdout)
            self.assertNotIn(value, result.stderr)


def settings(router, **extra):
    base = {'INFERENCE_BASE_URL': router.url, 'DIARY_CHAT_MODEL': CHAT, 'DIARY_AUX_MODEL': AUX}
    base.update(extra)
    return base


class PassAndRefuse(CheckTestCase):
    def test_passes_when_both_ids_are_served(self):
        with Router([CHAT, AUX, OTHER]) as router:
            result = self.run_check(self.env_file(**settings(router)))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('diary model check passed', result.stdout)
            self.assertEqual(router.requests, [('GET', '/v1/models')], 'one read-only GET of the model list, nothing else')

    def test_an_unserved_chat_id_refuses_naming_the_key_not_the_value(self):
        with Router([AUX, OTHER]) as router:
            result = self.run_check(self.env_file(**settings(router)))
            self.assert_refused(result, 'DIARY_CHAT_MODEL', 'LLM_CHAT_FALLBACK_MODEL')
            self.assertNotIn('DIARY_AUX_MODEL is', result.stderr)
            self.assert_no_values(result, CHAT, AUX, router.url, '127.0.0.1')

    def test_an_unserved_aux_id_refuses(self):
        with Router([CHAT, OTHER]) as router:
            result = self.run_check(self.env_file(**settings(router)))
            self.assert_refused(result, 'DIARY_AUX_MODEL', 'LLM_AUX_FALLBACK_MODEL')
            self.assertNotIn('the id set in DIARY_CHAT_MODEL is not served', result.stderr)
            self.assert_no_values(result, CHAT, AUX)

    def test_both_unserved_reports_both(self):
        with Router([OTHER]) as router:
            result = self.run_check(self.env_file(**settings(router)))
            self.assert_refused(result, 'DIARY_CHAT_MODEL', 'DIARY_AUX_MODEL')

    def test_an_unset_aux_id_follows_the_chat_id_like_compose(self):
        with Router([CHAT]) as router:
            result = self.run_check(self.env_file(**settings(router, DIARY_AUX_MODEL=None)))
            self.assertEqual(result.returncode, 0, result.stderr)
        with Router([OTHER]) as router:
            result = self.run_check(self.env_file(**settings(router, DIARY_AUX_MODEL='default')))
            self.assert_refused(result, 'DIARY_AUX_MODEL')

    def test_a_listed_embedding_or_reranking_section_is_not_a_chat_model(self):
        for flag in ('--embedding', '--embeddings', '--reranking', '--rerank'):
            with self.subTest(flag=flag), Router(body=listing(CHAT, AUX, flags={AUX: ['--model', 'x', flag]})) as router:
                result = self.run_check(self.env_file(**settings(router)))
                self.assert_refused(result, 'DIARY_AUX_MODEL')

    def test_an_unloaded_chat_section_still_counts_as_served(self):
        # The check must not require (or cause) a load: a sleeping model is served.
        body = listing(CHAT, AUX, flags={CHAT: ['--ctx-size', '4096'], AUX: []})
        with Router(body=body) as router:
            result = self.run_check(self.env_file(**settings(router)))
            self.assertEqual(result.returncode, 0, result.stderr)


class Fallbacks(CheckTestCase):
    def test_a_served_explicit_fallback_passes_with_a_notice(self):
        with Router([OTHER, AUX]) as router:
            result = self.run_check(self.env_file(**settings(router, LLM_CHAT_FALLBACK_MODEL=OTHER)))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('NOTICE', result.stdout)
            self.assertIn('LLM_CHAT_FALLBACK_MODEL', result.stdout)
            self.assert_no_values(result, CHAT, OTHER)

    def test_a_served_aux_fallback_passes(self):
        with Router([CHAT, OTHER]) as router:
            result = self.run_check(self.env_file(**settings(router, LLM_AUX_FALLBACK_MODEL=OTHER)))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('LLM_AUX_FALLBACK_MODEL', result.stdout)

    def test_an_unserved_fallback_refuses(self):
        with Router([AUX]) as router:
            result = self.run_check(self.env_file(**settings(router, LLM_CHAT_FALLBACK_MODEL=OTHER)))
            self.assert_refused(result, 'DIARY_CHAT_MODEL', 'LLM_CHAT_FALLBACK_MODEL', 'not served either')
            self.assert_no_values(result, OTHER, CHAT)

    def test_a_fallback_that_is_not_a_chat_model_does_not_rescue(self):
        with Router(body=listing(AUX, OTHER, flags={OTHER: ['--embedding']})) as router:
            result = self.run_check(self.env_file(**settings(router, LLM_CHAT_FALLBACK_MODEL=OTHER)))
            self.assert_refused(result, 'LLM_CHAT_FALLBACK_MODEL')

    def test_the_diarys_implicit_follow_the_chat_model_substitute_is_not_accepted(self):
        # The diary would follow the chat id for an unserved aux id, but nobody named that: refuse.
        with Router([CHAT]) as router:
            result = self.run_check(self.env_file(**settings(router)))
            self.assert_refused(result, 'DIARY_AUX_MODEL')

    def test_each_role_uses_only_its_own_fallback(self):
        with Router([OTHER]) as router:
            result = self.run_check(self.env_file(**settings(router, LLM_AUX_FALLBACK_MODEL=OTHER)))
            self.assert_refused(result, 'DIARY_CHAT_MODEL')
            self.assertNotIn('the id set in DIARY_AUX_MODEL', result.stderr)


class FailClosed(CheckTestCase):
    def test_an_unreachable_router_refuses(self):
        with Router([CHAT, AUX]) as router:
            url = router.url
        # The stub is shut down: the port now refuses connections.
        result = self.run_check(self.env_file(INFERENCE_BASE_URL=url, DIARY_CHAT_MODEL=CHAT, DIARY_AUX_MODEL=AUX))
        self.assert_refused(result, 'INFERENCE_BASE_URL', 'could not be reached')
        self.assert_no_values(result, url, '127.0.0.1', CHAT)

    def test_a_non_200_answer_refuses(self):
        for status in (401, 403, 404, 500, 503):
            with self.subTest(status=status), Router(status=status, body=b'{}') as router:
                result = self.run_check(self.env_file(**settings(router)))
                self.assert_refused(result, f'HTTP {status}')

    def test_a_redirect_is_not_followed(self):
        with Router(status=302, headers={'Location': '/v1/models2'}, body=b'') as router:
            router.answers['/v1/models2'] = (200, {}, listing(CHAT, AUX))
            result = self.run_check(self.env_file(**settings(router)))
            self.assert_refused(result, 'HTTP 302')
            self.assertEqual(router.requests, [('GET', '/v1/models')])

    def test_a_body_that_is_not_a_model_list_refuses(self):
        for body in (b'not json', b'{}', b'{"data": {"id": "x"}}', b'[]', b'{"data": []}'):
            with self.subTest(body=body), Router(body=body) as router:
                result = self.run_check(self.env_file(**settings(router)))
                self.assert_refused(result)

    def test_missing_keys_refuse_without_contacting_anything(self):
        with Router([CHAT, AUX]) as router:
            cases = {
                'DIARY_CHAT_MODEL': settings(router, DIARY_CHAT_MODEL=None),
                'DIARY_CHAT_MODEL (empty)': settings(router, DIARY_CHAT_MODEL=''),
                'DIARY_CHAT_MODEL (placeholder)': settings(router, DIARY_CHAT_MODEL='default'),
                'INFERENCE_BASE_URL': settings(router, INFERENCE_BASE_URL=None),
                'INFERENCE_BASE_URL (empty)': settings(router, INFERENCE_BASE_URL=''),
            }
            for name, keys in cases.items():
                with self.subTest(missing=name):
                    result = self.run_check(self.env_file(**keys))
                    self.assert_refused(result, name.split(' ')[0])
            self.assertEqual(router.requests, [], 'nothing is contacted when a key is missing')

    def test_the_key_is_looked_up_in_the_file_given_not_in_the_process_environment(self):
        with Router([CHAT, AUX]) as router:
            env_path = self.env_file(INFERENCE_BASE_URL=router.url, DIARY_AUX_MODEL=AUX)
            result = subprocess.run(['bash', str(CHECK), '--env-file', str(env_path)], capture_output=True, text=True,
                                    timeout=60, env=dict(os.environ, DIARY_CHAT_MODEL=CHAT))
            self.assert_refused(result, 'DIARY_CHAT_MODEL')

    def test_an_unreadable_env_file_and_bad_usage_fail(self):
        result = self.run_check(self.temp / 'does-not-exist.env')
        self.assert_refused(result, 'not readable')
        usage = subprocess.run(['bash', str(CHECK)], capture_output=True, text=True, timeout=30)
        self.assertEqual(usage.returncode, 2)
        self.assertIn('usage', usage.stderr)

    def test_a_non_http_router_address_refuses(self):
        for url in ('ftp://127.0.0.1/v1', 'host-without-scheme', 'http://user:pw@127.0.0.1:9/v1'):
            with self.subTest(url=url):
                result = self.run_check(self.env_file(INFERENCE_BASE_URL=url, DIARY_CHAT_MODEL=CHAT))
                self.assert_refused(result, 'INFERENCE_BASE_URL')
                self.assert_no_values(result, 'pw@')


class EnvFileAndSecrets(CheckTestCase):
    def test_comments_quotes_export_and_the_last_assignment_are_read_like_compose(self):
        with Router([CHAT, AUX]) as router:
            path = self.temp / 'cutover.env'
            path.write_text('\r\n'.join([
                '# a comment: DIARY_CHAT_MODEL=ignored',
                'DIARY_CHAT_MODEL=stale-first-value',
                f'export DIARY_CHAT_MODEL="{CHAT}"',
                f"DIARY_AUX_MODEL='{AUX}'   # trailing comment",
                f'INFERENCE_BASE_URL={router.url}',
                'UNRELATED=1', '']))
            result = self.run_check(path)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_credential_is_sent_as_a_bearer_header_and_never_printed(self):
        with Router([OTHER]) as router:
            keys = settings(router, INFERENCE_API_KEY=KEY)
            for flags in ((), ('-x',)):
                with self.subTest(flags=flags):
                    result = self.run_check(self.env_file(**keys), bash_flags=flags)
                    self.assert_refused(result, 'DIARY_CHAT_MODEL')
                    self.assert_no_values(result, KEY, CHAT, AUX, OTHER, router.url, '127.0.0.1')
            self.assertEqual(router.auth, [f'Bearer {KEY}'] * 2)

    def test_a_separate_aux_router_is_checked_with_its_own_credential(self):
        aux_key = KEY + '-aux'
        with Router([CHAT]) as chat_router, Router([AUX]) as aux_router:
            keys = settings(chat_router, INFERENCE_API_KEY=KEY, AUX_INFERENCE_BASE_URL=aux_router.url, AUX_INFERENCE_API_KEY=aux_key)
            result = self.run_check(self.env_file(**keys))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(chat_router.auth, [f'Bearer {KEY}'])
            self.assertEqual(aux_router.auth, [f'Bearer {aux_key}'])
        with Router([CHAT]) as chat_router, Router([OTHER]) as aux_router:
            result = self.run_check(self.env_file(**settings(chat_router, AUX_INFERENCE_BASE_URL=aux_router.url)))
            self.assert_refused(result, 'DIARY_AUX_MODEL')

    def test_the_script_only_ever_reads_the_model_list(self):
        text = CHECK.read_text()
        code = '\n'.join(l for l in text.splitlines() if not l.lstrip().startswith('#'))
        for forbidden in ('/slots', '/completion', '/chat/', '/props', '/load'):
            self.assertNotIn(forbidden, code, forbidden)
        calls = [l for l in code.splitlines() if re.search(r'\| curl |\bcurl "\$\{curl_args', l)]
        self.assertEqual(len(calls), 2, calls)  # with and without a credential: the same single GET
        for line in calls:
            self.assertIn('"$base/models"', line)
            self.assertIsNone(re.search(r'\s-(X|d|L|F|T)\b|--(data|request|upload|location|form)', line), line)


class CutoverHooks(unittest.TestCase):
    """Both overlay scripts run the check against their own .env before they change anything."""

    def hook(self, script):
        text = script.read_text()
        self.assertEqual(text.count('# BEGIN diary-models-check'), 1)
        block = text[text.index('# BEGIN diary-models-check'):text.index('# END diary-models-check')]
        self.assertIn('diary-models-check.sh" --env-file "$config"', block)
        self.assertIn('exit 1', block)
        return text

    def test_overlay_release_checks_before_any_change(self):
        text = self.hook(OVERLAY)
        start = text.index('# BEGIN diary-models-check')
        for change in ['old_native=$(container_id', 'mkdir -p "$base/releases/$NEW"', 'docker build', 'ln -sfn', 'sed -i', 'cp -p "$config"', 'up.sh']:
            self.assertLess(start, text.index(change, text.index('# END preflight-installed')), change)

    def test_diary_overlay_checks_before_any_change(self):
        text = self.hook(DIARY)
        start = text.index('# BEGIN diary-models-check')
        for change in ['docker image inspect', 'docker tag', 'docker build', 'docker stop', 'cp -p "$config"', 'sed -i', 'up.sh" --env-file']:
            self.assertLess(start, text.index(change, text.index('# END preflight-installed')), change)

    def test_the_installer_ships_the_check(self):
        text = (ROOT / 'deploy/preflight/install.sh').read_text()
        self.assertIn('required=(up.sh diary-image-guard.sh check.php diary-models-check.sh)', text)

    def test_compose_passes_the_explicit_fallback_keys_to_the_diary(self):
        # The check reads these keys from the .env; without a mapping the diary would never see them.
        for path in ('compose.yaml', 'deploy/examples/unraid-compose-manager.yml'):
            text = (ROOT / path).read_text()
            with self.subTest(path=path):
                self.assertIn('LLM_CHAT_FALLBACK_MODEL: ${LLM_CHAT_FALLBACK_MODEL:-}', text)
                self.assertIn('LLM_AUX_FALLBACK_MODEL: ${LLM_AUX_FALLBACK_MODEL:-}', text)


if __name__ == '__main__':
    unittest.main()
