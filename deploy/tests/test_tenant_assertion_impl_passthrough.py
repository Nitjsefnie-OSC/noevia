"""The retired tenant selector reaches no service after the native-only Diary release."""
import pathlib
import re
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.yaml', 'deploy/examples/unraid-compose-manager.yml']
KEY = 'TENANT_ASSERTION_IMPL'
def problems_for(text):
    return [line for line in text.splitlines()
            if re.match(r'^\s+(?:-\s*)?' + KEY + r'\s*[:=]', line)]
class RetiredTenantSelectorTests(unittest.TestCase):
    def test_no_compose_service_receives_the_retired_key(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                self.assertEqual(problems_for((ROOT/name).read_text()), [])
    def test_mapping_and_list_forms_are_rejected(self):
        for line in ['      TENANT_ASSERTION_IMPL: ${TENANT_ASSERTION_IMPL:-python}',
                     '      - TENANT_ASSERTION_IMPL=rust']:
            self.assertEqual(problems_for('  diary:\n    environment:\n'+line), [line])
    def test_unrelated_workspace_gate_is_preserved(self):
        for name in COMPOSE_COPIES:
            self.assertIn('WORKSPACE_RESTORE_VERIFY_IMPL:', (ROOT/name).read_text())
if __name__ == '__main__':
    unittest.main()
