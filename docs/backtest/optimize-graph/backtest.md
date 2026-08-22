---
id: backtest-optimize-graph
title: "optimize-graph back-test — twelve real prompts replanned"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "execution-optimization"
tags: [optimize-graph, back-test, evaluation, execution-graph, cost-vs-delivery]
links:
  - { to: kb-graph-and-loop-engineering, rel: depends-on }
  - { to: audit-log, rel: relates-to }
review-by: "2027-02-18"
summary: >-
  Back-test of the /optimize-graph skill against twelve real prompts drawn from 750 committed audit
  entries across TheTerrace, meridian-finance-planner and HealthWatch. Reports modeled time and token
  indices alongside rubric-scored completeness and rigor, with an explicit measured-vs-modeled
  integrity split — session timings in those logs span days of human-paced work and are therefore not
  execution times. Headline: completeness +14.8 pts, rigor +9.4 pts, and no case lost either.
---

# optimize-graph back-test

**The report is the HTML.** Open [`index.html`](./index.html) over `file://`; the data it renders is
`backtest-data.js` (`window.BACKTEST`). Both are dependency-free — no build, no CDN, no network.

## What this is

Twelve real prompts, quoted verbatim from the committed audit logs of three repositories, replanned
as execution graphs under `knowledge/execution-graph-optimization.md` (GO1–GO18) and compared against
what actually happened.

| | |
|---|---|
| **Corpus** | 750 audit entries — TheTerrace 372 · meridian-finance-planner 320 · HealthWatch 58 |
| **Multi-step share** | 481 / 750 = **64%** (269 single-step, which is the skip path) |
| **Cases** | 12 — four per repo, spanning small/simple to large/complex, including four with a non-success outcome |

## Headline results

| Metric | Result | Kind |
|---|---|---|
| Time to execute | **−34.3%** mean (−45.8% across the 9 cases that changed) | **modeled** — span ratio |
| Token usage | **−4.5%** mean | **modeled** — context-loads |
| Completeness | **+14.8 pts** | rubric, anchored on the measured outcome field |
| Rigor | **+9.4 pts** | rubric |
| Cases where rigor fell | **0 of 12** | the constraint the skill exists to honour |
| Cases where completeness fell | **0 of 12** | " |

**The token figure is small on purpose.** Parallelism does not reduce tokens — every branch still
loads its context. Only *collapsing* nodes and *avoiding rework* do. A back-test claiming a large
token saving from parallelism would be wrong.

## Integrity — what is measured and what is modeled

- **Verified (measured):** prompt text, summary, outcome, artifact count, skill, repo, entry id — quoted from `docs/audit/audit-log.jsonl` in each repo.
- **Inferred (derived):** the naive node list and the dependency edges, read from each summary. The *shape* is load-bearing; the exact node integer is not.
- **Inferred (modeled — NOT measured):** every time and token figure. **These logs contain no per-prompt timing or token data.** Session ids span days of human-paced work (mean ~55 h, median ~21 h), so session elapsed time is not execution time. Reporting it as duration would be the RIG-E error — treating an observation as conformance.

## The three cases that matter most

1. **meridian `al-0058` — prevention.** Five parallel model calls with no cap and no retry tripped 429/529 and failed a whole advisor panel. GO7's five-part fan-out contract mandates exactly the fix that was eventually applied (cap 2 + retry-with-backoff), so the nine-node investigation would not have existed.
2. **meridian `al-0310` — the largest completeness gain (+48).** Fourteen FRs fanned out with no per-branch exit condition; four ended open and four partial, reconciled afterwards in a backlog addendum. The defect is a join that cannot tell done from partial, not the fan-out.
3. **HealthWatch `al-0003` — the honesty case.** A ten-track parallel research run. `/optimize-graph` produces essentially the same plan, so the time gain is ~zero. Its only finding is a risk: it ran **ten wide with no cap**, and the meridian panel failed at **five**.

## Reproducing and verifying

```bash
# render proof (E11) - executes the page's real inline script against a DOM shim
node tools/verify-backtest-render.js        # -> VERDICT: MOUNTED, exit 0

# the PACK-G syntax gate now also covers docs/backtest/*/index.html
python tools/check-consistency.py
```

Both controls were **observed failing** on deliberately broken input before being trusted (CI6):
corrupting `backtest-data.js` drives the render proof to exit 1, and a syntax error in the inline
script is reported by the consistency gate as a PACK-G finding.

## Limits

The rubric scores are judgement, not instrumentation; Q1/Q4 in
`docs/knowledge/graph-and-loop-engineering/open-questions.md` name exactly this gap. The way to
replace the model with measurement is GO18 — record planned vs actual on real `/optimize-graph` runs
until the granularity and fan-out constants are measured rather than assumed.
