---
doc: INSTALL
purpose: 'Manual reconciliation guide and refresh changelog. On a repo refresh, read `changes` below — it is the key guide: it lists exactly what to re-copy and re-paste since the previous revision, so you do not have to diff the whole tree.'
bundle_version: '2026.08.05.3'
revision: 27
counts: { lenses: 23, skills: 18, knowledge_docs: 33, templates: 23, scripts: 12 }
refresh_protocol: 'Compare your repo last-applied revision to the `revision` above. If it is lower, apply each entry in `changes` in order — re-copy the listed `paths` to their mapped destinations (deployment map in the body), re-apply the Copilot frontmatter wraps, and where an entry `deploy` says RE-PASTE, replace the managed blocks wholesale between their markers. Never overwrite an accumulated docs/docs-index.js.'
changes:
  - { type: changed, area: skills, paths: ['commands/ui-design/SKILL.md', 'adapters/copilot/prompts/ui-design.prompt.md'], deploy: 'copy to .claude/skills/ui-design/SKILL.md and .github/prompts/ui-design.prompt.md', summary: 'ADDED THE TRIGGERED-STANDARDS TABLE. Raised by a user challenge: why are technical-ui-design.md and ui-visual-assets.md a pointer to a doc rather than distinct skills or flags? Neither, and the current wiring was the real defect. They are not separate skills (composable, not alternative - a CFD tool with a generated hero trips both; and 90% duplication of the flow/cast/DoD would drift). They are not modes (the existing create/review/elevate are mutually exclusive; these are orthogonal, which would give 12 modes). They are TRIGGERED DIRECTIVES in the Testing-Strategy sense - which both ui-interaction-design.md U1 and technical-ui-design.md section 0 already explicitly claim, and which /design and /implement already implement with a trigger table. /ui-design simply never did: technical-ui-design.md was reachable through exactly ONE reference, the second-to-last definition-of-done checkbox, for a 12-directive standard governing every expert surface. Now: an unconditional floor stated as a preamble, then four conditional rows (UI-T1 expert/quantitative, UI-T2 generated assets, UI-T3 fronts-a-model, UI-T4 native app) applied as a UNION with a gate consequence per row, and MAPPED AT STAGE 1 because the triggers reshape that stage - UI-T1 moves archetype selection into catalog section G, UI-T3 adds wrong-answer and uncertainty to the state inventory.' }
  - { type: changed, area: skills, paths: ['commands/design/SKILL.md', 'commands/implement/SKILL.md', 'commands/specify/SKILL.md', 'adapters/copilot/prompts/design.prompt.md', 'adapters/copilot/prompts/implement.prompt.md', 'adapters/copilot/prompts/specify.prompt.md'], deploy: 'copy skills to .claude/skills/<name>/SKILL.md and prompts to .github/prompts/<name>.prompt.md', summary: 'THE SWEEP (CI2 - fix the class, not the instance). Sweeping for the same shape found that /design, /implement and /specify referenced the UI standards and HAX but NEVER technical-ui-design.md - so a spec, design or build of a CAD tool, scientific visualiser, notebook, financial model or quant terminal had zero path to TQ1-TQ12. All three now carry the expert/quantitative trigger on both tool surfaces, with the correctness framing (a rainbow colormap, a unit-less quantity, or a point estimate for a stochastic result is a correctness defect, not taste).' }
  - { type: changed, area: templates, paths: ['templates/ui-capability-guide.template.html'], deploy: 'copy to docs/ai-forward-pack/templates/ and re-instantiate docs/ui-guide.html', summary: 'New section 3 Triggered standards explaining modes-are-exclusive vs triggers-are-composable and the union rule; the two Start here cards that read as manual doc-loading (/ui-design plus technical-ui-design.md) now read as trips UI-T1 / UI-T2; sections renumbered and the table of contents updated. Re-verified clean under ui-craft-gate.py --gate --a11y-obligation, well-formed, zero external URLs.' }
  - { type: changed, area: knowledge, paths: ['knowledge/continuous-improvement.md'], deploy: 'copy to .claude/knowledge/ and re-wrap into .github/instructions/', summary: 'Seed register gains PACK-A: a conditional standard wired as prose rather than as a trigger. It survives every existing check because the reference genuinely exists - link-checks and the consistency gate both pass - it is merely in the wrong place in the flow, and the cost stays invisible until someone makes the decision it should have shaped. Control: an explicit trigger table with union semantics, mapped at the stage the trigger reshapes.' }

---

## Changelog — what changed since the last version

**The frontmatter `changes` list above is the refresh guide.** When you pull a new bundle into an existing repo, you do **not** need to diff the whole tree: read `changes`, and apply exactly those re-copies and managed-block re-pastes. Each entry names the `paths` that moved and the precise `deploy` action (including the few that say **RE-PASTE** the managed blocks, which is the step most easily missed). Check your repo's last-applied `revision` against the `revision` in the frontmatter to know whether — and how far — you are behind.

