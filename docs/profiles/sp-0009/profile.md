---
id: profile-sp-0009
title: "Session profile sp-0009 - ai-forward"
type: doc
status: accepted
owner: "@timianmalloo"
tags: [profile, session-profiler, efficiency, adherence]
links:
  - { to: design-session-profiler, rel: relates-to }
review-by: "2026-12-18"
summary: >-
  Measured pass over 3 session(s) in ai-forward (last 2 days); 9 finding(s), top: SP-01, SP-07, SP-24.
---
# Session profile sp-0009

*Generated 2026-09-19T17:43:07Z by `session-profile.py`. Every number is read from the harness's own store unless marked est. (chars/token = 3.54). A missing measurement reads `not recorded`, never a guess (IO8).*

**Repos:** ai-forward  
**Window:** last 2 days  
**Sessions:** 3 (claude)

## Findings

| id | severity | confidence | finding | session | evidence | fix |
|---|---|---|---|---|---|---|
| SP-01 | Major | Verified | Context accretion: the main conversation grew past the point where every step re-reads a book | claude:2eb8c619 | t1: context 388,302 -> 442,306 tokens over 10 main requests; t2: context 443,492 -> 490,525 tokens over 12 main requests; t3: context 491,594 -> 501,689 tokens over 7 main requests | F-09, F-01 |
| SP-07 | Major | Verified | Sub-agent runaway: a delegation past a sane tool-call/token budget, or one the parent had to tell to converge | claude:2eb8c619 | t0: Research p2p coordination protocols: 57 tool calls, 1,712,806 tokens, 900s; t0: Research distributed job scheduling: 54 tool calls, 1,359,509 tokens, 905s; t0: Research agentic coordination frameworks: 48 tool calls, 2,458,062 tokens, 923s | F-04 |
| SP-24 | Major | Verified | Gate status behind a pipe: a verify/test run piped into tail/head/grep with no pipefail | claude:2eb8c619 | t4: gate piped: python3 -m pytest -q -x tests/docs_explorer/test_run_evals.py::RunEvalsCommandTests::test_; t4: gate piped: python3 -m pytest -q -x -s tests/docs_explorer/test_audit_selfcheck.py::SelfcheckTests::te; t5: gate piped: python3 -m pytest -q tests/docs_explorer/test_cross_platform_controls.py 2>&1 / grep -E '^ | F-20 |
| SP-09 | Major | Inferred | No goal state: a substantive turn whose first reply carries no Goal / Done when | claude:2eb8c619 | t1: 'continue when the research agents finish' - first reply has no Goal / Done when; t2: 'keep going while i review the proposal' - first reply has no Goal / Done when; t3: 'rebase then push and commit all' - first reply has no Goal / Done when | F-03 |
| SP-07 | Major | Verified | Sub-agent runaway: a delegation past a sane tool-call/token budget, or one the parent had to tell to converge | claude:94c2bb72 | t0: Mine ai-forward coordination state: 65 tool calls, 3,308,985 tokens, 443s; t0: Mine ai-de coordination corpus: 58 tool calls, 4,023,117 tokens, 567s | F-04 |
| SP-25 | Minor | Verified | Failed heredoc runs: a multi-line program passed through the shell and burned the request | claude:2eb8c619 | t9: heredoc failed: 48:/ AC-6 / Claude Code — Message your other Claude Code sessions / official / https://cod | F-21 |
| SP-17 | Nit | Verified | Reasoning visibility: the share of billed reasoning that came back as readable text | claude:2eb8c619 | 160,418 reasoning tokens billed on the main line; 248,565 chars of reasoning text on disk (~44% visible at 3.54 chars/token) | F-12 |
| SP-17 | Nit | Verified | Reasoning visibility: the share of billed reasoning that came back as readable text | claude:94c2bb72 | 13,688 reasoning tokens billed on the main line; 27,551 chars of reasoning text on disk (~57% visible at 3.54 chars/token) | F-12 |
| SP-17 | Nit | Verified | Reasoning visibility: the share of billed reasoning that came back as readable text | claude:3bf030a6 | 500 reasoning tokens billed on the main line; 0 chars of reasoning text on disk (~0% visible at 3.54 chars/token) | F-12 |

