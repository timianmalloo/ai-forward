"""FR-049 / class RIG-C, fourth occurrence.

`dream.py` writes the fleet learnings store and the defect-class register. `apply-learnings.py`
generates plans that mutate OTHER REPOSITORIES. They are the two scripts in the pack whose
defects propagate across the fleet, and until this file they were the two with no automated
proof at all — a regression in either was discoverable only by a human noticing a bad learning
after it had already been distributed.

These assert the properties that actually protect the fleet, not that the modules import:
  * the taint gate excludes untrusted and secret-bearing signals (dream)
  * an optimistic self-report is not promoted (dream)
  * scoring prefers an UNCONTROLLED recurring shape, which is the stated design intent
  * reconciliation says merge for a class the target already holds and add only for a novel
    one — this is what stops the federation duplicating or contradicting a target's register
  * `push` writes a plan and LEAVES THE TARGET BYTE-IDENTICAL (the never-merges invariant)
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"


def load(name):
    """Load a hyphenated script as a module (they are CLIs, not importable packages)."""
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPTS / f"{script}.py"), *args],
                          capture_output=True, text=True, cwd=cwd, timeout=90)


class DreamTaintGateTests(unittest.TestCase):
    """The taint gate is the security control on a store that is later DISTRIBUTED to other
    repositories. A false negative here ships someone's secret to the fleet."""

    def setUp(self):
        self.dream = load("dream")

    def test_an_untrusted_origin_is_tainted(self):
        untrusted = sorted(self.dream.UNTRUSTED_ORIGINS)[0]
        self.assertTrue(self.dream.is_tainted({"origin": untrusted, "sig": "anything"}))

    def test_a_clean_signal_is_not_tainted(self):
        self.assertFalse(
            self.dream.is_tainted({"origin": "audit-log", "sig": "a recurring shape"}),
            "over-tainting is also a defect: it silently empties the corpus")

    def test_a_secret_in_the_payload_taints_regardless_of_origin(self):
        signal = {"origin": "audit-log",
                  "sig": "token ghp_0123456789abcdefghijklmnopqrstuvwxyzAB"}
        self.assertTrue(self.dream.is_tainted(signal),
                        "a secret must never reach a store that is distributed to the fleet")

    def test_scrub_redacts_and_reports_the_hit(self):
        text, hit = self.dream.scrub("key ghp_0123456789abcdefghijklmnopqrstuvwxyzAB here")
        self.assertTrue(hit)
        self.assertIn("[REDACTED]", text)
        self.assertNotIn("ghp_0123456789", text)

    def test_scrub_leaves_clean_text_alone(self):
        text, hit = self.dream.scrub("an ordinary sentence about a defect class")
        self.assertFalse(hit)
        self.assertEqual("an ordinary sentence about a defect class", text)


class DreamScoringTests(unittest.TestCase):
    def setUp(self):
        self.dream = load("dream")

    def test_an_uncontrolled_class_outranks_a_controlled_one(self):
        """The stated intent: 'an uncontrolled recurring shape is higher-leverage'. If this
        inverts, /dream starts recommending work that is already done."""
        uncontrolled = self.dream.score(freq=3, distinct_days=2, has_control=False)
        controlled = self.dream.score(freq=3, distinct_days=2, has_control=True)
        self.assertGreater(uncontrolled, controlled)

    def test_score_is_monotonic_in_frequency(self):
        low = self.dream.score(freq=1, distinct_days=1, has_control=False)
        high = self.dream.score(freq=5, distinct_days=1, has_control=False)
        self.assertGreater(high, low)

    def test_score_is_bounded(self):
        extreme = self.dream.score(freq=10_000, distinct_days=10_000, has_control=False)
        self.assertLessEqual(extreme, 1.0, "an unbounded score breaks ranking")


