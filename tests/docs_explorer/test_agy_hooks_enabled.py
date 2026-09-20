"""Antigravity hook sections carry `"enabled": true`.

Measured on 2026-09-20 (S1 three-harness test, session s1-agy, Antigravity 1.2.7): the CLI log recorded
`hooks_manager.go:53] loaded 5 named hooks from 2 hooks.json file(s)` - our four project sections plus the
operator's user-level `agy-auto-approve` - and over seven tool calls only the user-level section produced
any effect. It is the only one of the five with `"enabled": true`; the agy binary parses an `enabled` field
(`json:"enabled"` struct tags). No heartbeat accumulator, no ledger row and no run-start marker appeared
for any of ours. Cause Inferred, not yet observed live; this test pins the shape the working hook has.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "pack" / "adapters" / "hooks" / "agy.ai-forward-hooks.json"


class AgyHooksEnabledTests(unittest.TestCase):
    def test_every_named_section_is_enabled(self):
        doc = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertTrue(doc, "the config names no sections")
        missing = sorted(name for name, section in doc.items() if section.get("enabled") is not True)
        self.assertEqual([], missing, f"Antigravity activates a named hook section only with enabled: true; missing on {missing}")

    def test_sections_keep_their_events(self):
        doc = json.loads(CONFIG.read_text(encoding="utf-8"))
        events = {name: sorted(k for k in section if k != "enabled") for name, section in doc.items()}
        self.assertEqual(events["heartbeat"], ["PostToolUse", "Stop"])
        self.assertEqual(events["mail-doorbell"], ["PreInvocation"])
        self.assertEqual(events["session-start"], ["PreInvocation"])
        self.assertEqual(events["reread-guard"], ["PreToolUse"])


if __name__ == "__main__":
    unittest.main()