## Fixes (the pack surfaces that own the controls)

| fix | what | where in the pack | control that fails on recurrence | findings |
|---|---|---|---|---|
| F-09 | Session hygiene: a new task starts a new session; tier and effort are per phase | knowledge/session-worktree-discipline.md WT1a; INSTALL.md (Copilot); pack-doctor `copilot settings` | pack-doctor WARNs on long_context + high effort as global defaults; this profiler flags context accretion | SP-01 |
| F-01 | CLAUDE.md is an `@AGENTS.md` import, not a copy | adapters/managed-blocks/CLAUDE.block.md; INSTALL.md 1.1; pack-doctor `claude-md import` | pack-doctor FAILs a repo whose CLAUDE.md carries the managed block beside an AGENTS.md that carries it too | SP-01 |
| F-04 | Every delegation carries a tool-call budget and a convergence condition | knowledge/execution-graph-optimization.md GO7; agent cards; audit `agent_runs` | a sub-agent past its budget stops and reports; the audit entry records calls vs budget | SP-07 |
| F-20 | A gate's exit status is never behind a pipe | adapters/managed-blocks/AGENTS.block.md (the shell rule beside CT26); scripts/run-verify-gates.py; scripts/conductor-join.py | SP-24 counts gate runs piped into tail/head/grep with no pipefail, and the subset that commit/merge/push on the same line | SP-24 |
| F-03 | Declare tier and fan-out cap in the goal state; record them in the audit entry | knowledge/communication-and-task-discipline.md CT19; scripts/audit-log.py --tier/--fan-out; /dream PACK-O miner | audit selfcheck + /dream flag a substantive turn with no tier, or a fan-out above the tier cap with no named hard gate | SP-09 |
| F-21 | A multi-line program is a file, then a run - never a heredoc | adapters/managed-blocks/AGENTS.block.md; commands/execute-with-coordination (the brief) | SP-25 counts failed heredoc runs (unexpected EOF, unterminated string, invalid escape) | SP-25 |
| F-12 | Ask each host for its richest reasoning summary, and treat summary-derived judgements as Inferred | INSTALL.md 1.6; adapters/hooks/claude-code.settings.hooks.json (showThinkingSummaries); pack-doctor `claude settings` | SP-17 reports visible-reasoning share per family; a family under 10% marks every text-derived drift finding Inferred | SP-17 |

## Model family x harness (the tuning view)

| family | harness | turns | req/turn | cache-read/turn | out/turn | reasoning/turn | reasoning visible | effort | intent trace | cost/turn (AIU) | ttft p90 (median) | ctx end (median) | wall s/turn | drift/turn |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anthropic | claude | 13 | 21.8 | 13,512,644 | 51,466 | 11,599 | 43.6% | not recorded | 100.0% | not recorded | not recorded | 490,525 | 1072 | 1.62 |
| anthropic+other | claude | 2 | 17.5 | 8,482,500 | 53,316 | 11,908 | 51.7% | not recorded | 100.0% | not recorded | not recorded | 39,871 | 1072 | 3.0 |

*drift/turn = sub-agents + re-reads + skill repeats + missing goal state + fan-out without tier + converge nudges + cap firings, per turn. reasoning visible = reasoning text on disk as a share of billed reasoning tokens (est.); below 10% every text-derived drift judgement is Inferred. effort = the host's recorded reasoning effort (Copilot) or not recorded (Claude Code). intent trace = shell calls carrying a one-line description.*

## claude session `2eb8c619` — Agentic coordination proposals evaluation

started 2026-09-19T04:54:56Z · updated 2026-09-19T17:42:55Z · cwd `/Users/mallalieut/projects/ai-forward` · prefix not recorded · compactions 1

