import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "docs" / "ai-forward-pack" / "scripts" / "audit-log.py"


class AuditLogRenderTests(unittest.TestCase):
    def test_render_replaces_existing_managed_viewer(self):
        with tempfile.TemporaryDirectory() as directory:
            docs_root = pathlib.Path(directory) / "docs"
            audit_root = docs_root / "audit"
            audit_root.mkdir(parents=True)
            viewer = audit_root / "index.html"
            viewer.write_text("stale managed viewer", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(docs_root),
                    "--project",
                    "Render Test",
                    "render",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=20,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = viewer.read_text(encoding="utf-8")
            self.assertNotIn("stale managed viewer", rendered)
            self.assertIn("Render Test", rendered)
            self.assertIn("clawpilotTheme", rendered)
            self.assertIn('node("button","head")', rendered)
            self.assertIn('head.setAttribute("aria-expanded","false")', rendered)


if __name__ == "__main__":
    unittest.main()
