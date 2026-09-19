"""coord-mail.py - the local message layer (spec-message-layer US-1..US-5, US-7..US-9).

Every test runs in a temporary git repository; nothing here touches the real .agents/.
Written red-first: the store contract (docs/coordination/coordination-p2-p8.md) is the oracle.
"""
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "pack" / "scripts"
MAIL = SCRIPTS / "coord-mail.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mail = _load("coord_mail_under_test", MAIL)
pa = _load("pack_apply_for_mail", SCRIPTS / "pack-apply.py")
doctor = _load("pack_doctor_for_mail", SCRIPTS / "pack-doctor.py")


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                          encoding="utf-8", check=False)


def _lines(path):
    text = Path(path).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


class TempRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="coord-mail-")).resolve()
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        _git(self.tmp, "init", "-q")
        _git(self.tmp, "config", "user.email", "t@example.com")
        _git(self.tmp, "config", "user.name", "t")
        self.root = self.tmp / ".agents"
        self.root.mkdir()

    def env(self, session="p2", **extra):
        env = {k: v for k, v in os.environ.items() if k not in ("AGENT_SESSION", "COORD_ROOT")}
        if session:
            env["AGENT_SESSION"] = session
        env.update(extra)
        return env

    def cli(self, *args, session="p2", **extra):
        return subprocess.run([sys.executable, str(MAIL), *args], cwd=str(self.tmp),
                              env=self.env(session, **extra), capture_output=True, text=True,
                              encoding="utf-8", check=False)


class SendAndTwin(TempRepo):
    def test_delegate_round_trip_and_ledger_twin(self):
        proc = self.cli("send", "--to", "p6", "--kind", "delegate", "--body", "take P6",
                        "--ref", "docs/x.md")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        mail_id = proc.stdout.strip()
        rows = _lines(self.root / "mail" / "p6.jsonl")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(set(row), {"id", "ts", "from", "to", "kind", "body", "ref", "ack"})
        self.assertEqual(row["id"], mail_id)
        self.assertTrue(mail_id.startswith("mail-"))
        self.assertTrue(row["ts"].endswith("Z"))
        self.assertEqual((row["from"], row["to"], row["kind"], row["body"], row["ref"], row["ack"]),
                         ("p2", "p6", "delegate", "take P6", "docs/x.md", None))
        twins = [r for r in _lines(self.root / "log" / "p2.jsonl") if r.get("type") == "mail"]
        self.assertEqual(len(twins), 1)
        twin = twins[0]
        self.assertNotIn("body", twin)
        for key in ("mail_id", "kind", "from", "to", "ref"):
            self.assertIn(key, twin)
        self.assertEqual((twin["mail_id"], twin["kind"], twin["from"], twin["to"], twin["ref"]),
                         (mail_id, "delegate", "p2", "p6", "docs/x.md"))

    def test_note_has_no_twin_but_ruling_does(self):
        self.assertEqual(self.cli("send", "--to", "p6", "--kind", "note", "--body", "hi").returncode, 0)
        self.assertFalse((self.root / "log").exists(), "a note must not reach the ledger")
        self.assertEqual(self.cli("send", "--to", "p6", "--kind", "ruling", "--body", "DR-1: yes",
                                  "--ref", "DR-1").returncode, 0)
        twins = [r for r in _lines(self.root / "log" / "p2.jsonl") if r.get("type") == "mail"]
        self.assertEqual([t["kind"] for t in twins], ["ruling"])

    def test_body_file_and_broadcast(self):
        (self.tmp / "brief.md").write_text("body from file", encoding="utf-8", newline="\n")
        proc = self.cli("send", "--to", "*", "--kind", "kick", "--body-file", "brief.md")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = _lines(self.root / "mail" / mail.BROADCAST_FILE)
        self.assertEqual(rows[0]["body"], "body from file")
        self.assertEqual(rows[0]["to"], "*")

    def test_refusals_write_nothing_and_exit_2(self):
        cases = [
            (self.cli("send", "--to", "p6", "--kind", "bogus", "--body", "x"), "unknown kind"),
            (self.cli("send", "--to", "p6", "--kind", "note", "--body", "x" * 4097), "4 KiB body"),
            (self.cli("send", "--to", "p6", "--kind", "note", "--body", "x", session=None), "no identity"),
            (self.cli("send", "--to", "_bad", "--kind", "note", "--body", "x"), "reserved session id"),
            (self.cli("send", "--to", "p6", "--kind", "note", "--body-file", "../outside.md"), "body-file outside"),
        ]
        for proc, label in cases:
            with self.subTest(label):
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertTrue(proc.stderr.strip(), "a refusal names its reason")
        self.assertFalse((self.root / "mail").exists(), "nothing was written")

    def test_full_inbox_is_refused_with_exit_3(self):
        for _ in range(mail.QUEUE_CAP):
            mail.append_mail(self.root, "p2", {"to": "p6", "kind": "note", "body": "n"})
        proc = self.cli("send", "--to", "p6", "--kind", "note", "--body", "one more")
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertIn("inbox full: 50 queued for p6", proc.stderr)
        self.assertEqual(len(_lines(self.root / "mail" / "p6.jsonl")), mail.QUEUE_CAP)


