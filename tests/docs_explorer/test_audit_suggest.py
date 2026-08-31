"""FR-071 (class SELF-REPORT). audit-log.py `suggest` listed every commit since the last
change-log entry with no filter, so it self-reported the very commit that recorded a change
entry (a logging closeout touches docs/audit/change-log.jsonl) and flooded with routine
commits - contrary to audit-and-change-log.md CL3, which surfaces only commits whose message
signals a decision (feat|BREAKING|migrate|arch|decision|adr).

These are seen failing on the pre-fix code: before the fix the logging-closeout and the
routine commit both surface; after the fix only the genuine unlogged decision surfaces.
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "docs" / "ai-forward-pack" / "scripts" / "audit-log.py"


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True,
                          capture_output=True, text=True)


def _commit(repo, message, files):
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        _git(repo, "add", rel)
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


class SuggestSelfReportTests(unittest.TestCase):
    def _run_suggest(self, repo):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(repo / "docs"), "suggest"],
            cwd=repo, capture_output=True, text=True, timeout=30,
        )

    def test_suggest_excludes_closeouts_and_non_decision_commits(self):
        with tempfile.TemporaryDirectory() as d:
            repo = pathlib.Path(d)
            # The control supplies its own git identity (CI-ENV): a fresh runner has none.
            _git(repo, "init", "-q")
            _git(repo, "config", "user.email", "t@example.com")
            _git(repo, "config", "user.name", "Test")
            _git(repo, "config", "commit.gpgsign", "false")

            base = _commit(repo, "chore: base", {"README.md": "x\n"})

            # A change-log entry whose git.after points at `base` (the pre-closeout sha).
            entry = {"id": "cl-0001", "title": "seed", "git": {"after": base}}
            line = json.dumps(entry) + "\n"
            (repo / "docs" / "audit").mkdir(parents=True, exist_ok=True)
            (repo / "docs" / "audit" / "change-log.jsonl").write_text(line, encoding="utf-8")

            # Commit B: the LOGGING CLOSEOUT - it records the change entry (touches the audit
            # .jsonl). suggest must NOT re-surface it (self-report).
            _commit(repo, "docs(audit): record decision cl-0001",
                    {"docs/audit/change-log.jsonl": line})
            # Commit C: a GENUINE unlogged decision (feat, no audit touch) - SHOULD surface.
            _commit(repo, "feat: add the widget", {"widget.py": "print(1)\n"})
            # Commit D: a routine, non-decision commit - must NOT flood.
            _commit(repo, "docs: fix a typo", {"README.md": "y\n"})
            # Commit E: a DECISION-worded commit that ALSO wrote the change log (a bundled
            # closeout). Its subject passes the CL3 message filter, so ONLY the logging-commit
            # filter can exclude it - it is already change-logged, so it must NOT surface.
            second = json.dumps({"id": "cl-0002", "title": "b", "git": {"after": base}}) + "\n"
            _commit(repo, "feat: bundled thing that logged itself",
                    {"impl.py": "print(2)\n", "docs/audit/change-log.jsonl": line + second})

            r = self._run_suggest(repo)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = r.stdout

            # The genuine unlogged decision surfaces.
            self.assertIn("add the widget", out,
                          f"a feat decision should be suggested. Output:\n{out}")
            # The logging closeout must NOT self-report.
            self.assertNotIn("record decision cl-0001", out,
                             f"a change-log closeout was self-reported (FR-071). Output:\n{out}")
            # The routine non-decision commit must NOT flood.
            self.assertNotIn("fix a typo", out,
                             f"a routine non-decision commit flooded suggest. Output:\n{out}")
            # A decision-worded commit that wrote the change log is already logged - excluded
            # by the logging-commit filter despite its feat subject.
            self.assertNotIn("bundled thing", out,
                             f"a bundled change-log closeout self-reported (FR-071). Output:\n{out}")


if __name__ == "__main__":
    unittest.main()
