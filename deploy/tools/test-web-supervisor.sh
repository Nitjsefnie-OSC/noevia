#!/usr/bin/env bash
# Tests build/web-supervisor.sh (the web image entrypoint) with stub `node` and noevia-server
# processes. Needs bash >= 4.3 (wait -n), like the image; skips on macOS's bash 3.2. CI runs it on
# Linux.
#
# sbstndalton/noevia#1071: sign-in and the account and the front read routes are the Rust front's
# permanently, so the supervisor starts nothing unless NOEVIA_FRONT=rust, NOEVIA_RUST_PROJECTS=1 and
# a noevia-server whose --features lists rust-auth and every front route feature. NOEVIA_RUST_AUTH is
# retired: whatever its value, it changes nothing and reaches neither process.
set -u
here="$(cd -- "$(dirname -- "$0")" && pwd)"
sup="$here/../../build/web-supervisor.sh"
if [ "${BASH_VERSINFO[0]}" -lt 4 ] || { [ "${BASH_VERSINFO[0]}" -eq 4 ] && [ "${BASH_VERSINFO[1]}" -lt 3 ]; }; then
  echo "skip - bash ${BASH_VERSION} has no wait -n (the image's bash does)"; exit 0
fi
work="$(mktemp -d "${TMPDIR:-/tmp}/web-supervisor-test.XXXXXX")"
trap 'rm -rf "$work"' EXIT
fails=0; passes=0
check() { if eval "$2"; then passes=$((passes+1)); echo "ok - $1"; else fails=$((fails+1)); echo "FAIL - $1"; fi; }

# The features build/web-supervisor.sh requires (FRONT_ROUTE_FEATURES), and a front that has them.
ROUTE_FEATURES="rust-chatgpt-status rust-storage-reads rust-storage-browse rust-export rust-free-chats rust-usage rust-stats rust-routing-default rust-sampling-settings rust-reasoning-settings rust-routing-mode"
BASE_FEATURES="code-net-guard rust-auth rust-projects $ROUTE_FEATURES"
RETIRED="NOEVIA_RUST_AUTH NOEVIA_RUST_USAGE NOEVIA_RUST_SAMPLING_SETTINGS NOEVIA_RUST_REASONING_SETTINGS NOEVIA_RUST_ROUTING_MODE NOEVIA_RUST_ROUTING_DEFAULT NOEVIA_RUST_STATS NOEVIA_RUST_EXPORT NOEVIA_RUST_CHATGPT_STATUS NOEVIA_RUST_STORAGE_READS NOEVIA_RUST_STORAGE_BROWSE"

