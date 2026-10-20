# Deployment and release operations

This public guide describes the release process. It is not an inventory of any running
installation. Keep host addresses, accounts, filesystem layouts, Compose Manager copies,
backup locations, credentials, and deployment receipts in an operator-owned local runbook.
`deploy/private/` is ignored by this repository; verify that local records remain untracked
before committing. Do not place them in a cloud-synced folder or attach them to an issue.

## Releasing after the repo split (#952)

The integration repository contains Compose definitions, deployment helpers, documentation,
and `release/versions.lock`. The client, core, services, and Rust workspace live in separate
repositories. An archive of this repository alone is not a complete application release.

1. Select reviewed commits with green CI. Record the exact integration commit and component
   refs. Preserve the current release and rollback configuration locally.
2. Assemble the pinned source with `deploy/tools/assemble-release.sh <commit> <output-dir>`.
   Verify the archive and recorded checksums. Use the supported build flow described by
   [DEPLOY.md](../DEPLOY.md), the helper usage, and the selected release's contracts.
3. Build and qualify the candidate before changing the active release. Keep disposable test
   state separate from production mounts. No test may read or modify a real Diary corpus.
4. Validate the installation's effective Compose configuration and writable mounts. Generic
   repository Compose files do not automatically synchronize with an operator's saved copies.
5. Back up configuration and application state with the installation's approved procedure;
   verify the backup and recovery inputs before cutover.
6. Check idle jobs, model activity, and the installation's backup/maintenance windows. Recreate
   only the services covered by the approved release, through the required preflight wrapper.
7. Verify readiness, selected image identities, native capabilities, scoped state integrity,
   and logs. Record what passed, what was skipped, and the rollback decision locally.

Keep `cowork`-prefixed environment variables, image names, container identities, cookies,
state paths, and storage keys compatible. Documentation cleanup does not migrate them.
Preserve configured remote inference endpoints and intentionally stopped model containers.
Do not start a model, benchmark, or deployment simply to check this guide.

## Settings and native-service compatibility

Model execution may use a self-hosted inference service, external providers, or an optional
local runtime. Retain the service-role boundaries, authentication, tenant isolation, write
approvals, and endpoint validation whichever execution path is configured.

At a native-image boundary, review the exact release contract before removing retired selector
keys. Keep the old image, its configuration, and its selector values together for rollback.
Do not copy historical selector lists into a newer release without checking current support.
`NOEVIA_RUST_PROJECT_WRITES` is retired: chat-context routes are always native, so do not set it for
a current image; the supervisor warns and ignores it. Set it only to roll back to an older image that
still reads it.

Native model-manager startup requires its configured roots and publisher lists to validate.
For an image transition requiring a publisher-data seed, use
`deploy/tools/seed-search-trusted.sh` against a verified compatible predecessor image. Preserve
an existing administrator-owned file and validate it; a missing or malformed publisher set
must refuse startup. The source image, output path, and release boundary are local runbook
inputs. The production image is not a source for data it no longer ships.

Filesystem ownership guards remain enforced. Inspect the actual candidate mounts rather
than recursively changing permissions or weakening validation. Retain the exact timezone,
trusted-set, startup, writer-lease, shutdown, and process-ownership requirements of the release.

## Release idle gate: Coding jobs (#1391)

Use `deploy/tools/release-idle-jobs.sh` and its companion against the selected application
image. A malformed, unreadable, or symlinked job store, a missing strict-mode implementation,
a timeout, or a failed container command refuses cutover. An absent job directory alone may
count as no jobs. The gate must not mutate job state or print account identifiers.

## Overlay releases

An overlay is appropriate only when the existing image and the candidate's dependency and
runtime contracts permit it. Read `deploy/examples/overlay-release.sh` and
`deploy/examples/diary-overlay.sh` before selecting this flow; inspect their actual service
scope. An overlay is not automatically web-only. Qualify the resulting image before activating
it, and do not use an overlay to bypass required native binaries or changed dependencies.

### Docling app-only overlay

Use this flow only when the docling service's Python app files changed and its native binary, dependency locks and downloaded models did not. The overlay starts from the docling image that is currently running and replaces exactly the app files that the production image copies into `/app/`. The whole overlay is these two lines:

