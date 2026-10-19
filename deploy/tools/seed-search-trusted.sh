#!/usr/bin/env bash
# Seed the model manager's trusted publisher sets for the native search (sbstndalton/noevia#1318
# step 1c). The native model manager reads them from SEARCH_TRUSTED_PATH (default
# /config/search-trusted.json, i.e. $LLAMACPP_CONFIG_DIR/search-trusted.json on the host).
# #2073: seed from the verified previous image that still contains the Python services source,
# before replacing it with the mandatory native image. The new image has no Python/app and
# refuses missing or empty trust sets; it cannot seed these lists or select a child fallback.
# Copying the previous image's lists preserves ranking inputs across the cutover.
# The lists are read from the image at deploy time; they are not kept in any repository.
#
#   deploy/tools/seed-search-trusted.sh <previous-model-manager-image> <llamacpp-config-dir> [--force]
#
# An existing file is left alone unless --force is given. The image (already present: no pull)
# runs read-only, without network, capabilities or privilege gain, in 256 MiB, and is removed
# afterwards. Its output is validated with jq before anything is written. Needs docker and jq.
set -u -o pipefail
usage() { echo "usage: seed-search-trusted.sh <image> <config-dir> [--force]" >&2; exit 2; }
fail() { echo "seed-search-trusted.sh: $*" >&2; exit 1; }
[ $# -ge 2 ] && [ $# -le 3 ] || usage
image="$1"; dir="$2"; force="${3:-}"
[ -z "$force" ] || [ "$force" = "--force" ] || usage
image_re='^[A-Za-z0-9][A-Za-z0-9_.:/@-]*$'
[[ $image =~ $image_re ]] || { echo "seed-search-trusted.sh: bad image reference" >&2; exit 2; }
[ -d "$dir" ] || { echo "seed-search-trusted.sh: $dir is not a directory" >&2; exit 2; }
command -v jq > /dev/null || fail "jq is required"
target="$dir/search-trusted.json"
if [ -e "$target" ] && [ "$force" != "--force" ]; then
  echo "seed-search-trusted.sh: $target exists; left unchanged (use --force to replace)"
  exit 0
fi
# Inside the image: both sets non-empty text, and the printed JSON parses back to the same value.
code='import json, sys
sys.path.insert(0, "/srv")
from app import discover
q, l = discover.TRUSTED_QUANTISERS, discover.TRUSTED_LABS
assert q and l, "empty trusted set"
assert all(isinstance(x, str) and x for x in q | l), "non-text entry"
value = {"quantisers": sorted(q), "labs": sorted(l)}
text = json.dumps(value, indent=1)
assert json.loads(text) == value
print(text)'
tmp="$(mktemp "$dir/.search-trusted.XXXXXX")" || fail "cannot create a temporary file in $dir"
trap 'rm -f "$tmp"' EXIT
docker run --rm --pull never --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --memory 256m \
  --entrypoint python "$image" -I -c "$code" > "$tmp" \
  || fail "reading the lists from $image failed; nothing written"
# Exactly one JSON object, keys exactly quantisers and labs, each a non-empty array of non-empty
# strings (the model manager checks the shape again at startup).
jq -se 'length == 1 and (.[0] | type == "object" and (keys == ["labs", "quantisers"])
        and all(.[]; type == "array" and length > 0 and all(.[]; type == "string" and length > 0)))' \
  "$tmp" > /dev/null 2>&1 || fail "unexpected output from $image; nothing written"
chmod 0644 "$tmp" && mv -f "$tmp" "$target" || fail "could not write $target; nothing written"
trap - EXIT
echo "seed-search-trusted.sh: wrote $target; restart the model manager to load it"
