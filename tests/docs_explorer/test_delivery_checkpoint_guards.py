"""Post-review verification invariants through real compiler/helper processes."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import test_delivery as fixtures


class DeliveryCheckpointGuardTests(unittest.TestCase):
    tmp: tempfile.TemporaryDirectory
    repo: Path
    state_root: Path
    audit: Path
    compiled_id: str
    setUp = fixtures.DeliveryTests.setUp
    def write(self, name, value):
        path = Path(self.tmp.name) / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    run_cli = fixtures.DeliveryTests.run_cli
    facts = fixtures.DeliveryTests.facts
    start = fixtures.DeliveryTests.start
    receipt = fixtures.DeliveryTests.receipt

    def reviewed(self, tier="T1", plain=False):
        if plain:
            shutil.rmtree(self.repo / ".git")
            self.state_root = Path(self.tmp.name) / "state"
        app = self.repo / "app.py"
        app.write_text("def value():\n    return 1\n", encoding="utf-8")
        self.start(contract_tier=tier, design_ready=True)
        proof = self.write("implementation.json", {"observed": "implementation fixture"})
        reviewed = self.run_cli("complete", "--task", "demo", "--stage", "implement",
                                "--actor", "author", "--evidence", proof)
        self.assertEqual(reviewed["gate"]["authority"], "reviewer")
        ready = self.run_cli("resume", "--task", "demo", "--receipt",
                             self.receipt(reviewed, actor="independent-reviewer", source="reviewer-report"))
        self.assertEqual(ready["next"], "verify")
        return app, ready

    def checkpoint_bytes(self):
        if getattr(self, "state_root", None):
            return next(self.state_root.glob("*/demo.json")).read_bytes()
        return (self.repo / ".git/ai-forward/delivery/demo.json").read_bytes()

    def closure(self, proof):
        return self.write("closure.json", {"criteria": [{"criterion": "feature works",
            "observed": "app.value() real subprocess returned the expected value", "evidence": [str(proof)]}],
            "changes": ["app.py"], "tests": ["app.value()"], "skips": [], "limits": [], "remaining_gates": []})

    def executed_proof(self, value, local=False):
        result = subprocess.run([sys.executable, "-B", "-c", f"from app import value; assert value() == {value}; print(value())"],
                                cwd=self.repo, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.write("verification.json", {"command": f"assert value() == {value}",
                          "exit": result.returncode, "stdout": result.stdout})
        if local:
            state = self.run_cli("status", "--task", "demo")
            destination = Path(state["local_area"]) / "verification.json"
            destination.write_bytes(path.read_bytes())
            return destination
        return path

    def test_verification_completion_refuses_postreview_product_edits(self):
        for tier in ("T1", "T2"):
            for plain in (False, True):
                with self.subTest(tier=tier, plain=plain):
                    self.repo = Path(self.tmp.name) / f"case-{tier}-{plain}"
                    self.repo.mkdir()
                    subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
                    if hasattr(self, "state_root"):
                        del self.state_root
                    app, ready = self.reviewed(tier=tier, plain=plain)
                    unchanged = self.checkpoint_bytes()
                    app.write_text("def value():\n    return 2\n", encoding="utf-8")
                    proof = self.executed_proof(2)
                    failed = self.run_cli("complete", "--task", "demo", "--stage", "verify", "--actor", "author",
                                          "--evidence", proof, "--closure", self.closure(proof), ok=False)
                    self.assertIn("input drift:", failed.stderr)
                    self.assertEqual(self.checkpoint_bytes(), unchanged)
                    app.write_text("def value():\n    return 1\n", encoding="utf-8")
                    state = self.run_cli("status", "--task", "demo")
                    self.assertEqual(state["decisions"], ready["decisions"])
                    self.assertEqual(state["next"], "verify")

    def test_verification_pauses_cannot_rebind_changed_product(self):
        for kind, authority in (("permission", "human"), ("decision", "human"), ("release", "human"), ("hard-veto", "reviewer")):
            with self.subTest(kind=kind):
                self.repo = Path(self.tmp.name) / kind
                self.repo.mkdir()
                subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
                app, _ = self.reviewed()
                unchanged = self.checkpoint_bytes()
                app.write_text("def value():\n    return 2\n", encoding="utf-8")
                proof = self.executed_proof(2)
                failed = self.run_cli("pause", "--task", "demo", "--kind", kind, "--authority", authority,
                                      "--question", "Resolve this gate?", "--actor", "author", "--evidence", proof, ok=False)
                self.assertIn("input drift:", failed.stderr)
                self.assertEqual(self.checkpoint_bytes(), unchanged)

    def test_unchanged_verification_allows_local_and_external_fresh_proof(self):
        self.reviewed()
        proof = self.executed_proof(1, local=True)
        paused = self.run_cli("pause", "--task", "demo", "--kind", "permission", "--authority", "human",
                              "--question", "Permit this final test?")
        resumed = self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(paused))
        self.assertEqual(resumed["next"], "verify")
        closed = self.run_cli("complete", "--task", "demo", "--stage", "verify", "--actor", "author",
                              "--evidence", proof, "--closure", self.closure(proof))
        self.assertIsNone(closed["next"])
        self.assertIsNone(self.run_cli("status", "--task", "demo")["next"])

    def test_nonignored_in_tree_verification_proof_is_not_a_drift_waiver(self):
        self.reviewed()
        unchanged = self.checkpoint_bytes()
        proof = self.repo / "new-proof.json"
        proof.write_text('{"observation":"new in-tree output"}', encoding="utf-8")
        failed = self.run_cli("complete", "--task", "demo", "--stage", "verify", "--actor", "author",
                              "--evidence", proof, "--closure", self.closure(proof), ok=False)
        self.assertIn("input drift:", failed.stderr)
        self.assertEqual(self.checkpoint_bytes(), unchanged)
    @unittest.skipIf(os.name == "nt", "POSIX executable permissions")
    def test_mode_only_drift_refuses_status_and_resume(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                self.repo = Path(self.tmp.name) / f"mode-{plain}"
                self.repo.mkdir()
                subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
                if plain:
                    shutil.rmtree(self.repo / ".git")
                    self.state_root = Path(self.tmp.name) / "state"
                script = self.repo / "run.sh"
                script.write_text("#!/bin/sh\nprintf 'working\\n'\n", encoding="utf-8")
                script.chmod(0o755)
                if not plain:
                    subprocess.run(["git", "-C", str(self.repo), "add", "run.sh"], check=True)
                    subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Fixture", "-c",
                                    "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], check=True)
                ran = subprocess.run([str(script)], capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(ran.returncode, 0, ran.stderr)
                original = script.read_bytes()
                self.start()
                paused = self.run_cli("pause", "--task", "demo", "--kind", "permission", "--authority", "human",
                                      "--question", "Run scoped check?")
                receipt = self.receipt(paused)
                unchanged = self.checkpoint_bytes()
                script.chmod(0o644)
                self.assertEqual(script.read_bytes(), original)
                with self.assertRaises(PermissionError):
                    subprocess.run([str(script)], check=True)
                for argv in (("status",), ("resume", "--receipt", receipt)):
                    failed = self.run_cli(*argv, "--task", "demo", ok=False)
                    self.assertIn("input drift:", failed.stderr)
                    self.assertEqual(self.checkpoint_bytes(), unchanged)
                script.chmod(0o755)
                self.assertIsNone(self.run_cli("resume", "--task", "demo", "--receipt", receipt)["gate"])

    @unittest.skipIf(os.name == "nt", "POSIX executable permissions")
    def test_scoped_repair_rejects_outside_mode_change_but_allows_scoped_mode(self):
        app = self.repo / "app.py"
        app.write_text("# authored product\n", encoding="utf-8")
        outside = self.repo / "run.sh"
        outside.write_text("#!/bin/sh\nprintf 'working\\n'\n", encoding="utf-8")
        outside.chmod(0o755)
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("authored.json", {"observed": "known implementation"})
        blocked = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof)
        import test_delivery_repairs as repairs
        review, authorization = repairs.DeliveryRepairTests.repair_inputs.__get__(self)(blocked)
        self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review,
                     "--authorization", authorization, "--actor", "author", "--path", "app.py")
        unchanged = self.checkpoint_bytes()
        app.chmod(0o755)
        outside.chmod(0o644)
        failed = self.run_cli("recheck", "--task", "demo", "--evidence", proof, ok=False)
        self.assertIn("unrelated workspace drift", failed.stderr)
        self.assertEqual(self.checkpoint_bytes(), unchanged)
        outside.chmod(0o755)
        pending = self.run_cli("recheck", "--task", "demo", "--evidence", proof)
        self.assertEqual(pending["repairs"][-1]["status"], "review")
        self.assertEqual(pending["gate"]["authority"], "reviewer")
        self.assertNotEqual(pending["snapshot"], blocked["snapshot"])

    @unittest.skipIf(os.name == "nt", "POSIX permission metadata")
    def test_permission_metadata_without_executable_change_is_not_drift(self):
        product = self.repo / "ordinary.txt"
        product.write_text("same content", encoding="utf-8")
        product.chmod(0o644)
        started = self.start()
        product.chmod(0o600)
        self.assertEqual(self.run_cli("status", "--task", "demo")["snapshot"], started["snapshot"])
    def test_inherited_git_root_variables_do_not_redirect_explicit_project(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                self.cli_env = None
                if hasattr(self, "state_root"):
                    del self.state_root
                self.repo = Path(self.tmp.name) / f"project-a-{plain}"
                self.repo.mkdir()
                subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
                if plain:
                    shutil.rmtree(self.repo / ".git")
                    self.state_root = Path(self.tmp.name) / "state"
                app = self.repo / "app.py"
                app.write_text("# project A\n", encoding="utf-8")
                self.start()
                other = Path(self.tmp.name) / f"project-b-{plain}"
                other.mkdir()
                subprocess.run(["git", "init", "-q", str(other)], check=True)
                self.cli_env = {**os.environ, "GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other)}
                redirected = self.run_cli("start", "--repo", self.repo, "--task", "isolated", "--facts", self.facts(),
                                          "--audit-root", self.audit, "--compiled-id", self.compiled_id)
                self.assertEqual(redirected["identity"]["root"], str(self.repo.resolve()))
                app.write_text("# actual A drift\n", encoding="utf-8")
                failed = self.run_cli("status", "--repo", self.repo, "--task", "isolated", ok=False)
                self.assertIn("input drift:", failed.stderr)
                self.cli_env = None
                if hasattr(self, "state_root"):
                    del self.state_root

    def test_inherited_git_index_and_config_do_not_change_fingerprint(self):
        (self.repo / "app.py").write_text("# project A\n", encoding="utf-8")
        expected = self.start()
        other = Path(self.tmp.name) / "project-b"
        other.mkdir()
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        (other / "other.py").write_text("# B index\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(other), "add", "other.py"], check=True)
        environments = [{"GIT_WORK_TREE": str(other)}, {"GIT_INDEX_FILE": str(other / ".git/index")},
                        {"GIT_COMMON_DIR": str(other / ".git")},
                        {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.worktree", "GIT_CONFIG_VALUE_0": str(other)}]
        for override in environments:
            with self.subTest(variables=sorted(override)):
                self.cli_env = {**os.environ, **override}
                actual = self.run_cli("status", "--repo", self.repo, "--task", "demo")
                self.assertEqual(actual["identity"], expected["identity"])
                self.assertEqual(actual["snapshot"], expected["snapshot"])
        self.cli_env = None


if __name__ == "__main__":
    unittest.main()
