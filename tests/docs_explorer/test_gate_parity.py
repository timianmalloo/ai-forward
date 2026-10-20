"""FR-067. Nothing asserted that tools/verify-bundle.ps1 still mirrors CI.

FR-061 makes verify-bundle.ps1 the officially recommended pre-commit proxy for CI, named in
CLAUDE.md and AGENTS.md. A proxy nothing holds to its original is Mock Fiction at the level of
the remedy: if the two drift, the front door teaches every agent to trust a control that no
longer represents the gate, and CTRL-D re-opens wearing the fix's own clothes.

FR-091 (revision 117) made the drift structurally impossible: tools/gates.py is the one list both
call (`test_gates.CallersUseTheListTests` pins that). What stays here is the canonical set: no gate
may silently leave the list, stop running locally, or stop running in CI.
"""

import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# (gate id, substring of its name in tools/gates.py)
CANONICAL_GATES = [
    ("1", "counts, skill/prompt parity"),
    ("1b", "no machine-specific paths"),
    ("1c", "subprocess text decodes state utf-8"),
    ("1d", "text writes and consoles are portable"),
    ("1e", "skill contracts: seat, CO-S0 before dispatch, CO-S2 on hard stops"),
    ("1f", "documented commands run in any shell"),
    ("1g", "ruling citations resolve to one heading each"),
    ("1h", "inline markers carry their required fields"),
    ("2", "source<->install drift"),
    ("3", "python test suite"),
    ("4", "docs explorer core contracts"),
    ("4b", "explainer render"),
    ("5", "knowledge-graph validation"),
    ("6", "vendored-foundation drift"),
    ("6b", "audit log is fully readable"),
    ("7", "eval cases well-formed"),
    ("8", "always-on context budget"),
    ("8b", "coordination layer installed"),
]


def gates():
    spec = importlib.util.spec_from_file_location("gates_for_parity", REPO / "tools" / "gates.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {gate[0]: gate for gate in module.GATES}


class GateParityTests(unittest.TestCase):
    def test_every_canonical_gate_is_in_the_list_and_runs_locally(self):
        listed = gates()
        for gate_id, name in CANONICAL_GATES:
            with self.subTest(gate=gate_id):
                self.assertIn(gate_id, listed, "a canonical gate left tools/gates.py")
                self.assertIn(name, listed[gate_id][1])
                self.assertTrue(listed[gate_id][4], "a canonical gate no longer runs locally")

    def test_every_canonical_gate_runs_in_some_ci_job(self):
        listed = gates()
        for gate_id, _name in CANONICAL_GATES:
            with self.subTest(gate=gate_id):
                self.assertTrue(listed[gate_id][3], "a canonical gate runs in no CI job")


if __name__ == "__main__":
    unittest.main()
