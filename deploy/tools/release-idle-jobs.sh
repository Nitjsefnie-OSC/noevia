#!/usr/bin/env bash
# Coding-job idle gate for a release cutover (#1391). Runs release-idle-jobs.cjs inside the live web
# container, against the image's own jobs.cjs in strict mode: an unreadable or unknown job
# directory is BUSY, never empty. Use it in every cutover's gate block:
#   bash deploy/tools/release-idle-jobs.sh || { echo "GATE_FAIL jobs"; exit 2; }
#   release-idle-jobs.sh [--container NAME]      (default cowork-web-1)
# Exit status: 0 idle, 2 busy or unknown state, 3 the gate cannot run (treat as busy), 64 usage.
# Prints one jobs_gate=... line; never account ids, paths or job contents. Read-only.
set -uo pipefail
here="$(cd -- "$(dirname -- "$0")" && pwd)"
container=cowork-web-1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --container) [[ $# -ge 2 ]] || { sed -n '2,8p' "$0" >&2; exit 64; }; container="$2"; shift ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 64 ;;
  esac
  shift
done
docker exec -i "$container" node - < "$here/release-idle-jobs.cjs"
status=$?
case "$status" in
  0|2|3) exit "$status" ;;
  *) echo "jobs_gate=error reason=exec-failed"; exit 3 ;;
esac
