# Model-Orchestration Standard

*Normative guidance for routing the pack's **own** work across models: which model (and how much reasoning effort) runs each activity a skill performs. It is the reflexive application of the **Layered-Optimized Architecture** (`layered-optimized-architecture.md`) to the pack itself — the Cheapest-Sufficient-Tier principle (P1), the Capability Router (Pattern 1.1), and the Capability Escalator (6.1), turned inward on skill execution. The **Orchestrator** persona is the runtime router; the **AI Systems Engineer** owns this standard and holds the veto; the audit log records every model choice. It composes with — and never replaces — the Rules-of-the-Road effort tiers (T0/T1/T2), the LOA capability tiers (T0–T4, for the product being built), and the Rigor Protocol stages.*

Normative keywords (**MUST**, **SHOULD**, **MAY**, **MUST NOT**) follow RFC 2119.

The governing idea: **the pack teaches LOA tier-allocation for the systems it builds; it must practise it on itself.** A skill is not one homogeneous call to one model — it is a sequence of *activities* with wildly different capability needs: a deterministic file copy, a broad architectural synthesis, a research spike, an adversarial hard-veto review, a red-green codegen loop. Routing each activity to the **cheapest model that is still sufficient** — and reserving the **best model for the work that carries the most rigor** — is what makes the pack fast and affordable without dulling the reasoning where it matters. Determinism lives in scripts (P2); rigor lives at the frontier; the human keeps the override.

---

## 0. Where this fits (four axes, not a new tier system)

This standard adds **one** axis to constructs the pack already has; it does not invent a fourth tier vocabulary.

| Axis | What it dials | Owner |
|---|---|---|
| Rules-of-the-Road effort tiers **T0/T1/T2** | *ceremony* by cost-of-error (T0 skips the swarm entirely) | `agent-rules-of-the-road` |
| LOA capability tiers **T0–T4** | model tier **for the product** being built | `layered-optimized-architecture` |
| Rigor Protocol **stages 0–5** | the *reasoning phase* of the work | `rigor-protocol` |
| **Execution-model tier (this doc)** | *which model + effort runs this activity* | Orchestrator (router) · AI Systems Engineer (veto) |

The effort tier is the spend gate: a **T0** task never convenes the frontier swarm; a **T2** task does. Execution-model routing refines choices *within* that envelope.

---

## 1. The activity archetypes (the routing key)

Every skill's work decomposes into a small set of **activity archetypes**. Routing keys on the archetype, exactly as the Testing Strategy keys on code shape. The Orchestrator classifies each stage/persona into one of these and dispatches accordingly.

| # | Activity archetype | Capability actually needed | Execution tier |
|---|---|---|---|
| **A** | Deterministic mechanics — file ops, deployment map, index derive/sync, audit/prompt append, git, scaffolding, count reconciliation | **none — this is a script** (LOA P2) | **Deterministic (no model)** |
| **B** | Grounding & graph traversal — load upstream artifacts, read the graph, read prior audit/decisions | light | Fast/cheap |
| **C** | Research & spikes — comparables, contract due-diligence, Stage-3 evidence, Spike Protocol | capable + tools/web, **parallelizable** | Research (mid–high) + subagents |
| **D** | Broad reasoning & framing — Stage 1–2, architecture/design synthesis, root-cause hypotheses | **frontier reasoning, high effort** | Frontier |
| **E** | Adversarial review — Stage-4 swarm, hard-veto lenses | frontier, high effort, **model ≠ author** | Frontier (**distinct**) |
| **F** | Implementation / TDD codegen | strong **coding** model; proof is deterministic tests | Coding |
| **G** | Creative UX/UI generation | capable, visual/UX-aware | Frontier / multimodal |
| **H** | Documentation & prose/diagram extraction | mid | Mid |
| **I** | Verification / eval | **deterministic** (run tests) + LLM-as-judge for probabilistic content (**distinct** judge) | Mixed (script + distinct model) |

**M1 — Classify before dispatch.** For any skill run above T0, the Orchestrator **MUST** map each stage/persona to its archetype(s) and route by the table above. An activity with no archetype is a gap to resolve, not a default-to-frontier.

**M2 — Cheapest sufficient tier.** Each activity **MUST** be dispatched to the **lowest-capability tier that still meets its correctness/quality bar** (LOA P1). Over-provisioning a frontier model onto archetype-A/B work is a defect (cost *and*, for A, a determinism risk).

---

## 2. Per-skill routing profiles (dominant archetypes)

The pack's 17 skills, keyed to §1. The reasoning-loop skills share a **frontier-reasoning + parallel-research + distinct-adversary** spine; the utility/lifecycle skills are **largely deterministic** (route to scripts, not a frontier model).

