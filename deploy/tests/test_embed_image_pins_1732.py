"""#1732: every llama.cpp image the embedding overlays default to is the live b11610 digest.

EmbeddingGemma 2 (#1636) needs llama.cpp #30054, and #30255/#30445 keep its memory small. b11580
(the old `embed-next` default) lacks #30255. `embed`, `embed-next` and the live-override example
must name one digest, the one `embed` and `llama` run on DaServer since 2026-10-14.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMBED_OVERLAY = ROOT / 'compose.embed.yaml'
LIVE_EXAMPLE = ROOT / 'deploy/examples/unraid-llamacpp.override.yml'
LIVE = 'ghcr.io/ggml-org/llama.cpp:server-vulkan-b11610@sha256:d64043576ad8fb29170563c769a997dbc1b9928f0d4a127fb9e4a9706ccb475b'


def service_block(text: str, name: str) -> str:
    match = re.search(rf'^  {re.escape(name)}:\n(.*?)(?=^  [a-z][a-z0-9-]*:\n|\Z)', text, re.M | re.S)
    if not match:
        raise AssertionError(f'service {name} not found')
    return match.group(1)


def default_image(block: str) -> str:
    line = re.search(r'^    image: (\S+)', block, re.M)
    if not line:
        raise AssertionError('no image line')
    value = line.group(1)
    env = re.fullmatch(r'\$\{[A-Z_]+:-(.+)\}', value)
    return env.group(1) if env else value


def code_lines(text: str) -> str:
    """The text without comments, so history notes may still name old builds."""
    return '\n'.join(line.split(' #')[0] for line in text.splitlines() if not line.lstrip().startswith('#'))


class EmbedImagePins(unittest.TestCase):
    def test_overlay_embed_and_embed_next_use_the_live_digest(self):
        text = EMBED_OVERLAY.read_text()
        self.assertEqual(default_image(service_block(text, 'embed')), LIVE)
        self.assertEqual(default_image(service_block(text, 'embed-next')), LIVE, 'embed-next must not default to a build without #30255')

    def test_live_example_embed_uses_the_live_digest(self):
        text = LIVE_EXAMPLE.read_text()
        self.assertEqual(default_image(service_block(text, 'embed')), LIVE)
        self.assertEqual(default_image(service_block(text, 'llama')), LIVE)

    def test_no_older_llama_cpp_digest_outside_comments(self):
        for path in (EMBED_OVERLAY, LIVE_EXAMPLE):
            code = code_lines(path.read_text())
            for digest in re.findall(r'llama\.cpp:[\w.-]+@sha256:[0-9a-f]{64}', code):
                self.assertEqual('ghcr.io/ggml-org/' + digest, LIVE, f'{path.name}: {digest}')

    def test_overlay_comments_do_not_claim_a_single_digest(self):
        self.assertNotIn('the only pinned llama.cpp digest', EMBED_OVERLAY.read_text())
        self.assertNotIn('the only llama.cpp digest this repo', EMBED_OVERLAY.read_text())


if __name__ == '__main__':
    unittest.main()
