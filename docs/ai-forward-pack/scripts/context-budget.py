#!/usr/bin/env python3
"""context-budget.py — the always-on context budget, measured (AI-Forward Pack).

An instruction set that is attached to every request IS the static prefix of every call.
It is re-read on every turn, it is billed on every turn (cached or not), and it subtracts
from the window before the user has said anything. Left undeclared, it grows silently:
each new knowledge doc looks free at the moment it is written, because nothing reports
what it costs.

This makes that cost a NUMBER, emitted on the normal path (instrumentation-over-inference
IO2/IO4: a feature is not done until its behaviour is measurable by default), and gates it
so the set cannot re-grow past a declared ceiling (continuous-improvement CI6: a lesson
recorded as prose is a memoir).

Every knowledge doc declares its own load scope in frontmatter:

    load: always                # attached to every request  -> Tier A, counts against the budget
    load: glob                  # attached to matching files -> Tier B, costs nothing elsewhere
    applyTo: "**/*.cs,**/*.csx"
    load: skill                 # read on demand by a skill  -> Tier C
    skills: [specify, implement]
    load: reference             # consulted, never attached  -> Tier D

FOUNDATION.md is the vendored provenance manifest: always-loaded by definition, kept
verbatim, and carries no frontmatter of its own.

Subcommands
  report      Tier table + the always-on total.
  gate        Fail when the always-on total exceeds --ceiling. CI-able.
  agents      Per-agent declared knowledge prefix (the sub-agent lens, P3).
  preflight   Fail when an assembled prefix would not fit a model's window (P5).

Token figures are ESTIMATES (chars / 4.83) and are labelled as such everywhere. The ratio
is calibrated against a measured system prompt of 184,364 tokens over 890,204 characters of
this doc set. It is accurate enough to gate on and is never presented as a measurement:
where an exact count matters, count with the target model's tokenizer.

Python 3.8+, stdlib only.
"""
import argparse
import os
import re
import sys

# Windows consoles default to cp1252, which cannot encode the glyphs this tool prints.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

# Calibrated against the profiled session: 890,204 chars of knowledge docs reported as
# 184,364 system tokens => 4.83 chars/token. An estimate, not a measurement (see module doc).
CHARS_PER_TOKEN = 4.83

# The vendored provenance manifest is always-loaded and deliberately frontmatter-free.
MANIFEST = "FOUNDATION.md"

TIERS = {
    "always": "A", "glob": "B", "skill": "C", "reference": "D",
}
TIER_NOTE = {
    "always": "attached to every request",
    "glob": "attached to matching files only",
    "skill": "read on demand by a skill",
    "reference": "consulted, never attached",
}

HERE = os.path.dirname(os.path.abspath(__file__))


def est_tokens(chars):
    """Estimated tokens for a character count. Always reported as an estimate."""
    return int(round(chars / CHARS_PER_TOKEN))


def find_dir(*candidates):
    """Resolve a pack directory from either the pack layout or an installed repo."""
    start = HERE
    for _ in range(6):
        for rel in candidates:
            path = os.path.join(start, rel)
            if os.path.isdir(path):
                return path
        parent = os.path.dirname(start)
        if parent == start:
            break
        start = parent
    return None


def knowledge_dir(explicit=None):
    if explicit:
        return explicit
    return find_dir(os.path.join("pack", "knowledge"), os.path.join(".claude", "knowledge"),
                    "knowledge")


def agents_dirs(explicit=None):
    if explicit:
        return [explicit]
    found = []
    for rel in (os.path.join("pack", "adapters", "claude-code", "agents"),
                os.path.join("pack", "adapters", "copilot", "agents"),
                os.path.join(".claude", "agents")):
        path = find_dir(rel)
        if path:
            found.append(path)
    # Prefer the pack sources when both are present; they are the source of truth.
    pack_sources = [p for p in found if os.sep + "pack" + os.sep in p]
    return pack_sources or found


def read_frontmatter(path):
    """Return (meta_dict, body). meta values are raw strings; lists are parsed for [a, b]."""
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        raw = fh.read()
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", raw, re.S)
    if not match:
        return {}, raw
    meta = {}
    for line in match.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not kv:
            continue
        key, val = kv.group(1), kv.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            meta[key] = [v.strip() for v in val[1:-1].split(",") if v.strip()]
        else:
            meta[key] = val.strip('"').strip("'")
    return meta, raw[match.end():]


