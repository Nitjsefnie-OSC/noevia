#!/usr/bin/env bash
# Synthetic candidate boot of a web image (#1416): no network, read-only root, all capabilities
# dropped, tmpfs for everything writable, throwaway tokens. It proves the image starts and answers
# GET /api/ready with the release sha before anything is switched. The container is removed on exit.
#
# Usage: candidate-boot.sh <release-sha> [image]
#   image defaults to cowork-web:<sha>.
#   CANDIDATE_FRONT=rust        the only front since sbstndalton/noevia#1071 (the web supervisor
#                               refuses node); booted with NOEVIA_RUST_AUTH=1 and NOEVIA_RUST_PROJECTS=1.
#   CANDIDATE_WAIT_SECONDS=N    bound on the readiness wait (default 120).
#
# Runs on the Docker host. Nothing here reads .env, and the throwaway tokens are never printed.
set -euo pipefail
sha="${1:-}"
if [[ ! "$sha" =~ ^[0-9a-f]{7,40}$ ]]; then
  echo "usage: candidate-boot.sh <release-sha> [image]" >&2
  exit 2
fi
image="${2:-cowork-web:$sha}"
front="${CANDIDATE_FRONT:-rust}"
case "$front" in
  rust) ;;
  node) echo "candidate-boot: the node front is gone (sbstndalton/noevia#1071); the web supervisor refuses it" >&2; exit 2 ;;
  *) echo "candidate-boot: CANDIDATE_FRONT must be rust" >&2; exit 2 ;;
esac
wait_s="${CANDIDATE_WAIT_SECONDS:-120}"
if [[ ! "$wait_s" =~ ^[0-9]+$ ]]; then
  echo "candidate-boot: CANDIDATE_WAIT_SECONDS must be a whole number of seconds" >&2
  exit 2
fi

name="cowork-candidate-$sha-$$"
# The data dir must be writable on a tmpfs. Startup runs mkdirSync(UI_DATA_DIR) and then writes the
# sqlite database and the secrets key there. The image default (/app/server/ui-data) sits on the
# read-only root, so without UI_DATA_DIR the candidate exits at startup with EROFS.
data_root="/candidate-data"
data_dir="$data_root/ui-data"
random_token() { head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n'; }
diary_token="$(random_token)"
ui_token="$(random_token)"

cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$name" \
  --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
  --tmpfs /tmp:size=64m,mode=1777 \
  --tmpfs "$data_root:size=256m,mode=0777" \
  -e UI_DATA_DIR="$data_dir" \
  -e UI_PORT=8021 \
  -e NOEVIA_FRONT="$front" \
  -e NOEVIA_RUST_AUTH=1 \
  -e NOEVIA_RUST_PROJECTS=1 \
  -e PUBLIC_ORIGIN=http://127.0.0.1:8021 \
  -e LEGACY_AUTH_COMPAT=false \
  -e DIARY_AUTH_TOKEN="$diary_token" \
  -e UI_AUTH_TOKEN="$ui_token" \
  "$image" >/dev/null

# The probe runs inside the container (the network is disabled, so the host cannot reach it).
probe='fetch("http://127.0.0.1:"+(process.env.UI_PORT||8021)+"/api/ready",{signal:AbortSignal.timeout(4000)})'
probe+='.then(r=>r.text()).then(t=>console.log(t)).catch(()=>process.exit(1))'
deadline=$(( $(date +%s) + wait_s ))
body=""
ready=0
while :; do
  if [ "$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null || echo false)" != true ]; then
    break
  fi
  body="$(docker exec "$name" node -e "$probe" 2>/dev/null || true)"
  if grep -q '"ready":true' <<<"$body" && grep -q "\"version\":\"$sha\"" <<<"$body"; then
    ready=1
    break
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    break
  fi
  sleep 2
done

# Count, never print, the log lines: they can carry paths and request detail.
errors="$(docker logs "$name" 2>&1 | grep -Eci 'error|EROFS|FATAL' || true)"
if [ "$ready" = 1 ]; then
  echo "ok: $image ready at $sha ($body), error lines: $errors (front $front)"
  exit 0
fi
echo "error: $image not ready at $sha within ${wait_s}s (front $front, last answer: ${body:-none}, error lines: $errors)" >&2
exit 1
