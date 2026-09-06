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

*sp-0002's SP-09 counts were measured with the CTX-J detector defect present and are corrected in place at the top of its findings table; not re-measured.*
| [sp-0003](sp-0003/profile.md) | 2026-09-06T22:11:11Z | theterrace | 12 | 36 | SP-01, SP-02, SP-03 |
