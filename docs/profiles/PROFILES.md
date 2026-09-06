---
id: session-profiles
title: "Session profiles"
type: doc
status: accepted
owner: "@timianmalloo"
tags: [profile, session-profiler, index]
links:
  - { to: design-session-profiler, rel: relates-to }
review-by: "2027-03-05"
summary: >-
  Index of /session-profiler runs - each row is one measured pass over the harness telemetry, mined by /dream as findings.
---

# Session profiles

*Each row is one measured pass over the harness telemetry (`session-profile.py`). Mined by `/dream` as findings.*

| id | generated | repos | sessions | findings | top |
|---|---|---|---|---|---|
| [sp-0001](sp-0001/profile.md) | 2026-09-05T20:09:26Z | theterrace, ai-forward | 23 | 84 | SP-01, SP-09, SP-02 |
| [sp-0002](sp-0002/profile.md) | 2026-09-06T19:08:41Z | ai-de, cfd-bench, theterrace | 48 | 274 | SP-01, SP-09, SP-01 |

*sp-0003, sp-0004 and sp-0005 are the **same twelve sessions** re-measured as each new detector landed — SP-19 (main-line dominance) in sp-0004, SP-20 (late addition on an unbounded turn) in sp-0005. The earlier rows are kept rather than deleted: a profile is a record of what the instrument could see on the day, and the arrival of a finding is itself part of the history. **Read sp-0005 for these sessions; the others are superseded.**

*sp-0002's SP-09 counts were measured with the CTX-J detector defect present and are corrected in place at the top of its findings table; not re-measured.*
| [sp-0003](sp-0003/profile.md) | 2026-09-06T22:11:11Z | theterrace | 12 | 36 | SP-01, SP-02, SP-03 |
| [sp-0004](sp-0004/profile.md) | 2026-09-06T22:23:12Z | theterrace | 12 | 37 | SP-01, SP-02, SP-03 |
| [sp-0005](sp-0005/profile.md) | 2026-09-06T22:56:36Z | theterrace | 12 | 38 | SP-01, SP-02, SP-03 |
