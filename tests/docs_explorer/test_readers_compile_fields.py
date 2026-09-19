"""The readers of the compile stage's audit fields (spec-compile-readers US-1..US-3, US-9).

session-profile.py: `compile_measurements(root, days)` and `compile_findings(measure)` over a
temp audit log with fixture entries; every empty cell reads `not recorded` (IO8). dream.py: the
CO-S0 miner beside PACK-O. verify-skill-contracts.py: the lint's self-test and each refusal
direction over fixture skills. Each test pins one exact oracle; all were observed red before the
code existed (CI6 red-first).
"""
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROFILER = ROOT / "pack" / "scripts" / "session-profile.py"
DREAM = ROOT / "pack" / "scripts" / "dream.py"
LINT = ROOT / "pack" / "scripts" / "verify-skill-contracts.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sp = _load("session_profile_readers", PROFILER)

TS = "2026-09-19T12:00:00Z"


def compilation(cid, raw="al-r1", version=1, harness="claude-code", dispatchable=True, drs=None,
                refusals=None, retries=0, engine=0.001, prompt="Goal state\nGoal: x\n", session="s1", ts=TS):
    return {"id": cid, "kind": "compilation", "datetime": ts, "session": session, "shortname": "compile-x",
            "prompt": prompt,
            "compiled": {"harness": harness, "template_version": version, "dispatchable": dispatchable,
                         "raw_id": raw, "decision_requests": drs if drs is not None else [],
                         "provenance": {"refusals": refusals or [], "retries": retries,
                                        "engine_seconds": engine, "compile_tokens": None}}}


def run(rid, session="s1", compiled_from=None, edit_distance=None, compiled=None, tier="T1", ts=TS, **extra):
    e = {"id": rid, "kind": "skill", "datetime": ts, "session": session, "shortname": "skill-" + rid,
         "tier": tier, "summary": "s"}
    if compiled_from is not None:
        e["compiled_from"] = compiled_from
        e["edit_distance"] = edit_distance
    if compiled is not None:
        e["compiled"] = compiled
    e.update(extra)
    return e


def write_log(root, entries, raw_lines=()):
    d = os.path.join(root, "docs", "audit")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "audit-log.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")
        for line in raw_lines:
            fh.write(line + "\n")


FIXTURE = [
    compilation("al-c1", drs=[{"id": "DR-1", "answer": None}, {"id": "DR-2", "answer": "yes"}],
                refusals=["raw mismatch"], retries=1, engine=0.002),
    compilation("al-c2", raw="al-r2", engine=0.001),
    run("al-w1", compiled_from="al-c1", edit_distance=0.31),
    run("al-w2", compiled_from="al-c2", edit_distance=0.05),
    run("al-w3", compiled=False),
]


class ProfilerCompileMeasurementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _measure(self, entries, raw_lines=()):
        write_log(self.tmp, entries, raw_lines)
        return sp.compile_measurements(self.tmp, 0)

    def test_measurements_from_fixture_log(self):
        m = self._measure(FIXTURE)
        t = m["by_template"]["claude-code v1"]
        self.assertEqual(2, t["compilations"])
        self.assertEqual(2, t["samples"])
        self.assertAlmostEqual(0.18, t["edit_distance_median"], places=4)
        self.assertGreaterEqual(t["edit_distance_p90"], 0.28)
        self.assertLessEqual(t["edit_distance_p90"], 0.31)
        s = m["by_session"]["s1"]
        self.assertEqual(3, s["substantive_recorded"])
        self.assertEqual(1, s["compiled_false"])
        self.assertAlmostEqual(0.33, s["compiled_false_share"], places=2)
        self.assertEqual(2, s["compilations"])
        self.assertTrue(m["source"].endswith("audit-log.jsonl"))

    def test_provenance_and_dr_rows(self):
        t = self._measure(FIXTURE)["by_template"]["claude-code v1"]
        self.assertEqual(1, t["refusals"])
        self.assertEqual(1, t["retries"])
        self.assertAlmostEqual(0.0015, t["engine_seconds_median"], places=4)
        self.assertAlmostEqual(1.0, t["decision_requests_per_compilation"], places=2)

    def test_empty_log_reads_not_recorded(self):
        m = self._measure([])
        self.assertEqual(sp.NOT_RECORDED, m["source"])
        self.assertEqual({}, m["by_session"])
        self.assertEqual({}, m["by_template"])
        self.assertEqual([], sp.compile_findings(m))

    def test_missing_log_reads_not_recorded(self):
        m = sp.compile_measurements(self.tmp, 0)
        self.assertEqual(sp.NOT_RECORDED, m["source"])
        self.assertEqual([], sp.compile_findings(m))

    def test_unrecorded_not_in_denominator(self):
        m = self._measure([run("al-w9"), run("al-w3", compiled=False)])  # w9 carries neither field
        s = m["by_session"]["s1"]
        self.assertEqual(1, s["substantive_recorded"])
        self.assertEqual(1, s["unrecorded"])
        self.assertAlmostEqual(1.0, s["compiled_false_share"], places=2)

    def test_non_numeric_distance_excluded(self):
        m = self._measure([compilation("al-c1"), run("al-w1", compiled_from="al-c1", edit_distance=None),
                           run("al-w2", compiled_from="al-c1", edit_distance="not recorded")])
        t = m["by_template"]["claude-code v1"]
        self.assertEqual(0, t["samples"])
        self.assertEqual(2, t["samples_unrecorded"])
        self.assertEqual(sp.NOT_RECORDED, t["edit_distance_median"])

    def test_unresolved_compiled_from_is_unknown_template(self):
        m = self._measure([run("al-w1", compiled_from="al-nope", edit_distance=0.4)])
        self.assertIn("unknown", m["by_template"])
        self.assertEqual(1, m["by_template"]["unknown"]["samples"])

    def test_malformed_line_skipped(self):
        m = self._measure(FIXTURE, raw_lines=["{not json"])
        self.assertEqual(1, m["skipped_lines"])
        self.assertEqual(2, m["by_template"]["claude-code v1"]["compilations"])

    def test_compile_measurements_rebuild_equal(self):
        write_log(self.tmp, FIXTURE)
        self.assertEqual(sp.compile_measurements(self.tmp, 0), sp.compile_measurements(self.tmp, 0))

    def test_sp27_fires_inferred_and_skips_t0(self):
        m = self._measure([run("al-w3", compiled=False, tier="T1")])
        f = {x["id"]: x for x in sp.compile_findings(m)}
        self.assertIn("SP-27", f)
        self.assertEqual("Inferred", f["SP-27"]["confidence"])
        self.assertEqual(["F-26"], f["SP-27"]["fixes"])
        self.assertIn("skill-al-w3", f["SP-27"]["evidence"][0]["note"])
        m0 = self._measure([run("al-w3", compiled=False, tier="T0")])
        self.assertNotIn("SP-27", {x["id"] for x in sp.compile_findings(m0)})

    def test_sp28_fires_verified_above_0_2_not_at_0_2(self):
        m = self._measure([compilation("al-c1"), run("al-w1", compiled_from="al-c1", edit_distance=0.25)])
        f = {x["id"]: x for x in sp.compile_findings(m)}
        self.assertIn("SP-28", f)
        self.assertEqual("Verified", f["SP-28"]["confidence"])
        self.assertEqual(["F-27"], f["SP-28"]["fixes"])
        m2 = self._measure([compilation("al-c1"), run("al-w1", compiled_from="al-c1", edit_distance=0.20)])
        self.assertNotIn("SP-28", {x["id"] for x in sp.compile_findings(m2)})

    def test_sp28_evidence_names_samples(self):
        m = self._measure([compilation("al-c1"), run("al-w1", compiled_from="al-c1", edit_distance=0.5)])
        f = [x for x in sp.compile_findings(m) if x["id"] == "SP-28"][0]
        self.assertEqual(1, f["metric"]["samples"])
        self.assertIn("samples: 1", f["evidence"][0]["note"])
        self.assertIn("claude-code v1", f["evidence"][0]["note"])

    def test_catalogs_gain_sp27_sp28_f26_f27_without_renumbering(self):
        for fid in ("SP-27", "SP-28"):
            self.assertIn(fid, sp.FINDINGS)
        self.assertEqual(["F-26"], sp.FINDINGS["SP-27"][2])
        self.assertEqual(["F-27"], sp.FINDINGS["SP-28"][2])
        for fx in ("F-26", "F-27"):
            self.assertIn(fx, sp.FIXES)
        self.assertEqual("SP-01", list(sp.FINDINGS)[0])
        self.assertEqual("SP-26", list(sp.FINDINGS)[25])
        self.assertIn("CO-S0", sp.FIXES["F-26"]["title"] + sp.FIXES["F-26"]["where"])

    def test_evidence_carries_no_prompt_text(self):
        secret = "sk-SECRET-VALUE-1234"
        m = self._measure([run("al-w3", compiled=False, prompt="please use " + secret)])
        blob = json.dumps(sp.compile_findings(m)) + json.dumps(m)
        self.assertNotIn(secret, blob)

    def _session(self, sid):
        turn = {"models": ["m"], "families": ["fam"], "main_requests": 3, "cache_read": 0, "output": 10,
                "reasoning": 0, "cost_aiu": 0, "ttft_p90": None, "ctx_end": None, "sub_agents": [],
                "rereads": {}, "skills": {}, "goal_state": True, "tier": "T1", "converge_nudges": 0,
                "nudges": 0, "aborts": 0, "wall_s": 1}
        return {"facts": {"id": sid, "harness": "claude"}, "turns": [turn]}

    def test_compare_rows_carry_compiled_and_edit_dist(self):
        m = self._measure(FIXTURE)
        rows, _ = sp.family_comparison([self._session("s1")], m)
        self.assertAlmostEqual(66.7, rows[0]["compiled_pct"], places=1)
        self.assertAlmostEqual(0.18, rows[0]["edit_dist_p50"], places=4)
        rows2, _ = sp.family_comparison([self._session("other")], m)
        self.assertIsNone(rows2[0]["compiled_pct"])
        rows3, _ = sp.family_comparison([self._session("s1")])  # the old call shape still works
        self.assertIsNone(rows3[0]["compiled_pct"])

    def test_render_has_compile_section(self):
        m = self._measure(FIXTURE)
        profile = {"id": "sp-t", "generated": "now", "repos": ["r"], "window": "all sessions", "sessions": [],
                   "findings": [], "comparison": [], "fixes": sp.FIXES, "compile": m}
        md = sp.render_markdown(profile)
        self.assertIn("## Compile stage (audit log)", md)
        self.assertIn("claude-code v1", md)
        self.assertIn("| compiled |", md)
        empty = dict(profile, compile=sp.compile_measurements(tempfile.mkdtemp(), 0))
        self.assertIn(sp.NOT_RECORDED, sp.render_markdown(empty).split("## Compile stage (audit log)")[1])

    def test_compile_subcommand_prints_the_rendered_section(self):
        write_log(self.tmp, FIXTURE)
        out = io.StringIO()
        old = sys.stdout
        sys.stdout = out
        try:
            rc = sp.main(["--repo", self.tmp, "--days", "0", "compile"])
        finally:
            sys.stdout = old
        self.assertEqual(0, rc)
        self.assertIn("claude-code v1", out.getvalue())
        self.assertIn("SP-27", out.getvalue())


