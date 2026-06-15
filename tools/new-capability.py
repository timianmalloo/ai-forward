#!/usr/bin/env python3
"""new-capability.py — scaffold a new AI-Forward pack capability with zero drift.

Extending the pack is repetitive and easy to get wrong (the recurring mistakes: a skill
that exists for Claude Code but not Copilot, no eval case, stale counts). This script does
the mechanical, drift-prone parts so a human or an agent (the /extendaibundle skill) never
has to remember them: it creates the correctly-placed skeleton files for BOTH tools and
re-derives the headline counts from the filesystem. Stdlib only; lives in tools/ (source).

Usage
  new-capability.py --kind skill     --name <name> --summary "<one-line description>"
  new-capability.py --kind knowledge --name <name> --summary "<one-line description>"
  new-capability.py ... --dry-run        # print the plan, write nothing
  new-capability.py ... --force          # overwrite existing skeleton files

After scaffolding it prints the exact remaining (judgement) steps. Run tools/verify-bundle.ps1
when done. Exit 0 on success, 1 on error.
"""
import argparse, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "pack")
NAME_RX = re.compile(r"^[a-z][a-z0-9-]+$")


def count_skills():
    cmd = os.path.join(PACK, "commands")
    return sum(1 for d in os.listdir(cmd) if os.path.isfile(os.path.join(cmd, d, "SKILL.md")))


def count_knowledge_docs():
    k = os.path.join(PACK, "knowledge")
    return sum(1 for f in os.listdir(k) if f.endswith(".md") and f != "FOUNDATION.md")


def write(path, text, dry, force):
    if os.path.exists(path) and not force:
        print(f"  EXISTS (skipped, use --force): {os.path.relpath(path, ROOT)}")
        return False
    if dry:
        print(f"  would write: {os.path.relpath(path, ROOT)}")
        return True
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8", newline="\n").write(text)
    print(f"  wrote: {os.path.relpath(path, ROOT)}")
    return True


def set_count(path, pattern, value, dry):
    """Replace the first capture-group number in `pattern` with value (regex with one group around the int)."""
    text = open(path, encoding="utf-8").read()
    m = re.search(pattern, text)
    if not m:
        print(f"  WARN: count pattern not found in {os.path.relpath(path, ROOT)}: {pattern}")
        return
    old = m.group(1)
    if old == str(value):
        return
    new = text[:m.start(1)] + str(value) + text[m.end(1):]
    if dry:
        print(f"  would set count {old} -> {value} in {os.path.relpath(path, ROOT)}")
        return
    open(path, "w", encoding="utf-8", newline="\n").write(new)
    print(f"  count {old} -> {value} in {os.path.relpath(path, ROOT)}")


SKILL_TEMPLATE = """---
name: {name}
description: {summary}
---

# Skill: /{name}

{summary}

**Spine:** runs the Rigor Protocol (`knowledge/rigor-protocol.md`). **Authority:** <name the governing standard(s)>. **Mode:** Peer Mode to author, Adversary Mode at the gate (`knowledge/collaborative-personas.md`).

## Grounding (first action)
Load what already exists and treat it as the authoritative source of truth (Rigor Protocol Stage 0). <What artifacts must be read first.> Skip this only if the user explicitly says so.

## Input
<What the user provides — a prompt, a path, a description.>

## Cast
- **Peers (author together):** Orchestrator, <lead persona>, <supporting personas>.
- **Adversaries (attack at the gate):** <reviewers, each with severity and any hard veto>.

## Flow (Rigor Protocol, specialized)
**Stage 0 — Interdict the rush.** <The premature move to prevent.>
**Stage 1 — OPEN.** <Frame the problem.>
**Stage 2 — INTERROGATE.** <Precise questions; surface assumptions.>
**Stage 3 — EVIDENCE.** <Establish, don't assert; spike the unfamiliar.>
**Stage 4 — DISCONFIRM (the gate).** Adversary Mode. <Who attacks what; authors do not self-clear.>
**Stage 5 — CONVERGE.** <Produce the artifact.>

## Output artifact
<Path and shape of what this skill produces.>

## Definition of done (exit gate)
- [ ] <Falsifiable completion criteria.>
- [ ] Adversarial gate passed; vetoes resolved or recorded; authors did not self-clear.

## Documentation & discoverability (last action)
Per the Discoverability Mandate (V10): write the artifact's frontmatter and sync the derived index via `python3 docs/ai-forward-pack/scripts/docs-graph.py derive` — never ad-hoc scripts (V18). Verify the artifact is linked into the graph. Work that is not discoverable in the Explorer is not done.

**Handoff:** <the next skill, if any>.
"""

