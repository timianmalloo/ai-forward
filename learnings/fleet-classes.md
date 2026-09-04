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

### Two registers of one quantity, created by a session that had not opened the first one
- **Signature:** Two registers of one quantity, created by a session that had not opened the first one
- **Control:** Coordination state splits into exactly TWO stores with different lifetimes and one authority rule: a TRACKED ownership register that is the sole authority on who owns what, and an UNTRACKED liveness store that says only who is running right now, in which tree, on what, and what they are blocked on — and that states no path or ownership table at all. A lint fails the liveness store when it contains an ownership/path table, and the liveness store's own header must point at the tracked register and declare that the tracked one wins on any disagreement. Add as a WT-series directive in session-worktree-discipline.md with the lint in coord doctor. (automated control)
- **Boundary:** Applies wherever more than one agent session writes to one repository. Does not apply to a single-session repo, where one register is correct and a second store is pure ceremony.
- **Confidence:** v
- **From:** drm-0009 / p14

### A session describes another session's ownership, contract or seam without opening the file that stat
- **Signature:** A session describes another session's ownership, contract or seam without opening the file that states it
- **Control:** Extend E15 in end-to-end-integrity.md from code to AGREEMENTS: never assert the shape of our own contracts, ownership, or seam from memory — open the register or label the claim Inferred. The tell is one session summarising another session's ownership without a citation, and the cheap check is that every cross-session claim about who owns what carries the register line it came from. (always-loaded instruction)
- **Boundary:** Applies to claims about shared, written agreements. It does not apply to a session describing its OWN in-flight work, which has no register to cite yet.
- **Confidence:** v
- **From:** drm-0009 / p15

### The enforcement path logs `not_checked` and permits the edit, because the caller had no identity to 
- **Signature:** The enforcement path logs `not_checked` and permits the edit, because the caller had no identity to check
- **Control:** An unidentified session is REFUSED at the guard, never logged as not-checked and allowed. Identity is required to start a session, so there is no path that reaches the edit boundary without one. Where a transition period needs tolerance, the tolerated case is counted and surfaced by doctor as a defect number, not written to the log as a normal outcome. (make it impossible)
- **Boundary:** Applies to any guard whose decision depends on knowing WHO is asking. A guard that is identity-independent (a syntax lint, a schema check) has no such failure mode.
- **Confidence:** v
- **From:** drm-0009 / p16

### Entry verbs are called reliably; the matching exit verb is skipped, and only a timeout reclaims the 
- **Signature:** Entry verbs are called reliably; the matching exit verb is skipped, and only a timeout reclaims the resource
- **Control:** The coordination doctor reports the entry/exit asymmetry as a first-class number — sessions started vs ended, claims vs releases, and claims outstanding — and a session-end that would leave claims open is refused or reported rather than silently succeeding. This upgrades PACK-M and WT6/WT7 from a stated principle to a measured one, and generalises them from worktrees to ANY session-scoped resource. (automated control)
- **Boundary:** Applies to any resource acquired per session and released by a separate call. It does not apply where acquisition is scoped by a construct that cannot be skipped (a context manager, a transaction).
- **Confidence:** v
- **From:** drm-0009 / p17

### A collaboration channel accumulates repeated same-shape requests against one seam, each handled indi
- **Signature:** A collaboration channel accumulates repeated same-shape requests against one seam, each handled individually
- **Control:** CI2 (class, not instance) applies to the collaboration channel, not only to defects. When a session opens the Nth request of the same shape against the same seam, it raises the CLASS — the missing capability behind all N — rather than the N+1th request. The channel's own review asks 'how many of these are one thing?' before it asks 'which is next?'. (knowledge doc)
- **Boundary:** Applies where one session repeatedly asks another for variations of one capability. It does not apply to genuinely distinct requests that merely arrive together.
- **Confidence:** i
- **From:** drm-0009 / p18

### One field carries three different kinds of identity, so no query over it means one thing
- **Signature:** One field carries three different kinds of identity, so no query over it means one thing
- **Control:** Declare the identity vocabulary once and validate the field against it: an AGENT is a stable logical actor, a SESSION is one run in one worktree, and they are separate fields. Reject a raw UUID in the agent field, and reject a work-item placeholder that is constant across every record — a field whose value never varies carries no information and should be removed rather than filled in. (automated control)
- **Boundary:** Applies to any shared record keyed by actor. Not applicable where a single anonymous writer is intended by design.
- **Confidence:** v
- **From:** drm-0009 / p19

### Two sessions collide on a lease and the collision is treated as a scheduling problem to wait out
- **Signature:** Two sessions collide on a lease and the collision is treated as a scheduling problem to wait out
- **Control:** A coordination refusal is a DEFECT SIGNAL about the decomposition: if two sessions need the same file at the same time, the work was split along the wrong seam and the plan is wrong, not the timing. The response is to re-cut the work item or record a block naming what is needed — never to retry on a timer, and never to widen the lease. Repeated refusals on one path escalate to a plan review. This is GO9 (a cap firing is a defect signal) pointed at coordination. (always-loaded instruction)
- **Boundary:** Applies to refusals arising from CONTENTION. A refusal caused by a missing identity or a malformed request is a different class (COORD-C) and is not evidence about the plan.
- **Confidence:** v
- **From:** drm-0009 / p20

### A documented default and the observed distribution differ by two orders of magnitude at the tail
- **Signature:** A documented default and the observed distribution differ by two orders of magnitude at the tail
- **Control:** Bound the lease at the guard rather than in prose: cap the TTL, and require a recorded reason above a stated threshold. Report the TTL distribution in doctor so the drift is visible as a number. The rule that should hold — 'a lease covers the minutes you are editing a file, never an area you intend to own' — is only real if something refuses the twelve-hour lease. (automated control)
- **Boundary:** Applies where leases are advisory over shared files. A long lease is legitimate for a genuinely exclusive, long-running operation — which should be a different verb, not a longer default.
- **Confidence:** v
- **From:** drm-0009 / p21
