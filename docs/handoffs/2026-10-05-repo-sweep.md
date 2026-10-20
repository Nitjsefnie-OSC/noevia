# Handoff — 2026-10-05: full repo sweep (bugs + old/deprecated/broken code)

> Historical software/planning record. Installation-specific access, accounts, paths,
> inventories, and recovery receipts are retained in a verified local archive excluded from
> Git. This record is not current authorization or proof of any live deployment.

Paste this as the first message of the next session. It is complete on purpose: running agents
ignore steering added later, so everything the sweep needs is in this brief.

---

You are taking over noevia (`sbstndalton/noevia`; local checkout `noevia-application/` inside a
Nextcloud-synced folder). Your task: **a full repository sweep**. Find and fix real bugs, and remove
old, deprecated, dead or broken code. Ship each fix through review → merge → deploy.

## Read first
1. `CLAUDE.md` → `AGENTS.md` → `docs/agent-brief.md`.
2. `docs/roadmap.md`, especially "Where things stand — 2026-10-05".
3. `docs/changelog.md` (latest releases and their rollback recipes) and `docs/deployment.md`.
4. Open issues: `gh issue list -R sbstndalton/noevia --state open`.

  These have specs (`docs/spec-task-packet.md`, `docs/spec-chat-brain.md`) and byte-identity
  tests for flag-off. Keep them passing.
- **Untouchable without the owner:** ChatGPT's branches (`codex/*`) and the issues it files. It is a
  co-worker that may push to main, so re-fetch main before every merge.

## Sweep scope
Work area by area; one PR per coherent area.

**Code areas:**
- **web server:** `apps/web/server`
- **web client:** `apps/web/src`
- **Diary:** `services/diary`
- **model-manager:** `services/model-manager`
- **deploy tooling:** `deploy/`, `tools/`
- **experiments:** `experiments/`

**What to look for:**
- **Bugs:** correctness, races, tenant isolation (every read and write must be scoped to the
  caller's workspace), injection boundaries, destructive paths, unbounded growth, errors thrown
  into request paths, and regex backtracking.
- **Dead or deprecated code:** unused exports and modules, superseded paths whose replacement
  has shipped, stale feature flags that are permanently on or off, obsolete experiments, and docs
  describing removed behaviour.
  - **Prove** a thing is dead before you delete it: grep every caller, check the tests, check
    `index.cjs` wiring, check the client `src`, check deploy scripts.
  - When unsure, file an issue instead of deleting.
- **Broken code:** tests skipped for no current reason, scripts that no longer run, and dangling
  references.
- **Do NOT rename `cowork*` identifiers.** That is intentional.

## Known loose ends worth checking in the sweep
- `docs/project-ideas.md` is untracked in the local checkout. It is the owner's file; leave it.
- The sensitivity option label in `routing-modes.cjs` is 137 chars, over the 120-char label
  limit, so it gets slightly truncated. This is a low-priority nit.
- The keyword pre-rule in `routing-modes.cjs` will false-positive on code like `token = …`.
  That fails toward "ask", but it is worth tuning.
- In hybrid routing, tool results are checked only by pre-rules, not by Laya. This is
  documented and deliberate until #780 lands.
- `checkLogin` 403 → unverified. A refresh 401/403 → "login rejected". This is consistent but
  worth one live check once the owner fixes #767.
- Old experiments in `experiments/` (acp-spike, persona-kv, …): check whether each is still
  referenced, and propose deleting the dead ones through issues.
- Stale docs: `docs/roadmap.md` "Next — in order" still lists items from 2026-09. Verify each
  against `main` and prune what is done.

## Finish
At the end, give a summary covering:
- the issues filed and closed
- the PRs merged and the releases deployed
- the code removed (files and lines)
- anything left for the owner

Update `docs/roadmap.md` "Where things stand", and save the memory ledger.
