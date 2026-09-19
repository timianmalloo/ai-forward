"""Codex readiness is checked on deployed files, including damaged/older installs."""
import importlib.util
import json
import re
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "pack/scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / "pack/scripts"))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


apply = load("pack-apply")
doctor = load("pack-doctor")


class CodexSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.install()

    def install(self):
        apply.Applier(str(ROOT), str(self.root), dry=False, install=True,
                      baselines=False, project="Codex fixture").run()

    def check(self):
        return doctor.check_codex(str(self.root))

    def test_fresh_install_and_source_surface_match_complete_skills(self):
        for source in (ROOT / "pack/commands").rglob("*"):
            if source.is_file():
                rel = source.relative_to(ROOT / "pack/commands")
                self.assertEqual(source.read_bytes(), (self.root / ".agents/skills" / rel).read_bytes())
                self.assertEqual(source.read_bytes(), (ROOT / ".agents/skills" / rel).read_bytes())
        agents = (self.root / "AGENTS.md").read_text()
        self.assertIn("docs/ai-forward-pack/codex.md", agents)
        guide = (self.root / "docs/ai-forward-pack/codex.md").read_text()
        for term in ("$collectknowledge", "$specify", ".claude/knowledge/", "AGENTS.override.md"):
            self.assertIn(term, guide)
        inventory = "docs/ai-forward-pack/codex-skills.json"
        self.assertEqual(json.loads((ROOT / inventory).read_text()),
                         json.loads((self.root / inventory).read_text()))
        for source in (ROOT / "pack/scripts").glob("*.py"):
            self.assertEqual(source.read_bytes(),
                             (self.root / "docs/ai-forward-pack/scripts" / source.name).read_bytes())
        self.assertEqual("PASS", self.check()["status"])

    def test_repair_restores_missing_codex_files(self):
        shutil.rmtree(self.root / ".agents/skills")
        (self.root / "docs/ai-forward-pack/codex.md").unlink()
        self.assertEqual("FAIL", self.check()["status"])
        self.install()
        self.assertEqual("PASS", self.check()["status"])

    def test_previous_revision_update_regenerates_inventory(self):
        path = self.root / "docs/ai-forward-pack/codex-skills.json"
        expected = json.loads(path.read_text())
        old = dict(expected)
        old.pop("specify")
        path.write_text(json.dumps(old))
        install = self.root / "docs/ai-forward-pack/INSTALL.md"
        install.write_text(re.sub(r"(?m)^revision: (\d+)",
                                 lambda m: "revision: " + str(int(m[1]) - 1), install.read_text()))
        app = apply.Applier(str(ROOT), str(self.root), dry=True, baselines=False, project="Codex fixture")
        app.run()
        self.assertEqual(old, json.loads(path.read_text()), "preview must not write")
        rows = apply.Applier(str(ROOT), str(self.root), dry=False, baselines=False, project="Codex fixture").run()
        self.assertEqual(expected, json.loads(path.read_text()))
        self.assertFalse(any(r["action"] == "CONFLICT" and r["path"].endswith("codex-skills.json") for r in rows))

    def test_missing_skill_reference_constitution_or_script_fails(self):
        for rel in (".agents/skills/specify/SKILL.md",
                    ".agents/skills/ui-design/reference/flow.md",
                    ".claude/knowledge/agent-rules-of-the-road.md",
                    "docs/ai-forward-pack/scripts/audit-log.py",
                    "docs/ai-forward-pack/codex.md"):
            with self.subTest(path=rel):
                path = self.root / rel
                saved = path.read_bytes()
                path.unlink()
                result = self.check()
                self.assertEqual("FAIL", result["status"])
                self.assertIn(rel, result["detail"])
                path.write_bytes(saved)

    def test_empty_or_invalid_metadata_fails(self):
        path = self.root / ".agents/skills/specify/SKILL.md"
        for text in ("# specify", "---\nname: specify\ndescription: ''\n---\n",
                     "---\nname: wrong-name\ndescription: valid\n---\n"):
            with self.subTest(text=text):
                path.write_text(text)
                self.assertEqual("FAIL", self.check()["status"])

    def test_missing_skill_in_both_mirrors_is_not_a_false_pass(self):
        for host in (".agents", ".claude"):
            shutil.rmtree(self.root / host / "skills/specify")
        local = self.root / ".agents/skills/local-extra"
        local.mkdir()
        (local / "SKILL.md").write_text("---\nname: local-extra\ndescription: Local skill\n---\n")
        self.assertEqual("FAIL", self.check()["status"])

    def test_extra_local_skill_does_not_fail_pack_readiness(self):
        local = self.root / ".agents/skills/local-extra"
        local.mkdir()
        (local / "SKILL.md").write_text("---\nname: local-extra\ndescription: Local skill\n---\n")
        self.assertEqual("PASS", self.check()["status"])

    def test_invalid_inventory_fails_closed(self):
        path = self.root / "docs/ai-forward-pack/codex-skills.json"
        for text in ("{", "{}", '{"specify": ["SKILL.md", "../../outside"]}'):
            with self.subTest(text=text):
                path.write_text(text)
                self.assertEqual("FAIL", self.check()["status"])

    def test_override_reports_shadowing_without_overwriting_user_file(self):
        path = self.root / "AGENTS.override.md"
        path.write_text("Custom instructions\n")
        result = self.check()
        self.assertEqual("WARN", result["status"])
        self.assertIn("AGENTS.override.md", result["detail"])
        self.assertEqual("Custom instructions\n", path.read_text())


if __name__ == "__main__":
    unittest.main()
