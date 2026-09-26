"""Settings refresh must preserve user policy and reject malformed targets atomically."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "pack" / "scripts" / "pack-apply.py"
HOOKS = ROOT / "pack" / "adapters" / "hooks"
PREFIX = ("py=$(python3 -c 'import sys;print(sys.executable)' 2>/dev/null); "
          "[ -x \"$py\" ] || py=$(python -c 'import sys;print(sys.executable)'); ")
OLD = PREFIX + '"$py" docs/ai-forward-pack/hooks/heartbeat.py --host claude --event PostToolUse'


class SettingsUpgradeTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "upgrade_applier", os.environ.get("AI_FORWARD_TEST_APPLIER", str(SCRIPT)))
        self.pa = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.pa)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / ".claude" / "settings.json"
        self.path.parent.mkdir()
        self.snippet = (HOOKS / "claude-code.settings.hooks.json").read_text(encoding="utf-8")

    def apply(self):
        app = self.pa.Applier(str(ROOT), str(self.root), dry=False, force=True, baselines=False)
        app._settings(self.snippet)
        return json.loads(self.path.read_text(encoding="utf-8-sig"))

    def test_custom_wrapper_and_mixed_entry_keep_their_policy(self):
        custom = {"matcher": "Write", "hooks": [
            {"type": "command", "command": OLD + "; additional-policy", "timeout": 9}]}
        managed = {"matcher": "Read", "hooks": [
            {"type": "command", "command": OLD, "timeout": 7},
            {"type": "command", "command": "custom-policy"}]}
        original = {"permissions": {"deny": ["Bash(rm *)"]},
                    "hooks": {"PostToolUse": [custom, managed]}}
        self.path.write_text(json.dumps(original), encoding="utf-8")
        result = self.apply()
        post = result["hooks"]["PostToolUse"]
        self.assertEqual(custom, post[0])
        self.assertEqual("Read", post[1]["matcher"])
        self.assertEqual(7, post[1]["hooks"][0]["timeout"])
        self.assertTrue(post[1]["hooks"][0]["command"].startswith("git -c alias.aif-hook="))
        self.assertEqual(managed["hooks"][1], post[1]["hooks"][1])
        self.assertEqual(original["permissions"], result["permissions"])

    def test_bom_normalized_and_second_update_identical(self):
        self.path.write_bytes(b'\xef\xbb\xbf{"permissions":{"deny":["Bash(rm *)"]}}')
        self.apply()
        once = self.path.read_bytes()
        self.assertFalse(once.startswith(b"\xef\xbb\xbf"))
        self.assertIn("PostToolUse", json.loads(once)["hooks"])
        self.apply()
        self.assertEqual(once, self.path.read_bytes())

    def test_malformed_nested_shapes_leave_original_bytes_unchanged(self):
        for text in ('[]', '{"hooks":[]}', '{"hooks":{"PreToolUse":{}}}',
                     '{"hooks":{"PreToolUse":[{"hooks":[{"type":"command"}]}]}}',
                     '{"hooks":{"PreToolUse":[{"hooks":[{"command":42}]}]}}'):
            with self.subTest(text=text):
                data = text.encode("utf-8")
                self.path.write_bytes(data)
                app = self.pa.Applier(str(ROOT), str(self.root), dry=False, force=True, baselines=False)
                app._settings(self.snippet)
                self.assertEqual(data, self.path.read_bytes())
                self.assertTrue(any(row["status"] == "fail" for row in app.rows))

    def test_existing_disabled_ownership_opt_in_is_preserved_not_added(self):
        old = PREFIX + 'root=$(git rev-parse --show-toplevel) || exit 2; exec "$py" "$root/docs/ai-forward-pack/scripts/coord-core.py" hook --host claude'
        original = {"disableAllHooks": True, "hooks": {"PreToolUse": [
            {"matcher": "Write", "hooks": [{"type": "command", "command": old, "timeout": 5}]}]}}
        self.path.write_text(json.dumps(original), encoding="utf-8")
        result = self.apply()
        self.assertTrue(result["disableAllHooks"])
        hook = result["hooks"]["PreToolUse"][0]["hooks"][0]
        self.assertTrue(hook["command"].startswith("git -c alias.aif-hook="))
        self.assertEqual(5, hook["timeout"])
        self.path.write_text("{}", encoding="utf-8")
        self.assertNotIn("coord-core.py", json.dumps(self.apply()))

    def test_sync_cli_uses_the_same_merger_as_installer(self):
        self.path.write_bytes(b'\xef\xbb\xbf{"permissions":{}}')
        self.apply()
        expected = self.path.read_bytes()
        self.path.write_bytes(b'\xef\xbb\xbf{"permissions":{}}')
        result = subprocess.run(
            [sys.executable, str(SCRIPT.with_name("named_hook_bundles.py")),
             str(HOOKS / "claude-code.settings.hooks.json"), str(self.path), "--claude-settings"],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(expected, self.path.read_bytes())

    def test_doctor_rejects_bom_and_legacy_commands(self):
        sys.path.insert(0, str(SCRIPT.parent))
        try:
            spec = importlib.util.spec_from_file_location("upgrade_doctor", SCRIPT.with_name("pack-doctor.py"))
            doctor = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(doctor)
        finally:
            sys.path.pop(0)
        self.path.write_bytes(b'\xef\xbb\xbf{"hooks":{}}')
        self.assertEqual("FAIL", doctor.check_hook_launchers(str(self.root))["status"])
        self.path.write_text(json.dumps({"hooks": {"PostToolUse": [{"hooks": [{"command": OLD}]}]}}),
                             encoding="utf-8")
        self.assertEqual("FAIL", doctor.check_hook_launchers(str(self.root))["status"])
        self.assertEqual("PASS", doctor.check_hook_launchers(str(ROOT))["status"])

    def test_named_ownership_command_migrates_without_enabling_or_erasing_wrapper(self):
        old = PREFIX + 'root=$(git rev-parse --show-toplevel) || exit 2; exec "$py" "$root/docs/ai-forward-pack/scripts/coord-core.py" hook --host agy'
        section = {"enabled": False, "PreToolUse": [{"matcher": "write_to_file", "hooks": [
            {"type": "command", "command": old, "timeout": 5},
            {"type": "command", "command": old + "; custom-policy"}]}]}
        source = (HOOKS / "agy.ai-forward-hooks.json").read_text(encoding="utf-8")
        merged = json.loads(self.pa.merge_named_hook_bundles(source, json.dumps({"ownership-guard": section})))
        actual = merged["ownership-guard"]
        self.assertFalse(actual["enabled"])
        handlers = actual["PreToolUse"][0]["hooks"]
        self.assertTrue(handlers[0]["command"].startswith("git -c alias.aif-hook="))
        self.assertEqual(5, handlers[0]["timeout"])
        self.assertEqual(section["PreToolUse"][0]["hooks"][1], handlers[1])

    def test_codex_stop_and_grok_ownership_keep_native_metadata(self):
        stem = PREFIX + 'root=$(git rev-parse --show-toplevel) || exit 2; exec "$py" "$root/docs/ai-forward-pack/'
        for host, command in (
            ("grok", stem + 'scripts/coord-core.py" hook --host grok'),
            ("codex", stem + 'hooks/owner-review-gate.py" --host codex --event Stop'),
        ):
            with self.subTest(host=host):
                config = {"hooks": {"Stop" if host == "codex" else "PreToolUse": [
                    {"matcher": "", "hooks": [{"type": "command", "command": command, "timeout": 5}]}]}}
                result = json.loads(self.pa.merge_hook_ownership(json.dumps(config)))
                event = next(iter(result["hooks"]))
                handler = result["hooks"][event][0]["hooks"][0]
                self.assertTrue(handler["command"].startswith("git -c alias.aif-hook="))
                self.assertEqual(5, handler["timeout"])
                self.assertEqual(result, json.loads(self.pa.merge_hook_ownership(json.dumps(result))))

    def test_invalid_utf8_is_rejected_by_installer_and_sync_without_policy_change(self):
        original = b'{"permissions":{"deny":["Bash(echo \xff)"]}}'
        self.path.write_bytes(original)
        app = self.pa.Applier(str(ROOT), str(self.root), dry=False, force=True, baselines=False)
        app._settings(self.snippet)
        self.assertEqual(original, self.path.read_bytes())
        self.assertTrue(any(row["status"] == "fail" for row in app.rows))
        result = subprocess.run(
            [sys.executable, str(SCRIPT.with_name("named_hook_bundles.py")),
             str(HOOKS / "claude-code.settings.hooks.json"), str(self.path), "--claude-settings"],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(original, self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
