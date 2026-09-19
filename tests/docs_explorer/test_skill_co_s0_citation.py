"""Every prose-input skill cites CO-S0 in the one fixed sentence, exactly once; every owned skill
declares its seat; the four hard stops cite CO-S2; optimize-graph carries the dispatchable stop
(spec-compile-readers US-4, US-5, US-7, US-8). The sentence may live inline in SKILL.md or in the
skill's reference/co-s0.md with a one-line pointer (the budget route) - exactly once across the
skill either way, and SKILL.md cites `CO-S0` in both routes. Observed red on base 2b3a815.
"""
import os
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMMANDS = ROOT / "pack" / "commands"

SENTENCE = ("Consume the compiled prompt when one is in hand (CO-S0, `knowledge/agent-coordination.md`; "
            "`/compile`): its goal state is the turn's goal state and its Not-in-scope is the interdiction "
            "— derive nothing from raw prose that a compiled prompt already fixed.")
DISPATCHABLE_STOP = ("Before dispatch, refuse a compiled prompt whose `dispatchable` is false or whose text still "
                     "carries an unanswered `DR-n` line — stop with `decision request unanswered: DR-n` (CO-S0).")

PROSE_INPUT = ["specify", "define-architecture", "design-slice", "implement", "investigate", "ui-design",
               "collectknowledge", "forensicreview", "migrate", "document", "code-hygiene", "adopt",
               "visualize", "adddomainexperts"]
ALREADY_CARRYING = ["optimize-graph", "prepare-for-coordination"]
HARD_STOP = ["investigate", "forensicreview", "code-hygiene", "apply-learnings"]
P2_OWNED = {"execute-with-coordination", "prepare-for-coordination"}
SEATS = {"Coordinator", "Sub-Agent", "either"}


def _skill_text(name):
    return (COMMANDS / name / "SKILL.md").read_text(encoding="utf-8")


def _union_text(name):
    text = _skill_text(name)
    ref = COMMANDS / name / "reference"
    if ref.is_dir():
        for p in sorted(ref.glob("*.md")):
            text += "\n" + p.read_text(encoding="utf-8")
    return text


def _frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""


class CoS0CitationTests(unittest.TestCase):
    def test_every_prose_input_skill_carries_the_sentence_exactly_once(self):
        for name in PROSE_INPUT:
            self.assertEqual(1, _union_text(name).count(SENTENCE), name)

    def test_pointer_route_skill_cites_co_s0_in_skill_md(self):
        for name in PROSE_INPUT:
            text = _skill_text(name)
            if SENTENCE in text:
                self.assertEqual(1, text.count("CO-S0"), name + ": the inline sentence is the one citation")
            else:
                self.assertTrue((COMMANDS / name / "reference" / "co-s0.md").is_file(), name)
                self.assertEqual(1, text.count("CO-S0"), name + ": the pointer is the one citation")
                self.assertIn("reference/co-s0.md", text, name)

    def test_optimize_graph_and_prepare_carry_it_once_not_twice(self):
        for name in ALREADY_CARRYING:
            self.assertEqual(1, _union_text(name).count(SENTENCE), name)

    def test_optimize_graph_carries_the_dispatchable_stop_once(self):
        self.assertEqual(1, _skill_text("optimize-graph").count(DISPATCHABLE_STOP))

    def test_every_owned_skill_declares_runs_as_from_the_closed_set(self):
        for d in sorted(p for p in COMMANDS.iterdir() if p.is_dir()):
            if d.name in P2_OWNED:
                continue
            fm = _frontmatter(_skill_text(d.name))
            m = re.search(r"^runs_as: (\S+)$", fm, re.M)
            self.assertIsNotNone(m, d.name + ": runs_as missing from frontmatter")
            self.assertIn(m.group(1), SEATS, d.name)
        self.assertEqual("Coordinator", re.search(r"^runs_as: (\S+)$", _frontmatter(_skill_text("optimize-graph")), re.M).group(1))
        for name in PROSE_INPUT:
            self.assertEqual("either", re.search(r"^runs_as: (\S+)$", _frontmatter(_skill_text(name)), re.M).group(1), name)

    def test_hard_stop_skills_cite_co_s2(self):
        for name in HARD_STOP:
            self.assertIn("CO-S2", _union_text(name), name)

    def test_no_machine_path_in_new_files(self):
        new = [ROOT / "pack" / "scripts" / "verify-skill-contracts.py",
               ROOT / "tests" / "docs_explorer" / "test_readers_compile_fields.py",
               pathlib.Path(__file__),
               ROOT / "docs" / "specs" / "compile-readers.md", ROOT / "docs" / "design" / "compile-readers.md"]
        needle = "/" + "Users" + "/"  # built, so this file does not carry the literal it forbids
        for p in new:
            self.assertNotIn(needle, p.read_text(encoding="utf-8"), str(p))


if __name__ == "__main__":
    unittest.main()
