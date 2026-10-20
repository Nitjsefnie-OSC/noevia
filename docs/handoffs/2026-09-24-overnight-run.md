# Historical software review findings — 2026-09-24

This document retains software findings and review batching from the historical run.
Installation inventories, operator instructions, deployment receipts, and recovery records
are preserved in the verified local archive excluded from Git. Findings below describe
the review at that date and do not assert current defects or authorize new work.

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
