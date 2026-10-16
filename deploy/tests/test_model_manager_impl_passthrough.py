"""MODEL_MANAGER_IMPL and MODEL_FILES_IMPL are retired (#1071) and reach no container.

The native model manager front and the model-files leaf are permanent: the model-loader image always
runs them, so a Compose passthrough could only bring back the old Python-only front on an image that
predates noevia-services#69 (its default was python). Only key names are read here; no .env value
is ever read.

The module keeps its old name because the #1318 selector passthrough tests import ROOT,
COMPOSE_COPIES and service_environment from it.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.llamacpp.yaml', 'deploy/examples/unraid-llamacpp.override.yml']
RETIRED = ('MODEL_MANAGER_IMPL', 'MODEL_FILES_IMPL')


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


def env_keys(text):
    """Every six-space `KEY:` (map form) or `- KEY=` (list form) environment key, in any service."""
    keys = []
    for line in text.split('\n'):
        m = re.match(r'^ {6}(?:- )?([A-Z][A-Z0-9_]*)\s*[:=]', line)
        if m:
            keys.append(m.group(1))
    return keys


def problems_for(text):
    return [f'{key} is retired (#1071) but still passed' for key in env_keys(text) if key in RETIRED]


class RetiredModelLoaderSwitchTests(unittest.TestCase):
    def test_no_compose_copy_passes_a_retired_switch(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8')), [])

    def test_a_leftover_passthrough_is_reported_in_either_form(self):
        for line in ('      MODEL_MANAGER_IMPL: ${MODEL_MANAGER_IMPL:-python}',
                     '      MODEL_FILES_IMPL: ${MODEL_FILES_IMPL:-rust}',
                     '      - MODEL_MANAGER_IMPL=rust'):
            text = f'  model-loader:\n    environment:\n{line}\n  web:\n'
            with self.subTest(line=line):
                self.assertEqual(len(problems_for(text)), 1)

    def test_the_kept_selectors_are_not_mistaken_for_retired_ones(self):
        text = ('  model-loader:\n    environment:\n'
                '      MODEL_MANAGER_SETTINGS_IMPL: ${MODEL_MANAGER_SETTINGS_IMPL:-python}\n'
                '      MODEL_MANAGER_SECTIONS_IMPL: ${MODEL_MANAGER_SECTIONS_IMPL:-python}\n')
        self.assertEqual(problems_for(text), [])

    def test_the_example_env_does_not_ask_for_them(self):
        text = (ROOT / '.env.example').read_text(encoding='utf-8')
        for key in RETIRED:
            with self.subTest(key=key):
                self.assertNotIn(key, text)


if __name__ == '__main__':
    unittest.main()
