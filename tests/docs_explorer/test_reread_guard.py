"""CTX-D control: the re-read guard hook warns on the third identical read in a turn and on a
paged tool output viewed whole, resets at the prompt boundary, and never blocks or breaks the
host's tool call (fail-open on every error path). The decision function is pure so the oracle
is exact; the subprocess tests pin the host contracts the configs are written to."""
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
GUARD = ROOT / "pack" / "adapters" / "hooks" / "reread-guard.py"


def _load():
    spec = importlib.util.spec_from_file_location("reread_guard", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class EvaluateTests(unittest.TestCase):
    def setUp(self):
        self.g = _load()

    def _copilot_view(self, path, state, **args):
        payload = {"sessionId": "s", "toolName": "view", "toolArgs": dict(path=path, **args)}
        return self.g.evaluate("copilot", payload, 3, state)

    def test_third_identical_read_warns_and_earlier_ones_do_not(self):
        state, w = self._copilot_view("C:/x/a.md", {})
        self.assertIsNone(w)
        state, w = self._copilot_view("C:/x/a.md", state)
        self.assertIsNone(w)
        state, w = self._copilot_view("C:/x/A.MD", state)  # same file, different case on Windows-style paths
        self.assertIsNotNone(w)
        self.assertIn("3 times", w)

    def test_paged_output_viewed_whole_warns_on_first_read(self):
        _, w = self._copilot_view("C:/t/copilot-tool-output-0abc.txt", {})
        self.assertIn("paged tool output", w)

    def test_paged_output_with_a_range_is_fine(self):
        _, w = self._copilot_view("C:/t/copilot-tool-output-0abc.txt", {}, view_range=[1, 40])
        self.assertIsNone(w)

    def test_prompt_submit_resets_the_counter(self):
        state = {"reads": {"c:\\x\\a.md": 2}}
        state, w = self.g.evaluate("copilot", {"sessionId": "s", "prompt": "next"}, 3, state)
        self.assertEqual({}, state)
        self.assertIsNone(w)

    def test_claude_payload_contract(self):
        state = {}
        for _ in range(2):
            state, w = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Read",
                                                  "tool_input": {"file_path": "/x/b.md"}}, 3, state)
            self.assertIsNone(w)
        state, w = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Read",
                                              "tool_input": {"file_path": "/x/b.md"}}, 3, state)
        self.assertIn("read 3 times", w)
        state, w = self.g.evaluate("claude", {"hook_event_name": "UserPromptSubmit", "prompt": "go"}, 3, state)
        self.assertEqual({}, state)

    def test_other_tools_are_ignored(self):
        state, w = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                              "tool_input": {"command": "ls"}}, 3, {})
        self.assertEqual({}, state)
        self.assertIsNone(w)


class ProcessContractTests(unittest.TestCase):
    """The shapes the host configs rely on: exit 0 always; JSON on stdout only when warning."""

    def _run(self, host, stdin):
        return subprocess.run([sys.executable, str(GUARD), "--host", host], input=stdin,
                              capture_output=True, text=True, timeout=30)

    def test_claude_warning_shape_and_exit_zero(self):
        sid = "test-{0}".format(os.getpid())
        payload = json.dumps({"session_id": sid, "hook_event_name": "PreToolUse", "tool_name": "Read",
                              "tool_input": {"file_path": "/x/c.md"}})
        self._run("claude", json.dumps({"session_id": sid, "hook_event_name": "UserPromptSubmit"}))
        for _ in range(2):
            p = self._run("claude", payload)
            self.assertEqual(0, p.returncode)
            self.assertEqual("", p.stdout.strip())
        p = self._run("claude", payload)
        self.assertEqual(0, p.returncode)
        out = json.loads(p.stdout)
        self.assertEqual("PreToolUse", out["hookSpecificOutput"]["hookEventName"])
        self.assertIn("systemMessage", out["hookSpecificOutput"])

    def test_copilot_warning_shape_uses_additional_context(self):
        sid = "test-cop-{0}".format(os.getpid())
        self._run("copilot", json.dumps({"sessionId": sid, "prompt": "reset"}))
        p = self._run("copilot", json.dumps({"sessionId": sid, "toolName": "view",
                                             "toolArgs": {"path": "/t/copilot-tool-output-0f.txt"}}))
        self.assertEqual(0, p.returncode)
        self.assertIn("additionalContext", json.loads(p.stdout))

    def test_fail_open_on_garbage_input(self):
        for stdin in ("", "not json", "[1,2]", "{}"):
            p = self._run("copilot", stdin)
            self.assertEqual(0, p.returncode, stdin)
            self.assertEqual("", p.stdout.strip(), stdin)


if __name__ == "__main__":
    unittest.main()
