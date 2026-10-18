#!/usr/bin/env bash
# seed-search-trusted.sh: writes the lists the image prints, atomically and 0644, never over an
# existing file without --force, and nothing at all when the image read fails, prints garbage or
# empty sets, or the file cannot be moved into place. Synthetic names only. Needs jq.
set -u
here="$(cd -- "$(dirname -- "$0")" && pwd)"
script="$here/seed-search-trusted.sh"
work="$(mktemp -d "${TMPDIR:-/tmp}/seed-trusted-test.XXXXXX")"
trap 'chmod -R u+w "$work" 2>/dev/null; rm -rf "$work"' EXIT
mkdir -p "$work/bin" "$work/config"
cat > "$work/bin/docker" <<'SHIM'
#!/usr/bin/env bash
echo "$*" >> "$SEED_TEST_LOG"
case "${SEED_TEST_MODE:-ok}" in
  fail) exit 1 ;;
  garbage) echo 'not json {' ;;
  empty) printf '{"quantisers": [], "labs": ["synthetic-l"]}\n' ;;
  extra) printf '{"quantisers": ["q"], "labs": ["l"], "x": []}\n' ;;
  two) printf '{"quantisers": ["q"], "labs": ["l"]}\n{"quantisers": ["q"], "labs": ["l"]}\n' ;;
  *) printf '{\n "quantisers": ["synthetic-q"],\n "labs": ["synthetic-l"]\n}\n' ;;
esac
SHIM
chmod +x "$work/bin/docker"
export PATH="$work/bin:$PATH" SEED_TEST_LOG="$work/log"
fails=0
check() { if [ "$2" = yes ]; then echo "ok   $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
is() { if eval "$1"; then echo yes; else echo no; fi; }
out="$work/config/search-trusted.json"
only_target() { [ "$(ls -A "$work/config")" = "search-trusted.json" ]; }
empty_dir() { [ -z "$(ls -A "$work/config")" ]; }
run() { SEED_TEST_MODE="$1" bash "$script" example/model-manager:1 "$work/config" ${2:+"$2"} > /dev/null 2>&1; echo $?; }

st=$(run ok)
check "writes the image's lists (exit 0)" "$(is "[ $st -eq 0 ] && grep -q synthetic-q '$out' && grep -q synthetic-l '$out'")"
check "the file is 0644" "$(is "[ \"\$(stat -c %a '$out')\" = 644 ]")"
check "no temporary file left" "$(is only_target)"
for flag in "--network none" "--read-only" "--cap-drop ALL" "--security-opt no-new-privileges" "--pull never" "--memory 256m"; do
  check "docker run has $flag" "$(is "grep -q -- '$flag' '$work/log'")"
done
echo '{"quantisers":["kept"],"labs":["kept"]}' > "$out"
st=$(run ok)
check "an existing file is kept" "$(is "[ $st -eq 0 ] && grep -q kept '$out'")"
st=$(run ok --force)
check "--force replaces it" "$(is "[ $st -eq 0 ] && grep -q synthetic-q '$out'")"
for mode in fail garbage empty extra two; do
  rm -f "$out"
  st=$(run "$mode")
  check "$mode output: exit 1, nothing written" "$(is "[ $st -eq 1 ] && empty_dir")"
done
# A failed move (stub mv that fails): exit 1, and the temporary file is removed.
cat > "$work/bin/mv" <<'SHIM'
#!/usr/bin/env bash
[ "${SEED_TEST_MV_FAIL:-0}" = 1 ] && exit 1
exec /bin/mv "$@"
SHIM
chmod +x "$work/bin/mv"
rm -f "$out"
st=$(SEED_TEST_MV_FAIL=1 run ok)
check "a failed move exits 1 and leaves nothing" "$(is "[ $st -eq 1 ] && empty_dir")"
chmod a-w "$work/config"
st=$(run ok)
check "an unwritable directory exits 1" "$(is "[ $st -eq 1 ] && empty_dir")"
chmod u+w "$work/config"
st=$(SEED_TEST_MODE=ok bash "$script" 'bad image;rm' "$work/config" > /dev/null 2>&1; echo $?)
check "a bad image reference is refused (exit 2)" "$(is "[ $st -eq 2 ]")"
st=$(run ok --other)
check "an unknown option is refused (exit 2)" "$(is "[ $st -eq 2 ]")"
[ "$fails" -eq 0 ] || { echo "$fails failed"; exit 1; }
echo "all passed"
