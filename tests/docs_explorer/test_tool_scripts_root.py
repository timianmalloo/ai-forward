"""PLAT-E. A repo tool invoked by absolute path must not take its target from the caller's cwd.

`tools/sync-pack.ps1` resolved every script from its own location but ran
`docs-graph.py derive` with no `--root`, and docs-graph defaults to `<cwd>/docs`. Run from
another checkout (a linked worktree synced from the primary's shell), sync re-derived the
OTHER tree's index and left this one stale; the stale `docs-index.js` was committed and only
CI's drift gate saw it (2026-10-17, run 39068149939).

Seen failing first on the sync-pack.ps1 that ran derive without `--root`.
"""
import re
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / "tools"
_CALL = re.compile(r"&\s*\$pyExe\s+@pyArgs\s+(\$\w+|\([^)]*\))\s+(.*)")


class ToolScriptRootTests(unittest.TestCase):
    def test_every_docs_graph_call_names_its_root(self):
        calls = []
        for script in sorted(TOOLS.glob("*.ps1")):
            text = script.read_text(encoding="utf-8")
            graph_vars = set(re.findall(r"(\$\w+)\s*=\s*Join-Path\s+\$repo\s+\"docs/ai-forward-pack/scripts/docs-graph\.py\"", text))
            for number, line in enumerate(text.splitlines(), 1):
                match = _CALL.search(line)
                if match and (match.group(1) in graph_vars or "docs-graph.py" in match.group(1)):
                    calls.append((script.name, number, line.strip()))
        self.assertTrue(calls, "no docs-graph.py call found; the pattern above no longer matches the tools")
        for name, number, line in calls:
            with self.subTest(at="{}:{}".format(name, number)):
                self.assertIn("--root", line, "docs-graph.py defaults to <cwd>/docs; pass --root")


if __name__ == "__main__":
    unittest.main()
