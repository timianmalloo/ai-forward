import json
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


class AuditLogGoalStateTests(unittest.TestCase):
    """P2 / PACK-O: the audit entry records the front-matter goal-state (CT19). `done_when`
    is the presence signal /dream mines — a substantive turn without it skipped the front
    matter. These assert the field round-trips into the committed corpus."""

    def _append(self, root, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root), "append",
             "--shortname", "t", "--session", "s", "--prompt", "p", "--summary", "did the thing",
             *extra],
            cwd=ROOT, capture_output=True, text=True, timeout=30)

    def _entries(self, root):
        text = (pathlib.Path(root) / "audit" / "audit-log.jsonl").read_text(encoding="utf-8")
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    def test_goal_and_done_when_are_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "docs"
            result = self._append(root, "--goal", "answer the question",
                                  "--done-when", "the answer is stated")
            self.assertEqual(0, result.returncode, result.stderr)
            entry = self._entries(root)[-1]
            self.assertEqual("answer the question", entry.get("goal"))
            self.assertEqual("the answer is stated", entry.get("done_when"))

    def test_done_when_absent_when_not_supplied(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "docs"
            result = self._append(root)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertNotIn("done_when", self._entries(root)[-1])


class AuditLogSignalsTests(unittest.TestCase):
    """AL2a / watcher telemetry: an OPTIONAL `signals` object carries the deterministic signals a
    turn actually observed at close, read by the watcher's DeterministicSignalsDeriver to lift an
    imported episode above its conservative default. Honest by construction — only supplied fields
    are emitted, so an un-instrumented turn omits the object and the reader falls back to a
    conservative default rather than a fabricated value (spec L127 / NG1). The absent-when-unsupplied
    test is the fabrication oracle: it reds any change that emits an empty or defaulted object."""

    def _append(self, root, *extra, stdin=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root), "append",
             "--shortname", "t", "--session", "s", "--prompt", "p", "--summary", "did the thing",
             *extra],
            cwd=ROOT, capture_output=True, text=True, timeout=30, input=stdin)

    def _entries(self, root):
        text = (pathlib.Path(root) / "audit" / "audit-log.jsonl").read_text(encoding="utf-8")
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    def test_signals_recorded_from_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "docs"
            result = self._append(root, "--signal-acceptance-met", "true",
                                  "--signal-verification-path", "true",
                                  "--signal-regression", "false")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                {"acceptance_met": True, "verification_path": True, "regression": False},
                self._entries(root)[-1].get("signals"))

    def test_signals_absent_when_no_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "docs"
            result = self._append(root)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertNotIn("signals", self._entries(root)[-1])

    def test_from_json_supplies_signals_and_a_flag_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "docs"
            payload = json.dumps({"signals": {"guidance_required": 3, "acceptance_met": False}})
            result = self._append(root, "--from-json", "-", "--signal-acceptance-met", "true",
                                  stdin=payload)
            self.assertEqual(0, result.returncode, result.stderr)
            signals = self._entries(root)[-1].get("signals")
            self.assertEqual(3, signals.get("guidance_required"))
            self.assertEqual(True, signals.get("acceptance_met"))


if __name__ == "__main__":
    unittest.main()
