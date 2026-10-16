#!/usr/bin/env bash
# The web image's entrypoint (full-Rust migration M1, docs/adr-0001-rust-and-repo-split.md
# "Amendment 2026-10-10"). noevia-server (noevia-rs bins/noevia-server) faces the network on
# UI_HOST:UI_PORT, Node behind it on UI_PORT+1000 (NOEVIA_LEGACY_UPSTREAM). The front answers the
# routes noevia-rs contracts/http/routes.toml gives to Rust and streams the rest to Node.
#
# sbstndalton/noevia#1071: the front read routes (usage, sampling and reasoning settings, routing
# mode and default, engine statistics, ChatGPT status, connected-storage metadata/list/read and the
# conversation export) and sign-in and the account (rust-auth) are the Rust front's permanently;
# Node no longer has them, and the deployment switch NOEVIA_RUST_AUTH is retired. So the image runs
# only with NOEVIA_FRONT=rust, NOEVIA_RUST_PROJECTS=1 (the export reads the free-chat list from
# disk) and a noevia-server whose --features lists rust-auth and every front route feature
# (FRONT_ROUTE_FEATURES). Anything else stops here, non-zero, before either process starts.
# NOEVIA_FRONT=node is refused for the same reason: Node alone would answer those routes 503.
# If either process exits, the other is stopped and the container exits non-zero, so Docker's
# restart policy brings both back together.
set -uo pipefail

# Only this script may confirm rust-projects / rust-project-chats / rust-free-chats to Node
# (below); never trust a value from the environment. (The retired confirmations, rust-auth's and the
# front routes', are scrubbed too, so an inherited value can never reach a Node of either age.)
unset NOEVIA_RUST_AUTH_CONFIRMED NOEVIA_RUST_PROJECTS_CONFIRMED NOEVIA_RUST_PROJECT_CHATS_CONFIRMED NOEVIA_RUST_FREE_CHATS_CONFIRMED NOEVIA_RUST_USAGE_CONFIRMED NOEVIA_RUST_SAMPLING_SETTINGS_CONFIRMED NOEVIA_RUST_REASONING_SETTINGS_CONFIRMED NOEVIA_RUST_ROUTING_MODE_CONFIRMED NOEVIA_RUST_ROUTING_DEFAULT_CONFIRMED NOEVIA_RUST_STATS_CONFIRMED NOEVIA_RUST_EXPORT_CONFIRMED NOEVIA_RUST_STORAGE_READS_CONFIRMED NOEVIA_RUST_STORAGE_BROWSE_CONFIRMED NOEVIA_RUST_CHATGPT_STATUS_CONFIRMED NOEVIA_RUST_PROJECT_WRITES_CONFIRMED NOEVIA_RUST_PROJECT_STORE_CONFIRMED NOEVIA_PROJECT_STORE_PORT NOEVIA_PROJECT_STORE_TOKEN NOEVIA_FRONT_CLIENT_IP
FRONT_ROUTE_FEATURES="rust-chatgpt-status rust-storage-reads rust-storage-browse rust-export rust-free-chats rust-usage rust-stats rust-routing-default rust-sampling-settings rust-reasoning-settings rust-routing-mode"
# Their old switches only earn a warning now (noevia-server says the same), and neither process
# gets them.
for retired in NOEVIA_RUST_AUTH NOEVIA_RUST_USAGE NOEVIA_RUST_SAMPLING_SETTINGS NOEVIA_RUST_REASONING_SETTINGS NOEVIA_RUST_ROUTING_MODE \
  NOEVIA_RUST_ROUTING_DEFAULT NOEVIA_RUST_STATS NOEVIA_RUST_EXPORT NOEVIA_RUST_CHATGPT_STATUS NOEVIA_RUST_STORAGE_READS \
  NOEVIA_RUST_STORAGE_BROWSE; do
  if [ -n "${!retired+set}" ]; then
    echo "web-supervisor: $retired is retired (sbstndalton/noevia#1071) and ignored; remove it from the environment" >&2
    unset "$retired"
  fi
done
front="${NOEVIA_FRONT:-node}"
case "$front" in
  rust) ;;
  node) echo "web-supervisor: NOEVIA_FRONT=node is no longer supported: the Rust front owns sign-in and routes Node no longer has (sbstndalton/noevia#1071); set NOEVIA_FRONT=rust and NOEVIA_RUST_PROJECTS=1" >&2; exit 2 ;;
  *) echo "web-supervisor: NOEVIA_FRONT must be rust, got '$front'" >&2; exit 2 ;;
esac
if [ "${NOEVIA_RUST_PROJECTS:-}" != 1 ]; then
  echo "web-supervisor: NOEVIA_RUST_PROJECTS=1 is required: the Rust front owns the conversation export Node no longer has (sbstndalton/noevia#1071)" >&2
  exit 2
fi

bin="${NOEVIA_SERVER_BIN:-/usr/local/bin/noevia-server}"
if [ ! -x "$bin" ]; then
  echo "web-supervisor: NOEVIA_FRONT=rust but this image has no noevia-server (its NOEVIA_RS_REF predates bins/noevia-server); update the image" >&2
  exit 2
