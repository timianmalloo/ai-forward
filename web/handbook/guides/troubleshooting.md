# Recover without making the situation less safe

When a workflow stops or an expected capability is absent, first identify which layer
is failing: skill discovery, the request, a local script, a harness permission, or the
behavior being built. A fix at the wrong layer can hide the symptom while weakening
the safeguard that exposed it.

## I cannot find a skill

Confirm that the pack is installed in the repository you actually opened. Check the
harness's skill selector and its discovery paths. For Codex, use the `$` selector or
`/skills`; a generic slash example is not proof that the host registered a command.

Refresh the session after changing installation files. Check for disabled skills or
overriding instructions, and ask the agent to identify the file it loaded.
See [harness setup](#harnesses) and [updatepack](#skill-updatepack).

## A script says Python is missing on Windows

Try the platform's actual interpreter form: `python` or `py -3`. The `python3` found
on some Windows machines is a Store alias, not a working Python installation.
Run the doctor to identify the local form. Do not install another environment
until you establish what is actually absent.

## The agent keeps adding work

Return to the goal, completion condition and exclusions. Ask which part of the new
work is required for the requested outcome. A useful adjacent idea can be recorded
without becoming an unapproved work order.

Use [also](#skill-also) for a deferred addition and an explicit stop when you want
the current track to end. [Compilation](#skill-compile) can help make the boundary
inspectable, but review its output for added scope.

## The output is plausible but the checks are weak

Ask what input would make the claim false. Then check whether the test exercises
that input through the real path, not a substitute that assumes the desired answer.

For HarborTasks, a twenty-row serialization test does not establish that all 63
matches were retrieved. Use the [rigor guide](#rigor) to separate the claim from
the evidence supporting it.

## Compilation will not finish or dispatch

Inspect unresolved decisions, missing references and the current compilation result.
An unanswered question is not a formatting problem to delete. Resolve it with the
person who owns the decision, then finish the appropriate prompt.

For native launch, use the finished per-track compilation ID required by the runner.
Do not substitute an old ID, an unfinished draft, or a command copied from a rendered
brief. See [the working sequence](#workflow).

## A coordinated worker appears idle

Check its assigned identity, worktree, deadline and returned state. Distinguish
waiting for a permission or Owner decision from a process that is stalled.
An acknowledgement that a message was read is not evidence that the task was done.

Use the coordinator's monitoring and escalation path with a bounded fallback.
Do not repeatedly nudge a worker without knowing what would let it progress.
Do not start a duplicate attempt if a side effect may already have happened.

## An edit or stop is refused

Read the actual reason. An edit may overlap another track's ownership, or the hook
may be unable to evaluate the request. A stop can be held while a decision the worker
raised still needs its Owner.

Resolve the ownership or decision through the workflow. Do not disable hooks,
rewrite a ledger by hand, impersonate the Owner or grant all tools merely to make
the message disappear. An unevaluated check is not a successful check.

## The native launch profile is not qualified

Qualification concerns the exact executable, configuration, permissions and relevant
behavior. A supported protocol or installed hook alone does not establish the whole
profile. Use [a manual brief or a smaller supported path](#coordination) until the
required behavior can be established.

Never substitute saved-session resume for an unsupported live-terminal attachment.
If you require a particular model, check actual execution evidence as well as the
request. Read [the harness-specific limits](#harnesses).

## Documentation and code disagree

Treat the disagreement as a finding. Read the current source and record whether the
implementation or the earlier intention needs correction. Refresh the affected guide
and its dependents; do not silently copy the plan into documentation as a shipped fact.

If generated pages are stale, rebuild them from their canonical source. Editing the
generated HTML or index directly creates another version that will drift.

## When to stop trying workarounds

Stop when the next step would widen permission, lose work, guess at data, cross an
unreviewed boundary or repeat an operation with unknown effects. Preserve the current
state and report the smallest question or action that would clear the block.

**Next:** [investigate a defect](#skill-investigate) for a demonstrated root cause,
or return to [the skill chooser](#skills) if the wrong workflow was selected.
