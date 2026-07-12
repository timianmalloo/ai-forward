"""Tests for pack/scripts/model-router.py -- the Model-Orchestration routing lookup.

Assertions are red-first: each would fail if the routing rules in
knowledge/model-orchestration.md (M4 cost/efficiency, M5 adversary independence, M6
deterministic-to-script) were not implemented.
"""

import importlib.util
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, "pack", "scripts", "model-router.py")


def load_router():
    spec = importlib.util.spec_from_file_location("model_router", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ModelRouterTests(unittest.TestCase):
    def setUp(self):
        self.mr = load_router()

    def test_every_skill_has_a_profile(self):
        # All 17 pack skills must be routable.
        self.assertEqual(len(self.mr.SKILL_PROFILES), 17)

    def test_adversary_is_hard_veto_and_distinct_in_both_profiles(self):
        # M5: E (adversarial review) is a hard-veto gate; reviewer model != author, always.
        for profile in ("efficiency", "cost"):
            rec = self.mr.route_archetype("E", profile, "design")
            self.assertTrue(rec["hard_veto"], profile)
            self.assertTrue(rec["distinct_from_author"], profile)
            self.assertEqual(rec["tier"], "frontier", profile)
            self.assertFalse(rec["downgraded_by_cost"], profile)

    def test_cost_mode_downgrades_borderline_but_not_hard_veto(self):
        # M4: cost mode trades DOWN borderline T1 work (B, H, non-veto D) only.
        b = self.mr.route_archetype("B", "cost", "adopt")
        self.assertEqual(b["tier"], "fast")
        d = self.mr.route_archetype("D", "cost", "specify")
        self.assertEqual(d["tier"], "mid")
        self.assertTrue(d["downgraded_by_cost"])
        # E is never downgraded by cost.
        e = self.mr.route_archetype("E", "cost", "specify")
        self.assertEqual(e["tier"], "frontier")

    def test_high_rigor_skills_keep_best_model_in_cost_mode(self):
        # M4: architecture and investigation always get the best model, even in cost mode.
        for skill in ("define-architecture", "investigate"):
            d = self.mr.route_archetype("D", "cost", skill)
            self.assertEqual(d["tier"], "frontier", skill)
            self.assertFalse(d["downgraded_by_cost"], skill)

    def test_efficiency_default_keeps_frontier_reasoning(self):
        result = self.mr.route_skill("define-architecture", "efficiency")
        tiers = {r["archetype"]: r["tier"] for r in result["routing"]}
        self.assertEqual(tiers["D"], "frontier")
        self.assertEqual(tiers["E"], "frontier")

    def test_deterministic_mechanics_never_use_a_model(self):
        # M6: archetype A is a script, in every profile and skill.
        for profile in ("efficiency", "cost"):
            rec = self.mr.route_archetype("A", profile, "auditlog")
            self.assertEqual(rec["tier"], "deterministic")
            self.assertIn("script", rec["model"])

    def test_utility_skills_are_deterministic_only(self):
        for skill in ("auditlog", "prompts", "searchprompts", "updatepack", "addpacktorepo"):
            result = self.mr.route_skill(skill, "efficiency")
            self.assertTrue(
                all(r["tier"] in ("deterministic", "fast") for r in result["routing"]),
                skill,
            )

    def test_unknown_skill_raises(self):
        with self.assertRaises(KeyError):
            self.mr.route_skill("no-such-skill", "efficiency")

    def test_cli_route_json_runs(self):
        rc = self.mr.main(["route", "--skill", "design", "--profile", "efficiency", "--json"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
