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


if __name__ == "__main__":
    unittest.main()
