Mirror of the local ledger `Claude handoff 2026-09-24/OVERNIGHT-RUN.md`; updated at the end of chat 3 (2026-09-24 20:25 EDT). Live: web+diary 11617a3.

> Historical software/planning record. Installation-specific access, accounts, paths,
> inventories, and recovery receipts are retained in a verified local archive excluded from
> Git. This record is not current authorization or proof of any live deployment.

# Noevia overnight review-and-fix run — handoff (2026-09-24 ~02:35 EDT)

## Paste this into a new chat (pick Fable, latest, effort medium, first)


```text
Continue the Noevia overnight review-and-fix run from "Claude handoff 2026-09-24/OVERNIGHT-RUN.md" in this project folder. Read it and the bug-fixing skill (/bug-fixing), verify fresh state (origin/main, open PRs, live web image), then keep going.
Roles: you (Fable, medium) only orchestrate and do final code reviews; send agents for all work. Opus 5.5 (model "opus", low) for code jobs and all merges into branches/main; Sonnet (high) for minor bug/code fixes; Haiku for clerical work and writing PR text.
Loop: review → fix → test → final review → merge → web-only deploy → verify → review again. When everything looks done, think again and keep going. Stop at 07:30 EDT or when weekly usage reaches 50% (check get_usage).
Never let the session compact: if context passes ~80%, stop, save state + in-progress work into a PR and this ledger, and tell me to start a fresh chat.
Standing rules: always deploy (web-only via guarded up.sh), deploy from main, delete merged branches, no model/tuning runs, synthetic fixtures only (never real Diary data), preserve tenant isolation and write approvals, never modify the dirty noevia-application working tree.
Update this ledger after every merge/deploy.
```


## State

## In flight

- **PR #75** https://github.com/sbstndalton/noevia/pull/75 — branch `fix/chat-save-races`, head `ae1e2ff`, worktree `/tmp/noevia-fix-chatsave`. Fixes F1, F2, F-P1 (new `apps/web/src/chat-save.ts` + `tests/chat-save.test.cjs`; 1379/1379 tests, typecheck/build/lint clean). Engineer reported 5/5 CI green; confirm the 6th (offline-contract) ran. Gap: App.tsx wiring that defers the merge during streaming is only typechecked, not render-tested — consider a synthetic QA script. NEXT: final review (Fable) → Opus squash-merge → web-only deploy → verify.

## Round 1 findings not yet assigned

Web frontend (App.tsx) — assigned above:
- F1 Med: chat-list upsert uses stale closure + whole-list PUT; overlapping sends drop a chat (App.tsx ~454-472).
- F2 Med: save-conflict merge remints ids / replaces transcript during a streaming reply; reply text lost (~421, ~693).
- F-P1: persist() inside setState updater (StrictMode double save). F-P3 Low: stats fetch per usage event out of order.
- Not covered: ChatView markdown link handling, models UI accessibility → second pass.

Web server core:
- S1 Low: index.cjs:642 returns raw err.message on 500s → only expose when err.status set.
- S2 Low: JSON `null` body → TypeError 500 (routes/approvals.cjs:34, routes/chat.cjs:27) → 400 on non-object body.
- S3 Low: tombstone check uses raw id, storage uses sanitized id (chat-lists.cjs:98 vs projects.cjs:175-177; also chat.cjs:39-40) → deleted chat resurrectable.
- S4 Low: id sanitizing to '' collides into one history file (projects.cjs:176) → 400.
- S-P1 Med (verify!): approve_all with null chatId → '-' shared key across id-less free chats (approvals.cjs:22, chat.cjs:93).
- S-P2 Low: approval wait doesn't check abortSignal.aborted first (approvals.cjs:50).
- S-P3 Low: tombstone checked before body read (chat-lists.cjs:98).
- Not reviewed: auth.cjs, import/export, uploads/files, Diary stream proxy, rest of chat.cjs, toolPolicy.

