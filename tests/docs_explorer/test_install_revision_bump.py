"""PACK-W. A change under `pack/` ships with a revision bump in `pack/adapters/INSTALL.md`.

INSTALL's own convention says every change to the bundle bumps `revision`, but nothing checked
it. On 2026-10-17 two changes to deployed files (the WT-D/WT-E hook fix and the Muse
re-measure) landed at revision 108. pack-apply finds a merge base from the commits whose
INSTALL text matches the installed copy, so revision 108 then named two different
`coord-core.py` and `context-budget.json`: an update from 108 refused with CONFLICT, and a
same-revision refresh kept the old hook as a "local deviation", so the fix could not reach a
consumer.

The check: the newest commit that touched `pack/` also touched `pack/adapters/INSTALL.md`.
Uncommitted edits are not judged; the gate runs on the tree that is about to be pushed.

Seen failing first on `332c297`, the tip after PR #12, whose last pack commit left INSTALL alone.
"""
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INSTALL = "pack/adapters/INSTALL.md"


def _last_commit(ref, path):
    out = subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%H", ref, "--", path],
                         capture_output=True, text=True, encoding="utf-8")
    return out.stdout.strip() if out.returncode == 0 else None


def unbumped_pack_commit(ref="HEAD"):
    """The newest commit at `ref` that changed pack/ without INSTALL.md, else None."""
    pack, install = _last_commit(ref, "pack"), _last_commit(ref, INSTALL)
    if not pack or not install:
        return None
    return None if pack == install else pack


class InstallRevisionBumpTests(unittest.TestCase):
    def setUp(self):
        if not (REPO / ".git").exists() or _last_commit("HEAD", "pack") is None:
            self.skipTest("no git history for pack/")

    def test_the_newest_pack_change_carries_an_install_revision(self):
        sha = unbumped_pack_commit()
        self.assertIsNone(sha, "commit {} changed pack/ without {}: bump `revision`, write this "
                          "revision's `changes`, archive the previous ones".format(sha, INSTALL))


if __name__ == "__main__":
    unittest.main()
