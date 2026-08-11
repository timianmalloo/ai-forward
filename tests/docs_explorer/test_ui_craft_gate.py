"""The UI craft gate must never render "nothing scanned" as "nothing wrong".

Found while answering a question about critiquing another repo: `ui-craft-gate.py` reported a
clean scan of a file it had never opened, because `npx --yes impeccable` failed on a machine
without the package - exit 1, no stdout - and the detector legitimately uses exit 1 for "found
anti-patterns". Empty output plus exit 1 is ambiguous, and it defaulted to clean.
"""
import subprocess
import sys
import textwrap
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "pack" / "scripts" / "ui-craft-gate.py"


def fake_detector(body, temp):
    """A stand-in detector whose behaviour we control exactly."""
    path = Path(temp) / "fake.py"
    path.write_text(body, encoding="utf-8")
    return f"{sys.executable} {path}"


def run_gate(target, detector):
    return subprocess.run(
        [sys.executable, str(GATE), str(target), "--impeccable", detector, "--markdown"],
        capture_output=True, text=True, timeout=120)


class NonScanIsNotACleanScanTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.temp = self._tmp.name
        self.target = Path(self.temp) / "page.html"
        self.target.write_text("<html><body><p>hi</p></body></html>", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_missing_detector_exit1_no_output_is_reported_not_passed(self):
        """The exact observed failure: exit 1, nothing on stdout, an error on stderr."""
        det = fake_detector(textwrap.dedent("""
            import sys
            sys.stderr.write("'impeccable' is not recognized")
            sys.exit(1)
        """), self.temp)
        result = run_gate(self.target, det)
        self.assertNotEqual(result.returncode, 0,
                            "a detector that scanned nothing must not exit 0")
        combined = result.stdout + result.stderr
        self.assertIn("nothing was scanned", combined)
        self.assertNotIn("_no findings_", combined,
                         "a non-scan must never render as a clean findings table")

    def test_non_json_output_is_reported_not_passed(self):
        det = fake_detector(textwrap.dedent("""
            print("Usage: impeccable <command>")
        """), self.temp)
        result = run_gate(self.target, det)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no JSON", result.stdout + result.stderr)

    def test_a_genuine_clean_scan_still_passes(self):
        """The guard must not turn every clean run into a failure - the true negative."""
        det = fake_detector('print("[]")', self.temp)
        result = run_gate(self.target, det)
        self.assertEqual(result.returncode, 0,
                         f"a real empty-findings scan must still pass:\n{result.stderr[-400:]}")
        self.assertIn("_no findings_", result.stdout)

    def test_findings_are_reported(self):
        """And a scan WITH findings still reports them - the true positive."""
        det = fake_detector(
            'print(\'[{"antipattern":"low-contrast","severity":"error",'
            '"file":"page.html","line":3}]\')', self.temp)
        result = run_gate(self.target, det)
        self.assertIn("low-contrast", result.stdout)


if __name__ == "__main__":
    unittest.main()
