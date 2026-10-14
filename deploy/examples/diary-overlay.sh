#!/bin/bash
# Diary image overlay: FROM the running image, replace agent/ only (plus, when the release pins
# noevia-rs, the tenant-assertion binary built from that pin). Rolls back on any failure.
# Usage (on DaServer, as root): bash diary-overlay.sh <SRC_SHA>. SRC_SHA is an unpacked release
# under releases/ whose services/diary/agent is shipped; it also becomes the new Diary tag
# (cowork-diary:<SRC_SHA>) and DIARY_VERSION in .env. COWORK_VERSION and the web image are untouched.
# agent/ is replaced whole: files the release no longer has are removed (#1624).
# Use when only files under services/diary/agent changed since the running image (check
# requirements.txt and Dockerfile are unchanged): no pip install runs, so no dependency can drift.
# Keeps cowork-diary:rollback-before-diary-overlay and config/.env.bak.before-diary-<SRC_SHA>.
# Backup (#1487): the Diary state and .env are archived into a new diary_<SRC_SHA>_<UTC> folder under
# /mnt/disk3/noevia-backups. The Appdata Backup plugin is NOT run: it stops whichever containers its own
# configuration selects. Only cowork-diary-1 is ever stopped, and only while that archive is taken.
set -euo pipefail
# #1148: the only place allowed to build or tag cowork-diary:* (deploy/preflight/diary-image-guard.sh
# refuses it everywhere else).
export NOEVIA_DIARY_OVERLAY=1
V=${1:?source release sha (becomes DIARY_VERSION)}; base=/mnt/docker/appdata/cowork; config=$base/config/.env
# $V becomes a path component, an image tag and a sed replacement below: only a hex SHA is allowed.
[[ $V =~ ^[0-9a-f]{7,40}$ ]] || { echo "source release sha must be 7 to 40 lowercase hex characters, got: $V" >&2; exit 1; }
# BEGIN preflight-installed (deploy/tests/test_overlay_scripts.py runs this block)
# #1597: up.sh fails closed unless the rest of deploy/preflight is installed beside it. Check the installed
# copy before anything is built, stopped or changed, so a partial install cannot strand a service.
for f in up.sh diary-image-guard.sh check.php; do
  [ -f "$base/tools/preflight/$f" ] || { echo "$base/tools/preflight/$f is missing; install the whole deploy/preflight directory with deploy/preflight/install.sh; not deploying" >&2; exit 1; }
