# Build with AI agents without losing engineering discipline

AI coding agents can turn a short request into a lot of work. The harder part is
deciding whether they understood the problem, made sound choices, and produced
something you can safely keep. AI-Forward gives that work a repeatable engineering
method.

It is a pack you add to a repository. The pack provides guidance the agent can read,
reusable workflows called **skills**, specialist review perspectives called
**personas**, and local tools for tasks such as recording decisions and coordinating
work. You continue to choose the outcome, review consequential decisions, and accept
or reject the result.

AI-Forward is not a new AI model or a hosted agent service. It does not make an agent
infallible. It helps you ask better questions, keep useful context, and make the
important checks visible.

## Start with the problem you have

**“It produces plausible code, but I do not trust the result.”** Start with
[making work trustworthy](#rigor). Learn how to turn assumptions into questions and
require an observable result rather than accepting a confident explanation.

**“My requests grow into work I did not ask for.”** Read
[from request to reviewed change](#workflow). Learn how to state a finish line,
make exclusions explicit, and choose an appropriate workflow.

**“Several agents keep stepping on each other's work.”** Read
[coordinate work without losing ownership](#coordination). Begin with a clear
division of work, not with a larger number of agents.

**“We rediscover the same decisions every session.”** Read
[keep project knowledge useful](#knowledge). Keep intent, decisions and documentation
in the project, where later work can find and question them.

If you are ready to try the pack, [start with one small task](#get-started). You do not
need a swarm or an elaborate project plan to begin.

## The basic working relationship

You provide the problem, constraints and what a useful outcome looks like. The agent
uses the repository's instructions and a suitable skill to work through that request.
You inspect the important decisions and returned artifacts before relying on them.

For example, suppose your team maintains **HarborTasks**, a small task-tracking
service. You ask for CSV export. A fast implementation might export the twenty rows
currently on screen. A useful first question is whether you meant those rows or
every task matching the current filter. AI-Forward is meant to make that question
part of the work, before the implementation hardens around an unchecked assumption.

HarborTasks is an illustrative example used throughout this handbook, not a bundled
application or a claim that these sample outputs were produced by a live run.

## A few terms before you begin

- A **model** produces the AI's responses.
- A **harness** is the application that gives it tools, a workspace and interaction
  controls: for example Claude Code, GitHub Copilot, Codex, Grok Build or Antigravity.
- An **instruction** is guidance the harness makes available to the agent.
- A **skill** is a reusable workflow for a kind of work, such as specifying a feature
  or investigating a defect.
- A **persona** is a specialist perspective, such as a test architect or security
  reviewer. It is a role in the work, not necessarily another process.
- A **script** performs a concrete operation. It is not interchangeable with a skill:
  a workflow can guide judgment while calling scripts for mechanical steps.
- An **artifact** is something the work leaves behind: a specification, a design,
  code, tests, a decision, or a useful piece of documentation.

The repository you are reading develops AI-Forward and also uses the pack on itself.
Most adopters do not need to develop the pack; they install it into their own project.

## Use only the structure the task needs

A comment correction does not need the same process as an authentication change.
One well-scoped agent is often better than several agents waiting on one another.
The point is to protect the decisions and checks that matter, not to make every
task look like a large programme.

The pack's workflows also have limits. A declared review is not the same as an
independent review. A test suite is not proof that a real user-facing path works.
An installed hook is not proof that a harness executed it. The relevant guides show
what to inspect and where setup or further qualification is needed.

**Your next step:** [install the pack and complete a first task](#get-started).
If it is already installed, [choose a workflow from the work you need to do](#skills).