class ReadAndAck(TempRepo):
    def seed(self):
        self.mine = mail.append_mail(self.root, "p2", {"to": "p6", "kind": "delegate", "body": "for p6"})
        self.bcast = mail.append_mail(self.root, "p2", {"to": "*", "kind": "kick", "body": "everyone"})
        self.other = mail.append_mail(self.root, "p2", {"to": "p8", "kind": "note", "body": "for p8"})

    def test_read_shows_own_and_broadcast_never_others(self):
        self.seed()
        proc = self.cli("read", session="p6")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("untrusted data", proc.stdout)
        self.assertIn("for p6", proc.stdout)
        self.assertIn("everyone", proc.stdout)
        self.assertNotIn("for p8", proc.stdout)

    def test_read_json_since_and_ack(self):
        self.seed()
        proc = self.cli("read", "--json", session="p6")
        rows = json.loads(proc.stdout)
        self.assertEqual({r["id"] for r in rows}, {self.mine, self.bcast})
        self.assertTrue(all(r["acked"] is False for r in rows))
        since = self.cli("read", "--json", "--since", self.mine, session="p6")
        self.assertEqual([r["id"] for r in json.loads(since.stdout)], [self.bcast])
        acked = self.cli("read", "--ack", "--json", session="p6")
        self.assertEqual(acked.returncode, 0, acked.stderr)
        again = self.cli("read", "--json", session="p6")
        self.assertEqual(json.loads(again.stdout), [])
        # the ack for the broadcast is colocated in the broadcast file, from p6
        acks = [r for r in _lines(self.root / "mail" / mail.BROADCAST_FILE) if r["kind"] == "ack"]
        self.assertEqual([(a["ref"], a["from"]) for a in acks], [(self.bcast, "p6")])

    def test_ack_is_a_new_line_idempotent_and_not_found_is_4(self):
        self.seed()
        before = (self.root / "mail" / "p6.jsonl").read_bytes()
        proc = self.cli("ack", self.mine, session="p6")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        after = (self.root / "mail" / "p6.jsonl").read_bytes()
        self.assertTrue(after.startswith(before), "the original line is byte-identical")
        rows = _lines(self.root / "mail" / "p6.jsonl")
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[1]["kind"], rows[1]["ref"], rows[1]["from"], rows[1]["to"]),
                         ("ack", self.mine, "p6", "p2"))
        self.assertEqual(self.cli("ack", self.mine, session="p6").returncode, 0)
        self.assertEqual(len(_lines(self.root / "mail" / "p6.jsonl")), 2, "idempotent")
        self.assertEqual(self.cli("ack", "mail-DOESNOTEXIST", session="p6").returncode, 4)
        twins = [r for r in _lines(self.root / "log" / "p6.jsonl")] if (self.root / "log" / "p6.jsonl").exists() else []
        self.assertEqual(twins, [], "an ack has no ledger twin")

    def test_nack_via_send_is_colocated(self):
        self.seed()
        proc = self.cli("send", "--kind", "nack", "--ref", self.mine, "--body", "no", "--to", "p2", session="p6")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = _lines(self.root / "mail" / "p6.jsonl")
        self.assertEqual(rows[-1]["kind"], "nack")
        self.assertEqual(self.cli("read", "--json", session="p6").returncode, 0)
        self.assertEqual([r["id"] for r in json.loads(self.cli("read", "--json", session="p6").stdout)],
                         [self.bcast], "a nacked message is no longer unread")