class DreamCompileMinerTests(unittest.TestCase):
    def setUp(self):
        self.dream = _load("dream_readers", DREAM)

    def _props(self, audit):
        corpus = {"audit": audit, "change": [], "mitigations": [], "classes": [], "markers": [], "counts": {}}
        proposals, _ = self.dream.build_proposals(corpus)
        return [p for p in proposals if str(p.get("sig", "")).startswith("CO-S0")]

    def test_compiled_false_presence_proposal(self):
        ps = [p for p in self._props([run("al-w3", compiled=False), run("al-w1", compiled_from="al-c1", edit_distance=0.1)])
              if "presence" in p["sig"]]
        self.assertEqual(1, len(ps))
        self.assertIn("1/2", ps[0]["title"])
        self.assertEqual("v", ps[0]["confidence"])
        self.assertIn("F-26", ps[0]["control"]["text"])
        self.assertIn("al-w3", ps[0]["evidence"][0]["eid"])

    def test_unanswered_dr_proposal(self):
        c = compilation("al-c1", dispatchable=False, drs=[{"id": "DR-1", "answer": None}],
                        prompt="Decision requests\n- DR-1 (#1): q? · default: d · answer: unanswered\n")
        ps = [p for p in self._props([c]) if "decision" in p["sig"]]
        self.assertEqual(1, len(ps))
        self.assertIn("DR-1", ps[0]["evidence"][0]["note"])
        self.assertEqual("al-c1", ps[0]["evidence"][0]["eid"])

    def test_dr_answered_later_not_proposed(self):
        first = compilation("al-c1", dispatchable=False, drs=[{"id": "DR-1", "answer": None}],
                            prompt="- DR-1 (#1): q? · answer: unanswered\n", ts="2026-09-19T11:00:00Z")
        later = compilation("al-c2", dispatchable=True, drs=[{"id": "DR-1", "answer": "stamp"}],
                            prompt="- DR-1 (#1): q? · answer: stamp\n", ts="2026-09-19T12:00:00Z")
        self.assertEqual([], [p for p in self._props([first, later]) if "decision" in p["sig"]])

    def test_refusals_proposal(self):
        ps = [p for p in self._props([compilation("al-c1", refusals=["raw mismatch", "raw mismatch"]),
                                      compilation("al-c2", raw="al-r2", refusals=["added scope"])])
              if "refusal" in p["sig"]]
        self.assertEqual(1, len(ps))
        notes = " ".join(e["note"] for e in ps[0]["evidence"])
        self.assertIn("raw mismatch", notes)
        self.assertIn("2", notes)
        self.assertIn("added scope", notes)

    def test_no_compile_fields_no_co_s0_proposal(self):
        self.assertEqual([], self._props([{"id": "al-1", "kind": "skill", "shortname": "a", "summary": "s",
                                           "done_when": "x"}]))
        self.assertEqual([], self._props([]))


