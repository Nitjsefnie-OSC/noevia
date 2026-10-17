#!/usr/bin/env bash
# #2005: `bash -x` must never print the remote auth key. remote_auth_read and remote_probe hold the header
# text in shell variables; their xtrace is suppressed while it is in scope and restored only if it was on.
# curl is a PATH shim (nothing leaves the machine); the key is a random synthetic string made here.
# Runs on macOS bash 3.2 and Linux. REMOTE_SERVICES_LIB points the test at another copy of the library.
set -u
here="$(cd -- "$(dirname -- "$0")" && pwd)"
lib="${REMOTE_SERVICES_LIB:-$here/remote-services.sh}"
work="$(mktemp -d "${TMPDIR:-/tmp}/remote-xtrace-test.XXXXXX")"
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin" "$work/keys"
chmod 700 "$work" "$work/keys"
cat > "$work/bin/curl" <<'SHIM'
#!/usr/bin/env bash
printf '200'
SHIM
chmod +x "$work/bin/curl"
export PATH="$work/bin:$PATH"

key="synth$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n')"
printf 'Authorization: Bearer %s\n' "$key" > "$work/keys/good.hdr"
printf 'Host: %s\n' "$key" > "$work/keys/host.hdr"        # refused by remote_auth_read after the line is parsed
printf 'Authorization: Bearer %s\n' "$key" > "$work/keys/open.hdr"
chmod 600 "$work/keys/good.hdr" "$work/keys/host.hdr"
chmod 644 "$work/keys/open.hdr"                            # refused on mode, before the content is read

fails=0; passes=0
check() { if eval "$2"; then passes=$((passes+1)); echo "ok - $1"; else fails=$((fails+1)); echo "FAIL - $1"; fi; }

# probe FILE [bash flags...]: runs remote_probe for the embedding role against FILE; stdout/stderr to $work/{out,err}.
probe() {
  local f="$1"; shift
  NOEVIA_REMOTE_SERVICES=embedding NOEVIA_REMOTE_EMBEDDING_HEALTH_URL=http://127.0.0.1:9/health \
    NOEVIA_REMOTE_EMBEDDING_AUTH_FILE="$f" LIB="$lib" \
    bash "$@" -c 'set -eu; . "$LIB"; remote_probe embedding; echo "rc=$?"; case $- in *x*) echo XTRACE_ON ;; *) echo XTRACE_OFF ;; esac' \
    > "$work/out" 2> "$work/err"
}

probe "$work/keys/good.hdr" -x
check "probe under bash -x: healthy answer" 'grep -q "^healthy|HTTP 200" "$work/out"'
check "probe under bash -x: tracing was really on (not a vacuous pass)" 'grep -q "remote_probe" "$work/err"'
check "probe under bash -x: key absent from stderr" '! grep -qF "$key" "$work/err"'
check "probe under bash -x: key absent from stdout" '! grep -qF "$key" "$work/out"'
check "probe under bash -x: xtrace restored afterwards" 'grep -qx XTRACE_ON "$work/out"'
check "probe under bash -x: set -e/-u intact (reached the end)" 'grep -qx "rc=0" "$work/out"'

probe "$work/keys/host.hdr" -x
check "refused header under bash -x: reported unhealthy" 'grep -q "^unhealthy|.*AUTH_FILE unusable" "$work/out"'
check "refused header under bash -x: key absent from stderr" '! grep -qF "$key" "$work/err" && grep -q "remote_probe" "$work/err"'
check "refused header under bash -x: xtrace restored" 'grep -qx XTRACE_ON "$work/out"'

probe "$work/keys/open.hdr" -x
check "open-mode key file under bash -x: key absent from stderr" '! grep -qF "$key" "$work/err" && grep -q "remote_probe" "$work/err"'

probe "$work/keys/good.hdr"
check "probe without -x: healthy, key absent, xtrace stays off" 'grep -q "^healthy|HTTP 200" "$work/out" && grep -qx XTRACE_OFF "$work/out" && ! grep -qF "$key" "$work/err" "$work/out"'

# remote_auth_read on its own, with errexit: a failing return must not end the shell, and xtrace comes back.
NOEVIA_REMOTE_SERVICES=embedding LIB="$lib" F="$work/keys/host.hdr" G="$work/keys/good.hdr" \
  bash -x -c 'set -eu; . "$LIB"
    if remote_auth_read "$F"; then echo BAD_ACCEPTED; fi
    remote_auth_read "$G"; echo "good=$?"
    case $- in *x*) echo XTRACE_ON ;; esac' > "$work/out" 2> "$work/err"
check "remote_auth_read under bash -x: key absent from stderr" '! grep -qF "$key" "$work/err" && grep -q "remote_auth_read" "$work/err"'
check "remote_auth_read: failure does not trip set -e, success returns 0" 'grep -qx "good=0" "$work/out" && ! grep -q BAD_ACCEPTED "$work/out"'
check "remote_auth_read: xtrace restored" 'grep -qx XTRACE_ON "$work/out"'

# The shipped entry point, traced end to end.
NOEVIA_REMOTE_SERVICES=embedding NOEVIA_REMOTE_EMBEDDING_HEALTH_URL=http://127.0.0.1:9/health \
  NOEVIA_REMOTE_EMBEDDING_AUTH_FILE="$work/keys/good.hdr" bash -x "$lib" --probe > "$work/out" 2> "$work/err"
check "bash -x remote-services.sh --probe: PASS line printed, key absent" 'grep -q "^PASS: embedding" "$work/out" && ! grep -qF "$key" "$work/err" "$work/out"'

echo "$passes passed, $fails failed"
[ "$fails" -eq 0 ]
