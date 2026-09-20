"""Class WT-A, the sweep: which root is which, from a LINKED worktree.

The `.agents` stores are per repository (the primary checkout); the files a session names and the
documents it commits are per checkout (its worktree). Two scripts had them crossed and every
fixture hid it, because in a single-checkout repo the two roots coincide:

- coord-mail.py refused `--brief` inside a worktree as "outside the repository" (observed on the
  operator's dispatch probe, 2026-09-19, MAIL-PATH);
- coord-board.py put the `.agents` root at the nearest checkout, so from a worktree it read the
  committed ledger copies and no inbox.

Both tests build a real linked worktree (a renamed directory would not reproduce it - PACK-P's
lesson) and were red before the fix.
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


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
                          env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x",
                                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x"))


def _run(script, args, cwd, session):
    env = dict(os.environ, AGENT_SESSION=session, PYTHONIOENCODING="utf-8")
    env.pop("COORD_ROOT", None)
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=str(cwd), env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class WorktreeRootTests(unittest.TestCase):
    def setUp(self):
        self.primary = Path(tempfile.mkdtemp(prefix="wt-a-primary-"))
        self.addCleanup(shutil.rmtree, self.primary, True)
        _git(self.primary, "init", "-q")
        (self.primary / "README.md").write_text("base\n", encoding="utf-8")
        _git(self.primary, "add", "-A")
        _git(self.primary, "commit", "-q", "-m", "base")
        self.wt = self.primary.parent / (self.primary.name + "-wt")
        _git(self.primary, "worktree", "add", "-q", str(self.wt), "-b", "wt")
        self.addCleanup(shutil.rmtree, self.wt, True)

    def test_dispatch_accepts_a_brief_inside_the_worktree(self):
        brief = self.wt / "docs" / "brief.md"
        brief.parent.mkdir(parents=True)
        brief.write_text("Reply READY.\n", encoding="utf-8")
        # An absent harness makes dispatch stop AFTER the path check and BEFORE any child spawns.
        result = _run("coord-mail.py", ["dispatch", "--harness", "copilot", "--brief", "docs/brief.md",
                                        "--deadline", "5", "--fallback", "stop"], self.wt, "wt-session")
        self.assertNotIn("MAIL-PATH", result.stdout + result.stderr,
                         "a brief inside the worktree was refused as outside the repository")

    def test_dispatch_still_refuses_a_brief_outside_any_checkout(self):
        outside = Path(tempfile.mkdtemp(prefix="wt-a-outside-"))
        self.addCleanup(shutil.rmtree, outside, True)
        (outside / "brief.md").write_text("x\n", encoding="utf-8")
        result = _run("coord-mail.py", ["dispatch", "--harness", "copilot", "--brief", str(outside / "brief.md"),
                                        "--deadline", "5", "--fallback", "stop"], self.wt, "wt-session")
        self.assertIn("MAIL-PATH", result.stdout + result.stderr)

    def test_board_from_a_worktree_reads_the_primary_stores(self):
        sent = _run("coord-mail.py", ["send", "--to", "someone", "--kind", "note", "--body", "hello from the primary"],
                    self.primary, "primary-session")
        self.assertEqual(sent.returncode, 0, sent.stdout + sent.stderr)
        self.assertTrue((self.primary / ".agents" / "mail").is_dir(), "the store lives at the primary")
        self.assertFalse((self.wt / ".agents" / "mail").exists(), "the worktree has no store of its own")
        board = _run("coord-board.py", ["board", "--json"], self.wt, "wt-session")
        self.assertEqual(board.returncode, 0, board.stdout + board.stderr)
        self.assertIn("hello from the primary", board.stdout,
                      "from a worktree the board must read the primary's inboxes, not an empty local root")
        self.assertNotIn("NOT CHECKED", board.stdout)


if __name__ == "__main__":
    unittest.main()
