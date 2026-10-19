"""PK-07's mechanical control: AL0.2 says in prose that neither a pack script nor the agent
running it may invent a git identity to force a blocked commit through. This is the second
half -- a PreToolUse hook that refuses the shell command itself, so the rule holds even when
the agent forgets it. The decision function is pure so the oracle is exact; the subprocess
tests pin the host contracts (exit 2 denies preToolUse on Claude Code, Grok Build's
Claude-format hooks, and Copilot CLI -- reread-guard.py's own documented contract)."""
import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

from hook_wiring import routes, wired_scripts

ROOT = pathlib.Path(__file__).resolve().parents[2]
GUARD = ROOT / "pack" / "adapters" / "hooks" / "git-identity-guard.py"


def _load():
    spec = importlib.util.spec_from_file_location("git_identity_guard", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class EvaluateTests(unittest.TestCase):
    def setUp(self):
        self.g = _load()

    def test_git_config_user_name_with_a_value_is_blocked(self):
        reason = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                            "tool_input": {"command": 'git config user.name "CI Bot"'}})
        self.assertIsNotNone(reason)
        self.assertIn("PK-07", reason)

    def test_git_config_global_user_email_with_a_value_is_blocked(self):
        reason = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                            "tool_input": {"command": "git config --global user.email a@b.com"}})
        self.assertIsNotNone(reason)

    def test_inline_dash_c_override_is_blocked(self):
        reason = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                            "tool_input": {"command": 'git -c user.name=bot -c user.email=a@b commit -m x'}})
        self.assertIsNotNone(reason)

    def test_chained_with_other_commands_is_still_caught(self):
        reason = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                            "tool_input": {"command": 'git add -A && git config user.name "x" && git commit -m y'}})
        self.assertIsNotNone(reason)

    def test_reading_the_identity_is_never_blocked(self):
        reason = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                            "tool_input": {"command": "git config user.name"}})
        self.assertIsNone(reason)

    def test_a_read_followed_by_a_shell_operator_or_redirect_is_never_blocked(self):
        for command in ("git config user.email && git status", "git config user.name || echo none",
                        "git config user.name 2>/dev/null", "git config user.email | cat",
                        "git config user.name > out.txt", "git config user.email; git log -1"):
            with self.subTest(command=command):
                reason = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                                    "tool_input": {"command": command}})
                self.assertIsNone(reason)

    def test_get_flag_is_never_blocked(self):
        reason = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                            "tool_input": {"command": "git config --get user.email"}})
        self.assertIsNone(reason)

    def test_an_unrelated_command_is_never_blocked(self):
        reason = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                            "tool_input": {"command": "git commit -m 'normal change'"}})
        self.assertIsNone(reason)

    def test_non_pretooluse_events_are_ignored(self):
        reason = self.g.evaluate("claude", {"hook_event_name": "UserPromptSubmit",
                                            "tool_input": {"command": 'git config user.name "x"'}})
        self.assertIsNone(reason)

    def test_grok_camelcase_payload_is_caught(self):
        reason = self.g.evaluate("grok", {"hookEventName": "PreToolUse", "toolName": "Bash",
                                          "toolInput": {"command": 'git config user.email "x@y"'}})
        self.assertIsNotNone(reason)

    def test_copilot_payload_is_caught(self):
        reason = self.g.evaluate("copilot", {"sessionId": "s", "toolName": "bash",
                                             "toolArgs": {"command": 'git config user.name "x"'}})
        self.assertIsNotNone(reason)

    def test_no_command_like_field_is_never_blocked(self):
        reason = self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Read",
                                            "tool_input": {"file_path": "/x/y.md"}})
        self.assertIsNone(reason)


