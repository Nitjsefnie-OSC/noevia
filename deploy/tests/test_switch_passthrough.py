"""Every native-front switch reaches the web container, and defaults off, in each repo compose copy.

#1400: the live Compose Manager override did not pass NOEVIA_RUST_USAGE, NOEVIA_RUST_SAMPLING_SETTINGS,
NOEVIA_RUST_REASONING_SETTINGS and NOEVIA_RUST_ROUTING_MODE through, so they could not be turned on
there. The repo copies (compose.yaml and deploy/examples/unraid-compose-manager.yml) must pass each of
them with the safe default `0`, and the preflight expected-key list must name them. Only key names and
the default expression are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.yaml', 'deploy/examples/unraid-compose-manager.yml']
PREFLIGHT_KEYS = ROOT / 'deploy/preflight/web-env-keys.txt'

# The native-front switches that must be operator-settable from .env without a compose edit.
SWITCHES = [
    'NOEVIA_RUST_AUTH',
    'NOEVIA_RUST_PROJECTS',
    'NOEVIA_RUST_USAGE',
    'NOEVIA_RUST_SAMPLING_SETTINGS',
    'NOEVIA_RUST_REASONING_SETTINGS',
    'NOEVIA_RUST_ROUTING_MODE',
    'NOEVIA_RUST_ROUTING_DEFAULT',
    'NOEVIA_RUST_STATS',
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


def problems_for(text, keys=SWITCHES):
    """Each way a compose text fails the rule, one message per problem (empty when it passes)."""
    env = web_environment(text)
    found = []
    for key in keys:
        lines = switch_lines(env, key)
        if len(lines) != 1:
            found.append(f'{key}: expected exactly one passthrough line, found {len(lines)}')
            continue
        if lines[0] != f'{key}: ${{{key}:-0}}':
            found.append(f'{key}: default is not off: {lines[0]}')
    return found


class SwitchPassthroughTests(unittest.TestCase):
    def test_every_compose_copy_passes_each_switch_through_with_default_off(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                text = (ROOT / name).read_text(encoding='utf-8')
                self.assertEqual(problems_for(text), [])

    def test_preflight_expected_keys_name_each_switch(self):
        keys = {line.strip() for line in PREFLIGHT_KEYS.read_text(encoding='utf-8').splitlines() if line.strip()}
        missing = [key for key in SWITCHES if key not in keys]
        self.assertEqual(missing, [], 'deploy/preflight/web-env-keys.txt is missing switches')

    def test_no_compose_copy_turns_a_switch_on(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                text = (ROOT / name).read_text(encoding='utf-8')
                for key in SWITCHES:
                    self.assertIsNone(
                        re.search(rf'{key}:\s*\$\{{{key}:-(?!0\}})', text),
                        f'{name} sets a non-zero default for {key}',
                    )

    def test_checker_flags_a_missing_or_on_by_default_passthrough(self):
        # Synthetic web service: one switch dropped, one defaulting on. The rule must catch both.
        synthetic = '\n'.join([
            'services:',
            '  web:',
            '    environment:',
            '      NOEVIA_RUST_AUTH: ${NOEVIA_RUST_AUTH:-0}',
            '      NOEVIA_RUST_USAGE: ${NOEVIA_RUST_USAGE:-1}',
            '  diary:',
            '    environment:',
            '      NOEVIA_RUST_ROUTING_MODE: ${NOEVIA_RUST_ROUTING_MODE:-0}',
            '',
        ])
        found = problems_for(synthetic, ['NOEVIA_RUST_AUTH', 'NOEVIA_RUST_USAGE', 'NOEVIA_RUST_ROUTING_MODE'])
        self.assertEqual(len(found), 2)
        self.assertTrue(any(msg.startswith('NOEVIA_RUST_USAGE: default is not off') for msg in found))
        self.assertTrue(any(msg.startswith('NOEVIA_RUST_ROUTING_MODE: expected exactly one') for msg in found))


if __name__ == '__main__':
    unittest.main()
