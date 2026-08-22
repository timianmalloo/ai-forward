"""Tests for coord-core.py — the Phase-1 agent-coordination walking skeleton.

Design: docs/design/coord-core-phase1.md. Test ids below map to its test plan (T1..T15).

Two of these are the point of the exercise and were written to fail first:
  T1  the LOG-A seam — an append onto a file that does not end in a newline fuses two
      records and loses BOTH, with exit code 0. The recorded instance is audit-log.py.
  T3  the empty-corpus rule (architecture R4) — a check that scanned nothing must not
      report "free". Written because this architecture's own allocator spike printed
      "COLLISION-FREE" over zero identifiers.
"""
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
SCRIPT = REPO / "pack" / "scripts" / "coord-core.py"


def load_module():
    spec = importlib.util.spec_from_file_location("coord_core", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CoordTestCase(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.root = self.repo / ".agents"
        (self.root / "log").mkdir(parents=True)
        self.addCleanup(self.tmp.cleanup)

    # -- helpers ---------------------------------------------------------
    def claim(self, session, path, wi="WI-1", at=None, ttl=300, agent=None, seq=None):
        return self.m.append_event(
            self.root,
            self.m.make_event(
                kind="claim", session=session, agent=agent or session, wi=wi,
                path=path, ttl=ttl, at=at if at is not None else time.time(), seq=seq,
            ),
        )

    def release(self, session, path, wi="WI-1", at=None):
        return self.m.append_event(
            self.root,
            self.m.make_event(
                kind="release", session=session, agent=session, wi=wi,
                path=path, at=at if at is not None else time.time(),
            ),
        )

    def check(self, path, me, now=None):
        return self.m.check(self.root, path, me, now if now is not None else time.time())

    def logfile(self, session):
        return self.root / "log" / f"{session}.jsonl"


class RecordWriterTests(CoordTestCase):
    def test_T1_append_after_missing_trailing_newline_does_not_fuse(self):
        """T1 / LOG-A. The failure this must make impossible to express.

        A merge resolution, a hand edit, or a writer that joined with "".join() leaves the
        file without a final newline. The next append then lands directly onto the previous
        record, fusing two well-formed objects into one unparseable line -- and BOTH are lost,
        not just the new one. The write succeeds and the exit code is 0.
        """
        self.claim("s1", "src/a/**")
        path = self.logfile("s1")

        # Reproduce the state something else leaves behind: no trailing newline.
        # Strip CR too -- on Windows a newline-translating writer leaves \r\n, and stripping
        # only \n leaves a \r that still terminates a line, masking the fusion entirely.
        raw = path.read_bytes()
        self.assertTrue(raw.endswith(b"\n"), "precondition: the writer terminated its own record")
        path.write_bytes(raw.rstrip(b"\r\n"))

        self.claim("s1", "src/b/**")

        lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(lines), 2, "the two records fused into one line -- both are lost")
        for i, line in enumerate(lines):
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                self.fail(f"record {i} is unparseable after the append: {exc}")

    def test_T16_record_is_lf_only_on_every_platform(self):
        """T16 / CTRL-PORT. The record is git-tracked and .gitattributes mandates
        `*.jsonl text eol=lf`. os.open() without O_BINARY translates \\n to \\r\\n on Windows,
        which makes the committed bytes platform-dependent -- and, found the hard way, masks
        the LOG-A test above, because a stray \\r still terminates a line.
        """
        self.claim("s1", "src/a/**")
        raw = self.logfile("s1").read_bytes()
        self.assertNotIn(b"\r", raw, "the record writer is translating newlines")

    def test_T10_concurrent_appends_do_not_interleave(self):
        """T10. Regression for spike S3: one write() per record is atomic under O_APPEND."""
        worker = self.repo / "w.py"
        worker.write_text(
            "import importlib.util,sys,time\n"
            f"spec=importlib.util.spec_from_file_location('c', r'{SCRIPT}')\n"
            "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
            "from pathlib import Path\n"
            "root=Path(sys.argv[1]); tag=sys.argv[2]\n"
            "for i in range(60):\n"
            "    m.append_event(root, m.make_event(kind='claim', session=tag, agent=tag,\n"
            "        wi='WI-'+str(i), path='src/'+tag+'/'+str(i)+'/**', ttl=300, at=time.time()))\n",
            encoding="utf-8",
        )
        procs = [
            subprocess.Popen([sys.executable, str(worker), str(self.root), f"w{i}"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for i in range(4)
        ]
        for p in procs:
            _, err = p.communicate()
            self.assertEqual(p.returncode, 0, err.decode())

        events, errors, files = self.m.read_events(self.root)
        self.assertEqual(errors, [], "a concurrent append produced an unparseable line")
        self.assertEqual(len(events), 240)
        self.assertEqual(files, 4)

    def test_T13_truncated_final_record_is_detected_not_silently_dropped(self):
        """T13 / DM11. Attempt the forbidden thing -- rewrite the file -- and assert the
        reader refuses the result rather than skipping the damaged line."""
        self.claim("s1", "src/a/**")
        self.claim("s1", "src/b/**")
        path = self.logfile("s1")
        text = path.read_text(encoding="utf-8")
        path.write_text(text[: len(text) - 25], encoding="utf-8")  # truncate mid-record

        events, errors, _ = self.m.read_events(self.root)
        self.assertTrue(errors, "a truncated record was silently dropped")
        self.assertIn("s1.jsonl", errors[0])

        decision = self.check("src/a/x.cs", "s2")
        self.assertEqual(decision["decision"], "not_checked")


class FoldTests(CoordTestCase):
    def test_T2_fold_is_idempotent_under_replay(self):
        """T2 / NFR-R1. Replaying the record twice must yield identical state."""
        now = time.time()
        self.claim("s1", "src/a/**", at=now)
        self.claim("s2", "tests/**", at=now)
        self.release("s2", "tests/**", at=now + 1)

        events, errors, _ = self.m.read_events(self.root)
        self.assertEqual(errors, [])
        first = self.m.fold(events, now + 2)
        second = self.m.fold(events, now + 2)
        self.assertEqual(first, second)
        self.assertEqual(self.m.fold(events + events, now + 2), first,
                         "replaying the same events twice changed the folded state")

    def test_T5_expired_lease_does_not_refuse(self):
        now = time.time()
        self.claim("s1", "src/**", at=now, ttl=60)
        self.assertEqual(self.check("src/a.cs", "s2", now=now + 30)["decision"], "deny")
        self.assertEqual(self.check("src/a.cs", "s2", now=now + 61)["decision"], "allow")

    def test_T15_duplicate_seq_is_idempotent(self):
        """T15 / F9. A retried tool call must not take a second lease."""
        now = time.time()
        self.claim("s1", "src/**", at=now, seq=1)
        self.claim("s1", "src/**", at=now, seq=1)
        events, _, _ = self.m.read_events(self.root)
        self.assertEqual(len(events), 2, "both writes landed (expected -- the file is append-only)")
        self.assertEqual(len(self.m.fold(events, now)), 1,
                         "a replayed event produced a second lease")

    def test_overlap_is_boundary_aware(self):
        o = self.m.overlaps
        self.assertTrue(o("src/**", "src/Ingest/Reader.cs"))
        self.assertTrue(o("src/Ingest/Reader.cs", "src/**"))
        self.assertFalse(o("src/A/**", "src/B/**"))
        self.assertFalse(o("src/Foo/**", "src/FooBar/**"),
                         "a segment prefix must not be read as a path prefix")


class CheckTests(CoordTestCase):
    def test_T3_empty_record_is_not_checked_not_clean(self):
        """T3 / architecture R4. A control that scanned nothing has not reported clean.

        Written because this architecture's own allocator spike printed
        "COLLISION-FREE WITHOUT COORDINATION" over zero identifiers.
        """
        decision = self.check("src/a.cs", "s1")
        self.assertEqual(decision["decision"], "not_checked",
                         "a scan of zero files reported the path free")
        self.assertEqual(decision["files_scanned"], 0)
        self.assertIn("0 files", decision["reason"])

    def test_T4_missing_identity_is_not_checked(self):
        self.claim("s1", "src/**")
        decision = self.check("src/a.cs", None)
        self.assertEqual(decision["decision"], "not_checked")
        self.assertEqual(decision["code"], "COORD-NOT-CHECKED-IDENTITY")
        self.assertIn("AGENT_SESSION", decision["reason"])

    def test_T7_overlapping_claim_by_other_session_is_refused(self):
        now = time.time()
        self.claim("opus", "src/**", wi="WI-142", at=now)
        decision = self.check("src/Ingest/Reader.cs", "copilot", now=now + 5)
        self.assertEqual(decision["decision"], "deny")
        self.assertEqual(decision["holder"], "opus")
        self.assertEqual(decision["wi"], "WI-142")
        self.assertEqual(decision["code"], "COORD-REFUSED")

    def test_T8_own_lease_and_free_path_are_allowed(self):
        now = time.time()
        self.claim("opus", "src/**", at=now)
        self.assertEqual(self.check("src/a.cs", "opus", now=now)["decision"], "allow")
        self.assertEqual(self.check("tests/a.cs", "copilot", now=now)["decision"], "allow")

    def test_T9_release_frees_the_path(self):
        now = time.time()
        self.claim("opus", "src/**", at=now)
        self.assertEqual(self.check("src/a.cs", "copilot", now=now)["decision"], "deny")
        self.release("opus", "src/**", at=now + 1)
        self.assertEqual(self.check("src/a.cs", "copilot", now=now + 2)["decision"], "allow")

    def test_T6_malformed_line_is_not_checked_and_names_the_line(self):
        self.claim("s1", "src/**")
        with open(self.logfile("s1"), "a", encoding="utf-8") as fh:
            fh.write("{not json\n")
        decision = self.check("src/a.cs", "s2")
        self.assertEqual(decision["decision"], "not_checked")
        self.assertEqual(decision["code"], "COORD-NOT-CHECKED-RECORD")
        self.assertIn("s1.jsonl:2", decision["reason"])


class BoundaryTests(CoordTestCase):
    def test_T11_claim_over_coordination_root_is_refused(self):
        """T11 / F8. A claim over the record itself would let one session lock the substrate."""
        with self.assertRaises(self.m.CoordError) as ctx:
            self.m.make_event(kind="claim", session="s1", agent="s1", wi="WI-1",
                              path=".agents/**", ttl=300, at=time.time())
        self.assertEqual(ctx.exception.code, "COORD-CLAIM-SELF")

    def test_T12_coord_root_outside_repo_is_not_checked(self):
        """T12 / A1 negative security. COORD_ROOT is attacker-controllable input that
        selects which file becomes trusted state (STRIDE B1, elevation)."""
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(outside, ignore_errors=True))
        root, err = self.m.resolve_root(self.repo, str(outside))
        self.assertIsNone(root)
        self.assertEqual(err["code"], "COORD-NOT-CHECKED-ROOT")

        root, err = self.m.resolve_root(self.repo, str(self.root))
        self.assertIsNone(err)
        self.assertEqual(root, self.root.resolve())


class WorktreeTests(unittest.TestCase):
    """T17. The Phase-1 exit criterion is that two sessions IN TWO WORKTREES see each
    other's leases. Found by running the demo: the default root was cwd/.agents, so every
    worktree got its own private record and neither could ever see the other. The record is
    per REPOSITORY, not per checkout -- git rev-parse --git-common-dir is what says so.
    """

    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.primary = self.base / "repo"
        self.primary.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "t@t")
        self._git("config", "user.name", "t")
        (self.primary / "f.txt").write_text("x", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "base")
        self.wt = self.base / "wt-a"
        self._git("worktree", "add", "-q", str(self.wt), "-b", "agent/a")

    def _git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=str(cwd or self.primary),
                              capture_output=True, text=True, check=True)

    def _run(self, cwd, session, *args):
        env = dict(os.environ)
        env.pop("COORD_ROOT", None)          # the point: NO explicit root
        env["AGENT_SESSION"] = session
        env["AGENT_NAME"] = session
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              cwd=str(cwd), env=env, capture_output=True, text=True)

    def test_T17_worktrees_share_one_record_without_configuration(self):
        granted = self._run(self.primary, "opus", "claim", "--wi", "WI-142",
                            "--path", "src/Ingest/**")
        self.assertEqual(granted.returncode, 0, granted.stderr)

        seen = self._run(self.wt, "copilot", "check", "src/Ingest/Reader.cs")
        self.assertEqual(seen.returncode, 3,
                         "a session in a linked worktree could not see the other's lease\n"
                         + seen.stdout + seen.stderr)
        self.assertIn("opus", seen.stdout)

    def test_T17b_repo_root_is_the_primary_checkout_not_the_worktree(self):
        root_primary, err = self.m.resolve_root(self.primary, None)
        self.assertIsNone(err)
        root_worktree, err = self.m.resolve_root(self.wt, None)
        self.assertIsNone(err)
        self.assertEqual(root_primary, root_worktree)


