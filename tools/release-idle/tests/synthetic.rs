#![forbid(unsafe_code)]
#[path = "../src/strict.rs"]
mod strict;
const ID: &str = "00000000-0000-0000-0000-000000000000";
fn event(t: &str, seq: u64, data: serde_json::Value) -> Vec<u8> {
    serde_json::json!({"job":ID,"seq":seq,"type":t,"at":1,"data":data})
        .to_string()
        .into_bytes()
}
#[test]
fn strict_json_rejects_duplicates_and_tails() {
    for raw in [
        br#"{"x":1,"x":2}"#.as_slice(),
        br#"{"x":{"y":1,"y":2}}"#,
        b"{}junk",
        b"{",
        b"\xff",
    ] {
        assert!(strict::json(raw).is_err());
    }
}
#[test]
fn creation_and_torn_tail_are_not_empty() {
    let good = event("job.created", 1, serde_json::json!({"kind":"code"}));
    assert_eq!(strict::journal(&good, ID), Ok("code".into()));
    let mut tail = good.clone();
    tail.extend_from_slice(b"\n{");
    assert!(strict::journal(&tail, ID).is_err());
    assert!(strict::journal(b"", ID).is_err());
    let mut duplicate = good.clone();
    duplicate.push(b'\n');
    duplicate.extend(event("job.created", 2, serde_json::json!({"kind":"code"})));
    assert!(strict::journal(&duplicate, ID).is_err());
}
#[test]
fn unknown_envelopes_and_kinds_refuse() {
    for kind in ["", "Code", "source", "browser", "unknown"] {
        assert!(strict::journal(
            &event("job.created", 1, serde_json::json!({"kind":kind})),
            ID
        )
        .is_err());
    }
    assert!(strict::journal(
        &event("job.created", 2, serde_json::json!({"kind":"code"})),
        ID
    )
    .is_err());
    assert!(strict::journal(&event("job.started", 1, serde_json::json!({})), ID).is_err());
}
#[test]
fn tuning_initial_and_status_contract() {
    assert_eq!(strict::tuning(b"{}", false), Ok(false));
    assert!(strict::tuning(b"{}", true).is_err());
    assert_eq!(
        strict::tuning(br#"{"job":null,"history":{}}"#, true),
        Ok(false)
    );
    for s in ["passed", "failed", "cancelled", "interrupted"] {
        let raw = serde_json::json!({"job":{"status":s}}).to_string();
        assert_eq!(strict::tuning(raw.as_bytes(), false), Ok(false));
    }
    assert_eq!(
        strict::tuning(br#"{"job":{"status":"running"}}"#, true),
        Ok(true)
    );
    for raw in [
        br#"{"job":{}}"#.as_slice(),
        br#"{"job":{"status":"completed"}}"#,
        br#"{"job":false}"#,
        br#"{"history":[]}"#,
    ] {
        assert!(strict::tuning(raw, true).is_err());
    }
}
#[test]
fn statuses_preserve_actual_terminal_contract() {
    for s in ["completed", "failed", "cancelled", "interrupted"] {
        let raw = serde_json::json!({"id":ID,"kind":"code","status":s}).to_string();
        assert_eq!(strict::outcome(raw.as_bytes(), ID, "code"), Ok(false));
    }
    for s in ["queued", "running", "waiting_approval"] {
        let raw = serde_json::json!({"id":ID,"kind":"code","status":s}).to_string();
        assert_eq!(strict::outcome(raw.as_bytes(), ID, "code"), Ok(true));
    }
    assert!(strict::outcome(
        br#"{"id":null,"kind":"code","status":"completed"}"#,
        ID,
        "code"
    )
    .is_err());
}
#[test]
fn chain_modes_and_caps_refuse() {
    let first = event("job.created", 1, serde_json::json!({"kind":"code"}));
    let mut second: serde_json::Value =
        serde_json::from_slice(&event("job.completed", 2, serde_json::json!({})))
            .expect("synthetic fixture");
    second["hash"] = serde_json::json!("a".repeat(64));
    second["previous"] = serde_json::Value::Null;
    let raw = format!("{}\n{}", String::from_utf8(first).expect("fixture"), second);
    assert!(strict::journal(raw.as_bytes(), ID).is_err());
    assert!(strict::journal(&vec![b'x'; 8 * 1024 * 1024 + 1], ID).is_err());
    assert!(strict::journal(&vec![b'x'; 256 * 1024 + 1], ID).is_err());
}
#[test]
fn account_and_journal_id_compatibility() {
    assert!(strict::id("AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA", true));
    assert!(!strict::id("AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA", false));
    assert!(!strict::id("../000000000000000000000000000000000", true));
}
#[path = "../src/fs.rs"]
#[allow(dead_code)]
mod fs;
use std::{
    path::PathBuf,
    sync::atomic::{AtomicUsize, Ordering},
};
static NEXT: AtomicUsize = AtomicUsize::new(0);
struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        let base = std::env::temp_dir()
            .canonicalize()
            .expect("synthetic temp parent");
        let path = base.join(format!(
            "noevia-idle-fixture-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).expect("fresh synthetic directory");
        Self(path)
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}
#[test]
fn directory_absence_is_distinct_from_symlink() {
    let f = Fixture::new();
    let mut tree = fs::Tree::open(&f.0).expect("fixture");
    let root = tree.root.try_clone().expect("fixture");
    assert!(tree
        .child(&root, "jobs", true, true)
        .expect("absent fixture")
        .is_none());
    std::os::unix::fs::symlink(&f.0, f.0.join("jobs")).expect("fixture symlink");
    assert!(tree.child(&root, "jobs", true, true).is_err());
    assert!(tree.stable().is_err());
}
#[test]
fn bounded_iteration_and_hardlinks_refuse() {
    let f = Fixture::new();
    std::fs::write(f.0.join("a"), b"a").expect("fixture");
    std::fs::hard_link(f.0.join("a"), f.0.join("b")).expect("fixture");
    let mut tree = fs::Tree::open(&f.0).expect("fixture");
    let root = tree.root.try_clone().expect("fixture");
    assert!(tree.enumerate(&root, 1).is_err());
    assert!(tree.child(&root, "a", false, false).is_err());
}
#[test]
fn snapshots_and_namespaces_detect_actual_change() {
    let f = Fixture::new();
    std::fs::write(f.0.join("a"), b"abc").expect("fixture");
    let mut tree = fs::Tree::open(&f.0).expect("fixture");
    let root = tree.root.try_clone().expect("fixture");
    tree.enumerate(&root, 2).expect("fixture list");
    let mut file = tree
        .child(&root, "a", false, false)
        .expect("fixture")
        .expect("present");
    assert!(fs::bytes(&mut file, 2).is_err());
    std::fs::write(f.0.join("a"), b"changed").expect("fixture");
    assert!(tree.stable().is_err());
}
#[test]
fn private_evidence_is_fresh_and_never_overwrites() {
    use std::os::unix::fs::MetadataExt;
    let f = Fixture::new();
    let path = f.0.join("evidence");
    let e = fs::Evidence::create(&path).expect("fixture evidence");
    assert_eq!(
        std::fs::metadata(&path).expect("fixture").mode() & 0o777,
        0o700
    );
    fs::Evidence::write(&e.dir, "raw", b"one").expect("fixture write");
    assert_eq!(
        std::fs::metadata(path.join("raw")).expect("fixture").mode() & 0o777,
        0o600
    );
    assert!(fs::Evidence::write(&e.dir, "raw", b"two").is_err());
    assert!(fs::Evidence::create(&path).is_err());
}
#[test]
fn exact_journal_and_row_ceiling_then_one_over() {
    let first = event(
        "job.created",
        1,
        serde_json::json!({"kind":"code","padding":""}),
    );
    let mut v: serde_json::Value = serde_json::from_slice(&first).expect("fixture");
    let base = first.len();
    v["data"]["padding"] = serde_json::Value::String("a".repeat(256 * 1024 - base));
    let row = v.to_string();
    assert_eq!(row.len(), 256 * 1024);
    assert_eq!(strict::journal(row.as_bytes(), ID), Ok("code".into()));
    let mut over = row.into_bytes();
    over.push(b' ');
    assert!(strict::journal(&over, ID).is_err());
    let mut raw = event("job.created", 1, serde_json::json!({"kind":"code"}));
    raw.resize(8 * 1024 * 1024, b'\n');
    assert_eq!(strict::journal(&raw, ID), Ok("code".into()));
    raw.push(b'\n');
    assert!(strict::journal(&raw, ID).is_err());
}
#[test]
fn event_ceiling_then_one_over() {
    let mut raw = event("job.created", 1, serde_json::json!({"kind":"code"}));
    for n in 2..=65536 {
        raw.push(b'\n');
        raw.extend(event("progress", n, serde_json::json!({})));
    }
    assert_eq!(strict::journal(&raw, ID), Ok("code".into()));
    raw.push(b'\n');
    raw.extend(event("progress", 65537, serde_json::json!({})));
    assert!(strict::journal(&raw, ID).is_err());
}
