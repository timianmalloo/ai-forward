"""Repair history regressions; receipts are synthetic mechanical fixtures, not consent.

Every delivery operation runs in a fresh process against real compiler/audit output.
"""
from pathlib import Path
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from typing import Any, Literal, cast, overload

import test_delivery as fixtures
import test_delivery_repairs as repairs
import test_delivery_outcome_repairs as outcomes
import test_delivery_submodules as submodules


class RepairHistoryTests(unittest.TestCase):
    tmp: tempfile.TemporaryDirectory
    repo: Path
    log: Path
    audit: Path
    compiled_id: str
    plain = False
    write = fixtures.DeliveryTests.write
    facts = fixtures.DeliveryTests.facts
    start = fixtures.DeliveryTests.start
    receipt = fixtures.DeliveryTests.receipt
    repair_inputs = repairs.DeliveryRepairTests.repair_inputs
    timed = outcomes.DeliveryOutcomeRepairsTests.timed
    record = outcomes.DeliveryOutcomeRepairsTests.record
    git = submodules.DeliverySubmoduleTests.git
    commit = submodules.DeliverySubmoduleTests.commit
    add_vendor = submodules.DeliverySubmoduleTests.add_vendor

    def setUp(self):
        fixtures.DeliveryTests.setUp(cast(Any, self))
        self.cli_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        if self.plain:
            shutil.rmtree(self.repo / ".git")
        self.state_root = Path(self.tmp.name) / "state"
        self.app = self.repo / "app.py"
        self.app.write_text("def value():\n    return 1\n", encoding="utf-8")
        spec = importlib.util.spec_from_file_location("repair_history_delivery", fixtures.SCRIPT)
        assert spec is not None and spec.loader is not None
        self.delivery = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.delivery)

    @overload
    def run_cli(self, *args: Any, ok: Literal[True] = True, cwd: Path | None = None) -> dict[str, Any]: ...

    @overload
    def run_cli(self, *args: Any, ok: Literal[False], cwd: Path | None = None) -> subprocess.CompletedProcess[str]: ...

    def run_cli(self, *args: Any, ok: bool = True, cwd: Path | None = None) -> dict[str, Any] | subprocess.CompletedProcess[str]:
        result = subprocess.run([sys.executable, "-B", str(fixtures.SCRIPT), *map(str, args),
                                 "--repo", str(self.repo), "--state-root", str(self.state_root)], cwd=cwd or self.repo,
                                text=True, encoding="utf-8", capture_output=True, env=self.cli_env)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    @property
    def checkpoint(self):
        return self.delivery.state_path(self.repo, "demo", self.state_root)

    def paused_verify(self, earlier_pause=False):
        self.start(contract_tier="T1", design_ready=True, questions=["requirements"])
        self.proof = self.write("proof.json", {"mechanical_fixture": True, "observed": "value returns 1"})
        self.run_cli("complete", "--task", "demo", "--stage", "specify", "--actor", "specifier", "--evidence", self.proof)
        authored = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "original-author", "--evidence", self.proof)
        self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(authored, actor="initial-reviewer", source="reviewer-report"))
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "verify")
        if earlier_pause:
            earlier = self.write("earlier-verify-proof.json", {"mechanical_fixture": True, "permission": "run the fixture check"})
            waiting = self.run_cli("pause", "--task", "demo", "--kind", "permission", "--authority", "human",
                                   "--question", "Mechanical fixture permission?", "--actor", "earlier-verify-author", "--evidence", earlier)
            self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(waiting))
        return self.run_cli("pause", "--task", "demo", "--kind", "hard-veto", "--authority", "reviewer",
                            "--question", "Mechanical fixture BLOCK: repair original scope", "--actor", "verify-author",
                            "--actor", "verify-coauthor", "--evidence", self.proof)

    def begin(self, paused, actor="repair-author"):
        review, authorization = self.repair_inputs(paused)
        return self.run_cli("repair", "--task", "demo", "--stage", "implement", "--review", review,
                            "--authorization", authorization, "--actor", actor, "--path", "app.py")

    def assert_invalid_checkpoint(self, state, original):
        self.checkpoint.write_bytes(original)
        with self.assertRaisesRegex(ValueError, "checkpoint refused: malformed"):
            self.delivery.save(self.checkpoint, state)
        self.assertEqual(self.checkpoint.read_bytes(), original)
        state["integrity"] = self.delivery.digest({k: v for k, v in state.items() if k != "integrity"})
        self.checkpoint.write_text(json.dumps(state), encoding="utf-8")
        poisoned = self.checkpoint.read_bytes()
        refused = self.run_cli("status", "--task", "demo", ok=False)
        self.assertIn("checkpoint refused: malformed", refused.stderr)
        self.assertEqual(self.checkpoint.read_bytes(), poisoned)
        self.checkpoint.write_bytes(original)

    def executed_proof(self, attempt):
        command = [sys.executable, "-B", "-c", f"from app import value; assert value() == {attempt}"]
        result = subprocess.run(command, cwd=self.repo, text=True, encoding="utf-8", capture_output=True, env=self.cli_env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.write(f"executed-{attempt}.json", {"mechanical_fixture": True, "command": command,
                          "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})

    def captured_repair(self, paused, relative="both", spelling="parent"):
        """Receipts are external; proof paths mean the original CLI cwd, not receipt.parent."""
        base = Path(self.tmp.name)
        origin = base / "capture-cwd"
        fresh = base / "unrelated" / "fresh-cwd"
        receipts = base / "receipts"
        for directory in (origin, fresh, receipts):
            directory.mkdir(parents=True, exist_ok=True)
        proofs = base / "proofs" if spelling == "parent" else origin / "proofs"
        proofs.mkdir(exist_ok=True)
        if spelling == "alias":
            alias = origin / "proof-alias"
            if not alias.exists():
                alias.symlink_to(proofs, target_is_directory=True)
        raw_prefix = {"parent": "../proofs", "direct": "proofs", "alias": "proof-alias"}[spelling]
        review, authorization = self.repair_inputs(paused)
        receipt_paths = []
        for label, original in (("review", review), ("authorization", authorization)):
            data = json.loads(original.read_bytes())
            proof = proofs / (label + "-proof.json")
            proof.write_bytes(Path(data["evidence"]).read_bytes())
            data["evidence"] = (raw_prefix + "/" + proof.name
                                if relative in (label, "both") else str(proof))
            receipt = receipts / (label + ".json")
            # Keep unusual whitespace so re-serialization would be detectable.
            receipt.write_text(json.dumps(data, indent=3) + "\n\n", encoding="utf-8")
            receipt_paths.append(receipt)
        active = self.run_cli("repair", "--task", "demo", "--stage", "implement",
                              "--review", receipt_paths[0], "--authorization", receipt_paths[1],
                              "--actor", "repair-author", "--actor", "repair-coauthor", "--path", "app.py", cwd=origin)
        return active, origin, fresh, receipt_paths

    def test_captured_relative_repair_proofs_survive_unrelated_cli_cwd(self):
        paused = self.paused_verify(earlier_pause=True)
        prior = self.checkpoint.read_bytes()
        for spelling in ("parent", "direct", "alias"):
            if spelling == "alias" and os.name == "nt":
                continue
            for relative in ("review", "authorization", "both", "neither"):
                with self.subTest(spelling=spelling, relative=relative):
                    self.checkpoint.write_bytes(prior)
                    active, origin, fresh, receipts = self.captured_repair(paused, relative, spelling)
                    raw_receipts = [path.read_bytes() for path in receipts]
                    captured = active["repairs"][-1]["evidence"]
                    for index, receipt in ((1, receipts[0]), (3, receipts[1])):
                        raw = json.loads(receipt.read_bytes())["evidence"]
                        expected = self.delivery.file_record(origin / raw)
                        self.assertEqual(captured[index]["sha256"], expected["sha256"])
                        self.assertTrue(Path(captured[index]["path"]).is_absolute())
                        # macOS /var and /private/var can name the same cwd;
                        # bind the actual captured file, not a spelling alias.
                        self.assertTrue(Path(captured[index]["path"]).samefile(expected["path"]))
                        # Deliberately plausible, unrelated current-cwd proof must not win.
                        if not Path(raw).is_absolute():
                            decoy = fresh / raw
                            decoy.parent.mkdir(parents=True, exist_ok=True)
                            decoy.write_text("Unrelated substituted current-cwd proof\n", encoding="utf-8")
                    persisted = self.checkpoint.read_bytes()
                    self.assertEqual(self.run_cli("status", "--task", "demo", cwd=origin), active)
                    recovered = self.run_cli("status", "--task", "demo", cwd=fresh)
                    self.assertEqual(recovered, active)
                    self.assertEqual(self.checkpoint.read_bytes(), persisted)
                    self.assertEqual(active["partial"][:len(paused["partial"])], paused["partial"])
                    self.assertEqual(active["repairs"][-1]["prior_gate"], paused["gate"])
                    self.assertEqual(active["repairs"][-1]["reopened"], [paused["completed"][-1]])
                    pending = self.run_cli("recheck", "--task", "demo", "--evidence", self.proof, cwd=fresh)
                    self.assertEqual(pending["repairs"][-1]["evidence"][:len(captured)], captured)
                    self.assertEqual(pending["repairs"][-1]["status"], "review")
                    self.assertEqual(pending["raw"], paused["raw"])
                    self.assertEqual(pending["contract"], paused["contract"])
                    unchanged = self.checkpoint.read_bytes()
                    for author in {row["actor"] for row in pending["completed"] + pending["partial"]}:
                        refusal = self.run_cli("resume", "--task", "demo", "--receipt",
                                               self.receipt(pending, actor=author, source="reviewer-report"), ok=False, cwd=fresh)
                        self.assertIn("author cannot clear", refusal.stderr)
                        self.assertEqual(self.checkpoint.read_bytes(), unchanged)
                    cleared = self.run_cli("resume", "--task", "demo", "--receipt",
                                           self.receipt(pending, actor="independent-reviewer", source="reviewer-report"), cwd=fresh)
                    self.assertEqual(cleared["repairs"][-1]["status"], "cleared")
                    self.assertEqual(self.run_cli("status", "--task", "demo", cwd=fresh), cleared)
                    self.assertEqual([path.read_bytes() for path in receipts], raw_receipts)

    def test_captured_proof_replacement_cannot_be_hidden_by_current_cwd_decoy(self):
        active, origin, fresh, receipts = self.captured_repair(self.paused_verify())
        original = self.checkpoint.read_bytes()
        for index, receipt in ((1, receipts[0]), (3, receipts[1])):
            with self.subTest(capture_slot=index):
                path = Path(active["repairs"][-1]["evidence"][index]["path"])
                raw = json.loads(receipt.read_bytes())["evidence"]
                content = path.read_bytes()
                decoy = fresh / raw
                decoy.parent.mkdir(parents=True, exist_ok=True)
                decoy.write_bytes(content)
                for replacement in (None, b"Replaced original capture bytes\n"):
                    if replacement is None:
                        path.unlink()
                    else:
                        path.write_bytes(replacement)
                    for verb in (("status", "--task", "demo"), ("recheck", "--task", "demo", "--evidence", self.proof)):
                        self.run_cli(*verb, ok=False, cwd=fresh)
                        self.assertEqual(self.checkpoint.read_bytes(), original)
                path.write_bytes(content)
        self.assertEqual(self.run_cli("status", "--task", "demo", cwd=origin), active)

    def test_active_capture_binding_refuses_replaced_hash_path_or_receipt(self):
        paused = self.paused_verify()
        prior = self.checkpoint.read_bytes()
        for relative, spelling in (("neither", "direct"), ("review", "parent"),
                                   ("authorization", "direct"), ("both", "alias")):
            if spelling == "alias" and os.name == "nt":
                continue
            with self.subTest(relative=relative, spelling=spelling):
                self.checkpoint.write_bytes(prior)
                self.assert_capture_binding(paused, relative, spelling)

    def assert_capture_binding(self, paused, relative, spelling):
        # Absolute controls separate binding failures from the relative-cwd bug.
        active, origin, fresh, receipts = self.captured_repair(paused, relative, spelling)
        original = self.checkpoint.read_bytes()
        alternate = self.write("unrelated-proof.json", {"mechanical_fixture": True, "unrelated": True})

        def replace_slot(state, slot, record):
            repair = state["repairs"][-1]
            repair["evidence"][slot] = record
            for row in state["partial"][-len(repair["actors"]):]:
                row["evidence"][slot] = record

        for index, receipt in ((1, receipts[0]), (3, receipts[1])):
            content = receipt.read_bytes()
            proof = Path(active["repairs"][-1]["evidence"][index]["path"])
            proof_content = proof.read_bytes()
            for mutation in ("path", "hash", "receipt-field"):
                with self.subTest(capture_slot=index, mutation=mutation):
                    state = json.loads(original)
                    if mutation == "path":
                        replace_slot(state, index, self.delivery.file_record(alternate))
                    elif mutation == "hash":
                        proof.write_bytes(b"Replacement capture\n")
                        replace_slot(state, index, self.delivery.file_record(proof))
                    else:
                        data = json.loads(content)
                        data["evidence"] = str(alternate)
                        receipt.write_text(json.dumps(data), encoding="utf-8")
                        replace_slot(state, index - 1, self.delivery.file_record(receipt))
                        replace_slot(state, index, self.delivery.file_record(alternate))
                    # Even a recomputed outer checksum is not a new repair capture.
                    try:
                        self.assert_invalid_checkpoint(state, original)
                    finally:
                        self.checkpoint.write_bytes(original)
                        receipt.write_bytes(content)
                        proof.write_bytes(proof_content)
        self.assertEqual(self.run_cli("status", "--task", "demo", cwd=fresh), active)

    def test_capture_paths_require_exact_lexical_receipt_relationship(self):
        paused = self.paused_verify()
        prior = self.checkpoint.read_bytes()
        for relative, spelling, mutation in (("neither", "direct", "absolute-mismatch"),
                                             ("both", "direct", "different-bases"),
                                             ("both", "parent", "normalized-parent"),
                                             ("both", "alias", "resolved-alias")):
            if spelling == "alias" and os.name == "nt":
                continue
            with self.subTest(relative=relative, spelling=spelling, mutation=mutation):
                self.checkpoint.write_bytes(prior)
                active, origin, fresh, receipts = self.captured_repair(paused, relative, spelling)
                original = self.checkpoint.read_bytes()
                state = json.loads(original)
                repair = state["repairs"][-1]
                path = Path(repair["evidence"][1]["path"])
                if mutation in ("normalized-parent", "resolved-alias"):
                    replacement = self.delivery.file_record(path.resolve())
                else:
                    base = Path(self.tmp.name) / "substituted-cwd"
                    raw = Path(json.loads(receipts[0].read_bytes())["evidence"])
                    replacement_path = base / (raw if not raw.is_absolute() else path.name)
                    replacement_path.parent.mkdir(parents=True, exist_ok=True)
                    replacement_path.write_bytes(path.read_bytes())
                    replacement = self.delivery.file_record(replacement_path)
                repair["evidence"][1] = replacement
                for row in state["partial"][-len(repair["actors"]):]:
                    row["evidence"][1] = replacement
                # Isolate lexical proof relationships from the binding check.
                # Recomputed hashes are not authentication of synthetic receipts.
                state["gate"]["binding"] = self.delivery.new_gate(state, "hard-veto", "reviewer", "fixture")["binding"]
                self.assert_invalid_checkpoint(state, original)
                self.assertEqual(self.run_cli("status", "--task", "demo", cwd=fresh), active)

    def test_reopened_receipt_timed_replacement_keeps_evidence_drift_diagnostic(self):
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("implementation.json", {"mechanical_fixture": True})
        blocked = self.run_cli("complete", "--task", "demo", "--stage", "implement",
                               "--actor", "original-author", "--evidence", proof)
        prior = self.checkpoint.read_bytes()
        for label in ("review", "authorization"):
            with self.subTest(receipt=label):
                self.checkpoint.write_bytes(prior)
                review, authorization = self.repair_inputs(blocked)
                target = review if label == "review" else authorization
                content = target.read_bytes()
                changed = {**json.loads(content), "decision": "approved" if label == "review" else "denied"}
                replacement = self.write("replacement-receipt.json", changed)
                args = ("repair", "--task", "demo", "--stage", "implement", "--review", review,
                        "--authorization", authorization, "--actor", "repair-author", "--path", "app.py")
                refusal = self.timed("read", target, replacement, *args)
                self.assertEqual(refusal.returncode, 1, refusal.stdout)
                self.assertIn("evidence drift:", refusal.stderr)
                self.assertEqual(self.checkpoint.read_bytes(), prior)
                target.write_bytes(content)
                active = self.run_cli(*args)
                self.assertEqual(self.run_cli("status", "--task", "demo"), active)

    def test_repeated_repairs_supersede_then_clear_and_close_in_fresh_processes(self):
        paused = self.paused_verify(earlier_pause=True)
        original_contract = paused["contract"]
        stale = self.receipt(paused, actor="independent-reviewer", source="reviewer-report")
        for attempt in (2, 3, 4):
            retained = paused["partial"]
            active = self.begin(paused, actor=f"repair-author-{attempt}")
            self.assertEqual(active["partial"][:len(retained)], retained)
            self.assertEqual(self.run_cli("status", "--task", "demo")["repairs"][-1]["status"], "active")
            self.app.write_text(f"def value():\n    return {attempt}\n", encoding="utf-8")
            fixed = self.executed_proof(attempt)
            pending = self.run_cli("recheck", "--task", "demo", "--evidence", fixed)
            self.assertEqual(pending["repairs"][-1]["status"], "review")
            self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "verify")
            self.assertEqual(pending["contract"], original_contract)
            unchanged = self.checkpoint.read_bytes()
            self.assertIn("decision refused:", self.run_cli("resume", "--task", "demo", "--receipt", stale, ok=False).stderr)
            self.assertEqual(self.checkpoint.read_bytes(), unchanged)
            for author in {row["actor"] for row in pending["completed"] + pending["partial"]}:
                refused = self.run_cli("resume", "--task", "demo", "--receipt",
                                       self.receipt(pending, actor=author, source="reviewer-report"), ok=False)
                self.assertIn("author cannot clear", refused.stderr)
                self.assertEqual(self.checkpoint.read_bytes(), unchanged)
            if attempt == 2:
                # A new BLOCK at re-review supersedes the preceding repair.
                paused = pending
                continue
            ready = self.run_cli("resume", "--task", "demo", "--receipt",
                                 self.receipt(pending, actor="fresh-independent-reviewer", source="reviewer-report"))
            self.assertEqual(ready["repairs"][-1]["status"], "cleared")
            if attempt == 3:
                paused = self.run_cli("pause", "--task", "demo", "--kind", "hard-veto", "--authority", "reviewer",
                                      "--question", "Mechanical new verification BLOCK", "--actor", "later-verify-author", "--evidence", fixed)
        self.assertEqual([row["status"] for row in ready["repairs"]], ["superseded", "cleared", "cleared"])
        closure = self.write("closure.json", {"criteria": [{"criterion": "feature works", "observed": "real value() returned 4",
                             "evidence": [str(fixed)]}], "changes": ["app.py"], "tests": ["assert value() == 4"],
                             "skips": [], "limits": ["Synthetic receipts test binding mechanics; not authenticated human consent"], "remaining_gates": []})
        closed = self.run_cli("complete", "--task", "demo", "--stage", "verify", "--actor", "final-verifier",
                              "--evidence", fixed, "--closure", closure)
        self.assertIsNone(closed["next"])
        self.assertIsNone(self.run_cli("status", "--task", "demo")["next"])
        self.assertEqual(closed["contract"], original_contract)

    def test_scoped_recheck_refuses_unrelated_bytes_or_mode_changes(self):
        outside = self.repo / "unrelated.py"
        outside.write_text("# original\n", encoding="utf-8")
        self.begin(self.paused_verify())
        original = self.checkpoint.read_bytes()
        self.app.write_text("def value():\n    return 2\n", encoding="utf-8")
        fixed = self.executed_proof(2)
        outside.write_text("# unrelated mutation\n", encoding="utf-8")
        self.assertIn("unrelated workspace drift", self.run_cli("recheck", "--task", "demo", "--evidence", fixed, ok=False).stderr)
        self.assertEqual(self.checkpoint.read_bytes(), original)
        outside.write_text("# original\n", encoding="utf-8")
        if os.name != "nt":
            mode = outside.stat().st_mode
            outside.chmod(mode | 0o111)
            self.assertIn("unrelated workspace drift", self.run_cli("recheck", "--task", "demo", "--evidence", fixed, ok=False).stderr)
            self.assertEqual(self.checkpoint.read_bytes(), original)
            outside.chmod(mode)
        self.assertEqual(self.run_cli("recheck", "--task", "demo", "--evidence", fixed)["repairs"][-1]["status"], "review")

    def test_denied_stale_or_wrong_binding_receipts_preserve_checkpoint_bytes(self):
        paused = self.paused_verify()
        review, authorization = self.repair_inputs(paused)
        data = json.loads(authorization.read_text(encoding="utf-8"))
        original = self.checkpoint.read_bytes()
        for changes in ({"decision": "denied"}, {"gate": "stale"}, {"binding": "0" * 64}):
            with self.subTest(repair_authorization=changes):
                bad = self.write("bad-authorization.json", {**data, **changes})
                self.assertIn("repair refused:", self.run_cli("repair", "--task", "demo", "--stage", "implement",
                              "--review", review, "--authorization", bad, "--actor", "repair-author", "--path", "app.py", ok=False).stderr)
                self.assertEqual(self.checkpoint.read_bytes(), original)
        active = self.begin(paused)
        original = self.checkpoint.read_bytes()
        self.assertIn("decision refused:", self.run_cli("resume", "--task", "demo", "--receipt",
                      self.receipt(active, actor="reviewer", source="reviewer-report"), ok=False).stderr)
        self.assertEqual(self.checkpoint.read_bytes(), original)
        pending = self.run_cli("recheck", "--task", "demo", "--evidence", self.proof)
        data = json.loads(self.receipt(pending, actor="independent-reviewer", source="reviewer-report").read_text(encoding="utf-8"))
        original = self.checkpoint.read_bytes()
        for changes in ({"decision": "denied"}, {"gate": paused["gate"]["id"]}, {"binding": "0" * 64}):
            with self.subTest(review_receipt=changes):
                self.assertIn("decision refused:", self.run_cli("resume", "--task", "demo", "--receipt",
                              self.write("bad-review-receipt.json", {**data, **changes}), ok=False).stderr)
                self.assertEqual(self.checkpoint.read_bytes(), original)

    def test_indexed_root_gitlink_marker_directory_survives_checkpoint_repair(self):
        if self.plain:
            self.skipTest("Plain projects do not have Gitlinks")
        self.commit(self.repo)
        marker = self.repo / "docs/audit/.run-starts.json"
        marker.mkdir(parents=True)
        head = self.git(self.repo, "rev-parse", "HEAD")
        self.git(self.repo, "update-index", "--add", "--cacheinfo", f"160000,{head},docs/audit/.run-starts.json")
        self.assertIn("160000", self.git(self.repo, "ls-files", "--stage", "--", "docs/audit/.run-starts.json"))
        emitted = self.delivery.snapshot(self.repo, self.delivery.local_area(self.repo, self.state_root))
        self.assertEqual(emitted["submodules"]["docs/audit/.run-starts.json"], {"directory": True})
        paused = self.paused_verify()
        self.assertEqual(paused["snapshot"], emitted)
        original = self.checkpoint.read_bytes()
        self.assertEqual(self.run_cli("status", "--task", "demo"), paused)
        refused = self.run_cli("start", "--task", "demo", "--facts", Path(self.tmp.name) / "facts.json",
                               "--audit-root", self.audit, "--compiled-id", self.compiled_id, ok=False)
        self.assertIn("task exists: resume it", refused.stderr)
        self.assertEqual(self.checkpoint.read_bytes(), original)
        active = self.begin(paused)
        self.assertEqual(active["repairs"][-1]["prior_gate"], paused["gate"])
        self.assertEqual(active["snapshot"], paused["snapshot"])
        self.assertEqual(self.run_cli("status", "--task", "demo"), active)

    @unittest.skipIf(os.name == "nt" or not hasattr(os, "mkfifo"), "FIFO requires POSIX")
    def test_indexed_root_gitlink_marker_fifo_survives_checkpoint_repair(self):
        if self.plain:
            self.skipTest("Plain projects do not have Gitlinks")
        self.commit(self.repo)
        marker = self.repo / "docs/audit/.run-starts.json"
        marker.parent.mkdir(parents=True)
        os.mkfifo(marker)
        head = self.git(self.repo, "rev-parse", "HEAD")
        self.git(self.repo, "update-index", "--add", "--cacheinfo", f"160000,{head},docs/audit/.run-starts.json")
        self.assertIn("160000", self.git(self.repo, "ls-files", "--stage", "--", "docs/audit/.run-starts.json"))
        emitted = self.delivery.snapshot(self.repo, self.delivery.local_area(self.repo, self.state_root))
        self.assertEqual(emitted["submodules"]["docs/audit/.run-starts.json"], {"special": 4096})
        paused = self.paused_verify()
        self.assertEqual(paused["snapshot"], emitted)
        original = self.checkpoint.read_bytes()
        self.assertEqual(self.run_cli("status", "--task", "demo"), paused)
        self.assertEqual(self.checkpoint.read_bytes(), original)
        active = self.begin(paused)
        self.assertEqual(active["repairs"][-1]["prior_gate"], paused["gate"])
        self.assertEqual(self.run_cli("status", "--task", "demo"), active)

    @unittest.skipIf(os.name == "nt" or not hasattr(os, "mkfifo"), "FIFO requires POSIX")
    def test_indexed_nested_gitlink_marker_directory_and_fifo_survive_repair(self):
        if self.plain:
            self.skipTest("Plain projects do not have Gitlinks")
        vendor = self.add_vendor()
        marker = vendor / "docs/audit/.run-starts.json"
        marker.parent.mkdir(parents=True)
        head = self.git(vendor, "rev-parse", "HEAD")
        self.git(vendor, "update-index", "--add", "--cacheinfo", f"160000,{head},docs/audit/.run-starts.json")
        for kind, expected in (("directory", {"directory": True}), ("fifo", {"special": 4096})):
            with self.subTest(kind=kind):
                if kind == "directory":
                    marker.mkdir()
                else:
                    os.mkfifo(marker)
                self.assertIn("160000", self.git(vendor, "ls-files", "--stage", "--", "docs/audit/.run-starts.json"))
                self.state_root = Path(self.tmp.name) / ("state-" + kind)
                emitted = self.delivery.snapshot(self.repo, self.delivery.local_area(self.repo, self.state_root))
                nested = emitted["submodules"]["vendor"]["checkout"]["submodules"]["docs/audit/.run-starts.json"]
                self.assertEqual(nested, expected)
                paused = self.paused_verify()
                self.assertEqual(paused["snapshot"], emitted)
                original = self.checkpoint.read_bytes()
                self.assertEqual(self.run_cli("status", "--task", "demo"), paused)
                self.assertEqual(self.checkpoint.read_bytes(), original)
                active = self.begin(paused)
                self.assertEqual(active["snapshot"], emitted)
                self.assertEqual(active["repairs"][-1]["prior_gate"], paused["gate"])
                self.assertEqual(self.run_cli("status", "--task", "demo"), active)
                original_active = self.checkpoint.read_bytes()
                for invalid in ({"directory": False}, {"special": True}, {"special": "4096"},
                                {"special": 32768}, {"directory": True, "special": 4096}):
                    with self.subTest(kind=kind, invalid=invalid):
                        state = json.loads(original_active)
                        state["snapshot"]["submodules"]["vendor"]["checkout"]["submodules"]["docs/audit/.run-starts.json"] = invalid
                        self.assert_invalid_checkpoint(state, original_active)
                if kind == "directory":
                    marker.rmdir()
                else:
                    marker.unlink()

    def test_indexed_gitlink_sentinels_refuse_wrong_types_modes_and_mixed_records(self):
        if self.plain:
            self.skipTest("Plain projects do not have Gitlinks")
        self.commit(self.repo)
        marker = self.repo / "docs/audit/.run-starts.json"
        marker.mkdir(parents=True)
        head = self.git(self.repo, "rev-parse", "HEAD")
        self.git(self.repo, "update-index", "--add", "--cacheinfo", f"160000,{head},docs/audit/.run-starts.json")
        paused = self.paused_verify()
        original = self.checkpoint.read_bytes()
        for suffix in self.delivery.RUNTIME_START_MARKERS:
            with self.subTest(allowed_suffix=suffix):
                for sentinel in ({"directory": True}, {"special": 4096}):
                    variant = json.loads(original)["snapshot"]
                    variant["submodules"] = {"payload/" + suffix: sentinel}
                    self.assertTrue(self.delivery.valid_snapshot(variant))
        for name in ("unrelated.py", "docs/audit/not-a-marker.json", "vendor/docs/audit/.run-starts.json.bak",
                     "../docs/audit/.run-starts.json"):
            with self.subTest(wrong_name=name):
                state = json.loads(original)
                state["snapshot"]["submodules"][name] = state["snapshot"]["submodules"].pop("docs/audit/.run-starts.json")
                self.assertFalse(self.delivery.valid_snapshot(state["snapshot"]))
                self.assert_invalid_checkpoint(state, original)
        wrong = ({"directory": False}, {"directory": 1}, {"directory": "true"}, {"directory": None},
                 {"special": False}, {"special": True}, {"special": "4096"}, {"special": None},
                 {"special": 0}, {"special": 32768}, {"special": 16384}, {"special": 40960},
                 {"special": 2.5}, {"directory": True, "special": 4096},
                 {"directory": True, "link": "/elsewhere"},
                 {"gitlink": [f"160000 {head} 0"], "checkout": "unavailable", "special": 4096},
                 {"gitlink": [f"160000 {head} 0"], "checkout": "unavailable", "directory": True},
                 {"arbitrary": "dictionary"}, {})
        for row in wrong:
            with self.subTest(row=row):
                state = json.loads(original)
                state["snapshot"]["submodules"]["docs/audit/.run-starts.json"] = row
                self.assertFalse(self.delivery.valid_snapshot(state["snapshot"]))
                self.assert_invalid_checkpoint(state, original)
        # A forged outer integrity cannot turn a malformed sentinel into permission
        # to replace the original task or begin an unreviewed repair.
        state = json.loads(original)
        state["snapshot"]["submodules"]["docs/audit/.run-starts.json"] = {"special": "4096"}
        state["integrity"] = self.delivery.digest({k: v for k, v in state.items() if k != "integrity"})
        self.checkpoint.write_text(json.dumps(state), encoding="utf-8")
        poisoned = self.checkpoint.read_bytes()
        for argv in (("start", "--task", "demo", "--facts", Path(self.tmp.name) / "facts.json",
                      "--audit-root", self.audit, "--compiled-id", self.compiled_id),
                     ("repair", "--task", "demo", "--stage", "implement", "--review", self.proof,
                      "--authorization", self.proof, "--actor", "repair-author", "--path", "app.py")):
            self.assertIn("checkpoint refused: malformed", self.run_cli(*argv, ok=False).stderr)
            self.assertEqual(self.checkpoint.read_bytes(), poisoned)
        self.checkpoint.write_bytes(original)
        self.assertEqual(self.run_cli("status", "--task", "demo"), paused)

    @unittest.skipIf(os.name == "nt", "Directory symlink creation requires Windows privileges")
    def test_indexed_root_gitlink_symlink_survives_fresh_start_status_and_repair(self):
        if self.plain:
            self.skipTest("Plain projects do not have Gitlinks")
        self.commit(self.repo)
        target = Path(self.tmp.name) / "external-dependency"
        target.mkdir()
        (target / "product.py").write_text("# outside the link\n", encoding="utf-8")
        head = self.git(self.repo, "rev-parse", "HEAD")
        self.git(self.repo, "update-index", "--add", "--cacheinfo", f"160000,{head},dependency")
        (self.repo / "dependency").symlink_to(target, target_is_directory=True)
        paused = self.paused_verify()
        self.assertEqual(paused["snapshot"]["submodules"]["dependency"], {"link": str(target)})
        original = self.checkpoint.read_bytes()
        (target / "product.py").write_text("# changed outside the link\n", encoding="utf-8")
        self.assertEqual(self.run_cli("status", "--task", "demo"), paused)
        self.assertEqual(self.checkpoint.read_bytes(), original)
        active = self.begin(paused)
        self.assertEqual(active["repairs"][-1]["prior_gate"], paused["gate"])
        self.assertEqual(self.run_cli("status", "--task", "demo"), active)
        self.assertEqual(active["snapshot"], paused["snapshot"])

    @unittest.skipIf(os.name == "nt", "Directory symlink creation requires Windows privileges")
    def test_indexed_nested_gitlink_symlink_survives_fresh_start_status_and_repair(self):
        if self.plain:
            self.skipTest("Plain projects do not have Gitlinks")
        vendor = self.add_vendor()
        source = Path(self.tmp.name) / "nested-source"
        source.mkdir()
        self.git(source, "init", "-q")
        (source / "nested.py").write_text("# nested original\n", encoding="utf-8")
        self.commit(source)
        self.git(vendor, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(source), "nested")
        self.commit(vendor)
        self.commit(self.repo)
        target = Path(self.tmp.name) / "preserved-nested-checkout"
        (vendor / "nested").rename(target)
        (vendor / "nested").symlink_to(target, target_is_directory=True)
        paused = self.paused_verify()
        self.assertEqual(paused["snapshot"]["submodules"]["vendor"]["checkout"]["submodules"]["nested"],
                         {"link": str(target)})
        original = self.checkpoint.read_bytes()
        (target / "nested.py").write_text("# changed outside the link\n", encoding="utf-8")
        self.assertEqual(self.run_cli("status", "--task", "demo"), paused)
        self.assertEqual(self.checkpoint.read_bytes(), original)
        active = self.begin(paused)
        self.assertEqual(self.run_cli("status", "--task", "demo"), active)
        self.assertEqual(active["snapshot"], paused["snapshot"])
        original = self.checkpoint.read_bytes()
        for bad in (None, "", 42, {"target": str(target)}, {"link": str(target), "checkout": "unavailable"}):
            with self.subTest(link_record=bad):
                state = json.loads(original)
                state["snapshot"]["submodules"]["vendor"]["checkout"]["submodules"]["nested"] = (
                    bad if isinstance(bad, dict) else {"link": bad})
                self.assertFalse(self.delivery.valid_snapshot(state["snapshot"]))
                self.assert_invalid_checkpoint(state, original)
        self.assertEqual(self.run_cli("status", "--task", "demo"), active)

    def test_malformed_recursive_submodule_snapshot_is_refused_before_write(self):
        if self.plain:
            self.skipTest("Plain projects do not have Gitlink snapshots")
        vendor = self.add_vendor()
        source = Path(self.tmp.name) / "nested-source"
        source.mkdir()
        self.git(source, "init", "-q")
        (source / "nested.py").write_text("# nested original\n", encoding="utf-8")
        self.commit(source)
        self.git(vendor, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(source), "nested")
        self.commit(vendor)
        self.commit(self.repo)
        started = self.start()
        original = self.checkpoint.read_bytes()
        self.assertIsInstance(started["snapshot"]["submodules"]["vendor"]["checkout"], dict)
        mutations = [
            ("submodules-null", lambda s: s["snapshot"].update(submodules=None)),
            ("checkout-null", lambda s: s["snapshot"]["submodules"]["vendor"].update(checkout=None)),
            ("index-null", lambda s: s["snapshot"]["submodules"]["vendor"]["checkout"].update(index=None)),
            ("nested-submodules-null", lambda s: s["snapshot"]["submodules"]["vendor"]["checkout"].update(submodules=None)),
            ("nested-checkout-null", lambda s: s["snapshot"]["submodules"]["vendor"]["checkout"]["submodules"]["nested"].update(checkout=None)),
            ("nested-index-null", lambda s: s["snapshot"]["submodules"]["vendor"]["checkout"]["submodules"]["nested"]["checkout"].update(index=None)),
            ("gitlink-wrong-type", lambda s: s["snapshot"]["submodules"]["vendor"].update(gitlink=[None])),
        ]
        for name, mutate in mutations:
            with self.subTest(snapshot=name):
                state = json.loads(original)
                mutate(state)
                self.assert_invalid_checkpoint(state, original)
        self.assertEqual(self.run_cli("status", "--task", "demo"), started)
        # A real uninitialized nested checkout remains a supported snapshot.
        self.git(vendor, "submodule", "deinit", "-f", "nested")
        self.state_root = Path(self.tmp.name) / "unavailable-state"
        unavailable = self.start()
        self.assertEqual(unavailable["snapshot"]["submodules"]["vendor"]["checkout"]["submodules"]["nested"]["checkout"], "unavailable")
        self.assertEqual(self.run_cli("status", "--task", "demo"), unavailable)

    def test_malformed_snapshot_is_refused_before_checkpoint_write(self):
        self.paused_verify()
        original = self.checkpoint.read_bytes()
        snapshot = json.loads(original)["snapshot"]
        for malformed in ({}, {k: v for k, v in snapshot.items() if k != "files"},
                          {**snapshot, "files": {}}, {**snapshot, "files": "not-a-digest"},
                          {**snapshot, "head": None}, {**snapshot, "branch": []}):
            with self.subTest(snapshot=malformed):
                state = json.loads(original)
                state["snapshot"] = malformed
                self.assert_invalid_checkpoint(state, original)

    def test_save_cannot_emit_an_unsupported_checkpoint_version(self):
        self.paused_verify()
        original = self.checkpoint.read_bytes()
        for version in (1, None, "missing"):
            with self.subTest(version=version):
                state = json.loads(original)
                if version == "missing":
                    state.pop("version")
                else:
                    state["version"] = version
                with self.assertRaisesRegex(ValueError, "checkpoint refused:"):
                    self.delivery.save(self.checkpoint, state)
                self.assertEqual(self.checkpoint.read_bytes(), original)

    def test_drift_and_integrity_refusals_do_not_rewrite_checkpoint(self):
        self.begin(self.paused_verify())
        self.run_cli("recheck", "--task", "demo", "--evidence", self.proof)
        original = self.checkpoint.read_bytes()
        cases = [("corrupt integrity", {"integrity": "0" * 64}, "corrupt or unsupported"),
                 ("wrong task", {"task": "other-task"}, "identity drift:"),
                 ("wrong worktree", {"identity": {"root": str(Path(self.tmp.name) / "other-project"), "kind": "plain"}}, "identity drift:"),
                 ("wrong state area", {"local_area": str(Path(self.tmp.name) / "other-state")}, "identity drift:")]
        for name, changes, error in cases:
            with self.subTest(case=name):
                state = json.loads(original)
                state.update(changes)
                if name != "corrupt integrity":
                    state["integrity"] = self.delivery.digest({k: v for k, v in state.items() if k != "integrity"})
                self.checkpoint.write_text(json.dumps(state), encoding="utf-8")
                poisoned = self.checkpoint.read_bytes()
                self.assertIn(error, self.run_cli("status", "--task", "demo", ok=False).stderr)
                self.assertEqual(self.checkpoint.read_bytes(), poisoned)
                self.checkpoint.write_bytes(original)
        for path, label in ((self.proof, "evidence drift:"), (Path(self.tmp.name) / "facts.json", "input drift:")):
            with self.subTest(file=label):
                content = path.read_bytes()
                path.write_bytes(content + b"\nchanged fixture bytes\n")
                self.assertIn(label, self.run_cli("status", "--task", "demo", ok=False).stderr)
                self.assertEqual(self.checkpoint.read_bytes(), original)
                with self.assertRaisesRegex(ValueError, label):
                    self.delivery.save(self.checkpoint, json.loads(original))
                self.assertEqual(self.checkpoint.read_bytes(), original)
                path.write_bytes(content)
        log = self.log.read_bytes()
        rows = [json.loads(line) for line in log.splitlines()]
        rows[0]["prompt"] += "\nChanged original compiler input"
        self.log.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        self.assertRegex(self.run_cli("status", "--task", "demo", ok=False).stderr, r"contract (?:refused|drift):")
        self.assertEqual(self.checkpoint.read_bytes(), original)
        self.log.write_bytes(log)
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "verify")

    def test_original_raw_cannot_drift_under_valid_integrity(self):
        self.begin(self.paused_verify())
        original = self.checkpoint.read_bytes()
        state = json.loads(original)
        state["raw"] += "\nInvented replacement acceptance criterion"
        self.assert_invalid_checkpoint(state, original)

    def test_review_gate_cannot_erase_displaced_verification_authors(self):
        self.begin(self.paused_verify(earlier_pause=True))
        pending = self.run_cli("recheck", "--task", "demo", "--evidence", self.proof)
        original = self.checkpoint.read_bytes()
        state = json.loads(original)
        state["partial"] = [row for row in state["partial"] if row["stage"] != "verify"]
        self.assert_invalid_checkpoint(state, original)
        self.checkpoint.write_text(json.dumps(state), encoding="utf-8")
        poisoned = self.checkpoint.read_bytes()
        refusal = self.run_cli("resume", "--task", "demo", "--receipt",
                               self.receipt(pending, actor="verify-author", source="reviewer-report"), ok=False)
        self.assertIn("checkpoint refused: malformed", refusal.stderr)
        self.assertEqual(self.checkpoint.read_bytes(), poisoned)
        self.checkpoint.write_bytes(original)
        self.assertEqual(self.run_cli("status", "--task", "demo"), pending)

    def test_active_reopen_cannot_erase_all_displaced_verification_authors(self):
        self.begin(self.paused_verify(earlier_pause=True))
        original = self.checkpoint.read_bytes()
        state = json.loads(original)
        state["partial"] = [row for row in state["partial"] if row["stage"] != "verify"]
        self.assert_invalid_checkpoint(state, original)
        self.checkpoint.write_text(json.dumps(state), encoding="utf-8")
        poisoned = self.checkpoint.read_bytes()
        refusal = self.run_cli("recheck", "--task", "demo", "--evidence", self.proof, ok=False)
        self.assertIn("checkpoint refused: malformed", refusal.stderr)
        self.assertEqual(self.checkpoint.read_bytes(), poisoned)
        self.checkpoint.write_bytes(original)
        pending = self.run_cli("recheck", "--task", "demo", "--evidence", self.proof)
        retained = self.checkpoint.read_bytes()
        for author in ("earlier-verify-author", "verify-author", "verify-coauthor"):
            refusal = self.run_cli("resume", "--task", "demo", "--receipt",
                                   self.receipt(pending, actor=author, source="reviewer-report"), ok=False)
            self.assertIn("author cannot clear", refusal.stderr)
            self.assertEqual(self.checkpoint.read_bytes(), retained)

    def test_displaced_history_requires_exact_valid_repair_witness(self):
        self.begin(self.paused_verify())
        original = self.checkpoint.read_bytes()
        cases = [
            ("no repair", lambda s: s.pop("repairs")),
            ("current-stage repair", lambda s: s["repairs"][-1].update(reopened=[])),
            ("wrong reopened stage", lambda s: s["repairs"][-1]["reopened"][0].update(stage="specify")),
            ("multiple reopened rows", lambda s: s["repairs"][-1]["reopened"].append(s["repairs"][-1]["reopened"][0])),
            ("wrong prior gate stage", lambda s: s["repairs"][-1]["prior_gate"].update(stage="implement")),
            ("wrong prior authority", lambda s: s["repairs"][-1]["prior_gate"].update(authority="human")),
            ("wrong prior kind", lambda s: s["repairs"][-1]["prior_gate"].update(kind="permission")),
            ("wrong prior id", lambda s: s["repairs"][-1]["prior_gate"].update(id="unbound")),
            ("wrong prior binding", lambda s: s["repairs"][-1]["prior_gate"].update(binding="0" * 64)),
            ("wrong prior evidence", lambda s: s["repairs"][-1]["prior_gate"].update(evidence=[])),
            ("wrong before manifest", lambda s: s["repairs"][-1]["before"]["entries"].update({"intruder.py": None})),
            ("wrong current gate stage", lambda s: s["gate"].update(stage="verify")),
            ("wrong active binding", lambda s: s["gate"].update(binding="0" * 64)),
            ("mutated repair paths", lambda s: s["repairs"][-1].update(paths=["unrelated.py"])),
            ("missing reopened proof", lambda s: s["partial"].pop(-2)),
            ("unrelated future author", lambda s: s["partial"].insert(0, {"stage": "verify", "actor": "intruder", "evidence": []})),
            ("changed preserved author", lambda s: s["partial"][0].update(actor="intruder")),
        ]
        for name, mutate in cases:
            with self.subTest(case=name):
                state = json.loads(original)
                mutate(state)
                self.assert_invalid_checkpoint(state, original)
        for status in ("review", "cleared", "superseded"):
            with self.subTest(historical_status=status):
                state = json.loads(original)
                state["repairs"][-1]["status"] = status
                self.assert_invalid_checkpoint(state, original)

    def test_repeated_verify_pauses_with_different_proof_preserve_all_authors(self):
        paused = self.paused_verify(earlier_pause=True)
        active = self.begin(paused)
        self.assertEqual(active["partial"][:len(paused["partial"])], paused["partial"])
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "implement")
        pending = self.run_cli("recheck", "--task", "demo", "--evidence", self.proof)
        self.assertIn("author cannot clear", self.run_cli("resume", "--task", "demo", "--receipt",
                      self.receipt(pending, actor="earlier-verify-author", source="reviewer-report"), ok=False).stderr)

    def test_malformed_partial_and_repair_records_fail_closed(self):
        self.begin(self.paused_verify())
        original = self.checkpoint.read_bytes()
        for field, value in (("partial", None), ("partial", []), ("repairs", None), ("repairs", {})):
            with self.subTest(field=field, value=value):
                state = json.loads(original)
                state[field].append(value)
                with self.assertRaisesRegex(ValueError, "checkpoint refused: malformed"):
                    self.delivery.save(self.checkpoint, state)
                self.assertEqual(self.checkpoint.read_bytes(), original)
                state["integrity"] = self.delivery.digest({k: v for k, v in state.items() if k != "integrity"})
                self.checkpoint.write_text(json.dumps(state), encoding="utf-8")
                poisoned = self.checkpoint.read_bytes()
                refused = self.run_cli("status", "--task", "demo", ok=False)
                self.assertIn("checkpoint refused: malformed", refused.stderr)
                self.assertEqual(self.checkpoint.read_bytes(), poisoned)
                self.checkpoint.write_bytes(original)

    def test_save_refuses_invalid_transition_before_overwriting_valid_bytes(self):
        self.paused_verify()
        original = self.checkpoint.read_bytes()
        invalid = json.loads(original)
        # A real shape violation with otherwise valid evidence, not a mock.
        invalid["partial"].append({"stage": "unrelated-future", "actor": "intruder", "evidence": []})
        with self.assertRaisesRegex(ValueError, "checkpoint refused: malformed"):
            self.delivery.save(self.checkpoint, invalid)
        self.assertEqual(self.checkpoint.read_bytes(), original)
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "verify")

    def test_verify_pause_repair_is_loadable_before_any_product_edit(self):
        paused = self.paused_verify()
        original_product = self.app.read_bytes()
        active = self.begin(paused)
        self.assertEqual(active["partial"][:len(paused["partial"])], paused["partial"])
        self.assertEqual(active["repairs"][-1]["prior_gate"], paused["gate"])
        self.assertEqual(active["repairs"][-1]["reopened"], [paused["completed"][-1]])
        self.assertEqual(active["completed"], paused["completed"][:-1])
        persisted = self.checkpoint.read_bytes()
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "implement")
        self.assertEqual(self.checkpoint.read_bytes(), persisted)
        pending = self.run_cli("recheck", "--task", "demo", "--evidence", self.proof)
        self.assertEqual(pending["repairs"][-1]["status"], "review")
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "verify")
        self.assertEqual(self.app.read_bytes(), original_product)
        self.assertEqual(pending["contract"], paused["contract"])
        self.assertEqual(pending["raw"], paused["raw"])
        for author in ("specifier", "original-author", "verify-author", "verify-coauthor", "repair-author"):
            unchanged = self.checkpoint.read_bytes()
            refused = self.run_cli("resume", "--task", "demo", "--receipt",
                                   self.receipt(pending, actor=author, source="reviewer-report"), ok=False)
            self.assertIn("author cannot clear", refused.stderr)
            self.assertEqual(self.checkpoint.read_bytes(), unchanged)


class PlainRepairHistoryTests(RepairHistoryTests):
    plain = True


if __name__ == "__main__":
    unittest.main()
