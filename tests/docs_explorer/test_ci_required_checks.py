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
# Jobs that run on every PR but must never be required: the duration budget fails on runner noise.
# FR-094: the test shards are not required either; each required OS check is an aggregator job
# that passes only when every shard of that OS passed (SHARDS maps aggregator -> shard job).
SHARDS = {"consistency-windows": "windows-shard", "consistency-macos": "macos-shard"}
NOT_REQUIRED = ("duration-budget",) + tuple(SHARDS.values())


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
        self.assertEqual(sorted(REQUIRED + NOT_REQUIRED), sorted(jobs),
                         "a new job is either a required check (REQUIRED + protection) or listed in NOT_REQUIRED")
        named, job = [], None
        for line in _block(self.text, "jobs"):
            m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
            job = m.group(1) if m else job
            if re.match(r"^    name:", line):
                named.append(job)
        self.assertEqual(sorted(SHARDS.values()), sorted(named),
                         "a job `name:` changes its check context; only the unrequired shard jobs may carry one")

    def test_each_required_os_check_waits_for_every_shard(self):
        for aggregator, shard in SHARDS.items():
            with self.subTest(job=aggregator):
                body = self.text.split("\n  " + aggregator + ":\n", 1)[1]
                body = body[:body.find("\n\n")] if "\n\n" in body else body
                self.assertIn("needs: " + shard, body)
                self.assertIn("if: always()", body, "a skipped aggregator would report no check at all")
                self.assertIn("needs." + shard + ".result }}\" = success", body)

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
