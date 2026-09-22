"""The publish boundary includes the actual HTML views, not arbitrary build output."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from windows_links import create_directory_alias, remove_test_path

ROOT = Path(__file__).resolve().parents[2]


class PagesBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / "tools").mkdir()
        shutil.copyfile(ROOT / "tools/build-pages-bundle.py", self.repo / "tools/build-pages-bundle.py")
        for name, content in {
            "docs/_site/bundle.html": "<h1>Public reference</h1>",
            "docs/_site/index.html": "<h1>Public hub</h1>",
            "docs/_site/private-output.html": "PRIVATE",
            "docs/audit/audit-log.jsonl": "PRIVATE",
            "docs/dreams/raw.md": "PRIVATE",
        }.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")

    def build(self):
        return subprocess.run([sys.executable, str(self.repo / "tools/build-pages-bundle.py")],
                              cwd=self.repo, capture_output=True, text=True, encoding="utf-8", timeout=10)

    def test_only_named_generated_public_views_are_published(self):
        result = self.build()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        site = self.repo / "_site"
        self.assertEqual("<h1>Public reference</h1>", (site / "docs/_site/bundle.html").read_text(encoding="utf-8"))
        self.assertTrue((site / "docs/_site/index.html").is_file())
        self.assertFalse((site / "docs/_site/private-output.html").exists())
        self.assertFalse((site / "docs/audit").exists())
        self.assertFalse((site / "docs/dreams").exists())

    def test_missing_generated_reference_fails_instead_of_publishing_a_dead_link(self):
        (self.repo / "docs/_site/bundle.html").unlink()
        result = self.build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("PAGES-GENERATED-MISSING", result.stderr)

    def test_generated_directory_alias_cannot_publish_local_audit_content(self):
        generated = self.repo / "docs/_site"
        for path in generated.iterdir():
            path.unlink()
        generated.rmdir()
        audit = self.repo / "docs/audit"
        (audit / "bundle.html").write_text("PRIVATE", encoding="utf-8", newline="\n")
        (audit / "index.html").write_text("PRIVATE", encoding="utf-8", newline="\n")
        create_directory_alias(generated, audit)
        self.addCleanup(remove_test_path, generated)
        result = self.build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("PAGES-GENERATED-ALIAS", result.stderr)
        self.assertFalse((self.repo / "_site/docs/_site/bundle.html").exists())


if __name__ == "__main__":
    unittest.main()
