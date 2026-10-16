"""Checkpoint input drift through real local Git submodules (no network)."""
from pathlib import Path
import json
import subprocess
import tempfile
import unittest

import test_delivery as fixtures


class DeliverySubmoduleTests(unittest.TestCase):
    tmp: tempfile.TemporaryDirectory
    repo: Path
    setUp = fixtures.DeliveryTests.setUp
    write = fixtures.DeliveryTests.write
    run_cli = fixtures.DeliveryTests.run_cli
    facts = fixtures.DeliveryTests.facts
    start = fixtures.DeliveryTests.start
    receipt = fixtures.DeliveryTests.receipt

    def git(self, repo, *args):
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit(self, repo):
        self.git(repo, "add", ".")
        self.git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")

    def add_vendor(self):
        source = Path(self.tmp.name) / "source"
        source.mkdir()
        self.git(source, "init", "-q")
        (source / "api.py").write_text("def api():\n    return 1\n", encoding="utf-8")
        self.commit(source)
        self.git(self.repo, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(source), "vendor")
        self.commit(self.repo)
        return self.repo / "vendor"

    def assert_stale_gate(self, receipt):
        for argv in (("status", "--task", "demo"), ("resume", "--task", "demo", "--receipt", receipt)):
            self.assertIn("input drift:", self.run_cli(*argv, ok=False).stderr)

    def pause_receipt(self):
        state = self.run_cli("pause", "--task", "demo", "--kind", "permission", "--authority", "human", "--question", "Permit verification?")
        return self.receipt(state)

    def test_submodule_checkout_head_and_parent_gitlink_index_are_bound(self):
        vendor = self.add_vendor()
        self.start()
        receipt = self.pause_receipt()
        head = self.git(vendor, "rev-parse", "HEAD")
        self.git(vendor, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-qm", "another revision with identical files")
        changed_head = self.git(vendor, "rev-parse", "HEAD")
        self.assert_stale_gate(receipt)
        self.git(vendor, "reset", "--hard", head)
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "implement")
        self.git(self.repo, "update-index", "--cacheinfo", f"160000,{changed_head},vendor")
        self.assert_stale_gate(receipt)
        self.git(self.repo, "reset", "-q", "HEAD", "--", "vendor")
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "implement")

    def test_nested_submodule_content_and_index_drift_are_bound(self):
        vendor = self.add_vendor()
        source = Path(self.tmp.name) / "nested-source"
        source.mkdir()
        self.git(source, "init", "-q")
        (source / "nested.py").write_text("# nested original\n", encoding="utf-8")
        self.commit(source)
        self.git(vendor, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(source), "nested")
        self.commit(vendor)
        self.commit(self.repo)
        self.start()
        receipt = self.pause_receipt()
        nested = vendor / "nested"
        product = nested / "nested.py"
        original = product.read_bytes()
        product.write_text("# nested changed\n", encoding="utf-8")
        self.assert_stale_gate(receipt)
        self.git(nested, "add", "nested.py")
        product.write_bytes(original)
        self.assert_stale_gate(receipt)
        self.git(nested, "reset", "-q", "HEAD", "--", "nested.py")
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "implement")

    def test_unchanged_submodule_ignores_runtime_but_tracks_untracked_inputs(self):
        vendor = self.add_vendor()
        (vendor / ".gitignore").write_text("cache/\n", encoding="utf-8")
        self.commit(vendor)
        self.commit(self.repo)
        state = self.start()
        self.assertIsInstance(state["snapshot"]["submodules"]["vendor"]["checkout"], dict)
        receipt = self.pause_receipt()
        (vendor / "cache").mkdir()
        (vendor / "cache/transient.txt").write_text("runtime", encoding="utf-8")
        self.assertEqual(self.run_cli("status", "--task", "demo")["snapshot"], state["snapshot"])
        (vendor / "new-input.py").write_text("# load bearing\n", encoding="utf-8")
        self.assert_stale_gate(receipt)
        self.assertFalse((self.repo / "docs").exists())

    def test_submodule_staged_change_is_detected_when_worktree_bytes_are_restored(self):
        vendor = self.add_vendor()
        self.start()
        api = vendor / "api.py"
        original = api.read_bytes()
        api.write_text("def api():\n    return 2\n", encoding="utf-8")
        self.git(vendor, "add", "api.py")
        api.write_bytes(original)
        self.assertIn("MM api.py", self.git(vendor, "status", "--porcelain"))
        self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
        self.git(vendor, "reset", "-q", "HEAD", "--", "api.py")
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "implement")

    def test_uninitialized_submodule_is_explicit_and_initialization_invalidates_context(self):
        self.add_vendor()
        self.git(self.repo, "submodule", "deinit", "-f", "--", "vendor")
        state = self.start()
        self.assertIn("submodules", state["snapshot"], "submodule availability must be explicit in checkpoint output")
        self.assertEqual(state["snapshot"]["submodules"]["vendor"]["checkout"], "unavailable")
        self.assertEqual(self.run_cli("status", "--task", "demo")["snapshot"], state["snapshot"])
        self.git(self.repo, "-c", "protocol.file.allow=always", "submodule", "update", "--init", "vendor")
        self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_parent_repair_refuses_submodule_internal_scope_before_any_edit(self):
        self.add_vendor()
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("proof.json", {"observed": "reviewed dependency"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof)
        review = self.write("block.json", json.loads(self.receipt(state, actor="reviewer", source="reviewer-report", decision="blocked").read_text(encoding="utf-8")))
        authorization = self.write("authority.json", {"task": "demo", "gate": state["gate"]["id"],
            "binding": state["gate"]["binding"], "source": "human-message", "actor": "operator", "decision": "approved",
            "stage": "implement", "paths": ["vendor/api.py"], "evidence": str(self.write("human.json", {"message": "Correct dependency"}))})
        failed = self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review, "--authorization", authorization, "--actor", "author", "--path", "vendor/api.py", ok=False)
        self.assertIn("repair refused:", failed.stderr)
        self.assertEqual(self.run_cli("status", "--task", "demo")["gate"], state["gate"])

    def test_submodule_tracked_worktree_change_blocks_status_and_resume(self):
        vendor = self.add_vendor()
        started = self.start()
        paused = self.run_cli("pause", "--task", "demo", "--kind", "permission", "--authority", "human", "--question", "Permit scoped verification?")
        receipt = self.receipt(paused)
        (vendor / "api.py").write_text("def api():\n    return 2\n", encoding="utf-8")
        self.assertIn("vendor", self.git(self.repo, "status", "--porcelain"))
        self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
        self.assertIn("input drift:", self.run_cli("resume", "--task", "demo", "--receipt", receipt, ok=False).stderr)
        (vendor / "api.py").write_text("def api():\n    return 1\n", encoding="utf-8")
        recovered = self.run_cli("status", "--task", "demo")
        self.assertEqual(recovered["snapshot"], started["snapshot"])
        self.assertEqual(recovered["gate"], paused["gate"])


if __name__ == "__main__":
    unittest.main()
