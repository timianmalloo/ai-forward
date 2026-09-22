# Create committed visual assets, not generated interfaces

Use this skill to produce imagery, fictional personas, direction boards or motion that a surface displays. It never generates the interface itself.

## When to use it

Use `visualize` after a surface or direction brief exists and the missing piece is visual content. Do not use it to “make the UI” or to generate screenshots of controls, forms, menus, charts or native windows.

## What you need

You need the surface, slot list, design language, budget and a confirmed generation backend or other asset source. The skill must check entitlement before planning around a provider.

## Try it

Slash-command harnesses:

```text
/visualize Create a direction board for the HarborTasks export success panel.
No UI chrome, no readable text, no real people.
```

Codex equivalent:

```text
$visualize Create a direction board for the HarborTasks export success panel.
```

## What happens

The skill writes the visual register in words, checks backend availability, generates candidates into scratch space only when permitted, culls them, optimizes survivors and records provenance, prompt, cost, alt text and licensing.

## What you get

Illustrative artifact shape:

```text
docs/assets/export/success-illustration.webp
DESIGN.md assets entry:
  purpose, file, backend, prompt, cost, alt text, licence check
```

These are illustrative output shapes, not a claim that generation was run here.

## Review before continuing

Reject assets with invented UI, unreadable text, real likenesses, missing alt text, unclear license, or provider URLs instead of committed files.

## Tips and recovery

If no backend is confirmed, stop rather than describing images. If the page layout is weak, run [ui-design](#skill-ui-design) first; imagery will not fix structure.

## Where to go next

Use [implement](#skill-implement) to wire approved assets, or [document](#skill-document) if the visual direction changes public documentation.