**Cost, in the units that are measured.** requests: main 284 · sub-agents 510; tokens: cache-read 181,310,320 · cache-write 3,981,362 · uncached in 10,736 · output 712,396; quota: not recorded; if API-billed: est. $122.57 (list rates cached 2026-06-24; 1 request(s) had no rate row and are unpriced); harness cost record: not recorded.

| turn | prompt | family | main req | ctx start | ctx end | cache read | output | cost AIU | ttft p90 | wall s | subs | re-reads | goal | tier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | evaluate the two proposals on agentic coordinati | anthropic+other | 33 | 58,504 | 0 | 16,943,514 | 105,706 | not recorded | not recorded | 2112 | 6 | 0 | yes | yes |
| 1 | continue when the research agents finish | anthropic | 10 | 388,302 | 442,306 | 3,875,424 | 51,663 | not recorded | not recorded | 669 | 0 | 0 | no | no |
| 2 | keep going while i review the proposal | anthropic | 12 | 443,492 | 490,525 | 5,605,127 | 29,933 | not recorded | not recorded | 447 | 0 | 0 | no | no |
| 3 | rebase then push and commit all | anthropic | 7 | 491,594 | 501,689 | 3,470,528 | 7,284 | not recorded | not recorded | 207 | 0 | 0 | no | no |
| 4 | in a separate work tree analyze the repo in term | anthropic | 23 | 502,356 | 628,820 | 29,141,885 | 91,271 | not recorded | not recorded | 1198 | 4 | 0 | yes | yes |
| 5 | approve P0 and P1, commit, rebase and push | anthropic | 48 | 629,981 | 821,645 | 36,517,395 | 107,438 | not recorded | not recorded | 2578 | 0 | 0 | no | no |
| 6 | keep going then commit and push all when its com | anthropic | 19 | 821,761 | 849,289 | 15,877,554 | 15,083 | not recorded | not recorded | 682 | 0 | 0 | no | no |
| 7 | keep going with P2 and P3 | anthropic | 16 | 850,224 | 937,416 | 22,554,637 | 60,848 | not recorded | not recorded | 962 | 2 | 0 | no | no |
| 8 | great lets go back to the work we were doing bef | anthropic | 3 | 937,992 | 940,417 | 2,817,267 | 1,828 | not recorded | not recorded | 240 | 0 | 0 | no | no |
| 9 | question answers here: 1: Ledger tracking defaul | anthropic | 34 | 940,842 | 157,330 | 10,163,674 | 64,652 | not recorded | not recorded | 1478 | 1 | 0 | no | no |
| 10 | keep going with best next action | anthropic | 27 | 169,482 | 275,132 | 7,273,340 | 57,733 | not recorded | not recorded | 1488 | 1 | 0 | yes | yes |
| 11 | commit and push all lets get main and origin ali | anthropic | 50 | 276,720 | 461,076 | 26,146,786 | 117,622 | not recorded | not recorded | 2847 | 2 | 0 | yes | yes |
| 12 | do the worktree clean up now then /session-profi | anthropic | 2 | 462,147 | 467,637 | 923,189 | 1,335 | not recorded | not recorded | 15 | 0 | 0 | no | no |

### Nodes (the sub-agent store: 16 agent file(s); 16 agent(s))

