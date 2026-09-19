"""Tests for the leader fence in conductor-join.py — spec-leader-designation US-7, design F11/F12.

Written red-first: before the fence existed `--epoch` was an unknown argument (exit 2) and a
join over a ref carrying a higher epoch merged anyway.

The fence is step 0, before the merge (and before `--continue`'s step 2): it reads
`coord-core.py leader who --json` and refuses with exit 11 (EXIT_FENCE — steps are 1..10 and 0 is
success) when the epoch it was given is lower than the ref's, or when the ref cannot be read.
An absent ref is "fence not applicable" (S2 has no leader) and the join proceeds.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JOIN = REPO / "pack" / "scripts" / "conductor-join.py"
REF = "refs/coord/leader"
ZERO = "0" * 40
EXIT_FENCE = 11


class JoinFenceCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "join@example.invalid")
        self.git("config", "user.name", "join")
        (self.repo / "docs" / "audit").mkdir(parents=True)
        (self.repo / "README.md").write_text("base\n", encoding="utf-8", newline="\n")
        contract = {"regenerate": [], "gates": []}
        (self.repo / "join.json").write_text(json.dumps(contract), encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "init")
        self.git("checkout", "-q", "-b", "feature/x")
        (self.repo / "x.txt").write_text("x\n", encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "feature")
        self.git("checkout", "-q", "main")
        self.base = self.head()

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=str(self.repo), check=check,
                              capture_output=True, text=True, encoding="utf-8")

    def head(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    def set_ref(self, payload):
        blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=str(self.repo),
                              input=payload, capture_output=True, text=True, encoding="utf-8",
                              check=True).stdout.strip()
        self.git("update-ref", REF, blob, ZERO)

    def live_record(self, epoch):
        import time
        now = time.time()
        return json.dumps({"leader": "lead", "epoch": epoch, "pinned_at": now,
                           "expires_at": now + 300, "ttl": 300, "host": "claude", "tree": "primary"},
                          sort_keys=True)

    def join(self, *extra):
        return subprocess.run(
            [sys.executable, str(JOIN), "feature/x", "--title", "merge x", "--audit-shortname",
             "join-x", "--audit-summary", "s", "--audit-goal", "g", "--audit-done-when", "d",
             "--no-push", "--docs-only", "--join", str(self.repo / "join.json"),
             "--session", "t", *extra],
            cwd=str(self.repo), capture_output=True, text=True, encoding="utf-8")

    def assert_no_merge(self):
        self.assertEqual(self.head(), self.base, "the merge ran although the fence refused")

    def test_fence_refuses_lower_epoch_before_the_merge(self):
        self.set_ref(self.live_record(2))
        result = self.join("--epoch", "1")
        self.assertEqual(result.returncode, EXIT_FENCE, result.stdout + result.stderr)
        self.assertIn("leader fence", result.stdout)
        self.assertIn("COORD-JOIN-EPOCH-STALE", result.stdout)
        self.assert_no_merge()

    def test_fence_proceeds_on_equal_epoch(self):
        self.set_ref(self.live_record(2))
        result = self.join("--epoch", "2")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.git("log", "-1", "--format=%s").stdout.startswith("chore(join)"))

    def test_fence_default_epoch_is_the_ref_at_start(self):
        self.set_ref(self.live_record(3))
        result = self.join()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("epoch 3", result.stdout)

    def test_fence_not_applicable_when_absent(self):
        result = self.join("--epoch", "5")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("not applicable", result.stdout)

    def test_fence_refuses_when_the_ref_cannot_be_read(self):
        self.set_ref("not json")
        result = self.join("--epoch", "1")
        self.assertEqual(result.returncode, EXIT_FENCE, result.stdout + result.stderr)
        self.assertIn("COORD-JOIN-LEADER-NOT-CHECKED", result.stdout)
        self.assert_no_merge()

    def test_fence_compares_a_released_ref_too(self):
        """A released ref still carries the epoch; a plan from before the release is stale."""
        import time
        now = time.time()
        self.set_ref(json.dumps({"leader": None, "epoch": 2, "pinned_at": now - 10,
                                 "expires_at": now + 290, "released_at": now, "ttl": 300,
                                 "host": "claude", "tree": "primary"}, sort_keys=True))
        result = self.join("--epoch", "1")
        self.assertEqual(result.returncode, EXIT_FENCE, result.stdout + result.stderr)
        self.assert_no_merge()

    def test_fence_runs_on_continue(self):
        self.git("merge", "-q", "--no-ff", "feature/x", "-m", "by hand")
        merged = self.head()
        self.set_ref(self.live_record(2))
        result = self.join("--continue", "--epoch", "1")
        self.assertEqual(result.returncode, EXIT_FENCE, result.stdout + result.stderr)
        self.assertEqual(self.head(), merged, "no join commit after a refused fence")

    def test_self_test_still_passes(self):
        result = subprocess.run([sys.executable, str(JOIN), "--self-test"], capture_output=True,
                                text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
