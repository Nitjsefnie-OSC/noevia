#!/usr/bin/env bash
# release-idle-jobs (#1391): an unreadable Coding job directory must make the release gate refuse,
# not read as "no jobs". Runs the gate against the pinned noevia-core jobs.cjs (release/versions.lock
# NOEVIA_CORE_REF, fetched shallowly; or NOEVIA_CORE_DIR=<checkout>) on synthetic state roots only,
# and through release-idle-jobs.sh with a stub `docker`. Needs node and git.
set -u
here="$(cd -- "$(dirname -- "$0")" && pwd)"
repo="$(cd -- "$here/../.." && pwd)"
gate="$here/release-idle-jobs.cjs"
work="$(mktemp -d "${TMPDIR:-/tmp}/idle-jobs-test.XXXXXX")"
trap 'chmod -R u+rwx "$work" 2>/dev/null; rm -rf "$work"' EXIT
fail=0; pass=0
check() { # name expected-status expected-line-regex -- command...
  local name="$1" want="$2" re="$3"; shift 4
  local got status
  got="$("$@" 2>"$work/stderr")"; status=$?
  if [[ "$status" == "$want" && "$got" =~ $re ]]; then pass=$((pass + 1)); echo "ok   $name"
  else fail=$((fail + 1)); echo "FAIL $name: status $status (want $want), output '$got'"; sed 's/^/     /' "$work/stderr" | head -5; fi
}

core="${NOEVIA_CORE_DIR:-}"
if [[ -z "$core" ]]; then
  ref="$(sed -n 's/^NOEVIA_CORE_REF=//p' "$repo/release/versions.lock")"
  [[ "$ref" =~ ^[0-9a-f]{40}$ ]] || { echo "FAIL no NOEVIA_CORE_REF in release/versions.lock"; exit 1; }
  core="$work/core"
  git init -q "$core" && git -C "$core" fetch -q --depth 1 https://github.com/sbstndalton/noevia-core "$ref" && git -C "$core" checkout -q FETCH_HEAD \
    || { echo "FAIL could not fetch noevia-core $ref"; exit 1; }
fi
jobs="$core/server/jobs.cjs"
[[ -f "$jobs" ]] || { echo "FAIL no $jobs"; exit 1; }
run() { node "$gate" --state-root "$1" --jobs-module "$jobs" "${@:2}"; }

user=11111111-2222-4333-8444-555555555555
mkroot() { local r="$work/$1"; mkdir -p "$r/users/$user"; echo "$r"; }
# A real job journal, written by core's own job store (synthetic project id).
addjob() { # account-dir: one new (queued) Coding job
  node -e '
    const { createJobs } = require(process.argv[1]);
    process.stdout.write(createJobs({ dir: process.argv[2], kinds: ["code"] }).create({ kind: "code", projectId: "qa-synthetic-project", capabilities: [] }));
  ' "$jobs" "$1"
}

empty="$(mkroot empty)"
check "no jobs directory anywhere is idle" 0 '^jobs_gate=idle accounts=1$' -- run "$empty"

active="$(mkroot active)"
addjob "$active/users/$user" >/dev/null
check "an active (queued) Coding job is busy" 2 '^jobs_gate=busy active=1$' -- run "$active"

if [[ "$(id -u)" != 0 ]]; then
  unreadable="$(mkroot unreadable)"
  mkdir -p "$unreadable/users/$user/jobs"; chmod 000 "$unreadable/users/$user/jobs"
  check "an unreadable account jobs directory is busy, not empty (#1391)" 2 '^jobs_gate=busy reason=job-state-unknown$' -- run "$unreadable"
  # The bug this replaces: the lenient list() the earlier cutover gates called reads it as no jobs.
  lenient="$(node -e 'const { createJobs } = require(process.argv[1]); process.stdout.write(String(createJobs({ dir: process.argv[2] }).list({ kind: "code" }).length));' "$jobs" "$unreadable/users/$user")"
  if [[ "$lenient" == 0 ]]; then pass=$((pass + 1)); echo "ok   control: lenient list() reads the same directory as 0 jobs"; else fail=$((fail + 1)); echo "FAIL control: lenient list() gave '$lenient'"; fi
  chmod 700 "$unreadable/users/$user/jobs"

  users_unreadable="$(mkroot users-unreadable)"
  chmod 000 "$users_unreadable/users"
  check "an unreadable users directory is busy" 2 '^jobs_gate=busy reason=users-unreadable$' -- run "$users_unreadable"
  chmod 700 "$users_unreadable/users"
