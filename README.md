# AI-Forward

The development home of the **AI-Forward Pack** — a repository-droppable extension that turns
the Agent Knowledge Pack's adversarial reviewer council into a working swarm: collaborating
peers that *author*, adversarial personas that *attack*, and a staged reasoning discipline (the
**Rigor Protocol**) that slows the rush to a plausible answer and replaces it with evidence at
every step. It works with **Claude Code**, **GitHub Copilot**, **Grok Build**, **Antigravity**, **Codex**, or any combination.

This repo is two things at once:

1. **The canonical source** for the pack — everything you edit to expand it lives in [`pack/`](pack/).
2. **A live install of the pack** — the pack is installed into this repo (`.claude/`, `.github/`,
   `.grok/`, `.agents/`, `docs/`) so the skills, agents, and knowledge are active in Claude Code, Copilot,
   Grok Build, Antigravity, and Codex *while you work on the pack itself*. Dogfooding: the pack is built using the pack.

For the pack's own story — why it exists, what's inside, how to use the thirty skills — read
[`pack/README.md`](pack/README.md) and [`pack/OVERVIEW.md`](pack/OVERVIEW.md).

For a newcomer-oriented learning path, use the
[AI-Forward handbook](https://timianmalloo.github.io/ai-forward/docs/portal/index.html).
It starts with the problems the pack addresses, then walks through adoption,
engineering practice, coordination, and the complete skill reference.
The handbook's canonical content is `web/handbook/`; `tools/build-handbook.py`
generates the public reader and its documentation-graph copies.

**Codex users:** invoke `$collectknowledge` or `$specify` (CLI/IDE: `/skills` or `$`).
Skills live in `.agents/skills/`; `AGENTS.md` supplies project instructions.
See the [Codex setup and troubleshooting guide](docs/ai-forward-pack/codex.md).

## Start with one outcome

Install once, then describe the result you want. You do not need to clone AI-Forward
or learn its workflow sequence first. Start with a small change you can review.

The standard setup installs the upstream `main` version. You need [Git](https://git-scm.com/downloads),
[uv](https://docs.astral.sh/uv/getting-started/installation/), network access and a
supported coding app with its own account/model access.

### 1. Install in your project

Open a terminal in the project you want to work on, then copy this one line. It works
in Windows PowerShell/Command Prompt and macOS/Linux terminals, with Git and uv on
PATH. A project without Git is welcome too; setup will not initialize it for you.

```text
uv run --no-config --no-project --script https://raw.githubusercontent.com/timianmalloo/ai-forward/main/bootstrap.py
```

No `--repo` or `--ref` is needed: setup already defaults to this upstream repository
and `main`. For unmerged changes, see [testing a contribution](#test-unmerged-changes).

Success reports `AI-Forward installed`, `AI-Forward updated` or
`AI-Forward already current`, with the revision and exact source commit. That means
the pack files are ready—not that a project task has been completed. Open this
project in your coding app and start a fresh chat so it can discover the new skill.

### 2. Ask for one result

In Claude Code or a coding app that exposes the installed `/deliver` entry point:

```text
/deliver Add CSV export for the current project and filter. Export every matching task, not only the visible page. Do not add scheduling or new roles.
```

This is a chat request, not a terminal command. Replace the example with a task in
your project. Say what correct behavior looks like and what must stay unchanged.

| Coding app | How to start |
|---|---|
| Claude Code | `/deliver <your task>` |
| Codex | `$deliver <your task>`; use `/skills` or `$` to find installed skills |
| Copilot CLI | Find `deliver` with `/skills`, then `/deliver <your task>`. You can also ask `Use the /deliver skill to <your task>`. If installed during a chat, use `/skills reload`, then `/skills info deliver`. |
| VS Code Copilot | Use `/deliver` when listed, or select/request the installed `deliver` skill. Agent Host sessions use skills, not the older prompt-file route. |
| Grok Build / Antigravity | Select or request the installed `deliver` skill by name using your app's skill support |

The agent chooses the needed workflows and continues through approved work. It does
not run every skill, map your entire repository or start a swarm by default.
Individual skills remain available when you want to direct a particular stage.

### 3. Review the result—or answer a necessary question

A useful handback shows changed files, checks that exercised your requested result,
any limits and any decision still needed. A plan or a passing test alone is not the
finish line. If 63 tasks match a filter but the page shows 20, the export must include
all 63. A test that serializes only the visible 20 does not prove that.

When a decision, permission or blocking review is needed, the agent explains what
is blocked, asks a specific question and saves its place with a task id. Reply in
the same chat. Your reply authorizes only the decision you actually answered; it
does not grant unrelated permissions or authorize deployment. A blocking review
requires the finding addressed and independently re-reviewed, not the author's own
approval.

In a fresh chat **in the same project**, use:

```text
/deliver resume <task-id>
```

Codex uses `$deliver resume <task-id>`; in Copilot CLI, ask it to use the `/deliver`
skill to resume that id. Replace `<task-id>` with the id the agent gave you.
The agent checks the saved request, project and evidence before reusing completed
work. If something changed, it explains what needs checking again rather than
silently starting over or inventing approval. Checkpoints are local; another clone
or computer does not automatically have them.

For a guided first task, read the [quick start](web/handbook/guides/get-started.md)
and [delivery guide](web/handbook/skills/deliver.md). Open `docs/portal/index.html`
locally for the searchable handbook built from this checkout.

### Setup options and safe stops

- **Preview:** append `--dry-run` to the setup line. It downloads/checks the source
  and shows the plan without writing to your project.
- **Repeat or update:** rerun the same line. Unchanged installed files stay current;
  newer source is reconciled against the installed version. Review the result.
- **Pin a version:** replace the branch in both the wrapper URL and `--ref` with
  the same full commit id. A branch can move; matching pins make a run reproducible.
- **Use local committed source:** `--source <clone-path>` uses a local Git clone's
  committed HEAD, not its uncommitted edits.

Setup does not change model/trust permissions, install project dependencies,
commit, push or deploy. If existing instructions, hooks, Git settings or checks
conflict, it stops and names the item for review. Keep the existing file and
reconcile the specific conflict; do not delete it or grant blanket permissions just
to make setup pass. Use a credential-free repository URL and Git's credential
helper, not a token in a URL.

Installing files is not proof that a model loaded or followed them. If `deliver`
is missing, check discovery before relying on it. The local progress helper checks
saved state; it does not authenticate a human decision or judge whether a result
meets the meaning of your request.

Manual reconciliation and source-clone installation are expert alternatives,
not additional onboarding steps. Source and version overrides are optional;
they do not belong in the normal setup command.

## Layout

```
ai-forward/
├─ pack/                  ← CANONICAL SOURCE — edit here to expand the pack
│   ├─ README.md  OVERVIEW.md  research-synthesis.md
│   ├─ knowledge/         ← the reasoning spine + 23-persona roster + vendored foundation
│   ├─ commands/          ← the 30 skills (SKILL.md + reference/ each)
│   ├─ templates/         ← the artifacts each skill produces
│   ├─ adapters/          ← INSTALL.md + Claude Code / Copilot agents + prompts + managed blocks
│   ├─ evals/             ← the pack's own regression suite
│   ├─ scripts/  ci/  examples/
│
├─ .claude/               ← GENERATED install (Claude Code reads this) — do not edit by hand
│   ├─ knowledge/  skills/  agents/
│
├─ .grok/                 ← GENERATED install (Grok Build reads this) — do not edit by hand
│   ├─ skills/  agents/  hooks/  rules/
│
├─ .agents/               ← GENERATED install (Antigravity reads this) — do not edit by hand
│   ├─ skills/  hooks.json  rules/  skills.json
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

`.claude/`, `.github/`, `.grok/`, `.agents/`, and `docs/` are **generated from `pack/`** and committed so a
fresh clone has a working install with no setup. `pack/` is the single source of truth — never
edit the generated copies directly; they're overwritten on the next sync.

## Using the pack (in this repo)

> **Running the scripts.** Commands are written `python3 <script>` (the POSIX name, matching every
> script's shebang). **On Windows use `python` or `py -3`** — python.org ships no `python3.exe`, and
> the `python3` you may see there is a Microsoft Store alias that is not Python (it prints *"Python
> was not found"* and exits `9009`). Run `pack-doctor.py` and its `python interpreter` check names
> the exact form for your machine. Full note: [`pack/adapters/INSTALL.md` §0](pack/adapters/INSTALL.md).

The pack is already installed, so in Claude Code here you can just run the skills — they apply
automatically by description, or call one explicitly:

```
/collectknowledge → /adddomainexperts → /create-proposal → /specify → /define-architecture → /design-slice → /implement → /document
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
4. Commit `pack/` **and** the regenerated `.claude/` + `.github/` + `.grok/` + `.agents/` + `docs/` together
   so source and install never drift. When you change the pack, also update the changelog in
   `pack/adapters/INSTALL.md` (bump `revision`) per the convention documented there.

## Sharing / distributing the pack

```powershell
pwsh tools/package-pack.ps1   # writes dist/ai-forward-pack.zip
```

Recipients can use the one-line setup above or drop the pack into their own repo by manual
reconciliation — the deployment map and update procedure are in [`pack/adapters/INSTALL.md`](pack/adapters/INSTALL.md). (`tools/sync-pack.ps1`
mirrors the Claude Code, Copilot, Grok Build, and Antigravity surfaces needed *here*; the distributable in
`pack/` carries the same wiring for consuming repos.)

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

### Test unmerged changes

Normal setup reads upstream `main`; it does not install an unmerged pull request.
The upstream launcher becomes available when the contribution adding it is merged.
Before then, reviewers can run the launcher from a committed local clone with
`--source <clone-path>`, or select a review source with `--repo <repository-url>`
and `--ref <branch-or-commit>`. Match the launcher to that same reviewed source.
These options are for reviewing contributions or choosing a version, not prerequisites
for using the released pack. No global Git settings or trust changes are needed.

## License

[Apache-2.0](LICENSE).
