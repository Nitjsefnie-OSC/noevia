"""deploy/tools/candidate-boot.sh boots a web candidate the way the runbook says, with a stubbed docker.

#1416: a read-only candidate exits at startup unless UI_DATA_DIR points at a writable tmpfs. These
tests check the argv the script gives docker (the data dir must sit under a --tmpfs mount), the
readiness decision (the sha must match, and the container is removed either way), the bounded wait,
and that the throwaway tokens are never printed. No real docker, image or network is used.
"""
import os
import pathlib
import shlex
import stat
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'deploy/tools/candidate-boot.sh'
SHA = 'abcdef123456'

STUB = r'''#!/usr/bin/env bash
# Records every docker call; answers from files in $STUB_DIR.
echo "$*" >> "$STUB_DIR/calls"
case "$1" in
  run) echo "stubcontainer"; exit 0 ;;
  inspect) echo "${STUB_RUNNING:-true}"; exit 0 ;;
  exec) cat "$STUB_DIR/ready" 2>/dev/null; exit "${STUB_EXEC_RC:-0}" ;;
  logs) cat "$STUB_DIR/logs" 2>/dev/null; exit 0 ;;
  rm) exit 0 ;;
  *) exit 1 ;;
esac
'''


class CandidateBootTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        (self.dir / 'bin').mkdir()
        stub = self.dir / 'bin' / 'docker'
        stub.write_text(STUB)
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        (self.dir / 'calls').write_text('')
        (self.dir / 'logs').write_text('')

    def tearDown(self):
        self.tmp.cleanup()

    def answer(self, body):
        (self.dir / 'ready').write_text(body)

    def run_script(self, *args, **env):
        full_env = dict(os.environ)
        full_env['PATH'] = f"{self.dir / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"
        full_env['STUB_DIR'] = str(self.dir)
        full_env.pop('CANDIDATE_FRONT', None)
        full_env.pop('CANDIDATE_WAIT_SECONDS', None)
        full_env.update(env)
        return subprocess.run(['bash', str(SCRIPT), *args], capture_output=True, text=True, env=full_env, timeout=60)

    def calls(self):
        return (self.dir / 'calls').read_text().splitlines()

    def run_argv(self):
        runs = [c for c in self.calls() if c.startswith('run ')]
        self.assertEqual(len(runs), 1, f'expected one docker run, got {runs}')
        return shlex.split(runs[0])

    def env_value(self, argv, key):
        pairs = [argv[i + 1] for i, a in enumerate(argv) if a == '-e' and i + 1 < len(argv)]
        found = [p.split('=', 1)[1] for p in pairs if p.startswith(key + '=')]
        self.assertEqual(len(found), 1, f'{key} passed {len(found)} times')
        return found[0]

    def test_refuses_a_non_sha_without_touching_docker(self):
        result = self.run_script('not-a-sha')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls(), [])

    def test_refuses_a_bad_front_and_a_bad_wait_without_touching_docker(self):
        self.assertEqual(self.run_script(SHA, CANDIDATE_FRONT='python').returncode, 2)
        # #1071: the node front is gone; the web supervisor would refuse it, so this does too.
        node = self.run_script(SHA, CANDIDATE_FRONT='node')
        self.assertEqual(node.returncode, 2)
        self.assertIn('#1071', node.stderr)
        self.assertEqual(self.run_script(SHA, CANDIDATE_WAIT_SECONDS='soon').returncode, 2)
        self.assertEqual(self.calls(), [])

    def test_data_dir_is_writable_tmpfs_on_a_read_only_root(self):
        self.answer('{"ready":true,"version":"%s"}' % SHA)
        self.run_script(SHA)
        argv = self.run_argv()
        self.assertIn('--read-only', argv)
        self.assertIn('--network', argv)
        self.assertEqual(argv[argv.index('--network') + 1], 'none')
        data_dir = self.env_value(argv, 'UI_DATA_DIR')
        tmpfs_mounts = [argv[i + 1] for i, a in enumerate(argv) if a == '--tmpfs']
        covering = [m for m in tmpfs_mounts if data_dir == m.split(':', 1)[0] or data_dir.startswith(m.split(':', 1)[0] + '/')]
        self.assertTrue(covering, f'UI_DATA_DIR={data_dir} is not under any --tmpfs mount: {tmpfs_mounts}')
        self.assertNotIn('/app/server/ui-data', data_dir, 'the image default sits on the read-only root')

    def test_drops_capabilities_and_disables_the_network_for_the_candidate(self):
        self.answer('{"ready":true,"version":"%s"}' % SHA)
        self.run_script(SHA)
        argv = self.run_argv()
        self.assertEqual(argv[argv.index('--cap-drop') + 1], 'ALL')
        self.assertIn('no-new-privileges', argv)
        # The only bootable configuration since #1071: the Rust front with native auth and projects.
        self.assertEqual(self.env_value(argv, 'NOEVIA_FRONT'), 'rust')
        self.assertEqual(self.env_value(argv, 'NOEVIA_RUST_AUTH'), '1')
        self.assertFalse(any(a.startswith('NOEVIA_RUST_PROJECTS') for a in argv), 'the retired projects switch is not passed (#1071)')

    def test_ready_at_the_sha_exits_zero_and_removes_the_container(self):
        self.answer('{"ready":true,"version":"%s"}' % SHA)
        result = self.run_script(SHA)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f'ready at {SHA}', result.stdout)
        self.assertTrue(any(c.startswith('rm -f ') for c in self.calls()), 'candidate not removed')

    def test_ready_at_another_sha_fails_and_still_removes_the_container(self):
        self.answer('{"ready":true,"version":"0000000"}')
        result = self.run_script(SHA, CANDIDATE_WAIT_SECONDS='0')
        self.assertEqual(result.returncode, 1)
        self.assertIn('not ready', result.stderr)
        self.assertTrue(any(c.startswith('rm -f ') for c in self.calls()), 'candidate not removed')

    def test_a_container_that_stopped_fails_without_waiting(self):
        self.answer('')
        result = self.run_script(SHA, STUB_RUNNING='false', CANDIDATE_WAIT_SECONDS='120')
        self.assertEqual(result.returncode, 1)
        self.assertFalse(any(c.startswith('exec ') for c in self.calls()), 'probed a stopped container')

    def test_wait_is_bounded(self):
        self.answer('')
        result = self.run_script(SHA, CANDIDATE_WAIT_SECONDS='0')
        self.assertEqual(result.returncode, 1)
        self.assertIn('within 0s', result.stderr)

    def test_throwaway_tokens_are_never_printed(self):
        self.answer('{"ready":true,"version":"%s"}' % SHA)
        result = self.run_script(SHA)
        argv = self.run_argv()
        for key in ('DIARY_AUTH_TOKEN', 'UI_AUTH_TOKEN'):
            value = self.env_value(argv, key)
            self.assertGreaterEqual(len(value), 32)
            self.assertNotIn(value, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
