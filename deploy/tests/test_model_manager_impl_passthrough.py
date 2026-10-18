"""Retired model-manager selectors cannot reach any container (#1318/#1071).

The production image is mandatory native and contains no Python fallback. Keep the
literal inventory so a stale key added to either Compose copy fails qualification.
Only configuration key names are read; no owner .env contents are accessed.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_COPIES = ['compose.llamacpp.yaml', 'deploy/examples/unraid-llamacpp.override.yml']
RETIRED = ('MODEL_MANAGER_IMPL', 'MODEL_FILES_IMPL', 'MODEL_MANAGER_BACKENDS_IMPL', 'MODEL_MANAGER_BACKEND_CONTROL_IMPL', 'MODEL_MANAGER_BADGES_IMPL', 'MODEL_MANAGER_BENCHMARK_OBSERVE_IMPL', 'MODEL_MANAGER_BENCHMARK_OVERVIEW_IMPL', 'MODEL_MANAGER_BENCHMARK_RUNNER_IMPL', 'MODEL_MANAGER_BENCH_RUNS_IMPL', 'MODEL_MANAGER_CHECK_UPDATES_IMPL', 'MODEL_MANAGER_DB_INIT_IMPL', 'MODEL_MANAGER_DIAGNOSE_IMPL', 'MODEL_MANAGER_DOWNLOADS_IMPL', 'MODEL_MANAGER_DOWNLOAD_PLAN_IMPL', 'MODEL_MANAGER_DOWNLOAD_TARGETS_IMPL', 'MODEL_MANAGER_DRAFT_HEADS_IMPL', 'MODEL_MANAGER_HOST_IMPL', 'MODEL_MANAGER_MODELS_IMPL', 'MODEL_MANAGER_MODEL_DELETE_IMPL', 'MODEL_MANAGER_MODEL_DETAIL_IMPL', 'MODEL_MANAGER_MODEL_UPDATES_IMPL', 'MODEL_MANAGER_OVERVIEW_IMPL', 'MODEL_MANAGER_PROMPTS_IMPL', 'MODEL_MANAGER_ROUTING_IMPL', 'MODEL_MANAGER_SAFE_DEFAULTS_IMPL', 'MODEL_MANAGER_SEARCH_IMPL', 'MODEL_MANAGER_SECTIONS_IMPL', 'MODEL_MANAGER_SECTION_AUTOCONFIG_IMPL', 'MODEL_MANAGER_SECTION_WRITES_IMPL', 'MODEL_MANAGER_SETTINGS_IMPL', 'MODEL_MANAGER_SETTINGS_WRITE_IMPL', 'MODEL_MANAGER_TELEMETRY_IMPL', 'MODEL_MANAGER_TOKEN_TEST_IMPL')


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


def env_keys(text):
    """Every six-space `KEY:` (map form) or `- KEY=` (list form) environment key, in any service."""
    keys = []
    for line in text.split('\n'):
        m = re.match(r'^ {6}(?:- )?([A-Z][A-Z0-9_]*)\s*[:=]', line)
        if m:
            keys.append(m.group(1))
    return keys


def problems_for(text):
    return [f'{key} is retired (#1071) but still passed' for key in env_keys(text) if key in RETIRED]


class RetiredModelLoaderSwitchTests(unittest.TestCase):
    def test_no_compose_copy_passes_a_retired_switch(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                text = (ROOT / name).read_text(encoding='utf-8')
                self.assertEqual(problems_for(text), [])
                self.assertIn('SEARCH_TRUSTED_PATH: /config/search-trusted.json',
                              [line.strip() for line in service_environment(text, 'model-loader')])

    def test_every_retired_key_is_refused_in_map_and_list_form(self):
        for key in RETIRED:
            for service in ('model-loader', 'web'):
                for line in (f'      {key}: ${{{key}:-python}}', f'      - {key}=rust'):
                    text = f'  {service}:\n    environment:\n{line}\n'
                    with self.subTest(key=key, service=service, line=line):
                        self.assertEqual(problems_for(text), [f'{key} is retired (#1071) but still passed'])

    def test_other_runtime_configuration_is_preserved(self):
        text = '  model-loader:\n    environment:\n      MODEL_LOADER_TOKEN: required\n      TZ: UTC\n      SEARCH_TRUSTED_PATH: /config/search-trusted.json\n'
        self.assertEqual(problems_for(text), [])

    def test_example_env_has_no_retired_configuration(self):
        text = (ROOT / '.env.example').read_text(encoding='utf-8')
        for key in RETIRED:
            with self.subTest(key=key):
                self.assertNotIn(key, text)


if __name__ == '__main__':
    unittest.main()