Diary service (services/diary/agent):
- D1 Med: evicted tenant states never closed (app.py:309-315) → close after releasing lock.
- D2 Med: concurrent edits from two tabs silently overwrite (app.py:432, corpus_store.py:373) → base-text hash + 409.
- D3 Low: unvalidated month → 502 with exception text (corpus_store.py:410) → validate ^\d{4}-\d{2}$.
- D-P1..P5: delete_tenant vs in-flight writes; WebDAV servers without ETag; storage-backup user id case; chat session keyed by raw header; directory listing reads whole files.

Not yet reviewed (reviewers stopped for the handoff — re-run):
- apps/web/server model code: llamacpp-*.cjs, model-manager.cjs, model-system.cjs, routes/models.cjs, system-one-router.cjs, decision-endpoint.cjs, maintenance gate, admin enforcement.
- services laya, model-manager, code-sandbox, ocr, docling (+ Dockerfiles/compose).

## Suggested batching
1. Server hardening PR (Sonnet high): S1–S4, S-P2, S-P3; verify S-P1 and fix if real (Opus).
2. Diary PR (Opus): D1, D2, D3; D-P3/D-P4 if confirmed.
3. Re-run the two stopped reviews + second-pass frontend review.

## Handoff state (written 04:25 EDT, chat 2)

