"""Grok Build is a third host (revision 71). Native destinations are
`.grok/{skills,agents,hooks,rules}`; knowledge is NOT copied into `.grok/rules/`
(CTX-B). These tests pin the map before the live install exists.
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
spec = importlib.util.spec_from_file_location("pack_apply_grok", SCRIPT)
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)


def _r(root, rel):
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return fh.read()


class GrokAgentFilenameTests(unittest.TestCase):
    def test_claude_code_names_are_unchanged(self):
        self.assertEqual("orchestrator.md", pa.grok_agent_filename("orchestrator.md"))
        self.assertEqual("ux-researcher-ia.md", pa.grok_agent_filename("ux-researcher-ia.md"))

    def test_copilot_source_suffix_is_stripped(self):
        self.assertEqual("csharp-developer.md",
                         pa.grok_agent_filename("csharp-developer_agent.md"))
        self.assertEqual("the-simplifier.md",
                         pa.grok_agent_filename("the-simplifier_agent.md"))


class GrokInstallTests(unittest.TestCase):
    def test_fresh_install_deploys_the_grok_surface(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        pa.Applier(str(ROOT), tmp, dry=False, install=True, baselines=False, project="Demo").run()

        self.assertTrue(os.path.isfile(os.path.join(tmp, ".grok", "skills", "specify", "SKILL.md")))
        self.assertTrue(
            os.path.isfile(os.path.join(tmp, ".grok", "skills", "implement", "SKILL.md")),
            "pack /implement overrides bundled /implement in a pack-installed repo",
        )
        flow = os.path.join(tmp, ".grok", "skills", "ui-design", "reference", "flow.md")
        self.assertTrue(os.path.isfile(flow), "whole skill directories land, including reference/")

        self.assertTrue(os.path.isfile(os.path.join(tmp, ".grok", "agents", "orchestrator.md")))
        self.assertTrue(os.path.isfile(os.path.join(tmp, ".grok", "agents", "csharp-developer.md")),
                        "_agent suffix stripped so spawn_subagent type matches persona name")
        self.assertFalse(os.path.isfile(os.path.join(tmp, ".grok", "agents", "csharp-developer_agent.md")))

        orch = _r(tmp, ".grok/agents/orchestrator.md")
        self.assertIsNotNone(orch)
        self.assertNotRegex(orch, r"(?m)^tools:", "Claude tools: vocabulary is stripped at the Grok boundary")

        self.assertTrue(os.path.isfile(os.path.join(tmp, ".grok", "hooks", "ai-forward.json")))
        hooks = json.loads(_r(tmp, ".grok/hooks/ai-forward.json"))
        commands = json.dumps(hooks)
        self.assertIn("--host grok", commands)
        self.assertIn("reread-guard.py", commands)
        self.assertIn("session-start.py", commands)

        rules = _r(tmp, ".grok/rules/grok-surface.md")
        self.assertIsNotNone(rules)
        self.assertIn(".grok/skills/", rules)
        self.assertIn(".claude/knowledge/", rules)
        self.assertNotIn("applyTo:", rules, "Copilot wraps must not be the Grok knowledge path")

        rules_dir = os.path.join(tmp, ".grok", "rules")
        extra = [f for f in os.listdir(rules_dir) if f.endswith(".md") and f != "grok-surface.md"]
        self.assertEqual([], extra, "knowledge docs must not land in .grok/rules/ (CTX-B): %s" % extra)
