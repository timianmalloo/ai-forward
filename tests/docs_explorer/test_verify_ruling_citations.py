"""verify-ruling-citations.py - a cited ruling number must be defined exactly once, by a heading in
docs/notes/rulings.md (spec-owner-review US-8; absorbed from ai-de's gate, re-homed).

Written red-first against a fixture with an undefined and a twice-defined number; the last test
runs the gate against this repository (the committed register defines Ruling 1).
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "pack" / "scripts" / "verify-ruling-citations.py"

FRONT = "---\nid: rulings\ntype: doc\n---\n\n# Rulings\n\n"


class Tree(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rulings-")).resolve()
        self.addCleanup(shutil.rmtree, str(self.tmp), True)

    def write(self, rel, body):
        path = self.tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8", newline="\n")

    def run_gate(self, *args):
        return subprocess.run([sys.executable, str(GATE), *args], capture_output=True, text=True,
                              encoding="utf-8", check=False)

    def check(self):
        return self.run_gate("--root", str(self.tmp))


class Gate(Tree):
    def test_undefined_citation_fails(self):
        self.write("docs/plans/p.md", "Per Ruling 7 we did this.\n")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Ruling 7", result.stdout)
        self.assertIn("docs/plans/p.md", result.stdout)
        self.assertIn("no heading", result.stdout)

    def test_twice_defined_fails(self):
        self.write("docs/notes/rulings.md", FRONT + "### Ruling 3 — one\n\na\n\n## Ruling 3 — again\n\nb\n")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Ruling 3", result.stdout)
        self.assertIn("defined twice", result.stdout)

    def test_clean_tree_exit_0(self):
        self.write("docs/notes/rulings.md", FRONT + "### Ruling 1 — create the register\n\nyes\n")
        self.write("pack/knowledge/x.md", "As Ruling 1 says.\n")
        self.write("docs/x.html", "<p>Per Rulings 1 and later.</p>\n")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 ruling(s) cited", result.stdout)
        self.assertIn("1 defined", result.stdout)

    def test_prose_only_definition_is_a_citation(self):
        self.write("docs/notes/rulings.md", FRONT + "Ruling 9 decided the thing, at length.\n")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Ruling 9", result.stdout)

    def test_definition_outside_the_register_does_not_count(self):
        self.write("docs/notes/other-note.md", "### Ruling 4 — elsewhere\n\nx\n")
        self.write("docs/notes/rulings.md", FRONT)
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Ruling 4", result.stdout)

    def test_four_level_heading_does_not_define(self):
        self.write("docs/notes/rulings.md", FRONT + "#### Ruling 2 — too deep\n\nx\n")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Ruling 2", result.stdout)

    def test_records_are_quotes_not_citations(self):
        self.write("docs/audit/audit-log.jsonl", '{"prompt": "ai-de said Ruling 38 forbids it"}\n')
        self.write("docs/dreams/d.json", '{"text": "Rulings 128"}\n')
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0 ruling(s) cited", result.stdout)

    def test_scans_the_five_roots_and_skips_the_deployed_copy(self):
        for rel in ("docs/a.md", "pack/b.md", ".agents/log/c.md", ".github/d.md", ".claude/e.md"):
            self.write(rel, "See Ruling 11.\n")
        self.write("docs/ai-forward-pack/knowledge/f.md", "See Ruling 12.\n")
        self.write("tests/g.md", "See Ruling 13.\n")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for rel in ("docs/a.md", "pack/b.md", ".agents/log/c.md", ".github/d.md", ".claude/e.md"):
            self.assertIn(rel, result.stdout)
        self.assertNotIn("Ruling 12", result.stdout)
        self.assertNotIn("Ruling 13", result.stdout)

    def test_self_test_passes(self):
        result = self.run_gate("--self-test")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("self-test", result.stdout)

    def test_usage_exit_2(self):
        result = self.run_gate("--root", str(self.tmp / "missing"))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_this_repository_is_clean(self):
        result = self.run_gate("--root", str(REPO))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("defined", result.stdout)


if __name__ == "__main__":
    unittest.main()
