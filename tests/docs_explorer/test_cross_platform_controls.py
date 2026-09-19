"""Cross-platform controls (PLAT-A / PLAT-B; docs/plans/cross-platform-readiness.md P1).

Every test here was observed RED before the fix it pins:

  * `coord classify init` wrote `sys.executable` into the TRACKED registry, so a Windows
    `python.exe` path landed in .agents/artifacts.yml and `coord regen` failed on macOS
    (2026-09-19, this repo, main @ 11e0197).
  * Three hook adapters shipped bare `python`, which stock macOS does not have; the
    Antigravity adapter's script path started with `../`.
  * `pack-doctor`'s coordination check validated that the registry PARSED and never that
    a derived command's interpreter RESOLVES on this machine.
  * Nothing failed on a machine-specific path inside a tracked, machine-readable file.

The rule these enforce: the interpreter word is resolved AT RUN TIME, on the machine that
runs it, by one resolver; a tracked file carries the portable token `python3`, never a path.
"""
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
COORD = REPO / "pack" / "scripts" / "coord-core.py"
DOCTOR = REPO / "pack" / "scripts" / "pack-doctor.py"
LINT = REPO / "pack" / "scripts" / "verify-no-machine-paths.py"
HOOKS = REPO / "pack" / "adapters" / "hooks"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RegistryTokenTests(unittest.TestCase):
    """PLAT-B: the registry travels with the repo, so it carries a token, not a path."""

    def setUp(self):
        self.m = load(COORD, "coord_core_xp")

    def test_pack_defaults_spell_the_interpreter_as_the_portable_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            for entry in self.m.pack_defaults(tmp):
                if entry["class"] != "derived":
                    continue
                self.assertTrue(entry["command"].startswith("python3 "),
                                "a derived command must start with the token `python3`, "
                                "never an interpreter path: " + entry["command"])
                self.assertNotIn(sys.executable, entry["command"])

    def test_the_resolver_substitutes_this_interpreter_for_the_token(self):
        resolved = self.m.resolve_interpreter("python3 x.py derive")
        self.assertTrue(resolved.startswith('"' + sys.executable + '"'), resolved)
        self.assertTrue(resolved.endswith(" x.py derive"), resolved)
        self.assertTrue(self.m.resolve_interpreter("python x.py").startswith('"' + sys.executable + '"'))

    def test_the_resolver_leaves_an_explicit_path_alone_so_a_stale_one_fails_loudly(self):
        legacy = '"C:\\Users\\someone\\python.exe" x.py derive'
        self.assertEqual(self.m.resolve_interpreter(legacy), legacy)
        self.assertEqual(self.m.resolve_interpreter("node tools/x.js"), "node tools/x.js")
        self.assertEqual(self.m.resolve_interpreter(""), "")

    def test_the_committed_registry_carries_no_interpreter_path(self):
        text = (REPO / ".agents" / "artifacts.yml").read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("#") or ": derived" not in line:
                continue
            self.assertNotRegex(line, r"[A-Za-z]:\\|python\.exe|/opt/homebrew/|/Users/",
                                ".agents/artifacts.yml:%d carries a machine path" % lineno)


class SettingsEntryTests(unittest.TestCase):
    def test_the_printed_settings_entry_names_no_absolute_path(self):
        m = load(COORD, "coord_core_xp2")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m._print_settings_entry(str(REPO))
        printed = buf.getvalue()
        self.assertNotIn(sys.executable, printed)
        self.assertNotIn(str(REPO), printed, "the entry is pasted into a TRACKED file")
        # Repo-relative, forward-slashed: pack/scripts/... in the pack repo itself,
        # docs/ai-forward-pack/scripts/... in a consuming repo.
        self.assertRegex(printed, r'\\"(pack|docs/ai-forward-pack)/scripts/coord-core.py\\" hook')
        self.assertIn("import sys;print(sys.executable)", printed)