| node | type | depth | model | span s | req | tools | reviews | cache read | output | ctx max | resumes | longest wait | if API-billed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ground ai-de coordination state | Explore | 1 | claude-opus-5 | 272 | 21 | 36 | 0 | 1,505,710 | 428 | 123,362 | 1 | — | est. $1.53 |
| Ground ai-forward coord layer | Explore | 1 | claude-opus-5 | 311 | 25 | 42 | 0 | 2,371,790 | 1,981 | 160,950 | 1 | — | est. $2.21 |
| Research agentic coordination frameworks | domain-researcher | 1 | claude-opus-5 | 923 | 27 | 48 | 0 | 2,266,275 | 2,663 | 189,072 | 1 | — | est. $2.38 |
| Research p2p coordination protocols | domain-researcher | 1 | claude-opus-5 | 900 | 25 | 57 | 0 | 1,565,344 | 3,504 | 149,271 | 1 | — | est. $1.77 |
| Research distributed job scheduling | domain-researcher | 1 | claude-opus-5 | 905 | 19 | 54 | 0 | 1,219,599 | 775 | 144,460 | 1 | — | est. $1.50 |
| Research quorum and leader election | domain-researcher | 1 | claude-opus-5 | 671 | 21 | 44 | 0 | 1,011,273 | 2,758 | 95,831 | 1 | — | est. $1.14 |
| Review pack scripts cross-platform | Explore | 1 | claude-opus-5 | 516 | 59 | 58 | 0 | 5,021,768 | 22,113 | 151,075 | 1 | — | est. $4.01 |
| Review tools, hooks, CI cross-platform | Explore | 1 | claude-opus-5 | 309 | 29 | 52 | 0 | 1,776,492 | 859 | 113,713 | 1 | — | est. $1.59 |
| Review skills and docs commands | Explore | 1 | claude-sonnet-5 | 367 | 63 | 62 | 0 | 5,449,541 | 8,585 | 150,510 | 1 | — | est. $1.55 |
| Mine ai-de Windows evidence | Explore | 1 | claude-sonnet-5 | 279 | 42 | 41 | 0 | 4,013,507 | 7,649 | 142,080 | 1 | — | est. $1.22 |
| P2 encoding sweep (file set A) | python-developer | 1 | claude-opus-5 | 559 | 51 | 58 | 0 | 5,329,838 | 6,080 | 152,983 | 1 | — | est. $3.77 |
| P3 newline sweep (file set B) | python-developer | 1 | claude-opus-5 | 571 | 36 | 48 | 0 | 2,917,053 | 9,290 | 119,460 | 1 | — | est. $2.33 |
| Survey skill delegation shapes | Explore | 1 | claude-opus-5 | 191 | 15 | 38 | 0 | 1,358,669 | 108 | 177,297 | 1 | — | est. $1.79 |
| Adversary review of compile-stage spec | test-architect | 1 | claude-fable-5-1 | 512 | 15 | 13 | 0 | 1,202,625 | 1,434 | 113,443 | 2 | — | est. $1.79 |
| Track A: compile engine, gate, templates | python-developer | 1 | claude-fable-5-1 | 902 | 28 | 53 | 0 | 3,358,285 | 5,438 | 187,816 | 1 | — | est. $3.47 |
| Track B: audit fields, /compile skill | python-developer | 1 | claude-fable-5-1 | 627 | 34 | 48 | 0 | 3,486,601 | 5,305 | 147,511 | 1 | — | est. $2.78 |

*if API-billed = tokens x first-party list rates cached 2026-06-24; the operator on a subscription pays quota, not this.*

## claude session `94c2bb72` — 

started 2026-09-18T15:07:12Z · updated 2026-09-19T04:50:19Z · cwd `/Users/mallalieut/projects/ai-forward` · prefix not recorded · compactions 0

**Cost, in the units that are measured.** requests: main 33 · sub-agents 109; tokens: cache-read 11,297,568 · cache-write 471,853 · uncached in 1,040 · output 62,376; quota: not recorded; if API-billed: est. $11.09 (list rates cached 2026-06-24; 0 request(s) had no rate row and are unpriced); harness cost record: $15.05.

| turn | prompt | family | main req | ctx start | ctx end | cache read | output | cost AIU | ttft p90 | wall s | subs | re-reads | goal | tier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | <command-message>dream</command-message> <comman | anthropic | 33 | 60,345 | 192,672 | 11,297,568 | 62,376 | not recorded | not recorded | 1137 | 3 | 0 | yes | yes |

