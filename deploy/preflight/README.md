# Writable boot-storage preflight

Run this on the Docker host before deployment. Unraid already provides PHP;
other hosts need PHP 8 or later if using this helper. No model, account or storage
configuration is changed by the check. It inspects resolved Compose JSON and does
not print environment values, credentials or volume driver options.

Install the whole directory, never `up.sh` alone: `up.sh` refuses to start anything unless
`diary-image-guard.sh` is beside it (#1148) and pipes the resolved config through `check.php` (#1597).

```sh
# On the Docker host, from a checkout or unpacked release: copies up.sh, diary-image-guard.sh,
# check.php and web-env-keys.txt into tools/preflight/ and verifies the copy.
bash deploy/preflight/install.sh                      # default /mnt/docker/appdata/cowork/tools/preflight
```

```sh
# From the repository root, using its Compose file and .env. --build is refused (it would rebuild
# and retag cowork-diary:*, #1148); build a named non-diary service first if needed.
bash deploy/preflight/up.sh -- -d --no-build

# DaServer, from any directory (the wrapper cds to the Compose Manager project,
# or $COWORK_PROJECT_DIR if set):
bash /mnt/docker/appdata/cowork/tools/preflight/up.sh \
  --env-file /mnt/docker/appdata/cowork/config/.env -- \
  -d --no-build --wait --wait-timeout 120
```

Global Compose options go before `--`; `up` options go after it. The wrapper
resolves the same files/environment, runs the check, and starts services only
if both Compose resolution and validation succeed. It preserves all supplied
Compose options and does not select different volumes.

For a read-only check:

```sh
docker compose config --format json | php deploy/preflight/check.php --config-json -
```

Rejects writable binds inside `/boot`, ancestor mounts exposing `/boot`, symlink
aliases (including missing descendants), and alternate mountpoints on a separate
boot device. Read-only mounts and normal Docker managed volumes are allowed.
Also blocks (D1) a `model-loader` service whose `MODEL_LOADER_TOKEN` is unset or
shorter than 32 characters, a `web` service without the same token, and a `diary`
service sharing any network (or host networking) with `model-loader`. The token is
compared, never printed. `overlay-release.sh` additionally rolls back if the running
Diary container can resolve `model-loader`. The live file fails this check until the
operator steps in `docs/research-master-container.md` are applied.

Named volumes with driver options need separate verification and are refused by
this helper; use ordinary binds for local paths so they can be inspected.

This is a deployment preflight, not a Docker daemon policy. Starting directly
through Compose Manager's GUI or plain `docker compose up` bypasses it. Do not
claim the web container can resolve host symlinks correctly. Keep existing state
bindings; this does not migrate to managed volumes or change the real Diary mount.

Verification: synthetic PHP path tests run on Unraid, wrapper failure/argument tests
run locally, and the resolved live Cowork configuration passes without changes.
