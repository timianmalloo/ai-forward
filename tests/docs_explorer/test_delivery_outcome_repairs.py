"""Outcome checkpoint regressions using real compiler/helper and file-writer processes.

The trace barrier only schedules an independent writer after a real read. It does
not substitute snapshot, parsing, hashing, approval, or persistence behavior.
Receipts are synthetic mechanics fixtures, not authenticated human consent.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from typing import Any, Literal, overload

import test_delivery as fixtures
import test_delivery_checkpoint_guards as guards

ROOT = fixtures.ROOT
SCRIPT = Path(os.environ.get("DELIVERY_REPAIR_SCRIPT", fixtures.SCRIPT))

BARRIER_RUNNER = r'''
from pathlib import Path
import runpy, sys, time
script, mode, target, signal, ack, *argv = sys.argv[1:]
fired = False
def trace(frame, event, arg):
    global fired
    if fired:
        return trace
    match = (event == 'return' and mode == 'snapshot' and frame.f_code.co_name == 'snapshot'
             and frame.f_globals.get('__file__') == script)
    if mode == 'save':
        match = (event == 'call' and frame.f_code.co_name == 'save'
                 and frame.f_globals.get('__file__') == script)
    if mode == 'read':
        match = (event == 'return' and frame.f_code.co_name in ('read_bytes', 'read_text')
                 and str(frame.f_locals.get('self', '')) == target)
    if match:
        fired = True
        Path(signal).write_text('captured', encoding='utf-8')
        deadline = time.monotonic() + 10
        while not Path(ack).exists():
            if time.monotonic() > deadline:
                raise RuntimeError('independent file writer did not acknowledge')
            time.sleep(.002)
    return trace
sys.argv = [script, *argv]
sys.settrace(trace)
runpy.run_path(script, run_name='__main__')
'''

FILE_WRITER = r'''
from pathlib import Path
import sys, time
signal, ack, target, replacement = map(Path, sys.argv[1:])
deadline = time.monotonic() + 15
while not signal.exists():
    if time.monotonic() > deadline:
        raise RuntimeError('helper read barrier was not reached')
    time.sleep(.002)
target.write_bytes(replacement.read_bytes())
ack.write_text('written', encoding='utf-8')
print('real independent file write completed', flush=True)
'''


class DeliveryOutcomeRepairsTests(unittest.TestCase):
    tmp: tempfile.TemporaryDirectory
    repo: Path
    state_root: Path
    audit: Path
    log: Path
    compiled_id: str
    setUp = fixtures.DeliveryTests.setUp
    write = fixtures.DeliveryTests.write
    facts = fixtures.DeliveryTests.facts
    start = fixtures.DeliveryTests.start
    receipt = fixtures.DeliveryTests.receipt
    reviewed = guards.DeliveryCheckpointGuardTests.reviewed
    checkpoint_bytes = guards.DeliveryCheckpointGuardTests.checkpoint_bytes
    closure = guards.DeliveryCheckpointGuardTests.closure
    executed_proof = guards.DeliveryCheckpointGuardTests.executed_proof

    def record(self, row):
        evidence = os.environ.get("DELIVERY_REPAIR_EVIDENCE_DIR")
        if evidence:
            destination = Path(evidence)
            destination.mkdir(parents=True, exist_ok=True)
            with (destination / "commands.jsonl").open("a", encoding="utf-8") as out:
                out.write(json.dumps({"test": self.id(), **row}, ensure_ascii=False) + "\n")

    @overload
    def run_cli(self, *args: Any, ok: Literal[True] = True) -> dict[str, Any]: ...

    @overload
    def run_cli(self, *args: Any, ok: Literal[False]) -> subprocess.CompletedProcess[str]: ...

    def run_cli(self, *args: Any, ok: bool = True) -> dict[str, Any] | subprocess.CompletedProcess[str]:
        if args[0] != "route" and getattr(self, "state_root", None):
            args = (*args, "--state-root", self.state_root)
        argv = [sys.executable, "-B", str(SCRIPT), *map(str, args)]
        result = subprocess.run(argv, cwd=self.repo, capture_output=True, text=True,
                                encoding="utf-8", timeout=30)
        self.record({"argv": argv, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def project(self, name, plain=False):
        self.repo = Path(self.tmp.name) / name
        self.repo.mkdir()
        if hasattr(self, "state_root"):
            del self.state_root
        if not plain:
            subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        else:
            self.state_root = Path(self.tmp.name) / (name + "-state")

    def timed(self, mode, target, replacement, *args):
        home = Path(self.tmp.name) / ("barrier-" + str(time.monotonic_ns()))
        home.mkdir()
        runner = home / "runner.py"
        writer_script = home / "writer.py"
        runner.write_text(BARRIER_RUNNER, encoding="utf-8")
        writer_script.write_text(FILE_WRITER, encoding="utf-8")
        signal, ack = home / "captured", home / "written"
        argv = [sys.executable, "-B", str(runner), str(SCRIPT), mode, str(target), str(signal), str(ack),
                *map(str, args)]
        if getattr(self, "state_root", None):
            argv += ["--state-root", str(self.state_root)]
        writer_argv = [sys.executable, "-B", str(writer_script), str(signal), str(ack), str(target), str(replacement)]
        writer = subprocess.Popen(writer_argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, encoding="utf-8")
        try:
            result = subprocess.run(argv, cwd=self.repo, capture_output=True, text=True,
                                    encoding="utf-8", timeout=30)
            output, error = writer.communicate(timeout=20)
            self.assertEqual(writer.returncode, 0, error)
            self.assertTrue(signal.exists() and ack.exists(), "real read/write witness must complete")
            self.assertEqual(target.read_bytes(), replacement.read_bytes())
            self.record({"argv": argv, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
                         "writer_argv": writer_argv, "writer_exit": writer.returncode,
                         "writer_stdout": output, "writer_stderr": error,
                         "replacement_sha256": hashlib.sha256(replacement.read_bytes()).hexdigest()})
            return result
        finally:
            if writer.poll() is None:
                writer.kill()
                writer.communicate()

    def transition(self, kind, proof):
        if kind == "complete":
            return ("complete", "--task", "demo", "--stage", "verify", "--actor", "author",
                    "--evidence", proof, "--closure", self.closure(proof))
        return ("pause", "--task", "demo", "--kind", kind,
                "--authority", "reviewer" if kind == "hard-veto" else "human",
                "--question", "Resolve this specific fixture gate?", "--actor", "author", "--evidence", proof)

    def test_verify_final_observation_refuses_timed_product_writes(self):
        for plain in (False, True):
            for kind in ("complete", "permission", "decision", "release", "hard-veto"):
                with self.subTest(plain=plain, kind=kind):
                    self.project(f"timed-{plain}-{kind}", plain)
                    app, ready = self.reviewed()
                    proof = self.executed_proof(1)
                    before = self.checkpoint_bytes()
                    replacement = Path(self.tmp.name) / "broken-app.py"
                    replacement.write_text("def value():\n    return 0\n", encoding="utf-8")
                    failed = self.timed("snapshot", app, replacement, *self.transition(kind, proof))
                    actual = subprocess.run([sys.executable, "-B", "-c", "from app import value; assert value() == 1"],
                                            cwd=self.repo, capture_output=True, text=True, encoding="utf-8")
                    self.assertNotEqual(actual.returncode, 0, "the independent writer must break real acceptance")
                    self.assertNotEqual(failed.returncode, 0, failed.stdout)
                    self.assertIn("input drift:", failed.stderr)
                    self.assertEqual(self.checkpoint_bytes(), before)
                    app.write_text("def value():\n    return 1\n", encoding="utf-8")
                    restored = self.run_cli("status", "--task", "demo")
                    self.assertEqual(restored["snapshot"], ready["snapshot"])
                    self.assertEqual(restored["decisions"], ready["decisions"])

    def test_ingestion_binds_captured_bytes_and_refuses_timed_replacement(self):
        import test_delivery_repairs as repairs
        for plain in (False, True):
            for intake in ("facts", "receipt", "closure", "review", "authorization"):
                with self.subTest(plain=plain, intake=intake):
                    self.project(f"binding-{plain}-{intake}", plain)
                    app = self.repo / "app.py"
                    app.write_text("def value():\n    return 1\n", encoding="utf-8")
                    if intake in ("facts", "review", "authorization"):
                        started = self.start(contract_tier="T1", design_ready=True)
                    else:
                        _, started = self.reviewed()
                    proof = self.executed_proof(1)
                    if intake == "facts":
                        target = self.facts(design_ready=True)
                        changed = {**json.loads(target.read_text(encoding="utf-8")), "risks": ["security"]}
                        argv = ("start", "--task", "incoming", "--facts", target,
                                "--audit-root", self.audit, "--compiled-id", self.compiled_id)
                    elif intake == "receipt":
                        paused = self.run_cli("pause", "--task", "demo", "--kind", "permission",
                                              "--authority", "human", "--question", "Permit scoped verification?")
                        target = self.receipt(paused)
                        changed = {**json.loads(target.read_text(encoding="utf-8")), "decision": "denied"}
                        argv = ("resume", "--task", "demo", "--receipt", target)
                    elif intake == "closure":
                        target = self.closure(proof)
                        changed = json.loads(target.read_text(encoding="utf-8"))
                        changed["criteria"][0]["criterion"] = "Substituted criterion"
                        argv = self.transition("complete", proof)
                    else:
                        blocked = self.run_cli("complete", "--task", "demo", "--stage", "implement",
                                               "--actor", "author", "--evidence", proof)
                        review, authorization = repairs.DeliveryRepairTests.repair_inputs.__get__(self)(blocked)
                        target = review if intake == "review" else authorization
                        changed = {**json.loads(target.read_text(encoding="utf-8")),
                                   "decision": "approved" if intake == "review" else "denied"}
                        argv = ("repair", "--task", "demo", "--stage", "implement", "--review", review,
                                "--authorization", authorization, "--actor", "author", "--path", "app.py")
                    original = target.read_bytes()
                    before = self.checkpoint_bytes()
                    replacement = self.write("replacement.json", changed)
                    failed = self.timed("read", target, replacement, *argv)
                    self.assertNotEqual(failed.returncode, 0, failed.stdout[:400])
                    self.assertRegex(failed.stderr, r"(?:input|evidence) drift:")
                    self.assertEqual(self.checkpoint_bytes(), before)
                    if intake == "facts":
                        area = Path(started["local_area"])
                        self.assertFalse(list(area.rglob("incoming.json")))
                    target.write_bytes(original)
                    accepted = self.run_cli(*argv)
                    self.assertEqual(accepted["snapshot"], started["snapshot"])
                    self.run_cli("status", "--task", "incoming" if intake == "facts" else "demo")
                    baseline = self.checkpoint_bytes()
                    target.write_bytes(replacement.read_bytes())
                    drift = self.run_cli("status", "--task", "incoming" if intake == "facts" else "demo", ok=False)
                    self.assertRegex(drift.stderr, r"(?:input|evidence) drift:")
                    self.assertEqual(self.checkpoint_bytes(), baseline)

    def test_verify_rechecks_product_after_presave_evidence_validation(self):
        for plain in (False, True):
            for kind in ("complete", "permission", "decision", "release", "hard-veto"):
                with self.subTest(plain=plain, kind=kind):
                    self.project(f"presave-{plain}-{kind}", plain)
                    app, _ = self.reviewed()
                    proof = self.executed_proof(1)
                    before = self.checkpoint_bytes()
                    replacement = Path(self.tmp.name) / "presave-broken.py"
                    replacement.write_text("def value():\n    return 0\n", encoding="utf-8")
                    failed = self.timed("save", app, replacement, *self.transition(kind, proof))
                    self.assertNotEqual(failed.returncode, 0, failed.stdout[:400])
                    self.assertIn("input drift:", failed.stderr)
                    self.assertEqual(self.checkpoint_bytes(), before)

    def finish_document(self, document, name, session):
        path = self.write(name + ".json", document)
        argv = [sys.executable, "-B", str(ROOT / "pack/scripts/prompt-compile.py"), "finish", str(path),
                "--session", session, "--audit-root", str(self.audit), "--no-clipboard"]
        result = subprocess.run(argv, cwd=self.repo, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.record({"argv": argv, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(self.log.read_text(encoding="utf-8").splitlines()[-1])

    def test_prestart_first_question_recovers_and_converts_same_task_in_fresh_processes(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                self.project(f"prestart-{plain}", plain)
                settled = self.start(contract_tier="T1", design_ready=True)
                original = settled["contract"]
                doc = json.loads(json.dumps(original["entry"]["compiled"]))
                question = "Use the existing feature boundary without release?"
                doc["decision_requests"] = [{"id": "DR-1", "assumption": "#1", "question": question,
                                              "default": "none", "answer": "unanswered"}]
                draft = self.finish_document(doc, "draft", "initial-session")
                self.assertIs(draft["dispatchable"], False)
                source = self.write("first-question-source.json", {"question": question,
                    "raw_id": doc["raw_id"], "source": "fixture-agent-question"})
                before_log = self.log.read_bytes()
                argv = ("prestart", "--task", "waiting", "--audit-root", self.audit,
                        "--compiled-id", draft["id"], "--question", question, "--evidence", source)
                waiting = self.run_cli(*argv)
                self.assertEqual(waiting["phase"], "prestart")
                self.assertIsNone(waiting["next"])
                self.assertEqual(waiting["raw"], original["raw_entry"]["prompt"])
                self.assertEqual(waiting["raw_id"], doc["raw_id"])
                self.assertEqual(waiting["question"], question)
                self.assertEqual(waiting["draft"]["entry"], draft)
                pointer = waiting["recovery"]
                self.assertEqual(pointer["task"], "waiting")
                self.assertEqual(Path(pointer["repo"]), self.repo.resolve())
                checkpoint = Path(pointer["checkpoint"])
                self.assertTrue(checkpoint.is_file())
                before = checkpoint.read_bytes()
                # A fresh process uses only the advertised pointer, not fixture
                # knowledge of the default Git versus explicit plain state root.
                pointer_args = ["status", "--task", pointer["task"], "--repo", pointer["repo"]]
                if pointer["state_root"] is not None:
                    pointer_args += ["--state-root", pointer["state_root"]]
                result = subprocess.run([sys.executable, "-B", str(SCRIPT), *pointer_args],
                                        cwd=Path(self.tmp.name), capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), waiting)
                self.assertEqual(self.run_cli("status", "--task", "waiting"), waiting)
                for verb_args in (("complete", "--stage", "implement", "--actor", "author", "--evidence", source),
                                  ("pause", "--kind", "decision", "--authority", "human", "--question", question),
                                  ("resume", "--receipt", source)):
                    refused = self.run_cli(*verb_args, "--task", "waiting", ok=False)
                    self.assertIn("prestart", refused.stderr)
                    self.assertEqual(checkpoint.read_bytes(), before)
                self.run_cli(*argv, ok=False)
                facts = self.facts(design_ready=True)
                start_args = ("start", "--task", "waiting", "--facts", facts, "--audit-root", self.audit)
                for compiled in (draft["id"], self.compiled_id):
                    self.run_cli(*start_args, "--compiled-id", compiled, ok=False)
                    self.assertEqual(checkpoint.read_bytes(), before)
                source_original = source.read_bytes()
                source.write_text('{"question":"changed"}', encoding="utf-8")
                self.assertIn("evidence drift:", self.run_cli("status", "--task", "waiting", ok=False).stderr)
                source.write_bytes(source_original)
                answer = self.write("human-answer-source.json", {"source": "human-message", "question": question,
                    "answer": "Use the existing feature boundary; preserve feature works and exclude release.",
                    "raw_id": doc["raw_id"], "fixture_only": True})
                # Existing compiler does not dispatch a merely answered DR. A new
                # settled document is authored only after the scoped source answer.
                resolved_doc = json.loads(json.dumps(original["entry"]["compiled"]))
                resolved_doc["goal_state"]["goal"] = "Add the small feature within its clarified existing boundary"
                resolved = self.finish_document(resolved_doc, "settled", "fresh-session")
                self.assertIs(resolved["dispatchable"], True)
                self.assertEqual(resolved["compiled"]["raw_id"], waiting["raw_id"])
                self.assertTrue(self.log.read_bytes().startswith(before_log))
                converted = self.run_cli(*start_args, "--compiled-id", resolved["id"], "--decision-evidence", answer)
                self.assertEqual(converted["task"], waiting["task"])
                self.assertEqual(converted["raw"], waiting["raw"])
                self.assertEqual(converted["prestart"], json.loads(before))
                self.assertEqual(converted["contract"]["entry"]["compiled"]["goal_state"], resolved_doc["goal_state"])
                self.assertEqual(converted["decisions"][0]["question"], question)
                self.assertEqual({row["path"] for row in converted["decisions"][0]["evidence"]},
                                 {str(source), str(answer)})
                self.assertEqual(converted["next"], "implement")
                self.assertEqual(self.run_cli("status", "--task", "waiting")["prestart"], json.loads(before))
                accepted_bytes = checkpoint.read_bytes()
                self.run_cli(*start_args, "--compiled-id", resolved["id"], "--decision-evidence", answer, ok=False)
                self.run_cli(*argv, ok=False)
                self.assertEqual(checkpoint.read_bytes(), accepted_bytes)
                answer.write_text('{"answer":"changed"}', encoding="utf-8")
                self.assertIn("evidence drift:", self.run_cli("status", "--task", "waiting", ok=False).stderr)
                if plain:
                    self.assertFalse((self.repo / ".git").exists())
                    self.assertFalse((self.repo / "docs").exists())

    def scope_case(self, name, plain=False, change="addition"):
        """Synthetic explicit human decision; real audit, compiler and helper."""
        self.project(name, plain)
        original = self.start(contract_tier="T1", design_ready=True)["contract"]
        document = json.loads(json.dumps(original["entry"]["compiled"]))
        question = "Which completion conditions and exclusions should this same feature use?"
        draft_doc = json.loads(json.dumps(document))
        draft_doc["decision_requests"] = [{"id": "DR-1", "question": question, "answer": "unanswered"}]
        draft = self.finish_document(draft_doc, name + "-draft", "initial")
        self.assertIs(draft["dispatchable"], False)
        question_source = self.write(name + "-question.json", {"question": question, "fixture_only": True})
        waiting = self.run_cli("prestart", "--task", "waiting", "--audit-root", self.audit,
            "--compiled-id", draft["id"], "--question", question, "--evidence", question_source)
        before = {k: document["goal_state"][k][:] for k in ("done_when", "not_in_scope")}
        if change == "addition":
            document["goal_state"]["done_when"].append("value() returns 1")
            answer_text = "Preserve feature works and add value() returns 1. Release remains excluded."
        elif change == "exclusion":
            document["goal_state"]["not_in_scope"] = ["deployment"]
            answer_text = "Explicitly replace the release exclusion with deployment; include a release checklist, not deployment."
        elif change == "modification":
            document["goal_state"]["done_when"] = ["value() returns 1"]
            answer_text = "Explicitly replace feature works with the precise value() returns 1 acceptance criterion."
        else:
            answer_text = "Keep the original completion conditions and exclusions exactly."
        after = {k: document["goal_state"][k][:] for k in before}
        answer = Path(self.tmp.name) / (name + "-answer.txt")
        answer.write_text(answer_text, encoding="utf-8")
        receipt = {"task": "waiting", "raw_id": waiting["raw_id"], "draft_id": draft["id"],
                   "question": question, "before": before, "after": after, "source": "human-message",
                   "actor": "fixture-human", "evidence": str(answer), "decision": "approved"}
        scope = self.write(name + "-scope.json", receipt)
        # Existing compiler assumption ledger retains the settled decision's
        # source without rewriting raw-phrase clauses or manufacturing a new raw.
        document["assumptions"].append({"id": "#scope-change", "belief": answer_text,
            "confirm": "Explicit approved original human answer at " + str(answer),
            "breaks": "The settled scope would not reflect the human decision",
            "consequential": True, "source": "human-message", "evidence": str(answer)})
        audit_before = self.log.read_bytes()
        resolved = self.finish_document(document, name + "-settled", "fresh")
        self.assertIs(resolved["dispatchable"], True)
        self.record({"scope_fixture": name, "receipt": receipt,
                     "receipt_bytes_hex": scope.read_bytes().hex(),
                     "answer_bytes_hex": answer.read_bytes().hex(),
                     "audit_prefix_bytes_hex": audit_before.hex()})
        checkpoint = Path(waiting["recovery"]["checkpoint"])
        argv = ("start", "--task", "waiting", "--facts", self.facts(design_ready=True),
                "--audit-root", self.audit, "--compiled-id", resolved["id"], "--decision-evidence", answer)
        return waiting, checkpoint, argv, scope, receipt, answer, audit_before

    def test_prestart_explicit_scope_change_converts_same_task(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                waiting, checkpoint, argv, scope, receipt, answer, audit_before = self.scope_case(
                    f"explicit-addition-{plain}", plain)
                original = checkpoint.read_bytes()
                converted = self.run_cli(*argv, "--scope-change", scope)
                self.assertEqual(converted["prestart"], json.loads(original))
                self.assertEqual(converted["raw"], waiting["raw"])
                self.assertEqual(converted["decisions"][0]["scope_change"], receipt)
                self.assertEqual(converted["contract"]["entry"]["compiled"]["goal_state"]["done_when"], receipt["after"]["done_when"])
                records = converted["decisions"][0]["evidence"]
                self.assertIn({"path": str(scope), "sha256": hashlib.sha256(scope.read_bytes()).hexdigest()}, records)
                self.assertIn({"path": str(answer), "sha256": hashlib.sha256(answer.read_bytes()).hexdigest()}, records)
                self.assertTrue(self.log.read_bytes().startswith(audit_before))
                self.assertEqual(self.run_cli("status", "--task", "waiting")["prestart"], converted["prestart"])
                if plain:
                    self.assertFalse((self.repo / ".git").exists())

    def test_prestart_explicit_exclusion_modification_and_unchanged_scope_complete(self):
        for plain in (False, True):
            for change in ("addition", "exclusion", "modification", "unchanged"):
                with self.subTest(plain=plain, change=change):
                    waiting, checkpoint, argv, scope, receipt, answer, audit_before = self.scope_case(
                        f"explicit-{change}-{plain}", plain, change)
                    before = checkpoint.read_bytes()
                    converted = self.run_cli(*argv, *(() if change == "unchanged" else ("--scope-change", scope)))
                    self.assertEqual(converted["prestart"], json.loads(before))
                    self.assertEqual(converted["contract"]["raw_entry"], waiting["draft"]["raw_entry"])
                    self.assertEqual(converted["contract"]["entry"]["compiled"]["clauses"],
                                     waiting["draft"]["entry"]["compiled"]["clauses"])
                    self.assertEqual(converted["contract"]["entry"]["compiled"]["assumptions"][-1]["evidence"], str(answer))
                    self.assertTrue(self.log.read_bytes().startswith(audit_before))
                    app = self.repo / "app.py"
                    app.write_text("def value():\n    return 1\n", encoding="utf-8")
                    result = subprocess.run([sys.executable, "-B", "-c", "from app import value; assert value() == 1"],
                        cwd=self.repo, capture_output=True, text=True, encoding="utf-8")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    proof = self.write("scope-real-proof.json", {"argv": ["from app import value; assert value() == 1"], "exit": result.returncode})
                    blocked = self.run_cli("complete", "--task", "waiting", "--stage", "implement",
                        "--actor", "author", "--evidence", proof)
                    self.assertEqual(blocked["gate"]["authority"], "reviewer")
                    self.run_cli("resume", "--task", "waiting", "--receipt",
                        self.receipt(blocked, actor="author", source="reviewer-report"), ok=False)
                    self.run_cli("resume", "--task", "waiting", "--receipt",
                        self.receipt(blocked, actor="independent-reviewer", source="reviewer-report"))
                    closure = self.write("scope-closure.json", {"criteria": [
                        {"criterion": criterion, "observed": "value() == 1 real subprocess passed", "evidence": [str(proof)]}
                        for criterion in receipt["after"]["done_when"]],
                        "changes": ["app.py"], "tests": ["real value() boundary"], "skips": [], "limits": ["synthetic consent mechanics"], "remaining_gates": []})
                    closed = self.run_cli("complete", "--task", "waiting", "--stage", "verify",
                        "--actor", "author", "--evidence", proof, "--closure", closure)
                    self.assertIsNone(closed["next"])
                    self.assertEqual(self.run_cli("status", "--task", "waiting")["prestart"], json.loads(before))

    def test_prestart_scope_change_refuses_unbound_unapproved_or_missing_answer(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                waiting, checkpoint, argv, scope, receipt, answer, _ = self.scope_case(f"bad-scope-{plain}", plain)
                before = checkpoint.read_bytes()
                self.assertIn("original completion conditions and exclusions", self.run_cli(*argv, ok=False).stderr)
                for key, value in (("task", "unrelated"), ("raw_id", "other-raw"), ("draft_id", "other-draft"),
                    ("question", "unrelated question"), ("before", {"done_when": [], "not_in_scope": []}),
                    ("after", receipt["before"]), ("decision", "denied"), ("decision", True),
                    ("actor", ""), ("source", "model-output"), ("evidence", "")):
                    with self.subTest(field=key, value=value):
                        scope.write_text(json.dumps({**receipt, key: value}), encoding="utf-8")
                        failed = self.run_cli(*argv, "--scope-change", scope, ok=False)
                        self.assertIn("prestart refused:", failed.stderr)
                        self.assertEqual(checkpoint.read_bytes(), before)
                for missing in receipt:
                    with self.subTest(missing=missing):
                        scope.write_text(json.dumps({k: v for k, v in receipt.items() if k != missing}), encoding="utf-8")
                        self.assertIn("prestart refused:", self.run_cli(*argv, "--scope-change", scope, ok=False).stderr)
                        self.assertEqual(checkpoint.read_bytes(), before)
                scope.write_text(json.dumps(receipt), encoding="utf-8")
                saved_answer = answer.read_bytes()
                for empty in (b"", b"   "):
                    answer.write_bytes(empty)
                    self.run_cli(*argv, "--scope-change", scope, ok=False)
                    self.assertEqual(checkpoint.read_bytes(), before)
                answer.unlink()
                self.run_cli(*argv, "--scope-change", scope, ok=False)
                answer.write_bytes(saved_answer)
                unrelated = self.write("unrelated-answer.json", {"answer": "not the original answer"})
                wrong_argv = (*argv[:-1], unrelated)
                self.assertIn("original scope-change answer", self.run_cli(*wrong_argv, "--scope-change", scope, ok=False).stderr)
                self.assertEqual(checkpoint.read_bytes(), before)
                no_task = ("start", "--task", "unrelated", *argv[3:])
                self.run_cli(*no_task, "--scope-change", scope, ok=False)
                self.assertEqual(checkpoint.read_bytes(), before)
                self.run_cli(*argv, "--scope-change", scope)

    def test_prestart_scope_receipt_and_answer_bytes_stay_bound(self):
        for plain in (False, True):
            for target_kind in ("scope", "answer"):
                for seam in ("read", "save"):
                    with self.subTest(plain=plain, target=target_kind, seam=seam):
                        _, checkpoint, argv, scope, receipt, answer, _ = self.scope_case(
                            f"scope-bytes-{plain}-{target_kind}-{seam}", plain)
                        target = scope if target_kind == "scope" else answer
                        original = target.read_bytes()
                        replacement = self.write("scope-denied.json", {**receipt, "decision": "denied"})
                        if target_kind == "answer":
                            replacement.write_text("No. Keep the original scope.", encoding="utf-8")
                        before = checkpoint.read_bytes()
                        failed = self.timed(seam, target, replacement, *argv, "--scope-change", scope)
                        self.assertNotEqual(failed.returncode, 0, failed.stdout[:400])
                        self.assertRegex(failed.stderr, r"evidence drift:")
                        self.assertEqual(checkpoint.read_bytes(), before)
                        target.write_bytes(original)
                        self.run_cli(*argv, "--scope-change", scope)
                        saved = checkpoint.read_bytes()
                        target.write_bytes(replacement.read_bytes())
                        self.assertIn("evidence drift:", self.run_cli("status", "--task", "waiting", ok=False).stderr)
                        self.assertEqual(checkpoint.read_bytes(), saved)
                        target.write_bytes(original)
                        self.run_cli("status", "--task", "waiting")

    def test_prestart_conversion_replay_refuses_silent_answer_or_history_dropping(self):
        for plain in (False, True):
            for change in ("addition", "unchanged"):
                with self.subTest(plain=plain, change=change):
                    _, checkpoint, argv, scope, receipt, answer, _ = self.scope_case(f"drop-{change}-{plain}", plain, change)
                    converted = self.run_cli(*argv, *(() if change == "unchanged" else ("--scope-change", scope)))
                    saved = checkpoint.read_bytes()
                    for mutation in ("answer", "history", "question-source", "scope-receipt"):
                        if mutation == "scope-receipt" and change == "unchanged":
                            continue
                        bad = json.loads(saved)
                        row = bad["decisions"][0]
                        if mutation == "answer":
                            row["evidence"] = [r for r in row["evidence"] if r["path"] != str(answer)]
                        elif mutation == "history":
                            bad["decisions"] = []
                        elif mutation == "question-source":
                            row["evidence"] = [r for r in row["evidence"] if r not in bad["prestart"]["evidence"]]
                        else:
                            row.pop("scope_change"); row.pop("scope_change_record")
                        bad["integrity"] = hashlib.sha256(json.dumps({k: v for k, v in bad.items() if k != "integrity"},
                            sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
                        checkpoint.write_text(json.dumps(bad), encoding="utf-8")
                        self.run_cli("status", "--task", "waiting", ok=False)
                        checkpoint.write_bytes(saved)
                    self.assertEqual(self.run_cli("status", "--task", "waiting")["prestart"], converted["prestart"])

    def test_prestart_legacy_conversion_without_dedicated_answer_list_remains_reusable(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                _, checkpoint, argv, _, _, answer, _ = self.scope_case(f"legacy-{plain}", plain, "unchanged")
                self.run_cli(*argv)
                # The first prestart repair recorded question+answer together in
                # evidence, with no dedicated decision_evidence field.
                legacy = json.loads(checkpoint.read_bytes())
                legacy["decisions"][0].pop("decision_evidence")
                legacy["integrity"] = hashlib.sha256(json.dumps({k: v for k, v in legacy.items() if k != "integrity"},
                    sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
                checkpoint.write_text(json.dumps(legacy), encoding="utf-8")
                saved = checkpoint.read_bytes()
                self.assertEqual(self.run_cli("status", "--task", "waiting")["decisions"], legacy["decisions"])
                answer_original = answer.read_bytes()
                answer.write_text("No, change the original scope", encoding="utf-8")
                self.assertIn("evidence drift:", self.run_cli("status", "--task", "waiting", ok=False).stderr)
                self.assertEqual(checkpoint.read_bytes(), saved)
                answer.write_bytes(answer_original)
                self.run_cli("status", "--task", "waiting")

    def test_prestart_refuses_changed_provenance_identity_and_different_raw_conversion(self):
        import importlib.util
        for plain in (False, True):
            with self.subTest(plain=plain):
                self.project(f"prestart-refusals-{plain}", plain)
                original = self.start(contract_tier="T1", design_ready=True)["contract"]
                doc = json.loads(json.dumps(original["entry"]["compiled"]))
                question = "Which original boundary should be reused?"
                doc["decision_requests"] = [{"id": "DR-1", "question": question, "answer": "unanswered"}]
                draft = self.finish_document(doc, "refusal-draft", "initial")
                source = self.write("question.txt.json", {"question": question})
                waiting = self.run_cli("prestart", "--task", "waiting", "--audit-root", self.audit,
                                       "--compiled-id", draft["id"], "--question", question, "--evidence", source)
                checkpoint = Path(waiting["recovery"]["checkpoint"])
                baseline = checkpoint.read_bytes()
                answer = self.write("answer.json", {"source": "human-message", "answer": "Keep the original scope",
                                                    "fixture_only": True})
                # Another legitimate accepted raw request, even with an answer,
                # cannot replace this prestart task's original raw identifier.
                raw_path = Path(self.tmp.name) / "other-raw.txt"
                raw_path.write_text(original["raw_entry"]["prompt"], encoding="utf-8")
                result = subprocess.run([sys.executable, "-B", str(ROOT / "pack/scripts/audit-log.py"),
                    "--root", str(self.audit), "append", "--kind", "prompt", "--shortname", "other-raw",
                    "--session", "fresh", "--prompt-file", str(raw_path), "--summary", "distinct request"],
                    cwd=self.repo, capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(result.returncode, 0, result.stderr)
                other_raw = json.loads(self.log.read_text(encoding="utf-8").splitlines()[-1])
                other_doc = json.loads(json.dumps(original["entry"]["compiled"]))
                other_doc["raw_id"] = other_raw["id"]
                other = self.finish_document(other_doc, "other-contract", "fresh")
                refused = self.run_cli("start", "--task", "waiting", "--facts", self.facts(design_ready=True),
                    "--audit-root", self.audit, "--compiled-id", other["id"], "--decision-evidence", answer, ok=False)
                self.assertIn("same original raw id", refused.stderr)
                self.assertEqual(checkpoint.read_bytes(), baseline)
                changed_scope = json.loads(json.dumps(original["entry"]["compiled"]))
                changed_scope["goal_state"]["done_when"] = ["substituted narrower acceptance"]
                narrowed = self.finish_document(changed_scope, "narrowed-contract", "fresh")
                refused = self.run_cli("start", "--task", "waiting", "--facts", self.facts(design_ready=True),
                    "--audit-root", self.audit, "--compiled-id", narrowed["id"], "--decision-evidence", answer, ok=False)
                self.assertIn("original completion conditions and exclusions", refused.stderr)
                self.assertEqual(checkpoint.read_bytes(), baseline)
                saved_log = self.log.read_bytes()
                rows = [json.loads(line) for line in saved_log.decode("utf-8").splitlines()]
                for row in rows:
                    if row["id"] == draft["id"]:
                        row["summary"] = "altered prior draft history"
                self.log.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
                self.assertIn("contract drift:", self.run_cli("status", "--task", "waiting", ok=False).stderr)
                self.assertEqual(checkpoint.read_bytes(), baseline)
                self.log.write_bytes(saved_log)
                # Copying the intact record to another project remains refused,
                # even if the task slug, source files and audit root are unchanged.
                other_project = Path(self.tmp.name) / ("other-project-" + str(plain))
                other_project.mkdir()
                if not plain:
                    subprocess.run(["git", "init", "-q", str(other_project)], check=True)
                spec = importlib.util.spec_from_file_location("delivery_pointer_fixture", SCRIPT)
                assert spec is not None and spec.loader is not None
                helper = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(helper)
                copied = helper.state_path(other_project, "waiting", getattr(self, "state_root", None))
                copied.parent.mkdir(parents=True, exist_ok=True)
                copied.write_bytes(baseline)
                result = self.run_cli("status", "--task", "waiting", "--repo", other_project, ok=False)
                self.assertIn("identity drift:", result.stderr)
                self.assertEqual(checkpoint.read_bytes(), baseline)
                self.assertEqual(self.run_cli("status", "--task", "waiting")["raw_id"], waiting["raw_id"])

    def test_preexisting_descendant_markers_are_ephemeral_but_other_bytes_are_not(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                self.project(f"markers-{plain}", plain)
                markers = []
                for store in ("docs/audit", ".agents/log/audit"):
                    for suffix in (".run-starts.json", ".run-starts.json.tmp"):
                        marker = self.repo / "src/nested" / store / suffix
                        marker.parent.mkdir(parents=True, exist_ok=True)
                        marker.write_text('{"preexisting":1}', encoding="utf-8")
                        markers.append(marker)
                if not plain:
                    subprocess.run(["git", "add", "src"], cwd=self.repo, check=True)
                started = self.start()
                before = self.checkpoint_bytes()
                for marker in markers:
                    marker.write_text('{"updated":2}', encoding="utf-8")
                self.assertEqual(self.run_cli("status", "--task", "demo")["snapshot"], started["snapshot"])
                for name in ("audit-log.jsonl", ".run-starts.json.backup", "durable.json"):
                    path = markers[0].parent / name
                    path.write_text('{"durable":true}', encoding="utf-8")
                    self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
                    self.assertEqual(self.checkpoint_bytes(), before)
                    path.unlink()
                registered = self.run_cli("start", "--task", "registered", "--facts", self.facts(),
                                          "--audit-root", self.audit, "--compiled-id", self.compiled_id,
                                          "--input", markers[0])
                markers[0].write_text('{"explicit":"load-bearing"}', encoding="utf-8")
                self.assertIn("input drift:", self.run_cli("status", "--task", "registered", ok=False).stderr)
                self.assertEqual(registered["inputs"][-1]["path"], str(markers[0]))

    def test_duration_marker_fixture_accepts_a_symlinked_temporary_root(self):
        alias = Path(self.tmp.name) / "temporary-root-alias"
        try:
            alias.symlink_to(Path(self.tmp.name).resolve(), target_is_directory=True)
        except OSError:
            if os.name == "nt":
                self.skipTest("Host does not permit directory symlink creation")
            raise
        aliased_tmp = tempfile.TemporaryDirectory(dir=alias)
        self.addCleanup(aliased_tmp.cleanup)
        self.assertNotEqual(Path(aliased_tmp.name), Path(aliased_tmp.name).resolve())
        original_tmp = self.tmp
        self.tmp = aliased_tmp
        try:
            # Exercise the same fixture and all link/directory safety assertions.
            self.test_duration_marker_exemption_never_hides_filesystem_links_or_directories()
        finally:
            self.tmp = original_tmp

    def test_duration_marker_exemption_never_hides_filesystem_links_or_directories(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_marker_fixture", SCRIPT)
        assert spec is not None and spec.loader is not None
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        for plain in (False, True):
            with self.subTest(plain=plain):
                self.project(f"marker-links-{plain}", plain)
                self.repo = self.repo.resolve()
                marker = self.repo / "src/docs/audit/.run-starts.json"
                marker.parent.mkdir(parents=True)
                marker.write_text("{}", encoding="utf-8")
                self.assertTrue(helper.runtime_start_marker(marker, self.repo.resolve()))
                outside = Path(self.tmp.name) / ("external-marker-" + str(plain))
                outside.write_text("{}", encoding="utf-8")
                marker.unlink()
                marker.symlink_to(outside)
                self.assertFalse(helper.runtime_start_marker(marker, self.repo.resolve()))
                started = self.start()
                replacement = Path(self.tmp.name) / ("external-other-" + str(plain))
                replacement.write_text("{}", encoding="utf-8")
                marker.unlink()
                marker.symlink_to(replacement)
                self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
                marker.unlink()
                marker.mkdir()
                self.assertFalse(helper.runtime_start_marker(marker, self.repo.resolve()))
                (marker / "durable.json").write_text("{}", encoding="utf-8")
                observed = helper.snapshot(self.repo, started["local_area"], details=True)
                durable_key = str(Path("src/docs/audit/.run-starts.json/durable.json")) if plain else "src/docs/audit/.run-starts.json/durable.json"
                self.assertIn(durable_key, observed["entries"])
                (marker / "durable.json").unlink()
                marker.rmdir()
                marker.parent.rmdir()
                external_folder = Path(self.tmp.name) / ("external-audit-" + str(plain))
                external_folder.mkdir()
                (external_folder / marker.name).write_text("{}", encoding="utf-8")
                marker.parent.symlink_to(external_folder, target_is_directory=True)
                self.assertFalse(helper.runtime_start_marker(marker, self.repo.resolve()))
                audit_key = str(Path("src/docs/audit")) if plain else "src/docs/audit"
                self.assertIn(audit_key, helper.snapshot(self.repo, started["local_area"], details=True)["entries"])

    def test_verify_serial_drift_and_unchanged_transition_controls(self):
        for plain in (False, True):
            self.project(f"controls-{plain}", plain)
            app, ready = self.reviewed()
            proof = self.executed_proof(1, local=True)
            before = self.checkpoint_bytes()
            app.write_text("def value():\n    return 0\n", encoding="utf-8")
            for kind in ("complete", "permission", "decision", "release", "hard-veto"):
                with self.subTest(plain=plain, serial=kind):
                    failed = self.run_cli(*self.transition(kind, proof), ok=False)
                    self.assertIn("input drift:", failed.stderr)
                    self.assertEqual(self.checkpoint_bytes(), before)
            app.write_text("def value():\n    return 1\n", encoding="utf-8")
            for kind in ("permission", "decision", "release", "hard-veto"):
                paused = self.run_cli(*self.transition(kind, proof))
                self.assertEqual(paused["snapshot"], ready["snapshot"])
                self.assertEqual(paused["decisions"][:len(ready["decisions"])], ready["decisions"])
                receipt = self.receipt(paused, actor="reviewer" if kind == "hard-veto" else "operator",
                                       source="reviewer-report" if kind == "hard-veto" else "human-message")
                self.run_cli("resume", "--task", "demo", "--receipt", receipt)
            closed = self.run_cli(*self.transition("complete", proof))
            self.assertEqual(closed["snapshot"], ready["snapshot"])
            self.assertIsNone(self.run_cli("status", "--task", "demo")["next"])


if __name__ == "__main__":
    unittest.main()
