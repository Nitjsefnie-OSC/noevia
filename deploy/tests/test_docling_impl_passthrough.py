"""The retired document extraction selector is pinned to the native server, never read from .env (#1071).

NOEVIA_DOCLING_IMPL chose between the native server and the Python HTTP server. The Python server is
deleted, so a leftover NOEVIA_DOCLING_IMPL=python in an older .env must not reach the container. The
overlay pins the native value instead of dropping the key, because an image built before the
retirement defaults to python and would otherwise start the Python server. Only key names and the
compose expression are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.docling.yaml', 'compose.yaml', 'deploy/examples/unraid-compose-manager.yml']
KEY = 'NOEVIA_DOCLING_IMPL'


def passes(text):
    """Every line that passes the retired key, in mapping or list form."""
    return [line.strip() for line in text.splitlines()
            if re.match(r'^\s+(?:-\s*)?["\']?' + KEY + r'\s*[:=]', line)]


def problems_for(text):
    """Lines that pass anything but the pinned native value (an .env interpolation included)."""
    return [line for line in passes(text) if line != f'{KEY}: rust']


class RetiredDoclingSelectorTests(unittest.TestCase):
    def test_the_overlay_pins_the_native_server(self):
        text = (ROOT / 'compose.docling.yaml').read_text(encoding='utf-8')
        self.assertEqual(passes(text), [f'{KEY}: rust'])

    def test_no_compose_copy_reads_the_retired_key_from_env(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8')), [])

    def test_env_interpolation_and_other_values_are_refused(self):
        for line in ['      NOEVIA_DOCLING_IMPL: ${NOEVIA_DOCLING_IMPL:-python}',
                     '      NOEVIA_DOCLING_IMPL: ${NOEVIA_DOCLING_IMPL:-rust}',
                     '      NOEVIA_DOCLING_IMPL: python',
                     '      - NOEVIA_DOCLING_IMPL=python',
                     '      - "NOEVIA_DOCLING_IMPL=${NOEVIA_DOCLING_IMPL}"']:
            self.assertEqual(problems_for('  docling:\n    environment:\n' + line), [line.strip()])
        self.assertEqual(problems_for('  docling:\n    environment:\n      NOEVIA_DOCLING_IMPL: rust'), [])

    def test_the_docling_service_keeps_its_other_settings(self):
        text = (ROOT / 'compose.docling.yaml').read_text(encoding='utf-8')
        for key in ('HF_HUB_OFFLINE:', 'DOCLING_ARTIFACTS_PATH:', 'DOCLING_RANGED_MAX_BYTES:'):
            self.assertIn(key, text)


if __name__ == '__main__':
    unittest.main()
