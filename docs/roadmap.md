# noevia roadmap

Status words: **Done** = deployed and verified · **Next** = to build, in the order listed ·
**Needs the user** = waiting on a decision, a device, or a maintenance window.

## Where things stand — 2026-10-06 (overnight: Rust start, repo split, bug rounds 3–7)

## Where things stand — 2026-10-05 (after the repo sweep, superseded)

### 2026-10-05: Full repo sweep

### 2026-10-02 … 10-05: Chat framing, provenance, routing modes

Built by agent pipelines. Every PR got a Fable review before merge, and every release was
web-only.

- **Chat framing, phases 1–6** (#737–#742; PRs #743–#748, #751):
  - Laya/decision-service frame suggestion (project, kind, tags, related chats) with a
    confirm-chip UI and a `/api/chats/:id/move` route.
  - A confirmed frame steers the prompt and biases the tool gate.
  - Gatherer → **task packet** → reasoner pipeline ([spec-task-packet.md](spec-task-packet.md)).
  - Tags, `[[chat]]` links, backlinks and a one-hop graph.
  - Opt-in one-way **vault mirror** into the Diary (it trashes only tombstoned chats, and an
    empty list brakes it).
  - Per-chat **brain notes** ([spec-chat-brain.md](spec-chat-brain.md)).
- **Review fixes:**
  - #755–#760: move dedupe, brain cleanup on delete, mirror foreign-note safety, mirror
    backoff, move frame validation, suggest rate limit and abort.
  - #764/#765 (mirror orphan, list `skipped`).
  - #768/#775 (archived chat counts).
- **Tool-layer provenance policy** (#769/#771): untrusted text in a write's
  recipient/URL/path/command forces a per-call approval card. It fails closed and only ever
  adds friction.
- **Storage login check** (#770/#772, #773, #776): the login is tested on save, and refresh
  failures now say whether the login was rejected, unchecked or redirected.
- **Routing modes** (#778/#779): local / cloud / hybrid. In hybrid, a sensitive turn gets an
  "ask before cloud" card. Per-chat Force local, a local/cloud badge, and tool results re-checked
  before every cloud round. The router asks Laya **one** ~1,000-char chunk per turn (Laya:
  `max_len` 512, single worker); `NOEVIA_ROUTER_CHUNKS` raises it after #780.
- **Eval harness** `experiments/framing-eval` (#750/#752, #753/#754): framed vs unframed,
  reasoner-slot scoring, kill criteria, local or remote OpenAI-compatible API. Every real run is
  approval-gated and none has run yet.
- **Separate project:** the reader→packet→reasoner model idea, with a feasibility draft in
  `../reader-reasoner-model/` (outside this repo). Its verdict: option A (two models plus LoRA)
  is plausible; B and C are low.

### Status snapshot — 2026-09-24 (superseded)

### 2026-09-24 — Overnight hardening (web releases `7b6942c` … `958022b`)

Merged fixes, release by release in [changelog.md](changelog.md): chat save/list races; server
error bodies, JSON validation, chat-id sanitising and approval scoping; system-model (Laya) guards
on delete, calibration, presets and sections, plus a research maintenance gate; MCP response cap
and abort; Diary edit conflicts, journal quarantine, tenant delete safety, `index_update`
validation and long names in trash; model-manager download path guard and code-sandbox process
cleanup; code-workspace/harness git-hook and symlink hardening, approvals by id, and the engine
key never committed; Drive mirror prune safety, storage read caps, SigV4 path, S3 region and
account-bound secrets; offsite S3 prefix; jobs journal resilience; chat replay role alternation;
DAV `Overwrite` default; deleting a user clears their MCP credentials. Diary and sidecar parts are
merged but not deployed (see above).

## Done

### 2026-09-22 — Cloud CSS state correction (release `72ae258`)
- Material 3 segmented, mode switch, menu and button state layers were corrected;
  Liquid primary actions keep their paired foreground/background on hover and press.
  Local Chromium validation now covers the complete 17-destination inventory and
  targeted interaction states. Native Apple/Safari parity remains open; see the audit.
- The unit suite now runs behind a test-only outbound guard and passes all 1,247
  cases with isolated state and disposable loopback fixtures. Guarded deployment is
  verified healthy; public assets match the validated build.

### 2026-09-22 — Three materials refined (release `827932b`)
- Removed Glassmorphism; older saved values fall back to Soft. Soft stays matte, Liquid
  controls use restrained highlights without label distortion, Material 3 uses tonal roles
  and correct state colors. Native-checkbox switches now meet 3:1 knob/track contrast.
- Keyboard focus, reduced preferences, approval decisions and account isolation verified.
  1,247 tests and all required checks pass. [Audit and iteration log](material-audit-2026-09-22.md).
- Deployed after verified backup; public assets match, services healthy, engine/embeddings/pi
  unchanged. Full evidence and rollback are in [deployment.md](deployment.md).

### 2026-09-22 — Outstanding branches integrated (release `04780e6`)
- Settings and project-library polish plus Claude/pi harness hardening merged into main.
  Existing model tuning retained without duplication; no outstanding branch excluded.
- 1,245 tests, typecheck/build/design lint, 15 synthetic browser/HTTP suites, real pi/Claude
  scripted-model checks, and 80 isolated Linux image tests pass. All three approval actions
  and tenant isolation preserved. No real Diary corpus used.
- Web deployed; pi sandbox rebuilt as `pi-0.87.0-99be0a2` and activated. Engine/embeddings
  unchanged; Laya remains pre-existing unhealthy. [Evidence](integration-2026-09-22.md).

### 2026-09-22 — Complete model auto-tuning (release `5a88558`)
- User-prioritized: **Tune untuned models**, beside Check for updates, detects missing/stale
  tunes and runs a sequential queue under one confirmed maintenance window. Context, KV cache,
  three MTP draft profiles, n-gram and batch settings are measured and quality-screened, then
  the fastest complete passing profile is applied. 60–70% acceptance is guidance, not a gate.
- Three deterministic probes plus long-context recall are smoke tests, not broad accuracy
  certification. Uses existing MTP heads only; no downloads. Rollback on cancellation/failure,
  restart recovery and external-edit protection tested. No production inference run started.
- App-only deployment; pi sandbox unchanged. Laya was already unhealthy at preflight and was
  left untouched (routing-health diagnosis is separate work).

### 2026-09-22 — Code mode runs pi (your go)
- The sandbox runs pi 0.87.0 through noevia's own ACP bridge; every non-read action reaches the
  approval card with its real command or path. Two live `scratch` tasks on the loaded model fixed
  `median()` (test `ok`, only `median.js` changed). OpenCode remains one `.env` change away.

### 2026-09-22 — Diary image overlay (your go)
- The Diary companion now runs the Trash-on-overwrite (`preserve`) and file-time (`modified`)
  fixes. Built `FROM` the running image with only `agent/` replaced (no dependency changes);
  backup, preflights, health and D1 isolation checked; rollback tag kept.

### 2026-09-22 — Diary local graph (release `080a91d`, deployed)
- Diary editor → Local graph: the open note, what it links to (Markdown and `[[wiki]]` links,
  including ones typed but not saved) and what links back (the existing bounded backlink scan),
  drawn as a small graph with clickable, keyboard-focusable nodes and a grouped list of names.
  Read-only; no index; says when the scan was partial. `qa/diary-local-graph.cjs`.

### 2026-09-22 — Pinned configs for Claude Code, Codex and pi (release `59249d9`, deployed)
- Claude Code and pi get noevia-written config (everything but reads asks, local engine only, no
  updates/telemetry; pi a fail-closed gate plus noevia's own ACP bridge). Both proven with the
  real CLIs against scripted fake models. Codex refused: measured, its commands ran unasked.
  Live remains OpenCode.

### 2026-09-22 — Routing labels and live footer (releases `e7b59d6`, `6c3cde0`, deployed)
- The footer follows the visible chat's own stream (generating, first output, exact usage and
  MTP across tool rounds), separate from engine polling. `qa/live-stats.cjs` passes; 375/768/1440
  light/dark inspected; stray wrapped-line separators fixed.
- System-One routing: Laya was sending most reasoning/code to Fast (23/40 held out). Concrete
  role labels: 36/40, verified through the deployed module with zero fallbacks at ~0.5 s.
  Second fresh set: 45/50.
- Step supervision (release `b055571`): the old wording paused a benign chat and added needless
  verify rounds; new wording 16/17 fresh, no needless pauses, every dangerous case stops.
  Laya chat smoke passes on the loaded model. [Evidence](research/system-one/19-routing-labels.md).

### 2026-09-22 — Context compaction inside tool continuations (release `3d2521d`, deployed)
- Every provider continuation after tool execution is re-budgeted. When tool results push the
  transient projection over its threshold, older context is summarized before the next request.
  The current user turn and complete assistant-call/result groups remain byte-identical; no
  transcript rewrite, fabricated result, blind truncation or tool replay. 1,196 tests pass.

### 2026-09-21 — Curated plugin starters (release `067ac1d`, deployed)
- Plugins → MCP servers and Skills open with "Recommended by noevia": Exa, Notion, Linear,
  Hugging Face and Cloudflare docs (first-party, hosted, all addable), and the pdf, docx, xlsx,
  doc-coauthoring, frontend-design and skill-creator skills, each with a line on why. Resolved
  against the live directories (5 and 6 found from the deployment host); a vanished pick drops out.

### 2026-09-21 — Ordinary WebDAV clients can write (release `42540fb`, web only)
- Your decision: relax If-Match, keeping a version. DELETE/MOVE use the current version; a PUT
  over a file first keeps its bytes in Trash (restores beside it). Protected files still need
  If-Match. `qa/dav-interop.cjs`: rclone 18/18 against the real companion on a throwaway tenant.
  DAV sharing stays off live; the Diary image is not rebuilt (`preserve` ships with it later).

### 2026-09-21 — Shared context across Chat and Code (release `dbfbd92`, deployed)
- Project settings → Shared context, shown when a project is in both Chat and Code; both off by
  default. "Code tasks see this project" starts a task with the goal, instructions, memories and
  recent chat titles (ahead of the task, never in its label). "Chats see recent Code tasks" tells
  a project chat what was asked and how it ended. Same user's workspace only; framed as data.

### 2026-09-21 — Code mode can reach the network (release `9611580`, deployed)
- The egress proxy runs inside web on port 8040; the sandbox reaches it as `egress` on the
  internal code network, and it is the sandbox's only way out. A task reaches only the
  domains its approved grant names, on 80/443, until the task ends. "Reach the network" and
  "Install dependencies" are offered again. Verified live: direct internet from the sandbox
  unreachable; no or forged token 407; a synthetic grant for `pypi.org` connects while
  `github.com`, a lookalike, `llama` and port 22 are 403, and revoking it gives 407. Fixed on
  the way: `NO_PROXY` was empty, so a granted task's own model calls would have been refused.

### 2026-09-21 — `index.cjs` is wiring (release `2ce73df`, deployed; QA sweep 77/77)
- **`index.cjs` is wiring.** The project, source and upload routes (`projects.cjs`,
  `routes/projects.cjs`), the provider registry (`providers.cjs`, `routes/providers.cjs`), the
  models routes (`models.cjs`, `routes/models.cjs`), the Diary routes with the connector
  endpoint (`diary.cjs`, `routes/diary.cjs`), sign-in/profile/admin (`routes/auth.cjs`), the
  storage connection (`routes/storage.cjs`), tool approvals, chat lists and history, reasoning
  settings, health and the HTTP helpers (`http.cjs`) each moved out with injected
  dependencies and a test with fakes; the member-origin policy is `createEndpointApproved` in
  `ssrf.cjs`. Every moved block is verbatim behind a sentinel, mounted in its original
  order; status codes, messages, the auth and CSRF gate and the approval actions are
  unchanged. 2,787 → 752 lines; `documents.test.cjs` no longer slices `index.cjs` as text.
  1,092 tests pass. The Claude Diary plugin README now points at Settings → Diary & storage →
  Connected apps for revocation.

### 2026-09-21
- **Code mode works and is on.** noevia pins the harness's own config (every action asks, one
  model endpoint, no self-update) and refuses a harness it cannot pin; registered repositories
  owned by the harness user are trusted instead of reported as "Not a git repository". The
  sandbox runs on an internal network whose only other member is the engine. A real task fixed
  the `scratch` fixture end to end twice. The Code tab gets the full height, and network and
  installs are shown unavailable (and never granted) because no egress proxy runs yet.
- **Docling is the extraction backend** — reading order, tables, Office/ODF/HTML/image formats.
  Fixed the same day: it was sent storage paths as names and refused every document in a folder;
  a 400 is now named for what it is and stays retryable, so affected documents heal on next sync.
- **Obsidian compatibility in the Diary:** `[[wiki links]]` render, open and count as backlinks;
  typing `[[` suggests files; frontmatter shows as properties; the tag filter reads `tags:`;
  unlinked mentions sit beside backlinks; new files can start from a `Templates` folder.
- **Diary connectors** are made and revoked in Settings (the server script is gone).
- **Auto-tune narrates itself** line by line, with heartbeats during engine loads.
- **Chat:** "Thought for 12s"; the context meter is one quiet line and no longer polls.
- **Usage** from real data: peak hour, favourite model, per-tool call counts.
- **Project screen:** header actions, context chips, an Outputs row, Context and Scheduled
  panel sections. **Nextcloud** is a connector of its own.
- **Repo:** usage accounting and the auto router moved out of `index.cjs`; dead components, the
  old Code sidebar CSS and the old Diary landing removed; design lint clean.
- **`index.cjs` taken apart** (release `a4e0178`, deployed): toolboxes and
  the built-in tools (`toolboxes.cjs`), the MCP wiring (`mcp-wiring.cjs`), the chat loop
  (`chat.cjs`) and the approvals gate each live in their own module with injected dependencies,
  a `routes/` file and tests that never boot the server; 4,241 → 2,787 lines. The tests that used
  to slice `index.cjs` as text now call the modules. Dead code removed end to end (the unused
  Hugging Face model search and variants routes, six uncalled helpers); the finished Docling
  handoff doc removed; every spec is now linked from `docs/README.md`.
- **Measured, not ported.** [research-language-consolidation.md](research-language-consolidation.md):
  Node costs ~10 µs of CPU per streamed token against the engine's 25–90 ms — 0.6 % of a
  paced reply — so nothing is worth porting to Rust, C++ or Python. The one slow Node path
  (`reduceToolResult`, quadratic on long listings, 53 ms) was fixed in place with parity
  tests: 0.5 ms. Rerun with `apps/web/scripts/profile-hot-paths.cjs`.

### Before 2026-09-21 (see the history file for detail)
Reliability fixes · PDF originals, OCR, images, DOCX · unified uploads · shared composers ·
onboarding and invites · the Diary (landing, days, Markdown editing, calendar, recovery, trash,
import/export, filters, sharing) · thinking modes · tool-call guard · app passwords and Markdown
DAV · instruction skills · backups with verified restore and Google Drive off-site copies ·
native llama.cpp with the Model Loader · MCP multi-server with OAuth, per-user keys and a
directory · skills auto-loading · tool routing · the Models page (tabs, routing, tuning,
benchmarks) · UI overhaul releases 1–4 (materials, primitives, Plugins page) · web address
rename with passkey continuity · Kiwix offline Wikipedia.

## Next — in order

Each builds on the one before or is ordered by value. Work top-down; record any reordering here.

**Repo split and Rust:** [ADR 0001](adr-0001-rust-and-repo-split.md). Done: prep (#897), macOS extracted (#900), Rust slices 1–2 (#896, #909; GGUF parser in the model-manager image, dark), egress proxy port (#926, dark), release assembly (#922), and the cutover (#952, 2026-10-07): noevia-web, noevia-core and noevia-services extracted at `f42f65f1` and pinned in `release/versions.lock`, `apps/web/` and `services/*` deleted here, releases assembled from the pins ([cutover runbook](repo-split-cutover.md)). Next: the web↔egress-proxy grant contract before the Rust proxy can replace code-egress.cjs; content-hash comparison in the assembly CI job (#938).

**Architecture under review:** the local-first System-One design ([research/system-one/](research/system-one/README.md)). Nothing below that touches routing, RAG, providers or model lifecycle starts before the review; its first prototype, RAG rerank, shipped in 67f336e (pool 12 → keep 6). Multi-hop rerun done (12→6 3/4). Next: watch fallback rates in the web log (`[rag] rerank`).

Pruned 2026-10-05 (repo sweep): items whose issues are closed were removed (they remain in git
history and the closed issues) — System-One next steps (#261, closed 09-30 "keep current
routing", follow-ups in #682), the Docling tax-folder re-read (#262, done 10-01), Deep research
measurement (#264, closed; only the owner's flag flip remains, see Needs the user), Skills
portability (#265/#19 closed; PR #20 merged 09-23), and the modular-platform workstreams (#266–#272
closed; contracts in [spec-service-boundaries.md](spec-service-boundaries.md)).

### GitHub milestone map

The [milestones](https://github.com/sbstndalton/noevia/milestones) group open enhancement issues
and future architecture work. They have no due dates; the numbered **Next** list above remains the
execution priority. Triaged bugs retain their separate priority. A milestone means planned work,
not a shipped release.

## Needs the user — in order

1. Confirm outstanding user-workflow checks on the intended device and approved synthetic data.
2. Select which repositories and execution nodes Code may access; keep grants scoped.
3. Approve any model download, benchmark, residency change, or inference-host migration separately.
4. Resolve storage-account configuration through the owner; do not record real account identifiers
   or document/source names in public issues. Validate rejected-login behavior with synthetic data.
5. Select a maintenance window and recovery plan before deployment or data migration.
6. Decide whether to enable optional DAV sharing, browser execution, or research features after
   their permission, privacy, and resource contracts qualify.

## Lessons worth keeping
