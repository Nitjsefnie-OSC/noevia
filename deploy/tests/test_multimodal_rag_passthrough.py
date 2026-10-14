"""NOEVIA_MULTIMODAL_RAG reaches web and the model manager from .env, and defaults off (#1726).

Web reads it for multimodal RAG (noevia-core server/multimodal-rag.cjs); the model manager reads the
same switch for the on-demand `<model>.vision` image-embedding preset (noevia-rs
noevia-model-manager embedding.rs). Without a compose passthrough the owner's .env value never takes
effect. Every repo copy must pass it with the safe default `0`, the preflight expected-key list must
name it, and no copy may turn it on. Only key names and default expressions are read here; no .env
value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
KEY = 'NOEVIA_MULTIMODAL_RAG'
PREFLIGHT_KEYS = ROOT / 'deploy/preflight/web-env-keys.txt'

# (compose copy, service) pairs that must pass the switch through.
COPIES = [
    ('compose.yaml', 'web'),
    ('deploy/examples/unraid-compose-manager.yml', 'web'),
    ('compose.embed.yaml', 'model-loader'),
    ('deploy/examples/unraid-llamacpp.override.yml', 'model-loader'),
]


def service_environment(text, service):
    """The `environment:` lines of one service (two-space service keys, six-space env keys)."""
    lines = text.split('\n')
    start = lines.index(f'  {service}:')
    body, in_env = [], False
    for line in lines[start + 1:]:
        if re.match(r'^ {2}\S', line):
            break
        if re.match(r'^ {4}environment:\s*$', line):
            in_env = True
            continue
        if in_env and re.match(r'^ {4}\S', line):
            break
        if in_env:
            body.append(line)
    return body


def problems_for(text, service):
    lines = [line.strip() for line in service_environment(text, service) if re.match(rf'^ {{6}}{KEY}:', line)]
    if len(lines) != 1:
        return [f'{service}: expected exactly one {KEY} passthrough line, found {len(lines)}']
    if lines[0] != f'{KEY}: ${{{KEY}:-0}}':
        return [f'{service}: {KEY} default is not off: {lines[0]}']
    return []


class MultimodalRagPassthroughTests(unittest.TestCase):
    def test_every_copy_passes_the_switch_through_with_default_off(self):
        for name, service in COPIES:
            with self.subTest(copy=name, service=service):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8'), service), [])

    def test_preflight_expected_keys_name_the_switch(self):
        keys = {line.strip() for line in PREFLIGHT_KEYS.read_text(encoding='utf-8').splitlines() if line.strip()}
        self.assertIn(KEY, keys)

    def test_the_check_catches_a_missing_or_enabled_passthrough(self):
        base = '  web:\n    environment:\n      OTHER: x\n'
        self.assertEqual(len(problems_for(base, 'web')), 1)
        self.assertEqual(len(problems_for(base + f'      {KEY}: ${{{KEY}:-1}}\n', 'web')), 1)
        self.assertEqual(problems_for(base + f'      {KEY}: ${{{KEY}:-0}}\n', 'web'), [])


if __name__ == '__main__':
    unittest.main()
