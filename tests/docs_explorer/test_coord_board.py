"""P6 — the board (spec-board / design-board).

A read model over the message store, never a store: every row is backed by an inbox line or a
ledger twin, an empty corpus says NOT CHECKED, --follow stops at its cap and says so, and a
human post goes only through the message layer's single writer (a fixture here, P4's
append_mail() at the join). All temp repos; the board under test is the pack SOURCE
(pack/scripts) because sync-pack is the coordinator's step.
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
BOARD = REPO / "pack" / "scripts" / "coord-board.py"
AUDIT = REPO / "pack" / "scripts" / "audit-log.py"
TEMPLATE = REPO / "pack" / "templates" / "audit-explorer.template.html"

FIXTURE_WRITER = textwrap.dedent('''
    """Fixture writer: the same signature and schema as P4's append_mail(root, session, entry)."""
    import json, os, pathlib

    REQUIRED = ("id", "ts", "from", "to", "kind", "body", "ref", "ack")

    def append_mail(root, session, entry):
        missing = [k for k in REQUIRED if k not in entry]
        if missing:
            raise ValueError("entry missing " + ",".join(missing))
        mail = pathlib.Path(root) / "mail"
        mail.mkdir(parents=True, exist_ok=True)
        with open(mail / (session + ".jsonl"), "a", encoding="utf-8", newline="\\n") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\\n")
        calls = pathlib.Path(root) / "writer-calls.jsonl"
        with open(calls, "a", encoding="utf-8", newline="\\n") as fh:
            fh.write(json.dumps({"session": session, "entry": entry}, sort_keys=True) + "\\n")
        return entry
