# Qualifying model settings

Qualify settings for an exact model artifact, runtime, hardware class, and workload. A preset
that loads is not proof that the claimed prompt length, vision path, or concurrency is usable.
Keep installed-model inventories, device identities, live presets, and operator telemetry locally
outside version control. Historical operational records are not transferable qualification.

Record model revision/checksum and quantization, engine build, context and output budgets,
batching/concurrency, cache type, GPU layers/device selection, memory limits, prompt template,
tool harness, workload version, quality checks, latency, and peak memory. Shared-memory iGPU
allocations and host RAM must be counted together; configured budgets are not measured capacity.

Compare matched configurations before tuning each candidate independently. Begin with bounded
synthetic prompts, measure prompt processing and generation separately, and test retrieval,
dates, corrections, tool arguments, abstention, and permission boundaries. A correct marker recall
test alone does not establish general reasoning quality. Keep failed trials and unknowns visible.

Production calibration, model loading, downloads, and changing live presets require explicit
scope and an approved maintenance window. Preserve the previous qualified configuration and
verify restoration after interruption. Never use real Diary content as a benchmark fixture.

See [model guidance](spec-model-guidance.md), [the roadmap](roadmap.md), and
[System-One research](research/system-one/README.md) for product-level evaluation requirements.
