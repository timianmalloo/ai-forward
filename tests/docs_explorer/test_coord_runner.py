"""AC1–10: deployed entry point, real git/ref/worktrees, offline wire subprocesses."""
import hashlib
import importlib.util
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
from types import SimpleNamespace
from unittest import mock
from coord_native_peer import NativeMetadataPeer

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "pack/scripts"
PEER = Path(__file__).parent / "fixtures/coord_runner_peer.py"
CAPS = dict.fromkeys(("worktree_isolation", "instructions", "hooks", "permissions"), "observed-only")
# Readiness waits poll until a state appears and stop as soon as it does, so a generous
# budget costs nothing on a healthy run. Each includes runner and peer process startup,
# measured at 0.26-0.28 s idle and up to 2.8 s at 10x CPU oversubscription (TEST-TIME-A).
START_WAIT_SECONDS = 10


class PlatformAdmissionTests(unittest.TestCase):
    def test_native_attach_refuses_unsupported_platform_before_reading_identity(self):
        with mock.patch.object(sys, "path", [str(SOURCE), *sys.path]):
            spec = importlib.util.spec_from_file_location("runner_platform_test", SOURCE / "coord-runner.py")
            runner = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(runner)
        with mock.patch.object(runner, "os", SimpleNamespace(name="nt")):
            with self.assertRaises(runner.Refused) as raised:
                runner.Runner.attach_owned(None, None, None)
        self.assertEqual("RUN-PLATFORM", raised.exception.code)


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
            "capabilities": dict(CAPS, interactive_permissions="observed-only")} for s, fp in current["fingerprints"].items()}}
        path = self.repo / "qualification.json"
        path.write_text(json.dumps(q), encoding="utf-8")
        return path

    def run_prepared(self, expected=0):
        q = self.qualify()
        self.pin()
        return self.cli("run", "--run", "test-run", "--qualification", str(q), expected=expected)

    def add_decision(self, session="worker-1"):
        result = subprocess.run([sys.executable, str(self.scripts / "coord-core.py"), "request", "add",
            "--to", "owner", "--from", session, "--reason", "decision-request", "--deadline", "300",
            "--fallback", "wait", "SECRET_DECISION_BODY"], cwd=self.repo,
            env=dict(self.env, AGENT_SESSION=session), capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)["id"]

    def test_open_owner_decision_blocks_ready_even_with_verified_receipt(self):
        self.prepare()
        rid = self.add_decision()
        result = self.run_prepared(expected=3)
        worker = result["workers"][0]
        self.assertEqual("blocked", worker["state"])
        self.assertEqual("RUN-DECISION-OPEN", worker["code"])
        self.assertEqual([rid], worker["decision_state"]["open_ids"])
        self.assertTrue(worker["receipts"])
        self.assertNotIn("SECRET_DECISION_BODY", json.dumps(result))

    def test_other_worker_decision_does_not_block_ready(self):
        self.prepare()
        self.add_decision("other-worker")
        result = self.run_prepared()
        self.assertEqual("ready_for_review", result["workers"][0]["state"])

    def test_actual_independent_owner_ruling_allows_final_readiness(self):
        self.prepare()
        rid = self.add_decision()
        ruled = subprocess.run([sys.executable, str(self.scripts / "coord-decide.py"), "rule", "next",
            "--request", rid, "--title", "Allow controlled handback", "--text", "Owner reviewed the bounded fixture"],
            cwd=self.repo, env=self.env, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, ruled.returncode, ruled.stdout + ruled.stderr)
        result = self.run_prepared()
        self.assertEqual("ready_for_review", result["workers"][0]["state"])
        self.assertEqual(0, result["workers"][0]["decision_state"]["open_count"])

    def test_malformed_decision_state_never_looks_empty(self):
        self.prepare()
        (self.repo / ".agents/requests.jsonl").write_text("[]\n", encoding="utf-8")
        result = self.run_prepared(expected=3)
        worker = result["workers"][0]
        self.assertEqual("blocked", worker["state"])
        self.assertEqual("RUN-DECISION-NOT-CHECKED", worker["code"])


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

    def file_roots(self):
        root = (self.repo / ".agents").resolve()
        (root / "mail").mkdir(parents=True, exist_ok=True)
        (root / "log").mkdir(exist_ok=True)
        paths = [root / "requests.jsonl", root / "log/worker-1.jsonl", root / "mail/owner.jsonl"]
        paths[0].touch()
        paths[2].touch()
        self.contract["workers"][0]["argv"][-1] = "file-roots"
        self.contract["workers"][0]["additional_roots"] = list(map(str, paths))
        return paths

    def test_file_roots_forwarding_and_append_stable_fingerprint(self):
        paths = self.file_roots()
        self.assertFalse(paths[1].exists())
        prepared = self.prepare()
        self.assertTrue(paths[1].is_file())
        before = self.cli("fingerprint", "--run", "test-run")["fingerprints"]
        with paths[2].open("a") as handle:
            handle.write("{}\n")
        self.assertEqual(before, self.cli("fingerprint", "--run", "test-run")["fingerprints"])
        result = self.run_prepared()
        self.assertEqual("ready_for_review", result["workers"][0]["state"])
        receipt = json.loads((Path(prepared["workers"][0]["worktree"]) / "receipt.json").read_text())
        self.assertEqual(list(map(str, paths)), receipt["additional_roots"])

    def test_file_roots_replacement_or_symlink_blocks_dispatch(self):
        paths = self.file_roots()
        prepared = self.prepare()
        q = self.qualify()
        self.pin()
        moved = paths[2].with_suffix(".old")
        paths[2].rename(moved)
        paths[2].touch()
        for symlink in (False, True):
            with self.subTest(symlink=symlink):
                if symlink:
                    paths[2].unlink()
                    paths[2].symlink_to(moved)
                failure = self.cli("run", "--run", "test-run", "--qualification", str(q), expected=2)
                self.assertEqual("RUN-ROOTS", failure["code"])
                self.assertFalse((Path(prepared["workers"][0]["worktree"]) / "prompt-started").exists())

    def test_file_roots_reject_malformed_out_of_scope_and_other_harnesses(self):
        paths = self.file_roots()
        valid = list(map(str, paths))
        for delta in ({"additional_roots": False}, {"additional_roots": None},
                      {"additional_roots": [str(self.repo.resolve() / "AGENTS.md")]},
                      {"additional_roots": valid * 2}, {"additional_roots": [valid[0], valid[0]]},
                      {"additional_roots": [str(paths[0].parent)]},
                      {"additional_roots": [str(paths[0].parent / "x/../requests.jsonl")]},
                      {"additional_roots": [], "harness": "grok"},
                      {"additional_root_identities": []}):
            with self.subTest(delta=delta):
                worker = self.worker("worker-1", "work-one", "file-roots")
                worker["additional_roots"] = valid
                worker.update(delta)
                self.contract["workers"] = [worker]
                self.contract_path.write_text(json.dumps(self.contract))
                failure = self.cli("prepare", "--contract", str(self.contract_path), expected=2)
                self.assertEqual("RUN-ROOTS", failure["code"])
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

    def test_native_denial_never_promotes_existing_artifact_to_ready(self):
        self.assert_native_denial_blocks("agy-denied")

    def test_native_error_step_never_promotes_existing_artifact_to_ready(self):
        self.assert_native_denial_blocks("agy-error")

    def assert_native_denial_blocks(self, mode):
        self.contract["workers"][0].update(harness="agy", transport="agy", prompts=["compiled-1", "compiled-1"])
        self.contract["workers"][0]["argv"][-1] = mode
        self.contract["workers"][0]["argv"] += ["--add-dir", "{worktree}", "--input-format", "stream-json", "--output-format", "stream-json"]
        prepared = self.prepare()
        tree = Path(prepared["workers"][0]["worktree"])
        (tree / "receipt.json").write_text('{"preexisting":true}', encoding="utf-8")
        result = self.run_prepared(expected=3)
        worker = result["workers"][0]
        self.assertEqual(("blocked", "permission_denied", 1),
                         (worker["state"], worker["transport"]["code"], worker["transport"]["native_denials"]))
        self.assertEqual("1", (tree / "prompt-count").read_text())
        self.assertNotIn("receipts", worker)
        status = self.cli("status", "--run", "test-run")
        self.assertEqual(result["workers"], status["workers"])
        self.assertNotIn("SECRET_DO_NOT_LOG", json.dumps(status))

    def test_extension_counter_reaches_persisted_status(self):
        self.contract["workers"][0]["argv"][-1] = "extensions"
        self.prepare()
        result = self.run_prepared()
        self.assertEqual("ready_for_review", result["state"])
        self.assertEqual(3, result["workers"][0]["transport"]["extension_notifications"])
        status = self.cli("status", "--run", "test-run")
        self.assertEqual(result["workers"], status["workers"])
        self.assertNotIn("SECRET_DO_NOT_LOG", json.dumps(status))

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
        until = time.monotonic() + START_WAIT_SECONDS
        while not marker.exists() and time.monotonic() < until and process.poll() is None:
            time.sleep(0.02)
        if not marker.exists():
            # Say why: a runner that exited first reports its transport code (for example
            # deadline_exceeded with prompts_started 0), which a bare assertion hides.
            detail = "runner still running after {0} s".format(START_WAIT_SECONDS)
            if process.poll() is not None:
                out, err = process.communicate(timeout=8)
                lines = out.strip().splitlines() or [err.strip()]
                detail = "runner exited {0} first; last output: {1}".format(
                    process.returncode, lines[-1][-800:])
            self.fail("worker must start before injecting the fault; " + detail)
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
        # The attempt deadline must fire AFTER the worker starts, while git is blocked, and
        # it is measured from attempt start - so it also pays for peer startup. At 1 s,
        # 10x CPU oversubscription made it fire first (deadline_exceeded, prompts_started
        # 0), as on the macOS runner. 4 s covers the 2.8 s worst start measured. The bound
        # stays far below the 30 s git stall, so a cleanup held by git still fails.
        self.contract["workers"][0]["deadline_seconds"] = 4
        self.contract["workers"][0]["prompts"] *= 2
        start = time.monotonic()
        process, marker = self.running()
        (self.repo / "stall-leader").write_text("fault", encoding="utf-8")
        stdout, stderr = process.communicate(timeout=15)
        self.assertEqual(process.returncode, 3, stdout + stderr)
        self.assertLess(time.monotonic() - start, 15)
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
        self.git("worktree", "remove", result["workers"][0]["worktree"])
        missing = self.cli("status", "--run", "test-run")
        self.assertIsNone(missing["workers"][0]["worktree"])
        self.assertTrue(Path(missing["workers"][0]["manual_brief"]).is_file())

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


    def runtime_policy(self, **changes):
        policy = dict(unattended=True, mailbox=False, max_turns=3, max_retries=1, permissions="deny")
        policy.update(changes)
        self.contract["workers"][0]["runtime"] = policy
        self.contract["workers"][0]["deadline_seconds"] = 10

    def test_dynamic_compiled_mailbox_reaches_same_native_session_and_closes(self):
        self.runtime_policy(mailbox=True)
        followup = json.loads(json.dumps(self.entries[-1]))
        followup["id"] = "compiled-2"
        self.entries.append(followup)
        self.write_audit()
        process, marker = self.running()
        self.cli("enqueue", "--run", "test-run", "--worker", "worker-1", "--compilation", "compiled-2")
        self.cli("finish", "--run", "test-run", "--worker", "worker-1")
        stdout, stderr = process.communicate(timeout=12)
        self.assertEqual(0, process.returncode, stdout + stderr)
        result = json.loads(stdout.splitlines()[-1])
        self.assertEqual("ready_for_review", result["state"])
        self.assertEqual(2, result["workers"][0]["transport"]["turns_completed"])
        self.assertEqual(2, json.loads((marker.parent / "receipt.json").read_text())["turns"])
        self.assertNotIn("SECRET", stdout)
        self.cli("enqueue", "--run", "test-run", "--worker", "worker-1", "--compilation", "compiled-2", expected=2)

    def test_interactive_permission_requires_exact_explicit_once_option(self):
        self.runtime_policy(permissions="ask")
        self.contract["workers"][0]["argv"][-1] = "permission"
        process, marker = self.running()
        deadline = time.monotonic() + START_WAIT_SECONDS
        pending = []
        while not pending and time.monotonic() < deadline:
            pending = self.cli("permissions", "--run", "test-run", "--worker", "worker-1")["requests"]
        self.assertEqual(1, len(pending))
        request = pending[0]["id"]
        detail = self.cli("permission-show", "--run", "test-run", "--worker", "worker-1", "--request", request)
        self.assertIn("SECRET", detail["request"]["toolCall"]["title"])
        self.cli("permission-decide", "--run", "test-run", "--worker", "worker-1", "--request", request,
                 "--option", "always", expected=2)
        self.assertFalse((marker.parent / "receipt.json").exists())
        self.cli("permission-decide", "--run", "test-run", "--worker", "worker-1", "--request", request, "--option", "yes")
        stdout, stderr = process.communicate(timeout=12)
        self.assertEqual(0, process.returncode, stdout + stderr)
        result = json.loads(stdout.splitlines()[-1])
        self.assertEqual(1, result["workers"][0]["transport"]["permission_allowed"])
        self.assertNotIn("SECRET", stdout)
        self.assertTrue((marker.parent / "receipt.json").exists())

    def test_ask_mode_requires_separate_observed_callback_capability(self):
        self.runtime_policy(permissions="ask")
        prepared = self.prepare()
        q_path = self.qualify()
        q = json.loads(q_path.read_text())
        q["workers"]["worker-1"]["capabilities"].pop("interactive_permissions")
        q_path.write_text(json.dumps(q))
        self.pin()
        result = self.cli("run", "--run", "test-run", "--qualification", str(q_path), expected=2)
        self.assertEqual("RUN-QUALIFICATION", result["code"])
        self.assertFalse((Path(prepared["workers"][0]["worktree"]) / "prompt-started").exists())

    def test_clean_pre_prompt_eof_retries_once_within_original_budget(self):
        self.runtime_policy()
        self.contract["workers"][0]["argv"][-1] = "startup-retry"
        self.prepare()
        result = self.run_prepared()
        attempts = result["workers"][0]["transport"]["attempts"]
        self.assertEqual(["early_eof", "complete"], [a["code"] for a in attempts])
        self.assertEqual([0, 1], [a["prompts_started"] for a in attempts])
        self.assertEqual("2", (self.repo / "startup-attempt").read_text())

    def test_dirty_startup_is_not_retried(self):
        self.runtime_policy()
        self.contract["workers"][0]["argv"][-1] = "dirty-startup-retry"
        self.prepare()
        result = self.run_prepared(expected=3)
        self.assertEqual("blocked", result["workers"][0]["state"])
        self.assertEqual("1", (self.repo / "startup-attempt").read_text())

    def test_eof_after_prompt_is_not_retried(self):
        self.runtime_policy()
        self.contract["workers"][0]["argv"][-1] = "post-dispatch-eof"
        self.prepare()
        result = self.run_prepared(expected=3)
        self.assertEqual(1, len(result["workers"][0]["transport"]["attempts"]))
        self.assertEqual(1, result["workers"][0]["transport"]["prompts_started"])

    def test_agy_ask_is_refused_before_preparation(self):
        self.runtime_policy(permissions="ask")
        self.contract["workers"][0]["harness"] = "agy"
        self.contract_path.write_text(json.dumps(self.contract))
        result = self.cli("prepare", "--contract", str(self.contract_path), expected=2)
        self.assertEqual("RUN-PERMISSION-UNSUPPORTED", result["code"])

    def test_runtime_controls_require_explicit_unattended_enablement(self):
        self.runtime_policy(unattended=False)
        self.contract_path.write_text(json.dumps(self.contract))
        self.assertEqual("RUN-RUNTIME", self.cli("prepare", "--contract", str(self.contract_path), expected=2)["code"])

    def test_unadvertised_runtime_mode_blocks_before_any_prompt(self):
        self.runtime_policy(mode_id="read-only")
        prepared = self.prepare()
        result = self.run_prepared(expected=3)
        self.assertEqual("unsupported_session_mode", result["workers"][0]["transport"]["code"])
        self.assertEqual(0, result["workers"][0]["transport"]["prompts_started"])
        self.assertFalse((Path(prepared["workers"][0]["worktree"]) / "prompt-started").exists())

    def test_completed_worker_refuses_input_while_other_worker_runs(self):
        self.runtime_policy(mailbox=True)
        self.contract["workers"].append(self.worker("worker-2", "work-two", "hang"))
        followup = json.loads(json.dumps(self.entries[-1]))
        followup["id"] = "compiled-2"
        self.entries.append(followup)
        self.write_audit()
        process, marker = self.running()
        self.cli("finish", "--run", "test-run", "--worker", "worker-1")
        # The completed first worker can be observed through its final transport
        # event while the second keeps the aggregate run active.
        deadline = time.monotonic() + START_WAIT_SECONDS
        response = None
        while time.monotonic() < deadline:
            result = subprocess.run([sys.executable, str(self.scripts / "coord-runner.py"), "finish",
                "--run", "test-run", "--worker", "worker-1"], cwd=self.repo, env=self.env,
                capture_output=True, text=True, timeout=3)
            response = json.loads(result.stdout.splitlines()[-1])
            if response.get("code") == "RUN-FINISHED":
                break
        self.assertEqual("RUN-FINISHED", response.get("code"), response)
        self.assertIsNone(process.poll())
        process.terminate()
        process.communicate(timeout=8)

    def test_profile_helper_hang_cannot_dispatch_after_deadline(self):
        self.runtime_policy()
        self.contract["workers"][0]["deadline_seconds"] = 1
        script = self.scripts / "coord-runner.py"
        script.write_text(script.read_text().replace('elif args.command == "_profile":',
                         'elif args.command == "_profile":\n                time.sleep(30)'))
        prepared = self.prepare()
        started = time.monotonic()
        result = self.run_prepared(expected=3)
        self.assertLess(time.monotonic() - started, 6)
        self.assertNotEqual("ready_for_review", result["state"])
        self.assertFalse((Path(prepared["workers"][0]["worktree"]) / "prompt-started").exists())

    def test_large_unicode_compilation_fits_private_helper_serialization(self):
        self.runtime_policy(mailbox=True)
        raw = "é" * 90000
        followup = json.loads(json.dumps(self.entries[-1]))
        followup.update(id="compiled-2", prompt=raw)
        followup["compiled"].update(raw_id="raw-2", raw_sha256=hashlib.sha256(raw.encode()).hexdigest())
        self.entries.extend([{"id": "raw-2", "kind": "prompt", "prompt": raw}, followup])
        self.write_audit()
        process, marker = self.running()
        self.cli("enqueue", "--run", "test-run", "--worker", "worker-1", "--compilation", "compiled-2")
        self.cli("finish", "--run", "test-run", "--worker", "worker-1")
        stdout, stderr = process.communicate(timeout=12)
        self.assertEqual(0, process.returncode, stdout + stderr)
        self.assertEqual(2, json.loads((marker.parent / "receipt.json").read_text())["turns"])

    def attachment(self, *, hang=False, peer_mode="ok"):
        prepared = self.prepare()
        self.pin()
        cwd = Path(prepared["workers"][0]["worktree"])
        peer = NativeMetadataPeer(cwd, peer_mode)
        self.addCleanup(peer.close)
        executable = self.repo / "native-queue"
        executable.write_text("#!" + sys.executable + "\nimport json,os,sys,time\nfrom pathlib import Path\n"
            "Path('queue-receipt.json').write_text(json.dumps({'argv':sys.argv[1:],'session':os.environ['AGENT_SESSION'],'pid':os.getpid()}))\n"
            + ("time.sleep(30)\n" if hang else "print('SECRET NATIVE OUTPUT')\n"))
        executable.chmod(0o700)
        args = ["attach", "--harness", "codex", "--worker", "worker-1", "--delivery-id", "live-one",
                "--native-session", "11111111-1111-4111-8111-111111111111", "--socket", str(peer.path),
                "--cwd", str(cwd), "--compilation", "compiled-1", "--executable", str(executable)]
        return args, cwd, peer

    def test_native_attachment_checks_thread_then_queues_once_as_worker(self):
        args, cwd, peer = self.attachment()
        result = self.cli(*args)
        self.assertEqual("queued", result["state"])
        receipt = json.loads((cwd / "queue-receipt.json").read_text())
        self.assertEqual("worker-1", receipt["session"])
        self.assertEqual(["queue", "--remote", "unix://" + str(peer.path), "--thread",
                          "11111111-1111-4111-8111-111111111111", "--message"], receipt["argv"][:6])
        self.assertNotIn("SECRET", json.dumps(result))
        self.assertEqual("RUN-ATTACH-REPLAY", self.cli(*args, expected=2)["code"])

    def test_foreign_native_cwd_cannot_receive_delegation(self):
        args, cwd, peer = self.attachment()
        peer.cwd = "/foreign"
        result = self.cli(*args, expected=3)
        self.assertEqual("RUN-ATTACH-CWD", result["code"])
        self.assertFalse((cwd / "queue-receipt.json").exists())

    def test_substituted_registered_directory_cannot_receive_attachment(self):
        args, cwd, peer = self.attachment()
        cwd.rename(cwd.with_name(cwd.name + "-retained"))
        cwd.mkdir()
        self.git("init", "-q", "-b", "work-one", cwd=cwd)
        result = self.cli(*args, expected=2)
        self.assertEqual("RUN-ATTACH-WORKTREE", result["code"])
        self.assertFalse((cwd / "queue-receipt.json").exists())

    def test_interrupting_attachment_reaps_owned_queue_child_and_keeps_backend(self):
        args, cwd, peer = self.attachment(hang=True)
        process = subprocess.Popen([sys.executable, str(self.scripts / "coord-runner.py"), *args],
            cwd=self.repo, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            marker = cwd / "queue-receipt.json"
            deadline = time.monotonic() + START_WAIT_SECONDS
            while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue(marker.exists())
            child_pid = json.loads(marker.read_text())["pid"]
            process.terminate()
            stdout, stderr = process.communicate(timeout=4)
            self.assertEqual(3, process.returncode, stdout + stderr)
            self.assertEqual("indeterminate", json.loads(stdout.splitlines()[-1])["state"])
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)
            self.assertTrue(peer.thread.is_alive())
            self.assertTrue(peer.path.exists())
        finally:
            if process.poll() is None:
                process.terminate()
                process.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
