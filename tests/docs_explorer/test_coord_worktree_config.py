"""A git worktree SHARES `.git/config` with its parent — the premise the pack got backwards.

The pack told every agent to run `coord install` inside each new worktree, justified as
*"(per-clone `.git/config`)"*. "Per-clone" is true. "Therefore per-worktree" does not follow:
a linked worktree has no config of its own unless `extensions.worktreeConfig` is set, and
`.git/hooks` is shared through the common dir as well.

So the instruction did not add a registration — it OVERWROTE the repository's one
registration with a path inside a temporary tree. Measured in a consuming repo: after an
install inside `…-feature-conductor-agent-plane`, `git config --show-origin --get
merge.coord-regen.driver` in the MAIN clone returned `file:.git/config` naming the
worktree's copy of the script. WT8 cleanup then deletes that tree and every later merge of
the ten paths `.gitattributes` declares invokes a script that is not there.

There is no signature while the tree exists: the rewritten path resolves and names a
byte-identical script, and `coord doctor` reported the drivers "declared and registered"
either way — it asked whether a driver was declared, never whether its path would outlive
the tree that wrote it.

Written to fail first. Every test here failed on 2026-09-09 before the refusal in
`cmd_install`, `driver_path_status` in `doctor`, and the wording corrections existed.
"""
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"
SCRIPT_COORD = SCRIPTS / "coord-core.py"


