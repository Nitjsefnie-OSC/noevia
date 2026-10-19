# noevia agent entry point

Read [docs/agent-brief.md](docs/agent-brief.md) before changing code, then
[docs/roadmap.md](docs/roadmap.md) for current status and priorities.

- Since the repo split (#952) the code lives in
  [noevia-web](https://github.com/sbstndalton/noevia-web) (client),
  [noevia-core](https://github.com/sbstndalton/noevia-core) (server, contracts, code-sandbox)
  and [noevia-services](https://github.com/sbstndalton/noevia-services) (Python sidecars).
  This repo pins them in `release/versions.lock`; do not re-add `apps/web/` or `services/*`
  here (CI refuses them). See the layout table in the agent brief.
- [DEPLOY.md](DEPLOY.md) and [cowork.setup.json](cowork.setup.json) describe
  generic fresh installs. For existing installations, combine the generic
  [docs/deployment.md](docs/deployment.md) guide with the operator-owned local runbook.
  Saved Compose Manager configuration may differ from fresh-install examples; keep its private paths and state outside version control.
- Cowork-prefixed identifiers are intentional compatibility contracts. Do not
  rename env vars, images, containers, cookies, state paths, or storage keys.
- Preserve tenant isolation and all three write-approval actions. Never send
  prompts to the real diary or modify its corpus for testing; use synthetic
  fixtures and mocked tools.

## Public repository privacy

Keep personal names and associations, private hostnames/IPs, personal filesystem paths,
real account/project/source examples, and deployment inventories out of new public code,
documentation, examples, issues, comments, and PR text. Use synthetic examples, generic
placeholders, or configurable values. Preserve required third-party attribution.

Keep actual installation details only in private local configuration or documentation that
is verified ignored and untracked. Preserve runtime functionality and compatibility contracts;
this rule does not authorize a blanket rewrite, deployment, access change, or history rewrite.
