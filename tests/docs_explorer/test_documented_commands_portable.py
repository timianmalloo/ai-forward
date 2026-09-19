"""Documented commands under pack/ run in any shell (PLAT-A; cross-platform readiness P4).

Observed RED before the rewrite it pins (2026-09-19, this repo, main @ a01ed77): the gate
`pack/scripts/verify-documented-commands.py` found backslash continuations, ` && ` chains and
line-initial bare `python` inside documented command blocks (the investigation's XS-01..25;
the red-first count is recorded in docs/notes/note-20260919-xp-cross-platform.md).

SCAN CONTRACT (GO14a) - the test asserts the gate's scan and the gate carries the same words:
  root       <repo>/pack
  recursion  commands/**/*.md, knowledge/*.md, adapters/INSTALL.md, templates/*.md
  blocks     fenced ``` / ~~~ blocks whose info string is empty or bash, sh, shell, zsh;
             a block whose first line is a shebang is a file (DC-207) and is skipped;
             blank and `#` comment lines are skipped
  tokens     continuation (line ends in whitespace + `\\`), and-chain (` && `),
             bare-python (first token `python`, optionally after a `$ ` prompt)
  allowlist  an inline `portable-ok: <reason>` marker on the line (a marker with no reason
             is itself a finding)
"""
import importlib.util
import pathlib
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
GATE = REPO / "pack" / "scripts" / "verify-documented-commands.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("verify_documented_commands", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DocumentedCommandsPortableTests(unittest.TestCase):
    def setUp(self):
        self.gate = load_gate()

    def test_every_documented_command_under_pack_is_single_line_unchained_and_python3(self):
        findings = self.gate.scan(REPO)
        lines = "\n".join("  {0}:{1}  {2:<14}{3}".format(f.path, f.lineno, f.token, f.line)
                          for f in findings)
        self.assertEqual([], findings,
                         "{0} portability finding(s) in documented commands under pack/:\n{1}"
                         .format(len(findings), lines))

    def test_the_gate_can_fail_on_each_shape_and_honours_the_marker(self):
        """DC-104: a gate that cannot go red proves nothing. Mirrors the gate's --self-test."""
        self.assertEqual(0, self.gate.self_test())

    def test_the_scan_contract_in_this_docstring_matches_the_gate(self):
        self.assertEqual(("commands/**/*.md", "knowledge/*.md", "adapters/INSTALL.md", "templates/*.md"),
                         self.gate.ROOT_GLOBS)
        self.assertEqual(frozenset({"", "bash", "sh", "shell", "zsh"}), self.gate.COMMAND_LANGS)
        self.assertEqual("portable-ok:", self.gate.MARKER)

    def test_a_consuming_repo_without_pack_is_reported_not_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(0, self.gate.main(["--root", tmp]))


if __name__ == "__main__":
    unittest.main()
