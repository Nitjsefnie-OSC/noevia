# Session kickoff prompt

Paste the block below into a new agent session, working in the project folder
"AI frontend thing". It is deliberately short: `docs/master-prompt.md` is the real brief, and
this only points at it, fixes the starting state and sets the working rules for the session.

Keep it in sync when the live release or the current phase changes.

---

```text
You're continuing work on noevia, the self-hosted workspace in `noevia-application/` inside the
project folder "AI frontend thing" (GitHub `sbstndalton/noevia`). This kickoff is for the user's
intended Opus 5 successor; do not claim that model identity if it is not actually available. Read
`docs/master-prompt.md` fully and follow it: the read-first list, "Working with the user", the
non-negotiables, testing, deploying and decisions D1–D27. Also read `docs/roadmap.md`,
`docs/deployment.md`, `docs/changelog.md`, `docs/research/system-one/README.md`, and
`docs/research/system-one/18-decision-service-settings.md`.

Before starting, read the current contributor instructions, inspect repository state and open
work, and coordinate ownership. Treat historical release receipts as offline operator records;
verify fresh evidence before proposing any operational action. This document grants no
deployment, inference or model-loading authorization.

Validate telemetry changes with deterministic synthetic checks and inspect light/dark layouts
at representative viewport sizes. Distinguish checks actually run from unverified browser or
runtime claims. Keep deployment and rollback receipts in local notes excluded from Git.

After that, test → adjust → deploy → verify System-One routing and step supervision using a small,
bounded set of synthetic, non-personal Fast/Smart/Code cases and the existing local answering
model. Inspect actual Laya decisions and change only what evidence supports. Use the configured decision backend; do not install or download models without authorization. Preserve fallbacks, manual model choices, approval gates and execution budgets.
This is not authority for benchmarks, paid APIs/search, Diary or personal sources, training,
model downloads, rented compute, engine changes or heavy workloads.

Commit, push and deploy each finished change (verified backup first, `overlay-release.sh`),
with `npm test`, `npm run typecheck`, `npm run build`, `npm run lint:design` and the affected QA
suites; for UI changes, look at screenshots at 375/768/1440 in light and dark.

Never send prompts to the real Diary or modify its corpus; synthetic fixtures only; never point
QA at production. On the server: detach long jobs with `setsid`, never use unbracketed
`pkill -f` patterns over SSH, and leave no sessions attached.

Ask when an answer changes what you build; otherwise choose sensibly, say so, and keep going.
When you stop, update `docs/roadmap.md` (Where things stand, Done, Next, Needs the user) and
clean up every server, port and temp file you started.
```
