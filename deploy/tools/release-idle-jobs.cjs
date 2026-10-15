'use strict';
// The Coding-job part of a release idle gate (#1391). Runs with the web image's own job store:
//   docker exec -i cowork-web-1 node - < deploy/tools/release-idle-jobs.cjs
// (release-idle-jobs.sh does exactly that). Enumerates the state root and every account directory
// under users/ with core jobs.cjs list({ strict: true }) (noevia-core#99), so a job directory that
// cannot be read exactly is BUSY, never "no jobs". Only an absent jobs directory counts as empty.
//
// Prints one line and exits:
//   0  jobs_gate=idle accounts=<n>
//   2  jobs_gate=busy active=<n>                 an active Coding job
//   2  jobs_gate=busy reason=<why>               unknown job state (unreadable, symlink, corrupt, cap)
//   3  jobs_gate=error reason=<why>              the gate itself cannot run (no strict job store)
// Never prints account ids, paths or job contents. Never touches job state: it never creates,
// recovers, prunes or cancels a job (it calls only list(); the strictness probe uses a temp dir).
//
// Options (tests): --state-root DIR (default $UI_DATA_DIR), --jobs-module FILE (default
// /app/server/jobs.cjs), --cap N (directories under users/, default 4096).
const fs = require('fs');
const os = require('os');
const path = require('path');

const args = process.argv.slice(2).filter((a) => a !== '-');
const opt = (name, fallback) => { const i = args.indexOf(name); return i >= 0 && i + 1 < args.length ? args[i + 1] : fallback; };
const stateRoot = opt('--state-root', process.env.UI_DATA_DIR || '');
const jobsModule = opt('--jobs-module', '/app/server/jobs.cjs');
const cap = Number(opt('--cap', '4096'));

const out = (line, code) => { process.stdout.write(`${line}\n`); process.exit(code); };
const busy = (reason) => out(`jobs_gate=busy reason=${reason}`, 2);
const error = (reason) => out(`jobs_gate=error reason=${reason}`, 3);

if (!stateRoot) error('no-state-root');
if (!Number.isInteger(cap) || cap < 1) error('bad-cap');

let createJobs;
try { ({ createJobs } = require(jobsModule)); } catch { error('no-job-store'); }
if (typeof createJobs !== 'function') error('no-job-store');

// The job store must refuse unknown state. An image whose jobs.cjs predates strict mode would
// silently read an unreadable directory as empty: prove strictness on a synthetic directory first.
(function proveStrict() {
  const probe = fs.mkdtempSync(path.join(os.tmpdir(), 'noevia-idle-probe-'));
  try {
    fs.mkdirSync(path.join(probe, 'jobs', '00000000-0000-4000-8000-000000000000.jsonl'), { recursive: true });
    let refused = false;
    try { createJobs({ dir: probe }).list({ strict: true }); } catch (e) { refused = e && e.code === 'JOBS_UNKNOWN'; }
    if (!refused) error('job-store-not-strict');
  } finally { fs.rmSync(probe, { recursive: true, force: true }); }
})();

// The account directories: the state root (legacy single-user data) and users/<id>. Anything under
// users/ that is not a plain directory, or a users/ that cannot be read, is unknown state.
const dirs = [stateRoot];
let rootStat;
try { rootStat = fs.lstatSync(stateRoot); } catch { busy('state-root-unreadable'); }
if (!rootStat.isDirectory()) busy('state-root-not-a-directory');
const usersDir = path.join(stateRoot, 'users');
let usersStat = null;
try { usersStat = fs.lstatSync(usersDir); } catch (e) { if (e.code !== 'ENOENT') busy('users-unreadable'); }
if (usersStat) {
  if (!usersStat.isDirectory()) busy('users-not-a-directory');
  let entries;
  try { entries = fs.readdirSync(usersDir, { withFileTypes: true }); } catch { busy('users-unreadable'); }
  if (entries.length > cap) busy('too-many-accounts');
  for (const d of entries) {
    if (!d.isDirectory()) busy('account-not-a-directory');
    dirs.push(path.join(usersDir, d.name));
  }
}

let active = 0;
for (const dir of dirs) {
  let jobs;
  try { jobs = createJobs({ dir }).list({ kind: 'code', strict: true }); }
  catch (e) { busy(e && e.code === 'JOBS_UNKNOWN' ? 'job-state-unknown' : 'job-read-failed'); }
  active += jobs.filter((j) => !['completed', 'failed', 'cancelled', 'interrupted'].includes(j.status)).length;
}
if (active) out(`jobs_gate=busy active=${active}`, 2);
out(`jobs_gate=idle accounts=${dirs.length - 1}`, 0);
