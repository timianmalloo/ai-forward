"""PACK-O rung-2 control: the /dream miner that flags turns which recorded no goal-state
(done_when) and surfaces done_when->summary pairs for scope-drift review. Unit-level against
dream.build_proposals so the oracle is exact and deterministic (no rendered dream needed).

These were observed failing on the pre-fix dream.py (no section-5 detector existed), which is
the red-first evidence CI6 requires before a control is trusted."""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
DREAM = ROOT / "docs" / "ai-forward-pack" / "scripts" / "dream.py"


def _load_dream():
    spec = importlib.util.spec_from_file_location("dream_mod", DREAM)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackOMinerTests(unittest.TestCase):
    def setUp(self):
        self.dream = _load_dream()

    @staticmethod
    def _corpus(audit):
        return {"audit": audit, "change": [], "mitigations": [], "classes": [],
                "markers": [], "counts": {}}

    def _packo(self, audit):
        proposals, _ = self.dream.build_proposals(self._corpus(audit))
        return [p for p in proposals if str(p.get("sig", "")).startswith("PACK-O")]

    def test_flags_substantive_turns_missing_done_when(self):
        audit = [
            {"id": "al-1", "kind": "skill", "shortname": "a", "summary": "s"},            # no done_when
            {"id": "al-2", "kind": "manual", "shortname": "b", "summary": "s",
             "done_when": "the answer is stated"},                                        # has it
        ]
        packo = self._packo(audit)
        self.assertEqual(1, len(packo), "a PACK-O presence proposal must be produced")
        self.assertIn("1/2", packo[0]["title"], "1 of 2 substantive turns lacked done_when")
        self.assertEqual("v", packo[0]["confidence"], "presence is mechanical -> Verified")

    def test_clean_corpus_still_reports_the_pair_for_review(self):
        """When every substantive turn HAS a done_when, presence is satisfied (0 missing) but the
        goal->summary pairs are still surfaced for human scope-drift review."""
        audit = [{"id": "al-1", "kind": "skill", "shortname": "a", "summary": "s",
                  "done_when": "x"}]
        packo = self._packo(audit)
        self.assertEqual(1, len(packo))
        self.assertIn("0/1", packo[0]["title"])

    def test_no_substantive_turns_no_proposal(self):
        self.assertEqual([], self._packo([]))
        # a purely conversational corpus (no substantive kinds) also yields nothing
        self.assertEqual([], self._packo([{"id": "al-1", "kind": "session-import"}]))


if __name__ == "__main__":
    unittest.main()
