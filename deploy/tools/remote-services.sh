#!/usr/bin/env bash
# Services assigned to another Inference machine (#1843): the laya/kev, embed and rerank sidecars.
# Sourced by preflight/up.sh and sidecar-restart-alert.sh; runs on bash 3.2 and Linux. Also usable
# directly:  remote-services.sh [--list|--probe]   (prints one status line per remote service).
#
# The assignment itself lives in web's settings store (Settings -> Inference machines). This host
# tooling must work before web is up and holds no web admin credential, so it reads an explicit
# operator list instead:
#   NOEVIA_REMOTE_SERVICES=embed,rerank          subset of: laya, kev, embed, rerank
#   NOEVIA_REMOTE_<NAME>_HEALTH_URL=http://pi5.lan:8080/health   (NAME upper case: EMBED, RERANK, LAYA, KEV)
#   NOEVIA_REMOTE_<NAME>_MACHINE=pi5             label used in messages (default: remote)
#   NOEVIA_REMOTE_PROBE_TIMEOUT=3                seconds, connect and total (1 to 30)
# NOEVIA_REMOTE_ENV_FILE=/mnt/docker/appdata/cowork/config/.env   optional: remote_load_env reads only the
#   NOEVIA_REMOTE_* KEY=value lines of that file (never executed or sourced); variables already in the
#   environment win. Lets cron and up.sh share the compose .env without exporting anything.
# Unset or empty NOEVIA_REMOTE_SERVICES: nothing here does anything. Health URLs must be http(s), carry
# no credentials and point at a LAN or Tailscale host (private/CGNAT IP literal, a single-label name or
# .local/.lan/.home.arpa/.internal/.ts.net); anything else is reported "refused" and not contacted.
# No secret is ever sent, printed or logged. Redirects are not followed.

remote_known_services="laya kev embed rerank"

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

remote_services() { # prints each valid configured service once; unknown names go to stderr
  local raw="${NOEVIA_REMOTE_SERVICES-}" item seen=" "
  [ -n "$raw" ] || return 0
  local IFS=','
  for item in $raw; do
    item="$(printf '%s' "$item" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
    [ -n "$item" ] || continue
    case " $remote_known_services " in
      *" $item "*) ;;
      *) echo "warning: NOEVIA_REMOTE_SERVICES: unknown service '$item' ignored (known: $remote_known_services)" >&2; continue ;;
    esac
    case "$seen" in *" $item "*) continue ;; esac
    seen="$seen$item "
    printf '%s\n' "$item"
  done
}

remote_var() { # service SUFFIX -> value of NOEVIA_REMOTE_<SERVICE>_<SUFFIX>
  local v="NOEVIA_REMOTE_$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]')_$2"
  printf '%s' "${!v-}"
}

remote_machine() { # service -> label safe to print
  local m
  m="$(remote_var "$1" MACHINE | tr -cd 'A-Za-z0-9._-' | cut -c1-40)"
  printf '%s' "${m:-remote}"
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

# remote_probe SERVICE -> prints "<state>|<detail>"; state is one of
#   healthy, unhealthy (HTTP answer other than 2xx), unreachable (timeout / connection), unconfigured, refused.
remote_probe() {
  local svc="$1" url timeout host code rc
  url="$(remote_var "$svc" HEALTH_URL)"
  if [ -z "$url" ]; then echo "unconfigured|no NOEVIA_REMOTE_$(printf '%s' "$svc" | tr '[:lower:]' '[:upper:]')_HEALTH_URL set"; return 0; fi
  if [[ ! "$url" =~ ^https?://([^/@?#:\[]+|\[[0-9a-fA-F:]+\])(:[0-9]{1,5})?([/?#].*)?$ ]]; then
    echo "refused|health URL must be http(s)://host[:port]/path without credentials"; return 0
  fi
  host="${BASH_REMATCH[1]}"
  if ! remote_host_allowed "$host"; then echo "refused|health URL host is not a LAN or Tailscale address"; return 0; fi
  timeout="${NOEVIA_REMOTE_PROBE_TIMEOUT:-3}"
  if [[ ! "$timeout" =~ ^[0-9]+$ ]] || [ "$timeout" -lt 1 ] || [ "$timeout" -gt 30 ]; then timeout=3; fi
  command -v curl >/dev/null 2>&1 || { echo "unreachable|curl is not installed on this host"; return 0; }
  code="$(curl -sS -o /dev/null -w '%{http_code}' --noproxy '*' --connect-timeout "$timeout" --max-time "$timeout" "$url" 2>/dev/null)"
  rc=$?
  if [ "$rc" -ne 0 ] || [ -z "$code" ] || [ "$code" = 000 ]; then echo "unreachable|no answer within ${timeout}s"; return 0; fi
  case "$code" in 2??) echo "healthy|HTTP $code" ;; *) echo "unhealthy|HTTP $code" ;; esac
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
