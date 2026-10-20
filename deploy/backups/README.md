# Application backup and restore

This guide describes backup coverage and verification. Configure schedules, destinations,
retention, selected services, and recovery receipts in the installation's local operator
runbook, excluded from Git. It is not a record of a running backup job.

## Coverage

- Include application state, configuration, tenant mappings, encryption keys, and the effective
  Compose inputs required to restore the same release. Match each key with the databases and
  provider files it encrypts.
- Coordinate writers before taking a consistent snapshot. Record service shutdown/startup
  dependencies and the expected interruption locally.
- Verify that each configured Diary storage backend is actually covered. A remote corpus is
  not backed up merely because the application's local configuration is included.
- Keep the destination outside application writable roots and file-sharing exports. A backup
  on the same machine is local recovery; it is not an independent off-site copy.

An operator may use a host backup plugin or another qualified mechanism. Inspect the selected
tool's current configuration and logs rather than assuming a historical schedule still runs.
Check archive completeness and writer recovery; a successful process exit is insufficient.

## Restore verification

Restore into a new private directory first and validate extraction paths. Check SQLite integrity,
configuration presence, encryption-key compatibility, and readable restored credentials without
printing their values. Load any required database extensions when checking vector databases.
Never send restored private content to an inference provider for verification.

Use synthetic state to test login, prior entries, continued writes, and stale-write conflicts.
The historical `qa/restore-http.cjs` workflow exercised these behaviors with real web/Diary
processes and a synthetic HTTP provider. A synthetic workflow does not prove a particular
production archive is complete, nor a disaster-site or container-image restore.

Before an authorized live restore, stop writers, preserve displaced state, and reconcile writes
newer than the backup. Preserve tenant boundaries and storage identity markers. An image rollback
does not authorize replacing application databases or a Diary corpus.

## Off-site copies

Store encryption recovery material separately from the encrypted backup. Verify the off-site
copy and restore process independently. Provider selection, account configuration, cost, and
retention are operator decisions; see [the off-site guide](../offsite/README.md).
