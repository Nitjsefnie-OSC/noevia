#!/usr/bin/env bash
# Seed the model manager's trusted publisher sets for the native search (sbstndalton/noevia#1318
# step 1c). The native model manager reads them from SEARCH_TRUSTED_PATH (default
# /config/search-trusted.json, i.e. $LLAMACPP_CONFIG_DIR/search-trusted.json on the host) and
# treats a missing file as empty sets, which would change the search ranking. This writes the
# file with the lists the services app in the given image defines today, so nothing changes.
# The lists are read from the image at deploy time; they are not kept in any repository.
#
#   deploy/tools/seed-search-trusted.sh <model-manager-image> <llamacpp-config-dir> [--force]
#
# An existing file is left alone unless --force is given. The image runs with no network and is
# removed afterwards; only `python` inside it is used.
set -u -o pipefail
usage() { echo "usage: seed-search-trusted.sh <image> <config-dir> [--force]" >&2; exit 2; }
[ $# -ge 2 ] && [ $# -le 3 ] || usage
image="$1"; dir="$2"; force="${3:-}"
[ -z "$force" ] || [ "$force" = "--force" ] || usage
image_re='^[A-Za-z0-9][A-Za-z0-9_.:/@-]*$'
[[ $image =~ $image_re ]] || { echo "seed-search-trusted.sh: bad image reference" >&2; exit 2; }
[ -d "$dir" ] || { echo "seed-search-trusted.sh: $dir is not a directory" >&2; exit 2; }
target="$dir/search-trusted.json"
if [ -e "$target" ] && [ "$force" != "--force" ]; then
  echo "seed-search-trusted.sh: $target exists; left unchanged (use --force to replace)"
  exit 0
fi
code='import json, sys
sys.path.insert(0, "/srv")
from app import discover
q, l = discover.TRUSTED_QUANTISERS, discover.TRUSTED_LABS
assert all(isinstance(x, str) and x for x in q | l)
print(json.dumps({"quantisers": sorted(q), "labs": sorted(l)}, indent=1))'
tmp="$(mktemp "$dir/.search-trusted.XXXXXX")" || exit 1
trap 'rm -f "$tmp"' EXIT
if ! docker run --rm --network none --entrypoint python "$image" -I -c "$code" > "$tmp"; then
  echo "seed-search-trusted.sh: reading the lists from $image failed; nothing written" >&2
  exit 1
fi
# Exactly one JSON object with the two keys (checked again by the model manager at startup).
grep -q '"quantisers"' "$tmp" && grep -q '"labs"' "$tmp" || {
  echo "seed-search-trusted.sh: unexpected output from $image; nothing written" >&2; exit 1; }
chmod 0644 "$tmp"
mv -f "$tmp" "$target"
trap - EXIT
echo "seed-search-trusted.sh: wrote $target; restart the model manager to load it"
