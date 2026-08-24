"""Q17 — the allocator seam in audit-log.py, and its survival across a pack sync.

Design: docs/design/coord-federation-phase3.md (Q17, H11), ADR-0008 (expand-migrate-contract).

`audit-log.py:next_id` was literally the KG-B shape: max(existing) + 1 computed from the
LOCAL file only, zero-padded to four digits. Two branches minting before either pushes are
invisible to each other, so the collision is structural -- nine recorded occurrences, twice
reaching main, once destroying an entry.

This is the EXPAND-MIGRATE-CONTRACT seam:
  expand    next_id delegates to the shared allocator when it is available
  migrate   new entries take a collision-proof id; EVERY existing al-NNNN keeps its value,
            and there is no backfill at all -- nothing is rewritten, so nothing is guessed
  contract  removing next_id is a later decision, deliberately NOT in Phase 3

H11 is the reason for the parity test: audit-log.py is a PACK-MANAGED file. `sync-pack.ps1`
copies pack/scripts/ over docs/ai-forward-pack/scripts/, so a seam added to only one copy
is silently reverted by the next sync. PACK-D is the recorded class for exactly that.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "pack" / "scripts" / "audit-log.py"
INSTALLED = ROOT / "docs" / "ai-forward-pack" / "scripts" / "audit-log.py"
IDS_SOURCE = ROOT / "pack" / "scripts" / "coord_ids.py"
IDS_INSTALLED = ROOT / "docs" / "ai-forward-pack" / "scripts" / "coord_ids.py"

LEGACY_RX = re.compile(r"^al-\d{4}$")


class SeamParityTests(unittest.TestCase):
    """H11 / PACK-D. A seam in one copy only is reverted by the next sync."""

    def test_Q17_the_allocator_seam_exists_in_both_copies(self):
        for path in (SOURCE, INSTALLED):
            body = path.read_text(encoding="utf-8")
            self.assertIn("coord_ids", body,
                          "the allocator seam is missing from {}".format(path))

    def test_Q17b_the_shared_allocator_module_is_shipped_in_both_copies(self):
        for path in (IDS_SOURCE, IDS_INSTALLED):
            self.assertTrue(path.is_file(),
                            "the shared allocator module is missing from {}".format(path))

    def test_Q17c_the_two_copies_of_the_allocator_are_identical(self):
        """One implementation, not two (ONE-A). The synced copy is a copy, not a fork."""
        self.assertEqual(IDS_SOURCE.read_bytes().replace(b"\r\n", b"\n"),
                         IDS_INSTALLED.read_bytes().replace(b"\r\n", b"\n"))


class AuditLogCase(unittest.TestCase):
    SCRIPT = INSTALLED

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.docs = pathlib.Path(self.tmp.name) / "docs"
        (self.docs / "audit").mkdir(parents=True)

    def seed(self, *rows):
        (self.docs / "audit" / "audit-log.jsonl").write_text(
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
            encoding="utf-8", newline="\n")

    def run_log(self, *args, env_extra=None):
        env = dict(os.environ)
        env.update(env_extra or {})
        return subprocess.run([sys.executable, str(self.SCRIPT), "--root", str(self.docs),
                               *args], cwd=str(ROOT), env=env, capture_output=True,
                              text=True, timeout=60)

    def rows(self):
        text = (self.docs / "audit" / "audit-log.jsonl").read_text(encoding="utf-8")
        return [json.loads(l) for l in text.splitlines() if l.strip()]

    def append(self, shortname, env_extra=None):
        return self.run_log("append", "--shortname", shortname, "--summary", "s",
                            "--kind", "manual", "--session", "test-session",
                            "--prompt", "p", env_extra=env_extra)


class MigrateTests(AuditLogCase):
    def test_Q17d_a_new_entry_takes_a_collision_proof_id(self):
        self.seed({"id": "al-0001", "shortname": "old", "datetime": "2026-01-01T00:00:00Z",
                   "session": "s", "summary": "s"})
        result = self.append("new-work")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        new = self.rows()[-1]["id"]
        self.assertTrue(new.startswith("al-"))
        self.assertFalse(LEGACY_RX.match(new),
                         "the new entry took the sequential shape that collides: " + new)

    def test_Q17e_existing_ids_are_never_rewritten_and_nothing_is_backfilled(self):
        """NFR-C2. There is no backfill at all, and that is the point -- nothing is
        rewritten, so nothing is guessed."""
        seeded = [{"id": "al-0001", "shortname": "a", "datetime": "2026-01-01T00:00:00Z",
                   "session": "s", "summary": "s"},
                  {"id": "al-0082", "shortname": "b", "datetime": "2026-01-02T00:00:00Z",
                   "session": "s", "summary": "s"}]
        self.seed(*seeded)
        self.assertEqual(self.append("c").returncode, 0)
        after = self.rows()
        self.assertEqual([r["id"] for r in after[:2]], ["al-0001", "al-0082"])
        self.assertEqual([r["shortname"] for r in after[:2]], ["a", "b"])

    def test_Q17f_two_rapid_appends_do_not_collide(self):
        """The defect, end to end through the CLI. Under the old scheme two writers that
        cannot see each other both compute max+1 and produce the same id."""
        self.seed({"id": "al-0001", "shortname": "a", "datetime": "2026-01-01T00:00:00Z",
                   "session": "s", "summary": "s"})
        self.assertEqual(self.append("first").returncode, 0)
        self.assertEqual(self.append("second").returncode, 0)
        ids = [r["id"] for r in self.rows()]
        self.assertEqual(len(set(ids)), len(ids), "ids collided: {}".format(ids))

    def test_Q17g_the_two_writers_that_cannot_see_each_other(self):
        """The actual KG-B condition: two branches, each with its own copy of the log,
        appending independently. Under max+1 both produce the same id."""
        self.seed({"id": "al-0001", "shortname": "base", "datetime": "2026-01-01T00:00:00Z",
                   "session": "s", "summary": "s"})
        import shutil
        other = pathlib.Path(self.tmp.name) / "branch2"
        shutil.copytree(self.docs, other / "docs")

        self.assertEqual(self.append("ours").returncode, 0)
        theirs = subprocess.run(
            [sys.executable, str(self.SCRIPT), "--root", str(other / "docs"), "append",
             "--shortname", "theirs", "--summary", "s", "--kind", "manual",
             "--session", "test-session", "--prompt", "p"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        self.assertEqual(theirs.returncode, 0, theirs.stdout + theirs.stderr)

        ours_id = self.rows()[-1]["id"]
        theirs_text = (other / "docs" / "audit" / "audit-log.jsonl").read_text(encoding="utf-8")
        theirs_id = json.loads(theirs_text.splitlines()[-1])["id"]
        self.assertNotEqual(ours_id, theirs_id,
                            "two branches that cannot see each other minted the same id")


class RollbackTests(AuditLogCase):
    def test_Q17h_the_legacy_scheme_is_one_env_var_away(self):
        """Expand-migrate-contract needs a rollback that is exercised, not assumed."""
        self.seed({"id": "al-0007", "shortname": "a", "datetime": "2026-01-01T00:00:00Z",
                   "session": "s", "summary": "s"})
        result = self.append("legacy", env_extra={"COORD_LEGACY_IDS": "1"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.rows()[-1]["id"], "al-0008",
                         "the rollback did not restore the sequential scheme")

    def test_Q17i_a_missing_allocator_degrades_to_the_legacy_scheme(self):
        """audit-log.py ships to repos whose pack may predate coord_ids.py. The fallback is
        the EXISTING legacy path retained deliberately, not a second implementation."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("audit_log_probe", INSTALLED)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        entries = [{"id": "al-0003"}]
        self.assertEqual(module.next_id(entries, "al", allocator=None), "al-0004")


