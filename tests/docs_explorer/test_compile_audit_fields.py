"""P7 compile stage (design-compile-stage, Track B): the audit-log and prompt-log fields.

A compilation is a new audit `kind` (note-20260919-compilation-is-an-audit-kind); a workflow
started from a compiled prompt records `compiled_from` + `edit_distance`; a plain skill entry
records `compiled: false`; a compilation never consumes a start marker (it is a record, not a
run); `--from-json` carries the structured `compiled` object, `mode` and `dispatchable` through;
a recompile is a second entry; `selfcheck` never flags a compilation for a missing goal-state;
`/prompts` shows a compilation row with its raw twin and `--raw` narrows to the pair.

Written red-first against the pack SOURCE scripts (pack/scripts/*), the files Track B owns;
observed failing before the change landed.
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDIT = ROOT / "pack" / "scripts" / "audit-log.py"
PROMPT_LOG = ROOT / "pack" / "scripts" / "prompt-log.py"

COMPILED_OBJECT = {
    "schema": "compiled-prompt/1",
    "raw_id": "al-0001",
    "raw_sha256": "0" * 64,
    "harness": "claude-code",
    "template": "claude-code",
    "template_version": 1,
    "goal_state": {"goal": "g", "done_when": ["d"], "not_in_scope": ["n"], "tier": "T0",
                   "fan_out_cap": 0, "context_ceiling": 400000, "main_line_budget": 10},
    "clauses": [{"section": "done_when", "text": "d", "trace": {"kind": "phrase", "ref": "d"}}],
    "assumptions": [],
    "decision_requests": [],
    "provenance": {"engine_seconds": 0.1, "compiler_model": None, "compile_tokens": None,
                   "refusals": [], "retries": 0},
}


def _run(script, root, *args, stdin=None):
    return subprocess.run(
        [sys.executable, str(script), "--root", str(root), *args],
        capture_output=True, text=True, encoding="utf-8", timeout=30, input=stdin,
    )


def _lines(root):
    path = root / "audit" / "audit-log.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class _Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name) / "docs"
        (self.root / "audit").mkdir(parents=True)
        self.addCleanup(self._tmp.cleanup)

    def append(self, *args, stdin=None):
        return _run(AUDIT, self.root, "append", *args, stdin=stdin)

    def compilation_json(self, raw_id="al-0001", dispatchable=False, mode="compiled"):
        compiled = dict(COMPILED_OBJECT, raw_id=raw_id)
        return json.dumps({"compiled": compiled, "mode": mode, "dispatchable": dispatchable})

    def append_compilation(self, shortname="compile-x", raw_id="al-0001", session="s"):
        return self.append("--kind", "compilation", "--shortname", shortname, "--session", session,
                           "--prompt", "rendered compiled text", "--summary", f"compiled {raw_id}",
                           "--from-json", "-", stdin=self.compilation_json(raw_id=raw_id))


class CompilationKindTests(_Base):
    def test_compilation_kind_accepted(self):
        result = self.append_compilation()
        self.assertEqual(result.returncode, 0, result.stderr)
        entries = _lines(self.root)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["kind"], "compilation")

    def test_from_json_carries_compiled_mode_dispatchable(self):
        result = self.append_compilation()
        self.assertEqual(result.returncode, 0, result.stderr)
        entry = _lines(self.root)[0]
        self.assertEqual(entry["mode"], "compiled")
        self.assertIs(entry["dispatchable"], False)
        self.assertEqual(entry["compiled"]["raw_id"], "al-0001")
        self.assertEqual(entry["compiled"]["schema"], "compiled-prompt/1")
        self.assertEqual(entry["compiled"]["goal_state"]["done_when"], ["d"])

    def test_recompile_is_a_second_entry_naming_the_same_raw_id(self):
        self.assertEqual(self.append_compilation(shortname="compile-x").returncode, 0)
        self.assertEqual(self.append_compilation(shortname="compile-x").returncode, 0)
        entries = _lines(self.root)
        self.assertEqual(len(entries), 2)
        self.assertNotEqual(entries[0]["id"], entries[1]["id"])
        self.assertEqual(entries[0]["compiled"]["raw_id"], entries[1]["compiled"]["raw_id"])

    def test_compilation_never_consumes_a_start_marker_and_writes_no_duration(self):
        started = _run(AUDIT, self.root, "start", "--session", "s", "--skill", "compile")
        self.assertEqual(started.returncode, 0, started.stderr)
        result = self.append_compilation(session="s")
        self.assertEqual(result.returncode, 0, result.stderr)
        compilation = _lines(self.root)[0]
        self.assertNotIn("duration_seconds", compilation)
        self.assertNotIn("duration_source", compilation)
        self.assertNotIn("started_at", compilation)
        # The marker is still live: the skill's own closing entry consumes it.
        closing = self.append("--kind", "skill", "--skill", "compile", "--shortname", "compile-x",
                              "--session", "s", "--prompt", "p", "--summary", "s")
        self.assertEqual(closing.returncode, 0, closing.stderr)
        self.assertIn("duration_seconds", _lines(self.root)[1])

    def test_compilation_entry_does_not_carry_compiled_false(self):
        self.assertEqual(self.append_compilation().returncode, 0)
        self.assertNotEqual(_lines(self.root)[0].get("compiled"), False)


class WorkflowEntryFieldsTests(_Base):
    def test_compiled_from_and_edit_distance_written(self):
        result = self.append("--kind", "skill", "--skill", "implement", "--shortname", "impl",
                             "--session", "s", "--prompt", "p", "--summary", "s",
                             "--compiled-from", "al-0002", "--edit-distance", "0.0731")
        self.assertEqual(result.returncode, 0, result.stderr)
        entry = _lines(self.root)[0]
        self.assertEqual(entry["compiled_from"], "al-0002")
        self.assertAlmostEqual(entry["edit_distance"], 0.0731)
        self.assertNotIn("compiled", entry)

    def test_edit_distance_without_compiled_from_is_refused(self):
        result = self.append("--kind", "skill", "--shortname", "impl", "--session", "s",
                             "--prompt", "p", "--summary", "s", "--edit-distance", "0.2")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("compiled-from", result.stderr)
        self.assertEqual(_lines(self.root), [])

    def test_edit_distance_outside_unit_interval_is_refused(self):
        result = self.append("--kind", "skill", "--shortname", "impl", "--session", "s",
                             "--prompt", "p", "--summary", "s",
                             "--compiled-from", "al-0002", "--edit-distance", "1.5")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertEqual(_lines(self.root), [])

    def test_compiled_false_on_plain_skill_entry(self):
        result = self.append("--kind", "skill", "--skill", "implement", "--shortname", "impl",
                             "--session", "s", "--prompt", "p", "--summary", "s")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIs(_lines(self.root)[0]["compiled"], False)

    def test_compiled_false_absent_on_non_skill_kinds(self):
        for kind in ("manual", "prompt", "script"):
            result = self.append("--kind", kind, "--shortname", kind, "--session", "s",
                                 "--prompt", "p", "--summary", "s")
            self.assertEqual(result.returncode, 0, result.stderr)
        for entry in _lines(self.root):
            self.assertNotIn("compiled", entry, entry["kind"])

    def test_from_json_compiled_from_counts_as_given(self):
        payload = json.dumps({"compiled_from": "al-0002", "edit_distance": 0.5})
        result = self.append("--kind", "skill", "--shortname", "impl", "--session", "s",
                             "--prompt", "p", "--summary", "s", "--from-json", "-", stdin=payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        entry = _lines(self.root)[0]
        self.assertEqual(entry["compiled_from"], "al-0002")
        self.assertAlmostEqual(entry["edit_distance"], 0.5)
        self.assertNotIn("compiled", entry)


class SelfcheckTests(_Base):
    def test_selfcheck_does_not_flag_a_compilation_for_a_missing_goal(self):
        self.assertEqual(self.append_compilation(session="S").returncode, 0)
        result = _run(AUDIT, self.root, "selfcheck", "--session", "S", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["gaps"], [])
        self.assertEqual(report["substantive"], 0)


class PromptLogTwinTests(_Base):
    def _seed(self):
        raw = self.append("--kind", "prompt", "--shortname", "raw-one", "--session", "s",
                          "--prompt", "build the widget", "--summary", "prompt logged for reuse")
        self.assertEqual(raw.returncode, 0, raw.stderr)
        raw_id = raw.stdout.strip()
        other = self.append("--kind", "prompt", "--shortname", "raw-two", "--session", "s",
                            "--prompt", "unrelated prose", "--summary", "prompt logged for reuse")
        self.assertEqual(other.returncode, 0, other.stderr)
        compiled = self.append_compilation(shortname="compile-raw-one", raw_id=raw_id)
        self.assertEqual(compiled.returncode, 0, compiled.stderr)
        return raw_id

    def _prompt_log(self, *args):
        store = self.root / "audit" / "audit-log.jsonl"
        return subprocess.run(
            [sys.executable, str(PROMPT_LOG), "--store", str(store), *args],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )

    def test_list_suffixes_compilation_rows(self):
        raw_id = self._seed()
        result = self._prompt_log("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"compile-raw-one ⟲ compiled from {raw_id}", result.stdout)
        self.assertTrue(any(". raw-one   ·" in line for line in result.stdout.splitlines()), result.stdout)
        self.assertFalse(any(". raw-one \u27f2" in line for line in result.stdout.splitlines()), result.stdout)

    def test_raw_filter_shows_the_pair_only(self):
        raw_id = self._seed()
        result = self._prompt_log("list", "--raw", raw_id, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(result.stdout)
        self.assertEqual({r["label"] for r in rows}, {"raw-one", "compile-raw-one"})

    def test_search_matches_both_kinds_and_honours_raw(self):
        raw_id = self._seed()
        both = self._prompt_log("search", "widget", "--json")
        self.assertEqual(both.returncode, 0, both.stderr)
        self.assertEqual({r["label"] for r in json.loads(both.stdout)}, {"raw-one"})
        compiled = self._prompt_log("search", "rendered", "--json")
        self.assertEqual({r["label"] for r in json.loads(compiled.stdout)}, {"compile-raw-one"})
        narrowed = self._prompt_log("search", "rendered", "--raw", raw_id, "--json")
        self.assertEqual({r["label"] for r in json.loads(narrowed.stdout)}, {"compile-raw-one"})
        other = self._prompt_log("search", "unrelated", "--raw", raw_id, "--json")
        self.assertEqual(json.loads(other.stdout), [])


if __name__ == "__main__":
    unittest.main()
