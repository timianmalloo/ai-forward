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

    def _run_hook(self, payload, env_extra=None, host="claude", cwd=None):
        env = dict(os.environ)
        env.pop("AGENT_SESSION", None)
        env["AGENT_HOST"] = host
        env.update(env_extra or {})
        return subprocess.run([sys.executable, str(self.hook), "--host", host], cwd=str(cwd or self.repo),
                              input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=30)

    def _starts(self, cwd=None):
        cwd = self.repo if cwd is None else cwd
        # Audit opt-in is resolved against the payload cwd, independently of check discovery.
        root = cwd / "docs" if (cwd / "docs" / "audit").is_dir() else cwd / ".agents" / "log"
        p = root / "audit" / ".run-starts.json"
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

    def _assert_ancestor_check_not_run(self):
        parent = self.repo.parent
        (parent / ".agents").mkdir()
        (parent / ".agents" / "session-checks.json").write_text(json.dumps({"checks": [{
            "name": "ancestor-check",
            "argv": ["{python}", "-c", "from pathlib import Path; Path('ancestor-ran').write_text('ran')"],
        }]}), encoding="utf-8")
        for cwd in (self.repo, self.repo / "src" / "nested"):
            with self.subTest(cwd=cwd):
                cwd.mkdir(parents=True, exist_ok=True)
                (parent / "ancestor-ran").unlink(missing_ok=True)
                r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "plain-boundary",
                                    "cwd": str(cwd)}, cwd=cwd)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("__harness__:plain-boundary", self._starts(cwd), "the marker still runs")
                self.assertFalse((parent / "ancestor-ran").exists(),
                                 "an installed plain project must not execute an ancestor declaration")
                self.assertEqual("", r.stdout)
                self.assertEqual("", r.stderr)

    def test_installed_plain_boundary_resolves_payload_and_hook_aliases(self):
        parent = self.repo.parent
        (parent / '.agents').mkdir()
        (parent / '.agents/session-checks.json').write_text(json.dumps({'checks': [{
            'name': 'ancestor', 'argv': ['{python}', '-c',
                'from pathlib import Path; Path("ancestor-ran").write_text("ran")']}]}), encoding='utf-8')
        alias = parent / 'project-alias'
        try:
            alias.symlink_to(self.repo, target_is_directory=True)
        except OSError:
            if os.name == 'nt':
                self.skipTest('Directory symlinks require host privileges; portable Windows case control is separate')
            raise
        original_hook = self.hook
        for payload_cwd, hook in ((alias, original_hook),
                                  (self.repo, alias / 'docs/ai-forward-pack/hooks/session-start.py')):
            with self.subTest(payload_cwd=payload_cwd, hook=hook):
                self.hook = hook
                (parent / 'ancestor-ran').unlink(missing_ok=True)
                result = self._run_hook({'hook_event_name': 'SessionStart', 'session_id': 'alias',
                                         'cwd': str(payload_cwd)}, cwd=self.repo)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertFalse((parent / 'ancestor-ran').exists(), 'Aliases must not bypass the installed boundary')
        self.hook = original_hook

    def test_installed_hook_does_not_discover_checks_from_an_unrelated_payload_project(self):
        outside = self.repo.parent / 'unrelated'
        (outside / '.agents').mkdir(parents=True)
        (outside / '.agents/session-checks.json').write_text(json.dumps({'checks': [{
            'name': 'unrelated', 'argv': ['{python}', '-c',
                'from pathlib import Path; Path("unrelated-ran").write_text("ran")']}]}), encoding='utf-8')
        result = self._run_hook({'hook_event_name': 'SessionStart', 'session_id': 'outside',
                                 'cwd': str(outside)}, cwd=self.repo)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse((outside / 'unrelated-ran').exists(),
                         'An installed hook must not discover commands outside its own project')

    def test_windows_case_alias_keeps_the_installed_boundary(self):
        # Run the actual function under Windows path semantics, not a native-host claim.
        import importlib.util
        import ntpath
        from types import SimpleNamespace
        spec = importlib.util.spec_from_file_location('startup_case_control', HOOK)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        def normalized(path):
            return ntpath.normcase(ntpath.normpath(path))
        ancestor = normalized(r'C:\.agents\session-checks.json')
        path = SimpleNamespace(**{name: getattr(ntpath, name) for name in
            ('abspath', 'realpath', 'normcase', 'join', 'dirname', 'commonpath')},
            isfile=lambda p: normalized(p) == ancestor, exists=lambda p: False)
        module.os = SimpleNamespace(path=path)
        module.HERE = r'C:\Project\docs\ai-forward-pack\hooks'
        module.CHECKS_FILE = r'.agents\session-checks.json'
        for cwd in (r'C:\Project', r'C:\project', r'C:\project\src'):
            with self.subTest(cwd=cwd):
                self.assertEqual((None, None), module._checks_file(cwd))

    def test_installed_plain_project_does_not_run_an_ancestor_check(self):
        self._assert_ancestor_check_not_run()
        self.assertFalse((self.repo / ".git").exists(), "plain projects need no Git initialization")

    def _linked_project(self):
        # A real linked worktree with a .git file, without creating a fixture commit.
        primary = pathlib.Path(self.tmp) / "primary.git"
        linked = pathlib.Path(self.tmp) / "linked"
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        for command in (["git", "clone", "--bare", "--shared", "--quiet", str(ROOT), str(primary)],
                        ["git", "-C", str(primary), "worktree", "add", "--detach", "--no-checkout",
                         str(linked), "HEAD"]):
            r = subprocess.run(command, capture_output=True, text=True, env=env, timeout=30)
            self.assertEqual(r.returncode, 0, r.stderr)
        shutil.copytree(self.repo / "docs", linked / "docs")
        self.repo = linked
        self.hook = linked / "docs" / "ai-forward-pack" / "hooks" / "session-start.py"
        self.audit = linked / "docs" / "ai-forward-pack" / "scripts" / "audit-log.py"
        self.assertTrue((linked / ".git").is_file())

    def _assert_own_check_runs_from_subdirectory(self):
        self._declare_checks({"name": "project-check", "argv": ["{python}", "-c",
                             "from pathlib import Path; Path('project-ran').write_text(str(Path.cwd()))"]})
        cwd = self.repo / "src" / "nested"
        cwd.mkdir(parents=True, exist_ok=True)
        r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "plain-own", "cwd": str(cwd)}, cwd=cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.repo.samefile(pathlib.Path((self.repo / "project-ran").read_text())),
                        'The check must execute in this project, not an unrelated directory')
        self.assertIn("__harness__:plain-own", self._starts(cwd))
        self.assertEqual("", r.stdout)
        self.assertEqual("", r.stderr)

    def test_own_check_directory_assertion_accepts_a_physical_project_alias(self):
        alias = self.repo.parent / 'own-alias'
        try:
            alias.symlink_to(self.repo, target_is_directory=True)
        except OSError:
            if os.name == 'nt':
                self.skipTest('Directory symlinks require host privileges')
            raise
        self.repo = alias
        self._assert_own_check_runs_from_subdirectory()

    def test_installed_plain_project_runs_its_own_check_from_a_subdirectory(self):
        self._assert_own_check_runs_from_subdirectory()

    def test_installed_linked_project_does_not_run_an_ancestor_check(self):
        self._linked_project()
        self._assert_ancestor_check_not_run()

    def test_installed_linked_project_runs_its_own_check_from_a_subdirectory(self):
        self._linked_project()
        self._assert_own_check_runs_from_subdirectory()

    def test_nearest_declaration_within_an_installed_project_wins(self):
        self._declare_checks({"name": "root-check", "argv": ["{python}", "-c",
                             "from pathlib import Path; Path('root-ran').write_text('ran')"]})
        project = self.repo
        self.repo = project / "src"
        self.repo.mkdir()
        self._declare_checks({"name": "nearest-check", "argv": ["{python}", "-c",
                             "from pathlib import Path; Path('nearest-ran').write_text(str(Path.cwd()))"]})
        self.repo = project
        cwd = project / "src" / "nested"
        cwd.mkdir()
        r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "nearest", "cwd": str(cwd)}, cwd=cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((project / "src").samefile(pathlib.Path((project / "src" / "nearest-ran").read_text())),
                        'The nearest declared check must execute in its own directory')
        self.assertFalse((project / "root-ran").exists())
        self.assertIn("__harness__:nearest", self._starts(cwd))

    def test_source_hook_keeps_git_root_discovery(self):
        self.hook = HOOK
        r = subprocess.run(["git", "init", "--quiet", str(self.repo)], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self._assert_own_check_runs_from_subdirectory()
        (self.repo / ".agents" / "session-checks.json").unlink()
        parent = self.repo.parent
        (parent / ".agents").mkdir()
        (parent / ".agents" / "session-checks.json").write_text(json.dumps({"checks": [{
            "name": "ancestor-check", "argv": ["{python}", "-c",
                                                   "from pathlib import Path; Path('ancestor-ran').write_text('ran')"],
        }]}), encoding="utf-8")
        r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "source-boundary",
                            "cwd": str(self.repo / "src" / "nested")}, cwd=self.repo / "src" / "nested")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((parent / "ancestor-ran").exists())
        self.assertIn("__harness__:source-boundary", self._starts(self.repo / "src" / "nested"))

    def test_source_hook_keeps_linked_git_root_discovery(self):
        self._linked_project()
        self.hook = HOOK
        self._assert_ancestor_check_not_run()
        self._assert_own_check_runs_from_subdirectory()

    def test_source_hook_keeps_plain_ancestor_discovery_without_an_installed_boundary(self):
        self.hook = HOOK
        parent = self.repo.parent
        (parent / ".agents").mkdir()
        (parent / ".agents" / "session-checks.json").write_text(json.dumps({"checks": [{
            "name": "source-ancestor-check", "argv": ["{python}", "-c",
                                                          "from pathlib import Path; Path('ancestor-ran').write_text('ran')"],
        }]}), encoding="utf-8")
        r = self._run_hook({"hook_event_name": "SessionStart", "session_id": "source-plain", "cwd": str(self.repo)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((parent / "ancestor-ran").exists(), "source hooks keep the existing ancestor search")
        self.assertIn("__harness__:source-plain", self._starts())

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

    def test_agy_hooks_config_wires_pre_invocation_and_pre_tool_use(self):
        config = json.loads((ROOT / "pack" / "adapters" / "hooks" / "agy.ai-forward-hooks.json")
                            .read_text(encoding="utf-8"))
        self.assertIn("PreInvocation", config.get("session-start", {}))
        self.assertIn("PreToolUse", config.get("reread-guard", {}))
        pre_inv = [h["command"] for h in config["session-start"]["PreInvocation"]]
        self.assertTrue(any("session-start.py" in c for c in pre_inv))
        pre_tool = [h["command"] for entry in config["reread-guard"]["PreToolUse"] for h in entry.get("hooks", [])]
        self.assertTrue(any("reread-guard.py" in c for c in pre_tool))

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
