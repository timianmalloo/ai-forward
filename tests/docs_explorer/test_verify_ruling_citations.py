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

    def test_r_n_register_defines_and_r_n_citations_resolve(self):
        # A register written as `## R-n · date · seat · title` (measured in x-harness-x-model-bench,
        # 2026-09-24): the gate read no heading and no citation there, so it passed while checking nothing.
        self.write("docs/notes/rulings.md", FRONT + "## R-7 · 2026-09-24 · Owner seat · task sources\n\nx\n\n"
                   "### R-4 — sub-agents fall back\n\ny\n")
        self.write("docs/plans/p.md", "Per R-7, and ruling R-4, we did this. See also (R-7).\n")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("2 ruling(s) cited", result.stdout)
        self.assertIn("2 defined", result.stdout)

    def test_dangling_r_n_citation_fails(self):
        self.write("docs/notes/rulings.md", FRONT + "## R-1 · 2026-09-24 · Owner · seats\n\nx\n")
        self.write("docs/plans/p.md", "As R-99 requires.\n")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("R-99", result.stdout)
        self.assertIn("docs/plans/p.md", result.stdout)
        self.assertIn("no heading", result.stdout)

    def test_r_n_defined_twice_fails(self):
        self.write("docs/notes/rulings.md", FRONT + "## R-3 · one\n\na\n\n### R-3 · again\n\nb\n")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("defined twice", result.stdout)

    def test_both_spellings_name_one_number(self):
        self.write("docs/notes/rulings.md", FRONT + "## R-5 · 2026-09-24 · Owner · N5\n\nx\n")
        self.write("docs/plans/p.md", "Ruling 5 and R-5 are the same decision.\n")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 ruling(s) cited", result.stdout)
        self.write("docs/notes/rulings.md", FRONT + "## R-5 · one\n\nx\n\n### Ruling 5 — two\n\ny\n")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("defined twice", result.stdout)

    def test_r_n_heading_rules_match_the_ruling_form(self):
        # a spike id heading is not a definition, and a four-level heading never defines
        self.write("docs/notes/rulings.md", FRONT + "## R-2.3 — spike\n\nx\n\n#### R-6 — too deep\n\ny\n")
        self.write("docs/plans/p.md", "Per R-2 and R-6.\n")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("R-2 ", result.stdout)
        self.assertIn("R-6 ", result.stdout)

    def test_register_headings_in_no_recognised_form_are_not_checked(self):
        # PACK-P: the R-n miss passed because 0 definitions over a register full of headings read as clean.
        # The next unrecognised numbering must fail loudly, not repeat that.
        self.write("docs/notes/rulings.md", FRONT + "## RUL-1 · 2026-09-24 · Owner · x\n\ny\n\n### RUL-2 · z\n\nw\n")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("NOT CHECKED", result.stdout)
        self.assertIn("2 heading(s)", result.stdout)

    def test_a_register_with_only_its_title_is_empty_not_unreadable(self):
        self.write("docs/notes/rulings.md", FRONT)
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_look_alike_ids_are_not_citations(self):
        self.write("docs/plans/p.md", "Spike R-2.3 and R-10.1, story US-13, HB-PRE-002, DR-1, PR-12, HR-4,"
                   " XR-9, lower r-5, R-12a, R-3-4, AR-R-7x and SR-1 are not rulings.\n")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0 ruling(s) cited", result.stdout)

    def test_this_repository_is_clean(self):
        result = self.run_gate("--root", str(REPO))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("defined", result.stdout)


if __name__ == "__main__":
    unittest.main()
