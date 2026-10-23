"""noevia#2115, #2117: every chat client reaches the router through the inference gate.

The gate admits one chat model at a time, so one chat can no longer unload the model another chat is
using. These checks read the Compose files the repo ships (key names and default expressions only; no
.env value is ever read). With Docker present they also render the files with obviously fake values;
nothing is started, built or pulled.
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
ONE_HOST = ['compose.llamacpp.yaml', 'deploy/examples/unraid-llamacpp.override.yml']
SPLIT = 'deploy/examples/inference-gate.override.yml'
STUB_MACHINE = 'deploy/tests/fixtures/inference-machine.stub.yml'
GATE_URL = 'http://inference-gate:8080'
# The gate's environment (bins/noevia-inference-gate/src/env.rs in the pinned noevia-rs), less
# GATE_LISTEN, whose default (0.0.0.0:8080) every copy keeps.
GATE_LIMITS = [
    'GATE_CHAT_SLOTS', 'GATE_EXEMPT_MODELS', 'GATE_MAX_WAIT_SECONDS', 'GATE_FAIR_HOLD_SECONDS',
    'GATE_RESIDENCY_GRACE_SECONDS', 'GATE_LEASE_IDLE_SECONDS', 'GATE_LEASE_HARD_SECONDS',
    'GATE_UNLOAD_TIMEOUT_SECONDS', 'GATE_ROUTER_DOWN_GRACE_SECONDS', 'GATE_SESSION_HOLD_SECONDS',
    'GATE_MAX_WAITERS', 'GATE_MAX_LEASES', 'GATE_MAX_BODY_BYTES', 'GATE_MAX_BUFFERED_BYTES',
    'GATE_BODY_TIMEOUT_SECONDS', 'GATE_UPSTREAM_HEADER_TIMEOUT_SECONDS', 'GATE_HEADER_READ_TIMEOUT_SECONDS',
    'GATE_MAX_CONNECTIONS',
]
STUBS = {
    'LLAMACPP_RENDER_DEVICE': '/dev/dri/renderD128', 'LLAMACPP_CARD_DEVICE': '/dev/dri/card0',
    'LLAMACPP_MODELS_DIR': '/stub/models', 'LLAMACPP_CONFIG_DIR': '/stub/config', 'LLAMACPP_CACHE_DIR': '/stub/cache',
    'LLAMACPP_CHAT_MODEL': 'stub-chat', 'LLAMACPP_AUX_MODEL': 'stub-aux', 'LLAMACPP_EMBED_MODEL': 'stub-embed',
    'MODEL_LOADER_TOKEN': 'stub-not-a-secret', 'MODEL_LOADER_DATA_DIR': '/stub/loader',
    'EMBED_MODEL_FILE': 'stub-embed.gguf', 'RERANK_MODEL_DIR': '/stub/rerank',
}


def read(name):
    return (ROOT / name).read_text(encoding='utf-8')


def service_block(text, service):
    """The lines of one two-space-indented service, up to the next service or top-level key."""
    lines = text.split('\n')
    start = lines.index(f'  {service}:')
    body = []
    for line in lines[start + 1:]:
        if re.match(r'^ {0,2}\S', line):
            break
        body.append(line)
    return '\n'.join(body)


def environment(block):
    """KEY: value pairs of a block's `environment:` map (six-space keys)."""
    env, inside = {}, False
    for line in block.split('\n'):
        if re.match(r'^ {4}environment:\s*$', line):
            inside = True
            continue
        if inside and re.match(r'^ {4}\S', line):
            break
        m = re.match(r'^ {6}([A-Z_][A-Z0-9_]*): (.*)$', line)
        if inside and m:
            env[m.group(1)] = m.group(2)
    return env


def gate_problems(text):
    """What is wrong with one copy's inference-gate service, as messages."""
    found = []
    block = service_block(text, 'inference-gate')
    env = environment(block)
    if 'command: ["noevia-inference-gate"]' not in block:
        found.append('the gate does not run noevia-inference-gate')
    if not re.search(r'(?m)^    image: cowork-model-loader:\$\{MODEL_MANAGER_VERSION:\?', block):
        found.append('the gate is not the model manager image at MODEL_MANAGER_VERSION')
    if env.get('GATE_UPSTREAM') != 'http://llama:8080':
        found.append(f"GATE_UPSTREAM is {env.get('GATE_UPSTREAM')!r}")
    if env.get('GATE_ADMIN_TOKEN') != '${INFERENCE_GATE_ADMIN_TOKEN:-}':
        found.append('GATE_ADMIN_TOKEN is not the shared INFERENCE_GATE_ADMIN_TOKEN, blank by default')
    for key in GATE_LIMITS:
        if env.get(key) != '${%s:-}' % key:
            found.append(f'{key} is not passed through with a blank default: {env.get(key)!r}')
    extra = sorted(set(env) - set(GATE_LIMITS) - {'GATE_UPSTREAM', 'GATE_ADMIN_TOKEN'})
    if extra:
        found.append(f'unexpected gate settings: {extra}')
    for needle, why in [('docker.sock', 'holds the Docker socket'), ('volumes:', 'mounts a volume'),
                        ('devices:', 'has a device'), ('privileged', 'is privileged')]:
        if needle in block:
            found.append(f'the gate {why}')
    for needle in ['read_only: true', 'user: "65534:65534"', 'cap_drop: [ALL]', '"no-new-privileges:true"',
                   'mem_limit: 512m', '/gate/v1/health']:
        if needle not in block:
            found.append(f'the gate lacks {needle}')
    return found


