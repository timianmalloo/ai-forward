"""Tests for coord-core.py Phase 3 — the artifact-class registry and the derived merge driver.

Design: docs/design/coord-federation-phase3.md (test plan Q6..Q14).

Q7 leads, and is written to fail first. Spike S12b established the hazard: a merge driver
that exits non-zero leaves the file UNMERGED, carrying OURS content, with NO conflict
markers. It looks clean. `git add .` then commits ours and silently discards theirs. So the
driver must never exit non-zero -- on any internal failure it writes conventional conflict
markers itself, and the failure becomes visible in the file rather than hidden in the index.

Q11 is the highest-severity case in the phase: a registry that marks a source tree `derived`
would authorise a merge to overwrite authored work.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "pack" / "scripts" / "coord-core.py"

CONFLICT_START = "<" * 7
CONFLICT_MID = "=" * 7
CONFLICT_END = ">" * 7


def load_module():
    spec = importlib.util.spec_from_file_location("coord_core", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DerivedCase(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "r"
        self.repo.mkdir(parents=True)
        self.git("init", "-q")
        self.git("config", "user.email", "t@t")
        self.git("config", "user.name", "t")
        self.root = self.repo / ".agents"
        self.root.mkdir()

    def git(self, *args, check=True, cwd=None):
        return subprocess.run(["git", *args], cwd=str(cwd or self.repo), check=check,
                              capture_output=True, text=True)

    def registry(self, text):
        (self.root / "artifacts.yml").write_text(text, encoding="utf-8", newline="\n")

    def write(self, rel, body):
        target = self.repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8", newline="\n")
        return target

    def run_cli(self, *args, session="s1"):
        env = dict(os.environ)
        env.pop("COORD_ROOT", None)
        env["AGENT_SESSION"] = session
        env["AGENT_NAME"] = session
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(self.repo),
                              env=env, capture_output=True, text=True)


# ---------------------------------------------------------------- the driver

class MergeDriverTests(DerivedCase):
    def _merge_inputs(self, ours="ours\n", base="base\n", theirs="theirs\n"):
        a = self.write("tmp_A", ours)      # %A - the result file git reads back
        o = self.write("tmp_O", base)      # %O - the merge base
        b = self.write("tmp_B", theirs)    # %B - theirs
        return a, o, b

    def test_Q7_driver_writes_conflict_markers_and_exits_zero_when_it_cannot_resolve(self):
        """Q7 / H4 / S12b. THE case that can silently discard someone's work.

        A driver exiting non-zero leaves an unmerged file with OURS content and no markers.
        It looks clean; `git add .` commits ours and loses theirs. So whenever the driver
        cannot resolve safely it writes the markers itself and exits 0 -- the failure
        becomes visible in the file, where a human and `git diff --check` both see it.

        Here the registry is unparseable, so nothing can be classified.
        """
        a, o, b = self._merge_inputs()
        (self.root / "artifacts.yml").write_text("docs/gen.txt: sideways\n",
                                                 encoding="utf-8", newline="\n")

        rc = self.m.cmd_merge_derived(self.root, self.repo, str(a), str(o), str(b),
                                      "docs/gen.txt")

        self.assertEqual(rc, 0, "a non-zero exit leaves a clean-looking unmerged file")
        content = a.read_text(encoding="utf-8")
        self.assertIn(CONFLICT_START, content, "could not resolve, yet wrote no marker")
        self.assertIn(CONFLICT_MID, content)
        self.assertIn(CONFLICT_END, content)
        self.assertIn("ours", content)
        self.assertIn("theirs", content, "theirs was discarded rather than surfaced")

    def test_Q7b_a_derived_path_resolves_to_ours_and_records_regen_owed(self):
        """The corrected contract: resolve now, regenerate after the merge completes."""
        a, o, b = self._merge_inputs()
        self.registry("docs/gen.txt: derived {} -c \"pass\"\n".format(sys.executable))
        rc = self.m.cmd_merge_derived(self.root, self.repo, str(a), str(o), str(b),
                                      "docs/gen.txt")
        self.assertEqual(rc, 0)
        content = a.read_text(encoding="utf-8")
        self.assertNotIn(CONFLICT_START, content, "a derived path must not conflict")
        self.assertEqual(content, "ours\n", "resolution takes ours, byte for byte")
        self.assertIn("docs/gen.txt", self.m.regen_owed(self.root),
                      "the regeneration this defers was never recorded as owed")

    def test_Q8_driver_touches_only_the_temp_result_file(self):
        """Q8 / A1 / STRIDE B8. %P is identity, never a write target."""
        a, o, b = self._merge_inputs()
        real = self.write("docs/gen.txt", "THE REAL FILE MUST NOT BE TOUCHED\n")
        before = {p: p.read_bytes() for p in (o, b, real)}
        self.registry("docs/gen.txt: derived {} -c \"pass\"\n".format(sys.executable))

        self.m.cmd_merge_derived(self.root, self.repo, str(a), str(o), str(b), "docs/gen.txt")

        for p, was in before.items():
            self.assertEqual(was, p.read_bytes(), "the driver wrote outside %A: {}".format(p))

    def test_Q11_source_tree_marked_derived_is_refused(self):
        """Q11 / A1 / STRIDE B7. The highest-severity path in this phase: a registry change
        that authorises a merge to overwrite authored work. The driver refuses when the path
        git is merging is not the path the registry classifies as derived."""
        a, o, b = self._merge_inputs()
        self.registry("docs/gen.txt: derived {} -c \"pass\"\n".format(sys.executable))

        rc = self.m.cmd_merge_derived(self.root, self.repo, str(a), str(o), str(b),
                                      "src/Ingest/Reader.cs")

        self.assertEqual(rc, 0, "the driver must still not exit non-zero")
        content = a.read_text(encoding="utf-8")
        self.assertIn(CONFLICT_START, content,
                      "an unclassified path was resolved instead of conflicted")
        self.assertIn("theirs", content)

    def test_Q7c_regeneration_that_hangs_is_bounded_and_stays_owed(self):
        """H5. A regenerator must never hang the caller, and a failed regeneration must be
        loud -- the artifact is then STALE, which is worse than a conflict because it looks
        finished."""
        self.registry("docs/gen.txt: derived {} -c \"import time; time.sleep(30)\"\n"
                      .format(sys.executable))
        self.m.record_regen_owed(self.root, "docs/gen.txt")
        rc, results = self.m.cmd_regen(self.root, self.repo, timeout=2)
        self.assertNotEqual(rc, 0, "a failed regeneration reported success")
        self.assertEqual(results[0]["status"], "failed")
        self.assertIn("docs/gen.txt", self.m.regen_owed(self.root),
                      "a failed regeneration must stay owed, not be cleared")

    def test_regen_runs_the_command_and_clears_the_debt(self):
        gen = self.repo / "regen.py"
        gen.write_text("import pathlib\n"
                       "pathlib.Path('docs').mkdir(exist_ok=True)\n"
                       "pathlib.Path('docs/gen.txt').write_text('REGENERATED\\n')\n",
                       encoding="utf-8", newline="\n")
        self.registry("docs/gen.txt: derived {} {}\n".format(sys.executable, gen))
        self.m.record_regen_owed(self.root, "docs/gen.txt")
        rc, results = self.m.cmd_regen(self.root, self.repo)
        self.assertEqual(rc, 0, results)
        self.assertIn("REGENERATED",
                      (self.repo / "docs" / "gen.txt").read_text(encoding="utf-8"))
        self.assertEqual(self.m.regen_owed(self.root), [])

    def test_Q6_driver_runs_under_rebase_not_only_merge(self):
        """Q6 / S11. Protected main forces rebase, and rebase is where the measured
        conflicts actually happen -- so merge alone is not the case that matters."""
        self.registry("docs/gen.txt: derived {} -c \"pass\"\n".format(sys.executable))
        install = self.run_cli("install")
        self.assertEqual(install.returncode, 0, install.stdout + install.stderr)

        self.write("docs/gen.txt", "v0\n")
        self.write("src.txt", "s0\n")
        self.git("add", "-A"); self.git("commit", "-qm", "base")
        self.git("checkout", "-qb", "feature")
        self.write("docs/gen.txt", "gen-feature\n"); self.write("src.txt", "s-feature\n")
        self.git("add", "-A"); self.git("commit", "-qm", "feature")
        self.git("checkout", "-q", "master")
        self.write("docs/gen.txt", "gen-master\n"); self.write("src.txt", "s-master\n")
        self.git("add", "-A"); self.git("commit", "-qm", "master")

        self.git("checkout", "-q", "feature")
        self.git("rebase", "master", check=False)
        unmerged = self.git("diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
        self.assertNotIn("docs/gen.txt", unmerged,
                         "the derived file conflicted under rebase; the driver did not run")
        self.assertIn("src.txt", unmerged, "the authored file must still conflict normally")
        self.git("rebase", "--abort", check=False)


# ------------------------------------------------------------------ registry

class FloorAdvisoryTests(DerivedCase):
    def test_installed_floor_does_not_block_a_commit_without_AGENT_SESSION(self):
        """Found by Q6 during integration, not by the design.

        `install` writes a pre-commit hook that runs on EVERY commit -- a human's by hand
        and any tool's, not just an agent's. Returning 4 with no identity blocked all of
        them, which is how a floor gets deleted instead of adopted. Advisory and loud is
        the same trade already made for the missing registry (US-8).
        """
        self.write("a.txt", "x\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")
        self.assertEqual(self.run_cli("install").returncode, 0)

        self.write("b.txt", "y\n")
        self.git("add", "-A")
        env = dict(os.environ)
        env.pop("AGENT_SESSION", None)
        done = subprocess.run(["git", "commit", "-qm", "by hand"], cwd=str(self.repo),
                              env=env, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0,
                         "the installed floor blocked a commit with no AGENT_SESSION:\n"
                         + done.stdout + done.stderr)
        self.assertEqual(self.git("rev-list", "--count", "HEAD").stdout.strip(), "2")


class RegisterClassTests(DerivedCase):
    def test_register_class_gets_the_conservation_driver_end_to_end(self):
        """The class Strategy, proven through git: a `register` artifact is unioned rather
        than resolved, and the entry two branches would have collided on survives."""
        import json as _json
        self.registry("audit.jsonl: register\n")
        self.write("audit.jsonl",
                   _json.dumps({"id": "al-0001", "shortname": "base"}) + "\n")
        self.git("add", "-A"); self.git("commit", "-qm", "base")
        self.assertEqual(self.run_cli("install").returncode, 0)
        self.git("add", "-A"); self.git("commit", "-qm", "install")

        base = _json.dumps({"id": "al-0001", "shortname": "base"}) + "\n"
        self.git("checkout", "-qb", "feature")
        self.write("audit.jsonl",
                   base + _json.dumps({"id": "al-0002", "shortname": "feature-work"}) + "\n")
        self.git("add", "-A"); self.git("commit", "-qm", "f")
        self.git("checkout", "-q", "master")
        self.write("audit.jsonl",
                   base + _json.dumps({"id": "al-0002", "shortname": "master-work"}) + "\n")
        self.git("add", "-A"); self.git("commit", "-qm", "m")

        self.git("merge", "feature", check=False)
        unmerged = self.git("diff", "--name-only", "--diff-filter=U",
                            check=False).stdout.split()
        self.assertNotIn("audit.jsonl", unmerged,
                         "the register conflicted instead of being unioned")
        rows = [_json.loads(l) for l
                in (self.repo / "audit.jsonl").read_text(encoding="utf-8").splitlines()
                if l.strip()]
        names = sorted(r["shortname"] for r in rows)
        self.assertEqual(names, ["base", "feature-work", "master-work"],
                         "an entry was destroyed by the id collision: {}".format(names))


class RegistryTests(DerivedCase):
    def test_classify_defaults_to_authored(self):
        self.registry("docs/gen.txt: derived cmd\n")
        self.assertEqual(self.m.classify(self.root, "src/anything.cs")[0], "authored")

    def test_longest_matching_pattern_wins(self):
        self.registry("docs/**: authored\ndocs/gen.txt: derived cmd\n")
        self.assertEqual(self.m.classify(self.root, "docs/gen.txt")[0], "derived")
        self.assertEqual(self.m.classify(self.root, "docs/other.md")[0], "authored")

    def test_Q12_overlapping_classes_are_a_registry_error(self):
        """Q12 / H7. Two patterns of DIFFERENT class matching identically is a registry
        error, not a precedence puzzle -- first-match-wins would make a path's class depend
        on file ordering."""
        self.registry("docs/gen.txt: derived cmd\ndocs/gen.txt: authored\n")
        with self.assertRaises(self.m.CoordError) as ctx:
            self.m.load_registry(self.root)
        self.assertEqual(ctx.exception.code, "COORD-CLASS-CONFLICT")

    def test_Q13_missing_registry_is_advisory_and_says_so(self):
        """Q13 / H8 / US-8. Unconfigured means advisory, and the layer SAYS it is."""
        klass, reason = self.m.classify(self.root, "anything")
        self.assertEqual(klass, "authored")
        self.assertEqual(reason, "COORD-CLASS-UNREGISTERED")
        result = self.run_cli("class", "anything", "--json")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["class"], "authored")
        self.assertEqual(payload["code"], "COORD-CLASS-UNREGISTERED")
        self.assertIn("advisory", payload["reason"])

    def test_Q14_registry_pattern_escaping_the_repo_is_refused(self):
        """Q14 / A1 / STRIDE B7."""
        self.registry("../../etc/passwd: derived cmd\n")
        with self.assertRaises(self.m.CoordError) as ctx:
            self.m.load_registry(self.root)
        self.assertEqual(ctx.exception.code, "COORD-CLASS-CONFLICT")

    def test_registry_ignores_comments_and_blank_lines(self):
        self.registry("# a comment\n\n  # indented comment\ndocs/gen.txt: derived cmd\n")
        entries = self.m.load_registry(self.root)
        self.assertEqual(len(entries), 1)

    def test_unknown_class_is_a_registry_error(self):
        self.registry("docs/gen.txt: sideways\n")
        with self.assertRaises(self.m.CoordError):
            self.m.load_registry(self.root)

    def test_derived_without_a_regenerate_command_is_a_registry_error(self):
        """A derived class with no way to regenerate cannot do its job, and would fall
        through to a conflict on every merge while claiming to be handled."""
        self.registry("docs/gen.txt: derived\n")
        with self.assertRaises(self.m.CoordError):
            self.m.load_registry(self.root)


# -------------------------------------------------------------------- doctor

class DoctorTests(DerivedCase):
    def test_Q9_unregistered_driver_is_detected_by_doctor(self):
        """Q9 / H3 / S13. check-attr reports the DECLARATION whether or not a driver
        exists, so only reading .gitattributes AND .git/config finds the gap."""
        self.write(".gitattributes", "docs/gen.txt merge=coord-regen\n")
        self.registry("docs/gen.txt: derived cmd\n")
        self.write("docs/gen.txt", "x\n")
        self.git("add", "-A"); self.git("commit", "-qm", "base")

        result = self.run_cli("doctor")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("COORD-DRIVER-NOT-EFFECTIVE", result.stdout)
        self.assertIn("conflict normally", result.stdout,
                      "doctor must state the CONSEQUENCE, which is a visible conflict")

    def test_doctor_reports_effective_once_registered(self):
        self.write("docs/gen.txt", "x\n")
        self.registry("docs/gen.txt: derived {} -c \"pass\"\n".format(sys.executable))
        self.git("add", "-A"); self.git("commit", "-qm", "base")
        self.assertEqual(self.run_cli("install").returncode, 0)
        result = self.run_cli("doctor")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("effective", result.stdout.lower())

    def test_doctor_over_zero_tracked_files_is_not_checked_not_clean(self):
        """R4, third occurrence -- and this one was written by me, the same afternoon I
        cited the rule. `git ls-files` is empty before the first commit, so scanning it
        establishes nothing; reporting `none declared` there is a clean-shaped non-scan.
        """
        self.registry("docs/gen.txt: derived {} -c \"pass\"\n".format(sys.executable))
        result = self.run_cli("doctor")
        self.assertIn("NOT CHECKED", result.stdout)
        self.assertIn("0 tracked files", result.stdout)
        self.assertNotEqual(result.returncode, 0)

    def test_doctor_reports_registry_errors(self):
        self.registry("docs/gen.txt: derived cmd\ndocs/gen.txt: authored\n")
        result = self.run_cli("doctor")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("COORD-CLASS-CONFLICT", result.stdout)

    def test_Q10_unregistered_driver_degrades_to_a_visible_conflict(self):
        """Q10 / S12a. Pins the correction to ADR-0009: an unregistered driver falls back
        to an ordinary 3-way merge with markers. The cost is a LOST BENEFIT, not lost work,
        and the ADR's 'silently gets default behaviour' framing was wrong."""
        self.write(".gitattributes", "gen.txt merge=coord-regen\n")   # declared, NOT registered
        self.write("gen.txt", "v0\n")
        self.git("add", "-A"); self.git("commit", "-qm", "base")
        self.git("checkout", "-qb", "feature")
        self.write("gen.txt", "feature\n"); self.git("add", "-A"); self.git("commit", "-qm", "f")
        self.git("checkout", "-q", "master")
        self.write("gen.txt", "master\n"); self.git("add", "-A"); self.git("commit", "-qm", "m")

        self.git("merge", "feature", check=False)
        unmerged = self.git("diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
        self.assertIn("gen.txt", unmerged, "expected an ordinary visible conflict")
        self.assertIn(CONFLICT_START, (self.repo / "gen.txt").read_text(encoding="utf-8"),
                      "the fallback must leave markers, not a silently-resolved file")


if __name__ == "__main__":
    unittest.main()
