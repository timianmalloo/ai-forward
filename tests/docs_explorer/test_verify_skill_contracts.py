"""verify-skill-contracts.py rules 5-7 and the P8 skill sweep (spec-skill-evolution US-1..US-9).

Rule 5 `compile missing`: every skill cites CO-S0 in SKILL.md. Rule 6 `pointer without
reference`: a SKILL.md that names reference/co-s0.md has a reference text carrying CO-S0.
Rule 7 `dispatch without deadline`: a dispatcher (or a fan-out cap above zero) names a deadline
and a fallback. Tree-level: the ten skills cite CO-S0, the six pointer skills carry the fixed
sentence exactly once across SKILL.md and reference/, the seam (b) owner-review sentences are
byte-present in the two coordination skills, prepare-for-coordination's track row names the five
fields. Observed red on base 9ea0e00 before the lint and the skills were edited.
"""
import importlib.util
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMMANDS = ROOT / "pack" / "commands"
LINT = ROOT / "pack" / "scripts" / "verify-skill-contracts.py"

SENTENCE = ("Consume the compiled prompt when one is in hand (CO-S0, `knowledge/agent-coordination.md`; "
            "`/compile`): its goal state is the turn's goal state and its Not-in-scope is the interdiction "
            "— derive nothing from raw prose that a compiled prompt already fixed.")
POINTER = "CO-S0 applies first — the sentence is `reference/co-s0.md`."

SWEEP_TEN = ["addpacktorepo", "also", "apply-learnings", "auditlog", "dream", "extendaibundle",
             "prompts", "searchprompts", "session-profiler", "updatepack"]
NEW_POINTER_SKILLS = ["apply-learnings", "dream", "session-profiler", "addpacktorepo", "updatepack", "extendaibundle"]
UTILITY_TOUCHPOINT = ["also", "auditlog", "prompts", "searchprompts"]

# seam-p5-to-coordinator.md (b), verbatim
EWC_STAGE5 = ("**Owner review is a ruling, never an acceptance (D6, CO1).** When a track raises a decision request "
              "(`coord decide request` — the five fields, a deadline and a fallback, P1's request plus a "
              "`decision-request` mail), the Owner seat answers it with `coord decide rule next --title \"…\" "
              "--text \"…\" --request <req-id>`: the next numbered heading is appended to `docs/notes/rulings.md`, "
              "the request is resolved with `Ruling NN`, and the requester is mailed. The requester never rules on "
              "its own request (`COORD-RULING-SELF`). A track's `Stop` is refused by `owner-review-gate.py` while a "
              "decision request it sent is open — that refusal is the loop's signal, not an error to work around; "
              "`coord decide list` shows what is open and what was ruled (`NOT CHECKED` over an empty corpus).")
EWC_STAGE6 = ("Before the join, `python3 docs/ai-forward-pack/scripts/verify-ruling-citations.py` is green: a "
              "`Ruling NN` cited anywhere under `docs/`, `pack/`, `.agents/log/`, `.github/`, `.claude/` with no "
              "heading in `docs/notes/rulings.md`, or a number defined twice, blocks the join (class ID-A).")
PFC_STAGE7 = ("Every track row names **who rules**: the Owner session a track's `coord decide request --to "
              "<owner-session>` addresses, and the register it rules into (`docs/notes/rulings.md`, class "
              "`register`). A plan whose tracks can raise a decision request but name no Owner session has no "
              "termination variant for that request (D5, D6).")


