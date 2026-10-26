"""PACK-W. A change under `pack/` ships with a revision bump in `pack/adapters/INSTALL.md`.

INSTALL's own convention says every change to the bundle bumps `revision`, but nothing checked
it. On 2026-10-17 two changes to deployed files (the WT-D/WT-E hook fix and the Muse
re-measure) landed at revision 108. pack-apply finds a merge base from the commits whose
INSTALL text matches the installed copy, so revision 108 then named two different
`coord-core.py` and `context-budget.json`: an update from 108 refused with CONFLICT, and a
same-revision refresh kept the old hook as a "local deviation", so the fix could not reach a
consumer.

The check: the newest commit that touched `pack/` also touched `pack/adapters/INSTALL.md`.
Uncommitted edits are not judged; the gate runs on the tree that is about to be pushed.

Seen failing first on `332c297`, the tip after PR #12, whose last pack commit left INSTALL alone.
"""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_upstream_adoption_integration import (recovered_revision_108_install, recovered_revision_109_install,
                                               recovered_revision_110_install, recovered_revision_111_install,
                                               recovered_revision_112_install, recovered_revision_113_install,
                                               recovered_revision_114_install, recovered_revision_115_install,
                                               recovered_revision_116_install, recovered_revision_117_install,
                                               recovered_revision_118_install)

REPO = Path(__file__).resolve().parents[2]
INSTALL = "pack/adapters/INSTALL.md"


def _last_commit(ref, path):
    out = subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%H", ref, "--", path],
                         capture_output=True, text=True, encoding="utf-8")
    return out.stdout.strip() if out.returncode == 0 else None


def _git(repo, *args):
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8")
    return out.stdout.strip() if out.returncode == 0 else ""


def history_is_cut(repo):
    """True when a shallow clone's boundary is where the check would look: the newest commit that
    touched pack/ has no fetched parent, so it appears to have changed every path."""
    if _git(repo, "rev-parse", "--is-shallow-repository") != "true":
        return False
    sha = _git(repo, "log", "-1", "--format=%H", "HEAD", "--", "pack")
    return bool(sha) and not _git(repo, "log", "-1", "--format=%P", sha)


def unbumped_pack_commit(ref="HEAD"):
    """The newest commit at `ref` that changed pack/ without INSTALL.md, else None."""
    pack, install = _last_commit(ref, "pack"), _last_commit(ref, INSTALL)
    if not pack or not install:
        return None
    return None if pack == install else pack


class ShallowCloneTests(unittest.TestCase):
    """PACK-W recurred on 2026-10-19: PR #24's last commit changed pack/ without INSTALL and CI passed,
    because a depth-1 checkout holds one grafted commit that seems to touch every path. The check
    now fails on a clone whose history is cut, instead of passing vacuously."""

    def test_a_depth_one_clone_is_reported_as_cut(self):
        if not (REPO / ".git").exists():
            self.skipTest("no git checkout")
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "shallow"
            subprocess.run(["git", "clone", "-q", "--no-tags", "--depth", "1", REPO.as_uri(), str(clone)],
                           check=True, capture_output=True)
            self.assertTrue(history_is_cut(clone))

    def test_this_checkout_with_history_is_not_cut(self):
        if not (REPO / ".git").exists():
            self.skipTest("no git checkout")
        if _git(REPO, "rev-parse", "--is-shallow-repository") == "true":
            self.skipTest("this checkout is itself shallow; the check above judges it")
        self.assertFalse(history_is_cut(REPO))


class InstallRevisionBumpTests(unittest.TestCase):
    def setUp(self):
        if not (REPO / ".git").exists() or _last_commit("HEAD", "pack") is None:
            self.skipTest("no git history for pack/")

    def test_the_newest_pack_change_carries_an_install_revision(self):
        self.assertFalse(history_is_cut(REPO), "this clone is too shallow to see which commit last changed "
                         "pack/ (a depth-1 checkout passes vacuously); fetch at least the PR's commits")
        sha = unbumped_pack_commit()
        self.assertIsNone(sha, "commit {} changed pack/ without {}: bump `revision`, write this "
                          "revision's `changes`, archive the previous ones".format(sha, INSTALL))


