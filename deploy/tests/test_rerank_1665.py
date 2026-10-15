"""#1665: the gte-multilingual TEI reranker sidecar and the web keys that select it.

compose.rerank.yaml runs gte-multilingual-reranker-base int8 on TEI cpu-1.9, launched as eval run 2
measured it (2 CPUs, 2 GiB, 2048 batch tokens, auto-truncate), on an internal network only web
joins, with no published ports. The reranker keys reach web in each base compose copy with empty
defaults (reranking stays off), the preflight list names them, and .env.example leaves them empty.
Only key names, defaults and compose text are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
OVERLAY = ROOT / 'compose.rerank.yaml'
COMPOSE_COPIES = ['compose.yaml', 'deploy/examples/unraid-compose-manager.yml']
PREFLIGHT_KEYS = ROOT / 'deploy/preflight/web-env-keys.txt'
TEI = ('ghcr.io/huggingface/text-embeddings-inference:cpu-1.9'
       '@sha256:2538ea1c9640d3763b15af668039d24172d063b42337b0c27796fc2be180c78d')
KEYS = [
    'NOEVIA_FEATURE_RAG_RERANK',
    'RERANK_BACKEND',
    'RERANK_BASE_URL',
    'RERANK_MODEL',
    'RERANK_API_KEY',
    'RAG_RERANK_POOL',
    'RAG_RERANK_KEEP',
    'RAG_RERANK_DEADLINE_MS',
]


def service_block(text, name):
    match = re.search(rf'^  {re.escape(name)}:\n(.*?)(?=^  [a-z][a-z0-9-]*:\n|^\S|\Z)', text, re.M | re.S)
    if not match:
        raise AssertionError(f'service {name} not found')
    return match.group(1)


def section(block, key):
    """The lines under a four-space key of a service block (stops at the next four-space key)."""
    match = re.search(rf'^    {key}:[^\n]*\n((?:(?: {{6}}|\s*$)[^\n]*\n)*)', block + '\n', re.M)
    return match.group(1) if match else ''


def environment(block):
    return {m.group(1): m.group(2).strip() for m in re.finditer(r'^ {6}([A-Z0-9_]+): (.*)$', section(block, 'environment'), re.M)}


def code_lines(text):
    return '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('#'))


class RerankSidecarTests(unittest.TestCase):
    def setUp(self):
        self.text = code_lines(OVERLAY.read_text(encoding='utf-8'))
        self.rerank = service_block(self.text, 'rerank')

    def test_image_is_tei_cpu_1_9_pinned_by_digest(self):
        self.assertEqual(re.search(r'^    image: (\S+)$', self.rerank, re.M).group(1), TEI)

    def test_command_matches_the_eval_launch(self):
        args = re.findall(r'^ {6}- "([^"]*)"$', section(self.rerank, 'command'), re.M)
        self.assertEqual(args, ['--model-id', '/model', '--hostname', '0.0.0.0', '--port', '8080', '--auto-truncate',
                                '--max-batch-tokens', '2048', '--max-client-batch-size', '64'])
        self.assertEqual(environment(self.rerank).get('HF_HUB_OFFLINE'), '"1"')

    def test_the_int8_model_is_mounted_read_only(self):
        mounts = re.findall(r'^ {6}- (.+)$', section(self.rerank, 'volumes'), re.M)
        self.assertTrue(mounts)
        for mount in mounts:
            self.assertTrue(mount.endswith(':ro'), mount)
        self.assertIn('/onnx/model_int8.onnx:/model/onnx/model.onnx:ro', mounts[0])
        self.assertTrue(mounts[0].startswith('${RERANK_MODEL_DIR:?'), 'a missing model folder must fail, not mount an empty dir')

    def test_two_cpus_and_a_2_gib_cap(self):
        self.assertRegex(self.rerank, r'(?m)^    cpus: \$\{RERANK_CPUS:-2\}$')
        self.assertRegex(self.rerank, r'(?m)^    mem_limit: \$\{RERANK_MEMORY_LIMIT:-2g\}$')
        self.assertRegex(self.rerank, r'(?m)^    memswap_limit: \$\{RERANK_MEMORY_LIMIT:-2g\}$')

    def test_healthcheck_probes_tei_health(self):
        self.assertIn('http://127.0.0.1:8080/health', section(self.rerank, 'healthcheck'))

    def test_internal_network_only_no_ports_no_gpu(self):
        for key in ('ports', 'devices', 'network_mode', 'privileged'):
            self.assertNotRegex(self.rerank, rf'(?m)^    {key}:', key)
        self.assertRegex(self.rerank, r'(?m)^    networks: \[rerank\]$')
        networks = self.text[self.text.index('\nnetworks:'):]
        self.assertRegex(networks, r'(?m)^  rerank:\n    internal: true$')

    def test_web_joins_the_network_and_defaults_to_the_sidecar_with_the_flag_off(self):
        web = service_block(self.text, 'web')
        self.assertRegex(web, r'(?m)^    networks: \[rerank\]$')
        env = environment(web)
        self.assertEqual(env['RERANK_BACKEND'], '${RERANK_BACKEND:-tei}')
        self.assertEqual(env['RERANK_BASE_URL'], '${RERANK_BASE_URL:-http://rerank:8080}')
        self.assertEqual(env['NOEVIA_FEATURE_RAG_RERANK'], '${NOEVIA_FEATURE_RAG_RERANK:-}', 'the overlay never turns reranking on')
        self.assertEqual(env['RERANK_API_KEY'], '${RERANK_API_KEY:-}')
        self.assertNotIn('INFERENCE_API_KEY', ''.join(env.values()))


class RerankKeyPassthroughTests(unittest.TestCase):
    def test_each_compose_copy_passes_every_key_with_an_empty_default(self):
        for name in COMPOSE_COPIES:
            env_lines = section(service_block((ROOT / name).read_text(encoding='utf-8'), 'web'), 'environment')
            for key in KEYS:
                with self.subTest(copy=name, key=key):
                    self.assertEqual(re.findall(rf'(?m)^ {{6}}{key}: (.*)$', env_lines), [f'${{{key}:-}}'])

    def test_the_preflight_list_names_every_key(self):
        listed = set(PREFLIGHT_KEYS.read_text(encoding='utf-8').split())
        self.assertEqual([k for k in KEYS if k not in listed], [])

    def test_env_example_leaves_every_key_empty(self):
        text = (ROOT / '.env.example').read_text(encoding='utf-8')
        for key in KEYS:
            with self.subTest(key=key):
                self.assertEqual(re.findall(rf'^{key}=(.*)$', text, re.M), [''])

    def test_no_compose_file_turns_reranking_on(self):
        for path in sorted(ROOT.glob('compose*.yaml')) + [ROOT / c for c in COMPOSE_COPIES[1:]]:
            with self.subTest(path=path.name):
                self.assertNotRegex(code_lines(path.read_text(encoding='utf-8')),
                                    r'NOEVIA_FEATURE_RAG_RERANK: *["\']?(1|true|on)\b')

    def test_a_non_empty_default_is_caught(self):
        text = '  web:\n    environment:\n      RERANK_BACKEND: ${RERANK_BACKEND:-tei}\n  diary:\n'
        env_lines = section(service_block(text, 'web'), 'environment')
        self.assertEqual(re.findall(r'(?m)^ {6}RERANK_BACKEND: (.*)$', env_lines), ['${RERANK_BACKEND:-tei}'])
        self.assertNotEqual(re.findall(r'(?m)^ {6}RERANK_BACKEND: (.*)$', env_lines), ['${RERANK_BACKEND:-}'])


if __name__ == '__main__':
    unittest.main()