class RenderTests(CoordTestCase):
    def test_T14_refusal_names_holder_reason_and_remedy(self):
        """T14 / UX-1. Four labelled lines, fixed order: what - who - why - what to do."""
        now = time.time()
        self.claim("opus", "src/**", wi="WI-142", at=now)
        decision = self.check("src/Ingest/Reader.cs", "copilot", now=now + 5)
        text = self.m.render(decision)
        lines = text.splitlines()
        self.assertEqual(len(lines), 4)
        self.assertTrue(lines[0].startswith("REFUSED"))
        self.assertIn("src/Ingest/Reader.cs", lines[0])
        self.assertIn("held by", lines[1])
        self.assertIn("opus", lines[1])
        self.assertIn("WI-142", lines[1])
        self.assertIn("because", lines[2])
        self.assertIn("remedy", lines[3])

    def test_not_checked_is_visually_distinct_from_allow(self):
        """A11y + machine-readability are the same requirement: no colour is load-bearing."""
        self.claim("s1", "src/**")
        nc = self.m.render(self.check("src/a.cs", None))
        self.assertIn("NOT CHECKED", nc)
        self.assertEqual(self.m.render(self.check("tests/a.cs", "s1")), "")


class CliTests(CoordTestCase):
    def run_cli(self, *args, session="s1", agent=None, root=None):
        env = dict(os.environ)
        env["COORD_ROOT"] = str(root or self.root)
        env.pop("AGENT_SESSION", None)
        if session:
            env["AGENT_SESSION"] = session
        env["AGENT_NAME"] = agent or session or "anon"
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(self.repo), env=env, capture_output=True, text=True,
        )

    def test_exit_codes_are_the_contract(self):
        self.assertEqual(self.run_cli("claim", "--wi", "WI-1", "--path", "src/**").returncode, 0)
        self.assertEqual(self.run_cli("check", "src/a.cs", session="s1").returncode, 0)
        r = self.run_cli("check", "src/a.cs", session="s2")
        self.assertEqual(r.returncode, 3)
        self.assertIn("REFUSED", r.stdout)
        self.assertEqual(self.run_cli("check", "src/a.cs", session=None).returncode, 4)

    def test_check_json_reports_what_it_scanned(self):
        self.run_cli("claim", "--wi", "WI-1", "--path", "src/**")
        r = self.run_cli("check", "src/a.cs", "--json", session="s2")
        payload = json.loads(r.stdout)
        self.assertEqual(payload["decision"], "deny")
        self.assertEqual(payload["files_scanned"], 1)
        self.assertGreaterEqual(payload["events_scanned"], 1)

    def test_tail_replays_refusals(self):
        """A refusal is an appended event, not only a string returned to one agent --
        otherwise the most interesting thing the system does would be invisible."""
        self.run_cli("claim", "--wi", "WI-1", "--path", "src/**")
        self.run_cli("check", "src/a.cs", session="s2")
        out = self.run_cli("tail", session="s2").stdout
        self.assertIn("refused", out)
        self.assertIn("s2", out)

    def test_release_then_claim_succeeds(self):
        self.run_cli("claim", "--wi", "WI-1", "--path", "src/**", session="s1")
        self.assertEqual(self.run_cli("claim", "--wi", "WI-2", "--path", "src/a.cs",
                                      session="s2").returncode, 3)
        self.run_cli("release", "--path", "src/**", session="s1")
        self.assertEqual(self.run_cli("claim", "--wi", "WI-2", "--path", "src/a.cs",
                                      session="s2").returncode, 0)


if __name__ == "__main__":
    unittest.main()
