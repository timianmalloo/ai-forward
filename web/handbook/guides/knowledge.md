# Keep project knowledge useful after the session ends

A productive session can still leave a project harder to continue. The reasoning is
buried in chat, a design no longer matches the code, and the next person has to
rediscover which assumptions were checked. AI-Forward keeps useful knowledge in the
repository so that future work has a starting point.

The goal is not to save everything. It is to preserve the intent, decisions and
explanations that someone will need, without turning the project into an unreadable
archive or retaining unnecessary sensitive material.

## Give each record a job

A specification explains the desired behavior. A design explains the chosen shape
and its important contracts. A decision record explains a choice and its consequences.
Tests and verification records explain what was actually checked. Documentation
explains the implemented system to a reader.

An audit log is different again: it records activity. It can help recover a prompt
or understand a sequence, but it is not a substitute for an explanatory guide.

For HarborTasks, preserve the decision that export includes all matching tasks rather
than only the 20 visible rows. The next engineer should not need to read a long chat
to discover why the query traverses multiple pages.

## Maintain a map rather than a folder maze

The **Docs Explorer** is a navigable map of repository artifacts. Documents carry
metadata and typed relationships so you can follow a design to its specification,
an implementation claim to its checks, or a decision to its consequences.

The map is derived from the documents. It should not become a second place where
someone manually maintains competing descriptions. When a document changes materially,
its dependents may need review; a valid link does not mean the linked claim is still current.

Use [document](#skill-document) for the documentation bundle and a full index refresh.
It can include API reference, architecture explanations and diagrams, while identifying
gaps rather than inventing documentation for code that has none.

```text
/document Refresh the documentation for HarborTasks' export feature. Explain
the user-visible behavior, the filter/query/download path, and known limits.
Keep the project overview and affected diagrams current.
```

In Codex, use `$document`. Inspect the rendered result as well as the source files:
a Markdown file can exist without a working public link or readable diagram.

## Distinguish intent from code relationships

The documentation graph records intent and traceability. A **code knowledge graph**
records relationships found in implementation, such as symbols, imports and calls.
Comparing the two can reveal an undocumented implementation or a design promise with
no code behind it.

Graphify is an optional integration for the code side. Its extracted relationships
and inferred relationships do not carry the same certainty. A graph is a way to
find what to inspect, not permission to treat every suggested edge as fact.

Obsidian is an optional reading and exploration lens over the Markdown knowledge base.
It does not replace canonical documents or the tools that derive the graph. Use it
if its navigation helps you; it is not required to use the pack.

Neither integration is an additional bundled skill in the handbook's skill inventory.
They are capabilities described by the pack's knowledge guidance and setup tools.

## Recover earlier work without replaying it blindly

Use [auditlog](#skill-auditlog) to find what was done or decided, and
[prompts](#skill-prompts) or [searchprompts](#skill-searchprompts) to recover a useful
request. Reuse should mean inspect, edit for the current situation, then submit—not
automatically rerun an old action with old assumptions.

For example, find the earlier export specification prompt, update it for a new format,
and check whether the old access and row-selection decisions still apply. A remembered
prompt is a starting point, not a current authorization.

## Keep the record safe and worth reading

Do not commit credentials, unnecessary personal data or private customer content.
Raw logs and model transcripts can contain work material even when their file names
look harmless. Keep operational/private records out of the public publishing surface.

Prefer a concise decision with a reason over copied conversation. Keep the rejected
alternative when it explains a constraint someone is likely to question later.
Correct overstatements visibly rather than presenting old claims as current facts.

## A useful continuation check

Before handing the project to another session or person, ask whether they can find:

1. the current outcome and exclusions;
2. the important decisions and unresolved questions;
3. the code and checks associated with the change;
4. the known limitations;
5. the next concrete action.

If they need unpublished chat to answer those questions, the knowledge handoff is
incomplete. More archived messages will not necessarily fix it.

**Next:** [turn recurring observations into improvements](#improvement), or
[refresh the documentation bundle](#skill-document).