class ReadPathTests(AuditLogCase):
    def test_Q17j_get_resolves_both_id_formats(self):
        """Both schemes coexist during migrate, and every reader must tolerate both."""
        self.seed({"id": "al-0001", "shortname": "legacy", "datetime": "2026-01-01T00:00:00Z",
                   "session": "s", "prompt": "p", "summary": "s"},
                  {"id": "al-01M0R4QEWQBJRKNF3JEHC99B2G", "shortname": "modern",
                   "datetime": "2026-01-02T00:00:00Z", "session": "s", "prompt": "p2",
                   "summary": "s"})
        legacy = self.run_log("get", "--id", "al-0001")
        self.assertEqual(legacy.returncode, 0, legacy.stdout + legacy.stderr)
        self.assertIn("legacy", legacy.stdout)
        modern = self.run_log("get", "--id", "al-01M0R4QEWQBJRKNF3JEHC99B2G")
        self.assertEqual(modern.returncode, 0, modern.stdout + modern.stderr)
        self.assertIn("modern", modern.stdout)

    def test_Q17k_verify_still_passes_with_both_formats_present(self):
        self.seed({"id": "al-0001", "shortname": "legacy", "datetime": "2026-01-01T00:00:00Z",
                   "session": "s", "summary": "s"},
                  {"id": "al-01M0R4QEWQBJRKNF3JEHC99B2G", "shortname": "modern",
                   "datetime": "2026-01-02T00:00:00Z", "session": "s", "summary": "s"})
        result = self.run_log("verify")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
