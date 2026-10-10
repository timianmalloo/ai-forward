import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"
SCRIPT = SCRIPTS / "pack-doctor.py"


def load_module():
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location("pack_doctor", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPTS))


class PackDoctorInterpreterTests(unittest.TestCase):
    """FR-031. The pack documents `python3`, which does not exist on a python.org Windows
    install. The doctor must name the working substitution rather than let the reader
    discover it one failing command at a time."""

    def setUp(self):
        self.module = load_module()
        native_environment = mock.patch.dict(os.environ, {"UV_RUN_RECURSION_DEPTH": "0"})
        native_environment.start()
        self.addCleanup(native_environment.stop)

    def _fake(self, ok_labels):
        """Stub run_bounded so only the given argv[0..1] forms report Python 3."""
        def runner(argv, **kwargs):
            label = " ".join(argv[:-1])
            if label in ok_labels:
                return SimpleNamespace(returncode=0, stdout="Python 3.12.10\n", stderr="")
            return SimpleNamespace(returncode=9009, stdout="", stderr="Python was not found")
        return runner

    def test_python3_available_passes(self):
        with mock.patch.object(self.module, "run_bounded", self._fake({"python3"})):
            result = self.module.check_interpreter()
        self.assertEqual("PASS", result["status"])

    def test_windows_shape_warns_and_names_the_substitution(self):
        # python3 absent, python present - the python.org Windows shape.
        with mock.patch.object(self.module, "run_bounded", self._fake({"python"})):
            result = self.module.check_interpreter()
        self.assertEqual("WARN", result["status"])
        self.assertIn("`python`", result["detail"])
        self.assertIn("python3", result["fix"])

    def test_no_interpreter_fails(self):
        with mock.patch.object(self.module, "run_bounded", self._fake(set())):
            result = self.module.check_interpreter()
        self.assertEqual("FAIL", result["status"])

    def test_launch_failure_is_a_miss_not_a_crash(self):
        def raiser(argv, **kwargs):
            raise OSError("not found")
        with mock.patch.object(self.module, "run_bounded", raiser):
            result = self.module.check_interpreter()
        self.assertEqual("FAIL", result["status"])

    def test_a_bad_call_is_not_swallowed_into_a_plausible_result(self):
        # Guards the bug this check shipped with: a TypeError from a wrong keyword was
        # caught by a bare `except Exception` and reported as "no Python found".
        def bug(argv, **kwargs):
            raise TypeError("unexpected keyword argument")
        with mock.patch.object(self.module, "run_bounded", bug):
            with self.assertRaises(TypeError):
                self.module.check_interpreter()


class PackDoctorGraphTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_empty_graph_is_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)

            result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("0 artifacts", result["detail"])

    def test_invalid_graph_is_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            docs = root / "docs"
            (docs / "invalid.md").write_text(
                "---\nid: invalid\ntitle: Invalid\ntype: unknown\n---\n",
                encoding="utf-8",
            )

            result = self.module.check_graph(str(root))

            self.assertEqual("FAIL", result["status"])
            self.assertIn("graph problem", result["detail"])

    def test_graph_timeout_is_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = type(
                "Result",
                (),
                {
                    "returncode": -1,
                    "stdout": "",
                    "stderr": "",
                    "timed_out": True,
                    "limit_exceeded": None,
                },
            )()

            original = self.module.run_bounded
            self.module.run_bounded = lambda *args, **kwargs: fake
            try:
                result = self.module.check_graph(str(root))
            finally:
                self.module.run_bounded = original

            self.assertEqual("WARN", result["status"])
            self.assertIn("timed out", result["detail"])

    def test_graph_output_limit_is_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = self._process_result(limit_exceeded="output")

            with mock.patch.object(self.module, "run_bounded", return_value=fake):
                result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("output limit", result["detail"])

    def test_graph_nonzero_exit_is_inconclusive_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = self._process_result(returncode=3, stderr="invalid")

            with mock.patch.object(self.module, "run_bounded", return_value=fake):
                result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("inconclusive", result["detail"])
            self.assertIn("invalid", result["detail"])

    def test_graph_containment_failure_is_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = self._process_result()
            fake.contained = False
            fake.containment_error = "AssignProcessToJobObject failed (5)"

            with mock.patch.object(self.module, "run_bounded", return_value=fake):
                result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("not run safely", result["detail"])
            self.assertIn("AssignProcessToJobObject", result["detail"])

    def test_graph_malformed_output_is_inconclusive_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = self._process_result(stdout="{not json")

            with mock.patch.object(self.module, "run_bounded", return_value=fake):
                result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("inconclusive", result["detail"])

    def test_graph_health_findings_are_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._install_graph_tool(temp)
            fake = self._process_result(
                stdout=json.dumps(
                    {
                        "artifacts": 2,
                        "problems": [],
                        "stale": ["a"],
                        "flagged": ["b"],
                        "orphans": [],
                    }
                )
            )

            with mock.patch.object(self.module, "run_bounded", return_value=fake):
                result = self.module.check_graph(str(root))

            self.assertEqual("WARN", result["status"])
            self.assertIn("stale/flagged/orphan", result["detail"])

    def test_main_returns_nonzero_when_any_check_fails(self):
        checks = [
            self.module._result("one", self.module.PASS, "ok"),
            self.module._result("two", self.module.FAIL, "broken"),
        ]
        with mock.patch.object(self.module, "run", return_value=checks), mock.patch.object(
            self.module.sys, "argv", ["pack-doctor.py", "--json"]
        ):
            with mock.patch("builtins.print"):
                exit_code = self.module.main()

        self.assertEqual(1, exit_code)

    def test_main_strict_returns_nonzero_when_any_check_warns(self):
        checks = [
            self.module._result("one", self.module.PASS, "ok"),
            self.module._result("two", self.module.WARN, "inconclusive"),
        ]
        with mock.patch.object(self.module, "run", return_value=checks), mock.patch.object(
            self.module.sys, "argv", ["pack-doctor.py", "--json", "--strict"]
        ):
            with mock.patch("builtins.print"):
                exit_code = self.module.main()

        self.assertEqual(1, exit_code)

    def test_main_non_strict_preserves_warning_exit_zero(self):
        checks = [self.module._result("one", self.module.WARN, "review needed")]
        with mock.patch.object(self.module, "run", return_value=checks), mock.patch.object(
            self.module.sys, "argv", ["pack-doctor.py", "--json"]
        ):
            with mock.patch("builtins.print"):
                exit_code = self.module.main()

        self.assertEqual(0, exit_code)

    @staticmethod
    def _process_result(
        returncode=0,
        stdout='{"artifacts": 0, "problems": [], "stale": [], "flagged": [], "orphans": []}',
        stderr="",
        timed_out=False,
        limit_exceeded=None,
    ):
        return SimpleNamespace(
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            limit_exceeded=limit_exceeded,
        )

    @staticmethod
    def _install_graph_tool(temp):
        root = Path(temp)
        destination = root / "docs" / "ai-forward-pack" / "scripts"
        destination.mkdir(parents=True)
        shutil.copy2(SCRIPTS / "docs-graph.py", destination / "docs-graph.py")
        return root


class PackDoctorNodeRunnerTests(unittest.TestCase):
    """FR-055 / class PACK-C — a documented command assumed portable. `npm run` executes
    scripts through a CHILD SHELL whose PATH can differ from the caller's, so node resolving
    for you proves nothing about whether the documented command works. Observed on a real
    Windows host: `node --version` -> v24.18.0, `cmd /c node --version` -> not recognized,
    `npm run test:docs-explorer:core` -> the same failure, tests themselves 31/31 green."""

    def setUp(self):
        self.module = load_module()

    def _fake(self, direct_ok=True, shell_ok=True):
        def runner(argv, **kwargs):
            is_shell = argv[0] in ("cmd", "sh")
            ok = shell_ok if is_shell else direct_ok
            if ok:
                return SimpleNamespace(returncode=0, stdout="v24.18.0\n", stderr="")
            return SimpleNamespace(
                returncode=1, stdout="",
                stderr="'node' is not recognized as an internal or external command")
        return runner

    def test_passes_when_the_spawned_shell_can_resolve_node(self):
        with mock.patch.object(self.module, "run_bounded", self._fake(True, True)):
            result = self.module.check_node_runner()
        self.assertEqual("PASS", result["status"])

    def test_warns_when_only_the_child_shell_cannot_find_node(self):
        """The exact FR-055 shape: green for you, red for `npm run`."""
        with mock.patch.object(self.module, "run_bounded", self._fake(True, False)):
            result = self.module.check_node_runner()
        self.assertEqual("WARN", result["status"],
                         "a documented command that cannot run must be reported, not assumed")

    def test_the_warning_names_the_working_invocation(self):
        """PACK-C's stated control is to NAME the form that works here, not just complain."""
        with mock.patch.object(self.module, "run_bounded", self._fake(True, False)):
            result = self.module.check_node_runner()
        text = json.dumps(result)
        self.assertIn("node --test", text, "must name the direct invocation that does work")

    def test_missing_node_is_reported_without_pretending_it_is_a_path_problem(self):
        with mock.patch.object(self.module, "run_bounded", self._fake(False, False)):
            result = self.module.check_node_runner()
        self.assertEqual("WARN", result["status"])
        self.assertIn("not on PATH", json.dumps(result))

    def test_the_check_is_wired_into_the_doctor_run(self):
        """A check nobody calls is not a control."""
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("check_node_runner()", source.split("def run(root)")[1][:800])


class PackDoctorCoordinationModeTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        scripts = self.root / "docs" / "ai-forward-pack" / "scripts"
        scripts.mkdir(parents=True)
        shutil.copy2(SCRIPTS / "coord-core.py", scripts / "coord-core.py")
        self.write(".agents/hooks.json", (REPO / "pack/adapters/hooks/agy.ai-forward-hooks.json").read_text(encoding="utf-8"))
        # Isolate Git probes from user/global configuration and enclosing checkouts.
        self.env = mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": os.devnull,
                                               "GIT_CONFIG_NOSYSTEM": "1"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def write(self, relative, text):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
        return target

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              capture_output=True, text=True, encoding="utf-8")

    def test_fresh_plain_and_git_installs_do_not_require_optional_registry(self):
        for git_checkout in (False, True):
            with self.subTest(git_checkout=git_checkout):
                if git_checkout:
                    self.git("init", "-q")
                result = self.module.check_coordination(str(self.root))
                self.assertEqual("WARN", result["status"], result)
                self.assertIn("NOT APPLICABLE", result["detail"])
                self.assertIn("optional", result["detail"])
                self.assertIn("serial", result["detail"])
                self.assertFalse((self.root / ".agents/artifacts.yml").exists())


    def test_missing_registry_fails_for_explicit_coordination_activation(self):
        cases = ("attributes", "driver", "pre-commit", "custom-hooks-path", "native-claude",
                 "native-copilot", "native-codex", "native-grok", "native-agy")
        for activation in cases:
            with self.subTest(activation=activation):
                # Separate repositories keep every activation signal independent.
                with tempfile.TemporaryDirectory() as temp:
                    saved = self.root
                    self.root = Path(temp)
                    try:
                        self.write("docs/ai-forward-pack/scripts/coord-core.py", "# installed\n")
                        self.git("init", "-q")
                        if activation == "attributes":
                            self.write(".gitattributes", "* text=auto eol=lf\n*.jsonl merge=coord-register\n")
                        elif activation == "driver":
                            self.git("config", "--local", "merge.coord-register.driver", "coord-core.py merge-register %A %O %B %P")
                        elif activation in ("pre-commit", "custom-hooks-path"):
                            if activation == "custom-hooks-path":
                                self.git("config", "--local", "core.hooksPath", "local hooks")
                            hook_dir = self.git("rev-parse", "--git-path", "hooks").stdout.strip()
                            hook = self.write(hook_dir + "/pre-commit", '#!/bin/sh\n# coord-core pre-commit floor\nexec python3 coord-core.py precommit\n')
                            hook.chmod(0o755)
                        else:
                            host = activation.removeprefix("native-")
                            config = subprocess.run([sys.executable, str(SCRIPTS / "coord-core.py"),
                                                     "hook", "--config", "--host", host],
                                                    check=True, capture_output=True, text=True)
                            relative = {"claude": ".claude/settings.json", "copilot": ".github/hooks/ownership.json",
                                        "codex": ".codex/hooks.json", "grok": ".grok/hooks/ownership.json",
                                        "agy": ".agents/hooks.json"}[host]
                            self.write(relative, config.stdout)
                        result = self.module.check_coordination(str(self.root))
                        self.assertEqual("FAIL", result["status"], result)
                        self.assertIn("activated", result["detail"])
                        self.assertIn("artifacts.yml", result["detail"])
                    finally:
                        self.root = saved


    def test_disabled_ownership_and_commented_attributes_are_not_activation(self):
        self.git("init", "-q")
        self.write(".gitattributes", "# *.jsonl merge=coord-register\n* text=auto eol=lf\n")
        config = subprocess.run([sys.executable, str(SCRIPTS / "coord-core.py"), "hook", "--config", "--host", "agy"],
                                check=True, capture_output=True, text=True)
        disabled = json.loads(config.stdout)
        disabled["ownership-guard"]["enabled"] = False
        self.write(".agents/hooks.json", json.dumps(disabled))
        self.assertEqual("WARN", self.module.check_coordination(str(self.root))["status"])
        # A stale default hook is not effective when Git points at a different directory.
        self.write(".git/hooks/pre-commit", "#!/bin/sh\n# coord-core pre-commit floor\n").chmod(0o755)
        self.git("config", "--local", "core.hooksPath", "other-hooks")
        self.assertEqual("WARN", self.module.check_coordination(str(self.root))["status"])

    def test_valid_minimal_registry_passes_and_malformed_registry_fails(self):
        self.write(".agents/artifacts.yml", "README.md: authored\n")
        self.assertEqual("PASS", self.module.check_coordination(str(self.root))["status"])
        for text in ("README.md: unsupported-class\n", "not a registry row\n", "index.js: derived\n",
                     ": authored\n", "README.md: authored\nREADME.md: register\n"):
            with self.subTest(text=text):
                self.write(".agents/artifacts.yml", text)
                result = self.module.check_coordination(str(self.root))
                self.assertEqual("FAIL", result["status"], result)
                self.assertIn("registry does not parse", result["detail"])


    def test_registry_non_utf8_is_reported_as_failure_not_a_crash(self):
        (self.root / ".agents/artifacts.yml").write_bytes(b"README.md: authored\n\xff")
        result = self.module.check_coordination(str(self.root))
        self.assertEqual("FAIL", result["status"], result)
        self.assertIn("unreadable", result["detail"])

    def test_valid_registry_ignores_commented_merge_driver_declarations(self):
        self.write(".agents/artifacts.yml", "README.md: authored\n")
        self.write(".gitattributes", "# *.jsonl merge=coord-register\n")
        result = self.module.check_coordination(str(self.root))
        self.assertEqual("PASS", result["status"], result)


