"""P6 — persona yield is recorded, so the roster is tuned on measurement not belief.

In the profiled session the two advisory personas (the Simplifier at 6 runs / 53.1 min and
the Patterns Expert at 4 runs / 33.2 min) consumed 57% of all agent time and produced
findings that changed nothing that shipped. The four hard-veto personas took 24% and drove
material change. Nobody could have known that in advance, and nobody could know it
afterwards either — because findings-accepted was never recorded against the persona that
raised them.

Convening cost is measured; convening VALUE was not. These tests pin the second half.
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "pack", "scripts", "audit-log.py")

spec = importlib.util.spec_from_file_location("audit_log_yield", SCRIPT)
audit_log = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_log)


class ParsePersonaYieldTests(unittest.TestCase):
    def test_parses_a_well_formed_record(self):
        got = audit_log.parse_persona_yield("the-simplifier|7|0")
        self.assertEqual(got, {"persona": "the-simplifier", "raised": 7, "accepted": 0})

    def test_accepted_may_not_exceed_raised(self):
        # A persona cannot have more findings accepted than it raised; silently keeping such
        # a row would corrupt every ratio computed from it.
        self.assertIsNone(audit_log.parse_persona_yield("x|2|5"))

    def test_non_numeric_or_malformed_degrades_to_none(self):
        self.assertIsNone(audit_log.parse_persona_yield("x|many|0"))
        self.assertIsNone(audit_log.parse_persona_yield("x|1"))
        self.assertIsNone(audit_log.parse_persona_yield("|1|0"))
        self.assertIsNone(audit_log.parse_persona_yield("x|-1|0"))


class AggregateYieldTests(unittest.TestCase):
    def entries(self):
        return [
            {"persona_yield": [{"persona": "the-simplifier", "raised": 4, "accepted": 0},
                               {"persona": "test-architect", "raised": 3, "accepted": 3}]},
            {"persona_yield": [{"persona": "the-simplifier", "raised": 3, "accepted": 0}]},
            {"summary": "an entry with no yield record at all"},
        ]

    def test_aggregates_across_entries(self):
        got = audit_log.aggregate_persona_yield(self.entries())
        self.assertEqual(got["the-simplifier"], {"raised": 7, "accepted": 0, "sessions": 2,
                                                 "acceptance": 0.0})
        self.assertEqual(got["test-architect"]["acceptance"], 1.0)

    def test_a_persona_with_no_raised_findings_has_no_ratio(self):
        # 0/0 is not 0% acceptance — it is no evidence. Reporting 0.0 would read as a
        # measured verdict on a persona that was never actually asked anything.
        got = audit_log.aggregate_persona_yield(
            [{"persona_yield": [{"persona": "quiet", "raised": 0, "accepted": 0}]}])
        self.assertIsNone(got["quiet"]["acceptance"])

    def test_empty_corpus_is_empty_not_an_error(self):
        self.assertEqual(audit_log.aggregate_persona_yield([]), {})


class ReconveneRuleTests(unittest.TestCase):
    """The rule the yield data exists to serve: an advisory persona re-convenes on evidence."""

    def test_advisory_persona_with_no_accepted_findings_should_not_re_convene(self):
        self.assertFalse(audit_log.should_reconvene(
            {"raised": 7, "accepted": 0}, advisory=True))

    def test_advisory_persona_that_landed_a_finding_may_re_convene(self):
        self.assertTrue(audit_log.should_reconvene(
            {"raised": 7, "accepted": 1}, advisory=True))

    def test_a_persona_never_yet_convened_always_gets_its_first_run(self):
        # The rule gates REPEAT convocations. Gating the first would make it unfalsifiable.
        self.assertTrue(audit_log.should_reconvene(None, advisory=True))
        self.assertTrue(audit_log.should_reconvene({"raised": 0, "accepted": 0}, advisory=True))

    def test_hard_veto_personas_are_never_yield_gated(self):
        # A veto lens exists to be able to say no. Gating it on past productivity would
        # silence exactly the review that has been quiet because the work was clean.
        self.assertTrue(audit_log.should_reconvene(
            {"raised": 9, "accepted": 0}, advisory=False))


if __name__ == "__main__":
    unittest.main()
