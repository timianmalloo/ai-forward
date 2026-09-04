---
id: api-scrub
title: "API — scrub.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  scrub.py — first-pass PII/secret redaction for Markdown (deployable).
---

# `scrub.py`

*Generated from `pack/scripts/scrub.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
scrub.py — first-pass PII/secret redaction for Markdown (deployable).

Redacts OBVIOUS personal data (emails) and common secret shapes (token prefixes, private keys)
from Markdown, with --check (report; nonzero on hit) and --write (redact in place). It is the
on-brand, dependency-free analogue of Squad's `scrub-emails`.

  ⚠ THIS IS A FIRST-PASS, NOT CI-GRADE. Regex recall is limited — it will miss PII/secrets that
  NLP (Microsoft Presidio) or entropy/rule engines (gitleaks, detect-secrets, TruffleHog) catch.
  Use those in CI for real enforcement, and git-filter-repo / BFG to PURGE anything already
  committed (scrub redacts going forward; it does not rewrite history).

Design: docs/design/rai-and-scrub.md. Stdlib only. Never prints a raw secret (preview is redacted).

Usage
  scrub.py [paths...] [--check | --write] [--aggressive] [--json]
  (default paths: docs/ and pack/ ; default mode: --check)
Exit: --check -> 1 if any finding else 0 ; --write -> 0.
```

## CLI — options

| Option | Help |
|---|---|
| `--aggressive` | also flag any 32+ char token (more false positives) |
| `--check` | report findings, nonzero exit on any (default) |
| `--json` | _(no help text — coverage gap)_ |
| `--write` | redact findings in place |

## Functions

### `scan_text(text, aggressive=…)`

Yield (lineno, category, raw_match) for each finding (skips already-redacted spans).

### `redact_text(text, aggressive=…)`

Return text with every match replaced by [REDACTED:<category>] (idempotent).

## Coverage

- Public functions: **2** · documented: **2** (**100%**)

