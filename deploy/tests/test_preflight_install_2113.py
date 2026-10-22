"""#2113: deploy/preflight/install.sh must not silently replace a locally extended up.sh.

An installed up.sh is replaced without asking only when it is byte-identical to the new one or to a released
version (up.sh.released-sha256). Anything else holds local edits: the install stops before it copies a thing, and
an explicit --replace-local-up-sh keeps the old file as up.sh.local-<UTC time>.bak first. Every path here is a
temporary directory; the sources are copies of the real preflight directory with synthetic up.sh contents.
"""
import hashlib
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / 'deploy/preflight'
FILES = ['up.sh', 'diary-image-guard.sh', 'check.php', 'diary-models-check.sh', 'web-env-keys.txt', 'install.sh',
         'up.sh.released-sha256']

LOCAL_STEP = '\n# local step: refresh the host firewall allow-list after the container gets a new address\ntrue\n'


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class InstallTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = pathlib.Path(tempfile.mkdtemp(prefix='noevia-install-2113-'))
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        self.src = self.temp / 'src'
        self.src.mkdir()
        for name in FILES:
            shutil.copy(PREFLIGHT / name, self.src / name)
        self.dest = self.temp / 'dest'

    def set_new_up(self, text, released=()):
        """Make `text` the up.sh to install and `released` (older contents) the released versions."""
        (self.src / 'up.sh').write_text(text)
        lines = ['# synthetic released list'] + [f'{sha(t)}  synthetic' for t in released]
        (self.src / 'up.sh.released-sha256').write_text('\n'.join(lines) + '\n')

    def install(self, *args, dest=True):
        argv = ['bash', str(self.src / 'install.sh'), *(([str(self.dest)] if dest else [])), *args]
        return subprocess.run(argv, capture_output=True, text=True, timeout=30)

    def installed(self, name='up.sh'):
        return (self.dest / name).read_text()

    def backups(self):
        return sorted(p.name for p in self.dest.glob('up.sh.local-*.bak'))

    def seed(self, up_text, others='old'):
        """An existing installation: up.sh plus the other files with recognisable old contents."""
        self.dest.mkdir()
        (self.dest / 'up.sh').write_text(up_text)
        for name in ('diary-image-guard.sh', 'check.php', 'diary-models-check.sh'):
            (self.dest / name).write_text(f'# {others} {name}\n')