mkdir -p "$work/bin"
# Each stub records its environment, then lives until killed or until its "die" file appears.
stub() {
  cat > "$1" <<STUB
#!/usr/bin/env bash
name=$2
if [ "\${1:-}" = --features ]; then printf '%s\\n' \${STUB_FEATURES-$BASE_FEATURES}; exit 0; fi
[ "\$name" = node ] && [ -n "\${STUB_NODE_DELAY:-}" ] && sleep "\$STUB_NODE_DELAY"
echo "\$name UI_HOST=\${UI_HOST:-} UI_PORT=\${UI_PORT:-} UPSTREAM=\${NOEVIA_LEGACY_UPSTREAM:-} ARGS=\$* CCONF=\${NOEVIA_RUST_PROJECT_CHATS_CONFIRMED:-} FCONF=\${NOEVIA_RUST_FREE_CHATS_CONFIRMED:-} PCONF=\${NOEVIA_RUST_PROJECTS_CONFIRMED:-} CONF=\${NOEVIA_RUST_AUTH_CONFIRMED:-}" >> "$work/log"
retired=""
for v in $RETIRED; do c="\${v}_CONFIRMED"; [ -n "\${!c:-}" ] && retired="\$retired \$c"; done
echo "\$name RETIRED=\$retired" >> "$work/log"
echo "\$name WCONF=\${NOEVIA_RUST_PROJECT_WRITES_CONFIRMED:-}" >> "$work/log"
echo "\$name SSTORE=\${NOEVIA_RUST_PROJECT_STORE_CONFIRMED:-} SPORT=\${NOEVIA_PROJECT_STORE_PORT:-} STOKLEN=\${#NOEVIA_PROJECT_STORE_TOKEN}" >> "$work/log"
echo "\$name AUTH=\${NOEVIA_RUST_AUTH-unset}" >> "$work/log"
echo "\$name KCONF=\${NOEVIA_FRONT_CLIENT_IP:-}" >> "$work/log"
trap 'echo "\$name TERM" >> "$work/log"; exit 0' TERM
# The supervisor TERMs the survivor as soon as one child exits. A front told to die at once would
# race Node's startup logging (Node killed mid-write, its later lines lost: #1822), so a dying
# front waits (bounded) until Node's last startup line is in the log.
if [ "\$name" = front ] && [ -f "$work/die-front" ]; then
  for _ in \$(seq 1 200); do grep -q "^node KCONF=" "$work/log" 2>/dev/null && break; sleep 0.05; done
fi
for _ in \$(seq 1 300); do
  [ -f "$work/die-\$name" ] && { echo "\$name died" >> "$work/log"; exit 3; }
  sleep 0.05
done
STUB
  chmod +x "$1"
}
stub "$work/bin/node" node
stub "$work/noevia-server" front
export PATH="$work/bin:$PATH"
# The live deployment; a test overrides any of it by naming the key again (env: last one wins).
run() { (cd "$work" && env NOEVIA_FRONT=rust NOEVIA_RUST_PROJECTS=1 NOEVIA_SERVER_BIN="$work/noevia-server" "$@" bash "$sup"); }
reset() { : > "$work/log"; rm -f "$work"/die-* "$work/rc"; }
wait_log() { for _ in $(seq 1 100); do grep -q "$1" "$work/log" 2>/dev/null && return 0; sleep 0.05; done; return 1; }
without() { local out="" f; for f in $BASE_FEATURES; do [ "$f" = "$1" ] || out="$out $f"; done; echo "$out"; }

# --- Fail closed before either process starts -----------------------------------------------
reset
run NOEVIA_FRONT= >/dev/null 2>"$work/err"; rc=$?
check "the image default (node) is refused, nothing started" '[ $rc -eq 2 ] && grep -q "NOEVIA_FRONT=node is no longer supported" "$work/err" && [ ! -s "$work/log" ]'
reset
run NOEVIA_FRONT=node >/dev/null 2>"$work/err"; rc=$?
check "NOEVIA_FRONT=node is refused, nothing started" '[ $rc -eq 2 ] && grep -q "#1071" "$work/err" && [ ! -s "$work/log" ]'
reset
run NOEVIA_FRONT=bogus >/dev/null 2>"$work/err"; rc=$?
check "an unknown NOEVIA_FRONT is refused" '[ $rc -eq 2 ] && grep -q "must be rust" "$work/err" && [ ! -s "$work/log" ]'
for missing in "NOEVIA_RUST_PROJECTS=" "NOEVIA_RUST_PROJECTS=0" "NOEVIA_RUST_PROJECTS=true"; do
  reset
  run "$missing" >/dev/null 2>"$work/err"; rc=$?
  check "$missing is refused, nothing started" '[ $rc -eq 2 ] && grep -q "NOEVIA_RUST_PROJECTS=1 is required" "$work/err" && [ ! -s "$work/log" ]'
done
# A Node front cannot be selected by turning the retired sign-in switch off either.
for value in "" 0 1; do
  reset
  run NOEVIA_FRONT=node NOEVIA_RUST_AUTH="$value" >/dev/null 2>"$work/err"; rc=$?
  check "NOEVIA_FRONT=node with NOEVIA_RUST_AUTH='$value' is refused, nothing started" '[ $rc -eq 2 ] && grep -q "NOEVIA_FRONT=node is no longer supported" "$work/err" && [ ! -s "$work/log" ]'
