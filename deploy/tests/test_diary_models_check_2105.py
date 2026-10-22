"""#2105: the release preflight refuses a cutover when the model ids the diary container will receive (or the
explicit fallback it would use instead) are not served by the chat router.

What is checked is the diary service's environment in the RESOLVED Compose configuration, so the tests put a
stub `docker` on PATH that answers `compose ... config --format json` with a synthetic configuration, and a stub
router on the loopback interface that records each request. No real docker, no external network. The check
must make one read-only GET of the model list, fail closed on every other outcome, and never print a value.
"""
import json
import os
import pathlib
import re
import shutil
import stat
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
TOKEN = 'synthetic-diary-token-987654'

STUB_DOCKER = r"""#!/bin/bash
log="$*"
printf '%s|%s\n' "$PWD" "${log//$'\n'/ }" >> "$STUB_DOCKER_LOG"
case "${1:-}" in
  compose)
    case " $* " in
      *" ps -q diary "*) [ -z "${STUB_DIARY_CID:-}" ] || echo "$STUB_DIARY_CID"; exit 0 ;;
      *" config "*) ;;
      *) exit 64 ;;
    esac
    [ -z "${STUB_COMPOSE_FAIL:-}" ] || { echo "interpolated: $STUB_SECRET" >&2; exit "$STUB_COMPOSE_FAIL"; }
    cat "$STUB_COMPOSE_JSON"
    ;;
  exec)
    # `docker exec -i <container> python -c <script>`: runs the script here with stdin passed through. Inside the
    # diary container the Compose service name resolves; here the alias is mapped to the loopback interface.
    [ -z "${STUB_EXEC_FAIL:-}" ] || exit "$STUB_EXEC_FAIL"
    [ "${2:-}" = -i ] && [ "${3:-}" = "${STUB_DIARY_CID:-none}" ] && [ "${4:-}" = python ] && [ "${5:-}" = -c ] || exit 64
    exec python3 -c 'import socket, sys
_g = socket.getaddrinfo
socket.getaddrinfo = lambda h, *a, **k: _g("127.0.0.1" if h == "router-relay" else h, *a, **k)
exec(sys.argv[1])' "$6"
    ;;
  *) exit 64 ;;
esac
"""

# The host cannot resolve a Compose service name: curl reports exit 6 for the alias, like a real resolver would.
STUB_CURL = r"""#!/bin/bash
case "$*" in *router-relay*) cat >/dev/null 2>&1 </dev/null; exit 6 ;; esac
exec "$STUB_REAL_CURL" "$@"
"""

ALIAS = 'router-relay'
CID = 'synthetic-diary-container-id'


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


def diary_env(router=None, url=None, **overrides):
    """The diary service's resolved environment. A value of None leaves the key out (it is not mapped)."""
    env = {'LLM_BASE_URL': url if url is not None else router.url, 'LLM_CHAT_MODEL': CHAT, 'LLM_AUX_MODEL': AUX,
           'DIARY_AUTH_TOKEN': TOKEN}
    env.update(overrides)
    return {k: v for k, v in env.items() if v is not None}


class CheckTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = pathlib.Path(tempfile.mkdtemp(prefix='noevia-models-check-'))
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        self.bin = self.temp / 'bin'
        self.bin.mkdir()
        docker = self.bin / 'docker'
        docker.write_text(STUB_DOCKER)
        docker.chmod(docker.stat().st_mode | stat.S_IXUSR)
        curl = self.bin / 'curl'
        curl.write_text(STUB_CURL)
        curl.chmod(curl.stat().st_mode | stat.S_IXUSR)
        self.real_curl = shutil.which('curl')
        self.docker_log = self.temp / 'docker.log'
        self.env_path = self.temp / 'cutover.env'
        self.env_path.write_text('# synthetic: the check never reads this file itself\n')

    def compose(self, env, services=None, raw=None):
        path = self.temp / 'compose.json'
        if raw is not None:
            path.write_bytes(raw)
        else:
            data = {'services': {'web': {'environment': {'X': '1'}}, 'diary': {'environment': env}}}
            if services is not None:
                data = {'services': services}
            path.write_text(json.dumps(data))
        return path

    def run_check(self, env=None, bash_flags=(), extra_args=(), compose_fail=None, raw=None, services=None, path=None,
                  diary_cid=None, exec_fail=None):
        compose_json = self.compose(env if env is not None else {}, services=services, raw=raw)
        environ = dict(os.environ, PATH=f'{self.bin}{os.pathsep}{os.environ["PATH"]}', STUB_DOCKER_LOG=str(self.docker_log),
                       STUB_COMPOSE_JSON=str(compose_json), STUB_SECRET=KEY, STUB_REAL_CURL=self.real_curl or 'curl')
        if compose_fail:
            environ['STUB_COMPOSE_FAIL'] = str(compose_fail)
        if diary_cid:
            environ['STUB_DIARY_CID'] = diary_cid
        if exec_fail:
            environ['STUB_EXEC_FAIL'] = str(exec_fail)
        if path is not None:
            environ['PATH'] = path
        return subprocess.run([shutil.which('bash'), *bash_flags, str(CHECK), '--env-file', str(self.env_path), *extra_args],
                              capture_output=True, text=True, timeout=60, env=environ)

    def assert_refused(self, result, *needles):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('REFUSED', result.stderr)
        for needle in needles:
            self.assertIn(needle, result.stderr)

    def assert_no_values(self, result, *values):
        for value in values:
            self.assertNotIn(value, result.stdout)
            self.assertNotIn(value, result.stderr)


