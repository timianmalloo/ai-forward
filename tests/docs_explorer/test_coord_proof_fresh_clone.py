"""Historical receipts must verify in a fresh clone without archive refs or alternates."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
AREA = Path("docs/knowledge/acp-compatibility")
VERIFIER = AREA / "verify-coordination-end-to-end.py"
FIXTURE = AREA / "coordination-receipts.pack"
DATA = AREA / "end-to-end-qualification.json"

class FreshCloneProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="coord-fresh-clone-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.base = Path(cls.temp.name)
        cls.source = cls.base / "source"
        cls.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        cls.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        cls.git("init", "--quiet", "--initial-branch=proof", str(cls.source))
        data = json.loads((ROOT / DATA).read_text())
        cls.worker = data["codex_owner_joins"][0]["worker_commit"]
        receipts = {r["receipt"]["path"] for r in data["profiles"] if r["scenario"] == "positive"}
        receipts.add(data["claude_owner"]["worker_proof"]["receipt"]["path"])
        for relative in (VERIFIER, DATA, FIXTURE, *map(Path, receipts)):
            target = cls.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        cls.git("-C", str(cls.source), "add", ".")
        cls.git("-C", str(cls.source), "-c", "user.name=Proof Fixture", "-c",
                "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
                "commit", "--quiet", "-m", "Portable proof fixture only")

    @classmethod
    def git(cls, *args, **kwargs):
        return subprocess.run(["git", *args], env=cls.env, capture_output=True,
                              check=True, timeout=20, **kwargs)

    def setUp(self):
        self.repo = self.base / self.id().rsplit(".", 1)[-1]
        self.git("clone", "--quiet", "--no-local", "--single-branch", "--branch", "proof",
                 str(self.source), str(self.repo))

    def run_verifier(self, *, env=None):
        return subprocess.run([sys.executable, str(self.repo / VERIFIER)],
                              cwd=self.repo, env=env or self.env, capture_output=True,
                              text=True, timeout=30)

    def assert_historical_object_absent(self):
        result = subprocess.run(["git", "-C", str(self.repo), "cat-file", "-t", self.worker],
                                env=self.env, capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)

    def test_fresh_single_branch_clone_runs_all_real_git_checks_without_importing_objects(self):
        self.assert_historical_object_absent()
        result = self.run_verifier()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("five distinct Git receipts", result.stdout)
        self.assert_historical_object_absent()
        self.assertFalse((self.repo / ".git/objects/info/alternates").exists())

    def test_missing_fixture_fails_even_if_local_git_has_historical_objects(self):
        self.git("-C", str(self.repo), "index-pack", "--stdin", input=(self.repo / FIXTURE).read_bytes())
        self.assertEqual(self.git("-C", str(self.repo), "cat-file", "-t", self.worker).stdout, b"commit\n")
        (self.repo / FIXTURE).unlink()
        result = self.run_verifier()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GIT-FIXTURE-MISSING", result.stderr)

    def test_corrupted_fixture_is_rejected_before_git_checks(self):
        path = self.repo / FIXTURE
        data = bytearray(path.read_bytes())
        data[len(data) // 2] ^= 1
        path.write_bytes(data)
        result = self.run_verifier()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GIT-FIXTURE-HASH", result.stderr)

    def test_wrong_fixture_size_is_rejected(self):
        path = self.repo / FIXTURE
        path.write_bytes(path.read_bytes()[:-1])
        result = self.run_verifier()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GIT-FIXTURE-SIZE", result.stderr)

    def test_current_receipt_tamper_is_still_rejected(self):
        data = json.loads((self.repo / DATA).read_text())
        receipt = self.repo / data["codex_owner_joins"][0]["receipt"]["path"]
        receipt.write_bytes(receipt.read_bytes() + b"tampered\n")
        result = self.run_verifier()
        self.assertNotEqual(result.returncode, 0)

    def test_wrong_worker_and_join_ancestry_are_not_sanitized_assertions(self):
        for field in ("worker_commit", "join_commit"):
            data = json.loads((self.source / DATA).read_text())
            data["codex_owner_joins"][0][field] = data["codex_owner_joins"][0]["source_base"]
            (self.repo / DATA).write_text(json.dumps(data))
            result = self.run_verifier()
            with self.subTest(field=field):
                self.assertNotEqual(result.returncode, 0)

    def test_inherited_git_object_override_cannot_redirect_fixture_import(self):
        outside = self.base / "foreign-objects"
        outside.mkdir(exist_ok=True)
        env = dict(self.env, GIT_OBJECT_DIRECTORY=str(outside), GIT_DIR=str(self.source / ".git"))
        result = self.run_verifier(env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(outside.iterdir()), [])

if __name__ == "__main__":
    unittest.main()