class GateServiceTests(unittest.TestCase):
    def test_each_copy_runs_the_gate_hardened_with_every_setting_passed_through(self):
        for name in ONE_HOST + [SPLIT]:
            with self.subTest(copy=name):
                self.assertEqual(gate_problems(read(name)), [])

    def test_a_missing_or_hard_coded_setting_is_reported(self):
        text = read(ONE_HOST[0])
        self.assertIn('GATE_MAX_WAIT_SECONDS is not passed through with a blank default: None',
                      gate_problems(text.replace('      GATE_MAX_WAIT_SECONDS: ${GATE_MAX_WAIT_SECONDS:-}\n', '')))
        self.assertIn("GATE_UPSTREAM is 'http://llama:9999'",
                      gate_problems(text.replace('GATE_UPSTREAM: http://llama:8080', 'GATE_UPSTREAM: http://llama:9999')))
        self.assertIn('the gate holds the Docker socket', gate_problems(text.replace(
            '    command: ["noevia-inference-gate"]\n',
            '    command: ["noevia-inference-gate"]\n    volumes:\n      - /var/run/docker.sock:/var/run/docker.sock\n', 1)))

    def test_on_one_host_the_router_is_behind_the_gate(self):
        for name in ONE_HOST:
            with self.subTest(copy=name):
                text = read(name)
                llama = service_block(text, 'llama')
                self.assertRegex(llama, r'(?m)^    networks: \[models\]$', 'the router is on models only')
                self.assertNotRegex(llama, r'(?m)^    ports:', 'the router publishes no port')
                self.assertRegex(service_block(text, 'inference-gate'), r'(?m)^    networks: \[default, models\]$')
                self.assertNotRegex(service_block(text, 'inference-gate'), r'(?m)^    ports:')
                # The model manager never shares a network with Diary (deploy/preflight D1).
                self.assertRegex(service_block(text, 'model-loader'), r'(?m)^    networks: \[models\]$')

    def test_web_and_diary_reach_the_router_only_through_the_gate(self):
        text = read('compose.llamacpp.yaml')
        web, diary = environment(service_block(text, 'web')), environment(service_block(text, 'diary'))
        self.assertEqual(web['INFERENCE_BASE_URL'], GATE_URL + '/v1')
        self.assertEqual(web['MODEL_MANAGER_BASE_URL'], GATE_URL)
        self.assertEqual(diary['LLM_BASE_URL'], GATE_URL + '/v1')
        self.assertEqual(diary['LLM_AUX_BASE_URL'], GATE_URL + '/v1')
        # The gate's upstream is the only address of the router left.
        self.assertEqual(re.findall(r'http://llama:8080\S*', text), ['http://llama:8080'])

    def test_web_receives_the_gate_admin_token_and_diary_does_not(self):
        for name in ['compose.yaml', 'deploy/examples/unraid-compose-manager.yml']:
            with self.subTest(copy=name):
                text = read(name)
                self.assertEqual(environment(service_block(text, 'web')).get('INFERENCE_GATE_ADMIN_TOKEN'),
                                 '${INFERENCE_GATE_ADMIN_TOKEN:-}')
                self.assertNotIn('INFERENCE_GATE_ADMIN_TOKEN', service_block(text, 'diary'))

    def test_the_split_override_moves_the_router_port_to_the_gate(self):
        text = read(SPLIT)
        self.assertEqual(service_block(text, 'llama').strip(), 'ports: !reset []')
        gate = service_block(text, 'inference-gate')
        self.assertIn('- "${INFERENCE_GATE_PUBLISH:?', gate)
        self.assertRegex(gate, r'(?m)^    networks: \[models\]$')
        self.assertIn('pull_policy: never', gate, 'the image is the one built for the release, never pulled')

    def test_env_example_documents_every_key_commented_out(self):
        text = read('.env.example')
        for key in GATE_LIMITS + ['INFERENCE_GATE_ADMIN_TOKEN', 'INFERENCE_GATE_PUBLISH']:
            with self.subTest(key=key):
                self.assertRegex(text, rf'(?m)^# {key}=')
                self.assertNotRegex(text, rf'(?m)^{key}=')
        self.assertIn('# INFERENCE_BASE_URL=http://inference-gate:8080/v1\n', text)

    def test_docs_give_rollback_the_firewall_release_step_and_known_limitations(self):
        text = read('docs/deployment.md')
        section = text[text.index('## Inference gate (#2115)'):]
        section = section[:section.index('\n## ', 1)]
        flat = ' '.join(section.split())
        for phrase in ['**Rollback.**', 'Host firewall (#2122)', 'INFERENCE_GATE_ADMIN_TOKEN',
                       'deploy/examples/inference-gate.override.yml',
                       # #2122: the firewall change is a release step, with a refused/allowed check.
                       "Release step: add the gate's port to the host's model-port firewall script.",
                       "add port 18000 to the host's model-port firewall script",
                       'from a LAN host that should be refused',
                       'from the allowed peer (the web host), the same request answers 200',
                       # #2133 item 6: the router's own reload after a download is invisible to the gate.
                       'the router can reload its presets on its own at the next request. The gate does not see this reload',
                       'Expect that request to wait on the reload',
                       # The model manager's direct paths are a stated limitation (#2138).
                       'backend restart', 'backend test', 'benchmark runner', 'sbstndalton/noevia#2138',
                       # Without the admin token the watchdog cannot unload a busy model.
                       'Set `INFERENCE_GATE_ADMIN_TOKEN` on both hosts',
                       'must name the same gate', "The web host's addresses stay unchanged",
                       '`AUX_INFERENCE_BASE_URL`', '`pull_policy: never`']:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, flat)
        for gone in ['do not change it as part of this release', 'reaches it there for presets']:
            self.assertNotIn(gone, flat)
        self.assertNotRegex(section, r'(?:^|\s)/(?:mnt|boot|etc|usr|home)/', 'no absolute server paths')
        self.assertNotRegex(section, r'\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d+\.\d+\.\d+\b', 'no installation address')