class Revision109MetadataTests(unittest.TestCase):
    """Revision 109: the one delta that ships WT-D, WT-E and the Muse 1.4.10 re-measure."""

    def test_revision_109_is_the_one_hook_scope_and_muse_delta(self):
        frontmatter = recovered_revision_109_install().split(b"---\n", 2)[1].decode("utf-8")
        self.assertRegex(frontmatter, r"(?m)^revision: 109$")
        self.assertIn("bundle_version: '2026.10.17.1'", frontmatter)
        self.assertEqual(1, frontmatter.count("  - { type: changed,"))
        self.assertIn("area: hook-scope-and-muse-remeasure", frontmatter)
        paths = re.search(r"paths: \[(.*?)\], deploy:", frontmatter)
        assert paths is not None
        for path in re.findall(r"'([^']+)'", paths.group(1)):
            with self.subTest(source_path=path):
                self.assertTrue((REPO / "pack" / path).is_file(), path)
        deploy = frontmatter.split("deploy: '", 1)[1].split("', summary:", 1)[0]
        for instruction in ("SOURCE clone, not an installed applier", "revision 108 to 109",
                            "coord-core.py", "local deviation"):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, deploy)

    def test_reversal_recovers_the_published_revision_108_source(self):
        raw = recovered_revision_109_install()
        self.assertEqual(285919, len(recovered_revision_108_install(raw)))
        corrupted = raw.replace(b"area: upstream-hook-cost-refresh", b"area: upstream-hook-cost-refresH", 1)
        self.assertNotEqual(raw, corrupted)
        with self.assertRaises(AssertionError):
            recovered_revision_108_install(corrupted)


class Revision111MetadataTests(unittest.TestCase):
    """Revision 111: the one delta that fixes the alias-escape spelling check (WT-E2)."""

    def test_revision_111_is_the_one_alias_escape_delta(self):
        raw = recovered_revision_111_install()
        frontmatter = raw.split(b"---\n", 2)[1].decode("utf-8")
        self.assertRegex(frontmatter, r"(?m)^revision: 111$")
        self.assertIn("bundle_version: '2026.10.17.3'", frontmatter)
        self.assertEqual(1, frontmatter.count("  - { type: changed,"))
        self.assertIn("area: alias-escape-spelling", frontmatter)
        for path in ("scripts/coord-core.py", "adapters/INSTALL.md"):
            self.assertTrue((REPO / "pack" / path).is_file(), path)
        self.assertEqual(289089, len(recovered_revision_110_install(raw)))
        with self.assertRaises(AssertionError):
            recovered_revision_110_install(raw.replace(b"area: hook-times-and-junctions",
                                                       b"area: hook-times-and-junctionS", 1))


class Revision112MetadataTests(unittest.TestCase):
    """Revision 112: the one delta that stops charging unparsed extension frames (RUN-B2)."""

    def test_revision_112_is_the_one_transport_tail_delta(self):
        raw = recovered_revision_112_install()
        frontmatter = raw.split(b"---\n", 2)[1].decode("utf-8")
        self.assertRegex(frontmatter, r"(?m)^revision: 112$")
        self.assertIn("bundle_version: '2026.10.17.4'", frontmatter)
        self.assertEqual(1, frontmatter.count("  - { type: changed,"))
        self.assertIn("area: transport-unparsed-extension-tail", frontmatter)
        for path in ("scripts/coord_transport.py", "commands/execute-with-coordination/reference/launch.md",
                     "adapters/INSTALL.md"):
            self.assertTrue((REPO / "pack" / path).is_file(), path)
        self.assertEqual(290647, len(recovered_revision_111_install(raw)))
        with self.assertRaises(AssertionError):
            recovered_revision_111_install(raw.replace(b"area: alias-escape-spelling",
                                                       b"area: alias-escape-spellinG", 1))


class Revision113MetadataTests(unittest.TestCase):
    """Revision 113: the one delta that records the new AGENTS.md size in the Muse profile."""

    def test_revision_113_is_the_one_muse_bytes_delta(self):
        raw = recovered_revision_113_install()
        frontmatter = raw.split(b"---\n", 2)[1].decode("utf-8")
        self.assertRegex(frontmatter, r"(?m)^revision: 113$")
        self.assertIn("bundle_version: '2026.10.18.1'", frontmatter)
        self.assertEqual(1, frontmatter.count("  - { type: changed,"))
        self.assertIn("area: muse-agents-md-bytes", frontmatter)
        for path in ("context-budget.json", "adapters/INSTALL.md"):
            self.assertTrue((REPO / "pack" / path).is_file(), path)
        self.assertEqual(292244, len(recovered_revision_112_install(raw)))
        with self.assertRaises(AssertionError):
            recovered_revision_112_install(raw.replace(b"area: transport-unparsed-extension-tail",
                                                       b"area: transport-unparsed-extension-taiL", 1))


