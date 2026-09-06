"""P8 — per-run wall-clock spans, so parallelism is MEASURED rather than asserted.

The profile that motivated this recorded 67 sub-agent runs totalling 152.6 minutes and
claimed that was "more than the elapsed time, because adversarial reviews ran in parallel."
It was not: 152.6 minutes of agent time sat inside roughly 240 minutes of wall clock, so
the published numbers were consistent with fully serial execution. The claim was
unfalsifiable because only per-run DURATIONS were recorded — never start and end stamps.

Summed duration cannot distinguish serial from parallel. The union of the intervals can.
These tests pin that: speedup is sum/span, and a set of runs that never overlap must
report a speedup of 1.0 no matter how many runs there are.
"""
import importlib.util
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "pack", "scripts", "audit-log.py")

spec = importlib.util.spec_from_file_location("audit_log_spans", SCRIPT)
audit_log = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_log)


def run(agent, start, end):
    return audit_log.parse_agent_run(f"{agent}|{start}|{end}")


class ParseAgentRunTests(unittest.TestCase):
    def test_parses_a_well_formed_span(self):
        got = run("the-simplifier", "2026-09-03T10:00:00Z", "2026-09-03T10:08:00Z")
        self.assertEqual(got["agent"], "the-simplifier")
        self.assertEqual(got["duration_seconds"], 480.0)

    def test_unparseable_stamp_degrades_to_none_not_a_wrong_span(self):
        # IO8: a measurement path degrades to "not recorded", never to a plausible wrong number.
        self.assertIsNone(run("x", "not-a-date", "2026-09-03T10:08:00Z"))
        self.assertIsNone(audit_log.parse_agent_run("missing-fields"))

    def test_end_before_start_is_refused(self):
        self.assertIsNone(run("x", "2026-09-03T10:08:00Z", "2026-09-03T10:00:00Z"))


class ParallelismTests(unittest.TestCase):
    def test_serial_runs_report_no_speedup(self):
        runs = [run("a", "2026-09-03T10:00:00Z", "2026-09-03T10:10:00Z"),
                run("b", "2026-09-03T10:10:00Z", "2026-09-03T10:20:00Z"),
                run("c", "2026-09-03T10:20:00Z", "2026-09-03T10:30:00Z")]
        got = audit_log.parallelism_fields(runs)
        self.assertEqual(got["agent_seconds"], 1800.0)
        self.assertEqual(got["span_seconds"], 1800.0)
        self.assertEqual(got["speedup"], 1.0)
        self.assertEqual(got["peak_concurrency"], 1)

    def test_fully_overlapping_runs_report_real_speedup(self):
        runs = [run("a", "2026-09-03T10:00:00Z", "2026-09-03T10:10:00Z"),
                run("b", "2026-09-03T10:00:00Z", "2026-09-03T10:10:00Z"),
                run("c", "2026-09-03T10:00:00Z", "2026-09-03T10:10:00Z")]
        got = audit_log.parallelism_fields(runs)
        self.assertEqual(got["agent_seconds"], 1800.0)
        self.assertEqual(got["span_seconds"], 600.0)
        self.assertEqual(got["speedup"], 3.0)
        self.assertEqual(got["peak_concurrency"], 3)

    def test_gap_between_waves_is_not_counted_as_occupied(self):
        # The union must exclude idle time, or a long quiet gap would inflate the span and
        # silently understate the parallelism that did happen.
        runs = [run("a", "2026-09-03T10:00:00Z", "2026-09-03T10:10:00Z"),
                run("b", "2026-09-03T11:00:00Z", "2026-09-03T11:10:00Z")]
        got = audit_log.parallelism_fields(runs)
        self.assertEqual(got["span_seconds"], 1200.0)
        self.assertEqual(got["speedup"], 1.0)

    def test_partial_overlap(self):
        runs = [run("a", "2026-09-03T10:00:00Z", "2026-09-03T10:10:00Z"),
                run("b", "2026-09-03T10:05:00Z", "2026-09-03T10:15:00Z")]
        got = audit_log.parallelism_fields(runs)
        self.assertEqual(got["agent_seconds"], 1200.0)
        self.assertEqual(got["span_seconds"], 900.0)
        self.assertEqual(got["peak_concurrency"], 2)

    def test_no_usable_runs_records_nothing(self):
        self.assertEqual(audit_log.parallelism_fields([]), {})
        self.assertEqual(audit_log.parallelism_fields([None]), {})

    def test_the_profiled_session_shape_is_shown_as_unproven(self):
        """152.6 min of agent time inside ~240 min of wall clock: serial fits."""
        runs = [run("r%d" % i,
                    "2026-09-03T%02d:00:00Z" % (10 + i),
                    "2026-09-03T%02d:30:00Z" % (10 + i)) for i in range(3)]
        got = audit_log.parallelism_fields(runs)
        self.assertEqual(got["speedup"], 1.0,
                         "non-overlapping runs must never report a speedup above 1.0")