class PassAndRefuse(CheckTestCase):
    def test_passes_when_both_ids_are_served(self):
        with Router([CHAT, AUX, OTHER]) as router:
            result = self.run_check(diary_env(router))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('diary model check passed', result.stdout)
            self.assertEqual(router.requests, [('GET', '/v1/models')], 'one read-only GET of the model list, nothing else')
            self.assert_no_values(result, TOKEN, CHAT, AUX, router.url)

    def test_the_resolved_config_is_asked_for_with_the_env_file_the_cutover_deploys(self):
        with Router([CHAT, AUX]) as router:
            self.run_check(diary_env(router))
        calls = self.docker_log.read_text().splitlines()
        self.assertEqual(len(calls), 1, calls)
        self.assertTrue(calls[0].endswith(f'|compose --env-file {self.env_path} config --format json'), calls)

    def test_an_unserved_chat_id_refuses_naming_the_key_not_the_value(self):
        with Router([AUX, OTHER]) as router:
            result = self.run_check(diary_env(router))
            self.assert_refused(result, 'LLM_CHAT_MODEL', 'LLM_CHAT_FALLBACK_MODEL')
            self.assertNotIn('id set in LLM_AUX_MODEL is not served', result.stderr)
            self.assert_no_values(result, CHAT, AUX, router.url, '127.0.0.1', TOKEN)

    def test_an_unserved_aux_id_refuses(self):
        with Router([CHAT, OTHER]) as router:
            result = self.run_check(diary_env(router))
            self.assert_refused(result, 'LLM_AUX_MODEL', 'LLM_AUX_FALLBACK_MODEL')
            self.assertNotIn('id set in LLM_CHAT_MODEL is not served', result.stderr)
            self.assert_no_values(result, CHAT, AUX, TOKEN)

    def test_both_unserved_reports_both(self):
        with Router([OTHER]) as router:
            result = self.run_check(diary_env(router))
            self.assert_refused(result, 'LLM_CHAT_MODEL', 'LLM_AUX_MODEL')

    def test_an_unset_aux_id_follows_the_chat_id_like_the_diary(self):
        for aux in (None, '', 'default'):
            with self.subTest(aux=aux), Router([CHAT]) as router:
                result = self.run_check(diary_env(router, LLM_AUX_MODEL=aux))
                self.assertEqual(result.returncode, 0, result.stderr)
        with Router([OTHER]) as router:
            result = self.run_check(diary_env(router, LLM_AUX_MODEL='default'))
            self.assert_refused(result, 'LLM_CHAT_MODEL')

    def test_a_listed_embedding_or_reranking_section_is_not_a_chat_model(self):
        for flag in ('--embedding', '--embeddings', '--reranking', '--rerank'):
            with self.subTest(flag=flag), Router(body=listing(CHAT, AUX, flags={AUX: ['--model', 'x', flag]})) as router:
                result = self.run_check(diary_env(router))
                self.assert_refused(result, 'LLM_AUX_MODEL')

    def test_an_unloaded_chat_section_still_counts_as_served(self):
        # The check must not require (or cause) a load: a sleeping model is served.
        with Router(body=listing(CHAT, AUX, flags={CHAT: ['--ctx-size', '4096'], AUX: []})) as router:
            result = self.run_check(diary_env(router))
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_environment_may_be_a_list_of_assignments(self):
        with Router([CHAT, AUX]) as router:
            entries = [f'{k}={v}' for k, v in diary_env(router).items()]
            result = self.run_check(entries)
            self.assertEqual(result.returncode, 0, result.stderr)