class PackDoctorPortableInvocationTests(unittest.TestCase):
    def assert_uv_remedy_uses_executable(self, fix, executable):
        import shlex
        from pathlib import PureWindowsPath
        parts = fix.split("`")
        self.assertEqual(3, len(parts), fix)
        argv = shlex.split(parts[1])  # The documented uv command uses POSIX quoting, even on Windows.
        self.assertEqual(["uv", "run", "--no-config", "--no-project", "--python"], argv[:5])
        self.assertEqual(7, len(argv), argv)
        path_type = PureWindowsPath if PureWindowsPath(executable).drive else Path
        self.assertEqual(path_type(executable), path_type(argv[5]))
        self.assertEqual("docs/ai-forward-pack/scripts/pack-doctor.py", argv[6])

    def test_uv_remedy_oracle_compares_parsed_windows_executable(self):
        executable = r"C:\Program Files\Python\python.exe"
        fix = ('use `uv run --no-config --no-project --python '
               '"C:/Program Files/Python/python.exe" '
               'docs/ai-forward-pack/scripts/pack-doctor.py` with this existing interpreter')
        self.assertNotIn(executable, fix)  # The old raw-string oracle is false.
        self.assert_uv_remedy_uses_executable(fix, executable)
        for wrong in (fix.replace("python.exe", "other.exe"),
                      fix.replace("python.exe", "python.exe.backup"),
                      fix.replace("uv run", "echo uv run")):
            with self.subTest(wrong=wrong), self.assertRaises(AssertionError):
                self.assert_uv_remedy_uses_executable(wrong + " " + executable, executable)

    @unittest.skipUnless(shutil.which("uv"), "requires an already installed uv; never downloads")
    def test_real_offline_uv_does_not_claim_caller_native_python_readiness(self):
        uv = shutil.which("uv")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scripts = root / "docs/ai-forward-pack/scripts"
            scripts.mkdir(parents=True)
            shutil.copy2(SCRIPT, scripts / SCRIPT.name)
            shutil.copy2(SCRIPTS / "bounded_process.py", scripts / "bounded_process.py")
            shutil.copy2(SCRIPTS / "platform_process.py", scripts / "platform_process.py")
            empty_path = root / "no native Python"
            empty_path.mkdir()
            env = dict(os.environ, PATH=str(empty_path), UV_PYTHON_DOWNLOADS="never")
            for key in ("VIRTUAL_ENV", "CONDA_PREFIX", "UV_RUN_RECURSION_DEPTH"):
                env.pop(key, None)
            self.assertIsNone(shutil.which("python3", path=env["PATH"]))
            self.assertIsNone(shutil.which("python", path=env["PATH"]))
            command = [uv, "run", "--no-config", "--no-project", "--offline",
                       "--python", sys.executable, str(scripts / SCRIPT.name), "--root", str(root), "--json"]
            proc = subprocess.run(command, env=env, cwd=root, capture_output=True,
                                  text=True, encoding="utf-8", timeout=120)
            # The incomplete install may FAIL other checks; the doctor itself must run.
            self.assertIn(proc.returncode, (0, 1), proc.stderr)
            self.assertTrue(proc.stdout.strip(), proc.stderr)
            output = json.loads(proc.stdout)
            result = next(row for row in output["checks"] if row["name"] == "python interpreter")
            self.assertEqual("WARN", result["status"], result)
            self.assertIn("uv-managed", result["detail"])
            self.assertIn("caller", result["detail"])
            self.assertIn("not verified", result["detail"])
            self.assertNotIn("documented commands run as written", result["detail"])
            self.assertIn("uv run", result["fix"])
            self.assert_uv_remedy_uses_executable(result["fix"], command[command.index("--python") + 1])


if __name__ == "__main__":
    unittest.main()
