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
# #1318 read slices passed through to model-loader only, each defaulting to python.
SLICE_KEYS = ('MODEL_MANAGER_MODELS_IMPL', 'MODEL_MANAGER_OVERVIEW_IMPL', 'MODEL_MANAGER_SEARCH_IMPL',
              'MODEL_MANAGER_SECTION_AUTOCONFIG_IMPL')


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


def slice_problems(text, key):
    lines = [l.strip() for l in service_environment(text, 'model-loader') if l.strip().startswith(key + ':')]
    if len(lines) != 1:
        return [f'expected exactly one {key} line in model-loader, found {len(lines)}']
    if lines[0] != f'{key}: ${{{key}:-python}}':
        return [f'{key} default is not python: {lines[0]}']
    return []


class SlicePassthroughTests(unittest.TestCase):
    def test_each_copy_passes_each_slice_once_with_python_default(self):
        for name in COMPOSE_COPIES:
            text = (ROOT / name).read_text(encoding='utf-8')
            for key in SLICE_KEYS:
                with self.subTest(copy=name, key=key):
                    self.assertEqual(slice_problems(text, key), [])
                    self.assertEqual(env_keys(text).count(key), 1)

    def test_web_does_not_get_a_slice_key(self):
        for name in COMPOSE_COPIES:
            text = (ROOT / name).read_text(encoding='utf-8')
            if '  web:' in text.split('\n'):
                for key in SLICE_KEYS:
                    with self.subTest(copy=name, key=key):
                        self.assertEqual([l for l in service_environment(text, 'web') if key in l], [])

    def test_missing_duplicate_or_non_python_default_is_reported(self):
        for key in SLICE_KEYS:
            head = '  model-loader:\n    environment:\n'
            good = f'      {key}: ${{{key}:-python}}\n'
            with self.subTest(key=key):
                self.assertEqual(len(slice_problems(head + '  web:\n', key)), 1)
                self.assertEqual(len(slice_problems(head + good + good, key)), 1)
                self.assertIn('not python', slice_problems(head + good.replace('python', 'rust'), key)[0])
                self.assertIn('not python', slice_problems(head + good.replace('python', ''), key)[0])


if __name__ == '__main__':
    unittest.main()
