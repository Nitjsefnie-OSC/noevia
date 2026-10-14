"""The #1639 decision-routing keys reach the web container, defaulting to empty, in each repo compose copy.

noevia-core#108 chooses the decision wording, contract and calibration by COWORK_DECISION_MODEL, and can
send the sensitivity check alone to COWORK_SENSITIVITY_DECISION_URL (so it stays on Laya while Kev serves
the rest). Empty means exactly today's behaviour. The web service has no env_file, so each key must be
forwarded explicitly, and the preflight expected-key list must name it. Only key names and the default
expression are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.yaml', 'deploy/examples/unraid-compose-manager.yml']
PREFLIGHT_KEYS = ROOT / 'deploy/preflight/web-env-keys.txt'
KEYS = [
    'COWORK_DECISION_URL',
    'COWORK_DECISION_MODEL',
    'COWORK_DECISION_API_KEY',
    'COWORK_SENSITIVITY_DECISION_URL',
    'COWORK_SENSITIVITY_DECISION_MODEL',
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


def problems_for(text, keys=KEYS):
    env = service_environment(text, 'web')
    found = []
    for key in keys:
        lines = [l.strip() for l in env if re.match(rf'^ {{6}}{key}:', l)]
        if len(lines) != 1:
            found.append(f'{key}: expected exactly one passthrough line in web, found {len(lines)}')
        elif lines[0] != f'{key}: ${{{key}:-}}':
            found.append(f'{key}: default is not empty: {lines[0]}')
    return found


class DecisionRoutingPassthroughTests(unittest.TestCase):
    def test_each_compose_copy_passes_every_key_with_an_empty_default(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8')), [])

    def test_the_preflight_list_names_every_key(self):
        listed = set(PREFLIGHT_KEYS.read_text(encoding='utf-8').split())
        self.assertEqual([k for k in KEYS if k not in listed], [])

    def test_env_example_leaves_every_key_empty(self):
        text = (ROOT / '.env.example').read_text(encoding='utf-8')
        for key in KEYS:
            with self.subTest(key=key):
                self.assertEqual(re.findall(rf'^{key}=(.*)$', text, re.M), [''])

    def test_a_missing_line_is_reported(self):
        text = '  web:\n    environment:\n      COWORK_DECISION_URL: ${COWORK_DECISION_URL:-}\n  diary:\n'
        self.assertEqual(len(problems_for(text)), len(KEYS) - 1)

    def test_a_non_empty_default_is_reported(self):
        lines = ''.join(f'      {k}: ${{{k}:-}}\n' for k in KEYS if k != 'COWORK_DECISION_MODEL')
        text = '  web:\n    environment:\n' + lines + '      COWORK_DECISION_MODEL: ${COWORK_DECISION_MODEL:-kev-0.8b}\n  diary:\n'
        self.assertEqual(problems_for(text), ['COWORK_DECISION_MODEL: default is not empty: COWORK_DECISION_MODEL: ${COWORK_DECISION_MODEL:-kev-0.8b}'])

    def test_only_web_gets_the_keys(self):
        for name in COMPOSE_COPIES:
            text = (ROOT / name).read_text(encoding='utf-8')
            services = [l[2:-1] for l in text.split('\n') if re.match(r'^ {2}[a-z][\w-]*:$', l)]
            for service in services:
                if service == 'web':
                    continue
                with self.subTest(copy=name, service=service):
                    env = service_environment(text, service)
                    self.assertEqual([l for l in env if any(re.match(rf'^ {{6}}{k}:', l) for k in KEYS)], [])


if __name__ == '__main__':
    unittest.main()
