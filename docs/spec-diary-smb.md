# Diary storage: server-local corpus and SMB access

Current direction (2026-09-14): app-owned Diary with delayed WebDAV backups now
supersedes the proposed SMB working-corpus cutover. See
[the managed Diary design](spec-managed-diary.md). The existing SMB implementation
and pilot below are historical evidence; no real cutover was performed.

Historical status: storage support deployed on 2026-09-12; restricted synthetic SMB pilot
created. Mac SMB authentication is pending. Real Diary cutover is not yet done.

## Implementation evidence — historical

The synthetic pilot exercised sequential saves, stale-write conflicts, reader ownership,
missing-volume refusal, and recovery with stubbed embeddings. It did not authorize a real
corpus cutover. Account identifiers, share settings, host paths, corpus inventories, and recovery
receipts remain in the local operator record. Re-qualify the selected implementation and storage
contract before any migration; do not replay historical deployment steps.

## User direction

Replace the Mac's Nextcloud-synced Diary working folder with a network-mounted
view of the authoritative server files. Preserve noevia capture/retrieval and
the ability for Claude and other clients to work with the same Diary. This
reopens SMB in Workstream 7; the older decision to exclude a share sidecar is
not the current plan for this deployment.

The reported symptom is stale local content after server-side updates. The
explanation that a same-named file cannot sync is unverified. The previous
Nextcloud push repair passed its server self-tests, but Mac synchronization and
pending local/cloud differences were not verified. Do not label that incident
fully diagnosed or resolved.

## Dedicated Diary scope

User clarification (2026-09-12): this is a dedicated Diary storage/share feature,
not a general noevia file server or a replacement for all Nextcloud storage.
Expose only this tenant's Entries, AI Memory and Raw Sources, with a dedicated
share identity, permissions and Mac mount. The share name `Diary` is a working
label to check for collisions during preflight. Keep non-Diary projects, uploads
and existing storage connections unchanged. Any future app controls belong under
Diary settings rather than a global storage migration flow.

A dedicated share does not require another Samba daemon: prefer Unraid's existing
SMB service with isolated configuration. If a separate service is later necessary,
it must receive only the same scoped corpus and its own explicit access policy.

## Intended topology

One dedicated, durable corpus directory on the deployment host, outside Nextcloud's internal
managed data tree, provides the authoritative Markdown files:

- The Diary container accesses it through a local bind mount and the existing
  `local` backend. On the same host, mounting the deployment host's own SMB share back into
  the container would add an unnecessary network dependency.
- Unraid's existing SMB service exports only this user's corpus. Prefer the
  host service over a second Samba container; inspect the existing configuration
  before selecting a share name, disk/pool path, identity or ACL.
- The Mac mounts that share under `/Volumes/...`, outside the Nextcloud desktop
  sync root. Client workflows must select this mount explicitly.
- SQLite journal/index files, authentication state, keys and other tenants'
  directories stay on local server storage, outside the SMB export.
- If Nextcloud access remains useful, connect the canonical corpus using its
  supported external-storage mechanism. Its view is secondary, with external
  change detection verified separately; do not maintain two authoritative copies.

The exact paths and account mapping are implementation preflight outputs, not
values to guess from the corpus name. Preserve Entries, AI Memory, Raw Sources,
existing date/layout settings and tenant isolation.

## Corrections to the pasted proposal

