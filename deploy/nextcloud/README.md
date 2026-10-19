# AIO notify-push internal callbacks

`repair-push.py` is an administrator helper for a compatible Nextcloud AIO layout. It changes
the notify-push callback URL and adds the exact internal Apache hostname to trusted domains.
It preserves the selected container's image ID, mounts, restart policy, and other settings;
the public endpoint and trusted-proxy list are unchanged. Review the actual AIO layout first.

Run on the Docker host with Python, the Docker CLI, and the access needed to inspect the
selected AIO containers. The helper is dry-run by default:

```sh
python3 deploy/nextcloud/repair-push.py
```

`--apply` is a distinct administrator operation that changes configuration and recreates a
container. It requires the current task's authorization. The helper verifies the AIO self-test
and rolls back its scoped change on failure; an already-correct setting is only verified.

## Compatibility defaults

The helper's current fixed backup-root default is `/mnt/docker/appdata/cowork/backups`.
This is an implementation default, not a published inventory of an installation. There is no
backup-directory CLI override. If using an existing Python container as the runtime, the same
backup root must be a persistent host bind, and the Docker socket and CLI must be available.
Select a compatible image locally; this guide does not name an installed image or a host target.
Do not run with transient backup storage or invent an unsupported path argument.

Configuration snapshots may contain credentials. Keep them outside version control and record
actual backup locations and recovery-container identities only in the local operator runbook.
AIO updates may recreate containers from their default definition; inspect current state and
re-qualify compatibility after an update. Internal callback repair does not make desktop file
sync transactional.
