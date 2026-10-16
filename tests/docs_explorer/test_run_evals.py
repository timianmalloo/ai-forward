import importlib.util
import io
import json
import os
import subprocess
import sys
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
        # Compare resolved to resolved: macOS temp dirs live under /private/var and are reached
        # through the /var symlink, so a one-sided resolve() fails there (T-2, cross-platform
        # readiness). Both sides name the same directory; that is the contract.
        self.assertEqual(str(Path(workspace).resolve()),
                         str(Path(captured["env"]["AIF_EVAL_WORKSPACE"]).resolve()))
        self.assertEqual(str(Path(workspace).resolve()), str(Path(captured["cwd"]).resolve()))
        self.assertEqual(7, captured["timeout_seconds"])

    def test_cmd_exit_completion_stdout_accepts_lf_and_crlf_but_not_missing_or_extra_output(self):
        case = {"assertions": [{"type": "cmd-exit", "cmd": ["python3", "-c", "pass"], "exit": 0, "stdout": "completed\n"}]}
        with tempfile.TemporaryDirectory() as workspace:
            for output, passes in (("completed\n", True), ("completed\r\n", True), ("", False), ("prefix completed\n", False), ("completed\nextra\n", False)):
                with self.subTest(output=output):
                    result = self._process_result()
                    result.stdout = output
                    with mock.patch.object(self.module, "run_bounded", return_value=result):
                        failures = self.module.check(case, workspace)
                    self.assertEqual(passes, not failures, failures)
            result = self._process_result(timed_out=True)
            result.stdout = "completed\n"
            with mock.patch.object(self.module, "run_bounded", return_value=result):
                self.assertTrue(self.module.check(case, workspace))
            result = self._process_result()
            result.returncode = 1
            result.stdout = "completed\n"
            with mock.patch.object(self.module, "run_bounded", return_value=result):
                self.assertTrue(self.module.check(case, workspace))

    def test_files_absent_rejects_malformed_patterns_and_unreadable_tree(self):
        with tempfile.TemporaryDirectory() as workspace:
            for patterns in ([], "*.md", [""], [None], [12]):
                with self.subTest(patterns=patterns):
                    failures = self.module.check({"assertions": [{"type": "files-absent", "patterns": patterns}]}, workspace)
                    self.assertTrue(failures)
            def unreadable(*args, **kwargs):
                kwargs["onerror"](PermissionError("unreadable product subtree"))
                return []
            with mock.patch.object(self.module.os, "walk", side_effect=unreadable):
                failures = self.module.check({"assertions": [{"type": "files-absent", "patterns": ["*.md"]}]}, workspace)
            self.assertTrue(any("unreadable" in failure for failure in failures), failures)

    def test_files_absent_case_sensitivity_is_explicit_and_allow_paths_stay_exact(self):
        with tempfile.TemporaryDirectory() as workspace:
            Path(workspace, "README.MD").write_text("Ordinary product guide\n", encoding="utf-8")
            assertion = {"type": "files-absent", "patterns": ["*.md"]}
            self.assertEqual([], self.module.check({"assertions": [assertion]}, workspace))
            assertion["case_sensitive"] = True
            self.assertEqual([], self.module.check({"assertions": [assertion]}, workspace))
            assertion["case_sensitive"] = False
            failures = self.module.check({"assertions": [assertion]}, workspace)
            self.assertTrue(any("README.MD" in failure for failure in failures), failures)
            assertion["allow"] = ["README.md"]
            self.assertTrue(self.module.check({"assertions": [assertion]}, workspace))
            assertion["allow"] = ["README.MD"]
            self.assertEqual([], self.module.check({"assertions": [assertion]}, workspace))

    def test_files_absent_case_sensitive_requires_a_boolean_even_on_an_empty_tree(self):
        with tempfile.TemporaryDirectory() as workspace:
            for value in (None, 0, 1, "false", "true", [], {}):
                with self.subTest(value=value):
                    failures = self.module.check({"assertions": [{
                        "type": "files-absent", "patterns": ["*.md"], "case_sensitive": value,
                    }, {"type": "file-exists", "path": "missing"}]}, workspace)
                    self.assertEqual(2, len(failures), failures)
                    self.assertIn("case_sensitive must be a boolean", failures[0])
                    self.assertIn("missing", failures[1])

    def test_unknown_assertion_type_is_refused(self):
        with tempfile.TemporaryDirectory() as workspace:
            failures = self.module.check({"assertions": [{"type": "file-exist", "path": "missing"}]}, workspace)
        self.assertEqual(1, len(failures))
        self.assertIn("unsupported assertion type", failures[0])

    def test_successful_file_exists_and_absent_assertions_still_pass(self):
        with tempfile.TemporaryDirectory() as workspace:
            Path(workspace, "present").write_text("present", encoding="utf-8")
            failures = self.module.check({"assertions": [
                {"type": "file-exists", "path": "present"},
                {"type": "file-absent", "path": "missing"},
            ]}, workspace)
        self.assertEqual([], failures)

    def test_malformed_assertion_is_refused_without_aborting_remaining_checks(self):
        with tempfile.TemporaryDirectory() as workspace:
            failures = self.module.check({"assertions": [
                {}, {"type": "file-exists", "path": "missing"},
            ]}, workspace)
        self.assertEqual(2, len(failures))
        self.assertIn("assertion", failures[0])
        self.assertIn("missing", failures[1])

    def test_grep_transcript_requires_observed_transcript_not_workspace_file(self):
        case = {"assertions": [{"type": "grep-transcript", "pattern": "observed"}]}
        with tempfile.TemporaryDirectory() as workspace:
            Path(workspace, "transcript.txt").write_text("observed", encoding="utf-8")
            failures = self.module.check(case, workspace)
        self.assertEqual(1, len(failures))
        self.assertIn("transcript not supplied", failures[0])

    def test_grep_transcript_matches_bounded_supplied_output(self):
        case = {"assertions": [{"type": "grep-transcript", "pattern": "observed"}]}
        with tempfile.TemporaryDirectory() as workspace:
            self.assertEqual([], self.module.check(case, workspace, transcript="observed\n"))
            self.assertTrue(self.module.check(case, workspace, transcript="unrelated\n"))
            failures = self.module.check(case, workspace, transcript="observed" + "x" * self.module.MAX_ASSERTION_FILE_BYTES)
        self.assertTrue(any("limit" in failure for failure in failures), failures)

    def test_exec_checks_captured_output_for_inherited_transcript_assertions(self):
        # Synthetic subprocess plumbing control, not evidence of actions or review.
        case = {"id": "transcript-control", "prompt": "plumbing", "assertions": [
            {"type": "grep-transcript", "pattern": "observed"},
        ]}
        result = self._process_result()
        result.stdout = "observed\n"
        with tempfile.TemporaryDirectory() as workspace, mock.patch.object(
            self.module, "run_bounded", return_value=result
        ):
            self.assertEqual([], self.module.run_exec(case, workspace, "synthetic-control", 1))
            result.stdout = "unrelated\n"
            self.assertTrue(self.module.run_exec(case, workspace, "synthetic-control", 1))

    def test_check_cli_reads_explicit_bounded_transcript_outside_workspace(self):
        # Explicit caller-supplied capture; never infer a transcript from artifacts.
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root, "workspace")
            workspace.mkdir()
            case_path = Path(root, "case.json")
            case_path.write_text(json.dumps({"id": "transcript-control", "assertions": [
                {"type": "grep-transcript", "pattern": "observed"},
            ]}), encoding="utf-8")
            transcript_path = Path(root, "captured-stdout.txt")
            transcript_path.write_text("observed\n", encoding="utf-8")
            argv = [str(SCRIPT), "--case", str(case_path), "--workspace", str(workspace), "--check", "--transcript", str(transcript_path)]
            with mock.patch.object(sys, "argv", argv):
                self.assertEqual(0, self.module.main())
            transcript_path.write_text("unrelated\n", encoding="utf-8")
            with mock.patch.object(sys, "argv", argv):
                self.assertEqual(1, self.module.main())

    def test_all_inherited_transcript_patterns_are_supported_without_being_skipped(self):
        # These finite strings test regex plumbing, not genuine skill execution.
        observations = {
            "also-01": "done when",
            "compile-01": "prompt-compile.py skeleton\nverbatim trace\nprompt-compile.py finish\ndispatchable",
            "execute-with-coordination-01": (
                "coord doctor\ncoord install\nconvergence condition budget\ntermination variant strictly decreasing\n"
                "seam request\nobserved-only\nevidence, not authority\nplanned vs actual\nworktree cleanup"
            ),
        }
        collected = []
        with tempfile.TemporaryDirectory() as workspace:
            for case_id, transcript in observations.items():
                case = json.loads((REPO / "pack/evals/cases" / (case_id + ".json")).read_text(encoding="utf-8"))
                assertions = [a for a in case["assertions"] if a["type"] == "grep-transcript"]
                collected.extend(assertions)
                with self.subTest(case=case_id):
                    self.assertEqual([], self.module.check({"assertions": assertions}, workspace, transcript=transcript))
                    self.assertEqual(len(assertions), len(self.module.check({"assertions": assertions}, workspace, transcript="")))
        self.assertEqual(14, len(collected))

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


