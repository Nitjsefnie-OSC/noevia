"""MODEL_MANAGER_IMPL reaches the model-loader container, defaulting to python, in each repo compose copy.

#1717: docs/deployment.md (#1668, #1689) says to set MODEL_MANAGER_IMPL=rust in .env, but no compose
copy forwarded it, so the image's entrypoint never saw it and kept execing uvicorn. Only key names and
the default expression are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.llamacpp.yaml', 'deploy/examples/unraid-llamacpp.override.yml']
EXPECTED = 'MODEL_MANAGER_IMPL: ${MODEL_MANAGER_IMPL:-python}'


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


def problems_for(text):
    found = []
    lines = [l.strip() for l in service_environment(text, 'model-loader') if re.match(r'^ {6}MODEL_MANAGER_IMPL:', l)]
    if len(lines) != 1:
        found.append(f'expected exactly one MODEL_MANAGER_IMPL line in model-loader, found {len(lines)}')
    elif lines[0] != EXPECTED:
        found.append(f'MODEL_MANAGER_IMPL default is not python: {lines[0]}')
    return found


class ModelManagerImplPassthroughTests(unittest.TestCase):
    def test_each_compose_copy_passes_the_selector_with_python_default(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8')), [])

    def test_a_missing_line_is_reported(self):
        text = '  model-loader:\n    environment:\n      DATA_DIR: /data\n  web:\n'
        self.assertEqual(len(problems_for(text)), 1)

    def test_a_rust_default_is_reported(self):
        text = '  model-loader:\n    environment:\n      MODEL_MANAGER_IMPL: ${MODEL_MANAGER_IMPL:-rust}\n  web:\n'
        self.assertIn('not python', problems_for(text)[0])

    def test_web_does_not_get_the_selector(self):
        for name in COMPOSE_COPIES:
            text = (ROOT / name).read_text(encoding='utf-8')
            if '  web:' in text.split('\n'):
                with self.subTest(copy=name):
                    web = [l for l in service_environment(text, 'web') if 'MODEL_MANAGER_IMPL' in l]
                    self.assertEqual(web, [])


if __name__ == '__main__':
    unittest.main()