```Dockerfile
FROM <running-docling-image>
COPY server.py extract.py isolation.py isolated_worker.py selftest.py synthetic_pdfs.py /app/
```

The file list must match the final `COPY <files> ./` in the production stage of the docling `Dockerfile` in the noevia-services repository. A services test, `test_overlay_docs_list_exactly_the_files_the_dockerfile_copies_to_app` in `docling/test_requirements_pinned.py`, enforces that this line lists the same files, so a change to that Dockerfile line must update this one in the same change. Qualify the resulting image before activating it, as for any overlay.

## The deploy

The operator's local runbook supplies the SSH target, application origin, release root,
environment file, saved Compose project, preflight installation path, and previous release.
Use explicitly configured values, not addresses copied from historical public notes. Keep
secrets out of URLs, command output, issue bodies, commit messages, and screenshots.

When Compose Manager is used, confirm the files the manager actually reads. Back up each
operator-owned copy before a scoped change. Always use the installed preflight entry point;
launching directly from a GUI may bypass mount and idle checks.

## Verification and rollback

Passing unit tests is not proof of a live user workflow. Distinguish local tests, CI, packaged
candidate checks, deployment readiness, authenticated UI verification, and model inference.
Use synthetic accounts and data for functional checks. Live tests need their own authorization.

Retain the previous assembled release, image identities, environment, and Compose files.
Rollback must restore the matching configuration and scoped services. Do not overwrite live
SQLite files or restore application data merely to revert an image. Recovery involving data
requires its own verified backup and migration plan. Preserve old releases until the operator's
retention policy permits removal.

Keep exact backup paths, host/service inventories, recovery manifests, and deployment evidence
outside version control. Public release notes should describe software behavior and validation
limits rather than the private state of an installation.

## Services on other Inference machines (#1843)

Services assigned to another inference machine are not counted against this host's budget.
The remote inference model is outside this budget too. Account for each role's residency on
its own machine; do not restart retained local sidecars merely because the selected role runs
elsewhere. This describes resource accounting, not any installation's current assignments.

Host preflight and restart-notification tooling reads an explicit `NOEVIA_REMOTE_SERVICES`
list because it cannot depend on web administrator credentials or settings while web is stopped.
The accepted role names and compatibility aliases are:

| Role | Earlier service name |
| --- | --- |
| `decision` | `kev` |
| `sensitivity` | `laya` |
| `embedding` | `embed` |
| `reranker` | `rerank` |

For each selected role, configure `NOEVIA_REMOTE_<ROLE>_HEALTH_URL` and an optional
`NOEVIA_REMOTE_<ROLE>_MACHINE` label using operator-local values. Role-named variables take
precedence over their earlier service-name aliases. An unset or empty role list leaves the
host helper inert. `NOEVIA_REMOTE_ENV_FILE` may name an operator-owned configuration file;
the helper reads only `NOEVIA_REMOTE_*` assignments as data, never executes the file, and
preserves values already present in the environment.

Health probes are bounded, advisory, restricted to accepted private/overlay destinations,
and do not follow redirects. URLs must contain no credentials. A 2xx response is healthy.
Without an authentication file, HTTP 401 (needs auth) or 403 means the endpoint is reachable
and requests authentication; a rejection after configured authentication is unhealthy.

`NOEVIA_REMOTE_<ROLE>_AUTH_FILE` optionally supplies complete header lines. The helper checks
the opened file's ownership, regular-file type, mode 0600 or stricter, bounded size, and safe
header syntax. Symlinks are refused; ancestors must not be writable by another user unless
protected by the sticky bit. A configured but unusable file reports
`NOEVIA_REMOTE_<ROLE>_AUTH_FILE unusable` and sends no request. It must not be interpreted as
healthy, unauthenticated, or recovered. Credential contents and paths are never logged.

Keep actual assignments, hosts, endpoints, labels, and authentication-file locations in the
local operator runbook or ignored configuration. These generic interfaces do not authorize
probing a machine, changing its assignments, or starting model inference.
