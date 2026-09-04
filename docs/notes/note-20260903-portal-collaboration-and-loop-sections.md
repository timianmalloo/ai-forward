---
id: note-20260903-portal-collaboration-and-loop-sections
title: "Portal gains Multi-Agent Collaboration and The Prompt Loop; roster becomes derived"
type: decision-note
status: accepted
owner: "@timianmalloo"
tags: [portal, pages, personas, prompt-loop, inventory, derived-artifacts]
links:
  - { to: architecture, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-03-03"
summary: >-
  Four decisions taken while adding the two requested Pages sections: where they sit in the
  reading order, deriving the persona roster from the agent files rather than editorial, leaving
  the UI knowledge docs out of knowledgeGroups on purpose, and recording GIT-A after a revert
  destroyed uncommitted work.
---

# Portal: collaboration + prompt-loop sections

Four decisions below ADR weight, recorded because each will look arbitrary to the next reader.

## 1. The two sections sit after Skills, not at the end

Section order is the reading order: *what it is* (Getting Started, Capabilities), *what it does*
(Skills), **how those skills are actually run** (Multi-Agent Collaboration, The Prompt Loop), then
the reference layers (Foundations, UI, Architecture, Systems, Graph, Reference).

Putting them after Reference would have filed the operating model as an appendix. Someone
evaluating the pack needs to know that work is reviewed by a convened panel and that every turn
opens with a stop condition **before** they read the knowledge-doc index, not after.

Section numbers are now derived from list position (`enumerate`) rather than hand-written, so
inserting a section cannot leave a stale label behind it — which it would have, twice, here.

## 2. The persona roster is derived from the agent definitions, not from editorial

The published table reads each agent's own frontmatter `description` and infers veto strength
from it (`hard veto` / `soft veto` / otherwise advisory), plus its declared `knowledge:` lens.

The alternative — listing the roster in `docs-portal-editorial.json` — was rejected because a
public page claiming a veto the shipped agent does not hold is a specific, plausible, and
undetectable failure. The skills section already had this property ("complete by construction");
the persona section now shares it. `test_veto_strength_matches_the_agents_own_description` pins it.

## 3. The seven UI knowledge docs stay out of `knowledgeGroups` deliberately

`foundations()` skips anything listed in `uiStandards` **before** the group lookup, because those
docs render in the UI & Design section instead. A `knowledgeGroups` entry for one of them is
therefore unreachable configuration.

This was briefly "fixed" during this session — the seven were mapped into a new group and a new
group order was added — on the mistaken reading that they were unrouted. They were not: every
knowledge doc surfaces exactly once, and the check now proves it. The mapping was reverted and
`test_ui_docs_are_excluded_from_foundations_by_design` exists so it is not helpfully re-added.

## 4. GIT-A: a revert is not an undo

Demonstrating the new control meant mutating files and putting them back. `git checkout -- <path>`
was used to put them back, which restores **HEAD** — destroying this session's uncommitted work in
`docs-portal-editorial.json` and `docs/portal/index.html`.

Recovered only because the editorial content happened to still exist in a scratchpad file and the
renderers were still in the transcript. Neither is a recovery mechanism.

**The rule taken from it:** demonstrate a control against a *copy* the tool is pointed at, never
against the real tree. The `context-budget` controls already had the right shape — every one takes
an explicit `--knowledge-dir` / `--config` — and the portal demonstration was redone with file
snapshots. Recorded as defect class **GIT-A**, `partially-controlled`: it is a practice and a
register entry, because no CI check can observe a destructive undo inside a working tree.
