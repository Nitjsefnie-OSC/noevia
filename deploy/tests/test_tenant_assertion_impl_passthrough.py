"""TENANT_ASSERTION_IMPL reaches the Diary container, defaulting to python, in each repo compose copy.

#1723: the owner approved TENANT_ASSERTION_IMPL=rust (#1147), but no compose copy forwarded the key to
`diary` (which has no env_file), so setting it in .env alone left the Diary on the python check. Only key
names and the default expression are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.yaml', 'deploy/examples/unraid-compose-manager.yml']
KEY = 'TENANT_ASSERTION_IMPL'
EXPECTED = 'TENANT_ASSERTION_IMPL: ${TENANT_ASSERTION_IMPL:-python}'


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


def problems_for(text):
    found = []
    lines = [l.strip() for l in service_environment(text, 'diary') if re.match(rf'^ {{6}}{KEY}:', l)]
    if len(lines) != 1:
        found.append(f'expected exactly one {KEY} line in diary, found {len(lines)}')
    elif lines[0] != EXPECTED:
        found.append(f'{KEY} default is not python: {lines[0]}')
    return found


class TenantAssertionImplPassthroughTests(unittest.TestCase):
    def test_each_compose_copy_passes_the_selector_with_python_default(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8')), [])

    def test_a_missing_line_is_reported(self):
        text = '  diary:\n    environment:\n      TZ: UTC\n  web:\n'
        self.assertEqual(len(problems_for(text)), 1)

    def test_a_rust_default_is_reported(self):
        text = '  diary:\n    environment:\n      TENANT_ASSERTION_IMPL: ${TENANT_ASSERTION_IMPL:-rust}\n  web:\n'
        self.assertIn('not python', problems_for(text)[0])

    def test_only_diary_gets_the_selector(self):
        for name in COMPOSE_COPIES:
            text = (ROOT / name).read_text(encoding='utf-8')
            services = [l[2:-1] for l in text.split('\n') if re.match(r'^ {2}[a-z][\w-]*:$', l)]
            for service in services:
                if service == 'diary':
                    continue
                with self.subTest(copy=name, service=service):
                    self.assertEqual([l for l in service_environment(text, service) if KEY in l], [])


if __name__ == '__main__':
    unittest.main()
