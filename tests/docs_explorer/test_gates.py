"""FR-091 / FR-094: one gate list drives the local proof and every CI job, and test shards partition
the suite. Red first: tools/gates.py did not exist, and the workflow carried hand-copied gate steps."""
import contextlib
import importlib.util
import io
import pathlib
import re
import unittest

import conftest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "pack-consistency.yml"


def load():
    spec = importlib.util.spec_from_file_location("gates_under_test", ROOT / "tools" / "gates.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GateListTests(unittest.TestCase):
    def setUp(self):
        self.g = load()

    def ids(self, **kwargs):
        ctx = self.g.Context(kwargs.get("ci", True), False, kwargs.get("shard"), kwargs["os_name"])
        return [gate_id for gate_id, _name, _action, _reason in self.g.selected(ctx)]

    def test_ids_are_unique_and_every_ci_job_runs_the_tests_last(self):
        ids = [gate[0] for gate in self.g.GATES]
        self.assertEqual(len(ids), len(set(ids)))
        for os_name in ("linux", "windows", "macos"):
            with self.subTest(os=os_name):
                self.assertEqual("3", self.ids(os_name=os_name)[-1])

    def test_a_later_shard_runs_only_its_tests_and_the_first_runs_every_gate(self):
        self.assertEqual(["3"], self.ids(os_name="windows", shard=(2, 3)))
        self.assertEqual(self.ids(os_name="windows"), self.ids(os_name="windows", shard=(1, 3)))

    def test_a_gate_that_changes_local_state_never_runs_locally(self):
        ctx = self.g.Context(False, False, None, "windows")
        reasons = {gate_id: reason for gate_id, _n, _a, reason in self.g.selected(ctx)}
        self.assertIn("CI runs it", reasons["9d"])

    def run_with(self, gates, ci):
        self.g.GATES = gates
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.g.main(["run"] + (["--ci"] if ci else []))
        return code, out.getvalue()

    def test_every_gate_runs_after_a_failure_and_the_run_fails(self):
        seen = []
        gates = [("a", "first", lambda ctx: seen.append("a") or False, self.g.ALL, True, "check"),
                 ("b", "second", lambda ctx: seen.append("b") or True, self.g.ALL, True, "check")]
        code, out = self.run_with(gates, ci=False)
        self.assertEqual(1, code)
        self.assertEqual(["a", "b"], seen)
        self.assertIn("FAIL", out)

    def test_a_skip_passes_locally_and_fails_in_ci(self):
        def unavailable(ctx):
            raise self.g.Skip("node is not installed")
        gates = [("a", "needs node", unavailable, self.g.ALL, True, "check")]
        self.assertEqual(0, self.run_with(gates, ci=False)[0])
        self.assertEqual(1, self.run_with(gates, ci=True)[0])


class ShardTests(unittest.TestCase):
    IDS = ["tests/docs_explorer/test_{}.py::Case::test_{}".format(a, b) for a in range(40) for b in range(25)]

    def test_shards_are_disjoint_and_cover_every_test(self):
        for count in (1, 2, 3, 4):
            with self.subTest(count=count):
                owners = [[i for i in range(1, count + 1) if conftest.in_shard(nodeid, (i, count))]
                          for nodeid in self.IDS]
                self.assertTrue(all(len(owner) == 1 for owner in owners))

    def test_the_split_ignores_path_separators(self):
        nodeid = "tests/docs_explorer/test_x.py::Case::test_y"
        self.assertEqual(conftest.in_shard(nodeid, (2, 3)), conftest.in_shard(nodeid.replace("/", "\\"), (2, 3)))

    def test_shards_are_roughly_even(self):
        sizes = [sum(conftest.in_shard(nodeid, (i, 3)) for nodeid in self.IDS) for i in (1, 2, 3)]
        self.assertLess(max(sizes) - min(sizes), len(self.IDS) * 0.1, sizes)


class CallersUseTheListTests(unittest.TestCase):
    def test_the_workflow_runs_gates_only_through_the_list(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("tools/gates.py run --ci", workflow)
        for copied in ("check-consistency.py", "verify-no-machine-paths.py", "marker-lint.py",
                       "docs-graph.py validate", "context-budget.py", "pytest tests", "sync-pack.ps1"):
            with self.subTest(gate=copied):
                self.assertNotIn(copied, workflow, "a gate was copied into the workflow")

    def test_the_baseline_fetch_never_cuts_the_checkout_history(self):
        # CI-ENV (2026-10-19, run 39302201214): the baseline step fetched main at depth 1 after a
        # depth-50 checkout. On a push to main that marked HEAD itself shallow, and PACK-W's
        # history check refused all three jobs. Every fetch of main must be as deep as the checkout.
        workflow = WORKFLOW.read_text(encoding="utf-8")
        checkout = set(re.findall(r"fetch-depth:\s*(\d+)", workflow))
        fetched = set(re.findall(r"git fetch [^\n]*--depth=(\d+)[^\n]*origin main", workflow))
        self.assertEqual({"50"}, checkout)
        self.assertEqual(checkout, fetched)

    def test_verify_bundle_delegates_to_the_list(self):
        script = (ROOT / "tools" / "verify-bundle.ps1").read_text(encoding="utf-8")
        self.assertIn("tools/gates.py", script.replace("\\", "/"))
        self.assertNotRegex(script, re.compile(r"^\s*Gate \"", re.M))


if __name__ == "__main__":
    unittest.main()
