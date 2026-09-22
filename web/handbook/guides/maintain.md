# Maintain the pack without losing local intent

There are two maintenance jobs: keeping an installed pack current in an application,
and changing AI-Forward itself. They use related files but are not the same workflow.
Choose the correct starting repository before asking an agent to make changes.

## Update an application repository

Use [updatepack](#skill-updatepack) from a repository that already has the pack
installed. Make the intended local AI-Forward source available and review the
reconciliation before accepting it.

The workflow distinguishes managed content from project-specific deviations. A
managed instruction block is replaced as a block; local meaning should not be
silently lost in a line-by-line merge or a wholesale directory copy.

```text
/updatepack Refresh this installed pack from the local AI-Forward clone.
Preserve project-owned instructions and show me any reconciliation decisions.
```

In Codex, use `$updatepack`. Restart or refresh the affected harness session when
necessary so file changes are actually discovered. Run the doctor and inspect its
findings rather than treating a successful copy as runtime qualification.

## Extend AI-Forward itself

Use [extendaibundle](#skill-extendaibundle) in the AI-Forward source repository when
you want a new reusable capability. Start from a concrete problem and the artifact
the capability should produce, not just a proposed command name.

```text
/extendaibundle Add a workflow for a recurring review task we can describe
precisely. Establish its inputs, outputs, limits and regression cases before
adding another skill to the pack.
```

The extension workflow covers research, specification, design and implementation
with the pack's scaffolding and consistency checks. A useful extension earns its
maintenance cost and works across its declared harness surfaces.

## Know which copy to change

`pack/` is the canonical source for the agent pack. Harness installation surfaces
and the shared installed bundle are generated from it. Editing a generated copy may
appear to work and then disappear on the next synchronization.

The public handbook has its own website authoring source under `web/handbook`.
Its rendered portal and graph-indexed Markdown copies are generated. That separation
keeps reader education from accidentally becoming always-loaded agent instructions.

For pack-source changes, use the repository's maintenance commands and deployment map:

```powershell
pwsh tools\sync-pack.ps1
pwsh tools\verify-bundle.ps1
```

These are source-repository commands, not commands every application user must run.
Read the current installation/change guidance before editing adapters or managed
blocks. Commit source and generated surfaces together when the pack changes.

## Keep compatibility explicit

A skill name may be shared while invocation, hooks, permissions and runtime behavior
differ by harness. Updating an adapter is not permission to claim that all versions
now behave alike. Recheck affected examples and qualification boundaries.

Preserve useful links or supply a redirect when reorganizing public content. Keep
internal records available as secondary reference rather than erasing history to
make the new explanation look simpler.

## Review the maintenance result

Look for the intended source change, corresponding generated outputs, meaningful
regression protection, and a clear refresh instruction for adopters. A green test
suite does not substitute for the pack's source/install consistency gates.

If you only need to explain an existing capability better, update its documentation.
Do not change runtime behavior merely to make a cleaner story possible.

**Next:** [update an installed pack](#skill-updatepack), [propose an extension](#skill-extendaibundle),
or [find the technical maintenance references](#maintainer).