**Convention (moving forward).** Every change to the bundle updates this file's frontmatter as part of the same change:
1. bump `revision` by 1 (monotonic — it never resets, so it is the reliable "is my repo behind?" anchor) and update `bundle_version` / `released` / `counts`;
2. replace `changes` with *this* version's delta only (so the frontmatter is always "since the previous revision");
3. move the **previous** `changes` into the **Prior revisions** log below as a dated, collapsed entry.

So at any moment: the frontmatter `changes` = the latest delta (the refresh guide), and this section = the full rolling history.

### Prior revisions
**Revision 26 - 2026-08-05.** Added the **UI & UX Capability Guide**: the how-to layer over the seven UI standards (layer stack, job-to-path picker, the /ui-design stages, a command sheet, an archetype picker, the veto table, the tells mapped to the detector rule that catches each, and where artifacts land). Ships as `templates/ui-capability-guide.template.html`, instantiated as `docs/ui-guide.html` with a graph hub node; `docs-graph.py` gained a **guide** surface kind so the Docs Explorer describes it properly. Dogfooded through revision 25's own control: 69 detector findings, all fixed in the artifact and none suppressed - including a `kicker-above-heading` the craft floor bans outright, and 68 `low-contrast` false positives that were resolved by moving to standards-track `forced-colors` after computing every pairing across all three modes (0 real failures). Templates 22->23.

**Revision 25 - 2026-08-05.** Integrated two external capabilities into the UI stack, each adopted only for the part it genuinely adds. **`ui-craft-detection.md`** (CD1-CD19) adopts the **Impeccable** detector (Apache-2.0) as a rung-2 automated control - the argument is the pack's own CI6 control ladder, and the proof is that it found three documented-in-prose defects in the pack's own mockup-harness template. The seam is free: the detector reads `DESIGN.md`, exactly the artifact U3a already mandates, so it enforces U3/U20 **outward** against built source for the first time (`design-lint.py` only ever checked inward). Impeccable's competing 23-command skill was deliberately not adopted. **`ui-visual-assets.md`** (VA1-VA18) governs generative imagery (Higgsfield): never generate the interface itself; generate once then download-optimize-commit (provider retention is 7 days); mood never structure; no likeness or customer-data egress. Added `scripts/ui-craft-gate.py` (the CD11 translation into DX22 rubric shape with the CD12 severity floors). Wired into /ui-design, /implement and /design on both surfaces; fixed the four defects the detector found in the pack's own templates; registered defect classes UX-C (controlled), VA-A, VA-B. Knowledge 31->33, scripts 11->12.

**Revision 24 — 2026-08-03.** Two fixes to `graphify-setup.py`. (1) The join lens was reporting **itself**: `docs/lenses/**` are graph artifacts, so the scan read `code-doc-join.md`'s own table of referenced paths and reported them again as gaps — a feedback loop that grows every run (measured in a consuming repo: 42 of 94 Gap-1 rows, 45%, were self-referential; after the fix, 0). Derived output is not a record and is now excluded from the scan. (2) `--check` now reports **lens freshness** — the code graph is git-ignored build output, so the only committed evidence of its age is the commit the lens records about itself, and nothing was looking at it. Deliberately narrow: only *source* changes count.

**Revision 22 — 2026-08-02.** Defect fix: the generated `graph-health` lens hardcoded a link to `docs-index`, which is not a graph node (`docs/docs-index.js` is derived data, not a frontmatter-bearing artifact), so `docs-graph.py validate` reported a dangling link in **every** repo that ran `--init` — failing the docs-health gate the pack itself recommends. Fixed in `obsidian-setup.py`; repos that already ran `--init` should repoint the link in their `docs/lenses/graph-health.md`.

**Revision 21 — 2026-08-02.** The **No-Guessing Protocol** (`no-guessing-protocol.md`, NG1–NG11) — mechanism rather than another prohibition, because a guess and a fact are indistinguishable from the inside. Three permitted moves when you do not know (check / mark with an inline `assume:` / ask) with no fourth; the pre-registration rule that an assumption not written down beforehand is a guess, which removes *"I assumed X"* as a post-hoc excuse; the tells; cheapest-check-first so the disciplined path is the lazy path; *Verified means observed, never likely*; no laundering a guess through a citation, tool, sub-agent or `INFERRED` edge; guess-caused bugs become defect classes; and the moment-of-writing question *"if this is wrong, how would I find out, and when?"*. Wired as the **first** managed-block bullet on both surfaces, cross-linked from E15 and CI9. Knowledge 30→31.

