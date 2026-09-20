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
        self.assertEqual("output_limit_exceeded", self.run_peer("extension_flood", output_limit=2048)["code"])
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
        for mode in ("stdout_flood", "stderr_flood", "both_flood"):
            with self.subTest(mode=mode):
                result = self.run_peer(mode, output_limit=8192)
                self.assertEqual("output_limit_exceeded", result["code"])
                self.assertLessEqual(result["stdout_bytes"] + result["stderr_bytes"], 8193)

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
        self.assertEqual("complete", self.run_peer(prompts=["first"], output_limit=count)["code"])
        self.assertEqual("output_limit_exceeded", self.run_peer(prompts=["first"], output_limit=count - 1)["code"])

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

    def test_windows_refuses_before_subprocess(self):
        with mock.patch.object(self.module.os, "name", "nt"), mock.patch.object(self.module.subprocess, "Popen") as spawn:
            result = self.run_peer()
        self.assertEqual("unsupported_platform", result["code"])
        spawn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
