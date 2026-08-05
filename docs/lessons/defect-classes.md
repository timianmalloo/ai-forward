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

**Status counts:** controlled `3` · partially-controlled `3` · uncontrolled `20`
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

### PACK-F — A default that is correct in the source repo and inverted in every consuming repo
- **Signature:** a rule, config or template is authored while working *in* the repo that produces an artifact, validated there, and shipped as the default for repos that *consume* it — where the same rule means the opposite thing. The giveaway is a rule phrased in terms of "the generated copies" without asking *generated from what, and does that source exist over there?*
- **Why it survives:** it is verified, and verified **in the wrong universe**. Every check passes in the authoring repo, the numbers improve, and the reasoning is sound *for that context*. Nothing in the source repo can detect it, because the condition that inverts the rule (`pack/` absent) never occurs there. It only fails after distribution, in someone else's repo, silently.
- **Instances:**
  - `2026-08-02` `.graphifyignore` / `graphify-setup.py` — the first `.graphifyignore` excluded `.claude/`, `.github/{instructions,prompts,agents}` and `docs/ai-forward-pack/` as "generated copies of `pack/`". Correct here: it cut the graph 3,898 → 2,033 nodes and removed duplicate god nodes. **Wrong in every consuming repo**, where there is no `pack/` and those trees are the *only* copy — measured on a real consumer: 153 files removed, **97 of which exist nowhere else** (28 knowledge docs, 17 skills, 23 personas, 19 templates, 10 scripts). A consuming repo would have had a code graph unable to answer "what governs our migrations?". Caught by a reviewer asking *"what will you miss in a project repo that adopts this as a starter?"* — not by any check.
- **Control:** `graphify-setup.py` now **detects the repo kind** (`pack/adapters/INSTALL.md` present → source; `docs/ai-forward-pack/` or `.claude/knowledge/` present → consumer; else plain) and emits the matching rules, recording the detected kind and canonical copy in the generated file's header. `--check` additionally **warns and exits 2** when an existing `.graphifyignore` excludes `.claude/` or `docs/ai-forward-pack/` in a repo where those are the only copy. Verified across all three repo kinds plus a planted-wrong-rules consumer. The standing question this adds: **before shipping a default, run it mentally in the repo that will receive it, not the one that authored it.**
- **Status:** `controlled`

### PACK-E — An ambiguous proper noun resolved inside my own frame
- **Signature:** a name arrives with no namespace ("Graphify", "the graph tool", "our linter"). The current conversation supplies a frame — we were discussing Obsidian — so the name is looked up *within that frame*, rigorously, and the negative result is reported as fact. The lookup was real; the universe was wrong.
- **Why it survives:** it arrives **with evidence**, which makes it more convincing than a plain guess. "I checked all 6,284 entries of the official registry and no such plugin exists" is a true statement, carries a citation, and is a correct answer to a question nobody asked. The pack's own rigor rules are satisfied — Stage 3 evidence gathered, source cited — because those rules police *how well you answer*, not *whether you answered the right question*. That is exactly the silo decision the standing method warns about: locally correct, globally wrong.
- **Instances:**
  - `2026-08-02` revision 19 — the user asked to compose Obsidian with "Graphify". Graphify was resolved against the Obsidian community-plugin registry, found absent, and substituted with `knowledge-graph-analysis`; the substitution was then written into a shipped knowledge doc, a script comment and the INSTALL changelog. Graphify is in fact a separate product (graphify.com) — an on-device **code** knowledge graph — which composes with the pack far better than the substitute. Corrected in revision 20; the substitution is now the worked example in `code-knowledge-graph.md` GK1.
- **Control:** `code-knowledge-graph.md` **GK1** — *establish the product from its own canonical source before composing with it*. The operational rule: when a proper noun is not already established, resolve it **frame-free first** (the bare name, its own site/registry) before resolving it inside the current topic; and when a lookup returns *absent*, treat that as evidence the **frame** may be wrong, not only the name. `NO AUTOMATED CONTROL` — this is a reasoning failure, not a mechanical one; the cheap alternative is to state the resolution explicitly and let the user correct it, which is what surfaced it here.
- **Status:** `partially-controlled`

### PACK-D — An array parameter arrives as one comma-joined string when the script is invoked as an executable
- **Signature:** a PowerShell script declares `[string[]] $Thing` and is invoked as `pwsh script.ps1 -Thing A,B`. Because `pwsh` is being run as a *native executable*, the argument is passed as the single literal string `"A,B"` and never re-parsed into an array. The script then processes one nonsense element. Dot-invoking (`& .\script.ps1 -Thing A,B`) works perfectly, so the script "works on my machine" and fails in the documented invocation.
- **Why it survives:** the author tests by dot-invoking, which is the natural thing to do while iterating in a session; the README then documents `pwsh script.ps1 ...`, which is the natural thing for a *user* to run. The two are never the same call. Nothing errors — the script proceeds with a wrong value — and if the error path also drops the offending input from its message (the usual pairing), the symptom is an empty "not found" that names nothing.
- **Instances:**
  - `2026-08-02` `tools/setup-obsidian-for-repo.ps1` — `-Repo A,B` via `pwsh` produced one iteration reporting `SKIP  - path not found` against an empty path, while both paths existed. Two defects in one: the unsplit argument, and an error message that had already nulled the variable it was reporting on.
- **Control:** the script now splits any element on `,` and trims at the parameter boundary, and the error path keeps the original input in `$requested` rather than the resolved variable. Verified by running **both** invocation forms plus a genuinely bad path. `NO AUTOMATED CONTROL YET` — the general fix is a lint over `tools/*.ps1` for array parameters lacking boundary normalisation; until then, the rule is: **test a script the way its own documentation says to invoke it.**
- **Status:** `partially-controlled`

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
| **UX-C** | Craft rule documented but not controlled | A named anti-pattern lives in a knowledge doc's prose table while the repo's own artifacts violate it | Prose is not executed; a reviewer must remember to consult a table at exactly the right moment | **Deterministic detector in CI** — `ui-craft-gate.py` / `impeccable detect` (CD8); ran against this pack's own templates and found 4 real instances (2 x `side-tab`, 1 x `layout-transition`, 1 x inset stripe), all now fixed and guarded by `evals/cases/ui-craft-detection-01.json` | `controlled` |
| **VA-A** | Generated asset referenced by provider URL | A mockup or page links a generation-provider CDN URL instead of a committed file | It renders perfectly today; the provider retains results for only 7 days | Generate once, download, optimize, commit, reference by relative path (VA4); `not-grep` on provider hosts in the eval | `controlled` |
| **VA-B** | Generated interface passed off as design | A generated "screenshot" or UI panel embedded in a design artifact | It looks finished, so nobody inspects the illegible text or the invented controls | Never generate the interface, only what it shows (VA5); mockups are hand-authored dependency-free HTML (DX8) | `uncontrolled` |
| **PACK-A** | Conditional standard wired as prose, not as a trigger | A standard declares itself "triggered" (Testing-Strategy sense), but the skill that should apply it references it only in narrative or a definition-of-done checkbox, so it surfaces *after* the decision it was supposed to shape | The reference genuinely exists, so link-checks and the consistency gate both pass. Nothing is missing; it is merely in the wrong place in the flow, and the cost is invisible until someone picks the wrong archetype | An explicit **trigger table** with union semantics, mapped at the stage the trigger reshapes rather than at the gate; a triggered-but-unmet directive fails the gate. Found via a user challenge: `technical-ui-design.md` (12 directives, governs every expert surface) was reachable from `/ui-design` only through the second-to-last DoD checkbox | `controlled` |
