"""PRIM-A's edit guard (pack/adapters/hooks/primary-guard.py): a session working in a linked
worktree never writes the primary checkout unnoticed.

Two parts, each proved against a real primary + linked worktree:
  (a) preventive: PreToolUse on Write/Edit/NotebookEdit refuses a path under the primary;
  (b) detective: SessionStart snapshots `git status --porcelain=v1 --untracked-files=all` of the
      primary, and PostToolUse on Bash/PowerShell reports any change at once (a shell's relative
      path is the shape a Write/Edit hook cannot see).
The hook records its own run time per call (IO), so its cost is measured, not assumed.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOOKS = ROOT / "pack" / "adapters" / "hooks"
GUARD = HOOKS / "primary-guard.py"
SESSION_START = HOOKS / "session-start.py"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def run(argv, cwd, payload=None, env=None):
    return subprocess.run(argv, cwd=str(cwd), input=json.dumps(payload) if payload is not None else None,
                          capture_output=True, text=True, encoding="utf-8", timeout=30,
                          env=env, creationflags=NO_WINDOW)


class PrimaryGuardTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        self.primary = pathlib.Path(tmp).resolve() / "primary"
        self.linked = pathlib.Path(tmp).resolve() / "linked"
        self.primary.mkdir()
        self.git(self.primary, "init", "-q", "-b", "main")
        self.git(self.primary, "config", "user.email", "t@example.invalid")
        self.git(self.primary, "config", "user.name", "T")
        (self.primary / "tracked.txt").write_text("one\n", encoding="utf-8")
        self.git(self.primary, "add", "tracked.txt")
        self.git(self.primary, "commit", "-q", "-m", "one")
        self.git(self.primary, "worktree", "add", "-q", "-b", "side", str(self.linked))
        self.env = dict(os.environ)
        self.env.pop("AGENT_SESSION", None)

    def git(self, cwd, *args):
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                              encoding="utf-8", check=True, creationflags=NO_WINDOW)

    def pre(self, tool, cwd, **tool_input):
        return run([sys.executable, str(GUARD), "--host", "claude", "--event", "PreToolUse"], cwd,
                   {"hook_event_name": "PreToolUse", "session_id": "s1", "cwd": str(cwd),
                    "tool_name": tool, "tool_input": tool_input}, self.env)

    def post(self, tool, cwd, command="x"):
        return run([sys.executable, str(GUARD), "--host", "claude", "--event", "PostToolUse"], cwd,
                   {"hook_event_name": "PostToolUse", "session_id": "s1", "cwd": str(cwd),
                    "tool_name": tool, "tool_input": {"command": command}}, self.env)

    def snapshot(self, cwd):
        return run([sys.executable, str(GUARD), "--host", "claude", "--event", "SessionStart"], cwd,
                   {"hook_event_name": "SessionStart", "session_id": "s1", "cwd": str(cwd)}, self.env)

    def common(self):
        return self.primary / ".git"

    # (a) preventive

    def test_a_write_to_the_primary_from_a_linked_tree_is_refused(self):
        r = self.pre("Write", self.linked, file_path=str(self.primary / "tracked.txt"), content="x")
        self.assertEqual(2, r.returncode, r.stdout + r.stderr)
        self.assertIn("primary checkout", r.stderr)
        self.assertIn(str(self.primary), r.stderr)

    def test_edit_and_notebook_edit_are_refused_too_and_a_relative_path_resolves_against_cwd(self):
        r = self.pre("Edit", self.linked, file_path=str(self.primary / "tracked.txt"))
        self.assertEqual(2, r.returncode, r.stdout + r.stderr)
        self.assertIn("primary checkout", r.stderr)
        r = self.pre("NotebookEdit", self.linked, notebook_path="../primary/n.ipynb")
        self.assertEqual(2, r.returncode, r.stdout + r.stderr)
        self.assertIn("primary checkout", r.stderr)

    def test_a_write_inside_the_linked_tree_is_allowed(self):
        r = self.pre("Write", self.linked, file_path=str(self.linked / "new.txt"), content="x")
        self.assertEqual(0, r.returncode, r.stdout + r.stderr)
        self.assertEqual("", r.stderr)

    def test_a_session_in_the_primary_itself_is_not_refused(self):
        r = self.pre("Write", self.primary, file_path=str(self.primary / "tracked.txt"), content="x")
        self.assertEqual(0, r.returncode, r.stdout + r.stderr)
        self.assertEqual("", r.stderr)

    def test_other_tools_are_never_refused_and_an_unreadable_payload_fails_open(self):
        r = self.pre("Read", self.linked, file_path=str(self.primary / "tracked.txt"))
        self.assertEqual((0, ""), (r.returncode, r.stderr))
        r = run([sys.executable, str(GUARD), "--host", "claude", "--event", "PreToolUse"], self.linked)
        self.assertEqual((0, ""), (r.returncode, r.stderr))

    # (b) detective

    def test_session_start_in_a_linked_tree_snapshots_the_primarys_status(self):
        (self.primary / "dirty.txt").write_text("d\n", encoding="utf-8")
        self.snapshot(self.linked)
        snaps = sorted(self.common().glob("aif-primary-snapshot-*"))
        self.assertEqual(1, len(snaps), snaps)
        self.assertIn("dirty.txt", snaps[0].read_text(encoding="utf-8"))

    def test_session_start_hook_takes_the_snapshot_through_the_guard(self):
        self.assertTrue(GUARD.is_file(), "the guard ships beside session-start.py")
        pack = self.linked / "docs" / "ai-forward-pack" / "hooks"
        pack.mkdir(parents=True)
        for name in ("session-start.py", "primary-guard.py", "coord_identity.py"):
            shutil.copy(HOOKS / name, pack / name)
        r = run([sys.executable, str(pack / "session-start.py"), "--host", "claude"], self.linked,
                {"hook_event_name": "SessionStart", "session_id": "s1", "cwd": str(self.linked)}, self.env)
        self.assertEqual(0, r.returncode, r.stdout + r.stderr)
        self.assertEqual(1, len(list(self.common().glob("aif-primary-snapshot-*"))))

    def test_a_shell_that_writes_a_relative_path_into_the_primary_is_reported_at_once(self):
        self.snapshot(self.linked)
        quiet = self.post("Bash", self.linked)
        self.assertEqual("", quiet.stdout.strip(), "no change, no report")
        relative = os.path.relpath(self.primary / "leak.txt", self.linked)
        run([sys.executable, "-c", f"open({relative!r}, 'w').write('leak')"], self.linked)
        r = self.post("PowerShell", self.linked, command="[IO.File]::WriteAllText('" + relative + "', 'leak')")
        self.assertEqual(0, r.returncode, r.stdout + r.stderr)
        context = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("leak.txt", context)
        self.assertIn("fast-forward", context)
        again = self.post("Bash", self.linked)
        self.assertEqual("", again.stdout.strip(), "a delta is reported once, not on every later call")

    def test_a_non_shell_tool_is_never_checked(self):
        self.snapshot(self.linked)
        (self.primary / "leak.txt").write_text("x\n", encoding="utf-8")
        r = self.post("Read", self.linked)
        self.assertEqual("", r.stdout.strip())

    def test_every_call_records_its_run_time(self):
        self.pre("Write", self.linked, file_path=str(self.primary / "x.txt"))
        self.snapshot(self.linked)
        self.post("Bash", self.linked)
        log = self.common() / "aif-primary-guard-times.jsonl"
        self.assertTrue(log.is_file(), "the guard records a run-time row per call")
        rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(["PreToolUse", "SessionStart", "PostToolUse"], [row["event"] for row in rows])
        for row in rows:
            self.assertIsInstance(row["ms"], float)
            self.assertGreaterEqual(row["ms"], 0.0)
        self.assertEqual("refused", rows[0]["decision"])

    def test_the_claude_settings_register_the_guard_on_its_events(self):
        hooks = json.loads((HOOKS / "claude-code.settings.hooks.json").read_text(encoding="utf-8"))["hooks"]

        def registered(event, matcher):
            return any("primary-guard.py" in h["command"] and f"--event {event}" in h["command"]
                       for entry in hooks.get(event, []) if entry.get("matcher") == matcher
                       for h in entry["hooks"])
        self.assertTrue(registered("PreToolUse", "Write|Edit|NotebookEdit"))
        self.assertTrue(registered("PostToolUse", "Bash|PowerShell"))


if __name__ == "__main__":
    unittest.main()