class ProbeTableTests(unittest.TestCase):
    """FR-088: the commands `evaluate()` allowed although each one sets an identity, and the
    text it blocked although nothing runs git. The guard reads command words, not text."""

    SETS_AN_IDENTITY = (
        "git -C . config user.name X",
        "git config --file .git/config user.email X",
        "git config -f .git/config user.email X",
        "git config --worktree user.name X",
        "git config set user.name X",
        "git config set --global user.email X",
        "git config --replace-all user.name X",
        "git config author.name X",
        "git config committer.email X",
        "git --git-dir=.git config user.name X",
        "git -c core.pager=cat -c user.email=a@b commit -m x",
        "git --config-env=user.name=NAME commit -m x",
        "GIT_AUTHOR_NAME=X git commit -m y",
        "GIT_COMMITTER_EMAIL=x@y git commit -m y",
        "env GIT_AUTHOR_EMAIL=x@y git commit -m y",
        "export GIT_AUTHOR_NAME=X",
        "$env:GIT_AUTHOR_NAME = 'X'",
        "$env:GIT_COMMITTER_EMAIL='x@y'",
        "git commit --author='X <x@y>' -m y",
        "git commit --author 'X <x@y>' -m y",
        "/usr/bin/git config user.name X",
        "git.exe config user.name X",
        "git status\ngit config user.name X",
        "bash -c \"git config user.name X\"",
        "pwsh -Command \"git config user.email X\"",
    )

    SETS_NOTHING = (
        "echo 'docs: git config user.name X is forbidden' > notes.md",
        "grep -n \"git config user.name\" docs/a.md",
        "git commit -m 'never run git config user.name X'",
        "git commit -m \"--author=X is wrong\"",
        "git -C . config user.name",
        "git config get user.name",
        "git config --get-all user.email",
        "git config --unset user.name",
        "git config --list",
        "git log --author=X",
        "echo GIT_AUTHOR_NAME=X",
        "git commit --reset-author -m y",
    )

    def _decide(self, command):
        return self.g.evaluate("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                          "tool_input": {"command": command}})

    def setUp(self):
        self.g = _load()

    def test_every_identity_setting_form_is_blocked(self):
        for command in self.SETS_AN_IDENTITY:
            with self.subTest(command=command):
                self.assertIsNotNone(self._decide(command))

    def test_text_that_only_mentions_an_identity_is_never_blocked(self):
        for command in self.SETS_NOTHING:
            with self.subTest(command=command):
                self.assertIsNone(self._decide(command))

    def test_unbalanced_quotes_still_catch_a_set(self):
        self.assertIsNotNone(self._decide("git config user.name 'X"))


class MainSubprocessTests(unittest.TestCase):
    def _run(self, host, payload):
        return subprocess.run([sys.executable, str(GUARD), "--host", host], input=json.dumps(payload),
                              capture_output=True, text=True, timeout=30)

    def test_claude_blocks_with_exit_2_and_a_stderr_reason(self):
        r = self._run("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                 "tool_input": {"command": 'git config user.name "x"'}})
        self.assertEqual(2, r.returncode)
        self.assertIn("PK-07", r.stderr)
        self.assertEqual("", r.stdout.strip(), "never prints to stdout (that reaches the model as context)")

    def test_claude_allows_a_normal_commit(self):
        r = self._run("claude", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                 "tool_input": {"command": "git commit -m 'normal change'"}})
        self.assertEqual(0, r.returncode)

    def test_grok_blocks_with_exit_2(self):
        r = self._run("grok", {"hookEventName": "PreToolUse", "toolName": "Bash",
                               "toolInput": {"command": 'git config --global user.email "x@y"'}})
        self.assertEqual(2, r.returncode)
        self.assertIn("PK-07", r.stderr)

    def test_copilot_blocks_with_exit_2(self):
        r = self._run("copilot", {"sessionId": "s", "toolName": "bash",
                                  "toolArgs": {"command": 'git config user.name "x"'}})
        self.assertEqual(2, r.returncode)
        self.assertIn("PK-07", r.stderr)

    def test_malformed_stdin_is_fail_open(self):
        r = subprocess.run([sys.executable, str(GUARD), "--host", "claude"], input="not json",
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(0, r.returncode, "a guard that cannot evaluate must never block a real tool call")

    def test_agy_is_not_a_supported_host(self):
        """Antigravity's PreToolUse deny contract is unverified in this pack (only `allow` is
        observed, by reread-guard.py); rather than guess a shape that might silently fail
        open or block everything, this guard is not wired for agy (left prose-only, AL0.2)."""
        r = self._run("agy", {})
        self.assertNotEqual(0, r.returncode, "agy is deliberately not an accepted --host value")


class HookConfigsWireTheGuardWhereGrounded(unittest.TestCase):
    """The guard is wired into every host config whose PreToolUse deny contract this pack
    has grounded (claude, grok, copilot) and deliberately absent from agy's (unverified)."""

    # Read through the dispatcher (B15): each config registers dispatch.py once per event.
    def test_claude_grok_and_copilot_run_the_guard_at_pretooluse(self):
        for host, event in (("claude", "PreToolUse"), ("grok", "PreToolUse"), ("copilot", "preToolUse")):
            self.assertIn("git-identity-guard.py", wired_scripts(host, event), host + " must run the guard")

    def test_agy_does_not_claim_the_guard(self):
        agy = [script for event in routes()["agy"] for script in wired_scripts("agy", event)]
        self.assertTrue(agy)
        self.assertNotIn("git-identity-guard.py", agy,
                         "agy's PreToolUse deny contract is unverified; do not claim enforcement")


if __name__ == "__main__":
    unittest.main()