### Nodes (the sub-agent store: 3 agent file(s); 3 agent(s))

| node | type | depth | model | span s | req | tools | reviews | cache read | output | ctx max | resumes | longest wait | if API-billed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Mine ai-de coordination corpus | domain-researcher | 1 | claude-opus-5 | 567 | 51 | 58 | 0 | 3,891,146 | 9,511 | 122,360 | 1 | — | est. $2.95 |
| Survey other pack-consuming repos | Explore | 1 | claude-sonnet-5 | 142 | 13 | 19 | 0 | 476,913 | 889 | 55,096 | 1 | — | est. $0.24 |
| Mine ai-forward coordination state | Explore | 1 | claude-opus-5 | 443 | 45 | 65 | 0 | 3,177,584 | 4,940 | 126,373 | 1 | — | est. $2.50 |

*if API-billed = tokens x first-party list rates cached 2026-06-24; the operator on a subscription pays quota, not this.*

## claude session `3bf030a6` — Re-login fix

started 2026-09-18T14:08:35Z · updated 2026-09-18T14:09:36Z · cwd `/Users/mallalieut/projects/ai-forward` · prefix not recorded · compactions 0

**Cost, in the units that are measured.** requests: main 2 · sub-agents 0; tokens: cache-read 21,487 · cache-write 18,382 · uncached in 2 · output 926; quota: not recorded; if API-billed: est. $0.15 (list rates cached 2026-06-24; 1 request(s) had no rate row and are unpriced); harness cost record: $0.22.

| turn | prompt | family | main req | ctx start | ctx end | cache read | output | cost AIU | ttft p90 | wall s | subs | re-reads | goal | tier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | why wasnt fable available as a choice | anthropic+other | 2 | 0 | 39,871 | 21,487 | 926 | not recorded | not recorded | 32 | 0 | 0 | no | no |
| 1 | it worked after i re-logged in | — | 0 | not recorded | not recorded | 0 | 0 | not recorded | not recorded | — | 0 | 0 | no | no |

## Confirmation pass (the reasoning step, 2026-09-19 — coordinator session 2eb8c619)

**Question asked:** did the two-track division of the compile-stage implementation pay, by the profiler's measure?

### The compile-stage window (turn 11, nodes "Track A" and "Track B")
| measure | Track A (python-developer) | Track B (python-developer) | coordinator main line, turn 11 |
|---|---|---|---|
| span | 902 s | 627 s | 2,847 s wall, 50 requests |
| requests · tool calls | 28 · 53 | 34 · 48 | 50 · — |
| cache read · output tokens | 3,358,285 · 5,438 | 3,486,601 · 5,305 | 26,146,786 · 117,622 |
| context max | 187,816 | 147,511 | 276,720 → 461,076 (turn start → end) |
| if API-billed | est. $3.47 | est. $2.78 | not recorded |
| declared budget · used | 90 calls / 90 min · 53 calls / 15 min | 70 calls / 60 min · 48 calls / 10.5 min | main-line 60 · 44 recorded |

**Verdict (Verified from the store):** the two nodes ran concurrently — their spans overlap entirely inside turn 11 — so the delegated work took 902 s of wall instead of 1,529 s serial, a 41% saving on that part. Both stayed under half their declared budgets, and neither was nudged to converge (`converge_nudges: 0`). **The coordinator's own line dominated the turn**: 2,847 s wall against 902 s of track time, because the design (≈ 20 min), the plan, two joins by script, the counts and gates ran serially on the main line. The tokens the division cost — two nodes at ≈ 3.4 M cache-read each — are roughly a quarter of the main line's 26 M for the same turn, so the "3× multiplier" the plan stated was **not observed**; the measured shape is closer to 1.3× on tokens. A single-session alternative was not run, so there is no like-for-like baseline: the token comparison is against the coordinator's own line, labelled as such.

