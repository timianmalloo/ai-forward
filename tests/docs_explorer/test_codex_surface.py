"""Native Codex installation must survive a fresh clone and consumer refresh."""
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import shutil
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("pack_apply_codex", ROOT / "pack/scripts/pack-apply.py")
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)


class CodexInstallTests(unittest.TestCase):
    def test_native_skills_references_personas_and_hooks_reach_consumer(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            applier = pa.Applier(str(ROOT), tmp, dry=False, install=True, baselines=False, project="Demo")
            applier.run()
            for source in (ROOT / "pack/commands").rglob("*"):
                if source.is_file() and "__pycache__" not in source.parts:
                    installed = target / ".agents/skills" / source.relative_to(ROOT / "pack/commands")
                    self.assertTrue(installed.is_file(), str(installed))
            self.assertTrue((target / ".codex/agents/orchestrator.toml").is_file())
            self.assertTrue((target / ".codex/agents/the-simplifier.toml").is_file())
            self.assertIn("Codex", (target / "AGENTS.md").read_text(encoding="utf-8"))
            hooks = json.loads((target / ".codex/hooks.json").read_text(encoding="utf-8"))
            self.assertIn("SessionStart", hooks["hooks"])
            self.assertIn("PreToolUse", hooks["hooks"])
            self.assertIn("!.agents/skills/", (target / ".gitignore").read_text(encoding="utf-8"))

    def test_repeated_install_preserves_unrelated_codex_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            config = target / ".codex/config.toml"
            config.parent.mkdir()
            config.write_text('[features]\nhooks = false\n', encoding="utf-8")
            hookfile = target / ".codex/hooks.json"
            custom = {"description": "Consumer hooks", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo local"}]}]}}
            hookfile.write_text(json.dumps(custom), encoding="utf-8")
            for _ in range(2):
                pa.Applier(str(ROOT), tmp, dry=False, install=True, baselines=False, project="Demo").run()
            result = json.loads(hookfile.read_text(encoding="utf-8"))
            self.assertEqual(custom["hooks"]["Stop"], result["hooks"]["Stop"])
            self.assertEqual("Consumer hooks", result["description"])
            self.assertEqual(1, len(result["hooks"]["SessionStart"]))
            self.assertEqual('[features]\nhooks = false\n', config.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

class CodexProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("codex_projection_test", ROOT / "pack/adapters/codex/render.py")
        cls.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.adapter)

    def test_every_persona_is_valid_toml_and_retains_full_body(self):
        projected = self.adapter.projections(ROOT / "pack")
        agents = [(relative, source, text) for relative, (source, text) in projected.items()
                  if relative.startswith(".codex/agents/")]
        sources = list((ROOT / "pack/adapters/claude-code/agents").glob("*.md")) + list((ROOT / "pack/adapters/copilot/agents").glob("*_agent.md"))
        self.assertEqual(len(sources), len(agents))
        for relative, source, text in agents:
            parsed = tomllib.loads(text)
            front, body = self.adapter.split_frontmatter((ROOT / "pack" / source).read_text(encoding="utf-8"))
            self.assertEqual(self.adapter.field(front, "name"), parsed["name"])
            self.assertEqual(self.adapter.field(front, "description"), parsed["description"])
            self.assertTrue(parsed["developer_instructions"].endswith(body.lstrip()))
            self.assertEqual({"name", "description", "developer_instructions"}, set(parsed))

    def test_guidance_only_refresh_uses_historical_projection_and_preserves_local_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            target = Path(tmp) / "consumer"
            source.mkdir()
            target.mkdir()
            def git(*args):
                return subprocess.run(["git", *args], cwd=source, capture_output=True, text=True, check=True).stdout.strip()
            git("init", "-q")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "user.name", "Fixture")
            adapter_dir = source / "pack/adapters/codex"
            adapter_dir.mkdir(parents=True)
            shutil.copyfile(ROOT / "pack/adapters/codex/render.py", adapter_dir / "render.py")
            guide = adapter_dir / "surface.md"
            guide.write_text("OLD GUIDANCE\n", encoding="utf-8")
            canonical = source / "pack/commands/demo/SKILL.md"
            canonical.parent.mkdir(parents=True)
            body = "---\nname: demo\ndescription: demo\n---\n\nBODY\n\nEND\n"
            canonical.write_text(body, encoding="utf-8")
            git("add", ".")
            git("commit", "-qm", "old projection")
            old_sha = git("rev-parse", "HEAD")
            installed = target / ".agents/skills/demo/SKILL.md"
            installed.parent.mkdir(parents=True)
            installed.write_text(self.adapter.skill_text(body, "OLD GUIDANCE\n") + "\nLOCAL NOTE\n", encoding="utf-8")
            guide.write_text("NEW GUIDANCE\n", encoding="utf-8")
            applier = pa.Applier(str(source), str(target), dry=False, install=True, baselines=False)
            applier.source_rev, applier.target_rev, applier.old_pack_sha = 73, 72, old_sha
            new = self.adapter.skill_text(body, "NEW GUIDANCE\n")
            applier.place("codex", "commands/demo/SKILL.md", str(installed), new)
            result = installed.read_text(encoding="utf-8")
            self.assertIn("NEW GUIDANCE", result)
            self.assertNotIn("OLD GUIDANCE", result)
            self.assertIn("LOCAL NOTE", result)
            self.assertEqual("MERGE", applier.rows[-1]["action"])

    def test_missing_changed_and_extra_files_all_fail_consistency(self):
        spec = importlib.util.spec_from_file_location("consistency_codex_test", ROOT / "tools/check-consistency.py")
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            pa.Applier(str(ROOT), tmp, dry=False, install=True, baselines=False, project="Demo").run()
            checker.ROOT, checker.PACK = tmp, str(ROOT / "pack")
            findings = []
            checker.check_codex_surface(findings)
            self.assertEqual([], findings)
            changed = target / ".agents/skills/specify/SKILL.md"
            changed.write_text("wrong", encoding="utf-8")
            missing = target / ".codex/agents/orchestrator.toml"
            missing.unlink()
            extra = target / ".agents/skills/specify/stale.md"
            extra.write_text("stale", encoding="utf-8")
            checker.check_codex_surface(findings)
            for name in ("specify/SKILL.md", "orchestrator.toml", "stale.md"):
                self.assertTrue(any(name in finding for finding in findings), findings)

    def test_modified_pack_hook_conflicts_instead_of_duplicate_or_overwrite(self):
        snippet = json.loads((ROOT / "pack/adapters/hooks/codex.hooks.json").read_text(encoding="utf-8"))
        current = json.loads(json.dumps(snippet))
        current["hooks"]["SessionStart"][0]["hooks"][0]["timeout"] = 99
        with self.assertRaisesRegex(ValueError, "modified pack hook"):
            self.adapter.merge_hooks(current, snippet)

    def test_doctor_reports_invalid_hook_shape_without_crashing(self):
        spec = importlib.util.spec_from_file_location("codex_doctor_test", ROOT / "pack/scripts/pack-doctor.py")
        doctor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(doctor)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            pa.Applier(str(ROOT), tmp, dry=False, install=True, baselines=False, project="Demo").run()
            for invalid in ([], None):
                (target / ".codex/hooks.json").write_text(json.dumps({"hooks": invalid}), encoding="utf-8")
                result = doctor.check_codex_surface(tmp)
                self.assertEqual("FAIL", result["status"])
                self.assertIn("hooks must be an object", result["detail"])
