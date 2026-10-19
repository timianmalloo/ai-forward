import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


class DecisionInterrogationSkillTests(unittest.TestCase):
    def read(self, relative):
        return (REPO / relative).read_text(encoding="utf-8")

    def test_TargetSkills_SharedContractAndClosure_AreWired(self):
        for name in ("specify", "ui-design", "define-architecture", "design-slice"):
            text = self.read(f"pack/commands/{name}/SKILL.md")
            self.assertIn("knowledge/decision-interrogation.md", text, name)
            self.assertIn("Question / Needed for / Recommendation", text, name)
            self.assertIn("one question at a time", text, name)

    def test_EarlyInterrogation_SpecifyAndUiDesign_IsIntrinsic(self):
        for name in ("specify", "ui-design"):
            text = self.read(f"pack/commands/{name}/SKILL.md")
            self.assertIn("During Stages 1-2", text, name)

    def test_SharedContract_FastPathAndSerialDialog_AreExplicit(self):
        text = self.read("pack/knowledge/decision-interrogation.md")
        self.assertIn("If no consequential question remains, continue", text)
        self.assertIn("| Question | Needed for | Recommendation |", text)
        self.assertIn("Ask one question at a time", text)
        self.assertRegex(text.lower(), r"ordinary\s+conversation")

    def test_SharedContract_OnlyTheHumanDecides_AndEachDecisionCarriesItsSource(self):
        # FR-106: the authoring skills run `runs_as: either`. As a Sub-Agent the skill's "human"
        # was its parent, so an agent's answer entered the artifact looking like a human decision.
        text = " ".join(self.read("pack/knowledge/decision-interrogation.md").split())
        self.assertIn("## DI7 - Only the human decides", text)
        self.assertIn("CO-S2", text)
        self.assertIn("is evidence, never a decision", text)
        self.assertIn("record resolved decisions in the artifact, each with its source", text)

    def test_CreateProposal_MarkdownHtmlAndMockupPaths_AreRequired(self):
        text = self.read("pack/commands/create-proposal/SKILL.md")
        self.assertIn("docs/proposals/<slug>.md", text)
        self.assertIn("docs/proposals/<slug>.html", text)
        self.assertIn("docs/mockups/", text)
        self.assertIn("render-markdown.py", text)

    def test_CollectKnowledge_NativeDeepResearchWithVerification_IsRequired(self):
        text = self.read("pack/commands/collectknowledge/SKILL.md")
        self.assertIn("native deep-research capability", text)
        self.assertIn("open and verify the cited primary sources", text)

    def test_MarkdownCompanion_GlobalRule_UsesDeterministicRenderer(self):
        text = self.read("pack/knowledge/knowledge-visualization.md")
        self.assertIn("V19 — Human-facing Markdown has an HTML companion", text)
        self.assertIn("scripts/render-markdown.py", text)


if __name__ == "__main__":
    unittest.main()
