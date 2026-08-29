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
import shutil
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


class WorktreeLifecycleTests(unittest.TestCase):
    """WT1-WT12. A new session starts in its own worktree, and nothing is left behind.

    The half that actually rots is cleanup, so these concentrate on the fail-safe conditions:
    every one is a HARD STOP that reports rather than removes. A cleanup that deletes on a
    heuristic will eventually delete the tree that mattered, and that single event ends the
    adoption of the whole practice — so 'refuses to delete' is the property under test, not
    'deletes successfully'.

    Real git, real trees: `testing-strategy.md` D4 forbids mocking engine semantics, and
    `unique_commits` in particular carries a spike-proven note about `--all` returning 0 for
    the exact case the guard exists to catch. A mock would have re-introduced that bug.
    """

    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "primary"
        self.repo.mkdir()
        self.root = self.repo / ".agents"
        (self.root / "log").mkdir(parents=True)
        self._git("init", "-q", "-b", "main")
        # CI-ENV: the control supplies its own identity rather than borrowing an ambient one.
        self._git("config", "user.email", "t@example.invalid")
        self._git("config", "user.name", "Test")
        (self.repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "seed")

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=str(self.repo),
                              capture_output=True, text=True, timeout=60)

    def _verdicts(self, cwd=None):
        records, err = self.m.worktree_inventory(self.repo)
        self.assertIsNone(err, err)
        primary = records[0]["path"]
        index = {}
        for r in records:
            if r.get("branch"):
                index[r["branch"]] = index.get(r["branch"], 0) + 1
        out = {}
        for r in records:
            safe, why = self.m.worktree_safety(r, primary, cwd or str(self.base), set(), index)
            out[Path(r["path"]).name] = (safe, why)
        return out

    def _add_tree(self, name="feature-x", branch="feature/x"):
        target = self.base / name
        result = self._git("worktree", "add", "-b", branch, str(target))
        self.assertEqual(0, result.returncode, result.stderr)
        return target

    # -- the hard stops ---------------------------------------------------
    def test_the_primary_checkout_is_never_removable(self):
        self.assertFalse(self._verdicts()["primary"][0])
        self.assertIn("primary", self._verdicts()["primary"][1])

    def test_the_current_working_directory_is_never_removable(self):
        tree = self._add_tree()
        safe, why = self._verdicts(cwd=str(tree))[tree.name]
        self.assertFalse(safe, "deleting the floor you stand on")
        self.assertIn("current working directory", why)

    def test_an_untracked_file_blocks_removal(self):
        """The most dangerous condition: a new file nobody committed exists NOWHERE else."""
        tree = self._add_tree()
        (tree / "only-copy.md").write_text("work that exists nowhere else\n", encoding="utf-8")
        safe, why = self._verdicts()[tree.name]
        self.assertFalse(safe)
        self.assertIn("untracked", why)

    def test_a_modified_file_blocks_removal(self):
        tree = self._add_tree()
        (tree / "seed.txt").write_text("edited\n", encoding="utf-8")
        safe, why = self._verdicts()[tree.name]
        self.assertFalse(safe)

    def test_an_unmerged_commit_blocks_removal(self):
        tree = self._add_tree()
        (tree / "new.txt").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=str(tree), capture_output=True, timeout=60)
        subprocess.run(["git", "-c", "user.email=t@example.invalid", "-c", "user.name=Test",
                        "commit", "-q", "-m", "unmerged"], cwd=str(tree),
                       capture_output=True, timeout=60)
        safe, why = self._verdicts()[tree.name]
        self.assertFalse(safe, "a commit that exists nowhere else is the only copy")
        self.assertIn("nowhere else", why)

    def test_a_live_session_blocks_removal(self):
        tree = self._add_tree()
        records, _ = self.m.worktree_inventory(self.repo)
        key = self.m._worktree_key(str(tree))
        for r in records:
            if self.m._worktree_key(r["path"]) == key:
                safe, why = self.m.worktree_safety(r, records[0]["path"], str(self.base),
                                                   {key}, {})
                self.assertFalse(safe)
                self.assertIn("live session", why)
                return
        self.fail("the added worktree was not in the inventory")

    def test_a_clean_merged_unheld_tree_is_safe(self):
        """The negative control: if nothing is ever safe, the tool is useless and will be
        bypassed — which is worse than deleting too eagerly, because it is silent."""
        tree = self._add_tree()
        safe, why = self._verdicts()[tree.name]
        self.assertTrue(safe, why)

    # -- the command contract ---------------------------------------------
    def test_cleanup_deletes_nothing_without_the_remove_flag(self):
        tree = self._add_tree()
        rc = self.m.cmd_worktree(self.root, self.repo, "cleanup", str(self.base), time.time())
        self.assertEqual(0, rc)
        self.assertTrue(tree.is_dir(), "cleanup must report a plan, never delete by default")

    def test_cleanup_with_remove_deletes_only_the_safe_tree(self):
        safe_tree = self._add_tree("safe-one", "feature/safe")
        held_tree = self._add_tree("held-one", "feature/held")
        (held_tree / "only-copy.md").write_text("nowhere else\n", encoding="utf-8")
        self.m.cmd_worktree(self.root, self.repo, "cleanup", str(self.base), time.time(),
                            remove=True)
        self.assertFalse(safe_tree.is_dir(), "the safe tree should have been reaped")
        self.assertTrue(held_tree.is_dir(), "the held tree must survive --remove")

    def test_cleanup_prunes_stale_metadata(self):
        """WT9: a hand-deleted directory leaves .git/worktrees/<name> and git keeps the name
        reserved, so the next `worktree add` fails describing a state the filesystem does not
        show."""
        tree = self._add_tree("ghost", "feature/ghost")
        shutil.rmtree(tree)          # simulate someone deleting the directory by hand
        self.m.cmd_worktree(self.root, self.repo, "cleanup", str(self.base), time.time(),
                            remove=True)
        records, err = self.m.worktree_inventory(self.repo)
        self.assertIsNone(err, err)
        names = [Path(r["path"]).name for r in records]
        self.assertNotIn("ghost", names, "stale metadata must be pruned")

    def test_new_creates_a_sibling_tree_not_a_nested_one(self):
        """A tree inside the repo would be walked by docs-graph, check-consistency and every
        test that scans the tree."""
        rc = self.m.cmd_worktree(self.root, self.repo, "new", str(self.base), time.time(),
                                 session="s-new", branch="feature/sibling")
        self.assertEqual(0, rc)
        created = [p for p in self.base.iterdir() if p.name.startswith("primary-")]
        self.assertEqual(1, len(created), [p.name for p in self.base.iterdir()])
        self.assertFalse(str(created[0]).startswith(str(self.repo) + os.sep),
                         "the new tree must not be nested inside the primary checkout")

    def test_new_refuses_without_a_name(self):
        rc = self.m.cmd_worktree(self.root, self.repo, "new", str(self.base), time.time())
        self.assertEqual(2, rc, "an unnamed tree is one nobody can ever safely clean up")

    def test_new_registers_the_session_in_the_new_tree(self):
        self.m.cmd_worktree(self.root, self.repo, "new", str(self.base), time.time(),
                            session="s-reg", branch="feature/registered")
        events, errors, _ = self.m.read_events(self.root)
        self.assertEqual([], errors)
        starts = [e for e in events if e.get("kind") == "session-start"
                  and e.get("session") == "s-reg"]
        self.assertEqual(1, len(starts), events)
        self.assertIn("registered", starts[0]["worktree"])


