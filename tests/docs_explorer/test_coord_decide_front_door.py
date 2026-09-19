"""The `coord decide` front door (coordination-p3-p5-p8, seam P5 -> coordinator (a)).

`coord-core.py decide ...` delegates to the sibling `coord-decide.py` exactly as `mail` and
`board` delegate to theirs: the child's exit code is the result, and a missing delegate is
reported NOT CHECKED (exit 4), never treated as "no decisions". Red first: both tests failed
on the tree before the parser and the delegation branch existed (`argparse` refused `decide`).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"


def _run(args, cwd, env=None):
    return subprocess.run([sys.executable, *args], cwd=str(cwd), env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class DecideFrontDoorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="decide-door-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        self.env = dict(os.environ, AGENT_SESSION="door-test", PYTHONIOENCODING="utf-8")
        self.env.pop("COORD_ROOT", None)

    def test_decide_list_reaches_the_delegate_and_reports_not_checked_on_an_empty_repo(self):
        result = _run([SCRIPTS / "coord-core.py", "decide", "list"], self.tmp, self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NOT CHECKED", result.stdout)

    def test_the_register_is_read_in_the_current_worktree_not_the_primary(self):
        # WT1: a tracked document is written where the session commits. From a linked worktree
        # `decide list` must look for docs/notes/rulings.md in THAT tree; before the fix it
        # reported the primary's path (observed on the land tree, 2026-09-19).
        subprocess.run(["git", "-C", str(self.tmp), "commit", "-q", "--allow-empty", "-m", "base"],
                       check=True, env=dict(self.env, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x",
                                            GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x"))
        wt = self.tmp.parent / (self.tmp.name + "-wt")
        subprocess.run(["git", "-C", str(self.tmp), "worktree", "add", "-q", str(wt), "-b", "wt"], check=True)
        self.addCleanup(shutil.rmtree, wt, True)
        (wt / "docs" / "notes").mkdir(parents=True)
        (wt / "docs" / "notes" / "rulings.md").write_text("# Rulings\n\n### Ruling 1 — in the worktree\n", encoding="utf-8")
        result = _run([SCRIPTS / "coord-core.py", "decide", "list"], wt, self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("NOT CHECKED — no register", result.stdout)
        self.assertIn("1 ruling(s)", result.stdout)

    def test_a_missing_delegate_is_not_checked_exit_4(self):
        # A copy of the front door with every sibling but coord-decide.py: the door must say so.
        door = self.tmp / "scripts"
        door.mkdir()
        for name in ("coord-core.py", "coord_ids.py", "repo_identity.py", "bounded_process.py"):
            src = SCRIPTS / name
            if src.exists():
                shutil.copy(src, door / name)
        result = _run([door / "coord-core.py", "decide", "list"], self.tmp, self.env)
        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
        self.assertIn("COORD-NOT-CHECKED", result.stdout)
        self.assertIn("coord-decide.py", result.stdout)


if __name__ == "__main__":
    unittest.main()
