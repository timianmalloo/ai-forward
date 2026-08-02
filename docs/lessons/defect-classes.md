---
id: defect-classes
title: "Defect-class register"
type: doc
status: accepted
owner: "@timianmalloo"
tags: [lessons, defect-classes, continuous-improvement]
links:
  - { to: architecture, rel: relates-to }
  - { to: kb-domain-and-data-modelling, rel: relates-to }
review-by: "2026-10-31"
summary: >-
  This repository's register of defect classes — the recurring shapes of things that go wrong
  here, what each one survives, and the control that now fails when the shape recurs. Read at
  grounding; appended to on every defect, correction or falsified assumption.
---

# Defect-class register

*Governed by `continuous-improvement.md` (CI1–CI12). **One entry per class, not per bug.** A new occurrence of an existing class appends to that class's Instances and triggers a control review — it does not create a new entry. Read this at grounding (CI5) for the area you are working in.*

**How to use this file**
1. On any defect, correction, or falsified assumption, answer **class → sweep → derive → prevent** in writing (CI2).
2. Find the matching class below, or add one. Append the instance.
3. Climb the control ladder (CI6) and record the highest rung that actually holds: *make it impossible* > *automated control* > *always-loaded instruction* > *knowledge doc* > *register entry only*.
4. A control is not a control until it has been **observed failing** on the un-fixed code.
5. If the class would help any project — not just this one — raise it upstream via `/extendaibundle` (CI8).

**Status counts:** controlled `2` · partially-controlled `1` · uncontrolled `20`
**Recurrence since last review:** `0` — *a second occurrence of a known class means the control was wrong, not that someone was careless (CI4).*

---

## Entry schema

```markdown
### <ID> — <the class, stated as a shape>
- **Signature:** how you recognise it in the wild — the smell, the code shape, the symptom.
- **Why it survives:** which controls it passes. (The most useful field: every durable class
  survives something, and naming what it survives is how you build the control that catches it.)
- **Instances:** <date/ref> — one line each, newest first.
- **Control:** the named test / gate / lint / analyzer / instruction that now fails when the shape
  recurs, with its location — and the date it was observed failing. Or `NONE YET — <why, and what
  would be needed>`.
- **Status:** `controlled` | `partially-controlled` | `uncontrolled`
```

---

## Project classes

*Classes discovered in this repository. Newest first.*

### PACK-C — An assertion encodes a transient magnitude assumption
- **Signature:** a check is written while a value is small and quietly bakes in its *magnitude* — a regex like `revision: [2-9]` (single digit), a fixed-width column, a two-character version field, an `id < 100` guard. It is correct on the day it is written and becomes wrong on the day the value grows, with no code change to blame. The failure is a **false negative on correct behaviour**: the thing under test works, and the check says it doesn't.
- **Why it survives:** it passes continuously for as long as the value stays small, so it accumulates trust. It only fires after a threshold crossing that nobody associates with it, and by then the check looks authoritative — the instinct is to suspect the behaviour, not the assertion. Nothing in a green suite ever exercises the larger value.
- **Instances:**
  - `2026-08-02` `pack/evals/cases/updatepack-01.json` — `"pattern": "revision: [2-9]"` was written when the pack was at a single-digit revision. At **revision 18** it can no longer match, so the eval would have reported FAIL for a correct `/updatepack` run. Found while raising the revision 17→18, not by the suite. Fixed to `revision: (?:[2-9]|[1-9][0-9]+)` and verified against 1 / 2 / 18 / 100.
- **Control:** `NONE YET — the general fix is a lint over eval-case regexes for bounded character classes applied to unbounded counters. Interim control: the "**Bump revision + add a changes entry**" step in the /extendaibundle flow now implies re-checking any assertion that reads the revision, and this register entry is the standing reminder. Escalate to an automated check if it recurs.`
- **Status:** `partially-controlled`

### PACK-B — A theme variant inherits a semantic colour it must re-state, and drops below AA
- **Signature:** a theme override block (`[data-theme="contrast"]`, a brand skin, a density mode) re-states the *structural* tokens — canvas, ink, line, accent — and silently inherits the *semantic* ones (`--danger`, `--ok`, `--warn`) from the theme above it. The inherited value was tuned against a different background and is now below 4.5:1. Nothing errors; the colour still "looks red".
- **Why it survives:** the theme visibly works — every structural pairing passes, and the semantic colour is only used on error/success states, which demos and screenshots rarely show. A contrast audit that only checks body text and headings misses it entirely; it needs the *semantic* pairings in the audit set.
- **Instances:**
  - `2026-08-02` `mockup-harness.template.html` — the high-contrast theme inherited the dark theme's `--danger:#ff8a80` against a pure-black canvas: **3.21:1, below AA**. Caught by the template's own in-artifact audit during a Playwright render test, before the template shipped.
- **Control:** the **in-artifact contrast audit** in `templates/mockup-harness.template.html` (`AUDIT.pairs` includes the semantic pairings and runs on every theme switch), plus **DX11** in `ui-design-craft.md` which now states the rule explicitly: *re-state semantic colours in every theme*. Observed failing on the un-fixed template — it reported `FAIL (needs 4.5:1)` for the contrast theme before the fix, and `0 contrast fail` after.
- **Status:** `controlled`

