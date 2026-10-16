"""Project source and folder-import limits reach web from .env, unset by default (#1806, #1805).

noevia-core reads PROJECT_SOURCE_LIMIT, PROJECT_DOCUMENT_LIMIT, PROJECT_IMAGE_LIMIT,
FOLDER_IMPORT_MAX_FILES and FOLDER_IMPORT_MAX_BYTES; when unset it keeps its built-in defaults
(60/60/12 sources, 100 MB). Since core#149/core#150 it also reads the large-document
read/OCR limits (PROJECT_DOCUMENT_READ_BYTES, _PAGE_LIMIT, _TEXT_LIMIT, _RANGE_PAGES,
PROJECT_SYNC_OCR_PAGES) and the large-document lock timings (LARGE_DOCUMENT_ACQUIRE_WAIT_MS,
LARGE_DOCUMENT_HOLD_WARN_MS). Every web compose copy must pass each key with an empty default so the
owner can set it later without changing the defaults today, and the preflight expected-key list must
name each one. Only key names and default expressions are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
KEYS = [
    'PROJECT_SOURCE_LIMIT',
    'PROJECT_DOCUMENT_LIMIT',
    'PROJECT_IMAGE_LIMIT',
    'FOLDER_IMPORT_MAX_FILES',
    'FOLDER_IMPORT_MAX_BYTES',
    'PROJECT_DOCUMENT_READ_BYTES',
    'PROJECT_DOCUMENT_PAGE_LIMIT',
    'PROJECT_DOCUMENT_TEXT_LIMIT',
    'PROJECT_DOCUMENT_RANGE_PAGES',
    'PROJECT_SYNC_OCR_PAGES',
    'LARGE_DOCUMENT_ACQUIRE_WAIT_MS',
    'LARGE_DOCUMENT_HOLD_WARN_MS',
    # core#156/#158 (#1868, #1869, #1881): long-document tail backfill budgets.
    'PROJECT_TAIL_EMBED_PER_PASS',
    'PROJECT_TAIL_EMBED_PER_HOUR',
    'PROJECT_TAIL_EMBED_PER_DOCUMENT',
    'PROJECT_TAIL_EMBED_BATCH',
    'PROJECT_UPLOAD_COMPLETION_PER_PASS',
    'PROJECT_BACKFILL_DUTY',
    'PROJECT_BACKFILL_MIN_PAUSE_MS',
    'PROJECT_BACKFILL_DELAY_MS',
    'PROJECT_BACKFILL_INTERVAL_MS',
]
PREFLIGHT_KEYS = ROOT / 'deploy/preflight/web-env-keys.txt'
COPIES = ['compose.yaml', 'deploy/examples/unraid-compose-manager.yml']


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


def problems_for(text, key):
    lines = [line.strip() for line in service_environment(text, 'web') if re.match(rf'^ {{6}}{key}:', line)]
    if len(lines) != 1:
        return [f'{key}: expected exactly one passthrough line, found {len(lines)}']
    if lines[0] != f'{key}: ${{{key}:-}}':
        return [f'{key}: default is not empty: {lines[0]}']
    return []


class SourceLimitsPassthroughTests(unittest.TestCase):
    def test_every_web_copy_passes_each_key_with_an_empty_default(self):
        for name in COPIES:
            text = (ROOT / name).read_text(encoding='utf-8')
            for key in KEYS:
                with self.subTest(copy=name, key=key):
                    self.assertEqual(problems_for(text, key), [])

    def test_preflight_expected_keys_name_each_key(self):
        keys = {line.strip() for line in PREFLIGHT_KEYS.read_text(encoding='utf-8').splitlines() if line.strip()}
        for key in KEYS:
            with self.subTest(key=key):
                self.assertIn(key, keys)

    def test_the_check_catches_a_missing_or_preset_passthrough(self):
        base = '  web:\n    environment:\n      OTHER: x\n'
        key = KEYS[0]
        self.assertEqual(len(problems_for(base, key)), 1)
        self.assertEqual(len(problems_for(base + f'      {key}: ${{{key}:-60}}\n', key)), 1)
        self.assertEqual(problems_for(base + f'      {key}: ${{{key}:-}}\n', key), [])


if __name__ == '__main__':
    unittest.main()
