"""CI-speed P6. The pack-consistency jobs are required status checks on `main` (P7); pin what that needs.

Branch protection names checks by context, and a job with no `name:` reports under its job id.
Renaming a job therefore leaves protection waiting for a check that no longer exists, and every
PR blocks. A `paths` filter on `pull_request` does the same to a PR outside those paths: the
required check never reports. This fails on either change, before it reaches protection.

REQUIRED is the list P7 writes into `required_status_checks.contexts`.
"""
import re
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "pack-consistency.yml"
REQUIRED = ("consistency", "consistency-windows", "consistency-macos")


def _block(text, key):
    """The lines of a top-level YAML block (`key:` at column 0) up to the next top-level key."""
    lines = text.split("\n")
    start = lines.index(key + ":")
    out = []
    for line in lines[start + 1:]:
        if line and not line.startswith((" ", "#")):
            break
        out.append(line)
    return out


class RequiredChecksTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_job_ids_are_the_required_check_contexts(self):
        jobs = [m.group(1) for line in _block(self.text, "jobs") for m in [re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)] if m]
        self.assertEqual(sorted(REQUIRED), sorted(jobs))
        names = [line for line in _block(self.text, "jobs") if re.match(r"^    name:", line)]
        self.assertEqual([], names, "a job `name:` changes its check context; update REQUIRED and protection together")

    def test_pull_request_runs_on_every_pr(self):
        on = _block(self.text, "on")
        self.assertIn("  pull_request:", on)
        trigger = on[on.index("  pull_request:") + 1:]
        nested = []
        for line in trigger:
            if re.match(r"^  \S", line):
                break
            nested.append(line.strip())
        self.assertFalse([l for l in nested if l and not l.startswith("#")],
                         "pull_request must be unfiltered: a filtered required check never reports")


if __name__ == "__main__":
    unittest.main()