class CollaborationTests(CoordTestCase):
    """Cross-session collaboration mode.

    These tests encode the AI-DE evidence: two sessions were successful only after
    they registered, published a session contract, and claimed files before editing.
    """

    def start_session(self, session, worktree, at=None, agent=None):
        return self.m.append_event(
            self.root,
            {
                "kind": "session-start",
                "session": session,
                "agent": agent or session,
                "wi": "WI-0",
                "path": "-",
                "at": at if at is not None else time.time(),
                "worktree": worktree,
            },
        )

    def test_session_list_reports_active_sessions_and_claims(self):
        now = time.time()
        self.start_session("core", "C:/repo-core", now - 20, agent="claude-code")
        self.start_session("design", "C:/repo-design", now - 10, agent="copilot")
        self.claim("design", "docs/mockups/**", wi="design-surfaces", at=now - 5,
                   agent="copilot")

        sessions, errors, files = self.m.active_sessions(self.root, now)

        self.assertEqual([], errors)
        self.assertEqual(2, len(sessions))
        self.assertEqual(2, files)
        design = next(s for s in sessions if s["session"] == "design")
        self.assertEqual("copilot", design["agent"])
        self.assertEqual("C:/repo-design", design["worktree"])
        self.assertEqual(["docs/mockups/*"], [c["path"] for c in design["claims"]])

    def test_session_end_removes_the_active_session(self):
        now = time.time()
        self.start_session("design", "C:/repo-design", now - 10, agent="copilot")
        self.m.append_event(
            self.root,
            {
                "kind": "session-end",
                "session": "design",
                "agent": "copilot",
                "wi": "WI-0",
                "path": "-",
                "at": now - 5,
                "worktree": "C:/repo-design",
            },
        )

        sessions, errors, _ = self.m.active_sessions(self.root, now)

        self.assertEqual([], errors)
        self.assertEqual([], sessions)

    def test_stale_session_is_not_active(self):
        now = time.time()
        self.start_session("old", "C:/repo-old", now - 120, agent="claude-code")
        self.start_session("fresh", "C:/repo-fresh", now - 10, agent="copilot")

        sessions, _, _ = self.m.active_sessions(self.root, now, stale_seconds=60)

        self.assertEqual(["fresh"], [s["session"] for s in sessions])

    def test_collaboration_check_requires_contract_for_multiple_live_sessions(self):
        now = time.time()
        self.start_session("core", "C:/repo-core", now - 20, agent="claude-code")
        self.start_session("design", "C:/repo-design", now - 10, agent="copilot")

        findings = self.m.collaboration_findings(self.root, self.repo, now)

        self.assertTrue(any(f["code"] == "COORD-COLLAB-NO-CONTRACT" for f in findings))

    def test_collaboration_check_passes_with_contract_for_multiple_live_sessions(self):
        now = time.time()
        self.start_session("core", "C:/repo-core", now - 20, agent="claude-code")
        self.start_session("design", "C:/repo-design", now - 10, agent="copilot")
        contract = self.repo / "docs" / "collaboration" / "session-contracts.md"
        contract.parent.mkdir(parents=True)
        contract.write_text("# Session contract\n", encoding="utf-8")

        findings = self.m.collaboration_findings(self.root, self.repo, now)

        self.assertFalse(
            any(f["code"] == "COORD-COLLAB-NO-CONTRACT" for f in findings),
            findings,
        )

    def run_cli(self, *args, root=None):
        env = dict(os.environ)
        env["COORD_ROOT"] = str(root or self.root)
        env.pop("AGENT_SESSION", None)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(self.repo), env=env, capture_output=True, text=True,
        )

    def test_cli_session_list_json_reports_active_sessions(self):
        now = time.time()
        self.start_session("design", "C:/repo-design", now - 10, agent="copilot")
        self.claim("design", "docs/mockups/*", wi="design-surfaces", at=now - 5,
                   agent="copilot")

        result = self.run_cli("session", "list", "--json")

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("design", payload["sessions"][0]["session"])
        self.assertEqual("copilot", payload["sessions"][0]["agent"])
        self.assertEqual("design-surfaces", payload["sessions"][0]["claims"][0]["wi"])
        self.assertEqual("docs/mockups/*", payload["sessions"][0]["claims"][0]["path"])

    def test_cli_collaborate_check_fails_when_contract_is_missing(self):
        now = time.time()
        self.start_session("core", "C:/repo-core", now - 20, agent="claude-code")
        self.start_session("design", "C:/repo-design", now - 10, agent="copilot")

        result = self.run_cli("collaborate", "check", "--json")

        self.assertEqual(3, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("COORD-COLLAB-NO-CONTRACT", payload["findings"][0]["code"])

    def test_cli_collaborate_check_fails_when_coordination_corpus_is_empty(self):
        empty_root = self.repo / "empty-coord"

        result = self.run_cli("collaborate", "check", "--json", root=empty_root)

        self.assertEqual(3, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("COORD-COLLAB-NOT-CHECKED-EMPTY", payload["findings"][0]["code"])
        self.assertEqual("blocker", payload["findings"][0]["severity"])
        self.assertEqual(0, payload["files_scanned"])
        self.assertFalse(empty_root.exists(), "the check should not create a fake corpus")

    def test_cli_collaborate_check_passes_when_contract_and_claims_exist(self):
        now = time.time()
        self.start_session("core", "C:/repo-core", now - 20, agent="claude-code")
        self.start_session("design", "C:/repo-design", now - 10, agent="copilot")
        self.claim("core", "src/core/*", wi="core-work", at=now - 5, agent="claude-code")
        self.claim("design", "docs/mockups/*", wi="design-work", at=now - 4, agent="copilot")
        contract = self.repo / "docs" / "collaboration" / "session-contracts.md"
        contract.parent.mkdir(parents=True)
        contract.write_text("# Session contract\n", encoding="utf-8")

        result = self.run_cli("collaborate", "check", "--json")

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["contract_exists"])
        self.assertEqual([], payload["findings"])


if __name__ == "__main__":
    unittest.main()
