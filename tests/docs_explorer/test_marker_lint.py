"""Tier-1 (prose-to-structure-review). `marker-lint.py` enforces field-completeness on the
inline `simplify:` (L5) and `assume:` (NG4) markers using backward-compatible semantic-cue
detection: a simplify: needs a trigger; an assume: needs a confirm route AND a breaks-if
consequence. It warns on legacy free-form by default (exit 0) and fails only under --gate (V16a).

Seen failing on the pre-fix tree: the script does not exist, so the run errors.
"""
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "docs" / "ai-forward-pack" / "scripts" / "marker-lint.py"


class MarkerLintTests(unittest.TestCase):
    def _write(self, tmp, name, text):
        p = tmp / name
        p.write_text(text, encoding="utf-8")
        return p

    def _run(self, tmp, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(tmp), *args],
            capture_output=True, text=True,
        )

    def setUp(self):
        import tempfile
        self._td = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._td.name)

    def tearDown(self):
        self._td.cleanup()

    # ---- complete markers pass (the canonical NG4/L5 examples) ----
    def test_complete_simplify_marker_is_ok(self):
        self._write(self.tmp, "a.py",
                    "x = 1\n# simplify: O(n2) match, fine for n<1k batches - index it when batch size grows\n")
        r = self._run(self.tmp, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["findings"], [])
        self.assertEqual(data["markers"], 1)

    def test_complete_multiline_assume_marker_is_ok(self):
        self._write(self.tmp, "b.py",
                    "# assume: the provider returns ISO-8601 in UTC. Seen in one sample payload, NOT stated in\n"
                    "#         the spec. If it is local time, every daily rollup silently shifts by the offset.\n"
                    "#         Confirm: request one record and inspect the raw timestamp field.\n"
                    "y = 2\n")
        r = self._run(self.tmp, "--json")
        data = json.loads(r.stdout)
        self.assertEqual(data["findings"], [], "multi-line assume block should assemble and pass")

    # ---- the rot cases are flagged ----
    def test_simplify_without_trigger_is_flagged(self):
        self._write(self.tmp, "c.py", "# simplify: just hardcode this for now\n")
        r = self._run(self.tmp, "--json")
        data = json.loads(r.stdout)
        codes = [f["code"] for f in data["findings"]]
        self.assertIn("simplify-no-trigger", codes)

    def test_assume_without_confirm_is_flagged(self):
        # has a consequence (if/breaks) but no confirm route
        self._write(self.tmp, "d.py", "# assume: the id is unique. If not, rows collide and the merge breaks.\n")
        r = self._run(self.tmp, "--json")
        codes = [f["code"] for f in json.loads(r.stdout)["findings"]]
        self.assertIn("assume-no-confirm", codes)
        self.assertNotIn("assume-no-consequence", codes)

    def test_assume_without_consequence_is_flagged(self):
        # has a confirm route but no stated consequence
        self._write(self.tmp, "e.py", "# assume: the id is unique. Verify by querying the index.\n")
        r = self._run(self.tmp, "--json")
        codes = [f["code"] for f in json.loads(r.stdout)["findings"]]
        self.assertIn("assume-no-consequence", codes)
        self.assertNotIn("assume-no-confirm", codes)

    # ---- word boundaries: 'if' inside 'verify' must not count as a consequence cue ----
    def test_confirm_word_does_not_satisfy_consequence(self):
        self._write(self.tmp, "f.py", "# assume: rates are per-second. Verify against the vendor docs.\n")
        r = self._run(self.tmp, "--json")
        codes = [f["code"] for f in json.loads(r.stdout)["findings"]]
        self.assertIn("assume-no-consequence", codes)

    # ---- continuation stops at the next non-comment line ----
    def test_continuation_stops_at_code(self):
        self._write(self.tmp, "g.py",
                    "# simplify: naive scan\n"
                    "do_work()  # when load grows, index it\n")  # trigger is on a CODE line, not the block
        r = self._run(self.tmp, "--json")
        codes = [f["code"] for f in json.loads(r.stdout)["findings"]]
        self.assertIn("simplify-no-trigger", codes, "code line after the marker is not part of the block")

    # ---- exit posture: warn by default, fail under --gate ----
    def test_default_warn_exit_zero_even_with_findings(self):
        self._write(self.tmp, "h.py", "# simplify: hardcoded\n")
        r = self._run(self.tmp)
        self.assertEqual(r.returncode, 0, "default is warn (grandfathers legacy)")

    def test_gate_exits_nonzero_on_findings(self):
        self._write(self.tmp, "i.py", "# simplify: hardcoded\n")
        r = self._run(self.tmp, "--gate")
        self.assertNotEqual(r.returncode, 0, "--gate fails on a finding")

    def test_gate_exits_zero_when_clean(self):
        self._write(self.tmp, "j.py", "# simplify: naive scan - index it when n grows\n")
        r = self._run(self.tmp, "--gate")
        self.assertEqual(r.returncode, 0)

    # ---- empty corpus is distinguishable from a clean one (E14) ----
    def test_empty_corpus_reports_zero(self):
        self._write(self.tmp, "k.py", "print('no markers here')\n")
        r = self._run(self.tmp, "--json")
        self.assertEqual(json.loads(r.stdout)["markers"], 0)

    # ---- FR-077: a marker is a comment, not a string that looks like one ----
    def test_marker_inside_string_literal_is_not_a_marker(self):
        self._write(self.tmp, "fixture.py",
                    'bad = "# simplify: hardcoded\\n"\n'
                    'also = "x = 1\\n# assume: no fields at all"\n'
                    "js = '// simplify: hardcoded'\n")
        r = self._run(self.tmp, "--json")
        data = json.loads(r.stdout)
        self.assertEqual(data["markers"], 0, data)

    def test_trailing_comment_marker_still_counts(self):
        # \x23 is the comment leader, escaped: written literally after a space inside this
        # string it is the residual LINT-A names, and this file would fail the repository scan.
        self._write(self.tmp, "t.py", "x = 1  \x23 simplify: hardcoded\n")
        r = self._run(self.tmp, "--json")
        codes = [f["code"] for f in json.loads(r.stdout)["findings"]]
        self.assertEqual(codes, ["simplify-no-trigger"])

    def test_one_bad_pack_marker_beside_test_fixtures_is_exactly_one_finding(self):
        (self.tmp / "pack").mkdir()
        (self.tmp / "tests").mkdir()
        self._write(self.tmp, "pack/tool.py", "# simplify: hardcoded\nx = 1\n")
        self._write(self.tmp, "tests/test_tool.py",
                    'self._write(tmp, "a.py", "# simplify: hardcoded\\n")\n'
                    '    "# assume: the id is unique.\\n"\n')
        r = self._run(self.tmp, "--json", "--gate")
        data = json.loads(r.stdout)
        self.assertEqual([f["src"] for f in data["findings"]], ["pack/tool.py#L1"], data)
        self.assertNotEqual(r.returncode, 0)

    # ---- .md is excluded by default (directive examples are not scanned) ----
    def test_md_excluded_by_default(self):
        self._write(self.tmp, "doc.md", "# simplify: a bad example with no trigger\n")
        r = self._run(self.tmp, "--json")
        self.assertEqual(json.loads(r.stdout)["markers"], 0, ".md not scanned unless --include-md")


class DreamMarkerHarvestTests(unittest.TestCase):
    """FR-077 sweep: dream.py harvests markers with the same grammar, so a test fixture's string
    literal entered the dream corpus as an owner marker. One grammar, two readers, one rule."""

    def test_harvest_skips_string_literals_and_keeps_comments(self):
        import importlib.util
        import tempfile
        spec = importlib.util.spec_from_file_location(
            "dream_mod", ROOT / "docs" / "ai-forward-pack" / "scripts" / "dream.py")
        dream = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dream)
        with tempfile.TemporaryDirectory() as td:
            (pathlib.Path(td) / "a.py").write_text(
                'fixture = "# simplify: hardcoded\\n"\n'
                "# simplify: naive scan - index it when n grows\n", encoding="utf-8")
            srcs = [m["src"] for m in dream.grep_markers(td)]
        self.assertEqual(srcs, ["a.py#L2"])


if __name__ == "__main__":
    unittest.main()