class Revision114MetadataTests(unittest.TestCase):
    """Revision 114: the one delta that stops the edit hook asking (EDIT-ASK) and hardens the
    identity guard (FR-088) and the byte-code cache (FR-086)."""

    def test_revision_114_is_the_one_edits_never_ask_delta(self):
        raw = recovered_revision_114_install()
        frontmatter = raw.split(b"---\n", 2)[1].decode("utf-8")
        self.assertRegex(frontmatter, r"(?m)^revision: 114$")
        self.assertIn("bundle_version: '2026.10.19.1'", frontmatter)
        self.assertEqual(1, frontmatter.count("  - { type: changed,"))
        self.assertIn("area: edits-never-ask-and-guard-hardening", frontmatter)
        for path in ("scripts/coord-core.py", "adapters/hooks/git-identity-guard.py",
                     "adapters/hooks/dispatch.py", "adapters/INSTALL.md"):
            self.assertTrue((REPO / "pack" / path).is_file(), path)
        self.assertEqual(293252, len(recovered_revision_113_install(raw)))
        with self.assertRaises(AssertionError):
            recovered_revision_113_install(raw.replace(b"area: muse-agents-md-bytes",
                                                       b"area: muse-agents-md-byteS", 1))


class Revision115MetadataTests(unittest.TestCase):
    """Revision 115: the one delta that scrubs session profiles (FR-103) and keeps them local
    outside the pack source repository (FR-104)."""

    def test_revision_115_is_the_one_profile_scrub_delta(self):
        raw = recovered_revision_115_install()
        frontmatter = raw.split(b"---\n", 2)[1].decode("utf-8")
        self.assertRegex(frontmatter, r"(?m)^revision: 115$")
        self.assertIn("bundle_version: '2026.10.19.2'", frontmatter)
        self.assertEqual(1, frontmatter.count("  - { type: changed,"))
        self.assertIn("area: profile-scrub-and-local-default", frontmatter)
        for path in ("scripts/session-profile.py", "scripts/dream.py", "commands/session-profiler/SKILL.md",
                     "adapters/copilot/prompts/session-profiler.prompt.md", "adapters/INSTALL.md"):
            self.assertTrue((REPO / "pack" / path).is_file(), path)
        self.assertEqual(295302, len(recovered_revision_114_install(raw)))
        with self.assertRaises(AssertionError):
            recovered_revision_114_install(raw.replace(b"area: edits-never-ask-and-guard-hardening",
                                                       b"area: edits-never-ask-and-guard-hardeninG", 1))


class Revision116MetadataTests(unittest.TestCase):
    """Revision 116: the one delta for FR-105 (profiler isolation), FR-106 (DI7) and FR-107 (forget)."""

    def test_revision_116_is_the_one_isolation_source_and_forget_delta(self):
        raw = recovered_revision_116_install()
        frontmatter = raw.split(b"---\n", 2)[1].decode("utf-8")
        self.assertRegex(frontmatter, r"(?m)^revision: 116$")
        self.assertIn("bundle_version: '2026.10.19.3'", frontmatter)
        self.assertEqual(1, frontmatter.count("  - { type: changed,"))
        self.assertIn("area: profiler-isolation-decision-source-and-forget", frontmatter)
        for path in ("scripts/session-profile.py", "scripts/delivery.py", "knowledge/decision-interrogation.md",
                     "commands/deliver/reference/checkpoints.md", "adapters/INSTALL.md"):
            self.assertTrue((REPO / "pack" / path).is_file(), path)
        self.assertEqual(297106, len(recovered_revision_115_install(raw)))
        with self.assertRaises(AssertionError):
            recovered_revision_115_install(raw.replace(b"area: profile-scrub-and-local-default",
                                                       b"area: profile-scrub-and-local-defaulT", 1))


