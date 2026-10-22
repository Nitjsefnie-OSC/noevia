"""The retired document extraction selector reaches no container (#1071).

NOEVIA_DOCLING_IMPL chose between the native server and the Python HTTP server. The Python server is
deleted and the image fixes the selector to the native value itself, so no compose copy passes it:
a leftover NOEVIA_DOCLING_IMPL=python in an older .env must not reach the container. Only key names
are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.docling.yaml', 'compose.yaml', 'deploy/examples/unraid-compose-manager.yml']
KEY = 'NOEVIA_DOCLING_IMPL'


def problems_for(text):
    """Every line that passes the retired key, in mapping or list form."""
    return [line for line in text.splitlines()
            if re.match(r'^\s+(?:-\s*)?["\']?' + KEY + r'\s*[:=]', line)]


class RetiredDoclingSelectorTests(unittest.TestCase):
    def test_no_compose_copy_passes_the_retired_key(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8')), [])

    def test_mapping_and_list_forms_are_refused(self):
        for line in ['      NOEVIA_DOCLING_IMPL: ${NOEVIA_DOCLING_IMPL:-python}',
                     '      NOEVIA_DOCLING_IMPL: rust',
                     '      - NOEVIA_DOCLING_IMPL=python',
                     '      - "NOEVIA_DOCLING_IMPL=rust"']:
            self.assertEqual(problems_for('  docling:\n    environment:\n' + line), [line])

    def test_the_docling_service_keeps_its_other_settings(self):
        text = (ROOT / 'compose.docling.yaml').read_text(encoding='utf-8')
        for key in ('HF_HUB_OFFLINE:', 'DOCLING_ARTIFACTS_PATH:', 'DOCLING_RANGED_MAX_BYTES:'):
            self.assertIn(key, text)


if __name__ == '__main__':
    unittest.main()
