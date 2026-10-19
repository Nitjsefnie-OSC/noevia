# Code mode — staged, off (historical snapshot, 2026-09-17)

> **Historical.** This records the state of the deployment host on 2026-09-17 (release `1fe3f1b`, flag off)
> and is kept only because the roadmap and master-prompt history link to it. It is not current:
> the Code sandbox has since moved to newer images (consult current source, release qualification, and the local operator runbook), and the commands and image names below are not
> instructions. Current setup: `services/code-sandbox/README.md` and
> `deploy/examples/code-sandbox.override.yml`.

This historical staging exercise used a disposable `scratch` repository and an isolated sandbox.
Its installation-specific image inventory, volume ownership, and saved Compose state remain
in the local operator archive. It does not establish the current state of any installation.

The synthetic fixture's `median()` had two deliberate bugs (lexicographic in-place sorting and
missing averaging for even-length inputs). Its test file was held unchanged. Equivalent disposable
fixtures are useful for qualifying the full task/approval/result path before granting real
repository access. Do not infer authorization to run such a test from this historical note.

## Historical sandbox qualification

Escape probes against the image under the override's hardening:

| Probe | Result |
|---|---|
| write `/etc`, `/srv` | refused (read-only root) |
| write the source repo as the harness | refused |
| Docker socket present | absent |
| secrets in the environment | none |
| `su root` | authentication failure |
| harness version | 1.18.31, `uid=1000(node)` |
| task clone: edit, `git status`, `git commit` | all succeed |
| noevia fetching the task branch back | succeeds |

## What staging found, and the code now handles

1. **Worktrees must live on the shared volume**, at a path identical in both containers —
   noevia sends an absolute path and the supervisor resolves that same path
   (`CODE_WORKSPACE_ROOT`).
2. **A new workspace is root-owned and the harness is not root**, so it must be handed over
   (`CODE_HARNESS_USER`). A handover that fails refuses the task.
3. **A handed-over git *worktree* cannot commit** — its objects and refs live in the source
   repository's `.git`, which the harness cannot write. With a separate harness user a task
   therefore gets `git clone --shared`: a repository it owns, the source read-only to it, no
   objects copied, and the branch fetched back on release.
4. **The tmpfs mounts need `uid=1000,gid=1000`**, not just a mode, or the harness cannot write
   its own `.gitconfig`.

## Example capability wiring

For a separately authorized qualification, the historical contract used these example keys on
`web`. Verify the current contract and preserve the operator configuration before any change:

   ```
   NOEVIA_FEATURE_CODE_HARNESS=true
   CODE_HARNESS_ENDPOINT=code-sandbox:8030
   CODE_REPOS=scratch|/workspaces/repos/scratch
   CODE_WORKSPACE_ROOT=/workspaces/trees
   CODE_HARNESS_USER=1000:1000
   ```

   plus `code-workspaces:/workspaces` mounted on web, and web and the sandbox both on the
   internal `code` network.
The sandbox and web share the same workspace path and an internal network. Activation and a
synthetic task run are separate authorized operations; inspect every approval when qualifying them.

Do not point it at a repository that matters until that has been done once. The whole contract
is still tested only against a scripted fake agent.
