"""Hook cost (bench decision B15, 2026-10-14). Measured in pack-on bench cells: three or four hook
processes before every tool call, each `git -> sh -> python`; a Grok file read took a median 11 s
pack-on against ~0 pack-off, and the coordination hooks ran in cells that never coordinate. The
session-start marker landed in the task's working copy.

Controls, one failure each:
  - every surface registers ONE pack command per host event (the dispatcher), and the dispatcher
    still runs every hook the surface ran before, with a blocking hook still blocking;
  - the coordination hooks write nothing and print nothing when the repository's coordination
    record holds nothing, even with a session identity in the environment;
  - the session-start marker is kept in the checkout's git dir, never in its working tree.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HOOKS = REPO / "pack" / "adapters" / "hooks"
SCRIPTS = REPO / "pack" / "scripts"
DISPATCH = HOOKS / "dispatch.py"
LAUNCHER = "git -c alias.aif-hook=!sh aif-hook docs/ai-forward-pack/hooks/run-hook.sh "
# Startup entries on Claude, Grok and Copilot run the dispatcher through the bounded upward
# search for run-hook.sh (plain-project startup from a child directory, revision 108).
START_EVENTS = ("SessionStart", "SubagentStart", "sessionStart", "subagentStart")


def launcher_for(host, event):
    if host in ("claude", "grok", "copilot") and event in START_EVENTS:
        return _load(SCRIPTS / "pack-apply.py", "pack_apply_launcher").STARTUP_LAUNCHER
    return LAUNCHER


PACK_HOOKS = ("reread-guard.py", "mail-doorbell.py", "heartbeat.py", "git-identity-guard.py",
              "owner-review-gate.py", "session-start.py", "dispatch.py")

# What each surface ran per event before the dispatcher (revision 100's configs). The dispatcher
# must run exactly these, in this order: a hook dropped here is a control silently lost.
ROUTES_BEFORE = {
    "claude": {
        "PreToolUse": ["reread-guard.py", "mail-doorbell.py", "git-identity-guard.py"],
        "UserPromptSubmit": ["reread-guard.py", "mail-doorbell.py"],
        "SessionStart": ["session-start.py"], "SubagentStart": ["session-start.py"],
        "PostToolUse": ["heartbeat.py"],
        "Stop": ["heartbeat.py", "owner-review-gate.py"], "SubagentStop": ["owner-review-gate.py"],
    },
    "grok": {
        "PreToolUse": ["reread-guard.py", "mail-doorbell.py", "heartbeat.py", "git-identity-guard.py"],
        "UserPromptSubmit": ["reread-guard.py", "mail-doorbell.py"],
        "SessionStart": ["session-start.py"], "SubagentStart": ["session-start.py"],
        "Stop": ["owner-review-gate.py"],
    },
    "copilot": {
        "sessionStart": ["session-start.py"], "subagentStart": ["session-start.py"],
        "preToolUse": ["reread-guard.py", "mail-doorbell.py", "git-identity-guard.py"],
        "postToolUse": ["heartbeat.py"], "userPromptSubmitted": ["reread-guard.py"],
        "agentStop": ["mail-doorbell.py", "heartbeat.py", "owner-review-gate.py"],
        "subagentStop": ["mail-doorbell.py", "heartbeat.py", "owner-review-gate.py"],
    },
    "agy": {
        "PreToolUse": ["reread-guard.py"], "PreInvocation": ["session-start.py", "mail-doorbell.py"],
        "PostToolUse": ["heartbeat.py"], "Stop": ["heartbeat.py", "owner-review-gate.py"],
    },
}


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shipped_commands(host):
    """[(event, command)] for every handler in a host's shipped hook config."""
    out = []
    if host in ("claude", "grok"):
        name = "claude-code.settings.hooks.json" if host == "claude" else "grok.ai-forward-hooks.json"
        config = json.loads((HOOKS / name).read_text(encoding="utf-8"))["hooks"]
        for event, entries in config.items():
            out += [(event, h["command"]) for e in entries for h in e["hooks"]]
    elif host == "copilot":
        config = json.loads((HOOKS / "copilot.ai-forward-hooks.json").read_text(encoding="utf-8"))["hooks"]
        for event, entries in config.items():
            for h in entries:
                assert h["bash"] == h["powershell"], h
                out.append((event, h["bash"]))
    else:
        config = json.loads((HOOKS / "agy.ai-forward-hooks.json").read_text(encoding="utf-8"))
        for section in config.values():
            for event, entries in section.items():
                if not isinstance(entries, list):
                    continue
                for e in entries:
                    out += [(event, h["command"]) for h in (e["hooks"] if "hooks" in e else [e])]
    return out


