# evals/ — regression testing the pack itself

The pack's skills, prompts, and knowledge docs are **prompt-code**: behavior-bearing assets
whose edits can silently regress behavior the same way code edits can. This folder is their
regression suite. It is **pack-maintenance tooling** — it does not deploy to target repos.

## The model

Each case in `cases/*.json` is a **golden task**: a realistic prompt for one skill, optional
workspace `setup` files, and a list of **objective assertions** about the repository state
after the skill ran — the trajectory's observable footprint, not a vibe:

- the artifact exists, in the right home, with **valid frontmatter** (checked by the same
  parser the script bundle uses);
- the directives left their fingerprints (`grep` for the failure-mode table, the STRIDE
  section, the phased plan, `review-by`, …);
- the graph is coherent (`index-has`, `docs-graph.py validate` exits 0, `freshness` clean).

Where judgment is required beyond these checks (is the summary *real*? is the design *good*?),
gate with human review or an LLM-as-judge rubric built from the skill's own **Definition of
done** — the DoD checklists are the rubrics; they already exist.

## Running

```bash
# 1. seed a fresh workspace (copies setup files, prints the golden prompt)
python3 evals/run-evals.py --case evals/cases/design-01-gateway.json --workspace /tmp/eval-ws --setup
# 2. run the skill against the workspace (Claude Code / Copilot — paste the printed prompt;
#    or wire a headless CLI in your own harness)
# 3. assert
python3 evals/run-evals.py --case evals/cases/design-01-gateway.json --workspace /tmp/eval-ws --check
```

`--check` over all cases (`--cases evals/cases`) exits nonzero on any failure — CI-able once
you record workspaces or wire headless execution.

## Cadence (industry-standard shape)

- **On every pack edit** (a skill, prompt, or knowledge doc changes): run the affected skill's
  cases. A small set surfaces regressions early — 10–20 per skill is the working target; the
  one starter case per skill here is the floor, not the suite.
- **On model-version changes**: run everything — model updates cause subtle behavioral drift
  across many task types at once.
- **Compare trajectories, not just outcomes**: re-running a case before and after a pack edit
  and diffing which assertions moved tells you whether you improved the skill or just changed it.

## Growing the suite

Promote real sessions into cases: when a skill run goes wrong in practice, freeze the prompt
and the workspace seed, write the assertion that would have caught it, and commit the case —
the same way a production defect becomes a regression test. Keep cases independent and
deterministic; anything time-sensitive uses relative dates.
