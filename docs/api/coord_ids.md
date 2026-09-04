---
id: api-coord_ids
title: "API — coord_ids.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  coord_ids.py - collision-proof identifiers, in ONE place.
---

# `coord_ids.py`

*Generated from `pack/scripts/coord_ids.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
coord_ids.py - collision-proof identifiers, in ONE place.

Imported by both `coord-core.py` and `audit-log.py`. It exists as its own module rather than
as a copy in each because six lines duplicated across two scripts is ONE-A -- a shared rule
with no gate accretes private copies, and the copies only diverge later, when one is edited.
The underscore in the filename is deliberate: a hyphen is not importable, which is why
`bounded_process.py` is named the way it is.

WHY NOT `uuid.uuid7()`: absent on the installed 3.12 (it landed in 3.14) and present on the
"3.x"-pinned CI runner. A stdlib call that exists on the runner and not on the developer's
machine is PACK-J by construction. Established by spike S1, not assumed.

WHY NOT SCANNING: the prevention built for KG-B scans every remote branch before allocating.
It works, it takes about a second over 22 branches, and it collided again within the hour --
two sessions that mint before either has pushed are invisible to each other. Scanning is
rejected as a DESIGN, not as an implementation.

Design: docs/design/coord-federation-phase3.md · ADR-0008.
```

## Functions

### `new_id(scheme, ts_ms=…)`

48 bits of millisecond timestamp + 80 bits of os.urandom, Crockford base32.

Time-ordered, so a register still sorts chronologically without a sequence. Issuance
requires no communication between issuers -- that second property is the whole point,
because a scheme that is only safe when issuers can see each other is the defect.

Proven at 1,500 ids from 6 separate processes pinned to a single millisecond with no
shared state and no network: 0 collisions.

### `resolve_prefix(rows, prefix)`

(status, result, corpus_size) where status is unique | ambiguous | nomatch.

The git short-hash idiom. ADR-0008 accepted that a 26-character id is not human-sayable
but did not name the consumer that breaks: asking for an entry by number. Prefix recall
restores that WITHOUT introducing a second identity.

The corpus size is returned with EVERY verdict (R4/PACK-P): "not found" over an empty
register must never render the same as "not found" over a full one.

## Coverage

- Public functions: **2** · documented: **2** (**100%**)

