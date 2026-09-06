"""The coordination layer's INSTALL path (CTX-H, proposal P2).

`coord-core.py` is 2,300 lines and a passing test suite that proves it works *as a library*.
Nothing proved it was ever switched ON, because no test had a subject for that question:
no deployment step wrote the registry, no doctor check missed it, and no gate covered it.
An uninstalled layer reports "0 decisions, nothing claimed" -- indistinguishable from a
working layer that saw no traffic.

These are the tests that have that subject. Written to fail first; every one of them failed
on 2026-09-06 before `check_coordination` and the `.gitignore` correction existed.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"
DOCTOR = SCRIPTS / "pack-doctor.py"
SCRIPT_COORD = SCRIPTS / "coord-core.py"


def load_coord():
    spec = importlib.util.spec_from_file_location("coord_core_p3", SCRIPT_COORD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_doctor():
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location("pack_doctor", DOCTOR)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPTS))


class DoctorCoordinationTests(unittest.TestCase):
    """The check that makes an uninstalled layer visible."""

    def setUp(self):
        self.m = load_doctor()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "target"
        (self.root / "docs" / "ai-forward-pack" / "scripts").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=str(self.root), check=True,
                       capture_output=True)

    def install_script(self):
        (self.root / "docs" / "ai-forward-pack" / "scripts" / "coord-core.py").write_text(
            "# stand-in\n", encoding="utf-8", newline="\n")

    def registry(self, text):
        agents = self.root / ".agents"
        agents.mkdir(exist_ok=True)
        (agents / "artifacts.yml").write_text(text, encoding="utf-8", newline="\n")

    def check(self):
        return self.m.check_coordination(str(self.root))

    def test_no_script_means_the_check_does_not_apply(self):
        """A repo without the coordination script is not failing to install it."""
        self.assertNotEqual(self.check()["status"], self.m.FAIL)

    def test_the_script_without_a_registry_is_a_FAIL(self):
        """THE finding. The layer shipped, nothing turned it on, and nothing noticed."""
        self.install_script()
        result = self.check()
        self.assertEqual(result["status"], self.m.FAIL)
        self.assertIn("classify init", result["fix"],
                      "the doctor must name the command that fixes it")

    def test_a_parsing_registry_is_a_PASS(self):
        self.install_script()
        self.registry("docs/audit/audit-log.jsonl: register\n")
        self.assertEqual(self.check()["status"], self.m.PASS)

    def test_an_unparseable_registry_is_a_FAIL_not_a_silent_authored_fallback(self):
        """`classify` degrades to `authored` on a broken registry -- safe, and invisible."""
        self.install_script()
        self.registry("this line has no colon\n")
        self.assertEqual(self.check()["status"], self.m.FAIL)

    def test_a_declared_but_unregistered_driver_is_a_WARN(self):
        """.git/config is per-clone and never committed, so every fresh clone and every
        new worktree starts with the driver declared and not registered."""
        self.install_script()
        self.registry("docs/audit/audit-log.jsonl: register\n")
        (self.root / ".gitattributes").write_text(
            "docs/audit/audit-log.jsonl merge=coord-register\n",
            encoding="utf-8", newline="\n")
        result = self.check()
        self.assertEqual(result["status"], self.m.WARN)
        self.assertIn("coord-core.py install", result["fix"],
                      "the fix must be runnable as written, not a shorthand")

    def test_the_check_is_wired_into_the_doctor_run(self):
        """A check nothing calls is prose."""
        self.install_script()
        names = [c["name"] for c in self.m.run(str(self.root))]
        self.assertIn("coordination", names)


class RegistryIsCommittableTests(unittest.TestCase):
    """OPS-B, inverted: an ignore rule that took effect on something that must be TRACKED.

    `.gitignore` carried a bare `.agents/`, which is right for the local coordination state
    (the append-only log, leases, regen-owed) and wrong for the one file in there that must
    travel with the repo. `coord classify init` would have written a registry git could never
    see, and the layer would have stayed per-clone forever -- while `coord doctor` reported
    the registry present, because it reads the filesystem.

    Git cannot re-include a file under an excluded DIRECTORY: `.agents/` stops the walk, so a
    later `!.agents/artifacts.yml` never fires. The pattern must exclude the CONTENTS
    (`.agents/*`) for the negation to be reachable. Read the state back, never the exit code.
    """

    def _check_ignore(self, cwd, path):
        """`--quiet`, NOT `-v`. Measured 2026-09-06: with the negation in place,
        `git check-ignore -v .agents/artifacts.yml` prints the `!` pattern and exits **0**,
        because a negation is still a match. Reading that exit code as "ignored" inverts the
        answer. `--quiet` exits 1 for a path that is not ignored, which is what git acts on --
        confirmed against `git status --porcelain`, which lists the file as untracked.
        """
        quiet = subprocess.run(["git", "check-ignore", "--quiet", "--", path], cwd=str(cwd),
                               capture_output=True, text=True)
        verbose = subprocess.run(["git", "check-ignore", "-v", "--", path], cwd=str(cwd),
                                 capture_output=True, text=True)
        return quiet.returncode == 0, (verbose.stdout or "").strip()

    def test_this_repo_does_not_ignore_its_own_registry(self):
        ignored, why = self._check_ignore(REPO, ".agents/artifacts.yml")
        self.assertFalse(ignored,
                         "the artifact registry must be committable; ignored by " + why)

    def test_this_repo_still_ignores_the_local_coordination_state(self):
        """The negation must not re-admit the per-run state it was protecting us from."""
        for path in [".agents/log/session.jsonl", ".agents/regen-owed.txt",
                     ".agents/requests.jsonl"]:
            with self.subTest(path=path):
                ignored, _why = self._check_ignore(REPO, path)
                self.assertTrue(ignored, path + " is per-run state and must stay ignored")

    def test_the_deployed_gitignore_lines_carry_the_same_shape(self):
        """A consuming repo must inherit the correction, not just this one."""
        sys.path.insert(0, str(SCRIPTS))
        try:
            spec = importlib.util.spec_from_file_location(
                "pack_apply", SCRIPTS / "pack-apply.py")
            pa = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pa)
        finally:
            sys.path.remove(str(SCRIPTS))
        lines = list(pa.GITIGNORE_LINES)
        self.assertIn("!.agents/artifacts.yml", lines,
                      "a consuming repo would write a registry git cannot track")
        self.assertNotIn(".agents/", lines,
                         "a bare directory exclude makes the negation unreachable")
        self.assertLess(lines.index(".agents/*"), lines.index("!.agents/artifacts.yml"),
                        "the negation must follow the pattern it re-admits from")


class DeploymentMapTests(unittest.TestCase):
    """The step that turns the layer on has to exist where installs read it."""

    def test_install_md_documents_the_coordination_step(self):
        text = (REPO / "docs" / "ai-forward-pack" / "INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("coord-core.py classify init", text,
                      "INSTALL.md is the deployment map; a step nobody documents is not a step")
        self.assertIn("coord-core.py install", text,
                      "PACK-C: the documented command must be runnable as written, not a shorthand")

    def test_this_repo_has_its_own_registry_committed(self):
        """Dogfood. The pack repo is a pack install; gate 11 asserts this stays true."""
        registry = REPO / ".agents" / "artifacts.yml"
        self.assertTrue(registry.exists(),
                        "run `coord classify init` -- the pack cannot ship a step it skipped")
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch",
                                  ".agents/artifacts.yml"],
                                 cwd=str(REPO), capture_output=True, text=True)
        self.assertEqual(tracked.returncode, 0,
                         "the registry exists but git does not track it")


class InstallIsIdempotentTests(unittest.TestCase):
    """`coord install` must declare the merge drivers EVERY time, not only the first.

    `.git/hooks` is shared by every worktree of a repository -- `coord install` says so itself
    when it writes the hook. So in every worktree after the first, the hook already exists and
    is unchanged, and the early return took the whole driver declaration with it: the command
    printed a success line and never touched `.gitattributes`.

    That is precisely the case `pack-doctor`'s WARN sends people to fix, which made the remedy
    a no-op exactly where the problem was. Observed red on 2026-09-06: second run left
    `.gitattributes` with zero `merge=coord-` lines.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "r"
        (self.repo / ".agents").mkdir(parents=True)
        for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
            subprocess.run(["git", *args], cwd=str(self.repo), check=True, capture_output=True)
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "gen.js").write_text("x" + chr(10), encoding="utf-8", newline=chr(10))
        (self.repo / ".agents" / "artifacts.yml").write_text(
            "docs/gen.js: derived echo regenerated" + chr(10), encoding="utf-8", newline=chr(10))
        subprocess.run(["git", "add", "-A"], cwd=str(self.repo), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "f"], cwd=str(self.repo), capture_output=True)

    def _install(self):
        script = REPO / "pack" / "scripts" / "coord-core.py"
        env = dict(os.environ, AGENT_SESSION="s1")
        env.pop("COORD_ROOT", None)
        return subprocess.run([sys.executable, str(script), "install"], cwd=str(self.repo),
                              env=env, capture_output=True, text=True)

    def _declared(self):
        ga = self.repo / ".gitattributes"
        return [l for l in (ga.read_text(encoding="utf-8").splitlines() if ga.exists() else [])
                if "merge=coord-" in l]

    def test_the_second_install_still_declares_the_drivers(self):
        self._install()
        (self.repo / ".gitattributes").unlink(missing_ok=True)   # a fresh worktree's state
        self._install()
        self.assertTrue(self._declared(),
                        "the hook already existed, so the driver declaration was skipped - which "
                        "is every worktree after the first, because .git/hooks is shared")

    def test_a_repeated_install_does_not_duplicate_declarations(self):
        self._install()
        self._install()
        lines = self._declared()
        self.assertEqual(len(lines), len(set(lines)), "declarations must not accumulate")


