#!/usr/bin/env python3
"""primary-guard.py -- PRIM-A's control: a session in a linked worktree never writes the primary
checkout unnoticed.

Two parts, because a Write/Edit hook alone misses the shape that fired the register's upgrade
trigger (a shell's .NET call with a relative path):

  (a) PREVENTIVE -- `--event PreToolUse` on Write, Edit and NotebookEdit. A path under the primary
      checkout (the parent of `git rev-parse --git-common-dir`) from a session whose own working
      tree is a DIFFERENT worktree is refused: exit 2, reason on stderr.
  (b) DETECTIVE, for shell writes -- `--event SessionStart` snapshots
      `git -C <primary> status --porcelain=v1 --untracked-files=all` (session-start.py calls it);
      `--event PostToolUse` on Bash and PowerShell compares and, on any change, tells the session
      the delta at once as `additionalContext`. A warning, not a block: a hook cannot undo a
      write, and the Leader's own fast-forward also changes the primary, so the message names
      that case. A reported delta becomes the new baseline, so it is reported once.

Every call appends one row to `<git common dir>/aif-primary-guard-times.jsonl` (event, tool,
decision, ms): the hook's own cost is measured, never assumed (IO). Every path fails open: an
unreadable payload, no git, or any error allows the call and exits 0.

Wired for Claude Code only: it is the one adapter registering both PreToolUse and PostToolUse
here. Grok has no PostToolUse registration, Copilot's payload names differ and Antigravity's
PreToolUse deny contract is unobserved, so none of them is guessed at.

Usage: primary-guard.py --host claude|grok --event PreToolUse|PostToolUse|SessionStart
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time

for _stream, _kw in ((sys.stdin, {"encoding": "utf-8", "errors": "replace"}),
                     (sys.stdout, {"encoding": "utf-8", "errors": "replace"}),
                     (sys.stderr, {"encoding": "utf-8", "errors": "replace"})):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(**_kw)
        except (ValueError, OSError, UnicodeError):
            pass

WRITE_TOOLS = ("Write", "Edit", "NotebookEdit")
SHELL_TOOLS = ("Bash", "PowerShell")
PATH_KEYS = ("file_path", "notebook_path", "path")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _git(cwd, *args):
    result = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, encoding="utf-8",
                            timeout=8, creationflags=NO_WINDOW)
    return result.stdout.strip() if result.returncode == 0 else None


def _norm(path):
    return os.path.normcase(os.path.realpath(path))


def _under(path, root):
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def trees(cwd):
    """(own working tree, primary checkout, git common dir), all normalised; None when not in a git tree."""
    top = _git(cwd, "rev-parse", "--show-toplevel")
    common = _git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not top or not common:
        return None
    return _norm(top), _norm(os.path.dirname(os.path.realpath(common))), os.path.realpath(common)


def primary_status(primary):
    return _git(primary, "status", "--porcelain=v1", "--untracked-files=all")


def _snapshot_path(common, session_id):
    return os.path.join(common, "aif-primary-snapshot-" + re.sub(r"[^A-Za-z0-9._-]", "_", session_id or "unknown"))


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def refuse_write(payload, cwd):
    """The reason string when a Write/Edit/NotebookEdit targets the primary from another tree, else None."""
    tool_input = payload.get("tool_input") or {}
    raw = next((tool_input[k] for k in PATH_KEYS if isinstance(tool_input.get(k), str) and tool_input[k]), None)
    found = trees(cwd)
    if raw is None or found is None:
        return None
    own, primary, _common = found
    target = _norm(raw if os.path.isabs(raw) else os.path.join(cwd, raw))
    if own == primary or not _under(target, primary) or _under(target, own):
        return None
    return (f"primary-guard (PRIM-A): {raw} is under the primary checkout {primary}, but this session's "
            f"working tree is {own}. Write in your own worktree; a change to the primary is the "
            "Leader's merge, never a worker's edit.")


def take_snapshot(session_id, cwd):
    """SessionStart: record the primary's status for a session in a linked tree."""
    found = trees(cwd)
    if found is None or found[0] == found[1]:
        return "skipped"
    status = primary_status(found[1])
    if status is None:
        return "skipped"
    _write(_snapshot_path(found[2], session_id), status)
    return "snapshot"


def shell_delta(session_id, cwd):
    """PostToolUse: the report text when the primary's status differs from the snapshot, else None."""
    found = trees(cwd)
    if found is None or found[0] == found[1]:
        return None
    path = _snapshot_path(found[2], session_id)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        before = handle.read()
    now = primary_status(found[1])
    if now is None or now == before:
        return None
    _write(path, now)
    old, new = set(before.splitlines()), set(now.splitlines())
    delta = [f"+ {line}" for line in sorted(new - old)] + [f"- {line}" for line in sorted(old - new)]
    return (f"primary-guard (PRIM-A): the primary checkout {found[1]} changed since this session started "
            f"(git status delta):\n" + "\n".join(delta) + "\nIf this session did not mean to write there, a "
            "shell command with a relative path may have; undo it. The Leader's own fast-forward of the "
            "primary also changes it, and is the expected case.")


def record(common, event, host, tool, decision, started, session_id):
    row = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "hook": "primary-guard",
           "event": event, "host": host, "tool": tool, "decision": decision, "session": session_id,
           "ms": round((time.perf_counter() - started) * 1000, 3)}
    with open(os.path.join(common, "aif-primary-guard-times.jsonl"), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=["claude", "grok"], required=True)
    parser.add_argument("--event", choices=["PreToolUse", "PostToolUse", "SessionStart"], required=True)
    args = parser.parse_args(argv)
    started = time.perf_counter()
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    cwd = str(payload.get("cwd") or os.getcwd())
    session_id = str(payload.get("session_id") or payload.get("sessionId") or "")
    tool = str(payload.get("tool_name") or "")
    decision, code, reason = "none", 0, None
    if args.event == "PreToolUse" and tool in WRITE_TOOLS:
        reason = refuse_write(payload, cwd)
        decision, code = ("refused", 2) if reason else ("allowed", 0)
        if reason:
            print(reason, file=sys.stderr)
    elif args.event == "PostToolUse" and tool in SHELL_TOOLS:
        reason = shell_delta(session_id, cwd)
        decision = "reported" if reason else "unchanged"
        if reason:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": reason}}))
    elif args.event == "SessionStart":
        decision = take_snapshot(session_id, cwd)
    found = trees(cwd)
    if found is not None and decision != "none":
        try:
            record(found[2], args.event, args.host, tool, decision, started, session_id)
        except OSError:
            pass
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - a guard must never break the host's tool call
        sys.exit(0)
