"""pack-onoff-analysis.html #3 (class PK-07): 4 of 54 pack-on cells in grid-1 and 4 in
grid-3 ran `git config user.*` in the TARGET repo so the agent could force a commit of pack
artifacts through -- no pack-off cell ever did. An invented identity is an attribution and
compliance risk, and a pack SCRIPT that falls back to setting one would train the same
behaviour mechanically. The standing rule (communication-and-task-discipline / the Audit
Mandate): never set a git identity; if a commit fails for a missing one, leave the change
uncommitted and say so.

This is the control, not the instance: a sweep over every pack script's SOURCE (never the
mirrors -- one fix covers all of them) that fails on any `git config user.*` outside a
documented, throwaway self-test fixture. The one legitimate occurrence today
(`conductor-join.py`'s `self_test()`, which only ever touches a `tempfile.TemporaryDirectory`
repo it created itself, never a caller's real repo) is named explicitly below; anything else
is a regression.
"""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO / "pack" / "scripts"

IDENTITY_PATTERN = re.compile(
    r'"config"\s*,\s*"user\.(?:email|name)"'      # git(args=["config", "user.email", ...])
    r'|git\s+config\s+user\.(?:email|name)\b',     # a shelled-out literal command string
    re.IGNORECASE,
)

# (filename, 1-based line number) -> why this one is not a violation. Each entry names the
# fixture it belongs to; anything not listed here that matches the pattern fails the sweep.
ALLOWED = {
    ("conductor-join.py", 638): "self_test() -- a throwaway tempfile.TemporaryDirectory repo "
                                 "the module creates and owns itself, never a caller's repo",
    ("conductor-join.py", 639): "self_test() -- see the line above",
    ("conductor-join.py", 837): "self_test()'s r2_case -- a throwaway tempfile.TemporaryDirectory repo",
    ("conductor-join.py", 838): "self_test()'s r2_case -- see the line above",
}


def _scan(root):
    offenders = []
    for path in sorted(root.glob("*.py")):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for lineno, line in enumerate(lines, 1):
            if IDENTITY_PATTERN.search(line):
                key = (path.name, lineno)
                if key not in ALLOWED:
                    offenders.append("{0}:{1}: {2}".format(path.name, lineno, line.strip()))
    return offenders


class NoScriptSetsGitIdentityTests(unittest.TestCase):
    def test_no_pack_script_sets_git_identity_outside_its_own_self_test_fixture(self):
        offenders = _scan(SCRIPTS_DIR)
        self.assertEqual(
            [], offenders,
            "a pack script must never run `git config user.*` against a caller's repo "
            "(class PK-07) -- found: " + "; ".join(offenders),
        )

    def test_the_sweep_actually_detects_a_violation(self):
        """Proves the control is live, not just vacuously green: a script that sets git
        identity outside the allowlist must be caught. Written against a throwaway copy,
        never the real tree."""
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            sandbox = Path(temp) / "scripts"
            sandbox.mkdir()
            (sandbox / "offender.py").write_text(
                'git(repo, "config", "user.email", "bot@example.invalid")\n',
                encoding="utf-8",
            )
            offenders = _scan(sandbox)
            self.assertEqual(
                1, len(offenders),
                "the sweep must flag an unlisted git-identity call -- it did not, so it "
                "would not have caught this defect class either",
            )

    def test_the_one_allowed_occurrence_still_matches_the_source_at_its_pinned_line(self):
        """Pins the allowlist to real content, not just a line number: if conductor-join.py
        is edited and the identity call moves or is reworded, this fails loudly instead of
        silently widening the allowlist's blind spot."""
        import ast

        path = SCRIPTS_DIR / "conductor-join.py"
        source = path.read_text(encoding="utf-8")
        lines = source.splitlines()
        # The function's real span, not a window above the line: the R2 cases sit deep inside it.
        body = next(node for node in ast.walk(ast.parse(source))
                    if isinstance(node, ast.FunctionDef) and node.name == "self_test")
        for (name, lineno), _why in ALLOWED.items():
            self.assertEqual("conductor-join.py", name)
            self.assertTrue(
                IDENTITY_PATTERN.search(lines[lineno - 1]),
                "ALLOWED line {0} no longer matches a git-identity call in {1} -- update the "
                "allowlist to the call's real location".format(lineno, name),
            )
            self.assertTrue(
                body.lineno < lineno <= body.end_lineno,
                "the allowed call at line {0} must still be inside self_test()".format(lineno),
            )


if __name__ == "__main__":
    unittest.main()