class WriterInvariants(TempRepo):
    def test_append_mail_is_the_single_writer(self):
        mail_id = mail.append_mail(self.root, "p2", {"to": "p6", "kind": "delegate", "body": "x", "ref": "r"})
        row = _lines(self.root / "mail" / "p6.jsonl")[0]
        self.assertEqual(set(row), {"id", "ts", "from", "to", "kind", "body", "ref", "ack"})
        self.assertEqual(row["id"], mail_id)
        twin = _lines(self.root / "log" / "p2.jsonl")[0]
        self.assertEqual(twin["type"], "mail")
        with self.assertRaises(mail.MailError):
            mail.append_mail(self.root, "p2", {"to": "p6", "kind": "shout", "body": "x"})
        with self.assertRaises(mail.MailError):
            mail.append_mail(self.root, "p2", {"to": "p6", "kind": "note", "body": "y" * 4097})
        self.assertEqual(len(_lines(self.root / "mail" / "p6.jsonl")), 1, "no partial write")

    def test_torn_last_line_is_repaired_not_fused(self):
        inbox = self.root / "mail" / "p6.jsonl"
        inbox.parent.mkdir(parents=True)
        with open(inbox, "w", encoding="utf-8", newline="\n") as fh:
            fh.write('{"id":"mail-0","ts":"2026-01-01T00:00:00Z","from":"p2","to":"p6","kind":"note","body":"","ref":null,"ack":null}')
        mail.append_mail(self.root, "p2", {"to": "p6", "kind": "note", "body": "second"})
        self.assertEqual(len(_lines(inbox)), 2)

    def test_corrupt_line_makes_read_not_checked(self):
        inbox = self.root / "mail" / "p6.jsonl"
        inbox.parent.mkdir(parents=True)
        inbox.write_text('{"broken"\n', encoding="utf-8", newline="\n")
        proc = self.cli("read", session="p6")
        self.assertEqual(proc.returncode, 4)
        self.assertIn("NOT CHECKED", proc.stderr)


class Dispatch(TempRepo):
    def _bin(self, name, body_py):
        bindir = self.tmp / "bin"
        bindir.mkdir(exist_ok=True)
        script = bindir / (name + ".py")
        script.write_text(body_py, encoding="utf-8", newline="\n")
        if os.name == "nt":
            launcher = bindir / (name + ".cmd")
            launcher.write_text('@"{0}" "{1}" %*\n'.format(sys.executable, script), encoding="utf-8", newline="\n")
        else:
            launcher = bindir / name
            launcher.write_text("#!/bin/sh\nexec \"{0}\" \"{1}\" \"$@\"\n".format(sys.executable, script),
                                encoding="utf-8", newline="\n")
            launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR)
        return bindir

    def _path(self, bindir=None):
        parts = [str(bindir)] if bindir else []
        for exe in (shutil.which("git"), sys.executable):
            parts.append(str(Path(exe).parent))
        return os.pathsep.join(parts)

    def setUp(self):
        super().setUp()
        (self.tmp / "brief.md").write_text("reply with the single word ok", encoding="utf-8", newline="\n")

    def test_refused_without_deadline_or_fallback(self):
        for args in (("--fallback", "skip"), ("--deadline", "5")):
            proc = self.cli("dispatch", "--harness", "claude-code", "--brief", "brief.md", *args,
                            PATH=self._path())
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertFalse((self.root / mail.HARNESS_STATUS_FILE).exists())

    def test_absent_harness_is_unsupported(self):
        proc = self.cli("dispatch", "--harness", "copilot", "--brief", "brief.md", "--deadline", "5",
                        "--fallback", "skip", PATH=self._path())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        status = json.loads((self.root / mail.HARNESS_STATUS_FILE).read_text(encoding="utf-8"))
        self.assertEqual(status["copilot"]["status"], "unsupported")
        self.assertEqual(set(status["copilot"]), {"version", "date", "status", "evidence"})
        self.assertIn("skip", json.loads(proc.stdout)["fallback"])

    def test_executed_harness_with_structured_reply_is_verified(self):
        bindir = self._bin("claude", "import sys,json\n"
                                    "if '--version' in sys.argv: print('9.9.9'); sys.exit(0)\n"
                                    "print(json.dumps({'result': 'ok', 'argv': sys.argv[1:]}))\n")
        proc = self.cli("dispatch", "--harness", "claude-code", "--brief", "brief.md", "--deadline", "30",
                        "--fallback", "skip", "--budget-calls", "3", PATH=self._path(bindir))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["status"], "verified")
        self.assertNotIn("fallback", result)
        status = json.loads((self.root / mail.HARNESS_STATUS_FILE).read_text(encoding="utf-8"))
        self.assertEqual(status["claude-code"]["status"], "verified")
        self.assertEqual(status["claude-code"]["version"], "9.9.9")
        self.assertIn("--output-format", status["claude-code"]["evidence"])

    def test_harness_past_the_deadline_is_observed_only_with_fallback(self):
        bindir = self._bin("codex", "import sys,time\n"
                                    "if '--version' in sys.argv: print('0.0.1'); sys.exit(0)\n"
                                    "time.sleep(20)\n")
        started = time.monotonic()
        proc = self.cli("dispatch", "--harness", "codex", "--brief", "brief.md", "--deadline", "1",
                        "--fallback", "record blocked and continue", PATH=self._path(bindir))
        self.assertLess(time.monotonic() - started, 15, "the deadline bounded the child")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["status"], "observed-only")
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["fallback"], "record blocked and continue")
        status = json.loads((self.root / mail.HARNESS_STATUS_FILE).read_text(encoding="utf-8"))
        self.assertEqual(status["codex"]["status"], "observed-only")
        self.assertNotIn("reply with the single word ok", status["codex"]["evidence"],
                         "the brief is redacted wherever it sits in argv, not by position")
        self.assertIn("<brief>", status["codex"]["evidence"])


