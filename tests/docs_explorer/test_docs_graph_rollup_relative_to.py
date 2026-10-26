"""`docs-graph.py rollup --relative-to <dir>` writes source links that resolve from the destination document.

A rollup printed links relative to the documentation root, so a rollup pasted into a nested document
(docs/security/...) linked to docs/security/design/x.md, which does not exist. The default stays relative
to the root; --relative-to names the directory of the document the rollup lands in. Upstreamed from
CFD-Workbench.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
GRAPH = REPO / "pack" / "scripts" / "docs-graph.py"


class RollupRelativeToTests(unittest.TestCase):
    def test_default_and_nested_destinations_resolve_to_the_real_source(self):
        with tempfile.TemporaryDirectory(prefix="rollup-links-") as directory:
            docs = Path(directory) / "docs"
            source = docs / "design" / "fixture.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                "---\nid: design-fixture\ntitle: Fixture\ntype: design\n"
                'status: proposed\nowner: "@test"\nreview-by: 2099-01-01\n'
                "summary: Test fixture.\n---\n\n## Risks\n\n"
                "| Boundary | Risk |\n|---|---|\n| File | Tamper |\n",
                encoding="utf-8", newline="\n")
            nested = docs / "security"
            nested.mkdir()
            for destination, options, expected in (
                    (docs, [], "design/fixture.md"),
                    (nested, ["--relative-to", str(nested)], "../design/fixture.md")):
                with self.subTest(destination=destination.name):
                    result = subprocess.run(
                        [sys.executable, str(GRAPH), "--root", str(docs), "rollup",
                         "--heading", "Risks", "--type", "design", *options],
                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertIn("[design-fixture]({0})".format(expected), result.stdout)
                    self.assertTrue((destination / expected).is_file())
                    self.assertEqual(source.resolve(), (destination / expected).resolve())


if __name__ == "__main__":
    unittest.main()
