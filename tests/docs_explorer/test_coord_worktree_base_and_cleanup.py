"""`coord worktree`: the base is resolved against the INVOKING tree, and cleanup reports
what it measured rather than what it intended.

Both are the PACK-P family -- a tool reading context from the wrong place, inside a system
whose own discipline (WT1) moves work between trees.

FINDING 1. `worktree new --base HEAD` ran `git -C <primary> worktree add ... HEAD`, so from a
linked worktree it silently based the new tree on the PRIMARY's commit. Its measured harm was
a FALSE NEGATIVE ON A FIX: a node that had just committed one created a tree with `--base
HEAD`, got the older commit, ran the pre-fix script, saw the pre-fix result and nearly
reported a correct fix as broken. A renamed directory cannot reproduce this -- only a real
LINKED WORKTREE has a HEAD of its own -- so these tests build one.

FINDING 2. `cleanup --remove` printed `len(removable) - failed`: a count derived from INTENT.
A git call that returned quietly counted as a success, so the summary could claim a tree was
gone while it was still there. It also never mentioned the state git actually leaves when a
delete fails -- DE-REGISTERED but still on disk -- which nothing tracks and no worktree
command will ever mention again.
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


def coord(cwd, *args):
    """Run the DEPLOYED coord-core.py with its cwd inside `cwd`, as a session would."""
    env = dict(os.environ)
    env.pop("AGENT_SESSION", None)
    return subprocess.run([sys.executable, str(COORD), "worktree"] + list(args),
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


class BaseResolvesAgainstTheInvokingWorktree(unittest.TestCase):
    """The falsifier is a REAL linked worktree: it is the only thing with its own HEAD."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.primary = make_primary(self.tmp.name)
        self.linked = pathlib.Path(self.tmp.name) / "host-repo-feature"
        git(self.primary, "worktree", "add", "-q", "-b", "feature/x", str(self.linked))
        # A commit that exists ONLY in the linked tree - this is what went missing.
        (self.linked / "only-here.txt").write_text("x\n", encoding="utf-8")
        git(self.linked, "add", "-A")
        git(self.linked, "commit", "-qm", "a commit only this tree has")
        self.linked_head = git(self.linked, "rev-parse", "HEAD").stdout.strip()
        self.primary_head = git(self.primary, "rev-parse", "HEAD").stdout.strip()
        self.assertNotEqual(self.linked_head, self.primary_head,
                            "precondition: the two trees must be at different commits")

    def _new_tree_head(self, *extra):
        result = coord(self.linked, "new", "--branch", "derived/child", *extra)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        child = pathlib.Path(self.tmp.name) / "host-repo-derived-child"
        self.assertTrue(child.is_dir(), result.stdout)
        return git(child, "rev-parse", "HEAD").stdout.strip(), result.stdout

    def test_explicit_base_head_takes_the_invoking_trees_commit(self):
        head, _ = self._new_tree_head("--base", "HEAD")
        self.assertEqual(head, self.linked_head,
                         "--base HEAD from a linked worktree must mean THIS tree's HEAD")
        self.assertNotEqual(head, self.primary_head)

    def test_the_default_base_is_also_the_invoking_trees_head(self):
        """The default carried the same defect while the help promised 'current HEAD'."""
        head, _ = self._new_tree_head()
        self.assertEqual(head, self.linked_head)

    def test_the_banner_names_the_base_commit(self):
        """IO2: the node above caught this only by checking HEAD by hand afterwards. The
        commit is now on the normal path, so a wrong base cannot be silent again."""
        _, out = self._new_tree_head("--base", "HEAD")
        self.assertIn(self.linked_head[:12], out)
        self.assertIn("base", out)

    def test_a_branch_name_resolves_the_same_from_either_tree(self):
        result = coord(self.linked, "new", "--branch", "derived/frommain", "--base", "main")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        child = pathlib.Path(self.tmp.name) / "host-repo-derived-frommain"
        self.assertEqual(git(child, "rev-parse", "HEAD").stdout.strip(), self.primary_head)

    def test_an_unresolvable_base_is_refused_with_a_named_error(self):
        result = coord(self.linked, "new", "--branch", "derived/bad", "--base", "no-such-ref")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("COORD-WORKTREE-BASE-UNRESOLVED", result.stdout + result.stderr)