done
# END preflight-installed
cd /boot/config/plugins/compose.manager/projects/Cowork
OLD=$(sed -n 's/^DIARY_VERSION=//p' "$config")
[ -n "$OLD" ] || { echo "DIARY_VERSION is not set in $config; see docs/deployment.md 'Migrating an existing .env'"; exit 1; }
[ "$OLD" != "$V" ] || { echo "DIARY_VERSION is already $V"; exit 1; }
[ -d "$base/releases/$V/services/diary/agent" ] || { echo "no releases/$V/services/diary/agent"; exit 1; }
! docker image inspect cowork-diary:$V >/dev/null 2>&1 || { echo "cowork-diary:$V already exists; refusing to overwrite"; exit 1; }
OLD_ID=$(docker image inspect cowork-diary:$OLD --format '{{.Id}}')
RUN_ID=$(docker inspect cowork-diary-1 --format '{{.Image}}')
[ "$OLD_ID" = "$RUN_ID" ] || { echo "running Diary is not cowork-diary:$OLD"; exit 1; }
echo "current cowork-diary:$OLD $OLD_ID"
# The scoped backup below needs both; checked here so a bad layout fails before anything is built (#1487).
backup_root=${BACKUP_ROOT:-/mnt/disk3/noevia-backups}
[ -d "$backup_root" ] || { echo "backup root $backup_root is missing; not deploying" >&2; exit 1; }
[ -d "$base/state/diary" ] && [ -f "$config" ] || { echo "$base/state/diary or $config is missing; not deploying" >&2; exit 1; }
tmp=$(mktemp -d); ctx=$tmp/ctx; mkdir "$ctx"
# Set while cowork-diary-1 is stopped for the scoped backup (#1487). Cleared once the recreate below
# is the next step, because from then on rollback() owns the Diary container. Any earlier exit
# starts Diary again on the image .env still names (the old one), so a failed run never leaves it down.
diary_stopped=0
# Brings Diary back on the image .env names. If up.sh cannot run at all (#1597: an incomplete preflight
# install), the container is still the stopped, unchanged one: start it directly, but only while it is
# still the old image, so a half-recreated new container is never started by accident.
recover_diary() {
  bash "$base/tools/preflight/up.sh" --env-file "$config" -- -d --no-build --no-deps --wait --wait-timeout 180 diary >&2 && return 0
  if [ "$(docker inspect cowork-diary-1 --format '{{.Image}}' 2>/dev/null)" = "$OLD_ID" ]; then
    echo "up.sh could not run; starting the unchanged cowork-diary-1 directly" >&2
    docker start cowork-diary-1 >&2 && return 0
  fi
  return 1
}
on_exit() {
  rm -rf "$tmp"
  if [ "$diary_stopped" = 1 ]; then
    echo "restarting cowork-diary-1 on its previous image after an interrupted run" >&2
    recover_diary || echo "cowork-diary-1 did not restart; start it by hand (docker start cowork-diary-1)" >&2
  fi
}
trap on_exit EXIT
docker tag "$OLD_ID" cowork-diary:rollback-before-diary-overlay
cp -r "$base/releases/$V/services/diary/agent" "$ctx/agent"
# BEGIN rs-stage (deploy/tests/test_overlay_scripts.py runs this block on synthetic Dockerfiles)
# TENANT_ASSERTION_IMPL=rust needs the tenant-assertion binary. When the release's Diary Dockerfile
# pins noevia-rs (ARG NOEVIA_RS_REF / NOEVIA_RS_SHA256), build it here in the same pinned,
# checksum-verified Rust stage and copy only the binary in: no pip install, no Python change, the
# runtime layers stay the running image's. Only the two validated hex pins are taken from the
# release's Dockerfile, never any of its text.
diary_df=$base/releases/$V/services/diary/Dockerfile
rs_ref=$(sed -n 's/^ARG NOEVIA_RS_REF=//p' "$diary_df" 2>/dev/null | head -1 || true)
rs_sum=$(sed -n 's/^ARG NOEVIA_RS_SHA256=//p' "$diary_df" 2>/dev/null | head -1 || true)
if [ -z "$rs_ref$rs_sum" ]; then
  echo "release Diary Dockerfile pins no noevia-rs: no tenant-assertion binary (TENANT_ASSERTION_IMPL must stay python)"
  printf 'FROM cowork-diary:rollback-before-diary-overlay\nRUN rm -rf ./agent\nCOPY agent/ ./agent/\n' > "$ctx/Dockerfile"
  rs_stage=0
else
  [[ $rs_ref =~ ^[0-9a-f]{40}$ && $rs_sum =~ ^[0-9a-f]{64}$ ]] || { echo "release Diary Dockerfile noevia-rs pin is not a 40-hex ref and 64-hex sha256" >&2; exit 1; }
  cat > "$ctx/Dockerfile" <<DOCKERFILE
FROM rust:1.99-slim-bookworm@sha256:2c3a22f0a5533ea2dd5a16627bc841228151faa2d4de2644ac9987e4a2f1f2fa AS tenant-assertion
ENV RUSTUP_TOOLCHAIN=1.99.0 CARGO_TERM_COLOR=never
WORKDIR /src
ADD https://codeload.github.com/sbstndalton/noevia-rs/tar.gz/$rs_ref /tmp/noevia-rs.tar.gz
RUN echo "$rs_sum  /tmp/noevia-rs.tar.gz" | sha256sum -c - \\
 && tar -xzf /tmp/noevia-rs.tar.gz --strip-components=1 \\
 && rm /tmp/noevia-rs.tar.gz \\
 && cargo build --release --locked -p tenant-assertion-cli \\
 && ./target/release/tenant-assertion self-test | grep -qx ok
FROM cowork-diary:rollback-before-diary-overlay
COPY --from=tenant-assertion /src/target/release/tenant-assertion /usr/local/bin/tenant-assertion
RUN rm -rf ./agent
COPY agent/ ./agent/
DOCKERFILE
  rs_stage=1
  echo "tenant-assertion from noevia-rs $rs_ref"
