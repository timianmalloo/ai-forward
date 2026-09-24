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
            self.assertNotRegex(line, r"[A-Za-z]:\\|python\.exe|/opt/homebrew/|/Users/",  # machine-path-ok: the assertion
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
    """PLAT-A: the Grok adapter runs hooks through sh and carries the run-time resolver inline. Antigravity
    runs hooks through cmd.exe on Windows (PLAT-C, AgyHookShellTests), and Copilot through PowerShell, which
    also reads the Claude-format commands (CopilotHookShellTests), so those carry the resolver in run-hook.sh."""

    ADAPTERS = ["grok.ai-forward-hooks.json"]

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
                    self.assertNotRegex(command, r"[A-Za-z]:\\|/Users/|/home/|/opt/homebrew/",  # machine-path-ok: the assertion
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


AGY_LAUNCHER = "git -c alias.aif-hook=!sh aif-hook docs/ai-forward-pack/hooks/run-hook.sh "


class AgyHookShellTests(unittest.TestCase):
    """PLAT-C: Antigravity runs hook commands through cmd.exe on Windows, from <repo>/.agents (measured
    2026-09-24, agy 1.2.10: `%OS%` expanded, `$env:OS` did not; `cd` printed <repo>\\.agents). The pack's
    POSIX-only commands (`py=$(...)`, `[ -x ...]`) therefore failed on every tool call, and agy reported each
    tool step as ERROR even when the tool itself succeeded. An agy command must be one plain program
    invocation that cmd.exe and sh parse alike; the interpreter is resolved at run time by the launcher,
    which git runs through its own sh from the top of the working tree."""

    def commands(self):
        data = json.loads((HOOKS / "agy.ai-forward-hooks.json").read_text(encoding="utf-8"))
        found = []

        def walk(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "command" and isinstance(value, str):
                        found.append(value)
                    else:
                        walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(data)
        return found

    def test_every_agy_command_parses_alike_under_cmd_and_sh(self):
        commands = self.commands()
        self.assertTrue(commands)
        for command in commands:
            with self.subTest(command=command):
                # '"' too: agy (Go) escapes an inner quote as \" when it launches cmd.exe, and git then reads it
                # literally (measured 2026-09-24: 'invalid key: "alias.aif-hook')
                for token in ("$(", "`", "[ ", "'", '"', ";", "&&", "||", "%"):
                    self.assertNotIn(token, command, f"{token!r} is shell-specific: cmd.exe and sh read it differently")
                self.assertTrue(command.startswith(AGY_LAUNCHER), "an agy hook runs through the launcher")
                hook = command[len(AGY_LAUNCHER):].split()[0]
                self.assertTrue((HOOKS / hook).is_file(), f"the launcher names a hook the pack ships: {hook}")
                self.assertIn("--host agy", command)

    def test_the_launcher_resolves_the_interpreter_at_run_time(self):
        launcher = (HOOKS / "run-hook.sh").read_bytes()
        self.assertNotIn(b"\r", launcher, "sh fails on CRLF")
        text = launcher.decode("utf-8")
        self.assertIn("import sys;print(sys.executable)", text)
        self.assertIn("python3", text)
        self.assertIn("python -c", text, "no fallback for python.org Windows")
        # agy (no flag) runs the hook by its tree-relative path from the top of the tree; Codex's
        # --caller-cwd returns to the caller's directory and names the hook relative to it (PLAT-C).
        self.assertIn('script="${up}docs/ai-forward-pack/hooks/$1"', text)
        self.assertIn('cd "./$GIT_PREFIX" || exit 2', text)
        self.assertIn('exec "$py" "$script" "$@"', text)
        self.assertNotIn("$(pwd)", text, "Git for Windows sh hands python.exe an unconverted /c/... path")

    @unittest.skipUnless(shutil.which("git") and (REPO / "docs/ai-forward-pack/hooks").is_dir(), "needs git and the installed pack")
    def test_the_agy_reread_guard_command_runs_the_way_agy_runs_it(self):
        command = next(c for c in self.commands() if "reread-guard.py" in c)
        # On Windows the host hands cmd.exe the raw command line; a list would be re-quoted by list2cmdline
        shell = "cmd /d /c " + command if os.name == "nt" else ["sh", "-c", command]
        payload = json.dumps({"toolCall": {"name": "view_file", "args": {"AbsolutePath": str(REPO / "README.md")}},
                              "conversationId": "xp-agy-test"})
        proc = subprocess.run(shell, input=payload, cwd=str(REPO / ".agents"), capture_output=True, text=True,
                              encoding="utf-8", timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


STUB = ("import json, pathlib, sys\n"
        "here = pathlib.Path(__file__).resolve()\n"
        "with (here.parents[3] / 'reached.jsonl').open('a', encoding='utf-8') as out:\n"
        "    out.write(json.dumps([here.name] + sys.argv[1:]) + chr(10))\n")


class CopilotHookShellTests(unittest.TestCase):
    """PLAT-A for Copilot. Measured 2026-09-24 (x-harness-x-model-bench capture window 1, reported by the
    Leader): Copilot CLI 1.0.89-1 under ACP on Windows, pack on, ran 8 pack hooks and all 8 ended
    success:false with a PowerShell ParserError on the pack's POSIX-shell hook command. Copilot runs hook
    commands through PowerShell there. The only POSIX-shell commands the pack installs are the Claude-format
    ones merged into .claude/settings.json, and Copilot 1.0.89-1 reads Claude settings: its runtime.node names
    `.claude` `settings.json` `settings.local.json`, "Failed to read Claude settings from" and
    ${CLAUDE_PROJECT_DIR} (Inferred from the binary; not observed in a hook log). So every command Copilot can
    run - the .github/hooks arms, the emitted ownership entry and the Claude-format commands - must be one
    quote-free launcher invocation that pwsh, cmd.exe and sh parse alike."""

    def sources(self):
        rows = []
        copilot = json.loads((HOOKS / "copilot.ai-forward-hooks.json").read_text(encoding="utf-8"))
        for entries in copilot["hooks"].values():
            rows += [("copilot " + arm, entry[arm]) for entry in entries for arm in ("bash", "powershell")]
        claude = json.loads((HOOKS / "claude-code.settings.hooks.json").read_text(encoding="utf-8"))
        for entries in claude["hooks"].values():
            rows += [("claude", hook["command"]) for entry in entries for hook in entry["hooks"]]
        emitted = subprocess.run([sys.executable, str(COORD), "hook", "--config", "--host", "copilot"],
                                 capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(0, emitted.returncode, emitted.stderr)
        for entry in json.loads(emitted.stdout)["hooks"]["preToolUse"]:
            rows += [("ownership " + arm, entry[arm]) for arm in ("bash", "powershell")]
        # the Claude ownership entry is merged into .claude/settings.json too, which Copilot reads (sweep)
        emitted = subprocess.run([sys.executable, str(COORD), "hook", "--config", "--host", "claude"],
                                 capture_output=True, text=True, encoding="utf-8", timeout=60)
        rows += [("ownership claude", h["command"]) for entry in json.loads(emitted.stdout)["hooks"]["PreToolUse"]
                 for h in entry["hooks"]]
        self.assertGreaterEqual(len(rows), 20)
        return rows

    def test_every_command_copilot_runs_is_one_quote_free_launcher_invocation(self):
        for source, command in self.sources():
            with self.subTest(source=source, command=command):
                for token in ("$", "`", "[ ", "'", '"', ";", "&&", "||", "%", "|", "<", ">"):
                    self.assertNotIn(token, command, f"{token!r} is shell-specific: pwsh, cmd.exe and sh read it differently")
                self.assertTrue(command.startswith(AGY_LAUNCHER), command)

    def assert_every_command_reaches_its_script(self, launch):
        import re
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "a checkout"
            hooks, scripts = root / "docs/ai-forward-pack/hooks", root / "docs/ai-forward-pack/scripts"
            hooks.mkdir(parents=True)
            scripts.mkdir(parents=True)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            shutil.copyfile(HOOKS / "run-hook.sh", hooks / "run-hook.sh")
            rows = self.sources()
            for _source, command in rows:
                name = re.search(r"([\w-]+\.py)", command).group(1)
                for folder in (hooks, scripts):
                    (folder / name).write_text(STUB, encoding="utf-8", newline="\n")
            marker = root / "reached.jsonl"
            for source, command in rows:
                with self.subTest(source=source, command=command):
                    marker.unlink(missing_ok=True)
                    proc = subprocess.run(launch(command), cwd=str(root), input="{}", capture_output=True, text=True,
                                          encoding="utf-8", timeout=60)
                    self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
                    self.assertTrue(marker.is_file(), "the script was not reached: " + proc.stderr)
                    name, arguments = re.search(r"([\w-]+\.py)(.*)$", command).groups()
                    self.assertEqual([name] + arguments.split(), json.loads(marker.read_text(encoding="utf-8").splitlines()[-1]))

    @unittest.skipUnless(shutil.which("pwsh") and shutil.which("git"), "pwsh is absent")
    def test_every_command_copilot_runs_reaches_its_script_under_pwsh(self):
        self.assert_every_command_reaches_its_script(lambda command: ["pwsh", "-NoProfile", "-Command", command])

    @unittest.skipUnless(os.name == "nt" and shutil.which("git"), "cmd.exe exists only on Windows")
    def test_every_command_copilot_runs_reaches_its_script_under_cmd(self):
        self.assert_every_command_reaches_its_script(lambda command: "cmd /d /c " + command)

    @unittest.skipUnless(shutil.which("sh") and shutil.which("git"), "sh or git is absent")
    def test_every_command_copilot_runs_reaches_its_script_under_sh(self):
        self.assert_every_command_reaches_its_script(lambda command: ["sh", "-c", command])


if __name__ == "__main__":
    unittest.main()