**SMB is not cache-free.** SMB leases allow client caching, and editors can keep
their own in-memory document. Removing desktop synchronization removes a separate
replication step; it does not guarantee an already-open editor refreshes instantly.
Test reopen/refresh and overwrite-by-rename behavior on the actual Mac clients.
[Samba lease documentation](https://www.samba.org/samba/docs/current/man-html/smb.conf.5.html#SMB2LEASES)

**Existing local conditional writes do not arbitrate external editors.**
`services/diary/agent/local_storage.py` uses a per-instance `threading.Lock`, checks
a content hash, then writes a temporary file and performs `os.replace`. A Samba
writer, another backend instance or another process does not acquire that Python
lock. An external save between the hash check and replace can be overwritten.
Atomic replacement prevents partial publication; it does not make the entire
read/check/write sequence a distributed compare-and-swap.

The SQLite journal supports the companion's recorded operations and recovery;
it does not journal or coordinate arbitrary SMB edits. Keep SQLite/WAL on the
server's local filesystem rather than exporting or opening it through SMB.
[SQLite network-filesystem guidance](https://www.sqlite.org/useovernet.html)

**An environment-variable-only migration is not established.**
`agent/app.py` resolves tenant storage: a supplied WebDAV/S3 storage header takes
precedence, and a non-legacy local tenant receives
`<retrieval-db-parent>/users/<user-id>/corpus`, overriding the generic
`CORPUS_LOCAL_ROOT`. Map the selected tenant, its stored connection settings,
effective path and mount first. A scoped bind mount may avoid a new backend;
if path configuration needs code, preserve tenant boundaries explicitly.

**Do not simply share Nextcloud's internal data directory.** Direct disk changes
can bypass its application bookkeeping. Even supported external storage can need
change detection/scanning before Nextcloud reflects external writes.
[Nextcloud external-storage documentation](https://docs.nextcloud.com/server/latest/admin_manual/configuration_files/external_storage_configuration_gui.html)

## Delivery sequence

1. **Inventory and preserve.** Inspect configuration/path metadata and client sync
   status. Reconcile pending Mac/server differences without automatically choosing
   either version; retain both originals and verified backups before cutover.
   Do not use private Diary content as synthetic test input.
2. **Synthetic pilot.** Use a disposable tenant/corpus and a restricted SMB share.
   Verify local bind access, Mac mounts, same-name updates and rename saves.
   Keep the real journal and live storage selection unchanged during this pilot.
3. **Choose the write contract.** Begin the pilot with SMB read access while
   noevia and the scoped Diary API perform guarded writes. For ordinary Mac/Claude
   filesystem editing, require either a tested single-writer editing handoff or
   coordinated locking/conflict preservation covering every writer and rename.
   Do not declare arbitrary simultaneous SMB/API edits safe because ETags exist.
   The existing Claude adapter remains useful on a local corpus.
4. **Implement gaps.** Confirm tenant path selection, failure when storage is
   unavailable (no silent empty replacement corpus), and reliable detection of
   external changes for retrieval/index invalidation. Direct SMB saves do not
   call the existing `workspace_files.py` dirty-index hook.
5. **Controlled migration.** Drain companion writes and outstanding journal work;
   copy/reconcile with hashes; set tenant storage and container mounts; verify
   permissions/layout; switch the Mac/Claude working path. Retire the old Diary
   sync selection only after reconciliation, without deleting the preserved copy.
6. **Verify and retain rollback.** Record the original settings and directories.
   If new writes occurred after switching, reconcile them before rollback; do not
   repoint clients at an older snapshot and lose those writes. Document the
   server change in the canonical the deployment host changelog when implementation occurs.

## Acceptance criteria

- A server-acknowledged synthetic update is visible on Mac reopen; measure the
  latency for both in-place updates and atomic rename replacement.
- If client editing is enabled, stale saves and overlapping companion/client
  writes conflict or preserve both proposals; neither update silently vanishes.
- Mac disconnect/reconnect, server/container restart and missing storage produce
  explicit failure/recovery rather than a false successful save or empty corpus.
- Retrieval notices external edits, renames and deletions within a measured,
  documented interval; a fresh filesystem read alone is not index freshness.
- Only the intended user's corpus is visible. No guest write access, cross-tenant
  traversal, exposed journal/database, or public SMB port is introduced.
- Backup restore and rollback preserve changes made after cutover. All failure
  and concurrency tests use synthetic files.

Storage support and the synthetic share are deployed. The real migration, Mac
mount verification and arbitrary writable SMB workflow are still pending.
