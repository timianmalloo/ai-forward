"""sync-pack mirrors generated surfaces instead of deleting and recreating them.

Delete-and-recreate removed every file on every run. On a volume without POSIX delete
semantics (exFAT, FAT32), a file another process holds open (an on-access scanner) stays
delete-pending, the parent directory then refuses removal ("The directory is not empty"),
and the run aborted with committed surfaces half-deleted. A mirror never deletes a file
whose bytes did not change, and a run that fails part-way leaves the tree untouched.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MIRRORED = (".claude/skills", ".claude/knowledge", ".github/instructions", ".agents/skills",
            "docs/ai-forward-pack/scripts")


@unittest.skipUnless(shutil.which("pwsh"), "PowerShell sync entry point unavailable")
class SyncPackMirrorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns(
            ".git", "node_modules", "__pycache__", ".venv"))

    def sync(self):
        return subprocess.run([shutil.which("pwsh"), "-NoProfile", "-File",
                               str(self.repo / "tools/sync-pack.ps1")], cwd=self.repo,
                              capture_output=True, text=True, encoding="utf-8", timeout=300)

    def assert_synced(self, result):
        self.assertEqual(0, result.returncode, result.stdout[-2000:] + result.stderr[-2000:])

    def files(self):
        return {path: path.read_bytes() for rel in MIRRORED
                for path in (self.repo / rel).rglob("*") if path.is_file()}

    def test_unchanged_files_are_not_recreated(self):
        self.assert_synced(self.sync())
        identity = {path: os.stat(path).st_ino for path in self.files()}
        self.assertTrue(identity)
        self.assert_synced(self.sync())
        recreated = [str(path.relative_to(self.repo)) for path, ino in identity.items()
                     if os.stat(path).st_ino != ino]
        self.assertEqual([], recreated[:5], "%d unchanged files were deleted and recreated" % len(recreated))

    def test_stale_generated_files_and_directories_are_removed(self):
        self.assert_synced(self.sync())
        stale = self.repo / ".claude/skills/retired-skill/reference/old.md"
        stale.parent.mkdir(parents=True)
        stale.write_text("removed from pack/", encoding="utf-8")
        self.assert_synced(self.sync())
        self.assertFalse((self.repo / ".claude/skills/retired-skill").exists())

    def test_generated_text_is_written_with_lf_line_endings(self):
        """The repo stores LF (.gitattributes eol=lf). Set-Content joins lines with CRLF on
        Windows, so every sync rewrote these files and git status listed them as modified."""
        self.assert_synced(self.sync())
        written = [path for rel in (".github/agents", ".grok/agents")
                   for path in (self.repo / rel).rglob("*") if path.is_file()]
        written += [self.repo / "docs/ai-forward-pack/codex-skills.json",
                    self.repo / ".agents/skills.json"]
        crlf = [str(path.relative_to(self.repo)) for path in written if b"\r" in path.read_bytes()]
        self.assertEqual([], crlf[:5], "%d generated files carry CR line endings" % len(crlf))

    def test_a_failed_run_leaves_generated_surfaces_untouched(self):
        self.assert_synced(self.sync())
        before = self.files()
        knowledge = next(path for path in sorted((self.repo / "pack/knowledge").glob("*.md"))
                         if path.name != "FOUNDATION.md")
        text = knowledge.read_text(encoding="utf-8")
        self.assertIn("\nload:", text)
        knowledge.write_text(text.replace("\nload:", "\nload: nonsense-", 1), encoding="utf-8")
        self.assertNotEqual(0, self.sync().returncode, "an unknown load scope must stop the sync")
        self.assertEqual(before, self.files())


if __name__ == "__main__":
    unittest.main()
