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

from hook_wiring import wired_scripts

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "pack" / "adapters" / "hooks" / "agy.ai-forward-hooks.json"


class AgyHooksEnabledTests(unittest.TestCase):
    def test_every_named_section_is_enabled(self):
        doc = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertTrue(doc, "the config names no sections")
        missing = sorted(name for name, section in doc.items() if section.get("enabled") is not True)
        self.assertEqual([], missing, f"Antigravity activates a named hook section only with enabled: true; missing on {missing}")

    def test_hooks_keep_their_events(self):
        # one `ai-forward` section, one dispatcher command per event (B15); the dispatcher's routes
        # say which hooks run there
        self.assertEqual(wired_scripts("agy", "PostToolUse"), ["heartbeat.py"])
        self.assertEqual(wired_scripts("agy", "PreInvocation"), ["session-start.py", "mail-doorbell.py"])
        self.assertEqual(wired_scripts("agy", "PreToolUse"), ["reread-guard.py"])
        self.assertEqual(wired_scripts("agy", "Stop"), ["heartbeat.py", "owner-review-gate.py"],
                         "Antigravity has a Stop event; the gate is wired on it")

    def test_event_shapes_follow_the_host_docs(self):
        """Tool events (PreToolUse/PostToolUse) take [{matcher, hooks:[handler]}]; lifecycle events
        (PreInvocation, PostInvocation, Stop) take [handler] directly. A PostToolUse handler in the direct
        form loaded without complaint and never fired (heartbeat, S1 test and headless probes, 2026-09-20)."""
        doc = json.loads(CONFIG.read_text(encoding="utf-8"))
        for name, section in doc.items():
            for event, entries in section.items():
                if event == "enabled":
                    continue
                for entry in entries:
                    with self.subTest(section=name, event=event):
                        if event in ("PreToolUse", "PostToolUse"):
                            self.assertIn("hooks", entry, f"{name}.{event}: tool events need the matcher/hooks wrapper")
                            self.assertIn("matcher", entry)
                            for handler in entry["hooks"]:
                                self.assertIn("command", handler)
                        else:
                            self.assertIn("command", entry, f"{name}.{event}: lifecycle events take handlers directly")
                            self.assertNotIn("hooks", entry)


if __name__ == "__main__":
    unittest.main()