done
reset
run NOEVIA_SERVER_BIN="$work/missing" >/dev/null 2>"$work/err"; rc=$?
check "no noevia-server binary is refused, nothing started" '[ $rc -eq 2 ] && grep -q "no noevia-server" "$work/err" && [ ! -s "$work/log" ]'
reset
run STUB_FEATURES="$(without code-net-guard)" COWORK_CODE_NET_ADDR=egress >/dev/null 2>"$work/err"; rc=$?
check "COWORK_CODE_NET_ADDR with a front without the guard is refused" '[ $rc -eq 2 ] && grep -q "no code-net-guard" "$work/err" && [ ! -s "$work/log" ]'
reset
run STUB_FEATURES="$(without rust-auth)" >/dev/null 2>"$work/err"; rc=$?
check "a front without rust-auth is refused, nothing started" '[ $rc -eq 2 ] && grep -q "no rust-auth" "$work/err" && [ ! -s "$work/log" ]'
reset
run STUB_FEATURES="$(without rust-projects)" >/dev/null 2>"$work/err"; rc=$?
check "a front without rust-projects is refused, nothing started" '[ $rc -eq 2 ] && grep -q "no rust-projects" "$work/err" && [ ! -s "$work/log" ]'
reset
run STUB_FEATURES= >/dev/null 2>"$work/err"; rc=$?
check "a front whose --features prints nothing is refused" '[ $rc -eq 2 ] && [ ! -s "$work/log" ]'
# #1071: every front route feature is required; a missing one fails closed and is named.
for feature in $ROUTE_FEATURES; do
  reset
  run STUB_FEATURES="$(without "$feature")" >/dev/null 2>"$work/err"; rc=$?
  check "a front without $feature is refused, nothing started" '[ $rc -eq 2 ] && grep -q "lacks the front route feature(s): $feature;" "$work/err" && [ ! -s "$work/log" ]'
done
reset
run STUB_FEATURES="code-net-guard rust-auth rust-projects rust-usage" >/dev/null 2>"$work/err"; rc=$?
check "every missing feature is listed at once" '[ $rc -eq 2 ] && grep -q "rust-chatgpt-status rust-storage-reads rust-storage-browse rust-export rust-free-chats rust-stats" "$work/err" && [ ! -s "$work/log" ]'
reset
run UI_PORT=65000 >/dev/null 2>&1; rc=$?
check "a UI_PORT with no room for +1000 is refused" '[ $rc -eq 2 ] && [ ! -s "$work/log" ]'

# --- The live configuration ------------------------------------------------------------------
reset; touch "$work/die-front"
retired_env=(); for v in $RETIRED; do retired_env+=("$v=1" "${v}_CONFIRMED=1"); done
run "${retired_env[@]}" UI_PORT=8021 >/dev/null 2>"$work/err"; rc=$?
check "a full front starts both; Node gets the projects and free-chat confirmations and no auth confirmation" 'grep -q "^node .* FCONF=1 PCONF=1 CONF=$" "$work/log" && grep -q "^front .* CCONF= FCONF= PCONF= CONF=$" "$work/log"'
check "no retired confirmation reaches either process, inherited or not" 'grep -q "^node RETIRED=$" "$work/log" && grep -q "^front RETIRED=$" "$work/log"'
check "a leftover retired switch earns a warning and changes nothing" 'grep -q "NOEVIA_RUST_STATS is retired" "$work/err" && grep -q "NOEVIA_RUST_EXPORT is retired" "$work/err" && grep -q "NOEVIA_RUST_AUTH is retired" "$work/err"'
check "the retired sign-in switch reaches neither process" 'grep -q "^node AUTH=unset$" "$work/log" && grep -q "^front AUTH=unset$" "$work/log"'
check "...and the run itself went ahead" '[ $rc -eq 3 ]'

