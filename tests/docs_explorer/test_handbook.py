"""Reader-first publishing contracts with real local source files and no model calls."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location("build_handbook", ROOT / "tools/build-handbook.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class HandbookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "web/handbook", self.root / "web/handbook")
        shutil.copytree(ROOT / "pack/commands", self.root / "pack/commands")
        shutil.copytree(ROOT / "pack/knowledge", self.root / "pack/knowledge")
        self.api = module()

    def test_build_covers_every_skill_and_knowledge_area(self):
        outputs, report = self.api.build(self.root)
        expected = {p.parent.name for p in (self.root / "pack/commands").glob("*/SKILL.md")}
        coverage = json.loads(outputs["docs/handbook/coverage.json"])
        self.assertEqual(expected, {row["skill"] for row in coverage["skills"]})
        knowledge = {p.stem for p in (self.root / "pack/knowledge").glob("*.md") if p.stem != "FOUNDATION"}
        guides = list((self.root / "web/handbook/guides").glob("*.md"))
        self.assertEqual(len(knowledge), report["knowledge_docs"])
        self.assertEqual(len(expected) + len(guides), report["pages"])
        self.assertIn("Build with AI agents", outputs["docs/portal/index.html"])
        self.assertNotIn('src="https://', outputs["docs/portal/index.html"])
        self.assertEqual(outputs, self.api.build(self.root)[0])

    def test_missing_skill_guide_fails_instead_of_creating_an_empty_card(self):
        (self.root / "web/handbook/skills/compile.md").unlink()
        with self.assertRaisesRegex(ValueError, "HANDBOOK-SKILL-COVERAGE"):
            self.api.build(self.root)

    def test_broken_routes_and_missing_knowledge_coverage_fail(self):
        path = self.root / "web/handbook/navigation.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["capabilities"][0]["sources"].pop()
        path.write_text(json.dumps(data), encoding="utf-8", newline="\n")
        with self.assertRaisesRegex(ValueError, "HANDBOOK-KNOWLEDGE-COVERAGE"):
            self.api.build(self.root)

    def test_script_breakout_text_is_encoded_as_data(self):
        path = self.root / "web/handbook/guides/overview.md"
        attack = '</script><script>window.handbookInjected=true</script>'
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write("\n\n" + attack + "\n")
        outputs, _ = self.api.build(self.root)
        html = outputs["docs/portal/index.html"]
        self.assertNotIn(attack, html)
        self.assertIn("\\u003c/script", html)


if __name__ == "__main__":
    unittest.main()