PROMPT_TEMPLATE = """---
mode: agent
description: {summary}
---
You are running the **{name}** workflow (`knowledge/rigor-protocol.md`). <Name the lead peer(s) and the adversary reviewers with their hard vetoes.> Ground in the prior artifacts and treat them as authoritative. Interdict the rush: <the premature move to prevent>. OPEN: <frame>. INTERROGATE: <precise questions>. EVIDENCE: <establish with sources / spikes>. DISCONFIRM: each reviewer gives a labeled critique with a severity and, for hard-veto roles, PASS/BLOCK + the veto-clears-when predicate. CONVERGE: <produce the artifact>. End with the status table (Completed | Remaining | Best next action).

**Last action — discoverability (V10):** write the artifact's frontmatter and sync the derived index via `python3 docs/ai-forward-pack/scripts/docs-graph.py derive` — no ad-hoc scripts (V18); verify it is linked into the graph.

**Running this in Copilot (single agent — make the dialog visible).** Copilot does not auto-spawn the personas as separate subagents the way Claude Code does, so enact the round-table *inline*: for each peer write a short labeled contribution in that persona's voice; then run the adversary round, each reviewer giving a labeled critique with a severity **[Blocker|Major|Minor|Nit]** and, for hard-veto roles, an explicit **PASS/BLOCK** plus the veto-clears-when predicate (`persona-cards.md` §8). Do not collapse this into one unattributed answer.

${{input}}
"""

EVAL_TEMPLATE = """{{
  "skill": "{name}",
  "prompt": "Run /{name} on <a representative golden task>.",
  "setup": [],
  "assertions": [
    {{ "type": "file-exists", "path": "<an artifact the skill must produce>" }}
  ],
  "id": "{name}-01"
}}
"""

KNOWLEDGE_TEMPLATE = """# {title}

<One-paragraph statement of what this knowledge doc governs and why it exists.>

## <Section>
<Content. Number normative rules if this is a standard (e.g., X1, X2, ...).>
"""


def scaffold_skill(name, summary, dry, force):
    print(f"Scaffolding skill /{name}")
    write(os.path.join(PACK, "commands", name, "SKILL.md"),
          SKILL_TEMPLATE.format(name=name, summary=summary), dry, force)
    write(os.path.join(PACK, "adapters", "copilot", "prompts", f"{name}.prompt.md"),
          PROMPT_TEMPLATE.format(name=name, summary=summary), dry, force)
    write(os.path.join(PACK, "evals", "cases", f"{name}-01.json"),
          EVAL_TEMPLATE.format(name=name), dry, force)
    n = count_skills() + (1 if dry else 0)
    set_count(os.path.join(PACK, "adapters", "INSTALL.md"), r"\bskills:\s*(\d+)", n, dry)
    set_count(os.path.join(PACK, "adapters", "managed-blocks", "CLAUDE.block.md"), r"Skills\s*\((\d+)\)", n, dry)
    set_count(os.path.join(PACK, "adapters", "managed-blocks", "AGENTS.block.md"), r"Workflows\s*\((\d+)\)", n, dry)
    print(f"\nSkill count is now {n}. Remaining steps (judgement - the skill flow owns these):")
    print(f"  1. Write the real SKILL.md body and the Copilot prompt (replace the <placeholders>).")
    print(f"  2. Add /{name} to the skill lists in CLAUDE.block.md and AGENTS.block.md (enforced by check-consistency).")
    print(f"  3. Curate evals/cases/{name}-01.json with real assertions.")
    print(f"  4. Update prose counts/lists: README.md, pack/README.md, pack/OVERVIEW.md (incl. the skill table),")
    print(f"     web/ai-forward-pack-explainer.html (SKILLS array + count strings), .github/copilot-instructions.md.")
    print(f"  5. Bump revision + add a `changes` entry in pack/adapters/INSTALL.md (archive the previous delta).")
    print(f"  6. Run: pwsh tools/verify-bundle.ps1   (sync + all consistency checks = the proof).")


def scaffold_knowledge(name, summary, dry, force):
    print(f"Scaffolding knowledge doc {name}.md")
    title = summary if summary else name.replace("-", " ").title()
    write(os.path.join(PACK, "knowledge", f"{name}.md"),
          KNOWLEDGE_TEMPLATE.format(title=title), dry, force)
    n = count_knowledge_docs() + (1 if dry else 0)
    set_count(os.path.join(PACK, "adapters", "INSTALL.md"), r"\bknowledge_docs:\s*(\d+)", n, dry)
    print(f"\nKnowledge-doc count is now {n}. Remaining steps:")
    print(f"  1. Write the doc body. The sync wraps it as a Copilot instruction and copies it to .claude/knowledge/.")
    print(f"     (FOUNDATION-manifest excepted; csharp-style-guide uses a .cs applyTo scope.)")
    print(f"  2. Update any prose 'N docs' counts (pack/OVERVIEW.md) — check-consistency lists exact lines.")
    print(f"  3. Bump revision + add a `changes` entry in pack/adapters/INSTALL.md.")
    print(f"  4. Run: pwsh tools/verify-bundle.ps1.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=["skill", "knowledge"])
    ap.add_argument("--name", required=True)
    ap.add_argument("--summary", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if not NAME_RX.match(args.name):
        sys.exit(f"invalid name '{args.name}' — use lowercase letters, digits, hyphens (e.g. my-capability)")
    if args.kind == "skill":
        scaffold_skill(args.name, args.summary or f"<one-line description of /{args.name}>", args.dry_run, args.force)
    else:
        scaffold_knowledge(args.name, args.summary, args.dry_run, args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
