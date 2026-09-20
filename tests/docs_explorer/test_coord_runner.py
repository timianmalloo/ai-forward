"""AC1–10: deployed entry point, real git/ref/worktrees, offline wire subprocesses."""
import hashlib
import json
import os
import signal
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "pack/scripts"
PEER = Path(__file__).parent / "fixtures/coord_runner_peer.py"
CAPS = dict.fromkeys(("worktree_isolation", "instructions", "hooks", "permissions"), "observed-only")


@unittest.skipUnless(os.name == "posix", "initial interactive runner is a POSIX pilot")
class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Runner test")
        self.scripts = self.repo / "docs/ai-forward-pack/scripts"
        shutil.copytree(SOURCE, self.scripts)
        (self.repo / "AGENTS.md").write_text("Test instructions\n", encoding="utf-8")
        shutil.copyfile(PEER, self.repo / "peer.py")
        raw = "Write receipt.json and stop."
        compiled = {"schema": "compiled-prompt/1", "mode": "pass-through",
            "raw_id": "raw-1", "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "goal_state": dict.fromkeys(("goal", "done_when", "not_in_scope", "tier",
                "fan_out_cap", "context_ceiling", "main_line_budget"), "fixture"),
            "decision_requests": [], "assumptions": [], "dispatchable": True,
            "harness": "codex", "template": "fixture", "template_version": 1,
            "clauses": [], "references": [], "graph_neighbours": [], "contract_slot": {}, "provenance": {}}
        self.entries = [{"id": "raw-1", "kind": "prompt", "prompt": raw},
            {"id": "compiled-1", "kind": "compilation", "dispatchable": True,
             "compiled": compiled, "prompt": raw}]
        self.audit = self.repo / "docs/audit/audit-log.jsonl"
        self.audit.parent.mkdir(parents=True)
        self.write_audit()
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        self.env = dict(os.environ, AGENT_SESSION="owner", AGENT_HOST="codex", AGENT_WI="parent")
        self.env.pop("COORD_ROOT", None)
        self.env.pop("AGENT_NAME", None)
        self.contract = {"schema": "coord-run/1", "run_id": "test-run", "owner": "owner",
            "parallelism": 2, "workers": [self.worker("worker-1", "work-one")]}
        self.contract_path = self.repo / "contract.json"

    def git(self, *args, cwd=None, check=True):
        return subprocess.run(["git", *args], cwd=cwd or self.repo, capture_output=True,
            text=True, encoding="utf-8", check=check)

    def write_audit(self):
        self.audit.write_text("".join(json.dumps(e) + "\n" for e in self.entries), encoding="utf-8")

    def worker(self, session, branch, mode="ok"):
        return {"session": session, "branch": branch, "harness": "codex", "transport": "acp",
            "argv": [sys.executable, str(self.repo / "peer.py"), mode], "prompts": ["compiled-1"],
            "deadline_seconds": 4, "output_limit": 65536, "fallback": "Use the retained manual brief",
            "required_capabilities": CAPS, "binding_files": ["AGENTS.md", str(self.repo / "peer.py")],
            "evidence": [{"kind": "file", "path": "receipt.json", "max_bytes": 4096}]}

    def cli(self, *args, expected=0, cwd=None):
        result = subprocess.run([sys.executable, str(self.scripts / "coord-runner.py"), *args],
            cwd=cwd or self.repo, env=self.env, capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines() if line.strip()][-1]

    def prepare(self, cwd=None):
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
        return self.cli("prepare", "--contract", str(self.contract_path), cwd=cwd)

    def pin(self, owner="owner", host="codex"):
        result = subprocess.run([sys.executable, str(self.scripts / "coord-core.py"),
            "leader", "pin", owner, "--host", host], cwd=self.repo, env=self.env,
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def qualify(self):
        current = self.cli("fingerprint", "--run", "test-run")
        q = {"schema": "coord-qualification/1", "workers": {s: {
            "fingerprint": fp, "version": "offline-peer-1", "evidence": "Offline protocol fixture only",
            "effective_policy": "Offline peer writes its fixed receipt only", "trust": "Disposable fixture",
            "capabilities": CAPS} for s, fp in current["fingerprints"].items()}}
        path = self.repo / "qualification.json"
        path.write_text(json.dumps(q), encoding="utf-8")
        return path

    def run_prepared(self, expected=0):
        q = self.qualify()
        self.pin()
        return self.cli("run", "--run", "test-run", "--qualification", str(q), expected=expected)

    def test_invalid_contract_never_creates_worker(self):
        for change in ({"deadline_seconds": 0}, {"output_limit": -1}, {"fallback": ""},
                       {"evidence": [{"kind": "file", "path": "../escape", "max_bytes": 10}]}):
            with self.subTest(change=change):
                worker = self.worker("worker-1", "work-one")
                worker.update(change)
                self.contract["workers"] = [worker]
                self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
                self.cli("prepare", "--contract", str(self.contract_path), expected=2)
                self.assertFalse((self.repo.parent / "repo-work-one").exists())

    def test_duplicate_or_parent_identity_refuses(self):
        self.contract["workers"].append(self.worker("worker-1", "work-two"))
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
        self.cli("prepare", "--contract", str(self.contract_path), expected=2)
        self.contract["workers"] = [self.worker("owner", "work-one")]
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
        self.cli("prepare", "--contract", str(self.contract_path), expected=2)

    def test_undispatchable_compilation_refuses(self):
        self.entries[1]["compiled"]["decision_requests"] = [{"id": "DR-1", "answer": None}]
        self.write_audit()
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
        self.cli("prepare", "--contract", str(self.contract_path), expected=2)

    def test_two_workers_repeated_turns_identity_and_no_raw_output(self):
        self.contract["workers"][0]["prompts"] *= 2
        self.contract["workers"].append(self.worker("worker-2", "work-two"))
        prepared = self.prepare()
        result = self.run_prepared()
        self.assertEqual(result["state"], "ready_for_review")
        for worker in prepared["workers"]:
            receipt = json.loads((Path(worker["worktree"]) / "receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["session"], worker["session"])
            self.assertNotEqual(receipt["wi"], "parent")
            self.assertEqual(receipt["host"], "codex")
            self.assertEqual(receipt["cwd"], worker["worktree"])
            self.assertEqual(receipt["turns"], 2 if worker["session"] == "worker-1" else 1)
        status = self.cli("status", "--run", "test-run")
        self.assertEqual(status["state"], "ready_for_review")
        self.assertNotIn("SECRET_DO_NOT_LOG", json.dumps(status))
        for log in (self.repo / ".agents/log").glob("*.jsonl"):
            self.assertNotIn("SECRET_DO_NOT_LOG", log.read_text(encoding="utf-8"))

    def test_transport_done_without_artifact_is_not_ready(self):
        self.contract["workers"][0]["argv"][-1] = "missing"
        self.prepare()
        result = self.run_prepared(expected=3)
        self.assertEqual(result["workers"][0]["state"], "evidence_incomplete")
        self.assertEqual(result["workers"][0]["transport"]["outcome"], "complete")

    def test_commit_evidence_requires_a_new_descendant(self):
        self.contract["workers"][0]["evidence"] = [{"kind": "commit"}]
        self.prepare()
        self.assertEqual(self.run_prepared(expected=3)["workers"][0]["state"], "evidence_incomplete")

    def test_commit_evidence_returns_actual_new_commit(self):
        self.contract["workers"][0]["evidence"] = [{"kind": "commit"}]
        self.contract["workers"][0]["argv"][-1] = "commit"
        prepared = self.prepare()
        result = self.run_prepared()
        actual = self.git("rev-parse", "HEAD", cwd=prepared["workers"][0]["worktree"]).stdout.strip()
        self.assertEqual(result["workers"][0]["receipts"][0]["commit"], actual)
        self.assertNotEqual(actual, prepared["base"])

    def test_prepared_manifest_cannot_be_rewritten(self):
        self.prepare()
        path = self.repo / ".git/coord-runs/test-run/manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["workers"][0]["prompt_texts"] = ["different admitted work"]
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(self.cli("fingerprint", "--run", "test-run", expected=2)["code"], "RUN-STORE")

    def test_configuration_drift_blocks_launch(self):
        prepared = self.prepare()
        q = self.qualify()
        self.pin()
        (Path(prepared["workers"][0]["worktree"]) / "AGENTS.md").write_text("changed", encoding="utf-8")
        result = self.cli("run", "--run", "test-run", "--qualification", str(q), expected=2)
        self.assertEqual(result["code"], "RUN-QUALIFICATION")
        self.assertFalse((Path(prepared["workers"][0]["worktree"]) / "receipt.json").exists())

    def test_absent_and_competing_leader_block(self):
        self.prepare()
        q = self.qualify()
        self.cli("run", "--run", "test-run", "--qualification", str(q), expected=2)
        self.pin("other", "claude")
        self.cli("run", "--run", "test-run", "--qualification", str(q), expected=2)

    def test_claude_owner_has_same_behavior(self):
        self.env["AGENT_HOST"] = "claude"
        self.prepare()
        q = self.qualify()
        self.pin(host="claude")
        result = self.cli("run", "--run", "test-run", "--qualification", str(q))
        self.assertEqual(result["state"], "ready_for_review")

    def test_duplicate_run_does_not_replay(self):
        prepared = self.prepare()
        self.run_prepared()
        q = self.qualify()
        self.cli("run", "--run", "test-run", "--qualification", str(q), expected=2)
        receipt = Path(prepared["workers"][0]["worktree"]) / "receipt.json"
        self.assertEqual(json.loads(receipt.read_text(encoding="utf-8"))["turns"], 1)

    def test_hang_is_bounded_and_status_is_failure(self):
        self.contract["workers"][0]["argv"][-1] = "hang"
        self.contract["workers"][0]["deadline_seconds"] = 1
        self.prepare()
        start = time.monotonic()
        result = self.run_prepared(expected=3)
        self.assertLess(time.monotonic() - start, 8)
        self.assertNotEqual(result["state"], "ready_for_review")

    def test_invoking_linked_head_is_base(self):
        linked = self.repo.parent / "initiator"
        self.git("worktree", "add", "-qb", "initiator", str(linked))
        (linked / "different.txt").write_text("specific base", encoding="utf-8")
        self.git("add", ".", cwd=linked)
        self.git("commit", "-qm", "different", cwd=linked)
        prepared = self.prepare(cwd=linked)
        self.assertEqual(prepared["base"], self.git("rev-parse", "HEAD", cwd=linked).stdout.strip())
        self.assertTrue((Path(prepared["workers"][0]["worktree"]) / "different.txt").exists())

    def test_symlink_evidence_never_satisfies_receipt(self):
        self.contract["workers"][0]["argv"][-1] = "missing"
        prepared = self.prepare()
        outside = self.repo / "unrelated.json"
        outside.write_text("not worker evidence", encoding="utf-8")
        (Path(prepared["workers"][0]["worktree"]) / "receipt.json").symlink_to(outside)
        result = self.run_prepared(expected=3)
        self.assertEqual(result["workers"][0]["state"], "evidence_incomplete")

    def running(self):
        prepared = self.prepare()
        q = self.qualify()
        self.pin()
        process = subprocess.Popen([sys.executable, str(self.scripts / "coord-runner.py"), "run",
            "--run", "test-run", "--qualification", str(q)], cwd=self.repo, env=self.env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        def cleanup():
            if process.poll() is None:
                process.terminate()
            process.communicate(timeout=8)
        self.addCleanup(cleanup)
        marker = Path(prepared["workers"][0]["worktree"]) / "prompt-started"
        until = time.monotonic() + 4
        while not marker.exists() and time.monotonic() < until and process.poll() is None:
            time.sleep(0.02)
        self.assertTrue(marker.exists(), "worker must start before injecting the fault")
        return process, marker

    def test_leader_change_cancels_owned_process_and_does_not_renew_successor(self):
        self.contract["workers"][0]["argv"][-1] = "hang"
        self.contract["workers"][0]["deadline_seconds"] = 10
        process, marker = self.running()
        current = json.loads(self.git("show", "refs/coord/leader").stdout)
        current.update(leader="successor", epoch=current["epoch"] + 1)
        blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=self.repo,
            input=json.dumps(current), capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()
        self.git("update-ref", "refs/coord/leader", blob)
        stdout, stderr = process.communicate(timeout=7)
        self.assertEqual(process.returncode, 3, stdout + stderr)
        self.assertEqual(self.git("rev-parse", "refs/coord/leader").stdout.strip(), blob)
        self.assertNotEqual(json.loads(stdout.splitlines()[-1])["state"], "ready_for_review")
        with self.assertRaises(ProcessLookupError):
            os.kill(int(marker.read_text(encoding="utf-8")), 0)

    def test_blocked_git_does_not_hold_attempt_cleanup(self):
        script = self.scripts / "coord-core.py"
        source = script.read_text(encoding="utf-8")
        source = source.replace('def _git_status(repo, *args, stdin=None):',
            'def _git_status(repo, *args, stdin=None):\n'
            '    if (Path(repo) / "stall-leader").exists():\n        time.sleep(30)')
        script.write_text(source, encoding="utf-8")
        self.contract["workers"][0]["argv"][-1] = "hang"
        self.contract["workers"][0]["deadline_seconds"] = 1
        self.contract["workers"][0]["prompts"] *= 2
        start = time.monotonic()
        process, marker = self.running()
        (self.repo / "stall-leader").write_text("fault", encoding="utf-8")
        stdout, stderr = process.communicate(timeout=6)
        self.assertEqual(process.returncode, 3, stdout + stderr)
        self.assertLess(time.monotonic() - start, 6)
        with self.assertRaises(ProcessLookupError):
            os.kill(int(marker.read_text(encoding="utf-8")), 0)

    def test_signal_cancels_the_owned_worker(self):
        self.contract["workers"][0]["argv"][-1] = "hang"
        self.contract["workers"][0]["deadline_seconds"] = 10
        process, marker = self.running()
        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=6)
        self.assertEqual(process.returncode, 3, stdout + stderr)
        with self.assertRaises(ProcessLookupError):
            os.kill(int(marker.read_text(encoding="utf-8")), 0)

    def test_same_owner_new_epoch_cannot_be_renewed_by_old_attempt(self):
        self.prepare()
        self.run_prepared()
        current = json.loads(self.git("show", "refs/coord/leader").stdout)
        current["epoch"] += 1
        blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=self.repo,
            input=json.dumps(current), capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()
        self.git("update-ref", "refs/coord/leader", blob)
        self.cli("_renew", "--run", "test-run", expected=2)
        self.assertEqual(self.git("rev-parse", "refs/coord/leader").stdout.strip(), blob)

    def test_partial_prepare_lists_retained_and_unprepared_workers(self):
        self.contract["workers"].append(self.worker("worker-2", "work-two"))
        (self.repo.parent / "repo-work-two").mkdir()
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
        self.cli("prepare", "--contract", str(self.contract_path), expected=2)
        result = self.cli("status", "--run", "test-run")
        self.assertEqual(result["state"], "prepare_failed")
        self.assertTrue(Path(result["workers"][0]["worktree"]).is_dir())
        self.assertTrue(Path(result["workers"][0]["manual_brief"]).is_file())
        self.assertIsNone(result["workers"][1]["worktree"])

    def test_worker_log_cannot_supply_owner_completion(self):
        self.prepare()
        forged = {"kind": "runner", "session": "worker-1", "run_id": "test-run", "at": time.time(),
                  "state": "finished", "result": {"state": "ready_for_review"}}
        (self.repo / ".agents/log/worker-1.jsonl").write_text(json.dumps(forged) + "\n", encoding="utf-8")
        self.assertEqual(self.cli("status", "--run", "test-run")["state"], "prepared")

    def test_worker_identity_cannot_be_reused_across_runs(self):
        self.prepare()
        self.contract["run_id"] = "second-run"
        self.contract["workers"][0]["branch"] = "work-two"
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
        result = self.cli("prepare", "--contract", str(self.contract_path), expected=2)
        self.assertEqual(result["code"], "RUN-IDENTITY")

    def test_mutated_compilation_rendition_is_never_dispatched(self):
        self.entries[1]["prompt"] = "UNRELATED_REVIEW_SENTINEL"
        self.write_audit()
        prepared = self.prepare()
        brief = Path(prepared["workers"][0]["manual_brief"]).read_text(encoding="utf-8")
        self.assertNotIn("UNRELATED_REVIEW_SENTINEL", brief)
        self.assertIn("Goal state", brief)
        self.assertIn("--session worker-1", brief)

    def test_substituted_clone_cannot_become_assigned_worktree(self):
        prepared = self.prepare()
        tree = Path(prepared["workers"][0]["worktree"])
        tree.rename(tree.with_name("retained-real-tree"))
        self.git("clone", "-q", "--no-hardlinks", str(self.repo), str(tree))
        self.git("checkout", "-q", "work-one", cwd=tree)
        result = self.cli("fingerprint", "--run", "test-run", expected=2)
        self.assertEqual(result["code"], "RUN-WORKTREE")

    def test_relative_executable_is_bound_to_actual_worker_cwd(self):
        adapter = self.repo / "local-adapter"
        adapter.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        adapter.chmod(0o700)
        self.git("add", "local-adapter")
        self.git("commit", "-qm", "adapter fixture")
        self.contract["workers"][0]["argv"] = ["./local-adapter"]
        prepared = self.prepare()
        before = self.cli("fingerprint", "--run", "test-run")["fingerprints"]
        (Path(prepared["workers"][0]["worktree"]) / "local-adapter").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        after = self.cli("fingerprint", "--run", "test-run")["fingerprints"]
        self.assertNotEqual(before, after)

    def test_aggregate_prompt_bound_refuses_before_worktree_creation(self):
        self.entries[1]["compiled"]["goal_state"]["goal"] = "g" * 200000
        self.write_audit()
        self.contract["workers"][0]["prompts"] *= 8
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
        self.cli("prepare", "--contract", str(self.contract_path), expected=2)
        self.assertFalse((self.repo.parent / "repo-work-one").exists())

    def test_queued_configuration_is_rechecked_before_spawn(self):
        self.contract["parallelism"] = 1
        self.contract["workers"][0]["argv"][-1] = "delay"
        self.contract["workers"].append(self.worker("worker-2", "work-two"))
        process, _ = self.running()
        queued = Path(self.cli("status", "--run", "test-run")["workers"][1]["worktree"])
        (queued / "AGENTS.md").write_text("changed while queued", encoding="utf-8")
        stdout, stderr = process.communicate(timeout=8)
        self.assertEqual(process.returncode, 3, stdout + stderr)
        result = json.loads(stdout.splitlines()[-1])
        self.assertEqual(result["workers"][1]["code"], "RUN-QUALIFICATION")
        self.assertFalse((queued / "prompt-started").exists())

    def test_competing_run_command_does_not_duplicate_prompt(self):
        self.contract["workers"][0]["argv"][-1] = "delay"
        process, marker = self.running()
        result = self.cli("run", "--run", "test-run", "--qualification", str(self.repo / "qualification.json"), expected=2)
        self.assertEqual(result["code"], "RUN-STARTED")
        stdout, stderr = process.communicate(timeout=8)
        self.assertEqual(process.returncode, 0, stdout + stderr)
        receipt = json.loads((marker.parent / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["turns"], 1)

    def test_real_compiler_finish_record_is_accepted_without_nested_cli_wrapper(self):
        shutil.copytree(REPO / "pack/templates", self.scripts.parent / "templates")
        compiled_path = self.repo / "compiled.json"
        def compile_cli(*args):
            result = subprocess.run([sys.executable, str(self.scripts / "prompt-compile.py"), *args],
                cwd=self.repo, env=self.env, capture_output=True, text=True, encoding="utf-8", timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        compile_cli("skeleton", "--text", "Write a receipt for this track.", "--harness", "codex", "--out", str(compiled_path))
        doc = json.loads(compiled_path.read_text(encoding="utf-8"))
        doc["mode"] = "pass-through"
        doc["goal_state"] = {k: "Track fixture contract" for k in doc["goal_state"]}
        doc["decision_requests"] = []
        doc["clauses"] = []
        doc["assumptions"] = []
        compiled_path.write_text(json.dumps(doc), encoding="utf-8")
        compile_cli("finish", str(compiled_path), "--session", "worker-1", "--skill", "implement",
                    "--compiler-model", "offline-test", "--no-clipboard")
        entries = [json.loads(line) for line in self.audit.read_text(encoding="utf-8").splitlines() if line.strip()]
        compilation = next(e for e in reversed(entries) if e["kind"] == "compilation")
        self.assertIn("codex exec", compilation["prompt"])
        self.contract["workers"][0]["prompts"] = [compilation["id"]]
        prepared = self.prepare()
        brief = Path(prepared["workers"][0]["manual_brief"]).read_text(encoding="utf-8")
        self.assertNotIn("codex exec", brief)
        self.assertIn("Track fixture contract", brief)
        self.assertEqual(self.run_prepared()["state"], "ready_for_review")


if __name__ == "__main__":
    unittest.main()