fi
# The code-network guard (sbstndalton/noevia#1246): with COWORK_CODE_NET_ADDR set, Node behind
# the front sees every request arrive on loopback, so only the front can refuse code-network
# requests. A front that does not report the guard must not face the network.
# (Captured first: with pipefail, grep -q exiting early could fail the pipeline via SIGPIPE.)
if [ -n "${COWORK_CODE_NET_ADDR:-}" ]; then
  features="$("$bin" --features 2>/dev/null || true)"
else
  features=code-net-guard
fi
if ! grep -qx 'code-net-guard' <<<"$features"; then
  echo "web-supervisor: COWORK_CODE_NET_ADDR is set but this noevia-server has no code-net-guard; update the image" >&2
  exit 2
fi
# The client address (noevia-core server/auth.cjs, #1578): Node believes X-Noevia-Client-Ip from its
# loopback peer only when this front drops client copies of it, which a front reports with
# client-address-header. Node is told so with NOEVIA_FRONT_CLIENT_IP=1; a front that predates the
# strip (a core/rs pin mismatch or an rs rollback) leaves Node on the socket address, never a
# header a client chose. Not an error: the address is the proxy's until the image catches up.
client_features="$("$bin" --features 2>/dev/null || true)"
client_ip_confirmed=""
if grep -qx 'client-address-header' <<<"$client_features"; then
  client_ip_confirmed=1
else
  echo "web-supervisor: this noevia-server has no client-address-header; Node ignores X-Noevia-Client-Ip and sees every client as the front" >&2
fi
# Rust-owned sign-in (noevia-core server/rust-auth.cjs), permanent since #1071: Node always refuses
# to write the account tables and no longer answers sign-in, so the front facing the network must.
# A front whose --features does not list rust-auth never starts.
rust_features="$("$bin" --features 2>/dev/null || true)"
if ! grep -qx 'rust-auth' <<<"$rust_features"; then
  echo "web-supervisor: this noevia-server has no rust-auth; Node no longer answers sign-in (sbstndalton/noevia#1071), so update the image" >&2
  exit 2
fi
# The permanent front read routes (#1071): every feature, or nothing starts.
missing=""
for feature in $FRONT_ROUTE_FEATURES; do
  grep -qx -- "$feature" <<<"$rust_features" || missing="$missing $feature"
done
if [ -n "$missing" ]; then
  echo "web-supervisor: this noevia-server lacks the front route feature(s):$missing; Node no longer answers those routes (sbstndalton/noevia#1071), so update the image" >&2
  exit 2
fi
# Rust-owned project routes, M4 (noevia-core server/rust-projects.cjs): with NOEVIA_RUST_PROJECTS=1
# the front answers a project's image routes and shares projects.json with Node under one lock, and
# Node refuses its copies of those writes. It builds on rust-auth (the front gates those routes
# itself, checked above), and only a front whose --features lists rust-projects may take them; Node
# is told so with NOEVIA_RUST_PROJECTS_CONFIRMED=1.
rust_projects_confirmed=""
if [ "${NOEVIA_RUST_PROJECTS:-}" = 1 ]; then
  if ! grep -qx 'rust-projects' <<<"$rust_features"; then
    echo "web-supervisor: NOEVIA_RUST_PROJECTS=1 but this noevia-server has no rust-projects; update the image" >&2
    exit 2
  fi
  rust_projects_confirmed=1
fi
# M4's chat-list slice (sbstndalton/noevia#1409): the front answers a project's chat list only when
# built with it, and then lists rust-project-chats; only then is Node told so, with
# NOEVIA_RUST_PROJECT_CHATS_CONFIRMED=1, and refuses its own chat-list save. A front that lists
# rust-projects alone answers the images only and leaves the chat list to Node: not an error.
rust_project_chats_confirmed=""
if [ "$rust_projects_confirmed" = 1 ] && grep -qx 'rust-project-chats' <<<"$rust_features"; then
  rust_project_chats_confirmed=1
fi
# M4's free-chat slice: the same, for GET/POST /api/freechats and the cargo feature rust-free-chats.
# Confirmed, Node takes free-chats.json.lock and merges the free list per item for its own writers
# of the file, and refuses its own free-list save. Independent of the project chat slice.
rust_free_chats_confirmed=""
if [ "$rust_projects_confirmed" = 1 ] && grep -qx 'rust-free-chats' <<<"$rust_features"; then
  rust_free_chats_confirmed=1
fi
# The project writes moved off Node (sbstndalton/noevia#1264): their own switch,
# NOEVIA_RUST_PROJECT_WRITES=1, off by default (NOEVIA_RUST_PROJECTS=1 alone never moves them). Node
# refuses its copies only once this front is confirmed to answer them: confirmed projects and a
# noevia-server that lists rust-project-writes. The front refuses to start otherwise.
rust_project_writes_confirmed=""
if [ "${NOEVIA_RUST_PROJECT_WRITES:-}" = 1 ]; then
  if [ "$rust_projects_confirmed" != 1 ]; then
    echo "web-supervisor: NOEVIA_RUST_PROJECT_WRITES=1 needs NOEVIA_RUST_PROJECTS=1" >&2
    exit 2
  fi
  if ! grep -qx 'rust-project-writes' <<<"$rust_features"; then
    echo "web-supervisor: NOEVIA_RUST_PROJECT_WRITES=1 but this noevia-server has no rust-project-writes" >&2
    exit 2
  fi
  rust_project_writes_confirmed=1
