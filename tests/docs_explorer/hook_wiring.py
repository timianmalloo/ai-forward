"""Which pack hooks a shipped hook config runs per host event, read through the dispatcher (B15).

Since revision 101 every config registers `run-hook.sh dispatch.py --host <h> --event <e>` once per
event, and `dispatch.py`'s ROUTES says which hooks that runs. Tests that ask "does host X run hook Y
at event E" read both halves here, so the answer follows the config AND the dispatcher table.
"""
import importlib.util
import json
import re
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[2] / "pack" / "adapters" / "hooks"
CONFIGS = {"claude": "claude-code.settings.hooks.json", "grok": "grok.ai-forward-hooks.json",
           "copilot": "copilot.ai-forward-hooks.json", "agy": "agy.ai-forward-hooks.json"}
_DISPATCH = re.compile(r"run-hook\.sh dispatch\.py --host (\w+) --event (\w+)$")


def routes():
    spec = importlib.util.spec_from_file_location("hook_wiring_dispatch", str(HOOKS / "dispatch.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ROUTES


def commands(host, hooks_dir=HOOKS):
    """[(event, matcher or None, command)] for every handler in the host's config."""
    config = json.loads((Path(hooks_dir) / CONFIGS[host]).read_text(encoding="utf-8"))
    out = []
    if host in ("claude", "grok"):
        for event, entries in config["hooks"].items():
            out += [(event, e.get("matcher"), h["command"]) for e in entries for h in e["hooks"]]
    elif host == "copilot":
        for event, entries in config["hooks"].items():
            out += [(event, h.get("matcher"), h["bash"]) for h in entries]
    else:
        for section in config.values():
            for event, entries in section.items():
                if isinstance(entries, list):
                    for e in entries:
                        out += [(event, e.get("matcher"), h["command"]) for h in (e["hooks"] if "hooks" in e else [e])]
    return out


def wired(host, event):
    """[(script, argv)] the host's config runs at `event`, in order."""
    table = routes()
    out = []
    for ev, _matcher, command in commands(host):
        match = _DISPATCH.search(command)
        if ev == event and match and match.groups() == (host, event):
            out += table[host][event]
    return out


def wired_scripts(host, event):
    return [script for script, _argv in wired(host, event)]
