"""The CTX-* controls added at revision 60, pinned red-first where the un-fixed shape can be
reproduced in a fixture: pack-doctor's `claude-md import`, `copilot settings` and `re-read guard
hook` checks; audit-log's --tier/--fan-out fields and selfcheck; dream's tier-gap evidence and
profiles miner."""
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "pack" / "scripts"


def _load(name, path):
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.remove(str(SCRIPTS))


BLOCK = "<!-- AI-FORWARD-PACK:BEGIN -->\n# block\n" + ("rule\n" * 3000) + "<!-- AI-FORWARD-PACK:END -->\n"


class PackDoctorCtxTests(unittest.TestCase):
    def setUp(self):
        self.doc = _load("pack_doctor_ctx", SCRIPTS / "pack-doctor.py")
        self.tmp = tempfile.mkdtemp()

    def _write(self, rel, text):
        p = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)

    def test_copy_beside_copy_is_reported(self):
        """The shape measured in the wild: two full copies -> WARN naming the double-load."""
        self._write("AGENTS.md", "# AGENTS\n" + BLOCK)
        self._write("CLAUDE.md", "# CLAUDE\n" + BLOCK)
        r = self.doc.check_claude_md_import(self.tmp)
        self.assertEqual(self.doc.WARN, r["status"])
        self.assertIn("paid twice", r["detail"])
        self.assertIn("@AGENTS.md", r["fix"])

    def test_import_form_passes(self):
        self._write("AGENTS.md", "# AGENTS\n" + BLOCK)
        self._write("CLAUDE.md", "# CLAUDE.md\n\n@AGENTS.md\n\n<!-- AI-FORWARD-PACK:BEGIN -->\n## Claude Code\n- addendum\n<!-- AI-FORWARD-PACK:END -->\n")
        self.assertEqual(self.doc.PASS, self.doc.check_claude_md_import(self.tmp)["status"])
        # and the CLAUDE.md block check accepts the import form when the addendum has no markers
        self._write("CLAUDE.md", "@AGENTS.md\n")
        self.assertEqual(self.doc.PASS, self.doc.check_block(self.tmp, "CLAUDE.md")["status"])

    def test_missing_claude_md_warns(self):
        self._write("AGENTS.md", "# AGENTS\n" + BLOCK)
        self.assertEqual(self.doc.WARN, self.doc.check_claude_md_import(self.tmp)["status"])

    def test_copilot_settings_global_long_context_warns(self):
        home = tempfile.mkdtemp()
        with open(os.path.join(home, "settings.json"), "w", encoding="utf-8") as fh:
            json.dump({"contextTier": "long_context", "effortLevel": "high"}, fh)
        with mock.patch.dict(os.environ, {"COPILOT_HOME": home}):
            r = self.doc.check_copilot_settings()
        self.assertEqual(self.doc.WARN, r["status"])
        self.assertIn("long_context", r["detail"])
        self.assertIn("effortLevel=high", r["detail"])

    def test_copilot_settings_defaults_pass_and_absent_passes(self):
        home = tempfile.mkdtemp()
        with open(os.path.join(home, "settings.json"), "w", encoding="utf-8") as fh:
            json.dump({"model": "x"}, fh)
        with mock.patch.dict(os.environ, {"COPILOT_HOME": home}):
            self.assertEqual(self.doc.PASS, self.doc.check_copilot_settings()["status"])
        with mock.patch.dict(os.environ, {"COPILOT_HOME": tempfile.mkdtemp()}):
            self.assertEqual(self.doc.PASS, self.doc.check_copilot_settings()["status"])

    def test_hooks_absent_warns_present_passes_config_without_script_fails(self):
        self.assertEqual(self.doc.WARN, self.doc.check_hooks(self.tmp)["status"])
        self._write(".github/hooks/ai-forward.json", "{}")
        self.assertEqual(self.doc.FAIL, self.doc.check_hooks(self.tmp)["status"])
        self._write("docs/ai-forward-pack/hooks/reread-guard.py", "# guard")
        self.assertEqual(self.doc.PASS, self.doc.check_hooks(self.tmp)["status"])

    def test_source_repo_reports_the_import_form(self):
        r = self.doc.check_claude_md_import(str(ROOT))
        self.assertEqual(self.doc.PASS, r["status"], r)


