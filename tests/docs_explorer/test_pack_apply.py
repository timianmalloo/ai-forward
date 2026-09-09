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
import re
import shutil
import subprocess
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

# INSTALL.md's frontmatter `changes:` list is an append-only HISTORY of shipped revisions,
# replayed in order by a repo catching up. Rewriting a past entry would falsify the record,
# and a later entry already carries the correction -- so both gates below read the BODY.
def install_body(text):
    return text.split(chr(10) + "---" + chr(10), 1)[-1]



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


class GitignoreDoesNotReverseARepoDecision(unittest.TestCase):
    """A blanket appended below an existing rule wins by git's last-match rule.

    Measured in a consuming repo on 2026-09-09: `.gitignore` line 495 recorded *"spikes/ is
    NOT ignored in this repo (pack default overridden): a contract labelled Verified must
    cite committed, re-runnable spike evidence (Test Architect gate, 2026-08-26)"*. The
    pack's INSTALL-2 block re-appended a blanket `spikes/` twenty-nine lines later and won.
    117 tracked spike files became reachable only with `git add -f` -- and a forgotten `-f`
    loses evidence with NO signature: `git add -A` drops a new ignored file silently, git
    status never lists it, and the commit succeeds.

    The defect is the mechanism, not the default. `INSTALL.md` has always carried the
    condition -- *"add `spikes/` to `.gitignore` **unless a probe is worth keeping as
    evidence**"* -- and the script applied it unconditionally. A repo that TRACKS files
    under `spikes/` has already answered that question in the only way git records an answer.

    Written to fail first; every test here failed on 2026-09-09 against the plain append.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        _w(self.tmp, ".gitignore", "bin/\n")

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.tmp, capture_output=True, text=True)

    def _init_repo(self):
        self._git("init", "-q")
        self._git("config", "user.email", "t@example.invalid")
        self._git("config", "user.name", "t")

    def _apply(self):
        return pa.Applier(str(ROOT), self.tmp, dry=False, force=True, install=True,
                          baselines=False, project="Demo").run()

    def _gitignore_rows(self, rows):
        return [r for r in rows if r["path"] == ".gitignore"]

    def test_the_default_still_applies_to_a_repo_with_no_spikes(self):
        """Proportionality: the pack default is right for repos that treat spikes/ as scratch."""
        self._init_repo()
        self._apply()
        self.assertIn("spikes/", _r(self.tmp, ".gitignore"))

    def test_a_repo_that_tracks_spikes_does_not_get_the_blanket(self):
        """THE finding, and the condition INSTALL.md already states."""
        self._init_repo()
        _w(self.tmp, "spikes/mcp/probe.md", "committed spike evidence\n")
        self._git("add", "-A")
        self._git("commit", "-qm", "spike evidence")
        rows = self._apply()
        text = _r(self.tmp, ".gitignore")
        self.assertNotIn("\nspikes/\n", "\n" + text,
                         "a repo tracking spike evidence must not have it ignored under it")
        self.assertTrue(any(r["action"] == "KEEP" and "spikes/" in r["note"]
                            for r in self._gitignore_rows(rows)),
                        "and the withholding must be REPORTED, not silent: " +
                        str(self._gitignore_rows(rows)))

    def test_a_pattern_the_repo_re_includes_is_reported_not_appended(self):
        """The general class: never append a line that reverses an existing negation."""
        self._init_repo()
        _w(self.tmp, ".gitignore",
           "# spikes/ is NOT ignored here (pack default overridden)\n!spikes/\n!spikes/**\n")
        rows = self._apply()
        text = _r(self.tmp, ".gitignore")
        self.assertNotIn("\nspikes/\n", "\n" + text)
        note = " ".join(r["note"] for r in self._gitignore_rows(rows))
        self.assertIn("!spikes/", note, "the report must name the rule it would have reversed")

    def test_a_declined_pattern_stays_declined_across_refreshes(self):
        """Without this, deleting the line is undone by the next /updatepack -- measured."""
        self._init_repo()
        _w(self.tmp, ".gitignore",
           "bin/\n" + pa.DECLINE_MARKER + "spikes/  our spikes are committed evidence\n")
        self._apply()
        self.assertNotIn("\nspikes/\n", "\n" + _r(self.tmp, ".gitignore"))
        self._apply()
        self.assertNotIn("\nspikes/\n", "\n" + _r(self.tmp, ".gitignore"),
                         "a declination that a second apply reverses is not a declination")

    def test_a_target_that_is_not_a_git_repo_keeps_the_old_behaviour(self):
        """R4: `git ls-files` failing is not evidence that spikes are untracked."""
        self._apply()
        self.assertIn("spikes/", _r(self.tmp, ".gitignore"))

    def test_every_other_pack_line_is_still_appended(self):
        self._init_repo()
        _w(self.tmp, "spikes/keep.md", "evidence\n")
        self._git("add", "-A")
        self._git("commit", "-qm", "spike")
        self._apply()
        text = _r(self.tmp, ".gitignore")
        for line in pa.GITIGNORE_LINES:
            if line == "spikes/":
                continue
            self.assertIn(line, text)


class GitignoreInvariantNotOneLiteralPattern(unittest.TestCase):
    """DEFECT 3. `.agents/*` + `!.agents/artifacts.yml` is ONE shape that satisfies the
    invariant, and the pack prescribed it as though it were the invariant.

    What the pack actually wants is *the registry travels with the repo*. Several ignore
    shapes satisfy that. A repo that COMMITS its per-run records under `.agents/` -- an
    episode-capture log, a coordination log -- satisfies it by the wider route, and the
    literal pattern breaks that repo: existing tracked files stay tracked and look fine
    while every NEW record becomes invisible to git. Measured in this very repository on
    2026-09-09: two `.agents/log/*.jsonl` tracked and healthy, four newer ones and
    `requests.jsonl` ignored, `git status` silent about all five.

    The repo has already answered the question by tracking the files. Read that answer.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self._git("init", "-q")
        self._git("config", "user.email", "t@example.invalid")
        self._git("config", "user.name", "t")

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.tmp, capture_output=True, text=True)

    def _apply(self):
        return pa.Applier(str(ROOT), self.tmp, dry=False, force=True, install=True,
                          baselines=False, project="Demo").run()

    def test_a_repo_that_commits_records_under_agents_keeps_them_visible(self):
        _w(self.tmp, ".agents/artifacts.yml", "docs/audit/audit-log.jsonl: register\n")
        _w(self.tmp, ".agents/log/episode.jsonl", '{"kind":"episode-close"}\n')
        self._git("add", "-A")
        self._git("commit", "-qm", "the repo commits its records")
        rows = self._apply()
        self.assertNotIn("\n.agents/*\n", "\n" + _r(self.tmp, ".gitignore"),
                         "a blanket here makes every NEW record invisible to git")
        note = " ".join(r["note"] for r in rows if r["path"] == ".gitignore")
        self.assertIn(".agents/*", note, "and the withholding must be reported")

    def test_a_repo_that_only_tracks_the_registry_still_gets_the_pattern(self):
        """No false positive: the pack default is right wherever it is not contradicted."""
        _w(self.tmp, ".agents/artifacts.yml", "docs/audit/audit-log.jsonl: register\n")
        self._git("add", "-A")
        self._git("commit", "-qm", "registry only")
        self._apply()
        text = _r(self.tmp, ".gitignore")
        self.assertIn(".agents/*", text)
        self.assertIn("!.agents/artifacts.yml", text)

    def test_the_pattern_written_actually_leaves_the_registry_visible(self):
        """Prove the INVARIANT, not the pattern -- with --quiet, never -v (see below)."""
        self._apply()
        self._git("add", ".gitignore")
        probe = subprocess.run(["git", "check-ignore", "--quiet", ".agents/artifacts.yml"],
                               cwd=self.tmp, capture_output=True, text=True)
        self.assertEqual(probe.returncode, 1,
                         "the registry must NOT be ignored; exit 1 from --quiet is that")


