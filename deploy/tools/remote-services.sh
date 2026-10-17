#!/usr/bin/env bash
# Services assigned to another Inference machine (#1843), named by role: decision, sensitivity, embedding,
# reranker (the service ids of Settings -> Inference machines). Sourced by preflight/up.sh and
# sidecar-restart-alert.sh; runs on bash 3.2 and Linux. Also usable directly:
#   remote-services.sh [--list|--probe]   (prints one status line per remote service).
#
# The assignment itself lives in web's settings store (Settings -> Inference machines). This host
# tooling must work before web is up and holds no web admin credential, so it reads an explicit
# operator list instead:
#   NOEVIA_REMOTE_SERVICES=embedding,reranker      subset of: decision, sensitivity, embedding, reranker
#   NOEVIA_REMOTE_<ROLE>_HEALTH_URL=http://pi5.lan:8080/health   (ROLE upper case: DECISION, SENSITIVITY, ...)
#   NOEVIA_REMOTE_<ROLE>_MACHINE=pi5             label used in messages (default: remote)
#   NOEVIA_REMOTE_<ROLE>_AUTH_FILE=/path/key.hdr optional (#1980): a file holding one full header line, e.g.
#     "Authorization: Bearer ...". It must be a regular file (not a symlink) of mode 0600 or stricter, else it
#     is ignored with a warning. It is passed as `curl -H @file`, so the key never appears in argv or output.
#   NOEVIA_REMOTE_PROBE_TIMEOUT=3                seconds, connect and total (1 to 30)
# Earlier service names are still accepted, in NOEVIA_REMOTE_SERVICES and in the per-service variable names
# (docs/deployment.md lists them); a role-named variable wins over the earlier one.
# NOEVIA_REMOTE_ENV_FILE=/mnt/docker/appdata/cowork/config/.env   optional: remote_load_env reads only the
#   NOEVIA_REMOTE_* KEY=value lines of that file (never executed or sourced); variables already in the
#   environment win. Lets cron and up.sh share the compose .env without exporting anything.
# Unset or empty NOEVIA_REMOTE_SERVICES: nothing here does anything. Health URLs must be http(s), carry
# no credentials and point at a LAN or Tailscale host (private/CGNAT IP literal, a single-label name or
# .local/.lan/.home.arpa/.internal/.ts.net); anything else is reported "refused" and not contacted.
# Answers, as core's machine health reads them: 2xx is healthy; 401/403 when no key was sent is healthy
# "needs auth" (the service is there and wants a login); 401/403 to a key that was sent, or any other
# answer, is unhealthy. No secret is ever printed or logged. Redirects are not followed.

remote_known_services="decision sensitivity embedding reranker"

remote_role_of() { # role id or earlier name -> role id (nothing when unknown)
  case "$1" in
    decision|kev) echo decision ;;
    sensitivity|laya) echo sensitivity ;;
    embedding|embed) echo embedding ;;
    reranker|rerank) echo reranker ;;
  esac
}

remote_legacy_name() { # role id -> its earlier name: still read from the environment; also its local Compose service
  case "$1" in
    decision) echo kev ;;
    sensitivity) echo laya ;;
    embedding) echo embed ;;
    reranker) echo rerank ;;
  esac
}

remote_upper() { printf '%s' "$1" | tr '[:lower:]' '[:upper:]'; }

remote_load_env() { # reads NOEVIA_REMOTE_* lines from $NOEVIA_REMOTE_ENV_FILE; no eval, no other key
  local f="${NOEVIA_REMOTE_ENV_FILE-}" line key val
  [ -n "$f" ] && [ -r "$f" ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    [[ "$line" =~ ^[[:space:]]*(NOEVIA_REMOTE_[A-Z0-9_]+)=(.*)$ ]] || continue
    key="${BASH_REMATCH[1]}"; val="${BASH_REMATCH[2]}"
    val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
    [ -z "${!key-}" ] || continue
    export "$key=$val"
  done < "$f"
}

remote_services() { # prints the role of each valid configured service once; unknown names go to stderr
  local raw="${NOEVIA_REMOTE_SERVICES-}" item role seen=" "
  [ -n "$raw" ] || return 0
  local IFS=','
  for item in $raw; do
    item="$(printf '%s' "$item" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
    [ -n "$item" ] || continue
    role="$(remote_role_of "$item")"
    if [ -z "$role" ]; then
      echo "warning: NOEVIA_REMOTE_SERVICES: unknown service '$item' ignored (known: ${remote_known_services// /, })" >&2
      continue
    fi
    case "$seen" in *" $role "*) continue ;; esac
    seen="$seen$role "
    printf '%s\n' "$role"
  done
}

