"""deploy/tools/flags.sh allow-list (#1193, #1195 nit): keys are matched whole, never line by line."""
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
FLAGS = ROOT / 'deploy/tools/flags.sh'


class FlagsAllowList(unittest.TestCase):
    def setUp(self):
        self.temp = pathlib.Path(tempfile.mkdtemp(prefix='noevia-flags-'))
        self.log = self.temp / 'docker.log'
        stub = self.temp / 'docker'
        stub.write_text('#!/bin/bash\nprintf "docker %s\\n" "$*" >> "$CALL_LOG"\necho "[{\\"Config\\":{\\"Env\\":[]}}]"\n')
        stub.chmod(0o755)

    def run_flags(self, *args):
        env = dict(os.environ, PATH=f'{self.temp}:{os.environ["PATH"]}', CALL_LOG=str(self.log))
        return subprocess.run(['bash', str(FLAGS), *args], env=env, capture_output=True, text=True, timeout=30)

    def test_a_key_with_an_allowed_first_line_and_another_line_is_refused_before_docker(self):
        for key in ['FOO_IMPL\nDIARY_AUTH_TOKEN', 'DIARY_AUTH_TOKEN\nFOO_IMPL', 'COWORK_VERSION\n']:
            with self.subTest(key=key):
                result = self.run_flags('cowork-web-1', key)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn('refusing key not on the allow-list', result.stderr)
                self.assertFalse(self.log.exists(), 'docker must not be called')

    def test_a_plain_allowed_key_reaches_docker(self):
        result = self.run_flags('cowork-web-1', 'FOO_IMPL')
        self.assertTrue(self.log.exists(), result.stderr)

    def test_a_container_name_with_a_second_line_is_refused(self):
        result = self.run_flags('cowork-web-1\n-x')
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())


if __name__ == '__main__':
    unittest.main()
