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
IDENTITY = ROOT / "pack" / "adapters" / "hooks" / "coord_identity.py"
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
        shutil.copy(IDENTITY, pack / "hooks" / "coord_identity.py")
        shutil.copy(AUDIT, pack / "scripts" / "audit-log.py")
        self.hook = pack / "hooks" / "session-start.py"
        self.audit = pack / "scripts" / "audit-log.py"

    def _run_hook(self, payload, env_extra=None, host="claude"):
        env = dict(os.environ)
        env.pop("AGENT_SESSION", None)
        env["AGENT_HOST"] = host
        env.update(env_extra or {})
        return subprocess.run([sys.executable, str(self.hook), "--host", host], cwd=str(self.repo),
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

    def test_grok_camelcase_payload_records_the_marker(self):
        """Grok Build's SessionStart envelope uses sessionId / workspaceRoot (user-guide 10-hooks.md)."""
        env = dict(os.environ)
        env.pop("AGENT_SESSION", None)
        payload = {"hookEventName": "session_start", "hook_event_name": "SessionStart",
                   "sessionId": "grok-abc", "workspaceRoot": str(self.repo)}
        r = subprocess.run([sys.executable, str(self.hook), "--host", "grok"], cwd=str(self.repo),
                           input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual("", r.stdout.strip())
        self.assertIn("__harness__:grok-abc", self._starts())

    # MUT-A (x-harness-x-model-bench, 2026-10-04): an interrupted mutation sweep left a mutant in the
    # primary, and nothing ran the repo's own `--check-clean` when the next session started there.
    def _declare_checks(self, *checks):
        (self.repo / ".agents").mkdir(exist_ok=True)
        (self.repo / ".agents" / "session-checks.json").write_text(
            json.dumps({"checks": list(checks)}), encoding="utf-8")

    def test_a_failing_repo_declared_check_reaches_the_session_with_its_remedy(self):
        self._declare_checks(
            {"name": "mutation-clean", "argv": ["{python}", "-c", "import sys; print('mutant applied: a.py'); sys.exit(1)"],
             "remedy": "run tools/mutate_check.py --restore"},
            {"name": "always-clean", "argv": ["{python}", "-c", "print('quiet')"], "remedy": "never shown"})
        r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "abc123", "cwd": str(self.repo)})
        self.assertEqual(r.returncode, 0, "a failing check never fails the session")
        self.assertIn("mutation-clean", r.stdout, "the failing check is not in the model's context")
        self.assertIn("mutant applied: a.py", r.stdout)
        self.assertIn("tools/mutate_check.py --restore", r.stdout)
        self.assertNotIn("always-clean", r.stdout)
        self.assertIn("__harness__:abc123", self._starts(), "the audit marker is still written")

    def test_a_passing_check_adds_nothing_and_other_hosts_report_on_stderr(self):
        self._declare_checks({"name": "always-clean", "argv": ["{python}", "-c", "pass"], "remedy": "x"})
        r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "abc123", "cwd": str(self.repo)})
        self.assertEqual("", r.stdout.strip())
        self._declare_checks({"name": "dirty", "argv": ["{python}", "-c", "import sys; sys.exit(3)"], "remedy": "fix"})
        r = self._run_hook({"hook_event_name": "session_start", "sessionId": "g1", "workspaceRoot": str(self.repo)},
                           host="grok")
        self.assertEqual("", r.stdout.strip(), "only Claude's SessionStart stdout is model context")
        self.assertIn("dirty", r.stderr)

    def test_the_hook_is_fail_open(self):
        r = subprocess.run([sys.executable, str(self.hook), "--host", "claude"], cwd=str(self.tmp),
                           input="not json", capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, "a hook that fails must never fail the session")
        r = self._run_hook({"hook_event_name": "SessionStart"})
        self.assertEqual(r.returncode, 0)

    def test_agy_pre_invocation_invocation_one_records_marker(self):
        env = dict(os.environ)
        env.pop("AGENT_SESSION", None)
        payload = {
            "hookEventName": "PreInvocation",
            "conversationId": "agy-abc-1",
            "invocationNum": 1,
            "workspacePaths": [str(self.repo)],
        }
        r = subprocess.run([sys.executable, str(self.hook), "--host", "agy"], cwd=str(self.repo),
                           input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual("", r.stdout.strip())
        self.assertIn("__harness__:agy-abc-1", self._starts())

    def test_agy_pre_invocation_subsequent_invocation_is_noop(self):
        env = dict(os.environ)
        env.pop("AGENT_SESSION", None)
        payload = {
            "hookEventName": "PreInvocation",
            "conversationId": "agy-abc-2",
            "invocationNum": 2,
            "workspacePaths": [str(self.repo)],
        }
        r = subprocess.run([sys.executable, str(self.hook), "--host", "agy"], cwd=str(self.repo),
                           input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual("", r.stdout.strip())
        self.assertNotIn("__harness__:agy-abc-2", self._starts())

    def test_copilot_session_start_uses_the_explicit_env_identity(self):
        r = self._run_hook({"hookEventName": "sessionStart", "sessionId": "cp-top", "cwd": str(self.repo)},
                           env_extra={"AGENT_SESSION": "worker-copilot"}, host="copilot")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("worker-copilot", self._starts())

    def test_copilot_subagent_start_without_documented_child_id_is_a_noop(self):
        r = self._run_hook({"hookEventName": "subagentStart", "sessionId": "cp-top",
                            "agentName": "general-purpose", "agentDisplayName": "General Purpose",
                            "cwd": str(self.repo)},
                           env_extra={"AGENT_SESSION": "worker-copilot"}, host="copilot")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._starts(), {})

    def test_claude_form_hook_is_skipped_when_copilot_loads_claude_settings_too(self):
        r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "dup", "cwd": str(self.repo)},
                           env_extra={"AGENT_SESSION": "worker-copilot", "AGENT_HOST": "copilot"}, host="claude")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._starts(), {})

    def test_invalid_copilot_child_identity_writes_nothing(self):
        r = self._run_hook({"hookEventName": "subagentStart", "sessionId": "../bad", "agentId": "agent-7",
                            "cwd": str(self.repo)},
                           env_extra={"AGENT_SESSION": "worker-copilot"}, host="copilot")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._starts(), {})