remote_var() { # service SUFFIX -> NOEVIA_REMOTE_<ROLE>_<SUFFIX>, else the same variable under the earlier name
  local role legacy v
  role="$(remote_role_of "$1")"; [ -n "$role" ] || role="$1"
  v="NOEVIA_REMOTE_$(remote_upper "$role")_$2"
  if [ -n "${!v-}" ]; then printf '%s' "${!v}"; return 0; fi
  legacy="$(remote_legacy_name "$role")"
  [ -n "$legacy" ] || return 0
  v="NOEVIA_REMOTE_$(remote_upper "$legacy")_$2"
  printf '%s' "${!v-}"
}

remote_var_name() { # service SUFFIX -> the role-named variable, for messages (never its value)
  local role
  role="$(remote_role_of "$1")"; [ -n "$role" ] || role="$1"
  printf 'NOEVIA_REMOTE_%s_%s' "$(remote_upper "$role")" "$2"
}

remote_machine() { # service -> label safe to print
  local m
  m="$(remote_var "$1" MACHINE | tr -cd 'A-Za-z0-9._-' | cut -c1-40)"
  printf '%s' "${m:-remote}"
}

remote_local_service() { # role -> the local Compose service that serves it when it is not remote
  remote_legacy_name "$(remote_role_of "$1")"
}