class OneProcessPerEvent(unittest.TestCase):
    def test_each_surface_registers_one_pack_command_per_event(self):
        """Fails if a surface launches more than one pack hook process for one host event."""
        for host in ROUTES_BEFORE:
            per_event = {}
            for event, command in shipped_commands(host):
                if any(hook in command for hook in PACK_HOOKS):
                    per_event.setdefault(event, []).append(command)
            self.assertEqual(sorted(per_event), sorted(ROUTES_BEFORE[host]), host)
            for event, commands in per_event.items():
                self.assertEqual(commands, [launcher_for(host, event) + "dispatch.py --host {} --event {}".format(host, event)],
                                 "{} {}".format(host, event))

    def test_the_dispatcher_runs_every_hook_each_surface_ran_before(self):
        """Fails if the dispatcher drops, adds or reorders a hook on any host event."""
        routes = _load(DISPATCH, "dispatch_routes").ROUTES
        for host, events in ROUTES_BEFORE.items():
            for event, hooks in events.items():
                self.assertEqual([script for script, _args in routes[host][event]], hooks,
                                 "{} {}".format(host, event))

    def dispatch(self, host, event, payload, env_extra=None, cwd=None):
        env = {k: v for k, v in os.environ.items() if k not in ("AGENT_SESSION", "AGENT_HOST", "COORD_ROOT")}
        env.update(env_extra or {})
        return subprocess.run([sys.executable, str(DISPATCH), "--host", host, "--event", event],
                              input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8",
                              env=env, cwd=str(cwd or REPO), timeout=60)

    def test_a_blocking_hook_still_blocks_through_the_dispatcher(self):
        """Fails if the git-identity guard's exit 2 (PK-07) is lost inside the dispatcher."""
        command = "git config user.email someone@example.com"
        cases = {
            ("claude", "PreToolUse"): {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                       "tool_input": {"command": command}},
            ("grok", "PreToolUse"): {"hookEventName": "PreToolUse", "toolName": "run_terminal_cmd",
                                     "toolInput": {"command": command}},
            ("copilot", "preToolUse"): {"toolName": "bash", "toolArgs": {"command": command}},
        }
        for (host, event), payload in cases.items():
            payload["session_id"] = payload["sessionId"] = "hc-" + uuid.uuid4().hex[:8]
            proc = self.dispatch(host, event, payload)
            self.assertEqual(proc.returncode, 2, "{}: {}".format(host, proc.stderr))
            self.assertIn("PK-07", proc.stderr)
            allowed = dict(payload, tool_input={"command": "git config user.email"},
                           toolInput={"command": "git config user.email"}, toolArgs={"command": "git status"})
            self.assertEqual(self.dispatch(host, event, allowed).returncode, 0, host)

    def test_the_third_identical_read_warns_through_the_dispatcher(self):
        """Fails if the re-read guard's warning does not reach stdout as one host-shaped object."""
        session = "hc-" + uuid.uuid4().hex[:8]
        payload = {"hook_event_name": "PreToolUse", "session_id": session, "tool_name": "Read",
                   "tool_input": {"file_path": str(REPO / "README.md")}}
        outs = [self.dispatch("claude", "PreToolUse", payload).stdout for _ in range(3)]
        self.assertEqual(outs[:2], ["", ""])
        message = json.loads(outs[2])["hookSpecificOutput"]["systemMessage"]
        self.assertIn("read 3 times", message)

    def test_two_hook_responses_merge_into_one_host_object(self):
        """Fails if two hooks answering one event print two JSON documents (a host parses one)."""
        merge = _load(DISPATCH, "dispatch_merge").merge_outputs
        merged = json.loads(merge(['{"decision": "block", "reason": "mail"}',
                                   '{"decision": "block", "reason": "owner"}']))
        self.assertEqual(merged, {"decision": "block", "reason": "mail\nowner"})
        merged = json.loads(merge([
            '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "systemMessage": "reread"}}', "",
            '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "mail"}}']))
        self.assertEqual(merged, {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                         "systemMessage": "reread", "additionalContext": "mail"}})
        self.assertEqual(merge(["", ""]), "")