class AuditTierTests(unittest.TestCase):
    SCRIPT = SCRIPTS / "audit-log.py"

    def _append(self, root, *extra):
        return subprocess.run([sys.executable, str(self.SCRIPT), "--root", root, "append", "--shortname", "t",
                               "--session", "s1", "--prompt", "p", "--summary", "s", "--kind", "skill"] + list(extra),
                              capture_output=True, text=True, timeout=60)

    def _entries(self, root):
        with open(os.path.join(root, "audit", "audit-log.jsonl"), encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def test_tier_and_fan_out_are_recorded(self):
        root = tempfile.mkdtemp()
        r = self._append(root, "--goal", "g", "--done-when", "d", "--tier", "T1", "--fan-out", "2")
        self.assertEqual(0, r.returncode, r.stderr)
        e = self._entries(root)[-1]
        self.assertEqual("T1", e["tier"])
        self.assertEqual(2, e["fan_out"])

    def test_absent_when_not_supplied_and_selfcheck_reports_the_gap(self):
        root = tempfile.mkdtemp()
        self._append(root, "--goal", "g", "--done-when", "d")
        e = self._entries(root)[-1]
        self.assertNotIn("tier", e)
        self.assertNotIn("fan_out", e)
        r = subprocess.run([sys.executable, str(self.SCRIPT), "--root", root, "selfcheck", "--session", "s1", "--json"],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(0, r.returncode, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(1, len(out["tier_gaps"]))


class DreamTierAndProfilesTests(unittest.TestCase):
    def setUp(self):
        self.dream = _load("dream_ctx", SCRIPTS / "dream.py")

    def _corpus(self, audit, profiles=()):
        return {"audit": audit, "change": [], "mitigations": [], "classes": [], "markers": [],
                "profiles": list(profiles), "counts": {}}

    def test_goal_state_without_tier_is_evidence(self):
        audit = [{"id": "al-1", "kind": "skill", "shortname": "a", "summary": "s", "done_when": "x"}]
        proposals, _ = self.dream.build_proposals(self._corpus(audit))
        packo = [p for p in proposals if str(p.get("sig", "")).startswith("PACK-O")]
        self.assertEqual(1, len(packo))
        self.assertTrue(any("without a tier" in e["note"] for e in packo[0]["evidence"]))

    def test_over_cap_fan_out_is_evidence(self):
        audit = [{"id": "al-1", "kind": "skill", "shortname": "a", "summary": "s", "done_when": "x", "tier": "T0",
                  "fan_out": 0, "agent_runs": [{"agent": "x"}, {"agent": "y"}]}]
        proposals, _ = self.dream.build_proposals(self._corpus(audit))
        packo = [p for p in proposals if str(p.get("sig", "")).startswith("PACK-O")]
        self.assertTrue(any("vs declared fan-out cap 0" in e["note"] for e in packo[0]["evidence"]))

    def test_profile_findings_become_control_upgrades(self):
        prof = {"id": "sp-0001", "generated": "2026-09-05T00:00:00Z",
                "findings": [{"id": "SP-04", "title": "Re-reads", "severity": "Minor", "fixes": ["F-07"],
                              "evidence": [{"turn": 3, "note": "public.html viewed 4x"}]}]}
        proposals, _ = self.dream.build_proposals(self._corpus([], [prof]))
        sp = [p for p in proposals if p.get("sig") == "session-profile SP-04"]
        self.assertEqual(1, len(sp))
        self.assertIn("F-07", sp[0]["control"]["text"])
        self.assertEqual("public.html viewed 4x", sp[0]["evidence"][0]["note"])

    def test_load_profiles_reads_the_directory(self):
        root = tempfile.mkdtemp()
        d = os.path.join(root, "docs", "profiles", "sp-0001")
        os.makedirs(d)
        with open(os.path.join(d, "profile.json"), "w", encoding="utf-8") as fh:
            json.dump({"id": "sp-0001", "generated": "2099-01-01T00:00:00Z", "findings": []}, fh)
        import datetime
        cutoff = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
        self.assertEqual(1, len(self.dream.load_profiles(root, cutoff)))
        self.assertEqual([], self.dream.load_profiles(tempfile.mkdtemp(), cutoff))


class ContextBudgetPrefixAndSkillsTests(unittest.TestCase):
    """CTX-B / CTX-E: the whole-prefix view flags a copy-beside-copy and the per-skill ratchet
    fails a new oversized skill; discovery never settles on a corpus that declares no scope."""

    def setUp(self):
        self.cb = _load("context_budget_ctx", SCRIPTS / "context-budget.py")
        self.tmp = tempfile.mkdtemp()

    def _write(self, rel, text):
        q = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(q), exist_ok=True)
        with open(q, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _kdir(self):
        self._write("knowledge/FOUNDATION.md", "# manifest")
        self._write("knowledge/a.md", "---" + chr(10) + "load: always" + chr(10) + "---" + chr(10) + ("x" * 4830))
        return os.path.join(self.tmp, "knowledge")

    def test_prefix_flags_a_full_copy_and_accepts_the_import_stub(self):
        kdir = self._kdir()
        self._write("AGENTS.md", "# A" + chr(10) + ("y" * 9660))
        self._write("CLAUDE.md", "# C" + chr(10) + ("y" * 9660))
        cfg = {"prefix_allowances": {"tool_definitions": 100, "host_prompt": 50}}
        comps, facts = self.cb.prefix_components(self.tmp, kdir, cfg, "copilot")
        names = [c[0] for c in comps]
        self.assertTrue(any("double-load" in n for n in names), names)
        self.assertFalse(facts["claude_is_import"])
        self._write("CLAUDE.md", "# CLAUDE.md" + chr(10) + chr(10) + "@AGENTS.md" + chr(10))
        comps, facts = self.cb.prefix_components(self.tmp, kdir, cfg, "copilot")
        self.assertTrue(facts["claude_is_import"])
        self.assertTrue(any("import stub" in n for n in [c[0] for c in comps]))
        comps_cl, _ = self.cb.prefix_components(self.tmp, kdir, cfg, "claude")
        self.assertTrue(any("via @import" in n for n in [c[0] for c in comps_cl]))

    def test_prefix_gate_fails_on_the_copy_and_passes_on_the_stub(self):
        kdir = self._kdir()
        self._write("AGENTS.md", "# A" + chr(10) + ("y" * 2000))
        self._write("CLAUDE.md", "# C" + chr(10) + ("y" * 2000))
        self._write("context-budget.json", json.dumps({"prefix_tokens": None, "growth_tolerance_pct": 2}))
        cfgp = os.path.join(self.tmp, "context-budget.json")
        argv = ["--root", self.tmp, "--knowledge-dir", kdir, "--config", cfgp, "prefix", "--host", "copilot", "--gate"]
        self.assertEqual(1, self.cb.main(argv), "a full copy beside AGENTS.md must fail the prefix gate")
        self._write("CLAUDE.md", "@AGENTS.md" + chr(10))
        self.assertEqual(0, self.cb.main(argv))

    def test_skills_gate_fails_a_new_skill_above_the_ceiling(self):
        self._write("commands/small/SKILL.md", "x" * 500)
        self._write("commands/huge/SKILL.md", "x" * 50000)
        self._write("context-budget.json", json.dumps({"skills_baseline": {}, "skill_ceiling_tokens": 5000}))
        cfgp = os.path.join(self.tmp, "context-budget.json")
        sdir = os.path.join(self.tmp, "commands")
        self.assertEqual(1, self.cb.main(["--skills-dir", sdir, "--config", cfgp, "skills", "--gate"]))
        self.assertEqual(0, self.cb.main(["--skills-dir", sdir, "--config", cfgp, "skills", "--update-baseline"]))
        self.assertEqual(0, self.cb.main(["--skills-dir", sdir, "--config", cfgp, "skills", "--gate"]),
                         "an acknowledged baseline passes; growth past it fails again")
        self._write("commands/small/SKILL.md", "x" * 5000)
        self.assertEqual(1, self.cb.main(["--skills-dir", sdir, "--config", cfgp, "skills", "--gate"]))

    def test_declares_scope_rejects_a_scope_less_vendored_copy(self):
        self._write("vendored/FOUNDATION.md", "# manifest")
        self._write("vendored/a.md", "# no frontmatter at all")
        self.assertFalse(self.cb._declares_scope(os.path.join(self.tmp, "vendored")))
        self.assertTrue(self.cb._declares_scope(self._kdir()))

if __name__ == "__main__":
    unittest.main()
