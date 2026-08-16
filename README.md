# AI-Forward

The development home of the **AI-Forward Pack** — a repository-droppable extension that turns
the Agent Knowledge Pack's adversarial reviewer council into a working swarm: collaborating
peers that *author*, adversarial personas that *attack*, and a staged reasoning discipline (the
**Rigor Protocol**) that slows the rush to a plausible answer and replaces it with evidence at
every step. It works with **Claude Code**, **GitHub Copilot**, or both.

This repo is two things at once:

1. **The canonical source** for the pack — everything you edit to expand it lives in [`pack/`](pack/).
2. **A live install of the pack** — the pack is installed into this repo (`.claude/`, `docs/`)
   so the skills, agents, and knowledge are active in Claude Code *while you work on the pack
   itself*. Dogfooding: the pack is built using the pack.

For the pack's own story — why it exists, what's inside, how to use the twenty-one skills — read
[`pack/README.md`](pack/README.md) and [`pack/OVERVIEW.md`](pack/OVERVIEW.md).

## Layout

```
ai-forward/
├─ pack/                  ← CANONICAL SOURCE — edit here to expand the pack
│   ├─ README.md  OVERVIEW.md  research-synthesis.md
│   ├─ knowledge/         ← the reasoning spine + 23-persona roster + vendored foundation
│   ├─ commands/          ← the 21 skills (one SKILL.md each)
│   ├─ templates/         ← the artifacts each skill produces
│   ├─ adapters/          ← INSTALL.md + Claude Code / Copilot agents + prompts + managed blocks
│   ├─ evals/             ← the pack's own regression suite
│   ├─ scripts/  ci/  examples/
│
├─ .claude/               ← GENERATED install (Claude Code reads this) — do not edit by hand
│   ├─ knowledge/  skills/  agents/
│
├─ docs/                  ← GENERATED install — templates, scripts, pack docs, Docs Explorer
│   ├─ index.html         ← the Docs Explorer (hierarchy · graph · mind map · health)
│   └─ ai-forward-pack/   ← templates/ scripts/ + README/OVERVIEW/research-synthesis/INSTALL
│
├─ tools/
│   ├─ sync-pack.ps1       ← regenerate .claude/ + docs/ from pack/  (run after editing pack/)
│   └─ package-pack.ps1    ← build dist/ai-forward-pack.zip for sharing
│
├─ web/
│   └─ ai-forward-pack-explainer.html ← self-contained interactive explainer (knowledge,
│                                        skills, Rigor Protocol, UI archetype mockups)
│
├─ CLAUDE.md              ← wiring that points Claude Code at the installed pack
└─ LICENSE                ← Apache-2.0
```

`.claude/` and `docs/` are **generated from `pack/`** and committed so a fresh clone has a
working install with no setup. `pack/` is the single source of truth — never edit the generated
copies directly; they're overwritten on the next sync.

## Using the pack (in this repo)

