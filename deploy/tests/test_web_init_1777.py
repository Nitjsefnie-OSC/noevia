"""#1777: the web service runs under Docker's init (tini) in both compose copies."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
FILES = ["compose.yaml", "deploy/examples/unraid-compose-manager.yml"]


def service_block(text, name):
    match = re.search(rf"(?m)^  {name}:\n((?:(?:    .*|\s*)\n)+)", text)
    assert match, name
    return match.group(1)


class WebInitTests(unittest.TestCase):
    def test_web_has_init_true(self):
        for rel in FILES:
            with self.subTest(file=rel):
                block = service_block((ROOT / rel).read_text(), "web")
                self.assertRegex(block, r"(?m)^    init: true\s*$")

    def test_supervisor_forwards_signals(self):
        script = ROOT / "build/web-supervisor.sh"
        if not script.exists():
            self.skipTest("supervisor lives in the assembled tree")
        self.assertRegex(script.read_text(), r"trap .*(TERM|INT)")


if __name__ == "__main__":
    unittest.main()
