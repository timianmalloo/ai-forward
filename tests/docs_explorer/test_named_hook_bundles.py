"""Actual sync invokes named_hook_bundles.py and shares the installer's named ownership."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class NamedHookSyncTests(unittest.TestCase):
    def test_named_hook_cli_preserves_custom_and_refuses_bad_or_symlink_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp)/"source.json", Path(tmp)/"target.json"
            source.write_text(json.dumps({"managed": {"enabled": True}}), encoding="utf-8")
            def run():
                import sys
                return subprocess.run([sys.executable, str(ROOT/"pack/scripts/named_hook_bundles.py"),
                    str(source), str(target)], capture_output=True, text=True, encoding="utf-8", timeout=10)
            target.write_text(json.dumps({"managed": {"enabled": False}, "local": {"enabled": True}}), encoding="utf-8")
            self.assertEqual(0, run().returncode)
            self.assertEqual({"managed": {"enabled": True}, "local": {"enabled": True}}, json.loads(target.read_text()))
            original = target.read_bytes()
            self.assertEqual(0, run().returncode)
            self.assertEqual(original, target.read_bytes())
            for bad in ("[]", "{broken"):
                target.write_text(bad, encoding="utf-8")
                self.assertNotEqual(0, run().returncode)
                self.assertEqual(bad, target.read_text())
            target.unlink()
            try:
                target.symlink_to(source)
            except OSError:
                return  # Windows may deny symlink creation; ordinary-file cases still ran.
            before = source.read_bytes()
            self.assertNotEqual(0, run().returncode)
            self.assertEqual(before, source.read_bytes())

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell sync entry point unavailable")
    def test_real_sync_preserves_named_opt_in_and_rejects_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)/"repo"
            shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__", ".venv"))
            hooks = repo/".agents/hooks.json"
            doc = json.loads(hooks.read_text())
            custom = {"enabled": True, "PreToolUse": []}
            doc["test-local-guard"] = custom
            hooks.write_text(json.dumps(doc))
            def sync():
                return subprocess.run([shutil.which("pwsh"), "-NoProfile", "-File", str(repo/"tools/sync-pack.ps1")],
                    cwd=repo,capture_output=True,text=True,encoding="utf-8",timeout=60)
            first = sync()
            self.assertEqual(0, first.returncode, first.stdout[-2000:]+first.stderr[-2000:])
            self.assertEqual(custom, json.loads(hooks.read_text())["test-local-guard"])
            before = hooks.read_bytes()
            self.assertEqual(0, sync().returncode)
            self.assertEqual(before, hooks.read_bytes())
            hooks.write_text("[]")
            self.assertNotEqual(0, sync().returncode)
            self.assertEqual("[]", hooks.read_text())