class Fallbacks(CheckTestCase):
    def test_a_fallback_in_the_env_file_but_not_mapped_into_the_diary_service_refuses(self):
        # The deployed Compose files do not pass the key on, so the diary never sees it.
        self.env_path.write_text(f'LLM_CHAT_FALLBACK_MODEL={OTHER}\nLLM_AUX_FALLBACK_MODEL={OTHER}\n')
        with Router([OTHER, AUX]) as router:
            result = self.run_check(diary_env(router))
            self.assert_refused(result, 'LLM_CHAT_MODEL', 'LLM_CHAT_FALLBACK_MODEL is not set in the diary service', 'map LLM_CHAT_FALLBACK_MODEL')
            self.assert_no_values(result, CHAT, OTHER)
        with Router([CHAT, OTHER]) as router:
            result = self.run_check(diary_env(router))
            self.assert_refused(result, 'LLM_AUX_MODEL', 'LLM_AUX_FALLBACK_MODEL')

    def test_a_mapped_served_chat_fallback_passes_with_a_notice(self):
        with Router([OTHER, AUX]) as router:
            result = self.run_check(diary_env(router, LLM_CHAT_FALLBACK_MODEL=OTHER))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('NOTICE', result.stdout)
            self.assertIn('LLM_CHAT_FALLBACK_MODEL', result.stdout)
            self.assert_no_values(result, CHAT, OTHER)

    def test_a_mapped_served_aux_fallback_passes(self):
        with Router([CHAT, OTHER]) as router:
            result = self.run_check(diary_env(router, LLM_AUX_FALLBACK_MODEL=OTHER))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('LLM_AUX_FALLBACK_MODEL', result.stdout)

    def test_a_mapped_but_empty_fallback_is_no_fallback(self):
        with Router([AUX]) as router:
            result = self.run_check(diary_env(router, LLM_CHAT_FALLBACK_MODEL=''))
            self.assert_refused(result, 'LLM_CHAT_MODEL')

    def test_an_unserved_fallback_refuses(self):
        with Router([AUX]) as router:
            result = self.run_check(diary_env(router, LLM_CHAT_FALLBACK_MODEL=OTHER))
            self.assert_refused(result, 'LLM_CHAT_MODEL', 'LLM_CHAT_FALLBACK_MODEL', 'not served either')
            self.assert_no_values(result, OTHER, CHAT)

    def test_a_fallback_that_is_not_a_chat_model_does_not_rescue(self):
        with Router(body=listing(AUX, OTHER, flags={OTHER: ['--embedding']})) as router:
            result = self.run_check(diary_env(router, LLM_CHAT_FALLBACK_MODEL=OTHER))
            self.assert_refused(result, 'LLM_CHAT_FALLBACK_MODEL')

    def test_the_diarys_implicit_follow_the_chat_model_substitute_is_not_accepted(self):
        # The diary would follow the chat id for an unserved aux id, but nobody named that: refuse (stricter on purpose).
        with Router([CHAT]) as router:
            result = self.run_check(diary_env(router))
            self.assert_refused(result, 'LLM_AUX_MODEL')

    def test_each_role_uses_only_its_own_fallback(self):
        with Router([OTHER]) as router:
            result = self.run_check(diary_env(router, LLM_AUX_FALLBACK_MODEL=OTHER))
            self.assert_refused(result, 'LLM_CHAT_MODEL')
            self.assertNotIn('id set in LLM_AUX_MODEL is not served', result.stderr)