class DeliverFeatureArtifactTests(unittest.TestCase):
    """Real subprocess artifact controls; these do not simulate a /deliver journey."""

    CASE_PATH = REPO / "pack/evals/cases/deliver-feature-01.json"
    CORRECT_APP = (
        "def clamp(value, low, high):\n"
        "    if low > high:\n"
        "        raise ValueError('inverted bounds')\n"
        "    return min(high, max(low, value))\n"
    )

    def setUp(self):
        self.module = load_module()
        self.case = json.loads(self.CASE_PATH.read_text(encoding="utf-8"))
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.module.seed(self.case, str(self.workspace))

    def write_app(self, content):
        (self.workspace / "app.py").write_text(content, encoding="utf-8")

    def check(self):
        return self.module.check(self.case, str(self.workspace))

    @classmethod
    def call_fault(cls, call, instruction):
        return (
            "import os\ncalls = 0\ndef clamp(value, low, high):\n"
            "    global calls\n    calls += 1\n"
            f"    if calls == {call}:\n        {instruction}\n"
            "    if low > high:\n        raise ValueError('inverted bounds')\n"
            "    return min(high, max(low, value))\n"
        )

    def test_hard_exit_at_import_first_call_or_final_boundary_is_refused(self):
        for stage, content in (
            ("import", "import os\nos._exit(0)\n"),
            ("first", self.call_fault(1, "os._exit(0)")),
            ("final", self.call_fault(9, "os._exit(0)")),
        ):
            with self.subTest(stage=stage):
                self.write_app(content)
                failures = self.check()
                self.assertTrue(failures, "exit 0 without complete oracle execution passed")
                self.assertTrue(any("stdout" in failure for failure in failures), failures)

    def test_correct_lf_and_crlf_complete_the_positive_oracle(self):
        contents = {item["path"]: item["content"] for item in self.case["setup"]}
        contents["app.py"] = self.CORRECT_APP
        real_open = open

        def windows_seed_writer(path, mode, **kwargs):
            # Use the real text writer: newline=None translates LF this way on Windows.
            return real_open(path, mode, newline="\r\n", **kwargs)

        for windows_translation in (False, True):
            for newline in (b"\n", b"\r\n"):
                with self.subTest(windows_translation=windows_translation, newline=newline):
                    if windows_translation:
                        with mock.patch.object(self.module, "open", side_effect=windows_seed_writer, create=True):
                            self.module.seed(self.case, str(self.workspace))
                        with io.TextIOWrapper(io.BytesIO(), encoding="utf-8", newline="\r\n") as writer:
                            writer.write(self.CORRECT_APP)
                            writer.flush()
                            (self.workspace / "app.py").write_bytes(writer.buffer.getvalue())
                        for name, content in contents.items():
                            self.assertEqual(content.encode("utf-8").replace(b"\n", b"\r\n"),
                                             (self.workspace / name).read_bytes())
                        if newline == b"\r\n":
                            # Old-code control: replacing LF in native CRLF doubles CR.
                            for name in contents:
                                path = self.workspace / name
                                path.write_bytes(path.read_bytes().replace(b"\n", newline))
                                self.assertIn(b"\r\r\n", path.read_bytes())
                            self.assertTrue(any("verifier identity changed" in failure
                                                for failure in self.check()))
                    else:
                        self.module.seed(self.case, str(self.workspace))
                        self.write_app(self.CORRECT_APP)
                    # Derive fixture bytes from canonical inputs, never native text output.
                    for name, content in contents.items():
                        path = self.workspace / name
                        expected = content.encode("utf-8").replace(b"\n", newline)
                        path.write_bytes(content.encode("utf-8").replace(b"\n", newline))
                        self.assertEqual(expected, path.read_bytes())
                        self.assertEqual(content, path.read_text(encoding="utf-8"))
                    self.assertEqual([], self.check())

    def test_system_exit_at_import_first_call_or_final_boundary_is_refused(self):
        for stage, content in (
            ("import", "raise SystemExit(0)\n"),
            ("first", self.call_fault(1, "raise SystemExit(0)")),
            ("final", self.call_fault(9, "raise SystemExit(0)")),
        ):
            with self.subTest(stage=stage):
                self.write_app(content)
                failures = self.check()
                self.assertTrue(failures)
                self.assertTrue(any("SystemExit" in failure for failure in failures), failures)

    def test_stub_wrong_boundaries_and_missing_inverted_check_are_refused(self):
        for name, content in (
            ("stub", "def clamp(value, low, high):\n    raise NotImplementedError\n"),
            ("always-low", "def clamp(value, low, high):\n    return low\n"),
            ("inverted", "def clamp(value, low, high):\n    return min(high, max(low, value))\n"),
            ("upper-boundary", self.CORRECT_APP.replace("min(high,", "min(high - 1,")),
            ("fractional", self.CORRECT_APP.replace("return min(high, max(low, value))", "return int(min(high, max(low, value)))")),
        ):
            with self.subTest(name=name):
                self.write_app(content)
                self.assertTrue(self.check())

    def test_case_is_a_t1_feature_with_proportional_applicable_review(self):
        prompt = self.case["prompt"]
        self.assertIn("T1", prompt)
        self.assertNotIn("T0", prompt)
        self.assertIn("proportionate", prompt)
        self.assertIn("independent review", prompt)
        self.assertEqual("artifact", self.case["qualification"]["kind"])
        self.assertIn("not", self.case["qualification"]["limits"].lower())

    def test_ordinary_document_extensions_and_directory_case_variants_are_refused(self):
        extensions = ("md", "markdown", "mdx", "rst", "txt", "adoc", "html", "htm",
                      "pdf", "doc", "docx", "odt", "rtf")
        names = ["guide.markdown", "README.MD", "DOCS/guide.json",
                 "nested/DoCs/guide.json", "DOCUMENTATION/guide.json",
                 "nested/Documentation/guide.json"]
        names.extend("nested/guide." + spelling for extension in extensions
                     for spelling in (extension, extension.upper(), extension.capitalize()))
        self.write_app(self.CORRECT_APP)
        for name in names:
            with self.subTest(name=name):
                path = self.workspace / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Unrequested product guide\n", encoding="utf-8")
                try:
                    failures = self.check()
                    self.assertTrue(any(name in failure for failure in failures), failures)
                finally:
                    path.unlink()

    def test_unsolicited_product_docs_are_refused(self):
        for name in (
            "docs/unrequested.md", "docs/audit/audit-log.jsonl", "docs/docs-index.js",
            "README.md", "nested/guide.rst", "nested/manual.html",
            "__pycache__/unrequested.md", ".pytest_cache/unrequested.md",
            "nested/.pytest_cache/unrequested.md", "nested/.pytest_cache/README.MD",
            "nested/.pytest_cache-extra/README.md", ".PYTEST_CACHE/README.md",
            "node_modules/unrequested.md", ".venv/unrequested.md",
            ".git/info/unrequested.md", ".git/ai-forward/unrequested.md",
            ".git/ai-forward/delivery-extra/proof.md", "nested/.git/ai-forward/delivery/proof.md",
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as workspace:
                self.module.seed(self.case, workspace)
                Path(workspace, "app.py").write_text(self.CORRECT_APP, encoding="utf-8")
                path = Path(workspace, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Unrequested product document\n", encoding="utf-8")
                self.assertTrue(self.module.check(self.case, workspace), f"unsolicited document {name} passed")

    def test_helper_closed_t1_feature_with_local_markdown_proof_passes_artifact(self):
        # Reuse real audit/compiler/helper subprocess fixtures, not an LLM journey.
        # The distinct reviewer label below exercises mechanics, not authentic review.
        from tests.docs_explorer import test_delivery as delivery_fixtures

        fixture = delivery_fixtures.DeliveryTests(methodName="runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        workspace = fixture.repo
        self.module.seed(self.case, str(workspace))
        started = fixture.start(contract_tier="T1", tier="T1", design_ready=True)
        self.assertEqual("T1", started["tier"])
        red = self.module.check(self.case, str(workspace))
        self.assertTrue(any("NotImplementedError" in failure for failure in red), red)
        (workspace / "app.py").write_text(self.CORRECT_APP, encoding="utf-8")
        self.assertEqual([], self.module.check(self.case, str(workspace)))

        local_area = Path(started["local_area"])
        self.assertEqual((workspace / ".git/ai-forward/delivery").resolve(), local_area.resolve())
        proof = local_area / "proof.md"
        proof.write_text(
            "# Task-local clamp proof\n\n"
            "Observed stub failures:\n" + "\n".join(red) + "\n\n"
            "Correct app passed every artifact assertion in real subprocesses.\n"
            "No authentication is established by these synthetic labels.\n",
            encoding="utf-8",
        )
        proof_link = local_area / "proof-link.md"
        try:
            proof_link.symlink_to(proof)
        except (OSError, NotImplementedError):
            pass  # Native platforms without symlink privilege still run the real closure.
        else:
            # A pathname allowance is not evidence acceptance: the helper still refuses links.
            rejected = fixture.run_cli("complete", "--task", "demo", "--stage", "implement",
                                       "--actor", "author", "--evidence", proof_link, ok=False)
            self.assertIn("nonempty regular file", rejected.stderr)
            proof_link.unlink()
        reviewed = fixture.run_cli("complete", "--task", "demo", "--stage", "implement",
                                   "--actor", "author", "--evidence", proof)
        self.assertEqual("reviewer", reviewed["gate"]["authority"])
        self_review = fixture.receipt(reviewed, actor="author", source="reviewer-report")
        self.assertIn("author cannot clear", fixture.run_cli(
            "resume", "--task", "demo", "--receipt", self_review, ok=False).stderr)
        receipt = fixture.receipt(reviewed, actor="synthetic-reviewer", source="reviewer-report")
        ready = fixture.run_cli("resume", "--task", "demo", "--receipt", receipt)
        self.assertEqual("verify", ready["next"])
        closure = fixture.write("closure.json", {
            "criteria": [{"criterion": "feature works", "observed": "real clamp oracle completed",
                          "evidence": [str(proof)]}],
            "changes": ["app.py"], "tests": ["complete clamp artifact assertions"],
            "skips": [], "limits": ["Synthetic review mechanics, not authentic review"],
            "remaining_gates": [],
        })
        closed = fixture.run_cli("complete", "--task", "demo", "--stage", "verify",
                                 "--actor", "author", "--evidence", proof, "--closure", closure)
        self.assertIsNone(closed["next"])
        self.assertIsNone(fixture.run_cli("status", "--task", "demo")["next"])
        self.assertEqual([], self.module.check(self.case, str(workspace)))
        proof.write_text(proof.read_text(encoding="utf-8") + "Later changed proof.\n", encoding="utf-8")
        self.assertIn("drift", fixture.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_real_pytest_from_root_and_tests_creates_allowed_cache_readme(self):
        for location in (".", "tests"):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as workspace:
                root = Path(workspace)
                self.module.seed(self.case, workspace)
                (root / "app.py").write_text(self.CORRECT_APP, encoding="utf-8")
                tests = root / "tests"
                tests.mkdir()
                (tests / "test_clamp.py").write_text(
                    "import sys\nfrom pathlib import Path\n"
                    "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
                    "from app import clamp\n"
                    "def test_clamp_bounds():\n"
                    "    assert clamp(-1, 0, 10) == 0\n"
                    "    assert clamp(5, 0, 10) == 5\n"
                    "    assert clamp(11, 0, 10) == 10\n",
                    encoding="utf-8",
                )
                cwd = root / location
                env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTEST_ADDOPTS="",
                           PYTEST_PLUGINS="", PYTHONDONTWRITEBYTECODE="1")
                result = subprocess.run(
                    [sys.executable, "-B", "-m", "pytest", "-q", "-c", os.devnull,
                     "--rootdir", str(cwd)], cwd=cwd, env=env,
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertIn("1 passed", result.stdout)
                cache_readme = cwd / ".pytest_cache/README.md"
                self.assertTrue(cache_readme.is_file(), result.stdout + result.stderr)
                self.assertEqual([], self.module.check(self.case, workspace))
                unwanted = cwd / ".pytest_cache/unrequested.md"
                unwanted.write_text("Unrequested product guide\n", encoding="utf-8")
                failures = self.module.check(self.case, workspace)
                self.assertTrue(any("unrequested.md" in f for f in failures), failures)

    def test_ordinary_runtime_caches_and_local_evidence_are_allowed(self):
        self.write_app(self.CORRECT_APP)
        for name in (
            "__pycache__/app.cpython-311.pyc", "nested/__pycache__/app.cpython-311.pyc",
            ".pytest_cache/CACHEDIR.TAG", ".pytest_cache/README.md",
            ".pytest_cache/.gitignore", ".pytest_cache/v/cache/nodeids",
            ".agents/log/audit/audit-log.jsonl", ".git/HEAD",
        ):
            path = self.workspace / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"runtime or existing task-local evidence\n")
        self.assertEqual([], self.check())

    def test_local_proof_allowance_does_not_change_generic_file_matching(self):
        self.write_app(self.CORRECT_APP)
        for name in (".git/ai-forward/delivery/proof.md", ".git/ai-forward/delivery/demo/proof.md"):
            path = self.workspace / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Task-local proof, not product documentation.\n", encoding="utf-8")
        self.assertEqual([], self.check())
        generic = {"assertions": [{"type": "files-absent", "patterns": ["*.md"]}]}
        failures = self.module.check(generic, str(self.workspace))
        self.assertTrue(any(".git/ai-forward/delivery/proof.md" in f for f in failures), failures)

    def test_directory_links_are_not_followed_but_product_document_link_is_refused(self):
        self.write_app(self.CORRECT_APP)
        with tempfile.TemporaryDirectory() as outside:
            proof = Path(outside, "outside.md")
            proof.write_text("External Markdown, not traversed.\n", encoding="utf-8")
            try:
                (self.workspace / "linked-directory").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"directory symlink unavailable: {error}")
            self.assertEqual([], self.check())
            # No new symlink/evidence semantic blessing: only existing walk behavior.
            (self.workspace / "product.md").symlink_to(proof)
            self.assertTrue(any("product.md" in f for f in self.check()))

    def test_case_discloses_local_proof_and_trusted_artifact_limits(self):
        limits = self.case["qualification"]["limits"]
        self.assertIn(".git/ai-forward/delivery/", limits)
        self.assertIn("trusted", limits)
        self.assertIn("symlink", limits)
        self.assertIn("authentic independent review", limits)
        self.assertIn("finite", limits)
        self.assertIn("case-insensitive", limits)
        self.assertIn("*/.pytest_cache/README.md", limits)
        self.assertIn("not content authentication", limits)

    def test_correct_file_writer_only_qualifies_the_artifact(self):
        command = self.module.command_for_host([
            "python3", "-c",
            "from pathlib import Path; Path('app.py').write_text(" + repr(self.CORRECT_APP) + ")",
        ])
        result = subprocess.run(command, cwd=self.workspace, capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], self.check())
        self.assertEqual("artifact", self.case["qualification"]["kind"])
        self.assertFalse(any(a["type"] == "grep-transcript" for a in self.case["assertions"]))

    def test_verifier_mutations_before_and_during_import_are_refused(self):
        for stage in ("before", "import"):
            with self.subTest(stage=stage):
                self.module.seed(self.case, str(self.workspace))
                self.write_app(self.CORRECT_APP)
                if stage == "before":
                    (self.workspace / "verify_clamp.py").write_text("# disabled\n", encoding="utf-8")
                else:
                    self.write_app(
                        "from pathlib import Path\n"
                        "Path('verify_clamp.py').write_text('# disabled\\n', encoding='utf-8')\n"
                        + self.CORRECT_APP
                    )
                failures = self.check()
                self.assertTrue(failures)
                self.assertTrue(any("verifier identity changed" in failure for failure in failures), failures)


if __name__ == "__main__":
    unittest.main()
