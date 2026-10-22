#!/usr/bin/env bash
# #2105: release preflight. Refuses a cutover when the model ids the diary container will receive are not
# served by the chat router, because the diary (services#2099) then refuses every answer instead of letting
# the router pick a model. Run on the Docker host BEFORE anything is built, stopped or changed:
#   diary-models-check.sh --env-file <the .env the cutover deploys> [--project-dir <the Compose project>]
# Exit 0: both ids resolve to a served chat model. Exit 1: refused (or failed closed). Exit 2: bad usage.
#
# What is checked is what the diary container will actually receive, not what the env file says: the script
# runs `docker compose --env-file <file> config --format json` in the Compose project (--project-dir, else the
# current directory) with the same files the deploy uses, and reads the environment of the `diary` service:
#   LLM_CHAT_MODEL, LLM_AUX_MODEL     the ids. A chat id that is missing, empty or the "default" placeholder fails.
#                                     An aux id that is missing, empty or "default" means the chat id (the diary does
#                                     the same, agent/config.py).
#   LLM_CHAT_FALLBACK_MODEL, LLM_AUX_FALLBACK_MODEL   optional explicit substitutes (agent/config.py, services#2099).
#                                     They count ONLY when the deployed Compose files map them into the diary
#                                     service; a value that sits in the env file but is not mapped is not seen by the
#                                     diary and is ignored here.
#   LLM_BASE_URL, LLM_API_KEY         the chat router (required; the check never guesses an address)
#   LLM_AUX_BASE_URL, LLM_AUX_API_KEY the aux router when mapped; when not mapped the chat router and key are used
# The env file itself is never parsed here (Compose interpolates it), so there is no second reading of `$`.
# Effective id, with explicit settings only: the configured id when the router serves it as a chat model, else
# the fallback's id when that is served, else REFUSED. This is STRICTER than the diary on purpose: the diary's
# last-resort "follow whatever chat resolved to" substitute for aux is not accepted (nobody named it), and a
# missing router address is refused although Compose would fill in a default that only means something inside
# a container. "Served" means listed by GET <router>/models and not launched with an embedding or reranking
# flag, the same test the diary applies. Being asleep still counts as served: the check is read-only. It makes
# one GET of the model list per router and nothing else (no slot query, no completion, no load), so it can
# never wake a model.
# Router addresses that are Compose service names: the GET runs on the host first (curl). When the host cannot
# resolve the name (curl exit 6) the very same single GET is made from inside the running `diary` container
# (`docker exec -i`, python from the Diary image, no redirects, bounded timeouts, the address and the credential
# on stdin, never argv), so the name resolves as the Diary resolves it (#2111). When no diary container is
# running the check refuses: it will not guess an address or start anything.
# Fails closed on: an unreadable env file, no docker or jq or curl, a Compose config that does not resolve, no
# `diary` service, a missing key above, a router that is unreachable, answers with a status other than 200
# (redirects are not followed), or sends a body that is not a model list.
# Secrets: the resolved config (it holds tokens) stays in a private temp file and only the keys above are read
# from it. The credential travels on a curl config pipe, never argv. No value is printed, neither ids,
# addresses nor credentials; messages name keys only. Needs bash, docker, curl and jq (python only inside the
# diary container, and only for the in-network read).
{ set +x; } 2>/dev/null
set -uo pipefail

env_file=""
project_dir=""
usage="usage: diary-models-check.sh --env-file <path to the .env the cutover deploys> [--project-dir <Compose project directory>]"
while [ $# -gt 0 ]; do
  case "$1" in
    --env-file) env_file="${2-}"; shift; [ $# -gt 0 ] && shift ;;
    --env-file=*) env_file="${1#--env-file=}"; shift ;;
    --project-dir) project_dir="${2-}"; shift; [ $# -gt 0 ] && shift ;;
    --project-dir=*) project_dir="${1#--project-dir=}"; shift ;;
    *) echo "$usage" >&2; exit 2 ;;
  esac
done
if [ -z "$env_file" ]; then
  echo "$usage" >&2
  exit 2
fi

refused=0
refuse() { echo "REFUSED (diary models, #2105): $*" >&2; refused=1; }
fail_closed() { echo "REFUSED (diary models, #2105): $*" >&2; exit 1; }

[ -f "$env_file" ] && [ -r "$env_file" ] || fail_closed "the environment file the cutover deploys is not readable; not deploying"
for tool in docker curl jq; do
  command -v "$tool" >/dev/null 2>&1 || fail_closed "$tool is required for this check and was not found; not deploying"
done
if [ -n "$project_dir" ]; then
  [ -d "$project_dir" ] && cd -- "$project_dir" || fail_closed "the Compose project directory is not usable; not deploying"
fi

umask 077
work="$(mktemp -d "${TMPDIR:-/tmp}/diary-models-check.XXXXXX")" || fail_closed "cannot create a temporary directory; not deploying"
trap 'rm -rf "$work"' EXIT