def _lint():
    spec = importlib.util.spec_from_file_location("verify_skill_contracts", LINT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _skill(name):
    return (COMMANDS / name / "SKILL.md").read_text(encoding="utf-8")


def _refs(name):
    ref = COMMANDS / name / "reference"
    return [p.read_text(encoding="utf-8") for p in sorted(ref.glob("*.md"))] if ref.is_dir() else []


def _body(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return text[m.end():] if m else text


SEAT = "---\nname: a\nruns_as: either\n---\n"


class LintRuleTests(unittest.TestCase):
    def setUp(self):
        self.check = _lint().check_skill

    def _codes(self, text, refs=()):
        return [line.split(":")[0] for line in self.check("a", text, list(refs))]

    def test_compile_missing_fires_on_a_seat_ful_skill_without_co_s0(self):
        self.assertIn("compile missing", self._codes(SEAT + "## Grounding\nplain.\n"))

    def test_compile_missing_is_silent_when_co_s0_is_cited_inline_or_by_pointer(self):
        self.assertNotIn("compile missing", self._codes(SEAT + "## Grounding\nCO-S0 first.\n"))
        self.assertNotIn("compile missing", self._codes(SEAT + "## Grounding\n" + POINTER + "\n", [SENTENCE]))

    def test_pointer_without_reference_fires_when_the_pointer_dangles(self):
        self.assertIn("pointer without reference", self._codes(SEAT + "## Grounding\n" + POINTER + "\n"))
        self.assertIn("pointer without reference", self._codes(SEAT + "## Grounding\n" + POINTER + "\n", ["unrelated stage detail"]))

    def test_pointer_with_reference_passes(self):
        self.assertEqual([], self._codes(SEAT + "## Grounding\n" + POINTER + "\n", [SENTENCE]))

    def test_dispatch_without_deadline_fires_on_a_dispatcher_naming_neither_word(self):
        text = "---\nname: a\nruns_as: Coordinator\n---\n## Stage 0\nCO-S0.\n## Stage 3 — Dispatch\nspawn under the five-part contract with a termination condition.\n"
        self.assertIn("dispatch without deadline", self._codes(text))

    def test_dispatch_without_deadline_fires_on_a_fan_out_naming_only_one_word(self):
        text = SEAT + "## Flow\nCO-S0; fan-out cap 2; five-part contract with a termination condition and a deadline.\n"
        self.assertIn("dispatch without deadline", self._codes(text))

    def test_dispatcher_naming_both_words_passes(self):
        text = "---\nname: a\nruns_as: Coordinator\n---\n## Stage 0\nCO-S0.\n## Stage 3 — Dispatch\nspawn under the five-part contract with a termination condition, a deadline and a fallback.\n"
        self.assertEqual([], self._codes(text))

    def test_non_dispatcher_is_not_asked_for_a_deadline(self):
        self.assertEqual([], self._codes(SEAT + "## Flow\nCO-S0. fan-out cap 0. plain.\n"))

    def test_self_test_exits_zero_and_names_eleven_directions(self):
        r = subprocess.run([sys.executable, str(LINT), "--self-test"], capture_output=True, text=True)
        self.assertEqual(0, r.returncode, r.stdout + r.stderr)
        self.assertIn("11 refusal directions fail", r.stdout)


class TreeTests(unittest.TestCase):
    def test_the_tree_is_clean(self):
        r = subprocess.run([sys.executable, str(LINT), "--root", str(ROOT)], capture_output=True, text=True)
        self.assertEqual(0, r.returncode, r.stdout)
        self.assertIn("clean - 28 skill(s)", r.stdout)

    def test_every_skill_cites_co_s0(self):
        for d in sorted(p for p in COMMANDS.iterdir() if p.is_dir()):
            self.assertIn("CO-S0", _body(_skill(d.name)), d.name)

    def test_the_ten_sweep_skills_cite_co_s0(self):
        missing = [n for n in SWEEP_TEN if "CO-S0" not in _body(_skill(n))]
        self.assertEqual([], missing)

    def test_new_pointer_skills_carry_the_fixed_sentence_once_and_the_pointer(self):
        for name in NEW_POINTER_SKILLS:
            body = _body(_skill(name))
            union = body + "\n" + "\n".join(_refs(name))
            self.assertEqual(1, union.count(SENTENCE), name + ": the fixed sentence exactly once across SKILL.md and reference/")
            self.assertIn(POINTER, body, name)
            self.assertTrue((COMMANDS / name / "reference" / "co-s0.md").is_file(), name)

    def test_utility_skills_cite_co_s0_without_the_fixed_sentence(self):
        for name in UTILITY_TOUCHPOINT:
            body = _body(_skill(name))
            self.assertIn("CO-S0", body, name)
            self.assertNotIn(SENTENCE, body, name + ": a utility skill names its own touch-point, not the consumer sentence")

    def test_seam_b_sentences_are_byte_present_at_their_stages(self):
        ewc = _skill("execute-with-coordination")
        self.assertIn(EWC_STAGE5, ewc)
        self.assertIn(EWC_STAGE6, ewc)
        self.assertLess(ewc.find("**Stage 5"), ewc.find(EWC_STAGE5))
        self.assertLess(ewc.find(EWC_STAGE5), ewc.find("**Stage 6"))
        self.assertLess(ewc.find("conductor-join.py <branch>"), ewc.find(EWC_STAGE6))
        self.assertLess(ewc.find(EWC_STAGE6), ewc.find("**Never remove a worktree"))
        join_ref = (COMMANDS / "execute-with-coordination" / "reference" / "join.md").read_text(encoding="utf-8")
        self.assertIn("It fences first", join_ref)
        self.assertIn("`reference/join.md`", ewc)
        pfc = _skill("prepare-for-coordination")
        self.assertIn(PFC_STAGE7, pfc)
        self.assertLess(pfc.find("decision request unanswered: DR-n"), pfc.find(PFC_STAGE7))
        self.assertLess(pfc.find(PFC_STAGE7), pfc.find("**Stage 8"))

    def test_prepare_for_coordination_track_row_names_the_five_fields(self):
        stage7 = _skill("prepare-for-coordination").split("**Stage 7")[1].split("**Stage 8")[0]
        for field in ("deadline", "fallback", "termination condition", "target harness", "doorbell status"):
            self.assertIn(field, stage7, field)

    def test_optimize_graph_fan_out_contract_names_deadline_and_fallback(self):
        text = _skill("optimize-graph")
        i = text.find("five-part contract")
        self.assertGreater(i, 0)
        window = text[i:i + 900]
        self.assertIn("deadline", window)
        self.assertIn("fallback", window)

    def test_no_machine_path_in_new_files(self):
        needle = "/" + "Users" + "/"
        for p in (LINT, pathlib.Path(__file__), ROOT / "docs" / "specs" / "skill-evolution.md",
                  ROOT / "docs" / "design" / "skill-evolution.md"):
            self.assertNotIn(needle, p.read_text(encoding="utf-8"), str(p))


if __name__ == "__main__":
    unittest.main()
