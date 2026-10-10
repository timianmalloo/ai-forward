"""Real deployment proof for the single delivery entry point."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DeliveryDeploymentTests(unittest.TestCase):
    def test_fresh_deployment_exposes_same_complete_deliver_on_every_surface(self):
        with tempfile.TemporaryDirectory(prefix="adoption project ") as directory:
            target = Path(directory)
            agents = "# Project rules\n\nKeep the product's own requirements.\n"
            (target / "AGENTS.md").write_text(agents, encoding="utf-8", newline="\n")
            result = subprocess.run(
                [sys.executable, str(ROOT / "pack/scripts/pack-apply.py"),
                 "apply", "--source", str(ROOT), "--target", str(target),
                 "--install", "--no-baselines", "--json"],
                capture_output=True, text=True, encoding="utf-8", timeout=90,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            source = ROOT / "pack/commands/deliver"
            for surface in (".claude/skills", ".grok/skills", ".agents/skills"):
                with self.subTest(surface=surface):
                    installed = target / surface / "deliver/SKILL.md"
                    self.assertTrue(installed.is_file(), "The one-command skill must actually be installed")
                    self.assertEqual(digest(installed), digest(source / "SKILL.md"))
                    for companion in source.rglob("*"):
                        if companion.is_file():
                            projected = target / surface / "deliver" / companion.relative_to(source)
                            self.assertTrue(projected.is_file(), "A resumable workflow must not lose its references")
                            self.assertEqual(digest(projected), digest(companion))
            prompt = target / ".github/prompts/deliver.prompt.md"
            self.assertTrue(prompt.is_file(), "Copilot needs the entry point too")
            self.assertEqual(digest(prompt), digest(ROOT / "pack/adapters/copilot/prompts/deliver.prompt.md"))
            self.assertIn(agents.strip(), (target / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertFalse((target / "docs/docs-index.js").exists(), "Onboarding must not invent a product graph")
            self.assertFalse((target / "docs/audit").exists(), "Onboarding must preserve audit opt-in")
            self.assertFalse((target / ".git").exists(), "Installing a pack does not authorize git-init")


if __name__ == "__main__":
    unittest.main()
