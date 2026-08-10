"""FR-046/FR-047. These scripts are deployed to every adopting repo and were, until now,
gated by nothing and tested by nothing - including scrub.py, which responsible-ai-policy.md
names as the PII/secret first-pass control, and design-lint.py, the U3a token control.

A control with no test is a claim, not a control (CI6).
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"

DEPLOYED = ["audit-log", "design-lint", "docs-graph", "foundation-check",
            "pack-doctor", "prompt-log", "scrub"]


def run(script, *args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run([sys.executable, str(SCRIPTS / f"{script}.py"), *args],
                          capture_output=True, text=True, env=e, timeout=60)


class HelpSurvivesLegacyConsoleTests(unittest.TestCase):
    """prompt-log.py --help exited 1 on Windows with UnicodeEncodeError because its help text
    carries arrow glyphs absent from cp1252. Six siblings survived only because their glyphs
    happen to be cp1252-safe - luck, not an invariant. This asserts the invariant."""

    def test_help_exits_zero_under_cp1252(self):
        for script in DEPLOYED:
            with self.subTest(script=script):
                result = run(script, "--help", env={"PYTHONIOENCODING": "cp1252"})
                self.assertEqual(
                    result.returncode, 0,
                    f"{script} --help failed under cp1252:\n{result.stderr[-600:]}")

    def test_no_unicode_error_in_stderr(self):
        for script in DEPLOYED:
            with self.subTest(script=script):
                result = run(script, "--help", env={"PYTHONIOENCODING": "cp1252"})
                self.assertNotIn("UnicodeEncodeError", result.stderr)


class ScrubControlTests(unittest.TestCase):
    """scrub.py is the named PII/secret control. A true positive AND a true negative, so a
    regression that disables the regexes fails, and so does one that flags everything."""

    def _scan(self, text):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "probe.md"
            target.write_text(text, encoding="utf-8")
            return run("scrub", str(target))

    def test_flags_a_real_email(self):
        result = self._scan("Contact alice.smith@example.com about this.")
        self.assertEqual(result.returncode, 1, "a real address must be reported")
        self.assertIn("email", result.stdout)

    def test_allowlists_the_github_noreply_identity(self):
        """FR-042: the noreply commit identity is not PII and must not be flagged."""
        result = self._scan("Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>")
        self.assertEqual(result.returncode, 0, f"noreply must not be flagged: {result.stdout}")

    def test_clean_text_reports_nothing(self):
        result = self._scan("This document contains no personal data at all.")
        self.assertEqual(result.returncode, 0)


class DesignLintControlTests(unittest.TestCase):
    """design-lint.py enforces U3a: every {token} reference resolves, and component specs
    carry no arbitrary hex."""

    def _lint(self, design):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "DESIGN.md"
            target.write_text(design, encoding="utf-8")
            return run("design-lint", str(target))

    # The contract was READ from design-lint.py, not assumed: it requires a `typography:`
    # block in frontmatter as well as `colors:`. The first fixture guessed and failed.
    GOOD = """---
colors:
  primary: "#2563eb"
typography:
  body: "Inter, sans-serif"
---
# Design
Buttons use {colors.primary} with {typography.body}.
"""

    BAD = """---
colors:
  primary: "#2563eb"
typography:
  body: "Inter, sans-serif"
---
# Design
Buttons use {colors.nonexistent}.
"""

    def test_resolvable_token_passes(self):
        self.assertEqual(self._lint(self.GOOD).returncode, 0)

    def test_unresolvable_token_is_reported(self):
        result = self._lint(self.BAD)
        self.assertNotEqual(result.returncode, 0,
                            "an unresolvable {token} must fail - that is the whole control")


if __name__ == "__main__":
    unittest.main()
