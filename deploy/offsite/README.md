# Mirroring encrypted off-site backups

[`rclone-sync.sh`](rclone-sync.sh) mirrors Noevia's sealed, content-addressed backup store to
an rclone remote. Choose the destination, schedule, credentials, log location, and retention in
the local operator runbook. This guide does not establish that any account or job is configured.

Backups must already be encrypted before mirroring. Keep the recovery key separately from both
the server and the encrypted copy; a mirror cannot recover data without its matching key.
Use the product's supported recovery-key export and connection flow. Do not publish keys,
authorization tokens, account identifiers, or private recovery paths.

## Configuration interface and defaults

These are defaults in the shipped script, not actual installation settings:

| Variable | Script default | Purpose |
| --- | --- | --- |
| `LOCAL` | `/mnt/user/noevia-backups/offsite` | Source encrypted store |
| `REMOTE` | `gdrive:noevia-offsite` | rclone destination |
| `RCLONE_CONFIG` | `/boot/config/rclone/rclone.conf` | Persistent rclone configuration |
| `LOG` | `offsite-sync.log` beside `LOCAL` | Result and failure log |
| `MAX_DELETE` | `500` | Per-run prune bound |

Set the installation's chosen values explicitly. For a scoped, separately authorized check,
the supported dry-run flag exercises the mirror without copying/pruning remote objects:

```sh
LOCAL="${ENCRYPTED_BACKUP_DIR:?Set the source store}" \
REMOTE="${BACKUP_REMOTE:?Set the rclone destination}" \
RCLONE_CONFIG="${RCLONE_CONFIG_FILE:?Set the local configuration file}" \
LOG="${BACKUP_SYNC_LOG:?Set the local log path}" \
bash deploy/offsite/rclone-sync.sh --dry-run
```

The script still writes its local log/status during a dry run. An actual mirror can copy and
prune remote objects; run it only within the current authorization and recovery plan.
For Google Drive, the supported connection uses `drive.file`; rclone holds the credential.
That scope is not permission to use another account. Keep credential setup and its exact
machine-specific commands in the operator's local record or the product's connection flow.

## Mirror safeguards

The script refuses a source lacking a healthy store structure, so an empty or unmounted
source cannot wipe the remote. It copies before pruning, uses immutable content checks,
and caps deletion. A differing remote object with the same content-addressed name is an
integrity failure, not something to overwrite. Tests are in
[`test_rclone_sync.py`](../tests/test_rclone_sync.py).

Verify rclone's result and content comparison. A successful transfer does not establish
end-to-end restore coverage or that a scheduled job is installed and running.

## Restore

Copy the encrypted remote store into a new, empty local destination using the approved rclone
account and configuration. Point the application at that recovered store and the matching key,
then use its restore flow, which validates file hashes and restores into a new directory.
Verify database integrity, decryption, tenant boundaries, and continued writes with synthetic
data. Preserve live state until the separately authorized recovery decision is made.
