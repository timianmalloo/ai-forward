# From request to reviewed change

A useful request tells the agent what should be different when the work is finished.
It does not have to prescribe the implementation. AI-Forward's workflows help turn
that intent into decisions, actions and a handback you can review.

There is no universal conveyor belt through every skill. Choose the next step from
what is still unknown. Research cannot substitute for a product decision, a design
cannot prove a running feature, and an implementation cannot silently settle a
question you intended to review.

## State the finish line

Begin with the outcome, a checkable completion condition and exclusions. Include
constraints the agent cannot discover from the repository, such as permitted model
families or whether a data export may include personal information.

```text
Goal: add CSV export for HarborTasks' current project and filter.
Done when: all 63 matching tasks are exported even though the page shows 20,
and another project's tasks are excluded.
Not in scope: scheduled exports, a reporting service, or new user roles.
```

This is an illustrative request, not a complete specification. It makes the important
ambiguity visible early and gives you a basis for rejecting unrelated work.

## Choose the next workflow

| What you need to establish | A useful starting point | What you inspect |
|---|---|---|
| The domain is unfamiliar | [Collect knowledge](#skill-collectknowledge) | Sources, uncertainties and vocabulary relevant to the problem |
| The desired behavior is unclear | [Specify the feature](#skill-specify) | Scope, user experience and testable acceptance criteria |
| System boundaries or load-bearing choices are changing | [Define architecture](#skill-define-architecture) | Responsibilities, contracts, alternatives and consequences |
| One component needs a concrete blueprint | [Design a slice](#skill-design-slice) | Inputs, outputs, failure handling and a credible verification plan |
| The design is understood and you need code | [Implement](#skill-implement) | The change and checks that distinguish correct from incorrect behavior |
| Existing behavior is wrong | [Investigate](#skill-investigate) | A demonstrated cause and a repair proposal before implementation |
| A large upgrade or refactor is needed | [Migrate](#skill-migrate) | Current behavior characterized before the change |
| Several tracks may be useful | [Prepare coordination](#skill-prepare-for-coordination) | Real independence, ownership, budgets and return evidence |

Small, well-understood work can take a short path. A change to identity, stored data
or concurrency needs more deliberate decisions and checks even if the diff is small.

## What compilation adds

In this pack, **compilation** means converting a prose request into a structured,
harness-appropriate starting prompt. It is not compilation of application source code.
The [compile skill](#skill-compile) makes the goal, traceable clauses, assumptions and
unanswered decisions explicit, and records the result with the original request.

```text
/compile Add CSV export for the active project and filter. Export every
matching task, not only the current page. Do not expand the reporting scope.
```

In Codex, use `$compile`. An illustrative compiled frame might identify the goal,
the completion check, exclusions, source references and a question about which columns
belong in the export. Review whether the frame preserves your intent. More polished
wording is not permission to add requirements.

Skills consume a compiled prompt when it is available. Do not assume that merely
typing prose causes the host application to run a compiler automatically. Follow the
actual workflow and inspect its output.

The native launch path has a concrete additional requirement: it consumes **finished,
dispatchable compilation audit IDs**, not arbitrary prompt strings. That matters for
coordination, because per-track prompts must be compiled after the plan fixes each
track's owned paths, budget and return contract.

## Planning and compilation are different decisions

An overall framing prompt can be compiled before planning. A per-track launch prompt
depends on the resulting plan. Keep those two uses distinct:

1. Clarify the overall outcome, with an explicit compilation when useful.
2. Decide whether several tracks are actually warranted.
3. Prepare the division of work, dependencies and ownership.
4. Compile each native-launch track's complete contract.
5. Execute through the selected mechanism and review the handbacks.

Unanswered decision requests must not be disguised as resolved instructions.
Compilation does not launch a process, grant tool permission or elect a coordinator.

## A worked path through HarborTasks

First, use `/specify` to settle all-matches behavior, columns, project access and empty
results. Suppose you decide that an empty export still contains the header and that
the export includes only fields the person can already view.

Next, use `/design-slice` for the export path. Ask it to inspect the actual paged query,
the file-format boundary and the UI entry point. The result should make clear how
all matches are retrieved without inventing an unrelated reporting subsystem.

Then use `/implement` for the bounded slice. The important negative case is not
“can we serialize twenty objects?” It is “does the real query-to-download path lose
the remaining matches?” Test the 63-match/20-row situation and the project boundary.

Finally, review the result and use `/document` to keep the useful explanation current.
The documentation should describe what was built, including limits, rather than
copy the earlier plan as if every promise had shipped.

If the backend and UI have independent ownership after a shared contract is settled,
you may instead prepare coordinated tracks. [The coordination guide](#coordination)
shows where that helps and what additional obligations it creates.

## Make a handback useful

A good handback tells you what changed, where to inspect it, what checks ran, what
did not run and what still needs a decision. An artifact's existence is not enough.
Inspect whether its contents meet the acceptance criteria.

For code, look beyond isolated units to the real composition and user path. For a
specification, check whether its acceptance criteria describe the desired behavior.
For a migration, inspect rollback and behavioral differences. The evidence you need
depends on the claim.

## Change the request without losing the thread

Use [also](#skill-also) for an addition that should be considered after the current
work reaches a safe checkpoint. Use an explicit stop when you want the current track
to end. Those are different instructions.

If the change invalidates the original goal, say so. Do not make the agent infer a
new scope from a passing comment, and do not accept a newly invented goal merely
because useful work was done on it.

**Next:** [make the checks meaningful](#rigor), [design the change](#design), or
[coordinate independent tracks](#coordination).