class Revision117MetadataTests(unittest.TestCase):
    """Revision 117: the one delta closing the revision-108 P3 findings (FR-090..FR-100, FR-110)."""

    def test_revision_117_is_the_one_host_parity_approval_and_release_pin_delta(self):
        raw = recovered_revision_117_install()
        frontmatter = raw.split(b"---\n", 2)[1].decode("utf-8")
        self.assertRegex(frontmatter, r"(?m)^revision: 117$")
        self.assertIn("bundle_version: '2026.10.19.4'", frontmatter)
        self.assertEqual(1, frontmatter.count("  - { type: changed,"))
        self.assertIn("area: native-host-parity-session-check-approval-and-release-pin", frontmatter)
        for path in ("scripts/coord-core.py", "scripts/delivery.py", "scripts/pack-apply.py", "scripts/marker-lint.py",
                     "scripts/dream.py", "adapters/hooks/reread-guard.py", "adapters/hooks/session-start.py",
                     "adapters/hooks/codex.hooks.json", "adapters/INSTALL.md"):
            self.assertTrue((REPO / "pack" / path).is_file(), path)
        self.assertEqual(298720, len(recovered_revision_116_install(raw)))
        with self.assertRaises(AssertionError):
            recovered_revision_116_install(raw.replace(b"area: profiler-isolation-decision-source-and-forget",
                                                       b"area: profiler-isolation-decision-source-and-forgeT", 1))


class Revision118MetadataTests(unittest.TestCase):
    """Revision 118: the one delta making corpus scans fail closed (CTRL-G)."""

    def test_revision_118_is_the_one_fail_closed_scan_delta(self):
        raw = recovered_revision_118_install()
        frontmatter = raw.split(b"---\n", 2)[1].decode("utf-8")
        self.assertRegex(frontmatter, r"(?m)^revision: 118$")
        self.assertIn("bundle_version: '2026.10.22.1'", frontmatter)
        self.assertIn("skills: 30,", frontmatter)
        self.assertIn("scripts: 47 }", frontmatter)
        self.assertEqual(1, frontmatter.count("  - { type: "))
        self.assertIn("area: fail-closed-corpus-scans", frontmatter)
        for path in ("scripts/docs-graph.py", "scripts/marker-lint.py", "scripts/scrub.py", "scripts/pack-apply.py",
                     "scripts/delivery.py", "scripts/xaml-token-lint.py", "adapters/INSTALL.md"):
            self.assertTrue((REPO / "pack" / path).is_file(), path)
        self.assertEqual(301270, len(recovered_revision_117_install(raw)))
        with self.assertRaises(AssertionError):
            recovered_revision_117_install(raw.replace(b"area: native-host-parity-session-check-approval-and-release-pin",
                                                       b"area: native-host-parity-session-check-approval-and-release-piN", 1))


class Revision119MetadataTests(unittest.TestCase):
    """Revision 119: the one delta upstreaming a consuming repo's fixes (join R2, loaders, regen, rollup, craft gate)."""

    def test_revision_119_is_the_one_upstream_consumer_fixes_delta(self):
        raw = (REPO / INSTALL).read_bytes()
        frontmatter = raw.split(b"---\n", 2)[1].decode("utf-8")
        self.assertRegex(frontmatter, r"(?m)^revision: 119$")
        self.assertIn("bundle_version: '2026.10.26.1'", frontmatter)
        self.assertIn("skills: 30,", frontmatter)
        self.assertIn("scripts: 47 }", frontmatter)
        self.assertEqual(1, frontmatter.count("  - { type: "))
        self.assertIn("area: upstream-consumer-fixes-join-r2-loaders-regen-rollup-posix-craft-gate", frontmatter)
        for path in ("scripts/conductor-join.py", "scripts/prompt-log.py", "scripts/coord-core.py", "scripts/docs-graph.py",
                     "scripts/ui-craft-gate.py", "scripts/coord_transport.py", "adapters/INSTALL.md"):
            self.assertTrue((REPO / "pack" / path).is_file(), path)
        self.assertEqual(304409, len(recovered_revision_118_install(raw)))
        with self.assertRaises(AssertionError):
            recovered_revision_118_install(raw.replace(b"area: fail-closed-corpus-scans",
                                                       b"area: fail-closed-corpus-scanS", 1))


if __name__ == "__main__":
    unittest.main()