class Migration(unittest.TestCase):
    """An installed repo carries revision 100's per-hook commands. A refresh that only appended the
    dispatcher would run every hook twice."""

    def setUp(self):
        self.pa = _load(SCRIPTS / "pack-apply.py", "pack_apply_hook_cost")

    def test_claude_settings_refresh_retires_the_per_hook_commands_and_keeps_custom_ones(self):
        """Fails if a refreshed .claude/settings.json still launches a pack hook outside the dispatcher."""
        old = {"hooks": {}}
        for event, hooks in ROUTES_BEFORE["claude"].items():
            for hook in hooks:
                args = " --event " + event if hook in ("mail-doorbell.py", "heartbeat.py", "owner-review-gate.py") else ""
                old["hooks"].setdefault(event, []).append(
                    {"hooks": [{"type": "command", "command": LAUNCHER + hook + " --host claude" + args, "timeout": 10}]})
        custom = {"matcher": "Bash", "hooks": [{"type": "command", "command": LAUNCHER + "../../../tools/guard.py"}]}
        old["hooks"]["PreToolUse"].insert(0, custom)
        snippet = (HOOKS / "claude-code.settings.hooks.json").read_text(encoding="utf-8")
        merged = json.loads(self.pa.merge_claude_settings(snippet, json.dumps(old)))
        self.assertEqual(merged["hooks"]["PreToolUse"][0], custom)
        for event in ROUTES_BEFORE["claude"]:
            commands = [h["command"] for e in merged["hooks"][event] for h in e["hooks"]]
            pack = [c for c in commands if any(hook in c for hook in PACK_HOOKS)]
            self.assertEqual(pack, [launcher_for("claude", event) + "dispatch.py --host claude --event " + event], event)
        self.assertEqual(merged, json.loads(self.pa.merge_claude_settings(snippet, json.dumps(merged))))

    def test_agy_refresh_retires_the_per_hook_sections_and_keeps_project_owned_ones(self):
        """Fails if .agents/hooks.json keeps a revision-100 named section beside the dispatcher's."""
        old = {name: {"enabled": True} for name in
               ("reread-guard", "session-start", "mail-doorbell", "heartbeat", "owner-review-gate")}
        old["ownership-guard"] = {"PreToolUse": [], "enabled": False}
        source = (HOOKS / "agy.ai-forward-hooks.json").read_text(encoding="utf-8")
        merged = json.loads(self.pa.merge_named_hook_bundles(source, json.dumps(old)))
        self.assertEqual(sorted(merged), sorted(set(json.loads(source)) | {"ownership-guard"}))
        self.assertEqual(merged["ownership-guard"], old["ownership-guard"])


