"""Guards in the live-server overlay scripts that can be exercised without Docker or the server.

The release SHA becomes a path component, an image tag and a sed replacement, so both scripts
refuse anything but a hex SHA before touching anything. The Diary overlay archives its own state
(#1487) and may stop or recreate only the Diary container; it never runs the Appdata Backup plugin.
"""
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
OVERLAY = ROOT / 'deploy/examples/overlay-release.sh'
DIARY = ROOT / 'deploy/examples/diary-overlay.sh'
RCLONE = ROOT / 'deploy/offsite/rclone-sync.sh'

BAD_SHAS = ['', 'ABCDEF1', 'abc12', 'abc123g', '../../etc', 'abc1234;touch x', 'abc1234 x', '$(id)', 'a' * 41]


def run(script, *args, **env):
    return subprocess.run(['bash', str(script), *args], env=dict(os.environ, **env),
                          capture_output=True, text=True, timeout=30)


class ShaValidation(unittest.TestCase):
    def test_overlay_release_rejects_non_sha_arguments_before_any_work(self):
        for bad in BAD_SHAS:
            for args in [('abc1234', bad), (bad, 'abc1234')]:
                with self.subTest(args=args):
                    result = run(OVERLAY, *args)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertTrue('hex characters' in result.stderr or 'release sha' in result.stderr, result.stderr)

    def test_diary_overlay_rejects_non_sha_argument_before_any_work(self):
        for bad in BAD_SHAS:
            with self.subTest(sha=bad):
                result = run(DIARY, bad)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue('hex characters' in result.stderr or 'source release sha' in result.stderr, result.stderr)

    def test_a_valid_sha_gets_past_validation(self):
        # Fails later (no server layout here), but never with the validation message.
        for script, args in [(OVERLAY, ('abc1234', 'def5678')), (DIARY, ('def5678',))]:
            self.assertNotIn('hex characters', run(script, *args).stderr)

    def test_overlay_release_tolerates_missing_engine_and_model_loader(self):
        text = OVERLAY.read_text()
        # No bare inspect of the optional containers: the engine goes through container_id, which
        # treats only "No such object" as absent (tested below).
        for line in text.splitlines():
            if 'docker inspect cowork-llama-1' in line:
                self.fail(f'bare inspect of the optional engine: {line}')
        self.assertIn('old_native=$(container_id cowork-llama-1) || exit 1', text)
        self.assertNotIn('cowork-model-loader-1 \\', text)

    def test_engine_probe_runs_before_the_release_changes_anything(self):
        text = OVERLAY.read_text()
        probe = text.index('old_native=$(container_id')
        for change in ['mkdir -p "$base/releases/$NEW"', 'docker build', 'ln -sfn', 'sed -i']:
            self.assertLess(probe, text.index(change), change)


class AssembledSource(unittest.TestCase):
    """#952: the release folder comes from the assembled tarball, checked before it is unpacked."""

    def test_overlay_takes_the_assembled_tarball_not_a_git_archive(self):
        text = OVERLAY.read_text()
        self.assertNotIn('src-$NEW', text)
        self.assertIn('src="/tmp/noevia-release-$NEW.tar.gz"', text)

    def test_release_refs_sha_is_checked_before_the_release_folder_exists(self):
        text = OVERLAY.read_text()
        check = text.index('[ "$src_sha" = "$NEW" ]')
        self.assertLess(text.index('tar -xzOf "$src" release-refs'), check)
        self.assertLess(check, text.index('mkdir -p "$base/releases/$NEW"'))
        self.assertLess(check, text.index('docker build'))

    def test_release_refs_check_rejects_a_tree_for_another_sha(self):
        # Run the overlay's own release-refs lines against synthetic tarballs.
        lines = OVERLAY.read_text().splitlines()
        start = next(i for i, l in enumerate(lines) if l.startswith('src="/tmp/noevia-release-$NEW.tar.gz"'))
        block = '\n'.join(lines[start:start + 4]).replace('/tmp/noevia-release-$NEW.tar.gz', '$TARBALL')
        with tempfile.TemporaryDirectory(prefix='noevia-overlay-src-') as temp:
            tree = pathlib.Path(temp) / 'tree'
            tree.mkdir()
            for sha, expect_ok in [('def5678', True), ('abc1234', False)]:
                (tree / 'release-refs').write_text(f'NOEVIA_SHA={sha}\nNOEVIA_WEB_SHA={"a" * 40}\n')
                tarball = pathlib.Path(temp) / f'{sha}.tar.gz'
                subprocess.run(['tar', '-czf', str(tarball), '-C', str(tree), 'release-refs'], check=True)
                result = subprocess.run(['bash', '-c', 'set -euo pipefail\nNEW=def5678\n' + block + '\necho CHECKED'],
                                        env=dict(os.environ, TARBALL=str(tarball)), capture_output=True, text=True, timeout=30)
                with self.subTest(sha=sha):
                    self.assertEqual('CHECKED' in result.stdout, expect_ok, result.stderr)
                    if not expect_ok:
                        self.assertIn('not deploying', result.stderr)