> **Running the scripts.** Commands are written `python3 <script>` (the POSIX name, matching every
> script's shebang). **On Windows use `python` or `py -3`** — python.org ships no `python3.exe`, and
> the `python3` you may see there is a Microsoft Store alias that is not Python (it prints *"Python
> was not found"* and exits `9009`). Run `pack-doctor.py` and its `python interpreter` check names
> the exact form for your machine. Full note: [`pack/adapters/INSTALL.md` §0](pack/adapters/INSTALL.md).

The pack is already installed, so in Claude Code here you can just run the skills — they apply
automatically by description, or call one explicitly:

```
/collectknowledge → /adddomainexperts → /specify → /define-architecture → /design → /implement → /document
                                                                              ↑
                                                            /investigate  (whenever a defect appears)
```

`/adopt` brings a brownfield repo into the pack; `/forensicreview` reconstructs and deeply reviews
an existing repo, then creates its prioritized risk backlog; `/migrate` runs characterization-first
refactors. Three **pack-lifecycle** skills manage the pack itself: `/addpacktorepo` installs it
into another local repo, `/updatepack` refreshes an installed repo to the latest revision, and
`/extendaibundle` adds new pack capabilities from a prose prompt with zero drift.
The natural order and what each skill produces are in [`pack/OVERVIEW.md`](pack/OVERVIEW.md).

## Expanding the pack (the sandbox loop)

1. Edit the source under [`pack/`](pack/) (a knowledge doc, a `commands/<name>/SKILL.md`, a
   persona in `pack/adapters/`, a template…).
2. Regenerate the install:
   ```powershell
   pwsh tools/sync-pack.ps1
   ```
3. Try the change in Claude Code in this repo (the regenerated skills/agents are now live).
4. Commit `pack/` **and** the regenerated `.claude/` + `docs/` together so source and install
   never drift. When you change the pack, also update the changelog in
   `pack/adapters/INSTALL.md` (bump `revision`) per the convention documented there.

## Sharing / distributing the pack

```powershell
pwsh tools/package-pack.ps1   # writes dist/ai-forward-pack.zip
```

Recipients drop the pack into their own repo by manual reconciliation — the deployment map and
update procedure are in [`pack/adapters/INSTALL.md`](pack/adapters/INSTALL.md). (`tools/sync-pack.ps1`
mirrors only the Claude Code surface needed *here*; the distributable in `pack/` carries the full
Claude Code **and** Copilot wiring.)

## Documentation

**Start here:** [`docs/portal/index.html`](docs/portal/index.html) is the **Documentation Portal** — the single, unified front door to the whole repo. Nine sections make everything navigable and discoverable from one place: **Getting Started · Capabilities · The Skills · Foundations · UI & Design · Architecture · Systems · Graph · Reference**. It covers a capabilities overview and a getting-started guide; concrete reference for every skill; the **Foundations** (the reasoning constitution, engineering guidance, and coding-style guides — the always-loaded knowledge docs); an in-depth **UI & Design** section (the seven UI standards + the UX/UI examples); the **Architecture** (the architecture of record, ADRs, specs, and component designs); the **Systems** (knowledge graph, dreaming, audit, personas); an embedded **Graph** view of the knowledge graph; and a **Reference** map that links out to every specialised surface. Open it over `file://`; it needs no server or build.

> **The portal is a lens, not a copy.** It is the *high-level, user-facing* layer. The repo's core knowledge stays exactly as structured as it is — the portal's Foundations, UI, and Architecture sections **list and link** the structured artifacts (knowledge docs, ADRs, specs, designs) with *derived summaries*; the artifacts themselves remain individually-owned Markdown in the knowledge graph.

> **Keep-current directive (how the portal never rots).** The portal is a **derived artifact** — its content (`docs/portal/portal-data.js`) is *generated* by `tools/build-docs-portal.py` as a pure function of committed sources: the **skill list + count** from `pack/commands/`, each **skill description** from its Copilot prompt, the **counts** from `INSTALL.md`, the **Foundations** from `pack/knowledge/*.md` (grouped by `tools/docs-portal-editorial.json`), the **Architecture** from `docs/architecture*.md` + `docs/adr/` + `docs/specs/` + `docs/design/`, the **UI examples** from `docs/mockups/`, and the **Graph** from `docs/docs-index.js`. The generator is **re-run by `sync-pack.ps1`** on every pack change, and **`check-consistency.py` drift-gates it** (it regenerates and asserts byte-identical output, so a stale portal is a failing build, not a matter of discipline). Therefore **adding a skill, a knowledge doc, an ADR, a spec, or a design automatically appears in the portal** on the next generation — nothing to hand-edit. When you change any of those sources, run `pwsh tools/sync-pack.ps1` (or `python tools/build-docs-portal.py`) and commit `docs/portal/portal-data.js` with it. Editorial framing (getting-started, capability cards, per-skill when/produces/handoff, the knowledge-doc grouping) lives in `tools/docs-portal-editorial.json`; the HTML shell `docs/portal/index.html` is stable.

`web/ai-forward-pack-explainer.html` is a self-contained interactive explainer — published to
GitHub Pages at **https://timianmalloo.github.io/ai-forward/** (or open the file directly in a
browser) — covering the knowledge constitution, the Rigor Protocol, the persona council, the
fourteen reasoning skills, the /auditlog and prompt-log utilities, and the UI archetype grammar — including a table of every template type and linkable,
rendered mockups of each. The full knowledge graph is browsable at [`docs/index.html`](docs/index.html)
(the Docs Explorer), and the architecture of record is in [`docs/architecture.md`](docs/architecture.md).
Both are generated and maintained by the `/document` skill.

## License

[Apache-2.0](LICENSE).