# The deployed Compose configuration, resolved with the env file the cutover deploys. Its stderr is dropped: it can
# echo interpolated settings.
docker compose --env-file "$env_file" config --format json > "$work/compose.json" 2>/dev/null
rc=$?
[ "$rc" -eq 0 ] || fail_closed "docker compose config did not resolve in the Compose project (exit $rc); run it by hand to see why; not deploying"
jq -e '.services | type == "object"' "$work/compose.json" >/dev/null 2>&1 \
  || fail_closed "docker compose config did not return a usable configuration; not deploying"
jq -e '.services.diary | type == "object"' "$work/compose.json" >/dev/null 2>&1 \
  || fail_closed "the resolved Compose configuration has no diary service; not deploying"

# svc_get KEY: sets svc_present (0/1) and svc_value from the diary service's resolved environment (a map, or a
# list of KEY=value entries). Only the named key is read.
svc_present=0; svc_value=""
svc_get() {
  local key="$1"
  svc_present=0; svc_value=""
  local filter='(.services.diary.environment // {})
    | (if type == "array" then (map(split("=") | {key: .[0], value: (.[1:] | join("="))}) | from_entries) else . end)'
  if [ "$(jq -r --arg k "$key" "$filter | has(\$k)" "$work/compose.json" 2>/dev/null)" = true ]; then
    svc_present=1
    svc_value="$(jq -r --arg k "$key" "$filter | (.[\$k] // \"\") | tostring" "$work/compose.json" 2>/dev/null)"
  fi
}

PLACEHOLDER=default

svc_get LLM_CHAT_MODEL; chat_id="$svc_value"
if [ -z "$chat_id" ] || [ "$chat_id" = "$PLACEHOLDER" ]; then
  refuse "LLM_CHAT_MODEL is missing, empty or the placeholder in the diary service's resolved environment; set the deployed model setting that feeds it to a model id the chat router serves"
  chat_id=""
fi
svc_get LLM_AUX_MODEL; aux_id="$svc_value"
if [ -z "$aux_id" ] || [ "$aux_id" = "$PLACEHOLDER" ]; then aux_id="$chat_id"; fi   # as the diary does
svc_get LLM_CHAT_FALLBACK_MODEL; chat_fallback="$svc_value"
svc_get LLM_AUX_FALLBACK_MODEL; aux_fallback="$svc_value"

svc_get LLM_BASE_URL; chat_url="$svc_value"
svc_get LLM_API_KEY; chat_key="$svc_value"
if [ -z "$chat_url" ]; then
  refuse "LLM_BASE_URL is missing or empty in the diary service's resolved environment, so the router's served models cannot be read"
fi
svc_get LLM_AUX_BASE_URL; aux_url="$svc_value"; [ -n "$aux_url" ] || aux_url="$chat_url"
svc_get LLM_AUX_API_KEY
if [ "$svc_present" = 1 ]; then aux_key="$svc_value"; else aux_key="$chat_key"; fi

if [ "$refused" != 0 ]; then
  echo "diary model check failed; the cutover is refused before anything was changed (#2105)." >&2
  exit 1
fi

# The in-network read: the same single GET as curl makes (no redirects, 10 s, 4 MiB cap), made by python inside the
# running diary container. stdin: the URL, then the credential (possibly empty). stdout: the HTTP status, a newline,
# then the body. Exit non-zero when the router cannot be read at all.
NET_GET='import sys, urllib.request, urllib.error
u = sys.stdin.readline().rstrip("\n"); k = sys.stdin.readline().rstrip("\n")
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):
        return None
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)
try:
    r = opener.open(urllib.request.Request(u, headers={"Authorization": "Bearer " + k} if k else {}, method="GET"), timeout=10)
except urllib.error.HTTPError as e:
    r = e
except Exception:
    sys.exit(7)
body = r.read(4194305)
if len(body) > 4194304:
    sys.exit(8)
sys.stdout.buffer.write(str(r.getcode()).encode() + b"\n" + body)'

# in_network_get URL KEY: sets status and writes $work/body; returns 70 when no diary container is running, else
# the exit code of the exec.
in_network_get() {
  local url="$1" key="$2" cid out="$work/netbody" bound=()
  cid="$(docker compose --env-file "$env_file" ps -q diary 2>/dev/null | head -n 1)"
  [ -n "$cid" ] || return 70
  command -v timeout >/dev/null 2>&1 && bound=(timeout 20)
  printf '%s\n%s\n' "$url" "$key" | ${bound[@]+"${bound[@]}"} docker exec -i "$cid" python -c "$NET_GET" > "$out" 2>/dev/null
  local rc=$?
  [ "$rc" -eq 0 ] || return "$rc"
  status="$(head -n 1 "$out")"
  tail -n +2 "$out" > "$work/body"
  return 0
}

