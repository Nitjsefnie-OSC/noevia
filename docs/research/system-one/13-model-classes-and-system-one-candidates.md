# 13. Model classes, and choosing the generic System-One model (draft for review)

Written 2026-09-21, after the RAG reranker went live (release `67f336e`). This document corrects
how the earlier docs used "System One". **The live reranker is not the generic System-One
implementation**, and it does not answer any question about one. Evidence tags as in doc 3:
[P] primary source, [B] independent benchmark, [V] vendor figure, [M] measured by us,
[E] our estimate, [—] unknown.

## 13.1 Three model classes (terminology used in all System-One docs)

| Class | Name | Job | Examples | Interface in noevia |
|---|---|---|---|---|
| **A** | **Specialised discriminative model** | One narrow scoring task it was trained for | `Qwen3-Reranker-0.6B` (RAG ranking, live); the embedding model (`nomic-embed-text-v1`) | Its own purpose, e.g. `rag.rerank`, through `decisions.rank()` or a dedicated call |
| **B** | **Generic System-One decision model** | Bounded orchestration decisions: pick, judge, stop, escalate | Candidates: Laya, SemIf-style option-logit readout (4B or smaller), a closed System-1 API (remote reference); floor: deterministic heuristics | `decide({ state, question, choices, constraints })`, provider-independent (doc 4) |
| **C** | **System-Two generative model** | Generation, reasoning, coding, synthesis | Qwen3.5-4B/9B, Gemma-4 E2B/E4B, gpt-oss-20B | Chat and Code paths |

```
noevia decision layer  (decide / rank; validation, deadline, fallback, logging: doc 4)
│
├── A. Specialised discriminative models
│   ├── rag.rerank      → Qwen3-Reranker-0.6B   (live, flag NOEVIA_FEATURE_RAG_RERANK)
│   └── embeddings      → nomic-embed-text-v1   (CPU embed container)
│
├── B. Generic System-One (UNRESOLVED; this doc)
│   └── model selection, mid-task switching, tool selection, retry/continue/stop,
│       output evaluation, escalation, context utility, residency
│       → backend: laya | llama-logit (SemIf-style) | remote | heuristic
│
└── C. System-Two generators
    └── Qwen / Gemma / gpt-oss …
```

Rules:
- **A is judged only on its own task.** The reranker stays because it measured better on RAG
  (80% → 86–91% correct on the synthetic set). A class-B model replaces it only if it beats it
  **on RAG ranking**, not to make the architecture uniform.
- **B is judged on noevia's bounded decisions.** A class-A score (reranking quality) is no
  evidence about B, and the reranker is never used as a class-B backend. It returns relevance
  logits for query–passage pairs, not calibrated answers to typed questions.
- **Callers do not know which backend answered.** Every class-B call goes through `decide()`.
  Specialised class-A purposes can have their own entry point, but they still sit behind the
  same validation, deadline and fallback.
- **Mixing is allowed.** Several class-A components plus one small class-B model is a legitimate
  end state (13.4).

## 13.2 What was verified about Laya (direct investigation, 2026-09-21)

Sources: the model repository file list and code (`rl_common.py`, `rl_agent_api.py`, configs,
`eval/results.md`) on Hugging Face [P], its model card [V], and the receptron Node/ONNX wrapper
[P]. **Nothing was downloaded or run.** Each weight file is 0.64–0.84 GB, and downloading needs
approval.

**Architecture [P, from code].**
- ModernBERT-large encoder (395M parameters, bidirectional, fully fine-tuned) plus a head trained
  from scratch; 421M in total.
- Each option gets a `[MASK]` marker. A scorer (LayerNorm → Linear → GELU → Linear) turns each
  marker into a logit, and a softmax runs over that question's options.
- **A separate act head** (`n_act=2`: answer or escalate) reads the pooled sequence plus a summary
  of its own answer distribution. It was trained with `escalate` costing 0.5 and a wrong act
  costing 3.0. That is a learned abstention signal, returned as `act_probability`.
- Trained with RL against proper scoring rules (log + spherical + RPS), so honest probabilities
  are the reward optimum. Temperatures are fitted afterwards per question type and option count
  (`temperature_by_options`).

