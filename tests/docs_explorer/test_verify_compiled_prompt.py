"""The compile-stage gate (verify-compiled-prompt.py) — the nine directions as unit tests.

Design: docs/design/compile-stage.md (Contracts › Exposed; Test plan T1/D1). The gate is the
control for "no added scope" (spec US-4): every clause in *Done when* and *Not in scope* must
trace to a verbatim phrase of the raw prompt or to a complete, consequential assumption with a
decision request. These tests pin each refusal code, the refusal grammar, and the self-test.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "pack", "scripts", "verify-compiled-prompt.py")

spec = importlib.util.spec_from_file_location("verify_compiled_prompt", SCRIPT)
vcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vcp)

RAW = ("Add a --dry-run flag to sync-pack.ps1. Don't touch the install counts.\n"
       "Done when the flag is documented in README.\n")
RAW_ID = "al-0001"
GRAMMAR = re.compile(r"^[a-z][a-z -]*: .+ — fix: .+$")


def base_doc() -> dict:
    return {
        "schema": "compiled-prompt/1",
        "raw_id": RAW_ID,
        "raw_sha256": hashlib.sha256(RAW.encode("utf-8")).hexdigest(),
        "raw_text_normalised": False,
        "harness": "claude-code", "template": "claude-code", "template_version": 1,
        "mode": "compiled",
        "goal_state": {"goal": "Add a --dry-run flag to sync-pack.ps1",
                       "done_when": ["the flag is documented in README"],
                       "not_in_scope": ["the install counts"],
                       "tier": "T1", "fan_out_cap": 0, "context_ceiling": 400000,
                       "main_line_budget": 40},
        "clauses": [
            {"section": "done_when", "text": "the flag is documented in README",
             "trace": {"kind": "phrase", "ref": "the flag is documented in README"}},
            {"section": "not_in_scope", "text": "the install counts",
             "trace": {"kind": "phrase", "ref": "Don't touch the install counts"}},
        ],
        "references": [], "graph_neighbours": [],
        "assumptions": [{"id": "#1", "belief": "sync-pack.ps1 has no dry-run flag today",
                         "confirm": "grep -n dry-run tools/sync-pack.ps1",
                         "breaks": "the flag would be added twice", "consequential": False}],
        "decision_requests": [],
        "contract_slot": {k: None for k in ("width_cap", "transient_retry", "per_branch_exit",
                                            "join_rule", "containment", "termination",
                                            "deadline", "fallback")},
        "dispatchable": True,
        "provenance": {"engine_seconds": None, "compiler_model": None, "compile_tokens": None,
                       "refusals": [], "retries": 0},
    }


def codes(refusals):
    return [r.split(": ", 1)[0] for r in refusals]


class NineDirections(unittest.TestCase):
    def check(self, doc, expected_code, target=None):
        refusals = vcp.verify_document(doc, RAW)
        self.assertIn(expected_code, codes(refusals), refusals)
        for r in refusals:
            self.assertRegex(r, GRAMMAR)
        if target is not None:
            self.assertTrue(any(r.startswith(f"{expected_code}: {target} — fix: ") for r in refusals), refusals)

    def test_1_added_done_when_clause_refused(self):
        doc = base_doc()
        doc["clauses"].append({"section": "done_when", "text": "CI is green", "trace": None})
        self.check(doc, "added scope", "CI is green")

    def test_2_added_not_in_scope_clause_refused(self):
        doc = base_doc()
        doc["clauses"].append({"section": "not_in_scope", "text": "the README", "trace": None})
        self.check(doc, "added scope", "the README")

    def test_3_trace_to_absent_phrase_refused(self):
        doc = base_doc()
        doc["clauses"][0]["trace"]["ref"] = "the flag is documented in CHANGELOG"
        self.check(doc, "invalid trace", "the flag is documented in README")

    def test_4_missing_field_refused(self):
        doc = base_doc()
        doc["goal_state"]["goal"] = ""
        self.check(doc, "field missing", "goal")

    def test_5_raw_hash_mismatch_refused(self):
        doc = base_doc()
        doc["raw_sha256"] = "0" * 64
        self.check(doc, "raw mismatch", RAW_ID)

    def test_6_complete_marker_accepted(self):
        self.assertEqual(vcp.verify_document(base_doc(), RAW), [])

    def test_7_incomplete_marker_refused(self):
        doc = base_doc()
        doc["assumptions"][0]["breaks"] = ""
        self.check(doc, "assumption incomplete", "#1")

    def test_8_trace_to_missing_assumption_refused(self):
        doc = base_doc()
        doc["clauses"][0]["trace"] = {"kind": "assume", "ref": "#9"}
        self.check(doc, "invalid trace", "the flag is documented in README")

    def test_9_assumption_only_trace_without_dr_refused(self):
        doc = base_doc()
        doc["clauses"][0]["trace"] = {"kind": "assume", "ref": "#1"}
        self.check(doc, "decision request missing", "#1")
        # consequential alone is not enough — the DR must exist
        doc["assumptions"][0]["consequential"] = True
        self.check(doc, "decision request missing", "#1")
        doc["decision_requests"].append({"id": "DR-1", "assumption": "#1",
                                         "question": "does the flag exist?", "default": "no",
                                         "answer": None})
        self.assertEqual(vcp.verify_document(doc, RAW), [])

    def test_case_change_is_invalid_trace(self):
        doc = base_doc()
        doc["clauses"][1]["trace"]["ref"] = "don't touch the install counts"
        self.check(doc, "invalid trace", "the install counts")

    def test_whitespace_runs_collapse_but_line_endings_normalise(self):
        doc = base_doc()
        doc["clauses"][0]["trace"]["ref"] = "the   flag is\tdocumented in README"
        crlf = RAW.replace("\n", "\r\n")
        doc["raw_sha256"] = hashlib.sha256(crlf.encode("utf-8")).hexdigest()
        self.assertEqual(vcp.verify_document(doc, crlf), [])

    def test_not_compiled_mode_skips_traces_keeps_fields_and_hash(self):
        doc = base_doc()
        doc["mode"] = "not-compiled"
        for k in doc["goal_state"]:
            doc["goal_state"][k] = "NOT COMPILED"
        doc["clauses"] = []
        self.assertEqual(vcp.verify_document(doc, RAW), [])
        doc["raw_sha256"] = "0" * 64
        self.assertIn("raw mismatch", codes(vcp.verify_document(doc, RAW)))
        doc["raw_sha256"] = base_doc()["raw_sha256"]
        doc["goal_state"]["tier"] = ""
        self.assertIn("field missing", codes(vcp.verify_document(doc, RAW)))

    def test_pass_through_mode_reports_under_its_own_code(self):
        doc = base_doc()
        doc["mode"] = "pass-through"
        doc["goal_state"]["tier"] = ""
        refusals = vcp.verify_document(doc, RAW)
        self.assertEqual(codes(refusals), ["pass-through refused"])
        self.assertTrue(refusals[0].startswith("pass-through refused: tier — fix: "))
        doc = base_doc()
        doc["mode"] = "pass-through"
        doc["clauses"][0]["trace"] = None   # trace checks are skipped in pass-through
        self.assertEqual(vcp.verify_document(doc, RAW), [])


class CliAndSelfTest(unittest.TestCase):
    def _repo(self, tmp, doc, raw=RAW):
        audit = os.path.join(tmp, "docs", "audit")
        os.makedirs(audit)
        with open(os.path.join(audit, "audit-log.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"id": RAW_ID, "kind": "prompt", "shortname": "dry-run flag",
                                 "prompt": raw, "session": "s", "summary": "x",
                                 "datetime": "2026-09-19T00:00:00Z"}) + "\n")
        path = os.path.join(tmp, "compiled.json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh)
        return os.path.join(tmp, "docs"), path

    def test_verify_cli_pass_prints_trace_table_and_refusal_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit_root, path = self._repo(tmp, base_doc())
            r = subprocess.run([sys.executable, SCRIPT, "verify", path, "--audit-root", audit_root],
                               capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("the flag is documented in README", r.stdout)
            doc = base_doc()
            doc["clauses"].append({"section": "done_when", "text": "CI is green", "trace": None})
            sub = os.path.join(tmp, "b")
            os.makedirs(sub)
            audit_root, path = self._repo(sub, doc)
            r = subprocess.run([sys.executable, SCRIPT, "verify", path, "--audit-root", audit_root],
                               capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(r.returncode, 1)
            self.assertRegex(r.stderr.strip().splitlines()[0], GRAMMAR)
            self.assertIn("added scope: CI is green", r.stderr)

    def test_verify_cli_raw_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = base_doc()
            doc["raw_id"] = "al-9999"
            audit_root, path = self._repo(tmp, doc)
            r = subprocess.run([sys.executable, SCRIPT, "verify", path, "--audit-root", audit_root],
                               capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(r.returncode, 1)
            self.assertIn("raw not found: al-9999 — fix: ", r.stderr)

    def test_usage_exit_2(self):
        r = subprocess.run([sys.executable, SCRIPT, "verify", "/nonexistent/compiled.json"],
                           capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(r.returncode, 2)

    def test_selftest_exits_zero_and_prints_nine_directions(self):
        r = subprocess.run([sys.executable, SCRIPT, "--self-test"],
                           capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for n in range(1, 10):
            self.assertIn(f"direction {n}", r.stdout)

    def test_every_refusal_matches_the_grammar(self):
        for r in vcp.self_test_refusals():
            self.assertRegex(r, GRAMMAR)


if __name__ == "__main__":
    unittest.main()