class SessionStartHookOptInTests(unittest.TestCase):
    """AL0.2 governs `audit-log.py append`'s default `--root` via `resolve_default_root`:
    docs/audit/ is seeded only when it already exists on disk (the repo's own opt-in
    signal). The session-start hook is a SECOND, independent definition of that same
    decision (DC-190's own gate: `if not os.path.isdir(docs): return 0` on the bare
    `docs/` directory, then an explicit `--root docs`) -- and an explicit --root is a
    direct ask that bypasses `resolve_default_root` entirely (AL0.2's own documented
    escape hatch). So in a repo with a bare `docs/` (common: README-only docs, no
    docs/audit/) that never opted into the Audit Mandate, the hook's own marker write
    creates docs/audit/ unasked -- and that directory then satisfies `append`'s opt-in
    check on every later call, seeding the real audit-log.jsonl into the product tree
    too (measured: `ignored docs/audit/.run-starts.json` in 51 of 138 grid-4 cells,
    `added docs/audit/audit-log.jsonl outside` in 18). The fix: the hook must resolve
    the root the same way `append` does -- one function, not two definitions -- by
    never forcing an explicit --root and never gating on bare `docs/` existing."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = pathlib.Path(self.tmp) / "repo"
        # bare docs/ -- NOT opted into the Audit Mandate (no docs/audit/ yet)
        (self.repo / "docs").mkdir(parents=True)
        pack = self.repo / "docs" / "ai-forward-pack"
        (pack / "hooks").mkdir(parents=True)
        (pack / "scripts").mkdir(parents=True)
        shutil.copy(HOOK, pack / "hooks" / "session-start.py")
        shutil.copy(IDENTITY, pack / "hooks" / "coord_identity.py")
        shutil.copy(AUDIT, pack / "scripts" / "audit-log.py")
        self.hook = pack / "hooks" / "session-start.py"

    def _run_hook(self, payload, host="claude"):
        env = dict(os.environ)
        env.pop("AGENT_SESSION", None)
        env["AGENT_HOST"] = host
        return subprocess.run([sys.executable, str(self.hook), "--host", host], cwd=str(self.repo),
                              input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=30)

    def test_the_hook_never_seeds_docs_audit_in_a_repo_that_has_not_opted_in(self):
        r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "abc123",
                            "cwd": str(self.repo)})
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertFalse((self.repo / "docs" / "audit").exists(),
                          "the hook must not auto-create docs/audit/ in a repo that never "
                          "opted into the Audit Mandate (AL0.2, PK-03)")

    def test_the_hook_degrades_to_the_pack_local_fallback_instead(self):
        r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "abc123",
                            "cwd": str(self.repo)})
        self.assertEqual(0, r.returncode, r.stderr)
        fallback = self.repo / ".agents" / "log" / "audit" / ".run-starts.json"
        self.assertTrue(fallback.exists(),
                         "the marker degrades to the pack's own local area, same as "
                         "append's resolve_default_root (D10)")


if __name__ == "__main__":
    unittest.main()
