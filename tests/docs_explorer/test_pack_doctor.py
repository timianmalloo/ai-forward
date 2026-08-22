import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"
SCRIPT = SCRIPTS / "pack-doctor.py"


def load_module():
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location("pack_doctor", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPTS))


class PackDoctorInterpreterTests(unittest.TestCase):
    """FR-031. The pack documents `python3`, which does not exist on a python.org Windows
    install. The doctor must name the working substitution rather than let the reader
    discover it one failing command at a time."""

    def setUp(self):
        self.module = load_module()

    def _fake(self, ok_labels):
        """Stub run_bounded so only the given argv[0..1] forms report Python 3."""
        def runner(argv, **kwargs):
            label = " ".join(argv[:-1])
            if label in ok_labels:
                return SimpleNamespace(returncode=0, stdout="Python 3.12.10\n", stderr="")
            return SimpleNamespace(returncode=9009, stdout="", stderr="Python was not found")
        return runner

    def test_python3_available_passes(self):
        with mock.patch.object(self.module, "run_bounded", self._fake({"python3"})):
            result = self.module.check_interpreter()
        self.assertEqual("PASS", result["status"])

    def test_windows_shape_warns_and_names_the_substitution(self):
        # python3 absent, python present - the python.org Windows shape.
        with mock.patch.object(self.module, "run_bounded", self._fake({"python"})):
            result = self.module.check_interpreter()
        self.assertEqual("WARN", result["status"])
        self.assertIn("`python`", result["detail"])
        self.assertIn("python3", result["fix"])

    def test_no_interpreter_fails(self):
        with mock.patch.object(self.module, "run_bounded", self._fake(set())):
            result = self.module.check_interpreter()
        self.assertEqual("FAIL", result["status"])

    def test_launch_failure_is_a_miss_not_a_crash(self):
        def raiser(argv, **kwargs):
            raise OSError("not found")
        with mock.patch.object(self.module, "run_bounded", raiser):
            result = self.module.check_interpreter()
        self.assertEqual("FAIL", result["status"])

    def test_a_bad_call_is_not_swallowed_into_a_plausible_result(self):
        # Guards the bug this check shipped with: a TypeError from a wrong keyword was
        # caught by a bare `except Exception` and reported as "no Python found".
        def bug(argv, **kwargs):
            raise TypeError("unexpected keyword argument")
        with mock.patch.object(self.module, "run_bounded", bug):
            with self.assertRaises(TypeError):
                self.module.check_interpreter()


class PackDoctorGraphTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_empty_graph_is_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)

            result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("0 artifacts", result["detail"])

    def test_invalid_graph_is_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            docs = root / "docs"
            (docs / "invalid.md").write_text(
                "---\nid: invalid\ntitle: Invalid\ntype: unknown\n---\n",
                encoding="utf-8",
            )

            result = self.module.check_graph(str(root))

            self.assertEqual("FAIL", result["status"])
            self.assertIn("graph problem", result["detail"])

    def test_graph_timeout_is_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = type(
                "Result",
                (),
                {
                    "returncode": -1,
                    "stdout": "",
                    "stderr": "",
                    "timed_out": True,
                    "limit_exceeded": None,
                },
            )()

            original = self.module.run_bounded
            self.module.run_bounded = lambda *args, **kwargs: fake
            try:
                result = self.module.check_graph(str(root))
            finally:
                self.module.run_bounded = original

            self.assertEqual("WARN", result["status"])
            self.assertIn("timed out", result["detail"])

    def test_graph_output_limit_is_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = self._process_result(limit_exceeded="output")

            with mock.patch.object(self.module, "run_bounded", return_value=fake):
                result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("output limit", result["detail"])

    def test_graph_nonzero_exit_is_inconclusive_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = self._process_result(returncode=3, stderr="invalid")

            with mock.patch.object(self.module, "run_bounded", return_value=fake):
                result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("inconclusive", result["detail"])
            self.assertIn("invalid", result["detail"])

    def test_graph_containment_failure_is_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = self._process_result()
            fake.contained = False
            fake.containment_error = "AssignProcessToJobObject failed (5)"

            with mock.patch.object(self.module, "run_bounded", return_value=fake):
                result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("not run safely", result["detail"])
            self.assertIn("AssignProcessToJobObject", result["detail"])

    def test_graph_malformed_output_is_inconclusive_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = self._process_result(stdout="{not json")

            with mock.patch.object(self.module, "run_bounded", return_value=fake):
                result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("inconclusive", result["detail"])

    def test_graph_health_findings_are_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = self._process_result(
                stdout=json.dumps(
                    {
                        "artifacts": 2,
                        "problems": [],
                        "stale": ["a"],
                        "flagged": ["b"],
                        "orphans": [],
                    }
                )
            )

            with mock.patch.object(self.module, "run_bounded", return_value=fake):
                result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("stale/flagged/orphan", result["detail"])

    def test_main_returns_nonzero_when_any_check_fails(self):
        checks = [
            self.module._result("one", self.module.PASS, "ok"),
            self.module._result("two", self.module.FAIL, "broken"),
        ]
        with mock.patch.object(self.module, "run", return_value=checks), mock.patch.object(
            self.module.sys, "argv", ["pack-doctor.py", "--json"]
        ):
            with mock.patch("builtins.print"):
                exit_code = self.module.main()

        self.assertEqual(1, exit_code)

    def test_main_strict_returns_nonzero_when_any_check_warns(self):
        checks = [
            self.module._result("one", self.module.PASS, "ok"),
            self.module._result("two", self.module.WARN, "inconclusive"),
        ]
        with mock.patch.object(self.module, "run", return_value=checks), mock.patch.object(
            self.module.sys, "argv", ["pack-doctor.py", "--json", "--strict"]
        ):
            with mock.patch("builtins.print"):
                exit_code = self.module.main()

        self.assertEqual(1, exit_code)

    def test_main_non_strict_preserves_warning_exit_zero(self):
        checks = [self.module._result("one", self.module.WARN, "review needed")]
        with mock.patch.object(self.module, "run", return_value=checks), mock.patch.object(
            self.module.sys, "argv", ["pack-doctor.py", "--json"]
        ):
            with mock.patch("builtins.print"):
                exit_code = self.module.main()

        self.assertEqual(0, exit_code)

    @staticmethod
    def _process_result(
        returncode=0,
        stdout='{"artifacts": 0, "problems": [], "stale": [], "flagged": [], "orphans": []}',
        stderr="",
        timed_out=False,
        limit_exceeded=None,
    ):
        return SimpleNamespace(
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            limit_exceeded=limit_exceeded,
        )

    @staticmethod
    def _install_graph_tool(temp):
        root = Path(temp)
        destination = root / "docs" / "ai-forward-pack" / "scripts"
        destination.mkdir(parents=True)
        shutil.copy2(SCRIPTS / "docs-graph.py", destination / "docs-graph.py")
        return root


class PackDoctorNodeRunnerTests(unittest.TestCase):
    """FR-055 / class PACK-C — a documented command assumed portable. `npm run` executes
    scripts through a CHILD SHELL whose PATH can differ from the caller's, so node resolving
    for you proves nothing about whether the documented command works. Observed on a real
    Windows host: `node --version` -> v24.18.0, `cmd /c node --version` -> not recognized,
    `npm run test:docs-explorer:core` -> the same failure, tests themselves 31/31 green."""

    def setUp(self):
        self.module = load_module()

    def _fake(self, direct_ok=True, shell_ok=True):
        def runner(argv, **kwargs):
            is_shell = argv[0] in ("cmd", "sh")
            ok = shell_ok if is_shell else direct_ok
            if ok:
                return SimpleNamespace(returncode=0, stdout="v24.18.0\n", stderr="")
            return SimpleNamespace(
                returncode=1, stdout="",
                stderr="'node' is not recognized as an internal or external command")
        return runner

    def test_passes_when_the_spawned_shell_can_resolve_node(self):
        with mock.patch.object(self.module, "run_bounded", self._fake(True, True)):
            result = self.module.check_node_runner()
        self.assertEqual("PASS", result["status"])

    def test_warns_when_only_the_child_shell_cannot_find_node(self):
        """The exact FR-055 shape: green for you, red for `npm run`."""
        with mock.patch.object(self.module, "run_bounded", self._fake(True, False)):
            result = self.module.check_node_runner()
        self.assertEqual("WARN", result["status"],
                         "a documented command that cannot run must be reported, not assumed")

    def test_the_warning_names_the_working_invocation(self):
        """PACK-C's stated control is to NAME the form that works here, not just complain."""
        with mock.patch.object(self.module, "run_bounded", self._fake(True, False)):
            result = self.module.check_node_runner()
        text = json.dumps(result)
        self.assertIn("node --test", text, "must name the direct invocation that does work")

    def test_missing_node_is_reported_without_pretending_it_is_a_path_problem(self):
        with mock.patch.object(self.module, "run_bounded", self._fake(False, False)):
            result = self.module.check_node_runner()
        self.assertEqual("WARN", result["status"])
        self.assertIn("not on PATH", json.dumps(result))

    def test_the_check_is_wired_into_the_doctor_run(self):
        """A check nobody calls is not a control."""
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("check_node_runner()", source.split("def run(root)")[1][:800])


if __name__ == "__main__":
    unittest.main()
