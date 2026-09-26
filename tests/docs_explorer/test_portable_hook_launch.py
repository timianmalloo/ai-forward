"""Execute the shipped hook commands, not just their contents, on the host shell."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "pack" / "adapters" / "hooks"
SCRIPTS = ROOT / "pack" / "scripts"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def commands(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("command", "bash", "powershell"):
                yield item
            else:
                yield from commands(item)
    elif isinstance(value, list):
        for item in value:
            yield from commands(item)


class PortableHookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo with space & apostrophe's"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.hooks = self.repo / "docs" / "ai-forward-pack" / "hooks"
        self.hooks.mkdir(parents=True)
        launcher = HOOKS / "run-hook.cjs"
        if launcher.exists():
            shutil.copyfile(launcher, self.hooks / launcher.name)
        stub = (
            "import json, os, sys\n"
            "print(json.dumps({'input': sys.stdin.read(), 'args': sys.argv[1:], "
            "'cwd': os.getcwd()}))\n"
            "print('hook stderr', file=sys.stderr)\n"
            "sys.exit(int(os.environ.get('TEST_HOOK_EXIT', '0')))\n"
        )
        for script in HOOKS.glob("*.py"):
            (self.hooks / script.name).write_text(stub, encoding="utf-8", newline="\n")
        target = self.hooks.parent / "scripts"
        target.mkdir()
        (target / "coord-core.py").write_text(stub, encoding="utf-8", newline="\n")
        (self.repo / ".agents").mkdir()
        self.env = {
            k: v for k, v in os.environ.items()
            if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "TEST_HOOK_EXIT")
        }

    def run_command(self, command, *, shell=None, exit_code=0):
        shell = shell or ("pwsh" if os.name == "nt" else "sh")
        argv = [shell, "-NoProfile", "-NonInteractive", "-Command", command] if shell == "pwsh" else [shell, "-c", command]
        return subprocess.run(
            argv, cwd=self.repo / ".agents", env=dict(self.env, TEST_HOOK_EXIT=str(exit_code)),
            input='{"sessionId":"portable","text":"quotes & $ stay data"}',
            text=True, encoding="utf-8", capture_output=True, timeout=15,
        )

    def test_all_shipped_commands_execute_from_subdirectory_with_payload(self):
        for name in ("claude-code.settings.hooks.json", "grok.ai-forward-hooks.json",
                     "agy.ai-forward-hooks.json", "copilot.ai-forward-hooks.json"):
            config = json.loads((HOOKS / name).read_text(encoding="utf-8"))
            for command in set(commands(config)):
                with self.subTest(adapter=name, command=command):
                    result = self.run_command(command)
                    self.assertEqual(0, result.returncode, result.stderr)
                    output = json.loads(result.stdout)
                    self.assertEqual('{"sessionId":"portable","text":"quotes & $ stay data"}', output["input"])
                    self.assertEqual(self.repo.resolve(), Path(output["cwd"]).resolve())
                    self.assertEqual("hook stderr\n", result.stderr)

    def test_native_ownership_emitters_cover_all_five_hosts(self):
        core = load("portable_core", SCRIPTS / "coord-core.py")
        for host in ("claude", "copilot", "codex", "grok", "agy"):
            with self.subTest(host=host):
                command = next(commands(core.native_hook_config(host)))
                result = self.run_command(command)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(["hook", "--host", host], json.loads(result.stdout)["args"])

    def test_real_child_exit_two_is_preserved(self):
        config = json.loads((HOOKS / "copilot.ai-forward-hooks.json").read_text(encoding="utf-8"))
        entry = config["hooks"]["preToolUse"][0]
        result = self.run_command(entry["powershell" if os.name == "nt" else "bash"], exit_code=2)
        self.assertEqual(2, result.returncode, result.stderr)
        direct = subprocess.run(
            ["node", str(self.hooks / "run-hook.cjs"), "reread-guard.py", "--host", "claude"],
            cwd=self.repo, env=dict(self.env, TEST_HOOK_EXIT="2"), input="payload",
            text=True, encoding="utf-8", capture_output=True, timeout=10,
        )
        self.assertEqual(2, direct.returncode, direct.stderr)
        self.assertEqual("payload", json.loads(direct.stdout)["input"])

    def test_invalid_invocation_is_rejected_before_python(self):
        for args in (["../other.py"], ["coord-core.py", "install"], ["heartbeat.py", "--host", "unknown"],
                     ["coord-core.py", "hook", "--host", "claude", "--force"]):
            with self.subTest(args=args):
                result = subprocess.run(
                    ["node", str(self.hooks / "run-hook.cjs"), *args], cwd=self.repo,
                    text=True, encoding="utf-8", capture_output=True, timeout=10,
                )
                self.assertNotEqual(0, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertIn("HOOK-ARGUMENT", result.stderr)

    def test_launcher_node_contracts(self):
        result = subprocess.run(
            ["node", "--test", str(ROOT / "tests" / "docs_explorer" / "hook_launcher.test.cjs")],
            cwd=ROOT, text=True, encoding="utf-8", capture_output=True, timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_git_root_overrides_do_not_redirect_the_bootstrap(self):
        config = json.loads((HOOKS / "claude-code.settings.hooks.json").read_text(encoding="utf-8"))
        self.env.update(GIT_DIR=str(ROOT / ".git"), GIT_WORK_TREE=str(ROOT), GIT_COMMON_DIR=str(ROOT / ".git"))
        result = self.run_command(next(commands(config)))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(self.repo.resolve(), Path(json.loads(result.stdout)["cwd"]).resolve())

    def test_missing_git_and_python_are_explicit_failures(self):
        config = json.loads((HOOKS / "claude-code.settings.hooks.json").read_text(encoding="utf-8"))
        argv = shlex.split(next(commands(config)))
        argv[0] = shutil.which("node")
        missing_git = subprocess.run(
            argv, cwd=self.repo, env=dict(self.env, PATH=""), capture_output=True,
            text=True, encoding="utf-8", timeout=10,
        )
        self.assertNotEqual(0, missing_git.returncode)
        self.assertEqual("", missing_git.stdout)
        missing_python = subprocess.run(
            [shutil.which("node"), str(self.hooks / "run-hook.cjs"), "--check"],
            cwd=self.repo, env=dict(self.env, PATH=""), capture_output=True,
            text=True, encoding="utf-8", timeout=10,
        )
        self.assertNotEqual(0, missing_python.returncode)
        self.assertIn("HOOK-PYTHON-MISSING", missing_python.stderr)

    def test_nested_repository_does_not_fall_back_to_parent_pack(self):
        nested = self.repo / ".agents"
        subprocess.run(["git", "init", "-q", str(nested)], check=True)
        config = json.loads((HOOKS / "claude-code.settings.hooks.json").read_text(encoding="utf-8"))
        result = self.run_command(next(commands(config)))
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)


class HookMigrationTests(unittest.TestCase):
    def setUp(self):
        self.pa = load("portable_apply", SCRIPTS / "pack-apply.py")
        self.snippet = (HOOKS / "claude-code.settings.hooks.json").read_text(encoding="utf-8")

    def test_legacy_commands_migrate_preserving_custom_metadata_and_permissions(self):
        legacy = json.loads((HOOKS / "legacy-commands.json").read_text(encoding="utf-8"))
        old, new = next((old, new) for old, new in legacy.items()
                        if new.endswith(" -- reread-guard.py --host claude"))
        current = {"permissions": {"deny": ["Bash(rm *)"]}, "hooks": {"PreToolUse": [
            {"matcher": "Read", "hooks": [{"type": "command", "command": old, "timeout": 7}]},
            {"matcher": "Write", "hooks": [{"type": "command", "command": old + "; custom-check"}]},
        ]}}
        merged = json.loads(self.pa.merge_claude_settings(self.snippet, json.dumps(current), legacy))
        self.assertEqual(current["permissions"], merged["permissions"])
        self.assertEqual({"type": "command", "command": new, "timeout": 7}, merged["hooks"]["PreToolUse"][0]["hooks"][0])
        self.assertEqual(current["hooks"]["PreToolUse"][1], merged["hooks"]["PreToolUse"][1])
        self.assertNotIn("coord-core.py", json.dumps(merged))

    def test_malformed_nested_settings_are_rejected(self):
        for current in ("[]", '{"hooks":[]}', '{"hooks":{"PreToolUse":{}}}',
                        '{"hooks":{"PreToolUse":[{"hooks":[{"command":42}]}]}}',
                        '{"hooks":{"PreToolUse":[{"hooks":[{"type":"command"}]}]}}'):
            with self.subTest(current=current):
                with self.assertRaises(ValueError):
                    self.pa.merge_claude_settings(self.snippet, current, {})

    def test_bom_is_repaired_and_second_merge_is_identical(self):
        merged = self.pa.merge_claude_settings(self.snippet, '\ufeff{"permissions":{}}', {})
        self.assertFalse(merged.startswith("\ufeff"))
        self.assertEqual(merged, self.pa.merge_claude_settings(self.snippet, merged, {}))

    def test_doctor_rejects_the_legacy_shape_and_observes_repaired_launcher(self):
        doctor = load("portable_doctor", SCRIPTS / "pack-doctor.py")
        legacy = json.loads((HOOKS / "legacy-commands.json").read_text(encoding="utf-8"))
        old = next(old for old, new in legacy.items() if new.endswith(" -- reread-guard.py --host claude"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = root / ".claude" / "settings.json"
            settings.parent.mkdir()
            settings.write_text(json.dumps({"hooks": {"PreToolUse": [
                {"hooks": [{"command": old}]}]}}), encoding="utf-8")
            self.assertEqual("FAIL", doctor.check_hook_launchers(tmp)["status"])
            settings.write_text(self.pa.merge_claude_settings(self.snippet, settings.read_text(encoding="utf-8"), legacy),
                                encoding="utf-8", newline="\n")
            launcher = root / "docs" / "ai-forward-pack" / "hooks" / "run-hook.cjs"
            launcher.parent.mkdir(parents=True)
            shutil.copyfile(HOOKS / launcher.name, launcher)
            self.assertEqual("PASS", doctor.check_hook_launchers(tmp)["status"])

    def test_installer_repairs_bom_and_preserves_invalid_target_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".claude" / "settings.json"
            path.parent.mkdir()
            path.write_bytes(b'\xef\xbb\xbf{"permissions":{"deny":["Bash(rm *)"]}}')
            app = self.pa.Applier(str(ROOT), tmp, dry=False, force=True, baselines=False)
            app._settings(self.snippet)
            self.assertFalse(path.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(["Bash(rm *)"], json.loads(path.read_text())["permissions"]["deny"])
            bad = b'{"hooks":{"PreToolUse":[{"hooks":[{"type":"command"}]}]}}'
            path.write_bytes(bad)
            app._settings(self.snippet)
            self.assertEqual(bad, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