fi
# END rs-stage
docker build -q -t cowork-diary:$V-candidate "$ctx" >/dev/null
docker run --rm --entrypoint python cowork-diary:$V-candidate -c "import agent.app, agent.workspace_files as w, agent.workspace_ops as o; assert hasattr(w,'_modified'); print('candidate imports ok')"
# BEGIN agent-exact (#1624: deploy/tests/test_overlay_scripts.py runs this through the whole script)
# COPY only adds and replaces, so the Dockerfile above deletes ./agent first. This proves the result: the
# candidate's /app/agent must hold exactly the release's files (names and sha256), nothing stale or missing.
agent_listing='find . -type f ! -path "*/__pycache__/*" -print0 | LC_ALL=C sort -z | xargs -0 -r sha256sum'
want=$(cd "$ctx/agent" && sh -c "$agent_listing")
got=$(docker run --rm --network none --entrypoint sh cowork-diary:$V-candidate -c "cd /app/agent && $agent_listing") \
  || { echo "could not list /app/agent in the candidate; not deploying" >&2; exit 1; }
if [ "$want" != "$got" ]; then
  echo "candidate /app/agent differs from releases/$V/services/diary/agent; not deploying:" >&2
  diff <(printf '%s\n' "$want") <(printf '%s\n' "$got") >&2 || true
  docker image rm cowork-diary:$V-candidate >/dev/null 2>&1 || true
  exit 1
fi
echo "candidate agent/ matches the release ($(printf '%s\n' "$want" | grep -c .) files)"
# END agent-exact
if [ "$rs_stage" = 1 ]; then
  docker run --rm --network none --entrypoint tenant-assertion cowork-diary:$V-candidate self-test | grep -qx ok || { echo "candidate tenant-assertion self-test failed; not deploying" >&2; exit 1; }
  echo "candidate tenant-assertion ok"
fi
cp -p "$config" "$config.bak.before-diary-$V"
# BEGIN diary-backup (deploy/tests/test_overlay_scripts.py runs this block through the whole script, with stub docker, gzip and php)
# Scoped backup (#1487): the Diary state directory and .env only, in a new folder that the Appdata Backup
# plugin never sees (no ab_ prefix). Nothing here stops or restarts any container but cowork-diary-1.
B="$backup_root/diary_${V}_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -m 700 "$B" || { echo "backup folder $B already exists; not deploying" >&2; exit 1; }
# Diary is stopped only while its SQLite files are copied, so they cannot change under the archive.
diary_stopped=1
docker stop --time 30 cowork-diary-1 >/dev/null
(umask 077; COPYFILE_DISABLE=1 tar -czf "$B/diary-appdata.tar.gz" -C "$base" state/diary config/.env)
gzip -t "$B/diary-appdata.tar.gz"
tar -tzf "$B/diary-appdata.tar.gz" > "$B/listing.txt"
grep -qx 'config/.env' "$B/listing.txt" && grep -qE '^state/diary(/|$)' "$B/listing.txt" \
  || { echo "backup $B does not list config/.env and state/diary; not deploying" >&2; exit 1; }
echo "backup $B"
echo "backup verified"
# END diary-backup
# Rollback: restore the .env (DIARY_VERSION=$OLD, whose image is untouched) and recreate Diary on it.
rollback() { echo "ROLLING BACK to cowork-diary:$OLD"; cp -p "$config.bak.before-diary-$V" "$config"; docker image rm cowork-diary:$V >/dev/null 2>&1 || true; recover_diary || echo "cowork-diary-1 is not running on cowork-diary:$OLD; start it by hand" >&2; exit 1; }
docker tag cowork-diary:$V-candidate cowork-diary:$V
sed -i "s/^DIARY_VERSION=.*/DIARY_VERSION=$V/" "$config"
diary_stopped=0
bash "$base/tools/preflight/up.sh" --env-file "$config" -- -d --no-build --no-deps --wait --wait-timeout 180 diary || rollback
! docker exec cowork-diary-1 python -c 'import socket; socket.gethostbyname("model-loader")' >/dev/null 2>&1 || { echo "diary can resolve model-loader"; rollback; }
docker exec cowork-web-1 node -e "fetch('http://diary:8010/api/health',{headers:{Authorization:'Bearer '+process.env.DIARY_AUTH_TOKEN}}).then(r=>{console.log('diary health via web',r.status);process.exit(r.ok?0:1)})" || rollback
docker inspect cowork-diary-1 --format 'diary {{.Config.Image}} {{.State.Health.Status}} restarts={{.RestartCount}} image={{.Image}}'
docker image rm cowork-diary:$V-candidate >/dev/null
echo DIARY_OVERLAY_COMPLETE
