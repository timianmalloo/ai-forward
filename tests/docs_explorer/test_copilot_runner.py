"""Copilot admission and Windows runtime contracts; no model credentials required."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
import test_coord_runner as runner_fixture

SCRIPTS = Path(__file__).resolve().parents[2] / "pack" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CopilotAdmission(unittest.TestCase):
    def test_successful_ownership_check_does_not_grant_native_tool_permission(self):
        import json
        core = load("coord-core")
        self.assertEqual({}, json.loads(core.hook_response("allow", "unleased", "copilot")))
        self.assertEqual("deny", core.hook_decision_of(json.loads(core._not_checked("bad payload", "copilot"))))

    def test_plugin_pascalcase_edit_alias_keeps_the_gpt_freeform_patch(self):
        core = load("coord-core")
        with tempfile.TemporaryDirectory() as directory:
            payload = {"hook_event_name": "PreToolUse", "session_id": "native",
                       "tool_name": "Edit", "cwd": directory,
                       "tool_input": "*** Begin Patch\n*** Add File: result.txt\n+ok\n*** End Patch\n"}
            self.assertEqual([("Edit", "result.txt")],
                             core.parse_hook_request(payload, directory, host="copilot", cwd=directory))
            payload["tool_input"] = "not a patch"
            with self.assertRaises(ValueError):
                core.parse_hook_request(payload, directory, host="copilot", cwd=directory)

    def test_copilot_plugin_explicitly_carries_native_lifecycle_hooks(self):
        import json
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "coord-core.py"), "plugin", "--emit",
                 directory, "--host", "copilot"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            hooks = json.loads((Path(directory) / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
            self.assertTrue({"PreToolUse", "PostToolUse", "SessionStart", "SubagentStart",
                             "Stop", "SubagentStop"} <= hooks.keys())
            self.assertTrue((Path(directory) / "hooks/lifecycle.py").is_file())
            self.assertIn("--host", (Path(directory) / "hooks/hook.py").read_text(encoding="utf-8"))

    def test_explicit_acp_model_is_required_and_bypass_flags_are_refused(self):
        runner = load("coord-runner")
        self.assertEqual("gpt-5.4", runner.copilot_model(
            ["copilot", "--acp", "--model", "gpt-5.4"]))
        for argv in (["copilot", "--acp"], ["copilot", "--model", "gpt-5.4"],
                     ["copilot", "--acp", "--model", "auto"],
                     ["copilot", "--acp", "--model", "gpt-5.4", "--model", "other"],
                     ["copilot", "--acp", "--model", "gpt-5.4", "--allow-all"],
                     *[["copilot", "--acp", "--model", "gpt-5.4", flag] for flag in (
                         "--yolo", "--allow-all-tools", "--allow-all-paths", "--allow-all-urls",
                         "--assisted-approval", "--resume", "--continue", "--connect")]):
            with self.subTest(argv=argv), self.assertRaises(runner.Refused):
                runner.copilot_model(argv)

    def test_other_explicit_models_are_not_globally_banned_by_session_policy(self):
        runner = load("coord-runner")
        self.assertEqual("other-explicit-model", runner.copilot_model(
            ["copilot", "--acp", "--model", "other-explicit-model"]))

    def test_compiler_has_a_native_copilot_template(self):
        compiler = load("prompt-compile")
        template = SCRIPTS.parent / "templates" / "prompt-templates" / "copilot.v1.md"
        self.assertIn("harness: copilot", template.read_text(encoding="utf-8"))
        self.assertTrue(Path(compiler.default_templates_dir(), template.name).is_file())


class CopilotComposition(unittest.TestCase):
    """Exercise the deployed runner with a synthetic ACP peer and real Git state."""
    git = runner_fixture.RunnerTests.git
    write_audit = runner_fixture.RunnerTests.write_audit
    cli = runner_fixture.RunnerTests.cli
    prepare = runner_fixture.RunnerTests.prepare
    run_prepared = runner_fixture.RunnerTests.run_prepared
    add_decision = runner_fixture.RunnerTests.add_decision

    def setUp(self):
        runner_fixture.RunnerTests.setUp(self)
        self.env["COPILOT_HOME"] = str(Path(self.tmp.name) / "native-state")
        policy = self.repo / ".github" / "allowed_models.txt"
        policy.parent.mkdir()
        policy.write_text("fallback: gpt-5.4\ngpt-5.4\n", encoding="utf-8", newline="\n")
        self.git("add", ".github")
        self.git("commit", "-qm", "Bind native fixture model policy")

    def worker(self, session, branch, mode="ok"):
        worker = runner_fixture.RunnerTests.worker(self, session, branch, mode)
        worker["harness"] = "copilot"
        worker["argv"] += ["--acp", "--model", "gpt-5.4"]
        worker["deadline_seconds"] = 12
        return worker

    def qualify(self):
        import json
        path = runner_fixture.RunnerTests.qualify(self)
        qualification = json.loads(path.read_text(encoding="utf-8"))
        for profile in qualification["workers"].values():
            profile["effective_model"] = "gpt-5.4"
        path.write_text(json.dumps(qualification), encoding="utf-8", newline="\n")
        return path

    def pin(self, owner="owner", host="copilot"):
        return runner_fixture.RunnerTests.pin(self, owner, host)

    def test_copilot_owner_worker_receipt_and_persisted_status(self):
        import json
        self.env["AGENT_HOST"] = "copilot"
        prepared = self.prepare()
        result = self.run_prepared()
        self.assertEqual("ready_for_review", result["state"])
        receipt = json.loads((Path(prepared["workers"][0]["worktree"]) / "receipt.json").read_bytes())
        self.assertEqual("copilot", receipt["host"])
        self.assertEqual("worker-1", receipt["session"])
        self.assertEqual(prepared["workers"][0]["worktree"], receipt["cwd"])
        self.assertEqual("ready_for_review", self.cli("status", "--run", "test-run")["state"])

    def test_plugin_working_directory_does_not_change_the_tool_target(self):
        import json
        import subprocess
        (self.repo / "held.txt").write_text("held\n", encoding="utf-8", newline="\n")
        plugin = self.repo / "plugin"
        plugin.mkdir()
        claim = subprocess.run(
            [sys.executable, str(self.scripts / "coord-core.py"), "claim",
             "--wi", "fixture", "--path", "held.txt"],
            cwd=self.repo, env=dict(self.env, AGENT_SESSION="holder"),
            capture_output=True, text=True, encoding="utf-8", timeout=10)
        self.assertEqual(0, claim.returncode, claim.stdout + claim.stderr)
        payload = {"hook_event_name": "PreToolUse", "cwd": str(self.repo), "tool_name": "Edit",
                   "tool_input": "*** Begin Patch\n*** Update File: held.txt\n@@\n-held\n+changed\n*** End Patch\n"}
        result = subprocess.run(
            [sys.executable, str(self.scripts / "coord-core.py"), "hook", "--host", "copilot"],
            cwd=plugin, env=dict(self.env, AGENT_SESSION="other"), input=json.dumps(payload),
            capture_output=True, text=True, encoding="utf-8", timeout=10)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("deny", load("coord-core").hook_decision_of(json.loads(result.stdout)))
        self.assertIn("holder - fixture", result.stdout)
        self.assertNotIn("NOT CHECKED", result.stdout)

    test_open_owner_decision_blocks_ready_even_with_verified_receipt = (
        runner_fixture.RunnerTests.test_open_owner_decision_blocks_ready_even_with_verified_receipt)
    test_actual_independent_owner_ruling_allows_final_readiness = (
        runner_fixture.RunnerTests.test_actual_independent_owner_ruling_allows_final_readiness)
    test_configuration_drift_blocks_launch = runner_fixture.RunnerTests.test_configuration_drift_blocks_launch
    test_absent_and_competing_leader_block = runner_fixture.RunnerTests.test_absent_and_competing_leader_block
    test_duplicate_run_does_not_replay = runner_fixture.RunnerTests.test_duplicate_run_does_not_replay

    def test_wrong_effective_model_cannot_satisfy_qualification(self):
        import json
        self.prepare()
        path = self.qualify()
        qualification = json.loads(path.read_bytes())
        qualification["workers"]["worker-1"]["effective_model"] = "different-model"
        path.write_text(json.dumps(qualification), encoding="utf-8", newline="\n")
        self.pin()
        result = self.cli("run", "--run", "test-run", "--qualification", str(path), expected=2)
        self.assertEqual("RUN-COPILOT-MODEL", result["code"])

    def test_missing_native_model_policy_is_refused_before_preparation(self):
        import json
        (self.repo / ".github/allowed_models.txt").unlink()
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8", newline="\n")
        result = self.cli("prepare", "--contract", str(self.contract_path), expected=2)
        self.assertEqual("RUN-COPILOT-POLICY", result["code"])
        self.assertFalse((self.repo.parent / "repo-work-one").exists())

    def test_copilot_does_not_inherit_codex_operational_roots(self):
        self.contract["workers"][0]["additional_roots"] = [str(self.repo / ".agents" / "requests.jsonl")]
        import json
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8", newline="\n")
        result = self.cli("prepare", "--contract", str(self.contract_path), expected=2)
        self.assertEqual("RUN-ROOTS", result["code"])

    def test_history_resume_or_connect_is_refused_before_preparation(self):
        import json
        for flag in ("--resume", "--connect"):
            worker = self.worker("worker-1", "work-one")
            worker["argv"] += [flag, "native-id"]
            self.contract["workers"] = [worker]
            self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8", newline="\n")
            with self.subTest(flag=flag):
                result = self.cli("prepare", "--contract", str(self.contract_path), expected=2)
                self.assertEqual("RUN-COPILOT-PROFILE", result["code"])
                self.assertFalse((self.repo.parent / "repo-work-one").exists())


class CopilotModelEvidence(unittest.TestCase):
    def test_recorded_model_misrouting_cannot_pass_the_inference_gate(self):
        import json
        report = json.loads((SCRIPTS.parent / "evals/fixtures/copilot-windows-qualification.json").read_bytes())
        runner = load("coord-runner")
        session = "4d6e86b8-8568-42f2-aedc-382babbe513e"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session-state" / session / "events.jsonl"
            path.parent.mkdir(parents=True)
            records = [report["cases"]["positive"], *report["invalid_initial_runs"]]
            for record in records:
                rows = [{"type": "assistant.message", "data": {"model": model}}
                        for model in record["assistant_models"]]
                rows.append({"type": "session.usage_checkpoint", "data": {
                    "promptCacheBreakState": [{"models": {model: {} for model in record["usage_models"]}}]}})
                path.write_text("\n".join(map(json.dumps, rows)), encoding="utf-8", newline="\n")
                with self.subTest(status=record.get("status", "qualified")):
                    if record.get("status") == "INVALID":
                        with self.assertRaises(runner.Refused):
                            runner.copilot_model_evidence(session, {"COPILOT_HOME": directory}, "gpt-5.4")
                    else:
                        self.assertEqual(["gpt-5.4"], runner.copilot_model_evidence(
                            session, {"COPILOT_HOME": directory}, "gpt-5.4")["actual_models"])
        self.assertTrue(report["cases"]["lease"]["lease_refused"])
        self.assertTrue(report["cases"]["lease"]["leased_unchanged"])
        self.assertEqual("permission_denied", report["cases"]["denial"]["code"])
        self.assertEqual("READY", report["cases"]["cancel"]["work_marker"])
        self.assertEqual("ready_for_review", report["cases"]["owner_worker"]["state"])
        self.assertEqual("incomplete", report["cases"]["owner_decision"]["state"])

    def test_actual_models_require_assistant_and_usage_not_advertised_cache(self):
        import json
        runner = load("coord-runner")
        session = "4d6e86b8-8568-42f2-aedc-382babbe513e"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session-state" / session / "events.jsonl"
            path.parent.mkdir(parents=True)
            rows = [{"type": "assistant.message", "data": {"model": "gpt-5.4"}},
                    {"type": "session.usage_checkpoint", "data": {"modelCacheState": [],
                     "promptCacheBreakState": [{"models": {"gpt-5.4": {"model": "gpt-5.4"}}}]}}]
            path.write_text("\n".join(map(json.dumps, rows)), encoding="utf-8", newline="\n")
            env = {"COPILOT_HOME": directory}
            evidence = runner.copilot_model_evidence(session, env, "gpt-5.4")
            self.assertEqual(["gpt-5.4"], evidence["actual_models"])
            for bad in (rows[:1], [rows[0], {"type": "session.usage_checkpoint",
                                          "data": {"modelCacheState": [{"modelId": "gpt-5.4"}]}}],
                        [rows[0], {"type": "session.usage_checkpoint", "data": {
                            "promptCacheBreakState": [{"models": {"different-model": {}}}]}}]):
                path.write_text("\n".join(map(json.dumps, bad)), encoding="utf-8", newline="\n")
                with self.subTest(rows=bad), self.assertRaises(runner.Refused):
                    runner.copilot_model_evidence(session, env, "gpt-5.4")
            with self.assertRaises(runner.Refused):
                runner.copilot_model_evidence("../outside", env, "gpt-5.4")


@unittest.skipUnless(os.name == "nt", "Win32 native filesystem boundary")
class WindowsFiles(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.api = load("coord_files")

    def test_regular_read_is_bounded_and_holds_file_and_parent_identity(self):
        parent = self.root / "nested"
        parent.mkdir()
        path = parent / "receipt.json"
        path.write_bytes(b'{"receipt":true}')
        with self.api.open_regular(path) as stream:
            self.assertEqual(b'{"receipt":true}', stream.read())
            with self.assertRaises(OSError):
                path.rename(parent / "replaced")
            with self.assertRaises(OSError):
                parent.rename(self.root / "moved")
        self.assertEqual(b'{"receipt":true}', self.api.read_regular(path, 32))
        with self.assertRaises(ValueError):
            self.api.read_regular(path, 2)

    def test_junction_ancestor_is_refused_without_symlink_privilege(self):
        import subprocess
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "secret").write_bytes(b"secret")
        junction = self.root / "junction"
        result = subprocess.run(
            [os.environ["ComSpec"], "/d", "/c", "mklink", "/J", str(junction), str(outside)],
            capture_output=True, text=True, encoding="utf-8", timeout=5)
        self.assertEqual(0, result.returncode, result.stderr)
        self.addCleanup(junction.rmdir)
        with self.assertRaises((OSError, ValueError)):
            self.api.read_regular(junction / "secret", 32)

    def test_directory_and_missing_file_are_not_regular_receipts(self):
        for path in (self.root, self.root / "absent"):
            with self.subTest(path=path), self.assertRaises((OSError, ValueError)):
                self.api.read_regular(path, 32)

    def test_controls_run_on_windows_and_do_not_replay_or_grant_foreign_options(self):
        controls = load("coord_runtime").Controls(self.root / "controls")
        first = controls.enqueue("compiled-one", "abc", 1)
        controls.dispatched(first["id"])
        controls.finish()
        self.assertIs(controls.next_prompt(), False)
        with self.assertRaises(ValueError):
            controls.dispatched(first["id"])
        request = controls.permission(
            {"sessionId": "worker", "requestId": 7, "toolCall": {"title": "fixture"},
             "options": [{"optionId": "once", "kind": "allow_once"},
                         {"optionId": "forever", "kind": "allow_always"}]},
            expires_at=200)
        for option in ("foreign", "forever"):
            with self.subTest(option=option), self.assertRaises(ValueError):
                controls.decide(request["id"], option, now=100)
        controls.decide(request["id"], "once", now=100)
        self.assertEqual("once", controls.answer(request["id"], now=100))

    def test_controls_reject_tampered_record_and_have_protected_inherited_acl(self):
        import ctypes
        from ctypes import wintypes
        import json
        controls = load("coord_runtime").Controls(self.root / "controls")
        controls.enqueue("compiled-one", "abc", 1)
        path = controls.directory / "000001.json"
        api = ctypes.WinDLL("advapi32", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.LocalFree.argtypes = (wintypes.HLOCAL,)
        api.GetNamedSecurityInfoW.argtypes = (
            wintypes.LPWSTR, ctypes.c_int, wintypes.DWORD, wintypes.LPVOID,
            wintypes.LPVOID, wintypes.LPVOID, wintypes.LPVOID,
            ctypes.POINTER(wintypes.LPVOID))
        api.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = (
            wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD,
            ctypes.POINTER(wintypes.LPWSTR), wintypes.LPVOID)
        descriptor, text = wintypes.LPVOID(), wintypes.LPWSTR()
        try:
            self.assertEqual(0, api.GetNamedSecurityInfoW(
                str(controls.directory), 1, 4, None, None, None, None, ctypes.byref(descriptor)))
            self.assertTrue(api.ConvertSecurityDescriptorToStringSecurityDescriptorW(
                descriptor, 1, 4, ctypes.byref(text), None))
            self.assertTrue(text.value.startswith("D:P"), text.value)
            self.assertNotIn(";;;WD)", text.value)
            self.assertNotIn(";;;AU)", text.value)
        finally:
            if text:
                kernel.LocalFree(ctypes.cast(text, wintypes.HLOCAL))
            if descriptor:
                kernel.LocalFree(descriptor)
        value = json.loads(path.read_bytes())
        value["compilation_id"] = "forged"
        path.write_text(json.dumps(value), encoding="utf-8", newline="\n")
        with self.assertRaises(ValueError):
            controls.records()


if __name__ == "__main__":
    unittest.main()
