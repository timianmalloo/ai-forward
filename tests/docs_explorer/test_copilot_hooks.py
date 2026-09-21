import importlib.util
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
SCRIPT = ROOT / "pack" / "scripts" / "coord-core.py"
HEARTBEAT = ROOT / "pack" / "adapters" / "hooks" / "heartbeat.py"
DOORBELL = ROOT / "pack" / "adapters" / "hooks" / "mail-doorbell.py"
GATE = ROOT / "pack" / "adapters" / "hooks" / "owner-review-gate.py"
MAIL = ROOT / "pack" / "scripts" / "coord-mail.py"
IDENTITY = ROOT / "pack" / "adapters" / "hooks" / "coord_identity.py"
FIXTURES = ROOT / "tests" / "docs_explorer" / "fixtures" / "harness"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = _load("coord_core_copilot_hooks", SCRIPT)
mail = _load("coord_mail_copilot_hooks", MAIL)
identity = _load("coord_identity_copilot_hooks", IDENTITY)


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class CopilotHooksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="copilot-hooks-")).resolve()
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir(parents=True)
        subprocess.run(["git", "-C", str(self.repo), "init", "-q"], check=True)
        (self.repo / "docs" / "audit").mkdir(parents=True)
        self.root = self.repo / ".agents"
        (self.root / "log").mkdir(parents=True)
        (self.repo / "src" / "Ingest").mkdir(parents=True)
        (self.repo / "src" / "Ingest" / "Reader.cs").write_text("class C {}\n", encoding="utf-8")

    def env(self, session="worker-copilot", **extra):
        env = {k: v for k, v in os.environ.items() if k not in ("COORD_ROOT", "AGENT_SESSION", "AGENT_NAME", "AGENT_HOST")}
        env["COORD_ROOT"] = str(self.root)
        if session:
            env["AGENT_SESSION"] = session
            env["AGENT_NAME"] = session
        env.update(extra)
        return env

    def run_script(self, script, *args, stdin=None, env=None):
        return subprocess.run([sys.executable, str(script), *args], cwd=str(self.repo),
                              env=env or self.env(), input=stdin, capture_output=True,
                              text=True, encoding="utf-8", check=False, timeout=30)

    def claim(self, session, path):
        core.append_event(self.root, core.make_event(
            kind="claim", session=session, agent=session, wi="WI-1", path=path, ttl=300, at=time.time()
        ))

    def ledger(self, session):
        path = self.root / "log" / f"{session}.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def native_payload(self):
        return {
            "hookEventName": "preToolUse",
            "sessionId": "cp-top",
            "cwd": str(self.repo),
            "toolName": "edit",
            "toolArgs": json.dumps({"path": str(self.repo / "src" / "Ingest" / "Reader.cs")}),
        }

    def plugin_payload(self):
        return {
            "input": {
                "cwd": str(self.repo),
                "toolCalls": [{
                    "name": "edit",
                    "args": json.dumps({"path": str(self.repo / "src" / "Ingest" / "Reader.cs")}),
                }],
            }
        }

    def native_patch_payload(self, patch=None):
        payload = fixture("copilot-native-apply-patch.json")
        payload["cwd"] = str(self.repo)
        payload["toolCalls"][0]["args"] = patch or payload["toolCalls"][0]["args"]
        return payload

    def test_native_hook_config_supports_copilot(self):
        result = self.run_script(SCRIPT, "hook", "--config", "--host", "copilot")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["version"], 1)
        entry = payload["hooks"]["preToolUse"][0]
        self.assertIn("coord-core.py hook --host copilot", entry["bash"])
        self.assertIn("coord-core.py hook --host copilot", entry["powershell"])
        self.assertIn("^(", entry["matcher"])

    def test_native_camel_case_payload_denies_non_holder_and_allows_holder(self):
        self.claim("holder", "src/Ingest/**")
        denied = self.run_script(SCRIPT, "hook", "--host", "copilot",
                                 stdin=json.dumps(self.native_payload()),
                                 env=self.env("other"))
        self.assertEqual(denied.returncode, 0, denied.stderr)
        self.assertEqual(core.hook_decision_of(json.loads(denied.stdout)), "deny")
        allowed = self.run_script(SCRIPT, "hook", "--host", "copilot",
                                  stdin=json.dumps(self.native_payload()),
                                  env=self.env("holder"))
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(core.hook_decision_of(json.loads(allowed.stdout)), "allow")

    def test_old_plugin_batch_payload_still_works_for_copilot(self):
        self.claim("holder", "src/Ingest/**")
        result = self.run_script(SCRIPT, "hook", "--host", "copilot",
                                 stdin=json.dumps(self.plugin_payload()),
                                 env=self.env("other"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(core.hook_decision_of(json.loads(result.stdout)), "deny")

    def test_batch_write_with_non_json_args_fails_closed(self):
        payload = self.plugin_payload()
        payload["input"]["toolCalls"][0]["args"] = "not-json"
        result = self.run_script(SCRIPT, "hook", "--host", "copilot",
                                 stdin=json.dumps(payload), env=self.env("other"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(core.hook_decision_of(json.loads(result.stdout)), "deny")

    def test_batch_write_without_path_fails_closed(self):
        payload = self.plugin_payload()
        payload["input"]["toolCalls"][0]["args"] = json.dumps({})
        result = self.run_script(SCRIPT, "hook", "--host", "copilot",
                                 stdin=json.dumps(payload), env=self.env("other"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(core.hook_decision_of(json.loads(result.stdout)), "deny")

    def test_batch_apply_patch_without_command_fails_closed(self):
        payload = self.plugin_payload()
        payload["input"]["toolCalls"][0]["name"] = "apply_patch"
        payload["input"]["toolCalls"][0]["args"] = json.dumps({})
        result = self.run_script(SCRIPT, "hook", "--host", "copilot",
                                 stdin=json.dumps(payload), env=self.env("other"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(core.hook_decision_of(json.loads(result.stdout)), "deny")

    def test_native_raw_apply_patch_allows_holder_and_denies_other_holder(self):
        self.claim("holder", "leased.txt")
        denied = self.run_script(SCRIPT, "hook", "--host", "copilot",
                                 stdin=json.dumps(self.native_patch_payload()),
                                 env=self.env("other"))
        self.assertEqual(denied.returncode, 0, denied.stderr)
        self.assertEqual(core.hook_decision_of(json.loads(denied.stdout)), "deny")
        allowed = self.run_script(SCRIPT, "hook", "--host", "copilot",
                                  stdin=json.dumps(self.native_patch_payload()),
                                  env=self.env("holder"))
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(core.hook_decision_of(json.loads(allowed.stdout)), "allow")

    def test_native_raw_apply_patch_malformed_or_traversal_fails_closed(self):
        bad_patches = (
            "not a patch",
            "*** Begin Patch\n*** Update File: ../outside.txt\n@@\n-a\n+b\n*** End Patch\n",
            "*** Begin Patch\n*** Update File: leased.txt\n*** Move to: ../outside.txt\n@@\n-a\n+b\n*** End Patch\n",
        )
        for patch in bad_patches:
            with self.subTest(patch=patch[:30]):
                result = self.run_script(SCRIPT, "hook", "--host", "copilot",
                                         stdin=json.dumps(self.native_patch_payload(patch)),
                                         env=self.env("other"))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(core.hook_decision_of(json.loads(result.stdout)), "deny")

    def test_batch_write_to_absolute_outside_path_fails_closed(self):
        outside = self.tmp / "outside.txt"
        outside.write_text("secret\n", encoding="utf-8")
        payload = self.plugin_payload()
        payload["input"]["toolCalls"][0]["args"] = json.dumps({"path": str(outside)})
        result = self.run_script(SCRIPT, "hook", "--host", "copilot",
                                 stdin=json.dumps(payload), env=self.env("other"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(core.hook_decision_of(json.loads(result.stdout)), "deny")

    def test_batch_write_to_symlink_or_junction_target_outside_fails_closed(self):
        outside_dir = self.tmp / "outside-dir"
        outside_dir.mkdir()
        (outside_dir / "secret.txt").write_text("secret\n", encoding="utf-8")
        payload = self.plugin_payload()
        if os.name == "nt":
            junction = self.repo / "junction"
            created = subprocess.run(
                [os.environ["ComSpec"], "/d", "/c", "mklink", "/J", str(junction), str(outside_dir)],
                capture_output=True, text=True, encoding="utf-8", timeout=5
            )
            self.assertEqual(0, created.returncode, created.stderr)
            self.addCleanup(junction.rmdir)
            target = junction / "secret.txt"
        else:
            link = self.repo / "outside-link"
            link.symlink_to(outside_dir, target_is_directory=True)
            self.addCleanup(link.unlink)
            target = link / "secret.txt"
        payload["input"]["toolCalls"][0]["args"] = json.dumps({"path": str(target)})
        result = self.run_script(SCRIPT, "hook", "--host", "copilot",
                                 stdin=json.dumps(payload), env=self.env("other"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(core.hook_decision_of(json.loads(result.stdout)), "deny")

    def test_heartbeat_uses_child_identity_not_parent_env_for_copilot_subagent(self):
        payload = {
            "hookEventName": "postToolUse",
            "sessionId": "cp-top",
            "agentId": "agent-7",
            "cwd": str(self.repo),
            "toolName": "edit",
            "toolArgs": json.dumps({"path": str(self.repo / "src" / "Ingest" / "Reader.cs")}),
        }
        env = self.env("parent", AGENT_HOST="copilot")
        first = self.run_script(HEARTBEAT, "--host", "copilot", "--event", "postToolUse",
                                stdin=json.dumps(payload), env=env)
        self.assertEqual(first.returncode, 0, first.stderr)
        stop = dict(payload, hookEventName="subagentStop")
        second = self.run_script(HEARTBEAT, "--host", "copilot", "--event", "subagentStop",
                                 stdin=json.dumps(stop), env=env)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.ledger("parent"), [])
        rows = [r for r in self.ledger("copilot-child.6.cp-top.7.agent-7") if r.get("kind") == "heartbeat"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["host"], "copilot")

    def test_heartbeat_counts_apply_patch_targets_without_recording_patch_text(self):
        env = self.env("holder", AGENT_HOST="copilot")
        payload = {
            "hookEventName": "postToolUse",
            "sessionId": "cp-top",
            "cwd": str(self.repo),
            "toolName": "apply_patch",
            "toolArgs": self.native_patch_payload()["toolCalls"][0]["args"],
        }
        self.run_script(HEARTBEAT, "--host", "copilot", "--event", "postToolUse",
                        stdin=json.dumps(payload), env=env)
        stop = dict(payload, hookEventName="agentStop")
        self.run_script(HEARTBEAT, "--host", "copilot", "--event", "agentStop",
                        stdin=json.dumps(stop), env=env)
        rows = [r for r in self.ledger("holder") if r.get("kind") == "heartbeat"]
        self.assertEqual((rows[-1]["calls"], rows[-1]["files"]), (1, 1))
        self.assertNotIn("CHANGED", (self.root / "log" / "holder.jsonl").read_text(encoding="utf-8"))

    def test_claude_form_duplicates_are_skipped_when_copilot_loads_claude_settings(self):
        now = time.time()
        mail.append_mail(self.root, "p2", {"to": "worker-copilot", "kind": "note", "body": "body"}, now=now)
        payload = {"hook_event_name": "PreToolUse", "session_id": "dup", "tool_name": "Edit", "tool_input": {}}
        env = self.env("worker-copilot", AGENT_HOST="copilot")
        doorbell = self.run_script(DOORBELL, "--host", "claude", "--event", "PreToolUse",
                                   stdin=json.dumps(payload), env=env)
        self.assertEqual((doorbell.returncode, doorbell.stdout.strip()), (0, ""))
        gate = self.run_script(GATE, "--host", "claude", "--event", "SubagentStop",
                               stdin=json.dumps(payload), env=env)
        self.assertEqual((gate.returncode, gate.stdout.strip(), gate.stderr.strip()), (0, "", ""))

    def test_canonical_child_identity_helper_is_consistent(self):
        self.assertEqual(identity.copilot_child_identity("cp-top", "agent-7"),
                         "copilot-child.6.cp-top.7.agent-7")

    def test_invalid_copilot_child_and_parent_identities_do_no_io(self):
        bad_cases = [
            {"sessionId": "../bad", "agentId": "agent-7"},
            {"sessionId": "cp-top", "agentId": "../bad"},
            {"sessionId": "x" * 65, "agentId": "agent-7"},
            {"sessionId": "cp/top", "agentId": "agent-7"},
        ]
        for payload_ids in bad_cases:
            with self.subTest(payload=payload_ids):
                payload = {
                    "hookEventName": "postToolUse",
                    "cwd": str(self.repo),
                    "toolName": "edit",
                    "toolArgs": json.dumps({"path": str(self.repo / "src" / "Ingest" / "Reader.cs")}),
                    **payload_ids,
                }
                beat = self.run_script(HEARTBEAT, "--host", "copilot", "--event", "postToolUse",
                                       stdin=json.dumps(payload), env=self.env("parent", AGENT_HOST="copilot"))
                self.assertEqual((beat.returncode, beat.stdout.strip(), beat.stderr.strip()), (0, "", ""))
                stop = self.run_script(GATE, "--host", "copilot", "--event", "subagentStop",
                                       stdin=json.dumps(payload), env=self.env("parent", AGENT_HOST="copilot"))
                self.assertEqual((stop.returncode, stop.stdout.strip(), stop.stderr.strip()), (0, "", ""))
        invalid_parent = self.run_script(DOORBELL, "--host", "copilot", "--event", "preToolUse",
                                         stdin=json.dumps({"sessionId": "cp-top"}),
                                         env=self.env("../bad"))
        self.assertEqual((invalid_parent.returncode, invalid_parent.stdout.strip(), invalid_parent.stderr.strip()), (0, "", ""))


if __name__ == "__main__":
    unittest.main()
