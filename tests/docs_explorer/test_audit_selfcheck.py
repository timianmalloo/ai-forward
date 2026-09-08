"""FC-1 (spec-agent-focus-controls). `audit-log.py selfcheck` is the bounded, inline, self-applied
session self-assessment: one deterministic pass over a session's substantive turns that reports
goal-state presence gaps and surfaces done_when -> summary review pairs (never a scope verdict).

Seen failing on the pre-fix code: the subcommand does not exist, so the run errors.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "docs" / "ai-forward-pack" / "scripts" / "audit-log.py"


def _entry(**kw):
    return json.dumps(kw, ensure_ascii=False) + "\n"


class SelfcheckTests(unittest.TestCase):
    def _write_log(self, root, entries):
        audit = root / "docs" / "audit"
        audit.mkdir(parents=True, exist_ok=True)
        (audit / "audit-log.jsonl").write_text("".join(entries), encoding="utf-8")

    def _run(self, root, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root / "docs"), "selfcheck", *args],
            capture_output=True, text=True, timeout=30,
        )

    def _fixture(self, root):
        self._write_log(root, [
            _entry(id="al-1", kind="skill", session="S", shortname="turn-a",
                   done_when="X is done", summary="did X"),
            _entry(id="al-2", kind="manual", session="S", shortname="turn-b",
                   summary="did a lot of other stuff"),  # substantive, NO done_when -> gap
            _entry(id="al-3", kind="read", session="S", shortname="trivial-read"),  # not substantive
            _entry(id="al-4", kind="skill", session="OTHER", shortname="other-session",
                   done_when="Y", summary="y"),  # different session
        ])

    def test_reports_presence_gap_and_excludes_trivial_and_other_sessions(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self._fixture(root)
            r = self._run(root, "--session", "S")
            self.assertEqual(r.returncode, 0, r.stderr)
            out = r.stdout
            self.assertIn("turn-b", out, f"the substantive turn missing done_when must be a gap:\n{out}")
            self.assertNotIn("trivial-read", out, "a non-substantive (read) turn must not be reported")
            self.assertNotIn("other-session", out, "a turn from another session must not be reported")

    def test_surfaces_review_pair_without_a_scope_verdict(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self._fixture(root)
            out = self._run(root, "--session", "S").stdout
            self.assertIn("X is done", out, "the done_when of a recorded turn should be surfaced")
            self.assertIn("did X", out, "the summary should be surfaced alongside its done_when")
            # It surfaces the pair for review; it must NOT auto-judge scope drift.
            for verdict in ("PASS", "FAIL", "DRIFTED", "OK - no drift"):
                self.assertNotIn(verdict, out, f"selfcheck must not emit a scope verdict ({verdict})")

    def test_deterministic_and_clean_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            # A session where every substantive turn HAS a goal-state -> clean pass.
            self._write_log(root, [
                _entry(id="al-1", kind="skill", session="S", shortname="a", done_when="a done", summary="a"),
                _entry(id="al-2", kind="manual", session="S", shortname="b", done_when="b done", summary="b"),
            ])
            r1 = self._run(root, "--session", "S")
            r2 = self._run(root, "--session", "S")
            self.assertEqual(r1.returncode, 0, r1.stderr)
            self.assertEqual(r1.stdout, r2.stdout, "selfcheck must be deterministic on identical input")
            self.assertIn("2 substantive", r1.stdout.replace("  ", " "))
            # No gaps -> a clean, explicit all-recorded line.
            self.assertRegex(r1.stdout, r"all .*substantive turns recorded a goal-state")

    def test_json_output_shape(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self._fixture(root)
            r = self._run(root, "--session", "S", "--json")
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["substantive"], 2)  # turn-a + turn-b (not read, not OTHER)
            self.assertEqual([g["shortname"] for g in data["gaps"]], ["turn-b"])
            self.assertEqual(len(data["review"]), 1)
            self.assertEqual(data["review"][0]["done_when"], "X is done")


    def test_gate_fails_on_a_gap_and_passes_when_clean(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self._fixture(root)  # turn-b is a substantive gap
            self.assertEqual(self._run(root, "--session", "S", "--gate").returncode, 1,
                             "--gate must exit non-zero when a substantive turn recorded no goal-state")
            self._write_log(root, [
                _entry(id="al-1", kind="skill", session="S", shortname="a", done_when="a done", tier="T0", summary="a"),
                _entry(id="al-2", kind="manual", session="S", shortname="b", done_when="b done", tier="T1", summary="b"),
            ])
            self.assertEqual(self._run(root, "--session", "S", "--gate").returncode, 0,
                             "--gate must exit 0 when every substantive turn has a goal-state")

    def test_gate_over_fan_out_cap_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self._write_log(root, [
                _entry(id="al-1", kind="skill", session="S", shortname="council", done_when="x", tier="T0",
                       fan_out=0, agent_runs=[{"agent": "one"}], summary="convened a sub-agent at T0 cap 0"),
            ])
            self.assertEqual(self._run(root, "--session", "S", "--gate").returncode, 1,
                             "--gate must fail a turn whose agent_runs exceed its declared fan_out cap")

    def test_gate_since_grandfathers_historical_but_catches_new(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self._write_log(root, [
                _entry(id="al-1", kind="skill", session="S", shortname="old-gap", summary="historical, no done_when"),
            ])
            env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                   "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
            import os as _os
            runenv = {**_os.environ, **env}
            subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=runenv)
            subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=runenv)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True, env=runenv)
            # --gate alone fails on the historical gap; --since HEAD grandfathers it.
            self.assertEqual(self._run(root, "--session", "S", "--gate").returncode, 1)
            self.assertEqual(self._run(root, "--session", "S", "--gate", "--since", "HEAD").returncode, 0,
                             "--since must grandfather entries already present on the ref")
            # A NEW uncommitted gap is caught even with --since HEAD.
            self._write_log(root, [
                _entry(id="al-1", kind="skill", session="S", shortname="old-gap", summary="x"),
                _entry(id="al-2", kind="skill", session="S", shortname="new-gap", summary="new, no done_when"),
            ])
            self.assertEqual(self._run(root, "--session", "S", "--gate", "--since", "HEAD").returncode, 1,
                             "--since must still catch a gap introduced after the ref")


class GateBaselineTests(SelfcheckTests):
    """A forward ratchet with no baseline has nothing to ratchet against.

    `ids_at_ref` states the intended stance in its own docstring -- "A forward ratchet fails
    open on a missing base (returns None), never on a bad current entry" -- but the call site
    did the opposite. When the base could not be read it skipped the filtering entirely and
    gated the WHOLE unfiltered history, so an unresolvable ref turned the ratchet into a
    retroactive audit and failed the build on entries that were explicitly grandfathered.

    That is the shape CI6 warns about -- a gate that fails for a reason unrelated to the
    change is a gate someone deletes -- and it is IO doctrine too: a check that could not run
    must say so rather than degrade to a plausible verdict in either direction.

    Observed red on 2026-09-07: `selfcheck --gate --since <bogus-ref>` exited 1 in a repo
    whose gate passed with a resolvable ref.

    Inherits `_write_log` / `_run` from SelfcheckTests so the fixture shape cannot drift.
    """

    BOGUS = "refs/heads/definitely-not-a-ref"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self._write_log(self.root, [
            _entry(id="al-1", kind="skill", session="S", shortname="old-gap",
                   summary="historical, no done_when"),
        ])
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "base"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, env=env,
                           capture_output=True)

    def test_the_fixture_really_would_fail_without_a_baseline(self):
        """Guards the other two: if the historical gap stopped failing, they would pass
        for the wrong reason."""
        self.assertEqual(self._run(self.root, "--session", "S", "--gate").returncode, 1)

    def test_an_unreadable_base_ref_does_not_fail_the_gate(self):
        result = self._run(self.root, "--session", "S", "--gate", "--since", self.BOGUS)
        self.assertEqual(result.returncode, 0,
                         "an unresolvable base makes every historical entry look new, so "
                         "failing here is a retroactive audit rather than a ratchet")

    def test_an_unreadable_base_ref_says_so_rather_than_passing_silently(self):
        out = self._run(self.root, "--session", "S", "--gate", "--since", self.BOGUS).stdout
        self.assertIn("NOT CHECKED", out,
                      "a check that could not run must say so, not look like a pass")

    def test_a_resolvable_base_still_gates_a_new_entry(self):
        """The regression guard: failing open on a MISSING base must not blind the gate."""
        self._write_log(self.root, [
            _entry(id="al-1", kind="skill", session="S", shortname="old-gap", summary="x"),
            _entry(id="al-2", kind="skill", session="S", shortname="new-gap",
                   summary="new, no done_when"),
        ])
        self.assertEqual(
            self._run(self.root, "--session", "S", "--gate", "--since", "HEAD").returncode, 1)


if __name__ == "__main__":
    unittest.main()