**Typed-decision interface [P].**
- The request shape is the closed API's: `system_one(state, {id: {type: choice|score|noul, instructions,
  criteria}})`.
- `choice` returns probabilities plus a confidence (1 − normalised entropy); `score` returns an
  expected level plus a distribution; `noul` returns P(true).
- All questions are scored in one batched forward pass. The state is truncated from the left to
  `max_len` (512 tokens; 1,024 for the typed-decisions and multilingual checkpoints).
- Options must fit a 192-token head budget (256 multilingual). Accuracy collapses past about 20
  options (Banking77: 0.425 vs the closed API 0.870 [V]).

This maps onto `decide()` directly: `choice`, `score` and `noul` are three of doc 4's kinds, and
`act_probability` fits the `abstain` / low-confidence path.

**Checkpoints [P].**

| Checkpoint | Encoder | Weight file | Context |
|---|---|---|---|
| `laya` | ModernBERT-large | 843 MB | 512 |
| `laya/typed-decisions` | ModernBERT-large | 843 MB | 1,024 |
| `laya/multilingual` | mmBERT-base, 322M | 644 MB | 1,024 |

The weight file sizes mean bf16 storage.

**Local inference requirements.**
- Python: PyTorch plus transformers [P].
- Node: `onnxruntime-node` via receptron/laya, MIT, 16 commits [P]. It downloads **fp32** ONNX
  weights (about 1.7 GB) and loads in "roughly 2 GB of RAM … plus a few hundred MB per batch" [P].
- No GGUF or llama.cpp path exists, so Laya would be the first ONNX runtime in noevia.

**CPU performance.**
- About 140 ms for 3 questions on Apple-silicon CPU, warm [P, wrapper README].
- 193–464 ms on CPU per the card [V].
- The System-1 benchmark ran it on a 4-thread Ryzen 5 3600: raw p50 0.79 s, with the benchmark's ×2 + 0.15 s
  adjustment [B].
- A cold checkpoint build takes about 7.4 s on CPU [V].
- Additional target hardware profiles remain untested [—].

**Accuracy and calibration.**

| Measure | Result | Source |
|---|---|---|
| Held-out task families (zero-shot) | 0.651 accuracy, ECE 0.204 | [V] |
| Agent-style typed-decisions workflows, zero-shot | **0.362** (random 0.318, majority class 0.461) | [V] |
| Same workflows after fine-tuning on their training split | 0.766 | [V] |
| Benchmark tiers: easy / standard / judge / **hard** | 94.4 / 72.9 / 69.2 / **34.1** | [B] |
| ECE before → after temperature refit | 0.466 → 0.081 | [V] |
| Coverage at 50%, in-task | 0.947 accuracy | [V] |
| Accuracy on non-Latin scripts | 0.000 at 0.952 confidence | [V] |

- The agent-style workflows are the closest public proxy for noevia's decisions, so the model card
  is right to call Laya "a fast base to specialise, not a zero-shot decision engine".
- Raw calibration is over-confident until the temperature refit.
- Its selective-prediction curve is its strength: 0.947 accuracy when it answers the half it is
  surest about.
- It is confidently wrong on non-Latin scripts, so language gating is required.

**Adaptation.**
- The published fine-tune took about 2 h on 2×T4 [P, config and notebook], so it is cheap.
- It needs labelled noevia decisions, which doc 9's corpus produces.
- Temperatures must be refitted on noevia's own data before any gating.

**Can it stay resident beside a large System Two?**
- On footprint, yes. It lives inside the web process (ONNX in Node), outside a separately configured llama.cpp process limit; both still consume host RAM.
- fp32 ONNX needs about 2 GB [P]. A bf16/fp16 or int8 export should need about 0.9 GB or
  0.5 GB [E, accuracy unverified].
- Fit must be measured alongside the selected System Two model, context size, and other services; file size alone does not establish safe residency.

**Maintenance and licence.**
- Weights Apache-2.0, wrapper MIT.
- About a week old, one vendor (Convai), and 0 recorded downloads on the Hub API today.
- Pin the exact revision.

## 13.3 Measuring residency on a target profile

CPU and integrated GPU may share system memory. Account for weights, KV cache,
working memory, other services, process/container limits, and concurrency together.
Record actual hardware, loaded models and measurements in local operator notes excluded
from Git. A result from one installation must not become a universal product limit.

## 13.4 Candidate comparison principles

- Compare deterministic heuristics, in-process classifiers, small CPU option-logit models,
  a dedicated decision model, and readout from an already loaded System Two.
- An in-process classifier avoids a separate inference slot but still consumes RAM.
- A dedicated model adds weights, KV cache, runtime overhead, and possible model swaps.
- Reusing System Two avoids duplicate weights but can queue decisions behind generation.
- Reranking and decision inference may compete for slots; measure that contention explicitly.
- Separate published weight estimates from measured peak resident memory. Quantized exports
  require accuracy validation; lower estimated memory does not establish equivalent quality.

## 13.5 Evaluation and qualification

Use identical synthetic or explicitly approved, deidentified inputs for every backend.
Keep training, calibration and held-out evaluation splits separate. Compare per-family
accuracy, selective accuracy, abstention, false PASS/FAIL rates, language coverage, cold
start, warm p50/p95 latency, swap-inclusive latency and peak memory.

Refit confidence temperatures before using a classifier to gate actions. Preserve hard
policy checks, bounded retries, timeouts and a deterministic refusal/fallback path.
Measure recovery after cancellation and model eviction. An inconclusive experiment is
not evidence of fitness for unattended use.

Run comparisons only in an explicitly approved resource window. Do not load models,
benchmark shared services, or change a running installation merely to refresh this note.
Publish generic methodology and software findings; keep hardware inventories, exact
installation budgets, runtime state, access details and operational receipts offline.