class IgnoreRules(TempRepo):
    def test_pack_apply_lines_track_ledgers_and_ignore_mail(self):
        self.assertIn("!.agents/log/", pa.GITIGNORE_LINES)
        self.assertIn(".agents/mail/", pa.GITIGNORE_LINES)
        self.assertLess(pa.GITIGNORE_LINES.index(".agents/*"), pa.GITIGNORE_LINES.index("!.agents/log/"))
        self.assertIn("!.agents/log/", pa.GITIGNORE_DEPENDENTS[".agents/*"])

    def test_git_reads_the_lines_as_intended(self):
        (self.tmp / ".gitignore").write_text("\n".join(pa.GITIGNORE_LINES) + "\n", encoding="utf-8", newline="\n")
        for rel, ignored in ((".agents/log/x.jsonl", False), (".agents/mail/x.jsonl", True),
                             (".agents/artifacts.yml", False), (".agents/other.tmp", True)):
            with self.subTest(rel):
                rc = _git(self.tmp, "check-ignore", "-q", rel).returncode
                self.assertEqual(rc == 0, ignored)

    def test_pack_apply_places_the_doorbell_hook(self):
        source = (SCRIPTS / "pack-apply.py").read_text(encoding="utf-8")
        self.assertIn('"mail-doorbell.py"', source)


class DoctorMailChecks(TempRepo):
    def by_name(self):
        return {r["name"]: r for r in doctor.check_mail(str(self.tmp))}

    def test_clean_repo_passes(self):
        (self.tmp / ".gitignore").write_text("\n".join(pa.GITIGNORE_LINES) + "\n", encoding="utf-8", newline="\n")
        results = self.by_name()
        for name in ("mail dir", "ledger tracking", "mail twins", "doorbells"):
            self.assertEqual(results[name]["status"], doctor.PASS, results[name])
        self.assertIn("not recorded", results["doorbells"]["detail"])

    def test_tracked_mail_dir_fails(self):
        mail.append_mail(self.root, "p2", {"to": "p6", "kind": "note", "body": "x"})
        _git(self.tmp, "add", "-f", ".agents/mail/p6.jsonl")
        result = self.by_name()["mail dir"]
        self.assertEqual(result["status"], doctor.FAIL)
        self.assertIn("p6.jsonl", result["detail"])
        self.assertTrue(result["fix"])

    def test_missing_twin_fails_and_names_the_id(self):
        mail_id = mail.append_mail(self.root, "p2", {"to": "p6", "kind": "delegate", "body": "x"})
        (self.root / "log" / "p2.jsonl").unlink()
        result = self.by_name()["mail twins"]
        self.assertEqual(result["status"], doctor.FAIL)
        self.assertIn(mail_id, result["detail"])
        mail.append_mail(self.root, "p2", {"to": "p6", "kind": "note", "body": "chatter"})
        self.assertIn(mail_id, self.by_name()["mail twins"]["detail"], "a note never needs a twin")

    def test_ignored_ledger_fails_naming_d10(self):
        (self.tmp / ".gitignore").write_text(".agents/*\n", encoding="utf-8", newline="\n")
        result = self.by_name()["ledger tracking"]
        self.assertEqual(result["status"], doctor.FAIL)
        self.assertIn("D10", result["detail"] + result["fix"])

    def test_doorbell_status_lines_come_from_harness_status(self):
        (self.root / mail.HARNESS_STATUS_FILE).write_text(json.dumps({
            "claude-code": {"version": "2.1.278", "date": "2026-09-19", "status": "verified", "evidence": "ran"},
            "copilot": {"version": None, "date": "2026-09-19", "status": "unsupported", "evidence": "not installed"},
        }), encoding="utf-8", newline="\n")
        result = self.by_name()["doorbells"]
        self.assertEqual(result["status"], doctor.PASS)
        self.assertIn("claude-code: verified (2.1.278, 2026-09-19)", result["detail"])
        self.assertIn("copilot: unsupported", result["detail"])


if __name__ == "__main__":
    unittest.main()
