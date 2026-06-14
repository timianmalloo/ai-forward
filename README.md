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

For the pack's own story — why it exists, what's inside, how to use the ten skills — read
[`pack/README.md`](pack/README.md) and [`pack/OVERVIEW.md`](pack/OVERVIEW.md).

## Layout

```
ai-forward/
├─ pack/                  ← CANONICAL SOURCE — edit here to expand the pack
│   ├─ README.md  OVERVIEW.md  research-synthesis.md
│   ├─ knowledge/         ← the reasoning spine + 23-persona roster + vendored foundation
│   ├─ commands/          ← the 10 skills (one SKILL.md each)
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

The pack is already installed, so in Claude Code here you can just run the skills — they apply
automatically by description, or call one explicitly:

```
/collectknowledge → /adddomainexperts → /specify → /define-architecture → /design → /implement → /document
                                                                              ↑
                                                            /investigate  (whenever a defect appears)
```

`/adopt` brings a brownfield repo into the pack; `/migrate` runs characterization-first
refactors. The natural order and what each skill produces are in [`pack/OVERVIEW.md`](pack/OVERVIEW.md).

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

`web/ai-forward-pack-explainer.html` is a self-contained interactive explainer (open it directly
in a browser) covering the knowledge constitution, the Rigor Protocol, the persona council, the
ten skills, and the UI archetype grammar — including a table of every template type and linkable,
rendered mockups of each. The full knowledge graph is browsable at [`docs/index.html`](docs/index.html)
(the Docs Explorer), and the architecture of record is in [`docs/architecture.md`](docs/architecture.md).
Both are generated and maintained by the `/document` skill.

## License

[Apache-2.0](LICENSE).
