# Kev-0.8B decision cutover, limited (#1639)

Owner approval (2026-10-14): "accept the Kev RAM and p50 bars, go limited". Kev-0.8B serves **route, tool
gate, step supervision, chat framing and the load advisor**, with calibration T 0.45. **Sensitivity stays on
Laya-en**: Kev is not qualified for it (#1647), and Hybrid routing stays off. Laya-en (`cowork-laya-1`,
`cowork-laya:0.3.5-noevia5`) keeps running unchanged and is the rollback.

Calibration: T=0.45 is applied in core when `COWORK_DECISION_MODEL=kev-0.8b` (noevia-core#108); nothing in
the deploy repo sets it.

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
`COWORK_DECISION_URL` only. A saved URL survives both the cutover and the rollback, so it is checked with the
real endpoint (the "Admin check" below) before the cutover and again after the rollback.

## 3. Procedure

**Idle gate** (all, right before each step that starts or recreates something: the Kev container start, the
web recreate and every rollback recreate; stop and retry later if one fails):
- no llama activity in 3 minutes; this must print `0`:
  `docker logs --since 3m cowork-llama-1 2>&1 | grep -ciE "launch_slot|print_timing|prompt eval"`;
- no auto-tune running (check the native-autotune state first; never recreate web during an owner-run tune);
- no `up.sh`, backup, release or eval process; `noevia-eval-decisions` is stopped and stays stopped (it mounts the same model store);
- Laya CPU near 0 and `MemAvailable` >= 8 GiB: `MIN_AVAILABLE_GB=8 /mnt/docker/appdata/cowork/eval/decisions/harness/gate.sh`.

**Admin check** (`GET /api/admin/decision-settings`, the real endpoint, from inside web). It needs an admin
session. The owner signs in as an administrator in the browser and puts that session's `Cookie` header value
into `/mnt/docker/appdata/cowork/config/admin-session.env` as one line `ADMIN_COOKIE=<value>` (mode 600, written in
an editor, never typed on a command line; delete the file when the rollback check or the soak is over):
```sh
docker exec --env-file /mnt/docker/appdata/cowork/config/admin-session.env cowork-web-1 node -e '
fetch("http://127.0.0.1:8021/api/admin/decision-settings",{headers:{cookie:process.env.ADMIN_COOKIE}})
 .then(async r=>{const j=await r.json();console.log(r.status,j.source,j.url)}).catch(e=>{console.error("FAIL",e.message);process.exit(1)})'
```
It must print `200 deployment <url>`: `http://laya:8040` before the cutover, `http://kev:11435` after it,
`http://laya:8040` after the rollback. `source` `admin` means a URL saved in Settings is overriding the env: stop,
and have the owner **clear it** in Settings (Settings, Decision service; if there is no clear button, **re-save**
the value this stage needs: `http://kev:11435` for the cutover, `http://laya:8040` for the rollback), then
run the check again until it prints `deployment`. A `403` or `401` means the cookie is stale: sign in again.

**Network checks** (before the Kev start, and again after it):
```sh
docker network inspect cowork_laya --format '{{.Internal}}'   # must print true; otherwise stop
docker exec cowork-web-1 getent hosts kev                       # after the Kev start: must print an address
```

**Soak log copy** (install at least 24 h **before** the cutover, so the baseline exists). The decision log keeps
only the current 1 MiB plus one rotated file, so it is copied every 6 h by a cron line (`crontab -e` as root on
DaServer; the `%` signs are escaped for cron):
```sh
mkdir -p /mnt/docker/appdata/cowork/state/kev-soak
# kev-soak-log-copy
0 */6 * * * D=/mnt/docker/appdata/cowork/state; T=$(date -u +\%Y\%m\%dT\%H\%MZ); cp -a $D/web/system-one-decisions.jsonl.1 $D/kev-soak/$T.jsonl.1 2>/dev/null; cp -a $D/web/system-one-decisions.jsonl $D/kev-soak/$T.jsonl 2>/dev/null; true
```
At the end of the soak (pass or rollback) remove it: `crontab -l | grep -v 'kev-soak-log-copy' | grep -v 'kev-soak/' | crontab -`
(this drops the marker comment and the line), then check with `crontab -l`. The copies hold text-free lines only;
keep them mode 600 and do not open them in a chat or issue.

**Counting without printing content.** The summary tool prints counts only, never rows. Over copies, count
the entries inside a time window with this (set `FROM` and `TO` as UTC ISO strings; copies overlap, so it
de-duplicates identical lines):
```sh
cat /mnt/docker/appdata/cowork/state/kev-soak/*.jsonl* | sort -u | docker exec -i -e FROM="$FROM" -e TO="$TO" cowork-web-1 node -e '
const [from,to]=[process.env.FROM,process.env.TO].map(String);const c={};
require("fs").readFileSync(0,"utf8").split("\n").filter(Boolean).forEach(l=>{let e;try{e=JSON.parse(l)}catch{return}
 if(!(e.at>=from&&e.at<to))return; const k=[e.kind,e.action||e.selected||e.source||e.event,e.fellBack||"-",e.cause||"-"].join("|");c[k]=(c[k]||0)+1});
console.log(JSON.stringify(c,null,1))'
```
(`FROM` and `TO` are timestamps, not secrets; the output is counts keyed by kind, action, fallback and cause.)

**Baseline (Laya, the 24 h before cutover).** Run it with `FROM` = cutover minus 24 h and `TO` = the cutover time.
Record, in `/mnt/docker/appdata/cowork/state/kev-soak/baseline.txt`:
- `S` = the number of `supervise` entries; `E` = those with `action` `escalate` and no `fellBack` (the pauses
  Laya caused); `W` = `supervise` entries with `fellBack` `weak-escalate`;
- per purpose, requests `N` and failures (`cause` in `http-*`, `network`, `aborted`, `invalid-result`, `parse`, `deadline`);
- `B` = benign pauses on Laya: the pauses in that window the owner reviews and marks as unneeded (the log is
  text-free, so only the owner can tell; use 0 if the owner marks none).
If `S` is under 20, extend the baseline window back to the earliest copy, and state the window used.

**Backup (and record the pre-cutover decision URL):**
```sh
P=/boot/config/plugins/compose.manager/projects/Cowork
E=/mnt/docker/appdata/cowork/config/.env
cp -a $P/docker-compose.yml $P/docker-compose.yml.bak.before-kev
cp -a $E $E.bak.before-kev   # keeps mode 600; evidence only, never copied back whole
docker inspect cowork-web-1 cowork-laya-1 --format '{{.Name}} {{.Id}} {{.Image}} {{.State.StartedAt}}' > /mnt/docker/appdata/cowork/state/kev-cutover-before.txt
# the decision URL is not a secret; no other .env value is read or printed
sed -n 's/^COWORK_DECISION_URL=//p' $E | tee /mnt/docker/appdata/cowork/state/kev-cutover-decision-url-before.txt   # expect http://laya:8040
```
Run the Admin check now (expect `200 deployment http://laya:8040`).

**Start Kev (web untouched).** Run the idle gate first: the 5 GiB container start is the heaviest step.
```sh
docker logs --since 3m cowork-llama-1 2>&1 | grep -ciE "launch_slot|print_timing|prompt eval"   # must print 0
docker network inspect cowork_laya --format '{{.Internal}}'                                      # must print true
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
Wait for `healthy` with a bounded loop (5 minutes at most):
```sh
for i in $(seq 1 60); do s=$(docker inspect --format '{{.State.Health.Status}}' cowork-kev 2>/dev/null); [ "$s" = healthy ] && break; sleep 5; done; echo "$s"   # must print healthy
docker exec cowork-web-1 getent hosts kev                                                                                  # must print an address
```
**Verify the image's healthcheck passes with `OLLAYA_API_KEY` set and `--cap-drop ALL`.** That combination has not
been run with this healthcheck before. If the loop does not print `healthy` (it prints `starting` or
`unhealthy`), the step **stops**: `docker logs cowork-kev --tail 20` (no secrets are logged), then
`docker stop cowork-kev`, and do not switch web. Nothing else was changed, so there is nothing more to roll back.

Then load the model once from inside web, which is the only client on that network. The key is read inside the
container from the env file, so it is never on a command line. The eval's cold load took 5.1 s:
```sh
docker exec --env-file /mnt/docker/appdata/cowork/config/kev.env cowork-web-1 node -e '
fetch("http://kev:11435/api/decide",{method:"POST",headers:{"content-type":"application/json",authorization:"Bearer "+process.env.OLLAYA_API_KEY},
 body:JSON.stringify({model:"ollaya.dev/library/kev:0.8b",keep_alive:-1})}).then(r=>r.json()).then(j=>console.log(j.done_reason,Math.round(j.load_duration/1e6),"ms"))'
```
Expect `load`, then check `docker stats --no-stream cowork-kev` (under 5 GiB) and `MemAvailable`.

**Switch web:** edit `.env` per section 2. Add the four new keys to the `web:` `environment:` of
`$P/docker-compose.yml`, below `COWORK_DECISION_URL`, exactly as in `compose.yaml`
(`COWORK_DECISION_MODEL: ${COWORK_DECISION_MODEL:-}` and so on). Then, after the idle gate, recreate web only:
```sh
docker logs --since 3m cowork-llama-1 2>&1 | grep -ciE "launch_slot|print_timing|prompt eval"   # must print 0
bash /mnt/docker/appdata/cowork/tools/preflight/up.sh --env-file /mnt/docker/appdata/cowork/config/.env -- -d --no-build --no-deps --wait --wait-timeout 120 web
```

## 4. Post-checks (synthetic only; one decision per purpose)

First the Admin check (real endpoint): it must print `200 deployment http://kev:11435`. Then, from inside web,
the script below runs the shipped code against the live env only (its settings store is a stub, so it cannot see a
URL saved in Settings; the Admin check does that):
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
- `cowork-kev` and `cowork-laya-1` are healthy with 0 restarts, `OOMKilled=false`; `docker network inspect cowork_laya --format '{{.Internal}}'` prints `true` and `docker exec cowork-web-1 getent hosts kev` prints an address;
- of all running containers, only `cowork-kev` (new) and `cowork-web-1` changed id;
- the web log has no `[system-one] COWORK_DECISION_MODEL names no known decision model` line.

Save the output as `/mnt/docker/appdata/cowork/state/kev-cutover-after.txt`.

## 5. Seven-day soak

The log copy cron line (section 3) keeps running. Once a day record
`docker inspect cowork-kev --format '{{.RestartCount}} {{.State.OOMKilled}}'` and
`docker stats --no-stream cowork-kev` next to the soak notes. At the end, count each window with the counting
command (day by day for the failure rates, the whole soak for the pause counts) and compare with
`baseline.txt`.

Kev stays only if, over all 7 days, **every** line holds:
- `cowork-kev`: `RestartCount` 0, `OOMKilled` false, `docker stats` memory under 4.75 GiB, healthy;
- per purpose and day, failures (`cause` `http-*`, `network`, `aborted`, `invalid-result`, `parse`) under 2% of
  requests, `deadline` under 5%; days with fewer than 20 requests for a purpose are summed with the next day;
- tool gate: 0 `impl-mismatch` and 0 `impl-fault` entries (`TOOL_GATE_IMPL=wasm` with the Kev budget);
- sensitivity: 100% of entries decided by Laya, none by Kev; turns stay local when it is unavailable;
- step supervision escalations: the escalation rate `E/S` over the soak is at least 0.5 times the Laya baseline
  rate and at most 2 times it, and at least 1 escalation per 100 supervise entries if the baseline had any;
  `weak-escalate` fallbacks are no more than the baseline rate plus 5 percentage points;
- benign pauses: the owner-marked unneeded pauses per 100 supervise entries are no higher than the baseline `B`
  per 100 plus 1 (so a baseline of 0 allows at most 1 per 100);
- no new owner complaint about routing, tool use or supervision (each one becomes a labelled issue);
- `MemAvailable` never below 4 GiB while a chat model is loaded (the #697 livelock guard).

Any breach is a rollback, not a tuning session. When the soak ends, remove the cron line (command in section 3)
and delete `admin-session.env`.

## 6. Rollback to Laya (exact)

Run the idle gate first, then:
```sh
E=/mnt/docker/appdata/cowork/config/.env
P=/boot/config/plugins/compose.manager/projects/Cowork
docker logs --since 3m cowork-llama-1 2>&1 | grep -ciE "launch_slot|print_timing|prompt eval"   # must print 0
# remove the four keys by name, then restore the decision URL recorded before the cutover; nothing else in .env is touched
sed -i '/^COWORK_SENSITIVITY_DECISION_URL=/d;/^COWORK_SENSITIVITY_DECISION_MODEL=/d;/^COWORK_DECISION_MODEL=/d;/^COWORK_DECISION_API_KEY=/d;/^COWORK_DECISION_URL=/d' $E
printf 'COWORK_DECISION_URL=%s\n' "$(cat /mnt/docker/appdata/cowork/state/kev-cutover-decision-url-before.txt)" >> $E
grep -c '^COWORK_DECISION_URL=http://laya:8040$' $E     # must print 1 (the recorded value; use that value if it was not laya)
bash /mnt/docker/appdata/cowork/tools/preflight/up.sh --env-file $E -- -d --no-build --no-deps --wait --wait-timeout 120 web
docker stop cowork-kev        # keep the container and files until the cause is understood
```
Never copy `.env.bak.before-kev` back over `.env`: any other edit made during the soak would be lost. With the
keys removed and the URL restored, web sends every decision, sensitivity included, to `http://laya:8040` with
Laya's wording and contract: byte for byte what it sent before #1639. The new compose lines can stay, because
they default to empty. To restore the compose file as well, run
`cp -a $P/docker-compose.yml.bak.before-kev $P/docker-compose.yml` before the `up.sh`.

Check afterwards: run the Admin check (it must print `200 deployment http://laya:8040`; if `source` is `admin`,
clear or re-save as described there), the post-check script must print `shared laya laya sensitivity laya laya`,
and every purpose must report `convaiinnovations/laya`. Remove the cron line and `admin-session.env`.