# remote_auth_file SERVICE -> prints the path of a usable header file, or nothing. A file that is set but not
# usable is reported on stderr by variable name only (never its path or content) and ignored.
remote_auth_file() {
  local f name mode
  f="$(remote_var "$1" AUTH_FILE)"
  [ -n "$f" ] || return 0
  name="$(remote_var_name "$1" AUTH_FILE)"
  if [ -L "$f" ] || [ ! -f "$f" ] || [ ! -r "$f" ]; then
    echo "warning: $name is not a readable regular file; ignored, probing without a key" >&2; return 0
  fi
  mode="$(stat -c '%a' -- "$f" 2>/dev/null || stat -f '%Lp' -- "$f" 2>/dev/null)"
  if [[ ! "$mode" =~ ^[0-7]{3,4}$ ]] || [ $((8#$mode & 8#7177)) -ne 0 ]; then
    echo "warning: $name must have mode 0600 or stricter (chmod 600); ignored, probing without a key" >&2; return 0
  fi
  # One or more "Name: value" lines and nothing else (blank lines aside). grep reads the file; nothing is printed.
  if ! grep -Eq '^[A-Za-z0-9-]+:[[:space:]]*[^[:space:]]' -- "$f" 2>/dev/null \
    || grep -Evq '^[A-Za-z0-9-]+:[[:space:]]*[^[:space:]]|^[[:space:]]*$' -- "$f" 2>/dev/null; then
    echo "warning: $name must hold a header line such as \"Authorization: Bearer <key>\"; ignored, probing without a key" >&2; return 0
  fi
  printf '%s' "$f"
}

# remote_probe SERVICE -> prints "<state>|<detail>"; state is one of
#   healthy (2xx, or 401/403 with no key sent: "needs auth"), unhealthy (any other HTTP answer, including
#   401/403 to a key that was sent), unreachable (timeout / connection), unconfigured, refused.
remote_probe() {
  local svc="$1" url timeout host code rc auth
  local hdr=()
  url="$(remote_var "$svc" HEALTH_URL)"
  if [ -z "$url" ]; then echo "unconfigured|no $(remote_var_name "$svc" HEALTH_URL) set"; return 0; fi
  if [[ ! "$url" =~ ^https?://([^/@?#:\[]+|\[[0-9a-fA-F:]+\])(:[0-9]{1,5})?([/?#].*)?$ ]]; then
    echo "refused|health URL must be http(s)://host[:port]/path without credentials"; return 0
  fi
  host="${BASH_REMATCH[1]}"
  if ! remote_host_allowed "$host"; then echo "refused|health URL host is not a LAN or Tailscale address"; return 0; fi
  timeout="${NOEVIA_REMOTE_PROBE_TIMEOUT:-3}"
  if [[ ! "$timeout" =~ ^[0-9]+$ ]] || [ "$timeout" -lt 1 ] || [ "$timeout" -gt 30 ]; then timeout=3; fi
  command -v curl >/dev/null 2>&1 || { echo "unreachable|curl is not installed on this host"; return 0; }
  auth="$(remote_auth_file "$svc")"
  # -H @file: curl reads the header from the file, so argv only ever holds the path.
  [ -z "$auth" ] || hdr=(-H "@$auth")
  code="$(curl -sS -o /dev/null -w '%{http_code}' --noproxy '*' --connect-timeout "$timeout" --max-time "$timeout" \
    ${hdr[@]+"${hdr[@]}"} "$url" 2>/dev/null)"
  rc=$?
  if [ "$rc" -ne 0 ] || [ -z "$code" ] || [ "$code" = 000 ]; then echo "unreachable|no answer within ${timeout}s"; return 0; fi
  case "$code" in
    2??) echo "healthy|HTTP $code" ;;
    401|403)
      if [ -n "$auth" ]; then echo "unhealthy|HTTP $code (key refused)"; else echo "healthy|HTTP $code (needs auth)"; fi ;;
    *) echo "unhealthy|HTTP $code" ;;
  esac
}

remote_host_allowed() { # host (brackets kept for IPv6) -> 0 when LAN/Tailscale/loopback only
  local h
  h="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  if [[ "$h" =~ ^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})$ ]]; then
    local a=$((10#${BASH_REMATCH[1]})) b=$((10#${BASH_REMATCH[2]})) c=$((10#${BASH_REMATCH[3]})) d=$((10#${BASH_REMATCH[4]}))
    [ "$a" -le 255 ] && [ "$b" -le 255 ] && [ "$c" -le 255 ] && [ "$d" -le 255 ] || return 1
    [ "$a" -eq 10 ] && return 0
    [ "$a" -eq 127 ] && return 0
    [ "$a" -eq 192 ] && [ "$b" -eq 168 ] && return 0
    [ "$a" -eq 172 ] && [ "$b" -ge 16 ] && [ "$b" -le 31 ] && return 0
    [ "$a" -eq 169 ] && [ "$b" -eq 254 ] && return 0
    [ "$a" -eq 100 ] && [ "$b" -ge 64 ] && [ "$b" -le 127 ] && return 0
    return 1
  fi
  case "$h" in
    \[::1\]|\[fd*\]|\[fe80:*\]) return 0 ;;
    \[*) return 1 ;;
    *[!a-z0-9.-]*|.*|*..*|-*) return 1 ;;
    *.local|*.lan|*.home.arpa|*.internal|*.ts.net) return 0 ;;
    *.*) return 1 ;;
    *) return 0 ;;
  esac
}

# remote_report -> one line per configured remote service. Advisory: always returns 0.
remote_report() {
  local svc res state detail
  while IFS= read -r svc; do
    [ -n "$svc" ] || continue
    res="$(remote_probe "$svc")"; state="${res%%|*}"; detail="${res#*|}"
    case "$state" in
      healthy) printf 'PASS: %s runs on machine %s (%s)\n' "$svc" "$(remote_machine "$svc")" "$detail" ;;
      unconfigured) printf 'INFO: %s is assigned to machine %s; the local sidecar is not required. Not probed: %s\n' "$svc" "$(remote_machine "$svc")" "$detail" ;;
      *) printf 'WARN: %s on machine %s is %s (%s)\n' "$svc" "$(remote_machine "$svc")" "$state" "$detail" ;;
    esac
  done < <(remote_services)
  return 0
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  remote_load_env
  case "${1---probe}" in
    --list) remote_services ;;
    --probe) remote_report ;;
    *) echo "usage: remote-services.sh [--list|--probe]" >&2; exit 64 ;;
  esac
fi