class CoordinationOff(unittest.TestCase):
    """A session identity alone does not make coordination on: the repository's coordination record
    must hold something (a session ledger, an inbox, or the request store)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "r"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(self.repo), check=True, capture_output=True)
        # the audit fallback's directory alone (AL0.2) is not coordination state
        (self.repo / ".agents" / "log" / "audit").mkdir(parents=True)

    def run_hook(self, script, host, event, payload):
        env = {k: v for k, v in os.environ.items() if k not in ("AGENT_SESSION", "AGENT_HOST", "COORD_ROOT")}
        env["AGENT_SESSION"] = "s1"
        return subprocess.run([sys.executable, str(HOOKS / script), "--host", host, "--event", event],
                              input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8",
                              env=env, cwd=str(self.repo), timeout=60)

    def ledgers(self):
        return sorted(p.name for p in (self.repo / ".agents" / "log").iterdir() if p.is_file())

    def test_coordination_hooks_write_and_print_nothing_without_a_coordination_record(self):
        """Fails if heartbeat, doorbell or owner gate writes a ledger in a repo that never coordinated."""
        stop = {"hook_event_name": "Stop", "session_id": "abc", "cwd": str(self.repo)}
        for script, event in (("heartbeat.py", "Stop"), ("mail-doorbell.py", "PreToolUse"),
                              ("owner-review-gate.py", "Stop")):
            proc = self.run_hook(script, "claude", event, stop)
            self.assertEqual((proc.returncode, proc.stdout), (0, ""), script + proc.stderr)
        self.assertEqual(self.ledgers(), [])
        self.assertFalse((self.repo / ".git" / "coord").exists(), "no heartbeat accumulator either")

    def test_a_registered_session_still_beats(self):
        """Fails if the off-switch also silences a repository that does coordinate."""
        core = _load(SCRIPTS / "coord-core.py", "coord_core_hook_cost")
        core.append_event(self.repo / ".agents", {"kind": "session-start", "session": "s1", "agent": "s1",
                                                  "wi": "WI-0", "path": "-", "at": 1.0, "worktree": "r"})
        proc = self.run_hook("heartbeat.py", "claude", "Stop",
                             {"hook_event_name": "Stop", "session_id": "abc", "cwd": str(self.repo)})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = [json.loads(line) for line in (self.repo / ".agents" / "log" / "s1.jsonl")
                .read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual([r["kind"] for r in rows], ["session-start", "heartbeat"])


class MarkerOutsideTheTree(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "r"
        pack = self.repo / "docs" / "ai-forward-pack"
        (pack / "hooks").mkdir(parents=True)
        (pack / "scripts").mkdir(parents=True)
        for name in ("dispatch.py", "session-start.py", "coord_identity.py"):
            shutil.copy(HOOKS / name, pack / "hooks" / name)
        shutil.copy(SCRIPTS / "audit-log.py", pack / "scripts" / "audit-log.py")
        (pack / "templates").mkdir()
        shutil.copy(REPO / "pack" / "templates" / "audit-explorer.template.html", pack / "templates")
        self.hook, self.audit = pack / "hooks" / "dispatch.py", pack / "scripts" / "audit-log.py"
        for args in (["init", "-q", "-b", "main"], ["add", "-A"],
                     ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "pack"]):
            subprocess.run(["git", *args], cwd=str(self.repo), check=True, capture_output=True)

    def status(self):
        return subprocess.run(["git", "status", "--porcelain", "--ignored", "--untracked-files=all"],
                              cwd=str(self.repo), capture_output=True, text=True, check=True).stdout

    def test_the_session_start_marker_leaves_the_working_tree_unchanged_and_still_measures(self):
        """Fails if the hook writes into the task's working copy, or the marker is lost to append."""
        env = {k: v for k, v in os.environ.items() if k not in ("AGENT_SESSION", "AGENT_HOST")}
        proc = subprocess.run([sys.executable, str(self.hook), "--host", "claude", "--event", "SessionStart"],
                              cwd=str(self.repo),
                              input=json.dumps({"hook_event_name": "SessionStart", "session_id": "abc",
                                                "cwd": str(self.repo)}),
                              capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.status(), "", "the session-start hook changed the working tree")
        done = subprocess.run([sys.executable, str(self.audit), "append", "--shortname", "close",
                               "--session", "node-a", "--kind", "manual", "--prompt", "p", "--summary", "s"],
                              cwd=str(self.repo), capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        log = self.repo / ".agents" / "log" / "audit" / "audit-log.jsonl"
        entry = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(entry.get("duration_source"), "session-start-hook", entry)

    def test_a_dispatch_times_itself_only_where_the_git_dir_asks(self):
        """Fails if a dispatch writes timing nobody asked for, or does not time itself where the bench
        asked by creating <git-dir>/ai-forward/hook-times.jsonl (bench REC-UNREAD-A, 2026-10-17:
        Claude Code keeps no start for a hook, so its hook time was not recorded)."""
        env = {k: v for k, v in os.environ.items() if k not in ("AGENT_SESSION", "AGENT_HOST")}
        payload = json.dumps({"hook_event_name": "SessionStart", "session_id": "abc", "cwd": str(self.repo)})

        def run():
            proc = subprocess.run([sys.executable, str(self.hook), "--host", "claude", "--event", "SessionStart"],
                                  cwd=str(self.repo), input=payload, capture_output=True, text=True, env=env,
                                  timeout=60)
            self.assertEqual(proc.returncode, 0, proc.stderr)

        times = self.repo / ".git" / "ai-forward" / "hook-times.jsonl"
        run()
        self.assertFalse(times.exists(), "a dispatch created the timing file")
        times.write_text("", encoding="utf-8")
        run()
        run()
        rows = [json.loads(line) for line in times.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(r["host"], r["event"], r["hooks"], r["exit"]) for r in rows],
                         [("claude", "SessionStart", ["session-start.py"], 0)] * 2)
        self.assertTrue(all(isinstance(r["ms"], (int, float)) and r["ms"] >= 0 and r["start"] for r in rows), rows)
        self.assertEqual(self.status(), "", "the timing changed the working tree")

    def test_revision_109_is_the_hook_times_delta(self):
        """Fails if revision 109's frontmatter is not its own one-row delta, or a path it lists is missing."""
        raw = (REPO / "pack" / "adapters" / "INSTALL.md").read_bytes()
        frontmatter = raw.split(b"---\n", 2)[1].decode("utf-8")
        self.assertRegex(frontmatter, r"(?m)^revision: 109$")
        self.assertIn("bundle_version: '2026.10.17.1'", frontmatter)
        self.assertEqual(1, frontmatter.count("  - { type: changed,"))
        self.assertIn("hook-times.jsonl", frontmatter)
        for path in ("adapters/hooks/dispatch.py", "adapters/INSTALL.md"):
            self.assertTrue((REPO / "pack" / path).is_file(), path)

    def append(self):
        env = {k: v for k, v in os.environ.items() if k not in ("AGENT_SESSION", "AGENT_HOST")}
        done = subprocess.run([sys.executable, str(self.audit), "append", "--shortname", "close",
                               "--session", "node-a", "--kind", "manual", "--prompt", "p", "--summary", "s"],
                              cwd=str(self.repo), capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_the_fallback_log_writes_only_its_jsonl_and_an_opted_in_log_keeps_its_views(self):
        """Fails if an append in the AL0.2 fallback renders the viewer (~520 lines per bench cell), or if
        a repo that opted in (docs/audit/ exists) loses its rendered views. Owner decision, 2026-10-14."""
        self.append()
        fallback = self.repo / ".agents" / "log" / "audit"
        self.assertEqual(sorted(p.name for p in fallback.iterdir()), ["audit-log.jsonl"])
        (self.repo / "docs" / "audit").mkdir()
        self.append()
        opted = sorted(p.name for p in (self.repo / "docs" / "audit").iterdir())
        self.assertEqual(opted, ["audit-data.js", "audit-log.jsonl", "audit-log.md", "index.html"])


if __name__ == "__main__":
    unittest.main()