# #1071: no NOEVIA_RUST_AUTH at all (the switch is retired): the front still owns sign-in and both start.
reset; touch "$work/die-front"
run >/dev/null 2>"$work/err"; rc=$?
check "without NOEVIA_RUST_AUTH both start, with no warning about it" '[ $rc -eq 3 ] && grep -q "^node AUTH=unset$" "$work/log" && ! grep -q "NOEVIA_RUST_AUTH" "$work/err"'

# M4's chat-list slice (#1409): confirmed to Node only for a front that lists rust-project-chats.
reset; touch "$work/die-front"
run NOEVIA_RUST_PROJECT_CHATS_CONFIRMED=1 >/dev/null 2>&1
check "a front without rust-project-chats leaves the chat list to Node; an inherited confirmation is dropped" 'grep -q "^node .* CCONF= FCONF=1 " "$work/log"'
reset; touch "$work/die-front"
run STUB_FEATURES="$BASE_FEATURES rust-project-chats" >/dev/null 2>&1
check "a front with rust-project-chats has the chat slice confirmed to Node only" 'grep -q "^node .* CCONF=1 FCONF=1 PCONF=1 CONF=$" "$work/log" && grep -q "^front .* CCONF= " "$work/log"'

# The project writes (#1264): their own switch over the confirmed project slice and the compiled
# rust-project-writes; never confirmed by NOEVIA_RUST_PROJECTS=1 alone (live today).
WRITES_FEATURES="$BASE_FEATURES rust-project-chats rust-project-writes"
reset; touch "$work/die-front"
run STUB_FEATURES="$WRITES_FEATURES" >/dev/null 2>&1
check "NOEVIA_RUST_PROJECTS=1 alone never confirms the project writes" 'grep -q "^node WCONF=$" "$work/log"'
reset
run NOEVIA_RUST_PROJECT_WRITES=1 >/dev/null 2>"$work/err"; rc=$?
check "project writes missing the native feature refuse before startup" '[ $rc -eq 2 ] && grep -q "no rust-project-writes" "$work/err" && [ ! -s "$work/log" ]'
reset; touch "$work/die-front"
run NOEVIA_RUST_PROJECT_WRITES=1 STUB_FEATURES="$WRITES_FEATURES" >/dev/null 2>&1
check "project writes confirmed only to Node after the native probe" 'grep -q "^node WCONF=1$" "$work/log" && grep -q "^front WCONF=$" "$work/log"'
reset; touch "$work/die-front"
run NOEVIA_RUST_PROJECT_WRITES_CONFIRMED=1 STUB_FEATURES="$WRITES_FEATURES" >/dev/null 2>&1
check "an inherited project-writes confirmation is dropped" 'grep -q "^node WCONF=$" "$work/log"'

# The project store (#1264): a per-start secret and UI_PORT+2000 for both processes, confirmed to
# Node only; never from the environment; refused without project-store.
reset; touch "$work/die-front"
run UI_PORT=8021 STUB_FEATURES="$BASE_FEATURES project-store" NOEVIA_PROJECT_STORE_TOKEN=inherited-secret-0123456789abcdef0123456789 NOEVIA_PROJECT_STORE_PORT=1 NOEVIA_RUST_PROJECT_STORE_CONFIRMED=1 >/dev/null 2>&1
check "store off (live today): no store, and inherited store values are dropped" 'grep -q "^node SSTORE= SPORT= STOKLEN=0$" "$work/log" && grep -q "^front SSTORE= SPORT= STOKLEN=0$" "$work/log"'
reset; touch "$work/die-front"
run UI_PORT=8021 NOEVIA_RUST_PROJECT_STORE=1 STUB_FEATURES="$BASE_FEATURES project-store" >/dev/null 2>&1
check "store on: Node is confirmed, both get UI_PORT+2000 and a fresh 64-character secret" 'grep -q "^node SSTORE=1 SPORT=10021 STOKLEN=64$" "$work/log" && grep -q "^front SSTORE= SPORT=10021 STOKLEN=64$" "$work/log"'
reset
run NOEVIA_RUST_PROJECT_STORE=1 >/dev/null 2>"$work/err"; rc=$?
check "store on with a front without project-store is refused, nothing started" '[ $rc -eq 2 ] && grep -q "no project-store" "$work/err" && [ ! -s "$work/log" ]'