class CleanupReportsWhatItMeasured(unittest.TestCase):
    """`classify_removals` is the read-back, isolated so it is testable without needing an
    OS-specific delete failure. The end-to-end cases below cover what IS portable."""

    def setUp(self):
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        import importlib.util
        spec = importlib.util.spec_from_file_location("coord_core_under_test", str(COORD))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.classify = module.classify_removals

    @staticmethod
    def _record(path):
        return {"path": path}

    def test_a_tree_still_registered_is_never_counted_as_removed(self):
        """The exact over-report: the attempt returned, so the old count called it a success."""
        attempts = [(self._record("/repo/tree-a"), None)]
        after = [{"path": "/repo/tree-a"}]
        removed, refused, orphaned = self.classify(attempts, after, exists=lambda p: True)
        self.assertEqual(removed, [])
        self.assertEqual(orphaned, [])
        self.assertEqual([p for p, _ in refused], ["/repo/tree-a"])

    def test_deregistered_but_still_on_disk_is_orphaned_not_removed(self):
        """git de-registers BEFORE deleting, so this state is real and nothing tracks it."""
        attempts = [(self._record("/repo/tree-b"), "error: failed to delete")]
        removed, refused, orphaned = self.classify(attempts, [], exists=lambda p: True)
        self.assertEqual(removed, [])
        self.assertEqual(refused, [])
        self.assertEqual([p for p, _ in orphaned], ["/repo/tree-b"])

    def test_gone_from_both_is_the_only_thing_counted_as_removed(self):
        attempts = [(self._record("/repo/tree-c"), None)]
        removed, refused, orphaned = self.classify(attempts, [], exists=lambda p: False)
        self.assertEqual(removed, ["/repo/tree-c"])
        self.assertEqual((refused, orphaned), ([], []))

    def test_every_attempt_lands_in_exactly_one_bucket(self):
        """A classification that can drop an attempt would under-report, which is the same
        defect wearing the other hat."""
        attempts = [(self._record("/r/a"), None), (self._record("/r/b"), "boom"),
                    (self._record("/r/c"), None)]
        after = [{"path": "/r/a"}]
        removed, refused, orphaned = self.classify(
            attempts, after, exists=lambda p: p == "/r/b")
        self.assertEqual(len(removed) + len(refused) + len(orphaned), len(attempts))


class CleanupScope(unittest.TestCase):
    """GO14a: the action's enforced scope must match its stated clause."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.primary = make_primary(self.tmp.name)
        self.trees = []
        for name in ("alpha", "beta"):
            path = pathlib.Path(self.tmp.name) / ("host-repo-" + name)
            git(self.primary, "worktree", "add", "-q", "-b", "spare/" + name, str(path))
            self.trees.append(path)

    def test_without_path_the_output_says_it_adjudicates_every_worktree(self):
        result = coord(self.primary, "cleanup")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("scope   ALL", result.stdout)
        self.assertIn("--path", result.stdout)

    def test_path_scopes_the_removal_to_one_tree(self):
        result = coord(self.primary, "cleanup", "--path", str(self.trees[0]), "--remove")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.trees[0].is_dir(), result.stdout)
        self.assertTrue(self.trees[1].is_dir(),
                        "a scoped removal must not touch a tree it was not given")
        self.assertIn("removed 1", result.stdout)

    def test_the_summary_counts_attempts_not_the_whole_repository(self):
        result = coord(self.primary, "cleanup", "--path", str(self.trees[0]), "--remove")
        self.assertIn("(of 1 attempted)", result.stdout)

    def test_an_unknown_path_is_refused_rather_than_widening_to_everything(self):
        missing = str(pathlib.Path(self.tmp.name) / "not-a-worktree")
        result = coord(self.primary, "cleanup", "--path", missing, "--remove")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("COORD-WORKTREE-NOT-FOUND", result.stdout + result.stderr)
        self.assertTrue(self.trees[0].is_dir(), "nothing may be removed on a bad --path")
        self.assertTrue(self.trees[1].is_dir())


@unittest.skipUnless(os.name == "nt",
                     "the orphan state needs a delete that FAILS while git has already "
                     "de-registered; POSIX happily unlinks a directory with open handles, so "
                     "this mechanism is Windows-only. classify_removals covers the logic "
                     "everywhere - this is the end-to-end proof that the state is real.")
class OrphanedTreeIsNamedEndToEnd(unittest.TestCase):
    def test_a_held_tree_is_reported_orphaned_and_the_run_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            primary = make_primary(directory)
            tree = pathlib.Path(directory) / "host-repo-held"
            git(primary, "worktree", "add", "-q", "-b", "spare/held", str(tree))
            holder = open(tree / "README.md", "rb")
            try:
                result = coord(primary, "cleanup", "--path", str(tree), "--remove")
            finally:
                holder.close()
            self.assertIn("ORPHANED", result.stdout, result.stdout)
            self.assertIn("orphaned 1", result.stdout)
            self.assertNotIn("removed 1", result.stdout)
            self.assertEqual(result.returncode, 4,
                             "a run that left an untracked directory behind is not a success")


if __name__ == "__main__":
    unittest.main()