SEAT = "runs_as: either\n"
GOOD = ("---\nname: {n}\ndescription: d\n{seat}---\n# Skill\n\n## Grounding\nConsume the compiled prompt (CO-S0).\n"
        "## Flow\nStage 1.\n")


def skill(root, name, body):
    d = os.path.join(root, "pack", "commands", name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)


class LintTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _run(self, *args):
        p = subprocess.run([sys.executable, str(LINT)] + list(args), capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    def test_self_test_exits_zero(self):
        rc, out = self._run("--self-test")
        self.assertEqual(0, rc, out)

    def test_good_skill_accepted(self):
        skill(self.tmp, "good", GOOD.format(n="good", seat=SEAT))
        rc, out = self._run("--root", self.tmp)
        self.assertEqual(0, rc, out)
        self.assertIn("clean", out)

    def test_seat_missing_refused(self):
        skill(self.tmp, "noseat", GOOD.format(n="noseat", seat=""))
        rc, out = self._run("--root", self.tmp)
        self.assertEqual(1, rc)
        self.assertIn("seat missing: noseat — fix:", out)

    def test_seat_invalid_refused(self):
        skill(self.tmp, "bad", GOOD.format(n="bad", seat="runs_as: Owner\n"))
        rc, out = self._run("--root", self.tmp)
        self.assertEqual(1, rc)
        self.assertIn("seat invalid: bad — fix:", out)

    def test_fan_out_without_co_s0_refused(self):
        skill(self.tmp, "fan", "---\nname: fan\n" + SEAT + "---\n## Flow\nRun with a fan-out cap 2 across nodes.\n")
        rc, out = self._run("--root", self.tmp)
        self.assertEqual(1, rc)
        self.assertIn("fan-out without compile: fan — fix:", out)
        skill(self.tmp, "fan", "---\nname: fan\n" + SEAT + "---\n## Flow\nCO-S0 first. Run with a fan-out cap of 3.\n")
        rc, out = self._run("--root", self.tmp)
        self.assertIn("fan-out without contract: fan — fix:", out)

    def test_fan_out_with_zero_cap_exempt(self):
        skill(self.tmp, "zero", "---\nname: zero\n" + SEAT + "---\n## Flow\nfan-out cap 0 → 2 is a raise; the tier · fan-out cap · budget row.\n")
        rc, out = self._run("--root", self.tmp)
        self.assertEqual(0, rc, out)

    def test_hard_stop_without_co_s2_refused(self):
        skill(self.tmp, "halt", "---\nname: halt\n" + SEAT + "---\n## Flow\nThen **STOP for human triage**.\n")
        rc, out = self._run("--root", self.tmp)
        self.assertEqual(1, rc)
        self.assertIn("hard stop without message: halt — fix:", out)
        skill(self.tmp, "halt", "---\nname: halt\n" + SEAT + "---\n## Flow\nThen **STOP for human triage** (CO-S2).\n")
        self.assertEqual(0, self._run("--root", self.tmp)[0])

    def test_dispatch_before_compile_refused(self):
        skill(self.tmp, "disp", "---\nname: disp\n" + SEAT + "---\n## Stage 3 — Dispatch\nspawn the tracks.\n## Later\nCO-S0.\n")
        rc, out = self._run("--root", self.tmp)
        self.assertEqual(1, rc)
        self.assertIn("dispatch before compile: disp — fix:", out)
        skill(self.tmp, "disp", "---\nname: disp\n" + SEAT + "---\n## Stage 0\nCO-S0 first.\n## Stage 3 — Dispatch\nspawn the tracks.\n")
        self.assertEqual(0, self._run("--root", self.tmp)[0])

    def test_exit_2_when_no_skills_root(self):
        rc, out = self._run("--root", self.tmp)
        self.assertEqual(2, rc)
        self.assertIn("skills root missing", out)


if __name__ == "__main__":
    unittest.main()
