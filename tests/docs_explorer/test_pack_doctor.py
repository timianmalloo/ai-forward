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


if __name__ == "__main__":
    unittest.main()