class BudgetOnTheSpanTests(unittest.TestCase):
    """P6 / class CTX-F: GO7 says record each branch's calls AGAINST ITS BUDGET, and the
    record could not express a budget.

    The doctrine half was already in place: GO7 carries the per-branch-budget and
    convergence-condition rows, and all 23 persona cards say "the budget firing is a finding
    for the parent, not a reason to continue". The span was `<agent>|<start>|<end>` -- three
    fields, no budget, no actuals -- so nothing could check any of it. That is PACK-A: a
    directive wired as prose, with no mechanism at the point it applies, and CI6's memoir.

    The measured shape it exists for: a domain-researcher ran 123 tool calls and 3.0M tokens
    on a proposal iteration and stopped only when the parent said "converge now" twice
    (SP-07). The parent knew - its prompts were full of BOUNDED and ONLY - and the prose was
    not holding.

    Deliberately a RECORD, not an enforcement: no harness mediates a sub-agent's tool count,
    and a control that cannot actually stop the call must not be labelled as though it can.
    """

    def test_the_three_field_form_still_parses(self):
        """Every existing caller and every logged entry uses it. Breaking them is not a fix."""
        run = audit_log.parse_agent_run("researcher|2026-09-06T10:00:00Z|2026-09-06T10:10:00Z")
        self.assertIsNotNone(run)
        self.assertEqual(run["agent"], "researcher")
        self.assertNotIn("budget_calls", run)

    def test_a_fourth_field_records_calls_against_budget(self):
        run = audit_run("researcher", "10:00:00", "10:10:00", "123/12")
        self.assertEqual(run["calls"], 123)
        self.assertEqual(run["budget_calls"], 12)
        self.assertTrue(run["over_budget"])

    def test_a_run_inside_its_budget_is_not_flagged(self):
        run = audit_run("tester", "10:00:00", "10:05:00", "8/12")
        self.assertEqual(run["calls"], 8)
        self.assertFalse(run["over_budget"])

    def test_exactly_at_the_budget_is_not_over(self):
        """The budget is a ceiling reached, not a ceiling crossed - GO9's circuit breaker
        fires AT the cap, and reaching it is the branch doing what it was told."""
        self.assertFalse(audit_run("t", "10:00:00", "10:01:00", "12/12")["over_budget"])

    def test_a_malformed_budget_leaves_the_span_usable_and_records_nothing(self):
        """IO8. The interval is still good evidence; a fabricated budget would not be.
        Dropping the whole span would lose the parallelism measurement over a typo."""
        run = audit_run("t", "10:00:00", "10:01:00", "twelve")
        self.assertIsNotNone(run)
        self.assertEqual(run["duration_seconds"], 60.0)
        self.assertNotIn("budget_calls", run)
        self.assertNotIn("over_budget", run)

    def test_a_zero_or_negative_budget_is_refused_not_treated_as_unlimited(self):
        for spec in ("5/0", "5/-1"):
            with self.subTest(spec=spec):
                run = audit_run("t", "10:00:00", "10:01:00", spec)
                self.assertNotIn("budget_calls", run,
                                 "a budget of zero is a typo, and treating it as unlimited "
                                 "is the success-shaped reading")

    def test_the_time_fields_are_unaffected_by_the_budget(self):
        run = audit_run("t", "10:00:00", "10:10:00", "3/9")
        self.assertEqual(run["duration_seconds"], 600.0)


class SelfcheckReadsTheBudgetTests(unittest.TestCase):
    """A field nothing reads is a field nobody fills in."""

    def _entry(self, runs, **kw):
        e = {"kind": "skill", "shortname": "s", "session": "sess", "done_when": "d",
             "tier": "T1", "agent_runs": runs}
        e.update(kw)
        return e

    def test_a_run_with_no_budget_is_reported_as_a_gap(self):
        out = audit_log.budget_findings([self._entry([{"agent": "a", "duration_seconds": 1.0}])])
        self.assertEqual(len(out["no_budget"]), 1)
        self.assertEqual(out["no_budget"][0]["agent"], "a")

    def test_a_run_over_its_budget_is_reported_as_a_finding(self):
        out = audit_log.budget_findings([self._entry(
            [{"agent": "researcher", "calls": 123, "budget_calls": 12, "over_budget": True}])])
        self.assertEqual(len(out["over_budget"]), 1)
        self.assertEqual(out["over_budget"][0]["calls"], 123)
        self.assertEqual(out["no_budget"], [])

    def test_a_run_inside_its_budget_is_reported_as_neither(self):
        out = audit_log.budget_findings([self._entry(
            [{"agent": "a", "calls": 4, "budget_calls": 12, "over_budget": False}])])
        self.assertEqual(out["over_budget"], [])
        self.assertEqual(out["no_budget"], [])

    def test_an_entry_with_no_runs_contributes_nothing(self):
        """A turn that delegated nothing has no budget to miss."""
        out = audit_log.budget_findings([self._entry([]), {"kind": "skill"}])
        self.assertEqual(out["over_budget"], [])
        self.assertEqual(out["no_budget"], [])

    def test_selfcheck_surfaces_both(self):
        src = io.open(SCRIPT, encoding="utf-8").read()
        body = src.split("def cmd_selfcheck", 1)[1].split(chr(10) + "def ", 1)[0]
        self.assertIn("budget_findings", body,
                      "selfcheck is where a turn's own record is read back; a finding it "
                      "does not surface is one nobody sees without a profiling pass")


