#!/usr/bin/env node
'use strict';
// #697/#720: before Diary's embeddings move from the inference engine to the `embed` sidecar, check
// that both servers produce the same vectors, so the Diary index built on the engine stays valid.
// Embeds a varied synthetic sample (40 documents + 10 queries, no user data) through each endpoint and
// checks two things:
//   1. per-string cosine similarity: the minimum must be >= min (default 0.997). On DaServer (2026-10-01,
//      same nomic GGUF, engine on Vulkan vs sidecar on CPU) this sample measured min 0.99863, median
//      0.99909: float noise, not a different model;
//   2. retrieval agreement: for each query, the top-k documents (k=5) ranked by each embedder; the mean
//      overlap@k must be >= minOverlap (default 0.9; measured 0.96: two of ten queries differed by one document).
//
//   node tools/embed-parity-check.cjs <engine-base> <engine-model> <sidecar-base> <sidecar-model> [min] [minOverlap]
//
// On DaServer the endpoints are internal; run it inside the web container, which reaches both:
//   docker exec -i cowork-web-1 node - http://llama:8080 nomic-embed-text-v1 \
//     http://embed:8080 nomic-embed-text-v1 < tools/embed-parity-check.cjs
//
// The engine request loads its embedding model. Under --models-max 1 that evicts the chat model, so
// check the router's /models first (nothing loaded or chat idle), and unload the embedding model
// afterwards (POST /models/unload). Exit 0: parity holds; 1: it does not; 2: usage or HTTP error.
//
// #1636 additions (all synthetic, no user data):
//   --profile=<nomic-v1|embeddinggemma-2>  frame the sample the way noevia sends it (queries and
//        documents get the profile's prompts; nomic-v1, the default, sends the text unchanged).
//   --dims=<N>  compare the first N dimensions, re-normalised (Matryoshka truncation, e.g. 256).
//   Reference mode: compare one server against reference vectors made elsewhere, e.g. the original
//   checkpoint in sentence-transformers (tools/embed-reference-vectors.py), to check a GGUF build:
//     node tools/embed-parity-check.cjs --print-sample --profile=embeddinggemma-2 > sample.json
//     python3 tools/embed-reference-vectors.py google/embeddinggemma-2 sample.json reference.json
//     node tools/embed-parity-check.cjs --reference=reference.json <base> <model> [min=0.99] [minOverlap=0.8]
//   Inside the web container the reference file must be readable there first, e.g.
//     docker cp reference.json cowork-web-1:/tmp/ && docker exec -i cowork-web-1 node - \
//       --reference=/tmp/reference.json http://embed-next:8080 embeddinggemma-2 < tools/embed-parity-check.cjs
//   A quantised GGUF is not bit-identical to the checkpoint: the reference default is min cosine 0.99
//   and overlap@5 0.8, and the output reports the query-to-best-document score distribution so the
//   retrieval thresholds (0.30 minimum score) can be checked for the new model.