fi
port="${UI_PORT:-8021}"
if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 64535 ]; then
  echo "web-supervisor: UI_PORT '$port' leaves no room for the legacy port UI_PORT+1000" >&2
  exit 2
fi
legacy=$((port + 1000))

# The project store (sbstndalton/noevia#1264): with NOEVIA_RUST_PROJECT_STORE=1 Node writes
# projects.json and free-chats.json only through the front's loopback store, at UI_PORT+2000, with
# a secret made here for this start and handed to both processes (never taken from the
# environment). Needs the confirmed free-chat slice and a front that lists project-store; the
# supervisor refuses to start otherwise.
rust_project_store_confirmed="" store_port="" store_token=""
if [ "${NOEVIA_RUST_PROJECT_STORE:-}" = 1 ]; then
  if [ "$rust_free_chats_confirmed" != 1 ]; then
    echo "web-supervisor: NOEVIA_RUST_PROJECT_STORE=1 needs NOEVIA_RUST_PROJECTS=1 and a noevia-server with rust-free-chats" >&2
    exit 2
  fi
  if ! grep -qx 'project-store' <<<"$rust_features"; then
    echo "web-supervisor: NOEVIA_RUST_PROJECT_STORE=1 but this noevia-server has no project-store" >&2
    exit 2
  fi
  store_port=$((port + 2000))
  if [ "$store_port" -gt 65535 ]; then
    echo "web-supervisor: UI_PORT '$port' leaves no room for the project store port UI_PORT+2000" >&2
    exit 2
  fi
  store_token="$(od -An -tx1 -N32 /dev/urandom | tr -d ' \n')"
  if [ "${#store_token}" -ne 64 ]; then
    echo "web-supervisor: could not make the project store secret" >&2
    exit 2
  fi
  rust_project_store_confirmed=1
fi

# Node binds UI_HOST for the UI listener AND the Diary file-sharing (DAV) listener. With DAV off
# the legacy port is loopback-only; with DAV on, Node keeps UI_HOST so DAV stays reachable, and
# the legacy port is then reachable from the container's networks too (never published by
# Compose; the same exposure Node's UI port has today) until core splits the two bind hosts.
node_host="127.0.0.1"
if [ -n "${COWORK_DAV_PORT:-}" ] && [ "${COWORK_DAV_PORT}" != 0 ]; then
  node_host="${UI_HOST:-0.0.0.0}"
  echo "web-supervisor: COWORK_DAV_PORT is set; Node's legacy port $legacy listens on $node_host, not loopback only" >&2
fi

node_pid="" front_pid="" signalled=0
stop() {
  local p
  for p in "$node_pid" "$front_pid"; do
    [ -n "$p" ] && kill -TERM "$p" 2>/dev/null
  done
  return 0
}
trap 'signalled=1; stop' TERM INT

UI_HOST="$node_host" UI_PORT="$legacy" \
  NOEVIA_FRONT_CLIENT_IP="$client_ip_confirmed" \
  NOEVIA_RUST_PROJECTS_CONFIRMED="$rust_projects_confirmed" NOEVIA_RUST_PROJECT_CHATS_CONFIRMED="$rust_project_chats_confirmed" \
  NOEVIA_RUST_FREE_CHATS_CONFIRMED="$rust_free_chats_confirmed" \
  NOEVIA_RUST_PROJECT_WRITES_CONFIRMED="$rust_project_writes_confirmed" \
  NOEVIA_RUST_PROJECT_STORE_CONFIRMED="$rust_project_store_confirmed" \
  NOEVIA_PROJECT_STORE_PORT="$store_port" NOEVIA_PROJECT_STORE_TOKEN="$store_token" \
  node server/index.cjs &
node_pid=$!
NOEVIA_PROJECT_STORE_PORT="$store_port" NOEVIA_PROJECT_STORE_TOKEN="$store_token" \
  NOEVIA_LEGACY_UPSTREAM="http://127.0.0.1:$legacy" "$bin" &
front_pid=$!

# Whichever exits first (or a signal) ends the wait.
wait -n "$node_pid" "$front_pid"
code=$?
if [ "$signalled" = 0 ]; then
  if kill -0 "$node_pid" 2>/dev/null; then which=noevia-server; else which=node; fi
  echo "web-supervisor: $which exited ($code); stopping the other" >&2
fi
stop
wait "$node_pid" 2>/dev/null
wait "$front_pid" 2>/dev/null
# docker stop: a clean exit. Anything else: non-zero, even when the process that left said 0.
[ "$signalled" = 1 ] && exit 0
[ "$code" = 0 ] && code=1
exit "$code"
