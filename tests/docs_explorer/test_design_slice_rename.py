import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


class DesignSliceRenameTests(unittest.TestCase):
    def test_pack_exposes_design_slice_not_design_skill(self):
        self.assertTrue((REPO / "pack" / "commands" / "design-slice" / "SKILL.md").exists())
        self.assertFalse((REPO / "pack" / "commands" / "design" / "SKILL.md").exists())
        self.assertTrue((REPO / "pack" / "adapters" / "copilot" / "prompts" / "design-slice.prompt.md").exists())
        self.assertFalse((REPO / "pack" / "adapters" / "copilot" / "prompts" / "design.prompt.md").exists())

    def test_generated_surfaces_expose_design_slice_not_design(self):
        self.assertTrue((REPO / ".claude" / "skills" / "design-slice" / "SKILL.md").exists())
        self.assertFalse((REPO / ".claude" / "skills" / "design" / "SKILL.md").exists())
        self.assertTrue((REPO / ".github" / "prompts" / "design-slice.prompt.md").exists())
        self.assertFalse((REPO / ".github" / "prompts" / "design.prompt.md").exists())

    def test_skill_frontmatter_and_prompt_name_are_design_slice(self):
        skill = (REPO / "pack" / "commands" / "design-slice" / "SKILL.md").read_text(encoding="utf-8")
        prompt = (REPO / "pack" / "adapters" / "copilot" / "prompts" / "design-slice.prompt.md").read_text(encoding="utf-8")
        self.assertRegex(skill, r"(?m)^name:\s*design-slice$")
        self.assertIn("# Skill: /design-slice", skill)
        self.assertIn("**design-slice** workflow", prompt)

    def test_current_pack_sources_have_no_old_design_command_references(self):
        offenders = []
        patterns = [
            re.compile(r"(?<![\w-])/design(?=$|[\s`'\"),.;:<>])"),
            re.compile(r"\.claude/skills/design(?!-)"),
            re.compile(r"\.github/prompts/design\.prompt\.md\b"),
            re.compile(r"commands/design(?!-)"),
            re.compile(r"--skill design(?!-)"),
            re.compile(r'"skill"\s*:\s*"design"'),
        ]
        roots = [REPO / "pack", REPO / ".claude", REPO / ".github"]
        for root in roots:
            for path in root.rglob("*"):
                if path.is_dir() or path.suffix.lower() not in {".md", ".json", ".py", ".ps1", ".html"}:
                    continue
                if path.name in {"INSTALL.md"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for pattern in patterns:
                    if pattern.search(text):
                        offenders.append(f"{path.relative_to(REPO)} matches {pattern.pattern}")
        self.assertEqual([], offenders)

    def test_ui_design_name_is_unchanged(self):
        self.assertTrue((REPO / "pack" / "commands" / "ui-design" / "SKILL.md").exists())
        self.assertTrue((REPO / "pack" / "adapters" / "copilot" / "prompts" / "ui-design.prompt.md").exists())


if __name__ == "__main__":
    unittest.main()
