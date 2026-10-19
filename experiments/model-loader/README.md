# Model-specific context calibration

Isolated inference-host experiment authorized on 2026-09-12. This is an operator tool,
not a background job and not a production-provider replacement.

> Archived in #846: the calibration and benchmark scripts (`calibrate.py`,
> `catalog.py`, `benchmark.py`, `test_calibration.py`) were removed from main; see
> git history at `84eeb471`. This README and the accompanying Compose example stay
> (`services/model-manager/tests/test_download_auth.py` reads the Compose file).

## Current follow-up — 2026-09-13

Production noevia remains `8fa1112`. The guarded Qwen trial passed with 253,944
input tokens at a configured 262,144-token context: correct start-marker recall,
complete output, no guard events and minimum 6.05 GiB host memory available.
The request took 2,140.2 seconds (35.7 minutes), mostly prompt processing.
This qualifies the exact b10920, q8 KV, one-slot synthetic text profile; it does
not establish reasoning quality, vision or concurrent-session capacity.
[Machine-readable evidence](../../docs/evidence/qwen-context-2026-09-13.json).

The test container stopped and production Gemma was restored with its original
32,768-context Vulkan q5_0/q4_0 settings. An independent live slots query confirmed
four idle slots, each with 32,768 tokens. No saved model options changed.

Fingerprint collection reads the actual test container's immutable image ID,
not a mutable local tag. The recorded raw trial and telemetry are also retained
on the deployment host under results/calibration. Historical September 12 results follow;
the Qwen qualification above supersedes their then-unverified capacity status.

## Measured results — 2026-09-12

| Model/configuration | Allocated context | Largest completed prompt | Result |
| --- | ---: | ---: | --- |
| Gemma 4 E4B Q4_K_M, test b10920, all GPU, q8 KV, one slot | 131,072 | 127,992 | Near-capacity verified; correct start-marker recall; 617.8 seconds total; minimum 11.58 GiB host memory available |
| Qwen 3.5 9B UD-Q4_K_XL, upstream recommendation, all GPU, q8 KV, one slot | 212,992 | 36,438 | Loaded and exceeded 32k successfully; correct recall; 133.9 seconds; full capacity not verified |
| Qwen 3.5 9B UD-Q4_K_XL, native ceiling, bounded prompt cache | 262,144 | 4,090 | Load/smoke verified only; minimum 8.32 GiB host memory available |

Three 256-token short generation runs gave median engine rates of 13.75 tok/s
for existing Lemonade and 13.71 tok/s for the 212,992-context test configuration.
There was no meaningful generation-speed improvement. Warm first-token latency
was about 0.49 seconds for Lemonade and 0.90 seconds for the test. The test's first
request included model loading (9.68 seconds until first token). This compares
whole configurations: backend build, KV quantization and slot count differ.

The Gemma profile qualifies for the remembered near-capacity catalog; the Qwen
profiles deliberately do not. Nothing here establishes image or multi-session
capacity. Production Gemma was independently loaded without changing saved options: Lemonade reported 32,768 tokens per slot and four slots. Its 8k UI observation is therefore not the current backend allocation; noevia has an 8k fallback path when allocation is unavailable. Qwen was restored afterward. Production noevia remains on its existing provider/release. The local
cold-load budgeting correction passed 342 web tests, typecheck/build and a real
HTTP regression including auto-routing to a cold Fast model; it is not deployed
to production by this experiment.

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

Needs the archived scripts (git history at `84eeb471`). Run from the trusted operator Mac with SSH access. Export a Model Loader
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

The calibration caps host prompt-cache RAM at 1 GiB. Upstream proposed 14,528 MiB
for Qwen and 8,192 MiB for Gemma, but its cache estimate does not subtract this
integrated GPU's shared allocation or this host's other services. The profile
also removes `cache-reuse`, which llama.cpp disables for these multimodal models.
Both overrides are recorded; other load knobs come from the recommendation or
explicit trial arguments.

Maximize context per model by testing the native ceiling first within a bounded
memory envelope. If a trial fails, retain the failure and test smaller context
or different cache/layer settings as separate fingerprints. Compare performance
as well as capacity; do not silently reduce GPU layers or quantize caches and
call the resulting profile equivalent.

Final state: Model Loader management UI is running. The test inference container
is stopped to release shared GPU memory; the saved Gemma profile remains available
in models.ini. Run a controlled calibration/switch before using it, rather than
starting a second large model alongside production. Production Qwen and its
original 32k load options were restored. The production noevia release is still
`ae39000`; application code changes in this workspace are locally tested only.

### Authentication before startup

The manager has Docker socket access and a LAN-published port. Compose requires a
non-empty `MODEL_LOADER_TOKEN`; generate a random value (for example with
`openssl rand -hex 32`) and store it in a private, untracked `.env` beside the
Compose file or in the deployment environment. Send it as `X-Model-Loader-Token`
for API requests. Only `/api/v1/health` is public; HTML pages also require the
header. Do not place the token in URLs or commit it. Run
`docker compose build --pull model-loader` before `docker compose up`; the
Compose file builds `../../services/model-manager` instead of reusing the old
pre-authentication `model-loader-test:e11a6ec` image.
