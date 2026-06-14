---
doc: INSTALL
purpose: 'Manual reconciliation guide and refresh changelog. On a repo refresh, read `changes` below — it is the key guide: it lists exactly what to re-copy and re-paste since the previous revision, so you do not have to diff the whole tree.'
bundle_version: '2026.06.14'
revision: 2
released: '2026-06-14'
counts: { lenses: 23, skills: 10, knowledge_docs: 18, templates: 15, scripts: 2 }
refresh_protocol: 'Compare your repo last-applied revision to the `revision` above. If it is lower, apply each entry in `changes` in order — re-copy the listed `paths` to their mapped destinations (deployment map in the body), re-apply the Copilot frontmatter wraps, and where an entry `deploy` says RE-PASTE, replace the managed blocks wholesale between their markers. Never overwrite an accumulated docs/docs-index.js.'
changes:
  - { type: added, area: knowledge, paths: ['knowledge/ui-archetype-grammar.md', 'knowledge/ui-archetype-catalog.md'], deploy: 'copy both to .claude/knowledge/ AND wrap each as .github/instructions/<name>.instructions.md (applyTo all files)', summary: 'UI Archetype Grammar G1-G16 (a hardened two-layer grammar that selects a UI archetype - routing/temporal/data - as a determinism control for code generation) plus a 16-archetype catalog with exemplars, canonical Archetype Signatures, and model-agnostic codegen descriptors. Knowledge docs 16 to 18.' }
  - { type: changed, area: knowledge, paths: ['knowledge/ui-interaction-design.md', 'knowledge/specification-standards.md'], deploy: 're-copy to .claude/knowledge/ and re-wrap the Copilot instructions' , summary: 'Cross-referenced the archetype grammar: the UI standard notes the grammar sits one level above it; spec standard S8 records the chosen Archetype Signature in Part C as the UI-layer selector.' }
  - { type: changed, area: skill, paths: ['commands/specify/', 'commands/design/', 'commands/implement/', 'adapters/copilot/prompts/specify.prompt.md', 'adapters/copilot/prompts/design.prompt.md', 'adapters/copilot/prompts/implement.prompt.md'], deploy: 're-copy each SKILL.md to .claude/skills/<name>/ and each prompt to .github/prompts/', summary: '/specify identifies the nearest archetype and records its signature in Part C; /design resolves each facet concrete against tokens/states; /implement builds to the signature facet rules (red-first state/a11y/perf tests) - so an agent reaches for the right archetype instead of a generic dashboard.' }
  - { type: changed, area: managed-block, paths: ['adapters/managed-blocks/CLAUDE.block.md', 'adapters/managed-blocks/AGENTS.block.md'], deploy: 'RE-PASTE both blocks wholesale between their BEGIN/END markers', summary: 'Added a UI-archetype line: for a user-facing UI, select the archetype as a determinism control before generating and build to its facet rules.' }
---

## Changelog — what changed since the last version

**The frontmatter `changes` list above is the refresh guide.** When you pull a new bundle into an existing repo, you do **not** need to diff the whole tree: read `changes`, and apply exactly those re-copies and managed-block re-pastes. Each entry names the `paths` that moved and the precise `deploy` action (including the few that say **RE-PASTE** the managed blocks, which is the step most easily missed). Check your repo's last-applied `revision` against the `revision` in the frontmatter to know whether — and how far — you are behind.

**Convention (moving forward).** Every change to the bundle updates this file's frontmatter as part of the same change:
1. bump `revision` by 1 (monotonic — it never resets, so it is the reliable "is my repo behind?" anchor) and update `bundle_version` / `released` / `counts`;
2. replace `changes` with *this* version's delta only (so the frontmatter is always "since the previous revision");
3. move the **previous** `changes` into the **Prior revisions** log below as a dated, collapsed entry.

So at any moment: the frontmatter `changes` = the latest delta (the refresh guide), and this section = the full rolling history.

### Prior revisions
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
| The 10 skills (`commands/*/SKILL.md`) | `.claude/skills/<name>/SKILL.md` | `.github/prompts/<name>.prompt.md` (wrapper that carries the same flow) |
| Thin command entry points | `.claude/commands/<name>.md` | `.github/prompts/<name>.prompt.md` |
| Peer agents (orchestrator, product-strategist, domain-researcher) | `.claude/agents/<name>.md` | `.github/agents/<name>.agent.md` |
| Adversary agents (the existing 11) | `.claude/agents/<name>.md` | `.github/agents/<name>.agent.md` |
| Templates (`templates/*`, 15 incl. the glossary, decision note, threat model, privacy review) | `docs/ai-forward-pack/templates/` (referenced by skills) | same (shared) |
| Script bundle (`scripts/*.py` — `docs-graph.py` + `foundation-check.py`) | `docs/ai-forward-pack/scripts/` (skills invoke docs-graph for all graph mechanics — V18; needs Python 3.8+, stdlib only) | same (shared) |
| CI reference workflow (`ci/docs-health.yml`) | `.github/workflows/docs-health.yml` (optional but recommended — gates PRs on graph health) | same (shared) |
| Pack regression suite (`evals/`) | **not deployed** — pack-maintenance tooling; lives wherever you maintain the pack source | — |
| Pack docs (`README`, `OVERVIEW`, `research-synthesis`, this file) | `docs/ai-forward-pack/` | same (shared) |
| The Docs Explorer (`templates/docs-explorer.template.html`) | `docs/index.html` (one-time copy, `__PROJECT__` substituted) | same (shared) |
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
   │  └─ adddomainexperts/SKILL.md   # tailors the roster to the project's domain
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

Keep `CLAUDE.md` short — it is always in context. Put the durable reasoning in the knowledge files and let the skills pull them in. Skills auto-apply by their `description`; a command of the same name is just a manual trigger, and the skill takes priority. Spikes run under `spikes/` (see `knowledge/spike-protocol.md`); add `spikes/` to `.gitignore` unless a probe is worth keeping as evidence.

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
   │  └─ document.prompt.md
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