else
  echo "skip unreadable cases: running as root"
fi

symlinked="$(mkroot symlinked)"
mkdir -p "$work/elsewhere"; ln -s "$work/elsewhere" "$symlinked/users/$user/jobs"
check "a symlinked jobs directory is busy" 2 '^jobs_gate=busy reason=job-state-unknown$' -- run "$symlinked"

linked_account="$(mkroot linked-account)"
ln -s "$work/elsewhere" "$linked_account/users/22222222-2222-4333-8444-555555555555"
check "an account entry that is a symlink is busy" 2 '^jobs_gate=busy reason=account-not-a-directory$' -- run "$linked_account"

corrupt="$(mkroot corrupt)"
mkdir -p "$corrupt/users/$user/jobs"; : > "$corrupt/users/$user/jobs/33333333-2222-4333-8444-555555555555.jsonl"
check "an empty job journal is busy" 2 '^jobs_gate=busy reason=job-state-unknown$' -- run "$corrupt"

many="$(mkroot many)"; mkdir -p "$many/users/44444444-2222-4333-8444-555555555555"
check "more accounts than the cap is busy" 2 '^jobs_gate=busy reason=too-many-accounts$' -- run "$many" --cap 1

check "a missing state root is busy" 2 '^jobs_gate=busy reason=state-root-unreadable$' -- run "$work/no-such-root"

# A job store that predates strict mode would read unknown state as empty: the gate refuses to run.
cat > "$work/lenient-jobs.cjs" <<'JS'
module.exports.createJobs = () => ({ list: () => [] });
JS
check "a job store without strict mode cannot pass the gate" 3 '^jobs_gate=error reason=job-store-not-strict$' -- node "$gate" --state-root "$empty" --jobs-module "$work/lenient-jobs.cjs"
check "no job store cannot pass the gate" 3 '^jobs_gate=error reason=no-job-store$' -- node "$gate" --state-root "$empty" --jobs-module "$work/missing.cjs"

# Through the wrapper: a stub docker runs the piped script with node and the synthetic root.
mkdir -p "$work/bin"
cat > "$work/bin/docker" <<SHIM
#!/usr/bin/env bash
[ "\$1" = exec ] || exit 1
shift; [ "\$1" = -i ] && shift; [ "\$1" = cowork-web-1 ] || exit 125
[ -n "\${STUB_HANG:-}" ] && exec sleep 5
node - --state-root "\$STUB_ROOT" --jobs-module "$jobs"
SHIM
chmod +x "$work/bin/docker"
# The wrapper calls timeout(1) (coreutils; on CI). Without it (a Mac) a pass-through stands in.
if ! command -v timeout >/dev/null; then printf '#!/usr/bin/env bash\nshift; exec "$@"\n' > "$work/bin/timeout"; chmod +x "$work/bin/timeout"; fi
check "wrapper: idle passes" 0 '^jobs_gate=idle' -- env PATH="$work/bin:$PATH" STUB_ROOT="$empty" bash "$here/release-idle-jobs.sh"
check "wrapper: busy refuses" 2 '^jobs_gate=busy' -- env PATH="$work/bin:$PATH" STUB_ROOT="$symlinked" bash "$here/release-idle-jobs.sh"
check "wrapper: a docker failure is an error, never idle" 3 '^jobs_gate=error reason=exec-failed$' -- env PATH="$work/bin:$PATH" STUB_ROOT="$empty" bash "$here/release-idle-jobs.sh" --container no-such

# A hung docker exec refuses (timeout's 124 is mapped to 3); a fake `timeout` keeps the test fast.
mkdir -p "$work/hangbin"; cp "$work/bin/docker" "$work/hangbin/docker"
cat > "$work/hangbin/timeout" <<'SHIM'
#!/usr/bin/env bash
[ "$1" = 60 ] || exit 99
shift; "$@" & pid=$!; ( sleep 1; kill "$pid" 2>/dev/null ) & w=$!
wait "$pid"; s=$?; kill "$w" 2>/dev/null
[ "$s" -ge 128 ] && exit 124; exit "$s"
SHIM
chmod +x "$work/hangbin/timeout"
check "wrapper: a hung docker exec is refused after the timeout" 3 '^jobs_gate=error reason=timeout$' -- env PATH="$work/hangbin:$PATH" STUB_ROOT="$empty" STUB_HANG=1 bash "$here/release-idle-jobs.sh"

echo "release-idle-jobs: $pass passed, $fail failed"
[[ "$fail" == 0 ]]
