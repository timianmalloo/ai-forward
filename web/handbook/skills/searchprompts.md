# Search past prompts by terms

Use this utility when you remember words from a previous prompt and want to reuse the exact text. It is the filtered companion to [prompts](#skill-prompts).

## When to use it

Use `searchprompts` for prompt reuse by keyword, such as “export paging” or “authorization CSV.” It should not execute the result for you.

## What you need

You need a prompt log. Matches contain all supplied terms, case-insensitive.

## Try it

Slash-command harnesses:

```text
/searchprompts export authorization
```

Codex equivalent:

```text
$searchprompts export authorization
```

Fallback script shape:

```text
python docs/ai-forward-pack/scripts/prompt-log.py search export authorization
```

## What happens

The skill filters the same newest-first stack that `prompts` uses. In an interactive terminal you can expand, collapse and copy; otherwise it prints matches for selection.

## What you get

Illustrative output shape:

```text
2 matches
1  Specify HarborTasks CSV export with authorized fields
2  Investigate export authorization regression
```

## Review before continuing

Read the full prompt before reuse. Search terms can find an old rejected approach as easily as an approved one.

## Tips and recovery

If no matches appear, broaden the terms or use [auditlog](#skill-auditlog) to search all entries, not only prompts.

## Where to go next

Reuse the copied prompt directly, or run [compile](#skill-compile) if it will be delegated or coordinated.
