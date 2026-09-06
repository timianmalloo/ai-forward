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


if __name__ == "__main__":
    unittest.main()
