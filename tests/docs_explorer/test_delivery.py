"""Delivery routing/checkpoint behavior in real disposable Git repositories."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from typing import Any, Literal, overload

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "pack/scripts/delivery.py"


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def write(self, name, value):
        path = Path(self.tmp.name) / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    @overload
    def run_cli(self, *args: Any, ok: Literal[True] = True) -> dict[str, Any]: ...

    @overload
    def run_cli(self, *args: Any, ok: Literal[False]) -> subprocess.CompletedProcess[str]: ...

    def run_cli(self, *args: Any, ok: bool = True) -> dict[str, Any] | subprocess.CompletedProcess[str]:
        if args and args[0] != "route" and getattr(self, "state_root", None):
            args = (*args, "--state-root", self.state_root)
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                cwd=self.repo, text=True, encoding="utf-8", capture_output=True,
                                env=getattr(self, "cli_env", None))
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def facts(self, **overrides):
        value = {"kind": "feature", "tier": "T0", "questions": [], "risks": [],
                 "ui": False, "coordination": False}
        value.update(overrides)
        return self.write("facts.json", value)

    def start(self, **overrides):
        contract_tier = overrides.pop("contract_tier", "T0")
        raw = ("Goal: Add a small feature\nDone when: feature works\nNot in scope: release\n"
               f"Tier: {contract_tier}\nFan-out cap: 0\nContext ceiling: 20000\nMain-line budget: 20\n")
        self.audit = Path(self.tmp.name) / "local"
        raw_path = Path(self.tmp.name) / "raw.txt"
        raw_path.write_text(raw, encoding="utf-8")
        skeleton = Path(self.tmp.name) / "compiled.json"
        compiler = ROOT / "pack/scripts/prompt-compile.py"
        audit_cli = ROOT / "pack/scripts/audit-log.py"
        result = subprocess.run([sys.executable, str(audit_cli), "--root", str(self.audit), "append",
                                 "--kind", "prompt", "--shortname", "delivery", "--session", "test",
                                 "--prompt-file", str(raw_path), "--summary", "raw request"],
                                cwd=self.repo, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        raw_id = json.loads((self.audit / "audit/audit-log.jsonl").read_text(encoding="utf-8").splitlines()[-1])["id"]
        for args in (["skeleton", "--from-audit", raw_id, "--harness", "claude-code",
                      "--out", str(skeleton), "--audit-root", str(self.audit)],
                     ["finish", str(skeleton), "--session", "test", "--audit-root", str(self.audit), "--no-clipboard"]):
            result = subprocess.run([sys.executable, str(compiler), *args], cwd=self.repo,
                                    capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
        self.log = self.audit / "audit/audit-log.jsonl"
        entries = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        self.compiled_id = entries[-1]["id"]
        return self.run_cli("start", "--task", "demo", "--facts", self.facts(**overrides),
                            "--audit-root", self.audit, "--compiled-id", self.compiled_id)

    def receipt(self, state, actor="operator", source="human-message", decision="approved"):
        gate = state["gate"]
        evidence = self.write("decision-evidence-" + gate["id"] + ".json", {"message": "Approve this scoped gate"})
        return self.write("receipt-" + gate["id"] + ".json", {"task": state["task"], "gate": gate["id"],
                    "binding": gate["binding"], "authority": gate["authority"],
                    "actor": actor, "source": source, "decision": decision,
                    "evidence": str(evidence)})

    def test_defect_gate_requires_explicit_bound_human_decision(self):
        self.start(kind="defect")
        evidence = self.write("diagnosis.json", {"root_cause": "verified", "phases": [1]})
        paused = self.run_cli("complete", "--task", "demo", "--stage", "investigate",
                              "--actor", "investigator", "--evidence", evidence)
        self.assertEqual(paused["next"], "repair-review")
        self.assertEqual(paused["gate"]["authority"], "human")
        result = self.run_cli("complete", "--task", "demo", "--stage", "repair-review",
                              "--actor", "model", "--evidence", evidence, ok=False)
        self.assertIn("stage refused:", result.stderr)
        receipt = self.receipt(paused, source="model-output")
        self.assertIn("decision refused:", self.run_cli("resume", "--task", "demo", "--receipt", receipt, ok=False).stderr)
        receipt = self.receipt(paused)
        resumed = self.run_cli("resume", "--task", "demo", "--receipt", receipt)
        self.assertEqual(resumed["next"], "implement")
        self.assertEqual([r["stage"] for r in resumed["completed"]], ["investigate", "repair-review"])
        self.assertIn("decision refused:", self.run_cli("resume", "--task", "demo", "--receipt", receipt, ok=False).stderr)

    def test_docs_only_t0_self_check_does_not_remove_real_hard_veto(self):
        state = self.start(kind="docs")
        self.assertEqual(state["stages"], ["document", "verify"])
        proof = self.write("docs-proof.json", {"observed": "requested document rendered"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "document",
                             "--actor", "author", "--evidence", proof)
        self.assertIsNone(state["gate"])
        paused = self.run_cli("pause", "--task", "demo", "--kind", "hard-veto", "--authority", "reviewer",
                              "--question", "Clear this actual applicable veto?", "--actor", "author", "--evidence", proof)
        self.assertIn("decision refused:", self.run_cli("resume", "--task", "demo", "--receipt",
                      self.receipt(paused, actor="author", source="reviewer-report"), ok=False).stderr)
        cleared = self.run_cli("resume", "--task", "demo", "--receipt",
                               self.receipt(paused, actor="reviewer", source="reviewer-report"))
        self.assertEqual(cleared["next"], "verify")

    def test_risk_bearing_documentation_still_needs_independent_review(self):
        self.start(kind="docs", risks=["contracts"], design_ready=True)
        proof = self.write("contract-proof.json", {"observed": "contract docs checked"})
        state = self.run_cli("complete", "--task", "demo", "--stage", "document",
                             "--actor", "author", "--evidence", proof)
        self.assertEqual(state["gate"]["authority"], "reviewer")

    def test_answered_dispatchable_compiler_requests_are_reusable(self):
        import importlib.util
        self.start()
        spec = importlib.util.spec_from_file_location("delivery_compiler_fixture", ROOT / "pack/scripts/prompt-compile.py")
        assert spec is not None and spec.loader is not None
        engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine)
        original = engine.find_entry(str(self.audit), self.compiled_id, "compilation")
        for answer in (None, "", "   ", "unanswered", [], {"approval": True}, "Use the existing feature boundary"):
            with self.subTest(answer=answer):
                entry = json.loads(json.dumps(original))
                entry.pop("id", None)
                entry["compiled"]["decision_requests"] = [{"id": "DR-1", "assumption": "#1",
                    "question": "Which boundary?", "default": "none", "answer": answer}]
                # Producer fixture: already dispatchable. Native finish's legacy blanket
                # false for any requests is separately an inherited compiler limitation.
                compiled_id = engine.append_compilation_entry(str(self.audit), entry)
                argv = ("start", "--task", "answered", "--facts", self.facts(),
                        "--audit-root", self.audit, "--compiled-id", compiled_id)
                if isinstance(answer, str) and answer == "Use the existing feature boundary":
                    self.assertEqual(self.run_cli(*argv)["next"], "implement")
                else:
                    self.assertIn("contract refused: unresolved compiler decisions", self.run_cli(*argv, ok=False).stderr)

    def test_permission_and_release_pauses_preserve_current_stage(self):
        self.start()
        for kind in ("permission", "release", "decision"):
            paused = self.run_cli("pause", "--task", "demo", "--kind", kind,
                                  "--authority", "human", "--question", "Approve scoped action?")
            self.assertEqual(paused["next"], "implement")
            self.assertEqual(self.run_cli("status", "--task", "demo")["gate"], paused["gate"])
            resumed = self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(paused))
            self.assertIsNone(resumed["gate"])
            self.assertEqual(resumed["completed"], [])

    def test_genuine_t0_code_refactor_reaches_self_check_without_automatic_review(self):
        app = self.repo / "app.py"
        app.write_text("def identity(value):\n    return value\n", encoding="utf-8")
        self.start()
        app.write_text("def identity(item):\n    return item\n", encoding="utf-8")
        result = subprocess.run([sys.executable, "-c", "from app import identity; assert identity(7) == 7"],
                                cwd=self.repo, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        proof = self.write("refactor-proof.json", {"command": "from app import identity; assert identity(7) == 7",
                                                  "exit": result.returncode})
        ready = self.run_cli("complete", "--task", "demo", "--stage", "implement",
                             "--actor", "author", "--evidence", proof)
        self.assertEqual(ready["tier"], "T0")
        self.assertEqual(ready["next"], "verify")
        self.assertIsNone(ready["gate"], "genuine T0 code has the same proportional self-check as T0 docs")
        paused = self.run_cli("pause", "--task", "demo", "--kind", "hard-veto", "--authority", "reviewer",
                              "--question", "Clear an actual applicable veto?", "--actor", "author", "--evidence", proof)
        self.assertIn("author cannot clear", self.run_cli("resume", "--task", "demo", "--receipt",
                      self.receipt(paused, actor="author", source="reviewer-report"), ok=False).stderr)
        cleared = self.run_cli("resume", "--task", "demo", "--receipt",
                               self.receipt(paused, actor="reviewer", source="reviewer-report"))
        self.assertEqual(cleared["next"], "verify")

    def test_outcome_closure_requires_independent_review_and_original_criteria_evidence(self):
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("proof.json", {"real_path": "feature exercised"})
        reviewed = self.run_cli("complete", "--task", "demo", "--stage", "implement",
                                "--actor", "author", "--evidence", proof)
        self.assertEqual(reviewed["gate"]["kind"], "hard-veto")
        self.assertIn("decision refused:", self.run_cli("resume", "--task", "demo",
                      "--receipt", self.receipt(reviewed, actor="author", source="reviewer-report"), ok=False).stderr)
        ready = self.run_cli("resume", "--task", "demo", "--receipt",
                             self.receipt(reviewed, actor="independent-reviewer", source="reviewer-report"))
        self.assertEqual(ready["next"], "verify")
        self.assertIn("closure refused:", self.run_cli("complete", "--task", "demo", "--stage", "verify",
                      "--actor", "author", "--evidence", proof, ok=False).stderr)
        closure = {"criteria": [{"criterion": "feature works", "observed": "actual feature path passed",
                                "evidence": [str(proof)]}], "changes": ["feature"], "tests": ["real path"],
                   "skips": [], "limits": [], "remaining_gates": []}
        file = self.write("closure.json", {**closure, "criteria": []})
        self.assertIn("closure refused:", self.run_cli("complete", "--task", "demo", "--stage", "verify",
                      "--actor", "author", "--evidence", proof, "--closure", file, ok=False).stderr)
        file = self.write("closure.json", closure)
        closed = self.run_cli("complete", "--task", "demo", "--stage", "verify", "--actor", "author",
                              "--evidence", proof, "--closure", file)
        self.assertIsNone(closed["next"])
        self.assertEqual(closed["closure"], closure)
        self.assertIsNone(self.run_cli("status", "--task", "demo")["next"])

    def test_plain_project_pauses_and_resumes_without_git_or_docs_bootstrap(self):
        shutil.rmtree(self.repo / ".git")
        self.state_root = self.repo / ".delivery-state"
        (self.repo / "app.py").write_text("# existing plain project\n", encoding="utf-8")
        started = self.start()
        self.assertEqual(started["identity"]["root"], str(self.repo.resolve()))
        paused = self.run_cli("pause", "--task", "demo", "--kind", "permission", "--authority", "human",
                              "--question", "Run the scoped test?")
        receipt = self.receipt(paused)
        local_receipt = self.state_root / "approval.json"
        local_receipt.write_bytes(receipt.read_bytes())
        resumed = self.run_cli("resume", "--task", "demo", "--receipt", local_receipt)
        self.assertEqual(resumed["next"], "implement")
        self.assertEqual(resumed["completed"], [])
        self.assertIsNone(self.run_cli("status", "--task", "demo")["gate"])
        self.assertFalse((self.repo / ".git").exists())
        self.assertFalse((self.repo / "docs").exists())
        (self.repo / "app.py").write_text("# unexpected drift\n", encoding="utf-8")
        self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_plain_directory_link_drift_is_not_silently_ignored(self):
        shutil.rmtree(self.repo / ".git")
        self.state_root = Path(self.tmp.name) / "state"
        a = Path(self.tmp.name) / "dependency-a"
        b = Path(self.tmp.name) / "dependency-b"
        a.mkdir()
        b.mkdir()
        link = self.repo / "dependency"
        link.symlink_to(a, target_is_directory=True)
        self.start()
        link.unlink()
        link.symlink_to(b, target_is_directory=True)
        self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_plain_default_state_home_and_project_identity_binding(self):
        import hashlib
        shutil.rmtree(self.repo / ".git")
        home = Path(self.tmp.name) / "state-home"
        self.cli_env = {**os.environ, "XDG_STATE_HOME": str(home)}
        started = self.start()
        self.assertEqual(started["local_area"], str(home / "ai-forward/delivery"))
        paused = self.run_cli("pause", "--task", "demo", "--kind", "decision", "--authority", "human",
                              "--question", "Approve?")
        self.assertIsNone(self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(paused))["gate"])
        other = Path(self.tmp.name) / "other-project"
        other.mkdir()
        other_identity = {"root": str(other.resolve()), "kind": "plain"}
        key = hashlib.sha256(json.dumps(other_identity, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        copied = home / "ai-forward/delivery" / key / "demo.json"
        copied.parent.mkdir(parents=True)
        original = next((home / "ai-forward/delivery").glob("*/demo.json"))
        copied.write_bytes(original.read_bytes())
        self.assertIn("identity drift:", self.run_cli("status", "--task", "demo", "--repo", other, ok=False).stderr)
        self.assertFalse((self.repo / ".git").exists())
        self.assertFalse((self.repo / "docs").exists())

    def test_git_subdirectory_uses_root_fingerprint_and_ignored_input_registration(self):
        (self.repo / ".gitignore").write_text("ignored.txt\ncache/\n", encoding="utf-8")
        ignored = self.repo / "ignored.txt"
        ignored.write_text("load-bearing input", encoding="utf-8")
        sub = self.repo / "src"
        sub.mkdir()
        (self.repo / "app.py").write_text("# root product\n", encoding="utf-8")
        self.repo = sub
        self.start()
        started = self.run_cli("start", "--task", "registered", "--facts", self.facts(), "--input", ignored,
                               "--audit-root", self.audit, "--compiled-id", self.compiled_id)
        self.assertEqual(started["identity"]["root"], str(sub.parent.resolve()))
        cache = sub.parent / "cache"
        cache.mkdir()
        (cache / "transient.log").write_text("unrelated runtime output", encoding="utf-8")
        self.assertEqual(self.run_cli("status", "--task", "registered")["next"], "implement")
        ignored.write_text("changed load-bearing input", encoding="utf-8")
        self.assertIn("input drift:", self.run_cli("status", "--task", "registered", ok=False).stderr)

    def test_checkpoint_mutation_cannot_drop_evidence_or_change_routes(self):
        self.start()
        checkpoint = self.repo / ".git/ai-forward/delivery/demo.json"
        data = json.loads(checkpoint.read_text(encoding="utf-8"))
        data["stages"] = ["verify"]
        checkpoint.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("checkpoint refused:", self.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_invalid_actor_and_consent_authority_are_fail_closed(self):
        self.start()
        proof = self.write("proof.json", {"result": "observed"})
        self.assertIn("stage refused:", self.run_cli("complete", "--task", "demo", "--stage", "implement",
                      "--actor", " ", "--evidence", proof, ok=False).stderr)
        self.assertIn("gate refused:", self.run_cli("pause", "--task", "demo", "--kind", "hard-veto",
                      "--authority", "human", "--question", "Clear author veto", ok=False).stderr)
        self.assertIn("gate refused:", self.run_cli("pause", "--task", "demo", "--kind", "permission",
                      "--authority", "reviewer", "--question", "Grant tool permission", ok=False).stderr)

    def test_known_design_is_reused_and_contract_tier_cannot_be_lowered(self):
        facts = self.facts(risks=["data"], design_ready=True)
        self.assertEqual(self.run_cli("route", "--facts", facts)["stages"], ["implement", "verify"])
        status = self.start(contract_tier="T2", design_ready=True)
        self.assertEqual(status["tier"], "T2")

    def test_resume_rejects_workspace_branch_and_contract_drift(self):
        self.start()
        subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/other"], cwd=self.repo, check=True)
        self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_concurrent_checkpoint_writer_is_refused_without_overwrite(self):
        self.start()
        lock = self.repo / ".git/ai-forward/delivery/demo.lock"
        lock.write_text("active writer", encoding="utf-8")
        self.assertIn("checkpoint busy:", self.run_cli("pause", "--task", "demo", "--kind", "decision",
                      "--authority", "human", "--question", "Approve?", ok=False).stderr)
        self.assertIsNone(self.run_cli("status", "--task", "demo")["gate"])
        self.assertTrue(lock.exists())

    def test_empty_native_entrypoint_asks_for_outcome_before_any_work(self):
        skill = (ROOT / "pack/commands/deliver/SKILL.md").read_text(encoding="utf-8")
        adapter = (ROOT / "pack/adapters/copilot/prompts/deliver.prompt.md").read_text(encoding="utf-8")
        for text in (skill, adapter):
            self.assertIn("What outcome would you like me to deliver?", text)
            self.assertIn("no task", text.lower())
        self.assertLess(skill.index("What outcome would you like me to deliver?"), skill.index("## Ground once"))

    def test_delivery_references_match_proportional_review_and_active_author_interface(self):
        skill = (ROOT / "pack/commands/deliver/SKILL.md").read_text(encoding="utf-8")
        routing = (ROOT / "pack/commands/deliver/reference/routing.md").read_text(encoding="utf-8")
        checkpoints = (ROOT / "pack/commands/deliver/reference/checkpoints.md").read_text(encoding="utf-8")
        adapter = (ROOT / "pack/adapters/copilot/prompts/deliver.prompt.md").read_text(encoding="utf-8")
        self.assertIn("Genuinely T0 code", skill)
        self.assertIn("T1/T2", checkpoints)
        self.assertIn("[--actor <actual-stage-author> ...]", checkpoints)
        self.assertIn("version 2", checkpoints)
        self.assertIn("partial-work authors", checkpoints)
        self.assertIn("LF-normalized", checkpoints)
        self.assertIn("load-bearing architecture", routing)
        self.assertIn("inherent concurrency", routing)
        self.assertIn("actual stage authors", adapter)

    def test_entrypoint_is_installable_with_loadable_progressive_references(self):
        import importlib.util
        skill_dir = ROOT / "pack/commands/deliver"
        self.assertTrue((skill_dir / "SKILL.md").is_file(), "delivery entrypoint missing")
        spec = importlib.util.spec_from_file_location("delivery_skill_contracts", ROOT / "pack/scripts/verify-skill-contracts.py")
        assert spec is not None and spec.loader is not None
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        refs = list((skill_dir / "reference").glob("*.md"))
        self.assertEqual(checker.check_skill("deliver", text, [p.read_text(encoding="utf-8") for p in refs]), [])
        for path in ("reference/routing.md", "reference/checkpoints.md"):
            self.assertTrue((skill_dir / path).is_file())
            self.assertIn(path, text)
        adapter = ROOT / "pack/adapters/copilot/prompts/deliver.prompt.md"
        self.assertTrue(adapter.is_file())
        self.assertIn(".claude/skills/deliver/SKILL.md", adapter.read_text(encoding="utf-8"))

    FEATURE_EVAL_CORRECT_APP = (
        "def clamp(value, low, high):\n"
        "    if low > high:\n"
        "        raise ValueError('inverted bounds')\n"
        "    return max(low, min(value, high))\n")

    def run_feature_eval(self, *, setup=False, check=True):
        case = ROOT / "pack/evals/cases/deliver-feature-01.json"
        self.assertTrue(case.is_file(), "delivery behavior eval missing")
        evaluator = ROOT / "pack/evals/run-evals.py"
        argv = [sys.executable, str(evaluator), "--case", str(case), "--workspace", str(self.repo)]
        if setup:
            argv.append("--setup")
        if check:
            argv.append("--check")
        return subprocess.run(argv, text=True, encoding="utf-8", capture_output=True)

    def test_feature_eval_oracle_rejects_stub_and_checks_boundaries(self):
        self.assertNotEqual(self.run_feature_eval(setup=True).returncode, 0)
        stub = (self.repo / "app.py").read_bytes()
        verifier = self.repo / "verify_clamp.py"
        original_verifier = verifier.read_bytes()
        verifier.write_text("# verifier disabled, app remains the unchanged stub\n", encoding="utf-8")
        self.assertEqual((self.repo / "app.py").read_bytes(), stub)
        tampered = self.run_feature_eval()
        self.assertNotEqual(tampered.returncode, 0, tampered.stdout + tampered.stderr)
        self.assertIn("verifier identity changed", tampered.stdout + tampered.stderr)
        verifier.write_bytes(original_verifier)
        (self.repo / "app.py").write_text(self.FEATURE_EVAL_CORRECT_APP, encoding="utf-8")
        result = self.run_feature_eval()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_feature_eval_rejects_successful_exit_during_import(self):
        seeded = self.run_feature_eval(setup=True, check=False)
        self.assertEqual(seeded.returncode, 0, seeded.stdout + seeded.stderr)
        verifier = self.repo / "verify_clamp.py"
        original_verifier = verifier.read_bytes()
        (self.repo / "app.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        result = self.run_feature_eval()
        self.assertEqual(verifier.read_bytes(), original_verifier)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SystemExit", result.stdout + result.stderr)

    def test_feature_eval_rejects_import_time_verifier_mutation(self):
        seeded = self.run_feature_eval(setup=True, check=False)
        self.assertEqual(seeded.returncode, 0, seeded.stdout + seeded.stderr)
        verifier = self.repo / "verify_clamp.py"
        original_verifier = verifier.read_bytes()
        (self.repo / "app.py").write_text(
            "from pathlib import Path\n"
            "Path('verify_clamp.py').write_text('# disabled at import time\\n', encoding='utf-8')\n"
            + self.FEATURE_EVAL_CORRECT_APP, encoding="utf-8")
        self.assertEqual(verifier.read_bytes(), original_verifier)
        result = self.run_feature_eval()
        self.assertEqual(verifier.read_text(encoding="utf-8"), "# disabled at import time\n")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("verifier identity changed", result.stdout + result.stderr)

    def test_feature_eval_rejects_correct_app_with_pre_disabled_verifier(self):
        seeded = self.run_feature_eval(setup=True, check=False)
        self.assertEqual(seeded.returncode, 0, seeded.stdout + seeded.stderr)
        (self.repo / "app.py").write_text(self.FEATURE_EVAL_CORRECT_APP, encoding="utf-8")
        verifier = self.repo / "verify_clamp.py"
        verifier.write_text("# verifier disabled\n", encoding="utf-8")
        result = self.run_feature_eval()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("verifier identity changed", result.stdout + result.stderr)
        self.assertEqual(verifier.read_text(encoding="utf-8"), "# verifier disabled\n")

    def test_feature_eval_accepts_correct_app_with_intact_lf_or_crlf_verifier(self):
        for newline in (b"\n", b"\r\n"):
            with self.subTest(newline=newline):
                seeded = self.run_feature_eval(setup=True, check=False)
                self.assertEqual(seeded.returncode, 0, seeded.stdout + seeded.stderr)
                verifier = self.repo / "verify_clamp.py"
                original_verifier = verifier.read_bytes().replace(b"\r\n", b"\n")
                verifier.write_bytes(original_verifier.replace(b"\n", newline))
                (self.repo / "app.py").write_bytes(self.FEATURE_EVAL_CORRECT_APP.encode("utf-8").replace(b"\n", newline))
                expected_verifier = verifier.read_bytes()
                result = self.run_feature_eval()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(verifier.read_bytes(), expected_verifier)

    def test_feature_eval_requires_each_boundary_check_to_finish(self):
        for call in range(1, 10):  # Eight value checks, then the inverted-bounds check.
            for fault in ("raise SystemExit(0)", "return None"):
                with self.subTest(call=call, fault=fault):
                    shutil.rmtree(self.repo / "__pycache__", ignore_errors=True)
                    seeded = self.run_feature_eval(setup=True, check=False)
                    self.assertEqual(seeded.returncode, 0, seeded.stdout + seeded.stderr)
                    verifier = self.repo / "verify_clamp.py"
                    original_verifier = verifier.read_bytes()
                    (self.repo / "app.py").write_text(
                        "calls = 0\n"
                        "def clamp(value, low, high):\n"
                        "    global calls\n"
                        "    calls += 1\n"
                        f"    if calls == {call}:\n"
                        f"        {fault}\n"
                        "    if low > high:\n"
                        "        raise ValueError('inverted bounds')\n"
                        "    return max(low, min(value, high))\n", encoding="utf-8")
                    result = self.run_feature_eval()
                    self.assertEqual(verifier.read_bytes(), original_verifier)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("SystemExit" if fault.startswith("raise") else "AssertionError",
                                  result.stdout + result.stderr)

    def test_malformed_receipt_types_and_missing_proof_have_stable_refusals(self):
        self.start()
        paused = self.run_cli("pause", "--task", "demo", "--kind", "decision", "--authority", "human",
                              "--question", "Approve this scoped action?")
        valid = json.loads(self.receipt(paused).read_text(encoding="utf-8"))
        for overrides in ({"actor": []}, {"actor": {"name": "operator"}}, {"actor": 42},
                          {"evidence": []}, {"evidence": None}, {"evidence": ""}):
            with self.subTest(overrides=overrides):
                result = self.run_cli("resume", "--task", "demo", "--receipt",
                                      self.write("malformed-receipt.json", {**valid, **overrides}), ok=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn("decision refused:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(self.run_cli("status", "--task", "demo")["gate"], paused["gate"])
        del valid["evidence"]
        result = self.run_cli("resume", "--task", "demo", "--receipt", self.write("missing-receipt.json", valid), ok=False)
        self.assertIn("decision refused:", result.stderr)

    def test_malformed_closure_rows_and_empty_proof_have_stable_refusals(self):
        self.start(kind="docs")
        proof = self.write("proof.json", {"observed": "rendered"})
        self.run_cli("complete", "--task", "demo", "--stage", "document", "--actor", "author", "--evidence", proof)
        base = {"criteria": [], "changes": [], "tests": [], "skips": [], "limits": [], "remaining_gates": []}
        for row in (None, 12, "feature works", {"criterion": "feature works", "observed": "rendered", "evidence": "not-a-list"},
                    {"criterion": "feature works", "observed": "rendered", "evidence": [None]},
                    {"criterion": "feature works", "observed": "rendered", "evidence": [""]}):
            with self.subTest(row=row):
                closure = self.write("bad-closure.json", {**base, "criteria": [row]})
                failed = self.run_cli("complete", "--task", "demo", "--stage", "verify", "--actor", "author",
                                      "--evidence", proof, "--closure", closure, ok=False)
                self.assertEqual(failed.returncode, 1)
                self.assertIn("closure refused:", failed.stderr)
                self.assertNotIn("Traceback", failed.stderr)
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "verify")

    def test_unsafe_state_root_cannot_hide_project_or_follow_symlink(self):
        self.start()
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        link = Path(self.tmp.name) / "linked-state"
        link.symlink_to(outside, target_is_directory=True)
        for root in (self.repo, self.repo.parent, link):
            with self.subTest(root=root):
                failed = self.run_cli("start", "--task", "unsafe", "--facts", self.facts(),
                                      "--audit-root", self.audit, "--compiled-id", self.compiled_id,
                                      "--state-root", root, ok=False)
                self.assertIn("state path refused:", failed.stderr)
                self.assertNotIn("Traceback", failed.stderr)
        self.assertEqual(list(outside.iterdir()), [])

    def test_structurally_malformed_checkpoints_fail_with_stable_error(self):
        import hashlib
        self.start()
        checkpoint = self.repo / ".git/ai-forward/delivery/demo.json"
        original = json.loads(checkpoint.read_text(encoding="utf-8"))
        for changes in ({"completed": [None]}, {"completed": "done"}, {"inputs": [None]},
                        {"gate": {"authority": []}}, {"stages": []}, {"decisions": [12]}, {"facts": None}):
            with self.subTest(changes=changes):
                broken = {**original, **changes}
                broken["integrity"] = hashlib.sha256(json.dumps({k: v for k, v in broken.items() if k != "integrity"},
                    sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
                checkpoint.write_text(json.dumps(broken), encoding="utf-8")
                failed = self.run_cli("status", "--task", "demo", ok=False)
                self.assertEqual(failed.returncode, 1)
                self.assertIn("checkpoint refused:", failed.stderr)
                self.assertNotIn("Traceback", failed.stderr)
        checkpoint.write_text(json.dumps(original), encoding="utf-8")
        self.assertEqual(self.run_cli("status", "--task", "demo")["next"], "implement")

    def test_malformed_record_paths_fail_with_stable_checkpoint_refusal(self):
        import hashlib
        self.start()
        checkpoint = self.repo / ".git/ai-forward/delivery/demo.json"
        original = json.loads(checkpoint.read_text(encoding="utf-8"))
        for record in (None, {}, {"path": [], "sha256": "invalid"}, {"path": "", "sha256": "invalid"}):
            with self.subTest(record=record):
                broken = {**original, "gate": {"id": "gate", "binding": "binding", "kind": "decision",
                    "authority": "human", "question": "Approve?", "stage": "implement", "evidence": [record]}}
                broken["integrity"] = hashlib.sha256(json.dumps({k: v for k, v in broken.items() if k != "integrity"},
                    sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
                checkpoint.write_text(json.dumps(broken), encoding="utf-8")
                failed = self.run_cli("status", "--task", "demo", ok=False)
                self.assertIn("checkpoint refused:", failed.stderr)
                self.assertNotIn("Traceback", failed.stderr)

    def test_whitespace_only_proof_is_not_stage_evidence(self):
        self.start()
        proof = Path(self.tmp.name) / "blank-proof.log"
        proof.write_text(" \n\t\r\n", encoding="utf-8")
        failed = self.run_cli("complete", "--task", "demo", "--stage", "implement", "--actor", "author",
                              "--evidence", proof, ok=False)
        self.assertIn("evidence missing:", failed.stderr)
        self.assertEqual(self.run_cli("status", "--task", "demo")["completed"], [])

    def test_negative_receipts_keep_task_paused(self):
        self.start()
        paused = self.run_cli("pause", "--task", "demo", "--kind", "decision",
                              "--authority", "human", "--question", "Approve?")
        valid = json.loads(self.receipt(paused).read_text(encoding="utf-8"))
        for field, value in (("task", "other"), ("gate", "stale"), ("binding", "stale"),
                             ("authority", "reviewer"), ("decision", "denied"), ("actor", ""),
                             ("source", "transport-complete")):
            with self.subTest(field=field):
                bad = self.write("bad-receipt.json", {**valid, field: value})
                self.assertIn("decision refused:", self.run_cli("resume", "--task", "demo", "--receipt", bad, ok=False).stderr)
                self.assertEqual(self.run_cli("status", "--task", "demo")["gate"], paused["gate"])
        bad = self.write("missing-proof-receipt.json", {**valid, "evidence": str(self.repo / "absent")})
        self.assertIn("evidence missing:", self.run_cli("resume", "--task", "demo", "--receipt", bad, ok=False).stderr)

    def test_workspace_contract_and_input_drift_are_not_adopted_on_resume(self):
        self.start()
        (self.repo / "unexpected.py").write_text("change", encoding="utf-8")
        self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
        (self.repo / "unexpected.py").unlink()
        entries = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        entries[-1]["summary"] = "changed contract record"
        self.log.write_text("\n".join(json.dumps(row) for row in entries) + "\n", encoding="utf-8")
        self.assertIn("contract drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_missing_stage_evidence_and_duplicate_task_are_refused(self):
        self.start()
        empty = Path(self.tmp.name) / "empty.log"
        empty.write_text("", encoding="utf-8")
        self.assertIn("evidence missing:", self.run_cli("complete", "--task", "demo", "--stage", "implement",
                      "--actor", "author", "--evidence", empty, ok=False).stderr)
        self.assertEqual(self.run_cli("status", "--task", "demo")["completed"], [])
        self.assertIn("task exists:", self.run_cli("start", "--task", "demo", "--facts", self.facts(),
                      "--audit-root", self.audit, "--compiled-id", self.compiled_id, ok=False).stderr)
        self.assertIn("invalid task:", self.run_cli("status", "--task", "../other", ok=False).stderr)
        self.assertIn("contract refused:", self.run_cli("start", "--task", "other", "--facts", self.facts(),
                      "--audit-root", self.audit, "--compiled-id", "absent", ok=False).stderr)

    def test_delivery_stdio_guard_passes_current_portable_text_io_validator(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_text_io", ROOT / "pack/scripts/verify-portable-text-io.py")
        assert spec is not None and spec.loader is not None
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        self.assertEqual(validator.scan_source(SCRIPT.read_text(encoding="utf-8")), [])

    def test_utf8_checkpoint_output_survives_legacy_stdio(self):
        self.start()
        proof = self.write("café-proof.json", {"result": "observed"})
        env = dict(os.environ, PYTHONIOENCODING="ascii")
        result = subprocess.run([sys.executable, str(SCRIPT), "complete", "--task", "demo", "--stage", "implement",
                                 "--actor", "author", "--evidence", str(proof)], cwd=self.repo,
                                capture_output=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertIn("café-proof.json", result.stdout.decode("utf-8"))
        failed = subprocess.run([sys.executable, str(SCRIPT), "route", "--facts", str(self.repo / "café-absent.json")],
                                cwd=self.repo, env=env, capture_output=True)
        self.assertEqual(failed.returncode, 1)
        self.assertNotIn("Traceback", failed.stderr.decode("utf-8", "replace"))
        self.assertIn("café-absent.json", failed.stderr.decode("utf-8"))

    def test_pack_installer_places_loadable_skill_and_runnable_helper(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_install", ROOT / "pack/scripts/pack-apply.py")
        assert spec is not None and spec.loader is not None
        applier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(applier)
        install = applier.Applier(str(ROOT), str(self.repo), dry=False, install=True, baselines=False)
        install.skills()
        install.bundle()
        for host in (".claude", ".agents", ".grok"):
            for suffix in ("SKILL.md", "reference/routing.md", "reference/checkpoints.md"):
                self.assertEqual((self.repo / host / "skills/deliver" / suffix).read_bytes(),
                                 (ROOT / "pack/commands/deliver" / suffix).read_bytes())
        self.assertTrue((self.repo / ".github/prompts/deliver.prompt.md").is_file())
        result = subprocess.run([sys.executable, str(self.repo / "docs/ai-forward-pack/scripts/delivery.py"),
                                 "route", "--facts", str(self.facts())], cwd=self.repo,
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["stages"], ["implement", "verify"])

    def test_partial_checkpoint_requires_actual_author_before_adopting_work(self):
        self.start()
        partial = self.repo / "partial.py"
        partial.write_text("# actual in-progress work\n", encoding="utf-8")
        proof = self.write("partial-proof.json", {"actor": "author", "changes": ["partial.py"]})
        for kind, authority in (("permission", "human"), ("hard-veto", "reviewer")):
            with self.subTest(kind=kind):
                failed = self.run_cli("pause", "--task", "demo", "--kind", kind, "--authority", authority,
                                      "--question", "Resolve scoped gate?", "--evidence", proof, ok=False)
                self.assertIn("actual stage authors", failed.stderr)
        partial.unlink()
        self.assertIsNone(self.run_cli("status", "--task", "demo")["gate"])

    def test_midstage_hard_veto_rejects_all_actual_authors_in_fresh_process(self):
        self.start()
        (self.repo / "partial.py").write_text("# author-owned partial work\n", encoding="utf-8")
        proof = self.write("partial-veto.json", {"actors": ["author", "coauthor"], "verdict": "BLOCK"})
        paused = self.run_cli("pause", "--task", "demo", "--kind", "hard-veto", "--authority", "reviewer",
                              "--question", "Resolve actual veto on partial.py?", "--actor", "author",
                              "--actor", "coauthor", "--evidence", proof)
        self.assertEqual(paused["completed"], [])
        for actor in ("author", "coauthor"):
            with self.subTest(actor=actor):
                failed = self.run_cli("resume", "--task", "demo", "--receipt",
                                      self.receipt(paused, actor=actor, source="reviewer-report"), ok=False)
                self.assertIn("author cannot clear", failed.stderr)
                self.assertEqual(self.run_cli("status", "--task", "demo")["gate"], paused["gate"])
        self.assertEqual([row["actor"] for row in paused["partial"]], ["author", "coauthor"])
        import hashlib
        binding_inputs = {key: paused[key] for key in ("identity", "task", "contract", "snapshot", "completed", "partial")}
        expected = hashlib.sha256(json.dumps(binding_inputs, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        self.assertEqual(paused["gate"]["binding"], expected)
        resumed = self.run_cli("resume", "--task", "demo", "--receipt",
                               self.receipt(paused, actor="independent-reviewer", source="reviewer-report"))
        self.assertEqual(resumed["completed"], [])
        self.assertEqual(resumed["partial"], paused["partial"])
        self.assertEqual(resumed["next"], "implement")
        self.assertTrue((self.repo / "partial.py").is_file())

    def test_pre_author_checkpoint_schema_is_refused_without_inventing_identity(self):
        import hashlib
        self.start()
        checkpoint = self.repo / ".git/ai-forward/delivery/demo.json"
        original = json.loads(checkpoint.read_text(encoding="utf-8"))
        old = {**original, "version": 1}
        old.pop("partial", None)
        old["integrity"] = hashlib.sha256(json.dumps({k: v for k, v in old.items() if k != "integrity"},
                                                   sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        checkpoint.write_text(json.dumps(old), encoding="utf-8")
        failed = self.run_cli("status", "--task", "demo", ok=False)
        self.assertIn("unsupported checkpoint", failed.stderr)
        self.assertEqual(json.loads(checkpoint.read_text(encoding="utf-8")), old)

    def test_midstage_pause_retains_partial_work_without_claiming_completion(self):
        self.start()
        partial = self.repo / "partial.py"
        partial.write_text("# implementation in progress\n", encoding="utf-8")
        evidence = self.write("partial-evidence.json", {"changes": ["partial.py"], "tests": "not yet permitted"})
        paused = self.run_cli("pause", "--task", "demo", "--kind", "permission", "--authority", "human",
                              "--question", "Permit integration test?", "--actor", "author", "--evidence", evidence)
        self.assertEqual(paused["completed"], [])
        self.assertEqual(paused["next"], "implement")
        self.assertEqual(self.run_cli("status", "--task", "demo")["gate"], paused["gate"])
        resumed = self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(paused))
        self.assertEqual(resumed["completed"], [])
        self.assertTrue(partial.is_file())
        evidence.unlink()
        self.assertIn("evidence drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_checkpoint_survives_fresh_process_and_skips_completed_work(self):
        started = self.start(questions=["requirements"])
        self.assertEqual(started["next"], "specify")
        self.assertEqual(started["raw"].splitlines()[0], "Goal: Add a small feature")
        evidence = self.write("spec-proof.json", {"result": "observed"})
        completed = self.run_cli("complete", "--task", "demo", "--stage", "specify",
                                 "--actor", "author", "--evidence", evidence)
        self.assertEqual(completed["next"], "implement")
        recovered = self.run_cli("status", "--task", "demo")
        self.assertEqual(recovered["completed"][0]["stage"], "specify")
        self.assertEqual(recovered["next"], "implement")
        self.assertFalse((self.repo / "docs").exists())
        self.assertFalse((self.repo / ".agents").exists())
        evidence.unlink()
        self.assertIn("evidence drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_load_bearing_architecture_raises_tier_and_requires_missing_design(self):
        for tier in ("T0", "T1", "T2"):
            with self.subTest(tier=tier):
                routed = self.run_cli("route", "--facts", self.facts(questions=["architecture"], tier=tier))
                self.assertEqual(routed["tier"], "T2")
                self.assertEqual(routed["stages"], ["define-architecture", "design-slice", "implement", "verify"])
                reused = self.run_cli("route", "--facts",
                                      self.facts(questions=["architecture"], tier=tier, design_ready=True))
                self.assertEqual(reused["tier"], "T2")
                self.assertEqual(reused["stages"], ["define-architecture", "implement", "verify"])
        started = self.start(questions=["architecture"], contract_tier="T0")
        self.assertEqual(started["tier"], "T2")
        proof = self.write("architecture-proof.json", {"reviewed_exit": "architecture skill exit evidence"})
        progressed = self.run_cli("complete", "--task", "demo", "--stage", "define-architecture",
                                  "--actor", "architect", "--evidence", proof)
        self.assertEqual(progressed["next"], "design-slice")
        self.assertIsNone(progressed["gate"], "selected skill still owns its reviewed exit criteria")

    def test_every_high_risk_trigger_and_migration_routes_at_t2(self):
        for risk in ("security", "identity", "data", "contracts", "money", "concurrency"):
            for tier in ("T0", "T1", "T2"):
                with self.subTest(risk=risk, tier=tier):
                    result = self.run_cli("route", "--facts", self.facts(risks=[risk], tier=tier))
                    self.assertEqual(result["tier"], "T2")
                    self.assertIn("design-slice", result["stages"])
        result = self.run_cli("route", "--facts", self.facts(kind="migration"))
        self.assertEqual(result["tier"], "T2")
        self.assertEqual(result["stages"], ["design-slice", "migrate", "verify"])

    def test_coordination_imposes_inherent_concurrency_floor_and_missing_design(self):
        for kind in ("feature", "defect", "migration", "docs"):
            for tier in ("T0", "T1", "T2"):
                with self.subTest(kind=kind, tier=tier):
                    routed = self.run_cli("route", "--facts", self.facts(kind=kind, tier=tier, coordination=True))
                    self.assertEqual(routed["tier"], "T2")
                    self.assertIn("design-slice", routed["stages"])
        started = self.start(coordination=True, contract_tier="T0")
        self.assertEqual(started["tier"], "T2")
        self.assertEqual(started["stages"],
                         ["design-slice", "prepare-for-coordination", "execute-with-coordination", "verify"])

    def test_coordination_keeps_preparation_and_task_specific_obligations(self):
        for kind, expected in (
            ("feature", ["prepare-for-coordination", "execute-with-coordination", "verify"]),
            ("defect", ["investigate", "repair-review", "prepare-for-coordination", "execute-with-coordination", "verify"]),
            ("migration", ["migration-characterization", "prepare-for-coordination", "execute-with-coordination", "verify"]),
        ):
            with self.subTest(kind=kind):
                result = self.run_cli("route", "--facts", self.facts(kind=kind, coordination=True, design_ready=True))
                self.assertEqual(result["stages"], expected)
                self.assertNotIn("implement", result["stages"])
                self.assertNotIn("migrate", result["stages"])

    def test_malformed_fact_members_have_stable_schema_errors(self):
        for facts in ({"risks": [{}]}, {"risks": [[]]}, {"questions": [None]}, {"kind": []}):
            with self.subTest(facts=facts):
                failed = self.run_cli("route", "--facts", self.facts(**facts), ok=False)
                self.assertIn("invalid facts:", failed.stderr)
                self.assertNotIn("Traceback", failed.stderr)

    def test_route_rejects_invalid_inputs_and_raises_risk_floor(self):
        bad = [{"kind": "unknown"}, {"tier": "T9"}, {"questions": ["invent"]},
               {"coordination": "yes"}, {"risks": ["whatever"]}, {"extra": True}]
        for overrides in bad:
            with self.subTest(overrides=overrides):
                result = self.run_cli("route", "--facts", self.facts(**overrides), ok=False)
                self.assertIn("invalid facts:", result.stderr)
        result = self.run_cli("route", "--facts", self.facts(risks=["data"]))
        self.assertEqual(result["tier"], "T2")
        self.assertEqual(result["stages"], ["design-slice", "implement", "verify"])

    def test_route_selects_only_unresolved_applicable_skills(self):
        facts = self.facts()
        self.assertEqual(self.run_cli("route", "--facts", facts)["stages"], ["implement", "verify"])
        cases = [
            ({"kind": "docs"}, ["document", "verify"]),
            ({"kind": "defect"}, ["investigate", "repair-review", "implement", "verify"]),
            ({"kind": "migration"}, ["design-slice", "migrate", "verify"]),
            ({"questions": ["requirements", "architecture", "design"], "ui": True},
             ["specify", "define-architecture", "design-slice", "ui-design", "implement", "verify"]),
            ({"coordination": True}, ["design-slice", "prepare-for-coordination", "execute-with-coordination", "verify"]),
        ]
        for overrides, expected in cases:
            with self.subTest(overrides=overrides):
                self.assertEqual(self.run_cli("route", "--facts", self.facts(**overrides))["stages"], expected)
        self.assertEqual(list(self.repo.iterdir()), [self.repo / ".git"])


if __name__ == "__main__":
    unittest.main()
