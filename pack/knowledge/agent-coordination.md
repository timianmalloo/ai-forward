---
load: skill
skills: [compile, optimize-graph, prepare-for-coordination, execute-with-coordination]
---
# Agent coordination — Owner / Coordinator / Sub-Agent (seeded: CO-S0, CO-L)

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

## CO-L — Leadership (designation, never election)

**What it is.** In S3 one Coordinator is the **leader**: the session that holds the running track and runs the join. Leadership is **designated by the human** (`coord leader pin <session>`), never elected (D3: FLP, two-node arithmetic, a human present). It lives in **one compare-and-swap cell** — the git ref `refs/coord/leader`, written only by `git update-ref <ref> <new> <old>` — and is **recorded** in the ledger (`type: leader` rows, one per attempted transition, refusals included). **The ref decides; the ledger records; the join fences.** A union-merged ledger cannot refuse a competing claim (SPK-3, `note-20260919-leadership-in-a-ref-not-the-ledger`), so nothing reads leadership back from the ledger to decide anything.

**The verbs.** `coord leader pin <session>` — refused with `COORD-LEADER-HELD` while a live designation exists, and with `COORD-LEADER-EXPIRED` over a lapsed one (use `reclaim`) · `who [--json]` — exit 0 live · 3 absent / expired / released · 4 NOT CHECKED · `renew` — holder only; the epoch never moves · `release` — holder only; the holder is cleared and **the epoch survives** · `reclaim <session>` — after an expiry **and** the quiet period; epoch + 1; a contested reclaim is recorded and pages the human. Every change of holder advances the **epoch** by exactly one; a renew never does (`spec-leader-designation`).

**The constants** are one block in `coord-core.py` — `LEADER_TTL`, `LEADER_RENEW` (TTL/3), `LEADER_RETRY`, `LEADER_QUIET` (D13, ratified 2026-09-19) — cited here by name and never restated as numbers; they are tuned from `coord metrics` (`leader_loss`, `reclaims`, `reclaim_latency_median_seconds`, `contested_pins`), never by hand in prose. The leader **MUST** renew every `LEADER_RENEW` seconds; a lost compare-and-swap is a refusal (`COORD-LEADER-STALE`) to re-read and retry after `LEADER_RETRY`.

**The join fence.** A Coordinator **MUST** run `coord leader who` before every join and pass the epoch its plan carries as `conductor-join.py --epoch <n>`. The join's step 0 refuses — exit 11, before the merge, never a silent fallback — a plan whose epoch is lower than the ref's (`COORD-JOIN-EPOCH-STALE`) or a ref it cannot read (`COORD-JOIN-LEADER-NOT-CHECKED`); an absent ref is *not applicable* (S2 has no leader). `coord doctor` prints the leader state, and a ref that cannot be read is **NOT CHECKED**, never "no leader" (R4).

**What reopens it.** Election — only if leader-loss stalls exceed 1/week after P2, measured by `coord metrics`. A quiet period on a voluntary release — if a released leader's in-flight join is ever observed after its release (`note-20260919-leader-release-keeps-the-epoch`). Pushing the ref across machines (`--force-with-lease=<ref>:<expect>`, **never** together with `--force` — SPK-2) — when S3 spans machines.
