# Fleet learnings (general, control-bearing classes)


### unknown-artifact-type-in-frontmatter
- **Signature:** unknown-artifact-type-in-frontmatter
- **Control:** docs-graph.py validate rejects any frontmatter 'type' not in the TYPES enum; run it after adding a graph node. (automated control)
- **Boundary:** Applies to any new .md graph node; type must be one of the known TYPES.
- **Confidence:** v
- **From:** drm-0002 / p1

### PACK-E · An ambiguous proper noun resolved inside my own frame
- **Signature:** PACK-E · An ambiguous proper noun resolved inside my own frame
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0003 / p3

### PACK-D · An array parameter arrives as one comma-joined string when the script is invoked as an exec
- **Signature:** PACK-D · An array parameter arrives as one comma-joined string when the script is invoked as an executable
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0003 / p4

### PACK-C · An assertion encodes a transient magnitude assumption
- **Signature:** PACK-C · An assertion encodes a transient magnitude assumption
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0003 / p5

### PACK-H · A fix to a hosted surface reported "done" from the working tree, not verified on the live s
- **Signature:** PACK-H · A fix to a hosted surface reported "done" from the working tree, not verified on the live surface
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0003 / p2

### PACK-N · Staleness inferred from a timestamp rather than from content truth
- **Signature:** PACK-N · Staleness inferred from a timestamp rather than from content truth
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0007 / p4

### PACK-Q · An adapter written to a contract's *documented* shape, never to a *recorded* one
- **Signature:** PACK-Q · An adapter written to a contract's *documented* shape, never to a *recorded* one
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0007 / p2

### PACK-C · An assertion encodes a transient magnitude assumption
- **Signature:** PACK-C · An assertion encodes a transient magnitude assumption
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0007 / p8

### PACK-O front-matter presence + scope-drift review
- **Signature:** PACK-O front-matter presence + scope-drift review
- **Control:** Presence (mechanical): every substantive turn records done_when (CT19); a missing one skipped the front matter. Satisfaction: review each done_when->summary pair where the summary exceeds the goal (scope drift, PACK-O). The audit done_when field + this miner ARE the rung-2 control (CI6). (automated control)
- **Boundary:** Presence is mechanical; 'summary exceeds goal' is surfaced for human review, not auto-judged. Trivial/conversational turns are exempt from logging (AL5b).
- **Confidence:** v
- **From:** drm-0007 / p11

### PACK-P · A check reports its verdict over a corpus it never established was non-empty
- **Signature:** PACK-P · A check reports its verdict over a corpus it never established was non-empty
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0007 / p3

### PACK-D · An array parameter arrives as one comma-joined string when the script is invoked as an exec
- **Signature:** PACK-D · An array parameter arrives as one comma-joined string when the script is invoked as an executable
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0007 / p7

### SHELL-A · Content routed through a shell construct that performs substitution on it
- **Signature:** SHELL-A · Content routed through a shell construct that performs substitution on it
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0007 / p1

### PACK-H · A fix to a hosted surface reported "done" from the working tree, not verified on the live s
- **Signature:** PACK-H · A fix to a hosted surface reported "done" from the working tree, not verified on the live surface
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0007 / p5

### PACK-E · An ambiguous proper noun resolved inside my own frame
- **Signature:** PACK-E · An ambiguous proper noun resolved inside my own frame
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0007 / p6

### Two or more agent sessions work one repository, but session registration, file ownership, seam contr
- **Signature:** Two or more agent sessions work one repository, but session registration, file ownership, seam contracts, and derived/append-only merge policy are not recorded before work begins.
- **Control:** Add a multi-session collaboration check: when more than one active worktree/session exists, fail or warn if any session is unregistered, if changed files lack a current coord claim or owner mapping, if no shared session contract exists, or if derived/append-only conflicts are hand-merged rather than regenerated/re-issued. Observe it failing on an unregistered two-session fixture and passing once both sessions register, claim files, and publish the seam contract. (automated control)
- **Boundary:** Applies to concurrent cross-agent repository writes. It does not apply to a single writing session, read-only exploration, or a normal human code review where one actor owns the worktree. It coordinates humans/agents by evidence; it is not a distributed lock unless the edited resource accepts fencing tokens.
- **Confidence:** v
- **From:** drm-0007 / p12

