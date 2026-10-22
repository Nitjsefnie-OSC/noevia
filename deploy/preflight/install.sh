#!/usr/bin/env bash
# Installs the whole preflight directory into the live tools folder and verifies the copy (#1597).
# up.sh fails closed unless diary-image-guard.sh sits beside it, and it pipes the resolved Compose
# config through check.php, so refreshing up.sh alone leaves every guarded deploy (and a Diary
# overlay) unable to start anything. Both overlay scripts also run diary-models-check.sh (#2105)
# before they change anything. Run on the Docker host from a checkout or an unpacked release:
#   bash deploy/preflight/install.sh [--replace-local-up-sh] [DEST]
#                                       # DEST defaults to /mnt/docker/appdata/cowork/tools/preflight
# Required files must all exist in the source; web-env-keys.txt is advisory and copied when present.
#
# Local edits (#2113): some installations add their own steps around `docker compose up` in the installed
# up.sh. The install does not delete them silently. An installed up.sh is replaced only when it is
# byte-identical to the new one or to a released version (up.sh.released-sha256, beside this script).
# Any other installed up.sh makes the install stop before anything is copied, naming the file; nothing
# is changed. To replace it anyway, pass --replace-local-up-sh: the installed file is first kept as
# up.sh.local-<UTC time>.bak beside it, so the local steps can be merged back into the new up.sh.
set -euo pipefail
src="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
dest=""
replace_local=0
for arg in "$@"; do
  case "$arg" in
    --replace-local-up-sh) replace_local=1 ;;
    -*) echo "usage: install.sh [--replace-local-up-sh] [DEST]" >&2; exit 2 ;;
    *) [[ -z "$dest" ]] || { echo "usage: install.sh [--replace-local-up-sh] [DEST]" >&2; exit 2; }; dest="$arg" ;;
  esac
done
dest="${dest:-/mnt/docker/appdata/cowork/tools/preflight}"
required=(up.sh diary-image-guard.sh check.php diary-models-check.sh)
optional=(web-env-keys.txt)
for f in "${required[@]}"; do
  [[ -f "$src/$f" ]] || { echo "error: $src/$f is missing; not installing a partial preflight" >&2; exit 1; }
done
for f in up.sh diary-image-guard.sh diary-models-check.sh; do
  bash -n "$src/$f" || { echo "error: $src/$f does not parse; not installing" >&2; exit 1; }
done

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else return 1; fi
}

# #2113: an installed up.sh that is neither the new one nor a released one holds local edits. Decide before
# anything is copied, so a refusal leaves the whole installation exactly as it was.
backup_up_sh=""
if [[ -e "$dest/up.sh" || -L "$dest/up.sh" ]]; then
  new_sum="$(sha256_of "$src/up.sh")" || { echo "error: neither sha256sum nor shasum is available to compare the installed up.sh; not installing" >&2; exit 1; }
  old_sum="$(sha256_of "$dest/up.sh")" || old_sum=""
  known=0
  if [[ -n "$old_sum" && "$old_sum" == "$new_sum" ]]; then
    known=1
  elif [[ -n "$old_sum" && -f "$src/up.sh.released-sha256" ]]; then
    released="$(awk '$1 !~ /^#/ && NF { print $1 }' "$src/up.sh.released-sha256")"
    if grep -Fxq -- "$old_sum" <<<"$released"; then known=1; fi
  fi
  if [[ "$known" != 1 ]]; then
    if [[ "$replace_local" != 1 ]]; then
      echo "error: $dest/up.sh is not a released version of up.sh (it has local edits, or $src/up.sh.released-sha256 is missing); not installing, nothing was changed." >&2
      echo "       Compare it with the new one:  diff $dest/up.sh $src/up.sh" >&2
      echo "       To replace it anyway (the old file is kept beside it as up.sh.local-<UTC time>.bak), run again with --replace-local-up-sh" >&2
      exit 1
    fi
    backup_up_sh="$dest/up.sh.local-$(date -u +%Y%m%dT%H%M%SZ).bak"
    [[ ! -e "$backup_up_sh" ]] || { echo "error: $backup_up_sh already exists; not installing" >&2; exit 1; }
    cp -p "$dest/up.sh" "$backup_up_sh" && cmp -s "$dest/up.sh" "$backup_up_sh" \
      || { echo "error: could not keep a copy of the local up.sh at $backup_up_sh; not installing" >&2; exit 1; }
    echo "kept the locally edited up.sh as $backup_up_sh; merge its local steps into the new up.sh if you still need them"
  fi
fi

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