def load_coord():
    spec = importlib.util.spec_from_file_location("coord_core_wt", SCRIPT_COORD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _TempRepo(unittest.TestCase):
    """A primary checkout with the layer deployed, and a linked worktree beside it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "primary"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")
        self.registry("docs/audit/audit-log.jsonl: register\n")
        (self.repo / "seed.txt").write_text("seed\n", encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "seed")

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=str(cwd or self.repo),
                              capture_output=True, text=True, check=False)

    def registry(self, text):
        agents = self.repo / ".agents"
        agents.mkdir(exist_ok=True)
        (agents / "artifacts.yml").write_text(text, encoding="utf-8", newline="\n")

    def deploy(self):
        """Put the layer where a consuming repo has it, and COMMIT it.

        Load-bearing: the harm only reproduces when each tree runs its OWN copy, which is
        what a consuming repo has. Running one shared checkout of the script from two cwds
        registers the same path twice and hides the defect entirely.
        """
        dest = self.repo / "docs" / "ai-forward-pack" / "scripts"
        dest.mkdir(parents=True, exist_ok=True)
        # DERIVED, not hand-listed: every importable sibling module (the underscore names)
        # ships with coord-core.py. A hand-maintained list here is a second copy of the
        # deployment map, and it breaks silently the day a new shared module lands -- which
        # is PACK-D, the same seam the coord_ids split was written up under.
        siblings = sorted(p.name for p in SCRIPTS.glob("*.py") if "_" in p.stem)
        for name in ["coord-core.py"] + siblings:
            (dest / name).write_text(
                (SCRIPTS / name).read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "deploy the layer")
        return dest / "coord-core.py"

    def run_cli(self, *args, cwd=None, script=None):
        cwd = cwd or self.repo
        script = script or (Path(cwd) / "docs" / "ai-forward-pack" / "scripts" /
                            "coord-core.py")
        if not Path(script).exists():
            script = SCRIPT_COORD
        return subprocess.run([sys.executable, str(script), *args],
                              cwd=str(cwd), capture_output=True, text=True)

    def add_worktree(self, name="wt"):
        target = self.base / name
        result = self.git("worktree", "add", "-q", str(target), "-b", name)
        self.assertEqual(result.returncode, 0, result.stderr)
        return target


class GitWorktreeConfigGroundTruth(_TempRepo):
    """The fact the pack asserted the opposite of. Nothing here tests our code."""

    def test_a_worktree_writes_config_into_its_parents_shared_file(self):
        wt = self.add_worktree()
        self.git("config", "probe.value", "written-from-the-worktree", cwd=wt)
        seen = self.git("config", "--get", "probe.value").stdout.strip()
        self.assertEqual(
            seen, "written-from-the-worktree",
            "a linked worktree shares .git/config with its parent; the pack's instruction "
            "to run `coord install` inside every worktree rests on the opposite belief")

    def test_worktree_config_extension_is_off_unless_a_repo_turns_it_on(self):
        """The one setting that WOULD make the pack's original claim true — and it is unset."""
        self.add_worktree()
        got = self.git("config", "--get", "extensions.worktreeConfig")
        self.assertNotEqual(got.returncode, 0,
                            "extensions.worktreeConfig is off by default; without it there "
                            "is no per-worktree config for `coord install` to write to")

    def test_the_hooks_directory_is_shared_too(self):
        """`install`'s other half lands in the common dir, so it is the same hazard."""
        wt = self.add_worktree()
        from_wt = self.git("rev-parse", "--git-path", "hooks", cwd=wt).stdout.strip()
        from_primary = self.git("rev-parse", "--absolute-git-dir").stdout.strip()
        self.assertTrue(
            Path(from_wt).resolve() == (Path(from_primary) / "hooks").resolve(),
            "a worktree's hooks path resolves into the PRIMARY .git, so an install there "
            "rewrites the primary's pre-commit floor as well")


class InstallRefusesInsideAWorktree(_TempRepo):
    """The control at the highest rung: make the harmful act impossible, not detectable."""

    def test_install_in_the_primary_still_works(self):
        self.deploy()
        result = self.run_cli("install")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        registered = self.git("config", "--get", "merge.coord-register.driver").stdout
        self.assertIn("coord-core.py", registered)

    def test_install_inside_a_linked_worktree_is_refused(self):
        self.deploy()
        wt = self.add_worktree()
        result = self.run_cli("install", cwd=wt)
        self.assertNotEqual(result.returncode, 0,
                            "install inside a linked worktree can only overwrite the "
                            "parent's registration with a path that dies with the tree")
        self.assertIn("COORD-INSTALL-IN-WORKTREE", result.stdout + result.stderr)

    def test_a_refused_install_leaves_the_parents_registration_untouched(self):
        """The measured harm, reproduced: the parent's driver was repointed at the tree."""
        self.deploy()
        self.assertEqual(self.run_cli("install").returncode, 0)
        before = self.git("config", "--get", "merge.coord-register.driver").stdout.strip()
        self.assertIn("primary", before.replace("\\", "/"))
        wt = self.add_worktree()
        self.run_cli("install", cwd=wt)
        after = self.git("config", "--get", "merge.coord-register.driver").stdout.strip()
        self.assertEqual(before, after,
                         "the shared .git/config must still name the primary's script")
        hook = (self.repo / ".git" / "hooks" / "pre-commit").read_text(encoding="utf-8")
        self.assertNotIn("/{}/".format(wt.name), hook.replace("\\", "/"),
                         "the shared pre-commit floor must not name the worktree either")

    def test_the_refusal_names_the_remedy_and_the_reason(self):
        wt = self.add_worktree()
        out = self.run_cli("install", cwd=wt).stdout
        self.assertIn("shares", out.lower(),
                      "the message must teach that the config is SHARED, not per-worktree")
        self.assertIn("--force", out, "a recorded exception needs a documented escape")

    def test_force_is_the_documented_escape(self):
        wt = self.add_worktree()
        result = self.run_cli("install", "--force", cwd=wt)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class DoctorChecksTheDriverPathOutlivesTheTree(_TempRepo):
    """The check `doctor` lacked: does the configured path RESOLVE, and where does it live?"""

    def set_driver(self, script_path):
        self.git("config", "merge.coord-register.name", "coord: union append-only registers")
        self.git("config", "merge.coord-register.driver",
                 '"{}" "{}" merge-register %A %O %B %P'.format(
                     sys.executable, str(script_path).replace("\\", "/")))

    def doctor(self):
        return self.run_cli("doctor")

    def test_a_driver_inside_the_primary_checkout_is_clean(self):
        good = self.repo / "docs" / "ai-forward-pack" / "scripts" / "coord-core.py"
        good.parent.mkdir(parents=True)
        good.write_text("# stand-in\n", encoding="utf-8", newline="\n")
        self.set_driver(good)
        self.assertNotIn("COORD-DRIVER-PATH", self.doctor().stdout)

    def test_a_driver_pointing_into_a_worktree_is_reported(self):
        """THE finding. Byte-identical script, resolving path, and doomed."""
        wt = self.add_worktree()
        foreign = wt / "docs" / "ai-forward-pack" / "scripts" / "coord-core.py"
        foreign.parent.mkdir(parents=True)
        foreign.write_text("# stand-in\n", encoding="utf-8", newline="\n")
        self.set_driver(foreign)
        result = self.doctor()
        self.assertIn("COORD-DRIVER-PATH-FOREIGN", result.stdout)
        self.assertNotEqual(result.returncode, 0)

    def test_a_driver_outside_the_repository_is_not_a_false_positive(self):
        """A global or out-of-tree install is a legitimate shape, not the measured hazard."""
        outside = self.base / "elsewhere" / "coord-core.py"
        outside.parent.mkdir(parents=True)
        outside.write_text("# stand-in\n", encoding="utf-8", newline="\n")
        self.set_driver(outside)
        self.assertNotIn("COORD-DRIVER-PATH", self.doctor().stdout)

    def test_a_driver_whose_script_is_gone_is_reported(self):
        """What the consuming repo would have hit the moment WT8 cleanup ran."""
        self.set_driver(self.base / "deleted-tree" / "coord-core.py")
        result = self.doctor()
        self.assertIn("COORD-DRIVER-PATH-MISSING", result.stdout)
        self.assertNotEqual(result.returncode, 0)

    def test_a_driver_command_we_cannot_read_is_not_reported_as_healthy(self):
        """R4: unresolved is not evidence of health."""
        self.git("config", "merge.coord-register.driver", "some-other-tool %A %O %B %P")
        result = self.doctor()
        self.assertIn("COORD-DRIVER-PATH-UNREADABLE", result.stdout)


class NoPackSurfaceStillTeachesTheWrongModel(unittest.TestCase):
    """The documentation half of the control: the wrong sentences must not come back.

    A behavioural control catches the harm. This catches the RE-PASTE — the realistic
    recurrence, because the claim lived in nine surfaces that are copied between each
    other, and one revived instance re-teaches it to every consuming repo.
    """

    # Each pattern is a phrasing MEASURED in the pack on 2026-09-09, whitespace-normalized.
    FORBIDDEN = [
        r"clone and every new worktree needs",
        r"clone or a new worktree lands",
        r"clone or a new worktree is exactly where",
        r"every clone and worktree needs it",
        r"worktree[^.]{0,40}needs? `?coord install",
        r"coord install`? (?:step )?(?:run )?\*{0,2}inside (?:that|each|the new) tree",
        r"per-clone\. Every tree",
        r"(?:run|then) `?coord install`? INSIDE",
        r"every (?:fresh )?clone and every (?:new )?worktree",
    ]

    def test_no_pack_surface_asserts_a_worktree_needs_its_own_install(self):
        pack = REPO / "pack"
        offenders = []
        for path in sorted(pack.rglob("*")):
            if not path.is_file() or path.suffix not in (".md", ".py", ".ps1"):
                continue
            if "__pycache__" in path.parts:
                continue
            text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8", errors="replace"))
            # INSTALL.md's frontmatter `changes:` list is an append-only HISTORY of
            # shipped revisions, replayed in order by a repo catching up. Rewriting a past
            # entry would falsify that record, and the new entry carries the correction --
            # so the gate reads the BODY, which is the instruction people follow today.
            if path.name == "INSTALL.md":
                text = text.split(" --- ", 1)[-1]
            for pattern in self.FORBIDDEN:
                if re.search(pattern, text, re.IGNORECASE):
                    offenders.append("{}: {}".format(path.relative_to(REPO), pattern))
        self.assertEqual(offenders, [],
                         "these surfaces still teach that a worktree needs its own "
                         "`coord install`; it shares the parent's .git/config:\n  " +
                         "\n  ".join(offenders))


if __name__ == "__main__":
    unittest.main()
