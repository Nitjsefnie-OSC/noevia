"""CHAT_MODEL_IDLE_UNLOAD_SECONDS reaches the model-loader container, blank by default, in each compose copy.

#1747: the model manager keeps llama.cpp's `sleep-idle-seconds` in the chat preset's `[*]` section so
an idle chat model unloads itself. Blank means the manager's 900-second default; 0 disables it. Only
key names and the default expression are read here; no .env value is ever read.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.llamacpp.yaml', 'deploy/examples/unraid-llamacpp.override.yml']
KEY = 'CHAT_MODEL_IDLE_UNLOAD_SECONDS'
EXPECTED = 'CHAT_MODEL_IDLE_UNLOAD_SECONDS: ${CHAT_MODEL_IDLE_UNLOAD_SECONDS:-}'


def service_environment(text, service):
    """The `environment:` lines of one service (two-space service keys, six-space env keys)."""
    lines = text.split('\n')
    start = lines.index(f'  {service}:')
    body, in_env = [], False
    for line in lines[start + 1:]:
        if re.match(r'^ {2}\S', line):
            break
        if re.match(r'^ {4}environment:\s*$', line):
            in_env = True
            continue
        if in_env and re.match(r'^ {4}\S', line):
            break
        if in_env:
            body.append(line)
    return body


def problems_for(text):
    found = []
    lines = [l.strip() for l in service_environment(text, 'model-loader') if re.match(rf'^ {{6}}{KEY}:', l)]
    if len(lines) != 1:
        found.append(f'expected exactly one {KEY} line in model-loader, found {len(lines)}')
    elif lines[0] != EXPECTED:
        found.append(f'{KEY} default is not blank: {lines[0]}')
    return found


class ChatIdleUnloadPassthroughTests(unittest.TestCase):
    def test_each_compose_copy_passes_the_setting_with_a_blank_default(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8')), [])

    def test_a_missing_line_is_reported(self):
        text = '  model-loader:\n    environment:\n      TZ: UTC\n  web:\n'
        self.assertEqual(len(problems_for(text)), 1)

    def test_a_hard_coded_default_is_reported(self):
        text = '  model-loader:\n    environment:\n      CHAT_MODEL_IDLE_UNLOAD_SECONDS: ${CHAT_MODEL_IDLE_UNLOAD_SECONDS:-0}\n  web:\n'
        self.assertIn('not blank', problems_for(text)[0])

    def test_only_model_loader_gets_the_setting(self):
        # The embedding router, Laya and the engine never see it (#1717 keeps embeddings warm).
        for name in COMPOSE_COPIES:
            text = (ROOT / name).read_text(encoding='utf-8')
            services = [l[2:-1] for l in text.split('\n') if re.match(r'^ {2}[a-z][\w-]*:$', l)]
            for service in services:
                if service == 'model-loader':
                    continue
                with self.subTest(copy=name, service=service):
                    self.assertEqual([l for l in service_environment(text, service) if KEY in l], [])

    def test_env_example_documents_the_key_commented_out(self):
        text = (ROOT / '.env.example').read_text(encoding='utf-8')
        self.assertIn(f'# {KEY}=\n', text)
        self.assertNotRegex(text, rf'(?m)^{KEY}=')


if __name__ == '__main__':
    unittest.main()
