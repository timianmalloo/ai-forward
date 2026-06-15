---
id: privacy-review
title: "Privacy Review"
type: privacy-review
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [privacy, linddun, data-governance]
links:
  - { to: architecture, rel: documents }
  - { to: design-aiforward-cli, rel: documents }
  - { to: design-pack-doctor, rel: documents }
  - { to: design-project-memory, rel: documents }
  - { to: design-rai-and-scrub, rel: documents }
review-by: "2026-12-11"
review-suggested: []
summary: >-
  Repo-level privacy posture for the pack-evolution tooling: the CLI and doctor touch no personal
  data; project memory may incidentally record handles/names (no special-category data, mitigated
  by the scrub); the scrub is itself a privacy control.
---

# Privacy Review

*The repo-level rollup of every component's privacy analysis (design SKILL Stage 3, LINDDUN-lite). The register below is **generated** — refresh it with the script bundle, never by hand:*

```bash
python3 docs/ai-forward-pack/scripts/docs-graph.py rollup --heading "Privacy analysis (LINDDUN-lite)" --type design
```

## 1. Personal-data posture

- **aiforward-cli** — no personal data (forwards argv to child processes).
- **pack-doctor** — no personal data (reads frontmatter metadata, file presence, marker counts; never document bodies).
- **project-memory** — *may* incidentally record handles/names that already appear in commits. Rule: **no special-category data** in memory; emails redacted by the scrub; retention = life of the repo (the value is permanence); rights path = git history rewrite if required.
- **rai-and-scrub** — the scrub is a **privacy control** (redaction); it holds nothing and transmits nothing (purely local).

## 2. Generated register (LINDDUN-lite, rolled up from the designs)

<!-- BEGIN GENERATED: docs-graph.py rollup -->
<!-- run: python3 docs/ai-forward-pack/scripts/docs-graph.py rollup --heading "Privacy analysis (LINDDUN-lite)" --type design -->
<!-- END GENERATED -->

## 3. Accepted-risk register (maintained by hand)

| Accepted risk | Component | Rationale | Residual |
|---|---|---|---|
| Durable retention of handles/names in project memory | project-memory | Permanence is the point of a memory ledger; data is no more than commit metadata already exposes | Low; rights path is `git-filter-repo` if ever required |
| Scrub false negatives leave some PII in history | rai-and-scrub | stdlib-only first-pass | Transferred to Presidio/gitleaks in CI; `git-filter-repo`/BFG for purge |