class FailClosed(CheckTestCase):
    def test_an_unreachable_router_refuses(self):
        with Router([CHAT, AUX]) as router:
            url = router.url
        # The stub is shut down: the port now refuses connections.
        result = self.run_check(diary_env(url=url))
        self.assert_refused(result, 'LLM_BASE_URL', 'could not be reached')
        self.assert_no_values(result, url, '127.0.0.1', CHAT, TOKEN)

    def test_a_non_200_answer_refuses(self):
        for status in (401, 403, 404, 500, 503):
            with self.subTest(status=status), Router(status=status, body=b'{}') as router:
                result = self.run_check(diary_env(router))
                self.assert_refused(result, f'HTTP {status}')

    def test_a_redirect_is_not_followed(self):
        with Router(status=302, headers={'Location': '/v1/models2'}, body=b'') as router:
            router.answers['/v1/models2'] = (200, {}, listing(CHAT, AUX))
            result = self.run_check(diary_env(router))
            self.assert_refused(result, 'HTTP 302')
            self.assertEqual(router.requests, [('GET', '/v1/models')])

    def test_a_body_that_is_not_a_model_list_refuses(self):
        for body in (b'not json', b'{}', b'{"data": {"id": "x"}}', b'[]', b'{"data": []}'):
            with self.subTest(body=body), Router(body=body) as router:
                result = self.run_check(diary_env(router))
                self.assert_refused(result)

    def test_a_resolved_diary_service_without_the_model_keys_fails_closed_without_contacting_the_router(self):
        with Router([CHAT, AUX]) as router:
            cases = {
                'both model keys absent': (diary_env(router, LLM_CHAT_MODEL=None, LLM_AUX_MODEL=None), 'LLM_CHAT_MODEL'),
                'chat key absent, aux set': (diary_env(router, LLM_CHAT_MODEL=None), 'LLM_CHAT_MODEL'),
                'chat key empty': (diary_env(router, LLM_CHAT_MODEL=''), 'LLM_CHAT_MODEL'),
                'chat key placeholder': (diary_env(router, LLM_CHAT_MODEL='default'), 'LLM_CHAT_MODEL'),
                'base url absent': (diary_env(router, LLM_BASE_URL=None), 'LLM_BASE_URL'),
                'base url empty': (diary_env(router, LLM_BASE_URL=''), 'LLM_BASE_URL'),
                'no keys at all': ({'DIARY_AUTH_TOKEN': TOKEN}, 'LLM_CHAT_MODEL'),
                'no environment at all': (None, 'LLM_CHAT_MODEL'),
            }
            for name, (env, needle) in cases.items():
                with self.subTest(case=name):
                    if env is None:
                        result = self.run_check(services={'diary': {'image': 'x'}})
                    else:
                        result = self.run_check(env)
                    self.assert_refused(result, needle)
            self.assertEqual(router.requests, [], 'nothing is contacted when a key is missing')

    def test_the_env_file_is_not_the_source_of_the_models(self):
        # The ids sit in the env file but the resolved diary service does not carry them.
        self.env_path.write_text(f'DIARY_CHAT_MODEL={CHAT}\nDIARY_AUX_MODEL={AUX}\nLLM_CHAT_MODEL={CHAT}\n')
        with Router([CHAT, AUX]) as router:
            result = self.run_check(diary_env(router, LLM_CHAT_MODEL=None, LLM_AUX_MODEL=None))
            self.assert_refused(result, 'LLM_CHAT_MODEL')
            self.assertEqual(router.requests, [])

    def test_no_diary_service_or_an_unusable_config_fails_closed(self):
        self.assert_refused(self.run_check(services={'web': {'environment': {}}}), 'no diary service')
        self.assert_refused(self.run_check(raw=b'not json'), 'usable configuration')
        self.assert_refused(self.run_check(raw=b'{}'), 'usable configuration')
        self.assert_refused(self.run_check(raw=b'[]'), 'usable configuration')

    def test_a_compose_config_that_does_not_resolve_fails_closed_and_leaks_nothing(self):
        result = self.run_check({}, compose_fail=1)
        self.assert_refused(result, 'docker compose config did not resolve')
        self.assert_no_values(result, KEY)

    def test_missing_docker_fails_closed(self):
        empty = self.temp / 'empty-path'
        empty.mkdir()
        result = self.run_check({}, path=str(empty))
        self.assert_refused(result, 'docker is required')

    def test_the_project_directory_is_where_compose_runs(self):
        project = self.temp / 'project'
        project.mkdir()
        with Router([CHAT, AUX]) as router:
            result = self.run_check(diary_env(router), extra_args=('--project-dir', str(project)))
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.docker_log.read_text().startswith(f'{project.resolve()}|compose '), self.docker_log.read_text())
        result = self.run_check({}, extra_args=('--project-dir', str(self.temp / 'absent')))
        self.assert_refused(result, 'project directory')

    def test_an_unreadable_env_file_and_bad_usage_fail(self):
        self.env_path.unlink()
        self.assert_refused(self.run_check({}), 'not readable')
        usage = subprocess.run(['bash', str(CHECK)], capture_output=True, text=True, timeout=30)
        self.assertEqual(usage.returncode, 2)
        self.assertIn('usage', usage.stderr)

    def test_a_non_http_router_address_refuses(self):
        for url in ('ftp://127.0.0.1/v1', 'host-without-scheme', 'http://user:pw@127.0.0.1:9/v1'):
            with self.subTest(url=url):
                result = self.run_check(diary_env(url=url))
                self.assert_refused(result, 'LLM_BASE_URL')
                self.assert_no_values(result, 'pw@')


