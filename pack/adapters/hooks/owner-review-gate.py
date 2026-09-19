#!/usr/bin/env python3
"""owner-review-gate.py - a session may not stop while a decision request it sent is still open (D6).

At the stop seam the host runs this script. It resolves the session to `$AGENT_SESSION` (the
identity decision requests are written under - the harness `session_id` on stdin is a different
namespace and cannot find them), reads P1's request store through P1's own reader
(coord-core.py `read_request_events` + `fold_requests`) and, when that session has an unresolved
request with `reason: decision-request` that IT sent, refuses the stop with a reason that names the
count and the ids - never a body.

Hosts and shapes (pack/adapters/hooks/README.md; per-host status in its table):
  claude  Stop / SubagentStop  -> exit 2, one line on stderr (the host feeds it back as the reason)
  grok    same (Claude-format hooks)                                        observed-only
  copilot agentStop / subagentStop -> exit 0 + {"decision":"block","reason":T} on stdout
  agy     no stop event -> unsupported: exit 0, always

FAIL-SAFE (Security lens: never block on a path you cannot evaluate; the doorbell rule). Exit 0
and print nothing on: no AGENT_SESSION; stdin not JSON; `stop_hook_active` set (the host's loop
guard); coord-core.py not beside the pack; COORD_ROOT outside the repository; no requests store; a
store with a malformed line; requests sent by other sessions or merely addressed to this one; any
exception. Nothing on stdin is ever executed.

Usage: owner-review-gate.py --host claude|grok|copilot|agy [--event <name>] [--session <id>]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

HERE = Path(__file__).resolve().parent
REASON = "decision-request"
CLAUDE_FORMAT_HOSTS = ("claude", "grok")
COPILOT_STOP_EVENTS = ("agentStop", "subagentStop")
TEXT = ("owner-review: {count} unresolved decision request(s) sent by {session} ({ids}); "
        "rule it (coord decide rule) or let it expire (coord request expire) before stopping")


def _load_core() -> Optional[Any]:
    """coord-core.py sits in ../../scripts (pack source) or ../scripts (deployed bundle)."""
    for candidate in (HERE.parent.parent / "scripts" / "coord-core.py", HERE.parent / "scripts" / "coord-core.py"):
        if candidate.is_file():
            spec = importlib.util.spec_from_file_location("coord_core_for_owner_review", str(candidate))
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    return None


def open_decision_requests(core: Any, root: Path, session: str) -> List[str]:
    """Ids of the open decision requests `session` sent; [] when the store cannot be read."""
    events, errors = core.read_request_events(root)
    if errors:
        return []
    return [str(r["id"]) for r in core.fold_requests(events)
            if r.get("reason") == REASON and str(r.get("from") or r.get("session") or "") == session
            and r.get("status") in core.REQUEST_OPEN]


def reason_text(session: str, ids: List[str]) -> str:
    return TEXT.format(count=len(ids), session=session, ids=", ".join(ids))


def _event_of(explicit: Optional[str], payload: Dict[str, Any]) -> str:
    return str(explicit or payload.get("hook_event_name") or payload.get("hookEventName")
               or payload.get("event") or "")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", choices=["claude", "grok", "copilot", "agy"], required=True)
    parser.add_argument("--event", default=None)
    parser.add_argument("--session", default=None)
    args = parser.parse_args(argv)
    try:
        if args.host == "agy":
            return 0          # no stop event: unsupported, recorded in the README table
        session = args.session or os.environ.get("AGENT_SESSION") or ""
        if not session:
            return 0
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        try:
            payload = json.loads(raw or "{}")
        except ValueError:
            return 0
        if not isinstance(payload, dict):
            return 0
        if payload.get("stop_hook_active") or payload.get("stopHookActive"):
            return 0
        if args.host == "copilot" and _event_of(args.event, payload) not in COPILOT_STOP_EVENTS:
            return 0
        core = _load_core()
        if core is None:
            return 0
        root, err = core.resolve_root(os.getcwd(), os.environ.get("COORD_ROOT"))
        if err or root is None or not Path(core.request_log_path(root)).is_file():
            return 0
        ids = open_decision_requests(core, Path(root), session)
        if not ids:
            return 0
        text = reason_text(session, ids)
        if args.host == "copilot":
            print(json.dumps({"decision": "block", "reason": text}))
            return 0
        print(text, file=sys.stderr)
        return 2
    except Exception:  # noqa: BLE001 - a gate at the trust seam never blocks on a path it cannot evaluate
        return 0


if __name__ == "__main__":
    sys.exit(main())