### PACK-A — An accessibility check that over-reports teaches the wrong design
- **Signature:** a mechanical a11y/lint check applies one threshold to a whole category (here: 3:1 to every `--line`-on-background pairing) without distinguishing what the standard actually requires. It produces a permanent, unfixable-looking FAIL, and the "fix" is to make the design worse — heavy dark dividers everywhere in the name of WCAG.
- **Why it survives:** the check *looks* rigorous, and nobody argues with a red FAIL next to "accessibility". The failure is in the check's *classification*, not its arithmetic, so re-running it never reveals anything. It survives precisely because it errs toward strictness, which reads as safe.
- **Instances:**
  - `2026-08-02` `mockup-harness.template.html` — the harness flagged decorative row dividers at 1.26:1 as an a11y failure. WCAG 2.2 SC 1.4.11 exempts purely decorative separators; only boundaries *needed to identify a control* and focus indicators require 3:1. Fixing the "failure" would have meant shipping a template that teaches heavy borders.
- **Control:** pairings are now **classified** (`text` 4.5 required · `large` 3.0 required · `ui` 3.0 required · `decorative` measured-and-reported-but-not-counted), with the reclassification rule written into **DX11**: *a divider that is the only thing separating two interactive rows is `ui`, not decoration* — report the ratio either way, never hide it. Verified across all three themes.
- **Status:** `controlled`

---

## Inherited classes (seeded from the pack)

*Observed in production across independent codebases running the AI-Forward pack (`continuous-improvement.md` §6). Each is **uncontrolled here until this repo builds the control** — that is the work, not the copying.*

| ID | Class | Signature | Why it survives | Control to build | Status here |
|---|---|---|---|---|---|
| **DM-A** | One quantity, two homes | A value produced in two places; a new call site wires to whichever it found first | Both implementations pass their own tests; nothing compares them | Derive once (DM7); cross-surface consistency test | `uncontrolled` |
| **DM-B** | Stored fact that nothing writes | A persisted flag beside a function computing the same thing | Reads succeed and return a plausible default | Reader/writer trace (DM15); stored-equals-derived test | `uncontrolled` |
| **DM-C** | Persisted field with no compute reader | Stored, entered, round-tripped, tested — read by nothing that computes | Round-trip tests pass perfectly | Reader trace: write / CRUD / schema / **compute** | `uncontrolled` |
| **DM-D** | Grain inferred, not declared | Period/owner derived from a date rule; exceptions break it | Works for every non-exceptional record | Declare the grain; put it in the key (DM8) | `uncontrolled` |
| **DM-E** | Semi-additive measure summed across time | Balances/positions/headcounts added over periods | The arithmetic is valid; only the meaning is wrong | Declare additivity per measure (DM9) | `uncontrolled` |
| **DM-F** | Type-1 where Type-2 was needed | A mutable attribute silently rewrites the meaning of past records | Nothing errors; history just changes | History rule per attribute (DM10); point-in-time test | `uncontrolled` |
| **E2E-A** | Field reaches the DTO but not the wire | Present in model, service, client type, column list; missing from the projection | Every layer's own test passes | Write the surface list first (E7); one end-to-end assertion per field | `uncontrolled` |
| **E2E-B** | Declared shape with no write path | A facet/status/enum/route declared and never set | Telemetry reports "nothing to do" — true, for the wrong reason | Test that the shape is written under the claimed condition | `uncontrolled` |
| **E2E-C** | Green suite, broken surface | All units green; the page never renders; the composition root is never exercised | Units construct their subject by hand | One proof through the real composition root to the rendered surface (E11) | `uncontrolled` |
| **E2E-D** | Component tests that can't see each other | Every part correct against its own expectation; parts disagree | Per-component coverage is high | Cross-surface consistency test on one seeded scenario (E12) | `uncontrolled` |
| **E2E-E** | The gate passed, its contents didn't | Several checks in one block; only the last exit code propagates | The gate is green | Run each control independently; assert each reports its own status (E13) | `uncontrolled` |
| **E2E-F** | Exit code taken as result | A command returned success; the state was never read back | Success is success-shaped | Read back the state and assert on it (E14) | `uncontrolled` |
| **E2E-G** | Reachability not verified | The surface exists but nothing links to it — or a link points at nothing | The feature works if you can get to it | Assert the navigation path to any new surface (E10) | `uncontrolled` |
| **RIG-A** | Own-code shape asserted from memory | "This type has that member" — written in a design, never opened | Designs aren't compiled | Read the file or label Inferred (E15); review opens the cited file | `uncontrolled` |
| **RIG-B** | Delegated inventory cited as fact | A sub-agent's counts/listings enter an artifact unverified | Sub-agent output is fluent and specific | Spot-check before citing (E16) | `uncontrolled` |
| **RIG-C** | Sweep stopped at the instance | The fix works; the sibling ships the same bug days later | The reported symptom is gone | class → sweep → derive → prevent (CI2) | `uncontrolled` |
| **REC-A** | Stale record / overstated claim | A comment, status table or doc asserts something that was true once | Documentation isn't executed | Re-verify records you touch (E17); correct overstatements in their own change | `uncontrolled` |
| **OPS-A** | Migration compiles but is never applied | The migration builds; the deployer doesn't run it | The build is green | Migrate-before-publish enforcement; exercise the down path (DM16) | `uncontrolled` |
| **UX-A** | Archetype mismatched to the task | A dashboard archetype on a data-entry task: everything visible, nothing sequenced | Each component is individually fine | Verify archetype vs JTBD on changes to *existing* screens too | `uncontrolled` |
| **UX-B** | Shipped with data-only states | Loading/empty/error never designed; "it looked fine with data" | Demos and tests use populated fixtures | Complete component state set as a design gate (U9) | `uncontrolled` |
