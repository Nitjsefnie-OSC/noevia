#!/usr/bin/env python3
"""Reference vectors for tools/embed-parity-check.cjs --reference (#1636).

Embeds the parity check's synthetic sample (no user data) with the ORIGINAL checkpoint through
sentence-transformers, so a GGUF build served by llama.cpp can be compared against it:

  node tools/embed-parity-check.cjs --print-sample --profile=embeddinggemma-2 > sample.json
  python3 tools/embed-reference-vectors.py google/embeddinggemma-2 sample.json reference.json

The sample texts already carry the profile's prompts (``task: search result | query: ...`` and
``title: none | text: ...``), so they are encoded verbatim: no ``prompt_name`` is added on top.
Vectors are L2-normalised float32, as llama-server's /v1/embeddings returns them.

This downloads the checkpoint (about 1.5 GB for google/embeddinggemma-2) and runs the model, so it
needs the owner's per-run approval like any model run. It is never run by CI or by noevia itself.
Needs: pip install "sentence-transformers>=6.1" torch. Runs in float32 (the model card: never float16).
"""
from __future__ import annotations

import json
import sys


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__.strip().splitlines()[0])
        print("usage: embed-reference-vectors.py <model id or path> <sample.json> <reference.json> ", file=sys.stderr)
        return 2
    model_id, sample_path, out_path = argv[1:]
    with open(sample_path, encoding="utf-8") as fh:
        sample = json.load(fh)
    texts = sample["texts"]
    if len(texts) != sample["docs"] + sample["queries"]:
        print("sample.json: texts must be docs + queries", file=sys.stderr)
        return 2

    import torch  # noqa: WPS433 — optional dependency, imported only when run
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_id, device="cpu", model_kwargs={"torch_dtype": torch.float32},
                                config_kwargs={"vision_config": None, "audio_config": None})
    vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, batch_size=8)
    revision = getattr(getattr(model, "model_card_data", None), "base_model_revision", None)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({
            "source": {"model": model_id, "revision": revision, "library": "sentence-transformers", "dtype": "float32"},
            "profile": sample.get("profile"),
            "docs": sample["docs"], "queries": sample["queries"],
            "texts": texts, "vectors": [[float(x) for x in v] for v in vectors],
        }, fh)
    print(f"{len(texts)} reference vectors of {len(vectors[0])} dimensions written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
