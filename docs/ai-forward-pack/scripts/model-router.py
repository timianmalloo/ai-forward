#!/usr/bin/env python3
"""model-router.py -- deterministic model-orchestration routing lookup.

Python 3.8+, stdlib only, cross-platform (Windows/macOS). No model, no network.
It is the archetype-A (deterministic) embodiment of the Model-Orchestration Standard
(knowledge/model-orchestration.md): given a skill (and optional profile), it returns the
recommended execution-model *tier* per activity archetype -- a strong default the
Orchestrator auto-dispatches and the human may overrule (M3).

Routing is expressed in capability TIERS, not hard model IDs (M8) -- names age. The
illustrative model/effort per tier is a hint for the current Copilot-CLI roster and is
meant to be re-pinned as the roster changes.

Usage:
  model-router.py route --skill design [--profile efficiency|cost] [--json]
  model-router.py list-skills
  model-router.py archetypes
  model-router.py tiers
"""

import argparse
import json
import sys

# Activity archetypes (model-orchestration.md Section 1): id -> (label, capability, tier).
ARCHETYPES = {
    "A": ("deterministic-mechanics", "none - this is a script", "deterministic"),
    "B": ("grounding-traversal", "light", "fast"),
    "C": ("research-spikes", "capable + tools, parallelizable", "research"),
    "D": ("broad-reasoning", "frontier reasoning, high effort", "frontier"),
    "E": ("adversarial-review", "frontier, high effort, model != author", "frontier"),
    "F": ("implementation-tdd", "strong coding model; proof is deterministic tests", "coding"),
    "G": ("creative-ux-ui", "capable, visual/UX-aware", "frontier"),
    "H": ("documentation", "mid", "mid"),
    "I": ("verification-eval", "deterministic tests + distinct judge for content", "mixed"),
}

# Illustrative tier -> model/effort mapping for the Copilot CLI. Re-pin as the roster moves.
TIERS = {
    "deterministic": {"model": "(script - no model)", "effort": "n/a"},
    "fast": {"model": "mini/flash-class", "effort": "low"},
    "mid": {"model": "mid reasoning", "effort": "medium"},
    "coding": {"model": "coding-optimized", "effort": "high"},
    "research": {"model": "capable + tools (parallel background agents)", "effort": "high"},
    "frontier": {"model": "strongest reasoning", "effort": "high/xhigh/max"},
    "mixed": {"model": "script + distinct judge model", "effort": "high"},
}

# Per-skill dominant archetypes (model-orchestration.md Section 2), ordered by weight.
SKILL_PROFILES = {
    "collectknowledge": ["C", "D", "A"],
    "adddomainexperts": ["D", "A"],
    "specify": ["D", "C", "E"],
    "define-architecture": ["D", "C", "E"],
    "design": ["D", "C", "G", "E"],
    "implement": ["F", "I", "E"],
    "investigate": ["D", "C", "E"],
    "document": ["H", "A"],
    "adopt": ["B", "A", "D", "C"],
    "forensicreview": ["H", "D", "E", "A"],
    "migrate": ["A", "F", "D", "E"],
    "updatepack": ["A", "B"],
    "addpacktorepo": ["A", "B"],
    "extendaibundle": ["C", "D", "F", "A"],
    "auditlog": ["A"],
    "prompts": ["A"],
    "searchprompts": ["A"],
}

# Skills whose highest-rigor work must always get the best model (M4), even in cost mode.
HIGH_RIGOR_SKILLS = {"define-architecture", "investigate"}


def is_hard_veto(archetype):
    """E (adversarial review) is always a hard-veto gate: reviewer model != author (M5)."""
    return archetype == "E"


def route_archetype(archetype, profile, skill):
    """Return the routing record for one archetype under a profile."""
    label, capability, base_tier = ARCHETYPES[archetype]
    tier = base_tier
    downgraded = False
    # Cost mode trades DOWN only borderline T1 work (B, H, non-veto D), never a hard-veto
    # surface, never the high-rigor skills' reasoning (M4). Deterministic/coding/research stay.
    if profile == "cost" and skill not in HIGH_RIGOR_SKILLS:
        if archetype in ("B", "H"):
            tier = "fast"
            downgraded = base_tier != "fast"
        elif archetype == "D":
            tier = "mid"
            downgraded = True
    hint = dict(TIERS[tier])
    record = {
        "archetype": archetype,
        "label": label,
        "capability": capability,
        "tier": tier,
        "model": hint["model"],
        "effort": hint["effort"],
        "hard_veto": is_hard_veto(archetype),
        "distinct_from_author": is_hard_veto(archetype),
        "downgraded_by_cost": downgraded,
    }
    return record


def route_skill(skill, profile):
    if skill not in SKILL_PROFILES:
        raise KeyError(skill)
    archetypes = SKILL_PROFILES[skill]
    records = [route_archetype(a, profile, skill) for a in archetypes]
    return {
        "skill": skill,
        "profile": profile,
        "high_rigor": skill in HIGH_RIGOR_SKILLS,
        "dispatch": "auto (Orchestrator); human may overrule (M3)",
        "routing": records,
    }


def cmd_route(args):
    try:
        result = route_skill(args.skill, args.profile)
    except KeyError:
        sys.stderr.write(
            "unknown skill '%s' -- run 'model-router.py list-skills'\n" % args.skill
        )
        return 2
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    print("skill: %s   profile: %s%s" % (
        result["skill"], result["profile"],
        "   [HIGH-RIGOR: best model always]" if result["high_rigor"] else "",
    ))
    print("dispatch: %s" % result["dispatch"])
    for r in result["routing"]:
        flags = []
        if r["hard_veto"]:
            flags.append("hard-veto: reviewer model != author")
        if r["downgraded_by_cost"]:
            flags.append("cost-downgraded")
        suffix = ("   (%s)" % "; ".join(flags)) if flags else ""
        print("  [%s] %-22s -> tier=%-13s model=%s (%s)%s" % (
            r["archetype"], r["label"], r["tier"], r["model"], r["effort"], suffix,
        ))
    return 0


def cmd_list_skills(_args):
    for skill in sorted(SKILL_PROFILES):
        print("%-20s %s" % (skill, " ".join(SKILL_PROFILES[skill])))
    return 0


def cmd_archetypes(_args):
    for a in sorted(ARCHETYPES):
        label, capability, tier = ARCHETYPES[a]
        print("%s  %-22s tier=%-13s %s" % (a, label, tier, capability))
    return 0


def cmd_tiers(_args):
    for tier in TIERS:
        print("%-13s model=%-45s effort=%s" % (tier, TIERS[tier]["model"], TIERS[tier]["effort"]))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Model-orchestration routing lookup.")
    sub = parser.add_subparsers(dest="command")
    p_route = sub.add_parser("route", help="recommend tiers for a skill's activities")
    p_route.add_argument("--skill", required=True)
    p_route.add_argument("--profile", choices=["efficiency", "cost"], default="efficiency")
    p_route.add_argument("--json", action="store_true")
    p_route.set_defaults(func=cmd_route)
    sub.add_parser("list-skills", help="list skills and their archetypes").set_defaults(func=cmd_list_skills)
    sub.add_parser("archetypes", help="list activity archetypes").set_defaults(func=cmd_archetypes)
    sub.add_parser("tiers", help="list capability tiers and illustrative models").set_defaults(func=cmd_tiers)
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