### A review artifact is produced every cycle, and nothing carries its output into the durable store, so
- **Signature:** A review artifact is produced every cycle, and nothing carries its output into the durable store, so the same proposals resurface indefinitely
- **Control:** The dream run reports its own promotion rate as a first-class number: for each proposal, how many prior dreams already raised it, and how many proposals from the previous dream were promoted. A proposal recurring for the Nth time is rendered as an ESCALATION at the top of the review view, not as a fresh idea in the middle of it. Optionally the run exits non-zero when the previous dream promoted nothing, on the same principle the pack applies to a cap firing: producing the artifact is not the same as the artifact being used. (automated control)
- **Boundary:** Applies to any produce-review-promote loop whose promote step is a separate manual command. It does not apply where the analysis writes directly, which is a different and worse design — the human gate is correct, it is the un-measured skip that is the defect.
- **Confidence:** v
- **From:** drm-0009 / p22

### unknown-artifact-type-in-frontmatter
- **Signature:** unknown-artifact-type-in-frontmatter
- **Control:** docs-graph.py validate rejects any frontmatter 'type' not in the TYPES enum; run it after adding a graph node. (automated control)
- **Boundary:** Applies to any new .md graph node; type must be one of the known TYPES.
- **Confidence:** v
- **From:** drm-0009 / p1

### PACK-N · Staleness inferred from a timestamp rather than from content truth
- **Signature:** PACK-N · Staleness inferred from a timestamp rather than from content truth
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0009 / p6

### PACK-Q · An adapter written to a contract's *documented* shape, never to a *recorded* one
- **Signature:** PACK-Q · An adapter written to a contract's *documented* shape, never to a *recorded* one
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0009 / p4

### PACK-E · An ambiguous proper noun resolved inside my own frame
- **Signature:** PACK-E · An ambiguous proper noun resolved inside my own frame
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0009 / p8

### PACK-C · An assertion encodes a transient magnitude assumption
- **Signature:** PACK-C · An assertion encodes a transient magnitude assumption
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0009 / p10

### PACK-O front-matter presence + scope-drift review
- **Signature:** PACK-O front-matter presence + scope-drift review
- **Control:** Presence (mechanical): every substantive turn records done_when (CT19); a missing one skipped the front matter. Satisfaction: review each done_when->summary pair where the summary exceeds the goal (scope drift, PACK-O). The audit done_when field + this miner ARE the rung-2 control (CI6). (automated control)
- **Boundary:** Presence is mechanical; 'summary exceeds goal' is surfaced for human review, not auto-judged. Trivial/conversational turns are exempt from logging (AL5b).
- **Confidence:** v
- **From:** drm-0009 / p13

### PACK-H · A fix to a hosted surface reported "done" from the working tree, not verified on the live s
- **Signature:** PACK-H · A fix to a hosted surface reported "done" from the working tree, not verified on the live surface
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0009 / p7

### PACK-D · An array parameter arrives as one comma-joined string when the script is invoked as an exec
- **Signature:** PACK-D · An array parameter arrives as one comma-joined string when the script is invoked as an executable
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0009 / p9

### SHELL-A · Content routed through a shell construct that performs substitution on it
- **Signature:** SHELL-A · Content routed through a shell construct that performs substitution on it
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0009 / p3

### PACK-P · A check reports its verdict over a corpus it never established was non-empty
- **Signature:** PACK-P · A check reports its verdict over a corpus it never established was non-empty
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0009 / p5

### GIT-A · A revert used as an undo, on a file that also carries unrelated uncommitted work
- **Signature:** GIT-A · A revert used as an undo, on a file that also carries unrelated uncommitted work
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0009 / p2

### assume marker harvest
- **Signature:** assume marker harvest
- **Control:** Review each assume: marker; a triggered one is a bug already written down (NG9). Verify or convert to a control. (knowledge doc)
- **Boundary:** Markers in this repo only; harvested at consolidation time.
- **Confidence:** v
- **From:** drm-0009 / p11

### simplify marker harvest
- **Signature:** simplify marker harvest
- **Control:** Review each simplify: marker against its upgrade trigger; a triggered one is debt due (L6). (knowledge doc)
- **Boundary:** Markers in this repo only; harvested at consolidation time.
- **Confidence:** v
- **From:** drm-0009 / p12