const DOCS = [
  'Went for a long walk by the river this morning; the fog lifted around nine.',
  'Note to self: call the plumber about the dripping kitchen tap before Friday.',
  'Grocery list: oats, 2 litres of milk, lemons, coffee beans, and dish soap.',
  'Finished reading a novel about a lighthouse keeper. The ending felt rushed.',
  'Team meeting moved to 14:30 on Tuesday; bring the quarterly numbers (Q3: +4.2%).',
  'Felt tired all day. Probably the late night; aim for bed before 23:00 tonight.',
  'Planted tomatoes, basil and two rows of carrots in the raised bed.',
  'The train was 25 minutes late again, so I missed the first half of the lecture.',
  'Ideas for the weekend: bake sourdough, repair the bike chain, visit the market.',
  'Booked flights for the conference in Lisbon, 12-15 March, seat 23A.',
  'Heute war ein ruhiger Tag. Ich habe Brot gebacken und am Abend gelesen.',
  'Morgen früh Zahnarzttermin um 8:15 Uhr, nicht vergessen!',
  'Wir sind mit dem Fahrrad zum See gefahren; das Wasser war noch kalt.',
  "Aujourd'hui j'ai visité le musée avec ma sœur ; les tableaux impressionnistes étaient magnifiques.",
  'Penser à renouveler le passeport avant le mois de juin.',
  'Le marché du samedi avait des fraises excellentes, 4 € la barquette.',
  'function add(a, b) { return a + b; } // TODO: handle overflow',
  'SELECT id, title FROM entries WHERE created_at > NOW() - INTERVAL 7 DAY ORDER BY id DESC;',
  'def fib(n):\n    return n if n < 2 else fib(n - 1) + fib(n - 2)',
  'git rebase -i HEAD~3 && git push --force-with-lease',
  'ok',
  '42',
  '!!! ??? ... ;;; ---',
  'Temperature 18.5 °C, humidity 62 %, wind 11 km/h NW, pressure 1013 hPa.',
  'Invoice #2026-0457: 3 × 19.99 = 59.97, VAT 19 % included.',
  'Phone battery died at 3pm; the charger is still at the office.',
  'Started learning the guitar. Chords C, G and Am are fine; F is still impossible.',
  'Dinner with old friends. We laughed about the camping trip when the tent collapsed in the rain.',
  'Mood: anxious about the presentation, but the rehearsal went better than expected.',
  'The cat knocked a glass off the table at 4 a.m. and then looked very pleased with itself.',
  'Ran 5 km in 27:40, a new personal best. Knee felt fine afterwards.',
  'Rewatched an old science-fiction film; the special effects aged badly but the story holds up.',
  'Budget for October: rent 950, food 320, transport 85, savings 300.',
  'Reminder: the library books are due on the 14th; two of them are overdue already.',
  'Spent the afternoon cleaning the attic and found letters from my grandmother written in 1962.',
  'It snowed overnight; the whole street was silent and white when I opened the curtains.',
  'Long reflection: lately I keep postponing the things that matter, filling the days with small urgent tasks instead. ' +
    'Next week I want to block two mornings for the writing project, switch off notifications, and see whether the ' +
    'feeling of being busy but not productive goes away. If it works, keep it as a weekly habit.',
  'Recipe: fry onions in olive oil, add garlic, crushed tomatoes and a pinch of sugar, simmer 20 minutes, season.',
  'Emoji test 😀🎉 — mixed scripts: Ελληνικά, русский, 日本語, العربية.',
  'URL https://example.invalid/path?q=synthetic&n=1 and email someone@example.invalid',
];

const QUERIES = [
  'when is the dentist appointment',
  'what did I plant in the garden',
  'running and exercise progress',
  'travel plans and flights',
  'cooking and recipes',
  'feeling stressed or anxious',
  'Python code snippet',
  'monthly money and expenses',
  'visite au musée',
  'Wetter und Schnee',
];

// noevia's embedding profiles (noevia-core server/embedding-profile.cjs; Diary agent/embedding.py).
const PROFILES = ['nomic-v1', 'embeddinggemma-2'];
function frame(profile, text, kind) {
  if (!PROFILES.includes(profile)) throw Error(`unknown profile ${profile} (known: ${PROFILES.join(', ')})`);
  if (profile === 'nomic-v1') return String(text);
  return kind === 'query' ? `task: search result | query: ${text}` : `title: none | text: ${text}`;
}
function sample(profile = 'nomic-v1', docs = DOCS, queries = QUERIES) {
  return [...docs.map((t) => frame(profile, t, 'document')), ...queries.map((t) => frame(profile, t, 'query'))];
}
function truncate(vec, dims) {
  if (!dims || dims >= vec.length) return vec;
  const v = vec.slice(0, dims);
  const n = Math.sqrt(v.reduce((a, x) => a + x * x, 0)) || 1;
  return v.map((x) => x / n);
}

function cosine(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length || !a.length) return NaN;
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i]; }
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}

