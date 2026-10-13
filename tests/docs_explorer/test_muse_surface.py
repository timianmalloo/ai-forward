"""Muse surface: the sixth harness reads the pack through the shared
.agents/skills surface plus its own path map (docs/ai-forward-pack/muse-surface.md).

Filesystem-only, like the Codex check: this pins that the deployed contract is
present and repairable. It never claims a running Muse catalog was queried -
that qualification lives in the surface doc's table (CO12).
"""
import importlib.util
import json
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

SURFACE_TERMS = (
    ".agents/skills/<name>/SKILL.md",
    ".claude/knowledge/<name>.md",
    "read_skill",
    "AGENTS.md takes precedence",
    "unsupported",
    "observed-only",
    "py -3",
)


class MuseSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.install()

    def install(self):
        apply.Applier(str(ROOT), str(self.root), dry=False, install=True,
                      baselines=False, project="Muse fixture").run()

    def check(self):
        return doctor.check_muse(str(self.root))

    def test_fresh_install_and_source_surface_match(self):
        source = ROOT / "pack/adapters/muse/muse-surface.md"
        installed = self.root / "docs/ai-forward-pack/muse-surface.md"
        self.assertTrue(source.is_file(), "pack/adapters/muse/muse-surface.md is missing")
        self.assertEqual(source.read_bytes(), installed.read_bytes())
        self.assertEqual(source.read_bytes(),
                         (ROOT / "docs/ai-forward-pack/muse-surface.md").read_bytes())
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("docs/ai-forward-pack/muse-surface.md", agents)
        guide = installed.read_text(encoding="utf-8")
        for term in SURFACE_TERMS:
            self.assertIn(term, guide)
        self.assertEqual("PASS", self.check()["status"])

    def test_missing_surface_or_pointer_fails(self):
        for rel in ("docs/ai-forward-pack/muse-surface.md",
                    ".agents/skills/specify/SKILL.md",
                    ".claude/knowledge/agent-rules-of-the-road.md",
                    "docs/ai-forward-pack/scripts/audit-log.py"):
            with self.subTest(path=rel):
                path = self.root / rel
                saved = path.read_bytes()
                path.unlink()
                result = self.check()
                self.assertEqual("FAIL", result["status"])
                self.assertIn(rel, result["detail"])
                path.write_bytes(saved)

    def test_missing_agents_pointer_fails(self):
        path = self.root / "AGENTS.md"
        saved = path.read_bytes()
        path.write_text(saved.decode("utf-8").replace(
            "docs/ai-forward-pack/muse-surface.md", "docs/ai-forward-pack/gone.md"),
            encoding="utf-8", newline="\n")
        result = self.check()
        self.assertEqual("FAIL", result["status"])
        self.assertIn("AGENTS.md does not direct Muse", result["detail"])
        path.write_bytes(saved)

    def test_invalid_manifest_or_metadata_fails_closed(self):
        manifest = self.root / "docs/ai-forward-pack/codex-skills.json"
        saved = manifest.read_bytes()
        for text in ("{", "{}", '{"specify": ["SKILL.md", "../../outside"]}'):
            with self.subTest(text=text):
                manifest.write_text(text, encoding="utf-8", newline="\n")
                self.assertEqual("FAIL", self.check()["status"])
        manifest.write_bytes(saved)
        skill = self.root / ".agents/skills/specify/SKILL.md"
        saved_skill = skill.read_bytes()
        skill.write_text("---\nname: wrong-name\ndescription: valid\n---\n",
                         encoding="utf-8", newline="\n")
        self.assertEqual("FAIL", self.check()["status"])
        skill.write_bytes(saved_skill)

    def test_repair_restores_missing_surface(self):
        (self.root / "docs/ai-forward-pack/muse-surface.md").unlink()
        self.assertEqual("FAIL", self.check()["status"])
        self.install()
        self.assertEqual("PASS", self.check()["status"])

    def test_extra_local_skill_does_not_fail(self):
        local = self.root / ".agents/skills/local-extra"
        local.mkdir()
        (local / "SKILL.md").write_text(
            "---\nname: local-extra\ndescription: Local skill\n---\n",
            encoding="utf-8", newline="\n")
        self.assertEqual("PASS", self.check()["status"])

    def test_muse_context_profile_is_recorded(self):
        cfg = json.loads((ROOT / "pack/context-budget.json").read_text(encoding="utf-8"))
        profile = cfg.get("muse_profile")
        self.assertIsInstance(profile, dict, "pack/context-budget.json has no muse_profile")
        self.assertEqual(profile["skills_source"], ".agents/skills")
        self.assertEqual(profile["catalog_cap_bytes"], 32768)
        self.assertIn("qualified_with", profile)
        inventory = json.loads(
            (ROOT / "docs/ai-forward-pack/codex-skills.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["skills_count"], len(inventory))
        self.assertEqual(profile["agents_md_bytes"], (ROOT / "AGENTS.md").stat().st_size)


if __name__ == "__main__":
    unittest.main()
