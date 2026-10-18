"""CI-speed P9: tools/ci-duration-budget.py judges this run against the trailing median, offline.

`gh` is replaced by a fake Actions API, so every verdict is exercised without the network: within
budget, over budget, too little history (never fails), and a job that did not succeed (reported
as not recorded, never as a duration).
"""
import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "ci-duration-budget.py"


def load():
    spec = importlib.util.spec_from_file_location("ci_duration_budget", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def job(name, secs, conclusion="success"):
    return {"name": name, "conclusion": conclusion, "started_at": "2026-10-18T00:00:00Z",
            "completed_at": "2026-10-18T00:{:02d}:{:02d}Z".format(int(secs) // 60, int(secs) % 60)}


class DurationBudgetTests(unittest.TestCase):
    def run_budget(self, now, past, min_history=3):
        module = load()
        runs = {"1": now, **{str(i + 10): jobs for i, jobs in enumerate(past)}}

        def fake_gh(path):
            if "/workflows/" in path:
                return {"workflow_runs": [{"id": int(k)} for k in runs if k != "1"]}
            run_id = path.split("/runs/")[1].split("/")[0]
            return {"jobs": runs[run_id]}

        module.gh = fake_gh
        out = io.StringIO()
        with redirect_stdout(out):
            code = module.main(["--repo", "o/r", "--run", "1", "--workflow", "w.yml", "--jobs", "a,b",
                                "--since", "2026-10-18", "--min-history", str(min_history)])
        return code, out.getvalue()

    def test_within_budget_passes_and_reports_the_ratio(self):
        code, out = self.run_budget([job("a", 110), job("b", 100)], [[job("a", 100), job("b", 100)]] * 3)
        self.assertEqual(0, code, out)
        self.assertIn("1.10x", out)

    def test_growth_over_the_threshold_fails_naming_the_job(self):
        code, out = self.run_budget([job("a", 160), job("b", 100)], [[job("a", 100), job("b", 100)]] * 3)
        self.assertEqual(1, code, out)
        self.assertIn("over budget: a", out)

    def test_too_little_history_never_fails(self):
        code, out = self.run_budget([job("a", 900), job("b", 900)], [[job("a", 100), job("b", 100)]] * 2)
        self.assertEqual(0, code, out)
        self.assertIn("not enough history (2 of 3)", out)

    def test_a_job_that_did_not_succeed_is_not_recorded_and_does_not_poison_history(self):
        past = [[job("a", 100), job("b", 100)]] * 3 + [[job("a", 9000, "failure"), job("b", 100)]]
        code, out = self.run_budget([job("a", 100), job("b", 100, "failure")], past)
        self.assertEqual(0, code, out)
        self.assertIn("| b | not recorded", out)
        self.assertIn("| a | 100 s | 100 s (n=3) | 1.00x | ok |", out)


if __name__ == "__main__":
    unittest.main()
