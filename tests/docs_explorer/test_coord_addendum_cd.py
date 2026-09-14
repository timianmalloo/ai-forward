"""Addenda C/D findings for `coord`: the cleanup label and the lease.

DC-142 (recurrence 2, measured 2026-09-13). `coord worktree cleanup` reported a frozen tree
`clean, merged, unheld - WOULD remove` while `git rev-list --count main..<branch>` read 21.
The old rule was "no commit exists nowhere else", and a PUSHED branch satisfies it: every
commit exists on its remote-tracking ref. "Merged" must mean merged into the repository's
DEFAULT branch, the count must be printed, and the tree must be HELD by default.

DC-163 (measured 2026-09-12). A brief that said "claim every file you will touch, --ttl 3600"
held the defect register for an hour while editing none of it; two joins queued ~50 min.
A `register`-class artifact merges by union and never needs a lease, so a claim on one is
refused outright; a TTL above 900 s is refused unless `--long-edit <reason>` records why.
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "docs" / "ai-forward-pack" / "scripts"
COORD = SCRIPTS / "coord-core.py"


def git(cwd, *args, check=True):
    done = subprocess.run(["git"] + list(args), cwd=str(cwd), capture_output=True, text=True)
    if check and done.returncode != 0:
        raise AssertionError("git {0} in {1}: {2}".format(" ".join(args), cwd, done.stderr))
    return done


def coord(cwd, *args, session=None):
    env = dict(os.environ)
    env.pop("AGENT_SESSION", None)
    env.pop("AGENT_NAME", None)
    if session:
        env["AGENT_SESSION"] = session
    return subprocess.run([sys.executable, str(COORD)] + list(args),
                          cwd=str(cwd), capture_output=True, text=True, env=env)


def make_primary(directory, name="host-repo"):
    repo = pathlib.Path(directory) / name
    repo.mkdir(parents=True)
    git(directory, "init", "-q", "-b", "main", str(repo))
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo


class MergedMeansMergedIntoTheDefaultBranch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.primary = make_primary(self.tmp.name)
        # A remote, so a pushed branch's commits "exist somewhere else" - the exact state
        # that fooled the old rule.
        bare = pathlib.Path(self.tmp.name) / "origin.git"
        git(self.tmp.name, "init", "-q", "--bare", str(bare))
        git(self.primary, "remote", "add", "origin", str(bare))
        git(self.primary, "push", "-q", "origin", "main")

    def _pushed_tree(self, name, commits):
        tree = pathlib.Path(self.tmp.name) / ("host-repo-" + name)
        git(self.primary, "worktree", "add", "-q", "-b", "feature/" + name, str(tree))
        for k in range(commits):
            (tree / "f{0}.txt".format(k)).write_text("x\n", encoding="utf-8")
            git(tree, "add", "-A")
            git(tree, "commit", "-qm", "commit {0}".format(k))
        git(tree, "push", "-q", "-u", "origin", "feature/" + name)
        return tree

    def test_a_pushed_but_unmerged_branch_is_held_and_the_count_is_printed(self):
        tree = self._pushed_tree("frozen", 3)
        result = coord(self.primary, "worktree", "cleanup")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        line = [l for l in result.stdout.splitlines() if "host-repo-frozen" in l]
        self.assertTrue(line, result.stdout)
        self.assertTrue(line[0].startswith("KEEP"), line[0])
        self.assertIn("3 commit(s) not on main", line[0])
        self.assertTrue(tree.is_dir())

    def test_remove_never_touches_a_held_unmerged_tree(self):
        tree = self._pushed_tree("frozen", 2)
        result = coord(self.primary, "worktree", "cleanup", "--remove")
        self.assertTrue(tree.is_dir(), result.stdout)
        self.assertIn("2 commit(s) not on main", result.stdout)

    def test_include_unmerged_is_the_named_escape(self):
        tree = self._pushed_tree("abandoned", 1)
        result = coord(self.primary, "worktree", "cleanup", "--path", str(tree),
                       "--remove", "--include-unmerged")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(tree.is_dir(), result.stdout)

    def test_a_merged_branch_is_safe_and_says_merged_into_main_with_zero(self):
        tree = self._pushed_tree("done", 1)
        git(self.primary, "merge", "-q", "--no-ff", "feature/done", "-m", "merge done")
        result = coord(self.primary, "worktree", "cleanup")
        line = [l for l in result.stdout.splitlines() if "host-repo-done" in l]
        self.assertTrue(line, result.stdout)
        self.assertTrue(line[0].startswith("WOULD"), line[0])
        self.assertIn("merged into main (0 ahead)", line[0])
        self.assertTrue(tree.is_dir())

    def test_list_carries_the_same_label(self):
        self._pushed_tree("frozen", 4)
        result = coord(self.primary, "worktree", "list")
        line = [l for l in result.stdout.splitlines() if "host-repo-frozen" in l]
        self.assertTrue(line and line[0].strip().startswith("HELD"), result.stdout)
        self.assertIn("4 commit(s) not on main", line[0])


class TheLeaseIsForTheMinutesOfTheEdit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_primary(self.tmp.name)
        agents = self.repo / ".agents"
        agents.mkdir()
        (agents / "artifacts.yml").write_text(
            "docs/audit/audit-log.jsonl: register\n"
            "docs/lessons/*.md: authored\n", encoding="utf-8")

    def test_a_register_class_path_cannot_be_claimed(self):
        result = coord(self.repo, "claim", "--wi", "WI-1", "--path", "docs/audit/audit-log.jsonl",
                       session="node-a")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("COORD-CLAIM-REGISTER-CLASS", result.stdout + result.stderr)
        self.assertIn("union", (result.stdout + result.stderr).lower())

    def test_a_ttl_above_the_cap_is_refused_without_a_reason(self):
        result = coord(self.repo, "claim", "--wi", "WI-1", "--path", "docs/lessons/x.md",
                       "--ttl", "3600", session="node-a")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("COORD-CLAIM-TTL-CAP", result.stdout + result.stderr)
        self.assertIn("900", result.stdout + result.stderr)

    def test_long_edit_records_the_reason_and_lifts_the_cap(self):
        result = coord(self.repo, "claim", "--wi", "WI-1", "--path", "docs/lessons/x.md",
                       "--ttl", "3600", "--long-edit", "a 40-minute restructure of one file",
                       session="node-a")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = list((self.repo / ".agents" / "log").glob("*.jsonl"))
        self.assertTrue(log)
        text = "\n".join(p.read_text(encoding="utf-8") for p in log)
        self.assertIn("40-minute restructure", text)
        self.assertIn('"ttl": 3600.0', text)

    def test_the_default_ttl_still_claims(self):
        result = coord(self.repo, "claim", "--wi", "WI-1", "--path", "docs/lessons/x.md",
                       session="node-a")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
