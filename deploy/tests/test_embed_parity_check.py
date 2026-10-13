"""#1636: tools/embed-parity-check.cjs frames the sample per profile and compares a server against
reference vectors. A fake embeddings server stands in for llama-server; no model is run."""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "embed-parity-check.cjs"
NODE = shutil.which("node")


def vector(text: str, flip: bool = False) -> list:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    v = [b / 255.0 + 0.01 for b in digest[:16]]
    n = math.sqrt(sum(x * x for x in v))
    v = [x / n for x in v]
    return list(reversed(v)) if flip else v


class Fake:
    def __init__(self, flip: bool = False):
        self.inputs: list = []
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                fake.inputs.extend(body["input"])
                data = [{"index": i, "embedding": vector(t, flip)} for i, t in enumerate(body["input"])]
                raw = json.dumps({"data": data}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *a):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/v1"

    def close(self):
        self.server.shutdown()


def run(*args):
    return subprocess.run([NODE, str(TOOL), *args], capture_output=True, text=True, timeout=60)


@unittest.skipUnless(NODE, "node is not installed")
class EmbedParityCheckTest(unittest.TestCase):
    def sample(self, profile):
        r = run("--print-sample", f"--profile={profile}")
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_default_profile_sends_the_sample_unchanged(self):
        s = self.sample("nomic-v1")
        self.assertEqual((s["docs"], s["queries"]), (40, 10))
        self.assertTrue(all(not t.startswith(("task:", "title:")) for t in s["texts"]))
        self.assertEqual(s["texts"][0], "Went for a long walk by the river this morning; the fog lifted around nine.")

    def test_embeddinggemma_profile_uses_the_card_prompts(self):
        s = self.sample("embeddinggemma-2")
        self.assertTrue(all(t.startswith("title: none | text: ") for t in s["texts"][:40]))
        self.assertTrue(all(t.startswith("task: search result | query: ") for t in s["texts"][40:]))
        self.assertEqual(run("--print-sample", "--profile=nomic-v9").returncode, 2)

    def test_two_servers_compare_on_the_framed_sample(self):
        a, b = Fake(), Fake()
        try:
            r = run("--profile=embeddinggemma-2", a.url, "embeddinggemma-2", b.url, "embeddinggemma-2")
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout)
            self.assertEqual(out["similarity"], 1)
            self.assertEqual(out["profile"], "embeddinggemma-2")
            self.assertIn("top1", out["scores"]["a"])
            self.assertTrue(a.inputs[0].startswith("title: none | text: "))
            self.assertTrue(a.inputs[-1].startswith("task: search result | query: "))
        finally:
            a.close(); b.close()

    def test_reference_mode_passes_on_matching_vectors_and_fails_on_a_different_model(self):
        s = self.sample("embeddinggemma-2")
        with tempfile.TemporaryDirectory() as tmp:
            ref = Path(tmp) / "reference.json"
            ref.write_text(json.dumps({"source": {"model": "synthetic"}, "profile": s["profile"], "docs": s["docs"], "queries": s["queries"],
                                       "texts": s["texts"], "vectors": [vector(t) for t in s["texts"]]}))
            same, other = Fake(), Fake(flip=True)
            try:
                r = run(f"--reference={ref}", same.url, "embeddinggemma-2")
                self.assertEqual(r.returncode, 0, r.stderr)
                out = json.loads(r.stdout)
                self.assertEqual((out["mode"], out["dimensions"]), ("reference", [16, 16]))
                self.assertEqual(same.inputs, s["texts"], "the reference texts are sent verbatim")
                self.assertEqual(run(f"--reference={ref}", other.url, "x").returncode, 1)
                truncated = json.loads(run(f"--reference={ref}", "--dims=8", same.url, "embeddinggemma-2").stdout)
                self.assertEqual(truncated["dimensions"], [8, 8])
                self.assertAlmostEqual(truncated["similarity"], 1, places=6)
                self.assertEqual(run(f"--reference={Path(tmp) / 'missing.json'}", same.url, "m").returncode, 2)
            finally:
                same.close(); other.close()


if __name__ == "__main__":
    unittest.main()