class HookAdapterConformanceTests(unittest.TestCase):
    """PLAT-A: the three Claude-format adapters get the run-time resolver the Copilot
    adapter already had in spirit (its bash/powershell arms)."""

    ADAPTERS = ["claude-code.settings.hooks.json", "grok.ai-forward-hooks.json",
                "agy.ai-forward-hooks.json"]

    def commands(self, name):
        data = json.loads((HOOKS / name).read_text(encoding="utf-8"))
        found = []

        def walk(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in ("command", "bash", "powershell") and isinstance(value, str):
                        found.append(value)
                    else:
                        walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(data)
        return found

    def test_every_command_resolves_its_interpreter_at_run_time(self):
        for name in self.ADAPTERS:
            for command in self.commands(name):
                with self.subTest(adapter=name, command=command):
                    self.assertFalse(command.startswith('"'), "quoted executable")
                    self.assertNotIn("../", command, "a path that escapes the repo")
                    self.assertNotRegex(command, r"[A-Za-z]:\\|/Users/|/home/|/opt/homebrew/",
                                        "a machine-specific path in a tracked hook config")
                    self.assertIn("import sys;print(sys.executable)", command,
                                  "the interpreter is fixed instead of resolved at run time")
                    self.assertIn("python3", command)
                    self.assertIn("python -c", command, "no fallback for python.org Windows")

    @unittest.skipUnless(shutil.which("sh"), "needs a POSIX sh (Git Bash provides one on Windows)")
    def test_the_claude_command_executes_under_sh_with_a_hook_payload(self):
        command = self.commands("claude-code.settings.hooks.json")[0]
        payload = json.dumps({"hook_event_name": "PreToolUse", "session_id": "xp-test",
                              "tool_name": "Read", "tool_input": {"file_path": "README.md"}})
        proc = subprocess.run(["sh", "-c", command], input=payload, cwd=str(REPO),
                              capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class DoctorResolvesDerivedCommandsTests(unittest.TestCase):
    """XP-30: a registry whose derived command cannot run HERE must FAIL, not PASS."""

    def setUp(self):
        self.d = load(DOCTOR, "pack_doctor_xp")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        (root / "docs" / "ai-forward-pack" / "scripts").mkdir(parents=True)
        (root / "docs" / "ai-forward-pack" / "scripts" / "coord-core.py").write_text("# stub\n", encoding="utf-8")
        (root / ".agents").mkdir()
        self.root = root

    def write_registry(self, command):
        (self.root / ".agents" / "artifacts.yml").write_text(
            "docs/docs-index.js: derived {0}\n"
            "docs/audit/audit-log.jsonl: register\n".format(command), encoding="utf-8", newline="\n")

    def test_an_unresolvable_interpreter_path_fails(self):
        self.write_registry('"C:\\Users\\nobody\\AppData\\Local\\Programs\\Python\\python.exe" docs/x.py derive')
        result = self.d.check_coordination(str(self.root))
        self.assertEqual(result["status"], self.d.FAIL, result)
        self.assertIn("classify init --force", result["fix"])

    def test_the_portable_token_passes(self):
        self.write_registry("python3 docs/ai-forward-pack/scripts/docs-graph.py derive")
        result = self.d.check_coordination(str(self.root))
        self.assertNotEqual(result["status"], self.d.FAIL, result)


class NoMachinePathsLintTests(unittest.TestCase):
    def run_lint(self, *args, cwd):
        return subprocess.run([sys.executable, str(LINT), *args], cwd=str(cwd),
                              capture_output=True, text=True, encoding="utf-8", timeout=120)

    def test_self_test_proves_the_gate_can_fail(self):
        proc = self.run_lint("--self-test", cwd=REPO)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("self-test", proc.stdout)

    def test_the_repo_is_clean(self):
        proc = self.run_lint(cwd=REPO)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_a_windows_home_path_in_a_tracked_config_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / ".agents").mkdir()
            bad = root / ".agents" / "artifacts.yml"
            bad.write_text('x: derived "C:\\Users\\malla\\AppData\\Local\\Programs\\Python\\python.exe" x.py\n',
                           encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
            proc = self.run_lint(cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("artifacts.yml", proc.stdout)


if __name__ == "__main__":
    unittest.main()
