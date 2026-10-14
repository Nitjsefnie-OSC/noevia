"""The Docling native switch reaches the container from .env and defaults to python (#1690).

The image sets NOEVIA_DOCLING_IMPL=python, so without a compose passthrough the owner's
NOEVIA_DOCLING_IMPL=rust in .env never takes effect. Only key names and the default expression are
read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
KEY = 'NOEVIA_DOCLING_IMPL'


def docling_environment(text):
    """The `environment:` lines of the docling service (two-space service keys, six-space env keys)."""
    lines = text.split('\n')
    start = lines.index('  docling:')
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


class DoclingImplPassthroughTests(unittest.TestCase):
    def test_compose_docling_passes_the_switch_with_python_default(self):
        env = docling_environment((ROOT / 'compose.docling.yaml').read_text(encoding='utf-8'))
        lines = [line.strip() for line in env if re.match(rf'^ {{6}}{KEY}:', line)]
        self.assertEqual(lines, [f'{KEY}: ${{{KEY}:-python}}'])


if __name__ == '__main__':
    unittest.main()