def audit_run(agent, start, end, budget):
    return audit_log.parse_agent_run("{0}|2026-09-06T{1}Z|2026-09-06T{2}Z|{3}".format(
        agent, start, end, budget))


class MainLineBudgetTests(unittest.TestCase):
    """F-14 / class CTX-M: the budget the pack did not have, on the 91%.

    Measured in sp-0003: the main line ran 714 requests for 89,429 AIU while its delegates ran
    701 for 8,491 - near-identical counts, TEN TIMES the cost per request, 91% of the session
    on the main line. Bare user-initiated requests alone cost 12,853 AIU, more than the whole
    delegate fleet. Every budget the pack has - GO7's fan-out contract, the tier cap, the
    per-branch tool-call budget - bounds delegates. Nothing bounded the main agent's own loop,
    because delegation is visible and a main line is just one more reasonable step, repeated.

    THE HONEST LIMIT, and why this is shaped the way it is: a branch can count its own tool
    calls, but the main agent CANNOT count its own model requests - only the harness store
    knows those. So the DECLARATION is the agent's (tool calls it made against the budget it
    committed to in the goal state) and the TRUTH is the profiler's (SP-19, read from the
    store). The two are reconciled, never conflated, and neither is called enforcement.
    """

    def _entry(self, **kw):
        e = {"kind": "skill", "shortname": "s", "session": "sess", "done_when": "d", "tier": "T1"}
        e.update(kw)
        return e

    def test_a_substantive_turn_with_no_main_budget_is_a_gap(self):
        out = audit_log.main_line_findings([self._entry()])
        self.assertEqual(len(out["no_budget"]), 1)

    def test_a_turn_over_its_main_budget_is_a_finding(self):
        out = audit_log.main_line_findings(
            [self._entry(main_calls=81, main_budget=20, main_over_budget=True)])
        self.assertEqual(len(out["over_budget"]), 1)
        self.assertEqual(out["over_budget"][0]["calls"], 81)
        self.assertEqual(out["no_budget"], [])

    def test_a_turn_inside_its_main_budget_is_neither(self):
        out = audit_log.main_line_findings(
            [self._entry(main_calls=6, main_budget=20, main_over_budget=False)])
        self.assertEqual(out["over_budget"], [])
        self.assertEqual(out["no_budget"], [])

    def test_a_non_substantive_entry_is_not_asked_for_a_budget(self):
        """A commit or a script run has no ceremony budget to declare."""
        out = audit_log.main_line_findings([{"kind": "commit", "shortname": "c"}])
        self.assertEqual(out["no_budget"], [])

    def test_the_parser_matches_the_branch_form(self):
        """One spelling for both budgets. Two would be a second thing to remember."""
        self.assertEqual(audit_log._parse_budget("81/20"), (81, 20))
        self.assertEqual(audit_log._parse_budget("6/20"), (6, 20))

    def test_selfcheck_surfaces_the_main_line(self):
        src = io.open(SCRIPT, encoding="utf-8").read()
        body = src.split("def cmd_selfcheck", 1)[1].split(chr(10) + "def ", 1)[0]
        self.assertIn("main_line_findings", body,
                      "the 91% has to surface where the 9% already does, or the asymmetry "
                      "that CTX-M is about survives the fix")

    def test_the_cli_accepts_it(self):
        src = io.open(SCRIPT, encoding="utf-8").read()
        self.assertIn("--main-budget", src)

    def test_ct19_names_the_field(self):
        """A field the standard does not ask for is a field nobody fills in."""
        ct19 = io.open(os.path.join(ROOT, "pack", "knowledge",
                                    "communication-and-task-discipline.md"),
                       encoding="utf-8").read()
        self.assertIn("Main-line budget", ct19,
                      "CT19's goal-state block is where a turn declares its budgets; the "
                      "main line is 91% of the cost and was not among them")


if __name__ == "__main__":
    unittest.main()
