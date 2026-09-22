"""mail-doorbell.py - a doorbell carries a count and a pointer, never a body (US-6).

Every host shape is asserted against the inbox body: if the body ever appears in a hook
response the test fails. The builder has no body parameter by construction.
"""
import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "pack" / "adapters" / "hooks"
DOORBELL = HOOKS / "mail-doorbell.py"
MAIL = ROOT / "pack" / "scripts" / "coord-mail.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


db = _load("mail_doorbell_under_test", DOORBELL)
mail = _load("coord_mail_for_doorbells", MAIL)

SECRET = "SECRET-BODY-must-never-ring"
HOST_EVENTS = [("claude", "PreToolUse"), ("claude", "UserPromptSubmit"),
               ("grok", "PreToolUse"), ("grok", "UserPromptSubmit"),
               ("agy", "PreInvocation"), ("copilot", "preToolUse"), ("copilot", "agentStop")]


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="doorbell-")).resolve()
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        subprocess.run(["git", "-C", str(self.tmp), "init", "-q"], check=True)
        self.root = self.tmp / ".agents"
        self.root.mkdir()
        now = time.time()
        self.old = mail.append_mail(self.root, "p2", {"to": "p6", "kind": "note", "body": "stale"},
                                    now=now - mail.DOORBELL_EXPIRY_S - 60)
        self.a = mail.append_mail(self.root, "p2", {"to": "p6", "kind": "delegate", "body": SECRET}, now=now - 5)
        self.acked = mail.append_mail(self.root, "p2", {"to": "p6", "kind": "note", "body": "seen"}, now=now - 4)
        mail.append_ack(self.root, "p6", self.acked)
        self.b = mail.append_mail(self.root, "p2", {"to": "*", "kind": "kick", "body": "all"}, now=now - 2)
        mail.append_mail(self.root, "p2", {"to": "p8", "kind": "note", "body": "not mine"}, now=now - 1)

    def env(self, session="p6"):
        env = {k: v for k, v in os.environ.items() if k not in ("AGENT_SESSION", "COORD_ROOT", "AGENT_HOST")}
        if session:
            env["AGENT_SESSION"] = session
        return env

    def run_hook(self, host, event, payload, session="p6"):
        return subprocess.run([sys.executable, str(DOORBELL), "--host", host, "--event", event],
                              input=json.dumps(payload), cwd=str(self.tmp), env=self.env(session),
                              capture_output=True, text=True, encoding="utf-8", check=False)


class Builder(Fixture):
    def test_state_counts_recent_unacked_only_and_points_at_the_newest(self):
        count, pointer = mail.doorbell_state(self.root, "p6", now=time.time())
        self.assertEqual(count, 2, "the stale note and the acked note do not ring")
        self.assertEqual(pointer, self.b)

    def test_builder_has_no_body_parameter(self):
        params = inspect.signature(db.payload_for).parameters
        self.assertNotIn("body", params)
        self.assertNotIn("entries", params)
        self.assertEqual(list(params)[:5], ["host", "event", "session", "count", "pointer"])

    def test_every_host_shape_carries_count_and_pointer_and_no_body(self):
        for host, event in HOST_EVENTS:
            with self.subTest(host=host, event=event):
                payload = db.payload_for(host, event, "p6", 2, self.b)
                text = json.dumps(payload)
                self.assertNotIn(SECRET, text)
                self.assertIn("2 new for p6", text)
                self.assertIn(self.b, text)
        self.assertEqual(db.payload_for("claude", "PreToolUse", "p6", 2, self.b),
                         {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "additionalContext": db.doorbell_text("p6", 2, self.b)}})
        self.assertEqual(db.payload_for("grok", "UserPromptSubmit", "p6", 2, self.b)["hookSpecificOutput"]["hookEventName"],
                         "UserPromptSubmit")
        # Antigravity parses the reply with protojson: injectSteps items are objects (docs/hooks); a string
        # list was rejected live on 2026-09-20 ("failed to unmarshal result ... via protojson").
        self.assertEqual(db.payload_for("agy", "PreInvocation", "p6", 2, self.b),
                         {"injectSteps": [{"ephemeralMessage": db.doorbell_text("p6", 2, self.b)}]})
        self.assertEqual(db.payload_for("copilot", "preToolUse", "p6", 2, self.b),
                         {"additionalContext": db.doorbell_text("p6", 2, self.b)})
        self.assertEqual(db.payload_for("copilot", "agentStop", "p6", 2, self.b),
                         {"decision": "block", "reason": db.doorbell_text("p6", 2, self.b)})

    def test_count_zero_and_stop_guard_ring_nothing(self):
        for host, event in HOST_EVENTS:
            with self.subTest(host=host, event=event):
                self.assertIsNone(db.payload_for(host, event, "p6", 0, None))
        self.assertIsNone(db.payload_for("copilot", "agentStop", "p6", 2, self.b, stop_hook_active=True))
        self.assertIsNotNone(db.payload_for("copilot", "preToolUse", "p6", 2, self.b, stop_hook_active=True))

    def test_a_hundred_line_inbox_rings_within_budget(self):
        # 50 queued is the cap, so the second fifty need the first fifty acknowledged by someone
        # (p1's acks do not count as p9's): 100 messages + 50 acks = 150 lines in the file.
        first = [mail.append_mail(self.root, "p2", {"to": "p9", "kind": "note", "body": "n%d" % i})
                 for i in range(mail.QUEUE_CAP)]
        for mail_id in first:
            mail.append_ack(self.root, "p1", mail_id)
        for i in range(mail.QUEUE_CAP):
            mail.append_mail(self.root, "p2", {"to": "p9", "kind": "note", "body": "m%d" % i})
        self.assertEqual(len((self.root / "mail" / "p9.jsonl").read_text(encoding="utf-8").splitlines()), 150)
        started = time.perf_counter()
        count, pointer = mail.doorbell_state(self.root, "p9", now=time.time())
        elapsed = time.perf_counter() - started
        self.assertEqual(count, 100 + 1, "100 unread for p9 plus the broadcast")
        self.assertLess(elapsed, 0.25)


