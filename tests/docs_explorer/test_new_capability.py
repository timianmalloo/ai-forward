"""FR-074. new-capability.py (the scaffolder the /extendaibundle skill drives) lives in
tools/ and, for its whole life, was gated by nothing and tested by nothing. A scaffolder that
silently breaks surfaces only when a contributor next extends the pack. These are
smoke/characterization tests: --help works, --dry-run writes NOTHING (the load-bearing
guarantee), and an invalid capability name is rejected.

A control with no test is a claim, not a control (CI6).
"""
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tools" / "new-capability.py"

# A name that does not correspond to any existing capability, so a real (non-dry) run would
# create files. The test never does a real run; it asserts dry-run leaves the tree untouched.
PROBE = "zzcapprobe"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )


def _skill_targets(name):
    return [
        REPO / "pack" / "commands" / name / "SKILL.md",
        REPO / "pack" / "adapters" / "copilot" / "prompts" / f"{name}.prompt.md",
        REPO / "pack" / "evals" / "cases" / f"{name}-01.json",
    ]


class NewCapabilitySmoke(unittest.TestCase):
    def test_help_exits_zero(self):
        r = run("--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("new-capability", (r.stdout + r.stderr).lower())

    def test_dry_run_skill_writes_nothing(self):
        targets = _skill_targets(PROBE)
        for p in targets:
            self.assertFalse(p.exists(), f"precondition failed: {p} already exists")
        r = run("--kind", "skill", "--name", PROBE, "--summary", "probe", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        # The load-bearing guarantee: --dry-run touches the filesystem for nothing.
        for p in targets:
            self.assertFalse(p.exists(), f"--dry-run created {p}; it must write nothing")

    def test_dry_run_names_the_planned_paths(self):
        r = run("--kind", "skill", "--name", PROBE, "--summary", "probe", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout + r.stderr
        # The plan should reference each surface it would create (both-tools, no-drift promise).
        self.assertIn(f"commands/{PROBE}/SKILL.md".replace("/", "\\"), out.replace("/", "\\"))
        self.assertIn(f"{PROBE}.prompt.md", out)
        self.assertIn(f"{PROBE}-01.json", out)

    def test_invalid_name_is_rejected(self):
        r = run("--kind", "skill", "--name", "Bad Name", "--summary", "x", "--dry-run")
        self.assertNotEqual(r.returncode, 0, "an invalid capability name must be rejected")


if __name__ == "__main__":
    unittest.main()
