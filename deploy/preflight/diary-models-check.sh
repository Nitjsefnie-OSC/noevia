#!/usr/bin/env bash
# #2105: release preflight. Refuses a cutover when the model ids the diary will be configured with are not
# served by the chat router, because the diary (services#2099) then refuses every answer instead of letting
# the router pick a model. Run on the Docker host BEFORE anything is built, stopped or changed:
#   diary-models-check.sh --env-file <the .env the cutover deploys>
# Exit 0: both ids resolve to a served chat model. Exit 1: refused (or failed closed). Exit 2: bad usage.
#
# Keys read from the env file (compose.yaml maps them into the diary container; only key names are printed):
#   DIARY_CHAT_MODEL            -> LLM_CHAT_MODEL, required (unset, empty or the "default" placeholder fails)
#   DIARY_AUX_MODEL             -> LLM_AUX_MODEL, optional: unset, empty or "default" means the chat id (compose.yaml)
#   LLM_CHAT_FALLBACK_MODEL     -> optional explicit substitute for the chat id (diary agent/config.py, services#2099)
#   LLM_AUX_FALLBACK_MODEL      -> optional explicit substitute for the aux id
#   INFERENCE_BASE_URL          -> the chat router, required (the check never guesses an address)
#   INFERENCE_API_KEY           -> optional bearer credential, sent only to the router
#   AUX_INFERENCE_BASE_URL, AUX_INFERENCE_API_KEY -> optional separate aux router (same defaults as compose.yaml)
# Effective id, as the diary resolves it with explicit settings only: the configured id when the router serves
# it as a chat model, else the fallback key's id when that is served, else REFUSED. The diary's last-resort
# "follow whatever chat resolved to" substitute for aux is deliberately NOT accepted here: nobody named it.
# "Served" means listed by GET <router>/models and not launched with an embedding or reranking flag, the same
# test the diary applies. Being asleep still counts as served: this check is read-only. It makes one GET of the
# model list and nothing else (no slot query, no completion, no load), so it can never wake a model.
# Fails closed on: an unreadable env file, a missing key above, a router that is unreachable, answers with a
# status other than 200 (redirects are not followed), or sends a body that is not a model list.
# Secrets: the credential travels on a curl config pipe (never argv) and no value from the env file is printed,
# neither ids, addresses nor credentials; messages name keys only. Needs bash, curl and jq.
{ set +x; } 2>/dev/null
set -uo pipefail

env_file=""
usage="usage: diary-models-check.sh --env-file <path to the .env the cutover deploys>"
while [ $# -gt 0 ]; do
  case "$1" in
    --env-file) env_file="${2-}"; shift; [ $# -gt 0 ] && shift ;;
    --env-file=*) env_file="${1#--env-file=}"; shift ;;
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
for tool in curl jq; do
  command -v "$tool" >/dev/null 2>&1 || fail_closed "$tool is required for this check and was not found; not deploying"
done

# env_get KEY: sets env_present (0/1) and env_value from the last assignment of KEY in the file. The file is only
# read, never sourced. Surrounding quotes are removed; an unquoted value ends at " #" like compose.
env_present=0; env_value=""
env_get() {
  local key="$1" line rest q
  env_present=0; env_value=""
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    [[ "$line" =~ ^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=(.*)$ ]] || continue
    [ "${BASH_REMATCH[2]}" = "$key" ] || continue
    rest="${BASH_REMATCH[3]}"
    rest="${rest#"${rest%%[![:space:]]*}"}"
    q="${rest:0:1}"
    if [ "$q" = '"' ] || [ "$q" = "'" ]; then
      rest="${rest:1}"; rest="${rest%%"$q"*}"
    else
      rest="${rest%% \#*}"; rest="${rest%"${rest##*[![:space:]]}"}"
    fi
    env_present=1; env_value="$rest"
  done < "$env_file"
}

PLACEHOLDER=default

env_get DIARY_CHAT_MODEL; chat_id="$env_value"
if [ -z "$chat_id" ] || [ "$chat_id" = "$PLACEHOLDER" ]; then
  refuse "DIARY_CHAT_MODEL is missing, empty or the placeholder in the environment file; set it to a model id the chat router serves"
  chat_id=""
fi
env_get DIARY_AUX_MODEL; aux_id="$env_value"
if [ -z "$aux_id" ] || [ "$aux_id" = "$PLACEHOLDER" ]; then aux_id="$chat_id"; fi   # compose.yaml and the diary do the same
env_get LLM_CHAT_FALLBACK_MODEL; chat_fallback="$env_value"
env_get LLM_AUX_FALLBACK_MODEL; aux_fallback="$env_value"

env_get INFERENCE_BASE_URL; chat_url="$env_value"
env_get INFERENCE_API_KEY; chat_key="$env_value"
if [ -z "$chat_url" ]; then
  refuse "INFERENCE_BASE_URL is missing or empty in the environment file, so the router's served models cannot be read"
fi
env_get AUX_INFERENCE_BASE_URL; aux_url="$env_value"; [ -n "$aux_url" ] || aux_url="$chat_url"
env_get AUX_INFERENCE_API_KEY
if [ "$env_present" = 1 ]; then aux_key="$env_value"; else aux_key="$chat_key"; fi   # compose: ${AUX_KEY-${INFERENCE_API_KEY:-}}

if [ "$refused" != 0 ]; then
  echo "diary model check failed; the cutover is refused before anything was changed (#2105)." >&2
  exit 1
fi

work="$(mktemp -d "${TMPDIR:-/tmp}/diary-models-check.XXXXXX")" || fail_closed "cannot create a temporary directory; not deploying"
trap 'rm -rf "$work"' EXIT

# fetch_chat_ids LABEL URL KEY OUTFILE: one read-only GET <URL>/models; writes the served chat-capable ids, one per
# line. LABEL names the key that holds the address, for messages. Returns 0, or 1 after reporting why.
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
    refuse "the id set in $id_key is not served by the router and $fb_key is not set; the diary would refuse every answer (set $id_key, or $fb_key, to a served id)"
  fi
}

fetch_chat_ids INFERENCE_BASE_URL "$chat_url" "$chat_key" "$work/chat.ids" && chat_ok=1 || chat_ok=0
if [ "$aux_url" = "$chat_url" ] && [ "$aux_key" = "$chat_key" ]; then
  aux_ok=$chat_ok
  if [ "$chat_ok" = 1 ]; then cp "$work/chat.ids" "$work/aux.ids"; fi
else
  fetch_chat_ids AUX_INFERENCE_BASE_URL "$aux_url" "$aux_key" "$work/aux.ids" && aux_ok=1 || aux_ok=0
fi

if [ "$chat_ok" = 1 ]; then resolve chat "$work/chat.ids" DIARY_CHAT_MODEL "$chat_id" LLM_CHAT_FALLBACK_MODEL "$chat_fallback"; fi
if [ "$aux_ok" = 1 ]; then resolve aux "$work/aux.ids" DIARY_AUX_MODEL "$aux_id" LLM_AUX_FALLBACK_MODEL "$aux_fallback"; fi

if [ "$refused" != 0 ]; then
  echo "diary model check failed; the cutover is refused before anything was changed (#2105)." >&2
  exit 1
fi
echo "diary model check passed (chat and aux resolve to served chat models)."
exit 0
