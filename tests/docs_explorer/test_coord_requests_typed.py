"""Tests for coord-core.py typed seam requests (P1) and the CTX-R lease control.

Design: docs/design/typed-seam-requests.md §11. Ids map to its test plan (T1..T11).

Written to fail first: on the un-fixed shape `request add` accepts a request with no deadline
and no fallback (exit 0) - the measured ai-de shape behind 28% of requests never resolving.
"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"
SCRIPT = SCRIPTS / "coord-core.py"


def load_module(name="coord_core", path=SCRIPT):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def blob_sha(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


class RequestCase(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.root = self.repo / ".agents"
        (self.root / "log").mkdir(parents=True)

    def run_cli(self, *args, session="s1"):
        env = dict(os.environ)
        env["COORD_ROOT"] = str(self.root)
        env.pop("AGENT_SESSION", None)
        if session:
            env["AGENT_SESSION"] = session
            env["AGENT_NAME"] = session
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(self.repo),
                              env=env, capture_output=True, text=True, encoding="utf-8")

    def add(self, *extra, deadline="900", fallback="stub the projection", text="need the contract",
            session="s1"):
        args = ["request", "add", "--to", "peer"]
        if deadline is not None:
            args += ["--deadline", deadline]
        if fallback is not None:
            args += ["--fallback", fallback]
        args += list(extra)
        if text is not None:
            args.append(text)
        return self.run_cli(*args, session=session)

    def rows(self):
        path = self.root / "requests.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()]

    def listed(self, status="all"):
        out = self.run_cli("request", "list", "--json", "--status", status)
        self.assertEqual(0, out.returncode, out.stderr)
        return {r["id"]: r for r in json.loads(out.stdout)["requests"]}


class AddTests(RequestCase):
    def test_T1_add_without_deadline_or_fallback_is_refused(self):
        no_deadline = self.add(deadline=None)
        self.assertEqual(2, no_deadline.returncode, no_deadline.stdout)
        self.assertIn("COORD-REQUEST-INCOMPLETE", no_deadline.stderr)
        self.assertIn("--deadline", no_deadline.stderr)
        no_fallback = self.add(fallback=None)
        self.assertEqual(2, no_fallback.returncode, no_fallback.stdout)
        self.assertIn("--fallback", no_fallback.stderr)
        no_text = self.add(text=None)
        self.assertEqual(2, no_text.returncode, no_text.stdout)
        self.assertIn("COORD-REQUEST-INCOMPLETE", no_text.stderr)
        self.assertEqual([], self.rows(), "a refused add must write nothing")

    def test_T2_add_records_deadline_at_and_a_ledger_twin(self):
        before = time.time()
        out = self.add()
        self.assertEqual(0, out.returncode, out.stderr)
        payload = json.loads(out.stdout)
        self.assertTrue(payload["id"].startswith("req-"))
        self.assertEqual("sent", payload["status"])
        row = self.rows()[0]
        self.assertAlmostEqual(before + 900, row["deadline_at"], delta=5)
        self.assertNotIn("deadline_s", row, "one stored quantity: the seconds are the input")
        self.assertEqual("stub the projection", row["fallback"])
        self.assertEqual("need the contract", row["text"])
        twins = [json.loads(line) for line in
                 (self.root / "log" / "s1.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(1, len(twins), twins)
        self.assertEqual("request", twins[0]["type"])
        self.assertEqual("add", twins[0]["action"])
        self.assertEqual(payload["id"], twins[0]["id"])

    def test_T2b_deadline_default_keyword_and_legacy_flags(self):
        out = self.add("--contract", "Ctx.Shortfall", "--reason", "why", "--ref", "mail-X",
                       "--blob", "abc", deadline="default", text=None)
        self.assertEqual(0, out.returncode, out.stderr)
        row = self.rows()[0]
        self.assertAlmostEqual(row["at"] + self.m.REQUEST_DEADLINE, row["deadline_at"], delta=1)
        self.assertEqual("Ctx.Shortfall", row["text"])
        self.assertEqual("mail-X", row["ref"])
        self.assertEqual(900, self.m.REQUEST_DEADLINE)
        self.assertEqual(20, self.m.REQUEST_RETRY)


class LifecycleTests(RequestCase):
    def test_T3_ack_pins_blob_and_a_changed_blob_is_stale(self):
        target = self.repo / "docs" / "x.md"
        target.parent.mkdir()
        target.write_bytes(b"v1\n")
        rid = json.loads(self.add("--path", "docs/x.md").stdout)["id"]
        no_blob = self.run_cli("request", "ack", rid, session="peer")
        self.assertEqual(2, no_blob.returncode)
        self.assertIn("COORD-REQUEST-ACK-NO-BLOB", no_blob.stderr)
        ack = self.run_cli("request", "ack", rid, "--blob", blob_sha(b"v1\n"), session="peer")
        self.assertEqual(0, ack.returncode, ack.stderr)
        self.assertEqual("acked", self.listed()[rid]["status"])
        self.assertIs(False, self.listed()[rid]["stale"])
        target.write_bytes(b"v2\n")
        self.assertIs(True, self.listed()[rid]["stale"])
        doctor = self.run_cli("doctor", session=None)
        self.assertIn("COORD-REQUEST-STALE-ACK", doctor.stdout)
        self.assertIn(rid, doctor.stdout)
        twin = json.loads((self.root / "log" / "peer.jsonl").read_text(
            encoding="utf-8").splitlines()[-1])
        self.assertEqual(("request", "ack", blob_sha(b"v1\n")),
                         (twin["type"], twin["action"], twin["blob"]))

    def test_T3b_stale_is_not_recorded_without_a_path_or_outside_the_repo(self):
        rid = json.loads(self.add().stdout)["id"]
        self.run_cli("request", "ack", rid, "--blob", "abc")
        self.assertEqual("not recorded", self.listed()[rid]["stale"])
        escape = json.loads(self.add("--path", "../../outside.md").stdout)["id"]
        self.run_cli("request", "ack", escape, "--blob", "abc")
        self.assertEqual("not recorded", self.listed()[escape]["stale"])

    def test_T3c_receive_then_ack_then_resolve_and_terminal_refuses_more(self):
        rid = json.loads(self.add().stdout)["id"]
        self.assertEqual(0, self.run_cli("request", "receive", rid, session="peer").returncode)
        self.assertEqual("received", self.listed()[rid]["status"])
        self.run_cli("request", "ack", rid, "--blob", "abc", session="peer")
        resolved = self.run_cli("request", "resolve", rid, "--resolution", "done", session="peer")
        self.assertEqual(0, resolved.returncode, resolved.stderr)
        self.assertEqual("resolved", self.listed()[rid]["status"])
        again = self.run_cli("request", "ack", rid, "--blob", "abc", session="peer")
        self.assertEqual(3, again.returncode)
        self.assertIn("COORD-REQUEST-TERMINAL", again.stdout + again.stderr)
        actions = [json.loads(line)["action"] for line in
                   (self.root / "log" / "peer.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(["receive", "ack", "resolve"], actions)

    def test_T4_expire_records_the_fallback_and_lists_it(self):
        nothing = self.run_cli("request", "expire")
        self.assertEqual(0, nothing.returncode, nothing.stderr)
        self.assertIn("0 expired", nothing.stdout)
        rid = json.loads(self.add(deadline="1", fallback="proceed with a stub").stdout)["id"]
        early = self.run_cli("request", "expire", rid)
        self.assertEqual(3, early.returncode)
        self.assertIn("COORD-REQUEST-NOT-DUE", early.stdout + early.stderr)
        time.sleep(1.2)
        out = self.run_cli("request", "expire")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertIn("1 expired", out.stdout)
        self.assertIn(rid, out.stdout)
        self.assertIn("proceed with a stub", out.stdout)
        last = self.rows()[-1]
        self.assertEqual("request-expire", last["kind"])
        self.assertEqual("fallback", last["outcome"])
        self.assertEqual("proceed with a stub", last["fallback"])
        row = self.listed("expired")[rid]
        self.assertEqual("expired", row["status"])
        self.assertEqual("fallback", row["outcome"])
        self.assertEqual(3, self.run_cli("request", "expire", rid).returncode)

    def test_T10_untyped_rows_list_as_untyped_and_never_expire(self):
        self.m.append_record(self.root / "requests.jsonl", {
            "kind": "request-add", "id": "req-LEGACY", "at": time.time() - 100000,
            "session": "old", "agent": "old", "from": "old", "to": "peer",
            "contract": "X", "reason": "y", "path": ""})
        self.assertEqual("untyped", self.listed()["req-LEGACY"]["status"])
        self.assertIn("req-LEGACY", self.listed("open"))
        out = self.run_cli("request", "expire")
        self.assertIn("0 expired", out.stdout)
        one = self.run_cli("request", "expire", "req-LEGACY")
        self.assertEqual(3, one.returncode)
        self.assertIn("COORD-REQUEST-UNTYPED", one.stdout + one.stderr)
        self.assertEqual("untyped", self.listed()["req-LEGACY"]["status"])

    def test_T11_a_fallback_with_a_newline_renders_on_one_line(self):
        self.add(deadline="1", fallback="first\nsecond")
        time.sleep(1.2)
        out = self.run_cli("request", "expire")
        self.assertNotIn("\nsecond", out.stdout)


class DoctorAndMetricsTests(RequestCase):
    def test_T5_doctor_fails_a_silent_expiry_until_expire_records_the_outcome(self):
        rid = json.loads(self.add(deadline="1").stdout)["id"]
        time.sleep(1.2)
        lines, problems = self.m.request_doctor_lines(self.root, self.repo, time.time())
        self.assertEqual(1, problems, lines)
        text = "\n".join(lines)
        self.assertIn("COORD-REQUEST-SILENT-EXPIRY", text)
        self.assertIn(rid, text)
        doctor = self.run_cli("doctor", session=None)
        self.assertEqual(1, doctor.returncode)
        self.assertRegex(doctor.stdout, r"requests\s+FAIL")
        self.run_cli("request", "expire")
        lines, problems = self.m.request_doctor_lines(self.root, self.repo, time.time())
        self.assertEqual(0, problems, lines)

    def test_T5b_doctor_warns_on_untyped_rows_and_says_not_recorded_over_no_store(self):
        lines, problems = self.m.request_doctor_lines(self.root, self.repo, time.time())
        self.assertEqual(0, problems)
        self.assertIn("not recorded", "\n".join(lines))
        self.m.append_record(self.root / "requests.jsonl", {
            "kind": "request-add", "id": "req-LEGACY", "at": time.time() - 100000,
            "session": "old", "agent": "old", "from": "old", "to": "peer", "contract": "X"})
        lines, problems = self.m.request_doctor_lines(self.root, self.repo, time.time())
        self.assertEqual(0, problems, lines)
        self.assertIn("COORD-REQUEST-UNTYPED 1", "\n".join(lines))
        self.assertIn("COORD-REQUEST-UNTYPED 1", self.run_cli("doctor", session=None).stdout)

    def test_T6_metrics_count_and_say_not_recorded_over_nothing(self):
        empty = json.loads(self.run_cli("metrics", "--json").stdout)
        for key in ("requests_unresolved_by_deadline", "requests_fallback_taken",
                    "requests_stale_acks"):
            self.assertEqual("not recorded", empty[key], key)
        target = self.repo / "y.md"
        target.write_bytes(b"a")
        rid = json.loads(self.add("--path", "y.md", deadline="1").stdout)["id"]
        self.run_cli("request", "ack", rid, "--blob", blob_sha(b"a"))
        target.write_bytes(b"b")
        time.sleep(1.2)
        overdue = json.loads(self.run_cli("metrics", "--json").stdout)
        self.assertEqual(1, overdue["requests_unresolved_by_deadline"])
        self.assertEqual(0, overdue["requests_fallback_taken"])
        self.assertEqual(1, overdue["requests_stale_acks"])
        self.run_cli("request", "expire")
        after = json.loads(self.run_cli("metrics", "--json").stdout)
        self.assertEqual(0, after["requests_unresolved_by_deadline"])
        self.assertEqual(1, after["requests_fallback_taken"])
        text = self.run_cli("metrics").stdout
        self.assertIn("fallback taken", text)

    def test_pack_doctor_check_requests(self):
        doctor = load_module("pack_doctor", SCRIPTS / "pack-doctor.py")
        absent = doctor.check_requests(str(self.repo))
        self.assertEqual("PASS", absent["status"])
        self.assertIn("not recorded", absent["detail"])
        self.m.append_record(self.root / "requests.jsonl", {
            "kind": "request-add", "id": "req-LEGACY", "at": 1.0, "session": "old",
            "agent": "old", "from": "old", "to": "peer", "contract": "X"})
        self.assertEqual("WARN", doctor.check_requests(str(self.repo))["status"])
        self.add(deadline="1")
        time.sleep(1.2)
        failed = doctor.check_requests(str(self.repo))
        self.assertEqual("FAIL", failed["status"])
        self.assertIn("COORD-REQUEST-SILENT-EXPIRY", failed["detail"])


class LeaseExceptTests(RequestCase):
    def test_T7_claim_except_excludes_the_named_paths(self):
        out = self.run_cli("claim", "--path", "pack/commands", "--wi", "WI-1",
                           "--except", "pack/commands/x/SKILL.md")
        self.assertEqual(0, out.returncode, out.stderr)
        event = json.loads((self.root / "log" / "s1.jsonl").read_text(encoding="utf-8").strip())
        self.assertEqual(["pack/commands/x/SKILL.md"], event["except"])
        self.assertEqual(0, self.run_cli("check", "pack/commands/x/SKILL.md", session="s2").returncode)
        self.assertEqual(3, self.run_cli("check", "pack/commands/y/SKILL.md", session="s2").returncode)
        self.assertEqual(0, self.run_cli("claim", "--path", "pack/commands/x/SKILL.md",
                                         "--wi", "WI-2", session="s2").returncode)

    def test_T8_doctor_warns_on_overlapping_live_leases(self):
        now = time.time()
        self.m.append_event(self.root, self.m.make_event("claim", "s1", "s1", "WI-1",
                                                          "pack/commands", now))
        self.m.append_event(self.root, self.m.make_event("claim", "s2", "s2", "WI-2",
                                                          "pack/commands/x/SKILL.md", now))
        lines, warns = self.m.lease_overlap_lines(self.root, now)
        self.assertEqual(1, warns, lines)
        text = "\n".join(lines)
        self.assertIn("COORD-LEASE-OVERLAP", text)
        self.assertIn("s1", text)
        self.assertIn("s2", text)
        doctor = self.run_cli("doctor", session=None)
        self.assertIn("COORD-LEASE-OVERLAP", doctor.stdout)
        self.m.append_event(self.root, self.m.make_event("release", "s1", "s1", "WI-1",
                                                          "pack/commands", now + 1))
        self.m.append_event(self.root, self.m.make_event("claim", "s1", "s1", "WI-1",
                                                          "pack/commands", now + 2,
                                                          excepts=["pack/commands/x/SKILL.md"]))
        lines, warns = self.m.lease_overlap_lines(self.root, now + 3)
        self.assertEqual(0, warns, lines)


if __name__ == "__main__":
    unittest.main()
