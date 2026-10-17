"""The web image's runtime stage ships the project-store test fixtures next to the in-image server tests (#1990).

Release candidates run server tests from /app/server inside the image. project-store-failures,
routes/import and rust-projects require ../tests/server/project-store-{stub,server}.cjs (i.e.
/app/tests/server/...), which the runtime stage did not copy (only the build stage did), so they failed
with MODULE_NOT_FOUND. The build context is the assembled tree, whose core/tests/server is already inside it
(assemble-release.sh) and not excluded by its .dockerignore, so a COPY in the runtime stage is enough.
Only the Dockerfile text is read here.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / 'build' / 'web.Dockerfile'
FIXTURES = ('project-store-stub.cjs', 'project-store-server.cjs')


def logical_lines(text):
    """Dockerfile instructions with backslash continuations joined; comments dropped."""
    out, cur = [], ''
    for line in text.split('\n'):
        if not cur and line.lstrip().startswith('#'):
            continue
        if line.endswith('\\'):
            cur += line[:-1] + ' '
            continue
        out.append(cur + line)
        cur = ''
    return [l.strip() for l in out if l.strip()]


def runtime_copies(text):
    """(sources, dest) of every COPY (not --from) in the last stage."""
    stage = []
    for line in logical_lines(text):
        if line.upper().startswith('FROM '):
            stage = []
        stage.append(line)
    copies = []
    for line in stage:
        if line.upper().startswith('COPY ') and '--from=' not in line:
            args = line.split()[1:]
            copies.append((args[:-1], args[-1]))
    return copies


def shipped_test_fixtures(text):
    """Fixture basenames copied into ./tests/server/ (/app/tests/server) in the runtime stage."""
    found = set()
    for sources, dest in runtime_copies(text):
        if dest.rstrip('/') not in ('./tests/server', 'tests/server', '/app/tests/server'):
            continue
        for src in sources:
            m = re.match(r'^core/tests/server/(.+)$', src)
            if m:
                found.add(m.group(1))
    return found


class WebImageTestFixturesTests(unittest.TestCase):
    def test_runtime_stage_copies_both_project_store_fixtures(self):
        text = DOCKERFILE.read_text(encoding='utf-8')
        self.assertEqual(sorted(set(FIXTURES) - shipped_test_fixtures(text)), [])

    def test_the_fixtures_are_copied_from_the_assembled_trees_core(self):
        # assemble-release.sh lays core/tests/server into the tree; the build stage copies it from there.
        text = DOCKERFILE.read_text(encoding='utf-8')
        self.assertIn('COPY core/tests/server ./tests/server', text)

    def test_only_the_two_fixtures_are_shipped_not_the_whole_tests_directory(self):
        text = DOCKERFILE.read_text(encoding='utf-8')
        self.assertEqual(shipped_test_fixtures(text), set(FIXTURES))

    def test_a_dockerfile_without_the_copy_is_reported(self):
        text = 'FROM a AS build\nCOPY core/tests/server ./tests/server\nFROM b\nCOPY core/server ./server\n'
        self.assertEqual(shipped_test_fixtures(text), set())

    def test_a_build_stage_only_copy_does_not_count(self):
        text = ('FROM a AS build\nCOPY core/tests/server/project-store-stub.cjs ./tests/server/\n'
                'FROM b\nCOPY core/server ./server\n')
        self.assertEqual(shipped_test_fixtures(text), set())

    def test_a_continued_copy_line_is_parsed(self):
        text = ('FROM b\nCOPY core/tests/server/project-store-stub.cjs \\\n'
                '  core/tests/server/project-store-server.cjs ./tests/server/\n')
        self.assertEqual(shipped_test_fixtures(text), set(FIXTURES))


if __name__ == '__main__':
    unittest.main()