def compose(*files, env=None):
    cmd = ['docker', 'compose', '--env-file', '.env.example']
    for f in files:
        cmd += ['-f', f]
    run_env = dict(os.environ, **STUBS, **(env or {}))
    for key in GATE_LIMITS + ['INFERENCE_GATE_ADMIN_TOKEN', 'INFERENCE_GATE_PUBLISH']:
        run_env.pop(key, None)
    run_env.update(env or {})
    return subprocess.run(cmd + ['config', '--format', 'json'], cwd=ROOT, env=run_env,
                          capture_output=True, text=True, timeout=60)


@unittest.skipUnless(shutil.which('docker') and subprocess.run(['docker', 'compose', 'version'], capture_output=True).returncode == 0,
                     'docker compose not installed')
class RenderedComposeTests(unittest.TestCase):
    def test_the_documented_stack_renders_the_gate_in_front_of_the_router(self):
        result = compose('compose.yaml', 'compose.llamacpp.yaml', 'compose.embed.yaml', 'compose.rerank.yaml', 'compose.docling.yaml')
        self.assertEqual(result.returncode, 0, result.stderr)
        services = json.loads(result.stdout)['services']
        gate, llama = services['inference-gate'], services['llama']
        self.assertEqual(gate['command'], ['noevia-inference-gate'])
        self.assertEqual(sorted(gate['networks']), ['default', 'models'])
        self.assertEqual(sorted(llama['networks']), ['models'])
        self.assertIsNone(llama.get('ports'))
        self.assertIsNone(gate.get('ports'))
        self.assertEqual(gate['image'], services['model-loader']['image'])
        self.assertEqual(gate['environment']['GATE_ADMIN_TOKEN'], '')
        self.assertEqual(services['web']['environment']['INFERENCE_BASE_URL'], GATE_URL + '/v1')
        self.assertEqual(services['diary']['environment']['LLM_AUX_BASE_URL'], GATE_URL + '/v1')
        self.assertNotIn('models', services['diary'].get('networks', {}), 'Diary still never joins models')

    def test_the_admin_token_reaches_the_gate_and_web_as_one_secret(self):
        result = compose('compose.yaml', 'compose.llamacpp.yaml', env={'INFERENCE_GATE_ADMIN_TOKEN': 'synthetic-admin-token-0001'})
        self.assertEqual(result.returncode, 0, result.stderr)
        services = json.loads(result.stdout)['services']
        self.assertEqual(services['inference-gate']['environment']['GATE_ADMIN_TOKEN'], 'synthetic-admin-token-0001')
        self.assertEqual(services['web']['environment']['INFERENCE_GATE_ADMIN_TOKEN'], 'synthetic-admin-token-0001')
        self.assertNotIn('INFERENCE_GATE_ADMIN_TOKEN', services['diary']['environment'])

    def test_on_an_inference_machine_the_gate_takes_over_the_router_port(self):
        result = compose(STUB_MACHINE, SPLIT, env={'INFERENCE_GATE_PUBLISH': '192.0.2.10:18000', 'MODEL_MANAGER_VERSION': 'stub'})
        self.assertEqual(result.returncode, 0, result.stderr)
        services = json.loads(result.stdout)['services']
        self.assertEqual(services['llama'].get('ports', []), [])
        [port] = services['inference-gate']['ports']
        self.assertEqual((port['host_ip'], port['published'], port['target']), ('192.0.2.10', '18000', 8080))
        self.assertEqual(sorted(services['inference-gate']['networks']), ['models'])
        self.assertEqual(services['inference-gate']['pull_policy'], 'never')

    def test_on_an_inference_machine_the_publish_address_is_required(self):
        result = compose(STUB_MACHINE, SPLIT, env={'MODEL_MANAGER_VERSION': 'stub'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('INFERENCE_GATE_PUBLISH', result.stderr)


if __name__ == '__main__':
    unittest.main()


OVERLAY = ROOT / 'deploy/examples/overlay-release.sh'


def overlay_block(name):
    text = OVERLAY.read_text()
    start = text.index(f'# BEGIN {name}')
    return text[start:text.index(f'# END {name}', start)]


class OverlayReleaseGateStep(unittest.TestCase):
    """The one-host release starts inference-gate before the Diary model check; the split layout is unchanged."""

    def run_block(self, services, up_status=0):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            log = tmp / 'docker.log'
            fake = tmp / 'bin' / 'docker'
            fake.parent.mkdir()
            fake.write_text('#!/bin/bash\necho "$*" >> "$DOCKER_LOG"\n'
                            'case "$*" in *"config --services"*) printf "%s\\n" $FAKE_SERVICES ;;'
                            ' *" up "*) exit "$UP_STATUS" ;; esac\n')
            fake.chmod(0o755)
            (tmp / 'manager').mkdir()
            script = 'set -euo pipefail\nmanager="$1"; config="$2"\n' + overlay_block('inference-gate') + 'echo BLOCK_DONE\n'
            env = dict(os.environ, PATH=f"{fake.parent}:{os.environ['PATH']}", DOCKER_LOG=str(log),
                       FAKE_SERVICES=' '.join(services), UP_STATUS=str(up_status))
            result = subprocess.run(['bash', '-c', script, 'x', str(tmp / 'manager'), str(tmp / '.env')],
                                    env=env, capture_output=True, text=True, timeout=30)
            calls = log.read_text().splitlines() if log.exists() else []
            return result, calls

    def test_one_host_release_starts_the_gate_by_name(self):
        result, calls = self.run_block(['web', 'diary', 'ocr', 'llama', 'model-loader', 'inference-gate'])
        self.assertEqual(result.returncode, 0, result.stderr)
        ups = [c for c in calls if ' up ' in f' {c} ']
        self.assertEqual(len(ups), 1, calls)
        self.assertIn('--no-deps', ups[0])
        self.assertIn('--no-build', ups[0])
        self.assertEqual(ups[0].split()[-1], 'inference-gate')
        for other in ['llama', 'model-loader', 'web', 'diary', 'ocr']:
            self.assertNotIn(other, ups[0].split())

    def test_one_host_release_stops_when_the_gate_does_not_come_up(self):
        result, _ = self.run_block(['web', 'diary', 'inference-gate'], up_status=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('BLOCK_DONE', result.stdout)
        self.assertIn('not deploying', result.stderr)

    def test_split_layout_release_starts_nothing_new(self):
        result, calls = self.run_block(['web', 'diary', 'ocr', 'docling'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('BLOCK_DONE', result.stdout)
        self.assertFalse([c for c in calls if ' up ' in f' {c} '], calls)

    def test_gate_step_runs_before_the_diary_model_check_and_the_cutover(self):
        text = OVERLAY.read_text()
        gate = text.index('# BEGIN inference-gate')
        self.assertLess(gate, text.index('# BEGIN diary-models-check'))
        self.assertLess(gate, text.index('--wait-timeout 180 web diary ocr'))
        # The cutover's own service set is unchanged in both layouts.
        self.assertEqual(text.count('--no-deps --wait --wait-timeout 180 web diary ocr\n'), 1)
        self.assertEqual(text.count('--no-deps --wait --wait-timeout 180 web diary ocr'), 2)
        self.assertIn("grep -xE 'docling|code-sandbox'", text)
        self.assertIn('for c in web diary ocr inference-gate llama model-loader; do', text)