class Replacement(InstallTestCase):
    def test_a_first_install_needs_no_flag_and_no_list(self):
        (self.src / 'up.sh.released-sha256').unlink()
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.installed(), (self.src / 'up.sh').read_text())
        self.assertEqual(self.backups(), [])

    def test_the_same_up_sh_is_reinstalled_without_a_flag(self):
        self.assertEqual(self.install().returncode, 0)
        again = self.install()
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(self.backups(), [])

    def test_an_older_released_up_sh_is_upgraded_without_a_flag(self):
        self.set_new_up('#!/bin/bash\n# new\n', released=['#!/bin/bash\n# older release\n'])
        self.seed('#!/bin/bash\n# older release\n')
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.installed(), '#!/bin/bash\n# new\n')
        self.assertEqual(self.installed('check.php'), (self.src / 'check.php').read_text())
        self.assertEqual(self.backups(), [])

    def test_a_locally_extended_up_sh_refuses_and_changes_nothing(self):
        released = '#!/bin/bash\n# older release\n'
        self.set_new_up('#!/bin/bash\n# new\n', released=[released])
        self.seed(released + LOCAL_STEP)
        before = {p.name: p.read_text() for p in self.dest.iterdir()}
        result = self.install()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(f'{self.dest}/up.sh is not a released version of up.sh', result.stderr)
        self.assertIn('--replace-local-up-sh', result.stderr)
        self.assertIn('diff ', result.stderr)
        self.assertEqual({p.name: p.read_text() for p in self.dest.iterdir()}, before, 'nothing was copied, backed up or removed')
        self.assertEqual(self.installed(), released + LOCAL_STEP)

    def test_the_real_up_sh_with_a_local_step_appended_refuses(self):
        self.assertEqual(self.install().returncode, 0)
        with (self.dest / 'up.sh').open('a') as handle:
            handle.write(LOCAL_STEP)
        edited = self.installed()
        result = self.install()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.installed(), edited)
        self.assertEqual(self.backups(), [])

    def test_the_flag_keeps_the_local_file_and_then_installs_everything(self):
        released = '#!/bin/bash\n# older release\n'
        self.set_new_up('#!/bin/bash\n# new\n', released=[released])
        self.seed(released + LOCAL_STEP)
        result = self.install('--replace-local-up-sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        backups = self.backups()
        self.assertEqual(len(backups), 1, backups)
        self.assertRegex(backups[0], r'^up\.sh\.local-\d{8}T\d{6}Z\.bak$')
        self.assertEqual(self.installed(backups[0]), released + LOCAL_STEP, 'the local steps are kept byte for byte')
        self.assertEqual(self.installed(), '#!/bin/bash\n# new\n')
        for name in ('diary-image-guard.sh', 'check.php', 'diary-models-check.sh'):
            self.assertEqual(self.installed(name), (self.src / name).read_text(), name)
        self.assertIn(backups[0], result.stdout)

    def test_the_flag_may_follow_or_precede_the_destination(self):
        self.set_new_up('#!/bin/bash\n# new\n')
        for argv in (('--replace-local-up-sh', str(self.dest)), (str(self.dest), '--replace-local-up-sh')):
            with self.subTest(argv=argv):
                shutil.rmtree(self.dest, ignore_errors=True)
                self.seed('#!/bin/bash\n# something local\n')
                result = subprocess.run(['bash', str(self.src / 'install.sh'), *argv], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(len(self.backups()), 1)

    def test_the_flag_makes_no_backup_when_nothing_local_is_replaced(self):
        released = '#!/bin/bash\n# older release\n'
        self.set_new_up('#!/bin/bash\n# new\n', released=[released])
        self.seed(released)
        self.assertEqual(self.install('--replace-local-up-sh').returncode, 0)
        self.assertEqual(self.backups(), [])
        shutil.rmtree(self.dest)
        self.assertEqual(self.install('--replace-local-up-sh').returncode, 0, 'a first install with the flag is fine')
        self.assertEqual(self.backups(), [])

    def test_without_the_released_list_a_differing_up_sh_is_treated_as_local(self):
        self.set_new_up('#!/bin/bash\n# new\n')
        (self.src / 'up.sh.released-sha256').unlink()
        self.seed('#!/bin/bash\n# older release\n')
        refused = self.install()
        self.assertEqual(refused.returncode, 1)
        self.assertIn('up.sh.released-sha256', refused.stderr)
        self.assertEqual(self.installed(), '#!/bin/bash\n# older release\n')
        self.assertEqual(self.install('--replace-local-up-sh').returncode, 0)
        self.assertEqual(len(self.backups()), 1)

    def test_an_unreadable_looking_list_line_or_comment_never_matches(self):
        local = '#!/bin/bash\n# local\n'
        self.set_new_up('#!/bin/bash\n# new\n')
        (self.src / 'up.sh.released-sha256').write_text(f'# {sha(local)}\n\nnot-a-hash\n{sha(local)[:40]}\n')
        self.seed(local)
        self.assertEqual(self.install().returncode, 1)

    def test_a_partial_source_still_fails_before_the_up_sh_decision(self):
        self.seed('#!/bin/bash\n# local\n')
        (self.src / 'check.php').unlink()
        result = self.install()
        self.assertEqual(result.returncode, 1)
        self.assertIn('check.php is missing', result.stderr)
        self.assertEqual(self.backups(), [])

    def test_an_unknown_option_is_a_usage_error_and_changes_nothing(self):
        self.seed('#!/bin/bash\n# local\n')
        result = self.install('--force')
        self.assertEqual(result.returncode, 2)
        self.assertIn('usage', result.stderr)
        self.assertEqual(self.installed(), '#!/bin/bash\n# local\n')
        extra = subprocess.run(['bash', str(self.src / 'install.sh'), str(self.dest), str(self.dest)], capture_output=True, text=True, timeout=30)
        self.assertEqual(extra.returncode, 2)


class ReleasedList(unittest.TestCase):
    """The list that makes ordinary upgrades quiet must keep up with up.sh."""

    def entries(self):
        text = (PREFLIGHT / 'up.sh.released-sha256').read_text()
        return [l.split()[0] for l in text.splitlines() if l.strip() and not l.lstrip().startswith('#')]

    def test_every_entry_is_a_sha256(self):
        entries = self.entries()
        self.assertTrue(entries)
        for entry in entries:
            self.assertRegex(entry, r'^[0-9a-f]{64}$')
        self.assertEqual(len(entries), len(set(entries)))

    def test_the_current_up_sh_is_listed(self):
        current = hashlib.sha256((PREFLIGHT / 'up.sh').read_bytes()).hexdigest()
        self.assertIn(current, self.entries(),
                      'append the sha256 of deploy/preflight/up.sh to deploy/preflight/up.sh.released-sha256 whenever up.sh changes')

    def test_the_installer_and_the_readme_document_the_override(self):
        self.assertIn('--replace-local-up-sh', (PREFLIGHT / 'install.sh').read_text())
        readme = (PREFLIGHT / 'README.md').read_text()
        self.assertIn('--replace-local-up-sh', readme)
        self.assertIn('up.sh.local-<UTC time>.bak', readme)
        self.assertTrue(re.search(r'up\.sh\.released-sha256', readme))


if __name__ == '__main__':
    unittest.main()
