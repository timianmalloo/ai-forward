# Make the important decisions before they become expensive

A small code change can hide a large decision. Adding a field may change what a
record means. Splitting a service may introduce a consistency boundary. Choosing an
AI model may affect cost, privacy and what can be reproduced.

AI-Forward separates problem definition, architecture and component design so that
you can inspect those decisions before implementation makes them harder to change.
You should not create all three artifacts by habit; use the level needed to settle
the actual uncertainty.

## Start with the problem, not the proposed mechanism

[Specification](#skill-specify) describes what users need and why. It considers
functional behavior, how people complete the task, and the interface where relevant.
If a layer does not apply, say why rather than silently omitting it.

[Architecture](#skill-define-architecture) settles responsibilities and load-bearing
boundaries across a system. [A design slice](#skill-design-slice) makes one component's
contracts, errors, data shape and test plan concrete.

For HarborTasks, “put a new button on the page” is not the whole export requirement.
The system must agree on which project, which filter, which fields and which rows
the button represents. The visible control is one surface of that decision.

## Model the meaning before the fields

The pack uses domain modelling to keep names and rules coherent:

- An **entity** has an identity that persists as its attributes change.
- A **value object** is described by its value, such as a date range or an amount
  with a currency, rather than by a separate identity.
- An **aggregate** is a small consistency boundary around a rule that must hold
  together, not a collection of everything related to a customer.
- A **bounded context** is an area in which a term has one agreed meaning.

In HarborTasks, a task's identity is not its title. A current task status and the
history of status changes answer different questions. Before adding storage, decide
whether a change should alter the meaning of an earlier report.

The pack favors an explicit history model: descriptive entities and recorded facts
about change, with derived totals computed from those facts. That is a deliberate
stance for auditability, not a claim that every application needs an analytical
warehouse. Record the representation you choose and why it suits the problem.

Declare the **grain**: what exactly does one row represent? For the illustrative CSV,
one row represents one matching task at export time. For a history table, one row
might represent one status transition. Mixing those meanings produces plausible
totals that answer the wrong question.

## Avoid two definitions of one quantity

If the export count is computed independently in the UI, service and export writer,
the definitions can diverge while each component's tests remain green. Prefer one
definition and check that the surfaces agree.

Where a value is cached for performance, make it rebuildable from its inputs and
verify that it equals the underlying calculation. Measure the need before creating
another persistent home for the same fact.

## Name the contracts and failure paths

A useful design says what a component accepts and returns, what it rejects, what it
does when a dependency fails, and how callers can tell. It also names which other
surfaces must agree: storage, model, service, wire representation, client and UI.

For export, consider empty results, malformed filters, authorization failures,
cancelled work and a file-format error. Ask how the person will recover, not just
which exception is thrown. Verify unfamiliar library behavior with a small experiment
before making the design depend on it.

## Use specialist perspectives deliberately

Personas are questions you bring to the work:

| Perspective | A useful question for the export |
|---|---|
| Product | Does this meet the person's actual reporting need? |
| Domain/data | Does each row have a clear meaning and correct history? |
| Security/privacy | Could another project's or an unnecessary private field be exported? |
| Test | What input makes a wrong implementation fail? |
| UX/accessibility | Can someone find, operate and recover from the export action? |
| Simplification | Are we building a reporting framework for a single bounded feature? |

Peers help form a design; adversaries challenge it. Independence matters more than
the number of named perspectives. The author does not resolve its own serious
review objection by declaring the work good enough.

## Where AI-integrated architecture applies

The pack's layered architecture guidance is relevant when the software being built
uses AI. It encourages keeping deterministic work deterministic, containing
probabilistic behavior behind clear boundaries, and selecting sufficient model
capability rather than the most expensive model by default.

The CSV serializer should not become an LLM call. Interpreting an ambiguous request
may benefit from a model; validating a schema or hashing a file belongs in ordinary
code. An AI-assisted development process does not imply an AI-powered product.

## Try a design slice

```text
/design-slice Design HarborTasks' CSV export from the approved specification.
Trace the active filter through the real query and download path. State the row
meaning, access boundary, empty-result behavior, failure recovery and test cases.
Reuse the current application structure unless it cannot satisfy the requirement.
```

In Codex, use `$design-slice`. A useful illustrative output names the contracts and
the checks that protect them, not just a preferred class diagram.

Before continuing, inspect assumptions about existing code, any new dependency,
the handling of stored data, and the failures the design proposes to accept.
Security, privacy and accessibility requirements are constraints on the solution,
not optional paragraphs to add after implementation.

**Next:** [implement a reviewed slice](#skill-implement), or return to
[problem framing](#skill-specify) if the intended behavior is still unsettled.
