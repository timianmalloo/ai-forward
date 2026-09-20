"""coord-decide.py and owner-review-gate.py - the Owner seat's mechanism (spec-owner-review US-1..US-10).

Every test runs in a temporary git repository; nothing here touches the real .agents/ or the real
register. Written red-first: the fixed contracts in docs/coordination/coordination-p3-p5-p8.md and
docs/design/owner-review.md are the oracle. The request store is written ONLY by coord-core.py
(P1) and the mails ONLY by coord-mail.py (P4); this suite asserts the rows they produce.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"
HOOKS = REPO / "pack" / "adapters" / "hooks"
DECIDE = SCRIPTS / "coord-decide.py"
CORE = SCRIPTS / "coord-core.py"
GATE = HOOKS / "owner-review-gate.py"

QUESTION = "Does the citation gate scan JSON records?"
FIELDS = {"--options": "prose only | prose and records", "--evidence": "audit-log.jsonl:164 quotes ai-de",
          "--recommendation": "prose only", "--reversibility": "one constant",
          "--blast-radius": "the gate's scan set"}


def _load(name, path):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rows(path):
    if not Path(path).exists():
        return []
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


class TempRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="coord-decide-")).resolve()
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        subprocess.run(["git", "-C", str(self.tmp), "init", "-q"], check=True)
        self.root = self.tmp / ".agents"
        (self.root / "log").mkdir(parents=True)
        self.store = self.root / "requests.jsonl"
        self.register = self.tmp / "docs" / "notes" / "rulings.md"

    def env(self, session="p5", **extra):
        env = {k: v for k, v in os.environ.items() if k not in ("AGENT_SESSION", "COORD_ROOT", "AGENT_NAME")}
        env["COORD_ROOT"] = str(self.root)
        if session:
            env["AGENT_SESSION"] = session
        env.update(extra)
        return env

    def run_script(self, script, *args, session="p5", stdin=None, env=None):
        return subprocess.run([sys.executable, str(script), *args], cwd=str(self.tmp),
                              env=env or self.env(session), input=stdin, capture_output=True,
                              text=True, encoding="utf-8", check=False)

    def decide(self, *args, session="p5"):
        return self.run_script(DECIDE, *args, session=session)

    def request_args(self, omit=(), to="coord", deadline="900", fallback="prose only, as a note",
                     question=QUESTION, **overrides):
        args = ["request"]
        if "--to" not in omit and to is not None:
            args += ["--to", to]
        for flag, value in FIELDS.items():
            if flag not in omit:
                args += [flag, overrides.get(flag, value)]
        if "--deadline" not in omit:
            args += ["--deadline", deadline]
        if "--fallback" not in omit:
            args += ["--fallback", fallback]
        if "question" not in omit and question is not None:
            args.append(question)
        return args

    def make_request(self, session="p5", to="coord"):
        result = self.decide(*self.request_args(to=to), session=session)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return json.loads(result.stdout.strip().splitlines()[-1])


class Request(TempRepo):
    def test_refused_without_five_fields_deadline_fallback(self):
        required = list(FIELDS) + ["--deadline", "--fallback", "--to", "question"]
        # no subTest: pytest's unittest bridge reports a subTest failure as a pass without the
        # subtests plugin (measured red-first: this test PASSED against a missing script)
        for missing in required:
            result = self.decide(*self.request_args(omit=(missing,)))
            self.assertEqual(result.returncode, 2, "omitting %s: %s%s" % (missing, result.stdout, result.stderr))
            self.assertIn("COORD-DECIDE-INCOMPLETE", result.stderr, missing)
            self.assertIn(missing if missing != "question" else "<question>", result.stderr)
            self.assertIn("remedy", result.stderr)
        self.assertFalse(self.store.exists(), "a refused request wrote a row")
        self.assertFalse((self.root / "mail").exists(), "a refused request sent mail")

    def test_writes_p1_record_and_decision_request_mail(self):
        out = self.make_request()
        self.assertTrue(out["id"].startswith("req-"))
        self.assertEqual(out["status"], "sent")
        self.assertTrue(str(out["mail"]).startswith("mail-"), out)
        rows = _rows(self.store)
        self.assertEqual([r["kind"] for r in rows], ["request-add"])
        row = rows[0]
        self.assertEqual(row["id"], out["id"])
        self.assertEqual((row["from"], row["to"], row["text"]), ("p5", "coord", QUESTION))
        self.assertEqual(row["reason"], "decision-request")
        self.assertIsNotNone(row.get("deadline_at"))
        self.assertEqual(row["fallback"], "prose only, as a note")
        contract = json.loads(row["contract"])
        self.assertEqual(sorted(contract), ["blast_radius", "evidence", "options", "recommendation", "reversibility"])
        self.assertEqual(contract["recommendation"], "prose only")
        mails = _rows(self.root / "mail" / "coord.jsonl")
        self.assertEqual(len(mails), 1, mails)
        self.assertEqual((mails[0]["kind"], mails[0]["from"], mails[0]["to"], mails[0]["ref"]),
                         ("decision-request", "p5", "coord", out["id"]))
        self.assertIn(QUESTION, mails[0]["body"])
        self.assertIn("recommendation: prose only", mails[0]["body"])
        twins = _rows(self.root / "log" / "p5.jsonl")
        self.assertTrue(any(t.get("type") == "request" and t.get("action") == "add" for t in twins), twins)
        self.assertTrue(any(t.get("type") == "mail" and t.get("kind") == "decision-request" for t in twins), twins)

    def test_no_second_writer_for_the_request_store(self):
        source = DECIDE.read_text(encoding="utf-8")
        self.assertNotIn('"request-add"', source, "coord-decide.py must not write request rows itself")
        self.assertNotIn("request-resolve", source, "coord-decide.py must resolve through coord-core.py")
        self.assertNotIn("requests.jsonl", source, "the store path belongs to coord-core.py")
        self.assertIn("append_mail", source)

    def test_body_over_4k_refused_before_write(self):
        result = self.decide(*self.request_args(**{"--evidence": "x" * 5000}))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("COORD-DECIDE-BODY-SIZE", result.stderr)
        self.assertFalse(self.store.exists())

    def test_to_broadcast_refused(self):
        result = self.decide(*self.request_args(to="*"))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("COORD-DECIDE-TO", result.stderr)
        self.assertFalse(self.store.exists())

    def test_missing_core_is_not_checked(self):
        empty = self.tmp / "nowhere"
        empty.mkdir()
        result = self.decide("--scripts", str(empty), *self.request_args())
        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
        self.assertIn("COORD-DECIDE-NOT-INSTALLED", result.stderr)

    def test_mail_failure_reported_not_fatal(self):
        mail = _load("coord_mail_for_decide_tests", SCRIPTS / "coord-mail.py")
        now = time.time()
        for i in range(mail.QUEUE_CAP):
            mail.append_mail(self.root, "p3", {"to": "coord", "kind": "note", "body": "n%d" % i}, now=now - 100 + i)
        out = self.make_request()
        self.assertTrue(str(out["mail"]).startswith("not sent: MAIL-FULL"), out)
        self.assertEqual(len(_rows(self.store)), 1)


class Rule(TempRepo):
    def rule(self, number, rid, session="coord", title="Citation gate scans prose only", text="Records quote; prose cites.",
             *extra):
        return self.decide("rule", str(number), "--title", title, "--text", text, "--request", rid, *extra,
                           session=session)

    def test_appends_heading_resolves_and_mails(self):
        rid = self.make_request()["id"]
        result = self.rule(1, rid)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual((out["ruling"], out["request"], out["resolution"]), (1, rid, "Ruling 1"))
        text = self.register.read_text(encoding="utf-8")
        self.assertIn("\n### Ruling 1 — Citation gate scans prose only\n", text)
        self.assertIn("Records quote; prose cites.", text)
        self.assertIn("request: " + rid, text)
        self.assertIn("ruled by: coord", text)
        kinds = [(r["kind"], r.get("resolution")) for r in _rows(self.store)]
        self.assertIn(("request-resolve", "Ruling 1"), kinds)
        mails = _rows(self.root / "mail" / "p5.jsonl")
        self.assertEqual([(m["kind"], m["ref"], m["from"]) for m in mails], [("ruling", rid, "coord")])
        self.assertIn("Ruling 1 — Citation gate scans prose only", mails[0]["body"])

    def test_defined_number_refused(self):
        first = self.make_request()["id"]
        self.assertEqual(self.rule(1, first).returncode, 0)
        second = self.make_request()["id"]
        result = self.rule(1, second)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("COORD-RULING-DEFINED", result.stderr)
        headings = re.findall(r"^### Ruling \d+", self.register.read_text(encoding="utf-8"), re.M)
        self.assertEqual(headings, ["### Ruling 1"])
        self.assertNotIn("request-resolve", [r["kind"] for r in _rows(self.store) if r["id"] == second])

    def test_non_next_number_refused(self):
        rid = self.make_request()["id"]
        result = self.rule(5, rid)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("COORD-RULING-NOT-NEXT", result.stderr)
        self.assertRegex(result.stderr, r"remedy.*\b1\b")
        self.assertFalse(self.register.exists())

    def test_next_literal_allocates_from_the_register(self):
        self.register.parent.mkdir(parents=True)
        self.register.write_text("---\nid: rulings\ntype: doc\n---\n\n# Rulings\n\n### Ruling 4 — by hand\n\nx\n",
                                 encoding="utf-8", newline="\n")
        rid = self.make_request()["id"]
        result = self.rule("next", rid)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout.strip().splitlines()[-1])["ruling"], 5)
        self.assertIn("### Ruling 5 — ", self.register.read_text(encoding="utf-8"))

    def test_self_rule_refused(self):
        rid = self.make_request()["id"]
        result = self.rule(1, rid, session="p5")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("COORD-RULING-SELF", result.stderr)
        self.assertFalse(self.register.exists())

    def test_unknown_or_terminal_request_leaves_register_unchanged(self):
        self.make_request()
        unknown = self.rule(1, "req-does-not-exist")
        self.assertEqual(unknown.returncode, 4, unknown.stdout + unknown.stderr)
        self.assertIn("COORD-REQUEST-NOT-FOUND", unknown.stdout + unknown.stderr)
        rid = self.make_request()["id"]
        resolved = self.run_script(CORE, "request", "resolve", rid, "--resolution", "by hand", session="coord")
        self.assertEqual(resolved.returncode, 0, resolved.stderr)
        terminal = self.rule(1, rid)
        self.assertEqual(terminal.returncode, 3, terminal.stdout + terminal.stderr)
        self.assertFalse(self.register.exists())

    def test_register_created_with_frontmatter_lf(self):
        rid = self.make_request()["id"]
        self.assertEqual(self.rule(1, rid).returncode, 0)
        raw = self.register.read_bytes()
        self.assertTrue(raw.startswith(b"---\n"), raw[:40])
        self.assertIn(b"\nid: rulings\n", raw)
        self.assertIn(b"\ntype: doc\n", raw)
        self.assertNotIn(b"\r\n", raw)

    def test_register_outside_repo_refused(self):
        rid = self.make_request()["id"]
        outside = Path(tempfile.mkdtemp(prefix="outside-"))
        self.addCleanup(shutil.rmtree, str(outside), True)
        result = self.decide("--register", str(outside / "rulings.md"), "rule", "1", "--title", "t", "--text", "x",
                             "--request", rid, session="coord")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("COORD-RULING-REGISTER", result.stderr)
        self.assertFalse((outside / "rulings.md").exists())


class List(TempRepo):
    def test_empty_corpus_renders_not_checked(self):
        result = self.decide("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("NOT CHECKED"), 2, result.stdout)
        as_json = self.decide("list", "--json")
        payload = json.loads(as_json.stdout)
        self.assertEqual(len(payload["not_checked"]), 2, payload)
        self.assertIsNone(payload["open"])
        self.assertIsNone(payload["rulings"])

    def test_renders_open_requests_and_rulings(self):
        seam = self.run_script(CORE, "request", "add", "--to", "coord", "--deadline", "900",
                               "--fallback", "stub", "a seam request, not a decision")
        self.assertEqual(seam.returncode, 0, seam.stderr)
        seam_id = json.loads(seam.stdout)["id"]
        zero = self.decide("list")
        self.assertIn("0 open decision request(s)", zero.stdout)
        self.assertNotIn(seam_id, zero.stdout)
        open_id = self.make_request()["id"]
        ruled_id = self.make_request()["id"]
        self.assertEqual(Rule.rule(self, 1, ruled_id).returncode, 0)
        result = self.decide("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 open decision request(s)", result.stdout)
        self.assertIn(open_id, result.stdout)
        self.assertNotIn(seam_id, result.stdout)
        self.assertIn("Ruling 1", result.stdout)
        self.assertIn("1 ruling(s)", result.stdout)
        payload = json.loads(self.decide("list", "--json").stdout)
        self.assertEqual([r["id"] for r in payload["open"]], [open_id])
        self.assertEqual([(r["number"], r["request"]) for r in payload["rulings"]], [(1, ruled_id)])
        self.assertEqual(payload["not_checked"], [])


class Gate(TempRepo):
    STOP = {"hook_event_name": "Stop", "session_id": "harness-abc", "stop_hook_active": False}

    def gate(self, *args, session="p5", stdin=None, env=None):
        return self.run_script(GATE, *args, session=session, stdin=json.dumps(self.STOP) if stdin is None else stdin,
                               env=env)

    def test_exit_2_with_reason_on_own_open_decision_request(self):
        rid = self.make_request()["id"]
        result = self.gate("--host", "claude")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("owner-review", result.stderr)
        self.assertIn(rid, result.stderr)
        self.assertIn("1 unresolved decision request", result.stderr)
        self.assertNotIn(QUESTION, result.stderr, "the reason carries ids, never a body")
        grok = self.gate("--host", "grok")
        self.assertEqual(grok.returncode, 2, grok.stderr)

    def test_resolved_request_no_longer_blocks(self):
        rid = self.make_request()["id"]
        self.assertEqual(Rule.rule(self, 1, rid).returncode, 0)
        result = self.gate("--host", "claude")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_fail_safe_paths_exit_0(self):
        rid = self.make_request()["id"]
        outside = Path(tempfile.mkdtemp(prefix="outside-root-"))
        self.addCleanup(shutil.rmtree, str(outside), True)
        cases = {
            "no AGENT_SESSION": dict(session=None),
            "stdin not json": dict(stdin="not json {"),
            "stop_hook_active": dict(stdin=json.dumps(dict(self.STOP, stop_hook_active=True))),
            "COORD_ROOT outside the repository": dict(env=self.env("p5", COORD_ROOT=str(outside))),
            "another session's request": dict(session="p8"),
            "addressed to me, not sent by me": dict(session="coord"),
        }
        blocking = self.gate("--host", "claude")
        self.assertEqual(blocking.returncode, 2, "precondition: the open request %s blocks" % rid)
        for name, kwargs in cases.items():
            result = self.gate("--host", "claude", **kwargs)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""), name)
        with open(self.store, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("{not json\n")
        result = self.gate("--host", "claude")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""), "malformed store line")
        bare = Path(tempfile.mkdtemp(prefix="bare-")).resolve()
        self.addCleanup(shutil.rmtree, str(bare), True)
        subprocess.run(["git", "-C", str(bare), "init", "-q"], check=True)
        env = {k: v for k, v in os.environ.items() if k not in ("COORD_ROOT",)}
        env["AGENT_SESSION"] = "p5"
        result = subprocess.run([sys.executable, str(GATE), "--host", "claude"], cwd=str(bare), env=env,
                                input=json.dumps(self.STOP), capture_output=True, text=True,
                                encoding="utf-8", check=False)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""), "no .agents at all")

    def test_copilot_block_shape_and_stop_guard(self):
        rid = self.make_request()["id"]
        result = self.gate("--host", "copilot", "--event", "agentStop", stdin=json.dumps({"sessionId": "x"}))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn(rid, payload["reason"])
        guarded = self.gate("--host", "copilot", "--event", "agentStop",
                            stdin=json.dumps({"sessionId": "x", "stop_hook_active": True}))
        self.assertEqual((guarded.returncode, guarded.stdout), (0, ""))
        other_event = self.gate("--host", "copilot", "--event", "preToolUse", stdin="{}")
        self.assertEqual((other_event.returncode, other_event.stdout), (0, ""))

    def test_agy_stop_answers_continue_while_a_request_is_open_and_stops_refusing_after_two(self):
        # Antigravity has a Stop event (heartbeat rows on Stop, 2026-09-20) and a Stop hook may answer
        # {"decision": "continue"} (docs/hooks). The refusal is capped by executionNum so an unruled
        # request cannot spin the loop forever.
        rid = self.make_request()["id"]
        first = self.gate("--host", "agy", "--event", "Stop",
                          stdin=json.dumps({"conversationId": "c", "executionNum": 1, "terminationReason": "model_stop"}))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(json.loads(first.stdout), {"decision": "continue"})
        self.assertIn(str(rid), first.stderr)
        third = self.gate("--host", "agy", "--event", "Stop",
                          stdin=json.dumps({"conversationId": "c", "executionNum": 3}))
        self.assertEqual((third.returncode, third.stdout), (0, ""), "after two refusals the stop is allowed")
        self.assertIn(str(rid), third.stderr, "the reason still lands on stderr")

    def test_agy_stop_is_silent_without_an_open_request(self):
        result = self.gate("--host", "agy", "--event", "Stop", stdin=json.dumps({"conversationId": "c", "executionNum": 1}))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))


class Hygiene(unittest.TestCase):
    def test_readme_documents_the_gate(self):
        readme = (HOOKS / "README.md").read_text(encoding="utf-8")
        self.assertIn("owner-review-gate.py", readme)
        self.assertIn("agentStop", readme)
        self.assertIn("unsupported", readme)
        self.assertRegex(readme, r"`Stop`")

    def test_scripts_carry_the_console_guard_and_no_bare_text_subprocess(self):
        for path in (DECIDE, GATE):
            source = path.read_text(encoding="utf-8")
            self.assertIn(".reconfigure(", source, path.name)
            for call in re.findall(r"subprocess\.run\((?:[^()]|\([^()]*\))*\)", source):
                if "text=True" in call:
                    self.assertIn('encoding="utf-8"', call, call)


if __name__ == "__main__":
    unittest.main()
