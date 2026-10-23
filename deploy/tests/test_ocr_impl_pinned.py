"""The retired OCR selectors are pinned to the native server, never read from .env (#1071).

NOEVIA_OCR_IMPL chose between the native noevia-ocr server and the Python OCR server, and
DOCX_TEXT_IMPL chose the DOCX reader inside the Python server. The Python server is deleted, so a
leftover NOEVIA_OCR_IMPL=python in an older .env must not reach the container. The compose copies pin
the native value instead of dropping the key, because an image built before the retirement defaults
to python and would otherwise start the Python server. DOCX_TEXT_IMPL was never passed and must stay
that way. Only key names and compose expressions are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.yaml', 'deploy/examples/unraid-compose-manager.yml']
EVERY_COMPOSE = sorted({*COMPOSE_COPIES, *(p.name for p in ROOT.glob('compose*.yaml'))})
KEY = 'NOEVIA_OCR_IMPL'
DOCX_KEY = 'DOCX_TEXT_IMPL'


def passes(text, key=KEY):
    """Every line that passes the key, in mapping or list form."""
    return [line.strip() for line in text.splitlines()
            if re.match(r'^\s+(?:-\s*)?["\']?' + key + r'\s*[:=]', line)]


def problems_for(text):
    """Lines that pass anything but the pinned native value (an .env interpolation included)."""
    return [line for line in passes(text) if line != f'{KEY}: rust']


def ocr_block(text):
    match = re.search(r'(?ms)^  ocr:\n(.*?)(?=^  \S|^\S|\Z)', text)
    return match.group(1) if match else ''


class RetiredOcrSelectorTests(unittest.TestCase):
    def test_each_copy_pins_the_native_server_in_the_ocr_service(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                text = (ROOT / name).read_text(encoding='utf-8')
                self.assertEqual(passes(ocr_block(text)), [f'{KEY}: rust'])
                self.assertEqual(passes(text), [f'{KEY}: rust'])

    def test_no_compose_file_reads_either_retired_key_from_env(self):
        for name in EVERY_COMPOSE:
            with self.subTest(copy=name):
                text = (ROOT / name).read_text(encoding='utf-8')
                self.assertEqual(problems_for(text), [])
                self.assertEqual(passes(text, DOCX_KEY), [])
                self.assertNotIn('${' + KEY, text)
                self.assertNotIn('${' + DOCX_KEY, text)

    def test_env_example_no_longer_offers_the_selectors(self):
        text = (ROOT / '.env.example').read_text(encoding='utf-8')
        self.assertNotRegex(text, rf'(?m)^\s*#?\s*{KEY}=')
        self.assertNotRegex(text, rf'(?m)^\s*#?\s*{DOCX_KEY}=')

    def test_env_interpolation_and_other_values_are_refused(self):
        for line in ['      NOEVIA_OCR_IMPL: ${NOEVIA_OCR_IMPL:-python}',
                     '      NOEVIA_OCR_IMPL: ${NOEVIA_OCR_IMPL:-rust}',
                     '      NOEVIA_OCR_IMPL: python',
                     '      NOEVIA_OCR_IMPL: ""',
                     '      - NOEVIA_OCR_IMPL=python',
                     '      - "NOEVIA_OCR_IMPL=${NOEVIA_OCR_IMPL}"']:
            self.assertEqual(problems_for('  ocr:\n    environment:\n' + line), [line.strip()])
        self.assertEqual(problems_for('  ocr:\n    environment:\n      NOEVIA_OCR_IMPL: rust'), [])

    def test_the_ocr_service_keeps_its_other_settings(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                block = ocr_block((ROOT / name).read_text(encoding='utf-8'))
                for key in ('OCR_EXTRACT_MAX_BYTES:', 'read_only: true', 'cap_drop: [ALL]', 'networks: [ocr]'):
                    self.assertIn(key, block)


if __name__ == '__main__':
    unittest.main()