class DreamPromotionOracleTests(unittest.TestCase):
    """An 'unverified' oracle is an optimistic self-report — promoting one would let a claim
    of a fix become a fleet-wide learning with nothing behind it."""

    def setUp(self):
        self.dream = load("dream")

    def _corpus(self, **over):
        corpus = {"mitigations": [], "classes": [], "markers": [],
                  "audit": [], "changes": []}
        corpus.update(over)
        return corpus

    def test_an_unverified_mitigation_is_not_promoted(self):
        corpus = self._corpus(mitigations=[
            {"oracle": "unverified", "summary": "I believe I fixed it", "origin": "local"}])
        proposals, _diary = self.dream.build_proposals(corpus)
        self.assertEqual([], [p for p in proposals if "I believe" in json.dumps(p)],
                         "an optimistic self-report must not become a learning")

    def test_a_red_green_mitigation_is_promoted(self):
        corpus = self._corpus(mitigations=[{
            "oracle": "red-green", "summary": "observed failing then passing",
            "class": "DM-A", "control": "a cross-surface consistency test",
            "origin": "local", "tests": ["test_x"]}])
        proposals, _diary = self.dream.build_proposals(corpus)
        self.assertTrue(proposals, "a verified mitigation is the strongest promotion signal")

    def test_a_tainted_mitigation_is_excluded_and_counted(self):
        untrusted = sorted(self.dream.UNTRUSTED_ORIGINS)[0]
        corpus = self._corpus(mitigations=[{
            "oracle": "red-green", "summary": "x", "origin": untrusted}])
        _proposals, diary = self.dream.build_proposals(corpus)
        self.assertGreaterEqual(diary["excluded"], 1,
                                "an exclusion must be counted, not silently dropped")


class DreamCliTests(unittest.TestCase):
    def test_help_exits_zero(self):
        self.assertEqual(0, run("dream", "--help").returncode)

    def test_run_on_an_empty_repo_does_not_crash(self):
        """A repo with no corpus must produce an empty dream, not a traceback."""
        with tempfile.TemporaryDirectory() as temp:
            os.makedirs(os.path.join(temp, "docs", "audit"))
            result = run("dream", "--root", temp, "run", cwd=temp)
            self.assertEqual(0, result.returncode,
                             f"empty corpus must be a valid outcome:\n{result.stderr[-800:]}")


