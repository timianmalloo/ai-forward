---
id: api-design-lint
title: "API — design-lint.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  design-lint.py — token-reference linter for design-language docs (AI-Forward).
---

# `design-lint.py`

*Generated from `pack/scripts/design-lint.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
design-lint.py — token-reference linter for design-language docs (AI-Forward).

Makes UI Standard U3 ("reference a token, never an arbitrary value") a *forcing
function* for a DESIGN.md-style design-language doc (templates/design-language.template.md).
Stdlib only; lives in the script bundle (deployed to docs/ai-forward-pack/scripts/).

Checks:
  1. FAIL  — every `{group.token}` reference in the body resolves to a token declared
            in the frontmatter (group in: colors, typography, rounded, spacing,
            elevation, motion). An unresolved reference is a broken token contract.
  2. FAIL  — the frontmatter declares at least a `colors:` and a `typography:` block
            (a design language without them is not one).
  3. WARN  — raw hex (`#rrggbb`) found in the body. Hex in the palette *table* is fine
            (that's documentation); hex in a component/layout spec should be a `{token}`.
            Non-failing — surfaced for human review.

Exit 0 clean (warnings allowed), 1 on any FAIL. Usage: design-lint.py <file.md> [...]
```

## CLI — options

| Option | Help |
|---|---|
| `--strict` | treat warnings as failures too |

## Functions

### `split_frontmatter(text)`

Return (frontmatter_lines, body_text). Frontmatter is the first --- ... --- block.

### `parse_tokens(fm_lines)`

Map each token-group to the set of token names declared under it.

Handles both block style (`colors:` then indented `  primary: ...`) and
inline-flow style (`rounded: { sm: 6px, md: 8px }` / `spacing: { scale: [...] }`).

### `lint(path)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **3** · documented: **2** (**67%**)
- Undocumented (recorded, not invented): `lint`

