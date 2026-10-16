"""MODEL_MANAGER_BENCHMARK_OVERVIEW_IMPL reaches the model-loader container, defaulting to python, in each repo compose copy.

#1318 (noevia-services#73, noevia-rs#148): the model-manager image reads MODEL_MANAGER_BENCHMARK_OVERVIEW_IMPL to decide whether
the native front answers GET /api/v1/benchmark. The image defaults it to python; without a compose
passthrough the owner could not switch it from .env, and an empty value must never be passed. Only key
names and the default expression are read here; no .env value is ever read.
"""
import pathlib
import unittest

from test_model_manager_impl_passthrough import COMPOSE_COPIES, ROOT, service_environment

KEY = 'MODEL_MANAGER_BENCHMARK_OVERVIEW_IMPL'
EXPECTED = 'MODEL_MANAGER_BENCHMARK_OVERVIEW_IMPL: ${MODEL_MANAGER_BENCHMARK_OVERVIEW_IMPL:-python}'


def problems_for(text):
    lines = [l.strip() for l in service_environment(text, 'model-loader') if l.strip().startswith(KEY + ':')]
    if len(lines) != 1:
        return [f'expected exactly one {KEY} line in model-loader, found {len(lines)}']
    if lines[0] != EXPECTED:
        return [f'{KEY} default is not python: {lines[0]}']
    return []


class ModelManagerBackendControlImplPassthroughTests(unittest.TestCase):
    def test_each_compose_copy_passes_the_selector_with_python_default(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8')), [])

    def test_a_missing_line_is_reported(self):
        text = '  model-loader:\n    environment:\n      MODEL_MANAGER_IMPL: ${MODEL_MANAGER_IMPL:-python}\n  web:\n'
        self.assertEqual(len(problems_for(text)), 1)

    def test_an_empty_or_rust_default_is_reported(self):
        for default in ('', 'rust'):
            text = f'  model-loader:\n    environment:\n      {KEY}: ${{{KEY}:-{default}}}\n  web:\n'
            with self.subTest(default=default):
                self.assertIn('not python', problems_for(text)[0])

    def test_web_does_not_get_the_selector(self):
        for name in COMPOSE_COPIES:
            text = (ROOT / name).read_text(encoding='utf-8')
            if '  web:' in text.split('\n'):
                with self.subTest(copy=name):
                    self.assertEqual([l for l in service_environment(text, 'web') if KEY in l], [])


if __name__ == '__main__':
    unittest.main()
