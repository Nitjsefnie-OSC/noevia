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

**Locally extended `up.sh` (#2113).** An installation may add its own steps around `docker compose up`
in the installed `up.sh`. `install.sh` never deletes them silently. It replaces an installed `up.sh`
only when that file is byte-identical to the new one or to a released version (the sha256 list in
`up.sh.released-sha256`, which is appended whenever `up.sh` changes; a test fails until it is). Any other
installed `up.sh` counts as locally edited: the install stops before it copies anything, prints
`diff <installed up.sh> <new up.sh>` to see the difference, and changes nothing (exit 1). To replace it
anyway, run `install.sh --replace-local-up-sh "${PREFLIGHT_INSTALL_DIR}"`: the edited file is first kept
beside it as `up.sh.local-<UTC time>.bak` (and the install stops if that copy cannot be made), then the
whole directory is installed. Merge the kept local steps into the new `up.sh` by hand if they are still
needed. A first install, or an installed `up.sh` that is already current or an older release, needs no flag.

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
  --env-file "${COMPOSE_ENV_FILE:?Select the environment file the cutover deploys}" \
  --project-dir "${COMPOSE_PROJECT_DIR:?Select the Compose project}"
```

It checks what the Diary container will actually receive, not what the environment file says. It runs
`docker compose --env-file <file> config --format json` in the Compose project (the same project files and
environment file the deploy uses) and reads the `diary` service's resolved environment: `LLM_CHAT_MODEL`,
`LLM_AUX_MODEL` (unset or `default` means the chat id, as in the Diary), `LLM_BASE_URL`, `LLM_API_KEY`, the
optional `LLM_AUX_BASE_URL` / `LLM_AUX_API_KEY`, and the explicit `LLM_CHAT_FALLBACK_MODEL` /
`LLM_AUX_FALLBACK_MODEL`. A fallback counts only when the deployed Compose files map it into the Diary
service; a value that sits in the environment file but is not mapped is not seen by the Diary and is
ignored, so the check refuses. The shipped Compose files map the two fallback keys. An operator's own
project files must do the same. The environment file itself is never parsed by the check (Compose
interpolates it).

It then makes one read-only `GET <router>/models`. Never a slot query, completion or load, so it cannot
wake a model; a sleeping model counts as served. An id that names an embedding or reranking section is not
a chat model. The cutover is refused when an effective id is not served: the configured id, else the
matching explicit fallback, else refusal.

**Router addresses that are Compose service names (#2111).** The Diary may reach its router by the name of
another service in the same Compose project, which the Docker host cannot resolve. When the host's `curl`
reports that the name does not resolve (exit 6), the same single GET is made from inside the running `diary`
container instead (`docker compose ps -q diary`, then `docker exec -i`), with the Diary image's own `python`
and the name resolved by the Diary's network. The request is the same read-only GET: no redirects, a 10 s
timeout, a 4 MiB cap. The address and the credential are sent on the exec's standard input, never on a
command line. Nothing is started, built or created. Only an address the host cannot resolve takes this
path; any other failure (connection refused, timeout, a non-200 answer, a body that is not a model list)
refuses as before. If no `diary` container is running there is nothing to resolve the name with, so the check
refuses and says so: start the Diary, or use an address the host can reach.

**This check is stricter than the Diary.** It does not accept the Diary's implicit last-resort substitute
for the aux role (follow whatever the chat role resolved to), because nobody named it. It also refuses a
missing router address, where Compose would fill in a default that only means something inside a container.
It fails closed on a Compose configuration that does not resolve, a missing `diary` service, a missing
model key, an unreachable router, any answer other than HTTP 200 (redirects are not followed) or a body
that is not a model list. Messages name keys only: no model id, address or credential is printed, the
resolved configuration (which holds tokens) stays in a private temporary file, and the credential is sent
through a curl config pipe (or the exec's standard input), not on the command line. Needs `docker`, `curl`
and `jq` on the host. Set the
ids in the operator's private environment file; the repository carries no model ids.

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
