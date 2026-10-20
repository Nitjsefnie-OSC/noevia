---
name: deploy-noevia
description: Prepare, verify, release, or roll back a Noevia installation using its operator-owned configuration and runbook. Distinguish source changes, candidate qualification, and live verification.
---

# Deploying and verifying Noevia

Read `AGENTS.md`, `docs/agent-brief.md`, and `docs/deployment.md`. Use `DEPLOY.md` for generic
fresh-install guidance. An existing installation may use a saved Compose Manager project and
preflight wrapper with different paths. Never infer the target, credentials, or live versions
from a public document.

## Establish scope and reachability

Confirm the user's authorized operation and current coordination ownership. Read the operator's
local, untracked runbook for the intended SSH target, application origin, saved configuration,
release root, and recovery procedure. Verify tools and network reachability without printing
credentials. A blocked route is not proof that the host is down; do not change access or
network settings to work around it.

If this environment cannot reach the target, report the exact blocker. A handoff must preserve
the verified branch/head, work completed, checks run, remaining acceptance criteria, ownership,
and rollback requirements. Keep private target details in the local coordination record, not
in a public repository handoff or comment.

## Prepare and qualify

Use the repositories pinned in `release/versions.lock` and the supported assembly helper.
Inspect the installation's effective configuration and confirm its saved Compose copies before
proposing changes. Back up configuration and state with verified recovery inputs. Build and
qualify the candidate before activating it. See `references/runbook-traps.md`.

Preserve compatibility identifiers, tenant isolation, authentication, and all three write
approval actions. Preserve configured remote inference services and intentionally stopped
model containers. Run candidate checks with disposable synthetic state. Do not invoke a real
Diary corpus or start inference, benchmarks, downloads, or deployment outside the current scope.

## Verify and record

Read actual image/release identities when live inspection is authorized. Separate code on a
branch, merged code, candidate tests, deployed readiness, and verified user behavior. Browser
regression suites using disposable local servers do not establish production verification.
Report skipped checks and failures plainly.

Record deployment receipts, service inventories, backups, and recovery paths only in the
operator's local runbook. Publish generic software behavior, compatible release requirements,
and validation limits. Recheck that private records are ignored and untracked before committing.