class HookCli(Fixture):
    def test_claude_hook_rings_with_count_and_pointer(self):
        proc = self.run_hook("claude", "PreToolUse", {"hook_event_name": "PreToolUse", "session_id": "x",
                                                      "tool_name": "Bash", "tool_input": {}})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertIn("2 new for p6", out["hookSpecificOutput"]["additionalContext"])
        self.assertNotIn(SECRET, proc.stdout)

    def test_event_falls_back_to_the_payload(self):
        proc = subprocess.run([sys.executable, str(DOORBELL), "--host", "claude"],
                              input=json.dumps({"hook_event_name": "UserPromptSubmit"}), cwd=str(self.tmp),
                              env=self.env(), capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(json.loads(proc.stdout)["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")

    def test_copilot_agent_stop_blocks_only_when_unguarded(self):
        blocked = self.run_hook("copilot", "agentStop", {"sessionId": "x"})
        self.assertEqual(json.loads(blocked.stdout)["decision"], "block")
        guarded = self.run_hook("copilot", "agentStop", {"sessionId": "x", "stop_hook_active": True})
        self.assertEqual(guarded.returncode, 0)
        self.assertEqual(guarded.stdout.strip(), "")

    def test_no_session_or_unreadable_store_is_silent_and_exit_0(self):
        proc = self.run_hook("claude", "PreToolUse", {}, session=None)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, ""))
        (self.root / "mail" / "p6.jsonl").write_text("{broken\n", encoding="utf-8", newline="\n")
        proc = self.run_hook("claude", "PreToolUse", {})
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, ""))
        mail.append_ack(self.root, "p7", self.b)   # p7 has no inbox of its own; the broadcast is now acked
        proc = self.run_hook("grok", "PreToolUse", {}, session="p7")
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, ""), "an empty inbox rings nothing")


class AdapterConfigs(unittest.TestCase):
    RESOLVER = "import sys;print(sys.executable)"

    def _commands(self, data):
        found = []

        def walk(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in ("command", "bash", "powershell") and isinstance(value, str):
                        found.append(value)
                    else:
                        walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(data)
        return [c for c in found if "mail-doorbell.py" in c]

    def _load_json(self, name):
        return json.loads((HOOKS / name).read_text(encoding="utf-8"))

    def test_claude_and_grok_ring_at_pre_tool_use_and_user_prompt_submit(self):
        for name in ("claude-code.settings.hooks.json", "grok.ai-forward-hooks.json"):
            data = self._load_json(name)["hooks"]
            host = "claude" if name.startswith("claude") else "grok"
            for event in ("PreToolUse", "UserPromptSubmit"):
                with self.subTest(name=name, event=event):
                    cmds = [h["command"] for entry in data[event] for h in entry.get("hooks", [])
                            if "mail-doorbell.py" in h["command"]]
                    self.assertEqual(len(cmds), 1)
                    self.assertIn("--host " + host, cmds[0])
                    self.assertIn("--event " + event, cmds[0])
                    self.assertIn(self.RESOLVER, cmds[0])
            entries = [e for e in data["PreToolUse"] if any("mail-doorbell.py" in h["command"] for h in e["hooks"])]
            self.assertNotIn("matcher", entries[0], "the doorbell rings at every tool, not only Read")

    def test_agy_rings_at_pre_invocation_as_inject_steps(self):
        data = self._load_json("agy.ai-forward-hooks.json")
        cmds = [h["command"] for h in data["mail-doorbell"]["PreInvocation"]]
        self.assertEqual(len(cmds), 1)
        self.assertIn("--host agy", cmds[0])
        self.assertIn("--event PreInvocation", cmds[0])
        self.assertIn(self.RESOLVER, cmds[0])
        self.assertIn("git rev-parse --show-toplevel", cmds[0])

    def test_copilot_rings_at_pre_tool_use_and_blocks_at_agent_stop(self):
        data = self._load_json("copilot.ai-forward-hooks.json")["hooks"]
        for event in ("preToolUse", "agentStop"):
            with self.subTest(event=event):
                entries = [e for e in data[event] if "mail-doorbell.py" in e.get("bash", "")]
                self.assertEqual(len(entries), 1)
                self.assertIn("--host copilot --event " + event, entries[0]["bash"])
                self.assertIn("--host copilot --event " + event, entries[0]["powershell"])
                self.assertNotIn("matcher", entries[0])

    def test_readme_documents_the_doorbell(self):
        readme = (HOOKS / "README.md").read_text(encoding="utf-8")
        self.assertIn("mail-doorbell.py", readme)
        self.assertIn("never a body", readme)


if __name__ == "__main__":
    unittest.main()
