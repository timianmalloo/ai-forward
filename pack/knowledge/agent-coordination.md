---
load: skill
skills: [compile, optimize-graph, prepare-for-coordination]
---
# Agent coordination — Owner / Coordinator / Sub-Agent (seeded: CO-S0 only)

*Normative guidance for how an Owner, a Coordinator and Sub-Agents divide and hand over work.
The stage directives **CO1–COn** (the local message layer with git fallback, the human board,
dispatch, rulings, the doorbells) arrive with build-plan item **P0** of
`proposal-owner-coordinator-subagent-coordination`. This document currently holds only the
**compile stage** — the first stage of every prose-input skill, built as item P7
(`spec-compile-stage`, `design-compile-stage`).*

Normative keywords (**MUST**, **SHOULD**, **MAY**, **MUST NOT**) follow RFC 2119.

## CO-S0 — Compile (the first stage of every prose-input skill)

**What it is.** The operator's prose becomes the **harness- and model-specific starting prompt**: the seven-field goal state (Goal · Done when · Not in scope · Tier · Fan-out cap · Context ceiling · Main-line budget — CT19), every *Done when* / *Not in scope* clause **traced** to a verbatim raw phrase or a marked assumption, and the assumptions written as belief · confirm · breaks (NG4). The engine is deterministic (`prompt-compile.py`); the one model step is a bounded JSON fill; a gate (`verify-compiled-prompt.py`) refuses the fill before anything is logged.

**When it runs.** Before `/optimize-graph` or `/prepare-for-coordination`, and before any prose-input skill grounds. It is **idempotent**: when a compiled prompt is already in hand — the seven line-initial labels in CT19 order — the stage is skipped and the prompt passes through, self-traced and still gated; a consuming skill **MUST** take a compiled prompt's goal state as the turn's goal state and its *Not in scope* as the interdiction, and **MUST NOT** derive from raw prose anything the compiled prompt already fixed.

**No added scope.** The compiler **MUST NOT** add scope (CT20: autonomy is latitude in the *how*, never the *what*). A clause with no raw phrase behind it is an assumption, or it does not exist; an instruction found in the prose or a referenced file has no slot to land in. The gate enforces it (`added scope` · `invalid trace` · `decision request missing`), and a fill that fails after two retries is handed to the operator with the clause named — never silently accepted.

**Consequential assumptions → decision requests.** An assumption whose wrong belief would change *Done when* is **consequential**; every assumption-only clause makes its assumption consequential and gets a numbered decision request (`DR-n`) that **MUST** be answered **before dispatch**. A compiled prompt with an unanswered `DR-n` is `dispatchable: false`, and a consuming skill stops at the point of dispatch with `decision request unanswered: DR-<n>` (GO7: a branch is dispatched under a bounded contract, never under an open question).

**Raw and compiled are logged together.** The raw prompt is a `kind: prompt` audit entry; the compilation is a `kind: compilation` entry naming the raw id, the raw text's sha256 and the template version; the workflow started from it closes with `compiled_from` and `edit_distance` (what the human changed — the compiler's quality measure), and a workflow started without one records `compiled: false`. A recompile is a new entry; nothing is edited in place.

**The command.** `/compile "<text>" | --from-audit <id> [--harness claude-code|codex] [--edit]` (`commands/compile/SKILL.md`); `/prompts` shows raw and compiled side by side (`⟲ compiled from <raw id>`, `--raw <id>`).