**Revision 20 — 2026-08-02.** Composed **Graphify** (graphify.com, Apache 2.0, PyPI `graphifyy`) — an on-device **code** knowledge graph — with the pack's docs graph: `code-knowledge-graph.md` (GK1–GK16) and `graphify-setup.py`. Three graphs, one knowledge base: docs hold intent and are the record, code holds reality and is a derived build output, Obsidian is the human lens. GK6–GK7 map `EXTRACTED`/`INFERRED`/`AMBIGUOUS` onto Verified/Inferred/Flagged, making E15 cheap to satisfy with a cited `file:line` traversal while keeping *a citation is not a promotion*. GK4 is **de-dup, not blanket ignore**, and inverts by repo kind — in a consuming repo there is no `pack/`, so `.claude/` and `docs/ai-forward-pack/` are the only copy and are kept (a blanket ignore there drops 153 files, 97 of which exist nowhere else). `--join` writes the code↔docs lens. Corrected the revision-19 claim that "Graphify" was an Obsidian plugin. Renamed the rollout script to `tools/setup-knowledge-graphs.ps1`, now covering both lenses. Knowledge 29→30, scripts 10→11.

**Revision 19 — 2026-08-02.** The **Obsidian lens** (`obsidian-lens.md`, OB1–OB14): `docs/` is already a valid Obsidian vault, so the lens costs nothing to adopt and must never become a dependency. Obsidian stays a reader; frontmatter is the record; no query is load-bearing in a canonical artifact; any relied-upon insight must also be obtainable dependency-free. Commits the vault **config** (incl. each plugin's `manifest.json` for version provenance), ignores the per-user **state** and plugin code — refining project-memory **M9**, which had said ignore `.obsidian/` wholesale. Graph coloured by artifact type with status overlays last. Added the stdlib `obsidian-setup.py` (`--check`/`--install-app`/`--init`/`--fetch-plugins`/`--analyze`, the last computing exact Brandes betweenness with no plugin required). Knowledge 28→29, scripts 9→10.

**Revision 18 — 2026-08-02.** Data-model primacy, end-to-end integrity, continuous improvement, and the `/ui-design` craft skill. Four knowledge docs: `domain-and-data-modelling.md` (DM1–DM18 — DDD conceptual model then dimensions + append-only facts; grain before columns, additivity, per-attribute history rule, derive-don't-store, expand-migrate-contract), `end-to-end-integrity.md` (E1–E18 — rigor is unconditional, the change-surface list, prove the rendered surface and cross-surface consistency, a gate's green ≠ its contents', read the state, never assert own-code shape from memory), `continuous-improvement.md` (CI1–CI12 — capture the class not the instance, class→sweep→derive→prevent, the control ladder, a seed register of 20 defect classes), `ui-design-craft.md` (DX1–DX25 — direction before pixels, the generic-AI-look tells, the fidelity ladder, the review harness, the 18-dimension critique rubric). New skill `/ui-design`; templates `mockup-harness`, `ui-review`, `defect-classes`. Wired into /specify, /define-architecture, /design, /implement, /investigate, the Data & Persistence and UX & Accessibility personas, and both managed blocks. Also fixed a pre-existing truncated "UI:" bullet in both managed blocks. Skills 17→18, knowledge 24→28, templates 19→22.

**Revision 17 — 2026-07-10.** Docs Explorer overhaul: Browse as the canonical projection with selection separated from neighborhood context, deterministic semantic layouts, and local/offline core behavior (`docs-explorer-core.js`); `docs-graph.py` gained docs-index/v2 identities, bounded context packets, atomic publish, persistent sibling JSONL locks, and empty-scalar frontmatter parsing; added `bounded_process.py`; Pack Doctor gained `--strict`; the Audit Explorer dropped CDN runtimes for local DOM APIs; added the Playwright/Python regression suites; `*.jsonl.lock` added to install hygiene, applied by `/addpacktorepo` and `/updatepack`. Scripts 7→9.

**Revision 16 — 2026-07-10.** Added `/forensicreview`: a docs-only deep architecture/design/implementation review that reconstructs architecture and documentation before emitting an evidence-linked P0-P3 backlog of risks, verified issues, and todos. Added its Copilot prompt and eval; registered it in the workflow knowledge, managed blocks, pack docs, and explainer. Skills 16→17.

**Revision 15 — 2026-06-30.** Added the project design-language artifact based on the Google Stitch DESIGN.md format, extended with the pack's UI floors; added `design-lint.py`; added attributed Linear design-language examples; wired the design-language through `/specify`, `/design`, `/implement`, the UI standards/catalog, and `docs-graph.py`. Templates 17→19; scripts 6→7.

**Revision 14 — 2026-06-30.** Added the **Solution-Selection Ladder** (`solution-selection-ladder.md`) — the 7-rung smallest-correct forcing function (YAGNI → reuse-in-codebase → stdlib → native → installed dep → one line → minimum), the inline `simplify:` ceiling/trigger marker, the debt ledger + rot-flag (mapped onto V13/V17), tier-gated ceremony (T0 code-first / T1-T2 full), and the Simplifier's delete-list output format — adapted from the ponytail skill (MIT) and hardened to compose with the Simplifier persona and the correctness floors. Wired into /design, /implement, /migrate and the-simplifier; managed blocks RE-PASTED. Knowledge docs 23→24.

**Revision 13 — 2026-06-27.** Unified the **prompt-log** onto the audit log — one store of prompts, not two. `prompt-log.py` became a reuse lens over the committed audit log (`docs/audit/audit-log.jsonl`): browse/search/list/show/get read the audit log, and `add` writes a `kind:prompt` entry through `audit-log.py` (the single writer) instead of a separate `.aiforward/prompts.jsonl`; a legacy store is read only via `--store`. Knowledge doc `audit-and-change-log.md` gained AL13; `/prompts`, `/searchprompts`, `/auditlog` and their Copilot prompts re-copied; managed blocks RE-PASTED.

**Revision 12 — 2026-06-27.** Added the **Audit & Change Log** system: a durable, committed, append-only audit log (`docs/audit/audit-log.jsonl`) of every meaningful prompt/skill/script and a curated change log (`docs/audit/change-log.jsonl`) of design decisions with git before/after — so work compounds across sessions. New knowledge doc `audit-and-change-log.md` (Audit Mandate AL5 — every skill appends as its last action; Change Mandate CL1–CL2 — collectknowledge/define-architecture/design/migrate capture the decision), the stdlib `audit-log.py` (the single writer of record), the `audit-explorer.template.html` viewer (searchable timeline · copy-prompt · full-history↔changes toggle), the `/auditlog` CLI skill, and the `docs/audit/audit-log.md` graph hub node. Wired into all 13 reasoning skills. Knowledge docs 22→23, templates 16→17, scripts 5→6, skills 15→16. (Revision 13 then unified the revision-11 prompt-log onto this one store.)

**Revision 11 — 2026-06-22.** Added the **prompt-log** capability (a personal prompt-reuse journal, distinct from the revision-12 audit/change log): a stdlib `prompt-log.py` engine — a project-local, labelled+timestamped log of prompts you can browse/search/reuse, stored at `<repo>/.aiforward/prompts.jsonl` (git-ignored) — and two utility skills, `/prompts` (an arrow-navigable stack: → expand, ← collapse, Enter reuse) and `/searchprompts` (freeform search of the same stack); reuse copies the chosen prompt to the clipboard to paste-and-edit. Managed blocks RE-PASTED. Skills 13→15, scripts 4→5. (Revision 13 unified this onto the audit log — prompt-log is now a reuse lens over `docs/audit/audit-log.jsonl`, not a separate store.)

**Revision 10 — 2026-06-14.** Added the AI commercial/cost/billing models knowledge doc (`ai-commercial-models.md`): M1 bring-your-own subscription/key (BYOK), M2 metered pass-through, M3 absorbed subscription, M4 credits/packs, M5 hybrid; architecture patterns AC1–AC5 mapped to LOA by name (Receipt Ledger as the meter, Token Budget Throttle as the quota, Capability Router/Cascade as margin control); data-governance AC6–AC7 (whose account/DPA; zero-retention/no-training applies at the commercial-API tier only); UX/UI AC8–AC9; decision framework AC10. The AI Systems Engineer now authors the commercial model in Peer Mode and interrogates it at the gate; `ui-interaction-design.md` gained U15a (cost & commercial transparency as a UX surface). Knowledge docs 21→22.
**Revision 9 — 2026-06-14.** Added the technical/scientific/quantitative UI capability: a new base-knowledge doc `technical-ui-design.md` (TQ1–TQ12 — density-with-hierarchy, numerical legibility, perceptually-uniform colormaps [viridis; never rainbow/jet], data-ink, uncertainty-first, direct-manipulation-plus-precision, units, provenance, reactive recompute, large-data performance); catalog Section G (six archetypes G1 Parametric Modeling Workbench, G2 Scientific Visualization Pipeline, G3 Computational Notebook, G4 Computational Spreadsheet/Grid, G5 Probabilistic/Uncertainty Explorer, G6 Multi-Panel Data Terminal); grammar enums (Arch:SpatialBounded, Nav:Ribbon, six Layouts); ui-interaction-design + both UX lenses cross-referenced. Knowledge docs 20→21.

**Revision 8 — 2026-06-14.** Applied four squad-comparison suggestions: the `aiforward` developer CLI (tools/, a stdlib Façade over the scripts); a deployable install-health `pack-doctor.py`; a `scrub.py` PII/secret first-pass; project-memory (a ledger template + `project-memory-and-obsidian.md`, Obsidian as an optional lens); and a committed `responsible-ai-policy.md` (MS RAI + NIST RMF crosswalk). Scripts 2→4, knowledge 18→20, templates 15→16.

**Revision 7 — 2026-06-14.** Added /extendaibundle (the 13th skill — extend the pack from a prose prompt, scaffolded by new-capability.py, proven by verify-bundle.ps1); /specify gained JTBD-based UX-archetype auto-selection (records the signature + rationale in spec Part C, announces it in the summary); spec template gained the Archetype Signature subsection.

**Revision 6 — 2026-06-14.** Both pack-lifecycle skills (/addpacktorepo, /updatepack) gained an explicit Modes section — a dry-run/preview that writes nothing and a stated idempotency contract; /addpacktorepo links the explainer's GitHub Pages URL with the local file as offline fallback.

**Revision 5 — 2026-06-14.** Hardened the two pack-lifecycle skills: /addpacktorepo resolves the pack source explicitly (current repo → explicit path → AI_FORWARD_PACK env → sibling ai-forward clone) like /updatepack, so it is no longer broken when invoked from a repo with no pack/ tree; both gained a Documentation & discoverability note explaining why a pack-lifecycle skill writes no knowledge-graph artifact.

**Revision 4 — 2026-06-14.** Updated skill count 10→12 in both managed blocks (CLAUDE.block.md, AGENTS.block.md); added /updatepack and /addpacktorepo to the skill/workflow lists so agents in both tools know the new skills exist. Managed blocks RE-PASTED.

**Revision 3 — 2026-06-14.** Added /updatepack skill (run from an installed repo to pull latest from a local ai-forward clone; diffs INSTALL.md revisions, applies only the changelog delta, shows a tabular action summary, offers commit+push) and /addpacktorepo skill (run from the AI-Forward repo to install the pack into any local repo by path; recces the target, applies the full deployment map, summarises every artifact and what it does, links to the explainer, offers commit+push). Skills count 10→12.

**Revision 2 — 2026-06-14.** UI Archetype Grammar G1-G16 + 16-archetype catalog (knowledge docs 16–18); UI Interaction Design and Specification Standards cross-referenced to the grammar; /specify, /design, /implement updated to identify and build to the archetype; managed blocks RE-PASTED with the archetype-selection line.

**Revision 1 — 2026-06-13 (baseline; changelog tracking began).** Specification Standards S1-S18 + three-layer spec template + UX Researcher/IA persona (roster to 23); UI & Interaction Design Standard U1-U20; threat-model + privacy-review templates (to 15); /adopt + /migrate skills (to 10); foundation-check.py, CI graph-health workflow, evals harness; tool-parity (orchestrator names both Claude Code subagent and Copilot inline-turn; INSTALL 1.2 strip-`tools:`-when-deploying-to-Copilot, 1.3 fit-for-both). Managed blocks RE-PASTED (spec + UI lines). For a repo predating changelog tracking, do one full reconciliation against the deployment map, then track `revision` from here.

---

# Installing the AI-Forward Pack (manual reconciliation)

This pack drops into any GitHub repository and works with **Claude Code**, **GitHub Copilot**, or **both at once**. It is built on the **Agent Knowledge Pack** (Body of Knowledge, Rules of the Road, Persona Catalog, Engineering Governance, Layered-Optimized Architecture, Testing Strategy, C# Style Guide) and **vendors those foundation docs into `knowledge/`**, so the bundle is self-contained — it works even in a repo that doesn't already have the base pack. (The vendored docs are copies; if you maintain the Agent Knowledge Pack separately, refresh them when it changes.)

The model is the same for both tools: **knowledge** files are always-available reference, **skills** carry the workflow logic, **agents** are the personas (peers + adversaries), and a thin **command/prompt** layer is just an entry point that invokes a skill. Only the file locations differ per tool.

> **This is the reconciliation guide — the pack ships with no installer.** You copy its content into a target repository by hand (or with your own tooling), using the deployment map below; the map is the contract — each source path has exactly one destination per tool. Reconciling a pack update = following the **`changes` changelog in this file's frontmatter** (the key guide — re-copy exactly the listed `paths`, re-apply the Copilot frontmatter wraps, and RE-PASTE the managed blocks where flagged); if your repo predates changelog tracking, diff once and then track `revision` from there.

> **Managed blocks.** `adapters/managed-blocks/CLAUDE.block.md` and `adapters/managed-blocks/AGENTS.block.md` are ready-to-paste: append each (markers included) to the repo's `CLAUDE.md` / `AGENTS.md`, creating the file if absent — they are the wiring that points each tool at everything else (reasoning spine, personas, skills, testing, instrumentation, Docs Explorer, foundation). On update, replace everything between the markers rather than merging line by line. (§1.1 below.)

> **Two one-time docs steps.** Copy `templates/docs-explorer.template.html` to `docs/index.html`, replacing `__PROJECT__` with the repo name (skip if the repo already owns a docs site there). Do **not** seed `docs/docs-index.js` by hand — the first skill run creates it (Discoverability Mandate, V10), and an accumulated index must never be overwritten.

---

## 1. What goes where

| Pack artifact | Claude Code | GitHub Copilot |
|---|---|---|
| Rules of the Road (the always-on rules) | `CLAUDE.md` (link to it) + `.claude/` | `AGENTS.md` |
| Knowledge docs (`knowledge/*.md`, plus the existing pack) | `.claude/knowledge/` or repo `docs/` referenced from `CLAUDE.md` | `.github/instructions/*.instructions.md` with `applyTo` globs |
| The 18 skills (`commands/*/SKILL.md`) | `.claude/skills/<name>/SKILL.md` | `.github/prompts/<name>.prompt.md` (wrapper that carries the same flow) |
| Thin command entry points | `.claude/commands/<name>.md` | `.github/prompts/<name>.prompt.md` |
| Peer agents (orchestrator, product-strategist, domain-researcher) | `.claude/agents/<name>.md` | `.github/agents/<name>.agent.md` |
| Adversary agents (the existing 11) | `.claude/agents/<name>.md` | `.github/agents/<name>.agent.md` |
| Templates (`templates/*`, 19 incl. the glossary, decision note, threat model, privacy review, design-language + preview) | `docs/ai-forward-pack/templates/` (referenced by skills) | same (shared) |
| Script bundle (`scripts/*` — stdlib-only Python tools plus dependency-free `docs-explorer-core.js`) | `docs/ai-forward-pack/scripts/` (`docs-graph.py` owns graph mechanics + bounded grounding packets; `docs-explorer-core.js` owns deterministic browser state/layout; `audit-log.py`/`prompt-log.py` own history/reuse; `design-lint.py` checks design-language references; Python tools need Python 3.8+) | same (shared) |
| CI reference workflow (`ci/docs-health.yml`) | `.github/workflows/docs-health.yml` (optional but recommended — gates PRs on graph health) | same (shared) |
| Pack regression suite (`evals/`) | **not deployed** — pack-maintenance tooling; lives wherever you maintain the pack source | — |
| Pack docs (`README`, `OVERVIEW`, `research-synthesis`, this file) | `docs/ai-forward-pack/` | same (shared) |
| The Docs Explorer (`templates/docs-explorer.template.html`) | `docs/index.html` (one-time copy, `__PROJECT__` substituted) | same (shared) |
| The UI capability guide (`templates/ui-capability-guide.template.html`) | `docs/ui-guide.html` (one-time verbatim copy) + a `docs/ui-guide.md` hub node; registers itself as a **guide** surface on the next `docs-graph.py derive` | same (shared) |
| Managed blocks (`adapters/managed-blocks/*.block.md`) §1.1 | paste into `CLAUDE.md` | paste into `AGENTS.md` |

**Knowledge-doc wrap for Copilot:** each `knowledge/<name>.md` becomes `.github/instructions/<name>.instructions.md` by prepending frontmatter `---` / `applyTo: "**"` / `---` (exception: `csharp-style-guide` is scoped with `applyTo: "**/*.cs,**/*.csx"`). Claude Code takes the files verbatim into `.claude/knowledge/`. `knowledge/FOUNDATION.md` is a **provenance manifest**, not an instruction doc — deploy it alongside the others but do **not** wrap it as a Copilot instruction.

**Ownership routing (recommended, V13).** Add a `docs/**` section to the repo's `CODEOWNERS` so documentation changes route to the artifact owners — and treat the frontmatter `owner:` field as the per-artifact source of truth (CODEOWNERS patterns go stale; review them on a cadence).

### 1.1 Managed blocks
The block files in `adapters/managed-blocks/` carry their own BEGIN/END markers. Append once; on every pack update, replace the marked region wholesale.

The peer agents in `adapters/claude-code/agents/` are written in Claude Code's subagent format. For Copilot, the same three personas are described in `knowledge/collaborative-personas.md` §3 and §6 — copy each into a `.github/agents/<name>.agent.md` with the constructive system prompt shown there. The four **added** adversaries (AI Systems Engineer, Data & Persistence Architect, Privacy & Data Governance, Release Engineer) — plus the five **UX/UI/app & documentation** lenses (Mobile App Developer, Native Desktop Developer, **UX Researcher / Information Architect**, UX & Accessibility, Documentation Steward) — also ship as agent files in `adapters/claude-code/agents/`; place them in both tools' agent directories. The original eleven adversaries ship as `*_agent.md` files in the Agent Knowledge Pack; **§8-upgraded drop-in replacements** that emit the verdict shape directly (severity, confidence, falsifiable veto-clears-when, owned anti-patterns) are in `adapters/copilot/agents/`. Deploy those in place of the originals — to `.github/agents/<name>.agent.md` (Copilot) or `.claude/agents/<name>.md` (Claude Code); the content is tool-neutral. Pair them with `knowledge/persona-cards.md` (the §8 cards) and `knowledge/persona-audit.md` (the operating standard) so routing, severity, and veto-clearing are consistent across both tools.

### 1.2 Frontmatter transform when deploying a Claude-Code persona to Copilot
The persona **bodies are tool-neutral** (they describe peer/adversary behavior, not tool mechanics — see §1.3); only the **YAML frontmatter** differs between the two tools' agent formats. When you copy a persona from `adapters/claude-code/agents/<name>.md` into Copilot's `.github/agents/<name>.agent.md`, apply this transform:

- **Strip the `tools:` line.** Claude Code uses `tools: [Read, Grep, Glob, WebSearch, WebFetch, Bash, Edit]` to scope a subagent's permissions; that token vocabulary is **Claude-Code-specific**. Copilot's agent format uses a *different* tool vocabulary (e.g. `code_search`, `readfile`, `#tool:web/fetch`) and **ignores unknown tool names**, silently falling back to all-tools — so a verbatim copy is misleading. Removing the line gives the correct, intended result: Copilot's documented default is **"agents can access all available tools."** (This is exactly why the §8-upgraded `*_agent.md` files in `adapters/copilot/agents/` carry *no* `tools:` line — match that pattern.) If you want to scope a Copilot agent, re-add a `tools:` array using Copilot's own tool names.
- **Keep `name:` and `description:`** as-is — both formats use them, and `description:` is what routes the agent in both tools.
- **`model:` is optional in both** and may be omitted; if present, use each tool's own model identifiers.

The reverse also holds: the `*_agent.md` adversaries in `adapters/copilot/agents/` carry no `tools:` line, so they drop into `.claude/agents/` unchanged (Claude Code likewise defaults to broad tool access when `tools:` is absent). **One source of truth per persona; a one-line frontmatter edit at the Copilot boundary.**

### 1.3 Why the personas and directives are fit for both tools
The pack is deliberately built so the *same* personas and knowledge directives work under both execution models, with the divergence isolated to the thin entry layer:

- **Knowledge docs and persona bodies are tool-neutral.** They describe *what* to reason about and *what* each lens checks — never *how* an agent is spawned. The single place a persona referenced a Claude-Code mechanic (the Orchestrator's "invoke the adversary as a separate subagent") now names **both** mechanisms: a separate **subagent** in Claude Code, a distinct labeled **inline turn** in Copilot.
- **The execution difference lives in the prompt layer.** Claude Code auto-convenes the relevant subagents when a skill runs (you watch the peer→adversary dialog as separate agent turns). Copilot runs a **single agent**, so every `*.prompt.md` instructs it to **enact the round-table inline** — voice each peer, then each adversary's labeled critique with a severity and explicit PASS/BLOCK — within one response. Same dialog, same vetoes, same artifact; different staging. (Details in §5 below.)
- **The artifacts are identical.** Both tools write the same `docs/` artifacts from the same `templates/`, run the same `docs-graph.py` bundle, and answer to the same gates — so a repo driven by either assistant, or both, stays consistent.

---

## 2. Claude Code install

```
your-repo/
├─ CLAUDE.md                      # short, always-true conventions; links the Rules of the Road
└─ .claude/
   ├─ knowledge/                  # this pack's knowledge/ + the existing pack's docs
   │  ├─ rigor-protocol.md
   │  ├─ collaborative-personas.md
   │  ├─ spike-protocol.md
   │  ├─ persona-audit.md          # gap analysis + the Persona Operating Standard
   │  ├─ persona-cards.md          # all 23 lenses as uniform §8 cards
   │  └─ (agent-body-of-knowledge.md, agent-rules-of-the-road.md, persona-catalog.md, …)
   ├─ skills/
   │  ├─ specify/SKILL.md
   │  ├─ define-architecture/SKILL.md
   │  ├─ design/SKILL.md
   │  ├─ implement/SKILL.md
   │  ├─ investigate/SKILL.md
   │  ├─ adddomainexperts/SKILL.md   # tailors the roster to the project's domain
   │  ├─ updatepack/SKILL.md         # update an installed pack from a local ai-forward clone
   │  └─ addpacktorepo/SKILL.md      # install the pack into a new local repo by path
   ├─ agents/
   │  ├─ orchestrator.md
   │  ├─ product-strategist.md
   │  ├─ domain-researcher.md
   │  ├─ ai-systems-engineer.md
   │  ├─ data-persistence-architect.md
   │  ├─ privacy-data-governance.md
   │  ├─ release-engineer.md
   │  └─ (enterprise-architect.md, test-architect.md, security-architect.md, … the 11)
   └─ commands/
      └─ specify.md               # thin wrappers (optional; skills auto-apply)
```

Keep `CLAUDE.md` short — it is always in context. Put the durable reasoning in the knowledge files and let the skills pull them in. Skills auto-apply by their `description`; a command of the same name is just a manual trigger, and the skill takes priority. Spikes run under `spikes/` (see `knowledge/spike-protocol.md`); add `spikes/` to `.gitignore` unless a probe is worth keeping as evidence. The graph tool's append-only JSONL writes use persistent sibling lock files to prevent inode-replacement races; add `*.jsonl.lock` to `.gitignore` and do not commit those local coordination files.

**Sample thin command** — `.claude/commands/specify.md`:

```markdown
---
description: Turn a prompt or idea into a crisp, testable product spec (runs the /specify skill).
---
Run the **specify** skill on the following input, in Peer Mode for authoring and
Adversary Mode at the gate. Produce the spec artifact from templates/spec.template.md
and do not let the authors clear their own hard veto.

Input: $ARGUMENTS
```

---

## 3. GitHub Copilot install

```
your-repo/
├─ AGENTS.md                      # the Rules of the Road (precedence, gates, Proof Pack)
└─ .github/
   ├─ instructions/
   │  ├─ rigor.instructions.md            # applyTo: "**"           (always)
   │  ├─ csharp.instructions.md           # applyTo: "**/*.cs"      (the C# style guide)
   │  └─ tests.instructions.md            # applyTo: "**/*Tests*.cs"
   ├─ prompts/
   │  ├─ specify.prompt.md
   │  ├─ define-architecture.prompt.md
   │  ├─ design.prompt.md
   │  ├─ implement.prompt.md
   │  ├─ investigate.prompt.md
   │  ├─ collectknowledge.prompt.md
   │  ├─ adddomainexperts.prompt.md
   │  ├─ document.prompt.md
   │  ├─ updatepack.prompt.md
   │  └─ addpacktorepo.prompt.md
   └─ agents/
      ├─ orchestrator.agent.md
      ├─ product-strategist.agent.md
      ├─ domain-researcher.agent.md
      └─ (the 11 adversary *.agent.md from the Agent Knowledge Pack)
```

Use `applyTo` globs so instructions attach to the files they govern (the C# style guide on `**/*.cs`, the testing directives on test files). The Rigor Protocol attaches to everything (`applyTo: "**"`). If you use the **GitHub Spec Kit**, these prompts compose with `/speckit.*`; the pack's `/specify` produces the spec the Spec Kit then drives.

**Where the peer dialog comes from — and why Copilot differs from Claude Code.** This is the one place the two tools genuinely diverge, so it is worth being explicit:

- **Claude Code** treats each file in `.claude/agents/` as a real **subagent**. When a skill runs, the orchestrator *spawns* the relevant personas (routed by each agent's `description`), each in its own context window, and they report back — so you literally watch the peer→adversary dialog happen as separate agent turns.
- **GitHub Copilot** runs as a **single agent** at a time. Custom agents (`.github/agents/*.agent.md`, formerly "chat modes") are personas you switch *into* (the agent picker, or `@name`), or chain with **handoffs** (Plan → Implement → Review) — Copilot does **not** auto-convene a chorus of subagents during one `/prompt`. A `/design` or `/implement` prompt runs in whatever single agent is active.

That is why, in Copilot, the skills "work" but you may not see the back-and-forth you expect. The pack's prompts therefore instruct Copilot to **enact the round-table inline** — voicing each peer's contribution, then each adversary's critique with a severity and an explicit PASS/BLOCK — within the one response. You have three ways to get the personas in Copilot, least to most manual: (1) run the `/<skill>` prompt and let it perform the inline dialog (default); (2) `@`-mention a specific agent (e.g. `@test-architect`) for a focused single-persona pass; (3) use agent **handoffs** to step through stages with pre-filled context. In Claude Code, just run the skill — the subagents convene automatically.

**Sample prompt wrapper** — `.github/prompts/specify.prompt.md`:

```markdown
---
mode: agent
description: Turn a prompt or idea into a crisp, testable product specification.
---
You are running the **specify** workflow (knowledge/rigor-protocol.md, specialized to the
problem). Convene the Product Strategist and Domain Researcher as collaborating peers to
author; then switch to the Simplifier, Test Architect, and Security (if identity/PII) as
adversaries at the gate. Run the stages: interdict the rush, OPEN the problem, INTERROGATE
with precise questions, establish comparables and user evidence with cited sources,
DISCONFIRM at the adversarial gate, CONVERGE to the spec. Write the spec using
templates/spec.template.md. The authors must not clear their own hard veto.

${input}
```

---

## 4. Running both tools in one repo

The two layers coexist without conflict: `CLAUDE.md`/`.claude/` for Claude Code, `AGENTS.md`/`.github/` for Copilot. Keep the **knowledge and templates as the single source of truth** in `docs/` (or duplicated by symlink), and let each tool's skills/prompts reference the same files, so the reasoning protocol, personas, and artifacts stay identical no matter which assistant a developer drives. Update the protocol once; both tools inherit it.

---

## 5. Smallest viable install

If you want to start small: install the **Rules of the Road** (`CLAUDE.md` / `AGENTS.md`), the **Rigor Protocol** and **Collaborating Personas** knowledge files, and the **`/specify`** and **`/implement`** skills with the **orchestrator**, **product-strategist**, **domain-researcher**, and **test-architect** agents. That gives you the rush-interdicting reasoning spine, the peer/adversary mode-switch, and a spec-to-tested-code loop. Add the architecture, design, and investigate workflows and the full adversary council as the work warrants (proportional to tier — Rules of the Road §0.2).
