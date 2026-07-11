import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "pack" / "evals" / "run-evals.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_evals", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class RunEvalsCommandTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.case = {
            "assertions": [
                {"type": "cmd-exit", "cmd": ["python3", "-c", "pass"], "exit": 0}
            ]
        }

    def test_cmd_exit_fails_when_process_times_out_even_if_exit_matches(self):
        result = self._process_result(timed_out=True)

        with tempfile.TemporaryDirectory() as workspace, mock.patch.object(
            self.module, "run_bounded", return_value=result
        ):
            failures = self.module.check(self.case, workspace)

        self.assertEqual(1, len(failures))
        self.assertIn("deadline", failures[0])

    def test_cmd_exit_fails_when_output_limit_is_exceeded_even_if_exit_matches(self):
        result = self._process_result(limit_exceeded="stdout")

        with tempfile.TemporaryDirectory() as workspace, mock.patch.object(
            self.module, "run_bounded", return_value=result
        ):
            failures = self.module.check(self.case, workspace)

        self.assertEqual(1, len(failures))
        self.assertIn("stdout limit", failures[0])

    def test_cmd_exit_fails_when_process_containment_is_not_established(self):
        result = self._process_result(
            contained=False,
            cleanup_error="synthetic cleanup failure",
            stderr="PROCESS_CLEANUP_FAILED",
        )

        with tempfile.TemporaryDirectory() as workspace, mock.patch.object(
            self.module, "run_bounded", return_value=result
        ):
            failures = self.module.check(self.case, workspace)

        self.assertIn("containment failed", failures[0])
        self.assertTrue(any("synthetic cleanup failure" in failure for failure in failures))
        self.assertTrue(any("PROCESS_CLEANUP_FAILED" in failure for failure in failures))

    def test_timeout_and_cleanup_failure_are_reported_independently(self):
        result = self._process_result(
            timed_out=True,
            contained=False,
            cleanup_error="tree survived",
        )

        with tempfile.TemporaryDirectory() as workspace, mock.patch.object(
            self.module, "run_bounded", return_value=result
        ):
            failures = self.module.check(self.case, workspace)

        self.assertTrue(any("deadline" in failure for failure in failures))
        self.assertTrue(any("containment failed" in failure for failure in failures))
        self.assertTrue(any("tree survived" in failure for failure in failures))

    def test_setup_rejects_absolute_and_traversal_paths(self):
        with tempfile.TemporaryDirectory() as workspace:
            for path in (
                str(Path(workspace).parent / "escape.txt"),
                "..\\escape.txt",
                "../escape.txt",
                "C:\\escape.txt",
                "\\\\server\\share\\escape.txt",
                "/tmp/escape.txt",
            ):
                with self.subTest(path=path):
                    with self.assertRaisesRegex(ValueError, "workspace-relative|escapes"):
                        self.module.seed(
                            {"setup": [{"path": path, "content": "blocked"}]},
                            workspace,
                        )

    def test_assertion_rejects_path_outside_workspace(self):
        case = {
            "assertions": [
                {"type": "file-exists", "path": "..\\outside.txt"},
            ]
        }

        with tempfile.TemporaryDirectory() as workspace:
            failures = self.module.check(case, workspace)

        self.assertEqual(1, len(failures))
        self.assertRegex(failures[0], "workspace-relative|escapes the eval workspace")

    def test_exec_rejects_prompt_interpolation(self):
        case = {"id": "unsafe-prompt", "prompt": "hello & exit 9", "setup": []}

        with tempfile.TemporaryDirectory() as workspace, self.assertRaisesRegex(
            ValueError, "AIF_EVAL_PROMPT"
        ):
            self.module.run_exec(
                case,
                workspace,
                "agent --prompt {prompt}",
                timeout_seconds=1,
            )

    def test_exec_rejects_workspace_interpolation(self):
        case = {"id": "unsafe-workspace", "prompt": "hello", "setup": []}

        with tempfile.TemporaryDirectory() as workspace, self.assertRaisesRegex(
            ValueError, "AIF_EVAL_WORKSPACE"
        ):
            self.module.run_exec(
                case,
                workspace,
                "agent --workspace {workspace}",
                timeout_seconds=1,
            )

    def test_case_id_must_be_a_lowercase_kebab_case_slug(self):
        for case_id in (
            "../escape",
            "..\\escape",
            "Uppercase",
            "contains space",
            "trailing-",
            "-leading",
            "",
        ):
            with self.subTest(case_id=case_id), self.assertRaisesRegex(
                ValueError, "kebab-case slug"
            ):
                self.module.validate_case_id(case_id)

    def test_batch_workspace_is_derived_from_validated_case_id(self):
        with tempfile.TemporaryDirectory() as workspace:
            resolved = self.module.workspace_path(workspace, "safe-case")

        self.assertEqual(
            str((Path(workspace) / "safe-case").resolve()),
            resolved,
        )

    def test_exec_passes_case_data_only_through_environment(self):
        case = {"id": "safe-case", "prompt": "hello & exit 9", "setup": [], "assertions": []}
        result = self._process_result()
        captured = {}

        def run_bounded(command, **kwargs):
            captured["command"] = command
            captured.update(kwargs)
            return result

        with tempfile.TemporaryDirectory() as workspace, mock.patch.object(
            self.module, "run_bounded", side_effect=run_bounded
        ):
            failures = self.module.run_exec(
                case,
                workspace,
                "agent --headless",
                timeout_seconds=7,
            )

        self.assertEqual([], failures)
        self.assertEqual("hello & exit 9", captured["env"]["AIF_EVAL_PROMPT"])
        self.assertEqual("safe-case", captured["env"]["AIF_EVAL_CASE"])
        self.assertEqual(str(Path(workspace).resolve()), captured["env"]["AIF_EVAL_WORKSPACE"])
        self.assertEqual(str(Path(workspace).resolve()), captured["cwd"])
        self.assertEqual(7, captured["timeout_seconds"])

    @staticmethod
    def _process_result(
        timed_out=False,
        limit_exceeded=None,
        contained=True,
        cleanup_error=None,
        stderr="",
    ):
        return SimpleNamespace(
            returncode=0,
            stdout="",
            stderr=stderr,
            timed_out=timed_out,
            limit_exceeded=limit_exceeded,
            contained=contained,
            containment_error=cleanup_error,
            cleanup_error=cleanup_error,
        )


if __name__ == "__main__":
    unittest.main()
