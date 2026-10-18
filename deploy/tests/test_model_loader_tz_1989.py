"""model-loader sets TZ=UTC in each repo compose copy (#1989).

The mandatory native model manager refuses to start unless TZ is exactly UTC
(noevia-rs bins/noevia-model-manager). An unset TZ is not accepted even when /etc/localtime is UTC, so the
service environment must carry it. Only key names and the literal value are read here; no .env value is read.
"""
import re
import unittest

from test_model_manager_impl_passthrough import COMPOSE_COPIES, ROOT, service_environment


def problems_for(text):
    lines = [l.strip() for l in service_environment(text, 'model-loader') if re.match(r'^\s*TZ\s*[:=]', l)]
    if len(lines) != 1:
        return [f'expected exactly one TZ line in model-loader, found {len(lines)}']
    if lines[0] != 'TZ: UTC':
        return [f'model-loader TZ is not exactly UTC: {lines[0]}']
    return []


class ModelLoaderTzTests(unittest.TestCase):
    def test_each_compose_copy_sets_tz_utc_on_model_loader(self):
        for name in COMPOSE_COPIES:
            with self.subTest(copy=name):
                self.assertEqual(problems_for((ROOT / name).read_text(encoding='utf-8')), [])

    def test_a_missing_tz_is_reported(self):
        text = '  model-loader:\n    environment:\n      DATA_DIR: /data\n  web:\n'
        self.assertEqual(len(problems_for(text)), 1)

    def test_a_non_utc_tz_is_reported(self):
        for value in ('Etc/UTC', 'Europe/London', ''):
            text = f'  model-loader:\n    environment:\n      TZ: {value}\n  web:\n'
            with self.subTest(value=value):
                self.assertIn('not exactly UTC', problems_for(text)[0])

    def test_tz_on_another_service_does_not_count(self):
        text = '  model-loader:\n    environment:\n      DATA_DIR: /data\n  web:\n    environment:\n      TZ: UTC\n'
        self.assertEqual(len(problems_for(text)), 1)


if __name__ == '__main__':
    unittest.main()
