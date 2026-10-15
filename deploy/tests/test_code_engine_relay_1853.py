"""The Code sandbox reaches a machine's model only through web's relay, never a route of its own (#1853).

Only the override's structure is read: the sandbox stays on the internal `code` network alone, that network
stays internal, and web receives CODE_ENGINE_RELAY_PORT (empty default: no relay). No .env value is read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
OVERRIDE = ROOT / 'deploy' / 'examples' / 'code-sandbox.override.yml'


def service_block(text, name):
    lines = text.split('\n')
    start = lines.index(f'  {name}:')
    out = []
    for line in lines[start + 1:]:
        if re.match(r'^ {0,2}\S', line):
            break
        out.append(line)
    return out


def sub_block(lines, key):
    """Lines under a four-space `key:` inside one service block."""
    out, inside = [], False
    for line in lines:
        if re.match(rf'^ {{4}}{key}:\s*$', line):
            inside = True
            continue
        if inside and re.match(r'^ {4}\S', line):
            break
        if inside:
            out.append(line)
    return out


def entries(lines):
    return [l.strip() for l in lines if l.strip() and not l.strip().startswith('#')]


class CodeEngineRelayTests(unittest.TestCase):
    def setUp(self):
        self.text = OVERRIDE.read_text(encoding='utf-8')

    def test_web_gets_the_relay_port_with_an_empty_default(self):
        env = entries(sub_block(service_block(self.text, 'web'), 'environment'))
        self.assertIn('CODE_ENGINE_RELAY_PORT: ${CODE_ENGINE_RELAY_PORT:-}', env)

    def test_the_sandbox_is_on_the_internal_code_network_only(self):
        sandbox = service_block(self.text, 'code-sandbox')
        self.assertEqual(entries(sub_block(sandbox, 'networks')), ['- code'])
        self.assertFalse(any(re.match(r'^ {4}(ports|network_mode|extra_hosts|dns):', l) for l in sandbox))
        networks = self.text.split('\nnetworks:\n', 1)[1].split('\nvolumes:\n', 1)[0]
        self.assertEqual(entries(networks.split('\n')), ['code:', 'internal: true'])

    def test_the_verifier_still_has_no_network(self):
        verify = service_block(self.text, 'code-verify')
        self.assertIn('network_mode: none', entries(verify))


if __name__ == '__main__':
    unittest.main()
