"""The native-front configuration reaches the web container in each repo compose copy.

#1400: the live Compose Manager override did not pass the native-front switches through, so they could
not be turned on there. sbstndalton/noevia#1071: the front read routes are now the Rust front's
permanently, and so are sign-in and the account and the project routes and store (NOEVIA_RUST_AUTH and
NOEVIA_RUST_PROJECTS are retired too); the web supervisor refuses to start without NOEVIA_FRONT=rust,
so the repo copies (compose.yaml and deploy/examples/unraid-compose-manager.yml) pass that with a default
that boots, and no longer pass the retired switches. The preflight expected-key list names it and none
of the retired ones. Only key names and the
default expression are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.yaml', 'deploy/examples/unraid-compose-manager.yml']
PREFLIGHT_KEYS = ROOT / 'deploy/preflight/web-env-keys.txt'

# What the web supervisor requires, with the default each compose copy must carry.
REQUIRED = {
    'NOEVIA_FRONT': 'rust',
}
# Retired by #1071: their routes (sign-in, the project routes and store, the read routes) are the
# Rust front's permanently.
RETIRED = [
    'NOEVIA_RUST_AUTH',
    'NOEVIA_RUST_PROJECTS',
    'NOEVIA_RUST_USAGE',
    'NOEVIA_RUST_SAMPLING_SETTINGS',
    'NOEVIA_RUST_REASONING_SETTINGS',
    'NOEVIA_RUST_ROUTING_MODE',
    'NOEVIA_RUST_ROUTING_DEFAULT',
    'NOEVIA_RUST_STATS',
    'NOEVIA_RUST_STORAGE_READS',
    'NOEVIA_RUST_STORAGE_BROWSE',
    'NOEVIA_RUST_EXPORT',
    'NOEVIA_RUST_CHATGPT_STATUS',
]


def web_environment(text):
    """The `environment:` lines of the web service, as text (two-space service keys, six-space env keys)."""
    lines = text.split('\n')
    start = lines.index('  web:')
    body = []
    in_env = False
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


def switch_lines(env_lines, key):
    return [line.strip() for line in env_lines if re.match(rf'^ {{6}}{key}:', line)]


def problems_for(text, required=REQUIRED, retired=RETIRED):
    """Each way a compose text fails the rule, one message per problem (empty when it passes)."""
    env = web_environment(text)
    found = []
    for key, default in required.items():
        lines = switch_lines(env, key)
        if len(lines) != 1:
            found.append(f'{key}: expected exactly one passthrough line, found {len(lines)}')
            continue
        if lines[0] != f'{key}: ${{{key}:-{default}}}':
            found.append(f'{key}: default is not {default}: {lines[0]}')
    for key in retired:
        if switch_lines(env, key):
            found.append(f'{key}: retired switch is still passed through')
    return found


class SwitchPassthroughTests(unittest.TestCase):
    def test_every_compose_copy_passes_the_required_front_config_with_defaults_that_boot(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                text = (ROOT / name).read_text(encoding='utf-8')
                self.assertEqual(problems_for(text), [])

    def test_no_compose_copy_mentions_a_retired_switch(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                text = (ROOT / name).read_text(encoding='utf-8')
                for key in RETIRED:
                    self.assertNotIn(key, text, f'{name} still names {key}')

    def test_preflight_expected_keys_name_the_required_and_none_retired(self):
        keys = {line.strip() for line in PREFLIGHT_KEYS.read_text(encoding='utf-8').splitlines() if line.strip()}
        self.assertEqual([k for k in REQUIRED if k not in keys], [], 'web-env-keys.txt is missing a required key')
        self.assertEqual([k for k in RETIRED if k in keys], [], 'web-env-keys.txt still expects a retired switch')

    def test_checker_flags_a_missing_wrong_default_or_retired_passthrough(self):
        synthetic = '\n'.join([
            'services:',
            '  web:',
            '    environment:',
            '      NOEVIA_FRONT: ${NOEVIA_FRONT:-node}',
            '      NOEVIA_RUST_STATS: ${NOEVIA_RUST_STATS:-0}',
            '      NOEVIA_RUST_PROJECTS: ${NOEVIA_RUST_PROJECTS:-1}',
            '      NOEVIA_RUST_AUTH: ${NOEVIA_RUST_AUTH:-1}',
            '  diary:',
            '    environment:',
            '      NOEVIA_RUST_AUTH: ${NOEVIA_RUST_AUTH:-1}',
            '',
        ])
        found = problems_for(synthetic)
        self.assertEqual(len(found), 4, found)
        self.assertTrue(any(msg.startswith('NOEVIA_RUST_AUTH: retired') for msg in found))
        self.assertTrue(any(msg.startswith('NOEVIA_FRONT: default is not rust') for msg in found))
        self.assertTrue(any(msg.startswith('NOEVIA_RUST_PROJECTS: retired') for msg in found))
        self.assertTrue(any(msg.startswith('NOEVIA_RUST_STATS: retired') for msg in found))


if __name__ == '__main__':
    unittest.main()