# The client address (noevia-core server/auth.cjs, #1578): Node is told to believe X-Noevia-Client-Ip
# only when the front reports client-address-header (it strips client copies of the header).
reset; touch "$work/die-front"
run STUB_FEATURES="$BASE_FEATURES client-address-header" >/dev/null 2>&1
check "a front with client-address-header confirms the client address to Node only" 'grep -q "^node KCONF=1$" "$work/log" && grep -q "^front KCONF=$" "$work/log"'
reset; touch "$work/die-front"
run NOEVIA_FRONT_CLIENT_IP=1 >/dev/null 2>"$work/err"
check "a front without it leaves Node unconfirmed (an inherited value is dropped) and still starts" 'grep -q "^node KCONF=$" "$work/log" && grep -q "no client-address-header" "$work/err"'

# #1822 regression: a front that dies at once must not cut a slow-starting Node's startup log short
# (the supervisor TERMs the survivor the moment one child exits).
reset; touch "$work/die-front"
run STUB_NODE_DELAY=0.4 >/dev/null 2>&1
check "a front dying at once does not truncate a slow Node's startup log" 'grep -q "^node WCONF=$" "$work/log" && grep -q "^node KCONF=" "$work/log"'

# --- Process lifecycle -----------------------------------------------------------------------
reset
(run UI_PORT=8021 UI_HOST=0.0.0.0 COWORK_DAV_PORT=0 >/dev/null 2>"$work/err"; echo $? > "$work/rc") &
wait_log "^front" && wait_log "^node"
check "Node on loopback UI_PORT+1000" 'grep -q "^node UI_HOST=127.0.0.1 UI_PORT=9021 " "$work/log"'
check "the front on UI_HOST:UI_PORT with Node as upstream" 'grep -q "^front UI_HOST=0.0.0.0 UI_PORT=8021 UPSTREAM=http://127.0.0.1:9021 " "$work/log"'
touch "$work/die-front"
for _ in $(seq 1 100); do [ -s "$work/rc" ] && break; sleep 0.05; done
check "the front dying stops Node" 'grep -q "^node TERM" "$work/log"'
check "...and the container exits non-zero" '[ "$(cat "$work/rc")" = 3 ]'

reset
(run UI_PORT=8021 >/dev/null 2>&1; echo $? > "$work/rc") &
wait_log "^front" && wait_log "^node"
touch "$work/die-node"
for _ in $(seq 1 100); do [ -s "$work/rc" ] && break; sleep 0.05; done
check "Node dying stops the front, non-zero exit" 'grep -q "^front TERM" "$work/log" && [ "$(cat "$work/rc")" = 3 ]'

reset
(cd "$work" && exec env NOEVIA_FRONT=rust NOEVIA_RUST_PROJECTS=1 NOEVIA_SERVER_BIN="$work/noevia-server" UI_PORT=8021 COWORK_DAV_PORT=8040 bash "$sup" >/dev/null 2>"$work/err") &
pid=$!
wait_log "^front" && wait_log "^node"
check "with DAV on, Node keeps UI_HOST (default 0.0.0.0) and says so" 'grep -q "^node UI_HOST=0.0.0.0 UI_PORT=9021 " "$work/log" && grep -q "not loopback only" "$work/err"'
kill -TERM "$pid"; wait "$pid"; rc=$?
check "docker stop (SIGTERM) stops both and exits 0" '[ $rc -eq 0 ] && grep -q "^node TERM" "$work/log" && grep -q "^front TERM" "$work/log"'

echo "passed $passes, failed $fails"
[ "$fails" -eq 0 ]
