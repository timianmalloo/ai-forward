"""PACK-P: a generated artifact must never carry the name of the directory it was generated in.

WHY THIS SUITE EXISTS, and why it uses a real linked worktree rather than a renamed folder.
The pack's own discipline (WT1) requires every writing session to run in its own git worktree,
and `coord worktree new` names that directory `<repo>-<branch-slug>`. Every generator that
labelled the project `basename(cwd)` therefore stamped the WORKTREE folder into a committed
artifact the moment the discipline was followed -- so the pack's worktree rule and the pack's
renderers were in direct conflict, and following one guaranteed corrupting the other.

A renamed directory would NOT reproduce this: renaming changes the answer of every rung at
once, so a broken resolver and a correct one agree. Only a LINKED WORKTREE separates them --
its own basename differs from the primary checkout's while both share one repository. That is
the mechanism under test, so that is what these tests build.

Observed failing on the un-fixed code (CI6) before the fix was trusted: `audit-log.py render`
run inside `ai-forward-fix-pack-p-canonical-project` wrote
`"project": "ai-forward-fix-pack-p-canonical-project"` and the matching <title>.
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "docs" / "ai-forward-pack" / "scripts"
AUDIT_LOG = SCRIPTS / "audit-log.py"


def git(cwd, *args):
    done = subprocess.run(["git"] + list(args), cwd=str(cwd),
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError("git {0} failed in {1}: {2}".format(
            " ".join(args), cwd, done.stderr.strip()))
    return done.stdout.strip()


def make_repo(directory, name, remote=None):
    """A real git repo with one commit -- the minimum `git worktree add` will accept."""
    repo = pathlib.Path(directory) / name
    (repo / "docs" / "audit").mkdir(parents=True)
    git(directory, "init", "-q", "-b", "main", str(repo))
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    if remote:
        git(repo, "remote", "add", "origin", remote)
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def render_audit(repo):
    """Run the DEPLOYED renderer with its cwd inside `repo`, exactly as a session would."""
    done = subprocess.run(
        [sys.executable, str(AUDIT_LOG), "--root", str(repo / "docs"), "render"],
        cwd=str(repo), capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    data = (repo / "docs" / "audit" / "audit-data.js").read_text(encoding="utf-8")
    project = re.search(r'"project":\s*"([^"]*)"', data)
    title = re.search(r"<title>([^<]*)</title>",
                      (repo / "docs" / "audit" / "index.html").read_text(encoding="utf-8"))
    return project.group(1), (title.group(1) if title else "")


class GeneratedIdentityIsWorktreeIndependent(unittest.TestCase):
    """The control. It fails on any generator that names the project from its own directory."""

    def test_render_from_a_linked_worktree_matches_the_primary_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            primary = make_repo(directory, "canonical-name")
            linked = pathlib.Path(directory) / "canonical-name-feature-some-branch"
            git(primary, "worktree", "add", "-q", "-b", "feature/some-branch", str(linked))
            (linked / "docs" / "audit").mkdir(parents=True, exist_ok=True)

            # The mechanism this suite exists for: two directories, different basenames,
            # one repository. A resolver that reads the filesystem disagrees here.
            self.assertNotEqual(primary.name, linked.name)

            from_primary = render_audit(primary)
            from_linked = render_audit(linked)

            self.assertEqual(
                from_primary, from_linked,
                "the generated project identity changed with the directory it was generated "
                "in: primary={0} linked={1} (class PACK-P)".format(from_primary, from_linked))
            self.assertEqual(from_linked[0], "canonical-name")
            self.assertNotIn("feature", from_linked[1])
            git(primary, "worktree", "remove", "--force", str(linked))

    def test_explicit_project_still_overrides_everything(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = make_repo(directory, "some-repo")
            done = subprocess.run(
                [sys.executable, str(AUDIT_LOG), "--root", str(repo / "docs"),
                 "--project", "Chosen Name", "render"],
                cwd=str(repo), capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            data = (repo / "docs" / "audit" / "audit-data.js").read_text(encoding="utf-8")
            payload = json.loads(re.search(r"window\.AUDIT_DATA = (\{.*\});", data, re.S).group(1))
            self.assertEqual(payload["project"], "Chosen Name")


class CanonicalProjectResolution(unittest.TestCase):
    """The rungs, each pinned separately so a regression names which one broke."""

    def setUp(self):
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        import repo_identity
        self.canonical_project = repo_identity.canonical_project

    def test_remote_beats_the_directory_name(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = make_repo(directory, "directory-name",
                             remote="https://github.com/owner/remote-name.git")
            self.assertEqual(self.canonical_project(str(repo)), "remote-name")

    def test_primary_checkout_is_used_when_there_is_no_remote(self):
        """Exercises the RELATIVE `.git` that `--git-common-dir` returns in a primary
        checkout -- a naive dirname() of it yields '', which is the trap in this rung."""
        with tempfile.TemporaryDirectory() as directory:
            repo = make_repo(directory, "no-remote-here")
            self.assertEqual(
                git(repo, "rev-parse", "--git-common-dir"), ".git",
                "precondition: git returns the relative form from a primary checkout")
            self.assertEqual(self.canonical_project(str(repo)), "no-remote-here")

    def test_a_subdirectory_resolves_to_the_repo_not_to_itself(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = make_repo(directory, "outer-repo")
            self.assertEqual(self.canonical_project(str(repo / "docs" / "audit")),
                             "outer-repo")

    def test_outside_a_git_repository_falls_back_without_raising(self):
        with tempfile.TemporaryDirectory() as directory:
            plain = pathlib.Path(directory) / "plain-directory"
            plain.mkdir()
            self.assertEqual(self.canonical_project(str(plain)), "plain-directory")


class EveryGeneratorUsesTheOneResolver(unittest.TestCase):
    """The sweep, as a test: a NEW generator that re-derives identity from the filesystem
    fails here rather than being found by eye in a diff months later."""

    FORBIDDEN = re.compile(
        r"basename\(\s*os\.path\.abspath\(\s*os\.path\.join\(\s*root,\s*['\"]\.\.['\"]")

    def test_no_pack_script_names_the_project_from_its_own_directory(self):
        offenders = []
        scanned = 0
        for path in sorted((ROOT / "pack" / "scripts").glob("*.py")):
            scanned += 1
            lines = path.read_text(encoding="utf-8").splitlines()
            for number, line in enumerate(lines, 1):
                if not self.FORBIDDEN.search(line):
                    continue
                # The soft-import fallback is the ONE allowed use: it runs only on an install
                # that predates repo_identity.py, and it sits directly under that import.
                context = "\n".join(lines[max(0, number - 8):number])
                if "from repo_identity import canonical_project" in context:
                    continue
                offenders.append("{0}:{1}".format(path.name, number))
        # PACK-P (the section entry): a scan that found nothing has not reported clean.
        self.assertGreater(scanned, 0, "scanned no scripts - the corpus was empty")
        self.assertEqual(
            offenders, [],
            "these lines derive the project name from the directory rather than from "
            "repo_identity.canonical_project (class PACK-P): {0}".format(offenders))


if __name__ == "__main__":
    unittest.main()
