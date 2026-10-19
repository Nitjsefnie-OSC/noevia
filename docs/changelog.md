# Software change history

> Hostnames and network addresses in this document are illustrative examples, not live targets.

These historical notes describe software changes and their recorded qualification limits.
Per-installation service inventories, real accounts, paths, backup receipts, and recovery
configuration are retained in a verified local archive excluded from version control.
The notes do not establish the current state of any running installation. Public history
prior to this cleanup can still contain the earlier text.

## Unreleased

No new deployment changes are recorded as pending here. The native completion and pin changes listed as candidates shipped in the release below.

## Release 9375ce98e35abb1cef148c75835ad62b65de2448 - 2026-10-19 (native-service completion; #1318, #1071, #2027)

Cutover completed with exit 0; the receipt was recorded at 2026-10-19 01:55Z. The native-only model manager, Diary, and Rust web front are live on deployment host. The Node request prologue still authenticates and delegates legacy workspace claims to the native helper; separate project-context route cleanup remains pending (core PR #206 is not merged or deployed).

Core 1896db0 makes role-context, streamed JSON validation, presets, and relevant tool decisions unconditionally Rust-owned, and adds the bounded Rust workspace-claim helper called by Node while the authenticated account transaction is held (#2027). Services 2545ebc retires Diary's tenant selector while keeping its restart guard and nonce cache.

**Other changes moved from Unreleased.** Core #192/#2038 rejects inherited argument keys and Stage 2 search-prefetch decisions (search can still be required), normalizes unknown harness reasons to unchecked, and treats malformed toolbox-ID projections as having no box IDs instead of throwing; valid inputs retain frozen behavior. Core #194 checks ship with this pin. In core#202, Rust owns preset names, values, canonical keys, and micro-batch decisions while file IO, revisions, and field metadata remain in the host; the old JS is a frozen oracle, faults refuse before writes, and LLAMACPP_PRESETS_IMPL is retired. Core #198 makes role-context/dossier policy Rust-only with a checksum-bound JS oracle; literal unpaired surrogates still fail closed. Core #199 makes streamed JSON validation/correction Rust-only, uses checksum-bound parser/caller oracles, refuses on module faults, and cannot fall back through STREAM_GUARD_IMPL=js. Core #184-189 retire GGUF metadata, project filenames, provider egress, browser policy, and code-actions selectors; core #190-191 retire tool-gate and permitted-tool selectors. Their JS rules and fixture generators are removed; unexpected leftover values are ignored with the documented warnings, and tool-gate mismatch/stricter log reasons are retired. MODEL_MANAGER_IMPL and MODEL_FILES_IMPL are also retired (#1957). Core #2027 routes legacy workspace claims through the helper advertised by the actual front binary; original files are retained and the bounded descriptor-relative copy/publication runs while the authenticated account transaction is held. Services#99 retires Diary TENANT_ASSERTION_IMPL, retaining its restart guard and nonce cache and limiting concurrent leaf children to four. noevia#2038 updates the deployment/Kev runbooks for retired switches. The final source pins above supersede intermediate rs/services pins noted before cutover.

**Qualification.** All eight required hosted checks were green. deployment host mandatory web legacy-helper tests passed 12/12 with no skips; both Diary native helper self-tests passed; the manager binary hash and 31-capability advertisement were verified. The isolated startup smoke passed. All three services are healthy with zero restarts. The full native contract passed on development host. The deployment host manager native contract process-qualification command exited 101 during child-process inspection because the host does not expose /proc/task/children, so deployment host all-thread/lifetime verification remains unavailable. A separate bounded synthetic manager PID/listener/graceful-shutdown smoke passed. The 02:02Z post-watch check found public readiness on the exact release, all three services healthy with zero restarts, and zero fatal/panic/traceback/wasm-fault log lines. No authenticated real-user UI test or inference/model invocation was performed.

What changed for you: nothing you will see day to day. These are bug fixes:
- Model deletion and model-file parsing keep the embedding hold and the admission permit until they finish, bounded by the route deadline (#1997, #1998).
- A benchmark waits for the chat engine to come back after its restart (#1940).
- Settings → Inference machines shows embeddings on a registered machine as that machine, even when the deployment also names its address (#1979).
- The host's remote health probes name services by role and can use an optional key file (#1980). Nothing on this server uses them: no `NOEVIA_REMOTE_*` key is set.

**Order.** rs#174 and rs#175 merged (204e6a2e); services#89 merged, then services#90 repinned rs; noevia#2004 merged; noevia#2007 pinned rs, core and services, plus the egress-proxy rs pin. noevia CI at 58cf299c is green. The "Deep research gate harness" job, an offline experiment that is not shipped, failed once on the push and passed on re-run. Release 58cf299c was assembled on the development host (tarball `c3d0a4e9…c4ab`, the same on both ends) and built on the box (`release-prep/58cf299c/`).

Candidates (`candidates.out`, `candidates-ml.out`):
- clean rust web: ready;
- leftover keys: ready, with retired-key warnings only;
- in-image tests: 173/173;
- isolated model-loader: 14 native features advertised, and updates and detail digests equal between the native parent and the Python child.

**Cutover** finished with ALL DONE OK at 17:37:51Z (`cutover.log`). It used the 26160903 script with no Compose sync and with checks for all 17 `rust` switches, including `DIAGNOSE`. Two earlier starts aborted before any live change:
- 17:28Z (`cutover.attempt1-gate-busy.log`): the idle gate saw a brief sidecar CPU spike.
- 17:29Z (`cutover.attempt2-sync-collision.log`): the periodic `[sources]` sync rewrote one `projects.json` during the backup, so the byte-compare failed (9/10). It left an unused backup, `release_58cf299c_20261017T172911Z`. The next start waited for that six-minute sync to pass (`after-sync.sh`).

Keep the development host .131 wiring.

## Release 26160903 — 2026-10-17 10:29Z (web + model manager; #1318 draft heads + backends (dark), #1970, #1972, #1978, #1983, #1984, #1985, #1986, #1987, #1989, #1990, #1993, #1994, #1995, #1996)

What changed for you: in Models, you can now dismiss a finished auto-tune from the Recover card. This is the web half of #1978 (web#91); a8121f10 shipped only the core half (core#182). The rest is safety and memory work:
- Model deletion: a reserved model folder is released when a client drops or times out (#1983), and mixed-mode deletes are fixed (#1984, #1994).
- Hub lookups: the draft-heads read now uses at most ~100 MiB per lookup instead of 1-2 GiB (#1985, #1995), and the update check's listing is bounded (#1996, security).
- The GPU probe only execs into active backend containers (#1986).
- Native draft heads and backends (#1318) ship dark: `MODEL_MANAGER_DRAFT_HEADS_IMPL` and `MODEL_MANAGER_BACKENDS_IMPL` are `python`.
- The model-loader now runs with `TZ=UTC` (#1989). After the release, `MODEL_MANAGER_DIAGNOSE_IMPL` was flipped to `rust`, so 17 model-manager switches are now `rust`. `MODEL_MANAGER_MODEL_DELETE_IMPL` stays `python`.

**Order.** rs#171 merged as 3cfa0a7c. Its one failed check, the Laya lifecycle test, was an unrelated flake (#2001) and passed on re-run. Then services#88 repinned rs to `3cfa0a7c` in all five Dockerfiles and their pin tests. Then noevia#2002 pinned rs, services and web, plus the egress-proxy rs pin. Every tarball sha256 was fetched independently, and both PRs had an independent review. Release 26160903 was assembled on the development host (tarball `25c8b16f…483f`, the same on both ends) and built on the box (`release-prep/26160903/`).

Candidates (`candidates.out`, `candidates-ml.out`):
- clean rust web: ready;
- leftover keys: ready, with retired-key warnings only;
- in-image tests: 156/156;
- isolated model-loader: 14 native features advertised, the new switches `python` with confirmations 0, and updates and detail digests equal between the native parent and the Python child.

**Switch flip** (in the release plan, model-loader only, gated, `.env` backup `config/.env.bak.before-flip-MODEL_MANAGER_DIAGNOSE_IMPL`, smoke test and 3-minute soak; evidence in `release-prep/flips-20261017c-mm/`): at 10:38Z `MODEL_MANAGER_DIAGNOSE_IMPL=rust`. The native diagnose answers 200 with the same failures (0) as Python did; the Python child answers 503; an unknown backend gets 404 and a request without a token 401. The soak was clean: 0 errors and no OOM.

  Keep the development host .131 wiring.

What changed for you: in Models, a saved idle-unload setting now shows a notice (#1976), and a failed auto-tune shows its failing phase with an admin Clear (#1977, #1978). Model deletion is safer: the Python delete no longer falls back to a same-named model in another folder (#1964, a data-loss fix), and it refuses while a download is queued or running into that model's folder (#1966). Native model deletion (#1318 slice 11) ships dark: `MODEL_MANAGER_MODEL_DELETE_IMPL=python`. After the release, `MODEL_MANAGER_SECTIONS_IMPL`, `MODEL_MANAGER_HOST_IMPL` and `MODEL_MANAGER_PROMPTS_IMPL` were flipped to `rust`; 16 model-manager switches are now `rust`. `MODEL_MANAGER_DIAGNOSE_IMPL` stays `python` (see below).

**Order.** services#84 (rs → db849107 in all five Dockerfiles), then noevia#1981 pins (each sha256 fetched twice; egress-proxy rs pin too) → a8121f10. Assembled on the Mac (tarball `fdf035a6…c3bc` on both ends), built on the box (`release-prep/a8121f10/`). Candidates: clean rust web candidate ready; leftover-keys candidate ready with warnings only; in-image tests 107/110 (the same 3 `MODULE_NOT_FOUND` files as before); isolated model-loader candidate with `native-model-delete` advertised, `MODEL_DELETE_IMPL` python and its confirmation 0, updates/detail byte-identical to the Python child.

**Switch flips** (owner-approved 2026-10-16, one at a time, model-loader only, each gated with an `.env` backup `config/.env.bak.before-flip-<KEY>`, a smoke test and a 3-minute soak):
- 07:15Z `MODEL_MANAGER_SECTIONS_IMPL=rust`: section list and section reads byte-identical to Python; Python child 503.
- 07:19Z `MODEL_MANAGER_HOST_IMPL=rust`: same shape, plus the native `gtt_used_gb` field (#1747, intended); Python child 503.
- 07:23Z `MODEL_MANAGER_PROMPTS_IMPL=rust`: the seed flag was already set; the prompt list is identical (4 prompts); validation probes give the same answers (400/422/404/422/401); Python child 503.
- Not flipped: `MODEL_MANAGER_DIAGNOSE_IMPL`. The model-loader has no `TZ`, and native diagnose refuses to start unless `TZ=UTC` exactly. `MODEL_MANAGER_MODEL_DELETE_IMPL` stays `python` until it is qualified.

**Rollback:** each flip: copy `config/.env.bak.before-flip-<KEY>` back and recreate model-loader only. Release: set `COWORK_VERSION` and `MODEL_MANAGER_VERSION` to f1ad65f4 (`config/.env.bak.before-a8121f10`, which also has the three flipped keys unset), restore the override from `docker-compose.override.yml.bak.before-a8121f10`, restore `tools/preflight` from the backup's `preflight.tar.zst`, point `current` at `releases/f1ad65f4`, then run `up.sh … --no-build --no-deps --wait` for model-loader, then web. Keep the development host .131 wiring.

## Release f1ad65f4 — 2026-10-17 03:56Z (web + model manager; #1318 slices 9–10, #1957, #1953, #1962)

What changed for you: nothing visible. The model manager now has native code for the benchmark runner (#1318 slice 9) and the download job table (#1318 slice 10). Both stay off: `MODEL_MANAGER_BENCHMARK_RUNNER_IMPL` and `MODEL_MANAGER_DOWNLOADS_IMPL` are `python`, as are all other `MODEL_MANAGER_*_IMPL`. A leftover `MODEL_FILES_IMPL` is now only a "retired and ignored" notice (#1957). The web image adds the #1953 import/replace review fixes and the #1962 contract test.

**Order.** services#80 (rs 99c2ca8a → 0f29e91c in all five Dockerfiles), then noevia#1968 pins (each sha256 was fetched twice; the egress-proxy rs pin was bumped too) → f1ad65f4. #1318 slice 11 (rs#160, services#79, #1963) was still open at pin time and is not included. Assembled on the Mac, built on the box (`release-prep/f1ad65f4/`). Candidates:
- The clean rust web candidate was ready. A candidate with leftover retired keys was ready, warned for each one, and had 0 confirmations.
- In-image tests: 107/110 passed. The same 3 files as in 6adf2033 failed with `MODULE_NOT_FOUND` because the repo-only `tests/server` stub isn't shipped in the image.
- The isolated model-loader candidate (synthetic GGUF, no network): native parent confirmed, all IMPLs `python`, `/api/v1/internal/*` 404 on both parent and child, updates/detail byte-identical to the Python child, #1934 probe 400 with the ini unchanged. The `MODEL_FILES_IMPL` leftover produced only the retired notice.

**Rollback:** set `COWORK_VERSION` and `MODEL_MANAGER_VERSION` to 6adf2033 (`config/.env.bak.before-f1ad65f4`), restore the override from `docker-compose.override.yml.bak.before-f1ad65f4`, restore `tools/preflight` from the backup's `preflight.tar.zst`, point `current` at `releases/6adf2033`, then run `up.sh … --no-build --no-deps --wait` for model-loader, then web.

## Release 6adf2033 — 2026-10-17 00:56Z (web + model manager; #1949, #1950, #1264, #1071, #1937, #1939, #1942, #1318)

What changed for you: importing conversations no longer deletes the imported chats' transcripts when the project store is on (#1949, a live data-loss bug), and replacing a project document no longer shows a false "Project changed; retry" (#1950). Sign-in, the project routes and the project store are now always the native front's: `NOEVIA_RUST_AUTH`, `NOEVIA_RUST_PROJECTS` and `NOEVIA_RUST_PROJECT_STORE` are retired, and leftover values only warn. The model manager's native parent is permanent. Every #1318 switch stays `python`.

**Order.** First services#77 (rs 4bb49e87), then noevia#1954 pins (each sha256 was fetched twice; the egress-proxy rs pin was bumped too). Then #1951. Then #1930, with main merged in and both retirements kept. Assembled on the Mac and built on the box (`release-prep/6adf2033/`). Candidates:
- The clean rust candidate was ready.
- A candidate with leftover `NOEVIA_RUST_AUTH/PROJECTS/PROJECT_STORE/STATS` was ready, warned for each, and had 0 confirmations. The store listened on 127.0.0.1:10021.
- In-image tests passed 106/109. The 3 failing files need the repo-only `tests/server` stub, and pass 47/47 with it mounted read-only; `routes/import.test.cjs` is one of them.
- The isolated model-loader candidate had the native parent confirmed, all IMPLs python, and `/api/v1/internal/*` returned 404 on both parent and child.

**Rollback:** set `COWORK_VERSION` and `MODEL_MANAGER_VERSION` to 8207bb96, restore the override from `docker-compose.override.yml.bak.before-6adf2033`, restore `tools/preflight` from the backup's `preflight.tar.zst`, point `current` at `releases/8207bb96`, then run `up.sh … --no-build --no-deps --wait` for model-loader, then web.

**Owner:** these retired keys are still in `.env` and only warn or do nothing: `NOEVIA_RUST_{AUTH,PROJECTS,PROJECT_STORE,USAGE,SAMPLING_SETTINGS,REASONING_SETTINGS,ROUTING_MODE,ROUTING_DEFAULT,STATS,CHATGPT_STATUS,STORAGE_READS,STORAGE_BROWSE,EXPORT}`, `MODEL_MANAGER_IMPL` and `MODEL_FILES_IMPL`.

## Release 8207bb96 and the project store flip — 2026-10-16 20:25Z / 20:39Z (web + model manager; #1264, #1934, #1922, #1906, #1908, #1902, #1318)

What changed for you: nothing visible. Saves to the project list and the free-chat list now go through the native front's internal project store instead of Node writing the files under a `flock` (#1264). A model settings name ending in a newline can no longer write an unparseable `models.ini` (#1934, a live Python bug). The owner approved the `NOEVIA_RUST_PROJECT_STORE` flip on 2026-10-16. Every other new switch ships off.

**Order.** services#72 (rs 1666ab66), then services#67 on main (rs 44e89709). noevia#1933 pins, where each archive's sha256 was fetched twice. Assembled on the Mac. `build.sh` on the box. Candidates: node and rust fronts ready; the image test files passed 146/147, and the 1 file needs the repo-only `tests/server` stub and passes 12/12 with it mounted read-only (core CI "Server tests" is green at a11598b7). The isolated model-loader candidate showed all new IMPLs python and confirmations 0, and `PUT /sections/qa-probe%0A` returned 400 on both parent and child with the synthetic `models.ini` byte-identical. Then the gate, then `release-prep/8207bb96/cutover.sh`.

**Gate (each run):** jobs idle, llama idle 0, GTT 29 MiB, MemAvailable 13.9–15.9 GiB, no autotune process (last state `failed`), sidecars idle.

**Flip `NOEVIA_RUST_PROJECT_STORE=1`.** Prerequisites: `NOEVIA_RUST_PROJECTS` and free-chats are confirmed, the front lists `project-store`, and UI_PORT+2000 (10021) had no listener in the web namespace. Attempt 1 (20:36Z) rolled back automatically at the token-in-args check. My scan matched its own shell, whose command line contained the key name as the grep pattern. Nothing of the token was found. The rollback was verified (key gone, store unconfirmed, healthy). Attempt 2 (20:38Z, scan fixed to skip its own pid) passed:
- Node is confirmed (1 process) and the front logs `project store on 127.0.0.1:10021`, with no "is ignored" warning.
- `ss` inside the container shows only `127.0.0.1:10021`, and the port is not published.
- The token key is absent from every container's inspect env, and neither the key nor the value is in any process args.
- Unauthenticated `POST /v1/read` and a wrong-token `/v1/write` both return 401. From model-loader, `web:10021` is not reachable.
- The 4 earlier switches are still confirmed. Only web changed.
- 10-minute watch: 0 `flock` processes in 300 samples, `PROJECTS_BUSY` 0, store errors 0, healthy, 0 restarts, no other container changed. No save happened during the watch, so the 6 projects/free-chats mtimes did not move. The owner's authenticated QA click-test covers saves.

## Switch flips on 7ac94a2f — 2026-10-16 08:52Z–09:17Z (web: 4 on; model manager: 1 rolled back; #1071, #1368, #1373, #1315, #1318)

What changed for you: nothing visible. The ChatGPT connection status, connected-storage metadata, the connected-storage list and text read, and the conversation export are now answered by the native front. The owner approved these flips on 2026-10-16 (one at a time, each with a smoke test and a ready rollback). The native model-manager settings read failed its smoke test and was rolled back, so the model-manager flips stopped there.

| # | Switch | Up | Gate (GTT, MemAvailable) | Result |
| --- | --- | --- | --- | --- |
| 1 | `NOEVIA_RUST_CHATGPT_STATUS=1` | 08:52:11Z | 29 MiB, 13.1 GiB | on |
| 2 | `NOEVIA_RUST_STORAGE_READS=1` | 08:58:07Z | 29 MiB, 13.0 GiB | on |
| 3 | `NOEVIA_RUST_STORAGE_BROWSE=1` | 09:03:36Z | 29 MiB, 13.0 GiB | on |
| 4 | `NOEVIA_RUST_EXPORT=1` | 09:09:04Z | 29 MiB, 12.9 GiB | on |
| 5 | `MODEL_MANAGER_SETTINGS_IMPL=rust` | 09:16:03Z | 29 MiB, 12.9 GiB | rolled back 09:17:00Z |

Every gate: jobs idle, llama idle 0, no autotune process (last job state `failed`, not running).

**Evidence (web).** The live front lists `rust-chatgpt-status`, `rust-storage-reads`, `rust-storage-browse` and `rust-export` in `--features`. After each flip the supervisor confirmed the switch to Node (`NOEVIA_RUST_<NAME>_CONFIRMED=1` in Node's environment; key names only were read). Probes on loopback were unauthenticated (no session was created on the live stack): every moved route answered 401 `application/json` `{"error"}` with `x-noevia-api: 1`, as before the flip, and the ChatGPT status 401 body is byte-identical to Node's. After flip 2, Node's own copy of `GET /api/integrations/storage` refuses with 503 `RUST_STORAGE_READS_OWNED` while the front still answers 401, which shows the front answers that route itself. For browse and export, Node checks the session before its ownership refusal, so the unauthenticated probe cannot show the hand-off; the confirmation is the evidence there. Each soak (08:52–08:57, 08:58–09:03, 09:03–09:08, 09:09–09:14): 0 error lines, healthy, 0 restarts, no OOM, public `/api/ready` 200, no cowork container with restarts. Only `cowork-web-1` changed id on each web flip.

**Export memory (before flip 4).** Measured in throwaway candidates of `cowork-web:7ac94a2f` (no network, read-only root, capabilities dropped, tmpfs data, synthetic owner and synthetic chats only, removed by name). Same data per pair; peak RSS (VmHWM) of the serving process and container cgroup `memory.peak`, before → after one export:

| Export | Node serves (switch 0) | Native serves (switch 1) |
| --- | --- | --- |
| 300 chats × 30 messages, ZIP 26,837,251 bytes (identical size) | Node 141 → 180 MiB (+39); cgroup peak 159 → 312 MiB | front 53 → 76 MiB (+23); cgroup peak 154 → 255 MiB |
| 700 chats × 30 messages, ZIP 62,620,451 bytes (identical size) | Node 135 → 270 MiB (+135); cgroup peak 180 → 462 MiB | front 53 → 114 MiB (+61); cgroup peak 179 → 378 MiB |
| 1000 chats × 30 messages (over the 64 MB cap) | 413 JSON | 413 JSON, front peak +66 MiB |

Native peak is lower than Node's in every case and far from the 8 GiB MemAvailable floor.

**Model manager failure (flip 5).** Recreate, health, restarts 0 and the child confirmation (`NOEVIA_NATIVE_MODEL_MANAGER_SETTINGS_CONFIRMED=1`) all passed, but the authenticated `GET /api/v1/settings` on the front returned `500 text/plain` (`Internal Server Error`, the native store-failure answer) instead of the earlier 200 `{hasToken, tokenHint}`. The Python child correctly refused with 503. Updates and the detail of 3 models stayed byte-identical. The front logged nothing. Rolled back at once: backup restored (byte-identical), model-loader-only recreate, healthy, 0 restarts, `MODEL_MANAGER_SETTINGS_IMPL=python`, settings 200 with the pre-flip body hash, five-minute soak clean. Likely cause (not yet reproduced, #1922): `/data/model_loader.db` is in WAL mode and has no `-wal`/`-shm` files while Python holds no connection. `settings::read` opens with `SQLITE_OPEN_READ_ONLY`, which cannot open a WAL database whose `-shm` does not exist. `MODEL_MANAGER_MODEL_UPDATES_IMPL` and `_MODEL_DETAIL_IMPL` were not attempted (the sequence stops on a failure). The model-loader runs in UTC (`TZ` unset in its env, `/etc/localtime` → `Etc/UTC`), which the detail switch needs.

## Release 7ac94a2f — 2026-10-16 08:28Z (web + model manager; #1863, #1880, #1901, #1751, #1264 slice 1 dark)

What changed for you: chat models now unload after 30 minutes idle (was 15), and an administrator can change that in Settings → Models → Performance (#1863). A chat role's model can be measured (auto-tuned) on its own Inference machine from Settings (#1880). Automatic routing sends short simple asks (count, list, a joke, a short poem or story) to Fast without a decision call, and Kev's route labels name simple short tasks as Fast (#1901, core#168). A decision call that hits a reset or refused connection is retried once within the deadline (#1751). Native project chat-context routes are shipped behind the new default-off `NOEVIA_RUST_PROJECT_WRITES` switch, which is off (#1264 slice 1).

## Release 3b23d181 — 2026-10-16 03:54Z (web only; #1894, #1895, #1896)

What changed for you: the Models page's local-engine health check now asks the model manager's `/api/v1/health` (#1894). When a model change is still finishing, a chat waits up to 3 s for it and then gets a retryable "still finishing" answer instead of an error; the client retries once (#1896). The composer pill is fixed (#1895).

## Release 88adc3a1 — 2026-10-16 02:54Z (web + model manager; #1886, #1891, #1889, #1318)

What changed for you: when a large PDF's storage read fails during a refresh, the source reopens from the copy noevia already stored, and every sync logs one `[sources] sync` count line (#1891). Opening a project no longer saves its settings when nothing changed (#1886). The model manager can serve model detail natively (#1318, #1889), but that is switched off.

**Rollback.** Run the idle gate first. No data migration. The added compose key is inert for the old image.


## Release 092bc8e0 — 2026-10-16 01:21Z (web only; core#158, #1885)

**Candidates.** `build-web-release.sh` from merged main (tarball `9a989e47…4237`, same sha256 on the Mac and the box), `candidate-boot.sh` node and rust fronts (ready, 0 error lines). Real OCR check: a throwaway `--rm`, no-network `cowork-ocr:eb5a4523` plus a `--rm` web container sharing its network namespace ran a synthetic probe (a valid 27 MiB one-page PDF read through core's real `storage-client` large-read path, so SAB-backed, then `ocr.extractPages`). Old image `eb5a4523`: `SharedArrayBuffer is not allowed` (the live error). New image: stream body, `Content-Length: 28312234`, no Transfer-Encoding, 1 page with the marker text recognised in 0.7 s. `server/upload-sab-1885.test.cjs` in the new image under Node 22: 12/12 pass.

**Post-checks.** Healthy, restarts 0, PID 1 `docker-init`; `/api/ready` `092bc8e0` on loopback and public; signed-out `/api/projects` and `/api/models/reranker` 401 on both; served dist equals image dist (145 files; `index.html`, `manifest.webmanifest`, `version.json` and 16 hashed asset names differ from `eb5a4523` although web is unchanged); allow-listed switches identical apart from `COWORK_VERSION`; embedding service 200 and `embed:8080/health` 200; Kev decision 0.33 s; decision config unchanged; project counts unchanged; preflight 0 missing keys. Only `cowork-web-1` changed id.

**Watch (20 min, read-only).** Web and OCR healthy, 0 restarts, 0 OOM, 0 web error/warn lines, OCR memory 27 MiB. The one record carrying the #1885 error (9 of 9 pages `ocr-needed`) was not processed: no `[documents]` or `[large-document-lock]` lines and no OCR `/extract` requests. The reopen happens on the next source sync/refresh.

## Release eb5a4523 — 2026-10-16 00:19Z (whole stack: web + OCR + Docling; #1854, #1867, #1868, #1869, #1876, #1878, #1879, #1881, #1882, #1853)

What changed for you: very long documents keep becoming searchable after the first sync: a background pass, 90 s after start and then every 5 minutes, embeds the rest of each long document within an hourly budget, and pauses whenever a chat or Diary turn runs (#1868, #1869, #1881). Large PDFs reach the OCR and Docling sidecars in page ranges of up to 96 MiB, stay within the sync's OCR budget, and pages left incomplete are retried at 400 dpi (#1867, #1882). Inference machines show per-machine measurements (#1854). The code relay is hardened (#1876), the Code pipeline and sandbox follow the Code role to its machine (#1853), and logs and the source count are fixed (#1878, #1879).

**Rollback.** Run the idle gate first. Restore all three together: the tested pairs are old core with old sidecars and new with new. Core sends `X-OCR-DPI` and ranges only when `/health` advertises them, so a partial state degrades to unranged reads rather than failing. No data migration. The added compose keys are empty and inert for the old images.


## Release 9b238027 — 2026-10-15 21:48Z (web + model manager; #1861, #1862, #1863, #1864, #1865, #1866, #1871, #1872, #1318)

What changed for you: Kev's health is checked at `/v1/models`, and a saved ChatGPT model the account no longer offers is flagged (#1861, #1862). Automatic routing pre-loads the shared Fast/Smart model while it decides, and cancels a wrong guess (#1863). Large PDFs are read in page ranges, up to 96 MiB per read, one large read at a time. Degraded pages are retried with OCR, at most 40 OCR pages per sync (#1864, #1865, #1871). The large-document lock has an acquire timeout (#1872). Citations show page numbers (#1866). Sources show where a PDF stopped and each page's OCR retry outcome. The model manager can serve model updates natively (#1318), but that is switched off.

**Rollback.** Run the idle gate first. No data migration; the added compose keys are inert for the old images.


## Release 88827187 — 2026-10-15 19:00Z (web only; Inference machines for every part, health probes with reasons; #1840, #1841, #1844, #1847, #1849, #1850, #1851, #1855, #1856, #1845, #1857, #1858, #1843)

What changed for you: OCR, Docling, sensitivity checks, chat roles, Manual, the router and Deep Research can each be assigned to an Inference machine, with tool limits per machine (#1841, #1844, #1847, #1840, #1851, #1849, #1850, #1855). Each chat turn checks that the assigned machine actually serves the model (#1851). Machine health shows a reason, and Kev answering 401 counts as up but needing sign-in (#1856). Routing shows a refresh note (#1857), and indexing shows a toast (#1858).

**Rollback.** Run the idle gate first. No data migration.


## Release a5d9cbf2 — 2026-10-15 16:31Z (whole stack: web + model manager + Diary overlay; #1576, #1638, #1315, #1368, #1373, #1318, #1826)

What changed for you: there is one chat surface now. Every project takes chats, and Task is a per-send choice in the composer (#1576, #1839). Settings gains an Inference machines page that lists machines and which part of noevia each one serves (#1638). The page also fixes refresh issues (#1814, #1828, #1829), shows the model in the inspector, and adds a Creative note. The native Rust routes for export (#1315), storage reads and browse (#1368) and ChatGPT status (#1373) ship in the image but stay switched off. The model manager can serve its settings natively (#1318), also switched off.

**Rollback.** Run the idle gate first. The #1576 migration changed no live file, so the old web reads the same data.


Model manager (to da2e18b9): `sed -i 's/^MODEL_MANAGER_VERSION=.*/MODEL_MANAGER_VERSION=da2e18b9/' $ENV`, then the same `up.sh` line with `model-loader`.

Diary (to da2e18b9): `sed -i 's/^DIARY_VERSION=.*/DIARY_VERSION=da2e18b9/' $ENV`, then the same `up.sh` line with `diary`. `cowork-diary:rollback-before-diary-overlay` is the same image.

Compose (#1826): the added keys are inert for the old images. If needed, restore `docker-compose.override.yml.bak.before-a5d9cbf2` in the Compose Manager project.

## Release da2e18b9 — 2026-10-15 11:28Z (whole stack: web + model manager + Diary overlay; #1806, #1665, #1666, #1667, #982, #1783)

What changed for you: a project's source text now lives in its own files instead of inside projects.json, so projects can hold up to 1000 sources, 200 documents and 12 images (#1806). A source whose text has gone missing says so in Sources (#1815). The Models page gains the reranker switch and choice, a decision model choice and a Creative role (#1665, #1666, #1667). The model manager no longer prunes operator `.bak` files next to `models.ini` (#1783). The Diary image now carries the Rust workspace ZIP gate (#982), still switched off.

**Rollback.** Run the idle gate first.

Web (to 3b978351). The old image reads source text only inline, so put it back first, with web (and so the Rust front) stopped:


The loop inlines each workspace that has a `migration-backups/projects-pre-1806-*.json` (one today). Alternatively, restore that backup over projects.json; sources added since are then lost.

Model manager (to a6de6203): `sed -i 's/^MODEL_MANAGER_VERSION=.*/MODEL_MANAGER_VERSION=a6de6203/' $ENV`, then the same `up.sh` line with `model-loader`.

Diary (to 9d308b22): `sed -i 's/^DIARY_VERSION=.*/DIARY_VERSION=9d308b22/' $ENV`, then the same `up.sh` line with `diary`. `cowork-diary:rollback-before-diary-overlay` is the same image.

## Release 3b978351 — 2026-10-15 08:21Z (web; folder import; #1805, #1806)

What changed for you: a project's Sources can take a whole folder. "Add folder" and dropping a folder onto Sources import every file in it, subfolders included, and an attached storage folder is now read recursively, so files in its subfolders become sources too (#1805). Limits are unchanged: 60 sources, 60 documents and 12 images per project, and at most 100 MB per folder import.

**Rollback.**

Web (to fee7d681):

## Release fee7d681 — 2026-10-15 06:25Z (web; gte reranker on 06:28Z; #1761, #1765, #1795, #1796, #1784, #1785, #1788, #1665)

What changed for you: project knowledge search now reorders its passages with the gte reranker before the model reads them (#1665), so the most relevant passage is more often first. A model that is unloaded after idling now reads "Sleeping" instead of looking broken, and a model that is set up but not loaded reads "Configured". The Models page can reset the decision model and shows Decision and Sensitivity rows. A chat gets a title after any completed reply, not only the first, with at most 3 tries. Fast turns on the local engine run without thinking. The "Stopped" note shows only for stopped or clean replies, and the app adopts the generated title against the first message.

**Rollback.**

Reranker off (keeps the release):

Web (to b84758dc):

b84758dc's core has no TEI backend, so turn the reranker off first.

## Release b84758dc — 2026-10-15 04:51Z (web; #1784–#1793, #1797)

What changed for you: a stopped answer is now marked "Stopped" instead of looking complete (#1784), and the last answer line no longer sits under "Jump to latest" while streaming (#1789). Chat titles follow the conversation instead of staying on the first greeting, and the app adopts the new title (#1785). The first reply of a new chat stops showing as streaming when it is done, without waiting up to 8 s for the title (#1797). A request that never mentions storage no longer triggers an unrelated Drive search (#1786). The High effort hint no longer leaks scratch reasoning into the reply (#1787), and Fast lowers only the default effort, so a greeting no longer spends seconds thinking (#1788). An attached image no longer hangs at "Reading image sources": describing it skips thinking and gives up after 120 s (#1790). A harmless image is no longer flagged as a password or key (#1791). Images count toward the context and are handled by compaction (#1792), and answers from a project knowledge file show their source chips again (#1793).

**Rollback.**

Web (to c453e9ec):

## Release c453e9ec — 2026-10-15 02:42Z (web; #1776, #1778, #1777; #1731 preset)

What changed for you: opening projects and documents no longer creates search indexes as a side effect (#1776). When a new chat's framing settles on the kind of chat early, it now stops waiting on a hung embedding, and a failed project or tag lookup keeps the kind it already found (#1778). The web container now runs under Docker's init, so it stops cleanly on restart (#1777). The chat model list no longer carries a preset for a model file that does not exist (#1731).

**Rollback.**

Web (to 2f583a82, without init):

## Release 2f583a82 — 2026-10-15 01:33Z / 01:35Z (web; embed `--models-max 3`; #1770, #1771, #1772, #1775)

What changed for you: PDFs that were added before multimodal RAG was turned on now get their figures read once (#1770). The image backfill no longer creates empty indexes for chat-context projects (#1771). An image pass no longer pushes a text embedding model out of the embeddings router (#1772). A new chat's framing now asks what kind of chat it is first (#1775).

**Rollback.**

Web (to 4a7f9d0b):

embed (to `--models-max 2`):

## Diary overlay 9d308b22 — 2026-10-15 00:56Z (Diary only; #1768, #1759, #1766 complete)

What changed for you: the Diary's search index is complete again. The 12 long Diary sections that could not be embedded are now embedded with EmbeddingGemma 2 (53 of 53).

**Incident (2026-10-15 ~00:50Z).** During the first candidate check for this overlay, an agent ran `docker container prune -f`, which removes every stopped container on the host. It removed the stopped containers `nextcloud-aio-borgbackup`, `nextcloud-aio-watchtower` and `noevia-eval-decisions`, plus its own throwaway containers. No running container and no volume was affected; all eight `nextcloud_aio_*` volumes are present. The Nextcloud AIO mastercontainer recreates its backup and watchtower containers when it next needs them; confirm at the next AIO backup. `noevia-eval-decisions` is not needed live (Kev runs as `cowork-kev`). New rule: never run `docker * prune`; remove only containers you created, by exact name.

**Rollback** (Diary only):

## Release 4a7f9d0b and multimodal RAG on — 2026-10-15 00:17Z / 00:20Z / 00:21Z / 00:22Z (web + multimodal enable: model-loader, embed, web; #1762, #1726)

What changed for you: a question about a project can now find its pictures, not just its text. Every image in a project gets one image vector from EmbeddingGemma 2. Retrieved images go to a chat model that can see them, and a model that can't see them gets the image's text or a cached caption. Diary images are never embedded (#1736). Separately, noevia now warns when an embedding address is public (#1762).

**Rollback.** Run the idle gate first.

Multimodal off, in this order:


The override lines can stay, since they default to `0`. With the flag off, stored image vectors are ignored and kept.

Web back to a6de6203: `ln -sfn $A/releases/a6de6203 $A/current`, set `COWORK_VERSION=a6de6203` with `sed`, then web-only `up.sh ... --no-build --no-deps --wait web`.

Never copy a `.env.bak.*` file back wholesale.

## Diary overlay d3474b3c and Kev cutover (limited) — 2026-10-15 00:01Z / 00:04Z / 00:12Z (Diary + new cowork-kev + web env; #1759, #1766, #1639)

What changed for you: the Diary now splits a chunk that the embedding server refuses as too long, instead of leaving it without a vector (#1759, #1766). The 12 long Diary chunks still need one re-index pass before EmbeddingGemma 2 covers all 53. Route, tool gate, step supervision, chat framing and the load advisor are now decided by Kev-0.8B. Sensitivity stays on Laya. This starts a 7-day soak that ends 2026-10-22.

### Diary overlay

The rs pin in the release's `diary/Dockerfile` moved (`0012da31` to `ed793085`), so `diary-overlay.sh` would have rebuilt tenant-assertion. The overlay ran the script's own steps with the agent-only Dockerfile instead (`FROM cowork-diary:rollback-before-diary-overlay`, `rm -rf ./agent`, `COPY agent/`). Candidate checks, all with `--network none`:

- 36 base layers identical, plus 2 new layers;
- `/app/agent` equals the services tree (33 files);
- the tenant-assertion binary is byte-identical, and its self-test prints `ok`;
- the imports load.

Coverage (counts only): active EG2 holds 41 of 53 vectors. The new code is live, but no pass has run since the restart: the Diary starts one only when a next model is set, or on `set-next`, `switch` or `rollback`. The 12 refused chunks need one re-index pass, which is being triggered separately.

Rollback: set `DIARY_VERSION=20b07d3f` with `sed`, then run `up.sh ... --no-build --no-deps --wait diary`. The old image is kept as `cowork-diary:20b07d3f` and as `cowork-diary:rollback-before-diary-overlay`.

### Kev cutover (docs/kev-cutover.md)

Preconditions all held. Laya baseline (counts only, 2026-09-22T15:16Z to 2026-10-14T10:28Z, 1185 entries):

- supervise S 92, escalations E 10, weak-escalate W 1, benign pauses B 0 (none marked yet);
- route N 304 / 40 failures; tool gate N 388 / 20; supervise 18 failures; sensitivity N 136 / 101.

Kev start: healthy within the bounded wait; cold load 5.8 s. Web recreate: idle gate, then web-only `up.sh ... --no-build --no-deps --wait --wait-timeout 120 web`. Env-level checks passed: `/api/ready` `a6de6203`, signed-out `/api/projects` 401, `getent hosts kev` from web.

After the re-save, the synthetic post-checks (first line `shared kev-0.8b kev sensitivity laya laya`):

| Purpose | Answer | Model | Time |
| --- | --- | --- | --- |
| route | smart | kev-0.8b | 480 ms |
| tool gate | none | kev-0.8b | 463 ms |
| chat framing | idea | kev-0.8b | 431 ms |
| load advisor | unknown | kev-0.8b | 339 ms |
| step supervision | verify | kev-0.8b | 597 ms |
| sensitivity | not_sensitive | convaiinnovations/laya | 600 ms |

Kev, Laya and web are healthy with 0 restarts and `OOMKilled=false`. `cowork_laya` is internal, and the web log has 0 "names no known decision model" lines. Kev memory: process VmHWM 4.41 GiB, and the cgroup peak reached its 5 GiB cap (page cache included, as in the eval). Only `cowork-web-1` changed id, and `cowork-kev` is new.

Soak: 7 days, ending 2026-10-22, against the criteria in `docs/kev-cutover.md` section 5.

Rollback (section 6): run the idle gate, then:

1. Remove the five decision keys by name with `sed`, and append `COWORK_DECISION_URL=` with the value recorded in `state/kev-cutover-decision-url-before.txt` (`http://laya:8040`). Never copy `.env.bak.before-kev` back.
2. Run web-only `up.sh ... --no-build --no-deps --wait web`, then `docker stop cowork-kev`.
3. Re-save `http://laya:8040` in Settings, Decision service.
4. Remove the cron line.

## Release a6de6203 — 2026-10-14 19:33Z / 19:40Z / 19:50Z (web + model manager + chat-engine restart; #1747 idle unload live)

What changed for you: a chat model that sits unused for 15 minutes now unloads itself, which gives its memory back (about 6.6 GiB GTT for Gemma 4 12B). The next message wakes it in about 12–15 seconds, and noevia keeps treating a sleeping model as available. Vision descriptions now use only the default provider, a missing sensitivity key logs a startup warning, and service addresses (embedding, rerank, System One) follow one on-this-network rule, checked when they connect.

**Evidence.**
- Pins:
  - services#47 and #1763 CI green; #1763 includes "Assembled release (pinned repos)".
  - Tarballs fetched twice each with identical results: core `67cadcba…518d`, rs `e16a8932…653c`, services `81f521e1…728a`.
  - The release tarball `7206e4df…5e02` matched on the Mac and on the box.
- Candidates:
  - Web: `candidate-boot.sh` node and rust fronts both `{"ready":true,"version":"a6de6203"}` with 0 error lines. Stamp `{"version":"a6de6203","web":"92b19d49…","core":"573b95c8…"}`.
  - Model manager (no network, read-only, cap_drop ALL, tmpfs stores): healthy, 0 error lines. Its binary contains `sleep-idle-seconds` and the d37a16e5 one does not.
  - A second isolated candidate with `MODEL_MANAGER_HOST_IMPL=rust` returned `gtt_used_gb: 0.01` on `/api/v1/host`.
- Gates before each step: llama idle count 0, GTT 14 MB (≤ 1 GiB), at least 17 GiB available, no autotune, Appdata Backup, compose or build running.
- Web after:
  - healthy, restarts 0; `/api/ready` `{"ready":true,"version":"a6de6203"}` on loopback and on https://noevia.example.com; signed-out `/api/projects` 401 on both
  - served `dist` equals the image's (143 files); allow-listed flags identical
  - `/api/v1/embedding-service` 200 (`managed:true`, nomic loaded); a synthetic decision via web reached Laya (200, `selected=answer`, 0.39 s)
  - 0 error or warn lines
- Model manager:
  - The first attempt at 19:36Z rolled back by itself. Its post-check expected `gtt_used_gb` on the live `/api/v1/host`, which is served by Python while `MODEL_MANAGER_HOST_IMPL` is off. The check was dropped.
  - The re-run at 19:40Z passed: healthy, restarts 0, pid 1 `noevia-model-manager`, `MODEL_MANAGER_IMPL=rust`, `embedding-service` 200, `embedding.ini` byte-identical.
  - The chat `models.ini` diff is exactly `+[*]`, `+sleep-idle-seconds = 900` and one blank separator line, with no lines removed.
- llama restart:
  - The first two attempts rolled back by themselves, and each left `models.ini` without the key; model-loader was force-recreated each time to write it again. The first attempt changed nothing: `up --no-deps` without `--force-recreate` does not recreate an unchanged service. The second recreated llama but failed the Vulkan check because `llama-server` is not on PATH (the binary is `/app/llama-server`).
  - The third, at 19:50Z, passed: healthy, restarts 0, the same 8 presets listed, `Vulkan0: AMD Radeon 890M Graphics (RADV STRIX1)` present. The router log shows `--sleep-idle-seconds`.
- Idle-unload proof (`gemma-4-12b-it-qat-q4_0`, the Fast role; synthetic prompt; max_tokens 64; web → llama):

  | Time | Event | Status | GTT |
  |---|---|---|---|
  | 19:52:45Z | before | `unloaded` | 14 MB |
  | 19:52:45Z | request 1: 200 `"OK"` in 15.0 s (cold load) | `loaded` | 7.09 GB |
  | 20:09:01Z | +16 min | `sleeping` | 16 MB |
  | 20:09:06Z | web `health()`: `loaded:true, sleeping:true, backend_alive:true`; the read did not wake it | `sleeping` | 16 MB |
  | 20:09:06Z | request 2: 200 `"OK"` in 11.9 s (woke) | `loaded` | 7.09 GB |
  | 20:25:18Z | +16 min, end state | `sleeping` | 16 MB |

**Rollback.** One service at a time, in reverse order:


The rollback images `cowork-web:d37a16e5` (`5907d421…`) and `cowork-model-loader:d37a16e5` (`43c37c7d…`) are kept.

## EmbeddingGemma 2 switch: preparation — 2026-10-14 17:59Z (embed memory limit live; model not switched yet)

What changed for you: nothing visible. Search still uses nomic-embed-text-v1. The embedding service can now hold nomic and EmbeddingGemma 2 together, which the owner-approved switch (#1636) needs. The switch itself is not done yet. It waits on core#111 being released in web, then on the administrator steps in `docs/deployment.md` ("Approved, in progress: embeddings …").

**Rollback** (memory limit only; nothing else changed):


Then send one synthetic embedding to `http://embed:8080/v1/embeddings` from web to load nomic at once (the model manager's watcher also re-warms it within about 30 s).

## Release d37a16e5 — 2026-10-14 16:45Z / 17:37Z / 17:42Z (whole stack: web + model manager + Docling; live)

What changed for you: decision prompts now use the wording tuned for Kev-0.8B, follow the configured decision model, and keep the Code route label (#1639, #1739, #1740). The decision model in use is unchanged until the separate Kev cutover. Multimodal RAG (#1726) is shipped in web, the model manager and Docling but stays off (`NOEVIA_MULTIMODAL_RAG` is not set). Docling can now return a document's figures and mark OCR-read pages, but only when it is asked to.

**Rollback.** One service at a time, in reverse order:


The rollback images `cowork-web:a03fbc63` (`01e9390d…`), `cowork-model-loader:a03fbc63` (`9a78968e…`) and `cowork-docling:785643f4` (`efee3285…`) are kept.

## llama.cpp image b11610 on embed and the chat engine — 2026-10-14 14:22Z / 14:32Z (live)

What changed for you: nothing visible. Both llama.cpp containers now run build 11610 instead of 10920 (owner: "approve the llama.cpp update, I can't imagine it would break anything in any other capacity honestly"). The new build can run EmbeddingGemma 2 (#1636), but the embedding model is **not** switched: nomic stays live. The switch needs its own owner approval.

**Evidence: embed (plan A in #1636).**
- Pull verified by RepoDigest (`d6404357…475b`); `--version` reports build 11610, commit `091b6a7fc`.
- Candidate: `--network none`, same args on port 8081, a read-only copy of `embedding.ini`, only the nomic folder mounted read-only. `/health` 200, `/v1/models` lists nomic, and a synthetic "QA synthetic sentence" returns 768 dims. **Cosine against live b10920 is 1.00000000** (max absolute difference 0), so the stored nomic vectors stay valid. Candidate removed.
- Attempt 1 (14:20:26Z) rolled back automatically at 14:21:18Z because of a bug in the check script (its Diary-path counter missed the first number, so it read 767). The service was fine: web path 200/768. The rollback was verified (override byte-identical to the backup, nomic loaded, embedding-service 200), and the fixed counter read 768 against b10920. Attempt 2 passed.
- After (attempt 2): healthy, restarts 0. nomic `loaded` without any request. On attempt 1 it went `unloaded` to `loaded` within 45 s: the #1717 watcher at work. The web path returns 200 with 768 dims. A throwaway container on `cowork_default` (the Diary's network; no Diary content touched) gets 768 numbers. `GET /api/v1/embedding-service` 200 (listed and loaded nomic). Embed error lines 0. Only `cowork-embed-1` changed among the cowork containers.

**Evidence: chat engine (plan B).**
- Gates right before the recreate: the Kev eval container `noevia-eval-decisions` stopped (exited 14:26:40Z, no restart in the following 3.5 min), llama idle count 0, 13 GiB available, no autotune or Appdata Backup.
- Flag check: every key in `models.ini` (including the per-preset `cache-ram` caps, #697, plus `spec-type`, `flash-attn`, `reasoning-format`, `cache-type-k`/`-v` and `-ngl`) exists in b11610's `--help`.
- Candidate: `--network none`, `--device none` (CPU), same command on port 8082, a read-only copy of `models.ini`, no model loaded. `/health` 200. All 8 presets parse and list as `unloaded`. The only error line is `gguf_init_from_file` for `laya_multilingual_f16.gguf`, a file that is already missing on disk. b11610 reads GGUF metadata while parsing presets and b10920 did not; it is not fatal, and the preset is still listed. Candidate removed.
- After: healthy, restarts 0. `/v1/models` lists the same 8 models as before. `--list-devices` in the live container shows `Vulkan0: AMD Radeon 890M Graphics (RADV STRIX1)`. One synthetic chat request on the Fast role model `gemma-4-12b-it-qat-q4_0` ("Reply with the word OK", `max_tokens` 8) returned HTTP 200 in 8.3 s including the model load, with no error and 10.6 tokens/s decode. `content` was empty with `finish_reason: length`: this preset has no `reasoning-format`, so the 8 tokens most likely went to the extracted reasoning. Not a benchmark. Llama error lines 0 (excluding the Laya file above). Web `/api/ready` `a03fbc63`. Only `cowork-llama-1` changed.
- The old image (`9f88885b…`, b10920) is still on disk. Nothing was pruned.

**Rollback** (either container alone; the b10920 image is local):


(Or restore both lines at once with `cp -p $O.bak.before-llamacpp-b11610-embed $O`, which predates both edits, then run `$UP embed` and `$UP llama`.) Run the idle gate before the llama recreate.

## Release a03fbc63 — 2026-10-14 14:09Z (web + model manager; live)

What changed for you: the New chat button works again (#1716). After the embedding container restarts, the model manager now loads the embedding model again by itself (#1717), so search does not wait for a first request.

**Rollback.**


## Diary switch TENANT_ASSERTION_IMPL=rust — 2026-10-14 13:52Z (Diary only; live)

What changed for you: nothing visible. The Diary now checks every web request's tenant signature twice, once in Python and once in the Rust `tenant-assertion` leaf. A request goes through only when both accept it (owner: "flip TENANT_ASSERTION_IMPL to rust, approved", #1147).

**Evidence.**
- Gates before the recreate: no other `up.sh` or `docker compose` running, llama idle count 0, no autotune or Appdata Backup.
- The recreate was diary-only: `up.sh … -d --no-build --no-deps --wait --wait-timeout 180 diary`, which exited 0 with Healthy. The image ID did not change, so the overlay is kept.
- `docker compose config` renders `rust` for diary only. `flags.sh cowork-diary-1 TENANT_ASSERTION_IMPL` reads `rust`. `tenant-assertion self-test` prints `ok`.
- Signed traffic: inside web, a `GET /api/health` signed with web's own `signTenantAssertion` and carrying a synthetic `X-Cowork-User-ID` returns 200 on python before the flip and 200 on rust after it. A tampered signature returned 401 before the flip, which shows the path is checked. Only status codes were read.
- Soak: 6 checks from 13:52 to 13:57:12Z plus one at 14:11:50Z. Each showed healthy, 0 restarts, 0 Diary 401/403/5xx, 0 tenant-assertion warnings, 0 tracebacks and a fresh signed 200. No real Diary use happened in that window, so only health and probe traffic ran under rust.

**Rollback** (Diary only; the key is removed by name, never by restoring `.env.bak` wholesale):


## Laya cutover 0.3.5-noevia5 — 2026-10-14 15:01Z (Laya only; live)

What changed for you: nothing visible. Laya now runs the image with the late-answer guards (#1074) and the native front (#1326). Owner-approved: "flip the Laya cutover to noevia too" (one Laya restart).

**Image diff (noevia4 → noevia5).** File lists differ only by `usr/local/bin/noevia-laya` (new, sha256 `59e26bf5…4763`). `/service/server.py` changed (sha256 `858f3909…c76d` in both the image and the live container): the #1074 guards (no send once an abandoned answer used the whole deadline; late mark only on the worker the request went to) and the #1326 framed engine worker (`--engine-worker`, u32 length + JSON, 16 KiB frames). Entrypoint `noevia-laya`. No dependency layer changed.

**Evidence.**
- Candidates (same image, `--network none`, read-only, uid 1000, cap_drop ALL, no-new-privileges, 6g, 2 CPUs, pids 128, model mount read-only, removed afterwards). Default mode at 1.8 s: process `python /service/server.py`, `/health` 200, synthetic 3-option decision `200 selected=answer` (answer 0.8878, code 0.0566, search 0.0556), 2.3 GiB. #1074 at the 0.5 s floor: overlapping and follow-up requests returned 503 (deadline), health stayed 200, then the same worker answered `200 answer` with no worker replacement, no traceback, 0 restarts. #1326 rust mode: `noevia-laya` parent + `python /service/server.py --engine-worker` child, `/health` 200, two decisions `200 answer` with identical scores.
- Gates: the cutover waited for the Kev decision eval (several rounds, including a live-Laya baseline run) and the reranker eval to stop. At 15:01:07Z: llama activity 0 in 3 min, Laya CPU 0, no eval container, harness, `up.sh`, autotune or backup process.
- After: `cowork-laya-1` id `712f944f…`, image noevia5, healthy, restarts 0, `LAYA_DECISION_TIMEOUT_S=1.8` kept. One synthetic decision from `cowork-web-1` via its `COWORK_DECISION_URL`: `200 selected=answer`, 575 ms. Of 38 running containers only `cowork-laya-1` changed id or start time. Web log soak 15:01:38Z–15:07:25Z: 0 decision/Laya timeout or error lines (no real decision traffic in that window); Laya healthy, restarts 0, 0 traceback lines, 2.2 GiB.
- Files on the deployment host: compose backup `docker-compose.yml.bak.before-laya-noevia5`; script/log `state/laya-noevia5/recreate.sh`, `state/laya-noevia5.log`; identity snapshots `state/laya-noevia5/{before,after}.txt`; image diff `state/laya-noevia5-diff/`.

**Rollback (to noevia4).**


Then check: image `cowork-laya:0.3.5-noevia4`, healthy, restarts 0, a synthetic `/v1/decisions` returns `selected` in the options.

## Docling native mode on — 2026-10-14 13:42Z (`NOEVIA_DOCLING_IMPL=rust`; live)

What changed for you: nothing visible. Document extraction now goes through the native `noevia-docling` server (#1322), with the same results: the synthetic PDF reads correctly and Markdown still gets the 415 "unsupported" answer. Owner-approved: "flip NOEVIA_DOCLING_IMPL to rust, approved".

**Rollback (python mode, same image).**


Then check: `NOEVIA_DOCLING_IMPL=python` in the container, child `python server.py`, `/health` 200, P4 PASS. This exact rollback ran during attempt 1 and passed.

## Docling cutover 785643f4 — 2026-10-14 13:30Z (native mode off; live)

What changed for you: Markdown files no longer go to Docling. They now get a clear "unsupported" answer (415) instead of the misleading "processing limits" error (#1711). PDF and other document extraction works as before. Native Docling stays off: `NOEVIA_DOCLING_IMPL` is not set, so the service runs `python server.py` (#1322, owner switch).


Note that rolling back brings back the #1711 `.md` 422.

## Release 785643f4 — 2026-10-14 13:04-13:20Z (web; model manager Rust front; settings-driven embedding live; Docling candidate built)

What changed for you:
- Cloud chats only see history from turns that went to that route (#1703).
- Summaries name only tools that exist (#1704).
- Performance → Memory budget shows estimates again, as do Will it fit?, the load-budget guard and calibration starting settings (#1708).
- A fetch where every URL failed shows a red ✕ (#1707).
- Projects shows a loading skeleton and an error with Retry (#1709).

Behind the scenes:
- The model manager runs its Rust front (owner-approved, #1689).
- The embedding service is now driven by Settings (#1668). It still serves the same model, nomic-embed-text-v1, so retrieval did not change and nothing was re-indexed.
- No model was switched, turned off, loaded beyond nomic, or deleted.
- No chat, tune or benchmark was run.

- **#1668 and the flip together.** Restore by key, not a whole `.env` copy:

  ```sh
  sed -i '/^MODEL_MANAGER_IMPL=/d;/^EMBED_MODEL_FILE=/d' $env
  cp -p $ovr.bak-1668-20261014-090939 $ovr
  $UP model-loader; $UP embed; $UP web
  ```

  The old embed command loads nomic from its fixed path. `embedding.ini` and `embedding-service.json` are ignored by the python front and can stay.
- **Web to fbb960dd:**

  ```sh
  ln -sfn $base/releases/fbb960dd $base/current
  sed -i 's/^COWORK_VERSION=.*/COWORK_VERSION=fbb960dd/' $env
  $UP web
  ```

  Preflight copy: `tools/preflight.bak.before-785643f4`.

## Docling cutover attempt fbb960dd — 2026-10-14 10:45Z (rolled back; no live change)

What changed for you: nothing. Docling stays on `cowork-docling:f6885a55`. The cutover to the native-off candidate was rolled back after the post-check P4 conversion failed. The same check also fails on the existing image, so this is filed as #1711.


## Release fbb960dd — 2026-10-14 (tool-call follow-ups, Models page prune, embedding warm-up; web + model manager)

What changed for you: an Auto (Fast) follow-up turn keeps its web search tools again (#1692), and a Code route turn that only produced reasoning now gets a final-answer round (#1693). A failed reply's private tool output is no longer sent to a cloud model on the next turn (#1700, #1702), and the Nextcloud rate limit is now per user (#1701). Tool calls that returned an error, including plain-text `ERROR:` results, no longer show a green check (#1694, #1699). Deleting a model now reloads the engine's preset list, and the Models page removes leftover presets for files that are gone when an admin opens it (#1695). It refuses to remove anything if the folder scan is empty or more than half would go (#1698). The model manager has the rs#104 embedding warm-up fixes (#1682, #1685, #1696); it still runs the python front, so the #1668 embedding service stays inactive. No chat, model load, switch, delete, prune, tune or benchmark was run to test this.

**Evidence.**
- CI green: noevia#1705 (8/8 incl. "Assembled release (pinned repos)") and `fbb960dd` on main, noevia-services#42 (6/6). Every archive sha256 (rs, core, web, services) was fetched twice from codeload, both matching. Core's front-contract workflows pin rs `7dc9bb4`; rs#104 touched only `bins/noevia-model-manager`, so they were not re-pinned.
- Assembled on the Mac from a clean checkout; `release-refs` matches the lock.
- `candidate-boot.sh` was ready at `fbb960dd` with 0 error lines for both `node` and `rust`.
- Model-loader candidate (no network, read-only, all capabilities dropped, tmpfs, throwaway token): health 200, 0 error lines, removed.
- Idle gate before each recreate: 0 generation lines in `cowork-llama-1`'s last 3 minutes. The native-autotune job reads `failed` (2026-10-13), and none was running. The Appdata Backup (04:10 EDT) had finished and was not running.
- After:
  - `/api/ready` `{"ready":true,"version":"fbb960dd"}` on loopback and on https://noevia.example.com; signed-out `/api/projects` 401.
  - Served `index.html` sha256 `4ecf07bc…f4f7` (was `4ba8ddbc…79d5`); assets `index-DWQEVJSk.js` and `index-DcnwelK8.css` (were `index-DngQeQDa.js` and `index-3UZdOIkM.css`).
  - #1695 one-time cleanup, read only (prune not called): the model-loader scan lists 5 files. 4 ordinary preset sections, 0 with a missing file. The guard would allow the prune, and it would remove nothing.
- Containers: only `cowork-web-1` and `cowork-model-loader-1` changed id. The other 39, including Laya, embed, llama, Docling, OCR, Diary and code-sandbox, kept their start times. Both changed containers are healthy with restart count 0. Snapshots: `state/snapshot.{before,after}-fbb960dd.txt`.

## Release 20b07d3f — 2026-10-14 (chat, UI and backend batches, embedding guards; web + model manager + Diary overlay)

What changed for you: the chat batch (core#100) retries a turn that came back with reasoning only or that promised a tool call without making one (#1477, #1552, #1587, #1592, #1604). Engine rows in Settings no longer stay on "Checking", and raw restart errors are now translated (#1545). The Features page has plain text for the Preview and Offline Wikipedia rows (#1580). The Models page now refuses to switch to an embedding model that the embeddings server doesn't serve (core#97). Code for the settings-driven embedding service (#1668) is included but **not active** (see Model manager below). Embeddings still run on `nomic-embed-text-v1`, unchanged. The Diary companion now has the #1636 per-model vector slots, with nomic as the active slot, so nothing was re-indexed. No chat, Diary message, model load, switch, delete, tune or benchmark was run to test this.

**Evidence.**
- CI green: noevia `20b07d3f` (8/8 incl. "Assembled release (pinned repos)"), noevia-core `668afe05` (9/9), noevia-web `5f0b956a` (2/2), noevia-rs `0012da31` (20/20), noevia-services `e8c91b9a` (6/6).
- The release was assembled on the Mac from a clean detached worktree; `release-refs` matches the lock.
- `candidate-boot.sh` was ready at `20b07d3f` with 0 error lines for both `node` and `rust`.
- Model-loader candidate (no network, read-only, tmpfs, synthetic token): health 200. Laya candidate: `server.py` matches the release, entrypoint `noevia-laya`, an unknown selector is refused. No model was started.
- Idle gate before each recreate: 0 generation lines in `cowork-llama-1`'s last 3 minutes; native-autotune job `failed` (2026-10-13), none running. The Appdata Backup plugin's 04:10 EDT run was waited out first.
- After:
  - `/api/ready` `{"ready":true,"version":"20b07d3f"}` on loopback and on https://noevia.example.com; signed-out `/api/projects` 401.
  - Served `index.html` sha256 `4ba8ddbc…79d5` (was `d59236b4…16d3`).
  - Embed: `/v1/models` lists `nomic-embed-text-v1`, and `/v1/embeddings` returns 768-dim vectors from both web's `EMBEDDING_BASE_URL` and the Diary's `LLM_EMBED_BASE_URL` (`http://embed:8080/v1`), before and after the Diary overlay.
  - Diary health via web 200.
  - #1379: a synthetic diagnosis in `cowork-model-loader:20b07d3f` returns `api_key=[redacted]`.
- Containers: only `cowork-web-1`, `cowork-model-loader-1` and `cowork-diary-1` changed id. The other 38, including Laya, embed, llama, Docling, OCR and code-sandbox, kept their ids and start times. Restart count 0 and healthy on all cowork containers. Snapshots: `state/snapshot.{before,after}-20b07d3f.txt`.

  The entrypoint keeps the Python server unless `NOEVIA_LAYA_IMPL=rust`. To roll back, restore the compose backup and rerun step 3.
- #1668: run the "Pending (release)" migration in `docs/deployment.md`. (The Rust model-manager front is always on since #1071; the umbrella `MODEL_MANAGER_IMPL` this item once asked to flip is retired.)
- #1322: an independent review of the native Docling overlay.

## Release d119c502 — 2026-10-14 (Models page overhaul, upload fixes; web only)

What changed for you: the Models page was rebuilt around what each model is assigned to (#1660-#1663): deleting a model now also removes its preset, so it no longer lingers as "File missing" (#1661), and the new assignments overview shows which model serves each role (#1662). Uploads got follow-up fixes, and files orphaned by a failed upload are cleaned up (#1653, #1664). Members no longer see environment variable names (#1656). The statistics route got small fixes (#1654). All Rust switches stay on, as before. No chat, Diary message, model load, delete, tune or benchmark was run to test this.

## Release 2461e63b — 2026-10-14 (core main released, #1647 hold lifted; Rust stats and routing-default built in; web only)

What changed for you: the hybrid sensitivity check now reads the decision service's confidence correctly (#1640), and hybrid routing can only reach a cloud model through a sensitivity model that passed qualification (#1647). No model is qualified yet, so **hybrid stays local** until one is. Tool results from your storage or Drive stay local under hybrid as well (#1646), and the "Send to cloud" card now says that private files may be sent for that turn (#1657). Uploading a file with a name that is already taken no longer silently replaces the project source (#1454), and renaming a project moves its storage folder (#1458). Date answers get the ISO week right (#1603). Signing in as another user in a different tab no longer leaves this tab showing the old account's state (#1643). The metrics and routing popovers no longer overlap (#1649). The embedding settings gained profiles (#1636); the default stays `nomic-v1`, nothing was re-indexed and `embed-next` was not started. The Rust front now includes the routing-default and engine statistics routes (`rust-routing-default`, `rust-stats`), but their switches stay off. No chat, Diary message, model load, tune or benchmark was run to test this.

## Release 1aed463c — 2026-10-13 (UI batch, Diary out of the page, 404 shell; web only)

What changed for you: the Diary is no longer kept hidden in the page behind the other views, so its text cannot leak into a chat tab (#1635). The Nextcloud connector tile and the empty-state icons now carry the two-tone accent, and the row you are on is fully accented (#1623 follow-ups). Chat titles made from a long first message end at a word with an ellipsis (#1601, #1579); a line break inside a comparison-table cell is shown as a break (#1598) and wide tables scroll with a visible fade at the edge (#1599); the turn metrics popover no longer squeezes or clips its values (#1610); the routing details popover opens above the message box instead of over the send button (#1631). Opening a page that does not exist now shows the app with a "not found" instead of a bare error (#1620). The Rust projects store now skips malformed file entries the way the Node server does (#1621); it is only used once `NOEVIA_RUST_PROJECTS` is turned on, which it is not. The live Compose file now passes the five remaining Rust switches to web, all off (#1400). No chat, Diary message, model load, tune or benchmark was run to test this.

**Held.** noevia-core main (`f10e5a9`, core#85 #1640 and later) is not in this release: release hold #1647.

## Release d907438b — 2026-10-13 (two-tone icons, visual fixes, Automatic tools; web only)

What changed for you: decorative icons now have a two-tone accent in the theme colour, while icons you can click stay one colour (#1623). Project names on cards no longer break through the middle of a hyphenated name (#1542), and Restore on an archived project restores it instead of opening it (#1626). The Add files and tools menu is no longer see-through (#1627), the engine metrics panel opens above the message box instead of covering the send button (#1628), the Code home project grid is centred (#1629), and the Push to git option no longer wraps onto its own row (#1630). In Automatic tools mode, a message that needs the web or your Nextcloud now gets Web search and Nextcloud offered to the model, so it can look things up instead of saying it cannot browse (#1550). No chat, Diary message, model load, tune or benchmark was run to test this.

**Open.** The preflight still warns that the live Compose file does not pass the four `NOEVIA_RUST_*` web keys (#1400; advisory). Haiku live testers follow this release.

## Release ab1445b0 — 2026-10-13 (2026-10-12 integration; web, Diary and model manager; MODEL_AUTOCONFIG=rust)

What changed for you: the 2026-10-12 sweep is live. Sidebar search finds chats by what was said in them, and the sidebar has keyboard navigation; storage failures and Retry are worded more clearly; focus rings and phone-width layouts were fixed in several places; the Usage page, Code Plugins/Customise and the Diary overview load and lay out better. The public site now sends HSTS (six months, no `includeSubDomains`) and a Permissions-Policy that turns off camera, microphone, location, payment and the other device features the app never uses (#1480). The Diary keeps the model's reasoning out of streamed and saved text, and its storage-backup reply only says storage was contacted after a verified remote run (#1609). The Models page's size recommendation is now double-checked by the Rust port (`MODEL_AUTOCONFIG=rust`, #1137); every recommendation it gave was the same before and after. No chat, Diary message, model load, tune or benchmark was run to test this.

**Open.** The preflight warns that the live Compose file does not pass `NOEVIA_RUST_USAGE`, `NOEVIA_RUST_SAMPLING_SETTINGS`, `NOEVIA_RUST_REASONING_SETTINGS` and `NOEVIA_RUST_ROUTING_MODE` to web (#1400; advisory, the switches stay at their off defaults). Brave click-through and Haiku live testers follow this release.

## Release 4746fb83 — 2026-10-12 (Diary companion answers again, #1422 #1065; web and Diary)

What changed for you: the Diary companion answers again. It had been set to a model name the local server does not serve, so every reply failed; it now uses a model the local server does serve (when the configured name is not one of them it falls back to a served chat model, and the Diary health reply says which). When a Diary reply fails before anything was saved, the app now says nothing was saved and puts your message back in the box instead of leaving an "uncertain" banner. The banner that used to stay stuck now offers Show it, Put back and Dismiss, and the old stuck exchanges from 2026-10-12 and 2026-09-18 can be dismissed. Nothing about your saved Diary entries changed, and no chat or Diary message was sent to test this.

## Release d7b6081d — 2026-10-12 (files attached to a free chat are shown with your message, #1441; web only)

What changed for you: files you attach to a chat are now presented to the model as attached to your message, so it stops saying nothing was attached. A message sent right after attaching waits up to 30 seconds for the file to be read instead of going out without it. The privacy check still reads attached files.

## Release 96691012 — 2026-10-12 (no "This looks sensitive" card when the privacy check cannot answer, #1421; web only)

What changed for you: in Hybrid, when the privacy check cannot give an answer, the turn stays local and no "This looks sensitive" card appears. The Local badge tooltip says why it stayed local, so there is nothing to approve or dismiss.

## Release 8d0b2e0a — 2026-10-12 (Nextcloud browser sign-in, #1427 #1432 #1433; web only)

## Release fdd5b48a — 2026-10-12 (M4 free-chats slice available, off by default)

## Release fca7489a — 2026-10-12 (M4 chat-list slice available, off by default; missing-model popup)

## Release dd15bf6f — 2026-10-12 (mobile layout repair #1314, reviewed Core and native sidecar pins; web only)

## Release cf521caa — 2026-10-11 (M6 native auth ownership guard pinned)

**Rollback.** Repoint `current` and `COWORK_VERSION` at `b44dae9a` and re-run the guarded `up.sh` for `web`; `cowork-web:b44dae9a` is kept.

## Release b44dae9a — 2026-10-10 (native sampling settings wired, default off; M6 with merged runtime pins, #1304)

Nothing is switched on by this entry. `NOEVIA_RUST_SAMPLING_SETTINGS` is passed through `compose.yaml` and the Unraid example with the default `0`, and listed in `deploy/preflight/web-env-keys.txt`. When it is `1`, `build/web-supervisor.sh` refuses to start unless `NOEVIA_RUST_AUTH=1` and the `rust-sampling-settings` feature are both present. The switch value on the live box for this release is not recorded in this repository.

## Release 4e9ca4c2 — 2026-10-10 (default-off native usage preflight key and isolated image qualification, #1291)

Nothing is switched on by this entry. `NOEVIA_RUST_USAGE` is listed in `deploy/preflight/web-env-keys.txt`, so the preflight's env-key drift check expects it. The web image copies the compiled native front into a qualification stage before the code-actions qualification test runs (#1279), and CI runs that test in its own step. The switch value on the live box for this release is not recorded in this repository.

## Release 9e9bdc0f — 2026-10-10 (S3 native OCR acceptance)

## Release 21057c0c — 2026-10-10 (M4 slice 1: Rust project images available, off by default)

**Evidence.** rs#64 (all 10 checks green, incl. the corpus replay through the Rust front with `NOEVIA_RUST_PROJECTS=1`) and core#60 (3 checks) were green; `core.ref` and the auth fixture's `core` field were moved to the core#60 squash (identical tree, only the sha changed). On the box: `/api/ready` returned `{"ready":true,"version":"21057c0c"}` locally and through the public URL; `noevia-server --features` lists `code-net-guard`, `header-read-timeout`, `rust-auth`, `rust-projects`; `flock --version` is util-linux 2.38.1; `flags.sh cowork-web-1` output is identical before and after; no error lines in the web log. No autotune, calibration or Coding job was running before the cutover. The switch is not turned on: with it off Node keeps owning project images exactly as before.

## Release 80852237 — 2026-10-10 (M3: Rust sign-in available, off by default)

**Evidence.** rs#63 fixed the differential test after core#58 (noevia#1254) made setup store `public_origin_admin`: the fixture now has a current scenario (Rust must equal Node) and a legacy one (no admin row; Rust accepts only what both Node states accept). All 9 rs checks and the 5 services checks were green; noevia CI incl. Assembled release was green. On the box: `/api/ready` returned `{"ready":true,"version":"80852237"}`, `noevia-server --features` lists `code-net-guard header-read-timeout rust-auth` (the old image lacked `rust-auth`), `flags.sh` output is identical before and after, the web log has no error or warning lines, and `/api/profile` still answers 401 without sign-in. No autotune, calibration or Coding task was running when web was recreated.

## Flag enabled 2026-10-09 — `BROWSER_POLICY_IMPL`, `TOOL_GATE_IMPL` and `TOOLBOXES_PERMITTED_IMPL` = `wasm` (config only; live web stays be3043cd)

**Evidence.** Switch proof: the release candidates for [#1226](https://github.com/sbstndalton/noevia/pull/1226) and [#1228](https://github.com/sbstndalton/noevia/pull/1228) and Haiku round 11 (0 failures, clean 2 h log). Candidate first, with the live environment: a throwaway `cowork-web:be3043cd` with the live container's environment in a private temp env-file (mode 600, shredded, never printed) plus the three keys `wasm`, on a throwaway `--internal` network where the alias `egress` resolved to the candidate, read-only root, all capabilities dropped, no-new-privileges, tmpfs for writable paths, no state or model mounts. Healthy, 0 restarts, `dav-parse.wasm verified for GGUF_META_IMPL, CODE_ACTIONS_IMPL, PROJECT_FILE_NAMES_IMPL, PROVIDER_EGRESS_IMPL, BROWSER_POLICY_IMPL, TOOL_GATE_IMPL, TOOLBOXES_PERMITTED_IMPL`, `codenet.guarding`, `/api/ready` 200, and zero impl_mismatch, wasm_fault, unverified, toolboxes_permitted, FATAL, too_large or failing closed lines. Container, network and env-file removed. Idle gate before the recreate: autotune and calibration state files unchanged (2026-10-08 01:21, 2026-09-23), no tune, bench or download container, no task lines in the web log, both code-sandbox containers hold a single sleeping `node`, nothing above 4 percent CPU (model-loader). Live after: healthy, 0 restarts; `deploy/tools/flags.sh cowork-web-1` (38 lines) differs from before in exactly the three keys (`js` to `wasm`); the verified line lists all seven `wasm` switches; `codenet.guarding` on `172.28.0.3` (same as before); 196 MCP tools (noevia 10, nextcloud 181, tavily 5); `/api/ready` 200 locally (version `be3043cd`) and on noevia.example.com; zero `impl_mismatch|wasm_fault|unverified|failing closed|too_large|toolboxes_permitted|FATAL` lines over a 10 minute soak (23:01 to 23:11 UTC), no `toolboxes_permitted.wasm_fault`. No chat, model run, load, tune, browser or Coding task; no Diary access.

## Flag enabled 2026-10-09 — `CODE_ACTIONS_IMPL=wasm` and `PROVIDER_EGRESS_IMPL=wasm` (config only; live web stays 22e5c113)

## Release be3043cd — 2026-10-09 (TOOL_GATE_IMPL and TOOLBOXES_PERMITTED_IMPL, dark; #1223 and #1224 fixed in the live JS; web and core; live)

## Release 3d06ea7d — 2026-10-09 (BROWSER_POLICY_IMPL, dark; #1218 and #1219 fixed in the live JS; web and core; live)

## Release 22e5c113 — 2026-10-09 (#1212 code-actions linear and limited in the Rust port; #1211 NFD names; web and core; live)

**Evidence.** Source: noevia main `22e5c113` (#1217, CI green incl. Assembled release); core#47 CI green after the test-only timing bound change (5000-level and refusal cases < 50 ms on CI; 40 to 1000 levels stay < 10 ms). Release tarball sha256 `e09149aa...59b5`, assembled on the Mac and identical on the box; image built on the deployment host with `build-web-release.sh` (`version.json` web `20961fc3` / core `2ac82a06`); `dav-parse.wasm` in the image `7f1ff7d3...fe58`, equal to the pin and to the noevia-rs `fed419ee` CI build. Before: native autotune and calibration state `passed`, no task lines in the web log for 10 minutes, llama and web under 3% CPU. Candidate (internal throwaway network with an `egress` alias, read-only, caps dropped, tmpfs, synthetic tokens, `CODE_ACTIONS_IMPL=wasm`, `PROJECT_FILE_NAMES_IMPL=wasm`): healthy, `/api/ready` 200 with version `22e5c113`, `dav-parse.wasm verified for GGUF_META_IMPL, CODE_ACTIONS_IMPL, PROJECT_FILE_NAMES_IMPL`; classify of a 40-level chain (613 chars) 0.565 ms and of a 1000-level chain (15013 chars) 0.767 ms through the Rust port (best of 20; JS 0.139 and 0.155 ms), replies identical to the JS and not `unverified`; `Cafe\u0301.md` and `Caf\u00e9.md` resolved to the same stored file in all four NFC/NFD combinations and under a folder, equal to the JS; no mismatch or fault lines; containers and network removed (the live switches were not flipped). Live: healthy, 0 restarts, started 2026-10-09 20:45:11 UTC; `/api/ready` 200 locally and on noevia.example.com; `deploy/tools/flags.sh cowork-web-1` identical before and after (`CODE_ACTIONS_IMPL=js`, `PROJECT_FILE_NAMES_IMPL=wasm`, `GGUF_META_IMPL=wasm`, `PROVIDER_EGRESS_IMPL=js`); live `dav-parse.wasm` `7f1ff7d3...fe58`; public `index-BAGxJsT9.js` and `index--Fp75r-d.css` byte-identical to the container's; 196 MCP tools across 3 servers; `codenet.guarding` on `172.28.0.3`, same as before; a before/after snapshot of all containers (`backups/snapfull-before-1212.txt`, `snapfull-after-1212.txt`, `snapfull-after10m-1212.txt`) differs only in `cowork-web-1` (also after 10 minutes, with no `impl_mismatch`, `wasm_fault`, `unverified` or `FATAL` line, 0 restarts). No model run, load or tune. Backup: `config/.env.bak.before-22e5c113`.

## Release a6b287da — 2026-10-09 (PROVIDER_EGRESS_IMPL, dark; #1208 and #1209 fixed in the live JS; web and core; live)

**Evidence.** Source: noevia main `a6b287da` (#1214, CI green incl. Assembled release). Release tarball sha256 `658a6ae1...4f40`, assembled on the Mac and identical on the box; image built on the deployment host with `build-web-release.sh` (`version.json` web `20961fc3` / core `263aff90`); `dav-parse.wasm` in the image `68cf8a00...8a9d`, equal to the pin and to the noevia-rs `68d8fbce` CI build. Before: native autotune state `passed` (files unchanged), no task lines in the web log for 10 minutes, llama and web under 1% CPU. Candidate (internal throwaway network with an `egress` alias, read-only, caps dropped, tmpfs, synthetic tokens, `PROVIDER_EGRESS_IMPL=wasm`): healthy, logged `dav-parse.wasm verified for PROVIDER_EGRESS_IMPL`, `/api/ready` 200 with version `a6b287da`, no mismatch or fault lines; containers and network removed (the live switch was not flipped). Live: healthy, 0 restarts, started 2026-10-09 20:07:49 UTC; `/api/ready` 200 locally and on noevia.example.com; `deploy/tools/flags.sh cowork-web-1` identical before and after except the new key (`PROVIDER_EGRESS_IMPL=js`; `CODE_ACTIONS_IMPL=js`, `PROJECT_FILE_NAMES_IMPL=wasm`, `GGUF_META_IMPL=wasm` kept); 196 MCP tools across 3 servers; `codenet.guarding` on `172.28.0.3`, same as before; a before/after snapshot of all containers (`backups/snapfull-before/after-provider-egress.txt`) differs only in `cowork-web-1` (also after 10 minutes, with no `impl_mismatch`, `wasm_fault`, `unverified` or `FATAL` line, 0 restarts). No model run, load or tune. Backups: `config/.env.bak.before-a6b287da`, `docker-compose.override.yml.bak.before-provider-egress`.

## Flag enabled 2026-10-09 — `CODE_ACTIONS_IMPL=wasm` and `PROJECT_FILE_NAMES_IMPL=wasm` (config only; live web stays 240eea5f)

## Release 240eea5f — 2026-10-09 (CODE_ACTIONS_IMPL + PROJECT_FILE_NAMES_IMPL, dark; #1201 find -exec fix live; web and core; live)

**Evidence.** Source: noevia main `240eea5f` (#1205, CI green incl. Assembled release). Release tarball sha256 `3eac5483...14a9`, assembled on the Mac and identical on the box; image built on the deployment host with `build-web-release.sh` (`version.json` web `20961fc3` / core `44165041`). Before: native autotune/calibration state files unchanged, no tune, bench or download container, no container over 5% CPU, no task lines in the web log. Candidate (internal throwaway network with an `egress` alias, read-only, caps dropped, tmpfs, synthetic tokens, both new switches `wasm`): healthy, logged `dav-parse.wasm verified for CODE_ACTIONS_IMPL, PROJECT_FILE_NAMES_IMPL`, `/api/ready` 200 with version `240eea5f`; container and network removed (the live switches were not flipped). Live: healthy, 0 restarts; `/api/ready` 200 locally and on noevia.example.com; `dav-parse.wasm` sha `94d37fa8...b793` (was `a0388ae5...`); `deploy/tools/flags.sh cowork-web-1` identical before and after except the two new keys (`CODE_ACTIONS_IMPL=js`, `PROJECT_FILE_NAMES_IMPL=js`); 196 MCP tools across 3 servers; `codenet.guarding` on `172.28.0.3`, same as before; a before/after snapshot of all containers (`backups/snapfull-before/after-240eea5f.txt`) differs only in `cowork-web-1` (also after 10 minutes, with no `impl_mismatch`, `wasm_fault`, `unverified` or `FATAL` line, 0 restarts). No model run, load or tune.

## Release 1c5172fb — 2026-10-09 (retire nine always-Rust switches; web and core, #1071 batch 3; live)

**Evidence.** Source: noevia main `1c5172fb` (#1202, CI green incl. Assembled release, offline-contract and tooling tests). Release tarball sha256 `ee164c9b...fb44` assembled on the Mac and identical on the box; the web image was built on the deployment host with `build-web-release.sh` (`version.json` web `20961fc3` / core `88d8e398`). Before: autotune and calibration state files unchanged (2026-10-08 01:21 and 2026-09-23), no tune, bench or download container, no container over 5% CPU, no task lines in the web log. Candidate (internal throwaway network with an `egress` alias, read-only, caps dropped, tmpfs, synthetic tokens, all nine switches set to `js`): healthy, nine `X is retired; Rust is always used` warnings, `dav-parse.wasm verified`, `codenet.guarding`, `/api/ready` 200 with version `1c5172fb`; container and network removed. Live: healthy, 0 restarts; `/api/ready` 200 locally and on noevia.example.com; `dav-parse.wasm` sha `a0388ae5...` (unchanged); `deploy/tools/flags.sh cowork-web-1` output (32 lines, including `GGUF_META_IMPL=wasm`) identical before and after; no retired warnings (live values are `wasm`); 196 MCP tools across 3 servers; `codenet.guarding` on `172.28.0.3`, same as before; zero `impl_mismatch`, `wasm_fault`, `failing closed`, `unverified`, `too_large` or retired lines over the first 10 minutes. `dist/` asset file names differ from 1e4e3b82 because the release stamp is baked into the bundle (same web ref `20961fc3`). A before/after/after-10-min snapshot of all containers (id, start time, restart count, image; `backups/snapfull-before/after/after10m-1c5172fb.txt`) differs only in `cowork-web-1` (also after 10 minutes, with no `impl_mismatch`, `wasm_fault`, `unverified` or `FATAL` line, 0 restarts). No model run, load or tune.

## Release 1e4e3b82 — 2026-10-09 (Retry forwarding log, Diary reset warnings, Diary retry QA; web and Diary; live)

**Evidence.** Idle gate before the web cutover and again right before the Diary overlay: autotune and calibration jobs `passed`/`Done` (state files unchanged since 2026-10-08 01:21 and 2026-09-23), no bench, tune or download container, both sandboxes running only their supervisors (read from `/proc`), no task or chat lines in the web log; loaded model `gemma-4-12b-it-qat-q4_0`, unchanged. No model was run, loaded, tuned or downloaded. Release tarball sha256 `f5011bd5...4209` identical on the Mac and the box; web built on the box by `build-web-release.sh`. Synthetic candidate (`--network none`, read-only, caps dropped, tmpfs): healthy, `/api/ready` 200 version `1e4e3b82`, `dav-parse.wasm verified for GGUF_META_IMPL`, the Retry log line present in `routes/diary.cjs`.

Web live: healthy, 0 restarts; `/api/ready` `{"ready":true,"version":"1e4e3b82"}` locally and on noevia.example.com (site 200); `/version.json` web `20961fc3` / core `921a03d5`; `dav-parse.wasm` sha `a0388ae5...` unchanged; `deploy/tools/flags.sh` output for web, model loader and Diary identical before and after (including `GGUF_META_IMPL=wasm`); 196 MCP tools; `codenet.guarding` on `172.28.0.3`, same as before; zero `impl_mismatch`, `wasm_fault`, `failing closed`, `too_large` or `unverified` lines over 10 minutes after the last web restart (16:33 to 16:43 UTC).

Diary live: healthy, 0 restarts, `tenant-assertion self-test` ok, web to Diary health 200, no traceback; the overlaid `storage_backoff.py` logs both reset lines with `log.warning`.

## Flag enabled 2026-10-09 — `GGUF_META_IMPL=wasm` (config only; live web stays 3eab05e3)

**Evidence.** Proof for the switch: [#1108](https://github.com/sbstndalton/noevia/issues/1108) real Gemma 3/4 and Qwen3 headers return identical summaries via wasm using 8-17% of the byte budget ([noevia-core#42](https://github.com/sbstndalton/noevia-core/pull/42)). Candidate first: a throwaway `cowork-web:3eab05e3` with the live environment (private temp env-file, shredded afterwards) plus `GGUF_META_IMPL=wasm`, on a throwaway `--internal` network where the alias `egress` resolved to the candidate, read-only root, tmpfs for writable paths, `/models` and `/cache` mounted read-only so the reader runs. Healthy, 0 restarts, `dav-parse.wasm verified for ...` listing `GGUF_META_IMPL`, no impl_mismatch, wasm_fault, failing closed, too_large, impl_refused or unverified line, `/api/ready` 200. (MCP discovery and the model-manager scan failed there only because the network is isolated.) Inside it, the web's own `gguf-meta.readSummary` over all 16 installed `.gguf` files (the main models, their projectors, the embed and the reranker model) returned summaries identical to the live `js` result. The `OsaurusAI` model directory holds no GGUF files. Candidate and network removed. Idle check before the recreate: autotune and calibration jobs `passed`/`Done` (state files unchanged since 2026-10-08 01:21 and 2026-09-23), code-sandbox and code-verify running only their supervisors (read from `/proc`), no container over 3% CPU, no task lines in the web log, no model load. Live after: healthy, restart count 0; `deploy/tools/flags.sh` shows `GGUF_META_IMPL=wasm`, and a diff of all 32 allow-listed switches against before shows that one line only; the verified line lists `GGUF_META_IMPL`; `codenet.guarding` on `172.28.0.3` (same as before); 196 MCP tools (noevia 10, nextcloud 181, tavily 5); `/api/ready` 200 locally and on noevia.example.com; the same read run inside the recreated live web (impl `wasm`) is identical to the pre-flip `js` result for all 16 files; zero `impl_mismatch|wasm_fault|failing closed|too_large|impl_refused|unverified|gguf-meta` lines over a 10 minute soak (15:37 to 15:48 UTC). No chat, model run, load or tune.

## Release 3eab05e3 — 2026-10-09 (KaTeX math, Diary reset logging, per-layer GGUF arrays; web, model manager and Diary; live)

**Evidence.** Before each cutover: autotune and calibration jobs `passed` (state files unchanged since 2026-10-08 01:21 and 2026-09-23), no bench, tune or download container, both sandboxes running only their supervisors (read from `/proc`), no task or chat lines in the web log, web, llama, both sandboxes and the loader at about 0% CPU. Loaded model `gemma-4-12b-it-qat-q4_0`, unchanged; no model was run, loaded, tuned or downloaded. Release tarball sha256 `29cd9194...e1da` identical on the Mac and the box. Web was built on the box by `build-web-release.sh` from the assembled tree; the model loader with `docker build releases/3eab05e3/services/model-manager`. Web candidate (`--network none`, read-only, caps dropped, tmpfs, synthetic): `/api/ready` 200 version `3eab05e3`, `dav-parse.wasm verified`, 61 KaTeX assets in `dist`. Loader candidate imports `gguf_meta`, `model_files`, `api`.

Web live: healthy, 0 restarts; `/api/ready` `{"ready":true,"version":"3eab05e3"}` locally and on noevia.example.com (site 200); `/version.json` web `5e0f0fe3` / core `5ba42d84`; `dav-parse.wasm` sha `a0388ae5...f1c3` unchanged; the effective `*_IMPL`/`NOEVIA_FEATURE_*`/`LAYA_LOAD_ADVISOR`/`COWORK_CODE_NET_ADDR` list identical before and after; 196 MCP tools across 3 servers; `codenet.guarding` on `172.28.0.3`, same as before; zero `impl_mismatch`, `wasm_fault`, `failing closed` or `unverified` lines over the first 10 minutes.

Model loader live: healthy, 0 restarts, `MODEL_AUTOCONFIG=python`, `GGUF_PARSER=rust`, `MODEL_FILES_IMPL=rust`. Autoconfig for all 8 sections at presets `fast` and `long-ctx` (16 answers) is byte-identical before and after; `models.ini` sha256 `41da90dd...` unchanged. Read-only Discover estimate (`GET /api/v1/search/repo?repo=LiquidAI/d1-3B-GGUF`) now returns a real estimate (Fast, 32K context, 30/30 layers on GPU) for the four GGUF groups; before it returned empty `estimates` with `estimatesReason` (#1186, #1159).

Diary live: healthy, 0 restarts, `tenant-assertion self-test` ok, `TENANT_ASSERTION_IMPL` unset, web to Diary health 200, no traceback in the log.

## Release f790069a — 2026-10-09 (hybrid-model autoconfig: recurrent state and attention layers, Discover estimate reason; web and model manager; live)

**Evidence.** Before: autotune and calibration state files unchanged (2026-10-08 01:21 and 2026-09-23), no task lines in the web log, sandbox and verifier running only their supervisors at 0% CPU (`docker top`), no container over 5% CPU, no model load in progress. Loaded model `gemma-4-12b-it-qat-q4_0`, unchanged. Release tarball sha256 `fcea4364...fc48` identical on the Mac and the box. Web was built on the box by `build-web-release.sh` from the assembled tree (no Mac-built dist layered onto an old image); the model loader with `docker build releases/f790069a/services/model-manager`. Candidate (`--network none`, read-only, caps dropped, tmpfs, synthetic): `/api/ready` 200 version `f790069a`, `dav-parse.wasm verified`; loader candidate imports and ships `gguf-meta`, `model-autoconfig`, `model-files`.

Web live: healthy, 0 restarts; `/api/ready` `{"ready":true,"version":"f790069a"}` locally and on noevia.example.com; `/version.json` web `43a25dae` / core `5ba42d84`; `dav-parse.wasm` sha `a0388ae5...f1c3` (unchanged); effective `*_IMPL`/`NOEVIA_FEATURE_*`/`LAYA_LOAD_ADVISOR`/`COWORK_CODE_NET_ADDR` list (32 lines) identical before and after; 196 MCP tools across 3 servers; `codenet.guarding` on `172.28.0.3`, same as before; zero `impl_mismatch`, `wasm_fault`, `failing closed` or `unverified` lines over the first 10 minutes.

## Release ac500b45 — 2026-10-09 (retire five always-Rust security switches; web and core, #1071 batch 2; live)

## Release 5c92fb14 — 2026-10-09 (live-tester UI fixes, Diary files throttle pass-through, Laya autoconfig answer, estimate diagnostics; web and model manager; live)

**Evidence.** Before: autotune and calibration state files unchanged (2026-10-08 01:21 and 2026-09-23, phase `Done`), no bench or tune container, both sandboxes running only their supervisor/verifier at 0% CPU (read from `docker top`), llama idle, no task lines in the web log, no model load in progress. Loaded model `gemma-4-12b-it-qat-q4_0`, unchanged afterwards. Release tarball sha256 `206279f2...f138` identical on the Mac and the box. Candidate (`--network none`, read-only, caps dropped, tmpfs, synthetic): `/api/ready` 200, version `5c92fb14`.

Web live: healthy, 0 restarts; `/api/ready` `{"ready":true,"version":"5c92fb14"}` locally and on noevia.example.com; `/version.json` web `4bfb57d2` / core `3dc4b72b`; `dav-parse.wasm verified`; effective `*_IMPL`/`NOEVIA_FEATURE_*`/`LAYA_LOAD_ADVISOR`/`COWORK_CODE_NET_ADDR` list (30 lines) identical before and after; 196 MCP tools across 3 servers; `codenet.guarding` on `172.28.0.3`, same as before; zero `impl_mismatch`, `wasm_fault`, `failing closed` or `unverified` lines over the first 10 minutes.

## Release e58351d4 — 2026-10-09 (model manager: autoconfig spec, files, present and baseline behind MODEL_AUTOCONFIG, dark; deterministic current_diff order; model-manager only)

Source: noevia main `e58351d4a401fb935231375b65efd0ee947d3fe0` (#1176 CI green incl. Assembled release). Assembled on the Mac with `deploy/tools/assemble-release.sh e58351d` (web `4388a1cc`, core `5dbd7865`, services `37fedc12`); tarball sha256 `ca81ea79...28c3` identical on the Mac and the box. The services tarball (`7be05aea...5edd45`) and the noevia-rs one (`67bbe3fe...c43`) were each fetched twice and matched. The image was built from `releases/e58351d4/services/model-manager` (`current` still points at `d28ce1c`).

**Candidate checks (before cutover).** A throwaway container (`--network none`, read-only root, caps dropped, tmpfs for `/models`, `/config`, `/data`, `/tmp`, a synthetic token) with `MODEL_AUTOCONFIG=rust` came up healthy (health 200) with no error lines. In the same image, 400 seeded synthetic `analyze()` calls (spec profiles in 318, companion-file trees in 182, present sections in 203, baselines in 350) ran under `python` and `rust`: 387 identical (52 of them the same early refusal), 0 other differences, 0 Rust-only refusals; 13 inputs on which Python itself raises were skipped. The candidate was removed afterwards.

## Release 0815292 — 2026-10-09 (retire six always-Rust switches; web and core, #1071 batch 1; live)

## Release c72ee95 — 2026-10-09 (Diary storage 429/401/5xx handling; Diary only)

**Evidence.** Idle before cutover: autotune and calibration state files unchanged since 2026-10-08 01:21 and 2026-09-23, no bench or tune process, every container under 5% CPU, both sandboxes running only their supervisors (plus one defunct zombie) read from `/proc`, llama loaded `gemma-4-12b-it-qat-q4_0` at 0% CPU with no load in progress. Appdata backup `ab_20261009_025217` was taken and verified by the script; candidate imports ok, candidate `tenant-assertion self-test` ok, preflights passed. After: `cowork-diary-1` `cowork-diary:c72ee95`, healthy, restart count 0, started 2026-10-09 06:57:37 UTC; `tenant-assertion self-test` prints `ok` inside it; `TENANT_ASSERTION_IMPL` is unset in the container and not in `.env`; web to Diary health (`/api/health` with the Diary token, run inside web) 200; Diary cannot resolve `model-loader`. Web `printenv` of every `*_IMPL` (21 names, nine `wasm` switches added earlier today included) is identical before and after. Ten minutes after cutover (06:57:37 to 07:07:37 UTC) the Diary log held 29 requests, all `GET /api/health` 200, no traceback, no 5xx. No storage call happened in that window (3 a.m. local, no browser traffic), so the live 424 mapping and the cool-down were not observed on the running service; the two hours before cutover had 364 requests including 2 HTTP 500 tracebacks (storage 429), 12 HTTP 424, and 11 upstream "401/429 ... degrading to empty" warnings. Instead the deployed image ran `tests/test_storage_backoff.py`, `test_workspace_files.py`, `test_managed_storage.py` and `test_dedicated_storage.py` in a throwaway container (no network, read-only root, no data mounts, tests mounted read-only): 89 passed. No real Diary content, storage login or model was used.


## Flags enabled 2026-10-09 — nine more `*_IMPL` switches (config only; live web stays d28ce1c)

**Evidence.** Candidate first: a throwaway `cowork-web:d28ce1c` container with the live environment (private temp env-file, deleted and shredded afterwards) plus all nine `=wasm`, on a throwaway `--internal` network where the alias `egress` resolved to the candidate, read-only root, tmpfs for writable paths, no live data mounts. It started healthy with 0 restarts; the log showed `dav-parse.wasm verified for ...` listing all 18 wasm switches including the nine, `codenet.guarding` on the candidate's own address, no impl_mismatch, wasm_fault, failing closed, impl_refused, unverified, error or FATAL lines, and `/api/ready` 200. (MCP discovery for nextcloud and tavily failed there only because the network is isolated.) The candidate and network were removed. Idle check before the recreate: autotune and calibration `passed`/Done, code-sandbox and code-verify running only their supervisors (read from `/proc`), web, llama and sandboxes at 0% CPU, one model loaded and idle, no model load in progress, no Coding job running. Live after the recreate: healthy, restart count 0; `printenv` shows the nine `wasm` and every other flag unchanged (diffed before/after); the verified line lists all nine; `codenet.guarding` on `172.28.0.3`, the same address as before; the same 3 MCP servers and 196 tools (noevia 10, nextcloud 181, tavily 5); live wasm sha256 unchanged; `/api/ready` 200 on 127.0.0.1:8021 and https://noevia.example.com; zero `impl_mismatch|wasm_fault|failing closed|impl_refused|unverified` lines over a 10 minute soak (06:35 to 06:45 UTC). Not exercised live, by instruction (no chats, model runs or Code tasks): a Code task through review and the stage moves (`COMPLETENESS_REPORT_IMPL`, `TASK_LIFECYCLE_IMPL`), a preset save and the Will-it-fit panel (`LLAMACPP_AUTOCONFIG_IMPL`). The core differential suites are the evidence for those paths.

## Release d28ce1c — 2026-10-09 (live-tester fixes #1154-#1160; web and core)

### Behaviour change

`PUT /api/model-manager/sections/:name` with an invalid size (`code: invalid_size`) now answers HTTP 400; it was 409, which the client showed as "settings file changed". The budget refusal stays 409.

**Evidence.** Before the build and again before `up.sh`: autotune job `passed`, calibration job `passed` (files unchanged since 2026-10-08 01:21 and 2026-09-23), no bench or tune container, web, llama, code-sandbox and code-verify at about 0% CPU, and the two sandboxes running only their supervisors plus one defunct `pi` zombie from 2026-10-07 (read from `/proc`). Candidate image: `version.json` `{"version":"d28ce1c","web":"4388a1cc...","core":"5dbd7865..."}`, wasm sha256 `a0388ae5...f1c3` equal to `dav-parse.lock`. Live: `/api/ready` 200 `{"ready":true,"version":"d28ce1c"}` locally (127.0.0.1:8021) and through https://noevia.example.com; live wasm sha256 equals the lock and the previous release's; the web log shows `dav-parse.wasm verified` for the same switches as before; the 31 effective `*_IMPL`, `NOEVIA_FEATURE_*`, `COWORK_CODE_NET_ADDR`, `MODEL_AUTOCONFIG` and `GGUF_PARSER` values are identical before and after (`backups/web-flags-before-d28ce1c.txt` / `-after-`). `dist/index.html` sha256 prefix `da1dbb4945a3b6b2`, `dist/version.json` prefix `e81b598c4205f968`. Container healthy, 0 restarts. No model was loaded, run or tuned, no Code task or Diary access.

## Release fc6ecbbf — 2026-10-09 (Diary overlay with the Rust tenant-assertion binary, TENANT_ASSERTION_IMPL off; Diary only)

**Tag repair ([#1148](https://github.com/sbstndalton/noevia/issues/1148)).** Before the overlay, the running Diary was image `ab3981a11bad` (untagged) while `cowork-diary:f6885a55` pointed at `9036068bf5d8`, a from-scratch build made 2026-10-07 03:00 and never deployed (the overlay script correctly refused). Both tags were fixed locally with no image deleted: `9036068bf5d8` is now `cowork-diary:f6885a55-rebuilt-unused` and `cowork-diary:f6885a55` is `ab3981a11bad` again, which is what ran.

**Candidate checks and cutover.** Before: model-loader, llama and both sandboxes idle, no bench or tune container. The candidate imported, and `tenant-assertion self-test` printed `ok` in a `--network none` container before `.env` was touched. Preflights passed; only `diary` was recreated (`Healthy`), and the script's "diary health via web" returned 200.

**Verify.** `cowork-diary-1`: `cowork-diary:fc6ecbbf`, healthy, restart count 0, started 2026-10-09 04:57:32 UTC. `/usr/local/bin/tenant-assertion` present and `self-test` prints `ok` inside it. `TENANT_ASSERTION_IMPL` unset in the container and in `.env`. No Diary errors and no web-side Diary errors in the 10 minutes after cutover.

## Release e2b6d7cd — 2026-10-09 (model manager: autoconfig input prep and values behind MODEL_AUTOCONFIG, dark; model-manager only)

Source: noevia main `e2b6d7cd69734a91ea953f4aba8fad0b9c14f16a` (#1161 CI green incl. Assembled release). Assembled on the Mac with `deploy/tools/assemble-release.sh e2b6d7c` (web `f20e7f61`, core `92144747`, services `468a7b66`); tarball sha256 `862008e7...5573` identical on the Mac and the box. The services tarball (`8478ba38...47a53`) and the noevia-rs one (`01573244...6591`) were each fetched twice and matched. noevia-rs main CI was green on `b7788837` before the pin. The image was built from `releases/e2b6d7cd/services/model-manager` (`current` still points at `2237e0d6`).

**Candidate checks (before cutover).** A throwaway container (`--network none`, read-only root, caps dropped, tmpfs for `/models`, `/config`, `/data`, `/tmp`, a synthetic token) with `MODEL_AUTOCONFIG=rust` came up healthy with no error lines; the binary sha256 (`4c41fcb7...6fc6`) later matched the live container's. Synthetic checks inside it: 120 captured `check` requests (99 with values, the rest early refusals) from a seeded `analyze()` corpus, binary output equal to the Python reference for all 120; 60 seeded `analyze()` calls under `rust` and `python` were identical (0 refusals, 0 other differences). Removed afterwards.

**Cutover and verify.** Before: autotune and calibration jobs `passed`, no download, benchmark `idle`, no bench or tune container, llama, web and both sandboxes at about 0% CPU (sandboxes and llama read from `/proc`: supervisors and the idle server only). Loaded model: `gemma-4-12b-it-qat-q4_0`, unchanged afterwards. Model-loader only: `up.sh -- -d --no-build --no-deps --wait --wait-timeout 120 model-loader` (preflight passed, `Healthy`). Live: healthy, 0 restarts, `MODEL_AUTOCONFIG=python`, `GGUF_PARSER=rust`, `MODEL_FILES_IMPL=rust`, no error or warning lines in the log, web `/api/ready` 200. `GET /sections/<name>/autoconfig` for all 8 live sections at presets `fast` and `long-ctx` (16 answers) before and after: equal once the `current_diff` lines are sorted (their order differs between processes, [#1152](https://github.com/sbstndalton/noevia/issues/1152)); `laya_multilingual_f16` answers "No model file found" in both. `models.ini` sha256 unchanged. The before/after snapshots of the running containers differ only in `cowork-model-loader-1`. No model was run, loaded, tuned or downloaded.

## Release a917cf7f — 2026-10-09 (model manager: autoconfig size core behind MODEL_AUTOCONFIG, dark; model-manager only)

Source: noevia main `a917cf7fa43c7949de6e5379312b58fc80979a96` (#1141 CI green incl. Assembled release). Assembled on the Mac with `deploy/tools/assemble-release.sh a917cf7f` (web `f20e7f61`, core `92144747`, services `8fe8e9cc`); tarball sha256 `77074b4c...c9a4` identical on the Mac and the box. The services tarball checksum (`bec3ab14...67d6`) and the noevia-rs `cd80eb27` one (`e988192a...7782`) were each fetched twice and matched. noevia-rs main CI was green on `cd80eb27` before the pin. The image was built from `releases/a917cf7f/services/model-manager` (`current` still points at `2237e0d6`, which web runs).

**Candidate checks (before cutover).** `/usr/local/bin/model-autoconfig` present (sha256 `b8bc8cda...48b4`); a throwaway container (`--network none`, read-only root, caps dropped, tmpfs for `/models`, `/config`, `/data`, a synthetic token) with `MODEL_AUTOCONFIG=rust` started healthy with no errors. Five synthetic requests (dense and MoE, 8 to 48 GiB, 4.7 to 60 GiB files) through `autoconfig.analyze`: the binary was called each time, `analyze` under `rust` equalled `analyze` under `python` field for field, and the binary's plan equalled Python's plan exactly. Removed afterwards.

## Release 2237e0d6 — 2026-10-08 (llamacpp-autoconfig in Rust, LLAMACPP_AUTOCONFIG_IMPL dark; size-knob validation; core#37; web and core)

### Behaviour change (independent of the switch, [#1132](https://github.com/sbstndalton/noevia/issues/1132))

A preset whose `ctx-size` (or `c`), `ubatch-size` or `batch-size` is set but is not a whole number (Infinity, -1, a decimal such as 4096.5, and 0 for `ubatch-size` or `batch-size`) is now refused at save and at load (`code: invalid_size`). `ctx-size` 0 still means the model's native context, and a leading `+` is accepted. A non-finite footprint never passes the load gate. Autotune KV ceilings are planned with the JS footprint (#1133), and the `estimateInputs` comparison also requires equal `moe`, `chat`, `nativeCtx` and current ctx/kv (#1134).

**Evidence.** Before the build and again before `up.sh`: autotune job `passed`, calibration job `passed`, code-sandbox and code-verify running only their supervisors (read from `/proc`), all five stored jobs terminal (newest 2026-10-08 02:00, unchanged). Live: `/api/ready` 200 `{"ready":true,"version":"2237e0d6"}` locally and through https://noevia.example.com; `dav-parse.wasm` sha256 `a0388ae5...f1c3` equals `dav-parse.lock` and the noevia-rs `743be45c` CI line "dav-parse.wasm sha256"; `LLAMACPP_AUTOCONFIG_IMPL=js`. Container healthy, 0 restarts. `dist/index.html` sha256 prefix `0c828fe804afb644` (was `536934cc40f7e130`), `dist/version.json` prefix `81f983584b2b090a` (was `3075f0d35052be40`). No model was loaded at any point.

**Live preset check (read-only).** Every section of the live `models.ini` (8 sections) was run through the new `sizeKnobProblem` rule inside the web container, both as the section alone (save) and merged over `[*]` (load): 0 refused. A synthetic file confirmed the check catches Infinity, -1, 4096.5 and ubatch 0, and accepts ctx-size 0.

**Flip evidence (not enabled live).** A throwaway container from the same image (`--network none`, read-only, `--cap-drop ALL`, tmpfs data, no live mounts or secrets) with `LLAMACPP_AUTOCONFIG_IMPL=wasm` started, logged `dav-parse.wasm verified for LLAMACPP_AUTOCONFIG_IMPL`, and answered `/api/ready` 200 with its wasm equal to the lock sha; it was removed afterwards. Switching it on is the owner's call.

**CI note.** The first run of "Deploy tooling shell/wrapper tests" on #1135 failed fetching a Docker Hub OAuth token; a rerun passed with no change.

## Release 7c2842a5 — 2026-10-08 (task lifecycle in Rust, TASK_LIFECYCLE_IMPL dark; core#36; web and core)

**Evidence.** Before the build and again before `up.sh`: autotune job `passed`, calibration job `passed`, code-sandbox and code-verify running only their supervisors (checked by reading `/proc`, since the images have no `ps` and `docker top` is not reliable there), and all five stored jobs terminal. Live: `/api/ready` 200 `{"ready":true,"version":"7c2842a5"}` locally and through https://noevia.example.com; `dav-parse.wasm` sha256 `b7e76964...c132` equals `dav-parse.lock` and the noevia-rs `5f497542` CI line "dav-parse.wasm sha256"; the web log shows the same wasm-verified flag list as before. Container healthy, 0 restarts. `dist/index.html` sha256 prefix `536934cc40f7e130`, `dist/version.json` prefix `3075f0d35052be40`. The five stored job journals are byte-for-byte untouched (same mtimes) and fold to an empty lifecycle without refusal; none is a Code task with lifecycle events, so there was no live lifecycle state to compare.

**Flip evidence (not enabled live).** A throwaway container from the same image (`--network none`, read-only, tmpfs data, no live mounts or secrets) with `TASK_LIFECYCLE_IMPL=wasm` started, logged `dav-parse.wasm verified for TASK_LIFECYCLE_IMPL`, was healthy, and answered `/api/ready` 200 with its wasm equal to the lock sha. No real Code task, review or Diary access was run. Switching it on is the owner's call.

## Release e921406d — 2026-10-08 (completeness report in Rust, COMPLETENESS_REPORT_IMPL dark; core#35; web and core)

**Evidence.** Autotune job `passed`, calibration job `passed`, code-sandbox idle (supervisor only, checked before the build), checked again immediately before `up.sh` (the sandbox re-check errored in `docker top` and was not repeated). Live: `/api/ready` 200 `{"ready":true,"version":"e921406d"}` locally and through https://noevia.example.com; `dav-parse.wasm` sha256 `bbbf172b...4c96` equals `dav-parse.lock` and the noevia-rs `bba1a0eb` CI line "dav-parse.wasm sha256"; the web log shows the wasm-verified flag list as before. Container healthy, 0 restarts. `dist/index.html` sha256 prefix `09afffb016873ad8`, `dist/version.json` prefix `6d8bf03129821ba1`.

**Flip evidence (not enabled live).** A throwaway container from the same image (`--network none`, read-only, tmpfs data, no live mounts or secrets) with `COMPLETENESS_REPORT_IMPL=wasm` started, logged `dav-parse.wasm verified for COMPLETENESS_REPORT_IMPL`, and answered `/api/ready` 200 with its wasm equal to the lock sha. No real Code task, review or Diary access was run. Switching it on is the owner's call.

## Release 15538388 — 2026-10-08 (role-context projections in Rust, ROLE_CONTEXT_IMPL dark; core#34; web and core)

**Evidence.** Autotune job `passed`, calibration job `passed`, code-sandbox idle (supervisor only), llama idle, checked before the build and again immediately before `up.sh`. Live: `/api/ready` 200 `{"ready":true,"version":"15538388"}` locally and through https://noevia.example.com; `dav-parse.wasm` sha256 `02bfcf9d...ddd6` equals `dav-parse.lock` and the noevia-rs `aa5eca78` CI line "dav-parse.wasm sha256"; the web log shows the same wasm-verified flag list as before. Container healthy, 0 restarts. `dist/index.html` sha256 prefix `795af0759ba28eeb`, `dist/version.json` prefix `c7f393950690f83d`.

**Flip evidence (not enabled live).** A throwaway container from the same image (`--network none`, read-only, tmpfs data, no live mounts or secrets) with `ROLE_CONTEXT_IMPL=wasm` started, logged `dav-parse.wasm verified for ROLE_CONTEXT_IMPL`, and answered `/api/ready` 200 with its wasm equal to the lock sha. No real Code task, review or Diary access was run. Switching it on is the owner's call.

## Release 3ace1bf5 — 2026-10-08 (code-net-guard decisions in Rust, CODE_NET_GUARD_IMPL dark; core#33; web and core)

**Evidence.** Autotune job `passed`, calibration job `passed`, code-sandbox idle (supervisor only), checked before the build and again immediately before `up.sh`. Live: `/api/ready` 200 `{"ready":true,"version":"3ace1bf5"}` locally and through https://noevia.example.com; `dav-parse.wasm` sha256 `92c74917...41b9` equals `dav-parse.lock` and the noevia-rs `b74eeae7` CI line "dav-parse.wasm sha256"; startup log still has `codenet.guarding` for the same address (`172.28.0.3`) as before the release.

**Flip evidence (not enabled live).** A throwaway container from the same image with `CODE_NET_GUARD_IMPL=wasm` and the live `COWORK_CODE_NET_ADDR` value (`egress`, passed through, on a throwaway internal network where it carries that alias) started, logged `dav-parse.wasm verified for ... CODE_NET_GUARD_IMPL`, logged `codenet.guarding` for its own address and answered `/api/ready` 200. A first attempt on the live `cowork_code` network exited 1 with `EADDRNOTAVAIL` because `egress` resolved to the live web's address, which the candidate cannot bind: a test-harness artifact, not the port. Switching it on is the owner's call.

## Release 0020d687 — 2026-10-08 (mcp-servers and decision checks in Rust, MCP_SERVERS_IMPL and DECISION_IMPL dark; core#32; web and core)

**Evidence.** Autotune job `passed`/Done, calibration idle, code-sandbox idle and llama idle (no log lines in 15 minutes), checked before the build and again immediately before `up.sh`. Synthetic candidate (`--network none`, read-only): `/api/ready` 200, `dav-parse.wasm` verified for `MCP_SERVERS_IMPL, DECISION_IMPL`, an `xn--` host fails closed (`ambiguous`). Live: `dav-parse.wasm` sha256 `862e144e...3466` equals `dav-parse.lock` and the noevia-rs `f0126c58` CI line "dav-parse.wasm sha256"; `/api/ready` 200 `{"ready":true,"version":"0020d687"}` locally and through https://noevia.example.com; web healthy, restart count 0.

## Flags enabled 2026-10-08 — S3_SIGN_IMPL, PROMPT_FRAMING_IMPL, SSRF_IMPL (config only; live web stays 82d0da73)

**Evidence.** Before every recreate: autotune job `passed`/Done, calibration done, web, llama and code-sandbox at about 0% CPU. Per flag, after the recreate: healthy, 0 restarts, the startup line `dav-parse.wasm verified for ...` lists the new flag (final line: `DAV_PARSE_IMPL, S3_PARSE_IMPL, UPLOAD_SNIFF_IMPL, MCP_FRAME_IMPL, AUTOTUNE_PLAN_IMPL, PRESET_RELOAD_IMPL, PROMPT_FRAMING_IMPL, S3_SIGN_IMPL, SSRF_IMPL`), no FATAL, `printenv` shows `wasm`, `/api/ready` 200 on 127.0.0.1:8021 and on noevia.example.com, MCP 196 tools across 3 servers (noevia 10, nextcloud 181, tavily 5), and a log with no `DavParseError`, no `could not be signed/checked/read/opened` and no SSRF refusal over a 2 minute soak (130 s or more each). Before `SSRF_IMPL`, every configured outbound host was listed (env `MCP_SERVERS`, `MCP_SERVER_URL`, `WEBDAV_BASE_URL`, `MCP_NEXTCLOUD_ORIGINS`, `COWORK_DECISION_URL`, provider, OCR, Docling, embedding and model-loader URLs, plus the stored storage connection and settings rows): all ASCII, none `xn--`, none with a trailing dot, none `metadata.google.internal`. Tavily connecting over public-fetch is the live proof of the wasm URL check. Not exercised live, by instruction (no chats, no model runs): a real chat turn with tool or web text for `PROMPT_FRAMING_IMPL`, and a signed S3 request (no S3 backend or S3 offsite target is configured, so `S3_SIGN_IMPL` is differential-only). The differential suites from `docs/deployment.md` and the verification note (`s3-sign-differential` 3/3, `prompt-framing-differential` 9/9, `ssrf-differential` 12/12) are the evidence for those paths.

## Release 82d0da73 — 2026-10-08 (stream-guard validator in Rust, STREAM_GUARD_IMPL dark; core#29; web and core)

**Evidence.** Autotune job `passed`/Done and code-sandbox idle (no processes, no llama requests in 10 minutes), checked before the build and again immediately before `up.sh`. Release tarball sha256 `f4aeda06...b821` identical on the Mac and the server. Synthetic candidates (`--network none`, read-only): `STREAM_GUARD_IMPL=js`, and the live flag set; no FATAL, `/api/ready` 200, `dav-parse.wasm` sha256 `ef088449...b819`, 30 exports including `stream_guard`, zero imports. Live after: healthy, 0 restarts, `/api/ready` 200 locally and on noevia.example.com, the startup line verifies the six web wasm flags (DAV_PARSE, S3_PARSE, UPLOAD_SNIFF, MCP_FRAME, AUTOTUNE_PLAN, PRESET_RELOAD), MCP 196 tools across 3 servers, no error lines, `STREAM_GUARD_IMPL` empty in the container.

## Release c4ade220 — 2026-10-08 (SSRF decisions in Rust, SSRF_IMPL dark; core#28; web and core)

**Evidence.** Autotune job `passed`/Done, code-sandbox idle, checked before the build and again immediately before `up.sh`. Release tarball sha256 `57bac3ab...24a0` identical on the Mac and the server. Two synthetic candidates (`--network none`, read-only): with the live flags, and with `SSRF_IMPL=wasm` added. Both: no FATAL, `/api/ready` 200, `dav-parse.wasm` sha256 `59a7d441...5b7b`, exports include `ssrf_policy`, zero imports. Live after: healthy, 0 restarts, `/api/ready` 200 locally and on noevia.example.com, the startup line verifies the six web wasm flags (DAV_PARSE, S3_PARSE, UPLOAD_SNIFF, MCP_FRAME, AUTOTUNE_PLAN, PRESET_RELOAD), MCP 196 tools across 3 servers (Tavily connected through public-fetch), `SSRF_IMPL` empty in the container.

## Release 20930e20 — 2026-10-08 (S3 SigV4 signing in Rust, S3_SIGN_IMPL dark; core#27; web and core)

**Evidence.** Autotune job `passed`/Done, code-sandbox idle (no processes beyond its supervisor, no log lines), checked before the build and again immediately before `up.sh`. Release tarball sha256 `3023cf3f...4284` identical on the Mac and the server. Synthetic candidate (`--network none`, read-only) with `S3_SIGN_IMPL=wasm`: no FATAL, verified line listed `S3_SIGN_IMPL`, `/api/ready` 200, `dav-parse.wasm` `c0f2287b...`, zero imports, exports include `s3_sign` and `s3_region`. Live: `cowork-web-1` healthy, 0 restarts, `/api/ready` 200 on 127.0.0.1:8021 and noevia.example.com, module verified line lists the six web wasm flags (`S3_SIGN_IMPL` not among them), MCP 196 tools across 3 servers, zero error markers in the log. No model run.

## Release 866f3db6 — 2026-10-08 (low/high context profiles, Long tune profile; core#24 web#15; #1079; web and core)

**Evidence.** Autotune job `passed`/Done (file untouched since 01:21), calibration finished, code-sandbox idle, llama silent, no task lines in the web log, no `*-long` section in `models.ini`, before the build and again immediately before `up.sh`. Release tarball sha256 `5d2b47ca...d481` identical on the Mac and the server. Candidate (`--network none`, read-only, synthetic data dir, six wasm flags on): no FATAL, `/api/ready` 200, `dav-parse.wasm` sha `7beab356...e609` equal to `DAV_PARSE_WASM_SHA256` in the pinned core lock, 26 exports (live 3e1e36df had 25) including `long_profile`. Live: healthy, 0 restarts; `/api/ready` 200 locally and on noevia.example.com; the module line lists `DAV_PARSE_IMPL, S3_PARSE_IMPL, UPLOAD_SNIFF_IMPL, MCP_FRAME_IMPL, AUTOTUNE_PLAN_IMPL, PRESET_RELOAD_IMPL`; 196 MCP tools across 3 servers; logs clean. `models.ini` byte-identical (sha `41da90dd...5d34`; a section is only added when a Long tune runs, none was run). `index.html` sha `49329a62...12ca` -> `f6ba2f41...1228`.

## Release 3e1e36df — 2026-10-08 (prompt-framing Rust slice dark, Laya served-elsewhere hardening, card size fallback; core#25 core#26 web#16; web and core)

**Evidence.** Autotune job `passed`/Done (file untouched since 01:21), calibration finished, code-sandbox and code-verify idle, llama silent, no task lines in the web log, before the build and again immediately before `up.sh`. Release tarball sha256 `39c7f2bb...a0b1` identical on the Mac and the server. Candidate (`--network none`, read-only, synthetic, run twice: flag empty and, candidate only, `PROMPT_FRAMING_IMPL=wasm`): no FATAL, `/api/ready` 200, `dav-parse.wasm` sha `bffb7c82...87da` equal to `DAV_PARSE_WASM_SHA256` in the pinned core lock, no imports, exports include `frame_untrusted`, `provenance` and `task_packet`; the wasm run passed the startup check including the `ẞ` hostname probe. Live: healthy, 0 restarts; `/api/ready` 200 locally and on noevia.example.com; the module line lists `DAV_PARSE_IMPL, S3_PARSE_IMPL, UPLOAD_SNIFF_IMPL, MCP_FRAME_IMPL, AUTOTUNE_PLAN_IMPL, PRESET_RELOAD_IMPL`; 196 MCP tools; logs clean. `index.html` sha `8f81783e...60ff` -> `49329a62...12ca`.

## Release 673768f5 — 2026-10-08 (Models page size/shape from the loader, Laya "Runs in its own service"; #1084, part of #1083; web and core)

**Evidence.** Autotune job `passed`/Done (file untouched since 01:21), calibration finished, code-sandbox idle, no task lines in the web log, before the build and again immediately before `up.sh`. Release tarball sha256 `b8e8e0eb...0f4a` identical on the Mac and the server. Candidate (`--network none`, read-only, synthetic): no FATAL, `/api/ready` 200, `dav-parse.wasm` verified (sha `ea7694f7...fbf7` in both the old and new image). Live: healthy, 0 restarts; `/api/ready` 200 locally and on noevia.example.com; the module line lists `DAV_PARSE_IMPL, S3_PARSE_IMPL, UPLOAD_SNIFF_IMPL, MCP_FRAME_IMPL, AUTOTUNE_PLAN_IMPL, PRESET_RELOAD_IMPL`; 196 MCP tools (noevia 10, nextcloud 181, tavily 5), Tavily connected this time; logs clean. `index.html` sha `8946de12...fcbb5` -> `8f81783e...a60ff`.

## Rust toggles, batch A — 2026-10-08 (config only, no release; #1071 groundwork)

Owner standing order 2026-10-08: enable the Rust switches proven in `rust-toggle-verification.md`, remove the old code later.

**Evidence.** Before: autotune and calibration jobs `passed`, no coding task, sandboxes idle, no model-loader download. Web: healthy, 0 restarts; the startup line `dav-parse.wasm verified for DAV_PARSE_IMPL, S3_PARSE_IMPL, UPLOAD_SNIFF_IMPL, MCP_FRAME_IMPL, ...`; no FATAL; `/api/ready` 200 locally and on noevia.example.com; each flag reads `wasm` in the container. MCP discovery on real servers under `MCP_FRAME_IMPL=wasm`: noevia 10 and Nextcloud 181 tools; Tavily logged one `fetch failed` at startup (outbound-only, as on a previous first start) while a direct list from the container gave 5 tools under both `wasm` and `js`, so the full set is 196. Model-loader: healthy, 0 restarts, `GGUF_PARSER=rust`, `/api/v1/health`, `/models` and `/sections` 200, no `gguf-meta failed` or error lines, `gguf-meta` returns a summary for a real model header, `models.ini` sha256 identical before and after. No model was run, loaded or tuned. A real storage listing, upload and a tool call need a signed-in session and were not exercised (differential-only so far; `S3_PARSE_IMPL` has no S3 backend to observe).

## Release 8273a712 — 2026-10-08 (route fallback cause, Laya keeps its worker and stays warm #1070; core, web, Laya)

**Evidence.** Autotune job `failed` (finished 2026-10-07 13:10), calibration `passed`, no preset reload pending, code-sandbox, code-verify and llama idle, before the build and again before `up.sh`. Release tarball sha256 `63c5f2da...23cd` identical on the Mac and the server. Web candidate (`--network none`, read-only, synthetic): no FATAL, `/api/ready` 200, `dav-parse.wasm verified`; the live asset hashes after cutover equal the candidate's. Laya candidate: the model load is needed for `/health`, so none was run; the new image ran `test_server.py` in a throwaway container (`--network none`, read-only, no model): 30 tests OK. Live after: web healthy, 0 restarts, `/api/ready` 200 locally and on `noevia.example.com` reporting `8273a712`, `version.json` web `91b3369c` / core `75e27122`, MCP 196 tools across 3 servers, no error lines in the web log. Laya healthy, 0 restarts, `/health` `{"ready": true}` from inside web (`http://laya:8040`). The Laya log shows neither a keep-warm note nor the "found no model tensors" warning (that warning is the only keep-warm log line, so its absence means tensors are being touched). Laya memory: 1.507 GiB before, 2.118 GiB right after start (limit 6 GiB); the extra is weights that were previously swapped out and are now kept resident.

## Release 9035443e — 2026-10-08 (autotune waits for outside clients, coding tasks hold the inference gate #1062 #1067 #1068 #1069; core)

**Evidence.** The autotune job state was `failed` (finished 2026-10-07 13:10), calibration `passed`, no preset reload pending, and the code-sandbox and engine were idle, both before the build and again immediately before `up.sh`. Release tarball sha256 `60a16515...a934` identical on the Mac and the server. Candidate (`--network none`, read-only, synthetic): no FATAL, `/api/ready` 200, `dav-parse.wasm` sha `ea7694f7...fbf7`, log line `dav-parse.wasm verified for AUTOTUNE_PLAN_IMPL, PRESET_RELOAD_IMPL`. Live after: `cowork-web-1` healthy, 0 restarts, `/api/ready` 200 locally and on `noevia.example.com` reporting `9035443e`, `version.json` web `ec8ec1c0` / core `aa15e0c9`, live `dav-parse.wasm` sha `ea7694f7...fbf7` (was `33a4c692...5333`), MCP 196 tools across 3 servers, no error lines in the log.

## Release 2b5c122f — 2026-10-07 (autotune KV policy #1057-#1061; web and core)

**Evidence.** No autotune or calibration job was running before the build or immediately before `up.sh`. Candidate (`--network none`, read-only, synthetic): no FATAL, `/api/ready` 200, `dav-parse.wasm` sha equals `DAV_PARSE_WASM_SHA256` (`33a4c692...5333`). Live: healthy, 0 restarts, `/api/ready` 200 locally and on noevia.example.com, the web log shows dav-parse.wasm verified for AUTOTUNE_PLAN_IMPL and PRESET_RELOAD_IMPL, MCP 196 tools across 3 servers. In the container `kvCandidates()` returns `bf16,q8_0` (`bf16,q8_0,q5_1,q5_0` with the q5 switch). The authenticated autotune status API was not queried (needs a session). No model run, reload or tune.

## Flags enabled — 2026-10-07 (owner approved; configuration only, no image change)

**What each flag does.** `AUTOTUNE_PLAN_IMPL=wasm`: the Rust planner orders autotune runs. `LAYA_LOAD_ADVISOR=on`: Laya advises on a guessed load failure only on a tie. `PRESET_RELOAD_IMPL=wasm`: a models.ini reload can go ahead while models are loaded. `MODEL_FILES_IMPL=rust`: Hugging Face tree listings go through `model-files tree` and fail closed (502) on bad input. None of these runs until the matching action (autotune, load failure, reload, repository listing) happens; nothing was triggered.

## Release f33a1b68 — 2026-10-07 (Library tab apply note #1036; web)

Source: noevia main `f33a1b68922a529be585e29bf47405c8d64c24ca` (#1054 CI green incl. Assembled release). Assembled from a clean clone with `deploy/tools/assemble-release.sh f33a1b68` (web `a3c1cb3e`, core `e58063bf`, services `8f7eefa2`); tarball sha256 `1c9f816b...c63` identical on the Mac and the box. The image build passed its tests (1042 pass, 0 fail).

**Candidate checks (before cutover).** A `--network none`, read-only, caps-dropped candidate with synthetic env and tmpfs state booted, `/api/ready` 200, no FATAL. `dav-parse.wasm` is unchanged (`29c2be61...`, equal to `DAV_PARSE_WASM_SHA256`). Asset check: `index.html` `2b696ac7...` to `64a8b0de...`. The candidate was removed.

**After cutover.** `cowork-web-1` healthy with 0 restarts, `/api/ready` 200 locally and at `noevia.example.com`, MCP `196 tools across 3 server(s)`, zero error markers in the web log, `version.json` lists web `a3c1cb3e` and core `e58063bf`. No model was run, no Laya call made, no reload.

## Release 247d4c1a — 2026-10-07 (autotune engine-failure text replaced by fixed sentences #1049; web)

Source: noevia main `247d4c1af18f2da0d4e25c1a30aa6b900dc2e7e9` (#1052 CI green incl. Assembled release; core#19 merged). Assembled from a clean clone with `deploy/tools/assemble-release.sh 247d4c1a` (web `0e0bc5a4`, core `e58063bf`, services `8f7eefa2`); tarball sha256 `7e0c798c...d6f` identical on the Mac and the box.

**Candidate checks (before cutover).** A `--network none`, read-only, caps-dropped candidate with synthetic env and tmpfs state booted, `/api/ready` 200, no FATAL. `dav-parse.wasm` is unchanged (`29c2be61...`, equal to `DAV_PARSE_WASM_SHA256`). The candidate was removed.

**After cutover.** `cowork-web-1` healthy with 0 restarts, `/api/ready` 200 locally and at `noevia.example.com`, MCP `196 tools across 3 server(s)` (10 + 181 + 5), zero error markers in the web log, `version.json` lists web `0e0bc5a4` and core `e58063bf`. No model was run, no Laya call made, no autotune run.

## Release 94599ba8 — 2026-10-07 (Laya load advisor #1004, dark; #1046 #1047 #1048; web)

Source: noevia main `94599ba84770fcce9863b659cbbfcde5e5e5bc02` (#1050 CI green incl. Assembled release; core#18 checks green). Assembled from a clean clone with `deploy/tools/assemble-release.sh 94599ba8` (web `0e0bc5a4`, core `88e70695`, services `8f7eefa2`); tarball sha256 `26b316f9...ff0b` identical on the Mac and the box.

**Candidate checks (before cutover).** A `--network none`, read-only, caps-dropped candidate with synthetic env and tmpfs state booted healthy, `/api/ready` 200, no FATAL. `dav-parse.wasm` hashes to `29c2be61...77d0`, equal to `DAV_PARSE_WASM_SHA256`, and its exports include `load_verdict` (also `autotune_plan`). The candidate was removed. Asset check: `index.html` `61c71cba...` (old) to `564b8d1b...` (new); `dav-parse.wasm` `1fe3fb07...` to `29c2be61...`.

**After cutover.** `cowork-web-1` healthy with 0 restarts, `/api/ready` 200 locally and at `noevia.example.com`, MCP `196 tools across 3 server(s)`, no FATAL/error in the web log, `version.json` lists web `0e0bc5a4` and core `88e70695`. No model was run, no Laya call made, no autotune run.

## Release f48b9666 — 2026-10-07 (models.ini reload while models are loaded #1012, sleeping counts as loaded; web)

Source: noevia main `f48b9666ffae73a5b5b35230ce19d239c79b10e9` (#1044 CI green incl. Assembled release). Assembled from a clean clone with `deploy/tools/assemble-release.sh f48b9666` (web `0e0bc5a4`, core `c5356ecd`, services `8f7eefa2`); tarball sha256 `b5c60754...5e6` identical on the Mac and the box. The core tarball checksum (`c106ae10...9929`) was fetched twice and matched.

**Candidate checks (before cutover).** A `--network none`, read-only, caps-dropped candidate with synthetic env and tmpfs state booted healthy, `/api/ready` 200, no FATAL in its logs. `dav-parse.wasm` hashes to `1fe3fb07...f9d`, equal to `DAV_PARSE_WASM_SHA256` in the image's `dav-parse.lock`, and its exports include `preset_reload`. The candidate was removed.

**After cutover.** `cowork-web-1` healthy with 0 restarts, `/api/ready` 200 locally and at `noevia.example.com`, MCP `196 tools across 3 server(s)`, zero error markers in the web log, `version.json` lists web `0e0bc5a4` and core `c5356ecd`. No `native-preset-reload-*.json` state file exists in the data dir (flag off). No model was run and no reload was triggered.

## Release 21c6cb3d — 2026-10-07 (core sandbox bridge toolCallFor #1000, web test-hang fix #1033, QA scripts #1030; web, code sandbox)

Source: noevia main `21c6cb3df0c768bd2d1b9e7e0f3033840edef742` (#1041 CI green incl. Assembled release, 2m2s). Assembled from a clean clone with `deploy/tools/assemble-release.sh 21c6cb3d` (web `0e0bc5a4`, core `d5a45ac7`, services `8f7eefa2`); tarball sha256 `5bb15380...7525` identical on the Mac and the box. The web (`a90858a6...7fb83`) and core (`84387ff5...39207`) tarball checksums were each fetched twice and matched.

**Build note.** On-box `build-web-release.sh` finished in 24 s end to end (8 cached steps, so dependency layers were reused; the test-and-build step took 15.2 s, tests alone about 13 s: 1042 tests, 1040 pass, 0 fail, 0 cancelled, with `--test-timeout=120000`), with no hang. Stamped `21c6cb3d` (`version.json` lists web `0e0bc5a4`, core `d5a45ac7`). One build is not proof the hang is gone, but the first on-box attempts for `8a8a7e83` and `f505f1bb` both hung in this stage and this one did not.

**Candidate checks (before cutover).** Web: a `--network none`, read-only candidate with synthetic env and tmpfs state returned `/api/ready` 200 `{"ready":true,"version":"21c6cb3d"}` with no FATAL in its logs; removed. Code sandbox: `/srv/wasm/sandbox-bridge.wasm` in the image hashes to `3a86e87a...9451`, equal to `SANDBOX_BRIDGE_WASM_SHA256` in core `code-sandbox/sandbox-bridge.lock`; pi reports 0.87.0; a `--network none`, read-only, caps-dropped, uid 1000 candidate started the supervisor and listened on 8030. A second throwaway candidate with `SANDBOX_BRIDGE_IMPL=rust` logged `sandbox-bridge.wasm loaded` (not set on the live container). Both were removed.

**Backups.** `config/.env.bak.before-21c6cb3d.<timestamp>` and `config/.env.bak.before-sandbox-21c6cb3d` (values never printed), `state/web/cowork.db.bak.before-21c6cb3d` (SQLite `.backup`, integrity ok), `backups/web-state-before-21c6cb3d-20261007072406.tgz`, `backups/current-pointer-before-21c6cb3d.txt`, `backups/web-old-image-before-21c6cb3d.txt`, `backups/code-old-image-before-21c6cb3d.txt`, `backups/old-assets-before-21c6cb3d.txt`, Compose Manager `docker-compose.yml.bak.before-21c6cb3d` and `docker-compose.override.yml.bak.before-21c6cb3d`, and container snapshots `releases/snapinspect-{before,after-web,after}-21c6cb3d.txt`.

**Cutover and verify.** Web first (`current` repointed, `COWORK_VERSION=21c6cb3d`), then `CODE_SANDBOX_VERSION=pi-0.87.0-21c6cb3d` with `up.sh --env-file ... --profile code -- -d --no-build --no-deps --wait --wait-timeout 120 code-sandbox code-verify`. Preflight passed each time. Live: web healthy, web/code-sandbox/code-verify 0 restarts; code-verify `net=none`, read-only; `/api/ready` 200 locally and through noevia.example.com with version `21c6cb3d`; MCP `196 tools across 3 server(s)`; served bundle `index-Bjmg-sH3.js` / `index-C2MwDKyg.css` (14 JS/CSS files changed hash against `228e2ae4`; old and new lists in `backups/`); sandbox, verify and web logs show no error markers; `sandbox-bridge.wasm` in the running sandbox hashes to `3a86e87a...`. Container snapshot diff: only `cowork-web-1`, `cowork-code-sandbox-1` and `cowork-code-verify-1` changed; every other container (llama, embed, diary, docling, ocr, model-loader, laya, Nextcloud, the media stack) kept its id and start time. No real tune, model run or Diary access was done.

## Release 228e2ae4 — 2026-10-07 (core autotune planner #1003 + models.ini backup retention #1021, web, model manager, OCR)

Source: noevia main `228e2ae422604b04ec560f5b55aaeb78472f9708` (#1034 CI green incl. Assembled release; main CI green). Assembled from a clean clone with `deploy/tools/assemble-release.sh 228e2ae4` (web `ef4a0339`, core `d4b8e4be`, services `8f7eefa2`); tarball sha256 `8ac1dfb6...6630` identical on the Mac and the box. The core (`1a50442d...571e`) and services (`97dd115b...faa2`) tarball checksums were each fetched twice and matched. The web image build passed first time (no test hang).

**Candidate checks (before cutover).** Web: `cowork-web:228e2ae4` stamped `228e2ae4` (`version.json` lists web `ef4a0339`, core `d4b8e4be`); `dav-parse.wasm` sha256 `73b47ada...a6b` equals `DAV_PARSE_WASM_SHA256` in `core/server/dav-parse.lock`, no imports, exports include `autotune_plan`; a candidate container (`--network none`, read-only root, caps dropped, tmpfs state, synthetic empty state) was healthy with no FATAL and `/api/ready` 200. Model manager: `/usr/local/bin/model-files` present, `model-files backups` answered a synthetic request (the first case of `model-backups.v1.json`) with exit 0 and the expected `rotating`/`revision`/empty `prune`; a `--network none` read-only candidate started cleanly; `MODEL_FILES_IMPL` and `GGUF_PARSER` not set in the image. OCR: `docx-text` present, candidate healthy. All candidates were removed.

**Backups.** `config/.env.bak.<timestamp>-before-228e2ae4` (mode 600, values never printed), `backups/cowork-db-before-228e2ae4.sqlite` (SQLite `.backup`, integrity ok), `backups/web-state-before-228e2ae4-<timestamp>.tgz`, `backups/current-pointer-before-228e2ae4.txt`, `backups/versions-before-228e2ae4.txt` (old tags and image ids), `backups/web-old-image-before-228e2ae4.txt`, `backups/old-assets-before-228e2ae4.txt`, `backups/models.ini.before-228e2ae4` with `models-ini-sha-before-228e2ae4.txt` and the `llamacpp-config` directory listing and name list, the Compose Manager `docker-compose.yml.bak.before-228e2ae4` and `docker-compose.override.yml.bak.before-228e2ae4`, and container snapshots `releases/snapinspect-before-228e2ae4.txt` and `snapinspect-after-228e2ae4.txt`.

## Release f505f1bb — 2026-10-07 (web: Back history on /models, single Tools and auto-tune entries, #1024 #1025)

Source: noevia main `f505f1bbe58233c9f270e722da4208dc694af81b` (CI green on #1031, including Assembled release; web main CI green at `ef4a0339`). Assembled from a clean clone with `deploy/tools/assemble-release.sh f505f1bb` (web `ef4a0339`, core `894e0528`, services `6a535513`); tarball sha256 `ec963cd5...4b16` identical on the Mac and the box. The pinned web tarball checksum (`e91b0f0d...8ee13`) was fetched twice and matched.

**Build note.** The first on-box `build-web-release.sh` run hung in the in-image test stage (idle CPU, no progress for 20 minutes), the same pattern as `8a8a7e83` attempt 1. It was killed (log kept as `build-f505f1bb.attempt1-hung.log`) and the second run passed with no source change, stamped `f505f1bb`.

**Candidate checks (before cutover).** Image `cowork-web:f505f1bb` (`sha256:f2148635...0970`) stamped `f505f1bb` (`version.json` lists web `ef4a0339`, core `894e0528`). A candidate container (`--network none`, read-only root, caps dropped, tmpfs state, synthetic empty state) was healthy with no FATAL, `/api/ready` 200, and logged `CHAT_TEMPLATE_CAPS_IMPL=wasm`. It was removed afterwards.

**Backups.** `config/.env.bak.20261007061455` (values never printed), `backups/cowork-db-before-f505f1bb.sqlite` (SQLite `.backup`, integrity ok), `backups/web-state-before-f505f1bb-20261007061455.tgz`, `backups/current-pointer-before-f505f1bb.txt`, `backups/web-old-image-before-f505f1bb.txt`, `backups/old-assets-before-f505f1bb.txt`, `backups/compose-before-f505f1bb.yml`, `backups/compose-override-before-f505f1bb.yml`, and the Compose Manager `docker-compose.yml.bak.before-f505f1bb` and `docker-compose.override.yml.bak.before-f505f1bb`. Non-web container snapshots: `snapshot.before-f505f1bb.txt` and `snapshot.after-f505f1bb.txt`.

**Cutover and verify.** `current` repointed, `COWORK_VERSION=f505f1bb`, guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 120 web` (preflight passed, `Healthy`). Live: `cowork-web:f505f1bb` healthy, 0 restarts; `/api/ready` 200 locally and through noevia.example.com; `/version.json` `{"version":"f505f1bb","web":"ef4a0339...","core":"894e0528..."}`; served JS, CSS and manifest assets 200 (`index.html` sha256 `29623c6a...d3d8`, 70 files under `dist/assets`); MCP unchanged at 196 tools across 3 servers; logs show no errors. Only `cowork-web-1` changed identity and start time; every other container's image id, start time and restart count matches the before snapshot. No UI click test was part of this release.

## Release e2209540 — 2026-10-07 (web: models/routing and picker redesign, #1006 #1007 #1008 #1009 #1013)

Source: noevia main `e2209540b5c96add66d46c553234ebc62d8d7a25` (CI green on #1022, including Assembled release). Assembled with `deploy/tools/assemble-release.sh e2209540` (web `66e0e11e`, core `894e0528`, services `6a535513`); tarball sha256 `a6935bea...0d09` identical on the Mac and the box. The pinned web and core tarball checksums were each fetched twice and matched.

**Candidate checks (before cutover).** Image `cowork-web:e2209540` stamped `e2209540` (`version.json` lists web `66e0e11e`, core `894e0528`). A candidate container (`--network none`, read-only root, tmpfs, synthetic empty state) was healthy with no FATAL, `/api/ready` 200, and logged `CHAT_TEMPLATE_CAPS_IMPL=wasm`. It was removed afterwards.

**Backups.** `config/.env.bak.20261007054617` (values never printed), `backups/cowork-db-before-e2209540.sqlite` (SQLite `.backup`, integrity ok), `backups/web-state-before-e2209540-20261007054617.tgz`, `backups/current-pointer-before-e2209540.txt`, `backups/compose-before-e2209540.yml`, `backups/compose-override-before-e2209540.yml`, and the Compose Manager `docker-compose.yml.bak.before-e2209540` and `docker-compose.override.yml.bak.before-e2209540`. Non-web container snapshots: `snapshot.before-e2209540.txt` and `snapshot.after-e2209540.txt`.

**Cutover and verify.** `current` repointed, `COWORK_VERSION=e2209540`, guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 120 web` (preflight passed, `Healthy`). Live: `cowork-web:e2209540` healthy, 0 restarts; `/api/ready` 200 locally and through noevia.example.com; `/version.json` as above; JS, CSS and manifest assets 200; MCP unchanged at 196 tools across 3 servers; logs show no errors. Only `cowork-web-1` changed identity and start time; every other container's image id, start time and restart count matches the before snapshot. The existing user's `projects.json` (334 projects, none with the new `routingMode`/`toolsMode` fields) parses and the log has no toolsMode/routingMode errors; the fields are optional and only written on a patch. No UI click test was part of this release.

## Release b34055c6 — 2026-10-07 (web: chat-template capability check, `CHAT_TEMPLATE_CAPS_IMPL`, #1002; real provider error reasons)

Source: noevia main `b34055c65b0bde7977f30429664786eb2de5d1bf` (CI green, including Assembled release). Assembled with `deploy/tools/assemble-release.sh b34055c6` (web `5b2c1838`, core `c78e3789`, services `6a535513`); tarball sha256 `2533be7f...c404d6` identical on the Mac and the box.

**Candidate checks (before cutover).** Image `cowork-web:b34055c6` stamped `b34055c6`; `dav-parse.wasm` sha256 `4c2b86d2...9410` equals `DAV_PARSE_WASM_SHA256` in `dav-parse.lock`; no imports; exports include `template_caps`, `provider_error` and `serving_verdict`. A candidate container (`--network none`, read-only root, tmpfs state, caps dropped) started with no FATAL and logged `[chat-template-caps] CHAT_TEMPLATE_CAPS_IMPL=wasm`. The image build passed first time (no test hang).

**Backups.** `config/.env.bak.20261007045232` (values never printed), `backups/cowork.db.before-b34055c6-20261007045232` (SQLite `.backup`, integrity ok), `backups/web-state-before-b34055c6-20261007045232.tgz`, `current.prev-8a8a7e83.txt`, and the Compose Manager `docker-compose.yml.bak.before-b34055c6` and `docker-compose.override.yml.bak.before-b34055c6`.

**Cutover and verify.** `current` repointed, `COWORK_VERSION=b34055c6`, guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 120 web` (preflight passed, `Healthy`). Live: `cowork-web:b34055c6` healthy, 0 restarts; `/api/ready` 200 locally and through noevia.example.com; `/version.json` `{"version":"b34055c6","web":"5b2c1838...","core":"c78e3789..."}`; assets 200; log shows `CHAT_TEMPLATE_CAPS_IMPL=wasm` and no FATAL; MCP 196 tools across 3 servers, unchanged. Container id, image and start time of every other container are identical before and after (`snapshot.before-b34055c6.txt`, `snapshot.after-b34055c6.txt` on the box); only `cowork-web-1` was recreated.

**Gemma 4 template check (no model loaded, no chat sent).** `/props?model=gemma-4-12b-it-qat-q4_0&autoload=false` answers 400 "model is not loaded" while the model is unloaded (the router has no template to return without loading it), so the template was read from the GGUF header instead: 18,681 bytes present, wasm `templateCaps` gives `known: true`, `tools: true`, `toolCalls: true`, `sendTools: true`. Chat will send tools to it.

## Release 8a8a7e83 — 2026-10-07 (web, plus code-verify recreate: MCP response framing in Rust/WASM behind dark `MCP_FRAME_IMPL`, #980; exact upload classify under `UPLOAD_SNIFF_IMPL=wasm`, #989)

Source: noevia main `8a8a7e83952f5cf405e9a90ca191803e3e5e52f7` (CI green on #1010 and on main, including Assembled release). Assembled with `deploy/tools/assemble-release.sh 8a8a7e83` (web `c80a3668`, core `57d7718a`, services `6a535513`), tarball sha256 `1ce0a6b6...c0a5` verified on the box.

**Build note.** The first server build hung for about 30 minutes in the image's client test step (`profile-features-request-dedup.test.cjs` idle at 0.3% CPU, Vite SSR); it was killed, nothing was tagged, and the identical rebuild passed in the normal time. The hung attempt's log is kept as `build-8a8a7e83.attempt1-hung.log`; treat it as a flake to watch.

**Candidate checks (before cutover).** Image `cowork-web:8a8a7e83`: stamped `8a8a7e83`; `dav-parse.wasm` sha256 `d9d3ce85...8d94` equals `DAV_PARSE_WASM_SHA256` in `dav-parse.lock`; no imports; exports include `mcp_rpc_body` and `mcp_schema_refs` (and the existing dav, s3, secret, storage and upload exports); no `*_IMPL` in the image environment. Run with `--network none`, read-only root, tmpfs state and a synthetic token: healthy, no FATAL line.

**Backups.** `config/.env.bak.before-8a8a7e83-20261007034306` and `config/.env.bak.before-code-verify-8a8a7e83-041448` (values never printed), `backups/cowork-db-before-8a8a7e83.sqlite` (SQLite `.backup`, integrity ok), `backups/web-state-before-8a8a7e83-20261007034306.tgz`, `backups/current-pointer-before-8a8a7e83.txt`, `backups/compose-before-8a8a7e83.yml`, `backups/compose-override-before-8a8a7e83.yml`, `docker-compose*.yml.bak.before-8a8a7e83` in the Compose Manager project, and container snapshots `releases/snapinspect-before-8a8a7e83.txt` and `snapinspect-after-8a8a7e83.txt`.

## Release b29d0e0b — 2026-10-07 (web and code sandbox: the sandbox bridge's Rust/WASM path behind dark `SANDBOX_BRIDGE_IMPL`, #999)

Source: noevia main `b29d0e0b28f0b4721c919b52234e77858d07250d` (CI green on #1001 including Assembled release, and on main). Assembled with `deploy/tools/assemble-release.sh b29d0e0b` (web `c80a3668`, core `32ca4bcb`, services `6a535513`).

**Candidate checks (before cutover).** Web image `cowork-web:b29d0e0b`: stamped `b29d0e0b`, no `*_IMPL` in the environment, `dav-parse.wasm` sha256 matches the core lock. Code-sandbox candidate, `--network none --read-only --cap-drop ALL --user 1000:1000`, no real workspace: `sandbox-bridge.wasm` sha256 `16c2930f...caed` matches `sandbox-bridge.lock`; `SANDBOX_BRIDGE_IMPL` unset; pi 0.87.0 (same as the live image); the supervisor started under js and listened on 8030 (checked from `/proc/net/tcp`, no connection made, since a connection starts an agent); `sandbox-bridge-wasm.test.cjs` and `pi-acp-bridge.test.cjs` 24 pass, 0 fail, 4 skipped (the noevia-rs fixture table is not in the image). No coding task was run.

**Backups.** `config/.env.bak.before-b29d0e0b-20261007031718` (values never printed), `backups/cowork-db-before-b29d0e0b.sqlite` (SQLite `.backup`, integrity ok), `backups/web-state-before-b29d0e0b-20261007031718.tgz`, `backups/current-pointer-before-b29d0e0b.txt` (release pointer, `COWORK_VERSION`, `CODE_SANDBOX_VERSION`, image ids), `backups/compose-before-b29d0e0b.yml`, `backups/compose-override-before-b29d0e0b.yml`, `docker-compose.override.yml.bak.before-b29d0e0b` and `docker-compose.yml.bak.before-b29d0e0b` in the Compose Manager project, snapshots `releases/snapinspect-before-b29d0e0b.txt` and `snapinspect-after-b29d0e0b.txt`.

**Cutover and verify.** Web first: `current` repointed, `COWORK_VERSION=b29d0e0b`, guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 120 web` (preflight passed, `Healthy`). Then `CODE_SANDBOX_VERSION=pi-0.87.0-b29d0e0b` and the same command for `code-sandbox`. Live: `cowork-web:b29d0e0b` healthy, 0 restarts; `/version.json` `{"version":"b29d0e0b","web":"c80a3668...","core":"32ca4bcb..."}`, also public; `/api/ready` 200; `/`, JS and CSS bundles and the three woff2 fonts 200; CSP has no Google source; egress is the node listener; `cowork-code-sandbox-1` running on the new tag, 0 restarts, `SANDBOX_BRIDGE_IMPL=js`, listening on 8030, sha of the module matches the lock; web and sandbox logs clean. The snapshot diff shows only `cowork-web-1` and `cowork-code-sandbox-1` changed.

## Release 9c3d67a3 — 2026-10-07 (web only: SECURITY, stored secrets with a GCM tag under 16 bytes are refused, #995; secret envelope in `dav-parse.wasm` behind dark `SECRET_ENVELOPE_IMPL`, #979)

Source: noevia main `9c3d67a3747222ffa3b9d33abcb361b1b40d9eb2` (CI green on #997 including Assembled release). Assembled with `deploy/tools/assemble-release.sh 9c3d67a3` (web `c80a3668`, core `92a7a0c5`, services `6a535513`), tarball sha256 `86bef729...` verified on the box, built with `build-web-release.sh`.

**Candidate checks (before cutover).** In `cowork-web:9c3d67a3`, `--network none`, real `.env` not loaded, throwaway state: `dav-parse.wasm` sha256 `4c6c8c59...2814` matches `dav-parse.lock`; exports include `secret_open` and `secret_seal`; no `*_IMPL` in the environment; `secret-envelope-wasm.test.cjs` 8/8, `secrets.test.cjs` 3/3, `secrets-rotate.test.cjs` 4/4; the server started healthy with no FATAL line.

**Credential check (booleans/counts only, read-only, never values).** A read-only script run in the live container opened every stored credential with the container's own key, before and after cutover, with identical results: `storage_connections` 2 rows (1 opens, 1 empty, 0 failed), `mcp_oauth_tokens` 0, `mcp_oauth_clients` 0. No decrypt, "needs re-auth" or "could not be opened" warning in the web log before, right after, or after a three-minute soak.

**Backups.** `config/.env.bak.20261007022641` (values never printed), `backups/cowork-db-before-9c3d67a3.sqlite` (SQLite `.backup`, integrity ok), `backups/web-state-before-9c3d67a3-20261007022641.tgz`, `backups/current-pointer-before-9c3d67a3.txt`, `backups/compose-before-9c3d67a3.yml`, snapshots `releases/snapinspect-before-9c3d67a3.txt` and `snapinspect-after-9c3d67a3.txt`.

**Cutover and verify.** `current` repointed, `COWORK_VERSION=9c3d67a3`, guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 120 web` (preflight passed, `Healthy`). Live: `cowork-web:9c3d67a3` healthy, 0 restarts; `/version.json` `{"version":"9c3d67a3","web":"c80a3668...","core":"92a7a0c5..."}`; `/api/ready` 200 (also public); `/`, JS and CSS bundles and the three woff2 fonts 200; CSP has no Google source; egress is the node listener; the snapshot diff shows only `cowork-web-1` changed.

## Release 8a8060d0 — 2026-10-07 (web only: a refused storage path is a 400, not a listing of the storage root, #984)

Source: noevia main `8a8060d0fea6f35fe93ff4dc89a15da8d4b6a24b` (CI green on #993, including Assembled release). Assembled on the Mac with `deploy/tools/assemble-release.sh 8a8060d0` (web `c80a3668`, core `c53cef6c`, services `6a535513`, noevia-rs `2b49af9`) and shipped as a tarball. The core and services checksums were computed twice from codeload and matched. Web built with `build-web-release.sh`.

**Candidate checks (before cutover).** In `cowork-web:8a8060d0`, `--network none`, read-only root, throwaway state: `listFiles` refused `../x`, `/abs`, `a/../../x` and a NUL path with status 400 and `Use a relative path inside the storage folder.` (no real storage touched); `storage-client-hardening.test.cjs` and `routes/storage.test.cjs` 21 of 21 pass; the candidate booted healthy, `/api/ready` 200, `version.json` showed core `c53cef6c`; no `*_IMPL` variable in the image env.

**Backups.** `config/.env.bak.20261007020453-before-8a8060d0` (values never printed), `backups/cowork-db-before-8a8060d0.sqlite` (SQLite `.backup`, integrity ok), `backups/web-state-before-8a8060d0-20261007020453.tgz`, `backups/current-pointer-before-8a8060d0.txt` and container snapshots `releases/snapinspect-before-8a8060d0.txt` and `snapinspect-after-8a8060d0.txt`.

**Cutover and verify.** `current` repointed, `COWORK_VERSION=8a8060d0`, guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 120 web` (preflight passed, `Healthy`). Live: `cowork-web:8a8060d0` healthy, 0 restarts; `/version.json` `{"version":"8a8060d0","web":"c80a3668…","core":"c53cef6c…"}`; `/api/ready` 200 (also through the public hostname); `/`, the JS and CSS bundles (`index-DR1AL8it.js`, `index-Dr_Ar-EH.css`, CSS unchanged) and the three woff2 fonts 200; the CSP has no Google sources and neither does the index; the egress listener is the node one (`egress.listening` on 172.28.0.3:8040, no egress-rs container); web log clean; no `*_IMPL` in the container env. The before/after snapshots differ only in `cowork-web-1` (id, image, start time). Server tarball and Mac scratch removed.

## Release 8f9ce34a — 2026-10-07 (web and OCR: upload checks in `dav-parse.wasm` behind dark `UPLOAD_SNIFF_IMPL`, Rust `docx-text` in the OCR image behind dark `DOCX_TEXT_IMPL`)

Source: noevia main `8f9ce34a62f36dbf78b60b5c9dc9001de40ddc92` (CI green on the head and on #988's assembled-release job). Assembled on the Mac with `deploy/tools/assemble-release.sh 8f9ce34a` (web `c80a3668`, core `2f41e11c`, services `3dd9d650`, noevia-rs `2b49af9`) and shipped as a tarball. Web built with `build-web-release.sh`; OCR built from `releases/8f9ce34a/services/ocr` as `cowork-ocr:3dd9d650`.

**Candidate checks (before cutover).** Web image: `dav-parse.wasm` sha256 `ff3a4f48…` equals `core/server/dav-parse.lock`; exports include `upload_validate`, `upload_classify` and `upload_decode`; no `*_IMPL` variable in the image env. OCR image: `docx-text extract` on an empty zip exits 1 with `docx-text: refused: missing` and no stdout; no `DOCX_TEXT_IMPL` in the image env. The OCR suite ran in the candidate with `--network none`, a read-only root and the source mounted read-only: 43 tests, 2 skips (differential, no binary configured) and 1 error. With `DOCX_TEXT_BIN` set, the differential, docx, switch and server tests pass (21 tests; differential: 89 identical, 478 both refused, 150 stricter). The one error is `test_pdf_reduce.test_budget_is_below_the_web_abort`, which reads the pre-split path `apps/web/server/pdf-reduce.cjs` and cannot pass outside the monorepo layout (a test-layout issue in noevia-services, not the candidate). No real documents were used.

**Backups.** `config/.env.bak.20261007014829-before-8f9ce34a` and `config/.env.bak.20261007015111-before-ocr-3dd9d650` (values never printed), `backups/cowork-db-before-8f9ce34a.sqlite` (SQLite `.backup`, integrity ok), `backups/web-state-before-8f9ce34a-20261007014829.tgz`, `backups/current-pointer-before-8f9ce34a.txt`, `backups/ocr-version-before-8f9ce34a.txt`, `backups/compose-before-8f9ce34a.yml` and `docker-compose*.yml.bak.before-8f9ce34a` in the Compose Manager project, and container snapshots `snapinspect-before-8f9ce34a.txt` and `snapinspect-after-8f9ce34a.txt`.

**Cutover and verify.** Web first: `current` repointed, `COWORK_VERSION=8f9ce34a`, guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 120 web` (preflight passed, `Healthy`). Then OCR: `OCR_VERSION=3dd9d650` and the same command with `ocr`. Live: `cowork-web:8f9ce34a` healthy, 0 restarts; `/version.json` `{"version":"8f9ce34a","web":"c80a3668…","core":"2f41e11c…"}`; `/api/ready` 200; `/`, the JS and CSS bundles and the woff2 fonts 200; no Google sources in the CSP or index; egress listener is the node one (`egress.listening` on 172.28.0.3:8040); web log clean. `cowork-ocr:3dd9d650` healthy, 0 restarts, `/health` 200, log clean, `DOCX_TEXT_IMPL` unset. The before/after snapshots differ only in `cowork-web-1` and `cowork-ocr-1` (id, image, start time). Server tarball and Mac scratch removed.

## Release 51871f21 — 2026-10-07 (web only: S3 listing parser and storage path rules behind dark switches, NUL refused in storage paths)

Source: noevia main `51871f21460ce431fe6e19cb2bb7736d6ac0043f` (#985). Assembled on the Mac with `deploy/tools/assemble-release.sh 51871f21` (web `c80a3668`, core `d8f70188`, services `66b40f96`; `release-refs` matched), built on the server with `noevia/deploy/tools/build-web-release.sh` (in-build tests and build passed, stamp verified).

**Candidate checks (before cutover).** Image `dav-parse.wasm` sha256 `6979df21364c7d545ef7597bebe2f3231c975900800178aee8005b7539f2649d` equals `DAV_PARSE_WASM_SHA256`, and the image's `server/dav-parse.lock` is byte-identical to core's; the module exports `memory, dav_input, dav_list, dav_output_len, dav_output_ptr, s3_list, storage_path`; none of the three `*_IMPL` flags is in the image environment; `safeRelativePath` refuses a NUL path and accepts `a/b.txt`. A throwaway container (`--network none`, synthetic env, no real state, removed afterwards) went ready: `/api/ready` 200 with version `51871f21`. A first attempt with `--read-only` crashed on creating `ui-data`; that was the test flag, not the image.

**Backups.** `config/.env.bak.before-51871f21` (values never printed), `state/web/cowork.db.bak.before-51871f21` (SQLite `.backup`, integrity ok), `releases/current-pointer-before-51871f21.txt`, container snapshots `releases/snapfull-before-51871f21.txt` and `releases/snapinspect-before-51871f21.txt` (after-snapshots alongside).

**Cutover and verify.** `current` repointed, `COWORK_VERSION=51871f21`, guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 120 web` (preflight passed, `Healthy`). Live: `cowork-web:51871f21` healthy, 0 restarts; `/version.json` `{"version":"51871f21","web":"c80a3668…","core":"d8f70188…"}`; `/api/ready` 200 (also through the public URL); `/` and woff2 fonts 200; no Google sources in the CSP or index; egress listener is the node one (`egress.listening` on 172.28.0.3:8040); web log clean; live wasm hash matches and no `*_IMPL` flag set. The before/after snapshots differ only in `cowork-web-1` (id, image, start time). No real storage reads were made.

## Release ebe6344d — 2026-10-07 (web only: WebDAV listing hardening, `<bdi>` isolation of storage file names)

Source: noevia main `ebe6344d1ceff69cc4a9805cf8a9cc231ee8b2b3` (`e9be748e`, #974, plus the docs-only changelog #975; CI green). Assembled on the Mac from a fresh clone with `deploy/tools/assemble-release.sh ebe6344d` (web `c80a3668`, core `e5c58db4`, services `66b40f96`; `release-refs` matched), built on the server with `noevia/deploy/tools/build-web-release.sh` (in-build tests and build passed, stamp verified).

**Candidate checks (before cutover).** Image `dav-parse.wasm` sha256 `211447151cc372cf794a979a08d595cd5385d1aeff46b638f04a3627910b4457` equals `DAV_PARSE_WASM_SHA256` in core's `server/dav-parse.lock`; `DAV_PARSE_IMPL` is not in the image environment; `server/dav-listing.cjs` exports `isListableName`. A throwaway container (`--network none`, tmpfs state, synthetic env, removed afterwards) went ready: `/api/ready` 200, `/` 200, `version.json` correct.

**Backups.** `config/.env.bak.before-ebe6344d` (values never printed), `state/web/cowork.db.bak.before-ebe6344d` (SQLite `.backup`, integrity ok), `releases/current-pointer-before-ebe6344d.txt`, container snapshots `releases/snapfull-before-ebe6344d.txt` and `releases/snapinspect-before-ebe6344d.txt` (after-snapshots alongside).

**Cutover and verify.** `current` repointed, `COWORK_VERSION=ebe6344d`, guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 120 web` (preflight passed, `Healthy`). Live: `cowork-web:ebe6344d` healthy, 0 restarts; `/version.json` `{"version":"ebe6344d","web":"c80a3668…","core":"e5c58db4…"}`; `/api/ready` 200 (also through the public URL); JS, CSS, icons and woff2 fonts 200; no Google sources in the CSP or index; egress listener is the node one (`egress.listening` on 172.28.0.3:8040); web log clean. The before/after snapshots differ only in `cowork-web-1` (id, image, start time); every other container keeps its id, start time and 0 restarts. No real storage reads were made.

## Release 4be51449 — 2026-10-07 (web only: WebDAV listing parser moved to `server/dav-listing.cjs`, dark `DAV_PARSE_IMPL` switch, `dav-parse.wasm` built into the web image)

Source: noevia main `4be51449abd7e6b5607ac3ffae00342aee6748ca`. Assembled on the Mac with `deploy/tools/assemble-release.sh 4be51449` (web `9dab1569`, core `7b95687c`, services `66b40f96`), built on the server with `noevia/deploy/tools/build-web-release.sh`.

**Candidate checks (before cutover).** Image `dav-parse.wasm` sha256 `ed104305…d659` equals `DAV_PARSE_WASM_SHA256` in core's `server/dav-parse.lock`; `DAV_PARSE_IMPL` is not in the image environment; `server/dav-listing.cjs` present. A throwaway container (`--network none`, empty state dir, removed afterwards) went healthy; `/api/ready` 200, `version.json` correct.

**Backups.** `config/.env.bak.before-4be51449` (values never printed), `state/web/cowork.db.bak.before-4be51449` (+ `-wal`), `releases/current-pointer-before-4be51449.txt`, container snapshot `releases/snapfull-before-4be51449.txt`.

**Cutover and verify.** `current` repointed, `COWORK_VERSION=4be51449`, guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 120 web` (preflight passed, `Healthy`). Live: `cowork-web:4be51449` healthy, 0 restarts; `/version.json` `{"version":"4be51449","web":"9dab1569…","core":"7b95687c…"}`; `/api/ready` 200 (also through the public URL); JS, CSS, woff2 fonts and icons 200; CSP has no Google sources; egress is the in-process node proxy (`CODE_EGRESS_IMPL` unset); logs clean. The post-snapshot (`releases/snapfull-after-4be51449.txt`) differs from the before one only in `cowork-web-1`. No storage browse call was made (no synthetic endpoint, real storage not touched).

## Release Model manager 08c65957 — 2026-10-07 (model manager only: Rust `model-files` CLI behind `MODEL_FILES_IMPL`, default python)

Source: noevia main `08c659572bdbf556e7e6508db3890a85d6cab3dd` (`48024b03` plus the 3a48d1e6 changelog only; CI success on both). Assembled on the Mac with `deploy/tools/assemble-release.sh 08c65957` from the pinned repos (web `9dab1569`, core `93d180a1`, services `66b40f96`), unpacked to `releases/08c65957/` with `release-refs` checked, and built with `docker build -t cowork-model-loader:08c65957 releases/08c65957/services/model-manager` (not through Compose, and `current` unchanged).

**Candidate checks (before cutover, `--network none`, no Hugging Face call).** `model-files` exits 0 on `[]` (`{"files":[]}`), 1 on non-JSON input and 2 on usage; `gguf-meta` exits 2 on usage; neither flag is in the image's environment. The service's own suite passed in a throwaway image (`FROM` the candidate plus `pytest` and `pytest-asyncio`, since removed): 360 passed, 10 skipped (the differential tests need `GGUF_META_BIN` and `MODEL_FILES_BIN`; they run in CI, as do the two `apps/web` tests, which have no tree here).

**Backups.** `config/.env.bak.20261006233320` (mode 600, values never printed); `docker-compose.yml.bak.before-mm-08c65957-20261006233320` and `docker-compose.override.yml.bak.before-mm-08c65957-20261006233320` (copies only, neither file was edited); `releases/mm-before-08c65957.txt` (previous tag and image id); container snapshots `releases/snapfull-before-mm-08c65957.txt` and `snapfull-after-mm-08c65957.txt`.

## Release 3a48d1e6 — 2026-10-07 (web only: first release after the repo split; Glass menus, phone-preview settings, click after closing Settings)

**Split release flow, first use.** The source is the assembled tarball from `deploy/tools/assemble-release.sh 3a48d1e6 <out>` run on the Mac from a clean checkout, not a `git archive`. It reads `release/versions.lock` as committed at the released SHA and fetches each pinned repo as a checksum-verified tarball. Pinned SHAs: noevia `3a48d1e6036d709f2f95d66e020b0a30607fcfd0`, noevia-web `9dab15691f3690d4cd62bf8817255f1b39f6df84`, noevia-core `93d180a199f06769be2c12f47277637f06c354c7`, noevia-services `54449fce271398da58117d280ca8089058fff0cc` (noevia-rs `14e08ddb`, not part of the web image). The tarball was unpacked to `releases/3a48d1e6/` and `release-refs` was checked to say `NOEVIA_SHA=3a48d1e6`.

**Release path: full build, not overlay.** `releases/3a48d1e6/noevia/deploy/tools/build-web-release.sh 3a48d1e6 releases/3a48d1e6` on the deployment host, the primary documented route, building the same tree CI's "Assembled release (pinned repos)" job built and booted. It runs the client and server tests in the image build and checks the stamp. `overlay-release.sh` was not used: it also recreates Diary and OCR, and a web-only release must not.

**Live Compose edit (one time, per `docs/deployment.md`).** `docker-compose.yml` web `build:` changed from `context: ${COWORK_SOURCE_DIR:?Set COWORK_SOURCE_DIR}/apps/web` to `context: ${COWORK_SOURCE_DIR:?Set COWORK_SOURCE_DIR}` plus `dockerfile: noevia/build/web.Dockerfile` (`args: COWORK_VERSION` kept). `docker-compose.override.yml` code-sandbox `build.context` changed from `.../services/code-sandbox` to `.../core/code-sandbox` (that block lives in the override file). Nothing else changed; `docker compose --env-file <.env> config -q` passes. Code-sandbox was not rebuilt.

**Backups.** `config/.env.bak.20261006230507` (mode 600, values never printed); `state/web/cowork.db.bak.before-3a48d1e6` (sqlite `.backup`, `integrity_check` ok); release pointer `current.prev-3a48d1e6` (-> `releases/7baecb40`); `docker-compose.yml.bak.before-3a48d1e6-20261006230507`, `docker-compose.yml.bak.20261006230507` and `docker-compose.override.yml.bak.20261006230507`; container snapshots `releases/snapfull-before-3a48d1e6.txt` and `snapfull-after-3a48d1e6.txt`.

**Cutover and verify.** Synthetic candidate first (throwaway state, loopback port, removed afterwards): healthy, `/version.json`, `/api/ready` and `/settings/appearance` 200, no Google source in the CSP. Then `current` and `COWORK_VERSION` repointed and web started alone with the guarded `up.sh --env-file .env -- -d --no-build --no-deps --wait --wait-timeout 120 web` (preflight passed, `Healthy`). Live: `cowork-web-1` healthy, `RestartCount` 0, `version.json` `{"version":"3a48d1e6","web":"9dab15691f3690d4cd62bf8817255f1b39f6df84","core":"93d180a199f06769be2c12f47277637f06c354c7"}`, `/api/ready` 200, `/settings/appearance` 200, bundle and CSS and three woff2 fonts 200, CSP has only `'self'` sources, egress implementation node, logs clean. The before/after snapshot differs in one line: `cowork-web-1` (new id, `cowork-web:3a48d1e6`, `StartedAt` 2026-10-07T03:15:17Z); every other container keeps its id and start time. Synthetic checks only: no model run, tune, Diary access or flag change.

## Release Laya f42f65f1 — 2026-10-07 (Laya only: concurrent serving, default still one model copy)

Exact source `f42f65f1271ef27bf697bf7e069c232468479791` (CI success on that commit). Same pattern as `noevia2`: `FROM cowork-laya:0.3.5-noevia1` plus `services/laya/server.py` from that SHA (sha256 `3a9d8b39...`, identical on the box, in the build context and inside the running container), so dependencies and model files are unchanged. Candidate check: the 23 `test_server.py` unit tests passed inside the new image (`--network none`, read-only, no model load).

**Backups.** `config/.env.bak.before-laya-f42f65f` (mode 600, values never printed), Compose project `docker-compose.yml.bak.before-laya-f42f65f`, container snapshots `releases/snapfull-before-laya-f42f65f.txt` and `snapfull-after-laya-f42f65f.txt`.

## Release 7baecb40 — 2026-10-07 (web only: UI redo, self-hosted fonts, dark Rust egress grant contract)

PRs: #953, #954, #955. Issues: #951, #956.

No feature flag, env var or compose override was changed (`CODE_EGRESS_IMPL` not set). No model run, tune, benchmark or download, no Code task, no private Diary access.

Exact source `7baecb404120d870fa37ad1189ef59776ac9aa9a` (main CI completed success on that commit before cutover). **Release path: Mac-built overlay, not a full image build.** The client was built on the Mac from a clean detached worktree with `npm ci` against the new lockfile and `STAMP_VERSION=7baecb40 npm run build` in `apps/web`, so `motion` is bundled into `dist/assets/index-*.js` (it is a client-only dependency; the server image installs only `apps/web/server` dependencies, whose `package.json` and lockfile did not change). `dist server contracts` (without `server/node_modules` and `server/ui-data`) were layered onto `cowork-web:a1dfd69f` with the standard overlay Dockerfile; `git archive` of the repo root went into `releases/7baecb40`. The three self-hosted `.woff2` files are emitted into `dist/assets` by Vite (not served from `public/`).

**Order and results.**

1. **Candidate.** Image Env, WorkingDir, ExposedPorts, User, Entrypoint, Cmd and Healthcheck identical to the old image; `dist/version.json` `7baecb40`, `dist/index.html` sha256 `06c13fdd...` equal to the Mac build, 70 files in `dist/assets`. Synthetic throwaway container (`--network none`, tmpfs data dir, removed afterwards): `/api/ready`, `/api/setup/status`, `/version.json`, `/settings/appearance` and `/` all 200; JS, CSS and the three fonts 200 with `font/woff2`.
2. **Backups.** `config/.env.bak.before-7baecb40` (mode 600, never printed), `state/web/cowork.db.bak.before-7baecb40`, release pointer copy `current.prev-7baecb40` (-> `releases/a1dfd69f`), container snapshots `releases/snapfull-before-7baecb40.txt` and `snapfull-after-7baecb40.txt`.
3. **Cutover.** `current` and `COWORK_VERSION` repointed; started alone with `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (preflight passed, `Healthy`). New `cowork-web-1` `StartedAt` 2026-10-07T02:00:14Z.

## Release a1dfd69f — 2026-10-06 (web only: model-download token and queue errors surfaced, Diary backup date uses the app locale)

PRs: #949. Issues: #948.

**Database migration.** None. No schema change in this release, so no database backup was taken and the previous image runs on the same database.

No feature flag was changed. No model run, tune, benchmark or download, no Code task, no private Diary access. The Diary overlay (still pending) was not touched.

Exact source `a1dfd69fd1524c00d667a5c56aad4d67ae985b09` (main CI completed success on that commit before cutover, 12 of 12 jobs). Built on the Mac from a clean detached worktree: `STAMP_VERSION=a1dfd69f npm run build` in `apps/web`, then `COPYFILE_DISABLE=1 tar -h --no-xattrs` of `dist server contracts` (without `server/node_modules` and `server/ui-data`), and a `git archive` of the repo root into `releases/a1dfd69f`. Dependencies gate against `e2f9d59b`: no change to `apps/web/package.json`, `apps/web/package-lock.json`, `apps/web/server/package.json` or `apps/web/server/package-lock.json`, so `node_modules` came from the old image.

**Order and results.**

1. **Web.** Layered `dist/`, `server/` and `contracts/` onto `cowork-web:e2f9d59b` with the standard overlay Dockerfile (86 to 90 layers, under the 100-layer flatten limit; Env, WorkingDir, ExposedPorts, User, Entrypoint, Cmd and Healthcheck identical to the old image). Before cutover the image was checked to contain `/app/contracts/project-icons.json` and `/app/contracts/project-limits.json`, `dist/version.json` `a1dfd69f` and a `dist/index.html` sha256 equal to the Mac build. Synthetic candidate in a throwaway `--network none` container with a tmpfs data dir: server booted on a fresh database, `/api/ready` 200, `/api/setup/status` 200, `/version.json` `a1dfd69f`; the container was removed. `config/.env.bak.before-a1dfd69f` taken, `current` and `COWORK_VERSION` repointed; started alone with `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (preflight passed, `Healthy`). Cutover 2026-10-06 13:06:40Z to 13:06:58Z; the new `cowork-web-1` `StartedAt` is 13:06:52Z.

## Release e2f9d59b — 2026-10-06 (web only: benchmarks rating-clear error, saved-prompt delete confirmation, project delete flow)

PRs: #944, #945. Issues: #943, #942.

**Database migration.** None. No schema change in this release, so no database backup was taken and the previous image runs on the same database.

No feature flag was changed. No model run, tune, benchmark or download, no Code task, no private Diary access. The Diary overlay (still pending) was not touched.

Exact source `e2f9d59b05896bc83f4e0c2964e8afa82aaf66cf` (main CI completed success on that commit before cutover). Built on the Mac from a clean detached worktree: `STAMP_VERSION=e2f9d59b npm run build` in `apps/web`, then `COPYFILE_DISABLE=1 tar -h --no-xattrs` of `dist server contracts` (without `server/node_modules` and `server/ui-data`), and a `git archive` of the repo root into `releases/e2f9d59b`. Dependencies gate against `eee0dc93`: no change to `apps/web/package.json`, `apps/web/package-lock.json`, `apps/web/server/package.json` or `apps/web/server/package-lock.json`, so `node_modules` came from the old image.

**Order and results.**

1. **Web.** Layered `dist/`, `server/` and `contracts/` onto `cowork-web:eee0dc93` with the standard overlay Dockerfile (82 to 86 layers, under the 100-layer flatten limit; Env, WorkingDir, ExposedPorts, User, Entrypoint, Cmd and Healthcheck identical to the old image). Before cutover the image was checked to contain `/app/contracts/project-icons.json` and `/app/contracts/project-limits.json`, `dist/version.json` `e2f9d59b` and a `dist/index.html` sha256 equal to the Mac build. Synthetic candidate in a throwaway `--network none` container with a tmpfs data dir: server booted on a fresh database, `/api/ready` 200, `/api/setup/status` 200, `/version.json` `e2f9d59b`; the container was removed. `config/.env.bak.before-e2f9d59b` taken, `current` and `COWORK_VERSION` repointed; started alone with `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (preflight passed, `Healthy`). Cutover 2026-10-06 12:51:07Z to 12:51:25Z; the new `cowork-web-1` `StartedAt` is 12:51:19Z.

## Release eee0dc93 — 2026-10-06 (web only: ChatGPT sign-in failed retry marks only the failed sign-in)

PRs: #935. Issues: #934.

**Database migration.** None. No schema change in this release, so no database backup was taken and the previous image runs on the same database.

No feature flag was changed. No model run, tune, benchmark or download, no Code task, no private Diary access. The Diary overlay (still pending) was not touched.

Exact source `eee0dc933789cda0b3b973060d9c0b066f80a631` (main CI green on that commit). Built on the Mac from a clean detached worktree: `STAMP_VERSION=eee0dc93 npm run build` in `apps/web`, then `COPYFILE_DISABLE=1 tar -h --no-xattrs` of `dist server contracts` (without `server/node_modules` and `server/ui-data`), and a `git archive` of the repo root into `releases/eee0dc93`. Dependencies gate against `e9efa32e`: no change to `apps/web/package.json`, `apps/web/package-lock.json`, `apps/web/server/package.json` or `apps/web/server/package-lock.json`, so `node_modules` came from the old image.

**Order and results.**

1. **Web.** Layered `dist/`, `server/` and `contracts/` onto `cowork-web:e9efa32e` with the standard overlay Dockerfile (78 to 82 layers, under the 100-layer flatten limit). Before cutover the image was checked to contain `/app/contracts/project-icons.json` and `/app/contracts/project-limits.json`, `dist/version.json` `eee0dc93` and a `dist/index.html` sha256 equal to the Mac build. Synthetic candidate in a throwaway `--network none` container with a tmpfs data dir: server booted on a fresh database, healthy, `/api/ready` 200, `/version.json` `eee0dc93`; the container was removed. `config/.env.bak.before-eee0dc93` taken, `current` and `COWORK_VERSION` repointed; started alone with `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (preflight passed, `Healthy`). Cutover 2026-10-06 12:31:09Z to 12:31:26Z; the new `cowork-web-1` `StartedAt` is 12:31:20Z.

## Release e9efa32e — 2026-10-06 (web only: capped response reads, sign-in limits and credential epoch, SSRF and egress hardening)

PRs: #924 #929 #931. Issues: #920 #927 #928 #930 #932 #933.

No feature flag was changed. No model run, tune, benchmark or download, no Code task, no private Diary access. The Diary overlay (still pending) was not touched.

Exact source `e9efa32e514aa23e43187fb9a7cfde0455de9cb0` (main CI green on that commit). Built on the Mac from a clean detached worktree: `STAMP_VERSION=e9efa32e npm run build` in `apps/web`, then `COPYFILE_DISABLE=1 tar -h --no-xattrs` of `dist server contracts` (without `server/node_modules` and `server/ui-data`), and a `git archive` of the repo root into `releases/e9efa32e`. Dependencies gate against `cf662822`: no change to `apps/web/package-lock.json`, `apps/web/server/package.json` or `apps/web/server/package-lock.json`, and the `dependencies`, `devDependencies`, `overrides` and `engines` fields of `apps/web/package.json` are identical, so `node_modules` came from the old image.

**Order and results.**

1. **Web.** Layered `dist/`, `server/` and `contracts/` onto `cowork-web:cf662822` with the standard overlay Dockerfile (74 to 78 layers, under the 100-layer flatten limit). Before cutover the image was checked to contain `/app/contracts/project-icons.json` and `/app/contracts/project-limits.json` and `dist/version.json` `e9efa32e`. Synthetic candidate in a throwaway `--network none` container with a tmpfs data dir: server booted on a fresh database (the migration ran there too, `credential_epoch` present), `/api/ready` 200, `/version.json` `e9efa32e`; the container was removed. Database backup taken, `config/.env.bak.before-e9efa32e` taken, `current` and `COWORK_VERSION` repointed; started alone with `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (preflight passed, `Healthy`). Cutover 2026-10-06 09:03:58Z to 09:04:15Z; the new `cowork-web-1` `StartedAt` is 09:04:09Z.

**New startup warning (action for the owner, not changed here).** The log now carries `WARNING: the public address uses https but TRUST_PROXY is off. If noevia runs behind a reverse proxy or tunnel, every visitor shares the proxy's address, so sign-in limits and audit-log addresses apply to everyone at once. Set TRUST_PROXY=true when the proxy sets X-Forwarded-For.` The live deployment is behind the tunnel with `TRUST_PROXY` off, so the new per-address sign-in limits are shared by all visitors until the owner decides to set it. No setting was changed in this release.

## Release cf662822 — 2026-10-06 (web only: capped storage/provider reads and the project-bound chat grant)

PRs: #911 #915 #916 (web half) #921. Issues: #902 #903 #905 #917 #918.

No feature flag was changed. No model run, tune, benchmark or download, no Code task, no private Diary access. The Diary overlay (still pending) was not touched.

Exact source `cf662822fee73a5ca838a2ca82338af5d89e72d9` (main CI green on that commit). Built on the Mac from a clean detached worktree: `STAMP_VERSION=cf662822 npm run build` in `apps/web`, then `COPYFILE_DISABLE=1 tar -h --no-xattrs` of `dist server contracts` (without `server/node_modules` and `server/ui-data`), and a `git archive` of the repo root into `releases/cf662822`. Dependencies gate: no change to `apps/web/package-lock.json`, `apps/web/server/package.json` or `apps/web/server/package-lock.json` since `8cbced50`, and the `dependencies`, `devDependencies`, `overrides` and `engines` fields of `apps/web/package.json` hash identically, so `node_modules` came from the old image.

**Order and results.**

1. **Web.** Layered `dist/`, `server/` and `contracts/` onto `cowork-web:8cbced50` with the standard overlay Dockerfile (70 to 74 layers, under the 100-layer flatten limit). Before cutover the image was checked to contain `/app/contracts/project-icons.json` and `/app/contracts/project-limits.json` and `dist/version.json` `cf662822`. Synthetic candidate in a throwaway `--network none` container with a tmpfs data dir: server booted, `/api/ready` 200, `/version.json` `cf662822`; the container was removed. `config/.env.bak.before-cf662822` taken; `current` and `COWORK_VERSION` repointed; started alone with `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (preflight passed, `Healthy`). Cutover 2026-10-06 08:01:17Z to 08:01:34Z; the new `cowork-web-1` `StartedAt` is 08:01:28Z.

## Release 227903da — 2026-10-06 (sidecars only: model-manager and OCR)

PRs: #907 #908 #912 #916. Issues: #901 #904 #909 #914.

No feature flag was changed, and `GGUF_PARSER` was not set. No model was loaded, unloaded, downloaded, benchmarked or tuned, no Code task ran, and nothing touched the private Diary. The engine's loaded model stayed loaded.

Exact source `227903da965c54666cf5c4aca65604341736a266` (main CI green on that commit). A `git archive` from the Mac checkout went to `releases/227903da`. Both images were built on the deployment host with plain `docker build` from that tree (`services/ocr`, `services/model-manager`) under `nice`, tagged `227903da-candidate`, tested, then retagged `227903da`; `current` was not repointed because only sidecars changed. The model-manager build runs a Rust builder stage that fetches the noevia-rs tarball from codeload.github.com, verifies its sha256 and builds `gguf-meta`; it succeeded on the deployment host without any network workaround.

**Order and results.**

1. **Candidate checks (before any cutover).** Model-manager: a throwaway `--network none` container with a synthetic token and a synthetic 4-key GGUF file (including a NaN float). `gguf-meta --help` printed its usage line (exit 2, by design), `gguf-meta <file>` exited 0 with a JSON summary, the app imported (`app.main`), `settings.gguf_parser` and `parser_choice()` both returned `python`, and `summarize_path` returned the Python summary. OCR: a throwaway `--network none --read-only` container, `/health` 200 `{"service": "ocr"}`, `pdf_reduce` and `server` import, `REDUCE_DEADLINE_SECONDS` present. Both containers were removed.
2. **Model-manager.** `config/.env.bak.before-sidecars-227903da` taken (it also covers the OCR line), `MODEL_MANAGER_VERSION` set, started alone with `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 model-loader` (preflight passed, `Healthy`). Cutover 2026-10-06 07:50:39Z to 07:51:10Z; the new `cowork-model-loader-1` `StartedAt` is 07:50:39Z.
3. **OCR.** `OCR_VERSION` set, started alone with the same `up.sh` line for `ocr`. Cutover 07:51:14Z to 07:51:30Z; the new `cowork-ocr-1` `StartedAt` is 07:51:24Z.

**Verify.** Model-loader: healthy, `RestartCount` 0, `/api/v1/health` 200 `{"ok":true}`, web's `GET /api/v1/backends` calls return 200 in its log, `/usr/local/bin/gguf-meta` present (sha256 `aa262b77...`), `parser_choice()` is `python`. OCR: healthy, `RestartCount` 0, `/health` 200 and web reaches `http://ocr:8030/health` with 200; `/app/pdf_reduce.py` sha256 `2d07bffb...`. The 60-line log tails of both are clean. `sidecar-restart-alert.sh --ack` was run and `--dry-run` afterwards reported nothing. Diffing a full container snapshot (name, image, status, `StartedAt`, restart count, id) before and after: only `cowork-model-loader-1` and `cowork-ocr-1` changed. Web, Diary, Docling, Code sandbox, code-verify, llama, embed, Laya, Kiwix, DAV relay, the tunnel and every non-noevia container kept id and `StartedAt`.

## Release 8cbced50 — 2026-10-06 (web only: round-3 server fixes and the `contracts/` move)

PRs: #898 #899. Issues: #891 #892 #893 #894 #895 #897.

No feature flag was changed. No model run, tune, benchmark or download, no Code task, no private Diary access. The Diary overlay (still pending since 8e96d876) was not touched.

Exact source `8cbced50c7ba13d2c6f9dc8366100815d4e8cf9b` (main CI green on that commit). Built on the Mac from a clean detached worktree: `STAMP_VERSION=8cbced50 npm run build` in `apps/web`, then `COPYFILE_DISABLE=1 tar -h --no-xattrs` of `dist server contracts` (without `server/node_modules` and `server/ui-data`), and a `git archive` of the repo root into `releases/8cbced50`. `apps/web/package.json` changed since `8e96d876` only in its `scripts` block (the dependencies, devDependencies, overrides and engines fields hash identically); no lockfile and no `apps/web/server/package*.json` changed, so `node_modules` came from the old image.

**Order and results.**

1. **Web.** Layered `dist/`, `server/` and `contracts/` onto `cowork-web:8e96d876` with the standard overlay Dockerfile (66 to 70 layers, under the 100-layer flatten limit). Before cutover the image was checked to contain `/app/contracts/project-icons.json` and `/app/contracts/project-limits.json`, `dist/version.json` `8cbced50` and the 52 server dependencies. Synthetic candidate in a throwaway `--network none` container with a tmpfs data dir: server booted, `/api/ready` 200 (`8cbced50`), `/version.json` 200. `config/.env.bak.before-8cbced50` taken; `current` and `COWORK_VERSION` repointed; started alone with `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (preflight passed, `Healthy`). Cutover 2026-10-06 07:21:24Z to 07:21:41Z; the new `cowork-web-1` `StartedAt` is 07:21:35Z.

**Verify.** Web: healthy, `RestartCount` 0; `127.0.0.1:8021/version.json` and `https://noevia.example.com/version.json` both `8cbced50`; `/api/ready` 200 `{"ready":true,"version":"8cbced50"}` locally and publicly; `/app/dist/index.html` sha256 `54526d90...` identical to the candidate image; in the container `contracts/project-icons.json` sha256 `bce8d2a2...` and `project-limits.json` `aa1ed3fc...`; the log shows MCP discovery (noevia 10, nextcloud 181, tavily 5 tools), `codenet.guarding` on `172.28.0.3` and no error line. Sidecars: diary, ocr, docling, model-loader, llama, embed and laya kept container id, `StartedAt` and restart count against the pre-cutover snapshot; code-sandbox and code-verify (missing from that snapshot because of a template error in the snapshot command) show `StartedAt` 2026-10-05T23:12:36Z, before the cutover. Only `cowork-web-1` changed.

## Release 8e96d876 — 2026-10-05 (repo sweep release 4, final: web and model-manager; Diary not deployed)

PRs: #888 #889. Issues: #841 #843 #845 #876 #884 #885 #886 #887 (#885 is closed on GitHub, but its fix does not run until the Diary overlay is re-run).

No feature flag was changed and `TRUST_PROXY` was not touched. No model run, tune, calibration, benchmark or download, no Code task, no private Diary access and nothing POSTed to the Diary by this release.

Exact source `8e96d87615894b7d55653c7ae49dc8d5c279f4b8` (main CI green on that commit: every job including `CI required`, plus the offline skills contract). A `git archive` from a throwaway worktree (SHA-256 `82bd1af4...`, matched on the server) went to `releases/8e96d876`. No `package.json`, lockfile, Diary or model-manager `requirements.txt`/Dockerfile changed since `f6885a55`. Evidence is in `/root/release-evidence-8e96d876/` on the deployment host (snapshots of all containers before and after each step, build logs, models lists before and after).

**Order and results.**

**Verify.** Web: healthy; `dist/version.json` `8e96d876`; `index.html` sha256 `b9c28030...` identical in the build, the image, `127.0.0.1:8021` and the public page; the served `index-DMgsd6_1.js` and `index-Cl1i6_9h.css` exist in the image's `dist/assets` (67 files); `/` 200, `/api/ready` 200 (`8e96d876`), unauthenticated `/api/profile`, `/api/diary/exchanges` and `/api/diary/storage-status` 401 locally and publicly (not 502); the log shows `codenet.guarding` with `["172.28.0.3"]`, the same address as before, and no error line. Diary: healthy on `f6885a55`, `/api/health` 200 with the token and 401 without. Model-loader: healthy on `8e96d876`, `RestartCount` 0; `GET /api/v1/models` lists the same 7 models and is byte-identical to the list before (`cmp`); `models.ini` is byte-identical to its backup; `/health`, `/overview`, `/downloads`, `/sections`, `/download-targets` and `/benchmark/progress` 200, the last `idle`, `active: false`; startup log has no warning, and the reaper logs only when it removes or fails to stop something, so its silence is expected: a read-only check from inside the container found the Docker client reachable and 0 containers with the label, and the unlabelled `llama-vulkan-test` and `model-loader-test` containers are unchanged. `cowork-llama-1` kept id, `StartedAt` (2026-10-01T06:39:59Z) and restart count.

- **Web** (previous `f6885a55`): `ln -sfn $B/releases/f6885a55 $B/current && sed -i 's/^COWORK_VERSION=.*/COWORK_VERSION=f6885a55/' $B/config/.env && $UP -- -d --no-build --no-deps --wait --wait-timeout 180 web`. The `cowork-web:f6885a55` image is retained.
- **Model-loader** (previous `f6885a55`): `sed -i 's/^MODEL_MANAGER_VERSION=.*/MODEL_MANAGER_VERSION=f6885a55/' $B/config/.env`, then the same `up.sh` ending in `model-loader`. The only schema change is `CREATE INDEX IF NOT EXISTS req_timing_dedupe`, which the old image ignores. `models.ini` was not changed (byte-identical to `config/llamacpp/models.ini.bak.before-8e96d876`). The `cowork-model-loader:f6885a55` image is retained.
- **Diary:** nothing to roll back; it was not changed.

## Release f6885a55 — 2026-10-05 (repo sweep release 3: web, Diary, model-manager, Code sandbox and Docling)

No feature flag was changed and `TRUST_PROXY` was not touched. No model run, tune, calibration, benchmark or download, no real document sent to Docling, no Code task, no private Diary access and nothing POSTed to the Diary by this release.

**Order and results.**

1. **Web.** `dist/` built on the deployment host (`npm ci`, `npm run build`, `STAMP_VERSION=f6885a55`, `node:22-bookworm-slim`, 4 GiB cap, from a copy of `apps/web`; CI is authoritative for tests) and layered onto `cowork-web:023ddcb5` with the same Dockerfile as before (63 layers, `sha256:a113faab...`). Synthetic candidate in a throwaway `--network none` container with an empty data dir: `/` 200, `/api/ready` 200 (`f6885a55`), `/api/profile` 401, `chat`, `projects`, `public-fetch`, `llamacpp-tune-spec` load. Backups `config/.env.bak.before-f6885a55`, `docker-compose.yml.bak.before-f6885a55`, `docker-compose.override.yml.bak.before-f6885a55`; only `COWORK_VERSION` differs in `.env`. Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (three preflight checks passed).
2. **Live override edits** (edited locally, copied back; no python on the host). (a) `web.environment` gained `COWORK_CODE_NET_ADDR: ${COWORK_CODE_NET_ADDR:-egress}`. Before recreating, `getent hosts egress` in web returned exactly one address, `172.28.0.3`, equal to the `egress.listening` bind; no other container has the `egress` alias. Web was recreated alone; the log shows `codenet.guarding` with `["172.28.0.3"]`, and public and local `/` 200, `/api/profile` 401, `/api/diary/exchanges` and `/api/diary/storage-status` 401 (not 403 or 502). A one-off read-only GET from `cowork-code-sandbox-1` to web's UI port on the code network returned 403 (`codenet.refused` logged once), which is the intended effect; the host path to the DAV port answered 421, not 403. (b) `docling` gained `init: true` next to `restart: unless-stopped`; `compose config` differed from before by that one line only, and it took effect at step 6.
3. **Diary.** `deploy/examples/diary-overlay.sh f6885a55` took appdata backup `ab_20261005_190839` (verified), built `cowork-diary:f6885a55` (`sha256:ab3981a1...`) `FROM` `023ddcb5` with `agent/` replaced, passed the candidate import test, recreated only `diary`; its own checks passed (model-loader unresolvable from Diary, health through web 200). `cowork-diary:rollback-before-diary-overlay` now points at `023ddcb5`, which is retained. Backup `config/.env.bak.before-diary-f6885a55`. The appdata backup stops and starts web and diary, so web restarted once more (`StartedAt` 23:08:53Z); that is the only reason web has a second start.
4. **Model-loader.** Read-only check from the web container first (token never printed): `/downloads` had no jobs, benchmark `idle`, no autotune or calibration log lines in 40 minutes, llama at 0.3% CPU. `models.ini` backed up as `config/llamacpp/models.ini.bak.before-f6885a55`, `.env` as `config/.env.bak.before-model-loader-f6885a55`; `cowork-model-loader:f6885a55` (`sha256:cb773503...`) built with `docker compose build model-loader` (pip layer cached; candidate import test passed), recreated alone.
5. **Code sandbox.** `docker top` showed only the supervisor (no task) and the logs were empty for 60 minutes. Built from `releases/f6885a55/services/code-sandbox` with `--network host --build-arg HARNESS_PACKAGE=@earendil-works/pi-coding-agent --build-arg HARNESS_VERSION=0.87.0` (pi 0.87.0, git 2.39.5; `pi-acp-bridge.cjs`, `verifier.cjs`, `supervisor.cjs` SHA-256 identical to the source). Backup `config/.env.bak.before-f6885a55` (taken at step 1) covers `CODE_SANDBOX_VERSION`. `code-sandbox` and `code-verify` recreated together with `up.sh --profile code -- -d --no-build --no-deps --wait`.
6. **Docling.** Idle first (no log lines for 10 minutes, 0.01% CPU). A plain `docker build` of `services/docling` missed the layer cache and began re-running `apt-get`, which would also have re-resolved unpinned `torch` and re-downloaded the models, so it was stopped after 90 seconds with nothing built. The image was instead built `FROM cowork-docling:9debec6` with only the six application files (`server.py extract.py isolation.py isolated_worker.py selftest.py synthetic_pdfs.py`) replaced, the same files the Dockerfile's final `COPY` places; user, workdir, cmd and healthcheck are inherited and identical. Candidate (`--network none`, read-only, tmpfs `/tmp`, `--init`): imports ok, `/health` 200; no document converted. Backup `config/.env.bak.before-docling-f6885a55`. Recreated alone.

## Release 023ddcb5 — 2026-10-05 (web low follow-ups, Diary and model-manager UI removal)

No feature flag was changed and `TRUST_PROXY` was not touched. No model run, tune, download, private Diary access or prompt to the Diary.

Exact source `023ddcb5e020d42db7224d58cb2b50ea45f1116b` (main CI green on that commit, all 14 checks). A `git archive` from a throwaway worktree (SHA-256 `eb4c3c8d...`, matched on the server) went to `releases/023ddcb5`. No web dependency file (`package.json`, lockfile) or Diary `requirements.txt`/Dockerfile changed since `c6702509`, so web reused the previous image's `node_modules` and Diary ran no `pip install`. The model-manager `requirements.txt` and Dockerfile did change (dependencies and vendor downloads removed), so that image was a real build.

**Web.** `dist/` was built on the deployment host (`npm ci`, `npm run build` with `STAMP_VERSION=023ddcb5`, in `node:22-bookworm-slim`, 4 GiB cap, from a copy of `apps/web` outside the release dir; the Dockerfile's `node --test` step was not run, CI is authoritative) and layered onto `cowork-web:c6702509` with the same Dockerfile `overlay-release.sh` generates (60 layers, no flattening). That Dockerfile deletes every application-owned entry in `/app/server` (keeping `node_modules` and `ui-data`) and `/app/dist` before copying, so removed files do not linger: `chat-turns.cjs` and `selection-constraint.cjs` are present in `cowork-web:c6702509` and absent in `cowork-web:023ddcb5`. Synthetic candidate check in a throwaway `--network none` container with an empty data dir: `/` 200, `/api/ready` 200 (`version 023ddcb5`), `/api/profile` 401, `chat.cjs`, `projects.cjs`, `public-fetch.cjs` and `llamacpp-tune-spec.cjs` load. Backups: `config/.env.bak.before-023ddcb5`, `docker-compose.yml.bak.before-023ddcb5`, `docker-compose.override.yml.bak.before-023ddcb5`; only `COWORK_VERSION` differs in `.env`. Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`); all three preflight checks passed.

**Diary.** `deploy/examples/diary-overlay.sh 023ddcb5` took appdata backup `ab_20261005_181633` (verified by the script as created by that run), built `cowork-diary:023ddcb5` (`sha256:5b710875...`) `FROM` the running `c6702509` image (`sha256:a6ca877c...`) with `agent/` replaced, passed its candidate import test, recreated only `diary`, and its own checks passed (model-loader unresolvable from Diary, health through web 200). `cowork-diary:c6702509` is retained, and `cowork-diary:rollback-before-diary-overlay` now points at that same image. Backup: `config/.env.bak.before-diary-023ddcb5`. The appdata backup plugin stops and starts web and diary, so web restarted once more (`StartedAt` 22:16:59Z) and came back healthy on `023ddcb5`; that is the only reason web has a second start.

**Model-loader.** First checked read-only (from the web container, token never printed): `/api/v1/downloads` returned no jobs, `activeDownloads` 0, benchmark `idle`, no autotune or calibration activity, llama at 0% CPU. `models.ini` was backed up as `config/llamacpp/models.ini.bak.before-023ddcb5`, `.env` as `config/.env.bak.before-model-loader-023ddcb5`; `cowork-model-loader:023ddcb5` (`sha256:4413c199...`) was built with `MODEL_MANAGER_VERSION=023ddcb5 docker compose build model-loader` from `services/model-manager` (candidate import test passed: `jinja2`, `multipart`, `app/templates` and `/srv/vendor` absent, `app.main` imports), then recreated alone with `up.sh ... --no-build --no-deps --wait --wait-timeout 180 model-loader`.

Rollback, one service at a time. Use `sed` on the single key rather than copying a whole `.env` backup back, because the backups were taken at different points and a whole-file restore would also revert the other services' tags.

## Release c6702509 — 2026-10-05 (web sweep batch, Diary overlay, model-loader image)

No feature flag was changed and `TRUST_PROXY` was not touched. The live `.env` has no `DIARY_SOURCE` key, which the new web requires (it throws at startup for anything but `sidecar`); web started and stayed healthy. No model run, tune, download, private Diary access or prompt to the Diary.

Exact source `c6702509a0358d56808bb10106031a5405b2c931` (main CI green on that commit, all 12 jobs; `d97e6c20`, `b2b5b0a6`, `415c8f0c` and `e11accb1` are ancestors). A `git archive` from a throwaway worktree (SHA-256 `843d2113...`, matched on the server) went to `releases/c6702509`. No dependency file (`package.json`, lockfiles, `requirements.txt`, any Dockerfile) changed since `29732472`/`9debec6`, so web reused the previous image's `node_modules`.

**Web.** `dist/` was built on the deployment host (`npm ci`, `npm run build` with `STAMP_VERSION=c6702509`, in `node:22-bookworm-slim`, 4 GiB cap; the Dockerfile's `node --test` step was not run, CI is authoritative) and `dist/` plus `server/` were layered onto `cowork-web:29732472` (57 layers, no flattening). Synthetic candidate check in a throwaway `--network none` container with an empty data dir: `/` 200, `/api/ready` 200, `/api/profile` 401, and `public-fetch.cjs` and `llamacpp-tune-spec.cjs` load. Backups: `config/.env.bak.before-c6702509`, `docker-compose.yml.bak.before-c6702509`, `docker-compose.override.yml.bak.before-c6702509`; only `COWORK_VERSION` differs in `.env`. Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`); all three preflight checks passed.

**Diary.** `deploy/examples/diary-overlay.sh c6702509` took appdata backup `ab_20261005_141455` (verified by the script as created by that run), built `cowork-diary:c6702509` (`sha256:a6ca877c...`) `FROM` the running `9debec6` image (`sha256:8775aed1...`) with `agent/` replaced, passed its candidate import test, recreated only `diary`, and its own checks passed (model-loader unresolvable from Diary, health through web 200). `cowork-diary:rollback-before-diary-overlay` and `cowork-diary:9debec6` are both retained. Backup: `config/.env.bak.before-diary-c6702509`. The appdata backup plugin stops and starts web and diary, so web restarted once more (`StartedAt` 18:15:21Z) and came back healthy on `c6702509`; that is the only reason web has a second start.

**Model-loader.** First checked read-only (from the web container, token never printed): no download jobs, benchmark idle, `activeDownloads` 0, no autotune or calibration log lines in the last 30 minutes (web had also just restarted). `cowork-model-loader:c6702509` was built with `docker compose build model-loader` from `services/model-manager` (candidate import test passed), `models.ini` backed up as `config/llamacpp/models.ini.bak.before-c6702509`, `.env` as `config/.env.bak.before-model-loader-c6702509`, then recreated alone with `up.sh ... --no-build --no-deps --wait --wait-timeout 180 model-loader`.

Rollback, one service at a time. Use `sed` on the single key rather than copying a whole `.env` backup back, because the three backups were taken at different points and a whole-file restore would also revert the other services' tags.

## Release 29732472 — 2026-10-05 (web: routing modes, flag off)

Reviewed head `f43ee95e` was already up to date with main (0 behind), and CI was green there (10/10). It was squash-merged with `--match-head-commit`, the branch was deleted, and there were no phantom deletions. Dependencies were unchanged since 3e7bbed8. `dist/` and `server/` were built from a `git archive` of `29732472` (`npm ci`, `npm run build` with `STAMP_VERSION=29732472`, in `node:22-bookworm-slim` on the deployment host) and layered onto `cowork-web:3e7bbed8` (54 layers, with the image's `server/node_modules` kept), web only. Synthetic candidate check in a throwaway `--network none` container: unauthenticated `GET` and `PUT /api/routing-mode` returned 401, and `/` and `/api/ready` returned 200. Backup: `config/.env.bak.before-29732472`; only `COWORK_VERSION` differs from it. Web was started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`), and the preflight checks passed.

## Release 3e7bbed8 — 2026-10-04 (web: consistent project chat counts, storage redirect label)

Reviewed head `1e513616` already contained main (0 behind), so no branch update was needed; CI was green there (10/10). It was squash-merged with `--match-head-commit`, the branch was deleted, and there were no phantom deletions. Dependencies were unchanged since 1eb8bbad. `dist/` and `server/` were built from a `git archive` of `3e7bbed8` (`npm ci`, `npm run build` with `STAMP_VERSION=3e7bbed8`, in `node:22-bookworm-slim` on the deployment host) and layered onto `cowork-web:1eb8bbad` (51 layers), web only. Synthetic candidate checks with no network: `storage-login-check-770` and `project-chat-count-768` passed 14/14 in a throwaway candidate container with the candidate `src/`, `tests/` and `typescript` mounted. Backup: `config/.env.bak.before-3e7bbed8`. Web was started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`), and the preflight checks passed. No storage settings were saved or changed on the live server.

## Release 1eb8bbad — 2026-10-04 (web: storage warning wording, project card count)

Reviewed head `bf339c68` already contained main (0 behind), so no branch update was needed; CI was green there (10/10). It was squash-merged with `--match-head-commit`, the branch was deleted, and there were no phantom deletions. Dependencies were unchanged since b653843c. `dist/` and `server/` were built from a `git archive` of `1eb8bbad` (`npm ci`, `npm run build` with `STAMP_VERSION=1eb8bbad`, in `node:22-bookworm-slim` on the deployment host) and layered onto `cowork-web:b653843c` (49 layers), web only. Synthetic candidate checks with no network: `storage-login-check-770` and `project-chat-count-768` passed 11/11 in a throwaway copy of the image with the candidate `server/`, `src/`, `tests/` and `typescript` added. The root `npm ci` lacks `better-sqlite3`, and the image lacks `src/` and `typescript`, so neither runs these alone. Backup: `config/.env.bak.before-1eb8bbad`. Web was started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`), and the preflight checks passed. No storage settings were saved or changed on the live server.

## Release b653843c — 2026-10-04 (web: storage login check)

Reviewed head `3f1e187e` already contained main, so no branch update was needed; CI was green there (10/10). It was squash-merged with `--match-head-commit`, the branch was deleted, and there were no phantom deletions. Dependencies were unchanged since 6f59ba82. `dist/` and `server/` were built from a `git archive` of `b653843c` (`npm ci`, `npm run build` with `STAMP_VERSION=b653843c`) and layered onto `cowork-web:6f59ba82` (43 layers, so no flattening was needed), web only. Synthetic candidate checks: `storage-login-check-770` and `manual-source-sync-toast` passed 9/9 against the archived build. The image has no `typescript`, so that test cannot run inside it. Backup: `config/.env.bak.before-b653843c`. Web was started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`). No storage settings were saved or changed on the live server.

## Release 6f59ba82 — 2026-10-04 (web: tool-layer provenance policy, flag off)

Main had moved 2 commits past reviewed head `578c91de`, so the branch was updated (merge-only, same files as main's delta) to `44827dad`; CI was green there (10/10). It was squash-merged with `--match-head-commit`, the branch was deleted, there were no phantom deletions, and main CI was green on `6f59ba82`. Dependencies were unchanged since 17b477dd. `dist/` and `server/` were built from a `git archive` of `6f59ba82` (`npm ci`, `npm run build` with `STAMP_VERSION=6f59ba82`) and layered onto `cowork-web:17b477dd`, web only. Synthetic candidate checks: the `provenance-policy` and `approval-card-provenance-769` tests passed 17/17 in the build; inside the image with no network, the server provenance tests passed 15/15. Backup: `config/.env.bak.before-6f59ba82`; no appdata backup was run. Web was started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`), and the preflight checks passed.

## Release 17b477dd — 2026-10-04 (web: vault mirror orphan note, skipped list-save ids)

Main had not moved since head `5c0be2d1` (0 behind, CI green), so no branch update was needed. The PR was squash-merged with `--match-head-commit`, the branch was deleted on the remote and locally, and main CI was green on `17b477dd`. Dependencies were unchanged since 25cabfb4. `dist/` and `server/` were built from a `git archive` of `17b477dd` (`npm ci`, `npm run build` with `STAMP_VERSION=17b477dd`) and layered onto `cowork-web:25cabfb4` (37 layers), web only. Synthetic candidate checks ran with no network: locally, `chat-lists-routes`, `routes/chat-lists`, `chat-vault-mirror`, `projects` and `list-save-skipped-765` passed 64/64; inside the image, the server tests passed 62/62. Backup: `config/.env.bak.before-17b477dd`; no appdata backup was run. Web was started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`), and the preflight checks passed.

## Release 25cabfb4 — 2026-10-04 (web: chat lists, suggest rate limit, vault mirror fixes)

Each PR was updated onto main (#763 already current at 281b3832; #762 to 36ee13b9; #761 to 9ea63d34), CI green on the new head, squash-merged with `--match-head-commit`, branch deleted, and main CI green after each merge. Dependencies unchanged since b31d0075. `dist/` and `server/` were built from a `git archive` of `25cabfb4` (`npm ci`, frontend tests, `npm run build` with `STAMP_VERSION=25cabfb4`) and layered onto `cowork-web:b31d0075`, web only. Candidate checked with no network: `chat-framing`, `chat-lists-routes`, `routes/chat-lists`, `chat-vault-mirror` and `projects` tests 76/76. Backup: `config/.env.bak.before-25cabfb4`; no appdata backup run. Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`); preflight checks passed.

## Release b31d0075 — 2026-10-02 (web: each chat as a small brain note, flags off)

Exact source `b31d0075` (squash of PR #751, tested head 455be68b, up to date with main, all CI green; squash-merged with `--match-head-commit`, branch deleted, no phantom deletions). `dist/` and `server/` were built from a `git archive` of that SHA (`npm ci` + `npm run build`, dependencies unchanged) and layered onto `cowork-web:58b4bffb` by hand, web only. Candidate checked with no network: `chat-brain`, `chat-framing` and `chat-vault-mirror` tests 51/51. Backup: `config/.env.bak.before-b31d0075`; no appdata backup run. Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`); all three preflight checks passed.

## Release 58b4bffb — 2026-10-02 (web: per-user chat mirror into the Diary vault, inert)

Exact source `58b4bffb` (squash of PR #748, tested head 3ee31b5 = d46cfb3 updated onto main after #747, all CI re-run green; squash-merged with `--match-head-commit`). `dist/` and `server/` were built from a `git archive` of that SHA (`npm ci` + `npm run build`, dependencies unchanged) and layered onto `cowork-web:23841302` by hand, web only. Backup: `config/.env.bak.before-58b4bffb`; no appdata backup run. Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`); all three preflight checks passed.

## Release 23841302 — 2026-10-02 (web: chat framing phase 5 organise, flag off)

Exact source `23841302` (squash of PR #747; tested head b85b4e0, branch updated onto main as 3af0c64 with an identical diff, all CI re-run green on the fresh base). `dist/` and `server/` were built from a `git archive` of that SHA (`npm ci` + `npm run build`) and layered onto `cowork-web:e5cd0443` by hand, web only. Backup: `config/.env.bak.before-23841302`; no appdata backup run. Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`); all three preflight checks passed.

## Release e5cd0443 — 2026-10-02 (web: chat framing phase 4, flag off)

Exact source `e5cd0443` (squash of PR #746, head 23eaec4, all CI green). `dist/` and `server/` were built from a `git archive` of that SHA (`npm ci` + `npm run build`) and layered onto `cowork-web:fe6fb292` by hand, web only. Backup: `config/.env.bak.before-e5cd0443`; no appdata backup run. Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (absolute `--env-file`); all three preflight checks passed.

## Release fe6fb292 — 2026-10-02 (web: chat framing phase 3, flag off)

Exact source `fe6fb292` (squash of PR #745, head b9157e0, all CI green). `dist/` and `server/` were built from a `git archive` of that SHA (`npm ci` + `npm run build`) and layered onto `cowork-web:90390780` with the overlay Dockerfile steps by hand, web only. Backup: `config/.env.bak.before-fe6fb292`; no appdata backup run (it would stop containers). Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web` (run with the absolute `--env-file` path); all three preflight checks passed.

## Release 90390780 — 2026-10-02 (web: chat framing phase 2 confirm UI, flag off)

Exact source `90390780` (squash of PR #744, head b17944c, all CI green). `dist/` and `server/` were built from a `git archive` of that SHA (`npm ci` + `npm run build`) and layered onto `cowork-web:7635054` (17 layers) with the overlay Dockerfile steps by hand, web only. Backup: `config/.env.bak.before-90390780`; no appdata backup run (it would stop containers). Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web`; all three preflight checks passed.

- **Verify:** web healthy, `RestartCount` 0, `dist/version.json` `0.2.0+muqlizbx`, `index.html` sha256 `11840e8c...` identical to the local build, `chat-framing.cjs` present in the image. All 35 other running containers (sidecars and unrelated) kept ID, StartedAt and restart count; only web changed. Live: `/` 200, `/api/ready` 200, unauthenticated `POST /api/chats/x/move` 401 and `GET /api/chat-framing/preferences` 401, served bundle `index-g3lXclSp.js`. No model run, tune or Diary access.

## Release 7635054 — 2026-10-02 (web: chat framing phase 1, flag off)

Exact source `7635054` (squash of PR #743, head 0a0a80e, all CI green). The web `dist/` and `server/` were built locally from `git archive` of that SHA and layered onto `cowork-web:6d7ae96` (17 layers) with the overlay Dockerfile steps by hand, web only. Backup: `config/.env.bak.before-7635054`; no appdata backup run (it would stop containers). Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web`; all three preflight checks passed.

- **Verify:** web healthy, `RestartCount` 0, `dist/version.json` `0.2.0+muqkih4y`, `index.html` sha256 `63fa58b8...` identical to the local build, `chat-framing.cjs` present in the image. The 12 other containers checked (diary, ocr, llama, model-loader, docling, code-sandbox, code-verify, laya, embed, dav-tailscale, kiwix, cloudflared) kept ID, StartedAt and restart count. Live: `/` 200, `/api/ready` 200, unauthenticated `POST /api/chat-framing/suggest` 401, served bundle `index-FeAYKJ4d.js`. No model run, tune or Diary access.

## Release 6d7ae96 — 2026-10-01 (web: Security hint hidden when the account can't connect)

Exact source `6d7ae96` (CI green on PR #736). Built with `deploy/tools/build-web-release.sh` (stamp check passed). Backups: `config/.env.bak.before-6d7ae96`, `docker-compose.override.yml.bak.before-6d7ae96` and `docker-compose.yml.bak.before-6d7ae96` in the Compose Manager project directory. Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

- **Verify:** web healthy, `RestartCount` 0, `dist/version.json` is `6d7ae96`. The 11 other cowork containers kept ID, StartedAt and restart count (before/after lists in `state/nonweb.{before,after}-6d7ae96.txt`, identical). `https://noevia.example.com/` returned 200 and `/api/profile` 401. The served `index-l3TWrmjh.js` and `index-Dd9SpLmJ.css` exist in the container's `dist/assets`, and the JS contains "only works when your Diary is turned on". Web still listens on 127.0.0.1:8021 and 127.0.0.1:8031. No model run, tune or Diary access.

## Release 448531e — 2026-10-01 (web: Connect a device)

Exact source `448531e` (CI green). Built with `deploy/tools/build-web-release.sh` (stamp check passed). Backups: `config/.env.bak.before-448531e`, `docker-compose.override.yml.bak.before-448531e` and `docker-compose.yml.bak.before-448531e` in the Compose Manager project directory. Started alone with the guarded `up.sh -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

## Release c526350 — 2026-10-01 (code-sandbox image for code-verify, restart-alert tool)

Exact source `c526350` (PR CI green). Backups: `config/.env.bak.before-c526350`, `tools/sidecar-restart-alert.sh.bak.before-c526350`. Started alone with the guarded `up.sh --profile code -- -d --no-build --no-deps --wait code-verify`.

- **Verify:** `code-verify` came up healthy and its startup log has no `EACCES` line. A probe from web (`reachability-probe`, valid nonce) got `not_configured` with the nonce echoed, and the container restarted. Two earlier malformed probes (wrong request shape) were refused and also restarted it, so `RestartCount` went 0 → 4 over four probes (two malformed, two valid, the last one after `--ack`).
- **Restart alert:** after `--ack` and the last probe, a `--dry-run` and a real run were both silent.
- **Snapshot:** 46 containers before and after; the only difference is code-verify (`671bdab4c6c7` → `c54a91c132bd`, new image). All others keep ID, StartedAt and restart count, including the `sg716-*` evaluation containers and `cowork-llama-1`. No model run, tune or Diary access.

## Release 3c7e527 — 2026-10-01 (web, model-loader, code-sandbox, new code-verify)

Exact source `3c7e5277468d50329c20efa7baa70ba51ba4779d` (main CI green, including the `sudo` `code-verify-root.test.cjs` run from #710). The `git archive` of the fresh clone has SHA-256 `119ded8af61ab4ddfed69208c171481fe397908edded4e90098a436e9d4e3efd`, matched on the server, and was extracted to `releases/3c7e527`. The release started after appdata backup `ab_20261001_041001` (plugin log `DONE` at 04:10:18) with all containers back up; no new backup was taken. Backups: `config/.env.bak.before-3c7e527`, `docker-compose.yml.bak.before-3c7e527`, `docker-compose.override.yml.bak.before-3c7e527`. Each service was started alone with the guarded `up.sh ... --no-build --no-deps --wait` (with `--profile code` for the Code services), in this order: model-loader, code-sandbox, code-verify, web.

- **Model manager:** no model was loaded. The start-up migration logged `set an explicit bounded cache-ram in 2 section(s): nomic-embed-text-v1, qwen3-reranker-0.6b-q8_0`. `models.ini` went from `5bd15b66…6173` to `4397b3b32ce00566a8b1fb7154a5d151248a0676640d04a152804cafb18cced5`; the pre-write copy is `models.ini.bak-20261001-084609`. Parsed section by section, the only change is `cache-ram = 0` added to those two sections; the writer also reordered lines and dropped blank lines. The app's `read_ini` reads it (8 sections). Healthy, `/api/v1/health` 200, zero restarts.
- **Code sandbox:** before the recreate, the sandbox ran only `node supervisor.cjs`, with no harness child and no established connection, so no Code task was running. After the recreate: read-only root, `cap_drop ALL`, uid 1000, only on `cowork_code`, listening on 8030, zero restarts.
- **Code verify:**
  - Container settings: `network_mode none` (only `lo`), read-only root, user `0:0` with CapEff `0xc0` (SETUID/SETGID only), NoNewPrivs 1, `group_add` 1005, pids 256, 2 GiB, 2 CPUs, `restart: always`. It mounts workspaces read-only and the socket volume. git runs as `1002:1005` and the test command as `1003:1003`. The socket directory is `root:root 0770` and the socket is `0660`.
  - Log: `listening on /run/noevia-verify/verify.sock (one request) ... 0 repositories configured`.
  - **`CODE_VERIFY` is empty.** `scratch`, the only entry in `CODE_REPOS`, has no `package.json` test script, pytest setup or Makefile; its test is a bare `node test.js`. So no repository has a command, and the pipeline would stop at verify (its flags are off).
- **Synthetic verify:** a throwaway repository `repos/verify-synthetic-3c7e527` (one `test.sh`, group 1005) was checked by a throwaway candidate verifier with the same image and hardening, its own socket volume and `CODE_VERIFY=synthverify|sh test.sh`. The result: `ok:true`, exit 0, nonce echoed, 49 ms. The test ran as uid/gid 1003, the copy was owned by 1002 and read-only to the test, `$TMPDIR` was writable, and the verifier then served its one request and exited. The candidate, its volume and the repository were removed.
- **Web:**
  - Built with `deploy/tools/build-web-release.sh`; the in-build tests and build step passed and the stamp was verified. Standalone loopback candidate: `/` 200, `/api/profile` 401, `version.json` `3c7e527`, 82 dist files.
  - Live: healthy, zero restarts. Public `/` 200, `/api/profile` 401, `/version.json` `3c7e527`. Served `index-Cya8YG3M.js`, `index-Cds-u3b1.css`, `theme.js`, `manifest.webmanifest`, `icon.svg`, `apple-touch-icon.png` and `index.html` are byte-identical to the image `dist`.
  - Mounts: `/llamacpp-config` RW=false, and `/run/noevia-verify` is mounted (the sandbox does not mount it). Web has no `CODE_VERIFY`. The web log shows no errors and no `[inference-budget]` line.
- **Read-only checks through web's modules** (DB opened read-only):
  - Decision deadline is 2000 ms; the budget is 16 GiB.
  - Estimates: `nomic-embed-text-v1` 1.27 GiB (model 0.14 + KV 0.07 + 1 GiB runtime, cache-ram 0) and `qwen3-reranker-0.6b-q8_0` 2.59 GiB (model 0.6 + KV 0.88 + 1 GiB, cache-ram 0). Before #723 each also counted 8 GiB of prompt cache. Chat estimates are unchanged (10.0, 11.15, 9.76, 7.42, 8.5 GiB).
  - `createCodeVerify().available()` is true. One raw probe from web to the live socket (`repo: reachability-probe`) got `not_configured` with the nonce echoed, and the verifier restarted as designed (code-verify RestartCount 1). `sidecar-restart-alert.sh --ack` was run afterwards.

Before/after snapshot of all containers (43 → 44): the only differences are model-loader `d7dda8e7ef3f` → `6a5ac490465a`, code-sandbox `563d1201582b` → `bd58b3d5e66f`, web `8a45208a9b65` → `b7826605665c`, and the new code-verify `671bdab4c6c7`. Llama, embed, diary, docling, laya, ocr, kiwix and every non-noevia container keep the same ID, StartedAt and restart count. There was no model run or tune and no Diary access.

Known follow-ups:
- Every verification restarts `code-verify` by design, so the sidecar restart alert will report each one.
- At each start the verifier logs `could not read /verify/run to sweep it: EACCES`. The server lacks DAC_OVERRIDE and `/verify/run` is 1003's 0700 tmpfs; it is fresh on every restart, so this is harmless.

## Diary overlay 9debec6 — 2026-10-01 (Diary embeds through the `embed` sidecar, #720)

**Parity (#720).** The single-string check of release 9debec6 gave cosine 0.99887, below its 0.999 threshold. The owner delegated the decision, and the broader sample was run with the multi-string `tools/embed-parity-check.cjs` ([#721](https://github.com/sbstndalton/noevia/pull/721)). Before running it, the router had no model loaded. The sample was 40 synthetic documents and 10 synthetic queries, no user data. Results for the router's `nomic-embed-text-v1` (Vulkan) against the `embed` sidecar (CPU, same GGUF, `--pooling mean`): min cosine 0.99863, median 0.99909, mean 0.99913, max 0.99962. Mean overlap@5 was 0.96: 8 of the 10 queries had identical top 5, and the other 2 differed by one document. The rule (min ≥ 0.997, overlap@5 ≥ 0.9) passes, so the vectors are the same model up to float noise and the existing Diary index stays valid without re-embedding. `nomic-embed-text-v1` was unloaded through the router afterwards.

**Deploy.** `diary-overlay.sh` took appdata backup `ab_20261001_024731` (02:47 server time, about 20 s, verified). That backup stopped and restarted web, so web is the same container `8a45208a9b65` with a new StartedAt (06:47:45Z) and zero restarts. The script's candidate imports passed. Diary was recreated alone with the guarded `up.sh ... --no-build --no-deps --wait`; it was healthy and `/api/health` through web returned 200. After the override edit Diary was recreated alone a second time: healthy, zero restarts, container `721fb8e0f26c`.

**Verification.** Diary's own `LLMClient` was built from its live config, without opening the journal or the storage backend. Its embedding client points at `http://embed:8080/v1/`, separate from the engine client, and a synthetic string returned 768 dimensions. A second synthetic call moved the sidecar's slot task id from 90 to 93. Afterwards the router reports `nomic-embed-text-v1` unloaded, and the Diary log has no errors. Llama, model-loader, docling, embed, laya, ocr, code-sandbox and kiwix keep the same IDs and start times. No model run, tune or private Diary access.

## Release 9debec6 — 2026-10-01 (Docling native-text fallback, one model within a 16 GiB inference budget, web)

Exact source `9debec6fb6d591d0821e5c17705480e07a02664c` (main CI green), `git archive` of a fresh clone (SHA-256 `78ae835513949c809fea6b1cb5dc30e6349ccc36c6a7e3442e1333dfb49d3a51`, matched on the server), to `releases/9debec6`. #717 and #718 were merged after this SHA and are not in this release. The last appdata backup before the release was `ab_20260930_041001`; no new backup was started. Backups: `config/.env.bak.before-9debec6`, `docker-compose.yml.bak.before-9debec6`, `docker-compose.override.yml.bak.before-9debec6`. Each service was recreated alone with the guarded `up.sh ... --no-build --no-deps --wait`, in this order: docling, model-loader, llama, web.

- **Docling:** all dependency and model layers came from cache, and the first 10 layers are identical to `2026-09-21`; only the final `COPY` differs. Synthetic selftest, first in a throwaway candidate with `--network none` and then in `cowork-docling-1`: `synthetic-picture-text.pdf` page 1 `native` with the widget-audit text (not `blank`), `synthetic-blank.pdf` `blank`. Healthy, zero restarts.
- **Model manager:** start-up migration logged nothing because all five chat sections already had `cache-ram = 1024` (the 2026-10-01 ops change on #697). `models.ini` is unchanged at `5bd15b66c852affae28976a3685a51551c97b53be2cae359106987fa399b6173`. `/api/v1/health`, `/sections` (8 sections) and `/backends` all return 200, and `/backends` now reports `mem_anon_gb`. Healthy, zero restarts.
- **Embedding parity (`tools/embed-parity-check.cjs`, from the release directory through `cowork-web-1`): FAILED.** Cosine 0.99887 between the router's `nomic-embed-text-v1` (Vulkan) and the `embed` sidecar (CPU, `--pooling mean`), 768 dimensions each, against the 0.999 threshold. So Diary was not switched and its overlay was not shipped. Diary still embeds through the engine, and under `--models-max 1` a Diary embedding request evicts the resident chat model. The `embed` command already had `--pooling mean`, so it was not changed.
- **Llama:** recreated with no model loaded; `nomic-embed-text-v1`, which the parity check had loaded, was unloaded first through the router. Args show `--models-max 1`. Still on `cowork_code`, `cowork_default`, `cowork_models` and `nextcloud-aio`. Healthy, zero restarts.
- **Web:** built with `deploy/tools/build-web-release.sh` (in-build tests and build passed on the first attempt, stamp verified). Standalone candidate on a loopback port with no production mounts: `/` 200, `/api/profile` 401, `version.json` `9debec6`, 82 dist files. Live checks:
  - Healthy, zero restarts. Public `/` 200, `/api/profile` 401, `/version.json` `9debec6`.
  - Served `index-CysxSA0D.js`, `index-DPcIRKIs.css`, `theme.js`, `manifest.webmanifest`, `icon.svg?v=9debec6` and `apple-touch-icon.png?v=9debec6` are byte-identical to the image `dist`.
  - `/llamacpp-config` RW=false. `NOEVIA_FEATURE_RAG_RERANK=false`, and `RERANK_BASE_URL` is absent.
  - Web log has no errors and no `[inference-budget]` line.
- **Budget and decision deadline**, read-only through the settings modules (DB opened read-only):
  - Decision deadline is 2000 ms.
  - Inference budget is 16 GiB (source `deployment`, range 2–25 GiB, host 29 GiB).
  - Chat-model estimates with no model loaded: Qwen3.5-4B 10.0, Qwen3.5-9B 11.15, gemma-3-12b 9.76, gemma-4-E2B 7.42, gemma-4-E4B 8.5 GiB. All fit within 16 GiB.

## Release web c70d1a9 — 2026-09-30 (auto-tune relative quality gate, Tune panel fixes)

Exact source `c70d1a9` (CI green on that commit), `git archive` of a fresh clone, extracted to `releases/c70d1a9`. Built with `deploy/tools/build-web-release.sh` (first attempt, no hang; stamped `c70d1a9`) and started with the guarded web-only `up.sh ... --no-build --no-deps --wait web`. Web healthy, zero restarts, `/` 200 locally and publicly, `/api/profile` 401, `/llamacpp-config` RW=false, public `index-DlCSqcVV.js` and `index-CHiiGa9G.css` byte-identical to the container. Every other container kept its ID, `StartedAt` and restart count. Stored decision deadline read back read-only through the settings module: 2000 ms. No model run, tune or Diary access.

## Release 53da4ce — 2026-09-30 (web + Laya: configurable decision deadline)

Exact source `53da4cee498d4b973024c332935aca9540b00175` (CI green on that commit), `git archive` of a fresh clone, extracted to `releases/53da4ce`. The running Laya was actually `cowork-laya:0.3.5-recovery-2ffd153` (the worker-recovery build), not `noevia1`; `noevia2` uses the same pattern (`FROM cowork-laya:0.3.5-noevia1` plus `services/laya/server.py` from the release), so dependencies and model files are unchanged and the recovery behaviour is kept. Laya was recreated alone with the guarded `up.sh --profile laya --no-build --no-deps --wait laya`: healthy, zero restarts, `/health` 200, no `LAYA_DECISION_TIMEOUT_S` warning in its log (the service logs only on a refused value), `LAYA_DECISION_TIMEOUT_S=1.8` present in the container environment.

Web was built with `deploy/tools/build-web-release.sh` (first attempt hung in the in-build Vite test `request-cache-cap.test.cjs` for 27 minutes on an I/O-loaded host and was killed before any cutover; the rerun passed) and started with the guarded web-only `up.sh`. Web healthy, zero restarts, `/` 200, `/api/profile` 401, `/llamacpp-config` RW=false, served `index-*.js` and `index-CHiiGa9G.css` byte-identical to the container. Every other container kept its ID, `StartedAt` and restart count.

Web decision deadline: stored `decision:configuration` changed from 1500 to 2000 ms (URL unchanged) through `createDecisionSettings().save` against the app's own settings store. The running process caches the value at startup, so web was restarted once afterwards and reads back 2000. Zero supervise records since the restart at the time of writing.

## Release web 2c1aee7 — 2026-09-30 (Create-project dialog files stored in connected storage)

Exact source `2c1aee79436f1f8140b4f015345516820dfe71f0`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `488ce821357c739a4714c6fe8bd0e49b96bb19655b4ed434e0fe30e6c5602d48`, matched on the server), to `releases/2c1aee7`. Main CI on `2c1aee7` was green before cutover. Web was built with `deploy/tools/build-web-release.sh 2c1aee7 apps/web` (stamp verified). `COWORK_VERSION` set to `2c1aee7` (`.env.bak.before-2c1aee7` kept).

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, targeting `web` only.

Checks: web healthy, zero restarts; zero error markers in web logs; `/llamacpp-config` RW=false; public root 200, `/api/profile` 401; the served `index-D3jigXrH.js` and `index-CHiiGa9G.css` are byte-identical to the image `dist`. Before/after snapshot of all 34 running containers (id, StartedAt, restart count): the only difference is the recreated web container (started 2026-09-30T10:18:19Z). Snapshots kept as `snap-before-2c1aee7.txt` / `snap-after-2c1aee7.txt`; older `.snap-*-92dfd2a` and `snap/*b4bed07*` files removed.

---

## Release web 92dfd2a — 2026-09-30 (Auto-tune link in Advanced mode, System-One gate fits Laya limits, reload mid-reply keeps the turn)

Exact source `92dfd2af56947c0aad314230c8c22c1d0e6287dd`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `5bf46b606d14b3eb3c259a98f9c876a7467286c91fd1d762c70a1bd3fa3d3622`, matched on the server), to `releases/92dfd2a`. Main CI on `92dfd2a` was green before cutover. Web was built with `deploy/tools/build-web-release.sh 92dfd2a apps/web` (stamp verified). `COWORK_VERSION` set to `92dfd2a` (`.env.bak.before-92dfd2a` kept).

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, targeting `web` only.

Checks: web healthy, zero restarts; zero error markers and no `[system-one]` lines in web logs; `/llamacpp-config` RW=false; public root 200, `/api/profile` 401; the served `index-JW8NVv0e.js` and `index-CHiiGa9G.css` are byte-identical to the image `dist`. Before/after snapshot of all 34 running containers (id, StartedAt, restart count, image): the only difference is the recreated web container (started 2026-09-30T09:43:46Z). `system-one-decisions.jsonl` had no records appended since cutover (no `cause` records yet); the new `cause` field is not yet exercised live.

---

## Release web b4bed07 — 2026-09-30 (provider capabilities are data, roles renamed Planner/Executor/Laya/Auditor, plannerReview flag)

Exact source `b4bed07d4b217ce51f6e5a4c6c71fb047cb3e194`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `2527bab6065aa451f203a36270abf30ebefaa2a4cbb74084410207b6e02c124c`, matched on the server), to `releases/b4bed07`. Main CI on `b4bed07` was green before cutover. Web was built with `deploy/tools/build-web-release.sh b4bed07 apps/web` (stamp verified). `.env` did not set `NOEVIA_FEATURE_ASTRA_REVIEW`, so no `NOEVIA_FEATURE_PLANNER_REVIEW` line was added. `COWORK_VERSION` set to `b4bed07` (`.env.bak.before-b4bed07` kept).

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, targeting `web` only.

---

## Release web b6fda27 — 2026-09-29 (model-loader is the models.ini writer, read-only preset mount, declined-write note, auto-tune arithmetic replies, Diary retry records)

Exact source `b6fda2728bbe90176a79f9d42439aa0d732087fc`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `049147c6b14935184a9a0d5a8145ba67b7c188861d3e8e6aafa645d03dd74964`, matched on the server), to `releases/b6fda27`. Main CI on `b6fda27` was green before cutover. Web was built with `deploy/tools/build-web-release.sh b6fda27 apps/web` (stamp verified).

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, targeting `web` only.

---

## Release web 4dc8ccf — 2026-09-29 (storage edit messages, no retry of conditional writes, phone chat header, unit wording, write-safety cards)

Exact source `4dc8ccf00e9a9fad66b76937eaf2b90db24ddbd0`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `a400a24024010fc9b7796b28ab75478c5c2a36fdc3a6447ba74d59827243e006`, matched on the server), to `releases/4dc8ccf`. #663 had all checks green (head `4f1a695`) before its squash merge as `4dc8ccf`, and main CI on `4dc8ccf` was green before cutover. Web was built with `deploy/tools/build-web-release.sh 4dc8ccf apps/web` (stamp verified). Standalone web candidate on a loopback port with no production mounts and a synthetic token: `/` 200, `/api/profile` 401, `/api/auth/device/code` 404, `version.json` `4dc8ccf`, 82 dist files.

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, targeting `web` only; `.env` and the Compose YAMLs were backed up as `*.bak.before-4dc8ccf`. The restart-alert baseline was re-acked.

Checks: web healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/api/auth/device/code` 404, `/version.json` `4dc8ccf`; all 82 files served publicly are byte-identical to the image `dist`; web logs clean. `astraReview`, `constrainedPlanDecoding` and `nativeClientAuth` are off (no `NOEVIA_FEATURE_*` override set for them, defaults apply; the device-code route returns 404).

---

## Release web ffdcd9b — 2026-09-29 (project tools edit uploads in place, phone-preview stacking, Code header inset, French wording, byte plural)

Exact source `ffdcd9b6da2f91d46138ff7911bab9da41813708`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `b16d8abe82130fb21571dbb8cef1c368bdabe39850439c325cb55a8e9079ab19`, matched on the server), to `releases/ffdcd9b`. Both PRs had all checks green before their squash merges (#654 as `3b1443c`, then #656 as `ffdcd9b`, still MERGEABLE after #654), and main CI on `ffdcd9b` was green before cutover. Web was built with `deploy/tools/build-web-release.sh ffdcd9b apps/web` (stamp verified). Standalone web candidate on a loopback port with no production mounts and a synthetic token: `/` 200, `/api/profile` 401, `/api/auth/device/code` 404, `version.json` `ffdcd9b`, 82 dist files.

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, targeting `web` only; `.env` and the Compose YAMLs were backed up as `*.bak.before-ffdcd9b`. The restart-alert baseline was re-acked.

Checks: web healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/api/auth/device/code` 404, `/version.json` `ffdcd9b`; all 82 files served publicly are byte-identical to the image `dist`; web logs clean. `astraReview`, `constrainedPlanDecoding` and `nativeClientAuth` are off (no `NOEVIA_FEATURE_*` override set for them, defaults apply; the device-code route returns 404).

---

## Release web 6e7eeba — 2026-09-29 (project files by bare name, phone-preview drawer, English size sentences, Auto label, timer start)

Exact source `6e7eebad39f312663f09742f727bbb97e3117480`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `b83aad0fac80a42407a31a58c0cfbf260f632c3bbdc1441697751298cfd05e59`, matched on the server), to `releases/6e7eeba`. Both PRs had all checks green before their squash merges (#646 as `eeafa4b`, then #647 as `6e7eeba`, still MERGEABLE after #646), and main CI on `6e7eeba` was green before cutover. Web was built with `deploy/tools/build-web-release.sh 6e7eeba apps/web` (stamp verified). Standalone web candidate on a loopback port with no production mounts and a synthetic token: `/` 200, `/api/profile` 401, `/api/auth/device/code` 404, `version.json` `6e7eeba`, 82 dist files.

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, targeting `web` only; `.env` and the Compose YAMLs were backed up as `*.bak.before-6e7eeba`. The restart-alert baseline was re-acked.

Checks: web healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/api/auth/device/code` 404, `/version.json` `6e7eeba`; all 82 served asset files byte-identical to the image `dist`; web logs clean. `astraReview`, `constrainedPlanDecoding` and `nativeClientAuth` are off (no `NOEVIA_FEATURE_*` override set for them, defaults apply).

---

## Release web 5e904b7 — 2026-09-29 (remaining English and de/fr wording, composer toolset names, Stopped placeholder, French byte units, Diary phone preview)

Exact source `5e904b731d194fad472cf2003bd9db859717f6e7`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `8db76c9eca25c4ed1d87280fe5283cd84464b34136436664d4bcede324060b62`, matched on the server), to `releases/5e904b7`. #639 had all checks green before its squash merge, and main CI on `5e904b7` was green before cutover. Web was built with `deploy/tools/build-web-release.sh 5e904b7 apps/web` (stamp verified). Standalone web candidate on a loopback port with no production mounts: `/` 200, `/api/profile` 401, `/api/auth/device/code` 404, `version.json` `5e904b7`.

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, targeting `web` only; `.env` and the Compose YAMLs were backed up as `*.bak.before-5e904b7`. The restart-alert baseline was re-acked.

Checks: web healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/api/auth/device/code` 404, `/version.json` `5e904b7`; all 82 served asset files byte-identical to the image `dist`; web logs clean. `astraReview`, `constrainedPlanDecoding` and `nativeClientAuth` are off (no `NOEVIA_FEATURE_*` override set for them, defaults apply).

---

## Release web 3007ae5 — 2026-09-29 (toolbox and chat chrome translations, offsite-backup qa, hardware answer, phone theme cards)

Exact source `3007ae57e5a12a64f35691d3bdf99c778a634581`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `f755634cb10c7538d46a1533db243cb1af29f47e84bb514cbdaefcccae6fe3aa`, matched on the server), to `releases/3007ae5`. Both PRs had all checks green before their squash merges (#631 as `7ef30f6`, then #632 as `3007ae5`, still MERGEABLE after #631), and main CI on `3007ae5` was green before cutover. Web was built with `deploy/tools/build-web-release.sh 3007ae5 apps/web` (stamp verified). Standalone web candidate on a loopback port with no production mounts: `/` 200, `/api/profile` 401, `/api/auth/device/code` 404, `version.json` `3007ae5`, 82 dist files.

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, targeting `web` only; `.env` and the Compose YAMLs were backed up as `*.bak.before-3007ae5`. The restart-alert baseline was re-acked.

Checks: web healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/api/auth/device/code` 404, `/version.json` `3007ae5`; all 82 served asset files byte-identical to the image `dist`; web logs clean. `astraReview`, `constrainedPlanDecoding` and `nativeClientAuth` are off (no `NOEVIA_FEATURE_*` override set for them, defaults apply).

---

## Release web a8a953a — 2026-09-29 (Code landing, admin Settings and Diary calendar localised, round-7 leftovers)

Exact source `a8a953a8e3fd43a1eafeafeec211b3af62a1fb0c`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `8edeea548fae661c5bf03ff5a40a4ca3562deeb31746ec2ddb5cc69cf89dbe27`, matched on the server), to `releases/a8a953a`. Both PRs had all checks green before their squash merges (#622 as `ecc0975`, then #621 as `a8a953a`, still MERGEABLE after #622), and main CI on `a8a953a` was green before cutover. Web was built with `deploy/tools/build-web-release.sh a8a953a apps/web` (stamp verified). Standalone web candidate on a loopback port with no production mounts: `/` 200, `/api/profile` 401, `version.json` `a8a953a`, 82 dist files.

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, targeting `web` only; `.env` and the Compose YAMLs were backed up as `*.bak.before-a8a953a`. The restart-alert baseline was re-acked.

Checks: web healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/api/auth/device/code` 404, `/version.json` `a8a953a`; all 82 served asset files byte-identical to the image `dist`; web logs clean. `astraReview`, `constrainedPlanDecoding` and `nativeClientAuth` are off (no `NOEVIA_FEATURE_*` override set for them, defaults apply).

---

## Release web + model-loader 381760c — 2026-09-29 (round 6 fixes, stopped-backend uptime, field ids)

Exact source `381760c3b1d58724c06bd8de61a6b7a86501cbec`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `7b80192f8d851a10a576c595945fbbf8efe63f958d0ed4bdba71d2b5af672229`, matched on the server), to `releases/381760c`. PR #611 (head `238aaab`) had all checks green before the squash merge, and main CI on `381760c` was green before cutover. Web was built with `deploy/tools/build-web-release.sh 381760c apps/web` (stamp verified). Standalone web candidate on a loopback port with no production mounts: `/` 200, `/api/profile` 401, `version.json` `381760c`, 82 dist files. Model-loader candidate: `app.api/main/discover/services` import cleanly.

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, one service at a time (`web`, then `model-loader`); `.env` and Compose YAMLs were backed up as `*.bak.before-381760c`. The restart-alert baseline was re-acked.

Checks: web and model-loader healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/api/auth/device/code` 404, `/version.json` `381760c`; all 82 served asset files byte-identical to the image `dist`; web and model-loader logs clean. `astraReview`, `constrainedPlanDecoding` and `nativeClientAuth` are off (no `NOEVIA_FEATURE_*` override set, defaults apply). Model-loader `/api/v1/health` 200; `/api/v1/backends` reports `uptime_s` 10256 and 14832 for the two running backends and `null` for the exited `llama-vulkan-test`; the `/api/v1/sections` schema carries `id` on all 98 fields (read from inside the web container with the token header). This closes [#603](https://github.com/sbstndalton/noevia/issues/603).

---

## Release web + model-loader 435ba54 — 2026-09-29 (locale gaps, backend uptime_s, tierId)

Exact source `435ba5419f2b448f8d78a208bbe58b474888aee7`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `366325c94b60002e4bc7fd43f03ff13875b72a103bbcf676198a0aa60fbf7413`, matched on the server), to `releases/435ba54`. All PR #599 checks were green before the squash merge. Web was built with `deploy/tools/build-web-release.sh 435ba54 apps/web` (stamp verified). Standalone web candidate on a loopback port with no production mounts: `/` 200, `/api/profile` 401, `version.json` `435ba54`, 82 dist files. Model-loader candidate: `app.api/main/discover/services` import cleanly.

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180`, one service at a time (`web`, then `model-loader`); `.env` and Compose YAMLs were backed up as `*.bak.before-435ba54`. The restart-alert baseline was re-acked.

Checks: web and model-loader healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/api/auth/device/code` 404, `/version.json` `435ba54`; 53 served asset files (including `index-*.js`/`index-f8aq2N0j.css`, `theme.js`, `lens.js`, `glass-highlight.js`) byte-identical to the image `dist`; web and model-loader logs clean. `astraReview`, `constrainedPlanDecoding` and `nativeClientAuth` are off. Model-loader `/api/v1/health` 200, `/api/v1/backends` includes `uptime_s` for every backend, and the `/api/v1/sections` schema carries `tierId` on all 10 tiers (read from inside the web container with the token header). Follow-up: [#603](https://github.com/sbstndalton/noevia/issues/603) (exited backends report an uptime).

---

## Release web ef6a83f — 2026-09-29 (unreadable sources excluded, Sources typography, lazy project folders)

Exact source `ef6a83fc4d42742f85ca73528f4e8a74c92ccf00`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `542b546ae96a41fb119a467f1d64bc2899cac6cd07b587e47c93b9ebeb3a923b`, matched on the server), to `releases/ef6a83f`. Main CI on that SHA was green. Web was built with `deploy/tools/build-web-release.sh ef6a83f apps/web` (stamp verified). Standalone candidate on a loopback port with no production mounts: `/` 200, `/api/profile` 401, `version.json` `ef6a83f`.

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180 web`; `.env` and Compose YAMLs were backed up as `*.bak.before-ef6a83f`. The restart-alert baseline was re-acked.

Checks: web healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/version.json` `ef6a83f`; served `index-BK7x-LxY.js`, `index-f8aq2N0j.css`, `theme.js`, `lens.js` and `glass-highlight.js` byte-identical to the image `dist`; web logs clean. `/api/auth/device/code` returns 404. `astraReview`, `constrainedPlanDecoding` and `nativeClientAuth` are off.

---

## Release web a70f5a0 — 2026-09-29 (locale-aware model numbers; native-client device sign-in, flag off)

Exact source `a70f5a0ee7c5c974ac0dbdf5593c8a88c7d61ae7`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `72ebf8f4fd7ca25ea95715470382e5470500535c014bcf9b5cf9c416dcad04ed`, matched on the server), to `releases/a70f5a0`. Main CI on that SHA was green. #591 was merged first after all its checks passed. Web was built with `deploy/tools/build-web-release.sh a70f5a0 <context>` (stamp verified). Standalone candidate on a loopback port with no production mounts: `/` 200, `/api/profile` 401, `version.json` `a70f5a0`, 68 asset files.

Cutover used the guarded `up.sh` with `--no-build --no-deps --wait --wait-timeout 180 web`; `.env` and Compose YAMLs were backed up as `*.bak.before-a70f5a0`. The restart-alert baseline was re-acked.

Checks: web healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/version.json` `a70f5a0`; served `index-BnZjcwNG.js`, `index-DSXrbO3N.css`, `theme.js`, `lens.js` and `glass-highlight.js` byte-identical to the image `dist`; web logs clean and the three `device_*` tables (plus indexes) exist. `/api/auth/device/code` returns 404 (flag off). `astraReview` and `constrainedPlanDecoding` off, `nativeClientAuth` and `browserExecutor` unavailable.

---

## Release web + model-loader b8755fb — 2026-09-28 (md uploads, model-switch race, embed loaded model, delete guard; preflight wrapper refreshed)

Exact source `b8755fb120de140606b66be0fec18a31d8a253ff`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `823022895659ed0faa359de2b2ddbd63034f9d59f734bb9f1820b3025ff0a566`, matched on the server), to `releases/b8755fb`. PR #583 was merged first after all its checks passed. Web was built with `deploy/tools/build-web-release.sh b8755fb <context>` (stamp verified by the script); model-loader from `services/model-manager`. `test_check.php` passes on the server; `test_wrapper.py` could not run there (no python3 on the host) and passed in CI. Candidates: web standalone `/` 200, `/api/profile` 401, `version.json` `b8755fb`, 65 asset files; model-loader `app.api/main/discover/services` import cleanly.

Cutover used the refreshed guarded `up.sh`, one service at a time (`web`, then `model-loader`), each with `--no-build --no-deps --wait --wait-timeout 180`. It was run from `/` and worked, which confirms the cwd-independent project lookup from #575. It re-acked the restart-alert baseline.

Checks: web and model-loader healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/version.json` `b8755fb`, served `index-B10eD_gz.js`, `index-NW1foXSN.css`, `theme.js`, `lens.js` and `glass-highlight.js` byte-identical to the image `dist`; web and model-loader logs clean. `astraReview` and `constrainedPlanDecoding` false, `browserExecutor` false and unavailable (no Playwright in the image); `nativeClientAuth` is not in the feature registry. Model-loader `/api/v1/health` 200; `/api/v1/backends` lists `cowork-embed-1` running with loaded model `nomic-embed-text-v1` (#580) and llama running `gemma-4-E2B_q4_0-it`. Delete guard, read-only check (nothing deleted): `model_holders` on the `nomic-embed-text-v1` entry returns `cowork-embed-1 (its command runs nomic-embed-text-v1/nomic-embed-text-v1.Q8_0.gguf)` plus `cowork-web-1 (EMBEDDING_MODEL is set to nomic-embed-text-v1)`.

---

## Release web + model-loader 682a45e — 2026-09-28 (embed status, Browser-mode flag, model-loader rope fixes, live round 2 fixes; embed on the models network)

Exact source `682a45e7c5b9696e3854d02fa672052179230658`, `git archive` of a fresh clone of `origin/main` (archive SHA-256 `62e777b19247d79aa377ba77185e4016fc056f2658143ee4a8ce8c676b67536d`, matched on the server), to `releases/682a45e`. PR #570 was merged first after all its checks passed. Web was built from `apps/web` with the repo Dockerfile and **`--build-arg COWORK_VERSION=682a45e`**; without the build arg `dist/version.json` says `0.2.0+<hash>` (the first build had this and was replaced before cutover). Model-loader was built from `services/model-manager`. Candidates: web standalone returned `/` 200, `/api/profile` 401, `version.json` `682a45e`, 65 asset files; model-loader `app.api/main/services/discover` import cleanly.

Checks: web healthy, zero restarts; public root 200 three times, `/api/profile` 401, `/version.json` `682a45e`, served `index-ChIYCx9M.js` and `index-CmIqOpBa.css` byte-identical to the image `dist`; web and model-loader logs clean (MCP discovery only). `astraReview`, `constrainedPlanDecoding` and `browserExecutor` all report false. Model-loader healthy, zero restarts; `/api/v1/health` 200; `/api/v1/sections` and `/api/v1/backends` return 200 from inside the web container using the `X-Model-Loader-Token` header (token never printed); backends lists `cowork-embed-1` as running, no "connection refused". Embed recreated on both `cowork_default` and `cowork_models`, healthy, zero restarts (its old restart count was 4463); `POST http://embed:8080/v1/embeddings` from web returns a vector and model-loader reaches `embed:8080/health` (200).

models.ini (#568): backed up as `models.ini.bak.20260928-214146-before-568`, then exactly `rope-scaling = linear` and `rope-scale = 8.0` removed from `[gemma-3-12b-it-qat-Q4_0]`; no duplicate section names. `cowork-llama-1` was deliberately **not restarted** (owner offline), so its running 12B args still reflect the old file until the next restart; the file itself is fixed.

---

## Release web 349a450 — 2026-09-28 (sampling recommendations, Skills revocation, Astra review behind a flag)

Includes the optional llama.cpp constrained-decoding module for the plan artifact (#517, flag reports unavailable), the web to model-loader `/api/v1` contract doc and tests (#269), per-model sampling recommendations and the auto-tune Sampling phase with i18n (#308), in-flight Skills revocation and web pinning (#272), and the Astra review step in Code mode (#519, `NOEVIA_FEATURE_ASTRA_REVIEW`, default off). The persona-swap experiments harness (#518) is not part of the image. No feature flag was set or changed.

Exact source `349a45080fa1514281d14759630e46134941954d`, archived from a fresh clone of `origin/main` (archive SHA-256 `2aff03974eeb5c22d4fbf2d29cdfa08db4fcda5df08f94ce56f16ea79b977f88` matched locally and on the server). Lockfiles were unchanged since `ad71baf`. The image was built from the release directory with the repository Dockerfile (the in-build unit tests ran and passed; `npm ci` was cached), tagged `cowork-web:349a450`, image `sha256:f3916685fcb8a30d71c88c9bc69be264a07bf6e8c2dc0a3f2038399b461ba5f6`. A network-disabled candidate container reported version `349a450`, `/api/profile` 401, `dist/index.html` plus 65 asset files, and both `server/sampling-recommendation.cjs` and `server/code-review.cjs` present before cutover.

Web is healthy with zero restarts, started `2026-09-29T00:20:10Z`. Public root returned 200 three times, unauthenticated `/api/profile` returns 401 and `/version.json` says `349a450`. The served `index-BTdwnJ6-.js` and `index-sYzZaw8b.css` exist in the image `dist/assets`. Web logs since start are clean (MCP discovery only). In the container `astraReview` and `constrainedPlanDecoding` both report false. A before/after snapshot of the 42 non-web containers (id, StartedAt, restart count, image) is identical, including the known embed crash loop (#336). The restart-alert baseline was re-acked by `up.sh`. No model runs, tune, private Diary access or new harness installation.

Rollback: restore `config/.env.bak.before-349a450`, point `current` at `releases/ad71baf`, and use the installed web-only no-build preflight. Previous releases, images (`cowork-web:ad71baf`) and the Compose Manager backups `docker-compose.yml.bak.before-349a450` and `docker-compose.override.yml.bak.before-349a450` remain available.

## Release web ad71baf — 2026-09-28 (provider edit in place and hosted context size)

Providers can be edited in place, and a hosted provider can state its context size (whole tokens, 2048 to 2,000,000). Closes #535 and #536. Server and frontend only.

Exact source `ad71baf1fb299f250ad9f673a063052216ecd43d`. A candidate check in the built image returned `parseContextTokens('65536')` = `{value:65536}` before cutover. Web is healthy with zero restarts, started `2026-09-28T22:28:36Z`, image `sha256:b2a07e0b6ff0`. Public root returns 200 and unauthenticated `/api/profile` returns 401. The served `index-YXY0J30A.js` and `index-PT_ypkNu.css` exist in the image `dist/assets`. Saved providers were preserved: the shared file still holds the default and NVIDIA Build rows (ids unchanged), and the server workspace module loads both from a copy of the file without printing keys. Non-web containers kept their IDs and start times; the only change is the known embed crash loop (#336), which is unrelated. No model runs.

Rollback: restore `config/.env.bak.before-ad71baf`, point `current` at `releases/0f5d9f2`, and use the installed web-only no-build preflight. Previous releases, images and the Compose backup `docker-compose.yml.bak.before-ad71baf` remain available.

## Release web 0f5d9f2 — 2026-09-28 (NVIDIA Build provider preset)

Adds an NVIDIA Build (free trial) provider preset. Egress rules classify a provider as external by its URL, so `https://integrate.api.nvidia.com/v1` is treated as an external provider while local endpoints stay internal. Server and frontend only.

Exact source `0f5d9f22ad0f0c9368c7b182852f722c5c29be5a`; all PR #534 CI checks were green. Archive SHA-256 `1b9fb96cbad6c4132c930532533f862483fcbcde401917d69320529a41879de9` matched locally and remotely. A network-disabled candidate container returned `isExternalProvider` true for the NVIDIA URL and false for a local llama URL before cutover.

Web is healthy with zero restarts, started `2026-09-28T22:05:11Z`, image `sha256:218f617c8a74`. Public root returns 200 and unauthenticated `/api/profile` returns 401. The served `index-CDPEbze5.js` and `index-DblQT3ZR.css` exist in the image `dist/assets`. The in-container check returned true for the NVIDIA URL. All non-web container IDs, start times and restart counts were unchanged except the known embedding crash loop (already at 4,361 restarts before the release, 4,371 after). No sidecar, model, tune, private Diary access or real provider request was performed.

Rollback: restore `config/.env.bak.before-0f5d9f2`, point `current` at `releases/8f92a01`, and use the installed web-only no-build preflight. Previous releases, images and the Compose backup `docker-compose.yml.bak.before-0f5d9f2` remain available.

## Release web ab70db5 — 2026-09-28 (portable Skills contract and sampling provenance)

Projects expose portable Skill manifests and an exact-version content read while retaining the existing Sources review UI contract. Tenant ownership, reviewed/enabled state, stale-version rejection and core tool approvals remain enforced. Source sampling recommendations now come from a bounded, commit-pinned `generation_config.json` fetch and carry provenance and artifact scope. They are reported metadata only, without a new UI, automatic application or model qualification. #272 and #308 remain open for their later client/invocation and sampling-quality work.

Exact source `ab70db58f664cf85562c93daa302f8d9392ae57b` passed 2,528 combined tests with no failures or skips, typecheck, production build and design lint. The individual slices also passed synthetic tenant-isolation HTTP checks and source-removal/artifact-staleness checks. Both PRs passed root exact-SHA reviews before push and merge plus all CI checks. Archive SHA-256 matched locally/remotely: `d5fe9581460954c1eeda974903afbdb8623230cc9d870eb8a44ab04e7dc60762`.

Web is healthy with zero restarts, started at `2026-09-28T02:26:31.396294407Z`. Public root returns 200, unauthenticated profile and new API routes 401, version `ab70db5`; `index-DRDnsqcu.js` and `index--htmrLTo.css` return 200 and exist in the image. The deployed server contains both new API implementations. Available memory remained about 9.0 GiB. All non-web IDs/images remained unchanged; all start times/restart counts stayed unchanged except the known missing-GGUF embedding crash loop (#336), from 3,198 to 3,199. No sidecar, model, corpus, preset or tuning action was performed.

Dedicated Luna Chrome verification, reviewed by root, confirmed the deployed version and rendered authenticated desktop shell and Appearance settings in its own tab. Logo colors remained Default leaves; no preferences, native selector options or palette test were changed. The owned tab was closed and the user’s existing tab left untouched. Mobile-specific rendering and physical Safari were not re-verified for this backend-only release.

Rollback: restore `config/.env.bak.before-ab70db5`, point `current` at `releases/b272746`, and use the installed web-only no-build preflight. Previous releases, images and Compose backups remain available.

## Release web b272746 — 2026-09-28 (calendar logo and tuner answer handling)

Appearance now offers per-device default, seasonal and monthly logo palettes, with an explicit hemisphere choice. Default geometry and favicon stay unchanged. The admin preview cycles palettes temporarily and clears when leaving Appearance. GPT-OSS quality probes request low reasoning effort with a bounded answer budget; strict final-answer scoring accepts harmless formatting wrappers but rejects empty or reasoning-only responses. Throughput probes retain their separate handling of capped output. No live tune or model inference was run.

Exact source `b272746d00217f88025809ebcaadae8c6b331310` passed 2,517 combined tests with no failures or skips, typecheck, build and design lint. Logo synthetic browser coverage passed 507 assertions across 1440/768/390 widths, light/dark, all three themes, admin/member, persistence and preview cleanup. Both PRs passed CI and root exact-SHA reviews. Source archive SHA-256 matched locally and remotely: `fb435cbc500dd0e1dbbf906a3fdb3d5c9717805d23cd76eac272ade9f3979c52`.

Web is healthy with zero restarts, started at `2026-09-28T02:11:30.068581928Z`. Public root returns 200, unauthenticated profile 401, version `b272746`; `index-DrBXtR_7.js` and `index--htmrLTo.css` return 200 and exist in the image. Available memory remained about 9.3 GiB. Every non-web container retained its ID and image. Start times and restart counts also stayed unchanged except the existing embedding crash loop: its count advanced from 3,183 to 3,184 while the same container reported its missing Nomic GGUF (#336). Embedding recovery was not attempted.

Dedicated Luna Chrome verification observed the deployed version and authenticated desktop Appearance controls: Default leaves, Test next palette, and the preview-only explanation. The user supplied a screenshot confirming the native macOS menu displays Default leaves, Seasonal and Monthly; the open popup is confirmed by that screenshot rather than an agent capture. No preference or palette test was changed. Current-release mobile verification and physical Safari remain unverified; synthetic responsive coverage is recorded separately above.

Rollback: restore `config/.env.bak.before-b272746`, point `current` at `releases/c90046e`, and use the installed web-only no-build preflight. Prior releases, images and Compose backups remain available.

## Release web c90046e — 2026-09-28 (server memory recovery and sidebar corrections)

The host had about 2.3 GiB available while two chat-model children held about 14.3 GiB of GPU-backed system memory, largely absent from Docker's memory display. Both reported no active or deferred requests; the 9B child also reported zero processed prompt/generated tokens. Rechecking those idle gauges and gracefully unloading that child raised available memory to about 9.7 GiB and reduced GTT from 15.3 GB to 7.7 GB. The 4B child remained loaded. This establishes the source of the current pressure, not the sole cause of the earlier OOM incident.

Web-mediated native model admission now serializes eviction/loading, verifies successful eviction, and refuses a conflicting load. This does not impose a host-wide memory limit on other router clients. The release also versions the core browser API contract, reduces static Brotli warmup cost, fixes Chat/Code selection shape and hidden-drawer indicator geometry, and keeps sidebar rows above the account footer without opaque heading bands.

Exact source: `c90046e29407e6d6be01e97db706d1e533248ca1`. Required local verification passed: 2,508 tests, typecheck, production build, design lint, 206 sidebar checks, 416 mode-switch checks, and existing phone drawer/settings QA. An initial performance timing assertion failed under heavy concurrent load; the bounded full rerun passed without changing that assertion. All PR CI checks passed, including the image build. Deployment required more than 8 GiB available before building; archive SHA-256 matched locally/remotely (`20f85743cb095fdfe00f28d8e7dba059d5d38afc857d72523b3c0fa0756b09d1`).

Verified `current` → `releases/c90046e`, healthy web with zero restarts, public root 200, unauthenticated profile 401, version c90046e, and served `index-BARUzto6.js` / `index-CeuNTAQ0.css` both 200 and present in the image. Every non-web container retained its ID, start time, image and restart count. Available memory remained about 9.7 GiB after deployment. Environment and Compose backups are retained as `*.bak.before-c90046e`.

Dedicated Luna live Chrome verification was dispatched immediately after activation and reviewed by root. Desktop Chat → Code → Chat, rounded inset selection and separate sidebar footer passed in the current Contemporary dark/sage theme. Mobile Chrome emulation reached 393×852, but CUA input timed out before the navigation drawer opened; live mobile drawer behavior remains unverified. Root corrected the report’s unsupported inference that Chat/Code was absent on mobile. Synthetic mobile coverage above remains separate. Physical Safari and real inference were not tested.

Rollback: point `current` at `releases/7a3f736`, restore `config/.env.bak.before-c90046e`, and run the same installed web-only no-build preflight. Model files were not changed; normal later demand can reload the unloaded model.

## Release web 7a3f736 — 2026-09-27 (theme consistency, navigation search, backup memory)

Theme families now control shared corner roles across controls, fields, cards, menus and dialogs, including sign-in/setup. Glass foreground overlays use a denser tint so underlying labels do not compete with menu text; translucent panes remain. Sidebar search finds available app destinations alongside chats and projects. Offsite backups stream consistent SQLite snapshots from temporary files instead of loading the full database into one Buffer, with cleanup on success, failure and cancellation. A synthetic 67 MB database demonstrates removal of the full snapshot Buffer allocation; this is not a total-process memory or throughput claim.

Root reviewed exact heads before push and again before matching-head squash merge; all PR CI gates passed. Combined main passed 2,497 tests, typecheck, an explicit temporary-output build and design lint, plus destination-search browser QA. Theme regressions passed 613 shape/material checks and 452 authentication/setup checks, with baseline failures reproduced, plus 216 reading states. Root inspected all theme/reading/authentication contact sheets and focal captures at 1440/768/390 in light/dark. These are synthetic Chrome fixtures; native WebKit, physical devices and actual credentials/inference are outside that coverage.

Deployed from main `7a3f736d9a47eaac3bc14d5ee675d272365d1a51` using git archive/scp and a the deployment host build. Environment and both Compose files backed up as `*.bak.before-7a3f736`. Verified current→releases/7a3f736, healthy web with zero restarts, `/` 200, unauthenticated `/api/profile` 401, `/version.json` 7a3f736, and served `index-CDVCXJFu.js` / `index-CsXTtFAF.css` present in the image. All 42 non-web containers retained identical IDs, StartedAt, images and restart counts. No flags or sidecars changed.

Dedicated Luna Chrome workers tested immediately after activation; root reviewed both reports. Current Contemporary appearance/settings/menu navigation and sidebar destination search, keyboard activation, clearing, no-results and browser Back passed the tested desktop paths. No settings were saved. Other live themes, light/mobile views, real authentication, backup execution and inference remain untested; synthetic theme matrices are separate evidence.

Rollback: point `current` to `releases/e51c5b1`, restore `config/.env.bak.before-7a3f736`, and run the same web-only preflight command from the Cowork Compose Manager directory.

## Release web e51c5b1 — 2026-09-27 (tool policy after approval)

Chat now rechecks the account's current tool policy immediately before dispatch. If a tool was changed to Block while its approval card was pending, submitting that old approval refuses the call and records a denial. The original issue still required the owner to approve the displayed arguments; this fixes stale policy enforcement, not an unauthenticated or silent write bypass.

Root reviewed the exact head before push and again before matching-head squash merge; all eight CI checks passed. Combined main passed 2,494 tests with zero failures or skips. Branch typecheck, explicit build to a unique /tmp output, and design lint passed. Synthetic tests exercise the real approval gate and owner decision route with fake provider/Drive execution, covering blocked reads/writes and unchanged ask behavior.

Deployed from main `e51c5b1454850af7054359f7c7a699620d046005` with git archive/scp and a the deployment host web build. Environment and both Compose files backed up as `*.bak.before-e51c5b1`. Verified current→releases/e51c5b1, healthy web with zero restarts, `/` 200, unauthenticated `/api/profile` 401, and served `index-BVAVsQI9.js` / `index-CLfPZER_.css` present in the image. All 42 non-web containers retained identical IDs, StartedAt, images and restart counts. No flags or sidecars changed.

Rollback: point `current` to `releases/c01f303`, restore `config/.env.bak.before-e51c5b1`, and run the same web-only preflight command from the Cowork Compose Manager directory.

## Release web c01f303 — 2026-09-27 (bounded passkey challenges)

Passkey challenge issuance now prunes expired rows transactionally and limits active challenges to 4,096. Capacity rejects new requests without invalidating existing ceremonies, with uniform public responses for known and unknown usernames. Registration and sign-in resume when challenges expire or are consumed. This bounds challenge records; it does not claim general HTTP/CPU denial-of-service protection or immediate SQLite file compaction.

Root reviewed the exact implementation before push and again before matching-head squash merge; all eight CI checks passed. Local focused auth tests, typecheck, build and design lint passed. Full local tests passed 2,491/2,491 on rerun; the first run had one unrelated chat-drafts LRU assertion failure that also passed in isolation. Synthetic real-route/SQLite tests cover concurrent issuance, cleanup, capacity errors and preservation of existing tokens.

Deployed from main `c01f303c4a797ccac429a5d1d010c732d1d67fb5` through git archive/scp and a the deployment host web build. Environment and both Compose files were backed up as `*.bak.before-c01f303`. Verified current→releases/c01f303, healthy web with zero restarts, `/` 200, unauthenticated `/api/profile` 401, and served `index-ogJdHrHD.js` / `index-CLfPZER_.css` in the image. All 42 non-web containers retained identical IDs, StartedAt, images and restart counts.

Rollback: point `current` to `releases/69a40a7`, restore `config/.env.bak.before-c01f303`, and run the same web-only preflight command from the Cowork Compose Manager directory.

## Release web 69a40a7 — 2026-09-27 (account deletion persistence)

Captured workspaces now guard chat-context observations, summaries, meter snapshots and optional context logs after account deletion. Late reply and tool usage updates also refuse to recreate the deleted account directory. These changes cover the named persistence paths, not every possible detached writer. Synthetic regressions pause manager/summarizer responses across deletion and verify active and other-tenant writes still work.

All PR heads were independently reviewed before push and again before matching-head squash merge; CI passed. Combined web source passed 2,489 tests with zero failures or skips; the final main delta after that run changes only the undeployed Diary service. Branch typecheck, build and design lint passed. The separately merged sidecar fixes passed their applicable CI, but this release does not activate them.

Deployed from main `69a40a7f020df373737f9bfa9ae5824ba97da34c` using git archive/scp and a the deployment host image build. Backed up the environment and both Compose files as `*.bak.before-69a40a7`, then ran only the owner's web preflight command. Verified current→releases/69a40a7, healthy web with zero restarts, `/` 200, unauthenticated `/api/profile` 401, and served `index-DRiaLDMn.js` / `index-CLfPZER_.css` present in the image. All 42 non-web containers retained identical IDs, StartedAt, images and restart counts. No flags, model jobs or sidecars changed.

Rollback: point `current` to `releases/f8a83f0`, restore `config/.env.bak.before-69a40a7`, and run the same web-only preflight command from the Cowork Compose Manager directory.

## Release web f8a83f0 — 2026-09-27 (model states, provider validation, source deletion)

Model loader checks and installed-model panels now distinguish initial loading from unavailable or empty results. Removing a provider clears its associated model selection in the current workspace, and explicit unknown provider IDs are rejected while the legacy alias remains supported. Shared-provider references in other workspaces remain a separate lifecycle gap. Account deletion now revokes captured workspaces and fences project/source persistence, detached source journals, and RAG work before and after asynchronous boundaries. The separate chat-context persistence path remains tracked in #478; this release makes no universal account-erasure claim.

Each exact PR head was independently reviewed before push and again before squash merge with a matching-head guard. All applicable CI passed. Combined main passed all 2,484 Node tests with zero skips after linking the worktree to existing server dependencies; no package installation was needed. Typecheck, builds and design lint passed on the implementation branches. Synthetic Playwright checks fail on their bases and pass the UI fixes at 1440/768/390 in light/dark, covering pending and settled responses; root inspected the screenshot matrices. Deletion regressions pause extraction, storage and synthetic embedding across revocation and preserve active/other-tenant behavior.

Deployed from main `f8a83f0af6c2ade08eaf77cf3cfe1814c24fbf8a` using git archive/scp and a the deployment host image build. Backed up `.env` and both Compose files as `*.bak.before-f8a83f0`; ran only the required web preflight activation. Verified current→releases/f8a83f0, healthy web with zero restarts, `/` 200, unauthenticated `/api/profile` 401, and served `index-BkrNM4Vo.js` / `index-CLfPZER_.css` present in the image. All 42 non-web containers retained identical IDs, StartedAt, images and restart counts. No flags, model jobs or sidecars changed.

Rollback: point `current` to `releases/e2f1e0a`, restore `config/.env.bak.before-f8a83f0`, and run the same web-only preflight command from the Cowork Compose Manager directory.

## Release web e2f1e0a — 2026-09-27 (project validation and UI navigation)

Rejected project configuration patches preserve the live sampling override. Chat turns and metadata requests explicitly targeting a deleted project return 404 instead of continuing without project context or reporting a discarded save as successful. Admin Settings deep links focus the requested section after profile loading unless the user has moved focus, including moving away and back. Code → Plugins opens Plugins; the main Customise default remains Connectors.

Root independently reviewed each exact local commit before push and again before squash merge with matching-head guards. All applicable CI checks passed. The combined project/chat regression suite passed 67 tests. Both UI Playwright scripts fail on the original base and pass on the reviewed branch at 1440/768/390 in light/dark; the focus-away-and-back regression also fails on the intermediate implementation. Root inspected the screenshot matrices. Local typecheck/build/design lint passed; full local npm test did not complete due baseline-matching missing server dependencies and a RAG stall, so no full local pass is claimed.

Built on the deployment host from main `e2f1e0ae3a55e28a7146c9ddf973f719d4e43e8a` using git archive/scp. Backed up `.env` and both Compose files as `*.bak.before-e2f1e0a`; activated only web through the required preflight command. Verified current→releases/e2f1e0a, healthy web with zero restarts, `/` 200, unauthenticated `/api/profile` 401, and served `index-BRTYQITs.js` / `index-kv_iUv4Y.css` present in the image. All 42 non-web containers retained identical IDs, StartedAt, images and restart counts. No flags, models or sidecars changed; embedding restore #336 remains owner-blocked.

Rollback: point `current` to `releases/d8f510d`, restore `config/.env.bak.before-e2f1e0a`, and run the same web-only preflight command from the Cowork Compose Manager directory.

## Release web d8f510d — 2026-09-27 (duplicate request fixes, #462)

Diary directory listings and Archived workspace reads now share requests. Chat context refreshes on chat changes and reply completion, avoiding the extra read caused by initial history hydration. Mutation, background-source completion and session invalidation preserve fresh reads. The request cache retains at most 128 keys and shares slow in-flight requests.

The reviewed PR head was `f16905dab654591f61fc00059b4014edf54c28cf`, squash-merged with a matching-head guard to `d8f510de4c2f646c83f5cadf4d7a42a17d264170`. Required CI is green, including Node tests/typecheck/build and Docker images; 754 frontend tests pass locally. Synthetic browser QA fails on main d0f9750 (two initial requests per endpoint) and passes on the fix (one, then one more after a mutation). The 1440/768/390 light/dark matrix was inspected before the final cache-only follow-up; final-head 1440-light request-count QA and cache regressions pass. Full local suites stalled at the same server RAG test after about 22 minutes with baseline missing-dependency failures; no full local pass is claimed.

Deployed from main using git archive/scp and a the deployment host image build. Backed up `.env` and both Compose files as `*.bak.before-d8f510d`, then used only `up.sh --env-file ... -- -d --no-build --no-deps --wait --wait-timeout 180 web`. Verified current→releases/d8f510d, web healthy with zero restarts, public `/` 200, unauthenticated `/api/profile` 401, and served `index-N4w7_lzO.js` / `index-kv_iUv4Y.css` present in the image. All 42 non-web containers retained identical IDs, StartedAt, images and restart counts across activation. No feature flags, models or sidecars changed; embed's existing crash loop (#336) remains owner-blocked.

Rollback: point `current` to `releases/b61a914`, restore `config/.env.bak.before-d8f510d`, and run the same web-only preflight command from the Cowork Compose Manager directory.

## Release web b61a914 — 2026-09-27 (merge #451, deploy #449 #460 #461 #451)

#449 (`5ccdd9d`), #460 (`a350d4f`) and #461 (`ea1ed04`) were already merged into `main` by a
previous release agent but not yet deployed; this release ships them for the first time. #451
(`feat/447-chatgpt-oauth-provider`, head `5985b35`) already had `main` merged in and was pushed
with CI running; `gh pr checks 451 --watch` finished 8/8 green (including "CI required"). Head
SHA confirmed as `5985b353c7ad589fd159b8b37610c298d8da0188`, `mergeStateStatus: CLEAN`. Marked
ready and squash-merged (`--match-head-commit 5985b353c7ad589fd159b8b37610c298d8da0188`) to
`b61a914b6f0bf974588b399096e31d109da48fdd`; `origin/main` advanced `ea1ed04` → `b61a914`. Remote
branch `feat/447-chatgpt-oauth-provider` deleted on merge. #452–#455 closed automatically on
merge; GitHub also auto-closed #447 despite the PR only saying "Refs #447" (no "Closes" keyword
against it) — reopened with an explanatory comment, since #451's own open questions call out that
a live sign-in test is still needed before #447 can close. Diff for this release limited to
`apps/web`, `THIRD_PARTY_NOTICES.md` and `docs/`, no `services/`, so this stayed a web-only
release; no other sidecar was touched. Worktrees/branches `/tmp/noevia-fix-446`,
`/tmp/noevia-fix-450`, `/tmp/noevia-fix-448` and `/tmp/noevia-feat-447` (and the matching local
branches `fix/448-glass-sticky-strips`, `fix/450-code-access-flash`,
`feat/447-chatgpt-oauth-provider`) removed after merge; `/tmp/noevia-fix-456`
(`fix/456-457-459-dup-fetches`, unfinished) was left alone.

`cowork-web-1` came up healthy, `RestartCount` 0, `Image=cowork-web:b61a914`,
`StartedAt=2026-09-27T03:40:45Z`. `cowork-diary-1`, `cowork-ocr-1`, `cowork-model-loader-1`,
`cowork-code-sandbox-1`, `cowork-laya-1`, `cowork-docling-1`, `cowork-llama-1` and `cowork-kiwix-1`
all kept their pre-release container `Id` and `StartedAt` unchanged, confirming `--no-deps` did
not recreate them. (`cowork-embed-1` is the same pre-existing, unrelated crash-loop noted in the
`b84b3b8` entry below — its `Id` is unchanged; its `RestartCount` continued climbing through the
deploy window, not caused by this release.) `https://noevia.example.com/` returned `200`,
`/api/profile` returned `401`, and the served `index.html` referenced
`index-CCKOIjC1.js`/`index-kv_iUv4Y.css`, both confirmed present in the deployed image's
`dist/assets` via `docker exec`. A read-only, unauthenticated check inside `cowork-web-1`
(`node -e "require('/app/server/features.cjs').createFeatures({env:process.env}).enabled('chatgptOAuth')"`)
returned `false`; no env var was set and the flag was not flipped.

## Release web b84b3b8 — 2026-09-26 (merge #445, deploy #445)

PR #445 (`fix/442-443-vision-role-size-units`) was draft with CI green (8/8, including "CI
required") at head `210c451a766200f8756d6e1b4938bdf556d5807a`, which already included `main` after
#444 (`origin/main` was still at `6d7f8e7`, the Batch 14 changelog commit, when this release
began — no re-merge was needed). Diff limited to `apps/web` (server routes + frontend), no
`services/`, so this was a web-only release; no other sidecar was touched. Marked ready and
squash-merged (`--match-head-commit 210c451a766200f8756d6e1b4938bdf556d5807a`) to `b84b3b8`;
`main`'s tree hash was confirmed identical to the PR head's tree hash post-merge
(`cad4f0554a4858032fbd309fbcf2b640418936dd`). Remote branch `fix/442-443-vision-role-size-units`
and its local worktree (`/tmp/noevia-fix-442`, registered under
`~/.noevia-deps/noevia-base/.git/worktrees`) deleted/removed after merge.

`cowork-web-1` came up healthy, `RestartCount` 0, `Image=cowork-web:b84b3b8`,
`StartedAt=2026-09-26T13:24:11Z`. `cowork-diary-1`, `cowork-ocr-1`, `cowork-model-loader-1`,
`cowork-code-sandbox-1`, `cowork-laya-1`, `cowork-docling-1`, `cowork-llama-1` and `cowork-kiwix-1`
all kept their pre-release container `Id` and `StartedAt` unchanged, confirming `--no-deps` did
not recreate them. (`cowork-embed-1` was already crash-looping before this deploy, unrelated and
untouched — its `Id` is unchanged; its `RestartCount` continued climbing during the deploy window
consistent with its ongoing restart loop, not this release.) `https://noevia.example.com/`
returned `200`, `/api/profile` returned `401`, and the served `index.html` referenced
`index-CIjrmDNW.js`/`index-Cd6S8biF.css`, both confirmed present in the deployed image's
`dist/assets` via `docker exec`. A read-only, unauthenticated `GET /api/auto-roles` from inside
`cowork-web-1` (`docker exec cowork-web-1 curl … http://localhost:8021/api/auto-roles`) returned
`401`; no `PUT` was issued against the endpoint.

## Release web 97bf1eb — 2026-09-26 (merge #444, deploy #444)

PR #444 (`fix/439-440-sidebar-search-nested-menu`) was draft with CI green (7/7) at head
`e7d9b87c852c2c4cc948bf50d66c06c888a68c50`, based on `origin/main` at `8b07148` — by the time of
this release `origin/main` had advanced to `7fc3fa5` (Batch 13's #441, which also touched every
`apps/web/src/i18n/*.ts` file). `git merge origin/main` in the PR worktree resolved automatically
with no manual conflict markers (the two PRs' `i18n` key additions and CSS landed on different
lines; #441 touched `ChatView.tsx`/`ComposerActions.tsx`/`ComposerTextarea.tsx`, #444 touched only
`Sidebar.tsx`, so neither PR's component edits overlapped) — merge commit `2029b90`. Full
verification against a fresh `npm run build` of the merged tree (`apps/web`) found one adjacency
regression the file-level merge couldn't catch: `qa/composer-434.cjs` passed, but
`qa/sidebar-search-nested-menu.cjs` failed a strict-mode Playwright assertion because #441 added
its own `sr-only role="status" aria-live="polite"` span to `ChatView` (#437's drop-hint
announcement) that now coexists with #444's sidebar result-count live region, and the QA suite's
locator matched both. Fixed by scoping the suite's locator to `.sidebar` (commit `3c54c3d`,
QA-only, no application code changed) rather than changing either live region's behaviour. `npm
test` (2368/2368), `npm run typecheck`, `npm run build` and `npm run lint:design` all passed on
the final tree; `qa/sidebar-search-nested-menu.cjs` (11/11) and `qa/composer-434.cjs` (8/8) both
passed against a fresh build of the final commit. CI went green (7/7) again at the new head after
pushing the QA fix. Marked ready and squash-merged (`--match-head-commit
3c54c3d9d908eb7838d131e5761933ac886c2f82`) to `97bf1eb`; `main`'s tree hash was confirmed identical
to the PR head's tree hash post-merge. Remote branch `fix/439-440-sidebar-search-nested-menu` and
its local worktree (`/tmp/noevia-fix-439-440`) deleted after merge. The already-stale
`/tmp/noevia-fix-434` worktree entry (Batch 13 had already merged and removed the directory, but
left a dangling `git worktree` registration) was pruned in the same pass.

`cowork-web-1` came up healthy, `RestartCount` 0, `Image=cowork-web:97bf1eb`,
`Started=2026-09-26T13:00:23Z`. `cowork-diary-1`, `cowork-ocr-1`, `cowork-model-loader-1`,
`cowork-code-sandbox-1`, `cowork-laya-1`, `cowork-docling-1`, `cowork-llama-1` and `cowork-kiwix-1`
all kept their pre-release container `Id` and `StartedAt` unchanged, confirming `--no-deps` did
not recreate them. (`cowork-embed-1` was already crash-looping before this deploy, unrelated and
untouched — its `Id` is unchanged; its `RestartCount` continued climbing during the deploy window
consistent with its ongoing restart loop, not this release.) `https://noevia.example.com/`
returned `200`, `/api/profile` returned `401`, and the served `index.html` referenced
`index-BeW2mCs9.js`/`index-Cd6S8biF.css`, both confirmed present in the deployed image's
`dist/assets` via `docker exec`.

## Release web 69712fb — 2026-09-26 (merge #441, deploy #441)

PR #441 was draft with CI green (7/7) at head `8894080`, based on `origin/main` at `8b07148`
(already current, so no main-merge or worktree rebase was needed). Marked ready and squash-merged
(`--match-head-commit 88940809a164df61652d0ee00ea7c260def7644e`) to `69712fb`. Remote branch
`fix/434-437-composer` and its local worktree/clone (`/tmp/noevia-fix-434`) deleted after merge.

`cowork-web-1` came up healthy, `RestartCount` 0, `Image=cowork-web:69712fb`,
`Started=2026-09-26T12:37:40Z`. `cowork-diary-1`, `cowork-ocr-1`, `cowork-model-loader-1`,
`cowork-code-sandbox-1`, `cowork-laya-1`, `cowork-docling-1`, `cowork-llama-1` and `cowork-kiwix-1`
all kept their pre-release container `Id` and `StartedAt` unchanged, confirming `--no-deps` did
not recreate them. (`cowork-embed-1` was already crash-looping before this deploy, unrelated and
untouched — its `Id` is unchanged; its `StartedAt` moved during the deploy window consistent with
its ongoing restart loop, not this release.) `https://noevia.example.com/` returned `200`,
`/api/profile` returned `401`, and the served `index.html` referenced
`index-Cny5uga5.js`/`index-s3O06YwV.css`, both present in the built image's `dist/assets`.

## Release web 11911da — 2026-09-26 (merge #438, deploy #438)

PR #438 was draft with CI green (7/7) at head `8521c95`, based on `origin/main` at `25fa6a6`
(already current, so no main-merge or worktree rebase was needed). Marked ready and
squash-merged (`--match-head-commit 8521c959520d6e6abfcdb7afdf0c44b167de2916`) to `11911da`.
Remote branch `fix/387-431-stream-scroll-md-lists` and its local worktree/branch (under
`noevia-fix-387`) deleted after merge.

`cowork-web-1` came up healthy, `RestartCount` 0, `Image=cowork-web:11911da...`,
`Started=2026-09-26T12:04:45Z`. `cowork-diary-1`, `cowork-ocr-1`, `cowork-model-loader-1`,
`cowork-code-sandbox-1`, `cowork-laya-1` and `cowork-docling-1` all kept their pre-release `Id`
and `StartedAt` unchanged, confirming `--no-deps` did not recreate them. (`cowork-embed-1` was
already crash-looping before this deploy, unrelated and untouched — its restart count moved from
973 to 975 across the deploy window, consistent with its ongoing loop, not this release.)
`https://noevia.example.com/` returned `200`, `/api/profile` returned `401` (both via the public
tunnel and directly on the box), and the served `index.html` referenced
`index-F2PShjwy.js`/`index-DUixMTw4.css`, both present in the built image's `dist/assets`.

## Release web 63d1187 — 2026-09-26 (merge #432 #433, deploy #432 #433)

Both PRs were draft with CI green (7/7 each) against `origin/main` at `e8123c9`; `gh pr diff --name-only`
confirmed disjoint files (#432: `Sidebar.tsx` + its qa script/test; #433: `ChatView.tsx`, `LibraryTab.tsx`,
CSS, four qa scripts) and neither touched `services/`, so this was a web-only release. Marked ready and
squash-merged #432 first (`--match-head-commit 122ad7e`) to `c35266f`, which auto-closed #362 and left
#355 open as intended. #433's worktree (`/tmp/noevia-fix-428`) then merged `origin/main` (`c35266f`) with
no conflicts (disjoint files), pushed the new head `af10341`, waited for CI green again, then squash-merged
(`--match-head-commit af10341`) to `63d1187`. Remote/local branches for both and worktrees
`/tmp/noevia-fix-355b` and `/tmp/noevia-fix-428` deleted after merge.

`cowork-web-1` came up healthy, `RestartCount` 0, `Image=cowork-web:63d1187`,
`Started=2026-09-26T11:53:07Z`. `cowork-diary-1`, `cowork-ocr-1`, `cowork-model-loader-1`,
`cowork-code-sandbox-1`, `cowork-laya-1`, `cowork-docling-1`, `cowork-llama-1` and `cowork-kiwix-1` all
kept their pre-release `Id` and `StartedAt` unchanged, confirming `--no-deps` did not recreate them.
(`cowork-embed-1` was already crash-looping before this deploy, unrelated and untouched.)
`https://noevia.example.com/` returned `200`, `/api/profile` returned `401`, and the served
`index.html` referenced `index-Ny00E2FY.js`/`index-jJp6eGxJ.css`, both present in the built image's
`dist/assets`.

## Release web 778f855 — 2026-09-26 (merge #427, deploy #427: header/container parity #413 #414 #415)

PR #427 (head `215d400`) was draft with CI green (7/7) against `origin/main` at `6db20fc`. No
`services/` changes, so this was a web-only release. Marked ready, squash-merged (`--match-head-commit
215d400`) to `778f855`; `origin/main` was still at `6db20fc` at merge time so GitHub applied the
PR's own 27-file diff cleanly (`mergeStateStatus: CLEAN`) with no unrelated main advancement to
reconcile. Worktree `/tmp/noevia-fix-413` and both copies of `fix/413-415-headers-containers`
deleted after merge.

`cowork-web-1` came up healthy, `RestartCount` 0, `Image=cowork-web:778f855`,
`Started=2026-09-26T10:59:27Z`. `cowork-diary-1`, `cowork-ocr-1` and `cowork-model-loader-1` kept
their pre-release `Id` and `StartedAt` unchanged, confirming `--no-deps` did not recreate them.
`https://noevia.example.com/` returned `200`, `/api/profile` returned `401`, and the served
`index.html` referenced `index-B47VqTZu.js`/`index-Dq9bnOZC.css`, both present in the built
image's `dist/assets`.

## Release web 39bf823 — 2026-09-26 (a11y focus/labels #418–#421 #345 #362; settings nav/summary/dedup #374 #422 #423)

PR #424 (head `3d88930`) and PR #425 (head `46d0f01`) were both draft with CI green against
`origin/main` at `2c53d24`. #424 was already up to date with `2c53d24` (no local merge needed);
`apps/web`: `npm test` 2296/2296, `typecheck`, `build`, `lint:design` all clean; CI green (7/7);
`qa/sidebar-focus-undo.cjs`, `qa/model-popup-focus.cjs`, `qa/appearance-family-labels.cjs`,
`qa/model-card-labels.cjs` and `qa/tool-catalogue-escape-focus.cjs` each **PASS** against the
built `dist` with `PLAYWRIGHT_MODULE`. Marked ready, squash-merged to `06f1c45`; `git diff`
against `origin/main` empty (tree invariance). Worktree and both copies of
`fix/418-421-345-a11y` deleted.

#425 was then merged against the new `origin/main` (`06f1c45`, i.e. #424) — `ort` auto-merge, no
conflicts across the anticipated overlap in `Sidebar.tsx`, `ModelPopup.tsx`, `GeneralSettings.tsx`,
`ToolCatalogue.tsx` and CSS, keeping both PRs' changes — to `48dde0e`. `npm test` 2303/2303,
`typecheck`, `build`, `lint:design` all clean; CI green (7/7) on the merged branch;
`qa/settings-nav-edge-and-summary-wrap.cjs` and `qa/profile-features-dedup.cjs` each **PASS**
against the built `dist`. Marked ready, squash-merged to `39bf823` (final `main` SHA); `git diff`
against `origin/main` empty. Worktree and both copies of `fix/374-422-423-small` deleted.

## Release web 584bdba — 2026-09-26 (spacing rhythm: #417)

PR #417 (head `627f216`) was draft with CI green against an earlier `origin/main`. Main had since
advanced to `6c7fafb` (#412, #416 plus their changelogs); merged `origin/main` into the branch in a
worktree (`ort` auto-merge, no conflicts — including `Sidebar.tsx`, which kept both #416's row-actions
focus fix and this PR's phone touch-target/spacing rules) to `95463ac`. From `apps/web`: `npm test`
2295/2295, `typecheck`, `build`, `lint:design` all clean; CI green (7/7 checks); `qa/spacing-rhythm.cjs`
(180 screenshots, flush=0 clipped=0 small=0 zoom=0 overflow=0 nav-error=0 probe-error=0 — 9 unrelated
`pageerror`s only in the Editorial family, pre-existing and not part of this script's flush/overflow
gate), `qa/sidebar-focus-undo.cjs` (4/4) and `qa/settings-focus-deep-links.cjs` (all scenarios) each
**PASS** against the built `dist` with `PLAYWRIGHT_MODULE`. Marked ready, squash-merged to `584bdba`
(final `main` SHA); `git diff` against `origin/main` is empty, confirming tree invariance. The worktree
and both local+remote copies of `fix/spacing-apple-rhythm` were deleted after merge.

Built `cowork-web:584bdba` on the deployment host from `releases/584bdba` (git archive of `main`@`584bdba`, scp'd —
no git creds on the box); the in-image build ran all 622 tests before `npm run build`, and
`stamp-icons` reported `version=584bdba`. The candidate image's `version.json` reported `584bdba` and
`dist/assets` contained the expected hashed `index-*.js`/`index-*.css` bundles before cutover. `current`
symlink and `COWORK_VERSION` updated; every other `*_VERSION` left untouched (`DIARY_VERSION=f6444b4`,
`OCR_VERSION=5004b50`, `MODEL_MANAGER_VERSION=1c87ab0`, `DOCLING_VERSION=2026-09-21`,
`CODE_SANDBOX_VERSION=pi-0.87.0-9b532a8`). Deployed with the guarded `tools/preflight/up.sh --env-file
config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

## Release web 3cf7233 — 2026-09-26 (two reviewed fixes: #412, #416)

Both PRs were draft with CI green against `origin/main` at `2c7488d` at the start of this release.
#412 (`c70ce3d`) merged `origin/main` cleanly (`ort` auto-merge, no conflicts) to `0639102`; `npm test`
2291/2291, `typecheck`, `build`, `lint:design` clean; CI green; squash-merged to `4b38263`. #416
(`faa6b1c`) then merged `origin/main` (the merge had been started against `2c7488d`, before #412 landed)
cleanly — `ort` auto-merge, no conflicts, only `docs/changelog.md` — to `39ee9a6`; `npm test` 2289/2289,
`typecheck`, `build`, `lint:design` clean; `qa/sidebar-focus-undo.cjs` (4/4) and `qa/url-history.cjs`
(11/11, including the `/c`, `/c/`, `/p`, `/p/` SPA-shell fallback) both **PASS** against the built `dist`
with `PLAYWRIGHT_MODULE`; CI green (including `offline-contract`); squash-merged to `3cf7233` (final
`main` SHA — this squash lands cleanly on top of #412's already-merged `plugin-directory.cjs` change,
which is why `git diff` against `origin/main` shows exactly that file). All worktrees and their
local+remote branches were deleted after merge. The pre-existing spacing branch (`fix/spacing-apple-rhythm`)
was left untouched, as scoped.

Built `cowork-web:3cf7233` on the deployment host from `releases/3cf7233` (git archive of `main`@`3cf7233`, scp'd —
no git creds on the box). A disposable, network-isolated candidate container confirmed `/` **200**,
`/api/profile` **401**, `/c` and `/p/` **200** `text/html`, `/api/nope` JSON, and that the image's
`dist/assets` contains the exact `index-CfeaRzvk.js` / `index-CW-35hg6.css` referenced by `index.html`
and `version.json` reporting `3cf7233`, before cutover. `current` symlink and `COWORK_VERSION` updated;
every other `*_VERSION` left untouched (`DIARY_VERSION=f6444b4`, `OCR_VERSION=5004b50`,
`MODEL_MANAGER_VERSION=1c87ab0`, `DOCLING_VERSION=2026-09-21`, `CODE_SANDBOX_VERSION=pi-0.87.0-9b532a8`).
Deployed with the guarded `tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait
--wait-timeout 180 web`.

Rollback: `ln -sfn releases/0a8cc31 current`, restore `.env.bak.before-3cf7233` (`COWORK_VERSION=0a8cc31`),
re-run `tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

## Release web 0a8cc31 — 2026-09-26 (three reviewed fixes: #407, #411, #408)

All three PRs were draft with CI green against `origin/main` at `2c0d59c` at the start of this release.
#407 (`511f8a7`) merged `origin/main` cleanly (`ort` auto-merge, no conflicts) to `0b59fdd`; `npm test`
2262/2262, `typecheck`, `build`, `lint:design` clean; CI green; squash-merged to `aead398`. #411
(`db447ce`) then merged `origin/main` (now carrying #407): clean `ort` auto-merge, no conflicts, to
`e563658`; `npm test` 2273/2273, `typecheck`, `build`, `lint:design` clean; CI green (including
`offline-contract`); squash-merged to `637f003`. #408 (`2472e3e`) then merged `origin/main` (now carrying
#411's `chat.cjs`/`ModelsSettings` changes): the anticipated conflicts in `ModelsSettings.tsx`,
`App.tsx` and `Sidebar.tsx` did not materialize — `ort` auto-merged cleanly, both sides kept, to
`bb4a63c`; `npm test` 2289/2289, `typecheck`, `build`, `lint:design` clean, and
`qa/settings-focus-deep-links.cjs` (run against the built `dist` with `PLAYWRIGHT_MODULE`) **PASS**; CI
green; squash-merged to `0a8cc31` (final `main` SHA). `git diff --quiet <head> origin/main` confirmed
tree-identical after each squash. All three worktrees and their local+remote branches were deleted
after merge. The pre-existing spacing branch and #410 were left untouched, as scoped.

Built `cowork-web:0a8cc31` on the deployment host from `releases/0a8cc31` (git archive of `main`@`0a8cc31`, scp'd —
no git creds on the box). Candidate image confirmed to contain the served `dist/assets/index-*.js`/
`index-*.css` bundle before cutover. `current` symlink and `COWORK_VERSION` updated; every other
`*_VERSION` left untouched (`DIARY_VERSION=f6444b4`, `OCR_VERSION=5004b50`,
`MODEL_MANAGER_VERSION=1c87ab0`, `DOCLING_VERSION=2026-09-21`, `CODE_SANDBOX_VERSION=pi-0.87.0-9b532a8`).
Deployed with the guarded `tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait
--wait-timeout 180 web`.

Rollback: `ln -sfn releases/592c4d3 current`, restore `.env.bak.before-0a8cc31` (`COWORK_VERSION=592c4d3`),
re-run `tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

## Release web 592c4d3 — 2026-09-26 (three reviewed fixes: #400, #395, #402)

All three PRs were draft with CI green against `origin/main` at `ff0d4ea` at the start of this release.
#400 (`74bb630`) merged `origin/main` cleanly (`ort` auto-merge, no conflicts) to `e67370e`; `npm test`
2221/2221, `typecheck`, `build`, `lint:design` clean; CI green; squash-merged to `edcf18d`. #395 (`9cab4ca`)
then merged `origin/main` (now carrying #400): the expected `ChatView.tsx` conflict materialized as a
two-line import-order conflict against #394's already-merged `edit-focus.ts` import — resolved by keeping
both import lines (`chat-drafts.ts` and `edit-focus.ts`), no logic conflict, to `10d6f8a`; `npm test`
2240/2240, `typecheck`, `build`, `lint:design` clean; CI green; squash-merged to `fff2a02`. #402 (`c284a4d`)
then merged `origin/main` (now carrying #395's `chat-drafts.ts`): clean `ort` auto-merge, no conflicts, to
`e37d7d8`; `npm test` 2262/2262, `typecheck`, `build`, `lint:design` clean; CI green (including
`offline-contract`); squash-merged to `592c4d3` (final `main` SHA). `git diff --quiet <head> origin/main`
confirmed tree-identical after each squash. All three worktrees and their local+remote branches were
deleted after merge. The pre-existing spacing branch and the #399 QA PR were left untouched, as scoped.

Built `cowork-web:592c4d3` on the deployment host from `releases/592c4d3` (git archive of `main`@`592c4d3`, scp'd — no
git creds on the box). Candidate image confirmed to contain `server/project-limits.json` and the served
`dist/assets/index-*.js`/`index-*.css` bundle before cutover. `current` symlink and `COWORK_VERSION`
updated; every other `*_VERSION` left untouched (`DIARY_VERSION=f6444b4`, `OCR_VERSION=5004b50`,
`MODEL_MANAGER_VERSION=1c87ab0`, `DOCLING_VERSION=2026-09-21`, `CODE_SANDBOX_VERSION=pi-0.87.0-9b532a8`).
Deployed with the guarded `tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait
--wait-timeout 180 web`.

Rollback: `ln -sfn releases/f70e969 current`, restore `.env.bak.before-592c4d3` (`COWORK_VERSION=f70e969`),
re-run `tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

---

## Release web f70e969 — 2026-09-26 (two reviewed fixes: #394, #391)

Both PRs were draft with CI green and `MERGEABLE` against `origin/main` at `d805cfd` at the start of this
release. #394 (`fa0f63f`) already had `d805cfd` as an ancestor, so `git merge origin/main` was a no-op and no
new merge commit was needed; squash-merged directly to `532b049` (`npm test` 2208/2208, `typecheck`, `build`,
`lint:design` clean; GitHub Actions CI green). #391 (`5a00528`) then merged `origin/main` (now at `532b049`,
carrying #394) — the expected `App.tsx`/`ChatView`-adjacent conflict did not materialize; the `ort` merge
strategy auto-merged `ChatView.tsx`, `DiaryModal.tsx`, `useChatScroll.ts`, i18n and the new `edit-focus.ts`/
`markdown-image.ts` files cleanly, keeping both PRs' changes intact, producing `704d569`. `npm test`
(2221/2221), `typecheck`, `build`, `lint:design` all clean on the merged worktree; GitHub Actions CI green
on the pushed head. `qa/url-history.cjs` ran against the built dist with a real Chromium
(`PLAYWRIGHT_MODULE` pointed at the codex-runtime `playwright` package, synthetic `page.route` API mocks,
no inference/storage/Diary/network) — all 10 scenarios passed, including the sign-in-returns-to-deep-link
case. Squash-merged #391 → `f70e969` (final `main` SHA). `git diff --quiet <head> origin/main` confirmed
tree-identical after each squash. Both worktrees and their local+remote branches were deleted after merge.

Built `cowork-web:f70e969` on the deployment host from `releases/f70e969` (git archive of `main`@`f70e969`, scp'd — no
git creds on the box). `current` symlink and `COWORK_VERSION` updated; every other `*_VERSION` left
untouched (`DIARY_VERSION=f6444b4`, `OCR_VERSION=5004b50`, `MODEL_MANAGER_VERSION=1c87ab0`,
`DOCLING_VERSION=2026-09-21`, `CODE_SANDBOX_VERSION=pi-0.87.0-9b532a8`; confirmed the `.env` diff before/after
is exactly the one `COWORK_VERSION` line). Deployed with the guarded
`tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

Rollback: `ln -sfn releases/5430d25 current`, restore `.env.bak.before-f70e969` (`COWORK_VERSION=5430d25`),
re-run `tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

---

## Release web 5430d25 — 2026-09-26 (two reviewed fixes: #384, #365/#356)

Both PRs were draft with CI green and `MERGEABLE` at the start of this release (`origin/main` unmoved at
`16ba52d` since the orchestrator's review). #386 (`f599869`) already had `16ba52d` as an ancestor, so no
merge commit was needed; #385 (`1bc6756`) merged `origin/main` cleanly (auto-merge, no conflicts) to pick
up #386's `ModelPopup.tsx`/`routes/projects.cjs` changes, producing `e9c5c53`. `npm test`
(2162→2181 passing), `npm run typecheck` and `npm run build`/`lint:design` were green on both worktrees;
GitHub Actions CI was green on both heads and re-verified after #385's merge commit was pushed. Squash-merged
in order: #386→`443396d`, #385→`5430d25` (final `main` SHA). `git diff --quiet <head> origin/main` confirmed
tree-identical after each squash. Both worktrees and their local+remote branches were deleted after merge.

Built `cowork-web:5430d25` on the deployment host from `releases/5430d25` (git archive of `main`@`5430d25`, scp'd — no
git creds on the box). Candidate verified before cutover: `version.json` reports `5430d25`; the built
`dist/assets/*.js` contain the new `msg.regenerate` i18n key; `server/routes/projects.cjs` in the image
contains `routingChosen`. `current` symlink and `COWORK_VERSION` updated; every other `*_VERSION` left
untouched (`DIARY_VERSION=f6444b4`, `OCR_VERSION=5004b50`, `MODEL_MANAGER_VERSION=1c87ab0`,
`DOCLING_VERSION=2026-09-21`, `CODE_SANDBOX_VERSION=pi-0.87.0-9b532a8`). Deployed with the guarded
`tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

Rollback: `ln -sfn releases/1c87ab0 current`, restore `.env.bak.before-5430d25` (`COWORK_VERSION=1c87ab0`),
re-run `tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

---

## Release web + model-loader 1c87ab0 — 2026-09-26 (five reviewed a11y/UX fixes: #345 #346 #352–#363 #366–#368, and deploying #347/#348)

All five PRs merged one at a time into `main` from base `31973d5`, each re-merged with the moving
`origin/main` tip and re-verified before squash-merge: #351→`74436e1`, #370→`b13250f` (conflict in
`ToolCatalogue.tsx` — kept #351's no-dialog-role/keepFocusOnMouseDown behaviour together with #370's
inline `placeCatalogue()` layout style), #369→`0b0b88e` (ChatView.tsx auto-merged both edit-action and
reply-telemetry/label changes cleanly), #364→`98641b0`, #382→`1c87ab0` (final `main` SHA; auto-merged
cleanly). Node/TS/build/lint:design green on every merge (2105→2155 tests passing as files were added);
`npm run typecheck` and `npm run lint:design` clean on every merge. GitHub Actions CI green on every
head before merge and again on every re-merged commit before squash.

Built `cowork-web:1c87ab0` and `cowork-model-loader:1c87ab0` on the deployment host from `releases/1c87ab0` (git
archive of `main`@`1c87ab0`, scp'd — no git creds on the box). Candidates verified before cutover:
web — `isSidecarModel('nomic-embed-text-v1')` is `true` with `--env-file config/.env`, `routes/health.cjs`
loads; model-loader — `app.api`/`app.main`/`app.services`/`app.discover` import cleanly and the router
exposes `/api/v1/models-ini`, `/api/v1/backends`, `/api/v1/search/repo`. `current` symlink and
`COWORK_VERSION`/`MODEL_MANAGER_VERSION` updated; every other `*_VERSION` left untouched. Deployed with
the guarded `tools/preflight/up.sh --no-build --no-deps --wait`, model-loader first per docs/deployment.md
("models.ini writer"), then web.

Rollback (web): `ln -sfn releases/7a72713 current`, restore `.env.bak.before-1c87ab0`
(`COWORK_VERSION=7a72713`, `MODEL_MANAGER_VERSION=f6444b4`), re-run
`tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web`.
Rollback (model-loader only): restore `.env.bak.before-1c87ab0`'s `MODEL_MANAGER_VERSION=f6444b4` line and
re-run the same `up.sh ... model-loader`.

---

## Release web 7a72713 — 2026-09-26 (five reviewed fixes: #339–#343)

All five PRs merged one at a time into `main` from base `cfe2fae`, each re-merged with the moving
`origin/main` tip and re-verified before squash-merge: #344→`a2cfb16`, #349→`3a10074`, #350→`9908192`,
#348→`791a17d`, #347→`7a72713` (final `main` SHA). Node/TS/build/lint:design green on every merge
(2052→2091 tests passing as files were added); model-manager pytest green on #348 (91 passed) and #347
(102 passed). Clean i18n-model-file and `noevia.css`/`app.css` auto-merges across #348/#350/#347, no
conflict markers. One local-only false alarm: `apps/web` `npm test` hung/failed intermittently on
`rag.test.cjs` in the #347 worktree due to a concurrent unrelated agent process contending for the
same Mac (a `noevia-fix-366` test run observed live); isolated GitHub Actions CI for #347 (unaffected by
local contention) passed clean, including the actually-changed Model manager suite, and was treated as
authoritative.

Built `cowork-web:7a72713` on the deployment host from `releases/7a72713` (git archive of `main`@`7a72713`, scp'd —
no git creds on the box). Candidate verified before cutover with a synthetic read-only check
(`docker run --env-file config/.env cowork-web:7a72713`): `model-system.cjs`'s
`isSidecarModel('nomic-embed-text-v1')` is `true` and `routes/health.cjs` loads. `current` symlink and
`COWORK_VERSION` updated; every other `*_VERSION` left untouched. Deployed with the guarded
`tools/preflight/up.sh --no-build --no-deps --wait web` (web only).

Rollback if needed: `ln -sfn releases/f6444b4 current`, restore `.env.bak.before-7a72713`
(`COWORK_VERSION=f6444b4`), re-run
`tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

---

## Release model-loader f6444b4 — 2026-09-25 (M3: model-loader is the single writer of models.ini)

Order per docs/deployment.md "models.ini writer": model-loader recreated first (healthy, `RestartCount=0`;
from the web container an unauthenticated `PUT /api/v1/models-ini` returned **401**, proving the endpoint
exists and is token-gated; the previous `5b6d9b6` image had no such route), then the flag added and `web`
recreated (healthy; `MODELS_INI_WRITER=model-loader` confirmed inside the container). Every other `cowork-*`
container and Cloudflared kept identical container IDs; public `/` 200. `cowork-embed-1` stays in its
pre-existing restart loop (#336, untouched).

Not verified here (needs an authenticated session): a preset save through the UI and the resulting
`models.ini.noevia-backup-<rev>` file. No calibration or autotune run was started.

Rollback: set `MODELS_INI_WRITER=web` (or delete the line) in `config/.env` and recreate `web`; to return the
sidecar, restore `.env.bak.before-m3` and recreate `model-loader` with `tools/preflight/up.sh ... model-loader`.

---

## Release diary f6444b4 — 2026-09-25 (M2: Diary tenant assertion + month-file protection)

Order followed per docs/deployment.md "Diary tenant key (M2)": (1) compose wiring added, `compose config` clean
with the key empty; (2) diary overlay to `f6444b4` with the key unset (appdata backup
`ab_20260925_170701` verified first; diary logged "DIARY_TENANT_KEY is unset: accepting tenant requests
without X-Cowork-Tenant-Assertion"; health via web 200); (3) key generated into `.env`, `web` recreated
(healthy, `RestartCount=0`, env contains the key, no tenant warning); (4) `diary` recreated with the key.

Verification after step 4: `cowork-diary-1` healthy, `RestartCount=0`; an unsigned tenant request from the
web container (`GET /api/diary/status` with only the bearer + `X-Cowork-User-ID`) returned **401** and diary
logged "tenant assertion rejected: missing or malformed assertion"; `/api/health` via web 200; every other
`cowork-*` container and Cloudflared kept identical container IDs; public `/` 200, `/api/profile` 401.
Not verified here (needs an authenticated browser session, `LEGACY_AUTH_COMPAT=false`): a real Diary tab
read/write through the signed path, covered by the unit suites (diary pytest 415, web
`diary-tenant-assertion.test.cjs`). Direct sidecar clients using `DIARY_LEGACY_USER_ID` stop working now that
the key is set.

Rollback, in this order only: remove `DIARY_TENANT_KEY` from `config/.env` (or restore
`.env.bak.before-m2-key`) and recreate `diary` with `tools/preflight/up.sh ... diary`; then recreate `web` the
same way. Never roll the diary image back to `9b532a8` while web still holds the key; once the key is gone,
`.env.bak.before-diary-f6444b4` + `up.sh ... diary` returns the previous image.

---

## Release f6444b4 — 2026-09-25 (web-only: fix boot crash from 0d602d6 retry)

This is a retry of an earlier same-day attempt to deploy `0d602d6`, which crash-looped on a missing
`/app/package.json` in the built image and was rolled back to `2037ffd`; `f6444b4` fixes that build
regression and CI now boots the image before merge.

Source shipped via `git archive` of `origin/main` at `f6444b4` (full:
`f6444b42538d362336b78da0d77d385bb097095a`) to `releases/f6444b4`. Only `cowork-web:f6444b4` was
built; no other image was touched. Candidate verification: `docker run --rm --entrypoint ls
cowork-web:f6444b4 /app/package.json` returned the file (the exact defect that broke `0d602d6`).

Verification: internal `GET /api/ready` on the container's `UI_PORT` (8021) returned `200
{"ready":true,"version":"0.2.0"}`; logs since deploy showed `egress.listening` on `172.28.0.4:8040`
and the expected `DIARY_TENANT_KEY` warning, no auth-token warnings; `https://noevia.example.com/`
returned 200 and `/api/profile` returned 401; the served `index-pLXervss.js` / `index-CY0nLBZh.css`
matched the hashes in `cowork-web:f6444b4`'s `/app/dist/assets`.

Rollback (not needed — deploy succeeded): restore `current` to `releases/2037ffd`, restore
`config/.env` from `.env.bak.before-f6444b4`, restore the two compose file backups, then re-run
`tools/preflight/up.sh --env-file config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

---

## Release 2037ffd — 2026-09-25 (web-only: theme families + cursor-pull hover)

No open PRs against `sbstndalton/noevia` were merged for this release (PR #315 was merged as part of this deploy; `gh pr list --state open` after merge showed only other unrelated work). `origin/main` was confirmed at `2037ffd` (full: `2037ffdbe211990d436b95a12b3927951b57be87`) with no trailing non-docs commits, and `git diff --stat 2037ffd origin/main -- apps/` was empty. CI on that SHA (`2037ffdbe211990d436b95a12b3927951b57be87`, workflow `CI`) completed success, including "Docker images build" (2m25s) and "Node tests, typecheck, frontend build" (1m31s).

Source shipped via `git archive` of `2037ffdbe211990d436b95a12b3927951b57be87` to `releases/2037ffd`. Only `apps/web/src` changed, so a full web build was required; it produced `index-Ck6gpNmS.js` / `index-CY0nLBZh.css`.

Candidate release was archived to `releases/2037ffd`, `.env` backed up to `.env.bak.before-2037ffd`, and `cowork-web:2037ffd` was built with `COWORK_VERSION=2037ffd`. Candidate verification used a synthetic in-image check: `docker run --rm --entrypoint cat cowork-web:2037ffd /app/dist/version.json` returned `{"version":"2037ffd"}` before cutover. The served `index.html` referenced `/assets/index-Ck6gpNmS.js` and `/assets/index-CY0nLBZh.css`, matching the hashes baked into `cowork-web:2037ffd`'s `/app/dist/assets`. An in-container grep confirmed the served CSS contained 335 occurrences of `data-family`, including `contemporary`, `editorial` and `glass` family selectors.

Post-cutover verification: `cowork-web-1` healthy, 0 restarts; `https://noevia.example.com/` returned 200 on 3/3 requests; `/api/profile` returned 401; `/version.json` returned `{"version":"2037ffd"}`; the served `index.html` referenced `/assets/index-Ck6gpNmS.js` and `/assets/index-CY0nLBZh.css`, matching the built dist; `docker logs cowork-web-1` showed only normal startup lines (MCP discovery, UI listening), no errors.

Rollback (not needed — verification passed): restore `.env.bak.before-2037ffd`, `ln -sfn releases/58b340c current`, then rerun the same `up.sh … --no-build --no-deps --wait web` command.


## Release 58b340c — 2026-09-25 (favicon/app-shell cache-busting, stamp-test fix)

Preflight: `gh pr list --repo sbstndalton/noevia --state open` showed only #315 (theme families work, not part of this release) — nothing was merged. `origin/main` was confirmed at `58b340c` (full: `58b340c1553fd42ec40a14bc9c1a6728b7f7a370`) with no trailing non-docs commits ahead of it for `apps/`, `compose.yaml`, `.github/` (`git diff --stat` empty against the prior release SHA `20a24c2`... verified against 58b340c as tip). CI on `58b340c1553fd42ec40a14bc9c1a6728b7f7a370` (workflow `CI`, run 36112669958) completed success, including "Docker images build" (2m19s) and "Node tests, typecheck, frontend build" (1m24s), plus Diary test suite, Docling extraction contract and Model manager test suite.

Source shipped via `git archive` of `58b340c1553fd42ec40a14bc9c1a6728b7f7a370` to `releases/58b340c` (the stale `releases/29d2d1d` directory, left over from an aborted attempt that failed the Dockerfile's test stage — fixed by #318 — was removed first). The compose build-arg patch above was required for the `STAMP_VERSION` build arg to resolve; `docker compose ... config` was used to confirm `args: COWORK_VERSION: 20a24c2` resolved correctly before the version bump, and `COWORK_VERSION: 58b340c` after. Building `cowork-web:58b340c` with `COWORK_VERSION=58b340c` completed cleanly, with `stamp-icons: version=58b340c stamped=index.html, manifest.webmanifest wrote version.json` in the build log.

Candidate verification used a synthetic in-image check: `docker run --rm --entrypoint cat cowork-web:58b340c /app/dist/version.json` returned `{"version":"58b340c"}` (not `0.2.0` or `dev`) before cutover. Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It recreated with zero restarts and reported healthy. Public `https://noevia.example.com/` returned 200 three times, `/api/profile` returned 401, `curl .../version.json` returned `{"version":"58b340c"}`, response headers carried `cache-control: no-store`, and the served `index.html` referenced `icon.svg?v=58b340c` / `icon.png?v=58b340c`. Served container asset filenames under `dist/assets` matched the built image's assets exactly. Logs since start were clean. Before/after `docker ps`/`docker inspect` snapshots of every container on the host showed only `cowork-web-1` changed (new container id, new `StartedAt`, restart count unchanged at 0); every other `cowork-*` sidecar (Laya, llama, embed, ocr, docling, kiwix, model-loader, diary, code-sandbox) and unrelated container (Nextcloud AIO stack, media stack) kept its identity and start time. Restart-alert baseline re-acked. No real tune, private Diary access, new harness installation, broader exposure or other production action was part of this release.

Rollback (untaken): restore `.env.bak.before-58b340c`, point `current` at `releases/20a24c2`, then rerun the same guarded no-build `web`-only `up.sh` command. The compose build-arg patch is left in place (harmless, and required going forward).

## Release 20a24c2 — 2026-09-25 (new leaf logo)

No open PRs against `sbstndalton/noevia` were merged for this release (`gh pr list --state open` was empty at preflight). `origin/main` was confirmed at `20a24c2` (full: `20a24c28b34865480aa83e7075c122f9abdcc3ff`) with no trailing non-docs commits, and `git diff --stat 20a24c2 origin/main -- apps/` was empty. CI on that SHA (workflow `CI`) completed success, including "Docker images build" and "Node tests, typecheck, frontend build".

Source shipped via `git archive` of `20a24c28b34865480aa83e7075c122f9abdcc3ff` to `releases/20a24c2`. `apps/web/src` and the public icon assets changed, so a full web build was required; it produced `index-3BnUMor0.js` / `index-DqhxSEgr.css`.

Rollback (untaken): restore `.env.bak.before-20a24c2`, point `current` at `releases/2ab7c99`, then rerun the same guarded no-build `web`-only `up.sh` command.

## Release 2ab7c99 — 2026-09-25 (Settings back/close loop fix, new chats default to Auto)

No open PRs against `sbstndalton/noevia` were merged for this release (`gh pr list --state open` was empty at preflight). `origin/main` was confirmed at `2ab7c99` (full: `2ab7c991d81e4b52d8bc724bdbbb5e434e2f2e6c`) with no trailing docs-only commits, and `git diff --stat 2ab7c99 origin/main -- apps/` was empty. CI on that SHA ("Fix Settings back/close loop through Models & routing; new chats default to Auto (#307)", workflow `CI`, plus "Offline skills MCP contract") completed success, including "Docker images build" and the "Node tests, typecheck, frontend build" job.

Source shipped via `git archive` of `2ab7c991d81e4b52d8bc724bdbbb5e434e2f2e6c` to `releases/2ab7c99`. Both `apps/web/server` and `apps/web/src` changed, so a full web build was required; it produced `index-Bwxxo8tc.js` / `index-DqhxSEgr.css`.

Candidate verification used synthetic checks only, no live inference or real Diary access: an in-container grep confirmed the built image's `server/chat.cjs` contains `project ? project.routing === 'auto' : true`. Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It recreated with zero restarts and reported healthy. Public `/` returned 200 three times, `/api/profile` returned 401, the served `index.html` asset references matched the built dist, and logs since start were clean. `diary` and `ocr` (spot-checked; other sidecars unchanged) kept identical container ids, `StartedAt` and zero restarts (before/after `docker inspect`/`docker ps` snapshot diff showed only `cowork-web-1` changed). Restart-alert baseline re-acked. No real tune, private Diary access, new harness installation, broader exposure or other production action was part of this release.

Rollback (untaken): restore `.env.bak.before-2ab7c99`, point `current` at `releases/4e19d28`, then rerun the same guarded no-build `web`-only `up.sh` command.

## Release 4e19d28 — 2026-09-25 (model delete now unloads, clears auto-router roles)

No open PRs against `sbstndalton/noevia` were merged for this release (`gh pr list --state open` was empty at preflight). `origin/main` was confirmed at `4e19d28` (full: `4e19d2850f49a6671f472a0b2d24ea02aebddff4`) with no trailing docs-only commits, and `git diff --stat 4e19d28 origin/main -- apps/` was empty. CI on that SHA (workflow `CI`, plus "Offline skills MCP contract") completed success, including "Docker images build" and the "Node tests, typecheck, frontend build" job.

Source shipped via `git archive` of `4e19d2850f49a6671f472a0b2d24ea02aebddff4` to `releases/4e19d28`. Both `apps/web/server` and `apps/web/src` changed, so a full web build was required; it produced `index-C3C3OjXI.js` / `index-DqhxSEgr.css`.

Candidate verification used synthetic checks only, no live inference or real Diary access. Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It recreated with zero restarts and reported healthy. Public `/` returned 200 three times, `/api/profile` returned 401, the served `index.html` asset references matched the built dist, and an in-container grep confirmed `server/models.cjs` contains `clearRoleReferences`. Logs since start were clean. `diary`, `code-sandbox`, `model-loader`, `ocr`, `docling`, `laya`, `llama`, `embed` and `kiwix` kept identical container ids, `StartedAt` and zero restarts (before/after `docker inspect` snapshot diff showed only `cowork-web-1` changed). Restart-alert baseline re-acked. No real tune, private Diary access, new harness installation, broader exposure or other production action was part of this release.

Rollback (untaken): restore `.env.bak.before-4e19d28`, point `current` at `releases/cfdb5b3`, then rerun the same guarded no-build `web`-only `up.sh` command.

## Release cfdb5b3 — 2026-09-25 (Laya tool gate, experimental, off by default)

No open PRs against `sbstndalton/noevia` were merged for this release (`gh pr list --state open` was empty at preflight). `origin/main` was confirmed at `cfdb5b3` (full: `cfdb5b30c483cfe39596cd80ccd8e7b43bd2231f`) with no trailing docs-only commits, and `git diff --stat cfdb5b3 origin/main -- apps/` was empty. CI on that SHA ("Tool gate: make small models use tools when the prompt needs them (experimental, off) (#301)", workflow `CI`, plus "Offline skills MCP contract") completed success, including "Docker images build" and the Node tests/typecheck/frontend-build job.

Source shipped via `git archive` of `cfdb5b30c483cfe39596cd80ccd8e7b43bd2231f` to `releases/cfdb5b3`. Both `apps/web/server` and `apps/web/src` changed, so a full web build was required; it produced `index-C8b5Zts7.js` / `index-DqhxSEgr.css` (unchanged locale chunks).

Candidate verification ran the built image standalone: an in-container listing confirmed `server/tool-gate.cjs` was present, and `server/features.cjs` showed the `toolGate` feature flag defaults to `enabled: false` (`NOEVIA_FEATURE_TOOL_GATE` was left unset in `.env`) — synthetic checks only, no live inference or real Diary access. Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It recreated with zero restarts and reported healthy. Public `/` returned 200 three times, `/api/profile` returned 401, the served `index.html` asset references matched the built dist, and logs since start were clean. `diary`, `code-sandbox`, `model-loader`, `ocr`, `docling`, `laya`, `llama`, `embed` and `kiwix` kept identical container ids, `StartedAt` and zero restarts (before/after `docker inspect` snapshot diff showed only `cowork-web-1` changed). Restart-alert baseline re-acked. `NOEVIA_FEATURE_TOOL_GATE` was not set — the tool gate stays off. No real tune, private Diary access, new harness installation, broader exposure or other production action was part of this release.

Rollback (untaken): restore `.env.bak.before-cfdb5b3`, point `current` at `releases/8454694`, then rerun the same guarded no-build `web`-only `up.sh` command.

## Release 8454694 — 2026-09-25 (i18n catalogues, QA scripts, docs)

No open PRs against `sbstndalton/noevia` were merged for this release (`gh pr list --state open` was empty at preflight). `origin/main` was confirmed at `8454694` (full: `84546946e4b3460e95e1f608ab5d75c77b117549`). CI on that SHA (`i18n: model manager segment, Diary & storage and Service status (#300)`, workflow `CI`) completed success.

Source shipped via `git archive origin/main` to `releases/8454694`. Only `apps/web/src` changed, so a full web build was required (no server changes); it produced `index-C5ea3Cp-.js` plus refreshed locale chunks (e.g. `de-DE-CJsuIpcy.js`).

Candidate verification ran the built image standalone: `dist/index.html` referenced the freshly built `index-C5ea3Cp-.js`, an in-container listing confirmed the de-DE locale chunks were present, and every pinned sidecar tag (`cowork-diary:9b532a8`, `cowork-ocr:5004b50`, `cowork-model-loader:5b6d9b6`, `cowork-code-sandbox:pi-0.87.0-9b532a8`, `cowork-docling:2026-09-21`) already existed locally — synthetic checks only, no live inference or real Diary access. Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It recreated with zero restarts and reported healthy. Public `/` returned 200 three times, `/api/profile` returned 401, the served `index.html` asset reference matched the built dist, a locale chunk (`de-DE-CJsuIpcy.js`) served 200, and logs since start were clean. `diary`, `code-sandbox`, `model-loader`, `ocr`, `docling`, `laya`, `llama`, `embed` and `kiwix` kept identical container ids, `StartedAt` and zero restarts (before/after `docker ps`/`inspect` snapshot diff showed only `cowork-web-1` changed). Restart-alert baseline re-acked. No model runs, real Diary data, new harness installation or broader exposure were part of this release.

Rollback (untaken): restore `.env.bak.before-8454694`, point `current` at `releases/5a47942`, then rerun the same guarded no-build `web`-only `up.sh` command.

## Release 5a47942 — 2026-09-24 (Projects/Cowork task status, connector permissions, usage drilldown, Customise UI; MCP custom-server preview)

No open PRs against `sbstndalton/noevia` were merged for this release (a PR touching #283 was open but explicitly out of scope). `origin/main` was confirmed at `5a47942` followed only by docs-only changelog commits (`037cc23`, `b247bfa`), and `git diff --stat 5a47942 origin/main -- apps/` was empty. CI on `5a47942` (Detect changed areas, Docker images build, Diary test suite, Model manager test suite, Docling extraction contract, Node tests/typecheck/frontend build, CI required) was all green before release.

Source shipped via `git archive 5a47942` to `releases/5a47942`. Both `apps/web/src` and `apps/web/server` changed, so a full web build was required; it produced `index-BHPy9b1M.js` / `index-Cf_aeTgD.css` plus the unchanged locale chunks.

Candidate verification ran the built image standalone: `dist/index.html` referenced the freshly built `index-BHPy9b1M.js`/`index-Cf_aeTgD.css`, and an in-container `grep` confirmed `server/routes/mcp-directory.cjs` contains the `custom/preview` route — synthetic checks only, no live inference or real Diary access. Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It recreated with zero restarts and reported healthy. Public `/` returned 200 three times, `/api/profile` returned 401, `/api/code/active` returned 401 unauthenticated, the served `index.html` asset references matched the built dist, and logs since start were clean. `diary`, `code-sandbox`, `model-loader`, `ocr`, `docling`, `laya`, `llama`, `embed` and `kiwix` kept identical container ids, `StartedAt` and zero restarts (snapshot diff before/after showed only `cowork-web-1` changed). Restart-alert baseline re-acked. No model runs, real Diary data, new harness installation or broader exposure were part of this release.

Rollback (untaken): restore `.env.bak.before-5a47942`, point `current` at `releases/9a8f29e`, then rerun the same guarded no-build `web`-only `up.sh` command.

## Release 9a8f29e — 2026-09-24 (i18n interface translations)

`origin/main` was confirmed at `9a8f29e` followed only by a docs-only changelog commit (`b247bfa`,
`git diff --stat 9a8f29e origin/main -- apps/` empty) and no open PRs were merged. CI on `9a8f29e`
(Detect changed areas, Docling extraction contract, Node tests/typecheck/frontend build, Model
manager test suite, Diary test suite, Docker images build, CI required) was all green before release.
Source shipped via `git archive 9a8f29e` to `releases/9a8f29e`. `apps/web/src` changed heavily, so a
full web build was required; it produced `index-DLVIslzU.js` / `index-hZUNMXvd.css` plus separate
locale chunks for all nine catalogues (`de-DE-Cv76COWg.js`, `fr-FR-CVCTYCXG.js`, `es-ES-k7TGcfPb.js`,
`it-IT-Cr3AnigY.js`, `nl-NL-DRkttd5-.js`, `pt-BR-5roZJfo7.js`, `sv-SE-CkBFoZrU.js`,
`nb-NO-pn-W27bk.js`).

Candidate verification ran the built image standalone: `/` served index.html, `/api/profile` returned
401, and `dist/assets` contained the locale chunks — synthetic checks only, no live inference or real
Diary access. Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It
recreated with zero restarts and reported healthy. Public `/` returned 200 three times, `/api/profile`
returned 401, the served `index.html` matched the container's `dist/index.html` byte-for-byte, the
served `index-*.js/css` names matched the built dist, and `de-DE-Cv76COWg.js` / `fr-FR-CVCTYCXG.js`
both returned 200 from the public URL. Logs since start were clean. `diary`, `code-sandbox`,
`model-loader`, `ocr`, `docling`, `laya`, `llama`, `embed` and `kiwix` kept identical container ids,
`StartedAt` and zero restarts (snapshot diff before/after showed only `cowork-web-1` changed).
Restart-alert baseline re-acked. No model runs, real Diary data, new harness installation or broader
exposure were part of this release.

Rollback (untaken): restore `.env.bak.before-9a8f29e`, point `current` at `releases/e35ab29`, then
rerun the same guarded no-build `web`-only `up.sh` command.

## Release e35ab29 — 2026-09-24 (browser executor wired into managed jobs)

`origin/main` was confirmed at `e35ab29` (only #281, unrelated, open against it) and every check-run
on that commit (CI: Detect changed areas, Model manager test suite, Diary test suite, Docker images
build, Node tests/typecheck/frontend build, Docling extraction contract, CI required; plus Offline
skills MCP contract) was completed/success before release. `apps/web/server` and `apps/web/src` both
changed since the live `c09ee38`, so a full web build was required. Source shipped via
`git archive e35ab29` to `releases/e35ab29`. The in-image test suite ran as part of the build
(334/334 passing) and produced `index-ClOM-B3G.js` / `index-hZUNMXvd.css`.

Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It recreated with zero
restarts and reported healthy. Public `/` returned 200 three times, `/api/profile` returned 401, the
served `index-*.js/css` names matched the web image's `dist/assets` byte-for-byte by filename,
`server/browser-service.cjs` and `server/routes/browser.cjs` were confirmed present in the container,
and logs since start were clean (no `[egress]` or `[browser]` errors). `diary`, `code-sandbox`,
`model-loader`, `ocr`, `docling`, `laya`, `llama`, `embed` and `kiwix` kept identical container ids,
`StartedAt` and zero restarts (snapshot diff before/after showed only `cowork-web-1` changed).
Restart-alert baseline re-acked. No model runs, real Diary data, new harness installation or broader
exposure were part of this release; only synthetic candidate checks were used.

Rollback (from the Compose Manager project directory):
- Web: `cp -p config/.env.bak.before-e35ab29 config/.env`, `ln -sfn releases/c09ee38 current`, then
  `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

## Release c09ee38 — 2026-09-24 (model evidence import)

`origin/main` was confirmed at `c09ee38` (no PRs open against it besides unrelated #280) and every
check-run on that commit (CI: Detect changed areas, Model manager test suite, Docker images build,
Diary test suite, Node tests/typecheck/frontend build, Docling extraction contract, CI required;
plus Offline skills MCP contract) was completed/success before release. `apps/web/server` and
`apps/web/src` both changed since the live `d5cf1ea`, so a full web build was required. Source
shipped via `git archive c09ee38` to `releases/c09ee38`. The in-image test suite ran as part of the
build (334/334 passing) and produced `index-CNbsCH0G.js` / `index-hZUNMXvd.css`.

Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It recreated with zero
restarts and reported healthy. Public `/` returned 200 three times, `/api/profile` returned 401,
the served `index-*.js/css` names matched the web image's `dist/assets` byte-for-byte by filename,
`server/model-evidence-import.cjs` was confirmed present in the container, and logs since start were
clean. `diary`, `code-sandbox`, `model-loader`, `ocr`, `docling`, `laya`, `llama`, `embed` and
`kiwix` kept identical container ids, `StartedAt` and zero restarts (snapshot diff before/after
showed only `cowork-web-1` changed). Restart-alert baseline re-acked. No model runs, real Diary
data, new harness installation or broader exposure were part of this release.

Rollback (from the Compose Manager project directory):
- Web: `cp -p config/.env.bak.before-c09ee38 config/.env`, `ln -sfn releases/d5cf1ea current`, then
  `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

## Release d5cf1ea — 2026-09-24 (theme families, visual and motion system batch J)

`origin/main` was confirmed at `d5cf1ea` and every check-run on that commit (Docling extraction
contract, Docker images build, Node tests/typecheck/frontend build, Model manager test suite,
Diary test suite, Detect changed areas, CI required) was completed/success before release.
Only `apps/web/src` changed since the live `c7f7999`. Source shipped via `git archive d5cf1ea`
to `releases/d5cf1ea`. Web required a full build (frontend changed); the in-image test suite ran
as part of the build and passed, producing `index-DNSqOhiT.js` / `index-CsqE8JA1.css`.

Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It recreated with zero
restarts and reported healthy. Public `/` returned 200, `/api/profile` returned 401, the served
`index-*.js/css` names matched the web image's `dist/assets` byte-for-byte by filename, and the
served `/theme.js` contained `data-family`. `diary`, `code-sandbox`, `model-loader`, `ocr`,
`docling`, `laya`, `llama`, `embed` and `kiwix` kept identical container ids, `StartedAt` and zero
restarts. Restart-alert baseline re-acked. No model runs, real Diary data, new harness installation
or broader exposure were part of this release.

Rollback (from the Compose Manager project directory):
- Web: `cp -p config/.env.bak.before-d5cf1ea config/.env`, `ln -sfn releases/c7f7999 current`, then
  `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

## Release c7f7999 — 2026-09-24 (settings reorganisation, notifications, memory, response style, keyboard, archived chats, Customise, home recents)

`origin/main` was confirmed at `c7f7999` and every check-run on that commit (Docling extraction
contract, Docker images build, Node tests/typecheck/frontend build, Model manager test suite,
Diary test suite, offline-contract, Detect changed areas, CI required) was completed/success before
release. Only `apps/web` changed since the live `89142c0`. Source shipped via `git archive c7f7999`
to `releases/c7f7999`. Web required a full build (frontend changed); server/Dockerfile/package files
unchanged in scope but the build ran end to end, producing `index-BjjnjAwL.js` / `index-7jjrR2RA.css`.

Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It recreated with zero
restarts and reported healthy. Public `/` returned 200, `/api/profile` returned 401, and the served
`index-*.js/css` names matched the web image's `dist/assets` byte-for-byte by filename.
`diary`, `code-sandbox`, `model-loader`, `ocr`, `docling`, `laya`, `llama`, `embed` and `kiwix` kept
identical container ids, `StartedAt` and zero restarts. Restart-alert baseline re-acked. No model
runs, real Diary data, new harness installation or broader exposure were part of this release.

Rollback (from the Compose Manager project directory):
- Web: `cp -p config/.env.bak.before-c7f7999 config/.env`, `ln -sfn releases/89142c0 current`, then
  `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

## Release 89142c0 — 2026-09-24 (composer Chat/Cowork toggle, tool catalogue)

`origin/main` was confirmed at `89142c0` and every check-run on that commit (Docling extraction
contract, Docker images build, Node tests/typecheck/frontend build, Model manager test suite,
offline-contract, Detect changed areas) was completed/success before release. Only `apps/web`
changed since the live `9b532a8`. Source shipped via `git archive 89142c0` to `releases/89142c0`.
Web required a full build (frontend changed); server/Dockerfile/package files unchanged in scope
but the build ran end to end, producing `index-DKpCIBTO.js` / `index-DghX1G7f.css`.

Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web` only. It recreated with zero
restarts and reported healthy. Public `/` returned 200, `/api/profile` returned 401, and the served
`index-*.js/css` names matched the web image's `dist/assets` byte-for-byte by filename.
`diary`, `code-sandbox`, `model-loader`, `ocr`, `docling`, `laya`, `llama`, `embed` and `kiwix` kept
identical container ids, `StartedAt` and zero restarts. Restart-alert baseline re-acked. No model
runs, real Diary data, new harness installation or broader exposure were part of this release.

Rollback (from the Compose Manager project directory):
- Web: `cp -p config/.env.bak.before-89142c0 config/.env`, `ln -sfn releases/9b532a8 current`, then
  `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 web`.

## Release 9b532a8 — 2026-09-24 (model manager guided tuning, secrets rotation, Diary tombstone/quarantine, upload/RAG/MCP hardening, code-sandbox batch A)

Source shipped via `git archive 9b532a8` to `releases/9b532a8`. Web required a full build (frontend
changed across `apps/web/src`); server/Dockerfile/package files unchanged in scope but the build ran
end to end, producing `index-BJqPT_o9.js` / `index-BrNEIg3U.css`. Diary and code-sandbox diffs against
`d264606`/`pi-0.87.0-dda50c2` were confirmed limited to `services/diary/agent` and
`services/code-sandbox/{pi-acp-bridge.cjs,supervisor.cjs}` respectively (Dockerfiles/requirements
identical), so both are overlays with no dependency install.

Cutover used the guarded `up.sh --no-build --no-deps --wait` for `web`, `diary-overlay.sh 9b532a8` for
Diary (appdata backup `ab_20260924_173346` verified, `gzip -t` passed), and `up.sh --profile code
--no-build --no-deps --wait` for `code-sandbox`. All three recreated with zero restarts and reported
healthy/running. Public `/` returned 200, `/api/profile` returned 401, and the served `index-*.js/css`
names matched the web image's `dist/assets` byte-for-byte by filename. `model-loader`, `laya`, `ocr`,
`docling`, `llama`, `embed` and `kiwix` kept identical container ids, `StartedAt` and zero restarts.
Restart-alert baseline re-acked.

Rollback (from the Compose Manager project directory):
- Web: `cp -p config/.env.bak.before-9b532a8 config/.env`, `ln -sfn releases/d264606 current`, then
  `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 web`.
- Diary: `sed -i 's/^DIARY_VERSION=.*/DIARY_VERSION=d264606/' config/.env` (or restore
  `config/.env.bak.before-diary-9b532a8`), then `up.sh --env-file … -- -d --no-build --no-deps --wait
  --wait-timeout 180 diary`.
- Code sandbox: `sed -i 's/^CODE_SANDBOX_VERSION=.*/CODE_SANDBOX_VERSION=pi-0.87.0-dda50c2/'
  config/.env` (or restore `config/.env.bak.before-code-sandbox-9b532a8`), then `up.sh --env-file …
  --profile code -- -d --no-build --no-deps --wait --wait-timeout 180 code-sandbox`.

## Release d264606 — 2026-09-24 (code-actions publish/network gating, fetchJson body cap, Diary corpus_store NameError and queued-edit races)

Source shipped via `git archive d264606` to `releases/d264606`. All of `apps/web` outside `server/` is identical to b5941e4
(only `code-actions.cjs`, `http.cjs` and their tests changed), so the web image is `FROM cowork-web:b5941e4` with `/app/server`
replaced (candidate `sha256:fa337d92…`). With no network, the in-image `code-actions.cjs`/`http.cjs` SHA-256 hashes match the
release, `node --check` passes and the two changed test files pass 30 of 30. Dist still serves `index-BsftJ7Co.js` /
`index-CV0N4hHI.css`. The Diary diff vs b5941e4 was `agent/corpus_store.py`, `agent/journal.py` and one test (requirements.txt
and Dockerfile identical). The overlay took appdata backup `ab_20260924_151049` (gzip verified), then recreated Diary as image
`cb092351…`; Diary health via web returned 200. In-container `journal.py` contains `unapplied_exchange_edit` and
`corpus_store.py` contains `errors: Optional`.

Cutover used guarded `up.sh … --no-build --no-deps --wait` for `web`, then the Diary overlay (its appdata backup restarted web
again). Web started at 19:11:03Z and Diary at 19:11:10Z. Both are healthy with zero restarts. All other cowork containers
(code-sandbox, model-loader, laya, ocr, docling, llama, embed, kiwix) kept identical ids and start times. Public `/` returned 200
on 3 of 3 requests, and `/api/profile` returned 401. Web logs had zero error markers over 60 s. No Diary data was read.
Restart-alert baseline re-acked.

Rollback (from the Compose Manager project directory):
- Web: `cp -p config/.env.bak.before-d264606 config/.env` (also reverts DIARY_VERSION), `ln -sfn releases/b5941e4 current`, then `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 web`.
- Diary: `sed -i 's/^DIARY_VERSION=.*/DIARY_VERSION=b5941e4/' config/.env` (or restore `config/.env.bak.before-diary-d264606`), then `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 diary`.

## Release b5941e4 — 2026-09-24 (routing/menu fixes, stale loaded summary, chat-only prompt suite, Diary polling and journal replay order, admin-gated warm-up, backup-worker backoff)

Source shipped via `git archive b5941e4` to `releases/b5941e4`. `apps/web/src` changed vs 11617a3 (lockfile and
Dockerfile identical), so web was built on the deployment host (`cowork-web:b5941e4`, image `752c3966e0ca`). Candidate checks were run
with no network. `isChatGenerationModel` (chat-model-kind.cjs) and `MAX_BACKOFF_MS` (diary-backup-worker.cjs) are present.
Dist serves `index-BsftJ7Co.js` / `index-CV0N4hHI.css`. The `installedSummary` / `notifyModelsChanged` grep can't match
minified output because both are renamed identifiers. The bundle and SettingsShell chunk hashes changed from 11617a3.
The Diary diff vs 11617a3 was `agent/journal.py` plus one test (requirements.txt and Dockerfile identical). The overlay took
appdata backup `ab_20260924_144722` (gzip verified). It then recreated Diary as image `aedb9cef…`, and Diary health via web
returned 200. The in-container `/app/agent/journal.py` contains `ORDER BY rowid`.

Cutover used guarded `up.sh … --no-build --no-deps --wait` for `web`, then the Diary overlay. Web started at 18:47:36Z and
Diary at 18:47:43Z. Both are healthy with zero restarts. All other cowork containers (code-sandbox, model-loader, laya, ocr,
docling, llama, embed, kiwix) kept identical ids and start times. Public `/` returned 200 on 3 of 3 requests, and
`/api/profile` returned 401. Web logs had zero error markers over 60 s. No Diary data was read. Restart-alert baseline re-acked.

Rollback (from the Compose Manager project directory):
- Web: `cp -p config/.env.bak.before-b5941e4 config/.env` (also reverts DIARY_VERSION), `ln -sfn releases/11617a3 current`, then `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 web`.
- Diary: `sed -i 's/^DIARY_VERSION=.*/DIARY_VERSION=11617a3/' config/.env` (or restore `config/.env.bak.before-diary-b5941e4`), then `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 diary`.

## Release 11617a3 — 2026-09-24 (round-13 fixes: harness approval bypasses, MCP discovery TTL, Diary storage-outage handling, UI fixes)

Source shipped via `git archive 11617a3` to `releases/11617a3`. `apps/web/src` changed vs dda50c2
(lockfile and Dockerfile identical), so web was built on the deployment host with `docker compose build web`
(`cowork-web:11617a3`, image `23fd3187b3cb`). Candidate checks, run with no network: the in-image `code-harness.cjs` and
`mcp-wiring.cjs` SHA-256 hashes match the release; `pinnedParent` and `discoveryFailTtlMs` are present; dist serves
`index-CzWzWYqN.js` / `index-CV0N4hHI.css`. Diary diff vs 5b6d9b6 was `agent/` plus tests only (requirements.txt and
Dockerfile identical). The overlay took appdata backup `ab_20260924_140932` (gzip verified), which restarted web at
18:09:47Z (same container id). It then recreated Diary as image `96dc142c…`, and Diary health via web returned 200.

Cutover used guarded `up.sh … --no-build --no-deps --wait` for `web`, then the Diary overlay. Web and Diary are healthy
with zero restarts. All other cowork containers (code-sandbox, model-loader, laya, ocr, docling, llama, embed, kiwix)
kept identical ids and start times. Public `/` returned 200 on 3 of 3 requests, and `/api/profile` returned 401. The served assets exist in
the image, and web logs had no error markers over 60 s. The Diary import check passed; no Diary data was read. Restart-alert
baseline re-acked.

Rollback (from the Compose Manager project directory):
- Web: `cp -p config/.env.bak.before-11617a3 config/.env` (also reverts DIARY_VERSION), `ln -sfn releases/dda50c2 current`, then `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 web`.
- Diary: `sed -i 's/^DIARY_VERSION=.*/DIARY_VERSION=5b6d9b6/' config/.env` (or restore `config/.env.bak.before-diary-11617a3`), then `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 diary`.

## Release dda50c2 — 2026-09-24 (harness containment, RAG/prompt budget, round-12 hardening, pi bridge timeouts)

Source shipped via `git archive dda50c2` to `releases/dda50c2`. Web lockfiles and all of `apps/web`
outside `server/` are identical to 958022b, so the web image is `FROM cowork-web:958022b` with
`/app/server` replaced (node_modules kept) and the existing dist reused (`index-BaEAos9j.js`,
`index-CVYcHCIL.css`). Candidate `sha256:e6544d4d…`: server `.cjs` hashes match the release; the in-image
server tests pass 1144 of 1152. The 958022b image fails the same 8 tests the same way (repo files that
are not in the image). With no network, `/api/setup/status` returned 200. Sandbox `sha256:2ecb13d6…`:
the diff against 5b6d9b6 was only the bridge and its test; `node --check` passes; bridge tests 5/5;
the in-container bridge SHA-256 `5ce4f3db…` matches the release.

Cutover used guarded `up.sh … --no-build --no-deps --wait` for `web`, then `--profile code` for
`code-sandbox`. Both were recreated with zero restarts. Web is healthy and the sandbox is running. All other cowork containers
(diary, model-loader, laya, ocr, docling, llama, embed, kiwix) kept identical ids and start times.
Public `/` returned 200 on 3 of 3 requests, and `/api/profile` returned 401. The served assets exist in the image. Web logs had no error markers over 60 s.
Restart-alert baseline re-acked.

Rollback (from the Compose Manager project directory):
- Web: `cp -p config/.env.bak.before-dda50c2 config/.env` (also reverts the sandbox tag), `ln -sfn releases/958022b current`, then `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 web`.
- Code sandbox: `sed -i 's/^CODE_SANDBOX_VERSION=.*/CODE_SANDBOX_VERSION=pi-0.87.0-5b6d9b6/' config/.env`, then `up.sh --env-file … --profile code -- -d --no-build --no-deps --wait --wait-timeout 180 code-sandbox`.

## Release 5b6d9b6 — 2026-09-24 (Diary hardening, model manager + code sandbox hardening, per-service tags; sidecars only)

Source shipped via `git archive 5b6d9b6` to `releases/5b6d9b6`. Before building, diffs against the
running sources were confirmed limited to Diary `agent/` (+ tests, README), model manager `app/*.py`
(+ tests) and code sandbox `supervisor.cjs`; Dockerfiles and requirements identical, so every image
is an overlay `FROM` the running one with no pip/npm step.

1. Per-service tags: backed up `docker-compose.yml`, `docker-compose.override.yml` and `.env` as
   `*.bak.before-per-service-tags`; diary/ocr/model-loader image lines switched to the required
   variables, pinned to the running tags (5004b50/5004b50/a1ededd). `compose config` resolved every
   cowork image to its running tag and a dry-run `up` recreated nothing; no container changed.
2. Model manager `sha256:869beb3f…`: recreated `model-loader` only (guarded `up.sh`), healthy,
   `/api/v1/health` 200 from web; api.py in the container matches the release (shardBase guard).
3. Code sandbox `sha256:ba39f7fc…`: recreated `code-sandbox` only (`up.sh --env-file … --profile code --`),
   running with zero restarts, supervisor.cjs SHA-256 matches the release, TCP reachable from web.
4. Diary `sha256:ab519fdf…`: `diary-overlay.sh 5b6d9b6` took appdata backup
   `ab_20260924_130511` (verified; it stops/starts web and diary, so web kept its container id
   but has a new start time), recreated diary only, healthy, health via web 200.

All other cowork containers (laya, llama, embed, ocr, docling, kiwix) kept identical ids and start
times. Public `/` 200, `/api/profile` 401.

Rollback (from the Compose Manager project directory; old images untouched):
- Model manager: `sed -i 's/^MODEL_MANAGER_VERSION=.*/MODEL_MANAGER_VERSION=a1ededd/' config/.env`, then `up.sh --env-file … -- -d --no-build --no-deps --wait --wait-timeout 180 model-loader`.
- Code sandbox: `sed -i 's/^CODE_SANDBOX_VERSION=.*/CODE_SANDBOX_VERSION=pi-0.87.0-99be0a2/' config/.env`, then `up.sh --env-file … --profile code -- -d --no-build --no-deps --wait --wait-timeout 180 code-sandbox`.
- Diary: `sed -i 's/^DIARY_VERSION=.*/DIARY_VERSION=5004b50/' config/.env` (or restore `config/.env.bak.before-diary-5b6d9b6`), then `up.sh … diary`.
- Per-service-tag migration: restore the three `*.bak.before-per-service-tags` files.

## Release 958022b — 2026-09-24 (job start controller leak, phone preview Settings, web-only)

Web changes deployed: [#102](https://github.com/sbstndalton/noevia/pull/102) starting a background job no
longer leaks a controller when the journal write fails; the phone preview on desktop collapses
Settings panes like a real phone.

## Release c3a03c7 — 2026-09-24 (account cleanup, job journals, research saves, code harness hardening, web-only)

Web changes deployed: [#98](https://github.com/sbstndalton/noevia/pull/98) deleting a user removes their MCP
sign-ins and directory keys; disabled admin credentials are no longer used for discovery; WebDAV
hrefs decode HTML entities; `$` in key templates is handled literally;
[#99](https://github.com/sbstndalton/noevia/pull/99) one unreadable job journal no longer blocks other background
jobs; [#100](https://github.com/sbstndalton/noevia/pull/100) research reports save to the current project by id,
the phone preview honours `data-layout` in JS checks, and the approval card re-enables after a
decision; [#101](https://github.com/sbstndalton/noevia/pull/101) code harness config writes refuse symlinks,
approvals are answered by id, the engine key is never committed (tracked config is refused and
pinned files are removed before auto-commit), and grants are released once. Diary changes in #99
are merged but not deployed by this web-only release.

## Release 852ef76 — 2026-09-24 (S3 region, storage secret v2, replay history, web-only)

Web changes deployed: [#96](https://github.com/sbstndalton/noevia/pull/96) S3 connections store and sign with a
region (new `storage_connections.region` column, default `us-east-1`, migrated at startup); storage
secrets are always encrypted and bound to the account (v2), and legacy v1 secrets are upgraded on
read; [#97](https://github.com/sbstndalton/noevia/pull/97) model replay merges adjacent same-role turns and never
starts with an assistant turn; WebDAV MOVE/COPY default `Overwrite` to `T` per RFC 4918.

## Release 0c2be32 — 2026-09-24 (routing model, Diary edit proxy and offsite backup hardening, web-only)

Web changes deployed: [#90](https://github.com/sbstndalton/noevia/pull/90) Details/Configure hide tuning and calibration for the system
routing model, and the Settings routing summary wraps at narrow widths; [#91](https://github.com/sbstndalton/noevia/pull/91) the Diary
edit proxy forwards `base_hash` and relays 409 conflicts; [#92](https://github.com/sbstndalton/noevia/pull/92) fixes offsite S3 listing
with a "/" prefix and adds a Drive-copy busy-lock guard; [#95](https://github.com/sbstndalton/noevia/pull/95) the Drive mirror never
prunes a foreign backup store (store id, sibling folder, 25% guard, serialized runs), caps
storage reads/listings, and fixes SigV4 canonical path encoding. [#93](https://github.com/sbstndalton/noevia/pull/93) (Diary trash long
names) and [#94](https://github.com/sbstndalton/noevia/pull/94) (Diary tenant delete race, fixed 502 text) are merged but NOT deployed by
this web-only release.

## Release 7e8ce3a — 2026-09-24 (code-workspace and Drive hardening, web-only)

Web changes deployed: [#86](https://github.com/sbstndalton/noevia/pull/86) the code-workspace
release refuses harness-planted git hooks, filters and fsmonitor, and runs git with them
disabled; [#88](https://github.com/sbstndalton/noevia/pull/88) caps Drive reads (Range request
plus a streamed cap), makes autoconfig suggest only calibrator-verified context sizes, and adds
InstructionSkills guards. [#87](https://github.com/sbstndalton/noevia/pull/87) (Diary
index_update validation and quarantine) is merged but NOT deployed by this web-only release.

## Release 7ce2213 — 2026-09-24 (hardening batch, web-only)

Web changes deployed: [#76](https://github.com/sbstndalton/noevia/pull/76) server error
bodies no longer leak raw errors, JSON bodies are checked, chat ids are sanitized and
approvals are scoped; [#80](https://github.com/sbstndalton/noevia/pull/80) and
[#83](https://github.com/sbstndalton/noevia/pull/83) guard the system model (Laya) from
delete, calibration, preset apply and section delete/rename, and gate research maintenance;
[#81](https://github.com/sbstndalton/noevia/pull/81) hides system-model rename/delete in the
Configure tab, merges racing history loads and orders stats updates;
[#82](https://github.com/sbstndalton/noevia/pull/82) caps and aborts MCP responses and makes
the diary stream and tool arguments robust; [#85](https://github.com/sbstndalton/noevia/pull/85)
makes chat delete stop the reply and block saves, resets the project view on switch, and keeps
merged roles alternating. [#77](https://github.com/sbstndalton/noevia/pull/77),
[#79](https://github.com/sbstndalton/noevia/pull/79) and [#84](https://github.com/sbstndalton/noevia/pull/84)
(Diary service, model-manager, code-sandbox) are merged but NOT deployed by this web-only release.

`cowork-web-1` came up healthy with zero restarts (previous image `cowork-web:7b6942c`).
Public checks: `/` returned 200 and `/api/profile` returned 401 (3/3 tries); the served
`index-DoBtRaex.js` and `index-B1OLP7Ag.css` are present in the image's `dist/assets`;
`errorResponse` from #76 is exported in the running container.

## Release 7b6942c — 2026-09-24 (chat save races)

`cowork-web-1` came up healthy with zero restarts (previous image `cowork-web:9ee7bb0`).
Public checks: `/` returned 200 and `/api/profile` returned 401 (3/3 tries); the served
`index-RdBcm5Rx.js` and `index-B1OLP7Ag.css` are present in the image's `dist/assets`.
Later PRs merged to main after 7b6942c are not part of this release.

## Release 9ee7bb0 — 2026-09-23 (Laya excluded from auto-tuner)

`cowork-web-1` came up healthy with zero restarts (previous image `cowork-web:6b59118`).
Read-only, without starting a tune, `require('/app/server/model-system.cjs')` inside
the running container confirmed `isSystemModel('laya_multilingual_f16')` returns
`true` (reason: "System routing model — not tuned"/"not deleted"), while an ordinary
model ID returns `false`. Locally the container answered its root path with the
expected unauthenticated 302 redirect and the built `dist/assets` matched the served
bundle name pattern from prior releases.

## Release 6b59118 — 2026-09-23 (Auto routing label in inference stats and saved replies)

`cowork-web-1` came up healthy with zero restarts (previous image `cowork-web:6b1621c`).
`https://noevia.example.com/` returned 200 and `/api/profile` returned 401 unauthenticated.
Served `index.html` referenced `index-CU_LuO7r.js` and `index-B1OLP7Ag.css`, both present
byte-identically in the built image's `dist/assets`. Laya (`cowork-laya:0.3.5-recovery-2ffd153`),
Diary, OCR, code-sandbox, model-loader, docling and the native llama engine kept identical
container IDs and `StartedAt` timestamps before and after cutover; only synthetic checks were
used, no real tune or Diary access.

## Release 6b1621c — 2026-09-23 (auto-tune recovery and compact progress)

Auto-tune now waits until the router reports every model unloaded before saving the
next candidate profile. This prevents the immediate 409 that could follow a rejected
quality probe while the previous model was still unloading. A bounded timeout names
the blocking model and state; cancellation still restores the current phase. Failed
quality probes report the check and failure type without storing generated answers.
The Auto Tune panel puts status, progress and Resume above compact queued details.

[Issue #72](https://github.com/sbstndalton/noevia/issues/72) was fixed by
[PR #73](https://github.com/sbstndalton/noevia/pull/73), merged as `6b1621c`.
All 1,354 web tests, typecheck, build and design lint passed; the candidate web image
passed 32 isolated tuner/calibration tests. A web-only guarded overlay from `5004b50`
completed with the web container healthy. Public CSS and model-manager JavaScript
match the validated build; protected routes return 401 without authentication.
Brave review confirmed the deployed layout and recovery controls without resuming a
real tune. Diary, OCR, llama and the Laya recovery image retained their container
IDs and start times. Configuration and Compose backups named `.bak.before-6b1621c`
are retained for web-only rollback to `5004b50`; no full appdata backup was run
because it would restart unrelated services. Historical state cannot explain why
the initial f16 quality probe failed.

## Release 827932b — 2026-09-22 (three-material refinement)

Removed the redundant Glassmorphism mode from preferences, pre-paint initialization,
settings, CSS and reference samples; old saved values fall back to Soft. Soft is matte
with restrained depth and visible switch boundaries. Liquid Glass is limited to functional
controls, with readable content, restrained highlights, no label refraction or pointer tilt,
and reduced-preference handling. Material 3 uses paired color roles, tonal selection,
correct pressed/disabled states and native-checkbox switch contrast. Shared geometry stays
stable. General now correctly distinguishes synced theme/accent from browser-local preferences.

`ui/material-refinement` (`7663b40`, `827932b`) was pushed, then fast-forwarded into main
from `9cf92b3` after a fresh fetch. No remote changes conflicted; no force push or branch
deletion. The original `ui-polish-update` checkout is unchanged and clean.

Validation: 1,247 unit tests, typecheck, build and design lint pass. Fourteen distinct
synthetic browser suites pass, including Code, approvals and onboarding in all three
materials. The broad inventory covers 468 states; the final focused confirmation covers
198 states, with zero detected overflow, matte-mode blur leaks or page errors. Both themes,
375/768/1440 widths, smaller approval/drawer viewports, keyboard focus and accessibility
preferences are covered. All 12 rendered switch on/off/mode/theme pairs meet 3:1 contrast.
The Impeccable detector's five dimension-animation findings were fixed. See the full
[material audit and iteration log](material-audit-2026-09-22.md) for evidence and scope limits.
No real Diary corpus, live model inference or user data was used for testing.

Backup `ab_20260922_143433` completed successfully; web, Diary and extra-file archives
independently passed `gzip -t`. Local/remote SHA-256 matched for source
`0731f040149d450e122841bd69443f7bb6475a1f50389c16125b933cde0c7d01` and app
`9b7232a1d68dbf4b6fb211de415f91d77b795eae39d437b1bf802c3c739b269d` archives.
Guarded overlay `04780e6` → `827932b` passed mount/env/tenant-isolation preflights and
reported `RELEASE_827932b_COMPLETE` at 14:46 EDT. Web, Diary and OCR are healthy with zero
restarts. Native engine, embeddings, pi sandbox and Laya IDs/start times are unchanged.
Laya remains pre-existing unhealthy. Existing volume/swap-limit warnings are unchanged.

Public index serves `index-U2SHbFp3.js` / `index-Dtub7VGn.css`; both and `theme.js`, `lens.js`,
`glass-highlight.js` match the local build byte-for-byte. Unauthenticated profile/admin-users
requests return 401; web logs contain zero error markers since cutover. A Python HTTP client
received 403; ordinary curl returned 200 and verified every public asset without changing any
edge/security configuration.

Rollback: restore `config/.env.bak.before-827932b`, point `current` at `releases/04780e6`,
then run the guarded no-build startup for web/diary/ocr. Old images, branches and backups
are retained. The subsequent main commit records rollout evidence only; deployed application
source is `827932b`.

## Release 04780e6 — 2026-09-22 (development branches integrated)

Integrated `ui-polish-update` (`7014b69`) and local
`codex/harness-hardening-claude-pi` (`c729379`) from `origin/main` (`506f0f8`).
The tuning commit already existed as a patch-equivalent change; no duplicate feature
or stale alternative was applied. Only documentation conflicted. See
[integration evidence](integration-2026-09-22.md).

1,245 unit tests, typecheck, build, design lint and 15 synthetic browser/HTTP suites
pass. Real pi 0.87.0 and Claude ACP 0.79.0 pass local scripted-model approval checks,
including hostile Claude repository resources. The Linux pi candidate passes the same
allow/decline fixture with no network or production volumes. The web image passes 80
isolated harness/approval/tuning tests. No real Diary corpus or live inference was used.

Backup `ab_20260922_135257` completed successfully; web, Diary and extra-file archives
independently passed `gzip -t`. Source/app archive checksums matched before deployment.
Guarded overlay `5a88558` → `04780e6` passed all preflights and reported
`RELEASE_04780e6_COMPLETE`. Web, Diary and OCR are healthy, zero restarts. The pi
sandbox was rebuilt from its Dockerfile with pi 0.87.0 and lifecycle scripts disabled,
then activated as `cowork-code-sandbox:pi-0.87.0-99be0a2`; its deployed bridge SHA-256
matches source, version is 0.87.0, and the container runs with zero restarts.

The first candidate package accidentally included a dependency symlink; Docker refused
it before cutover. The corrected archive excludes dependencies/state. The initial sandbox
activation put the profile flag after the wrapper separator; Compose refused it, the env
was restored, and the corrected preflight invocation succeeded. Neither failed attempt
ran an unvalidated candidate.

Public index serves `index-B5Qudv_W.js` / `index-3Twk2Xqu.css`; JavaScript SHA-256 matches
the local build. Unauthenticated model-tuning access returns 401, and web logs contain
zero error markers since cutover. Native llama, embeddings and Laya IDs/start times
are unchanged. Laya's pre-existing unhealthy status remains outside this release.
The existing unmanaged-volume and kernel swap-limit warnings remain unchanged.

Rollback: restore `config/.env.bak.before-04780e6` (including the old pi tag), point
`current` at `releases/5a88558`, then use the guarded preflight no-build startup for
web/diary/ocr and `--profile code -- -d --no-build --no-deps code-sandbox` for the
sandbox. The old release, pi image and backups are retained. The subsequent record
commit is documentation only; deployed application source is `04780e6`.

## 2026-09-22 — Complete automatic model tuning (release `5a88558`)

Models → Your models now has **Tune untuned models** beside **Check for updates**. One
confirmed maintenance window runs a sequential queue of configured chat models without a
current tune. It measures f16/q8/q4 KV cache, long-context recall, three existing-MTP-head draft
settings, n-gram and batch sizes. Three deterministic quality probes screen each setting; the
fastest passing complete profile is rechecked and applied automatically. 60–70% draft acceptance
is guidance, not a cutoff. No model/head downloads; no production benchmarks were started.

Changed artifacts, presets/defaults or engine builds invalidate a tune. Cancellation, failures
and interrupted runs restore the active model's original settings when safe, without overwriting
external edits. Earlier successful queue entries remain tuned. The probes are smoke tests, not
general quality certification. 1,242 tests, typecheck/build/design lint and both affected browser
suites pass; six responsive/theme layouts inspected. The deployed image passes all 10 synthetic
full-tuning tests. Native engine, embeddings and pi sandbox remain unchanged.

## 2026-09-22 — Claude Code and pi pins hardened (source only)

Claude Code now receives the full noevia-owned permission/model configuration inline, exposes a
fixed core tool set, and loads no settings, context, hooks, skills/commands or MCP servers from the
checked-out repository. Its own sandbox can no
longer auto-approve Bash, and both automatic and manual self-update paths are off. pi starts with
only noevia's approval gate and a fixed tool set, never loads project resources or context, makes no startup
network checks, saves no session, and waits for the true whole-turn completion event. Its package
install can no longer run lifecycle scripts. Codex remains refused because it cannot meet the
per-command approval rule. Verified with fake ACP/pi processes; no CLI was installed, no model was
run, and this source change is not deployed.

## 2026-09-22 — Code mode now runs pi

The coding agent in Code mode is now **pi**, the minimal agent many forks start from. It runs in
the same locked-down sandbox. Because pi normally never asks before acting, noevia adds its own
gate: every edit and command shows up on your approval card first, with the exact command or
file. Tested live twice on the throwaway `scratch` repository: it fixed the bug and the tests
pass. OpenCode is still installed and one setting away.

## 2026-09-22 — Diary service updated

The Diary service now keeps the previous version in Trash when a WebDAV client overwrites a
file, and reports each file's last-modified time so sync apps like Obsidian can tell what
changed. Nothing else in the Diary changed, and no Diary data was touched. File sharing (WebDAV)
remains off until you turn it on.

## 2026-09-22 — A local graph for Diary notes

Open a note in the Diary editor and expand **Local graph** to see the notes it links to and the
notes that link back, as a small diagram and a list you can click. Links you have just typed show
straight away. Two-way links are drawn heavier, incoming links dashed. It only reads: nothing is
indexed or changed, and it says so when the backlink scan could not cover every file.

## 2026-09-22 — Claude Code and pi can be pinned; Codex refused (releases `59249d9`, `d59d1a0`, `2577e16`)

Nothing changes in Code mode today; it still runs OpenCode. noevia now knows how to lock down
more coding agents the way it locks OpenCode: every edit, command and web access asks you,
the agent's own "skip permissions" modes are off, it talks only to your local engine, and it does
not update itself or send telemetry. For pi, which has no permission prompts of its own, noevia
installs a gate that asks for every non-read action and blocks if it cannot ask. Installing any
of them in the sandbox is your call. Tested with the real Claude Code and pi against a scripted
fake model: approvals reach you, Decline blocks, and a repository's own settings can't skip the
question. Codex was tested the same way and is **refused**: its commands ran without asking.

## 2026-09-22 — Step supervision stops pausing ordinary chats (release `b055571`)

With Step supervision on, Laya sometimes stopped a harmless chat for review (for example after a
plain project list) and added needless "double-check" rounds. New wording, measured on synthetic
cases: 16/17 on a fresh set with no needless pauses or extra rounds, and every synthetic
dangerous case (hidden instructions, credential requests, destructive commands) still stops.

## 2026-09-22 — System-One decisions show up in the web log (release `e19119d`)

Each routing and supervision decision writes one line — chosen role or action, margin, time
and whether it fell back — and never the message. This is how the next tuning step gets real
evidence instead of synthetic cases.

## 2026-09-22 — System-One routing picks Smart and Code when it should (release `6c3cde0`)

Laya was routing most reasoning and code questions to the Fast model. Probing it with the exact
requests production sends, on synthetic messages, showed the abstract role descriptions were the
cause: 23 of 40 held-out decisions right. Concrete descriptions ("greetings, thanks, or a
one-line factual answer" / "explaining, comparing, planning…" / "anything involving programming
code…") score 36 of 40; the rest are near-ties. Step supervision was checked the same way (8/9)
and left alone. Fallbacks, manual model choice and approvals are unchanged.
[Evidence](research/system-one/19-routing-labels.md).

## 2026-09-22 — Request-local live inference readouts (source `80d116f`, deployed in `e7b59d6`)

The inference footer now follows the visible chat's own event stream instead of treating the
engine-wide `/api/stats` poll as reply telemetry. It shows the routed model and generating state
immediately, records server-observed first output as it arrives, and applies provider-reported
tokens, rate and MTP acceptance without waiting for the next poll. Tool-loop rounds are
cumulative and use a weighted provider rate. Missing measurements remain explicitly unavailable;
they are never guessed from chunks or text. Engine totals/hardware stay separately labelled, so
another chat or a stale poll cannot replace the visible reply's facts.

Verification: 39 focused telemetry/tool-loop tests and 1,111 socket-free tests pass; typecheck,
production build (195 modules), design lint and diff whitespace checks pass. The full suite could
not complete in this task sandbox: 34 listener-based tests were refused with `listen EPERM`, while
1,143 tests passed and no assertion failure was observed. A fully synthetic, port-free browser QA
was added, but Chromium launch and visual inspection were blocked by the task's browser sandbox.
No inference, benchmark, paid endpoint, personal source or Diary data was used. Production remains
on `3d2521d` until the pushed source is deployed and checked on the deployment host.

## 2026-09-22 — Compact context inside tool continuations

The chat loop now rechecks and, when necessary, compacts its model-facing projection before
every continuation after tool execution. The saved transcript and cross-turn summary remain
unchanged. The current user turn, assistant tool calls and their matching results stay
byte-identical and atomic; invalid or oversized protected groups stop with a readable error
without deleting messages, fabricating results or replaying tools. Continuation summaries use
the existing provider-neutral compaction call and conservative context estimate, in bounded
rolling batches. The context meter and opt-in context log report the compacted continuation.

Verification: 1,196 web tests, typecheck, production build, design lint and diff whitespace
checks pass. Focused coverage forces the real handler over budget between tool rounds and
confirms the next request receives a summary plus the intact current tool group. No model
inference, paid endpoint, personal source or Diary data was used.

### 2026-09-21 — Material 3 shares component geometry

## 2026-09-22 — Configure and enable Laya routing in Experimental

Added shared decision-service setup with editable URL/deadline, installed-Laya shortcut,
health-only connection test and persistent admin Save. Routing now uses the configured
Laya service for Fast/Smart/Code instead of requiring the old option-logit endpoint.
Settings apply to subsequent routing and supervision decisions without restart.
1192 tests, typecheck, build and design lint pass; scoped light/dark responsive UI verified.
See [configuration and verification](research/system-one/18-decision-service-settings.md).

## 2026-09-21 — Laya endpoint for model-independent step supervision

Connected the experimental checkpoint seam to a private typed-decision service.
Laya uses a separate CPU-only, offline serving container; the selected answering
provider (including OpenRouter/OpenAI-compatible endpoints) remains unchanged.
Validated bounded responses, no redirects or shared answering credentials, and
existing fallback/approval limits. Pinned model/runtime and optional Compose profile.
One authorized synthetic Laya inference passed on the deployment host; no benchmarks.
See [service scope and setup](../services/laya/README.md).

## 2026-09-21 — Experimental step supervision

Added a separate unavailable-by-default Experimental entry and a provider-neutral chat
checkpoint seam. Mocked decisions can continue, request a bounded verification round,
or pause for review. Failed decisions preserve existing behavior; durable escalation
uses the existing checkpoint store and blocks automatic restoration. No Jev/Laya calls,
model switching or replay. 1181 web tests, typecheck, build and design lint pass.
See [scope and verification](research/system-one/17-step-supervision.md).

Material 3 now inherits the shared dimensions, padding, font metrics and layout borders
instead of replacing them. Tonal colors, radii, shadows and inset outlines retain the
Material appearance. Removed the width-changing selected checkmark and matched segment
font weights; rounded selection fills stay within wrapped tracks. Sidebar spacing also
uses the common tokens. Regression test rejects Material-only geometry overrides.

Verification: 1171 unit tests, typecheck/build/design lint and diff whitespace checks pass.
Synthetic browser comparison: 43 settings/navigation boxes match exactly across Soft,
Liquid glass, Glassmorphism and Material 3 at 375 and 1440 CSS px, plus the normal desktop
viewport. Visually inspected the corrected selection fills. No model or personal-data tests.

### 2026-09-21 — Descriptions above settings controls at every width

Corrected the requested layout: shared settings descriptions occupy their own full-width
row above buttons/selectors even on wide desktops. Compact on/off switches retain their
inline label. Wrapped segmented choices remain visible. This supersedes the prior
width-dependent placement in 126637e.

### 2026-09-21 — Release 126637e deployed

User authorized automatic deployment. Live now includes the shared responsive-control fixes,
Experimental settings and prior bounded continuation source changes. Backup and preflight
passed; all checked services healthy, public HTTP 200. Live Material text/options visually
verified. System-One remains off/unconfigured, durable chat inactive, native engine unchanged.
See [deployment verification and rollback](deployment.md).

### 2026-09-21 — Shared settings and segmented-control wrapping (local, undeployed)

Fixed the shared flex-row cause of one-word-per-line descriptions and clipped controls.
Settings rows now wrap by their available content width, including narrow desktop panels;
text retains a readable minimum width and control/value groups stay within the card.
Segmented controls throughout the app wrap instead of hiding options in a horizontal
scroller. Their selection highlight now tracks both axes and the selected button height,
including Material 3. Coding composer action groups also wrap within their available width.

Verification: 1170 unit tests passed; typecheck, build, design lint and diff whitespace
checks passed. Synthetic browser checks reproduced the original narrow desktop General
settings and confirmed readable descriptions and all Material choices visible. Checked
Material/Density/Motion/Layout at 375, approximately 768 (767 due to browser zoom rounding),
and 1440 CSS pixels: no document or segment overflow. Verified second-row Material 3
selection/highlight alignment, light/dark styling, capability label/value rows and the
Experimental switch page. Desktop screenshots were inspected; viewport override screenshots
still suffer the in-app browser's tiled-capture issue. A complete every-view/two-theme sweep
and physical-device testing were not run. No live preferences or data changed; no deployment.

### 2026-09-21 — Experimental System-One routing switch (local, undeployed)

Settings → Experimental now exposes an administrator-only System-One routing switch,
using the existing persisted/audited feature registry. On selects the option-logit
comparison baseline for new Auto role decisions; off restores the existing classifier.
Failures and deadlines fall back to that classifier. Requires an explicitly configured
private decision endpoint; no model is loaded, downloaded or selected automatically.
1170 unit tests, typecheck, build and design lint passed. Synthetic browser checks covered
save/reload, keyboard rollback and mobile/desktop presentation. See
[implementation and verification](research/system-one/16-experimental-routing.md).
No deployment or real inference. Dedicated System-One model selection remains open.

### 2026-09-21 — Default model mode setting (release c53713b, deployed)

### 2026-09-21 — Broader continuation verification (local, undeployed)

Added separate-process SIGKILL tests for durable generation and ambiguous tool execution.
Verified 1164 web tests, 64 decision/experiment tests, four synthetic real-HTTP suites,
typecheck/build/design lint, and targeted browser tool/approval/responsive checks.
Read-only live checks found Diary disabled for the account and a Nextcloud viewer registration
console error; no file-preview failure reproduced. See [exact scope and results](verification-2026-09-21-continuation.md).
No production changes, model inference or personal data operations.

### 2026-09-21 — First durable-chat slice (local, disabled, undeployed)

Added an optional chat recorder using the existing tenant job journal, with fsynced hash chains,
canonical tool results separate from context projections, stable turn identity, approval history
and persisted retry limits. Mocked replacement generation preserves completed tool results;
ambiguous execution requires review and cannot replay. No production wiring or switching.
See [implementation scope and exact verification](research/system-one/15-durable-chat-slice.md).
Focused durability/regression tests: 45 passed. Final web suite: 1162 passed; typecheck, build
and design lint passed. No live provider, Diary, engine, downloads or deployment involved.

### 2026-09-21 — Adapter cutoff and conditional bounds (local, undeployed)

Applied the reviewed continuation patch at its exact d6e7081 base. Independent run budget
covers version/startup/requests; cleanup is bounded and recorded separately. Partial option
scores now carry normalized conditional bounds and reject malformed distributions.
Current-repository verification: focused tests 28/28; existing decision/experiment tests 36/36;
web unit suite 1138/1138; typecheck, build and design lint pass with installed dependencies.
Only synthetic Node workers ran. No inference, downloads, live checks or deployment.

### 2026-09-21 — Auto routing is the default (release f9dc5df, deployed)

At the user's request, new projects are created with Auto (Fast/Smart) routing unless Manual is asked for. This replaces the step-12 Manual default. The setup wizard's Auto box starts ticked, and unticking it stores `manual`. Existing projects keep their setting. Auto with no Fast/Smart roles configured now uses the project's model instead of refusing the message. Also in this release: the multi-hop rerun on the fixed corpus. Rerank 12→6 got 3/4 against 2/4 for the baseline, and 24→3 got 1/4, which supports keeping 6. 1,116/1,116 unit tests; typecheck clean.

### 2026-09-21 — RAG rerank in chat (release 67f336e, deployed)

Project retrieval now takes a cosine pool (`RAG_RERANK_POOL`, default 12, max 24) and lets Qwen3-Reranker-0.6B pick the chunks kept (`RAG_RERANK_KEEP`, default 6) through the decision layer (`decisions.rank()`, `llama-rerank` backend). A down, malformed or slow reranker (`RAG_RERANK_DEADLINE_MS`, default 3000) falls back to the cosine top-6 used before, so chat never waits past the deadline. The whole feature is behind `NOEVIA_FEATURE_RAG_RERANK` + `RERANK_BASE_URL`. The engine's model manager keeps `RERANK_MODEL` loaded beside the chat model, the way it keeps the embedding model. Placement (the user's choice): the reranker is the router's second resident, `reranking = true` / `pooling = rank` in `models.ini`. Embeddings stay on the CPU `embed` container. the deployment host GPU timing, warm: 12 chunks ~1.95 s, 24 ~3.9 s (CPU was ~21 s). The prototype scored 12→6 at 89%, 24→6 at 86% and 24→3 at 91%; keep stays at 6 because at 3 one exact-number demotion loses the answer. 1,115/1,115 unit tests.

### 2026-09-21 — Curated plugin starters (release 067ac1d, deployed)

`server/plugin-starters.json` is noevia's starter list: five first-party hosted MCP servers (Exa, Notion, Linear, Hugging Face, Cloudflare docs) and six Anthropic skills, each with a one-line reason. `GET /api/plugins/directory?starters=1` resolves them against the live registry and skills repository (cached an hour), keeps their order and drops any that vanished. The Plugins page shows them as "Recommended by noevia" above each directory until you search. Verified from the deployment host: 5 servers, 6 skills. 1,103/1,103 unit tests; `qa/shared-sidebar` extended and green.

### 2026-09-21 — Ordinary WebDAV clients can write (release 42540fb, web only)

rclone, Finder, Explorer and Obsidian sync send no `If-Match`, so every DAV write was refused (428). Per the user's decision, DELETE and MOVE without `If-Match` use the version read at request time (both reversible); an untagged `Overwrite: T` reads the destination's version (the replaced file goes to Trash); a PUT over an existing file first keeps its bytes in Trash through the companion's new `preserve` op — restorable beside the file as `<name> (replaced <UTC time>).md` — then writes against the version just read. Protected files still require `If-Match`. New `qa/dav-interop.cjs` runs rclone against the real web server and the real companion on a throwaway tenant: 18/18. Web released; the Diary image is not rebuilt (the live Diary stays untouched), and DAV sharing remains off live (`COWORK_DAV_PORT=0`).

### 2026-09-21 — Shared context across a project's Chat and Code modes (release dbfbd92, deployed)

`shared-context.cjs`: `project.sharedContext = { chat, code }`, both off by default, validated on the project config route. Sharing into Code prepends the project's goal, instructions, memories and up to eight recent chat titles to the agent's prompt (not to the task label); sharing into Chat adds up to six recent Code tasks (prompt, status, branch, error) to the system prompt. Both blocks are capped at 6,000 characters and framed as reference data. Edit project shows the toggles only when Chat and Code are both on. 1,101/1,101 unit tests; `qa/project-modes` extended and green at 375/1440 light/dark.

### 2026-09-21 — Code mode can reach granted domains (release 9611580, deployed)

The egress proxy (`code-egress.cjs`, D15) now runs inside web on `CODE_EGRESS_PORT` (8040), reached by the sandbox as `egress` on the internal code network. A Code task approved for network or installs, with named domains, gets a per-task token that allows only those domains on 80/443 and is revoked when the task ends; unset, the capabilities stay unavailable. A granted task now keeps the engine host in `NO_PROXY` — empty, its model calls would have gone through the proxy and been refused as a private address. Live compose: web joins `code` with alias `egress` and gets `CODE_EGRESS_PORT`/`CODE_EGRESS_HOST` (`.bak.before-egress` backups of the override and `.env`).

### 2026-09-21 — index.cjs is wiring (branch `wip/index-split`, release 2ce73df, deployed)

Everything `handleRequestScoped` still carried inline moved into its own module with injected
dependencies and a `routes/` file: the project, source and upload routes (`projects.cjs`), the
provider registry (`providers.cjs`), the models routes (`models.cjs`), the Diary routes and the
connector endpoint (`diary.cjs`), then sign-in/profile/admin, the storage connection, tool
approvals, the chat lists and transcripts, reasoning settings, health, and the HTTP helpers
(`http.cjs`). The member-origin policy shared by providers, storage and the Diary corpus is now
`createEndpointApproved` in `ssrf.cjs`. Each move is verbatim behind one sentinel and mounted in
its original order, so every status code, message, the session and CSRF gate and the three
approval actions answer as before; `index.cjs` is 2,787 → 752 lines and holds only config,
construction, the router and server start. 68 new tests, none booting the server;
`documents.test.cjs` now calls the modules instead of slicing `index.cjs` as text. The Claude
Diary plugin README's revocation section points at Settings → Diary & storage → Connected apps
instead of a deleted script.


### 2026-09-21 — index.cjs in pieces, and a measurement instead of a port (release a4e0178, deployed)

The server's toolboxes and built-in tools, its MCP wiring and its chat loop each moved out of
`index.cjs` into a module with injected dependencies (`toolboxes.cjs`, `mcp-wiring.cjs`,
`chat.cjs`) and a `routes/` file, with tests that never boot the server; the tests that used
to slice `index.cjs` as text now call the modules. Behaviour is unchanged: the approval gate,
the per-user MCP credentials and the project a tool call acts for all travel exactly as
before. `index.cjs` is 4,241 → 2,787 lines.

Removed because nothing called them: the Hugging Face model search and the variants listing
(server routes, front-end wrappers and their types), six helpers in `index.cjs`, a finished
Docling handoff document. Every spec is now linked from the docs index, and the Claude Diary
plugin README no longer points at a script that was deleted.

Measured, with synthetic data: Node spends about 10 µs of CPU per streamed token; the engine
spends 25–90 ms. Nothing is worth porting. The one slow Node path — fitting a long tool
result to the model's budget re-rendered every surviving record on every step — is now
linear: a 500-record listing reduces in 0.5 ms instead of 53, byte-identical. Study and
numbers: `docs/research-language-consolidation.md`; rerun with
`apps/web/scripts/profile-hot-paths.cjs`.


### 2026-09-21 — The Code tab, full height and honest about the network (2d7ba8f)

The chat composer no longer sits under the Code tab, which left the task form half the height
with an unrelated send button below it. And because this server runs no egress proxy, "Reach the
network" and "Install dependencies" are shown unavailable with the reason — and the server no
longer grants them — instead of being accepted and then quietly never happening.


### 2026-09-21 — "Thought for 12s" (bbae129)

A reasoning reply now says how long the model thought — from its first thought to the first word
of the answer, or to the tool it decided to use — measured as it streamed and kept with the chat.
Older chats, and ones streamed on another device, fall back to the length of the thinking.


### 2026-09-21 — A quieter chat footer (5ae8d7f)

The context meter no longer takes a row above the composer to say "Calculated when you send":
a short chat that has not been measured shows nothing, a measured one shows a single quiet line
aligned with the composer, and a long unmeasured chat still offers compaction. It is read when
a chat opens and when a reply finishes, instead of every three seconds for every open chat.
"Thought for 312 words" now reads "Thought · 312 words".


### 2026-09-21 — Templates for new Diary files (a1ededd)

A `Templates` folder at the Diary's root — Obsidian's convention — is offered when a new file is
still empty. `{{title}}`, `{{date}}` and `{{time}}` are filled in (with optional formats, as in
Obsidian); anything else in braces stays as written. Nothing is saved until you save.


### 2026-09-21 — Unlinked mentions (780b8c7)

"Find links to this file" also lists the notes that name it in prose without linking it — whole
words, case-insensitive, never inside code or properties. They are shown, not rewritten: turning
a mention into a link is an edit to someone's note, and edits here are explicit.


### 2026-09-21 — Auto-tune says what it is doing, as it does it (f66ecd2)

A run is 5–15 minutes of a progress bar that can sit still for a minute while the engine
loads, and a still screen reads as nothing happening. Auto-tune now keeps a timed, line-by-line
account: each test and the exact settings it writes, "still loading · 25s" while the engine
loads, every workload's speed and draft acceptance, why a candidate was rejected, what it chose
and why, and whether the original settings were put back after a cancel. It follows the newest
line while running, and folds away once the run is done. The panel now refreshes every second.


### 2026-09-21 — A note's properties, and the tags a vault really uses (5b0e531)

A leading YAML block is shown as the properties it is rather than as three dashes and a list of
keys pretending to be prose; a line the reader cannot parse is shown as written rather than
dropped. The tag filter now also reads the `tags:` property, which is where a diary written in
Obsidian keeps its tags — excluding it meant the filter quietly missed most of them.


### 2026-09-21 — Documents in folders could not be read (c237480)

The Docling sidecar refuses a name that could be a path, and noevia's names are paths, so every
document inside a folder failed with "Document extraction unavailable (HTTP 400)" while a file
at the root worked. noevia now sends the file name. A 400 is also named for what it is — noevia
sending the document wrongly — and stays retryable, so the documents it broke read again on the
next sync rather than keeping a cached failure. Rollback 71f1ab0.


### 2026-09-21 — Typing [[ offers the files you could mean (71f1ab0)

The Markdown editor suggests the files in the folder as soon as you type `[[`, inserts the
shortest name that is unambiguous and closes the brackets for you. Arrow keys choose, Enter or
click inserts, Escape leaves what you typed alone. It stays a textarea throughout — the
suggestions are an offer beside it, not a form control.


### 2026-09-21 — The Docling sidecar is deployed

Document extraction now uses the sidecar that was verified in September and then sat unused:
reading order, table structure, and the Office, OpenDocument, HTML and image formats that were
previously stored whole and unread. CPU-only, so it never contends with the engine for VRAM.


### 2026-09-21 — Obsidian-style [[links]] in the Diary (f72c2a6)

A vault written in Obsidian is full of `[[wiki links]]`, and noevia rendered every one as
literal text and found none of them when asked what links to a file. They now render as links,
open the file, and count as backlinks alongside relative Markdown links. Aliases, heading and
block anchors and the `![[embed]]` form are all recognised; a link to a file that is not there
is shown as the writer wrote it rather than as a button that opens nothing. Nothing is
rewritten: the vault stays exactly as its owner left it.


### 2026-09-21 — Connect an app to the Diary in Settings (6eb1698)

Connected apps is a section of Settings → Diary & storage: name it, copy the credential once,
revoke it in one click. It replaces `diary-connector-admin.cjs`, a script an administrator had
to run on the server. Also removed: two components nothing rendered, and the CSS of two
interfaces that no longer exist (the old Code sidebar and the old Diary landing).


### 2026-09-21 — Code mode runs, and is on (f57dd21)

noevia writes the coding harness's own configuration file — every action class asking, one model
endpoint, no self-update — and refuses a harness whose configuration it cannot pin. A repository
owned by the harness user is used instead of being reported as "Not a git repository". The
sandbox is deployed on an internal network whose only other member is the engine, and a real
task fixed the scratch fixture end to end. Rollback 39b0970.


### 2026-09-21 — Usage: peak hour, favourite model, tool calls (b126eb6)

The usage file gained two counters: replies by hour of the local clock, and one count per tool
call recorded where the call runs. Usage shows a peak hour on a readable clock, the busiest
model and a per-tool list. Older files read as empty rather than needing a migration, and an
account with nothing recorded says so. Rollback 05cc153.


### 2026-09-21 — The project screen (05cc153)

Header actions, context chips above the composer, an Outputs row for the documents noevia made
in the project, labelled recent chats, and a context panel with Context and a Scheduled row
marked not yet available. Covered by `qa/project-screen.cjs` at 1440 light and 390 dark.
Rollback 5379771.


### 2026-09-21 — Nextcloud is a connector of its own (5379771)

Plugins → Connected lists Nextcloud beside Google Drive. It reuses the connection set under
Settings → Diary & storage, says plainly when that connection is missing, not configured on
this server, or at an address outside `MCP_NEXTCLOUD_ORIGINS`, lists the toolboxes it offers,
and carries the same per-tool permissions as Drive — writes can never be “Always allow”.
Rollback 76865e1.


### 2026-09-21 — Routing split; Projects tab (76865e1)

Routing keeps the Auto roles; thinking effort is its own panel; per-project routing is its own
tab. Rollback a73a72d.


### 2026-09-20 — Models page: one tab bar (a73a72d)

Routing, Hardware, Benchmarks and Prompts are tabs instead of sections stacked under the model
list. Rollback d99c066.


### 2026-09-20 — README, icon set, last Cowork prose (d99c066)

The logo's two squares now read as depth in light mode; adds a favicon, Apple touch icon,
maskable icons and a web manifest (none existed). README describes what noevia does today.
Rollback 06f5aa4.


### 2026-09-20 — Add an MCP server by URL (06f5aa4)

Admins can add a server that is not in the registry, with an optional sign-in header (shared
or per account) or OAuth. Same checks as a directory server. Rollback 8b458e9.


### 2026-09-20 — Routing panel spacing and width (8b458e9)

The four Auto role pickers sit two to a row; Default thinking effort is separated from the
save button; disclosure rows and panels share one spacing scale. Rollback b8d78a9.


### 2026-09-20 — The UI and MCP branch is merged into main (b8d78a9)

An overnight deploy of main had replaced the 2026-09-19 UI and MCP work, which was only on
`claude/blissful-brown-v86y3o`. Merged (two conflicts: appended tool-routing tests and
release notes, both kept) and deployed together with Docling and tool-result compaction.
823 server tests, 74 QA suites. Rollback aad6216.


### 2026-09-19 — Models page: faster, cards side by side, one toolbar (06f9402)

The list shows at once while file details load; the folder scan is cached server-side.
Cards up to three per row; tabs, search and filters on one line. Rollback d459867.


### 2026-09-19 — Diary from Code; model and tools panel reworked (d459867)

Diary opens from Code mode. The model panel spreads model and tools side by side on wide
screens, with a segmented Auto/Manual switch, one-line model rows, compact tools and a budget
meter, on an opaque surface. Rollback da5dfa9.


### 2026-09-19 — Per-account API keys for directory MCP servers (da5dfa9)

Admins choose 'Each person uses their own key' or 'Everyone uses this key'; each account adds
its own key in Plugins → Connected and only then gets the server's tools. Rollback 3f3ff1e.


### 2026-09-19 — Hand-registered apps for MCP sign-in (3f3ff1e)

Sign-in services without self-registration: the admin registers an app with the shown return
address and enters its client ID (and secret). Stored encrypted; replacing it signs everyone
out. Rollback c173952.


### 2026-09-19 — Per-account OAuth sign-in for directory MCP servers (c173952)

Servers that ask for OAuth are added through a sign-in tab; each account signs in for itself
from Plugins → Connected and only then is offered the server's tools. PKCE, resource
indicator, refresh; tokens encrypted per account. Rollback e4fc0d3.


### 2026-09-19 — Sign-in keys for directory MCP servers (e4fc0d3)

Hosted servers that need a key can be added: checked before saving, stored encrypted, never
returned, sent only to that server in its declared headers; changeable; admins only. Rollback
6330ea8.


### 2026-09-19 — Skills auto-load; skills and MCP servers from the directory; long model names (6330ea8)

A message matching one enabled skill gets its reviewed instructions. Plugins → Skills adds a
published SKILL.md to a project (arrives needing review). Admins can add hosted MCP servers
from the registry: own toolbox, no credentials, every tool asks, removable. Model names keep
their start and quantization ending; the model list filters. Nine QA suites updated; all 74
pass. Rollback a163543.


### 2026-09-19 — Settings no longer reopens on a quick reload (a163543)

Closing Settings forgets it as the reload target at once. qa/mtp and qa/google-drive pass again.
Rollback 957e972.


### 2026-09-19 — Model picker Tune button back to 44px (957e972)

A later generic button rule had shrunk it to 30px. Rollback ba95afa.


### 2026-09-19 — Engine holds the embedding model beside the chat model (ba95afa)

llama `--models-max 2` (live override edited, backup kept); before a chat model is used, other
chat models are unloaded and the embedding model stays. Tool routing (already on via
NOEVIA_FEATURE_TOOL_ROUTER=true) no longer evicts the chat model. Rollback 41cb2aa.


### 2026-09-19 — Tool routing: "Using:" line and ask-for-more (41cb2aa)

When routing narrows a message's toolboxes the reply says which, and the model can ask once for
the rest of the project's tools. Routing stays off: the live engine holds one model
(`--models-max 1`), so the embedding model would evict the chat model on every message.
Rollback 363171c.


### 2026-09-19 — Re-fit after zoom (363171c)

The page re-stretches after zooming in and back out on iOS. Rollback c71a30d.


### 2026-09-19 — Tall screens: full layout from 520px, pages grow, greeting centred (c71a30d)

A zoomed-out phone keeps the sidebar from 520px wide; short pages grow up to 125% on phones and
tablets; the empty chat greeting sits mid-height. Rollback 70631b0.


### 2026-09-19 — Shrink-to-fit for slightly-too-tall pages and menus (70631b0)

Pages and menus that overflow by a little are scaled just enough to fit (never below 82%);
long lists keep their size and scroll. Rollback f87b157.


### 2026-09-19 — One sidebar for Chat and Code; Plugins page (f87b157)

Code mode reuses the chat sidebar (current look, switch in the header, aligned rail, shared
collapse). Closing Settings keeps you in Code. New chat floats over the list; the collapsed
rail names items on hover; Chat/Code eases in. Google Drive moved from Settings to Plugins,
which also browses the MCP registry and Anthropic's skills. Rollback 027bd00.


### 2026-09-18 — iOS keyboard fix; web image flattened (027bd00)

The keyboard no longer pushes the page up on iOS. The web image had hit Docker's 127-layer
limit; overlay-release.sh now flattens it automatically past 100 layers. Rollback d995cd9.


### 2026-09-18 — Composer focus, iOS keyboard, phone Settings (d995cd9)

No square focus ring in the composer; the app follows the iOS keyboard; legacy narrow phone
Settings rules removed. Rollback 7326ac0.


### 2026-09-18 — Visual pass (7326ac0)

Legibility sweep across sizes, materials and themes with real device user agents; fixed the
phone composer row, phone Settings width, sidebar row alignment. Rollback 4c151be.


### 2026-09-18 — Sidebar header and phone drawer like Claude's (4c151be)

Small Chat/Code switch beside the logo; full-width phone drawer with search on top; the
drawer closes when you switch mode. Rollback 5cd033b.


### 2026-09-18 — Diary in the bottom bar, sliding Chat/Code, project colours (5cd033b)

Diary beside Search; liquid-glass Chat/Code thumb; phone Code drawer works; project colours
everywhere. Rollback 5a0e026.


### 2026-09-18 — Icon centring scoped; row options beside the title (5a0e026)

Only icon-only buttons centre their icon; sidebar row options no longer cover the title.
Rollback 350050e.


### 2026-09-18 — Composer like Claude's, SVG icons (350050e)

Centred SVG + with a files-and-tools menu (no duplicate model entry), Thinking as a menu of
levels, Code keeps a closed sidebar, every icon an SVG and centred. Rollback 91a89ba.


### 2026-09-18 — Account menu and Search like Claude (91a89ba)

Light/dark in the account menu, Search beside the account, account menu unclipped from
the rail, clean rail Chat/Code, no blank page entering Code. Rollback 94909d3.


### 2026-09-18 — Collapsed sidebar like ChatGPT's (94909d3)

Icon-only rail with the avatar at the bottom, remembered per device, expands from its
empty space. Rollback 4152d15.


### 2026-09-18 — Settings and sidebar organised like ChatGPT (4152d15)

Sidebar order Pinned, Projects, Recent chats. Settings is one flat list: General, …,
Security and login, Account; renamed pages, same content. Rollback 95eacd6.


### 2026-09-18 — Sidebar as one scrolling plane (4ea3282, 95eacd6)

Like ChatGPT: one scrolling rail, Diary and Plugins with the top destinations, flat
Projects/Pinned/Recent lists, only the account pinned, every chat listed. Rollback 4ea3282.


### 2026-09-18 — Material 3 and phone fixes (265c650, 6930549)

The Material material is now Material 3 component by component; touch fields are 16px
everywhere; narrow Appearance controls fit; Projects counts active projects; sidebar lists
never collapse to their heading. Two guarded overlays after verified backups; five
services healthy. Rollback 265c650.


### 2026-09-18 — Phone review fixes (3d20de0, a2a1c8e, e777259)

Three guarded web-only overlays over d11cfac, each after a verified appdata backup.
The phone drawer is whole from any view, Diary/Plugins are never under the footer,
row menus are no longer clipped, theme previews and the selected ring are correct,
Settings rows align, the strip no longer reports a false outage at start, and desktop
list headings stay in view. Five services healthy after each. Rollback a2a1c8e.


### 2026-09-18 — UI overhaul release 3 and phone-review fixes

Deployed d11cfac over ab2720a as a web-only overlay (no dependency changes). 861 web tests,
typecheck, design lint and a fresh build passed first; appdata backup ab_20260918_112354.
Five services healthy, zero restarts, native engine untouched. Live browser QA was partial
(write-approval card, phone width, themes and accents still owed). No real Diary corpus used.
Rollback ab2720a with .env.bak.before-d11cfac; see deployment.md.


## 2026-09-14 — Qualified direct native inference in production

### 2026-09-14 — Markdown date/tag filters

Deployed 48432fe: bounded stored-file search supports inclusive filename dates and
whole hashtags, alone or combined with text. 426 web tests, 343 Linux image tests,
CI and synthetic six-size/two-theme editor checks passed. Production health and
ordinary-chat smoke test passed; no real Diary corpus used.


### 2026-09-14 — native model UI and mobile approvals

Deployed 02495a7: embedding/reranking excluded from chat selection, accurate native
MTP guidance, 44-pixel approval targets. Full arguments and three decisions verified
in six viewports/both themes. 424 web tests, 343 exact-image server tests and CI
passed. Production synthetic chat and all four service health checks passed.


Switched the existing 2570a02 app release to pinned native llama.cpp with guarded
GPU and isolated app/client workload tests. Preserved existing model IDs, shared
provider settings and rollback backups; retained Lemonade stopped for recovery.
Verified live phone chat, 32k context and actual MTP counters; archived synthetic
verification chat. Added repeatable native and populated mobile QA. No real Diary
corpus testing, migration or reindex. See deployment.md for exact rollback.

# Changelog

## Mobile viewport and native adapter release — 2026-09-14

Production web, Diary and OCR run **2570a02**, replacing 55b2767. Mobile composers
remain reachable at keyboard height; model/settings dialogs follow the visible
viewport and phone telemetry uses one scrollable row. Direct llama.cpp support
is included, while the active production inference backend remains Lemonade.
Native GPU workload qualification and cutover are still outstanding.

Verification: 423 local web tests, typecheck/build, seven viewport sizes in both
themes, keyboard/draft/zoom regressions, all personal settings categories, Diary
calendar/list and Markdown conflict/save checks, native profiles and model guidance.
The exact Linux candidate passed 342 server tests and 221 Diary tests (two existing
dependency warnings). OCR image matches the previously verified image. GitHub CI
passed. Backup `ab_20260914_031839` verified web/Diary state before the installed
mount preflight performed rollout. All three services are healthy with zero
restarts/OOM; web and internal OCR probes return 200. Public assets match
`index-DZyp8_tE.js` and `index-D7vxMZ0U.css`, with `/viewport.js` present.

Authenticated production checks reproduced and resolved the short-height composer
bug, verified populated model selection and administrator settings, and completed
a synthetic ordinary-chat inference returning `MOBILE_OK`. That test chat was
archived. No real Diary prompts, corpus edits/import or model configuration changes.
Retain 55b2767 and `.bak.before-2570a02` env/Compose backups for rollback.


Newest first. Merged from `QA-2026-09-08.md` and `review-fixes.md`.

Dependency audits report known advisories; they are not a guarantee that software
is free of vulnerabilities. Keep dependencies, the host, and the inference services
updated.

---

## Calendar landing rollout — 2026-09-14

All three services run **5894266**, replacing a6d15c3. Diary opens on the current
month with Calendar selected, a List toggle above, and the composer below.
404 local web tests, typecheck/build and synthetic responsive/draft recovery
checks pass; the candidate passes 324 serial Linux server tests. Diary/OCR image
IDs are identical to the prior release's verified images (199/13 tests).
Mount preflight passed; all services healthy, zero restarts/OOM; web and OCR
health return 200. Public JS/CSS hashes match index-CdTrv7d0.js and
index-Bm_DWXB9.css. Authenticated production Diary opens with Calendar selected
and date markers loaded. No prompts sent or corpus edits. Retain a6d15c3 and
.bak.before-5894266 configuration backups for rollback. This record is
documentation only; deployed application source remains 5894266.

## Diary workspace, model guidance and context rails — 2026-09-14

Production now runs **a6d15c3** on web, Diary and OCR, replacing fca1f19.
Includes guarded Markdown editing/recovery/navigation, explicit hardware and
memory guidance, and continuous context rails that move below narrow content.
GitHub main includes all five application commits.

Validation: 404 local web tests, typecheck/build and synthetic responsive editor
checks pass. Exact candidate images pass 324 serial Linux server tests, 199 Diary
tests (two existing dependency warnings), and all 13 OCR tests with fixtures.
The installed writable-mount preflight passed. All three services are healthy
with zero restarts/OOM; web setup-status and internal OCR return HTTP 200.
Public JS/CSS hashes match the tested build (index-CXIpF5Wf.js and
index-DGAF1v_V.css). Authenticated production reload succeeds, and the project
view has one transparent context rail. No real Diary prompts or corpus edits.

Retain fca1f19 and config/Compose backups .bak.before-a6d15c3 for rollback.
No environment schema, mounts or model configuration changes. This documentation
commit records the rollout; deployed application source remains a6d15c3.

## Chat context budgeting and compaction — 2026-09-10

Added ordinary/project-chat context meter above the composer with an expandable
breakdown of messages/summary, instructions/memory/sources, tools, generation
reserve, safety buffer and free space. Counts are conservative UTF-8 estimates,
not exact tokenizer or account totals; unknown limits use a labelled 8k fallback.
Lemonade uses the loaded model's configured ctx_size, not its architecture maximum.
The first prepared request establishes the meter; later visible output updates
its estimate. Existing chats can use Compact chat before sending another turn.

Manual and automatic compaction summarize older exchanges with the selected
provider, preserve two recent exchanges verbatim, and keep the full visible/saved
transcript. Summaries are private per-user/per-chat files and exact-prefix hashes
invalidate them after edits. Failed/unusable/truncated summaries retain previous
context; oversized sources/recent messages fail clearly rather than being dropped.
Compaction is lossy and may omit details. Diary's separate journal is unchanged.

Requests reserve up to 4,096 generation tokens and 15% estimation margin; automatic
compaction triggers when input exceeds the remainder (about 72% for 32k). High
effort cannot expand or discard this budget. Tool continuations are rechecked;
context errors inside SSE are surfaced, and heartbeat frames cover silent waits.
No automatic retry of tools or writes. Configured capacity is not a guarantee of
available shared-backend memory, and non-Lemonade model limits remain a fallback.

338 tests, typecheck/build, and synthetic browser QA pass: manual/automatic
compaction, transcript retention, cache reuse, failure handling, streamed errors,
375/768/1440 widths and both palettes. Deployed `ae39000`; all three services
healthy, public assets match, 290 Linux server and 13 worker tests passed. No private
financial data, Diary prompts, model reloads or live corpus changes used in QA.

## 2026-09-10 — shared Diary server connector and Nextcloud push repair

Deployed `12a1646`: dedicated revocable Diary credentials and live version-checked
Markdown tools. Stale saves conflict rather than overwriting newer files. Private
Claude plugin prepared; import and a real Claude round trip remain outstanding.
The plugin identifies itself as `noevia-diary/1.0` because production rejects the
default Python client identifier. Synthetic tests pass; no corpus edits performed.
Nextcloud push now uses its internal Apache callback; six self-tests pass before
and after restart. Rerun the repair after AIO recreates the push container.

## 2026-09-10 — oversized PDFs and native local-Qwen thinking

Deployed `ddbe852` (including `2408c32`). PDFs up to 60 MB receive asynchronous
native-text extraction and image compression before the 25 MB storage limit is
applied. Validated compressed PDFs and labelled text-only fallbacks use distinct
filenames; originals remain on the user's computer. Invalid, encrypted and
unrecoverable inputs fail without replacing existing sources. Local Qwen Low/High
now uses the actual thinking-template switch rather than a hint. Default remains
provider default. The exact installed 9B GGUF lacks MTP weights; support in the
original architecture does not make this file MTP-capable.

329 web tests, typecheck/build, synthetic browser checks, 281 Linux server and
13 real worker tests passed. Health/public assets verified. Shared Diary editing
is designed around version-checked server access; the Claude adapter is not yet
configured. Nextcloud's push self-test found a reverse-proxy trust failure, while
Mac upload-queue health remains unverified. See `spec-diary-shared-editing.md`.
No real Diary writes, corpus reconciliation or model changes were performed.

## 2026-09-10 — MTP controls, acceptance and fixed inference footer

Deployed `cac1778`, including `df8a486` (New chat launch) and `8eb7b99` (native
MTP Yes/No load controls and permanent inference footer). Chat and Diary show
actual acceptance: cumulative backend counters when available, otherwise the
current user's last response timings, labelled accordingly. Installed llama.cpp
b9632 uses the latter and updates at completion. Unsupported models explain why
MTP cannot be enabled; existing GPU/cache/context settings survive changes.

325 web tests, 178 Diary tests (3 skipped), typecheck/build, synthetic browser
checks, 277 isolated Linux server tests and eight worker tests pass. The Diary
wheel-scroll regression timed out during concurrent browser runs and passed on
its isolated rerun. All three services run `cac1778` with zero restarts/OOM;
Diary healthy, web/OCR 200, public assets match. No production model loads or
real Diary corpus tests. Multi-GPU benchmarking and compatible external draft
models remain experiments. Broader roadmap testing pause continues.

## 2026-09-10 — live Diary progress and long-request connection

Deployed `3ef0501`. Diary now streams real provider thinking/answer output while
retrieval and capture stages report their progress with an elapsed timer. Optional
tool traces stay on their turn. Immediate response headers and keep-alives prevent
silent long-running exchanges from waiting for capture before responding. Proxy
HTML is sanitized, interrupted saves are explicitly unconfirmed, and there is no
automatic resend. Switching app views keeps the mounted exchange; full page reload
recovery remains open. 319 web tests, typecheck/build, 177 Diary tests (3 skips),
synthetic browser regressions, 271 Linux server and eight worker tests passed.
All services healthy; public build assets match. Broader roadmap remains paused.

## 2026-09-10 — Diary reading and reasoning feedback

Deployed `ecaaa73`: saved summaries are a separate disclosure during the active
conversation; the day composer stays outside scrolling content. Diary and normal
chat stop following output when the reader scrolls up. Provider reasoning reaches
the Diary thinking disclosure separately from journal text and follow-up history.
Diary reasoning arrives at completion, only when the provider supplies it; live
Diary streaming and durable full conversation history remain open.
315 web tests, typecheck/build, 172 Diary tests (3 skips), synthetic browser checks,
267 candidate Linux server tests and eight worker tests passed. All three services
run the release, public assets match, zero restarts/OOM. Broader roadmap paused.

## 2026-09-10 — skill metadata names the file to load

The existing skill index now supplies exact filenames, escapes metadata as JSON,
and bounds catalogue size. Tool permissions and source loading remain unchanged.
314 web tests, typecheck/build and 171 Diary tests (3 skipped) pass, including a
real-handler prompt assertion. Full instruction-skill lifecycle remains planned.
Deployed `79cd24f` after 267 Linux server and eight worker tests. Wizard and
limited default-off DAV shipped in `9e2bfbb`.

## 2026-09-10 — explicit Diary and storage choices during setup

Fresh setup asks Diary/chat before account creation. Storage offers server-held
or existing external service choices; skipping and failed saves preserve the
configuration. The picker waits for saved settings before editing or saving.
Admin preferences include the existing thinking default. 310 web tests,
typecheck/build, 171 Diary tests (3 skipped) and expanded synthetic browser checks
pass. Existing completed users remain completed. Rollout pending.

## 2026-09-10 — optional bounded Diary file sharing

Added a separate, default-off listener and per-user sharing controls. Supported
Markdown reads/property lists/conditional writes use the existing tenant file API.
App-password scope and configured transport are enforced. No port is published by
default. Full DAV/file-manager compatibility remains open. 310 web / 171 diary
(3 skipped), typecheck/build and synthetic real-app browser checks pass. Rollout
pending; production sharing will remain off.

## 2026-09-10 — revocable device app passwords

Per-user name/scope/date metadata, shown-once random secrets, Argon2id hashes and
individual revocation are available in Profile & security. Credentials do not
permit account login or chat. Sharing remains unavailable; no new listener opens.
304 web / 171 diary tests (3 skipped), typecheck/build and synthetic real-app
browser checks pass. 257 Linux server and eight worker tests passed; deployed `2525de5`.

## 2026-09-10 — DOCX main-body text and tables

Unified uploads and connected-folder refresh retain originals and extract bounded
DOCX body/table text in the private worker, with explicit partial-coverage labels.
Malformed replacements clear stale text and remain downloadable; no dependencies
or corpus changes. 301 web / 171 diary tests (3 skipped), typecheck/build, six
local worker tests and synthetic real-worker browser QA pass. 254 candidate Linux server and eight worker tests passed; deployed `e18f1de`. See the roadmap audit for parser limits.

## 2026-09-10 — engine throughput omits unstable short samples

The display labels the engine rate as reported and omits invalid or sub-second
count/rate samples instead of displaying timer-dominated spikes. Valid longer
samples remain untouched; missing values stay unavailable. 297 web / 171 diary
tests (3 skipped), typecheck/build, live read-only sample and manual UI check pass.
This is sample filtering, not a repaired upstream benchmark. Deployed `3b1e256`.

## 2026-09-10 — reasoning-only output is no longer presented as an answer

The final-answer channel now reports that no final answer was returned instead of
copying internal narration. Per-round tracking covers tool continuations, retaining
tool results and separate reasoning. No extra inference/tool retries. 295 web /
171 diary tests (3 skipped), typecheck/build and synthetic real-server browser
verification pass. Model output quality remains a separate limitation. Deployed `34df7c2`.

## 2026-09-10 — thinking effort reports what the provider receives

Added admin defaults, project/free-chat overrides and optional Diary extras effort
controls beside model selection. Documented GPT-5.4 on OpenAI receives a parameter;
other pairs get labelled hints. High hints request an explicit 8,192-token budget,
with field-rejection fallback. Default leaves the request unchanged. The companion
and approval gate remain unchanged. 292 web / 171 diary tests (3 skipped),
typecheck/build, synthetic real-server/browser checks and local inference pass.
Uncapped budgets and wider provider verification remain out of scope for this v1.
Deployed `6570c51`.

## 2026-09-10 — Diary components are easier to maintain

Landing, calendar and context sidebar are extracted from dense inline JSX.
Existing navigation, storage and composer behavior remains; Up honors busy like
other file navigation. 281 web / 171 diary tests (3 skipped), typecheck/build,
both synthetic browser suites and manual calendar review pass. Deployed `7a34a0a`.

## 2026-09-10 — Diary landing reflects its actual contents

Empty diaries show a first-entry composer without a fictitious month. Populated
diaries show memory files, recent entry dates and tenant Raw Sources Markdown,
with month navigation below. Loading/errors do not masquerade as empty diaries.
Operator-wide import paths remain administrator-only. 281 web / 171 diary tests
(3 skipped), typecheck/build, synthetic browser and manual layout checks pass.
Deployed `8edacf7`.

## 2026-09-10 — first-entry folders survive interrupted writes

New corpora receive Entries, AI Memory and Raw Sources seed READMEs with their
first logged exchange. Create-only writes use the existing durable journal and
ETag recovery, preserving existing files and avoiding duplicate entries on retry.
Existing/imported entry corpora are not migrated. AI Memory files join direct
context reads without copying legacy memory. 171 diary tests (3 skipped), 281 web
tests, typecheck/build and synthetic manual verification pass. Deployed `b34c33f`.

## 2026-09-10 — older entries remain available without semantic matches

The companion now falls back to bounded direct tenant file reads when semantic
retrieval is missing, empty or fails. It reads two explicit past ISO dates plus
three preceding days by default, within shared context limits. References state
the limited scope; successful semantic matches avoid extra reads. Existing daily
and monthly layouts remain the single source of truth. No write path changed.
166 diary tests (3 skipped), 281 web tests, typecheck/build pass. Deployed `23ba691`.

## 2026-09-10 — landing Diary messages follow the selected day

Landing messages previously stayed in a hidden home conversation. Send now opens
the destination day first, preserving its existing history, local/streamed replies,
retry state and optional-tool approval scope. Past-day selection and timestamps
stay unchanged; cancellation never starts capture. 281 web tests, typecheck/build,
157 diary tests (3 skipped), synthetic browser regressions and manual review pass.
Deployed as `5b1ef12`.


## 2026-09-10 — resumable member onboarding and explicit Diary choices

Invitations inherited a completed-onboarding default, skipping setup entirely.
New invitees now start incomplete, and members get Diary/preferences/passkeys
without administrator setup or global model controls. Saved Diary choices hydrate
the wizard immediately; updates persist with visible failures and retained focus.
Back and sign-out/resume clarify navigation; the dead-end models step is removed.
Completion preserves existing consent and defaults missing rows off. The separate
legacy feature backfill no longer re-enables missing rows on each restart.

Verification: 278 web tests, typecheck/build, 157 diary tests (3 skipped, two
existing warnings), synthetic real-server browser regression and manual review.
Application **`baf38aa`** is deployed to all three services, replacing `66af1ad`.
All 234 server tests passed in an isolated production-host image; 42 scoped live
assertions passed, including synthetic invitation/resume/completion/role boundaries
and cleanup. Public UI served the final bundle without resetting the existing user
into onboarding. Five synthetic accounts were removed; no real diary prompts or
corpus changes. `.bak.before-baf38aa` config/Compose/override and the previous
release remain for rollback. Tailscale was restored to stopped.


## 2026-09-10 — shared composers and opt-in Diary context

Project landing pages and Diary lacked the composer controls, and free chats could
not retain their own attachments/tool selection. All functional chat composers now
share the + menu. Diary extras are opt-in for the current session and off on reload;
its normal retrieval/capture remains active. Preparation uses the existing MCP
approvals and tool loop, then supplies bounded reference to the diary companion.
Attachments stay outside the diary corpus. See the audit for test evidence and
behavioral boundaries.


## 2026-09-10 — composer files and tool controls

Tools and uploads were buried outside the conversation. A + control now opens
a compact menu above the chat composer: Files and photos, Tools grouped into
Built-in/Connectors, and Model and routing. Project tool selections use the
existing permission-checked configuration route; all three write approvals remain.
Uploads retain the existing file limits, organized Nextcloud storage, and progress.
No skills or plugin execution features are implied by this menu.


## 2026-09-10 — unified uploads and visible processing

Application release `48027ef` replaces `e3b29bb` in production. One Sources upload
control now accepts non-archive originals up to 25 MB, including DOCX. Connected
storage receives Documents/Images/Text/Other subfolders; the UI uses the same
groups. Opaque formats remain stored-only, with authenticated original downloads
and explicit model-context disclosure. Images retain a bounded local cache for
inference; the 8 MB image-input budget is separate from the storage limit.

Earlier local image uploads are copied to connected storage on refresh. Transfer
percentage and per-file elapsed time are distinct from saving/extraction stages;
image chat exposes preparation status before model processing. The obsolete 1 MB
background request cap and 40-file refresh cap were corrected. The project quota
remains 60 total sources, with regression coverage for a 41-file refresh.

Verification: 256 web tests, typecheck/build, and 155 diary tests passed (3 skipped,
two existing dependency warnings). Local browser checks covered mixed uploads and
mobile source rows. Authenticated production checks uploaded synthetic PNG, PDF,
and DOCX files through one chooser, confirmed Documents/Images storage paths,
OCR-ready PDF metadata, original links, timing details, and successful refresh.
Image preparation feedback appeared at 0.2 seconds in the synthetic chat check;
the model correctly identified the shapes, colors, and ZEBRA-73 heading in 21.9
seconds. The synthetic chat and project were archived after verification.
The diary corpus and private financial files were not used for testing.

Deployment used the existing Tailscale configuration because the LAN route was
unavailable. All three service images use `48027ef`; prior release and
`.env.bak.before-48027ef` / Compose backups are retained for rollback. Tailscale
was restored to its previous stopped state after deployment and verification.


## 2026-09-10 — bounded reliability, OCR and image rollout

Production now runs `e3b29bb` (previous `cd717b0` retained). This includes the
agent deployment contract, duplicate tool-call protection, page-aware PDF source
retention/status, binary source reads, isolated local OCR, and image handling fixes.
All changes were pushed to main after 247 web tests, typecheck/build, 155 diary
tests (3 skipped), and three real OCR container tests passed.

Lemonade 10.8.0's Qwen 9B registration now loads its matching mmproj. Synthetic
inference recovered an invoice, dated/signed amounts, and total; authenticated
production chat identified a blue circle, orange triangle, and ZEBRA-73 from a
separate image, then correctly cited the scanned second PDF page and its values.
A synthetic mixed PDF uploaded through Nextcloud and showed OCR-ready status and
an Original PDF link. No real diary prompts or financial-document tests were used.

The live Compose Manager file now includes the internal OCR network and service;
web can reach OCR health, diary is healthy, and all three images use `e3b29bb`.
Compose/env backups carry `.bak.before-e3b29bb`; the Lemonade registration backup
is `user_models.json.bak.noevia-vision-20260910`. OCR preserves original/native
text, labels its output, and enforces documented resource limits. Existing PDFs
need refresh/re-upload. OCR accuracy, complex tables, and handwriting still need
human checking; interrupted polling after a server restart requires retry.


## 2026-09-08 — development continuation and QA

Based on a clean `0f8a9c1` checkout. The older UI master prompt was treated as
design context; much of its implementation was already present.

### Environment and build

- Fresh startup creates the state directory before writing its encryption key.
- **Dev, build and type-check scripts now invoke Node directly**, fixing the
  long-standing "`npm run typecheck` is broken" workaround. Vite uses the runner
  config loader, avoiding temporary writes inside the external dependency symlink.

### Projects and sources

- New project folders include the project ID, preventing same-name projects from
  sharing a folder. Existing paths preserved.
- Uploading to an older project creates its missing storage folder on demand.
  Without remote storage, text/PDF uploads remain usable as local sources. S3 uses
  a prefix instead of an unsupported directory operation.
- Image/document request caps account for base64 expansion while keeping
  decoded-byte limits — a 7 MB image no longer fails the advertised 8 MB limit.
- Failed source reads preserve the previous source text. Successful empty listings
  and explicit detachment still remove old sources.
- A refresh preserves uploads and folder changes made while it was awaiting
  storage. Opening a project refreshes attached folders, throttled to once a minute
  for the same folder selection.
- Invalid project settings no longer partly mutate the live project.
- Debounced edits merge different changed fields instead of dropping all but the
  last patch. The edit dialog awaits saving and retains input on failure.
- Model/routing/toolbox save errors are displayed rather than silently ignored or
  becoming unhandled rejections.

### Vision

- Probes are scoped to endpoint, credentials and model, with expiring results.
  Missing projectors and availability failures now have **distinct, actionable
  explanations** shown in chat — previously a 500 ("maybe missing mmproj") was
  conflated with a 400 ("model cannot do this"), which is what led to
  "Qwen3.5-9B is blind" being asserted wrongly.
- Image-description cache keys include the user, provider endpoint and full
  question. Provider authorization runs before image requests; vision requests
  refuse redirects and respond to chat cancellation.

### Tools and approvals

- Repeated tool calls across inference rounds retain distinct chip identities.
- Pending approvals keep their full arguments and all three decision buttons.

### UI and accessibility

- Mobile chat breadcrumbs truncate long names without hiding Settings or the
  inspector. Project headings reserve inspector space. Tool results use a compact
  layout; approval arguments remain fully visible and wrap.
- Mobile Settings uses a category selector so forms get full width. Provider fields
  have accessible labels. The diary navigation-expand control is restored on phones.
- Project/model dialogs use native modality, Escape dismissal and focus restoration.
  Keyboard activation of a card's child controls no longer opens the project.
  Filter/archive empty states are explicit.
- Creation uses shared text-file validation rather than reading arbitrary selected
  binaries as text. Project initials use theme text contrast; the initial browser
  theme colour matches the dark canvas.
- `MarkdownPreview`: parenthesized links and tables now render.

### Verification

Web **161 passed** (11 new regressions); diary **145 passed, 3 skipped** (no diary
implementation changes); typecheck, build and `git diff --check` all passed.

Browser checks used an isolated authenticated instance at localhost:8022 with
disposable state and a local inference simulator — no production diary messages,
files or tool writes were created. Phone (375), tablet (768) and desktop (1440)
layouts in both themes, plus chat overflow at 320/640/641/1024 with no clipping or
horizontal overflow. Exercised onboarding, project creation, model selection,
failed-chat retry, two successive clock-tool rounds, Markdown tables/code/
parenthesized links, settings, diary home/calendar/error states, coding preview and
keyboard modal/card controls.

Docker was unavailable on the Mac; container builds and Compose validation were not
run locally. A live RAG/embedding smoke test remains necessary.

### Deployment note

Read-only SSH confirmed the deployment host still ran `0f8a9c1` with a healthy diary
container. The patch introduced no required environment variables. Publishing and
deployment were subsequently approved; rollout is recorded in the deployment host
changelog. Existing projects that already share a folder are **not** automatically
split or moved.

---

## Earlier — diary conversation and reliability update

Diary questions now receive thoughtful replies directly in the diary conversation.
**The separate Insights screen, reflection endpoints and activity badge were
removed.** The logger still preserves the user's own words separately from
assistant commentary.

Clearer diary and chat composers, consistent focus states, better text contrast,
calmer cards, mobile layout adjustments, reduced-motion support. Setup completion is
acknowledged by the server before exiting, and unfinished onboarding resumes after
sign-in.

### Reliability and security

- Streaming errors use SSE after headers are sent. Split SSE lines are retained; all
  provider fetch paths refuse redirects and respect cancellation signals.
- Retry identifies the exact failed final message and preserves earlier history.
- Provider deletion updates the correct private/shared collection.
- Diary edits report pending writes honestly. Durable invalidation prevents stale
  retrieval after a crash, and pending operations replay in order.
- S3 storage enforces conditional writes; a disposable capability probe rejects
  unsupported servers before writing diary data. Bucket listings paginate.
- Members can connect only to operator-approved origins, avoiding DNS-rebinding
  exposure from member-controlled endpoints. Existing shared providers remain
  usable — see `SECURITY.md` for `MEMBER_OUTBOUND_ORIGINS`.
- External import folders require administrator access. Requests, import reads,
  session histories and pending Nextcloud login flows are bounded.
- Tenant UUID validation is strict; legacy migration applies only to the designated
  owner. Cache eviction no longer closes active requests' resources.
- Browser security headers protect against framing and MIME sniffing. Node runtime
  builds use the lockfile without falling back to an unlocked install.
- Auxiliary inference uses the documented endpoint/key fallback.
- The Python installer was upgraded past a known advisory.

### Verification

Node suite covers provider deletion, first-round model failures, split SSE, redirect
refusal, request limits and approved-origin checks. Diary tests cover failed-edit
acknowledgment, crash recovery, stale-retrieval exclusion, empty-document cleanup
and refusal of nonconforming S3 stores. The UI was exercised with an isolated local
fixture using synthetic responses.

---

## 2026-09-09 — deployed `f6832bf`

Three commits shipped to the deployment host, replacing `8a78172`:

- `d8a6f2c` journal poison pill — one malformed entry no longer blocks every
  subsequent diary write.
- `def7c18` state directory permissions — parents of a nested state path took the
  umask rather than `0o700`.
- `f6832bf` docs consolidated from ten files to nine; the old
  `noevia-design-system.md` palette was stale and would have reintroduced the
  fire-engine red the UI overhaul removed.

Verified before push: 162 node, 147 python + 3 skipped, typecheck clean, on `main`
rather than on the feature branch. Verified after deploy: both containers on
`:f6832bf`, diary healthy, the poison-pill fix present *inside the running
container*, `localhost:8021` and `https://legacy-noevia.example.com` both 200, no
errors or tracebacks in either container log since restart.

**Not yet verified against real data** — these need an authenticated browser
session and were not done: a real diary write (the poison-pill fix is in exactly
that path), a Nextcloud upload, and one MCP write approval.

Rollback: `releases/8a78172` is on disk; repoint `current` and `COWORK_VERSION`,
then rebuild. Env backup at `config/.env.bak.20260909203405`.

### Incident during this deploy

The working tree's entire `docs/` directory disappeared mid-session — all nine
files at once, after they were committed and pushed. This is the same Nextcloud
eviction that previously ate `dist/assets` and `node_modules`. Nothing was lost
(`git checkout -- docs/` restored it, and `origin/main` was never affected), but
it is a reminder that this checkout lives on a sync client that removes files
underneath you. Commit early; do not treat the working tree as durable storage.

## 2026-09-09 — aux model 404, found while verifying the deploy

`LLM_AUX_MODEL` was the literal string `default` on the live deployment, because
`DIARY_AUX_MODEL` was never set and every compose file fell back to that
placeholder. No backend serves a model by that name, so **every** summariser,
skip-classifier and index-maintenance call had been 404ing — for at least five
days before it was noticed.

It hid because the pipeline degrades gracefully: `summarizer failed (...);
logging verbatim assistant reply`. Entries kept being written correctly and only
lost their `— Topic` headers. September 5–9 have 0 topics across 75 time headers.

Fixed in three places, because a fix in only one of them leaves the trap armed
for the next deployment:

- **Live `.env`**: `DIARY_AUX_MODEL=gemma-4-E2B-it-GGUF-UD-Q4_K_XL`. Verified the
  aux model now returns 200 on the exact call that was failing.
- **compose.yaml, deploy/examples/unraid-compose-manager.yml, and the live
  compose-manager copy**: `${DIARY_AUX_MODEL:-${DIARY_CHAT_MODEL:-default}}`.
  This mirrors what line 36/37 already did for `llm.aux.base_url` and
  `api_key` — the aux *model* was simply never given the same fallback.
  All three interpolation cases verified against real `docker compose config`.
- **services/diary/agent/config.py**: `_resolve_aux_model()` treats an empty or
  placeholder aux model as "reuse the chat model" and logs a warning naming
  `DIARY_AUX_MODEL`. This catches every deployment path, not just compose. Four
  tests, including that an explicit aux model is never overridden and that a
  wholly unconfigured pair is left alone rather than guessed at.

Historic entries were **not** backfilled. `/api/relog` looks like the tool for it
and is not: it re-logs an exchange from the *current in-memory session* at
`now=datetime.now()`, with an empty `sub_header`. Pointed at old entries it would
append duplicates stamped today rather than repair anything.

Tests: 151 python (+4), 162 node.

Synthetic source refresh also passed through the browser's background polling
path. The QA project and chat were archived (recoverable); their invented fixtures
remain available for review. The temporary OCR test container and host fixtures
were removed. Production remains on the tested application release `e3b29bb`.

Composer release `3320fc3` is deployed, replacing `48027ef`. All three service
images use the new tag; `.bak.before-3320fc3` config/Compose backups and the prior
release are retained. Diary health passed and web-to-OCR health returned 200.
The authenticated production browser verified a composer upload to Nextcloud and
enabled Nextcloud Files using the new menu. Qwen on the real Lemonade endpoint
then made exactly one `nc_webdav_list_directory` MCP call against the synthetic
project's Documents folder. The successful result named the synthetic DOCX; the
exchange took 23.7 seconds. This was a live integration test, not a locally
configured MCP endpoint. The QA chat/project were archived, local QA server and
tabs closed, viewport reset, and Tailscale restored to stopped. No real diary or
financial corpus was used.


Shared-composer rollout: application `12ba04f` replaces `3320fc3`. All three
production images use the new tag. `.bak.before-12ba04f` environment/Compose
backups and the previous release are retained; no environment/schema additions
were needed. Diary health passed and web-to-OCR health returned 200. The live
authenticated browser confirmed the new Diary + menu and extras OFF by default.
No production diary prompts were sent, nor were extras enabled against the real
corpus. Execution/approval tests used isolated synthetic inference, MCP, and diary
fixtures; the earlier real MCP integration test remains recorded above. Temporary
QA servers/tabs were closed, viewport reset, and Tailscale returned to stopped.

Live reliability audit rollout: `4ec8269` is now deployed to all three services,
following `cfc3a05` and `12ba04f`. Fixed repeat legacy migration into new admin
accounts, stale image input after oversized replacement, and administrator
deletion blocked by issued invitation/recovery tokens. Deletion also preserves
the last active admin when other admins are disabled. All three fixes passed
live rechecks; 266 web tests, typecheck/build, 157 diary tests (3 skipped), and
222 server tests inside the built image passed. Real Nextcloud approvals, OCR,
vector retrieval and isolated diary capture were exercised. Synthetic accounts,
corpora and the QA Nextcloud folder were removed. No real diary prompts/corpus
changes. Backups `.bak.before-cfc3a05` and `.bak.before-4ec8269` and previous
releases retained. [Coverage and remaining concerns](roadmap.md).

Composer model placement: `dc325d5` deployed to all services, replacing `4ec8269`.
Removed the chat-header model selector and placed it beside Send inside the text
composer, keeping the existing picker/routing behavior. Long labels truncate on
mobile. 266 web tests, typecheck/build and 157 diary tests (3 skipped) passed;
synthetic browser layout/switch/send checks and the live picker check passed.
Thinking-effort options are a future follow-up. `.bak.before-dc325d5` backups and
the prior release are retained; no environment/Compose changes were needed.

Shared composer controls: `66af1ad` deployed, replacing `dc325d5`. Project landing
and Diary home/day composers now share the model-button component and placement
used in free/project chats. Diary shows its fixed companion until extras are
enabled; the enabled picker configures optional context only. Thinking options
remain planned. Tests: 266 web, typecheck/build, 157 diary (3 skipped). Synthetic
mobile/desktop and light/dark checks, scoped picker checks, live project/Diary
checks and service health passed. No real diary prompts or corpus edits.

## Model manager: settings-native styling, layout mode, working search — 2026-09-17

Settings → Models & routing now draws on the same surfaces, radii, type scale and control
sizes as the rest of the settings pane; see design-system.md. No class names or tab
structure changed.

Hugging Face search no longer asks the hub for `full=true`. That parameter existed only to
fill in a per-repo GGUF file count, and it made the hub serialize every sibling file of
every hit — against the client's 20s timeout an ordinary browse of the top 30 GGUF repos
could time out and surface as "Network error" with an empty list. The count is now shown
only when the hub volunteers it. A named search that the `gguf` tag filter answers with
nothing is retried once without the filter and narrowed to repos that look like GGUF, so a
repo the hub has not tagged is still findable; browse mode (no query) is not retried, since
an untagged top-30 is not a GGUF browse. Failures are reported with the reason — a 401/403
points at the saved token, a 429 explains that a token raises the rate limit — instead of a
bare status code, and owner avatars, which noevia's Download tab never renders, can no
longer fail the search. Changing Sort by re-runs the search, and the empty state
distinguishes "nothing matched your search" from "the browse list came back empty".

New: a Layout control (Automatic / Phone / Desktop) backed by `public/layout-mode.js` and
user-agent detection. It sits in Settings → Appearance.

Verified locally: `npm run typecheck` and `npm run build` clean; web tests unchanged from
this checkout's baseline (274 pass, 45 pre-existing environment failures, identical before
and after); model-manager Python tests 19 passed, including 8 new ones covering the search
query, both fallbacks and the error messages. The hub itself was not reachable from the
development environment, so the search changes are verified against a mocked hub only.

## Merged main (PR #1) into the model-tuning branch — 2026-09-17

Four files conflicted, all of them touched by both PR #1 and Discover. Decisions:

- **`noevia.css`** — PR #1's surfaces win: `--bg-surface` on `--border-subtle`,
  `--radius-panel` for panels, 14px for rows, tiles, results and tables,
  `--radius-control` for fields, and the shared glass block with its reduced-transparency
  fallback. Its pixel sizes are re-expressed as this branch's type-scale roles, which is
  the same value in every rule the two sides both set, and the 550 weights it carried over
  are normalised to 600 — both are `lint:design` rules rather than a look. Each side's
  appended block is kept whole; PR #1's shared material goes last, as its comment assumes.
- **`api.py`** — Discover's endpoint wins, with one correction. It caught
  `httpx.HTTPStatusError`/`httpx.HTTPError`, which `search_models` no longer raises; taken
  verbatim, every rate-limited or unreachable hub would have become an unhandled 500
  instead of a readable error, and silently, because the types simply stop lining up. It
  now catches `hf.HfSearchError`, and the avatar lookup is guarded again. Both are pinned
  by new tests in `test_api.py`; the first fails against the unmerged endpoint.
- **`DownloadTab.tsx`** — Discover wins outright. Its header search box, sort control and
  filters supersede PR #1's local ones, and its `[sort]` effect already re-runs the search,
  so that fix is retired. Carried across: the query is trimmed, a new search collapses an
  expanded repository (the sort and filter paths did this, pressing Enter did not), a
  malformed body can no longer crash the list, the caption reads the term the results were
  actually fetched for rather than the 400ms-behind search box, and a hub error offers a
  retry.
- **`SettingsShell.tsx`** — this branch's settings restructure wins; the `general` section
  PR #1 mounted the layout control in no longer exists. `LayoutModeControl` is now
  `LayoutModeChoice`, a Layout row in `AppearanceSettings` next to chat font and density.

`hf.py` never conflicted — this branch does not touch it, so PR #1's search fix applies to
Discover unchanged. Dropping `full=true` costs Discover nothing either: it already fetches
repo trees itself, because the hub's search response carries no file sizes.

Verified: typecheck, build and `lint:design` clean; web tests 473 pass / 57 fail, identical
to this branch's head before the merge (the failures are this environment's missing native
dependencies); model-manager pytest 48 passed, up from 38 + PR #1's 8, plus the 2 new ones
above.
# 2026-09-22 (cloud material state correction; deployed as `72ae258`)

Corrected wrapped Material 3 segmented boundaries and role-paired hover/pressed
states for the mode switch, menus, outlined and destructive buttons. Liquid primary
actions retain legible primary colors during interaction, including in dialogs.
No geometry or application behavior changed. The cloud browser binary was unavailable;
rendered review remains pending. See [audit continuation](material-audit-2026-09-22.md).

The test runner now isolates state and restricts outbound sockets to disposable
fixture ports. The SSRF and egress disconnect tests no longer target arbitrary
host-local ports. All 1,247 guarded tests pass, along with typecheck, build and
design lint; the cloud browser blocks the local fixture, so visual QA is pending.

Local recovery: both cloud commits were recovered through their exact combined diff.
All 1,247 guarded tests and required static checks pass locally; the 468-state
synthetic view sweep, accessibility preferences, Code mode and mobile approvals pass.
Fixed two remaining nested/collapsed hover/press cascade conflicts and added a
rendered interaction regression. See the audit and deployment record for final status.