class CapabilityIsNotAMeasurementTests(unittest.TestCase):
    """CTX-H, the reporting half (proposal P3): `coord doctor` printed a constant as state.

    Six of `coord doctor`'s lines are measured in the repo it runs in. The harness lines are
    not: `HARNESS_STATUS` is a static dict of spike results, identical in every repo forever.
    Printed under the same heading, a reader takes `harness copilot edit boundary: enforcing`
    as this repo's measured state -- which is IO5 (instrumentation over inference) pointed at
    the pack's own instrument.

    Three specific rots this pins, all found by reading the file rather than running it:
      * the honest branch was UNREACHABLE -- `if edit_boundary != "enforcing"` cannot fire now
        that both entries say enforcing, so "the commit floor is the real enforcement" never
        printed, in either harness, ever;
      * `plugin emit` restated a SUPERSEDED conclusion in a string literal ("Copilot is
        advisory ... until a live session proves a deny is honoured") beside the constant
        recording that a live session did;
      * the comment above the doctor loop said the same superseded thing a third time.

    A capability claim with no version has no expiry, so every entry must carry the date and
    the harness version it was established against.
    """

    def setUp(self):
        self.m = load_coord()

    def test_every_entry_carries_its_provenance(self):
        for name, status in self.m.HARNESS_STATUS.items():
            with self.subTest(harness=name):
                self.assertTrue(status.get("established"),
                                "when was this established? a claim with no date never goes stale")
                self.assertTrue(status.get("harness_version"),
                                "against WHICH harness version? Copilot's deny was proven on "
                                "1.0.80 and the runtime has moved since")

    def test_one_renderer_serves_both_surfaces(self):
        """The two surfaces disagreed because each carried its own literal. One function."""
        self.assertTrue(hasattr(self.m, "render_harness_capability"),
                        "both surfaces must render from one source")
        src = SCRIPT_COORD.read_text(encoding="utf-8")
        for func in ("def cmd_doctor", "def cmd_plugin_emit"):
            body = src.split(func, 1)[1].split(chr(10) + "def ", 1)[0]
            self.assertIn("render_harness_capability", body,
                          func + " must render capability through the shared function")
            self.assertNotIn("edit boundary: {}", body,
                             func + " still formats a harness verdict itself")

    def test_the_heading_says_it_is_not_measured_here(self):
        lines = self.m.render_harness_capability()
        head = lines[0].lower()
        self.assertIn("capability", head)
        self.assertTrue("not measured here" in head or "not measured in this repo" in head,
                        "the heading must separate the constant from the measured lines: " + head)

    def test_the_rendered_lines_carry_the_date_and_version(self):
        text = chr(10).join(self.m.render_harness_capability())
        for name, status in self.m.HARNESS_STATUS.items():
            self.assertIn(status["established"], text, name + ": establishment date not shown")
            self.assertIn(status["harness_version"], text, name + ": harness version not shown")

    def test_the_commit_floor_sentence_prints_for_every_harness(self):
        """It is true in BOTH states and it is the sentence that matters, so it is not
        conditional on a status that can never take the other value."""
        lines = self.m.render_harness_capability()
        floors = [l for l in lines if l.strip().startswith("floor")]
        self.assertEqual(len(floors), len(self.m.HARNESS_STATUS),
                         "every harness needs its own floor line - counting the substring "
                         "would also match the prose inside a `why`, which is not the point")
        for line in floors:
            self.assertIn("commit floor", line.lower())

    def test_no_literal_anywhere_restates_a_harness_verdict(self):
        """REC-A: the superseded claim survived in two places because both were prose."""
        src = SCRIPT_COORD.read_text(encoding="utf-8")
        for stale in ("Copilot is advisory at the edit boundary",
                      "Copilot's deny contract is unverified"):
            self.assertNotIn(stale, src,
                             "a superseded verdict is restated in prose: " + stale)

    def test_a_non_enforcing_entry_still_renders_its_reason(self):
        """The honest path must be REACHABLE. It was dead code for two revisions."""
        original = self.m.HARNESS_STATUS
        try:
            self.m.HARNESS_STATUS = {"probe": {"edit_boundary": "observed-only",
                                               "why": "the deny was not honoured",
                                               "established": "2026-01-01",
                                               "harness_version": "0.0.1"}}
            text = chr(10).join(self.m.render_harness_capability())
            self.assertIn("the deny was not honoured", text)
            self.assertIn("observed-only", text)
        finally:
            self.m.HARNESS_STATUS = original


