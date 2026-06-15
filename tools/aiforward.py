#!/usr/bin/env python3
"""aiforward.py — the AI-Forward pack developer CLI (a thin Facade over tools/ + scripts/).

One memorable entry point that dispatches to the pack's existing scripts so a contributor
does not have to remember which file does what. It adds NO behavior of its own — every
subcommand shells out to a script that already owns it, and the child's exit code is
propagated unchanged (so `aiforward verify` is CI-usable exactly like verify-bundle.ps1).

Design: docs/design/aiforward-cli.md. Stdlib only; not deployed into target repos (it is a
source-repo developer convenience — the deployable health/scrub scripts are pack/scripts/).

Usage
  aiforward <command> [args...]
  aiforward --help

Commands
  verify    prove the bundle is consistent          -> pwsh tools/verify-bundle.ps1
  sync      regenerate both tool surfaces            -> pwsh tools/sync-pack.ps1
  check     count/skill-list consistency             -> python tools/check-consistency.py
  new       scaffold a new capability                -> python tools/new-capability.py
  doctor    install-health of THIS repo              -> python <scripts>/pack-doctor.py
  graph     knowledge-graph mechanics                -> python <scripts>/docs-graph.py
  scrub     redact obvious PII/secrets (first-pass)  -> python <scripts>/scrub.py
"""
import os, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _graph_dir():
    """Resolve the script bundle: pack/scripts (source repo) or docs/ai-forward-pack/scripts (install)."""
    for cand in (os.path.join(REPO, "pack", "scripts"),
                 os.path.join(REPO, "docs", "ai-forward-pack", "scripts")):
        if os.path.isdir(cand):
            return cand
    return None


def _py(rel_or_abs):
    return [sys.executable, rel_or_abs]


# Pattern: Command dispatch table — name -> a builder of the child argv (no logic, just routing).
def _build(cmd):
    g = _graph_dir()
    tools = os.path.join(REPO, "tools")
    table = {
        "verify": lambda: ("pwsh", [os.path.join(tools, "verify-bundle.ps1")]),
        "sync":   lambda: ("pwsh", [os.path.join(tools, "sync-pack.ps1")]),
        "check":  lambda: (sys.executable, [os.path.join(tools, "check-consistency.py")]),
        "new":    lambda: (sys.executable, [os.path.join(tools, "new-capability.py")]),
        "doctor": lambda: (sys.executable, [os.path.join(g, "pack-doctor.py")] if g else None),
        "graph":  lambda: (sys.executable, [os.path.join(g, "docs-graph.py")] if g else None),
        "scrub":  lambda: (sys.executable, [os.path.join(g, "scrub.py")] if g else None),
    }
    return table.get(cmd)


HELP = __doc__


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(HELP)
        return 0
    cmd, rest = argv[0], argv[1:]
    builder = _build(cmd)
    if builder is None:
        sys.stderr.write(f"aiforward: unknown command '{cmd}'. Run 'aiforward --help'.\n")
        return 2
    exe, args = builder()
    if args is None:
        sys.stderr.write(f"aiforward: '{cmd}' needs the script bundle (pack/scripts or "
                         f"docs/ai-forward-pack/scripts), which was not found.\n")
        return 2
    target = args[0]
    if not os.path.exists(target):
        sys.stderr.write(f"aiforward: target script not found: {target}\n")
        return 2
    try:
        # argv as a list, no shell=True -> no shell interpolation of user args.
        return subprocess.run([exe, *args, *rest], cwd=REPO).returncode
    except FileNotFoundError:
        manual = " ".join([exe, *[os.path.relpath(a, REPO) if os.path.isabs(a) else a for a in args], *rest])
        sys.stderr.write(
            f"aiforward: '{exe}' not found. Install it, or run manually:\n  {manual}\n"
            + ("  (the 'verify'/'sync' commands need PowerShell 7 — https://aka.ms/powershell)\n"
               if exe == "pwsh" else ""))
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
