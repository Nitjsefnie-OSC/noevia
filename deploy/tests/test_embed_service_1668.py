"""#1668: the embedding service is settings-driven in every compose copy the repo keeps.

The embed container must be a llama.cpp router reading the model manager's preset, never a fixed
`--model` path (which made the model impossible to switch or delete from the UI, and crash-looped
the container when the file was deleted, #336). It stays CPU-only and separate from the chat engine,
and the model manager is told which one container it may restart or stop.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMBED_OVERLAY = ROOT / 'compose.embed.yaml'
LIVE_EXAMPLE = ROOT / 'deploy/examples/unraid-llamacpp.override.yml'


def service_block(text: str, name: str) -> str:
    """The text of one top-level service (two-space indented key) up to the next one."""
    match = re.search(rf'^  {re.escape(name)}:\n(.*?)(?=^  [a-z][a-z0-9-]*:\n|\Z)', text, re.M | re.S)
    if not match:
        raise AssertionError(f'service {name} not found')
    return match.group(1)


def command_args(block: str) -> list:
    inline = re.search(r'^    command: \[(.*)\]$', block, re.M)
    if inline:
        return re.findall(r'"([^"]*)"', inline.group(1))
    listed = re.search(r'^    command:\n((?:      - .*\n|      #.*\n)+)', block, re.M)
    if not listed:
        raise AssertionError('no command')
    return re.findall(r'^      - "([^"]*)"', listed.group(1), re.M)


class EmbedServiceIsSettingsDriven(unittest.TestCase):
    def check_embed(self, text: str) -> None:
        embed = service_block(text, 'embed')
        args = command_args(embed)
        self.assertIn('--models-preset', args)
        self.assertEqual(args[args.index('--models-preset') + 1], '/config/embedding.ini')
        self.assertEqual(args[args.index('--models-max') + 1], '2', 'active + next during a switch')
        self.assertEqual(args[args.index('--device') + 1], 'none', 'CPU only: never competes with the chat engine')
        for fixed in ('-m', '--model', '--alias'):
            self.assertNotIn(fixed, args, f'{fixed} pins the model in compose again')
        self.assertRegex(embed, r'LLAMACPP_CONFIG_DIR[^\n]*:/config:ro', 'the preset is read-only here')
        self.assertRegex(embed, r'model-loader:\n\s+condition: service_healthy', 'the preset exists before the router starts')

    def check_model_loader(self, text: str) -> None:
        loader = service_block(text, 'model-loader')
        for key in ('EMBED_CONTAINER', 'EMBED_URL', 'EMBED_PRESET_PATH', 'EMBEDDING_MODEL', 'EMBED_MODEL_FILE'):
            self.assertRegex(loader, rf'\n\s+{key}:', key)
        self.assertIn('EMBED_PRESET_PATH: /config/embedding.ini', loader)
        # Seeds only: nothing defaults the seed to the "default" placeholder.
        self.assertNotRegex(loader, r'EMBEDDING_MODEL: \$\{EMBEDDING_MODEL:-default\}')

    def test_overlay(self):
        text = EMBED_OVERLAY.read_text()
        self.check_embed(text)
        self.check_model_loader(text)
        self.assertRegex(service_block(text, 'web'), r'EMBEDDING_SERVICE_URL: http://embed:8080/v1')

    def test_live_override_example(self):
        text = LIVE_EXAMPLE.read_text()
        self.check_embed(text)
        self.check_model_loader(text)
        self.assertRegex(service_block(text, 'web'), r'EMBEDDING_SERVICE_URL: http://embed:8080/v1')

    def test_chat_engine_stays_single_model_and_separate(self):
        llama = service_block(LIVE_EXAMPLE.read_text(), 'llama')
        args = command_args(llama)
        self.assertEqual(args[args.index('--models-preset') + 1], '/config/models.ini', 'the chat engine never reads embedding.ini')
        self.assertEqual(args[args.index('--models-max') + 1], '1')


if __name__ == '__main__':
    unittest.main()