# fetch_chat_ids LABEL URL KEY OUTFILE: one read-only GET <URL>/models; writes the served chat-capable ids, one per
# line. LABEL names the setting that holds the address, for messages. Returns 0, or 1 after reporting why.
fetch_chat_ids() {
  local label="$1" url="$2" key="$3" out="$4" base status rc
  case "$url" in
    http://*|https://*) ;;
    *) refuse "$label must be an http(s) address"; return 1 ;;
  esac
  base="${url%/}"
  case "${base#*://}" in
    *@*|*[[:space:]]*) refuse "$label must not carry credentials or whitespace"; return 1 ;;
  esac
  local curl_args=(-sS --connect-timeout 5 --max-time 10 --max-filesize 4194304 -o "$work/body" -w '%{http_code}')
  rm -f "$work/body"
  if [ -n "$key" ]; then
    key="${key//\\/\\\\}"; key="${key//\"/\\\"}"
    status="$(printf 'header = "Authorization: Bearer %s"\n' "$key" | curl "${curl_args[@]}" -K - -- "$base/models" 2>/dev/null)"; rc=$?
  else
    status="$(curl "${curl_args[@]}" -- "$base/models" 2>/dev/null)"; rc=$?
  fi
  if [ "$rc" -eq 6 ]; then
    # The host cannot resolve the name: it is probably a Compose service name. Read it the way the diary does.
    rm -f "$work/body"
    in_network_get "$base/models" "$key"; rc=$?
    case "$rc" in
      0) echo "NOTICE: the address in $label does not resolve on the host; its model list was read from inside the diary container's network" ;;
      70) refuse "the address in $label does not resolve on the host (curl exit 6) and no diary container is running to resolve it as the diary does; start the diary or use an address the host can reach"
          return 1 ;;
      *) refuse "the router named by $label could not be reached from inside the diary container either (exit $rc); a router that cannot be read blocks the cutover"
         return 1 ;;
    esac
  fi
  if [ "$rc" -ne 0 ]; then
    refuse "the router named by $label could not be reached (curl exit $rc); a router that cannot be read blocks the cutover"
    return 1
  fi
  if [ "$status" != 200 ]; then
    refuse "the router named by $label answered HTTP $status to its model list (for 401 or 403 check its API key setting); expected 200"
    return 1
  fi
  if ! jq -e '(.data | type) == "array"' "$work/body" >/dev/null 2>&1; then
    refuse "the router named by $label did not return a model list"
    return 1
  fi
  jq -r '.data[]? | select(type == "object" and (.id | type) == "string" and .id != "")
         | select(((.status | if type == "object" then .args else null end) | if type == "array" then . else [] end
                   | any(. == "--embedding" or . == "--embeddings" or . == "--reranking" or . == "--rerank")) | not)
         | .id' "$work/body" > "$out" 2>/dev/null || { refuse "the model list of the router named by $label could not be read"; return 1; }
  if [ ! -s "$out" ]; then
    refuse "the router named by $label serves no chat model"
    return 1
  fi
  return 0
}

is_served() { [ -n "$2" ] && grep -Fxq -- "$2" "$1"; }

# resolve ROLE FILE ID_KEY ID FALLBACK_KEY FALLBACK: ROLE is "chat" or "aux". Reports a pass, a notice or a refusal.
resolve() {
  local role="$1" file="$2" id_key="$3" id="$4" fb_key="$5" fb="$6"
  if is_served "$file" "$id"; then
    echo "diary $role model: the id set in $id_key is served"
  elif is_served "$file" "$fb"; then
    echo "NOTICE: diary $role model: the id set in $id_key is not served; the explicit fallback set in $fb_key is, and the diary will use it"
  elif [ -n "$fb" ]; then
    refuse "the id set in $id_key is not served by the router, and the fallback set in $fb_key is not served either; the diary would refuse every answer"
  else
    refuse "the id set in $id_key is not served by the router and $fb_key is not set in the diary service's resolved environment; the diary would refuse every answer (set $id_key to a served id, or map $fb_key into the diary service in the deployed Compose files and set it to a served id)"
  fi
}

fetch_chat_ids LLM_BASE_URL "$chat_url" "$chat_key" "$work/chat.ids" && chat_ok=1 || chat_ok=0
if [ "$aux_url" = "$chat_url" ] && [ "$aux_key" = "$chat_key" ]; then
  aux_ok=$chat_ok
  if [ "$chat_ok" = 1 ]; then cp "$work/chat.ids" "$work/aux.ids"; fi
else
  fetch_chat_ids LLM_AUX_BASE_URL "$aux_url" "$aux_key" "$work/aux.ids" && aux_ok=1 || aux_ok=0
fi

if [ "$chat_ok" = 1 ]; then resolve chat "$work/chat.ids" LLM_CHAT_MODEL "$chat_id" LLM_CHAT_FALLBACK_MODEL "$chat_fallback"; fi
if [ "$aux_ok" = 1 ]; then resolve aux "$work/aux.ids" LLM_AUX_MODEL "$aux_id" LLM_AUX_FALLBACK_MODEL "$aux_fallback"; fi

if [ "$refused" != 0 ]; then
  echo "diary model check failed; the cutover is refused before anything was changed (#2105)." >&2
  exit 1
fi
echo "diary model check passed (chat and aux resolve to served chat models)."
exit 0
