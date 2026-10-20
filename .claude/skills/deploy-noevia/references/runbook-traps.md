# Deployment compatibility and recovery checks

Read `docs/deployment.md` and the installation's local operator runbook before an authorized
release. This guide does not identify a live host or grant deployment permission.

1. **Assemble all pinned components.** Since the repository split, an archive of the integration
   repository alone does not contain the application. Verify source refs and archive checksums.
2. **Inspect effective Compose inputs.** Repository examples and saved operator configuration do
   not synchronize automatically. Back up the copies actually used by the installation and
   validate the effective configuration before a change.
3. **Use the installed preflight wrapper.** Confirm writable mount validation, maintenance-window
   checks, idle-job checks, and service scope. A manager GUI can bypass these checks.
4. **Qualify before activation.** Verify the candidate's binaries, contracts, startup, health,
   and compatibility using isolated state. Do not switch the active release after a failed check.
5. **Retain rollback inputs.** Keep the previous release, images, environment, and Compose files
   together locally. Roll back only the scoped services; an image rollback must not overwrite
   live application databases or private corpora.

Never infer model residency or current versions from historical notes. Exact paths, SSH targets,
origins, backup inventories, network topology, and credentials remain outside version control.
