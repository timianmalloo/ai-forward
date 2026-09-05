"""pack-apply.py is the deployment map as a program. These tests pin the properties that used to
depend on someone remembering them: a doc whose load scope moved loses its stale wrapped copy;
CLAUDE.md is converted to the @AGENTS.md import with a backup and its unique paragraphs kept;
a repo-local parity control encoding the old invariant is rewritten into a shim that keeps its
other assertions; a repo-local deviation over an unchanged pack file is kept; docs/docs-index.js
is never touched; plan writes nothing; apply is idempotent; a fresh install needs --install."""
import importlib.util
import json
import os
import pathlib
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "pack" / "scripts" / "pack-apply.py"

spec = importlib.util.spec_from_file_location("pack_apply", SCRIPT)
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)

PARITY = """#requires -Version 7.0
# asserts the standing-method block is identical in AGENTS.md and CLAUDE.md
$agentsBlock = Get-Block -Path $agents
$claudeBlock = Get-Block -Path $claude
Assert-True ($null -ne $claudeBlock) 'CLAUDE.md carries a delimited standing-method block.'
foreach ($required in 'Generalize before you commit', 'Derive, don''t duplicate') {
    Assert-True ($agentsBlock.Contains($required)) "states '$required'."
}
$surfaces = @(
    @{ Path = '.claude/skills/implement/SKILL.md'; Needle = 'Generalized, not point-wise' }
)
"""