- Live web: cowork-web:c3a03c7 (deploy 9). Pending: #102 merge (merger 10) → deploy 10 if the 5-hour usage window allows; otherwise deploy the final main in the next chat.
- Merged tonight (28 PRs): #75 #76 #77 #79 #80 #81 #82 #83 #84 #85 #86 #87 #88 #90 #91 #92 #93 #94 #95 #96 #97 #98 #99 #100 #101 (+ #102 pending). Web-only deploys: 7b6942c, 7ce2213, 7e8ce3a, 0c2be32, 852ef76, c3a03c7.
- NOT deployed (need image rebuilds, not web-only): Diary #77 #84 #87 #93 #94 #99(diary part); model-manager + code-sandbox #79. Diary ships via the running-image agent/ overlay flow (see memory); sidecar images need a tag bump.
- Open PRs left for the user: #89 (chat-row marquee → static ellipsis: design decision), #78 (pre-existing docs PR, untouched).
- User TODOs: delete synthetic chats "QA test message 1/2"; load a model then re-run the live streaming race tests (offline Playwright versions all PASS on 7ce2213: /tmp/noevia-qa-races/apps/web/qa/races-offline.cjs); investigate the unexplained graceful Diary restart at 04:10 EDT; decide #89.
- Unassigned plausible findings (all low unless noted): OCR/docling slow-upload holds only slot; model-manager URL download SSRF (check exposure); laya /health 503 during restart vs healthcheck start_period; code-sandbox write backpressure; decision-endpoint 204 body; S3 query "+" vs "%20"; s3_storage.py caches sha256 as ETag when server returns none (412 spin); X-Cowork-Storage unbounded length; tenant cache keyed by full storage header; offsite-backup reads whole files; webdav.py get/list_dir no size cap; connector rate limit keyed by socket IP behind proxy; mcp-oauth pending map uncapped/state burnable; invitations outlive a disabled admin; project delete vs upload race; unbounded project creation via /api/chats/:id/context; research double "save partial"; front-matter notes treated as skill candidates; session/prompt no overall timeout; sync .slice(0,60) drops sources silently and deletes RAG chunks; shared-project sync uses caller's storage; synced text unmarked as untrusted in prompts (MED, design); Diary edit UI does not exist (editDiaryEntry removed) so base_hash/409 has no client; DiaryView storage identity key ignores region; v1 secrets still written by workspace.cjs/mcp-oauth.cjs/directory-mcp.cjs; transcript-merge [u,u] now handled server-side (#97).
- Never reviewed: services/code-sandbox supervisor start-message cwd/env limits, pi/DSH gate scripts, uploads.ingest/documentSources internals, hash-bound skill review path, chat prompt assembly, dav-ops companion rules, s3_storage.py signer parity beyond "( )" case, secrets at rest rotation.
- Worktrees to clean if left: /tmp/noevia-review-fe (read-only, safe to remove), /tmp/noevia-qa-races (throwaway), /tmp/noevia-fix-rowclip (#89), plus older pre-run worktrees under /tmp and ~/.codex (not this run's).
- Lessons (also in memory): put every PR/SHA in an agent's FIRST prompt (merges/deploys added by SendMessage get classifier-blocked); deploy agents are blocked nondeterministically at archive/scp — relaunch a fresh one following docs/deployment.md verbatim; run up.sh from the Compose project folder; reviewer agents have no shell (create worktrees for them).

## Paste this into a new chat (Fable, latest, effort medium)


```text
Continue the Noevia overnight review-and-fix run from "Claude handoff 2026-09-24/OVERNIGHT-RUN.md" in this project folder. Read the "Handoff state" section and the bug-fixing skill (/bug-fixing), verify fresh state (origin/main, open PRs, live web image), then keep going.
Roles: you (Fable, medium) only orchestrate and do final code reviews; send agents for all work. Opus 5.5 (model "opus", low) for code jobs and all merges into branches/main; Sonnet (high) for minor bug/code fixes; Haiku for clerical work and writing PR text. Browser click-tests: Opus low agent of type `claude` using Claude in Chrome (Brave is connected as Browser 1).
Loop: review → fix → test → final review → merge → web-only deploy → verify → review again. Stop at the user's stated time or when weekly usage reaches 50% (check get_usage; also watch the 5-hour window).
Never let the session compact: if context passes ~80%, stop, save state + in-progress work into a PR and this ledger, and tell me to start a fresh chat.
Standing rules: always deploy (web-only via guarded up.sh from the Compose project folder), deploy from main, delete merged branches, no model/tuning runs, synthetic fixtures only (never real Diary data), preserve tenant isolation and write approvals, never modify the dirty noevia-application working tree. Put every PR/SHA an agent must merge or deploy in its FIRST prompt.
Update this ledger after every merge/deploy.
```


- 04:30 (real) Merger 10 done: #102 → 958022b. Release agent 10 launched: web-only deploy of 958022b. This is the last action of chat 2; final report follows.
- DEPLOYED cowork-web:958022b (#102 live). Verified 200/401, assets match, 42 sidecars unchanged, logs clean, changelog a21b449. Rollback: previous c3a03c7, backups *.bak.before-958022b. Live web = origin/main 958022b (+ changelog a21b449). CHAT 2 STOPPED HERE (5-hour usage window ~80%); resume with the "Paste this" prompt above.
- 04:45 (real) User asked to update the README (PR #78, docs/readme-current-version, 56bf498; README.md, docs/README.md, docs/agent-brief.md, docs/roadmap.md). Opus agent launched to refresh it to 958022b state (live release, deploy notes, tonight's hardening summary, test evidence) and squash-merge it. Docs only, no deploy.
- 04:55 (real) PR #78 refreshed (243178b) and squash-merged → main bd27f22: roadmap now states source/live 958022b, tonight's 7 web releases, not-yet-deployed Diary/sidecar list, deploy + rollback flow, hardening summary, test counts. README/docs README/agent-brief keep the PR's original edits. Fable review: one wording fix (CI check count) being committed to main by Opus. Local branch docs/readme-current-version is checked out in the Nextcloud noevia-application tree — left alone (remote deleted). Live web is 958022b; docs-only commits since need no deploy. Open PRs: #89 only.
- 05:00 (real) Roadmap CI wording fixed on main → 9de5b66. origin/main 9de5b66 (docs-only ahead of live 958022b). CHAT 2 DONE.
- 05:05 (real) User delegated the open decisions. Decided: PR #89 CLOSED (marquee intentional; branch kept). Next chat, in order: (1) per-service image tag variables in compose (DIARY_VERSION, OCR_VERSION, MODEL_MANAGER_VERSION, CODE_SANDBOX_VERSION) so releases are one image at a time and COWORK_VERSION no longer implies phantom sidecar tags; (2) deploy #79 (model-manager + code-sandbox tag bump) — High fix; (3) Diary overlay deploy (#77 #84 #87 #93 #94 #99); (4) alert on unexpected sidecar restarts (Diary restart 04:10 EDT unexplained, benign); (5) path-filtered CI + per-service changelog sections. Live streaming tests skipped (offline suite covers them). QA chats "QA test message 1/2" left for the user to delete. Multi-repo split deferred until per-service versioning is in place.
- 05:10 (real) State saved to PR #103 (handoff/2026-09-24-overnight-run, 6ba7f39, docs/handoffs/2026-09-24-overnight-run.md) — open, not merged; the next chat updates it (copy this ledger over it) and merges it at the end of its run.

## Handoff state (chat 3, written 20:05 EDT 2026-09-24 — final deploy of 11617a3 in progress; see the last ledger line for its result)

- origin/main 11617a3 (+ changelog commits). Live before the final deploy: web dda50c2, diary 5b6d9b6, model-loader 5b6d9b6, code-sandbox pi-0.87.0-dda50c2, ocr 5004b50, docling 2026-09-21, laya 0.3.5-recovery-2ffd153. Per-service tags live in .env (DIARY_VERSION, OCR_VERSION, MODEL_MANAGER_VERSION, CODE_SANDBOX_VERSION, DOCLING_VERSION); COWORK_VERSION = web only.
- Done today: the 5 ordered tasks (#106 tags, #79 sidecar deploy, Diary overlay, #105 alert installed + cron, #104 path-filtered CI + changelog sections); merged 20 PRs (#104 #105 #106 #132–#135 #166–#169 #171 #172 #187 #188 #189 + changelog commits); web deploys dda50c2 and 11617a3; sidecar deploys model-loader 5b6d9b6, code-sandbox pi-0.87.0-5b6d9b6 → pi-0.87.0-dda50c2, diary 5b6d9b6 → 11617a3.
- Issues: 80 filed (#107–#186 minus user-filed #174 #175); all confirmed findings fixed and closed except the OPEN list: #111 #113 #115 #116 #120 #121 #122 #127 #128 #129 #130 #139 #140 #146 #147 #148 #149 #157 #160 #161 #173 #182 #185 (all low/plausible/design) + user's #174 #175. Label "triaged" on all.
- Not covered / next review targets: member (non-admin) view of Models tabs + server-side mm route roles; Sidebar "more" menu a11y; mcp.cjs session handling; code-workspace recover(); journal ordering across dependent ops after a quarantine; managed_storage restore endpoints; frontend DiaryView/Chat after #171/#172; live authenticated QA of code tasks (pi) and approvals (needs a loaded model — user approval).
- Worktrees: /tmp/noevia-review-base (detached, safe), /tmp/noevia-fix-rowclip (#89 closed — remove), /tmp/noevia-diary-venv (Diary venv, keep), older pre-run worktrees under /tmp/noevia-audit-*, ~/.codex (not this run's).
- Rules learned today: Sonnet agents may treat mid-task SendMessage addenda as injection — put everything in the first prompt; `--profile code` goes BEFORE `--` in up.sh; PR check runs sometimes do not attach to a pushed head — merging main + push re-triggers.
- 20:20 DEPLOYED cowork-web:11617a3 (full build on the deployment host; #166 #167 #168 #169 #171 #172 #187 #188 #189 live) + cowork-diary:11617a3 (overlay; Diary parts of #134 #168 #169 #189; backup ab_20260924_140932). Verified 200/401 ×3, assets match, in-container greps, logs clean, Diary import ok, --ack done; 8 other containers unchanged. Changelog 99964bc. Rollback: web dda50c2 via .env.bak.before-11617a3 + symlink; diary DIARY_VERSION=5b6d9b6 + up.sh diary. Live now = origin/main 11617a3 for web AND Diary; code-sandbox pi-0.87.0-dda50c2 (current), model-loader 5b6d9b6 (current), ocr 5004b50 (unchanged code). Issue #131 closed (fixed by #135). CHAT 3 ENDING: updating docs/handoffs/2026-09-24-overnight-run.md from this ledger and merging PR #103.
