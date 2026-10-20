#!/usr/bin/env bash
# Print the effective NON-SECRET switches of a container (#1193), for release checks.
#
#   deploy/tools/flags.sh <container>            KEY=value for allow-listed keys only
#   deploy/tools/flags.sh --keys <container>     allow-listed key names only, no values
#   deploy/tools/flags.sh <container> KEY...     only those keys; any key off the allow-list is
#                                                refused (exit 2) before docker is even called
#
# Allow-list (anchored, matched on the KEY NAME inside jq before any value is emitted):
#   *_IMPL  NOEVIA_FEATURE_*  DECISION_LOAD_ADVISOR  LAYA_LOAD_ADVISOR (old alias)  MODEL_AUTOCONFIG  GGUF_PARSER
#   COWORK_CODE_NET_ADDR  COWORK_VERSION  DIARY_VERSION  MODEL_MANAGER_VERSION
# Everything else (tokens, keys, passwords, URLs with credentials...) is never printed. Do NOT
# grep `docker inspect` output for values in release briefs; use this or list key names only.
set -u -o pipefail
allow='^([A-Z0-9_]+_IMPL|NOEVIA_FEATURE_[A-Z0-9_]+|DECISION_LOAD_ADVISOR|LAYA_LOAD_ADVISOR|MODEL_AUTOCONFIG|GGUF_PARSER|COWORK_CODE_NET_ADDR|COWORK_VERSION|DIARY_VERSION|MODEL_MANAGER_VERSION)$'
usage() { echo "usage: flags.sh [--keys] <container> [KEY...]" >&2; exit 2; }
keys_only=0
[ "${1:-}" = "--keys" ] && { keys_only=1; shift; }
[ $# -ge 1 ] || usage
container="$1"; shift
case "$container" in -*|"") usage ;; esac
# [[ =~ ]] matches the whole string; grep -E would match line by line, so a value with a newline
# could pass on one good line (#1195 nit).
name_re='^[A-Za-z0-9][A-Za-z0-9_.-]*$'
[[ $container =~ $name_re ]] || { echo "flags.sh: bad container name" >&2; exit 2; }
want=()
for k in "$@"; do
  if ! [[ $k =~ $allow ]]; then
    echo "flags.sh: refusing key not on the allow-list: $k" >&2   # the name only; never a value
    exit 2
  fi
  want+=("$k")
done
command -v jq >/dev/null 2>&1 || { echo "flags.sh: jq is required" >&2; exit 1; }
json="$(docker inspect "$container" 2>/dev/null)" || { echo "flags.sh: docker inspect failed for $container" >&2; exit 1; }
wantjson='[]'
[ ${#want[@]} -gt 0 ] && wantjson="$(printf '%s\n' "${want[@]}" | jq -R . | jq -s .)"
printf '%s' "$json" | jq -r --arg allow "$allow" --argjson keys_only "$keys_only" --argjson want "$wantjson" '
  (.[0].Config.Env // [])[]
  | (index("=")) as $i
  | {k: (if $i == null then . else .[:$i] end), v: (if $i == null then "" else .[$i+1:] end)}
  | select(.k | test($allow))
  | select(($want | length) == 0 or (.k as $k | $want | index($k) != null))
  | if $keys_only == 1 then .k else "\(.k)=\(.v)" end' | sort
