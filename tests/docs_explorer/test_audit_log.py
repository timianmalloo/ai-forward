import json
import pathlib
import shutil
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


class StartMarkerMeasuresOneRun(unittest.TestCase):
    """DEFECT 4, judged: WORKING AS DESIGNED, DOCUMENTED AMBIGUOUSLY, and PINNED BY NOTHING.

    The `start` marker is CONSUMED by the next `append` -- deliberately, so a stale stamp
    can never attach a plausible wrong duration to an unrelated entry (IO8: degrade to
    "not recorded", never to a wrong number). AL4a scopes the obligation to a RUN ("every
    skill, as part of its grounding step"), and the session id is the key, not the scope.
    Measured over this repo's own 162-entry log: of 22 multi-entry sessions, 5 carry more
    than one duration -- so the claim that a session can only ever record one is false.

    What was true is that nothing tested any of it. The pack's flagship self-instrumentation
    was asserted in prose in four documents and verified nowhere; by CI6 that is a memoir.
    """

    SCRIPT = ROOT / "pack" / "scripts" / "audit-log.py"

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.docs = pathlib.Path(self.tmp) / "docs"
        (self.docs / "audit").mkdir(parents=True)

    def run_log(self, *args):
        result = subprocess.run([sys.executable, str(self.SCRIPT), "--root", str(self.docs),
                                 *args], cwd=str(ROOT), capture_output=True, text=True,
                                timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def entries(self):
        path = self.docs / "audit" / "audit-log.jsonl"
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def append(self, shortname, session="S1"):
        self.run_log("append", "--shortname", shortname, "--session", session,
                     "--kind", "script", "--prompt", "probe the start marker",
                     "--summary", "probe", "--outcome", "success")

    def test_one_marker_measures_one_run(self):
        self.run_log("start", "--session", "S1")
        self.append("first")
        self.append("second")
        first, second = self.entries()
        self.assertIn("duration_seconds", first, "the marked run is measured")
        self.assertNotIn("duration_seconds", second,
                         "and the next entry degrades to ABSENT, never to a wrong number")
        self.assertNotIn("started_at", second)

    def test_a_second_start_measures_a_second_run_in_the_same_session(self):
        """The behaviour the documentation obscured: re-marking works, per run."""
        self.run_log("start", "--session", "S1")
        self.append("run-one-close")
        self.run_log("start", "--session", "S1")
        self.append("run-two-close")
        first, second = self.entries()
        self.assertIn("duration_seconds", first)
        self.assertIn("duration_seconds", second)

    def test_the_docs_say_one_marker_measures_one_run(self):
        """The documentation half. A reader who marks once and appends five times must be
        told why four say nothing, or they will read correct behaviour as a broken gauge."""
        for rel in ("pack/knowledge/audit-and-change-log.md",
                    "pack/adapters/managed-blocks/AGENTS.block.md"):
            text = (ROOT / rel).read_text(encoding="utf-8", errors="replace").lower()
            self.assertTrue("one marker measures one run" in text,
                            rel + " must state the marker's scope where the claim is made")


if __name__ == "__main__":
    unittest.main()
