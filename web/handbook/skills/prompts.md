# Reuse a past prompt from the project log

Use this utility to browse logged prompts newest-first and copy one for paste-and-edit. It is a reuse lens over the audit log, not a command that reruns work automatically.

## When to use it

Use `prompts` when you remember that a useful request was used before but do not know its exact wording. Use [searchprompts](#skill-searchprompts) when you know terms to filter by.

## What you need

The prompt must have been logged. The pack encourages logging substantive prompts, but no CLI hook captures every prompt automatically.

## Try it

Slash-command harnesses:

```text
/prompts
```

Codex equivalent:

```text
$prompts
```

Fallback script shape:

```text
python docs/ai-forward-pack/scripts/prompt-log.py browse
```

## What happens

The skill opens an interactive stack when a terminal supports it: move with arrow keys, expand with right arrow, collapse with left arrow, and press Enter to copy. Without a terminal, it prints a numbered list.

## What you get

Illustrative output shape:

```text
1  2026-09-20  Specify HarborTasks CSV export
2  2026-09-18  Investigate export paging bug
```

The chosen prompt is copied or printed for you to edit before sending.

## Review before continuing

Make sure the reused prompt still matches today's task. A good old prompt can carry stale scope, paths or assumptions.

## Tips and recovery

If nothing appears, add important prompts explicitly with `prompt-log.py add`. If you need the broader activity timeline, use [auditlog](#skill-auditlog).

## Where to go next

Paste and edit the prompt into the next workflow, or use [compile](#skill-compile) before dispatching it to a worker.
