# Model-specific context calibration

Isolated inference-host experiment authorized on 2026-09-12. This is an operator tool,
not a background job and not a production-provider replacement.

> Archived in #846: the calibration and benchmark scripts (`calibrate.py`,
> `catalog.py`, `benchmark.py`, `test_calibration.py`) were removed from main; see
> git history at `84eeb471`. This README and the accompanying Compose example stay
> (`services/model-manager/tests/test_download_auth.py` reads the Compose file).

## Qualification scope

A completed synthetic near-capacity prompt can establish capacity for its exact runtime,
model, KV-cache configuration and concurrency profile. It does not establish reasoning
quality, vision support or multi-session capacity. Compare complete configurations and
include cold-load time; a warm generation rate alone cannot qualify a replacement.

Keep actual installation profiles, model-residency state, raw telemetry and restoration
receipts in a local operator archive excluded from Git. Recheck any target profile before
using historical capacity results.

## Experiment configuration

This archived experiment's Compose file is an operator example, not a live inventory.
Select the model runtime, device bindings, port bindings, authentication token, read-only
model mounts, and independent configuration/state roots for an isolated test host. Review
the actual configuration before running anything. The Docker socket is privileged; a
discovery whitelist is not an authorization boundary. No public tunnel is implied.

Keep production and candidate residency within a measured shared-memory budget. Check
restoration after interruption; a local process cannot guarantee recovery through a host
or network failure. Raw host telemetry and installation configuration belong in the local
operator record, separate from generic workload and qualification evidence.

## What is remembered

`calibrate.py` writes an atomic trial record and sampled JSONL memory/state log
locally and copies them to the server's `results/calibration/` directory. The
identity includes model checksum evidence, backend image, kernel/GPU, complete
load configuration and workload version. Gemma and Qwen have different records.
Passing identical trials are reused; retries archive earlier failures.

`catalog.py` distinguishes allocation from near-capacity validation. A successful
4k prompt at 256k allocated context does not qualify as a verified 256k profile.
Qualification requires a completed prompt using at least 95% of configured
context, marker recall, no memory guard events and at least 4 GiB host headroom.
Records retain actual prompt counts, generated output, timings and scope. These
synthetic tests do not establish language quality, vision memory needs or
multi-session performance. Keep space for the desired reasoning/output budget.

No calibration result is automatically transferred to a different backend build.
Noevia separately records live allocation observations per tenant/provider/model
and always rechecks the live backend before using a value. Observations are not
stress-test certificates. Cold models load before the check, preventing the
generic 8k fallback from being mistaken for that model's real allocation.

## Running a trial

Needs the archived scripts (git history at `84eeb471`). Run from an authorized operator workstation. Export a Model Loader
recommendation's `values` as JSON first. Server-side model checksum evidence must
exist at `results/model-sha256.txt`. Review `HOST`, `ROOT`, `TEST`, `PROD`, device
paths, memory reserve and compose settings before using this on another host.

```sh
python3 calibrate.py --recommendation gemma-recommended.json \
  --results results --test-model gemma4-e4b-test \
  --native-context 131072 --context 131072 --prompt-tokens 128000
python3 catalog.py results > results/catalog.json
python3 -m unittest discover -p 'test_*.py' -v
```

Bound prompt-cache RAM using the target profile's shared-memory budget. Upstream
recommendations may omit integrated-GPU allocations or other services. Record any
cache/layer overrides in the trial fingerprint and validate their quality implications.

Maximize context per model by testing the native ceiling first within a bounded
memory envelope. If a trial fails, retain the failure and test smaller context
or different cache/layer settings as separate fingerprints. Compare performance
as well as capacity; do not silently reduce GPU layers or quantize caches and
call the resulting profile equivalent.

### Authentication before startup

The manager has Docker socket access; review port publication for the selected test host. Compose requires a
non-empty `MODEL_LOADER_TOKEN`; generate a random value (for example with
`openssl rand -hex 32`) and store it in a private, untracked `.env` beside the
Compose file or in the deployment environment. Send it as `X-Model-Loader-Token`
for API requests. Only `/api/v1/health` is public; HTML pages also require the
header. Do not place the token in URLs or commit it. Run
`docker compose build --pull model-loader` before `docker compose up`; the
Compose file builds `../../services/model-manager` instead of reusing the old
pre-authentication `model-loader-test:e11a6ec` image.
