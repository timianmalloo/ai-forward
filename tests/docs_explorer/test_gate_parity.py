"""FR-067. Nothing asserted that tools/verify-bundle.ps1 still mirrors CI.

FR-061 makes verify-bundle.ps1 the officially recommended pre-commit proxy for CI, named in
CLAUDE.md and AGENTS.md. A proxy nothing holds to its original is Mock Fiction at the level of
the remedy: if the two drift, the front door teaches every agent to trust a control that no
longer represents the gate, and CTRL-D re-opens wearing the fix's own clothes.

The two files cannot share a literal list - one is PowerShell, the other is YAML consumed by
GitHub - so the shared declaration lives HERE, and drift in either direction fails:
  * a gate present in verify-bundle.ps1 with no CI step  -> local passes, CI has no such gate
  * a CI step with no local gate                         -> CI fails on something never run locally
  * a gate/step in neither list                          -> the declaration itself is stale

Deliberately NOT string-scraping one file and diffing it against the other: that just moves the
drift into the scraper. The canonical list below is the contract; both files are checked against
it, and adding a gate means editing three places on purpose.
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VERIFY_BUNDLE = REPO / "tools" / "verify-bundle.ps1"
CI_WORKFLOW = REPO / ".github" / "workflows" / "pack-consistency.yml"

# (gate id, substring that must appear in verify-bundle.ps1, substring in the CI step name)
CANONICAL_GATES = [
    ("counts",        "1. counts, skill/prompt parity",      "Count & skill-list consistency"),
    ("drift",         "2. source<->install drift",           "Source↔install drift"),
    ("pytest",        "3. python test suite",                "Python test suite"),
    ("docs-explorer", "4. docs explorer core contracts",     "Docs Explorer core contracts"),
    ("explainer",     "4b. explainer render",                "Explainer render + accessibility proof"),
    ("graph",         "5. knowledge-graph validation",       "Knowledge-graph validation"),
    ("foundation",    "6. vendored-foundation drift",        "Vendored-foundation drift"),
    ("audit",         "6b. audit log is fully readable",     "Audit log is fully readable"),
    ("evals",         "7. eval cases well-formed",           "Eval cases well-formed"),
]


def _local_gate_labels():
    """Labels passed to the Gate helper in verify-bundle.ps1 (Skip uses the same labels)."""
    text = VERIFY_BUNDLE.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r'^\s*Gate\s+"([^"]+)"', text, re.M))


def _ci_step_names():
    text = CI_WORKFLOW.read_text(encoding="utf-8", errors="ignore")
    return set(m.strip() for m in re.findall(r"^\s+- name:\s*(.+?)\s*$", text, re.M))


class GateParityTests(unittest.TestCase):
    def test_both_files_exist(self):
        self.assertTrue(VERIFY_BUNDLE.is_file(), f"missing {VERIFY_BUNDLE}")
        self.assertTrue(CI_WORKFLOW.is_file(), f"missing {CI_WORKFLOW}")

    def test_every_canonical_gate_runs_locally(self):
        labels = _local_gate_labels()
        for gate_id, local_sub, _ in CANONICAL_GATES:
            with self.subTest(gate=gate_id):
                self.assertTrue(
                    any(local_sub in label for label in labels),
                    f"gate '{gate_id}' is declared canonical but no Gate in verify-bundle.ps1 "
                    f"matches {local_sub!r}. Local verification no longer mirrors CI, and the "
                    f"front door (FR-061) points agents at it.")

    def test_every_canonical_gate_runs_in_ci(self):
        names = _ci_step_names()
        for gate_id, _, ci_sub in CANONICAL_GATES:
            with self.subTest(gate=gate_id):
                self.assertTrue(
                    any(ci_sub in name for name in names),
                    f"gate '{gate_id}' is declared canonical but no step in "
                    f"pack-consistency.yml matches {ci_sub!r}.")

    def test_no_local_gate_is_undeclared(self):
        """A gate added locally but never declared here is drift the other checks cannot see."""
        labels = _local_gate_labels()
        declared = [sub for _, sub, _ in CANONICAL_GATES]
        undeclared = [l for l in labels if not any(sub in l for sub in declared)]
        self.assertEqual(
            [], sorted(undeclared),
            "verify-bundle.ps1 runs gates not declared in CANONICAL_GATES; add them here and "
            "to pack-consistency.yml, or the local run and CI have silently diverged.")

    def test_gate_counts_agree(self):
        self.assertEqual(
            len(CANONICAL_GATES), len(_local_gate_labels()),
            "verify-bundle.ps1 gate count differs from the canonical declaration.")


if __name__ == "__main__":
    unittest.main()