**What the division bought, measured:** isolation (each node's context max stayed under 190 k while the main line ended at 461 k), and zero refused decisions, zero edits outside a lease, two coordinator-raised seams both applied. **What it did not buy:** wall clock on the whole turn — the serial spine (design → plan → join → join → gates) is where the minutes went.

### Findings confirmed or struck
| id | verdict | evidence read |
|---|---|---|
| SP-01 context accretion | **confirmed** — this session carried five tasks (proposal, cross-platform, spec, design, implementation) across 13 turns; context 388 k → 940 k before the one compaction at turn 9, then 157 k → 467 k after it | turn table; WT1a says a new task starts a new session — the coordinator kept one |
| SP-07 sub-agent runaway | **confirmed for turn 0 only** (four research nodes at 48–57 tool calls, 1.4–2.5 M tokens, ≈ 900 s each, no budget declared at the time); **not present in the compile-stage window** — the two contracted nodes returned under budget, which is F-04 working | nodes table |
| SP-24 gate behind a pipe | **confirmed** for turns 4–5 (cross-platform work: pytest piped into tail/grep); the landing scripts of turns 10–11 read every gate's exit on its own line | evidence strings |
| SP-09 no goal state (Inferred) | **confirmed on all four flagged turns** by opening the transcript: t1 "All four research agents have finished…", t2 "Continuing with the cheap remaining items…", t3 "Committing in three reviewable commits…", t12 "Running the fail-safe cleanup…" — none opens with Goal / Done when. Classification: t1–t3 *legitimate continuation* of a goal set in the prior turn, still a CT19 miss; t12 a two-command T0 turn, still a miss | `first-replies.py` over the session jsonl |
| SP-25 failed heredoc | **confirmed** (turn 9, one failed `python3 - <<'PY'` run); the coordinator used heredoc-shaped patches repeatedly this session and the worktree guard refused several — class SHELL-A | evidence string; guard refusals in turns 9–11 |
| SP-17 reasoning visibility (44%) | **struck as a tuning matter** — changes no guidance this run; F-12 already covers it | — |
| SP-14 family drift | **not raised**: the second family has 2 turns; the rule needs ≥ 3 comparable turns per family | compare table |
| SP-15 overlapping sessions | **reconciled**: sessions 2eb8c619 and 94c2bb72 share the launch cwd but wrote in separate worktrees; the two tracks ran in their own trees (`coord worktree new`), removed after the join | `coord worktree list` before cleanup |

### Fixes (from the catalog; no new surface needed)
| fix | closes | control that fails on recurrence | how it was observed |
|---|---|---|---|
| F-09 session hygiene (WT1a) | SP-01 | SP-01 re-flags a session whose context grows past the book point; pack-doctor `copilot settings` | this profile |
| F-03 goal state on every substantive turn | SP-09 | SP-09 / `/dream` PACK-O miner on `done_when` presence | four turns confirmed |
| F-04 budget + convergence on every delegation | SP-07 (turn 0) | SP-07 re-flags an unbudgeted node; the contracted nodes of turn 11 show the control holding | nodes table |
| F-20 gate status never behind a pipe | SP-24 | SP-24 count | turns 4–5 |
| F-21 a multi-line program is a file, then a run | SP-25 | SP-25 count; the worktree guard's refusal | turn 9 |

### Per-family tuning notes
anthropic / claude, 13 turns: drift 1.69 per turn, entirely `sub_agents` (13) and `no_goal` (9) — no re-reads, no skill repeats, no nudges. The tuning is not a model setting: it is the coordinator writing the goal state first on continuation turns, and ending a session at a task boundary. No SP-14 claim (second family under the turn floor).

### Coordination notes
Two tracks, two trees, both removed by the fail-safe cleanup after the join; the stray `spec/compile-stage` tree removed the same way once the primary's `main` caught up. Sessions ended from inside their trees. Residual: `coord worktree cleanup` still reads "not on main" for squash-landed work — the linear-history rule and the ancestry check disagree by design; `--include-unmerged` is the documented override.