class Wt4ExceptionIsCountedTests(unittest.TestCase):
    """CTX-I / proposal P5: record which tree a session started in, so WT4 has a rate.

    Measured across 48 sessions in three repos: 16 worktrees existed and NOT ONE profiled
    session ran inside one, including three pairs that overlapped in time in a primary
    checkout. WT4 permits the primary as a *recorded* exception -- and an exception with no
    counter becomes the default, which is what the measurement shows happened.

    This is deliberately NOT a refusal. There is no baseline for how often the exception is
    correct, and a refusal built on no baseline is tuning from a feeling, which is the thing
    the whole profiling loop exists to prevent. Record the fact; argue about enforcement once
    there is a rate.

    Sessions recorded before this field existed must read `not recorded`, never be counted as
    worktree (IO8: degrade to unknown, never to a plausible wrong number).
    """

    def setUp(self):
        self.m = load_coord()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "r"
        self.repo.mkdir(parents=True)
        for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
            subprocess.run(["git", *args], cwd=str(self.repo), check=True, capture_output=True)
        (self.repo / "f.txt").write_text("x" + chr(10), encoding="utf-8", newline=chr(10))
        subprocess.run(["git", "add", "-A"], cwd=str(self.repo), capture_output=True)
        subprocess.run(["git", "commit", "-qm", "f"], cwd=str(self.repo), capture_output=True)
        self.root = self.repo / ".agents"
        self.root.mkdir()

    def _events(self):
        events, _errors, _n = self.m.read_events(str(self.root))
        return events

    def test_a_session_started_in_the_primary_records_that(self):
        self.m.cmd_session(str(self.root), "start", "s1", "a1", str(self.repo), 1000.0,
                           repo=str(self.repo))
        starts = [e for e in self._events() if e.get("kind") == "session-start"]
        self.assertEqual(len(starts), 1)
        self.assertEqual(starts[0].get("tree"), "primary",
                         "WT4's exception must be recorded where a later pass can count it")

    def test_a_session_started_in_a_linked_worktree_records_that(self):
        wt = Path(self.tmp.name) / "r-feature"
        subprocess.run(["git", "worktree", "add", "-q", "-b", "feature", str(wt)],
                       cwd=str(self.repo), check=True, capture_output=True)
        self.m.cmd_session(str(self.root), "start", "s2", "a2", str(wt), 1000.0,
                           repo=str(self.repo))
        starts = [e for e in self._events() if e.get("kind") == "session-start"]
        self.assertEqual(starts[0].get("tree"), "worktree")

    def test_metrics_reports_the_exception_rate(self):
        self.m.cmd_session(str(self.root), "start", "s1", "a1", str(self.repo), 1000.0,
                           repo=str(self.repo))
        payload = self.m.wt4_exception_rate(str(self.root))
        self.assertEqual(payload["sessions_recorded"], 1)
        self.assertEqual(payload["in_primary"], 1)
        self.assertEqual(payload["pct"], 100.0)

    def test_sessions_from_before_the_field_read_not_recorded(self):
        """IO8. An old event has no `tree`; counting it as a worktree would invent a number."""
        self.m.append_event(str(self.root), {"kind": "session-start", "session": "old",
                                             "agent": "a", "wi": "WI-0", "path": "-",
                                             "at": 900.0, "worktree": "k"})
        payload = self.m.wt4_exception_rate(str(self.root))
        self.assertEqual(payload["sessions_recorded"], 0)
        self.assertEqual(payload["not_recorded"], 1)
        self.assertIsNone(payload["pct"], "a rate over an empty corpus is not a measurement")

    def test_metrics_prints_it(self):
        self.m.cmd_session(str(self.root), "start", "s1", "a1", str(self.repo), 1000.0,
                           repo=str(self.repo))
        import contextlib, io as _io
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.m.cmd_metrics(str(self.root), str(self.repo), False)
        out = buf.getvalue().lower()
        self.assertIn("primary", out, "the WT4 rate must surface where the measures are read")

    def test_worktree_new_records_a_worktree_session(self):
        """`coord worktree new` is the OTHER session-start emitter. Both or neither."""
        src = SCRIPT_COORD.read_text(encoding="utf-8")
        body = src.split("def cmd_worktree", 1)[1].split(chr(10) + "def ", 1)[0]
        start = body.split('"kind": "session-start"', 1)[1][:300]
        self.assertIn('"tree"', start,
                      "worktree new registers a session too; an uncounted emitter makes the "
                      "rate wrong in the direction that flatters us")


if __name__ == "__main__":
    unittest.main()