def _w(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return p


def _r(root, rel):
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def _rows(rows):
    return {(r["path"], r["action"]) for r in rows}


class InstalledRepoTests(unittest.TestCase):
    """A target that already carries the pack at the source revision, in the OLD shapes."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        install = (ROOT / "pack" / "adapters" / "INSTALL.md").read_text(encoding="utf-8")
        _w(self.tmp, "docs/ai-forward-pack/INSTALL.md", install)
        agents_block = (ROOT / "pack" / "adapters" / "managed-blocks" / "AGENTS.block.md").read_text(encoding="utf-8")
        self.old_claude = ("# CLAUDE.md\n\nRepo prose shared with AGENTS.md.\n\n"
                           "**Only in CLAUDE.md:** a repo-local note that must survive.\n\n"
                           "<!-- STANDING-METHOD:BEGIN -->\nGeneralize before you commit. Derive, don't duplicate.\n<!-- STANDING-METHOD:END -->\n\n"
                           + agents_block.replace(".github/instructions/no-guessing-protocol.instructions.md", ".claude/knowledge/no-guessing-protocol.md"))
        _w(self.tmp, "CLAUDE.md", self.old_claude)
        _w(self.tmp, "AGENTS.md", "# AGENTS.md\n\nRepo prose shared with AGENTS.md.\n\n"
                                  "<!-- STANDING-METHOD:BEGIN -->\nGeneralize before you commit. Derive, don't duplicate.\n<!-- STANDING-METHOD:END -->\n\n"
                                  "<!-- AI-FORWARD-PACK:BEGIN (old) -->\nold block\n<!-- AI-FORWARD-PACK:END -->\n\n## After the block\n\nkept.\n")
        _w(self.tmp, ".github/instructions/ui-design-craft.instructions.md", "---\napplyTo: \"**/*.html\"\n---\nstale wrapped copy")
        _w(self.tmp, ".github/instructions/repo-local.instructions.md", "---\napplyTo: \"**\"\n---\nrepo-authored, not the pack's")
        _w(self.tmp, "docs/docs-index.js", "window.DOCS_INDEX = {accumulated: true};")
        _w(self.tmp, "docs/index.html", "<html>existing explorer</html>")
        _w(self.tmp, "scripts/test-standing-method-parity.ps1", PARITY)
        _w(self.tmp, ".claude/settings.json", json.dumps({"permissions": {"allow": ["Bash(git status)"]}}))
        _w(self.tmp, ".gitignore", "bin/\n")
        # a repo-local deviation over a pack file that is unchanged between revisions
        also = (ROOT / "pack" / "commands" / "also" / "SKILL.md").read_text(encoding="utf-8")
        _w(self.tmp, ".claude/skills/also/SKILL.md", also + "\n**Repo-local addition** kept by the deviation register.\n")

    def _apply(self, dry=False, **kw):
        app = pa.Applier(str(ROOT), self.tmp, dry=dry, force=True, baselines=False, **kw)
        return app.run()

    def test_plan_writes_nothing(self):
        before = {}
        for base, _d, files in os.walk(self.tmp):
            for f in files:
                p = os.path.join(base, f)
                before[p] = os.path.getmtime(p), os.path.getsize(p)
        rows = self._apply(dry=True)
        after = {}
        for base, _d, files in os.walk(self.tmp):
            for f in files:
                p = os.path.join(base, f)
                after[p] = os.path.getmtime(p), os.path.getsize(p)
        self.assertEqual(before, after, "plan must not touch the target")
        self.assertIn(("CLAUDE.md", "CONVERT"), _rows(rows))

    def test_apply_converts_claude_md_and_keeps_what_is_unique(self):
        rows = self._apply()
        claude = _r(self.tmp, "CLAUDE.md")
        self.assertTrue(claude.startswith("# CLAUDE.md\n\n@AGENTS.md\n"))
        self.assertIn("a repo-local note that must survive", claude)
        self.assertNotIn("Repo prose shared with AGENTS.md", claude, "shared prose lives in AGENTS.md only")
        self.assertNotIn("STANDING-METHOD:BEGIN", claude, "the standing method lives once, in AGENTS.md")
        self.assertEqual(1, claude.count("AI-FORWARD-PACK:BEGIN"))
        self.assertIn("## Claude Code", claude)
        backup = _r(self.tmp, "docs/ai-forward-pack/retired/CLAUDE.md.rev{0}.md".format(pa.Applier(str(ROOT), self.tmp, dry=True).target_rev))
        self.assertEqual(self.old_claude, backup)
        agents = _r(self.tmp, "AGENTS.md")
        self.assertNotIn("old block", agents)
        self.assertEqual(1, agents.count("AI-FORWARD-PACK:BEGIN"))
        self.assertIn("## After the block\n\nkept.", agents, "text after the block survives with its blank line")
        self.assertIn(("AGENTS.md", "UPDATE"), _rows(rows))

    def test_stale_wrapped_copy_is_removed_and_repo_local_instruction_is_kept(self):
        rows = self._apply()
        self.assertFalse(os.path.exists(os.path.join(self.tmp, ".github/instructions/ui-design-craft.instructions.md")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, ".github/knowledge/ui-design-craft.md")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, ".github/instructions/repo-local.instructions.md")))
        self.assertIn((".github/instructions/ui-design-craft.instructions.md", "REMOVE"), _rows(rows))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, ".github/instructions/no-guessing-protocol.instructions.md")))

    def test_parity_control_is_rewritten_into_a_shim_with_its_other_assertions(self):
        rows = self._apply()
        shim = _r(self.tmp, "scripts/test-standing-method-parity.ps1")
        self.assertIn("pack-apply shim", shim)
        self.assertIn("@AGENTS", shim)
        self.assertIn("Generalized, not point-wise", shim, "skill-surface needle carried over")
        self.assertIn("Generalize before you commit", shim, "required phrase carried over")
        self.assertIn("Derive, don''t duplicate", shim)
        self.assertEqual(PARITY, _r(self.tmp, "docs/ai-forward-pack/retired/test-standing-method-parity.ps1"))
        self.assertIn(("scripts/test-standing-method-parity.ps1", "REWRITE"), _rows(rows))

    def test_protected_and_existing_surfaces_are_untouched(self):
        self._apply()
        self.assertEqual("window.DOCS_INDEX = {accumulated: true};", _r(self.tmp, "docs/docs-index.js"))
        self.assertEqual("<html>existing explorer</html>", _r(self.tmp, "docs/index.html"))

    def test_settings_and_gitignore_are_merged_not_replaced(self):
        self._apply()
        cfg = json.loads(_r(self.tmp, ".claude/settings.json"))
        self.assertEqual(["Bash(git status)"], cfg["permissions"]["allow"])
        self.assertTrue(cfg["showThinkingSummaries"])
        self.assertIn("PreToolUse", cfg["hooks"])
        gi = _r(self.tmp, ".gitignore")
        self.assertTrue(gi.startswith("bin/\n"))
        for line in pa.GITIGNORE_LINES:
            self.assertIn(line, gi)

    def test_repo_local_deviation_over_unchanged_pack_file_is_kept(self):
        rows = self._apply()
        self.assertIn("Repo-local addition", _r(self.tmp, ".claude/skills/also/SKILL.md"))
        self.assertIn((".claude/skills/also/SKILL.md", "KEEP"), _rows(rows))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, ".claude/skills/ui-design/reference/flow.md")), "whole skill directories land")
        self.assertTrue(os.path.exists(os.path.join(self.tmp, ".github/agents/test-architect.agent.md")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, ".github/hooks/ai-forward.json")))

    def test_second_apply_is_a_no_op(self):
        self._apply()
        rows = self._apply()
        changing = [r for r in rows if r["action"] not in ("UNCHANGED", "SKIP", "KEEP")]
        self.assertEqual([], changing, changing)


class FreshAndGuardTests(unittest.TestCase):
    def test_fresh_target_needs_install_flag(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        rows = pa.Applier(str(ROOT), tmp, dry=True).run()
        self.assertEqual(1, len(rows))
        self.assertEqual("fail", rows[0]["status"])
        rows = pa.Applier(str(ROOT), tmp, dry=False, install=True, baselines=False, project="Demo").run()
        self.assertTrue(os.path.exists(os.path.join(tmp, "CLAUDE.md")))
        self.assertTrue(os.path.exists(os.path.join(tmp, "docs/index.html")), "Docs Explorer instantiated on a fresh install")
        self.assertIn("# Demo", _r(tmp, "AGENTS.md"))
        self.assertTrue(os.path.exists(os.path.join(tmp, "docs/ai-forward-pack/INSTALL.md")))
        self.assertFalse(os.path.exists(os.path.join(tmp, "docs/docs-index.js")), "never seeded (V10)")

    def test_source_repo_is_already_current(self):
        rows = pa.Applier(str(ROOT), str(ROOT), dry=True, baselines=False).run()
        self.assertIn(("revision", "UNCHANGED"), _rows(rows))
        bad = [r for r in rows if r["action"] not in ("UNCHANGED", "SKIP", "KEEP")]
        self.assertEqual([], bad, "the applier agrees with sync-pack on the source repo: " + str(bad[:5]))

    def test_strip_tools_and_normalise(self):
        self.assertEqual("---\nname: x\n---\nbody", pa.strip_tools("---\nname: x\ntools: [Read,\n  Grep]\n---\nbody"))
        self.assertEqual(pa.normalise("see `.github/instructions/rigor-protocol.instructions.md` now"),
                         pa.normalise("see `.claude/knowledge/rigor-protocol.md`   now"))


if __name__ == "__main__":
    unittest.main()
