"""Class WT-A, the sweep's second half: "which tree" questions answered about the primary.

Every test builds a real linked worktree and runs from a SUBDIRECTORY of it, which is where the
two errors hide: `os.path.isdir(".git")` walks past a worktree's pointer FILE, and
`repo_root()` (the primary, by design, for the `.agents` stores) was also used for the hook's
path base, the pre-commit floor's index and the request reader's current blob.
All four were red before the fix.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"
CORE = SCRIPTS / "coord-core.py"


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
                          env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x",
                                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x"))


def _env(session):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for key in ("COORD_ROOT", "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"):
        env.pop(key, None)
    if session is None:
        env.pop("AGENT_SESSION", None)
    else:
        env["AGENT_SESSION"] = session
    return env


def _core(args, cwd, session, stdin=None):
    return subprocess.run([sys.executable, str(CORE), *args], cwd=str(cwd), env=_env(session), input=stdin,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _load(script_name):
    spec = importlib.util.spec_from_file_location(script_name.replace("-", "_").replace(".py", ""),
                                                  str(SCRIPTS / script_name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _blob(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


class CheckoutTopTests(unittest.TestCase):
    def setUp(self):
        self.primary = Path(tempfile.mkdtemp(prefix="wt-a2-primary-"))
        self.addCleanup(shutil.rmtree, self.primary, True)
        _git(self.primary, "init", "-q")
        (self.primary / "src").mkdir()
        (self.primary / "src" / "a.cs").write_text("a\n", encoding="utf-8")
        (self.primary / "f.txt").write_text("B\n", encoding="utf-8")
        _git(self.primary, "add", "-A")
        _git(self.primary, "commit", "-q", "-m", "base")
        self.wt = self.primary.parent / (self.primary.name + "-wt")
        _git(self.primary, "worktree", "add", "-q", str(self.wt), "-b", "wt")
        self.addCleanup(shutil.rmtree, self.wt, True)
        self.sub = self.wt / "src"

    # --- the three script-local root walks -------------------------------------------------
    def test_the_script_root_walks_stop_at_a_worktree_pointer_file(self):
        for name in ("prompt-log.py", "prompt-compile.py", "verify-compiled-prompt.py"):
            with self.subTest(script=name):
                module = _load(name)
                got = Path(module._repo_root(str(self.sub))).resolve()
                self.assertEqual(got, self.wt.resolve(),
                                 f"{name}: from a worktree subdirectory the root must be the worktree top, got {got}")

    def test_the_script_root_walks_still_find_a_primary(self):
        module = _load("prompt-log.py")
        self.assertEqual(Path(module._repo_root(str(self.primary / "src"))).resolve(), self.primary.resolve())

    # --- coord-core: the hook's path base ---------------------------------------------------
    def test_the_hook_matches_an_absolute_worktree_path_to_its_lease(self):
        claimed = _core(["claim", "--wi", "WI-1", "--path", "src/**"], self.primary, "s1")
        self.assertEqual(claimed.returncode, 0, claimed.stdout + claimed.stderr)
        payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Edit",
                              "tool_input": {"file_path": str(self.wt / "src" / "a.cs")}})   # no cwd field
        result = _core(["hook"], self.sub, "s2", stdin=payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("deny", result.stdout,
                      "another session's lease on src/** must refuse an edit of <worktree>/src/a.cs")

    # --- coord-core: the pre-commit floor's index -------------------------------------------
    def test_precommit_reads_the_worktree_index_not_the_primary_index(self):
        (self.primary / "src" / "c.cs").write_text("c\n", encoding="utf-8")
        (self.primary / "src" / "d.cs").write_text("d\n", encoding="utf-8")
        _git(self.primary, "add", "src/c.cs", "src/d.cs")               # two staged in the primary
        (self.wt / "src" / "b.cs").write_text("b\n", encoding="utf-8")
        _git(self.wt, "add", "src/b.cs")                                 # one staged in the worktree
        _core(["claim", "--wi", "WI-1", "--path", "docs/**"], self.primary, "s1")   # a record exists
        result = _core(["precommit"], self.sub, "s2")
        self.assertIn("1 staged path(s)", result.stdout,
                      f"the floor must read the committing worktree's index (1 path), not the primary's (2):\n{result.stdout}")

    # --- coord-core: the request reader's current blob --------------------------------------
    def test_request_staleness_is_read_against_the_worktree_file(self):
        (self.wt / "f.txt").write_text("A\n", encoding="utf-8")         # worktree copy differs from the primary's
        added = _core(["request", "add", "--to", "s2", "--deadline", "600", "--fallback", "x", "--path", "f.txt",
                       "ask"], self.sub, "s1")
        self.assertEqual(added.returncode, 0, added.stdout + added.stderr)
        req_id = json.loads(added.stdout.strip().splitlines()[-1])["id"]
        received = _core(["request", "receive", req_id], self.sub, "s2")
        self.assertEqual(received.returncode, 0, received.stdout + received.stderr)
        acked = _core(["request", "ack", req_id, "--blob", _blob(b"A\n")], self.sub, "s2")
        self.assertEqual(acked.returncode, 0, acked.stdout + acked.stderr)
        listed = _core(["request", "list"], self.sub, "s1")
        row = next(line for line in listed.stdout.splitlines() if req_id in line)
        self.assertIn("stale=False", row,
                      "the ack was written against the worktree's f.txt; read against the primary's copy it looks stale")


if __name__ == "__main__":
    unittest.main()
