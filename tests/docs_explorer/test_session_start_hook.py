"""The session-start hook (DC-190): the audit marker is set by the HOST at the session seam,
not by a skill remembering to. A node that grounds before `audit-log.py start` reported a
duration measured from the wrong instant (CV-4, 2026-09-13); a resumed node's second run
set none at all (six nodes, AC-09). The hook runs on `SessionStart` and `SubagentStart`
and records the instant the session actually began.

The marker it writes is a HARNESS marker: `append` uses it only when the closing entry's
own session/skill marker is absent, records `duration_source: session-start-hook` so a
reader knows the instant was the session's start rather than grounding, and consumes it -
one marker measures one run, so a second run without its own `start` reads no duration
rather than the session's whole age (IO8).
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOOK = ROOT / "pack" / "adapters" / "hooks" / "session-start.py"
AUDIT = ROOT / "pack" / "scripts" / "audit-log.py"


class SessionStartHookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = pathlib.Path(self.tmp) / "repo"
        (self.repo / "docs" / "audit").mkdir(parents=True)
        # the deployed layout: hooks/ beside scripts/ under docs/ai-forward-pack/
        pack = self.repo / "docs" / "ai-forward-pack"
        (pack / "hooks").mkdir(parents=True)
        (pack / "scripts").mkdir(parents=True)
        shutil.copy(HOOK, pack / "hooks" / "session-start.py")
        shutil.copy(AUDIT, pack / "scripts" / "audit-log.py")
        self.hook = pack / "hooks" / "session-start.py"
        self.audit = pack / "scripts" / "audit-log.py"

    def _run_hook(self, payload, env_extra=None):
        env = dict(os.environ)
        env.pop("AGENT_SESSION", None)
        env.update(env_extra or {})
        return subprocess.run([sys.executable, str(self.hook), "--host", "claude"], cwd=str(self.repo),
                              input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=30)

    def _starts(self):
        p = self.repo / "docs" / "audit" / ".run-starts.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def _append(self, session="node-a", skill="implement"):
        r = subprocess.run([sys.executable, str(self.audit), "--root", str(self.repo / "docs"), "append",
                            "--shortname", "close", "--session", session, "--skill", skill, "--kind", "skill",
                            "--prompt", "p", "--summary", "s"], cwd=str(self.repo), capture_output=True,
                           text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        entries = [json.loads(l) for l in (self.repo / "docs" / "audit" / "audit-log.jsonl")
                   .read_text(encoding="utf-8").splitlines() if l.strip()]
        return entries[-1]

    def test_session_start_records_a_harness_marker(self):
        r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "abc123", "cwd": str(self.repo),
                            "reason": "startup"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual("", r.stdout.strip(), "the hook adds nothing to the model's context")
        starts = self._starts()
        self.assertIn("__harness__:abc123", starts, starts)

    def test_subagent_start_records_a_marker_keyed_to_the_agent(self):
        r = self._run_hook({"hook_event_name": "SubagentStart", "session_id": "abc123", "agent_id": "a1b2",
                            "agent_type": "general-purpose", "cwd": str(self.repo)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("__harness__:abc123/a1b2", self._starts())

    def test_agent_session_in_the_environment_keys_the_marker_to_the_session(self):
        r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "abc123", "cwd": str(self.repo)},
                           env_extra={"AGENT_SESSION": "conductor"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("conductor", self._starts())

    def test_append_falls_back_to_the_harness_marker_and_says_so(self):
        self._run_hook({"hook_event_name": "SessionStart", "session_id": "abc123", "cwd": str(self.repo)})
        entry = self._append()
        self.assertIn("duration_seconds", entry)
        self.assertEqual("session-start-hook", entry.get("duration_source"))
        second = self._append(session="node-b")
        self.assertNotIn("duration_seconds", second, "one marker measures one run")

    def test_a_skills_own_marker_wins_over_the_harness_marker(self):
        self._run_hook({"hook_event_name": "SessionStart", "session_id": "abc123", "cwd": str(self.repo)})
        subprocess.run([sys.executable, str(self.audit), "--root", str(self.repo / "docs"), "start",
                        "--session", "node-a"], check=True, capture_output=True)
        entry = self._append()
        self.assertNotIn("duration_source", entry, "the skill's own grounding mark is the measurement")
        self.assertIn("__harness__:abc123", self._starts(), "the harness marker is left for a run that has none")

    def test_the_hook_is_fail_open(self):
        r = subprocess.run([sys.executable, str(self.hook), "--host", "claude"], cwd=str(self.tmp),
                           input="not json", capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, "a hook that fails must never fail the session")
        r = self._run_hook({"hook_event_name": "SessionStart"})
        self.assertEqual(r.returncode, 0)

    def test_the_settings_snippet_wires_both_events(self):
        snippet = json.loads((ROOT / "pack" / "adapters" / "hooks" / "claude-code.settings.hooks.json")
                             .read_text(encoding="utf-8"))
        for event in ("SessionStart", "SubagentStart"):
            cmds = [h["command"] for entry in snippet["hooks"].get(event, []) for h in entry.get("hooks", [])]
            self.assertTrue(any("session-start.py" in c for c in cmds), event + " must run the hook")


if __name__ == "__main__":
    unittest.main()
