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
bash deploy/preflight/install.sh "${PREFLIGHT_INSTALL_DIR:?Select the install directory}"
```

```sh
# From the repository root, using its Compose file and .env. --build is refused (it would rebuild
# and retag cowork-diary:*, #1148); build a named non-diary service first if needed.
bash deploy/preflight/up.sh -- -d --no-build

# Installed wrapper, with explicit operator-selected project and environment:
COWORK_PROJECT_DIR="${COMPOSE_PROJECT_DIR:?Select the Compose project}" \
bash "${PREFLIGHT_INSTALL_DIR:?Select the installed helper}/up.sh" \
  --env-file "${COMPOSE_ENV_FILE:?Select the environment file}" -- \
  -d --no-build --wait --wait-timeout 120
```

## Diary model settings (#2105)

The Diary refuses to answer when its configured chat or aux model id is not served by the chat
router and no explicit fallback is set. `diary-models-check.sh` is installed beside `up.sh` and run by
`deploy/examples/overlay-release.sh` and `deploy/examples/diary-overlay.sh` before they build, stop or
change anything:

```sh
bash "${PREFLIGHT_INSTALL_DIR:?Select the installed helper}/diary-models-check.sh" \
  --env-file "${COMPOSE_ENV_FILE:?Select the environment file the cutover deploys}"
```

It reads `DIARY_CHAT_MODEL`, `DIARY_AUX_MODEL` (unset means the chat id, as in Compose), the optional
`LLM_CHAT_FALLBACK_MODEL` / `LLM_AUX_FALLBACK_MODEL`, and `INFERENCE_BASE_URL` / `INFERENCE_API_KEY`
(plus `AUX_INFERENCE_BASE_URL` / `AUX_INFERENCE_API_KEY` for a separate aux router) from that file, then
makes one read-only `GET <router>/models`. Never a slot query, completion or load, so it cannot wake a
model; a sleeping model counts as served. An id that names an embedding or reranking section is not a chat
model. The cutover is refused when an effective id is not served: the configured id, else the matching
explicit fallback key, else refusal (the Diary's implicit "follow the chat model" substitute for aux is not
accepted, because nobody named it). It also fails closed on a missing key, an unreachable router, any
answer other than HTTP 200 (redirects are not followed) or a body that is not a model list. Messages name
keys only: no model id, address or credential is printed, and the credential is sent through a curl config
pipe, not on the command line. Needs `curl` and `jq` on the host. Set the ids in the operator's private
environment file; the repository carries no model ids. Compose maps the two fallback keys into the Diary
container, so a fallback in the environment file is the one the Diary will use.

## Implementation defaults

`install.sh` accepts a destination argument and defaults to
`/mnt/docker/appdata/cowork/tools/preflight`. When no project is explicitly pinned,
`up.sh` uses `COWORK_PROJECT_DIR`, or its existing default Compose Manager directory
`/boot/config/plugins/compose.manager/projects/Cowork` when that directory exists.
These are implementation defaults, not statements about any running installation.
Select actual paths locally and retain them outside version control.

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
Diary container can resolve `model-loader`. Resolve a failing configuration through the
current isolation contract before attempting an authorized release.

Named volumes with driver options need separate verification and are refused by
this helper; use ordinary binds for local paths so they can be inspected.

This is a deployment preflight, not a Docker daemon policy. Starting directly
through Compose Manager's GUI or plain `docker compose up` bypasses it. Do not
claim the web container can resolve host symlinks correctly. Keep existing state
bindings; this does not migrate to managed volumes or change the real Diary mount.

Verification uses synthetic PHP path tests and wrapper failure/argument tests. Qualifying
those tests does not prove a particular installation passes; validate its effective Compose
inputs separately without publishing their values.
