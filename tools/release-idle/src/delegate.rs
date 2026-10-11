use crate::{fs::Evidence, strict::Result};
use std::{
    fs::File,
    io::Read,
    os::fd::AsRawFd,
    process::{Command, Stdio},
    sync::mpsc,
    thread,
    time::{Duration, Instant},
};
// No business reducer or hashing implementation here. Actual immutable get() owns both.
const GLUE: &str = r#"'use strict';
try {
 const base='/proc/self/fd/0';
 const loader=require(base+'/runtime/dav-parse-wasm.cjs');
 loader.verifyAtStartup({DAV_PARSE_WASM:base+'/runtime/wasm/dav-parse.wasm'});
 const {createJobs}=require(base+'/runtime/jobs.cjs');
 const job=createJobs({dir:base+'/'+process.argv[1]}).get(process.argv[2]);
 if(!job || (Object.hasOwn(job,'revision') && job.lifecycle===null))throw Error('unknown');
 process.stdout.write(JSON.stringify({id:job.id,kind:job.kind,status:job.status}));
} catch { process.exitCode=2; }
"#;
fn drain<R: Read + Send + 'static>(
    mut pipe: R,
    tx: mpsc::Sender<()>,
) -> thread::JoinHandle<(Vec<u8>, bool)> {
    thread::spawn(move || {
        let mut out = Vec::new();
        let r = pipe.by_ref().take(4097).read_to_end(&mut out);
        let failed = r.is_err() || out.len() > 4096;
        if failed {
            let _ = tx.send(());
        }
        out.truncate(4096);
        (out, failed)
    })
}
pub fn get(node: &File, ev: &Evidence, ordinal: usize, id: &str) -> Result<Vec<u8>> {
    let stdin = ev.dir.try_clone().map_err(|_| "fd-clone")?;
    rustix::io::fcntl_setfd(node, rustix::io::FdFlags::empty()).map_err(|_| "node-descriptor")?;
    let child = Command::new(format!("/proc/self/fd/{}", node.as_raw_fd()))
        .env_clear()
        .env(
            "DAV_PARSE_WASM",
            "/proc/self/fd/0/runtime/wasm/dav-parse.wasm",
        )
        .arg("--no-addons")
        .arg("--no-warnings")
        .arg("-e")
        .arg(GLUE)
        .arg(format!("item-{ordinal}"))
        .arg(id)
        .stdin(Stdio::from(stdin))
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn();
    let restored = rustix::io::fcntl_setfd(node, rustix::io::FdFlags::CLOEXEC);
    let mut child = child.map_err(|_| "delegate-spawn")?;
    if restored.is_err() {
        let _ = child.kill();
        let _ = child.wait();
        return Err("node-descriptor");
    }
    let (tx, rx) = mpsc::channel();
    let stdout = child.stdout.take().ok_or("delegate-pipe")?;
    let stderr = child.stderr.take().ok_or("delegate-pipe")?;
    let a = drain(stdout, tx.clone());
    let b = drain(stderr, tx);
    let start = Instant::now();
    let status = loop {
        match child.try_wait() {
            Ok(Some(s)) => break Ok(s),
            Ok(None) => {}
            Err(_) => break Err("delegate-wait"),
        }
        if rx.try_recv().is_ok() {
            break Err("delegate-output-cap");
        }
        if start.elapsed() > Duration::from_secs(5) {
            break Err("delegate-timeout");
        }
        thread::sleep(Duration::from_millis(10));
    };
    if status.is_err() {
        let _ = child.kill();
        let _ = child.wait();
    }
    let output = a.join().map_err(|_| "delegate-reader")?;
    let errors = b.join().map_err(|_| "delegate-reader")?;
    Evidence::write(&ev.dir, &format!("delegate-{ordinal}.stdout"), &output.0)?;
    Evidence::write(&ev.dir, &format!("delegate-{ordinal}.stderr"), &errors.0)?;
    let s = status?;
    if output.1 || errors.1 {
        return Err("delegate-output-cap");
    }
    if !s.success() || !errors.0.is_empty() {
        return Err("delegate-failed");
    }
    Ok(output.0)
}
