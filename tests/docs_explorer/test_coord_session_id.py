"""AGENT_SESSION becomes a file name (.agents/log/<session>.jsonl) - so it is validated, never rewritten.

Seam XP -> P3 of coordination-p3-p5-p8 (cross-platform readiness P4). Observed RED before the
sanitiser (this repo, main @ a01ed77): `AGENT_SESSION=bad:id coord session start` registered the
session and wrote `.agents/log/bad:id.jsonl` - a name NTFS refuses outright, and `a/b` or `..`
would write outside the log directory on every OS.

The rule: a session id is `[A-Za-z0-9._-]+` and neither `.` nor `..`. Anything else is REFUSED
with `COORD-BAD-SESSION-ID` (exit 2) before any write; nothing is ever silently rewritten, because
two agents whose ids differ only in a stripped character would then share one log file.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "pack" / "scripts" / "coord-core.py"


def load_module():
    spec = importlib.util.spec_from_file_location("coord_core_session_id", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SessionIdTests(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "r"
        self.repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=str(self.repo), check=True)
        self.root = self.repo / ".agents"
        self.root.mkdir()

    def run_cli(self, *args, session):
        env = dict(os.environ)
        env.pop("COORD_ROOT", None)
        env["AGENT_SESSION"] = session
        env["AGENT_NAME"] = session
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(self.repo),
                              env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")

    def log_files(self):
        logdir = self.root / "log"
        return sorted(p.name for p in logdir.iterdir()) if logdir.is_dir() else []

    def test_the_rule_accepts_portable_names_and_refuses_everything_else(self):
        for ok in ("xp-cross-platform", "coord.p3_p5", "S1", "a", "2eb8c619-spec-compile"):
            self.assertIsNone(self.m.session_id_error(ok), ok)
        for bad in ("a:b", "a/b", "a\\b", "..", ".", "", " x", "x y", "café", "x\n", "C:x"):
            message = self.m.session_id_error(bad)
            self.assertIsNotNone(message, repr(bad))
            self.assertIn("COORD-BAD-SESSION-ID", message)

    def test_session_start_refuses_a_colon_and_writes_nothing(self):
        done = self.run_cli("session", "start", session="bad:id")
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("COORD-BAD-SESSION-ID", done.stderr)
        self.assertEqual([], self.log_files())

    def test_check_refuses_a_session_that_would_escape_the_log_directory(self):
        done = self.run_cli("check", "x.txt", session="../escape")
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("COORD-BAD-SESSION-ID", done.stderr)
        self.assertEqual([], self.log_files())
        self.assertFalse((self.repo / "escape.jsonl").exists())

    def test_worktree_new_refuses_a_session_argument_with_a_slash(self):
        done = self.run_cli("worktree", "new", "--branch", "t/x", "--session", "p3/xp", session="ok")
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("COORD-BAD-SESSION-ID", done.stderr)
        self.assertEqual([], self.log_files())

    def test_a_portable_session_still_registers(self):
        done = self.run_cli("session", "start", session="xp-cross-platform")
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        self.assertEqual(["xp-cross-platform.jsonl"], self.log_files())


if __name__ == "__main__":
    unittest.main()
