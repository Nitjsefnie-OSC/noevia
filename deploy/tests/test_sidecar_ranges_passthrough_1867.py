"""The OCR and Docling ranged-body caps reach their sidecars from .env, unset by default (#1867).

noevia-rs' noevia-ocr reads OCR_EXTRACT_MAX_BYTES and docling-service reads DOCLING_RANGED_MAX_BYTES
(the Python servers that also read them are retired, #1071). Both default to 96 MiB when the value is unset,
empty, not a number or not positive. Every compose copy that defines the sidecar must pass the key with
an empty default, so the image default applies today and the owner can lower it later. Only key names
and default expressions are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

from test_source_limits_passthrough import service_environment

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = [
    ('compose.yaml', 'ocr', 'OCR_EXTRACT_MAX_BYTES'),
    ('deploy/examples/unraid-compose-manager.yml', 'ocr', 'OCR_EXTRACT_MAX_BYTES'),
    ('compose.docling.yaml', 'docling', 'DOCLING_RANGED_MAX_BYTES'),
]


def problems_for(text, service, key):
    lines = [l.strip() for l in service_environment(text, service) if re.match(rf'^ {{6}}{key}:', l)]
    if len(lines) != 1:
        return [f'{service}.{key}: expected exactly one passthrough line, found {len(lines)}']
    if lines[0] != f'{key}: ${{{key}:-}}':
        return [f'{service}.{key}: default is not empty: {lines[0]}']
    return []


class SidecarRangesPassthroughTests(unittest.TestCase):
    def test_each_sidecar_copy_passes_its_cap_with_an_empty_default(self):
        for name, service, key in CASES:
            with self.subTest(copy=name, service=service):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8'), service, key), [])

    def test_the_cap_is_not_passed_to_web(self):
        for name, _service, key in CASES:
            text = (ROOT / name).read_text(encoding='utf-8')
            if '  web:' in text.split('\n'):
                with self.subTest(copy=name):
                    self.assertFalse(any(key in l for l in service_environment(text, 'web')))

    def test_the_check_catches_a_missing_or_preset_passthrough(self):
        base = '  ocr:\n    environment:\n      OTHER: x\n'
        key = 'OCR_EXTRACT_MAX_BYTES'
        self.assertEqual(len(problems_for(base, 'ocr', key)), 1)
        self.assertEqual(len(problems_for(base + f'      {key}: ${{{key}:-1048576}}\n', 'ocr', key)), 1)
        self.assertEqual(problems_for(base + f'      {key}: ${{{key}:-}}\n', 'ocr', key), [])


if __name__ == '__main__':
    unittest.main()
