"""`coord regen` writes a derived file into the INVOKING checkout, never the primary.

The regen debt and the registry are repository-wide (they live in the shared coordination store), but
the generated file belongs to the checkout that ran the command. Before the fix, `coord regen` from a
linked worktree ran the generator with cwd = the primary checkout (the store's owner), so the primary
gained an unasked-for change and the worktree kept the stale file. Upstreamed from CFD-Workbench.
"""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
CORE = REPO / "pack" / "scripts" / "coord-core.py"
SPEC = importlib.util.spec_from_file_location("coord_core_regen_checkout_test", CORE)
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)

GENERATED = "docs/audit/audit-data.js"


def run(argv, cwd, env=None):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", check=False, timeout=120)
    if result.returncode:
        raise AssertionError("{0} exited {1}: {2}{3}".format(argv[:3], result.returncode, result.stdout, result.stderr))


class RegenCheckoutTests(unittest.TestCase):
    def test_regen_from_a_linked_worktree_writes_there_and_leaves_the_primary(self):
        with tempfile.TemporaryDirectory(prefix="coord-regen-checkout-") as directory:
            base = Path(directory)
            primary, linked = base / "primary", base / "linked"
            primary.mkdir()
            run(["git", "init", "-q"], primary)
            (primary / "docs" / "audit").mkdir(parents=True)
            (primary / GENERATED).write_text("original\n", encoding="utf-8", newline="\n")
            (primary / "generate.py").write_text(
                "from pathlib import Path\n"
                "Path('docs/audit/audit-data.js').write_text('regenerated\\n', encoding='utf-8', newline='\\n')\n",
                encoding="utf-8", newline="\n")
            (primary / ".agents").mkdir()
            (primary / ".agents" / "artifacts.yml").write_text(
                GENERATED + ": derived python generate.py\n", encoding="utf-8", newline="\n")
            run(["git", "add", "-A"], primary)
            run(["git", "-c", "user.name=Regen Test", "-c", "user.email=regen@example.invalid", "-c", "commit.gpgsign=false",
                 "commit", "-q", "-m", "fixture"], primary)
            run(["git", "worktree", "add", "-q", "-b", "linked", str(linked)], primary)
            store = primary / ".agents"
            core.record_regen_owed(store, GENERATED)
            env = dict(os.environ, AGENT_SESSION="coord-regen-test", AGENT_HOST="codex")

            run([sys.executable, str(CORE), "regen"], linked, env=env)

            self.assertEqual("original\n", (primary / GENERATED).read_text(encoding="utf-8"),
                             "regen from a linked worktree rewrote the primary checkout's file")
            self.assertEqual("regenerated\n", (linked / GENERATED).read_text(encoding="utf-8"),
                             "regen did not write the invoking worktree's file")
            self.assertFalse(core.regen_owed(store), "the debt was not cleared")


if __name__ == "__main__":
    unittest.main()