async function embed(base, model, texts, fetchImpl = fetch, batch = 8) {
  const url = `${String(base).replace(/\/+$/, '').replace(/\/v1$/, '')}/v1/embeddings`;
  const out = [];
  for (let i = 0; i < texts.length; i += batch) {
    const input = texts.slice(i, i + batch);
    const r = await fetchImpl(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model, input }), signal: AbortSignal.timeout(120000) });
    if (!r.ok) throw Error(`${url} answered HTTP ${r.status}`);
    const items = (await r.json())?.data;
    if (!Array.isArray(items) || items.length !== input.length) throw Error(`${url} returned ${items?.length ?? 0} embeddings for ${input.length} inputs`);
    for (const item of [...items].sort((x, y) => (x.index ?? 0) - (y.index ?? 0))) {
      if (!Array.isArray(item?.embedding) || !item.embedding.length) throw Error(`${url} returned no embedding`);
      out.push(item.embedding);
    }
  }
  return out;
}

function topK(query, docs, k) {
  return docs.map((d, i) => [cosine(query, d), i]).sort((x, y) => y[0] - x[0]).slice(0, k).map(([, i]) => i);
}

function stats(values) {
  const s = [...values].sort((a, b) => a - b);
  const mid = s.length >> 1;
  return { min: s[0], median: s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2, mean: s.reduce((a, b) => a + b, 0) / s.length, max: s[s.length - 1] };
}

// How strongly each query matches its best document (and its 5th): the numbers the retrieval
// thresholds are set against, so a new model's score range can be checked before cutover.
function queryScores(vectors, nDocs) {
  const top1 = [], top5 = [];
  for (let q = nDocs; q < vectors.length; q++) {
    const s = vectors.slice(0, nDocs).map((d) => cosine(vectors[q], d)).sort((x, y) => y - x);
    top1.push(s[0]); top5.push(s[Math.min(4, s.length - 1)]);
  }
  return { top1: stats(top1), top5: stats(top5) };
}

function compare(a, b, { nDocs, nQueries, k, min, minOverlap }) {
  const sims = a.map((_, i) => cosine(a[i], b[i]));
  const cos = stats(sims);
  const kk = Math.min(k, nDocs);
  const overlaps = Array.from({ length: nQueries }, (_, q) => {
    const ta = topK(a[nDocs + q], a.slice(0, nDocs), kk);
    const tb = new Set(topK(b[nDocs + q], b.slice(0, nDocs), kk));
    return ta.filter((i) => tb.has(i)).length / kk;
  });
  const overlap = nQueries ? overlaps.reduce((x, y) => x + y, 0) / overlaps.length : 1;
  const ok = sims.every(Number.isFinite) && cos.min >= min && overlap >= minOverlap;
  return { ok, similarity: cos.min, cosine: cos, overlapAtK: overlap, k: kk, overlaps, strings: a.length, min, minOverlap };
}

/**
 * One server against reference vectors made elsewhere. `reference` is the JSON written by
 * tools/embed-reference-vectors.py: { texts, vectors, docs, queries, profile, source }.
 */
async function checkReference({ base, model, reference, min = 0.99, minOverlap = 0.8, k = 5, dims = 0, fetchImpl = fetch }) {
  const { texts, vectors, docs: nDocs, queries: nQueries } = reference || {};
  if (!Array.isArray(texts) || !Array.isArray(vectors) || texts.length !== vectors.length || nDocs + nQueries !== texts.length) {
    throw Error('reference file must hold texts, vectors (one per text), docs and queries counts');
  }
  const got = (await embed(base, model, texts, fetchImpl)).map((v) => truncate(v, dims));
  const ref = vectors.map((v) => truncate(v, dims));
  if (got[0].length !== ref[0].length) throw Error(`the server returned ${got[0].length} dimensions, the reference has ${ref[0].length} (use --dims)`);
  const r = compare(got, ref, { nDocs, nQueries, k, min, minOverlap });
  return { ...r, mode: 'reference', profile: reference.profile || null, source: reference.source || null, dimensions: [got[0].length, ref[0].length], scores: { server: queryScores(got, nDocs), reference: queryScores(ref, nDocs) } };
}

