"""WORKSPACE_RESTORE_VERIFY_IMPL reaches the Diary container with an empty default in each repo
compose copy (#982). Empty means the Diary's own default (python), so the image decides and a
compose copy can never silently switch the workspace ZIP gate to rust. Only key names and the
default expression are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

from test_tenant_assertion_impl_passthrough import COMPOSE_COPIES, ROOT, service_environment

KEY = 'WORKSPACE_RESTORE_VERIFY_IMPL'
EXPECTED = 'WORKSPACE_RESTORE_VERIFY_IMPL: ${WORKSPACE_RESTORE_VERIFY_IMPL:-}'


def problems_for(text):
    lines = [l.strip() for l in service_environment(text, 'diary') if re.match(rf'^ {{6}}{KEY}:', l)]
    if len(lines) != 1:
        return [f'expected exactly one {KEY} line in diary, found {len(lines)}']
    if lines[0] != EXPECTED:
        return [f'{KEY} default is not empty: {lines[0]}']
    return []


class WorkspaceRestoreVerifyImplPassthroughTests(unittest.TestCase):
    def test_each_compose_copy_passes_the_selector_with_an_empty_default(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8')), [])

    def test_a_missing_line_is_reported(self):
        self.assertEqual(len(problems_for('  diary:\n    environment:\n      TZ: UTC\n  web:\n')), 1)

    def test_a_rust_or_python_default_is_reported(self):
        for default in ('rust', 'python'):
            text = f'  diary:\n    environment:\n      {KEY}: ${{{KEY}:-{default}}}\n  web:\n'
            self.assertIn('not empty', problems_for(text)[0])

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
