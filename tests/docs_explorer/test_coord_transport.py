"""AC5/AC6: real subprocess boundaries for the ACP / Agy process seam."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "pack/scripts/coord_transport.py"
PEER = Path(__file__).with_name("coord_transport_peer.py")


def load_module():
    spec = importlib.util.spec_from_file_location("coord_transport", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(os.name == "posix", "POSIX pilot; Windows admission tested separately")
class TransportTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.events = []

    def run_peer(self, mode="normal", **overrides):
        options = dict(transport="acp", argv=[sys.executable, str(PEER), mode, str(self.root)],
                       cwd=str(self.root), env=dict(os.environ), prompts=["first", "second"],
                       deadline_seconds=2, output_limit=64 * 1024, emit=self.events.append,
                       cancelled=lambda: False, before_prompt=lambda remaining: True)
        options.update(overrides)
        started = time.monotonic()
        result = self.module.run_session(**options)
        budget = options["deadline_seconds"] if 0 < options["deadline_seconds"] <= 3600 else 2
        self.assertLess(time.monotonic() - started, budget + 4.2)
        self.assertIsNone(result["cleanup_error"], result)
        return result

    def requests(self):
        path = self.root / "requests.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_runtime_mode_selects_only_advertised_fresh_mode_before_prompt(self):
        result = self.run_peer("mode_advertised", mode_id="read-only")
        self.assertEqual("complete", result["code"])
        requests = self.requests()
        methods = [r.get("method") for r in requests]
        self.assertLess(methods.index("session/set_mode"), methods.index("session/prompt"))
        self.assertEqual(1, methods.count("session/set_mode"))
        request = requests[methods.index("session/set_mode")]
        self.assertEqual({"sessionId": "acp-fixture", "modeId": "read-only"}, request["params"])
        self.assertIn("session_mode_selected", [event["event"] for event in self.events])

    def test_expected_model_match_mismatch_and_missing_gate_fresh_session(self):
        result = self.run_peer("model_match", expected_model="gpt-5.4")
        self.assertEqual(("complete", "gpt-5.4", True), (result["code"], result["selected_model"], result["selected_model_set"]))
        self.assertEqual(["initialize", "session/new", "session/set_model", "session/prompt", "session/prompt"],
                         [r.get("method") for r in self.requests()])
        created = next(event for event in self.events if event["event"] == "session_created")
        self.assertEqual("gpt-5.4", created["selected_model"])
        selected = next(event for event in self.events if event["event"] == "session_model_selected")
        self.assertEqual("gpt-5.4", selected["requested_model"])
        for mode in ("model_missing", "model_mismatch"):
            with self.subTest(mode=mode):
                self.events.clear()
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode, expected_model="gpt-5.4")
                self.assertEqual(("complete", 2, True), (result["code"], result["prompts_started"], result["selected_model_set"]))
                self.assertEqual(["initialize", "session/new", "session/set_model", "session/prompt", "session/prompt"],
                                 [r.get("method") for r in self.requests()])
        self.events.clear()
        (self.root / "requests.jsonl").unlink(missing_ok=True)
        result = self.run_peer("model_set_error", expected_model="gpt-5.4")
        self.assertEqual(("remote_error", 0, False), (result["code"], result["prompts_started"], result["selected_model_set"]))
        methods = [r.get("method") for r in self.requests()]
        self.assertEqual(["initialize", "session/new", "session/set_model"], methods[:3])
        self.assertIn(methods[3:], ([], ["session/cancel"]))

    def test_expected_model_invalid_or_incompatible_input_refuses_before_spawn(self):
        for options in ({"expected_model": True}, {"expected_model": ""}, {"expected_model": "gpt-5.4", "transport": "agy"},
                        {"expected_model": "gpt-5.4", "session_id": "acp-fixture"}):
            with self.subTest(options=options), mock.patch.object(self.module.subprocess, "Popen") as spawn:
                self.assertEqual("invalid_input", self.run_peer(**options)["code"])
                spawn.assert_not_called()

    def test_runtime_mode_unknown_unadvertised_malformed_and_error_do_not_prompt(self):
        for mode, code in (("normal", "unsupported_session_mode"), ("mode_unknown", "unsupported_session_mode"),
                           ("mode_duplicate", "unsupported_session_mode"), ("mode_malformed", "unsupported_session_mode"),
                           ("mode_error", "remote_error")):
            with self.subTest(mode=mode):
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode, mode_id="read-only")
                self.assertEqual((code, 0), (result["code"], result["prompts_started"]))
                self.assertFalse(any(r.get("method") == "session/prompt" for r in self.requests()))

    def test_runtime_mode_default_omitted_and_incompatible_input(self):
        self.assertEqual("complete", self.run_peer("mode_advertised")["code"])
        self.assertFalse(any(r.get("method") == "session/set_mode" for r in self.requests()))
        for options in ({"mode_id": True}, {"mode_id": ""}, {"mode_id": "read-only", "transport": "agy"},
                        {"mode_id": "read-only", "session_id": "acp-fixture"}):
            with self.subTest(options=options), mock.patch.object(self.module.subprocess, "Popen") as spawn:
                self.assertEqual("invalid_input", self.run_peer(**options)["code"])
                spawn.assert_not_called()

    def test_runtime_load_existing_session_preserves_identity_without_creation(self):
        for mode in ("load_matching", "load_omitted", "load_meta"):
            with self.subTest(mode=mode):
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode, session_id="acp-fixture", permission_handler=lambda *args: "once")
                self.assertEqual(("complete", 2, "acp-fixture"),
                                 (result["code"], result["turns_completed"], result["session_id"]))
                methods = [r.get("method") for r in self.requests()]
                self.assertNotIn("session/new", methods)
                request = next(r for r in self.requests() if r.get("method") == "session/load")
                self.assertEqual({"sessionId": "acp-fixture", "cwd": str(self.root), "mcpServers": []}, request["params"])
                self.assertIn("session_loaded", [e["event"] for e in self.events])

    def test_loaded_shared_session_is_never_cancelled_by_client_timeout(self):
        result = self.run_peer("load_prompt_hang", session_id="acp-fixture", deadline_seconds=.2)
        self.assertEqual(("deadline_exceeded", 1), (result["code"], result["prompts_started"]))
        self.assertNotIn("session/cancel", [r.get("method") for r in self.requests()])

    def test_runtime_load_rejects_capability_response_and_foreign_update(self):
        for mode, code in (("load_no_capability", "unsupported_session_load"),
                           ("load_false_capability", "unsupported_session_load"),
                           ("load_truthy_capability", "unsupported_session_load"),
                           ("load_mismatch", "protocol_error"), ("load_null", "protocol_error"),
                           ("load_error", "remote_error"), ("load_foreign_update", "protocol_error"),
                           ("load_meta_mismatch", "protocol_error"), ("load_permission", "protocol_error")):
            with self.subTest(mode=mode):
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode, session_id="acp-fixture", permission_handler=lambda *args: "once")
                self.assertEqual((code, 0), (result["code"], result["prompts_started"]))
                self.assertFalse(any(r.get("method") in ("session/new", "session/prompt") for r in self.requests()))
                self.assertEqual(0, result["permission_allowed"])

    def test_runtime_load_metadata_cwd_must_match_requested_directory(self):
        for mode, code in (("load_cwd_matching", "complete"), ("load_cwd_foreign", "protocol_error"),
                           ("load_cwd_null", "protocol_error")):
            with self.subTest(mode=mode):
                result = self.run_peer(mode, session_id="acp-fixture")
                self.assertEqual(code, result["code"])

    def test_runtime_load_timeout_never_cancels_existing_session_turn(self):
        result = self.run_peer("load_hang", session_id="acp-fixture", deadline_seconds=.15)
        self.assertEqual(("deadline_exceeded", 0), (result["code"], result["prompts_started"]))
        self.assertFalse((self.root / "cancel.received").exists())
        self.assertFalse(any(r.get("method") == "session/cancel" for r in self.requests()))

    def test_runtime_live_load_requires_verified_identity_and_cwd(self):
        for mode, code in (("load_cwd_matching", "complete"), ("load_omitted", "unverified_session_cwd"),
                           ("load_cwd_no_identity", "unverified_session_cwd")):
            with self.subTest(mode=mode):
                result = self.run_peer(mode, session_id="acp-fixture", require_loaded_cwd=True)
                self.assertEqual(code, result["code"])
                self.assertEqual(code == "complete", result["loaded_cwd_verified"])
        for options in ({"require_loaded_cwd": True}, {"require_loaded_cwd": 1},
                        {"require_loaded_cwd": True, "session_id": "valid", "transport": "agy"}):
            with self.subTest(options=options), mock.patch.object(self.module.subprocess, "Popen") as spawn:
                self.assertEqual("invalid_input", self.run_peer(**options)["code"])
                spawn.assert_not_called()

    def test_runtime_load_input_and_agy_and_roots_reject_before_spawn(self):
        for options, code in (({"session_id": ""}, "invalid_input"), ({"session_id": True}, "invalid_input"),
                              ({"session_id": "bad id"}, "invalid_input"),
                              ({"session_id": "valid", "transport": "agy"}, "unsupported_session_load"),
                              ({"session_id": "valid", "additional_roots": []}, "unsupported_file_roots")):
            with self.subTest(options=options), mock.patch.object(self.module.subprocess, "Popen") as spawn:
                result = self.run_peer(**options)
                self.assertEqual(code, result["code"])
                spawn.assert_not_called()

    def test_runtime_dynamic_prompts_wait_then_close_and_recheck_authority(self):
        for transport in ("acp", "agy"):
            with self.subTest(transport=transport):
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                choices = iter([None, "dynamic SECRET", False])
                fences = []
                result = self.run_peer(transport=transport, prompts=["first"], next_prompt=lambda remaining: next(choices),
                    before_prompt=lambda remaining: fences.append(remaining) or True)
                self.assertEqual(("complete", 2, 2), (result["code"], result["turns_completed"], result["prompts_started"]))
                self.assertEqual(2, len(fences))
                self.assertNotIn("SECRET", json.dumps([result, self.events]))

    def test_runtime_dynamic_refusal_never_sends_the_followup(self):
        fences = []
        result = self.run_peer(prompts=["first"], next_prompt=lambda remaining: "second",
            before_prompt=lambda remaining: fences.append(remaining) or len(fences) == 1)
        self.assertEqual(("dispatch_refused", 1), (result["code"], result["prompts_started"]))
        self.assertEqual(1, sum(r.get("method") == "session/prompt" for r in self.requests()))

    def test_runtime_mailbox_deadline_cancel_and_turn_limit(self):
        start = time.monotonic()
        result = self.run_peer(prompts=["first"], next_prompt=lambda remaining: None,
                               cancelled=lambda: time.monotonic() - start > .15)
        self.assertEqual(("cancelled", 1), (result["code"], result["turns_completed"]))
        result = self.run_peer(prompts=["first"], next_prompt=lambda remaining: None, deadline_seconds=.15)
        self.assertEqual("deadline_exceeded", result["code"])
        result = self.run_peer(prompts=["first"], next_prompt=lambda remaining: "extra", max_turns=1)
        self.assertEqual(("turn_limit_exceeded", 1), (result["code"], result["prompts_started"]))

    def test_runtime_once_approval_reaches_completion_and_preserves_private_identity(self):
        polls = []
        def decide(request, remaining):
            polls.append(request)
            return None if len(polls) < 3 else "once"
        result = self.run_peer("runtime_permission", prompts=["first"], permission_handler=decide)
        self.assertEqual(("complete", 1, 1, 0), (result["code"], result["permission_requests"],
                         result["permission_allowed"], result["permission_denials"]))
        self.assertEqual(3, len(polls))
        self.assertEqual(polls[0], polls[1])
        self.assertEqual({"sessionId", "requestId", "requestSequence", "options", "toolCall"}, set(polls[0]))
        self.assertEqual("permission-request", polls[0]["requestId"])
        self.assertNotIn("SECRET", json.dumps([result, self.events]))

    def test_runtime_reused_native_permission_id_gets_new_request_sequence(self):
        requests = []
        def decide(request, remaining):
            requests.append(request)
            return "once" if request["requestSequence"] == 1 else "reject"
        result = self.run_peer("runtime_permission", permission_handler=decide)
        self.assertEqual(("permission_denied", 1, 1, 1), (result["code"], result["turns_completed"],
                         result["permission_allowed"], result["permission_denials"]))
        self.assertEqual([1, 2], [r["requestSequence"] for r in requests])
        self.assertEqual(requests[0]["requestId"], requests[1]["requestId"])

    def test_runtime_permission_reject_unknown_persistent_and_mutated_options(self):
        for decision, code in (("reject", "permission_denied"), ("allow", "permission_decision_invalid"),
                               ("unknown", "permission_decision_invalid"), (True, "permission_decision_invalid")):
            with self.subTest(decision=decision):
                result = self.run_peer("runtime_permission", permission_handler=lambda request, remaining: decision)
                self.assertEqual((code, 0), (result["code"], result["turns_completed"]))
        def tamper(request, remaining):
            request["options"].append({"optionId": "injected", "kind": "allow_once"})
            return "injected"
        self.assertEqual("permission_decision_invalid", self.run_peer("runtime_permission", permission_handler=tamper)["code"])
        calls = []
        result = self.run_peer("runtime_permission_duplicate", permission_handler=lambda *args: calls.append(args))
        self.assertEqual(("protocol_error", []), (result["code"], calls))

    def test_runtime_permission_wait_retains_deadline_cancel_and_output_bound(self):
        result = self.run_peer("runtime_permission", permission_handler=lambda *args: None, deadline_seconds=.15)
        self.assertEqual("deadline_exceeded", result["code"])
        start = time.monotonic()
        result = self.run_peer("runtime_permission", permission_handler=lambda *args: None,
                               cancelled=lambda: time.monotonic() - start > .15)
        self.assertEqual("cancelled", result["code"])
        replies = [r for r in self.requests() if r.get("id") == "permission-request" and "result" in r]
        self.assertTrue(any(r["result"]["outcome"] == {"outcome": "cancelled"} for r in replies))
        # RUN-A: output past the bound is marked, not fatal; the deadline still ends a flood.
        result = self.run_peer("runtime_permission_flood", permission_handler=lambda *args: None, output_limit=4096,
                               deadline_seconds=.3)
        self.assertEqual(("deadline_exceeded", True), (result["code"], result["output_truncated"]))

    def test_runtime_callback_failure_and_prompt_started_retry_floor(self):
        def broken(*args):
            raise RuntimeError("SECRET")
        for options in ({"next_prompt": broken}, {"permission_handler": broken}):
            with self.subTest(options=options):
                mode = "runtime_permission" if "permission_handler" in options else "normal"
                result = self.run_peer(mode, prompts=["first"], **options)
                self.assertEqual(("callback_failed", 1), (result["code"], result["prompts_started"]))
                self.assertNotIn("SECRET", json.dumps(result))
        def broken_event(event):
            if event["event"] == "prompt_started":
                raise RuntimeError("SECRET")
        result = self.run_peer(emit=broken_event)
        self.assertEqual(("callback_failed", 1), (result["code"], result["prompts_started"]))

    def test_runtime_agy_ask_and_invalid_callbacks_refuse_before_spawn(self):
        for options, code in (({"transport": "agy", "permission_handler": lambda *a: None}, "unsupported_permission_handler"),
                              ({"next_prompt": 1}, "invalid_input"), ({"permission_handler": 1}, "invalid_input"),
                              ({"max_turns": True}, "invalid_input"), ({"max_turns": 9}, "invalid_input")):
            with self.subTest(options=options), mock.patch.object(self.module.subprocess, "Popen") as spawn:
                result = self.run_peer(**options)
                self.assertEqual(code, result["code"])
                spawn.assert_not_called()

    def test_runtime_dynamic_input_schema_size_and_slow_callback(self):
        for value, code in ((True, "invalid_dynamic_prompt"), ("", "invalid_dynamic_prompt"),
                            ({}, "invalid_dynamic_prompt"), ("x" * (self.module.MAX_INPUT_BYTES + 1), "input_limit_exceeded")):
            with self.subTest(code=code, kind=type(value).__name__):
                result = self.run_peer(prompts=["first"], next_prompt=lambda remaining: value)
                self.assertEqual((code, 1), (result["code"], result["prompts_started"]))
        def slow(remaining):
            time.sleep(.2)
            return "late"
        result = self.run_peer(prompts=["first"], deadline_seconds=.15, next_prompt=slow)
        self.assertEqual(("deadline_exceeded", 1), (result["code"], result["prompts_started"]))

    def test_runtime_pending_event_failure_cancels_native_request(self):
        def fail(event):
            if event["event"] == "permission_pending":
                raise RuntimeError("SECRET")
        result = self.run_peer("runtime_permission", prompts=["first"], emit=fail, permission_handler=lambda *args: "once")
        self.assertEqual(("callback_failed", 1, 0), (result["code"], result["prompts_started"], result["permission_allowed"]))
        reply = next(r for r in self.requests() if r.get("id") == "permission-request" and "result" in r)
        self.assertEqual({"outcome": "cancelled"}, reply["result"]["outcome"])

    def test_runtime_cleanup_never_flushes_queued_prompt(self):
        pending = []
        original = self.module._Wire.queue
        def queue_then_cancel(wire, message):
            original(wire, message)
            if message.get("method") == "session/prompt":
                pending.append(True)
        with mock.patch.object(self.module._Wire, "queue", queue_then_cancel):
            result = self.run_peer(prompts=["first"], cancelled=lambda: bool(pending))
        self.assertEqual(("cancelled", 1), (result["code"], result["prompts_started"]))
        self.assertFalse(any(r.get("method") == "session/prompt" for r in self.requests()))
    def test_runtime_cleanup_never_flushes_queued_approval(self):
        def broken_observer(event):
            if event["event"] == "permission_allowed":
                raise RuntimeError("SECRET")
        result = self.run_peer("runtime_permission", prompts=["first"], permission_handler=lambda *a: "once", emit=broken_observer)
        self.assertEqual("callback_failed", result["code"])
        self.assertFalse(any(r.get("result", {}).get("outcome", {}).get("optionId") == "once" for r in self.requests()))

    def test_acp_two_turns_progress_and_no_raw_output(self):
        result = self.run_peer()
        self.assertEqual(("complete", "complete", 2),
                         (result["outcome"], result["code"], result["turns_completed"]))
        self.assertEqual("acp-fixture", result["session_id"])
        self.assertEqual("1.2.3", result["reported_version"])
        self.assertGreater(result["stdout_bytes"], 0)
        methods = [row.get("method") for row in self.requests()]
        self.assertEqual(["initialize", "session/new", "session/prompt", "session/prompt"], methods)
        self.assertEqual({}, self.requests()[0]["params"]["clientCapabilities"])
        self.assertTrue(any(row["event"] == "progress" for row in self.events))
        self.assertNotIn("SECRET", json.dumps([result, self.events]))
        self.assertNotIn("additionalDirectories", self.requests()[1]["params"])

    def test_explicit_file_roots_forwarded_and_permission_denial_preserved(self):
        path = self.root.resolve() / "ledger.jsonl"
        path.touch()
        for mode, code, turns in (("roots_ok", "complete", 2), ("roots_permission", "permission_denied", 0)):
            with self.subTest(mode=mode):
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode, additional_roots=[str(path)])
                self.assertEqual((code, turns), (result["code"], result["turns_completed"]))
                self.assertEqual([str(path)], self.requests()[1]["params"]["additionalDirectories"])

    def test_file_roots_require_codex_identity_and_advertised_capability(self):
        path = self.root.resolve() / "ledger.jsonl"
        path.touch()
        for mode in ("normal", "roots_no_capability"):
            with self.subTest(mode=mode):
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode, additional_roots=[str(path)])
                self.assertEqual("unsupported_file_roots", result["code"])
                self.assertEqual(["initialize"], [r["method"] for r in self.requests()])

    def test_file_replacement_during_admission_prevents_prompt(self):
        path = self.root.resolve() / "ledger.jsonl"
        for phase in (1, 2):
            (self.root / "requests.jsonl").unlink(missing_ok=True)
            path.touch()
            calls = []
            def replace(remaining):
                calls.append(remaining)
                if len(calls) == phase:
                    path.rename(path.with_suffix(".old"))
                    path.touch()
                return True
            with self.subTest(phase=phase):
                result = self.run_peer("roots_ok", additional_roots=[str(path)], before_prompt=replace)
                self.assertEqual(("file_roots_changed", phase - 1), (result["code"], result["turns_completed"]))
                self.assertEqual(phase - 1, sum(r.get("method") == "session/prompt" for r in self.requests()))

    def test_invalid_file_roots_refuse_before_spawn(self):
        path = self.root.resolve() / "ledger.jsonl"
        path.touch()
        link = path.with_suffix(".link")
        link.symlink_to(path)
        for value in (False, "bad", [str(path.parent)], [str(link)], [str(path)] * 4,
                      [str(path), str(path)], [str(path.parent / "missing")], ["relative"]):
            with self.subTest(value=value):
                result = self.run_peer("roots_ok", additional_roots=value)
                self.assertEqual("invalid_file_roots", result["code"])
                self.assertEqual([], self.requests())

    def test_agy_observed_snake_case_wire_shape_and_two_turns(self):
        result = self.run_peer(transport="agy")
        self.assertEqual(("complete", "agy-fixture", 2),
                         (result["outcome"], result["session_id"], result["turns_completed"]))
        self.assertEqual([{"event": "user", "message": {"content": text}} for text in ("first", "second")], self.requests())
        self.assertNotIn("SECRET", json.dumps([result, self.events]))

    def test_agy_duplicate_result_cannot_complete_an_unsent_prompt(self):
        result = self.run_peer("agy_duplicate", transport="agy")
        self.assertEqual(("protocol_error", 1), (result["code"], result["turns_completed"]))
        self.assertEqual(1, len(self.requests()))

    def test_recorded_acp_extensions_do_not_replace_responses_or_leak(self):
        result = self.run_peer("extensions")
        self.assertEqual(("complete", 2, 12), (result["code"], result["turns_completed"], result["extension_notifications"]))
        self.assertEqual(["initialize", "session/new", "session/prompt", "session/prompt"],
                         [r.get("method") for r in self.requests()])
        self.assertNotIn("SECRET", json.dumps([result, self.events]))

    def test_grok_recorded_early_updates_bind_before_ordered_prompts(self):
        for mode, progress in (("grok_early", 3), ("grok_multiple", 5)):
            with self.subTest(mode=mode):
                self.events.clear()
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode)
                self.assertEqual(("complete", "acp-fixture", 2, progress, 6), (
                    result["code"], result["session_id"], result["turns_completed"],
                    result["progress_updates"], result["extension_notifications"]))
                self.assertEqual(["initialize", "authenticate", "session/new", "session/prompt", "session/prompt"],
                                 [row.get("method") for row in self.requests()])
                self.assertEqual("session_created", self.events[0]["event"])
                self.assertEqual("progress", self.events[1]["event"])
                self.assertNotIn("SECRET", json.dumps([result, self.events]))

    def test_grok_early_updates_require_one_valid_identity_and_phase(self):
        for mode in ("grok_initialize", "grok_authenticate", "grok_missing_id", "grok_empty_id", "grok_long_id",
                     "grok_bad_update", "grok_missing_discriminator", "grok_bad_discriminator", "grok_changed", "grok_mismatch"):
            with self.subTest(mode=mode):
                self.events.clear()
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode)
                self.assertEqual(("protocol_error", None, 0, 0), (result["code"], result["session_id"],
                                  result["turns_completed"], result["progress_updates"]))
                self.assertFalse(any(row.get("method") == "session/prompt" for row in self.requests()))
                self.assertFalse(any(row["event"] == "session_created" for row in self.events))

    def test_grok_early_updates_never_replace_creation_response(self):
        for mode, code in (("grok_eof", "early_eof"), ("grok_error", "remote_error"), ("grok_hang", "deadline_exceeded")):
            with self.subTest(mode=mode):
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode, deadline_seconds=.25)
                self.assertEqual((code, None, 0), (result["code"], result["session_id"], result["progress_updates"]))
                self.assertFalse(any(row.get("method") == "session/prompt" for row in self.requests()))

    def test_grok_candidate_or_missing_identity_never_authorizes_permissions(self):
        for mode in ("grok_permission_missing", "grok_permission_null", "grok_permission_candidate"):
            with self.subTest(mode=mode):
                self.events.clear()
                result = self.run_peer(mode)
                self.assertEqual(("protocol_error", 0, 0), (result["code"], result["permission_requests"], result["turns_completed"]))
                self.assertFalse(any(row["event"] == "permission_denied" for row in self.events))

    def test_grok_early_flood_retains_byte_deadline_and_cancel_limits(self):
        result = self.run_peer("grok_flood", output_limit=2048, deadline_seconds=.3)
        self.assertEqual(("deadline_exceeded", True, None), (result["code"], result["output_truncated"], result["session_id"]))
        start = time.monotonic()
        result = self.run_peer("grok_flood", output_limit=16 * 1024 * 1024,
                               cancelled=lambda: time.monotonic() - start > .1)
        self.assertEqual("cancelled", result["code"])
        self.assertEqual((None, 0), (result["session_id"], result["progress_updates"]))

    def test_watcher_exact_grok_response_never_completes_the_pending_prompt(self):
        result = self.run_peer("watcher_match")
        self.assertEqual(("complete", 2, 2, "1.0.34", "grok._meta.agentVersion"), (
            result["code"], result["turns_completed"], result["compatibility_responses"],
            result["reported_version"], result["reported_version_source"]))
        self.assertEqual(2, sum(row.get("method") == "session/prompt" for row in self.requests()))

    def test_watcher_exact_grok_response_is_accepted_on_a_later_release(self):
        # Measured 2026-09-24 on grok 1.0.41 (Windows, x-harness-x-model-bench qualify-4): the identical
        # skills-reload response arrives inside session/prompt. 1.0.34-only pinning failed every newer grok.
        result = self.run_peer("watcher_later_version")
        self.assertEqual(("complete", 2, 2, "1.0.41"), (
            result["code"], result["turns_completed"], result["compatibility_responses"], result["reported_version"]))

    def test_watcher_other_profile_phase_shape_and_ids_remain_rejected(self):
        for suffix in ("early", "other_version", "prerelease_version", "no_shell", "string_shell", "agentinfo_only",
                       "extra", "inner_extra", "bool", "float", "other_id", "bad_result"):
            with self.subTest(suffix=suffix):
                result = self.run_peer("watcher_" + suffix)
                self.assertEqual(("protocol_error", 0, 0), (
                    result["code"], result["turns_completed"], result["compatibility_responses"]))
                self.assertNotIn("SECRET", json.dumps([result, self.events]))

    def test_watcher_acknowledgement_alone_cannot_credit_a_turn(self):
        result = self.run_peer("watcher_hang", deadline_seconds=.25)
        self.assertEqual(("deadline_exceeded", 0, 1), (
            result["code"], result["turns_completed"], result["compatibility_responses"]))

    def test_watcher_compatibility_responses_share_attempt_resource_limits(self):
        # RUN-A: a flood past the byte bound is marked and ended by the deadline, never credited as a turn.
        result = self.run_peer("watcher_flood", output_limit=2048, deadline_seconds=.3)
        self.assertEqual(("deadline_exceeded", True, 0), (result["code"], result["output_truncated"], result["turns_completed"]))
        start = time.monotonic()
        result = self.run_peer("watcher_flood", output_limit=16 * 1024 * 1024,
                               cancelled=lambda: time.monotonic() - start > .1)
        self.assertEqual("cancelled", result["code"])

    def test_extension_requests_still_receive_method_not_found(self):
        result = self.run_peer("extension_request", prompts=["first"])
        self.assertEqual("complete", result["code"])
        reply = next(r for r in self.requests() if r.get("id") == "unknown-request")
        self.assertEqual(-32601, reply["error"]["code"])
        result = self.run_peer("extension_params", prompts=["first"])
        self.assertEqual(("complete", 9), (result["code"], result["extension_notifications"]))

    def test_extension_envelopes_and_session_updates_remain_validated(self):
        for mode in ("bad_extension_params", "bad_extension_null", "bad_extension_result", "bad_extension_error",
                     "bad_extension_id", "bad_extension_standard", "foreign_update"):
            with self.subTest(mode=mode):
                self.assertEqual("protocol_error", self.run_peer(mode)["code"])

    def test_extension_flood_retains_output_and_cancellation_bounds(self):
        # RUN-A: extension notifications are counted apart from the byte bound; the deadline ends a flood.
        result = self.run_peer("extension_flood", output_limit=2048, deadline_seconds=.3)
        self.assertEqual(("deadline_exceeded", False), (result["code"], result["output_truncated"]))
        self.assertGreater(result["extension_notification_bytes"], 2048)
        started = time.monotonic()
        result = self.run_peer("extension_flood", output_limit=16 * 1024 * 1024,
                               cancelled=lambda: time.monotonic() - started > .08)
        self.assertEqual("cancelled", result["code"])

    def test_native_agy_denial_blocks_all_later_prompts(self):
        for mode in ("agy_denied", "agy_permission_step"):
            with self.subTest(mode=mode):
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode, transport="agy")
                self.assertEqual(("blocked", "permission_denied", 1, 0, 0),
                    (result["outcome"], result["code"], result["native_denials"], result["permission_requests"], result["turns_completed"]))
                self.assertEqual(1, len(self.requests()))
                self.assertTrue(any(e["event"] == "native_permission_denied" and e.get("action_id") for e in self.events))
                self.assertNotIn("SECRET", json.dumps([result, self.events]))

    def test_native_agy_errors_and_malformed_denials_cannot_complete(self):
        for mode, code in [("agy_error_step", "native_tool_error"), ("agy_foreign_step", "protocol_error"),
                           ("agy_missing_error_id", "protocol_error"), ("agy_preinit_error", "protocol_error")] + [
                ("agy_malformed_denials_" + str(i), "protocol_error") for i in range(5)]:
            with self.subTest(mode=mode):
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode, transport="agy")
                self.assertEqual((code, 0), (result["code"], result["turns_completed"]))
                self.assertEqual(1, len(self.requests()))
                self.assertEqual(0, result["native_denials"])
        self.assertEqual("complete", self.run_peer("agy_empty_denials", transport="agy")["code"])

    def test_progress_is_counted_but_durable_events_are_coalesced(self):
        result = self.run_peer("progress_flood", prompts=["first"])
        self.assertEqual("complete", result["code"])
        self.assertEqual(101, result["progress_updates"])
        self.assertEqual(1, sum(row["event"] == "progress" for row in self.events))

    def test_cached_auth_only_and_native_auth_failure_is_explicit(self):
        result = self.run_peer("auth")
        self.assertEqual("complete", result["code"])
        request = next(row for row in self.requests() if row.get("method") == "authenticate")
        self.assertEqual("cached_token", request["params"]["methodId"])
        result = self.run_peer("auth_required")
        self.assertEqual("authentication_required", result["code"])
        self.assertNotIn("SECRET", json.dumps(result))

    def test_unknown_server_request_is_method_not_found(self):
        result = self.run_peer("unknown_request", prompts=["first"])
        self.assertEqual("complete", result["code"])
        reply = next(row for row in self.requests() if row.get("id") == "unknown-request")
        self.assertEqual(-32601, reply["error"]["code"])

    def test_permission_denial_sticks_even_after_end_turn(self):
        for mode in ("permission", "permission_no_reject"):
            with self.subTest(mode=mode):
                (self.root / "requests.jsonl").unlink(missing_ok=True)
                result = self.run_peer(mode)
                self.assertEqual(("blocked", "permission_denied", 1, 0), (
                    result["outcome"], result["code"], result["permission_requests"], result["turns_completed"]))
                requests = self.requests()
                self.assertEqual(1, sum(row.get("method") == "session/prompt" for row in requests))
                reply = next(row for row in requests if row.get("id") == "permission-request")
                expected = {"outcome": "selected", "optionId": "reject"} if mode == "permission" else {"outcome": "cancelled"}
                self.assertEqual(expected, reply["result"]["outcome"])
                self.assertTrue(any(row.get("action_id") for row in self.events))

    def test_other_terminal_reasons_are_not_complete(self):
        for mode, transport in (("max_tokens", "acp"), ("agy_failure", "agy")):
            with self.subTest(mode=mode):
                result = self.run_peer(mode, transport=transport)
                self.assertEqual("incomplete", result["code"])
                self.assertEqual(0, result["turns_completed"])

    def test_invalid_unknown_wrong_response_and_eof(self):
        for mode, code in (("malformed", "protocol_error"), ("unknown", "protocol_error"),
                           ("invalid_utf8", "protocol_error"), ("partial_eof", "protocol_error"),
                           ("wrong_id", "protocol_error"), ("early_eof", "early_eof")):
            with self.subTest(mode=mode):
                self.assertEqual(code, self.run_peer(mode)["code"])

    def test_stdout_stderr_and_unterminated_floods_are_bounded(self):
        # RUN-A: the output bound marks, it never fails. Memory is bounded by the unparsed buffer (one
        # unterminated frame), and time by the deadline. The buffer bound is lowered here to keep the test fast.
        self.module.MAX_BUFFER_BYTES = 64 * 1024
        for mode, code in (("stdout_flood", "buffer_limit_exceeded"), ("stderr_flood", "deadline_exceeded"),
                           ("both_flood", "buffer_limit_exceeded")):
            with self.subTest(mode=mode):
                result = self.run_peer(mode, output_limit=8192, deadline_seconds=.5)
                self.assertEqual((code, True), (result["code"], result["output_truncated"]))
                self.assertLessEqual(result["stdout_bytes"], 2 * 64 * 1024)

    def test_blocked_input_and_hung_response_share_finite_deadline(self):
        for mode, transport, prompts in (("blocked_stdin", "agy", ["x" * 1024 * 1024]), ("hang", "acp", ["first"])):
            with self.subTest(mode=mode):
                result = self.run_peer(mode, transport=transport, prompts=prompts, deadline_seconds=.2)
                self.assertEqual("deadline_exceeded", result["code"])

    def test_cancellation_sends_acp_cancel_and_stops_remaining_prompts(self):
        start = time.monotonic()
        result = self.run_peer("hang", cancelled=lambda: time.monotonic() - start > .15)
        self.assertEqual("cancelled", result["code"])
        self.assertTrue((self.root / "cancel.received").exists())

    def test_before_prompt_refusal_and_elapsed_deadline_block_dispatch(self):
        calls = []
        def admission(remaining):
            calls.append(remaining)
            return len(calls) == 1
        result = self.run_peer(before_prompt=admission)
        self.assertEqual(("dispatch_refused", 1), (result["code"], result["turns_completed"]))
        self.assertEqual(2, len(calls))
        self.assertLess(calls[1], calls[0])
        (self.root / "requests.jsonl").unlink()
        def delayed(remaining):
            time.sleep(.25)
            return True
        result = self.run_peer(before_prompt=delayed, deadline_seconds=.2)
        self.assertEqual("deadline_exceeded", result["code"])
        self.assertFalse(any(row.get("method") == "session/prompt" for row in self.requests()))

    def test_owned_descendant_is_killed_even_when_it_ignores_term(self):
        for mode, code in (("descendant", "deadline_exceeded"), ("exited_parent", "early_eof"),
                           ("complete_descendant", "complete")):
            with self.subTest(mode=mode):
                (self.root / "child.ready").unlink(missing_ok=True)
                result = self.run_peer(mode, deadline_seconds=.4)
                self.assertEqual(code, result["code"])
                self.assertTrue((self.root / "child.ready").exists())
                pid = (self.root / "child.pid").read_text()
                status = subprocess.run(["ps", "-o", "stat=", "-p", pid], capture_output=True, text=True, timeout=2)
                self.assertTrue(not status.stdout.strip() or status.stdout.strip().startswith("Z"), status.stdout)

    def test_deadline_is_one_budget_for_all_turns(self):
        result = self.run_peer("slow_turn", deadline_seconds=.27)
        self.assertEqual(("deadline_exceeded", 1), (result["code"], result["turns_completed"]))

    def test_agy_cancellation_uses_process_termination(self):
        start = time.monotonic()
        result = self.run_peer("hang", transport="agy", cancelled=lambda: time.monotonic() - start > .15)
        self.assertEqual("cancelled", result["code"])
        self.assertFalse((self.root / "cancel.received").exists())

    def test_exact_output_budget_and_one_byte_over(self):
        result = self.run_peer(prompts=["first"])
        count = result["stdout_bytes"] + result["stderr_bytes"]
        result = self.run_peer(prompts=["first"], output_limit=count)
        self.assertEqual(("complete", False, 0), (result["code"], result["output_truncated"], result["output_bytes_over_limit"]))
        result = self.run_peer(prompts=["first"], output_limit=count - 1)
        self.assertEqual(("complete", True, 1), (result["code"], result["output_truncated"], result["output_bytes_over_limit"]))

    # RUN-A, run w1-s1 (x-harness-x-model-bench, 2026-09-24): grok 1.0.41 had committed all 7 commits of its
    # slice when the transport failed it at 906 s with output_limit_exceeded (16776903 stdout + 314 stderr
    # bytes, 526 extension notifications). An output bound must never fail a working attempt.
    def test_output_past_the_bound_is_marked_truncated_and_never_fails_the_attempt(self):
        limit = 16 * 1024 * 1024  # the maximum, as in w1-s1
        result = self.run_peer("long_slice", prompts=["first"], output_limit=limit, deadline_seconds=60)
        self.assertEqual(("complete", 1), (result["code"], result["turns_completed"]))
        self.assertEqual((526, 314), (result["extension_notifications"], result["stderr_bytes"]))
        self.assertGreaterEqual(result["progress_updates"], 3138)
        charged = result["stdout_bytes"] + result["stderr_bytes"] - result["extension_notification_bytes"]
        self.assertGreater(charged, limit)
        self.assertEqual((True, charged - limit), (result["output_truncated"], result["output_bytes_over_limit"]))

    def test_extension_notifications_are_counted_apart_from_the_output_bound(self):
        result = self.run_peer("extension_burst", prompts=["first"])  # 526 notifications of about 4 KiB, 64 KiB bound
        self.assertEqual(("complete", 526, False, 0), (result["code"], result["extension_notifications"],
                                                      result["output_truncated"], result["output_bytes_over_limit"]))
        self.assertGreater(result["extension_notification_bytes"], 64 * 1024)
        self.assertGreater(result["stdout_bytes"], 64 * 1024)

    def test_invalid_bounds_and_cancelled_admission_do_not_spawn(self):
        for values in ({"prompts": []}, {"prompts": ["x"] * 9}, {"output_limit": 0},
                       {"deadline_seconds": float("nan")}, {"deadline_seconds": 0},
                       {"cancelled": lambda: True}):
            with self.subTest(values=values), mock.patch.object(self.module.subprocess, "Popen") as spawn:
                result = self.run_peer(**values)
                self.assertNotEqual("complete", result["code"])
                spawn.assert_not_called()

    def test_spawn_and_callback_failures_are_sanitized(self):
        result = self.run_peer(argv=[str(self.root / "missing-SECRET")])
        self.assertEqual("spawn_failed", result["code"])
        def fail(_):
            raise RuntimeError("SECRET")
        result = self.run_peer(before_prompt=fail)
        self.assertEqual("callback_failed", result["code"])
        self.assertNotIn("SECRET", json.dumps(result))

    def test_pipe_setup_failure_reaps_the_real_child(self):
        original_spawn = self.module.subprocess.Popen
        processes = []
        def spawn(*args, **kwargs):
            child = original_spawn(*args, **kwargs)
            processes.append(child)
            return child
        with mock.patch.object(self.module.subprocess, "Popen", side_effect=spawn), mock.patch.object(
                self.module.os, "set_blocking", side_effect=OSError("SECRET")):
            result = self.run_peer()
        self.assertEqual("io_error", result["code"])
        self.assertEqual(1, len(processes))
        self.assertIsNotNone(processes[0].poll())
        self.assertTrue(all(stream.closed for stream in (processes[0].stdin, processes[0].stdout, processes[0].stderr)))

    def test_exit_between_poll_and_signal_rechecks_macos_zombie_error(self):
        original = self.module.os.killpg
        calls = []
        def signal_group(pid, sig):
            calls.append(sig)
            if len(calls) == 1:
                raise PermissionError("simulated macOS exit race")
            return original(pid, sig)
        with mock.patch.object(self.module.os, "killpg", side_effect=signal_group):
            result = self.run_peer("early_eof")
        self.assertEqual("early_eof", result["code"])

    def test_input_frame_limit_and_empty_prompt_refuse(self):
        result = self.run_peer(transport="agy", prompts=["x" * (self.module.MAX_INPUT_BYTES + 1)])
        self.assertEqual("input_limit_exceeded", result["code"])
        self.assertEqual("invalid_input", self.run_peer(prompts=[""])["code"])
        # Non-ASCII serialization can exceed the frame cap despite fewer characters.
        result = self.run_peer(transport="agy", prompts=["\U0001f600" * (self.module.MAX_INPUT_BYTES // 4)])
        self.assertEqual("input_limit_exceeded", result["code"])

    def test_unknown_platform_refuses_before_subprocess(self):
        with mock.patch.object(self.module.os, "name", "java"), mock.patch.object(self.module.subprocess, "Popen") as spawn:
            result = self.run_peer()
        self.assertEqual("unsupported_platform", result["code"])
        spawn.assert_not_called()


@unittest.skipUnless(os.name == "nt", "POSIX executes the same contract methods above")
class SharedTransportContractsOnWindows(unittest.TestCase):
    setUp = TransportTests.setUp
    run_peer = TransportTests.run_peer
    requests = TransportTests.requests
    test_model_selection_contract = TransportTests.test_expected_model_match_mismatch_and_missing_gate_fresh_session
    test_watcher_matching_contract = TransportTests.test_watcher_exact_grok_response_never_completes_the_pending_prompt
    test_watcher_resource_contract = TransportTests.test_watcher_compatibility_responses_share_attempt_resource_limits
    # RUN-A: the runner that failed w1-s1 ran on this wire (_ThreadedWire), so the bound contract runs here too.
    test_output_bound_contract = TransportTests.test_output_past_the_bound_is_marked_truncated_and_never_fails_the_attempt
    test_extension_bound_contract = TransportTests.test_extension_notifications_are_counted_apart_from_the_output_bound
    test_exact_bound_contract = TransportTests.test_exact_output_budget_and_one_byte_over
    test_flood_bound_contract = TransportTests.test_stdout_stderr_and_unterminated_floods_are_bounded


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(os.name == "nt", "Windows transport proof")
class TestWindowsTransport(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.events = []

    def run_peer(self, mode="normal", **overrides):
        options = dict(transport="acp", argv=[sys.executable, str(PEER), mode, str(self.root)],
                       cwd=str(self.root), env=dict(os.environ), prompts=["first", "second"],
                       deadline_seconds=2, output_limit=64 * 1024, emit=self.events.append,
                       cancelled=lambda: False, before_prompt=lambda remaining: True)
        options.update(overrides)
        started = time.monotonic()
        result = self.module.run_session(**options)
        budget = options["deadline_seconds"] if 0 < options["deadline_seconds"] <= 3600 else 2
        self.assertLess(time.monotonic() - started, budget + 4.2)
        self.assertIsNone(result["cleanup_error"], result)
        return result

    def requests(self):
        path = self.root / "requests.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_windows_blocked_input_and_hung_response_share_finite_deadline(self):
        for mode, transport, prompts in (("blocked_stdin", "agy", ["x" * 1024 * 1024]), ("hang", "acp", ["first"])):
            with self.subTest(mode=mode):
                result = self.run_peer(mode, transport=transport, prompts=prompts, deadline_seconds=.2)
                self.assertEqual("deadline_exceeded", result["code"])

    def test_windows_pending_permission_cancel_emits_cancelled_reply(self):
        start = time.monotonic()
        result = self.run_peer("runtime_permission", permission_handler=lambda *args: None,
                               cancelled=lambda: time.monotonic() - start > .15)
        self.assertEqual("cancelled", result["code"])
        replies = [r for r in self.requests() if r.get("id") == "permission-request" and "result" in r]
        self.assertTrue(any(r["result"]["outcome"] == {"outcome": "cancelled"} for r in replies))

    def test_windows_pre_and_post_prompt_eof_do_not_replay(self):
        early = self.run_peer("early_eof")
        self.assertEqual(("early_eof", 0), (early["code"], early["prompts_started"]))
        result = self.run_peer("post_prompt_eof", prompts=["first"])
        self.assertEqual(("early_eof", 1, 0), (result["code"], result["prompts_started"], result["turns_completed"]))
        self.assertEqual(1, sum(r.get("method") == "session/prompt" for r in self.requests()))

    def test_windows_interleaved_stdout_and_stderr_remain_protocol_safe(self):
        result = self.run_peer("stderr_interleaved")
        self.assertEqual(("complete", 2), (result["code"], result["turns_completed"]))
        self.assertGreater(result["stderr_bytes"], 0)

    def test_windows_owned_descendant_is_killed_even_when_parent_exits(self):
        for mode, code in (("descendant", "deadline_exceeded"), ("exited_parent", "early_eof"),
                           ("complete_descendant", "complete")):
            with self.subTest(mode=mode):
                (self.root / "child.ready").unlink(missing_ok=True)
                result = self.run_peer(mode, deadline_seconds=.4)
                self.assertEqual(code, result["code"])
                self.assertTrue((self.root / "child.ready").exists())
                pid = int((self.root / "child.pid").read_text())
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline and self._process_exists(pid):
                    time.sleep(0.05)
                self.assertFalse(self._process_exists(pid))

    def test_windows_expected_model_requires_setter_before_prompt(self):
        result = self.run_peer("model_match", expected_model="gpt-5.4")
        self.assertEqual(("complete", "gpt-5.4", True), (result["code"], result["selected_model"], result["selected_model_set"]))
        self.assertEqual(["initialize", "session/new", "session/set_model", "session/prompt", "session/prompt"],
                         [r.get("method") for r in self.requests()])

    @staticmethod
    def _process_exists(pid):
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