| Skill | Dominant activities | Routing profile |
|---|---|---|
| `collectknowledge` | C, D, A | research + frontier synthesis + cheap write |
| `adddomainexperts` | D, A | mid + cheap write |
| `specify` | D, C, E | frontier + research + **distinct** adversary |
| `define-architecture` | D, **C (spikes)**, E | frontier + parallel research + distinct architect council |
| `design` | D, C, **G**, E | frontier + research + creative + adversary |
| `implement` | **F**, I, E | coding + deterministic verify + distinct pre-merge review |
| `investigate` | D (hard), C, E | **frontier-max** + verify-by-data + adversary |
| `document` | H, A | mid + deterministic index |
| `adopt` | B/A, D, C | mostly mechanical + mid recovery + research (glossary mining) |
| `forensicreview` | H+D, E, A | frontier + mid + deterministic backlog |
| `migrate` | A (characterization), F, D, E | deterministic harness + coding + frontier blast-radius + adversary |
| `updatepack` · `addpacktorepo` | **A** (+B recon) | **deterministic — no model** |
| `extendaibundle` | C→D→F + A | research → frontier → coding → deterministic verify |
| `auditlog` · `prompts` · `searchprompts` | **A** | **deterministic — no model** |

---

## 3. The routing policy (the five settled rules)

These directives encode the resolved policy (decision note `note-20260712-model-orchestration-policy`).

**M3 — Auto-dispatch by default; the human always overrules (advisory default).** The Orchestrator **auto-dispatches** each stage/persona to its recommended tier by default, and **MUST** state the routing it chose (so it is visible). The human **MAY overrule** any routing decision at any time — a stated tier is a strong default, never a cage. An explicit user instruction (a chosen model, "use the cheap model here", "no subagents") **MUST** win over the table.

**M4 — Optimize for efficiency by default; a `cost` knob trades down borderline work only.** The routing **profile** is user-selectable: `efficiency` (quality over cost) or `cost`. The **default is `efficiency`** — the activities that carry the **most rigor MUST get the best available model**: adversarial hard-veto review (E), architecture (`define-architecture`), and root-cause investigation (`investigate`). `cost` mode **MAY** trade down to a cheaper tier **only on borderline T1 work** (B, H, and non-veto D), and **MUST NOT** clip the model on a hard-veto gate, a T2 task, or an irreversible/high-cost-of-error surface.

**M5 — Adversary independence is a hard rule.** On any **hard-veto gate** (Stage 4; the Security, Test Architect, Distributed Systems, AI Systems, Data & Persistence, Privacy lenses; the author's own review), the **reviewer model MUST differ from the author model** — structural separation (BoK §II.3), the model-routing form of self-consistency. If honoring independence is **truly blocking** (e.g. only one model is available in the environment), the Orchestrator **MUST surface it for human review** rather than silently self-review; the human **MAY overrule** and accept single-model review as a recorded deviation. A hard-veto gate cleared by the *same* model that authored the work is not cleared (Rules of the Road §3.2).

**M6 — Deterministic work is a script; the skill surface always remains.** Archetype-A activities **MUST** run as **deterministic scripts, not model calls** (LOA P2). Where such work is still inline in a skill, it **SHOULD** be extracted into a cross-platform script (Python 3.8+ stdlib or `pwsh`). **But the skill always exists** — a skill **MAY** be a thin surface whose whole job is to invoke a script — so the experience stays **skills-centric**. The pack's archetype-A mechanics are already script-backed (`audit-log.py`, `prompt-log.py`, `docs-graph.py`, `new-capability.py`, `sync-pack.ps1`, `verify-bundle.ps1`, `check-consistency.py`); `model-router.py` (this standard's tool) is the routing lookup. The rule: **if a step is deterministic and repeatable, it belongs in a script bound to a skill — never in a model call.**

**M7 — Target the GitHub Copilot CLI on Windows and macOS.** This standard optimizes for the **GitHub Copilot CLI** as the runtime: its per-subagent **`model` + `reasoning_effort`** selection and its **background parallel agents** are the dispatch mechanism the Orchestrator uses (fan out archetype-C research and archetype-E adversary lenses as parallel background agents, each pinned to its tier). Scripts **MUST** be **cross-platform** (run on Windows PowerShell/`pwsh` and macOS). Model choices are expressed as **capability tiers** (§4), mapped to the environment's current roster, so the standard survives model churn (Provider Portability, LOA 6.6) and works identically on both OSes.

---

## 4. Capability tiers → concrete models (map per environment)

Routing is expressed in **capability tiers**, not hard model IDs — named models age (the same currency discipline LOA applies to its examples). Resolve tiers to the Copilot CLI's **current** roster via `model-router.py`; the mapping below is *illustrative*, to be re-pinned as the roster changes.