class ComposeServiceRouter(CheckTestCase):
    """#2111: the diary reaches its router by a Compose service name that the host cannot resolve (curl exit 6). The
    same single GET is then made from inside the running diary container, where the name resolves."""

    def alias_url(self, router):
        return router.url.replace('127.0.0.1', ALIAS)

    def exec_calls(self):
        return [l for l in self.docker_log.read_text().splitlines() if '|exec ' in l]

    def test_a_compose_service_name_is_read_through_the_diary_container(self):
        with Router([CHAT, AUX, OTHER]) as router:
            env = diary_env(url=self.alias_url(router), LLM_API_KEY=KEY)
            result = self.run_check(env, diary_cid=CID)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('diary model check passed', result.stdout)
            self.assertIn('inside the diary container', result.stdout)
            self.assertEqual(router.requests, [('GET', '/v1/models')], 'one read-only GET of the model list, nothing else')
            self.assertEqual(router.auth, [f'Bearer {KEY}'])
            self.assert_no_values(result, KEY, TOKEN, CHAT, AUX, ALIAS)
        calls = self.exec_calls()
        self.assertEqual(len(calls), 1, calls)
        self.assertIn(f'|exec -i {CID} python -c ', calls[0])
        for secret in (KEY, TOKEN, ALIAS, CHAT, '/v1/models'):
            self.assertNotIn(secret, '\n'.join(self.docker_log.read_text().splitlines()[1:]), 'the credential and the address stay off argv')

    def test_the_compose_service_name_is_found_in_the_project_that_owns_the_diary(self):
        project = self.temp / 'project'
        project.mkdir()
        with Router([CHAT, AUX]) as router:
            result = self.run_check(diary_env(url=self.alias_url(router)), diary_cid=CID, extra_args=('--project-dir', str(project)))
            self.assertEqual(result.returncode, 0, result.stderr)
        ps = [l for l in self.docker_log.read_text().splitlines() if ' ps -q diary' in l]
        self.assertEqual(len(ps), 1, ps)
        self.assertTrue(ps[0].startswith(f'{project.resolve()}|compose --env-file {self.env_path} ps -q diary'), ps)

    def test_the_names_still_have_to_be_served(self):
        with Router([AUX, OTHER]) as router:
            result = self.run_check(diary_env(url=self.alias_url(router)), diary_cid=CID)
            self.assert_refused(result, 'LLM_CHAT_MODEL', 'LLM_CHAT_FALLBACK_MODEL')
            self.assert_no_values(result, CHAT, AUX, ALIAS)
        with Router([CHAT, AUX]) as router:
            env = diary_env(url=self.alias_url(router), LLM_CHAT_MODEL=OTHER, LLM_CHAT_FALLBACK_MODEL=AUX)
            result = self.run_check(env, diary_cid=CID)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('NOTICE: diary chat model', result.stdout)

    def test_no_running_diary_container_refuses_without_starting_anything(self):
        with Router([CHAT, AUX]) as router:
            result = self.run_check(diary_env(url=self.alias_url(router)))
            self.assert_refused(result, 'LLM_BASE_URL', 'no diary container is running')
            self.assert_no_values(result, ALIAS, CHAT)
            self.assertEqual(router.requests, [])
        self.assertEqual(self.exec_calls(), [])
        self.assertFalse([l for l in self.docker_log.read_text().splitlines() if '|run ' in l or '|start ' in l or ' up ' in l])

    def test_a_failed_exec_refuses(self):
        with Router([CHAT, AUX]) as router:
            result = self.run_check(diary_env(url=self.alias_url(router)), diary_cid=CID, exec_fail=1)
            self.assert_refused(result, 'LLM_BASE_URL', 'inside the diary container either')
            self.assert_no_values(result, ALIAS, CHAT)
            self.assertEqual(router.requests, [])

    def test_a_router_the_diary_cannot_reach_either_refuses(self):
        with Router([CHAT, AUX]) as router:
            url = self.alias_url(router)
        result = self.run_check(diary_env(url=url), diary_cid=CID)  # the stub router is shut down: connection refused
        self.assert_refused(result, 'LLM_BASE_URL', 'inside the diary container either')
        self.assert_no_values(result, ALIAS, CHAT, url)

    def test_answers_other_than_a_model_list_refuse_through_the_container_too(self):
        for status in (401, 404, 500):
            with self.subTest(status=status), Router(status=status, body=b'{}') as router:
                result = self.run_check(diary_env(url=self.alias_url(router)), diary_cid=CID)
                self.assert_refused(result, f'HTTP {status}')
        with Router(status=302, headers={'Location': '/v1/models2'}, body=b'') as router:
            router.answers['/v1/models2'] = (200, {}, listing(CHAT, AUX))
            result = self.run_check(diary_env(url=self.alias_url(router)), diary_cid=CID)
            self.assert_refused(result, 'HTTP 302')
            self.assertEqual(router.requests, [('GET', '/v1/models')], 'redirects are not followed')
        for body in (b'not json', b'{"data": {"id": "x"}}', b'{"data": []}'):
            with self.subTest(body=body), Router(body=body) as router:
                self.assert_refused(self.run_check(diary_env(url=self.alias_url(router)), diary_cid=CID))

    def test_only_an_unresolvable_name_goes_through_the_container(self):
        # A host-reachable address never touches the container, and other curl failures are not retried there.
        with Router([CHAT, AUX]) as router:
            self.assertEqual(self.run_check(diary_env(router), diary_cid=CID).returncode, 0)
        with Router([CHAT, AUX]) as router:
            url = router.url
        self.assert_refused(self.run_check(diary_env(url=url), diary_cid=CID), 'curl exit 7')
        self.assertEqual(self.exec_calls(), [])

    def test_a_separate_aux_router_by_service_name_uses_its_own_credential(self):
        aux_key = KEY + '-aux'
        with Router([CHAT]) as chat_router, Router([AUX]) as aux_router:
            env = diary_env(chat_router, LLM_API_KEY=KEY, LLM_AUX_BASE_URL=self.alias_url(aux_router), LLM_AUX_API_KEY=aux_key)
            result = self.run_check(env, diary_cid=CID)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(chat_router.auth, [f'Bearer {KEY}'])
            self.assertEqual(aux_router.auth, [f'Bearer {aux_key}'])
        self.assertEqual(len(self.exec_calls()), 1, 'only the address the host cannot resolve goes through the container')


