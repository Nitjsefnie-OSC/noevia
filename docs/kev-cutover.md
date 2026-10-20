# Qualifying a decision-backend transition (#1639)

This public guide retains the compatibility and evaluation requirements from the historical
Kev-0.8B trial. Host paths, installed artifacts, network inventories, container receipts,
credentials, schedules, and the exact cutover/rollback commands remain in the local operator
archive. This is neither proof of current deployment state nor authorization to start a model.

## Preconditions and compatibility

Confirm the current core contract and candidate image before changing any endpoint. The
historical integration needed noevia-core#108; an older image understood only the predecessor
contract. A reachable backend is not sufficient if the caller and response contracts differ.
Check the actual current implementation and any retired selectors rather than replaying old
environment settings against a newer native release.

Verify the exact model artifacts, runtime build, and checksums locally. Do not download or
pull missing artifacts under the authority of this guide. Record resource limits, required
startup headroom, network isolation, health behavior, and a compatible predecessor before an
approved transition. Retain the configured model store; never prune it as cleanup.

## Role-specific qualification

The historical trial considered Kev for routing, tool gating, step supervision, chat framing,
and load advice. Sensitivity classification remained on a separately qualified backend because
Kev was not qualified for that role (#1647). Backend selection must preserve this distinction;
a shared endpoint must not silently change privacy routing or fall back to a weaker policy.

Core's historical `kev-0.8b` profile applied calibration T=0.45 to the served probabilities.
That does not replace the runtime's own calibration or qualify a different artifact/build.
Record both layers and use the current source contract for supported model identifiers.

Relevant configuration keys include `COWORK_DECISION_URL`, `COWORK_DECISION_MODEL`,
`COWORK_DECISION_API_KEY`, `COWORK_SENSITIVITY_DECISION_URL`, and
`COWORK_SENSITIVITY_DECISION_MODEL`. Check effective saved administrator settings as well as
environment configuration: a saved override can take precedence. Inspect privately, never
print credentials, and do not modify account settings merely to make a test pass.

## Candidate and resource checks

Use an isolated candidate and synthetic data first. Qualify request/response behavior for each
intended purpose, deadline/failure handling, health checks under the selected hardening,
graceful shutdown, and sensitivity isolation. Run through the same settings resolution and
decision modules the application uses; a stub that ignores saved settings proves less.

Account for total resident memory and page cache. In the historical limited trial, measured
VmHWM was 4.58 GiB under a 5 GiB cgroup cap; a 4.6 GiB hard limit would have left almost no
headroom. These are evidence for that configuration, not universal sizing defaults. Measure
the candidate alongside the installation's other authorized workloads before selecting limits.

Before a separately authorized cutover, satisfy the current idle/tune/backup-window gates and
record only the scoped services and configuration that may change. Keep the predecessor
available for rollback. Do not broaden access, change unrelated services, or invoke real Diary
data as part of verification.

## Baseline and bounded soak

Capture a baseline before activating the candidate. Keep text-free operational records local;
publish aggregate metrics and validation limits rather than log rows or real conversations.
Deduplicate overlapping rotated-log copies and retain exact UTC windows and sample counts.
Thin baselines must be reported as uncertain rather than treated as reliable comparisons.

The historical seven-day limited trial used these acceptance criteria:

- No restarts/OOM kills and health maintained; candidate memory stayed below its qualified cap.
- Per-purpose daily failures below 2% and deadlines below 5%; days with fewer than 20 requests
  were combined before computing rates.
- Tool-gate implementation faults remained zero. Do not count a retired mismatch event that
  the current implementation can no longer emit.
- Sensitivity stayed exclusively on its qualified backend and failed closed when unavailable.
- Supervision escalation rate stayed between 0.5 and 2 times the baseline; where the baseline
  contained escalations, at least one per 100 supervision events was required.
- Weak-escalate fallback increased by no more than five percentage points, and owner-marked
  benign pauses increased by no more than one per 100 supervision events.
- New routing/tool/supervision complaints became tracked findings. Resource headroom stayed
  within the locally qualified bound throughout the run.

Select a soak period and thresholds for the actual configuration before starting; these old
criteria do not automatically authorize another trial. A breach triggers the agreed rollback,
not an unbounded tuning session. Remove only temporary monitoring installed for that trial.

## Rollback

Recheck idle gates, restore the recorded predecessor endpoint and only the configuration keys
changed by this transition, then verify settings resolution and every affected decision role.
Do not copy an old environment file over unrelated changes made during the soak. Preserve
candidate files and evidence for diagnosis. An image/backend rollback does not overwrite live
application databases, private corpora, or model stores.

Use [the generic release guide](deployment.md) with the operator's local recovery procedure.
No cutover, inference, deployment, or settings change is authorized by this document alone.