| Tier | Use for (archetypes) | How to pick (Copilot CLI) |
|---|---|---|
| **Deterministic** | A | a **script** — no model |
| **Fast/cheap** | B, H, drafts | a mini/flash-class model, low effort |
| **Coding** | F (implement/migrate) | a coding-optimized model, medium–high effort |
| **Frontier reasoning** | D, E, G, I-judge | the strongest reasoning model, **high/xhigh/max** effort |
| **Research (+parallel)** | C (spikes, collectknowledge) | a capable model with tools, fanned out as background agents |

**M8 — Express routing as tiers; pin models at the edge.** Skills and personas **MUST** name a **tier** (and, for A, "script"), not a hard model ID; the concrete model+effort is resolved at dispatch from the environment roster. This keeps the pack portable across model updates and across Windows/macOS.

---

## 5. Governance, escalation, and audit

**M9 — Escalate on low confidence or a triggered hard-veto surface.** A cheap-tier pass that returns **low confidence** (a Flagged claim, an unresolved unknown), or any activity that **touches a hard-veto surface** (security, data migration, money, irreversible action, an AI capability with no eval), **MUST escalate** to the frontier tier rather than ship the cheap result (LOA Capability Escalator 6.1). Escalation is cheaper than a wrong answer on a load-bearing path.

**M10 — Determinism guard (AI Systems Engineer hard veto).** Non-deterministic model output **MUST NOT** flow into a path that requires determinism (an index derive, a count, a deployment map, a git operation) without a deterministic check. The AI Systems Engineer holds the hard veto here, exactly as for a product AI surface.

**M11 — Audit the model choice.** Every skill run **SHOULD** record, in its audit-log entry, the **routing profile** (`efficiency`|`cost`) and the **tier/model + effort** used for its load-bearing stages (E and D at minimum), so inference cost and the efficiency/cost trade become visible and tunable over time (ties to `ai-commercial-models.md`; LOA Token Budget Throttle 2.4). A recorded routing choice is the evidence that M2–M5 were honored.

**M12 — Ownership.** The **AI Systems Engineer** owns this standard, the tier→model mapping, and the routing table; the **Orchestrator** is the runtime Capability Router that applies it (auto-dispatch, escalation ladder, parallel fan-out, mode-switch); the **human** holds the override (M3) and the deviation sign-off (M5). Persona agent files **MAY** carry an optional `model`/`effort` hint (the default tier for that lens); the Orchestrator's dispatch and any explicit user instruction override it.

---

## 6. Self-verification checklist (model routing)

- [ ] Each stage/persona above T0 was **classified** into an activity archetype and routed by §1 (M1).
- [ ] Each activity ran at the **cheapest sufficient tier**; no frontier model on archetype-A/B work (M2).
- [ ] The Orchestrator **auto-dispatched** and **stated** its routing; an explicit user instruction overrode it (M3).
- [ ] Profile honored: `efficiency` by default; **best model on the highest-rigor work** (E, architecture, investigation); `cost` traded down only borderline T1 work, never a hard-veto/T2 surface (M4).
- [ ] Every **hard-veto gate** was cleared by a **model distinct from the author**; a blocking single-model case was surfaced for human review, not self-cleared (M5).
- [ ] Deterministic mechanics ran as **cross-platform scripts bound to a skill**, not model calls; the skill surface remained (M6).
- [ ] Routing expressed as **tiers**, resolved to the Copilot-CLI roster; parallel research/adversary lenses fanned out as background agents; scripts run on Windows and macOS (M7–M8).
- [ ] Low-confidence or hard-veto-surface activities **escalated** to frontier (M9); no non-determinism leaked into a deterministic path (M10).
- [ ] The run **recorded its routing profile and tier/model** for load-bearing stages in the audit log (M11).

---

## 7. References

- **`layered-optimized-architecture.md`** — P1 (Cheapest Sufficient Tier), P2 (Determinism at the Floor), Pattern 1.1 (Capability Router), 6.1 (Capability Escalator), 6.6 (Provider Portability), 2.4 (Token Budget Throttle), Composition B/H (the loop this dogfoods) — *the authority this standard reflexively applies to the pack.*
- **`agent-rules-of-the-road.md`** §0.2 (effort tiers T0/T1/T2), §3.2 (gate records — a same-model self-clear is not a clear).
- **`rigor-protocol.md`** §5 (skill → technique → adversaries → artifact), §3 Stage 4 (disconfirm / adversarial).
- **`persona-audit.md`** §8 (persona operating standard; the AI Systems Engineer's veto and convene triggers) and `collaborative-personas.md` §5 (the per-skill casting sheet routing keys on).
- **`ai-commercial-models.md`** — inference cost as a first-class concern the audit ties into.
- **Decision note** `docs/notes/note-20260712-model-orchestration-policy.md` — the five resolved policy questions (dispatch, cost/efficiency, adversary independence, deterministic-to-script, Copilot-CLI/OS target).
- **`scripts/model-router.py`** — the deterministic routing lookup (archetype/skill/stage + profile → tier + illustrative model), cross-platform (Python 3.8+ stdlib).