class Secrets(CheckTestCase):
    def test_the_credential_is_sent_as_a_bearer_header_and_never_printed(self):
        with Router([OTHER]) as router:
            env = diary_env(router, LLM_API_KEY=KEY)
            for flags in ((), ('-x',)):
                with self.subTest(flags=flags):
                    result = self.run_check(env, bash_flags=flags)
                    self.assert_refused(result, 'LLM_CHAT_MODEL')
                    self.assert_no_values(result, KEY, TOKEN, CHAT, AUX, OTHER, router.url, '127.0.0.1')
            self.assertEqual(router.auth, [f'Bearer {KEY}'] * 2)

    def test_a_separate_aux_router_is_checked_with_its_own_credential(self):
        aux_key = KEY + '-aux'
        with Router([CHAT]) as chat_router, Router([AUX]) as aux_router:
            env = diary_env(chat_router, LLM_API_KEY=KEY, LLM_AUX_BASE_URL=aux_router.url, LLM_AUX_API_KEY=aux_key)
            result = self.run_check(env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(chat_router.auth, [f'Bearer {KEY}'])
            self.assertEqual(aux_router.auth, [f'Bearer {aux_key}'])
        with Router([CHAT]) as chat_router, Router([OTHER]) as aux_router:
            result = self.run_check(diary_env(chat_router, LLM_AUX_BASE_URL=aux_router.url))
            self.assert_refused(result, 'LLM_AUX_MODEL')

    def test_the_script_only_ever_reads_the_model_list(self):
        code = '\n'.join(l for l in CHECK.read_text().splitlines() if not l.lstrip().startswith('#'))
        for forbidden in ('/slots', '/completion', '/chat/', '/props', '/load'):
            self.assertNotIn(forbidden, code, forbidden)
        calls = [l for l in code.splitlines() if re.search(r'\| curl |\bcurl "\$\{curl_args', l)]
        self.assertEqual(len(calls), 2, calls)  # with and without a credential: the same single GET
        for line in calls:
            self.assertIn('"$base/models"', line)
            self.assertIsNone(re.search(r'\s-(X|d|L|F|T)\b|--(data|request|upload|location|form)', line), line)
        docker_calls = [l for l in code.splitlines() if re.match(r'\s*docker ', l)]
        self.assertEqual(len(docker_calls), 1, docker_calls)
        self.assertIn('config --format json', docker_calls[0])
        # The in-network read (#2111) is the same single GET: one exec, no other verbs, no redirects.
        self.assertEqual(len(re.findall(r'docker exec', code)), 1)
        self.assertEqual(len(re.findall(r'docker compose --env-file "\$env_file" ps -q diary', code)), 1)
        self.assertIn('method="GET"', code)
        self.assertNotRegex(code, r'method="(POST|PUT|DELETE|PATCH)"')
        self.assertIn('return None', code)  # the redirect handler refuses to follow
        self.assertNotRegex(code, r'docker (run|start|restart|stop|kill|rm|cp|build|compose (up|start|down|run))\b')

    def test_the_script_does_not_read_the_env_file(self):
        code = '\n'.join(l for l in CHECK.read_text().splitlines() if not l.lstrip().startswith('#'))
        self.assertNotRegex(code, r'<\s*"\$env_file"')
        self.assertNotIn('source ', code)


class CutoverHooks(unittest.TestCase):
    """Both overlay scripts run the check against their own .env and Compose project before they change anything."""

    def hook(self, script):
        text = script.read_text()
        self.assertEqual(text.count('# BEGIN diary-models-check'), 1)
        block = text[text.index('# BEGIN diary-models-check'):text.index('# END diary-models-check')]
        self.assertIn('diary-models-check.sh" --env-file "$config"', block)
        self.assertIn('exit 1', block)
        return text, block

    def test_overlay_release_checks_before_any_change_in_its_compose_project(self):
        text, block = self.hook(OVERLAY)
        self.assertIn('--project-dir "$manager"', block)
        start = text.index('# BEGIN diary-models-check')
        for change in ['old_native=$(container_id', 'mkdir -p "$base/releases/$NEW"', 'docker build', 'ln -sfn', 'sed -i', 'cp -p "$config"', 'up.sh']:
            self.assertLess(start, text.index(change, text.index('# END preflight-installed')), change)

    def test_diary_overlay_checks_before_any_change_from_inside_its_compose_project(self):
        text, block = self.hook(DIARY)
        start = text.index('# BEGIN diary-models-check')
        # The script has changed into the Compose project directory by then, so the check resolves the same files.
        self.assertGreater(start, text.index('cd /boot/config/plugins/compose.manager/projects/Cowork'))
        for change in ['docker image inspect', 'docker tag', 'docker build', 'docker stop', 'cp -p "$config"', 'sed -i', 'up.sh" --env-file']:
            self.assertLess(start, text.index(change, text.index('# END preflight-installed')), change)

    def test_the_installer_ships_the_check(self):
        text = (ROOT / 'deploy/preflight/install.sh').read_text()
        self.assertIn('required=(up.sh diary-image-guard.sh check.php diary-models-check.sh)', text)

    def test_compose_passes_the_explicit_fallback_keys_to_the_diary(self):
        # The shipped Compose files map the keys; an operator's own project files must do the same, which the
        # check verifies on the resolved configuration.
        for path in ('compose.yaml', 'deploy/examples/unraid-compose-manager.yml'):
            text = (ROOT / path).read_text()
            with self.subTest(path=path):
                self.assertIn('LLM_CHAT_FALLBACK_MODEL: ${LLM_CHAT_FALLBACK_MODEL:-}', text)
                self.assertIn('LLM_AUX_FALLBACK_MODEL: ${LLM_AUX_FALLBACK_MODEL:-}', text)


if __name__ == '__main__':
    unittest.main()
