#!/usr/bin/env bash
# seed-search-trusted.sh: writes the lists the image prints, atomically, never over an existing
# file without --force, and nothing at all when the image read fails. Synthetic names only.
set -u
here="$(cd -- "$(dirname -- "$0")" && pwd)"
script="$here/seed-search-trusted.sh"
work="$(mktemp -d "${TMPDIR:-/tmp}/seed-trusted-test.XXXXXX")"
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin" "$work/config"
cat > "$work/bin/docker" <<'SHIM'
#!/usr/bin/env bash
echo "$*" >> "$SEED_TEST_LOG"
[ "${SEED_TEST_FAIL:-0}" = 1 ] && exit 1
printf '{\n "quantisers": ["synthetic-q"],\n "labs": ["synthetic-l"]\n}\n'
SHIM
chmod +x "$work/bin/docker"
export PATH="$work/bin:$PATH" SEED_TEST_LOG="$work/log"
fails=0
check() { if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
out="$work/config/search-trusted.json"

bash "$script" example/model-manager:1 "$work/config" > /dev/null
check "writes the image's lists" "grep -q synthetic-q '$out' && grep -q synthetic-l '$out'"
check "runs the image without network" "grep -q -- '--network none' '$work/log'"
check "no temporary file left" "[ -z \"\$(ls -A '$work/config' | grep -v '^search-trusted.json$')\" ]"
echo '{"quantisers":[],"labs":[]}' > "$out"
bash "$script" example/model-manager:1 "$work/config" > /dev/null
check "an existing file is kept" "grep -q '\"quantisers\":\[\]' '$out'"
bash "$script" example/model-manager:1 "$work/config" --force > /dev/null
check "--force replaces it" "grep -q synthetic-q '$out'"
rm -f "$out"
SEED_TEST_FAIL=1 bash "$script" example/model-manager:1 "$work/config" > /dev/null 2>&1
check "a failed read writes nothing" "[ ! -e '$out' ] && [ -z \"\$(ls -A '$work/config')\" ]"
bash "$script" 'bad image;rm' "$work/config" > /dev/null 2>&1
check "a bad image reference is refused" "[ \$? -eq 2 ]"
bash "$script" example/model-manager:1 "$work/config" --other > /dev/null 2>&1
check "an unknown option is refused" "[ \$? -eq 2 ]"
[ "$fails" -eq 0 ] || { echo "$fails failed"; exit 1; }
echo "all passed"