class ApplyLearningsReconciliationTests(unittest.TestCase):
    """Reconciliation is the whole safety property of the federation: it decides whether an
    incoming learning is NEW to a target or something the target already holds. Get it wrong
    in one direction and every push duplicates the target's register; wrong in the other and
    approved learnings are silently dropped."""

    def setUp(self):
        self.apply = load("apply-learnings")

    def _register(self, repo, body):
        lessons = Path(repo) / "docs" / "lessons"
        lessons.mkdir(parents=True)
        (lessons / "defect-classes.md").write_text(body, encoding="utf-8")
        return self.apply.target_register(repo)

    def test_a_class_the_target_already_holds_reconciles_to_merge(self):
        with tempfile.TemporaryDirectory() as temp:
            reg = self._register(temp, "### PACK-E — An ambiguous proper noun resolved "
                                       "inside my own frame\n- **Status:** `uncontrolled`\n")
            verdict = self.apply.reconcile(
                {"sig": "PACK-E · An ambiguous proper noun resolved inside my own frame"}, reg)
            self.assertEqual("merge", verdict,
                             "pushing a duplicate into a target's register is the failure "
                             "this reconciliation exists to prevent")

    def test_a_genuinely_new_class_reconciles_to_add(self):
        with tempfile.TemporaryDirectory() as temp:
            reg = self._register(temp, "### PACK-E — An ambiguous proper noun\n")
            verdict = self.apply.reconcile(
                {"sig": "OPS-CI · Unbounded per-item CI cost on a premium runner"}, reg)
            self.assertEqual("add", verdict,
                             "over-merging silently drops an approved learning")

    def test_an_empty_target_register_takes_everything_as_new(self):
        with tempfile.TemporaryDirectory() as temp:
            reg = self.apply.target_register(temp)
            self.assertEqual("add", self.apply.reconcile({"sig": "ANY-X · a novel shape"}, reg))

    def test_slug_is_deterministic_and_bounded(self):
        long_signature = "X" * 400
        first = self.apply.slug(long_signature)
        self.assertEqual(first, self.apply.slug(long_signature), "must be deterministic")
        self.assertLessEqual(len(first), 60, "an unbounded slug becomes an unusable filename")

    def test_slug_normalises_punctuation_so_one_class_has_one_identity(self):
        self.assertEqual(self.apply.slug("PACK-E · An ambiguous noun"),
                         self.apply.slug("PACK-E - An  ambiguous  noun"))

    def test_target_detection_recognises_an_installed_pack(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertFalse(self.apply.target_has_pack(temp))
            os.makedirs(os.path.join(temp, ".claude"))
            self.assertTrue(self.apply.target_has_pack(temp))


class ApplyLearningsNeverMergesTests(unittest.TestCase):
    """The load-bearing invariant, stated in the tool's own help text: 'push ... as reviewable
    plans (never merges)'. It writes into someone else's repository's future, so the assertion
    is byte-identity of the target after a push — not merely that no exception was raised."""

    def setUp(self):
        self.apply = load("apply-learnings")

    def test_push_writes_a_plan_and_leaves_the_target_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "ai-forward"
            target = Path(temp) / "victim"
            (root / "learnings").mkdir(parents=True)
            (root / "learnings" / "fleet-classes.jsonl").write_text(
                json.dumps({"sig": "NEW-X · a shape the target has never seen",
                            "control": {"rung": "automated control", "text": "a test"},
                            "origin": "dream"}) + "\n",
                encoding="utf-8")
            lessons = target / "docs" / "lessons"
            lessons.mkdir(parents=True)
            register = lessons / "defect-classes.md"
            original = "### OLD-A — something else\n- **Status:** `controlled`\n"
            register.write_text(original, encoding="utf-8")
            (target / ".claude").mkdir()

            result = run("apply-learnings", "--root", str(root), "push",
                         "--repos", str(target))

            self.assertEqual(0, result.returncode, result.stderr[-900:])
            self.assertEqual(original, register.read_text(encoding="utf-8"),
                             "apply-learnings MUST NOT mutate a target repository")
            plans = list((root / "learnings" / "plans").glob("*"))
            self.assertTrue(plans, "a push with a novel learning must produce a plan")

    def test_help_exits_zero(self):
        self.assertEqual(0, run("apply-learnings", "--help").returncode)


class ControlShapeToleranceTests(unittest.TestCase):
    """Found BY these tests, in the first assertion written against apply-learnings.py:
    `l.get("control", {}).get("text")` raised an unhandled AttributeError when `control` was
    a bare string — crashing the tool that writes into other people's repositories, possibly
    after it had already written plans for earlier targets. The fleet store is a plain
    committed JSONL anyone can hand-edit, so the string shape is reachable. The sweep found
    the identical line in dream.py: one class, two instances (CI2)."""

    def test_apply_learnings_accepts_the_object_shape_dream_writes(self):
        apply = load("apply-learnings")
        self.assertEqual("a test",
                         apply.control_text({"control": {"rung": "automated", "text": "a test"}}))

    def test_apply_learnings_accepts_a_bare_string_control(self):
        apply = load("apply-learnings")
        self.assertEqual("a test", apply.control_text({"control": "a test"}))

    def test_apply_learnings_still_rejects_a_genuinely_absent_control(self):
        """The CI6 guard must be unchanged — only the crash is gone."""
        apply = load("apply-learnings")
        self.assertEqual("", apply.control_text({}))
        self.assertEqual("", apply.control_text({"control": None}))
        self.assertEqual("", apply.control_text({"control": {"rung": "x"}}))

    def test_dream_tolerates_both_shapes_identically(self):
        dream = load("dream")
        self.assertEqual("a test", dream.control_text({"control": "a test"}))
        self.assertEqual("a test", dream.control_text({"control": {"text": "a test"}}))
        self.assertEqual("", dream.control_text({"control": []}))


if __name__ == "__main__":
    unittest.main()