ID = 'a1b2c3d4e5f60718293a4b5c6d7e8f90' * 2


class ContainerId(unittest.TestCase):
    """Run the `container-id` block of overlay-release.sh against a fake `docker` on PATH."""

    def block(self):
        lines = OVERLAY.read_text().splitlines()
        start = next(i for i, l in enumerate(lines) if l.startswith('# BEGIN container-id'))
        end = next(i for i, l in enumerate(lines) if l.startswith('# END container-id'))
        return '\n'.join(lines[start + 1:end])

    def probe(self, docker_body):
        with tempfile.TemporaryDirectory(prefix='noevia-fake-docker-') as temp:
            fake = pathlib.Path(temp) / 'docker'
            fake.write_text('#!/bin/bash\n' + docker_body + '\n')
            fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
            script = 'set -euo pipefail\n' + self.block() + '\nold=$(container_id cowork-llama-1) || exit 1\necho "ID=[$old]"'
            return subprocess.run(['bash', '-c', script], env=dict(os.environ, PATH=f'{temp}:{os.environ["PATH"]}'),
                                  capture_output=True, text=True, timeout=30)

    def test_returns_the_id_of_an_existing_container(self):
        result = self.probe(f'echo {ID}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f'ID=[{ID}]', result.stdout)

    def test_a_cli_warning_next_to_the_id_is_not_part_of_the_id(self):
        result = self.probe(f'echo "WARNING: a deprecated flag" >&2; echo {ID}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f'ID=[{ID}]', result.stdout)

    def test_unexpected_success_output_stops_the_release_and_is_reported(self):
        for body in ['echo sha256:abc123', 'echo "WARNING: only a warning"', 'echo ' + ID.upper(), 'echo ' + ID[:-1],
                     f'echo {ID}; echo {ID[::-1]}', 'true']:
            with self.subTest(body=body):
                result = self.probe(body)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('unexpected output', result.stderr)
                self.assertIn('not deploying', result.stderr)
                self.assertNotIn('ID=[', result.stdout)

    def test_a_missing_container_is_absent_not_an_error(self):
        for message in ['Error: No such object: cowork-llama-1', 'Error response from daemon: No such container: cowork-llama-1']:
            with self.subTest(message=message):
                result = self.probe(f'echo "{message}" >&2; exit 1')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('ID=[]', result.stdout)

    def test_any_other_inspect_failure_stops_with_the_docker_error(self):
        for message in ['Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?',
                        'permission denied while trying to connect to the Docker daemon socket', 'context deadline exceeded']:
            with self.subTest(message=message):
                result = self.probe(f'echo "{message}" >&2; exit 1')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertIn('not deploying', result.stderr)
                self.assertNotIn('ID=[', result.stdout)

    def test_a_failure_without_any_output_is_still_an_error(self):
        result = self.probe('exit 1')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('ID=[', result.stdout)


class RcloneJsonEscape(unittest.TestCase):
    def escape(self, value):
        text = RCLONE.read_text()
        start = text.index('json_escape() {')
        func = text[start:text.index('\n}\n', start) + 3]
        out = subprocess.run(['bash', '-c', func + '\njson_escape "$1"', 'x', value], capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout

    def test_every_c0_control_quote_and_backslash_round_trips_through_json(self):
        value = 'a"b\\c' + ''.join(chr(i) for i in range(1, 32)) + 'z\x7f'
        escaped = self.escape(value)
        self.assertFalse(any(ord(c) < 32 for c in escaped), repr(escaped))
        self.assertEqual(json.loads('"' + escaped + '"'), value)

    def test_plain_text_is_unchanged(self):
        self.assertEqual(self.escape('gdrive:noevia backups'), 'gdrive:noevia backups')


class ScopedDiaryOverlay(unittest.TestCase):
    """#1487: diary-overlay.sh runs end to end against a synthetic appdata tree.

    Paths are pointed at a temp tree; docker, php and gzip are stubs on PATH that record their argv
    (gzip can be told to fail `-t`). The real preflight up.sh runs and reaches the stubbed docker
    compose. Only cowork-diary-1 may be stopped, restarted or recreated, and the Appdata Backup plugin
    never runs. Every value is synthetic.
    """

    NEW = 'abc1234'
    OLD = 'def5678'
    OLD_ID = 'sha256:' + 'a' * 64
    LIFECYCLE = {'stop', 'start', 'restart', 'kill', 'rm', 'down', 'pause', 'unpause', 'update'}

    DOCKER_STUB = r"""
printf 'docker %s\n' "$*" >> "$CALL_LOG"
case "$*" in
  "image inspect cowork-diary:@NEW@") exit 1 ;;
  "image inspect cowork-diary:@OLD@ --format {{.Id}}") echo "@OLD_ID@" ;;
  "inspect cowork-diary-1 --format {{.Image}}") echo "@OLD_ID@" ;;
  "inspect cowork-diary-1 --format diary"*) echo "diary healthy restarts=0" ;;
  "exec cowork-diary-1 python -c"*) exit 1 ;;
  "run --rm --entrypoint python"*) echo "candidate imports ok" ;;
  "compose "*" config --format json") echo "{}" ;;
esac
exit 0
"""
    PHP_STUB = r"""
printf 'php %s\n' "$*" >> "$CALL_LOG"
cat >/dev/null
exit 0
"""
    GZIP_STUB = r"""
for arg in "$@"; do
  if [ "$arg" = -t ] && [ -n "${INJECT_GZIP_FAILURE:-}" ]; then echo "gzip: injected failure" >&2; exit 1; fi
done
exec "@REAL_GZIP@" "$@"
"""

    # The script's `sed -i EXPR FILE` is GNU syntax (DaServer, CI). BSD sed (macOS) needs `-i ''`, so the
    # test shim adds it only when the real sed is BSD; the script text is never changed for the test.
    SED_STUB = r"""
if [ "$1" = -i ] && ! "@REAL_SED@" --version >/dev/null 2>&1; then shift; exec "@REAL_SED@" -i '' "$@"; fi
exec "@REAL_SED@" "$@"
"""

    def setUp(self):
        self.temp = pathlib.Path(tempfile.mkdtemp(prefix='noevia-diary-overlay-'))
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        self.base = self.temp / 'appdata'
        self.manager = self.temp / 'manager'
        self.backups = self.temp / 'backups'
        self.bin = self.temp / 'bin'
        self.log = self.temp / 'calls.log'
        for d in [self.base / 'config', self.base / 'state/diary/users/u1', self.base / 'state/web',
                  self.base / 'tools/preflight', self.base / f'releases/{self.NEW}/services/diary/agent',
                  self.manager, self.backups, self.bin]:
            d.mkdir(parents=True)
        self.config = self.base / 'config/.env'
        self.config.write_text(f'COWORK_VERSION=0000000\nDIARY_VERSION={self.OLD}\nDIARY_AUTH_TOKEN=synthetic-token\n')
        (self.base / 'state/diary/users/u1/managed-diary.db').write_bytes(b'synthetic diary state')
        (self.base / 'state/web/cowork.db').write_bytes(b'synthetic web state')
        (self.base / f'releases/{self.NEW}/services/diary/agent/app.py').write_text('x = 1\n')
        (self.base / f'releases/{self.NEW}/services/diary/Dockerfile').write_text('FROM python:3.12-slim\n')
        (self.manager / 'compose.yaml').write_text('services: {}\n')
        shutil.copy(ROOT / 'deploy/preflight/up.sh', self.base / 'tools/preflight/up.sh')
        subst = {'@NEW@': self.NEW, '@OLD@': self.OLD, '@OLD_ID@': self.OLD_ID,
                 '@REAL_GZIP@': shutil.which('gzip') or '/usr/bin/gzip', '@REAL_SED@': shutil.which('sed') or '/usr/bin/sed'}
        self.stub('docker', self.DOCKER_STUB, subst)
        self.stub('php', self.PHP_STUB, subst)
        self.stub('gzip', self.GZIP_STUB, subst)
        self.stub('sed', self.SED_STUB, subst)
        text = DIARY.read_text()
        for old, new in [('base=/mnt/docker/appdata/cowork;', f"base='{self.base}';"),
                         ('cd /boot/config/plugins/compose.manager/projects/Cowork', f"cd '{self.manager}'")]:
            self.assertEqual(text.count(old), 1, old)
            text = text.replace(old, new)
        self.script = self.temp / 'diary-overlay.sh'
        self.script.write_text(text)

    def stub(self, name, body, subst):
        for token, value in subst.items():
            body = body.replace(token, value)
        path = self.bin / name
        path.write_text('#!/bin/bash\n' + body)
        path.chmod(0o755)

    def overlay(self, backups=None, env=None):
        environ = dict(os.environ, PATH=f'{self.bin}:{os.environ["PATH"]}', CALL_LOG=str(self.log),
                       BACKUP_ROOT=str(backups or self.backups), COWORK_PROJECT_DIR=str(self.manager))
        environ.pop('INJECT_GZIP_FAILURE', None)
        environ.update(env or {})
        return subprocess.run(['bash', str(self.script), self.NEW], env=environ, capture_output=True, text=True, timeout=60)

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def assert_only_diary_is_disturbed(self, calls):
        for line in calls:
            self.assertNotIn('appdata.backup', line, line)
            argv = line.split()
            if argv[0] == 'php':
                continue
            self.assertEqual(argv[0], 'docker', line)
            verb = argv[1]
            if verb == 'compose':
                self.assertEqual(argv[2:4], ['--env-file', str(self.config)], line)
                sub = argv[4]
                if sub == 'up':
                    self.assertIn('--no-deps', argv, line)
                    self.assertEqual(argv[-1], 'diary', line)
                else:
                    self.assertEqual(sub, 'config', f'compose {sub} is not allowed in the Diary overlay: {line}')
            elif verb in self.LIFECYCLE:
                self.assertEqual(argv[-1], 'cowork-diary-1', f'{verb} must name only the Diary container: {line}')
            if 'cowork-web-1' in line:
                self.assertEqual(verb, 'exec', f'web may only be read through docker exec: {line}')

    def test_success_stops_and_recreates_only_diary_and_archives_only_diary_state(self):
        result = self.overlay()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('DIARY_OVERLAY_COMPLETE', result.stdout)
        calls = self.calls()
        self.assert_only_diary_is_disturbed(calls)
        stops = [c for c in calls if c.startswith('docker stop')]
        self.assertEqual(stops, ['docker stop --time 30 cowork-diary-1'])
        ups = [c for c in calls if c.startswith('docker compose') and ' up ' in c]
        self.assertEqual(len(ups), 1, ups)
        self.assertTrue(ups[0].endswith(' diary'), ups[0])
        self.assertLess(calls.index(stops[0]), calls.index(ups[0]))
        self.assertIn(f'DIARY_VERSION={self.NEW}', self.config.read_text())
        # No Appdata Backup plugin folder, and one diary_<SHA>_<UTC> folder holding only Diary state and .env.
        self.assertEqual(list(self.backups.glob('ab_*')), [])
        folders = list(self.backups.iterdir())
        self.assertEqual(len(folders), 1, folders)
        self.assertRegex(folders[0].name, rf'^diary_{self.NEW}_\d{{8}}T\d{{6}}Z$')
        with tarfile.open(folders[0] / 'diary-appdata.tar.gz') as archive:
            names = archive.getnames()
        self.assertIn('config/.env', names)
        self.assertIn('state/diary/users/u1/managed-diary.db', names)
        self.assertFalse([n for n in names if n.startswith('state/web')], names)

    def test_a_failed_archive_restarts_diary_on_the_old_image_and_leaves_the_env_alone(self):
        result = self.overlay(env={'INJECT_GZIP_FAILURE': '1'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('restarting cowork-diary-1', result.stderr)
        calls = self.calls()
        self.assert_only_diary_is_disturbed(calls)
        stop = calls.index('docker stop --time 30 cowork-diary-1')
        ups = [i for i, c in enumerate(calls) if c.startswith('docker compose') and ' up ' in c]
        self.assertEqual(len(ups), 1, calls)
        self.assertGreater(ups[0], stop)
        self.assertIn(f'DIARY_VERSION={self.OLD}', self.config.read_text())
        self.assertFalse([c for c in calls if c.startswith('docker tag') and c.endswith(f'cowork-diary:{self.NEW}')])

    def test_a_missing_backup_root_fails_before_anything_is_built_or_stopped(self):
        result = self.overlay(backups=self.temp / 'absent')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('backup root', result.stderr)
        self.assertIn('not deploying', result.stderr)
        calls = self.calls()
        self.assert_only_diary_is_disturbed(calls)
        self.assertFalse([c for c in calls if c.startswith(('docker stop', 'docker build', 'docker compose'))], calls)
        self.assertIn(f'DIARY_VERSION={self.OLD}', self.config.read_text())

    def test_the_script_text_has_no_plugin_call_and_no_stack_wide_command(self):
        text = DIARY.read_text()
        self.assertNotIn('backup.php', text)
        self.assertNotIn('appdata.backup', text)
        for line in text.splitlines():
            if line.lstrip().startswith('#'):
                continue
            if re.search(r'\bdocker (stop|restart|kill|rm|down|pause)\b', line) or re.search(r'\bcompose\b.*\b(down|stop|restart|kill|rm)\b', line):
                self.assertIn('cowork-diary-1', line, line)


class RsStage(unittest.TestCase):
    """Run the `rs-stage` block of diary-overlay.sh against synthetic release Dockerfiles."""

    REF = 'a' * 40
    SUM = 'b' * 64

    def block(self):
        lines = DIARY.read_text().splitlines()
        start = next(i for i, l in enumerate(lines) if l.startswith('# BEGIN rs-stage'))
        end = next(i for i, l in enumerate(lines) if l.startswith('# END rs-stage'))
        return '\n'.join(lines[start + 1:end])

    def stage(self, dockerfile):
        temp = pathlib.Path(tempfile.mkdtemp(prefix='noevia-rs-stage-'))
        (temp / 'releases/abc1234/services/diary').mkdir(parents=True)
        if dockerfile is not None:
            (temp / 'releases/abc1234/services/diary/Dockerfile').write_text(dockerfile)
        (temp / 'ctx').mkdir()
        script = 'set -euo pipefail\nbase=$1; V=abc1234; ctx=$1/ctx\n' + self.block() + '\necho "STAGE $rs_stage"'
        result = subprocess.run(['bash', '-c', script, 'x', str(temp)], capture_output=True, text=True, timeout=30)
        out = (temp / 'ctx/Dockerfile').read_text() if (temp / 'ctx/Dockerfile').exists() else None
        return result, out

    def test_a_pinned_release_builds_the_binary_from_exactly_that_pin(self):
        result, df = self.stage(f'FROM rust AS x\nARG NOEVIA_RS_REF={self.REF}\nARG NOEVIA_RS_SHA256={self.SUM}\nRUN pip install evil\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('STAGE 1', result.stdout)
        self.assertIn(f'tar.gz/{self.REF} ', df)
        self.assertIn(f'echo "{self.SUM}  /tmp/noevia-rs.tar.gz" | sha256sum -c - \\\n', df)
        self.assertIn('cargo build --release --locked -p tenant-assertion-cli', df)
        # The builder image is pinned by registry digest, not a movable tag (#1145).
        self.assertRegex(df, r'(?m)^FROM rust:1\.99-slim-bookworm@sha256:[0-9a-f]{64} AS tenant-assertion$')
        self.assertNotRegex(df, r'(?m)^FROM rust:[^@\n]* AS')
        self.assertIn('COPY --from=tenant-assertion /src/target/release/tenant-assertion /usr/local/bin/tenant-assertion', df)
        self.assertTrue(df.rstrip().endswith('COPY agent/ ./agent/'))
        # Only the pins are taken from the release's Dockerfile; never its text, and no pip.
        self.assertNotIn('pip', df)
        self.assertEqual(df.count('FROM cowork-diary:rollback-before-diary-overlay'), 1)

    def test_an_unpinned_release_keeps_the_agent_only_overlay(self):
        for dockerfile in ('FROM python:3.12-slim\nCOPY agent/ ./agent/\n', None):
            with self.subTest(dockerfile=dockerfile):
                result, df = self.stage(dockerfile)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('STAGE 0', result.stdout)
                self.assertEqual(df, 'FROM cowork-diary:rollback-before-diary-overlay\nCOPY agent/ ./agent/\n')

    def test_a_malformed_pin_stops_before_any_build(self):
        for ref, digest in [('a' * 39, self.SUM), (self.REF, 'B' * 64), (self.REF + ';id', self.SUM), (self.REF, ''),
                            ('', self.SUM), ('$(id)' + 'a' * 35, self.SUM)]:
            with self.subTest(ref=ref, digest=digest):
                result, df = self.stage(f'ARG NOEVIA_RS_REF={ref}\nARG NOEVIA_RS_SHA256={digest}\n')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('not a 40-hex ref', result.stderr)
                self.assertIsNone(df)


if __name__ == '__main__':
    unittest.main()
