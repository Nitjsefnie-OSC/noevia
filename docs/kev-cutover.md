# Kev-0.8B decision cutover, limited (#1639)

Owner approval (2026-10-14): "accept the Kev RAM and p50 bars, go limited". Kev-0.8B serves **route, tool
gate, step supervision, chat framing and the load advisor**, with calibration T 0.45. **Sensitivity stays on
Laya-en**: Kev is not qualified for it (#1647), and Hybrid routing stays off. Laya-en (`cowork-laya-1`,
`cowork-laya:0.3.5-noevia5`) keeps running unchanged and is the rollback.

This page is the procedure. Nothing here has been run. Key names only: secret values are never written in
this repo, in an issue or in a log.

## 0. Preconditions (all must hold; otherwise stop)

1. **Core:** noevia-core#108 is merged and a web image built from it is live (normal release flow). Order
   matters: the old web image speaks only Laya's contract, so pointing it at Kev makes every decision
   fail (it falls back, but nothing is decided). With #108 and the new keys empty, the web sends exactly
   what it sends today.
2. **Deploy:** this PR is merged, and the four new keys are added to the **live** compose file's `web`
   environment (the hand-maintained third copy, see step 3); `up.sh`'s preflight warns about missing keys.
3. **Model on disk:** Kev-0.8B is already on DaServer from the #1639 eval. No download is needed or
   allowed. The manifest is `/mnt/docker/appdata/cowork/eval/decisions/models/models/manifests/ollaya.dev/library/kev/0.8b`
   (sha256 of the manifest file `8a0d4094df504ca7329bc999dabbb89c15ad5221f55728acde0ff61c2b3909f2`). It
   pins the layers: Qwen3.5-0.8B-Base weights `sha256:c2b1e5a1…bab6c` (1.75 GB, HF rev `dc7cdfe2`),
   the Kev adapter `sha256:9b908623…885a` and head `sha256:f400bd12…20b6` (HF `jaredpalmer/kev-0.8b`
   rev `9a45d25e`), the tokenizer, the decision graph and the upstream calibration (`temperature` 2.35,
   applied by Ollaya; core's T 0.45 is fitted on top of the served probabilities, as in the eval).
   Check before starting that the manifest still hashes to the value above. If it is missing or differs,
   **stop**: the model is not on DaServer, and this runbook does not download it.
4. **Image on disk:** `ghcr.io/ollaya-dev/ollaya:0.13.0@sha256:31f749def61165d7bbb15def4e3d799a403461e0b8b777f359a924bb9b845ce6`
   (local image id `sha256:5d6f3bad7a698504c4547f2dd35df7094e709031e8ac7cb2a9f12d13dd1abbf9`, used by the
   stopped `noevia-eval-decisions` container). Always run it **by digest**. If it is not on disk, stop and
   ask the owner before pulling.
5. **Memory:** Kev's measured peak was VmHWM **4.58 GiB** (4,914,647,040 B) with the cgroup at its 5 GiB
   cap (page cache included), at 2 and at 4 CPUs. Laya stays up alongside it (6 GiB limit, about 2.2 GiB
   used). `MemAvailable` must be at least 8 GiB before the start (the eval's gate).

## 1. How Kev is served

One container, **outside** compose (so a compose `up` never touches it), on the internal decision network
that web and Laya already share:

| Setting | Value | Why |
| --- | --- | --- |
| Name | `cowork-kev` | |
| Image | `ghcr.io/ollaya-dev/ollaya:0.13.0@sha256:31f749de…5ce6` | the evaluated build, by digest |
| Network | `cowork_laya` (`internal: true`), alias **`kev`** | no internet egress at all; core accepts `http://kev:<port>` (noevia-core#108) |
| Published ports | **none** | web reaches it on the internal network |
| CPU | `--cpus 2`, `OLLAYA_THREADS=2`, `OLLAYA_DEVICE=cpu` | like-for-like with Laya and the 2-CPU latency run |
| Memory | `--memory 5g --memory-swap 5g` | see the note below |
| Other caps | `--pids-limit 512 --cap-drop ALL --security-opt no-new-privileges`, uid 1000 (image default) | as evaluated |
| Model store | `-v /mnt/docker/appdata/cowork/eval/decisions/models:/home/ollaya/.ollaya` | the files the eval measured; do not clean this directory while Kev is live |
| Offline | `OLLAYA_REGISTRY=http://127.0.0.1:9`, `OLLAYA_HF_ENDPOINT=http://127.0.0.1:9` | Ollaya itself never fetches; the internal network blocks the rest |
| Residency | `OLLAYA_MAX_LOADED_MODELS=1`, `OLLAYA_KEEP_ALIVE=-1` | one model, kept loaded |
| Key | `OLLAYA_API_KEY` from `/mnt/docker/appdata/cowork/config/kev.env` (mode 600) | the same value as web's `COWORK_DECISION_API_KEY` |
| Healthcheck | the image's own: `/usr/local/bin/ollaya-healthcheck`, every 30 s, timeout 5 s, start period 15 s, 3 retries | |
| Restart | `--restart unless-stopped` | |

**Memory limit.** The brief says "about 4.6 GiB", but the measured VmHWM is 4.58 GiB. A 4.6 GiB hard
limit would leave about 20 MiB of headroom, and the cgroup also counts page cache, so it risks an OOM kill
under load. Use **5g**, which is what the eval ran at with no OOM. If the owner wants 4.6g anyway, run
the step-4 checks plus 100 synthetic decisions at that limit first, and check `OOMKilled=false`.

## 2. Env keys (web, `/mnt/docker/appdata/cowork/config/.env`)

| Key | Value at cutover | Today |
| --- | --- | --- |
| `COWORK_DECISION_URL` | `http://kev:11435` | `http://laya:8040` |
| `COWORK_DECISION_MODEL` | `kev-0.8b` | empty |
| `COWORK_DECISION_API_KEY` | the Kev key (secret; same as `OLLAYA_API_KEY` in `kev.env`) | empty |
| `COWORK_SENSITIVITY_DECISION_URL` | `http://laya:8040` | empty |
| `COWORK_SENSITIVITY_DECISION_MODEL` | `laya` | empty |

No other key changes. `NOEVIA_FEATURE_*` switches are unchanged; Hybrid routing stays off.

The **decision settings saved in Settings** override `COWORK_DECISION_URL`, and the model id belongs to
`COWORK_DECISION_URL` only. Before the cutover, check `GET /api/admin/decision-settings` as an admin. If
`source` is `admin` with another URL, Kev would get the Laya wording and contract there, so the owner
must either clear that setting or save `http://kev:11435`.

## 3. Procedure

**Idle gate** (all, right before each step that recreates something; stop and retry later if one fails):
- no llama activity in 3 minutes: `docker logs --since 3m cowork-llama-1 2>&1 | grep -ciE "launch_slot|print_timing|prompt eval"` is `0`;
- no auto-tune running (check the native-autotune state first; never recreate web during an owner-run tune);
- no `up.sh`, backup, release or eval process; `noevia-eval-decisions` is stopped and stays stopped (it mounts the same model store);
- Laya CPU near 0 and `MemAvailable` ≥ 8 GiB: `MIN_AVAILABLE_GB=8 /mnt/docker/appdata/cowork/eval/decisions/harness/gate.sh`.

**Backup:**
```sh
P=/boot/config/plugins/compose.manager/projects/Cowork
cp -a $P/docker-compose.yml $P/docker-compose.yml.bak.before-kev
cp -a /mnt/docker/appdata/cowork/config/.env /mnt/docker/appdata/cowork/config/.env.bak.before-kev   # keeps mode 600
docker inspect cowork-web-1 cowork-laya-1 --format '{{.Name}} {{.Id}} {{.Image}} {{.State.StartedAt}}' > /mnt/docker/appdata/cowork/state/kev-cutover-before.txt
```

**Start Kev (web untouched):**
```sh
sha256sum /mnt/docker/appdata/cowork/eval/decisions/models/models/manifests/ollaya.dev/library/kev/0.8b   # must be 8a0d4094…09f2
(umask 077; [ -s /mnt/docker/appdata/cowork/config/kev.env ] || printf 'OLLAYA_API_KEY=%s\n' "$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')" > /mnt/docker/appdata/cowork/config/kev.env)
docker run -d --name cowork-kev --restart unless-stopped \
  --network cowork_laya --network-alias kev \
  --cpus 2 --memory 5g --memory-swap 5g --pids-limit 512 \
  --cap-drop ALL --security-opt no-new-privileges \
  --env-file /mnt/docker/appdata/cowork/config/kev.env \
  -e OLLAYA_DEVICE=cpu -e OLLAYA_THREADS=2 -e OLLAYA_MAX_LOADED_MODELS=1 -e OLLAYA_KEEP_ALIVE=-1 \
  -e OLLAYA_REGISTRY=http://127.0.0.1:9 -e OLLAYA_HF_ENDPOINT=http://127.0.0.1:9 \
  -v /mnt/docker/appdata/cowork/eval/decisions/models:/home/ollaya/.ollaya \
  ghcr.io/ollaya-dev/ollaya:0.13.0@sha256:31f749def61165d7bbb15def4e3d799a403461e0b8b777f359a924bb9b845ce6
```
Wait for `healthy`, then load the model once from inside web, which is the only client on that network.
The eval's cold load took 5.1 s:
```sh
docker exec -e K="$(sed -n 's/^OLLAYA_API_KEY=//p' /mnt/docker/appdata/cowork/config/kev.env)" cowork-web-1 node -e '
fetch("http://kev:11435/api/decide",{method:"POST",headers:{"content-type":"application/json",authorization:"Bearer "+process.env.K},
 body:JSON.stringify({model:"ollaya.dev/library/kev:0.8b",keep_alive:-1})}).then(r=>r.json()).then(j=>console.log(j.done_reason,Math.round(j.load_duration/1e6),"ms"))'
```
Expect `load`, then check `docker stats --no-stream cowork-kev` (under 5 GiB) and `MemAvailable`.

**Switch web:** edit `.env` per section 2. Add the four new keys to the `web:` `environment:` of
`$P/docker-compose.yml`, below `COWORK_DECISION_URL`, exactly as in `compose.yaml`
(`COWORK_DECISION_MODEL: ${COWORK_DECISION_MODEL:-}` and so on). Then, after the idle gate, recreate web only:
```sh
bash /mnt/docker/appdata/cowork/tools/preflight/up.sh --env-file /mnt/docker/appdata/cowork/config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web
```

## 4. Post-checks (synthetic only; one decision per purpose)

From inside web, through the shipped code and the live env (Settings' saved URL is checked separately in
section 2):
```sh
docker exec cowork-web-1 node -e '
const s=require("/app/server/decision-settings.cjs").createDecisionSettings({store:{get:()=>null,set(){}},env:process.env});
const b=s.backend(), z=s.sensitivityBackend();
console.log("shared",b.model,b.wording,"sensitivity",z.model,z.wording);
const two=(purpose,q,a,c)=>({kind:"choice",purpose,question:q,context:{stateText:"Synthetic check, no user data."},options:[{id:a,label:a},{id:c,label:c}]});
(async()=>{
 for (const [name,be,req] of [
  ["route",b,two("model.route","Which configured model role should answer this user message?","fast","smart")],
  ["tool.gate",b,two("tool.gate","Synthetic: which tool?","web_search","none")],
  ["chat.frame.kind",b,two("chat.frame.kind","What kind of chat does this first message start?","question","idea")],
  ["load.advisor",b,two("load.advisor","Which of these does its error text describe?","oom","unknown")],
  ["routing.sensitivity",z,two("routing.sensitivity","Does this content contain sensitive personal or confidential information?","sensitive","not_sensitive")]]) {
  const t=Date.now(); const r=await be.decide(req); console.log(name,r.selected,r.metadata.model,Date.now()-t,"ms");
 }
 const t=Date.now(); const v=await b.supervise({goal:"Synthetic check",outputs:[{role:"tool",content:"synthetic result"}]}); console.log("step.supervise",v.action,Date.now()-t,"ms");
})().catch(e=>{console.error("FAIL",e.reason||e.message);process.exit(1);});'
```
Pass criteria:
- the first line reads `shared kev-0.8b kev sensitivity laya laya`;
- every purpose answers with one of its options, `metadata.model` is `kev-0.8b` for the five shared
  purposes and `convaiinnovations/laya` for sensitivity, and each takes under 1.5 s;
- `cowork-kev` and `cowork-laya-1` are healthy with 0 restarts, `OOMKilled=false`;
- of all running containers, only `cowork-kev` (new) and `cowork-web-1` changed id;
- the web log has no `[system-one] COWORK_DECISION_MODEL names no known decision model` line.

Save the output as `/mnt/docker/appdata/cowork/state/kev-cutover-after.txt`.

## 5. Seven-day soak

Once a day, copy web's decision log (`system-one-decisions.jsonl` in web's data directory; it keeps
only the current 1 MiB plus one rotated file) next to the soak notes, and record
`docker inspect cowork-kev --format '{{.RestartCount}} {{.State.OOMKilled}}'` and `docker stats --no-stream cowork-kev`.

Kev stays only if, over all 7 days:
- `cowork-kev`: 0 restarts, never OOM-killed, memory under 4.75 GiB, healthy;
- per purpose and day, decision failures (`http-*`, `network`, `aborted`, `invalid-result`, `parse`)
  under 2% of requests, deadline misses under 5%;
- tool gate: 0 `impl-mismatch` and 0 `impl-fault` entries (`TOOL_GATE_IMPL=wasm` with the Kev budget);
- sensitivity: every entry decided by Laya, none by Kev; turns stay local when it is unavailable;
- step supervision: no rise in benign pauses reported, and at least the escalations seen on Laya;
- no new owner complaint about routing, tool use or supervision (each one becomes a labelled issue);
- `MemAvailable` never below 4 GiB while a chat model is loaded (the #697 livelock guard).

Any breach is a rollback, not a tuning session.

## 6. Rollback to Laya (exact)

```sh
cp -a /mnt/docker/appdata/cowork/config/.env.bak.before-kev /mnt/docker/appdata/cowork/config/.env
bash /mnt/docker/appdata/cowork/tools/preflight/up.sh --env-file /mnt/docker/appdata/cowork/config/.env -- -d --no-build --no-deps --wait --wait-timeout 180 web
docker stop cowork-kev        # keep the container and files until the cause is understood
```
With the keys empty again, web sends every decision, sensitivity included, to `http://laya:8040` with
Laya's wording and contract: byte for byte what it sent before #1639. The new compose lines can stay,
because they default to empty. To restore the compose file as well, run
`cp -a $P/docker-compose.yml.bak.before-kev $P/docker-compose.yml` before the `up.sh`. Check afterwards:
the post-check script prints `shared laya laya sensitivity laya laya`, and every purpose reports
`convaiinnovations/laya`.