class GitignoreVerificationRule(unittest.TestCase):
    """`git check-ignore -v` INVERTS the answer for a re-included path -- measured.

    With `-v`, exit 0 means "some pattern matched", and a `!` negation counts as a match.
    So for `.agents/artifacts.yml` under `.agents/*` + `!.agents/artifacts.yml`:
    `--quiet` exits 1 (correct: not ignored) while `-v` exits 0 and prints the negation.
    Anyone verifying with `-v` concludes the opposite of the truth.

    Revision 63 recorded this. Three pack surfaces still prescribed `-v` afterwards, and
    one of them is an ALWAYS-APPLIED instruction, so the superseded guidance was the copy
    loaded on every task while the correction sat in a changelog entry.
    """

    SURFACES = ["pack/knowledge/continuous-improvement.md",
                "pack/knowledge/ui-visual-assets.md",
                "pack/scripts/pack-apply.py",
                "pack/adapters/INSTALL.md"]

    def test_measured_the_inversion_is_real(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        subprocess.run(["git", "init", "-q"], cwd=tmp, capture_output=True)
        _w(tmp, ".gitignore", ".agents/*\n!.agents/artifacts.yml\n")
        _w(tmp, ".agents/artifacts.yml", "x: authored\n")
        quiet = subprocess.run(["git", "check-ignore", "--quiet", ".agents/artifacts.yml"],
                               cwd=tmp, capture_output=True, text=True)
        verbose = subprocess.run(["git", "check-ignore", "-v", ".agents/artifacts.yml"],
                                 cwd=tmp, capture_output=True, text=True)
        self.assertEqual(quiet.returncode, 1, "--quiet: 1 == not ignored (the truth)")
        self.assertEqual(verbose.returncode, 0,
                         "-v: 0 == some pattern matched, including the negation")

    def test_no_pack_surface_prescribes_dash_v_as_the_verification(self):
        offenders = []
        for rel in self.SURFACES:
            text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
            if rel.endswith("INSTALL.md"):
                text = install_body(text)
            for match in re.finditer(r"check-ignore\s+(-v|--verbose)", text):
                line = text.count(chr(10), 0, match.start()) + 1
                offenders.append("{0}:{1}".format(rel, line))
        self.assertEqual(offenders, [],
                         "`check-ignore -v` exits 0 for a re-included path and inverts the "
                         "answer; the verification is `--quiet` (0 == ignored): " +
                         ", ".join(offenders))


if __name__ == "__main__":
    unittest.main()