''')


def _mail(i, frm, to, kind, ref=None, body="hello", ts="2026-09-19T18:00:00Z", ack=None):
    return {"id": i, "ts": ts, "from": frm, "to": to, "kind": kind, "body": body,
            "ref": ref, "ack": ack}


def _twin(i, frm, to, kind, ref=None, at=1789000000.0, session="p4-mail"):
    return {"type": "mail", "mail_id": i, "kind": kind, "from": frm, "to": to, "ref": ref,
            "at": at, "session": session, "seq": 1}


def _write_lines(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write((row if isinstance(row, str) else json.dumps(row)) + "\n")


class _Repo:
    """A temp git-less repo root with a .agents directory; the board takes --root explicitly."""

    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix="board-")
        self.root = pathlib.Path(self.dir) / ".agents"
        self.root.mkdir()
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run(self, *args, timeout=30):
        return subprocess.run([sys.executable, str(BOARD), "--root", str(self.root), *args],
                              capture_output=True, text=True, encoding="utf-8", timeout=timeout,
                              cwd=self.dir)


class BoardReadTests(unittest.TestCase):
    def test_union_and_dedup_by_id(self):
        with _Repo() as repo:
            _write_lines(repo.root / "mail" / "b.jsonl", [_mail("m1", "a", "b", "delegate", ref="docs/x.md")])
            _write_lines(repo.root / "mail" / "a.jsonl", [_mail("m2", "b", "a", "note")])
            _write_lines(repo.root / "log" / "a.jsonl", [_twin("m1", "a", "b", "delegate", ref="docs/x.md")])
            result = repo.run("board", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            rows = {r["id"]: r for r in payload["rows"]}
            self.assertEqual(set(rows), {"m1", "m2"}, "one row per mail id, union of both sources")
            self.assertEqual(rows["m1"]["source"], "both")
            self.assertEqual(rows["m2"]["source"], "inbox")
            self.assertEqual(rows["m1"]["body"], "hello")
            # A row with no store line behind it is impossible: every emitted id was read from a file.
            store_ids = set()
            for f in list((repo.root / "mail").glob("*.jsonl")) + list((repo.root / "log").glob("*.jsonl")):
                for line in f.read_text(encoding="utf-8").splitlines():
                    obj = json.loads(line)
                    store_ids.add(obj.get("id") or obj.get("mail_id"))
            self.assertTrue(set(rows) <= store_ids)

    def test_ledger_only_twin_shows_not_on_this_machine(self):
        with _Repo() as repo:
            _write_lines(repo.root / "log" / "p4.jsonl", [_twin("m3", "p4-mail", "coordinator", "blocked", ref="DR-3")])
            result = repo.run("board")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("(not on this machine)", result.stdout)
            self.assertIn("p4-mail → coordinator", result.stdout)
            payload = json.loads(repo.run("board", "--json").stdout)
            self.assertEqual(payload["rows"][0]["source"], "ledger")

    def test_ack_line_marks_row_acked_with_a_word(self):
        with _Repo() as repo:
            _write_lines(repo.root / "mail" / "b.jsonl", [
                _mail("m1", "a", "b", "delegate"),
                _mail("m5", "a", "b", "kick", ts="2026-09-19T18:01:00Z"),
            ])
            _write_lines(repo.root / "mail" / "a.jsonl", [
                _mail("m4", "b", "a", "ack", ref="m1", body="", ts="2026-09-19T18:02:00Z"),
            ])
            result = repo.run("board")
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = [ln for ln in result.stdout.splitlines() if ln.startswith("2026-")]
            m1 = next(ln for ln in lines if " m1 " in ln or ln.endswith("m1"))
            m5 = next(ln for ln in lines if " m5 " in ln or ln.endswith("m5"))
            self.assertIn("✓ acked", m1)
            self.assertIn("- unacked", m5)
            payload = json.loads(repo.run("board", "--json").stdout)
            rows = {r["id"]: r for r in payload["rows"]}
            self.assertTrue(rows["m1"]["acked"])
            self.assertFalse(rows["m5"]["acked"])

    def test_empty_corpus_is_not_checked_exit_0(self):
        with _Repo() as repo:
            result = repo.run("board")
            self.assertEqual(result.returncode, 0, result.stderr)
            # the board prints the RESOLVED root (macOS: /var -> /private/var), as coord-core does
            self.assertIn("NOT CHECKED — no inbox or ledger mail found under " + str(repo.root.resolve()), result.stdout)
            payload = json.loads(repo.run("board", "--json").stdout)
            self.assertEqual(payload["status"], "not-checked")
            self.assertEqual(payload["rows"], [])

    def test_unreadable_line_is_reported_not_hidden(self):
        with _Repo() as repo:
            _write_lines(repo.root / "mail" / "b.jsonl", [_mail("m1", "a", "b", "delegate"), "{not json"])
            result = repo.run("board")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("m1", result.stdout)
            self.assertIn("NOT CHECKED — ", result.stderr)
            self.assertIn("b.jsonl:2 unreadable", result.stderr)

    def test_board_is_a_pure_fold(self):
        with _Repo() as repo:
            _write_lines(repo.root / "mail" / "b.jsonl", [_mail("m1", "a", "b", "delegate")])
            _write_lines(repo.root / "log" / "a.jsonl", [_twin("m1", "a", "b", "delegate")])
            first = json.loads(repo.run("board", "--json").stdout)["rows"]
            second = json.loads(repo.run("board", "--json").stdout)["rows"]
            for row in first + second:
                row.pop("age_seconds", None)   # wall-clock; everything else must be equal
            self.assertEqual(first, second)

    def test_session_and_since_filters(self):
        with _Repo() as repo:
            _write_lines(repo.root / "mail" / "b.jsonl", [
                _mail("m1", "a", "b", "delegate", ts="2026-09-19T18:00:00Z"),
                _mail("m2", "c", "*", "note", ts="2026-09-19T18:01:00Z"),
                _mail("m3", "c", "d", "note", ts="2026-09-19T18:02:00Z"),
            ])
            rows = json.loads(repo.run("board", "--json", "--session", "b").stdout)["rows"]
            self.assertEqual([r["id"] for r in rows], ["m1", "m2"])
            rows = json.loads(repo.run("board", "--json", "--since", "m1").stdout)["rows"]
            self.assertEqual([r["id"] for r in rows], ["m2", "m3"])

    def test_follow_stops_at_max_polls_and_says_so(self):
        with _Repo() as repo:
            _write_lines(repo.root / "mail" / "b.jsonl", [_mail("m1", "a", "b", "delegate")])
            result = repo.run("board", "--follow", "--max-polls", "2", "--interval", "0.01")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("m1"), 1, "a row is printed once across polls")
            self.assertTrue(result.stdout.rstrip().endswith("stopped: --max-polls 2 reached"), result.stdout)

    def test_root_outside_repository_is_refused(self):
        with _Repo() as repo:
            outside = tempfile.mkdtemp(prefix="outside-")
            try:
                result = subprocess.run([sys.executable, str(BOARD), "--root", outside, "board"],
                                        capture_output=True, text=True, encoding="utf-8",
                                        timeout=30, cwd=repo.dir)
                self.assertEqual(result.returncode, 2)
                self.assertIn("COORD-NOT-CHECKED-ROOT", result.stderr)
            finally:
                shutil.rmtree(outside, ignore_errors=True)


class BoardPostTests(unittest.TestCase):
    def _writer(self, repo):
        path = pathlib.Path(repo.dir) / "fixture_mail.py"
        path.write_text(FIXTURE_WRITER, encoding="utf-8")
        return str(path)

    def test_post_goes_through_the_writer_fixture(self):
        with _Repo() as repo:
            writer = self._writer(repo)
            result = repo.run("board", "post", "--to", "p4-mail", "use the fixture writer until the join",
                              "--writer", writer, "--from", "human")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("posted ", result.stdout)
            calls = [json.loads(ln) for ln in (repo.root / "writer-calls.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(calls), 1)
            # The writer's `session` is the SENDER (P4: append_mail(root, session, entry)); the
            # recipient travels inside the entry. CI on Windows caught the inversion (EINVAL on `*`).
            self.assertEqual(calls[0]["session"], "human")
            entry = calls[0]["entry"]
            self.assertEqual(entry["to"], "p4-mail")
            self.assertEqual(set(entry), {"id", "ts", "from", "to", "kind", "body", "ref", "ack"})
            self.assertEqual(entry["kind"], "note")
            self.assertEqual(entry["to"], "p4-mail")
            self.assertEqual(entry["from"], "human")
            self.assertIsNone(entry["ref"])
            self.assertIsNone(entry["ack"])
            self.assertRegex(entry["id"], r"^[0-9A-HJKMNP-TV-Z]{26}$")
            self.assertRegex(entry["ts"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
            # the posted note is now a board row, read back through the same fold
            rows = json.loads(repo.run("board", "--json").stdout)["rows"]
            self.assertEqual([r["id"] for r in rows], [entry["id"]])

    def test_post_ruling_carries_ref_and_requires_it(self):
        with _Repo() as repo:
            writer = self._writer(repo)
            refused = repo.run("board", "post", "--to", "*", "x", "--kind", "ruling", "--writer", writer)
            self.assertEqual(refused.returncode, 2)
            self.assertIn("--ref", refused.stderr)
            ok = repo.run("board", "post", "--to", "*", "ruled", "--kind", "ruling", "--ref", "DR-3", "--writer", writer)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            call = json.loads((repo.root / "writer-calls.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(call["entry"]["kind"], "ruling")
            self.assertEqual(call["entry"]["ref"], "DR-3")

    def test_post_without_writer_is_refused(self):
        with _Repo() as repo:
            result = repo.run("board", "post", "--to", "a", "x", "--writer", os.path.join(repo.dir, "missing.py"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("message layer", result.stderr)
            self.assertIn("--writer", result.stderr)
            self.assertFalse((repo.root / "mail").exists(), "a refused post writes nothing")

    def test_post_body_bound_and_kind_validated(self):
        with _Repo() as repo:
            writer = self._writer(repo)
            too_long = repo.run("board", "post", "--to", "a", "x" * 4097, "--writer", writer)
            self.assertEqual(too_long.returncode, 2)
            self.assertIn("4096", too_long.stderr)
            bad_kind = repo.run("board", "post", "--to", "a", "x", "--kind", "delegate", "--writer", writer)
            self.assertEqual(bad_kind.returncode, 2)

    def test_post_never_opens_a_mail_file(self):
        source = BOARD.read_text(encoding="utf-8")
        appends = re.findall(r'open\([^)]*["\']a[bt+]?["\']', source)
        self.assertEqual(appends, [], "the board never appends to a JSONL itself (single-writer rule)")
        self.assertNotIn("os.O_APPEND", source)
        self.assertIn("append_mail", source)


class RenderMessagesTests(unittest.TestCase):
    def _render(self, directory):
        docs_root = pathlib.Path(directory) / "docs"
        (docs_root / "audit").mkdir(parents=True)
        result = subprocess.run([sys.executable, str(AUDIT), "--root", str(docs_root), "--project",
                                 "Board Test", "render"], cwd=directory, capture_output=True,
                                text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        data_js = (docs_root / "audit" / "audit-data.js").read_text(encoding="utf-8")
        payload = json.loads(data_js.split("window.AUDIT_DATA = ", 1)[1].rstrip().rstrip(";").replace("<\\/", "</"))
        return payload, (docs_root / "audit" / "index.html").read_text(encoding="utf-8")

    def test_render_emits_messages_without_bodies(self):
        with tempfile.TemporaryDirectory() as directory:
            twin = _twin("m9", "p4-mail", "coordinator", "blocked", ref="DR-3")
            twin["body"] = "a body that must never reach the page"
            _write_lines(pathlib.Path(directory) / ".agents" / "log" / "p4-mail.jsonl",
                         [{"type": "lease", "session": "p4-mail", "at": 1.0}, twin])
            payload, _ = self._render(directory)
            self.assertIn("messages", payload)
            self.assertEqual(len(payload["messages"]), 1)
            row = payload["messages"][0]
            self.assertEqual(row["id"], "m9")
            self.assertEqual(row["kind"], "blocked")
            self.assertEqual(row["from"], "p4-mail")
            self.assertEqual(row["to"], "coordinator")
            self.assertEqual(row["ref"], "DR-3")
            self.assertEqual(row["session"], "p4-mail")
            self.assertTrue(row["ts"].endswith("Z"))
            self.assertNotIn("body", row)

    def test_render_without_a_ledger_emits_an_empty_list(self):
        with tempfile.TemporaryDirectory() as directory:
            payload, _ = self._render(directory)
            self.assertEqual(payload["messages"], [])

    def test_template_has_messages_view(self):
        html = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn('"Messages"', html)
        self.assertIn("NOT CHECKED — nothing recorded", html)
        self.assertIn("coord board", html)
        self.assertIn("DATA.messages", html)
        self.assertIn('setAttribute("scope","col")', html)   # table semantics are set at runtime
        self.assertIn("not recorded here", html)
        self.assertIn("audit-kind", html)
        # no new colours: every colour literal in the stylesheet already existed in the token block
        style = re.search(r"<style>(.*?)</style>", html, flags=re.S).group(1)
        literals = set(re.findall(r"#[0-9a-fA-F]{3,8}\b", style.split("*{box-sizing", 1)[1]))
        self.assertEqual(literals, set(), "rules after the token block use var(--cp-*) only")

    def test_template_script_parses(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed: the page script's syntax check runs in CI")
        html = TEMPLATE.read_text(encoding="utf-8")
        script = html.rsplit("<script>", 1)[1].split("</script>", 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "page.js"
            path.write_text(script, encoding="utf-8", newline="\n")
            result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True,
                                    encoding="utf-8", timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
