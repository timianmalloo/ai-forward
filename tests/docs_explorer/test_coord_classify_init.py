"""coord classify init — the registry is derivable, not authored (CTX-H, proposal P1).

The five artifacts the pack itself generates are the SAME obligation in every repo it is
installed into. Asking each repo to hand-author them is asking each repo to repeat the same
near-miss: the cfd-bench coordination plan first wrote `audit-log.py regen` from inference,
and there is no such subcommand — it is `render`.

That near-miss is the whole reason this command runs the regenerate command BEFORE writing
it. A *wrong* regenerate command is worse than a missing entry: the merge resolves silently,
`merge-derived` records a regeneration owed, `coord regen` then fails forever, and until
someone reads the output the artifact is permanently stale while every tool reports it as
handled. `load_registry` already refuses a `derived` entry with NO command; it cannot refuse
one with the wrong command. This does.

Written to fail first: every test here failed with AttributeError (no `cmd_classify_init`)
on 2026-09-06 before the command existed.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "pack" / "scripts" / "coord-core.py"


def load_module():
    spec = importlib.util.spec_from_file_location("coord_core", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InitCase(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "r"
        self.repo.mkdir(parents=True)
        self.git("init", "-q")
        self.git("config", "user.email", "t@t")
        self.git("config", "user.name", "t")
        self.root = self.repo / ".agents"
        self.root.mkdir()

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=str(self.repo), check=check,
                              capture_output=True, text=True)

    def write(self, rel, body=""):
        target = self.repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8", newline="\n")
        return target

    def commit_all(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "fixture")

    def registry_text(self):
        path = self.root / self.m.REGISTRY_NAME
        return path.read_text(encoding="utf-8") if path.exists() else None

    def init(self, candidates=None, force=False):
        return self.m.cmd_classify_init(str(self.root), str(self.repo),
                                        candidates=candidates, force=force)

    def _writer(self, target, extra=None):
        """A regenerate command that rewrites `target` (and optionally something else)."""
        paths = [target] + ([extra] if extra else [])
        body = ";".join(
            "open(r'{0}','w').write('regenerated')".format(self.repo / p) for p in paths)
        return '"{0}" -c "{1}"'.format(sys.executable, body)


class DefaultsTests(InitCase):
    def test_it_writes_a_register_entry_for_a_pack_artifact_that_exists(self):
        self.write("docs/audit/audit-log.jsonl", '{"id":"a"}\n')
        self.commit_all()
        code = self.init()
        text = self.registry_text()
        self.assertIsNotNone(text, "classify init must write the registry")
        self.assertIn("docs/audit/audit-log.jsonl: register", text)
        self.assertEqual(code, 0)

    def test_it_does_not_enumerate_artifacts_this_repo_does_not_have(self):
        """`# everything else stays authored by default. Do not enumerate it.`

        A registry naming a path that does not exist is a claim about the repo that nothing
        checks — and the pattern would silently start matching the day someone creates it.
        """
        self.write("docs/audit/audit-log.jsonl", "{}\n")
        self.commit_all()
        self.init()
        self.assertNotIn("health-history", self.registry_text() or "")

    def test_the_written_registry_parses_back(self):
        """A registry this tool writes that its own parser rejects is the worst outcome."""
        self.write("docs/audit/audit-log.jsonl", "{}\n")
        self.write("docs/audit/change-log.jsonl", "{}\n")
        self.commit_all()
        self.init()
        entries = self.m.load_registry(str(self.root))
        self.assertTrue(entries, "the emitted registry must load")
        for _pattern, klass, command in entries:
            self.assertIn(klass, self.m.CLASSES)
            if klass == "derived":
                self.assertTrue(command, "a derived entry must carry its command")

    def test_the_pack_defaults_name_only_real_subcommands(self):
        """RIG-D, and the exact near-miss: `audit-log.py regen` does not exist.

        Every default carries a *derivable* command; this asserts none of them was written
        from what the script is called rather than from what it accepts.
        """
        defaults = self.m.pack_defaults(str(self.repo))
        self.assertTrue(defaults, "the pack ships derivable defaults")
        for cand in defaults:
            self.assertIn(cand["class"], self.m.CLASSES)
            self.assertTrue(cand.get("patterns"), "a candidate declares the set it owns")
            if cand["class"] == "derived":
                self.assertNotIn(" regen", cand["command"],
                                 "audit-log.py has no `regen` subcommand; it is `render`")


class VerificationTests(InitCase):
    """The control the cfd-bench near-miss argues for."""

    def test_a_failing_regenerate_command_is_refused_not_written(self):
        target = self.write("gen/out.txt", "old\n")
        self.commit_all()
        candidates = [{"patterns": ["gen/out.txt"], "class": "derived",
                       "command": '"{0}" -c "raise SystemExit(1)"'.format(sys.executable),
                       "requires": ["gen/out.txt"]}]
        code = self.init(candidates=candidates)
        self.assertNotIn("gen/out.txt", self.registry_text() or "",
                         "an entry whose command fails must not be written: the merge would "
                         "resolve silently and the artifact would go permanently stale")
        self.assertNotEqual(code, 0, "a refused entry must be reported, not silently dropped")
        self.assertTrue(target.exists())

    def test_a_command_that_touches_another_path_is_refused(self):
        """A regenerate command with a side effect is not a regenerate command."""
        self.write("gen/out.txt", "old\n")
        self.write("src/hand-written.txt", "authored\n")
        self.commit_all()
        candidates = [{"patterns": ["gen/out.txt"], "class": "derived",
                       "command": self._writer("gen/out.txt", extra="src/hand-written.txt"),
                       "requires": ["gen/out.txt"]}]
        code = self.init(candidates=candidates)
        self.assertNotIn("gen/out.txt", self.registry_text() or "")
        self.assertNotEqual(code, 0)

    def test_a_clean_command_is_accepted_even_when_the_tree_was_already_dirty(self):
        """The check is the DELTA, not the absolute state — otherwise it never passes."""
        self.write("gen/out.txt", "old\n")
        self.write("src/hand-written.txt", "committed\n")
        self.commit_all()
        (self.repo / "src" / "hand-written.txt").write_text("dirty before we started\n",
                                                            encoding="utf-8", newline="\n")
        candidates = [{"patterns": ["gen/out.txt"], "class": "derived",
                       "command": self._writer("gen/out.txt"),
                       "requires": ["gen/out.txt"]}]
        code = self.init(candidates=candidates)
        self.assertIn("gen/out.txt: derived", self.registry_text() or "")
        self.assertEqual(code, 0)


class SafetyTests(InitCase):
    def test_it_does_not_overwrite_an_existing_registry(self):
        self.write("docs/audit/audit-log.jsonl", "{}\n")
        self.commit_all()
        existing = "docs/mine.txt: register\n"
        (self.root / self.m.REGISTRY_NAME).write_text(existing, encoding="utf-8", newline="\n")
        code = self.init()
        self.assertEqual(self.registry_text(), existing,
                         "a hand-tuned registry is repo configuration; never clobber it")
        self.assertNotEqual(code, 0)

    def test_force_replaces_it_and_says_so(self):
        self.write("docs/audit/audit-log.jsonl", "{}\n")
        self.commit_all()
        (self.root / self.m.REGISTRY_NAME).write_text("docs/mine.txt: register\n",
                                                      encoding="utf-8", newline="\n")
        self.init(force=True)
        self.assertIn("docs/audit/audit-log.jsonl", self.registry_text() or "")

    def test_the_cli_exposes_it(self):
        """`coord classify init` — the form the proposal published and the skills call."""
        self.write("docs/audit/audit-log.jsonl", "{}\n")
        self.commit_all()
        env = dict(os.environ)
        env.pop("COORD_ROOT", None)
        env["AGENT_SESSION"] = "s1"
        proc = subprocess.run([sys.executable, str(SCRIPT), "classify", "init"],
                              cwd=str(self.repo), env=env, capture_output=True, text=True)
        self.assertIn("audit-log.jsonl", proc.stdout + proc.stderr)
        self.assertTrue((self.root / self.m.REGISTRY_NAME).exists())


class OwnedSetTests(InitCase):
    """A generator owns a SET of artifacts, not one path.

    Found by running this command against the pack's own repo: `audit-log.py render` rebuilds
    `audit-data.js` AND ensures `index.html` exists, so the single-path form reported the
    viewer as a stray side effect and refused the entry. The check was right and the model
    was wrong -- classifying half a generator's output leaves the other half conflicting by
    hand forever, which is the contention the registry exists to remove.
    """

    def test_one_command_owning_two_paths_yields_two_entries(self):
        self.write("gen/a.txt", "old\n")
        self.write("gen/b.txt", "old\n")
        self.commit_all()
        candidates = [{"patterns": ["gen/a.txt", "gen/b.txt"], "class": "derived",
                       "command": self._writer("gen/a.txt", extra="gen/b.txt"),
                       "requires": ["gen/a.txt"]}]
        code = self.init(candidates=candidates)
        text = self.registry_text() or ""
        self.assertIn("gen/a.txt: derived", text)
        self.assertIn("gen/b.txt: derived", text)
        self.assertEqual(code, 0)

    def test_the_audit_renderer_default_declares_both_of_its_outputs(self):
        """Pin the specific pair the control found, so nobody re-narrows it."""
        for cand in self.m.pack_defaults(str(self.repo)):
            if "audit-log.py" in cand.get("command", ""):
                self.assertEqual(sorted(cand["patterns"]),
                                 ["docs/audit/audit-data.js", "docs/audit/index.html"])
                break
        else:
            self.fail("no audit renderer among the pack defaults")


if __name__ == "__main__":
    unittest.main()