def scan(kdir):
    """Every knowledge doc with its declared scope and estimated size. Sorted, deterministic."""
    docs = []
    for name in sorted(os.listdir(kdir)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(kdir, name)
        meta, _ = read_frontmatter(path)
        chars = os.path.getsize(path)
        if name == MANIFEST:
            load = "always"
        else:
            load = meta.get("load", "")
        docs.append({
            "name": name[:-3], "path": path, "chars": chars,
            "tokens": est_tokens(chars), "load": load,
            "applyTo": meta.get("applyTo", ""), "skills": meta.get("skills", []),
        })
    return docs


def always_on(docs):
    return [d for d in docs if d["load"] == "always"]


# --------------------------------------------------------------------------- report

def cmd_report(args):
    kdir = knowledge_dir(args.knowledge_dir)
    if not kdir:
        print("context-budget: no knowledge directory found", file=sys.stderr)
        return 1
    docs = scan(kdir)
    undeclared = [d for d in docs if d["load"] not in TIERS]
    by_tier = {}
    for doc in docs:
        by_tier.setdefault(doc["load"], []).append(doc)

    print(f"knowledge dir: {kdir}")
    print(f"docs: {len(docs)}   (token figures are ESTIMATES at {CHARS_PER_TOKEN} chars/token)\n")
    for load in ("always", "glob", "skill", "reference"):
        group = sorted(by_tier.get(load, []), key=lambda d: -d["tokens"])
        if not group:
            continue
        total = sum(d["tokens"] for d in group)
        print(f"Tier {TIERS[load]} — load: {load:<9} {len(group):2d} docs  ~{total:>7,d} tok"
              f"   ({TIER_NOTE[load]})")
        if args.verbose:
            for doc in group:
                extra = doc["applyTo"] or (", ".join(doc["skills"]) if doc["skills"] else "")
                print(f"      ~{doc['tokens']:>6,d}  {doc['name']}"
                      + (f"   [{extra}]" if extra else ""))
        print()

    total_always = sum(d["tokens"] for d in always_on(docs))
    total_all = sum(d["tokens"] for d in docs)
    print(f"ALWAYS-ON (the static prefix): ~{total_always:,} est. tokens"
          f"  of ~{total_all:,} across the whole set")
    if total_all:
        print(f"                               {100.0 * total_always / total_all:.0f}% of the corpus is attached to every request")
    if undeclared:
        print(f"\nUNDECLARED load scope ({len(undeclared)}): " + ", ".join(d["name"] for d in undeclared))
        return 1
    return 0


# ----------------------------------------------------------------------------- gate

def cmd_gate(args):
    kdir = knowledge_dir(args.knowledge_dir)
    if not kdir:
        print("context-budget: no knowledge directory found", file=sys.stderr)
        return 1
    docs = scan(kdir)
    undeclared = [d for d in docs if d["load"] not in TIERS]
    total = sum(d["tokens"] for d in always_on(docs))
    print(f"always-on knowledge: ~{total:,} est. tokens across {len(always_on(docs))} docs"
          f"   (ceiling {args.ceiling:,})")

    failed = False
    if undeclared:
        print(f"FAIL: {len(undeclared)} doc(s) declare no `load:` scope — "
              + ", ".join(d["name"] for d in undeclared))
        print("      An undeclared doc is an unbudgeted doc. Add `load:` frontmatter.")
        failed = True
    if total > args.ceiling:
        over = total - args.ceiling
        print(f"FAIL: over the always-on ceiling by ~{over:,} tokens.")
        print("      Every always-on doc is re-read on EVERY call. Move a doc to")
        print("      `load: glob` / `load: skill` / `load: reference`, or raise the")
        print("      ceiling deliberately — but not silently.")
        for doc in sorted(always_on(docs), key=lambda d: -d["tokens"])[:5]:
            print(f"        ~{doc['tokens']:>6,d}  {doc['name']}")
        failed = True
    if failed:
        return 1
    print(f"clean - ~{args.ceiling - total:,} est. tokens of headroom")
    return 0


# --------------------------------------------------------------------------- agents

def cmd_agents(args):
    """Per-agent declared knowledge prefix (P3). An agent inherits its LENS, not the world."""
    kdir = knowledge_dir(args.knowledge_dir)
    adirs = agents_dirs(args.agents_dir)
    if not kdir or not adirs:
        print("context-budget: knowledge or agents directory not found", file=sys.stderr)
        return 1
    sizes = {d["name"]: d["tokens"] for d in scan(kdir)}
    base = sum(d["tokens"] for d in always_on(scan(kdir)))

    rows, undeclared, unknown_refs = [], [], []
    for adir in adirs:
        for name in sorted(os.listdir(adir)):
            if not name.endswith(".md"):
                continue
            meta, _ = read_frontmatter(os.path.join(adir, name))
            agent = meta.get("name") or name[:-3]
            if "knowledge" not in meta:
                undeclared.append(agent)
                continue
            docs = meta["knowledge"] if isinstance(meta["knowledge"], list) else []
            missing = [d for d in docs if d not in sizes]
            unknown_refs.extend(f"{agent} -> {d}" for d in missing)
            rows.append((agent, docs, sum(sizes.get(d, 0) for d in docs)))

    rows.sort(key=lambda r: -r[2])
    print(f"per-agent knowledge prefix (ESTIMATES; the main thread's always-on set is ~{base:,})\n")
    for agent, docs, total in rows:
        print(f"  ~{total:>6,d} tok  {agent:<32} {len(docs)} doc(s)")
        if args.verbose:
            for doc in docs:
                print(f"                    - {doc}  (~{sizes.get(doc, 0):,})")
    if rows:
        worst = max(r[2] for r in rows)
        print(f"\n  widest lens: ~{worst:,} est. tokens"
              f"   ({100.0 * worst / base:.0f}% of the main thread's always-on set)" if base else "")
    failed = False
    if unknown_refs:
        print("\nFAIL: agent references a knowledge doc that does not exist:")
        for ref in unknown_refs:
            print(f"        {ref}")
        failed = True
    if undeclared:
        print(f"\nFAIL: {len(undeclared)} agent(s) declare no `knowledge:` lens — "
              + ", ".join(sorted(undeclared)))
        print("      An agent with no declared lens inherits the whole set, which is")
        print("      what put a main-thread-sized prefix on every delegated run.")
        failed = True
    return 1 if failed else 0


# ------------------------------------------------------------------------ preflight

def cmd_preflight(args):
    """Fail BEFORE a fan-out when the assembled prefix cannot fit the target window (P5).

    One failure at the context ceiling predicts every sibling in the wave: the prefix is
    the same for all of them. Probing it once costs a subsecond; discovering it per-run
    cost 27 of 39 delegated runs in the profiled session.
    """
    kdir = knowledge_dir(args.knowledge_dir)
    if not kdir:
        print("context-budget: no knowledge directory found", file=sys.stderr)
        return 1
    docs = scan(kdir)
    sizes = {d["name"]: d["tokens"] for d in docs}

    if args.agent:
        adirs = agents_dirs(args.agents_dir)
        lens, found = None, False
        for adir in adirs or []:
            for name in sorted(os.listdir(adir)):
                if not name.endswith(".md"):
                    continue
                meta, _ = read_frontmatter(os.path.join(adir, name))
                if (meta.get("name") or name[:-3]) == args.agent:
                    lens, found = meta.get("knowledge", []), True
                    break
            if found:
                break
        if not found:
            print(f"preflight: agent '{args.agent}' not found", file=sys.stderr)
            return 1
        if not isinstance(lens, list):
            lens = []
        knowledge = sum(sizes.get(d, 0) for d in lens)
        scope = f"agent '{args.agent}' ({len(lens)} doc lens)"
    else:
        knowledge = sum(d["tokens"] for d in always_on(docs))
        scope = "main thread (always-on set)"

    prefix = knowledge + args.tools + args.overhead
    headroom = args.window - prefix
    print(f"preflight: {scope}")
    print(f"  knowledge   ~{knowledge:>8,d} est. tokens")
    print(f"  tools        {args.tools:>8,d}")
    print(f"  overhead     {args.overhead:>8,d}")
    print(f"  prefix      ~{prefix:>8,d}  of a {args.window:,} window"
          f"  ({100.0 * prefix / args.window:.0f}%)")
    print(f"  headroom    ~{headroom:>8,d}")

    if headroom < args.min_headroom:
        print(f"\nFAIL: less than the required {args.min_headroom:,} tokens of working headroom.")
        print("      Do NOT dispatch this wave — every run in it carries the same prefix,")
        print("      so one failure here is all of them. Narrow the lens (`knowledge:` in")
        print("      the agent), pick a model with a larger window, or scope a doc out of")
        print("      the always-on tier.")
        return 1
    print("\nclean - the wave fits")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="context-budget.py",
        description="Measure, gate and preflight the always-on context budget.")
    parser.add_argument("--knowledge-dir", help="override knowledge doc discovery")
    parser.add_argument("--agents-dir", help="override agent definition discovery")
    sub = parser.add_subparsers(dest="cmd")

    p_rep = sub.add_parser("report", help="tier table + always-on total")
    p_rep.add_argument("-v", "--verbose", action="store_true", help="list every doc")
    p_rep.set_defaults(func=cmd_report)

    p_gate = sub.add_parser("gate", help="fail over the always-on ceiling (CI-able)")
    p_gate.add_argument("--ceiling", type=int, default=45000,
                        help="max estimated always-on tokens (default 45000)")
    p_gate.set_defaults(func=cmd_gate)

    p_ag = sub.add_parser("agents", help="per-agent declared knowledge prefix")
    p_ag.add_argument("-v", "--verbose", action="store_true", help="list each agent's docs")
    p_ag.set_defaults(func=cmd_agents)

    p_pre = sub.add_parser("preflight", help="fail before a fan-out that cannot fit")
    p_pre.add_argument("--window", type=int, required=True, help="target model context window")
    p_pre.add_argument("--agent", help="preflight one agent's lens instead of the main thread")
    p_pre.add_argument("--tools", type=int, default=24070,
                       help="tool-definition tokens (default 24070, the profiled figure)")
    p_pre.add_argument("--overhead", type=int, default=0, help="any further fixed prefix")
    p_pre.add_argument("--min-headroom", type=int, default=32000,
                       help="working headroom the task itself needs (default 32000)")
    p_pre.set_defaults(func=cmd_preflight)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
