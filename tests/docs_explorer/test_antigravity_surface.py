"""Antigravity (agy) is a fourth host (revision 72). Native destinations are
`.agents/{skills,rules,hooks.json,skills.json}`; knowledge is read on-demand
from `.claude/knowledge/` (CTX-B). These tests pin the map before the live install exists.
"""
import importlib.util
import json
import os
import pathlib
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "pack" / "scripts" / "pack-apply.py"
spec = importlib.util.spec_from_file_location("pack_apply_agy", SCRIPT)
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)


def _r(root, rel):
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return fh.read()


class AntigravityInstallTests(unittest.TestCase):
    def test_fresh_install_deploys_the_antigravity_surface(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        pa.Applier(str(ROOT), tmp, dry=False, install=True, baselines=False, project="Demo").run()

        self.assertTrue(os.path.isfile(os.path.join(tmp, ".agents", "skills", "specify", "SKILL.md")),
                        "specify skill must land under .agents/skills/")
        self.assertTrue(os.path.isfile(os.path.join(tmp, ".agents", "skills", "implement", "SKILL.md")),
                        "implement skill must land under .agents/skills/")
        flow = os.path.join(tmp, ".agents", "skills", "ui-design", "reference", "flow.md")
        self.assertTrue(os.path.isfile(flow), "whole skill directories land under .agents/skills/, including reference/")

        self.assertTrue(os.path.isfile(os.path.join(tmp, ".agents", "skills.json")),
                        ".agents/skills.json must be deployed for explicit agy discovery")
        skills_cfg = json.loads(_r(tmp, ".agents/skills.json"))
        entries = [e.get("path") for e in skills_cfg.get("entries", [])]
        self.assertTrue(any(".agents/skills" in str(e) or ".claude/skills" in str(e) for e in entries),
                        "skills.json must declare skills path")

        self.assertTrue(os.path.isfile(os.path.join(tmp, ".agents", "hooks.json")),
                        ".agents/hooks.json must be deployed")
        hooks = json.loads(_r(tmp, ".agents/hooks.json"))
        commands = json.dumps(hooks)
        self.assertIn("--host agy", commands)
        self.assertIn("reread-guard.py", commands)
        self.assertIn("session-start.py", commands)

        rules = _r(tmp, ".agents/rules/agy-surface.md")
        self.assertIsNotNone(rules, ".agents/rules/agy-surface.md must exist")
        self.assertIn(".agents/skills/", rules)
        self.assertIn(".claude/knowledge/", rules)
        self.assertNotIn("applyTo:", rules, "Copilot wraps must not be the agy knowledge path")


if __name__ == "__main__":
    unittest.main()
