#!/usr/bin/env bash
# #1148: release/build helpers refuse to build or tag cowork-diary:* outside diary-overlay.sh.
# Stubs docker with a PATH shim that logs every call; runs on macOS bash 3.2 and Linux.
set -u
here="$(cd -- "$(dirname -- "$0")" && pwd)"
guard="$here/../preflight/diary-image-guard.sh"
up="$here/../preflight/up.sh"
build="$here/build-web-release.sh"
work="$(mktemp -d "${TMPDIR:-/tmp}/diary-image-guard-test.XXXXXX")"
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin" "$work/ctx"
log="$work/calls"
cat > "$work/bin/docker" <<SHIM
#!/usr/bin/env bash
echo "\$*" >> "$log"
SHIM
chmod +x "$work/bin/docker"
export PATH="$work/bin:$PATH"
unset NOEVIA_DIARY_OVERLAY
# shellcheck source=../preflight/diary-image-guard.sh
. "$guard"

fails=0; passes=0
check() { if eval "$2"; then passes=$((passes+1)); echo "ok - $1"; else fails=$((fails+1)); echo "FAIL - $1"; fi; }
# expect <want-rc> <name> <argv...>: runs the guard on argv and checks its exit status.
expect() {
  local want="$1" name="$2"; shift 2
  guard_diary_image "$@" >/dev/null 2>&1; local rc=$?
  if [ "$rc" = "$want" ]; then passes=$((passes+1)); echo "ok - $name"; else fails=$((fails+1)); echo "FAIL - $name (rc=$rc want=$want)"; fi
}

# Images: diary tags are refused, every other tag is not.
expect 3 "docker build tagging cowork-diary:<sha> is refused" docker build -q -t cowork-diary:f6885a55 /ctx
expect 3 "docker build --tag=cowork-diary:<sha> is refused" docker build --tag=cowork-diary:f6885a55 /ctx
expect 3 "buildx build tagging cowork-diary is refused" docker buildx build -t cowork-diary:x /ctx
expect 3 "docker tag onto cowork-diary:rollback is refused" docker tag abc123 cowork-diary:rollback-before-diary-overlay
expect 3 "docker tag onto bare cowork-diary is refused" docker tag abc123 cowork-diary
expect 0 "docker build tagging cowork-web is allowed" docker build -f x -t cowork-web:682a45e --build-arg COWORK_VERSION=682a45e /ctx
expect 0 "docker tag of a diary image to another name is allowed" docker tag cowork-diary:f6885a55 cowork-web:backup
expect 0 "a cowork-diary-looking repo name is not a diary tag" docker build -t cowork-diary-tools:1 /ctx
expect 0 "a non-build docker command is allowed" docker image inspect cowork-diary:f6885a55

# Compose: a build with no service list, or with diary, builds the diary image.
expect 3 "compose build with no service list is refused" docker compose -f compose.yaml build
expect 3 "compose build diary is refused" docker compose --env-file .env build diary
expect 3 "compose build with diary among others is refused" docker compose build web diary
expect 0 "compose build of a named non-diary service is allowed" docker compose -f compose.yaml build web
expect 0 "compose build --build-arg value is not read as a service" docker compose build --build-arg X=1 web
expect 3 "compose build with only a value option has no service and is refused" docker compose build --build-arg X=1
expect 3 "compose up --build is refused" docker compose up -d --build
expect 3 "compose up --build for a named service is refused (web depends on diary)" docker compose up -d --build web
expect 3 "compose run --build is refused" docker compose --profile code run --build web
expect 0 "compose up without --build is allowed" docker compose up -d --no-build --no-deps --wait diary
expect 0 "compose up for a named service without --build is allowed" docker compose up -d web
expect 0 "compose config is allowed" docker compose -f compose.yaml config --format json
NOEVIA_DIARY_OVERLAY=1 guard_diary_image docker build -t cowork-diary:f6885a55-candidate /ctx >/dev/null 2>&1; rc=$?
check "the overlay marker allows a diary build and tag" '[ $rc -eq 0 ]'
NOEVIA_DIARY_OVERLAY=1 guard_diary_image docker compose build >/dev/null 2>&1; rc=$?
check "the overlay marker allows a compose build" '[ $rc -eq 0 ]'
guard_diary_image docker tag abc cowork-diary:x >/dev/null 2>&1; rc=$?
check "the guard refuses again once the marker is gone" '[ $rc -eq 3 ]'

# up.sh: refuses before it calls docker at all.
: > "$log"
bash "$up" -- -d --build >/dev/null 2>"$work/up.err"; rc=$?
check "up.sh refuses --build with rc 3" '[ $rc -eq 3 ]'
check "up.sh names the refusal" 'grep -q "refusing" "$work/up.err"'
check "up.sh made no docker call on refusal" '[ ! -s "$log" ]'
bash "$up" -- -d web >/dev/null 2>"$work/up.ok.err"
check "up.sh does not refuse a plain up" '! grep -q "refusing" "$work/up.ok.err"'
# With the guard file missing, up.sh fails closed.
mkdir -p "$work/preflight" && cp "$up" "$work/preflight/up.sh"
: > "$log"
bash "$work/preflight/up.sh" -- -d >/dev/null 2>"$work/missing.err"; rc=$?
check "up.sh fails closed without the guard file" '[ $rc -eq 2 ] && [ ! -s "$log" ]'

# build-web-release.sh: the release image name passes; the guard file is required.
sha=682a45e
printf 'NOEVIA_SHA=%s\n' "$sha" > "$work/ctx/release-refs"
mkdir -p "$work/ctx/noevia/build"; touch "$work/ctx/noevia/build/web.Dockerfile"
printf '{"version":"%s"}\n' "$sha" > "$work/versionjson"
cat > "$work/bin/docker" <<SHIM
#!/usr/bin/env bash
echo "\$*" >> "$log"
if [ "\$1" = run ]; then cat "$work/versionjson"; fi
SHIM
: > "$log"
bash "$build" "$sha" "$work/ctx" >/dev/null 2>&1; rc=$?
check "build-web-release.sh still builds cowork-web:<sha>" '[ $rc -eq 0 ] && grep -q -- "-t cowork-web:$sha" "$log"'
mkdir -p "$work/tools" && cp "$build" "$work/tools/build-web-release.sh"
: > "$log"
bash "$work/tools/build-web-release.sh" "$sha" "$work/ctx" >/dev/null 2>&1; rc=$?
check "build-web-release.sh fails closed without the guard file" '[ $rc -eq 2 ] && [ ! -s "$log" ]'

echo "passed=$passes failed=$fails"
[ "$fails" -eq 0 ]