async function check({ engine, engineModel, sidecar, sidecarModel, min = 0.997, minOverlap = 0.9, k = 5, docs = DOCS, queries = QUERIES, profile = 'nomic-v1', dims = 0, fetchImpl = fetch }) {
  const texts = sample(profile, docs, queries);
  // Sequential: the engine request may load a model; keep the two servers' load apart.
  const a = (await embed(engine, engineModel, texts, fetchImpl)).map((v) => truncate(v, dims));
  const b = (await embed(sidecar, sidecarModel, texts, fetchImpl)).map((v) => truncate(v, dims));
  const sims = texts.map((_, i) => cosine(a[i], b[i]));
  const cos = stats(sims);
  const kk = Math.min(k, docs.length);
  const overlaps = queries.map((_, q) => {
    const ta = topK(a[docs.length + q], a.slice(0, docs.length), kk);
    const tb = new Set(topK(b[docs.length + q], b.slice(0, docs.length), kk));
    return ta.filter((i) => tb.has(i)).length / kk;
  });
  const overlap = queries.length ? overlaps.reduce((x, y) => x + y, 0) / overlaps.length : 1;
  const ok = sims.every(Number.isFinite) && cos.min >= min && overlap >= minOverlap;
  return { ok, similarity: cos.min, cosine: cos, overlapAtK: overlap, k: kk, overlaps, strings: texts.length, dimensions: [a[0].length, b[0].length], min, minOverlap, profile, scores: { a: queryScores(a, docs.length), b: queryScores(b, docs.length) } };
}

module.exports = { cosine, check, checkReference, embed, topK, frame, sample, truncate, queryScores, DOCS, QUERIES, PROFILES };

function parseArgs(argv) {
  const flags = {}, rest = [];
  for (const a of argv) {
    const m = /^--([a-z-]+)(?:=(.*))?$/.exec(a);
    if (m) flags[m[1]] = m[2] ?? true; else rest.push(a);
  }
  return { flags, rest };
}

if (require.main === module || !module.parent) {
  const { flags, rest } = parseArgs(process.argv.slice(2));
  const profile = typeof flags.profile === 'string' ? flags.profile : 'nomic-v1';
  const dims = flags.dims ? Number(flags.dims) : 0;
  const done = (p) => p.then((r) => { console.log(JSON.stringify(r)); process.exit(r.ok ? 0 : 1); })
    .catch((e) => { console.error(String(e?.message || e)); process.exit(2); });
  if (!PROFILES.includes(profile) || !(Number.isInteger(dims) && dims >= 0)) {
    console.error(`--profile must be one of ${PROFILES.join(', ')}; --dims a whole number`);
    process.exit(2);
  }
  if (flags['print-sample']) {
    console.log(JSON.stringify({ profile, docs: DOCS.length, queries: QUERIES.length, texts: sample(profile) }));
  } else if (flags.reference) {
    const [base, model, min, minOverlap] = rest;
    if (!base || !model || typeof flags.reference !== 'string') {
      console.error('usage: embed-parity-check.cjs --reference=<file.json> <base> <model> [min=0.99] [minOverlap=0.8] [--dims=N]');
      process.exit(2);
    }
    let reference;
    try { reference = JSON.parse(require('node:fs').readFileSync(flags.reference, 'utf8')); } catch (e) { console.error(`cannot read ${flags.reference}: ${e.message}`); process.exit(2); }
    done(checkReference({ base, model, reference, dims, min: min ? Number(min) : 0.99, minOverlap: minOverlap ? Number(minOverlap) : 0.8 }));
  } else {
    const [engine, engineModel, sidecar, sidecarModel, min, minOverlap] = rest;
    if (!engine || !engineModel || !sidecar || !sidecarModel) {
      console.error('usage: embed-parity-check.cjs [--profile=nomic-v1|embeddinggemma-2] [--dims=N] <engine-base> <engine-model> <sidecar-base> <sidecar-model> [min=0.997] [minOverlap=0.9]');
      console.error('       embed-parity-check.cjs --reference=<file.json> <base> <model> [min=0.99] [minOverlap=0.8]');
      console.error('       embed-parity-check.cjs --print-sample [--profile=...]');
      process.exit(2);
    }
    done(check({ engine, engineModel, sidecar, sidecarModel, profile, dims, min: min ? Number(min) : 0.997, minOverlap: minOverlap ? Number(minOverlap) : 0.9 }));
  }
}
