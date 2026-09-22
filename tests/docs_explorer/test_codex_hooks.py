"""Native Codex hook payloads and deployed commands, including nested Windows cwd."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "pack/adapters/hooks"
spec = importlib.util.spec_from_file_location("codex_guard", HOOKS / "reread-guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class CodexGuardTests(unittest.TestCase):
    def test_native_shell_reads_warn_and_prompt_resets(self):
        for command in ('cat "docs/my file.md"', 'Get-Content -LiteralPath "docs/my file.md" -Raw'):
            state = {}
            payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                       "tool_input": {"command": command}}
            for _ in range(3):
                state, warning = guard.evaluate("codex", payload, state=state)
            self.assertIn("3 times", warning or "")
            self.assertEqual(({}, None), guard.evaluate("codex", {"hook_event_name": "UserPromptSubmit"}, state=state))

    def test_ambiguous_commands_are_ignored(self):
        for command in ('cat a b', 'cat a; cat a', 'cat $(echo a)', 'cat *.md',
                        'Get-Content a | Select-Object -First 1', 'echo cat a', 'cat a > out'):
            state, warning = guard.evaluate("codex", {"tool_name": "Bash", "tool_input": {"command": command}})
            self.assertEqual({}, state, command)
            self.assertIsNone(warning)

    def test_subprocess_warning_is_advisory_and_reset_is_silent(self):
        with tempfile.TemporaryDirectory() as temp:
            env = dict(os.environ, TMPDIR=temp, TMP=temp, TEMP=temp)
            payload = {"session_id": "codex-guard-fixture", "hook_event_name": "PreToolUse",
                       "tool_name": "Bash", "tool_input": {"command": "cat docs/readme.md"}}
            for _ in range(3):
                result = subprocess.run([sys.executable, str(HOOKS / "reread-guard.py"), "--host", "codex"],
                    input=json.dumps(payload), text=True, capture_output=True, env=env, timeout=15)
                self.assertEqual(0, result.returncode, result.stderr)
            output = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual("PreToolUse", output["hookEventName"])
            self.assertIn("3 times", output["additionalContext"])
            self.assertNotIn("permissionDecision", output)
            payload["hook_event_name"] = "UserPromptSubmit"
            result = subprocess.run([sys.executable, str(HOOKS / "reread-guard.py"), "--host", "codex"],
                input=json.dumps(payload), text=True, capture_output=True, env=env, timeout=15)
            self.assertEqual("", result.stdout)


class CodexMarkerTests(unittest.TestCase):
    def test_handlers_have_unique_stable_merge_identity(self):
        config = json.loads((HOOKS / "codex.hooks.json").read_text(encoding="utf-8"))
        names = [handler.get("statusMessage", "")
                 for groups in config["hooks"].values() for group in groups for handler in group["hooks"]]
        self.assertTrue(all(name.startswith("AI-Forward Codex ") for name in names))
        self.assertEqual(len(names), len(set(names)))

    def test_installed_command_from_nested_repo_with_spaces(self):
        config = json.loads((HOOKS / "codex.hooks.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="codex hooks ") as temp:
            repo = Path(temp) / "repo with spaces"
            nested = repo / "src/nested"
            nested.mkdir(parents=True)
            subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
            bundle = repo / "docs/ai-forward-pack"
            (bundle / "hooks").mkdir(parents=True)
            (bundle / "scripts").mkdir()
            shutil.copy(HOOKS / "session-start.py", bundle / "hooks")
            shutil.copy(ROOT / "pack/scripts/audit-log.py", bundle / "scripts")
            env = dict(os.environ)
            env.pop("AGENT_SESSION", None)
            for event in ("SessionStart", "SubagentStart"):
                handler = config["hooks"][event][0]["hooks"][0]
                self.assertFalse(handler.get("async", False))
                payload = {"hook_event_name": event, "session_id": "parent", "cwd": str(nested)}
                if event == "SubagentStart":
                    payload.update(agent_id="child", agent_type="test-architect")
                # PowerShell 7 (pwsh) is explicit in the Windows hook command;
                # exercise both outer shells rather than assume which Codex uses.
                commands = ([["pwsh", "-NoProfile", "-Command", handler["commandWindows"]],
                             'cmd /d /s /c "' + handler["commandWindows"] + '"' ] if os.name == "nt"
                            else [["sh", "-c", handler["command"]]])
                for index, command in enumerate(commands):
                    payload["session_id"] = "parent-" + str(index)
                    result = subprocess.run(command, cwd=nested, env=env, input=json.dumps(payload),
                                            text=True, capture_output=True, timeout=30)
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual("", result.stdout)
                    starts = json.loads((repo / "docs/audit/.run-starts.json").read_text(encoding="utf-8"))
                    marker = "__harness__:" + payload["session_id"]
                    if event == "SubagentStart":
                        marker += "/child"
                    self.assertIn(marker, starts)


if __name__ == "__main__":
    unittest.main()
