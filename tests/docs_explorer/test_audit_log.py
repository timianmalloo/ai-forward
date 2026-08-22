import pathlib
import re
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


class AuditLogDataLossTests(unittest.TestCase):
    """FR-052. `read_log` swallowed a JSONDecodeError with a bare `pass`, so a corrupted
    entry vanished from every reader with no warning, no counter and no signal — in the
    file that is this project's durable memory and the corpus /dream consolidates over.
    Refusing to crash on one bad line is right; discarding it invisibly is not. These were
    observed failing on the pre-fix code."""

    GOOD = ('{"id":"al-0001","shortname":"a","datetime":"2026-01-01T00:00:00Z",'
            '"session":"s","prompt":"p","summary":"s"}')

    def _log(self, directory, *lines):
        audit = pathlib.Path(directory) / "docs" / "audit"
        audit.mkdir(parents=True)
        (audit / "audit-log.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return pathlib.Path(directory) / "docs"

    def _run(self, root, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root), *args],
            cwd=ROOT, capture_output=True, text=True, timeout=30)

    def test_verify_passes_on_a_clean_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._log(directory, self.GOOD)
            result = self._run(root, "verify")
            self.assertEqual(0, result.returncode, result.stderr)

    def test_verify_fails_on_a_corrupted_line(self):
        """The gate: a line nothing can read must not report as a healthy log."""
        with tempfile.TemporaryDirectory() as directory:
            root = self._log(directory, self.GOOD, "{not valid json")
            result = self._run(root, "verify")
            self.assertEqual(1, result.returncode,
                             "an unreadable line must fail verify — it is invisible to /dream")

    def test_verify_names_the_file_and_line(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._log(directory, self.GOOD, "{not valid json")
            result = self._run(root, "verify")
            self.assertIn("audit-log.jsonl:2", result.stderr.replace("\\", "/"))

    def test_a_reader_warns_but_still_succeeds(self):
        """Both halves at once: the tool keeps working AND says what it dropped."""
        with tempfile.TemporaryDirectory() as directory:
            root = self._log(directory, self.GOOD, "{not valid json")
            result = self._run(root, "list", "--n", "5")
            self.assertEqual(0, result.returncode, "one bad line must not break the tool")
            self.assertIn("SKIPPED", result.stderr)
            self.assertIn("al-0001", result.stdout, "the readable entry is still returned")

    def test_no_bare_file_handles_remain(self):
        """FR-053, swept as a class rather than four named line numbers: a handle opened
        outside a context manager can outlive its use or truncate a write on the exception
        path — in the system of record."""
        source = SCRIPT.read_text(encoding="utf-8")
        offenders = [
            (n, line.strip())
            for n, line in enumerate(source.splitlines(), 1)
            if re.search(r"(?<!with )\bopen\(", line) and "with open" not in line
        ]
        self.assertEqual([], offenders, f"bare open() without a context manager: {offenders}")


if __name__ == "__main__":
    unittest.main()
