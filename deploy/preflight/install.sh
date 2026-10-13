#!/usr/bin/env bash
# Installs the whole preflight directory into the live tools folder and verifies the copy (#1597).
# up.sh fails closed unless diary-image-guard.sh sits beside it, and it pipes the resolved Compose
# config through check.php, so refreshing up.sh alone leaves every guarded deploy (and a Diary
# overlay) unable to start anything. Run on the Docker host from a checkout or an unpacked release:
#   bash deploy/preflight/install.sh [DEST]     # DEST defaults to /mnt/docker/appdata/cowork/tools/preflight
# Required files must all exist in the source; web-env-keys.txt is advisory and copied when present.
set -euo pipefail
src="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
dest="${1:-/mnt/docker/appdata/cowork/tools/preflight}"
required=(up.sh diary-image-guard.sh check.php)
optional=(web-env-keys.txt)
for f in "${required[@]}"; do
  [[ -f "$src/$f" ]] || { echo "error: $src/$f is missing; not installing a partial preflight" >&2; exit 1; }
done
for f in up.sh diary-image-guard.sh; do
  bash -n "$src/$f" || { echo "error: $src/$f does not parse; not installing" >&2; exit 1; }
done
mkdir -p "$dest"
copied=()
for f in "${required[@]}" ${optional[@]+"${optional[@]}"}; do
  [[ -f "$src/$f" ]] || continue
  # Copy beside the target, then rename: a reader never sees a half-written file.
  cp "$src/$f" "$dest/.$f.new"
  case "$f" in *.sh) chmod 755 "$dest/.$f.new" ;; *) chmod 644 "$dest/.$f.new" ;; esac
  mv -f "$dest/.$f.new" "$dest/$f"
  copied+=("$f")
done
for f in "${required[@]}"; do
  [[ -f "$dest/$f" ]] && cmp -s "$src/$f" "$dest/$f" || { echo "error: $dest/$f is missing or differs after install" >&2; exit 1; }
done
echo "installed preflight into $dest: ${copied[*]}"
