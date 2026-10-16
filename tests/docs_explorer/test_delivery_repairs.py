"""Same-task reviewer remediation with real compiler and disposable projects."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile

import unittest
import test_delivery as fixtures


class DeliveryRepairTests(unittest.TestCase):
    # Reuse only the real CLI fixture, not the inherited test cases.
    tmp: tempfile.TemporaryDirectory
    repo: Path
    state_root: Path
    setUp = fixtures.DeliveryTests.setUp
    write = fixtures.DeliveryTests.write
    run_cli = fixtures.DeliveryTests.run_cli
    facts = fixtures.DeliveryTests.facts
    start = fixtures.DeliveryTests.start
    receipt = fixtures.DeliveryTests.receipt

    def repair_inputs(self, state, stage="implement", paths=None):
        paths = paths or ["app.py"]
        suffix = state["gate"]["id"]
        report = self.write("block-evidence-" + suffix + ".json", {"verdict": "BLOCK", "finding": "Correct the scoped implementation before independent re-review", "paths": paths})
        review = self.write("block-" + suffix + ".json", {"task": "demo", "gate": suffix,
            "binding": state["gate"]["binding"], "authority": "reviewer", "actor": "reviewer",
            "source": "reviewer-report", "decision": "blocked", "evidence": str(report)})
        authorization = self.write("authority-" + suffix + ".json", {"task": "demo", "gate": suffix,
            "binding": state["gate"]["binding"], "source": "human-message", "actor": "operator", "decision": "approved",
            "stage": stage, "paths": paths, "evidence": str(self.write("human-" + suffix + ".json", {"message": "Repair exactly the scoped original feature"}))})
        return review, authorization

    def test_midstage_veto_supports_another_block_without_restarting_work(self):
        app = self.repo / "app.py"
        app.write_text("def value():\n    return 0\n", encoding="utf-8")
        self.start()
        proof = self.write("partial.json", {"observed": "partial code reviewed and blocked"})
        state = self.run_cli("pause", "--task", "demo", "--kind", "hard-veto", "--authority", "reviewer", "--question", "Fix the blocked partial implementation?", "--actor", "author", "--evidence", proof)
        fixed = proof
        for attempt in range(2):
            review, authorization = self.repair_inputs(state)
            self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review, "--authorization", authorization, "--actor", "author", "--actor", "coauthor", "--path", "app.py")
            app.write_text(f"def value():\n    return {attempt + 1}\n", encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", "-c", f"from app import value; assert value() == {attempt + 1}"], cwd=self.repo, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            fixed = self.write(f"fix-{attempt}.json", {"observed": f"value path returned {attempt + 1}", "exit": result.returncode})
            state = self.run_cli("recheck", "--task", "demo", "--evidence", fixed)
            self.assertEqual(state["completed"], [])
            self.assertEqual(state["next"], "implement")
        self.assertEqual(len(state["repairs"]), 2)
        self.assertEqual(state["repairs"][0]["status"], "superseded")
        for author in ("author", "coauthor"):
            self.assertIn("author cannot clear", self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(state, actor=author, source="reviewer-report"), ok=False).stderr)
        ready = self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(state, actor="reviewer", source="reviewer-report"))
        self.assertEqual(ready["completed"], [])
        self.assertEqual(ready["next"], "implement")
        verified = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", fixed)
        self.assertIsNone(verified["gate"])
        closure = self.write("closure.json", {"criteria": [{"criterion": "feature works", "observed": "real value path returns 2", "evidence": [str(fixed)]}], "changes": ["app.py"], "tests": ["assert value() == 2"], "skips": [], "limits": [], "remaining_gates": []})
        closed = self.run_cli("complete", "--task", "demo", "--stage", "verify", "--actor", "author", "--evidence", fixed, "--closure", closure)
        self.assertIsNone(closed["next"])
        self.assertIsNone(self.run_cli("status", "--task", "demo")["next"])

    def test_recheck_cannot_replace_scoped_file_with_external_symlink(self):
        app = self.repo / "app.py"
        app.write_text("# product\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("implementation.json", {"observed": "product executed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state)
        active = self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review, "--authorization", authorization, "--actor", "author", "--path", "app.py")
        outside = self.write("outside.json", {"unrelated": "external input"})
        app.unlink()
        app.symlink_to(outside)
        failed = self.run_cli("recheck", "--task", "demo", "--evidence", proof, ok=False)
        self.assertIn("repair refused:", failed.stderr)
        checkpoint = self.repo / ".git/ai-forward/delivery/demo.json"
        self.assertEqual(json.loads(checkpoint.read_text(encoding="utf-8"))["gate"], active["gate"])

    @unittest.skipIf(os.name == "nt", "POSIX hardlink alias control")
    def test_recheck_refuses_scoped_file_replaced_by_external_hardlink(self):
        app = self.repo / "app.py"
        app.write_text("# product\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("implementation.json", {"observed": "product executed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement",
                             "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state)
        active = self.run_cli("repair", "--task", "demo", "--stage", "implement",
                              "--review", review, "--authorization", authorization,
                              "--actor", "author", "--path", "app.py")
        outside = self.write("outside.py", {"content": "external"})
        app.unlink()
        os.link(outside, app)
        failed = self.run_cli("recheck", "--task", "demo", "--evidence", proof, ok=False)
        self.assertIn("repair refused:", failed.stderr)
        self.assertEqual(json.loads((self.repo / ".git/ai-forward/delivery/demo.json").read_text(
            encoding="utf-8"))["gate"], active["gate"])

    @unittest.skipIf(os.name == "nt", "POSIX FIFO control")
    def test_recheck_refuses_scoped_file_replaced_by_fifo_before_snapshot(self):
        app = self.repo / "app.py"
        app.write_text("# product\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("implementation.json", {"observed": "product executed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement",
                             "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state)
        self.run_cli("repair", "--task", "demo", "--stage", "implement",
                     "--review", review, "--authorization", authorization,
                     "--actor", "author", "--path", "app.py")
        app.unlink()
        os.mkfifo(app)
        failed = self.run_cli("recheck", "--task", "demo", "--evidence", proof, ok=False)
        self.assertIn("repair refused:", failed.stderr)

    @unittest.skipIf(os.name == "nt", "POSIX FIFO control")
    def test_repair_refuses_existing_fifo_before_workspace_snapshot(self):
        app = self.repo / "app.py"
        app.write_text("# product\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("implementation.json", {"observed": "product executed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement",
                             "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state)
        app.unlink()
        os.mkfifo(app)
        result = subprocess.run(
            [sys.executable, str(fixtures.SCRIPT), "repair", "--task", "demo",
             "--stage", "implement", "--review", str(review), "--authorization",
             str(authorization), "--actor", "author", "--path", "app.py"],
            cwd=self.repo, text=True, encoding="utf-8", capture_output=True, timeout=5)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertRegex(result.stderr, r"(?:repair refused|input drift):")

    @unittest.skipIf(os.name == "nt", "POSIX hardlink alias control")
    def test_repair_refuses_existing_external_hardlink(self):
        app = self.repo / "app.py"
        app.write_text("# product\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("implementation.json", {"observed": "product executed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement",
                             "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state)
        outside = self.write("outside.py", {"content": "external"})
        app.unlink()
        os.link(outside, app)
        failed = self.run_cli("repair", "--task", "demo", "--stage", "implement",
                              "--review", review, "--authorization", authorization,
                              "--actor", "author", "--path", "app.py", ok=False)
        self.assertRegex(failed.stderr, r"(?:repair refused|input drift):")

    def test_original_author_cannot_clear_repair_by_a_different_author(self):
        (self.repo / "app.py").write_text("# original\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("original.json", {"observed": "original code reviewed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "original-author", "--evidence", proof)
        review, authorization = self.repair_inputs(state)
        self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review, "--authorization", authorization, "--actor", "repair-author", "--path", "app.py")
        (self.repo / "app.py").write_text("# corrected\n", encoding="utf-8")
        state = self.run_cli("recheck", "--task", "demo", "--evidence", self.write("fix.json", {"observed": "correction checked"}))
        failed = self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(state, actor="original-author", source="reviewer-report"), ok=False)
        self.assertIn("author cannot clear", failed.stderr)

    def test_denied_human_scope_cannot_begin_repair(self):
        (self.repo / "app.py").write_text("# original\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("original.json", {"observed": "reviewed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state)
        data = json.loads(authorization.read_text(encoding="utf-8"))
        denied = self.write("denied.json", {**data, "decision": "denied"})
        failed = self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review, "--authorization", denied, "--actor", "author", "--path", "app.py", ok=False)
        self.assertIn("repair refused:", failed.stderr)
        self.assertEqual(self.run_cli("status", "--task", "demo")["gate"], state["gate"])

    def test_repair_refuses_unrelated_edits_and_cannot_clear_active_work(self):
        app = self.repo / "app.py"
        app.write_text("# original\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("proof.json", {"observed": "reviewed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state)
        active = self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review, "--authorization", authorization, "--actor", "author", "--path", "app.py")
        self.assertIn("decision refused:", self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(active, actor="reviewer", source="reviewer-report"), ok=False).stderr)
        checkpoint = self.repo / ".git/ai-forward/delivery/demo.json"
        unchanged = checkpoint.read_bytes()
        app.write_text("# scoped correction\n", encoding="utf-8")
        unrelated = self.repo / "unrelated.py"
        unrelated.write_text("# not authorized\n", encoding="utf-8")
        self.assertIn("unrelated workspace drift", self.run_cli("recheck", "--task", "demo", "--evidence", proof, ok=False).stderr)
        self.assertEqual(checkpoint.read_bytes(), unchanged)
        self.assertIn("stage refused:", self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof, ok=False).stderr)
        unrelated.unlink()
        pending = self.run_cli("recheck", "--task", "demo", "--evidence", proof)
        self.assertEqual(pending["gate"]["kind"], "hard-veto")

    def test_repair_refuses_unrelated_staged_content_even_with_restored_bytes(self):
        app = self.repo / "app.py"
        app.write_text("# original\n", encoding="utf-8")
        unrelated = self.repo / "unrelated.py"
        unrelated.write_text("# original unrelated\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], cwd=self.repo, check=True)
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("proof.json", {"observed": "reviewed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state)
        self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review, "--authorization", authorization, "--actor", "author", "--path", "app.py")
        app.write_text("# correction\n", encoding="utf-8")
        original = unrelated.read_bytes()
        unrelated.write_text("# staged outside scope\n", encoding="utf-8")
        subprocess.run(["git", "add", "unrelated.py"], cwd=self.repo, check=True)
        unrelated.write_bytes(original)
        self.assertIn("unrelated workspace drift", self.run_cli("recheck", "--task", "demo", "--evidence", proof, ok=False).stderr)

    def test_ignored_product_file_is_not_silently_accepted_as_repair_scope(self):
        (self.repo / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
        (self.repo / "ignored.py").write_text("# load-bearing ignored file\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("proof.json", {"observed": "reviewed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state, paths=["ignored.py"])
        failed = self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review, "--authorization", authorization, "--actor", "author", "--path", "ignored.py", ok=False)
        self.assertIn("repair refused:", failed.stderr)
        self.assertEqual(self.run_cli("status", "--task", "demo")["gate"], state["gate"])

    def test_plain_runtime_file_is_not_silently_accepted_as_repair_scope(self):
        shutil.rmtree(self.repo / ".git")
        self.state_root = self.repo / ".delivery-state"
        (self.repo / "node_modules").mkdir()
        (self.repo / "node_modules/dependency.py").write_text("# omitted runtime input\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("proof.json", {"observed": "reviewed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state, paths=["node_modules/dependency.py"])
        failed = self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review, "--authorization", authorization, "--actor", "author", "--path", "node_modules/dependency.py", ok=False)
        self.assertIn("repair refused:", failed.stderr)
        self.assertEqual(self.run_cli("status", "--task", "demo")["gate"], state["gate"])

    def test_malformed_repair_index_manifest_has_stable_checkpoint_refusal(self):
        (self.repo / "app.py").write_text("# original\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("proof.json", {"observed": "reviewed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state)
        self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review, "--authorization", authorization, "--actor", "author", "--path", "app.py")
        checkpoint = self.repo / ".git/ai-forward/delivery/demo.json"
        original = checkpoint.read_bytes()
        for changes in ({"index_entries": []}, {"head": None}, {"branch": []}, {"files": None}):
            with self.subTest(changes=changes):
                state = json.loads(original)
                state["repairs"][-1]["before"].update(changes)
                import hashlib
                state["integrity"] = hashlib.sha256(json.dumps({k: v for k, v in state.items() if k != "integrity"}, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
                checkpoint.write_text(json.dumps(state), encoding="utf-8")
                failed = self.run_cli("recheck", "--task", "demo", "--evidence", proof, ok=False)
                self.assertIn("checkpoint refused:", failed.stderr)
                self.assertNotIn("Traceback", failed.stderr)
        checkpoint.write_bytes(original)
        self.assertEqual(self.run_cli("status", "--task", "demo")["repairs"][-1]["status"], "active")

    def test_repair_authority_and_binding_controls_preserve_the_original_veto(self):
        app = self.repo / "app.py"
        app.write_text("# original\n", encoding="utf-8")
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("proof.json", {"observed": "reviewed"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof)
        review, authorization = self.repair_inputs(state)
        checkpoint = self.repo / ".git/ai-forward/delivery/demo.json"
        unchanged = checkpoint.read_bytes()
        records = {"review": json.loads(review.read_text(encoding="utf-8")), "authorization": json.loads(authorization.read_text(encoding="utf-8"))}
        cases = [("review", {"actor": "author"}), ("review", {"decision": "approved"}),
                 ("authorization", {"source": "model-output"}), ("authorization", {"source": "host-permission"}),
                 ("authorization", {"decision": None}), ("authorization", {"gate": "stale"}),
                 ("authorization", {"stage": "migrate"}), ("authorization", {"paths": ["unrelated.py"]}),
                 ("authorization", {"actor": []}), ("authorization", {"evidence": []})]
        for kind, changes in cases:
            with self.subTest(kind=kind, changes=changes):
                bad = self.write("invalid-repair-receipt.json", {**records[kind], **changes})
                failed = self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", bad if kind == "review" else review,
                                      "--authorization", bad if kind == "authorization" else authorization, "--actor", "author", "--path", "app.py", ok=False)
                self.assertIn("repair refused:", failed.stderr)
                self.assertNotIn("Traceback", failed.stderr)
                self.assertEqual(checkpoint.read_bytes(), unchanged)
        app.write_text("# unexplained edit before authorization\n", encoding="utf-8")
        self.assertIn("input drift:", self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review, "--authorization", authorization, "--actor", "author", "--path", "app.py", ok=False).stderr)
        self.assertEqual(checkpoint.read_bytes(), unchanged)

    def test_completed_veto_repair_preserves_task_and_unrelated_progress(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                if plain:
                    shutil.rmtree(self.repo / ".git")
                    self.state_root = self.repo / ".delivery-state"
                app = self.repo / "app.py"
                app.write_text("def value():\n    return 1\n", encoding="utf-8")
                self.start(contract_tier="T1", design_ready=True, questions=["requirements"])
                spec_proof = self.write("spec-proof.json", {"requirements": "feature works"})
                self.run_cli("complete", "--task", "demo", "--stage", "specify", "--actor", "specifier", "--evidence", spec_proof)
                proof = self.write("implementation-proof.json", {"observed": "value returns 1"})
                blocked = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author", "--evidence", proof)
                prior, authority = self.repair_inputs(blocked)
                stale = self.receipt(blocked, actor="reviewer", source="reviewer-report")
                repairing = self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", prior,
                                         "--authorization", authority, "--actor", "author", "--path", "app.py")
                self.assertEqual([r["stage"] for r in repairing["completed"]], ["specify"])
                self.assertEqual(repairing["next"], "implement")
                self.assertEqual(repairing["repairs"][-1]["prior_gate"], blocked["gate"])
                app.write_text("def value():\n    return 2\n", encoding="utf-8")
                result = subprocess.run([sys.executable, "-B", "-c", "from app import value; assert value() == 2"], cwd=self.repo, capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(result.returncode, 0, result.stderr)
                fixed = self.write("repair-proof.json", {"command": "assert value() == 2", "exit": result.returncode})
                pending = self.run_cli("recheck", "--task", "demo", "--evidence", fixed)
                self.assertEqual(pending["completed"][0], blocked["completed"][0])
                self.assertNotEqual(pending["gate"]["binding"], blocked["gate"]["binding"])
                self.assertIn("decision refused:", self.run_cli("resume", "--task", "demo", "--receipt", stale, ok=False).stderr)
                self.assertIn("author cannot clear", self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(pending, actor="author", source="reviewer-report"), ok=False).stderr)
                ready = self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(pending, actor="reviewer", source="reviewer-report"))
                self.assertEqual(ready["task"], "demo")
                self.assertEqual(ready["contract"], blocked["contract"])
                closure = self.write("closure.json", {"criteria": [{"criterion": "feature works", "observed": "real value path returns 2", "evidence": [str(fixed)]}], "changes": ["app.py"], "tests": ["assert value() == 2"], "skips": [], "limits": [], "remaining_gates": []})
                closed = self.run_cli("complete", "--task", "demo", "--stage", "verify", "--actor", "author", "--evidence", fixed, "--closure", closure)
                self.assertIsNone(closed["next"])
                self.assertIsNone(self.run_cli("status", "--task", "demo")["next"])
                # Use another disposable project for the plain half.
                self.repo = Path(self.tmp.name) / "plain"
                self.repo.mkdir(exist_ok=True)
                subprocess.run(["git", "init", "-q", str(self.repo)], check=True)


if __name__ == "__main__":
    unittest.main()
