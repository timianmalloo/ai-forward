"""Bootstrap CLI acceptance tests; every target and Git setting is disposable."""
import functools
import hashlib
import http.server
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "bootstrap.py"


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.target = self.base / "sample project"
        self.target.mkdir()
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1",
                        GIT_CONFIG_GLOBAL=str(self.base / "no-global-config"),
                        GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1",
                        GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.invalid",
                        GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.invalid")
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_CONFIG_COUNT"):
            self.env.pop(key, None)

    def run_bootstrap(self, *args, cwd=None, source=None):
        return subprocess.run([sys.executable, str(SCRIPT), "--source", str(source or ROOT), *args],
                              cwd=cwd or self.target, env=self.env, capture_output=True,
                              text=True, encoding="utf-8", timeout=120)

    def write(self, rel, content):
        path = self.target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        return path

    def snapshot(self):
        return {p.relative_to(self.target).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mode)
                for p in self.target.rglob("*") if p.is_file()}

    def git(self, *args, cwd=None):
        result = subprocess.run(["git", *args], cwd=cwd or self.target, env=self.env,
                                capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.strip()

    def clone_source(self):
        source = self.base / "source"
        self.git("clone", "--no-hardlinks", str(ROOT), str(source), cwd=self.base)
        return source

    def test_no_source_overrides_use_upstream_main_defaults(self):
        # A disposable post-merge mirror exercises the real default command
        # without pretending the unmerged launcher is available upstream now.
        source = self.clone_source()
        self.git('checkout', '-B', 'main', cwd=source)
        tracked = self.git('ls-files', cwd=ROOT).splitlines()
        for relative in tracked:
            origin = ROOT / relative
            destination = source / relative
            if origin.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origin, destination)
        self.git('add', '-A', cwd=source)
        self.git('commit', '--allow-empty', '-qm', 'Disposable current-source fixture', cwd=source)
        commit = self.git('rev-parse', 'main', cwd=source)
        upstream = 'https://github.com/timianmalloo/ai-forward.git'
        self.git('config', '--file', self.env['GIT_CONFIG_GLOBAL'],
                 f'url.{source.as_uri()}.insteadOf', upstream, cwd=self.base)
        command = [sys.executable, str(SCRIPT)]
        before = self.snapshot()
        dry = subprocess.run(command + ['--dry-run'], cwd=self.target, env=self.env,
                             capture_output=True, text=True, encoding='utf-8', timeout=120)
        self.assertEqual(0, dry.returncode, dry.stdout + dry.stderr)
        self.assertEqual(before, self.snapshot())
        installed = before
        for repeat in (False, True):
            result = subprocess.run(command, cwd=self.target, env=self.env,
                                    capture_output=True, text=True, encoding='utf-8', timeout=120)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            receipt = json.loads((self.target / 'docs/ai-forward-pack/bootstrap-receipt.json').read_text(encoding='utf-8'))
            self.assertEqual(upstream, receipt['source_repository'])
            self.assertEqual('main', receipt['requested_ref'])
            self.assertEqual(commit, receipt['source_commit'])
            self.assertEqual((source / 'pack/commands/deliver/SKILL.md').read_bytes(),
                             (self.target / '.agents/skills/deliver/SKILL.md').read_bytes())
            self.assertFalse((self.target / '.git').exists())
            if repeat:
                self.assertIn('already current', result.stdout)
                self.assertEqual(installed, self.snapshot())
            else:
                installed = self.snapshot()

    def test_credential_repository_url_is_rejected_without_leak_or_target_writes(self):
        url = "https://test-user:SYNTHETIC_TEST_TOKEN@example.invalid/pack.git"
        self.git("config", "--file", self.env["GIT_CONFIG_GLOBAL"],
                 f"url.{ROOT.as_uri()}.insteadOf", url, cwd=self.base)
        before = self.snapshot()
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", url, "--ref", "HEAD"],
                                cwd=self.target, env=self.env, capture_output=True,
                                text=True, encoding="utf-8", timeout=120)
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertIn("credential", result.stderr.lower())
        self.assertNotIn("SYNTHETIC_TEST_TOKEN", result.stdout + result.stderr)
        self.assertNotIn("test-user", result.stdout + result.stderr)

    def test_dry_run_cannot_execute_target_stdlib_shadows(self):
        self.env.pop("PYTHONPATH", None)
        for name in ("json", "subprocess"):
            with self.subTest(module=name):
                self.target = self.base / name
                self.target.mkdir()
                self.write(name + ".py",
                           "from pathlib import Path\n"
                           "Path('PROJECT_MODULE_EXECUTED').write_text('unexpected execution', encoding='utf-8')\n"
                           "raise RuntimeError('Target module must not execute')\n")
                before = self.snapshot()
                result = self.run_bootstrap("--dry-run")
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.target / "PROJECT_MODULE_EXECUTED").exists())

    def test_apply_cannot_execute_target_sitecustomize_from_pythonpath(self):
        marker = self.base / "APPLY_CHILD_EVENTS"
        self.write("sitecustomize.py",
                   "from pathlib import Path\n"
                   f"Path({str(marker)!r}).open('a', encoding='utf-8').write('unexpected child import\\n')\n")
        env = dict(self.env, PYTHONPATH=str(self.target))
        result = subprocess.run([sys.executable, "-I", "-B", str(SCRIPT),
                                 "--source", str(ROOT)],
                                cwd=self.target, env=env, capture_output=True,
                                text=True, encoding="utf-8", timeout=120)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertFalse(marker.exists(), "The actual apply child must not import target sitecustomize")
        self.assertTrue((self.target / "AGENTS.md").is_file(), "The isolated apply must still install")

    def entry_snapshot(self):
        # Include directories, mtimes and bytecode, not just the managed files.
        return {p.relative_to(self.target).as_posix():
                (p.is_dir(), p.stat().st_mode, p.stat().st_mtime_ns,
                 hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None)
                for p in [self.target, *self.target.rglob("*")]}

    def entry_shadow(self, name):
        # Same side-effecting collision as the real reviewer fixture.
        self.write(name + ".py",
                   "from pathlib import Path\n"
                   "Path('PROJECT_MODULE_EXECUTED').write_text('unexpected parent import')\n"
                   "raise RuntimeError('Target module must not execute')\n")

    def assert_entry_preview(self, command, env):
        before = self.entry_snapshot()
        result = subprocess.run(command, cwd=self.target, env=env, capture_output=True,
                                text=True, encoding="utf-8", timeout=120)
        # Always evaluate no-write and no-import oracles, even if the CLI fails.
        self.assertEqual((0, before, False, False),
                         (result.returncode, self.entry_snapshot(),
                          (self.target / "PROJECT_MODULE_EXECUTED").exists(),
                          (self.target / "__pycache__").exists()),
                         result.stdout + result.stderr)
        self.assertIn("no target writes", result.stdout)
        self.assertIn(self.git("rev-parse", "HEAD", cwd=ROOT), result.stdout)
        return result.stdout

    def test_saved_wrapper_entry_cannot_execute_adjacent_stdlib_shadows(self):
        env = dict(self.env)
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        for name in ("json", "subprocess"):
            with self.subTest(module=name):
                self.target = self.base / (name + " saved Ω quote' semicolon;")
                self.target.mkdir()
                self.entry_shadow(name)
                # A relative, option-looking script name must still select this
                # exact wrapper, not argv[0] as an interpreter option or source.
                wrapper = self.target / "-bootstrap.py"
                shutil.copy2(SCRIPT, wrapper)
                self.assert_entry_preview(
                    [sys.executable, "./-bootstrap.py", "--source", str(ROOT),
                     "--ref", "HEAD", "--dry-run"], env)

    @unittest.skipUnless(shutil.which("uv"), "uv CLI not installed")
    def test_uv_remote_entry_ignores_target_pythonpath_stdlib_shadows(self):
        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass
        server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/bootstrap.py"
            env = dict(self.env, UV_PYTHON=sys.executable, UV_PYTHON_DOWNLOADS="never",
                       UV_CACHE_DIR=str(self.base / "uv-cache"))
            env.pop("PYTHONDONTWRITEBYTECODE", None)
            env.pop("UV_OFFLINE", None)  # only the localhost script fetch needs HTTP
            for name in ("json", "subprocess"):
                outputs = []
                for pythonpath in ("", "."):
                    with self.subTest(module=name, pythonpath=pythonpath):
                        self.target = self.base / (name + (" control" if not pythonpath else " pythonpath"))
                        self.target.mkdir()
                        self.entry_shadow(name)
                        self.write("pyproject.toml", "[project]\nname = 'unrelated'\nversion = '0.0.0'\n"
                                   "dependencies = ['nonexistent-bootstrap-project-dependency']\n")
                        self.write("uv.toml", "intentionally invalid TOML\n")
                        outputs.append(self.assert_entry_preview(
                            ["uv", "run", "--no-config", "--no-project", "--script", url,
                             "--source", str(ROOT), "--ref", "HEAD", "--dry-run"],
                            dict(env, PYTHONPATH=pythonpath)))
                with self.subTest(module=name, control_matches_collision=True):
                    self.assertEqual(2, len(outputs), "both the empty-path control and collision must pass")
                    self.assertEqual(outputs[0], outputs[1])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_entry_isolation_preserves_arguments_binary_stdin_cwd_and_exit(self):
        # Replace only the CLI endpoint in a disposable trusted copy, leaving the
        # actual entry/import code intact. This is a transport oracle, not a mock
        # of the interpreter restart or an execution of project/source modules.
        footer = 'if __name__ == "__main__":\n    sys.exit(main())\n'
        probe = ('if __name__ == "__main__":\n'
                 '    print(json.dumps({"args": sys.argv[1:], "stdin": sys.stdin.buffer.read().hex(),\n'
                 '                      "cwd": str(Path.cwd()), "interpreter": sys.executable,\n'
                 '                      "isolated": int(sys.flags.isolated or globals().get("_AI_FORWARD_ENTRY_ISOLATED", False)),\n'
                 '                      "no_bytecode": int(sys.dont_write_bytecode)}))\n'
                 '    sys.exit(7)\n')
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(1, text.count(footer))
        wrapper = self.write("transport Ω quote' semicolon;.py", text.replace(footer, probe))
        env = dict(self.env, PYTHONPATH=".")
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        payload = b"\x00\xffstdin must survive\r\n"
        arguments = ["--source", "source with spaces", "--ref", "refs/heads/Ω quote' semicolon;",
                     "", "--", "-option-looking"]
        for flags in ([], ["-S"], ["-I"], ["-I", "-B"]):
            with self.subTest(flags=flags):
                before = self.entry_snapshot()
                result = subprocess.run([sys.executable, *flags, str(wrapper), *arguments],
                                        cwd=self.target, env=env, input=payload, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
                observed = json.loads(result.stdout)
                self.assertEqual(Path(observed.pop("cwd")).resolve(), self.target.resolve())
                self.assertEqual(observed,
                                 {"args": arguments, "stdin": payload.hex(),
                                  "interpreter": sys.executable, "isolated": 1, "no_bytecode": 1})
                self.assertEqual(before, self.entry_snapshot())
                self.assertEqual(b"", result.stderr)

    def test_source_named_custom_hook_bundle_is_refused_without_losing_disable_or_metadata(self):
        bundle = {"enabled": False,
                  "Stop": [{"type": "command", "command": "local-stop", "timeout": 30}],
                  "project-note": {"reason": "deliberately disabled", "ticket": "PRODUCT-1"}}
        path = self.write(".agents/hooks.json", json.dumps({"heartbeat": bundle}))
        original = path.read_bytes()
        before = self.snapshot()
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(original, path.read_bytes())
        self.assertIn("CONFLICT", result.stderr)
        self.assertIn(".agents/hooks.json", result.stderr)
        self.assertIn("heartbeat", result.stderr)
        self.assertIn("reconcile", result.stderr)

    def test_stale_locally_authored_instructions_require_review_before_any_writes(self):
        path = self.write(".github/instructions/ui-design-craft.instructions.md",
                          "Project-specific mandatory UI rules, not shipped pack text.\n")
        original = path.read_bytes()
        before = self.snapshot()
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(original, path.read_bytes())
        self.assertIn("REVIEW", result.stderr)
        self.assertIn(path.relative_to(self.target).as_posix(), result.stderr)
        self.assertIn("reconcile", result.stderr)

    def test_product_crlf_git_policy_requires_review_without_semantic_or_byte_changes(self):
        self.git("init")
        self.write("product.txt", "product\n")
        attributes = self.write(".gitattributes", "")
        attributes.write_bytes(b"* text=auto eol=crlf\r\n*.bin -text\r\n")
        policy = self.git("check-attr", "eol", "--", "product.txt")
        self.assertEqual("product.txt: eol: crlf", policy)
        before = self.snapshot()
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(policy, self.git("check-attr", "eol", "--", "product.txt"))
        self.assertIn("REVIEW", result.stderr)
        self.assertIn(".gitattributes", result.stderr)
        self.assertIn("reconcile", result.stderr)

    def test_powershell_product_safety_check_requires_review_and_stays_active(self):
        self.write("CLAUDE.md", "Preserve project instructions.\n")
        original = ("# CLAUDE.md parity is checked by the project docs stage.\n"
                    "if ($env:UNSAFE_RELEASE -eq '1') { throw 'PROJECT_SAFETY_GATE' }\n")
        path = self.write("scripts/product-gates.ps1", original)
        before = self.snapshot()
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(original, path.read_text(encoding="utf-8"))
        self.assertIn("PROJECT_SAFETY_GATE", path.read_text(encoding="utf-8"))
        self.assertIn("REVIEW", result.stderr)
        self.assertIn("scripts/product-gates.ps1", result.stderr)
        self.assertIn("reconcile", result.stderr)
        self.assertFalse((self.target / "AGENTS.md").exists())

    def test_isolated_preview_does_not_write_wrapper_bytecode_into_target(self):
        wrapper = self.target / "bootstrap.py"
        shutil.copy2(SCRIPT, wrapper)
        before = self.snapshot()
        result = subprocess.run([sys.executable, str(wrapper), "--source", str(ROOT), "--dry-run"],
                                cwd=self.target, env=self.env, capture_output=True,
                                text=True, encoding="utf-8", timeout=120)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.target / "__pycache__").exists())

    def test_source_selected_named_hook_deviation_is_not_based_on_a_duplicate_name_map(self):
        source = self.clone_source()
        snippet = source / "pack/adapters/hooks/agy.ai-forward-hooks.json"
        bundles = json.loads(snippet.read_text(encoding="utf-8"))
        bundles["source-selected-pulse"] = bundles.pop("heartbeat")
        snippet.write_text(json.dumps(bundles), encoding="utf-8", newline="\n")
        self.git("add", "pack/adapters/hooks/agy.ai-forward-hooks.json", cwd=source)
        self.git("commit", "-m", "Fixture: source-selected hook name", cwd=source)
        original = {"source-selected-pulse": {"enabled": False, "project-note": "local policy"}}
        self.write(".agents/hooks.json", json.dumps(original))
        before = self.snapshot()
        result = self.run_bootstrap(source=source)
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("CONFLICT", result.stderr)
        self.assertIn("source-selected-pulse", result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(original, json.loads((self.target / ".agents/hooks.json").read_text(encoding="utf-8")))

    def test_source_selected_stale_removal_requires_review_without_a_duplicate_path_map(self):
        source = self.clone_source()
        self.git("mv", "pack/knowledge/ui-design-craft.md", "pack/knowledge/source-selected-rule.md", cwd=source)
        self.git("commit", "-m", "Fixture: source-selected stale path", cwd=source)
        path = self.write(".github/instructions/source-selected-rule.instructions.md", "Mandatory local rules.\n")
        before = self.snapshot()
        result = self.run_bootstrap(source=source)
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("REVIEW", result.stderr)
        self.assertIn(path.relative_to(self.target).as_posix(), result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual("Mandatory local rules.\n", path.read_text(encoding="utf-8"))

    def test_unrelated_large_ignored_trees_are_not_read_or_copied(self):
        self.assert_unrelated_trees_untouched(is_git=True)

    def test_plain_project_ignored_trees_are_not_read_or_copied(self):
        self.assert_unrelated_trees_untouched(is_git=False)
        self.assertFalse((self.target / ".git").exists())

    def assert_unrelated_trees_untouched(self, is_git):
        if is_git:
            self.git("init")
        self.write(".gitignore", "node_modules/\n.venv/\nassets/\n")
        self.write("CLAUDE.md", "Local instructions that require import conversion.\n")
        forbidden = []
        for name in ("node_modules", ".venv", "assets"):
            directory = self.target / name
            directory.mkdir()
            forbidden.append(str(directory))
            for number in range(80):
                (directory / f"unrelated-{number}.bin").write_bytes(b"unrelated bytes")
            with (directory / "large.bin").open("wb") as stream:
                stream.truncate(64 * 1024 * 1024)
        fifo = self.target / "unrelated-pipe.py"
        if os.name != "nt":
            os.mkfifo(fifo)
        wrapper = (
            "import os, runpy, sys\n"
            f"forbidden = {forbidden!r}\n"
            "def audit(event, args):\n"
            "    if event not in ('open', 'os.scandir') or not args or not isinstance(args[0], (str, bytes, os.PathLike)):\n"
            "        return\n"
            "    path = os.path.abspath(os.fsdecode(args[0]))\n"
            "    if any(path == root or path.startswith(root + os.sep) for root in forbidden):\n"
            "        raise AssertionError('unrelated target tree accessed: ' + path)\n"
            "sys.addaudithook(audit)\n"
            f"sys.argv = [{str(SCRIPT)!r}, '--source', {str(ROOT)!r}]\n"
            f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
        )
        # -I deliberately ignores PYTHONPATH/sitecustomize. Inject the same read
        # oracle into those -c children explicitly; script children still inherit
        # sitecustomize. The read/copy assertion must cover every planning process.
        audit_code = wrapper.split("sys.argv =")[0]
        isolated_log = self.base / "isolated-audit-events"
        marker_code = (f"with open({str(isolated_log)!r}, 'a', encoding='utf-8') as audit_log: "
                       "audit_log.write('isolated child\\n')\n")
        instrument = (
            "import subprocess\n"
            "original_popen = subprocess.Popen\n"
            "def audited_popen(command, *args, **kwargs):\n"
            "    if '-I' in command and '-c' in command:\n"
            "        command = list(command)\n"
            "        at = command.index('-c') + 1\n"
            f"        command[at] = {audit_code!r} + {marker_code!r} + command[at]\n"
            "    return original_popen(command, *args, **kwargs)\n"
            "subprocess.Popen = audited_popen\n"
        )
        wrapper = wrapper.replace("sys.addaudithook(audit)\n", "sys.addaudithook(audit)\n" + instrument)
        audit_dir = self.base / "audit"
        audit_dir.mkdir()
        (audit_dir / "sitecustomize.py").write_text(audit_code, encoding="utf-8", newline="\n")
        env = dict(self.env, PYTHONPATH=str(audit_dir))
        # Start this trusted instrumentation in the same isolated/no-bytecode
        # entry mode as the CLI, so a restart cannot discard the read oracle.
        # Keep the parent hook, all three child markers and script-child audit.
        result = subprocess.run([sys.executable, "-I", "-B", "-c", wrapper], cwd=self.target, env=env,
                                capture_output=True, text=True, encoding="utf-8", timeout=120)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(3, len(isolated_log.read_text(encoding="utf-8").splitlines()),
                         "identity and both source plans must execute the audit oracle")
        self.assertTrue((self.target / "AGENTS.md").is_file())
        for directory in forbidden:
            self.assertEqual(64 * 1024 * 1024, (Path(directory) / "large.bin").stat().st_size)
            self.assertEqual(b"unrelated bytes", (Path(directory) / "unrelated-0.bin").read_bytes())
        if os.name != "nt":
            self.assertTrue(fifo.exists())

    @unittest.skipIf(os.name == "nt", "Named FIFO is a POSIX fixture")
    def test_copy_style_claude_does_not_scan_ignored_dependency_scripts(self):
        self.git("init")
        self.write(".gitignore", ".venv/\n")
        self.write("CLAUDE.md", "Local Claude instructions.\n")
        self.write(".venv/dependency.py", "# CLAUDE.md parity in an unrelated dependency\n")
        os.mkfifo(self.target / ".venv/dependency-pipe.py")
        result = self.run_bootstrap()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("@AGENTS.md", (self.target / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertEqual("# CLAUDE.md parity in an unrelated dependency\n",
                         (self.target / ".venv/dependency.py").read_text(encoding="utf-8"))
        self.assertEqual("Local Claude instructions.\n",
                         (self.target / "docs/ai-forward-pack/retired/CLAUDE.md.revpre.md").read_text(encoding="utf-8"))

    def test_source_specific_retired_backups_and_local_baselines(self):
        source = self.clone_source()
        applier = source / "pack/scripts/pack-apply.py"
        applier.write_text(applier.read_text(encoding="utf-8").replace(
            '"retired",\n                              "CLAUDE.md.rev',
            '"retired", "source-specific",\n                              "CLAUDE.md.rev'), encoding="utf-8", newline="\n")
        self.git("add", "pack/scripts/pack-apply.py", cwd=source)
        self.git("commit", "-m", "Fixture: source-specific retired backup", cwd=source)
        original = "Local Claude prose.\n"
        self.write("CLAUDE.md", original)
        self.write(".claude/skills/local/SKILL.md", "# Local skill\nKeep local instructions.\n")
        self.write(".claude/skills/local/reference.bin", "large unrelated reference asset\n")
        self.write(".claude/knowledge/local.md", "---\nload: reference\n---\nLocal reference knowledge.\n")
        result = self.run_bootstrap(source=source)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(original, (self.target / "docs/ai-forward-pack/retired/source-specific/CLAUDE.md.revpre.md").read_text(encoding="utf-8"))
        self.assertIn(original.strip(), (self.target / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertTrue((self.target / ".github/knowledge/ui-design-craft.md").is_file())
        config = json.loads((self.target / "docs/ai-forward-pack/context-budget.json").read_text(encoding="utf-8"))
        self.assertIn("local", config["skills_baseline"])
        self.assertEqual("large unrelated reference asset\n", (self.target / ".claude/skills/local/reference.bin").read_text(encoding="utf-8"))
        before = self.snapshot()
        repeat = self.run_bootstrap(source=source)
        self.assertEqual(0, repeat.returncode, repeat.stdout + repeat.stderr)
        self.assertEqual(before, self.snapshot())

    def test_tracked_parity_control_under_ignored_directory_still_requires_review(self):
        self.git("init")
        self.write(".gitignore", "scripts/\n")
        self.write("CLAUDE.md", "Local prose.\n")
        original = "# CLAUDE.md standing-method parity\nWrite-Host 'keep assertions'\n"
        self.write("scripts/tracked-parity.ps1", original)
        self.git("add", "-f", "scripts/tracked-parity.ps1")
        self.git("commit", "-m", "Fixture: tracked ignored control")
        index = (self.target / ".git/index").read_bytes()
        head = self.git("rev-parse", "HEAD")
        status = self.git("status", "--porcelain=v1")
        before = {path: value for path, value in self.snapshot().items()
                  if not path.startswith(".git/")}
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("REVIEW", result.stderr)
        self.assertIn("scripts/tracked-parity.ps1", result.stderr)
        after = {path: value for path, value in self.snapshot().items()
                 if not path.startswith(".git/")}
        self.assertEqual(before, after)
        self.assertEqual(head, self.git("rev-parse", "HEAD"))
        self.assertEqual(status, self.git("status", "--porcelain=v1"))
        self.assertEqual(index, (self.target / ".git/index").read_bytes())
        self.assertEqual(original, (self.target / "scripts/tracked-parity.ps1").read_text(encoding="utf-8"))
        self.assertFalse((self.target / "docs/ai-forward-pack/retired/tracked-parity.ps1").exists())

    def test_retired_backup_owned_paths_refuse_link_and_nonregular_conflicts(self):
        kinds = ["hardlink"] + (["symlink", "fifo"] if os.name != "nt" else [])
        for kind in kinds:
            with self.subTest(kind=kind):
                self.target = self.base / kind
                self.target.mkdir()
                self.write("CLAUDE.md", "Local Claude prose.\n")
                destination = self.target / "docs/ai-forward-pack/retired/CLAUDE.md.revpre.md"
                destination.parent.mkdir(parents=True)
                external = self.base / (kind + "-external.txt")
                external.write_text("External original.\n", encoding="utf-8", newline="\n")
                if kind == "hardlink":
                    os.link(external, destination)
                elif kind == "symlink":
                    destination.symlink_to(external)
                else:
                    os.mkfifo(destination)
                result = self.run_bootstrap()
                self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertIn("non-regular" if kind == "fifo" else kind, result.stderr)
                self.assertEqual("External original.\n", external.read_text(encoding="utf-8"))
                self.assertEqual("Local Claude prose.\n", (self.target / "CLAUDE.md").read_text(encoding="utf-8"))
                self.assertFalse((self.target / "AGENTS.md").exists())

    def test_failed_rollback_keeps_original_backup_and_reports_recovery_location(self):
        spec = importlib.util.spec_from_file_location("bootstrap_under_test", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.write("a-existing.txt", "original bytes\n")
        stage = self.base / "stage"
        stage.mkdir()
        (stage / "a-existing.txt").write_text("changed bytes\n", encoding="utf-8", newline="\n")
        (stage / "z-new.txt").write_text("new bytes\n", encoding="utf-8", newline="\n")
        recovery = self.base / "recovery"
        recovery.mkdir()
        paths = {"a-existing.txt", "z-new.txt"}
        before = module.inventory(self.target, paths)
        original_copy = module.shutil.copy2
        def failing_copy(source, destination, *args, **kwargs):
            if Path(source) == stage / "z-new.txt" or Path(source) == recovery / "a-existing.txt":
                raise OSError("injected promotion/rollback failure")
            return original_copy(source, destination, *args, **kwargs)
        with mock.patch.object(module.tempfile, "mkdtemp", return_value=str(recovery)), \
             mock.patch.object(module.shutil, "copy2", side_effect=failing_copy):
            with self.assertRaisesRegex(module.BootstrapError, "recovery incomplete") as error:
                module.promote(stage, self.target, before, paths)
        self.assertIn(str(recovery), str(error.exception))
        self.assertEqual("original bytes\n", (recovery / "a-existing.txt").read_text(encoding="utf-8"))
        self.assertEqual("changed bytes\n", (self.target / "a-existing.txt").read_text(encoding="utf-8"))

    @unittest.skipIf(os.name == "nt", "Windows symlink creation requires privileges")
    def test_unsafe_readback_retains_recovery_without_restoring_through_link(self):
        spec = importlib.util.spec_from_file_location("bootstrap_under_test", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.write("user.txt", "original bytes\n")
        external = self.base / "external.txt"
        external.write_text("external bytes\n", encoding="utf-8", newline="\n")
        stage = self.base / "stage"
        stage.mkdir()
        (stage / "user.txt").write_text("new bytes\n", encoding="utf-8", newline="\n")
        recovery = self.base / "recovery"
        recovery.mkdir()
        paths = {"user.txt"}
        before = module.inventory(self.target, paths)
        original_copy = module.shutil.copy2
        def replaced_copy(source, destination, *args, **kwargs):
            result = original_copy(source, destination, *args, **kwargs)
            if Path(source) == stage / "user.txt":
                Path(destination).unlink()
                Path(destination).symlink_to(external)
            return result
        with mock.patch.object(module.tempfile, "mkdtemp", return_value=str(recovery)), \
             mock.patch.object(module.shutil, "copy2", side_effect=replaced_copy):
            with self.assertRaisesRegex(module.BootstrapError, "recovery incomplete"):
                module.promote(stage, self.target, before, paths)
        self.assertEqual("original bytes\n", (recovery / "user.txt").read_text(encoding="utf-8"))
        self.assertEqual("external bytes\n", external.read_text(encoding="utf-8"))

    def test_baseline_failure_leaves_target_completely_untouched(self):
        source = self.clone_source()
        (source / "pack/scripts/context-budget.py").write_text("raise SystemExit('deliberate failing gate')\n", encoding="utf-8", newline="\n")
        self.git("add", "pack/scripts/context-budget.py", cwd=source)
        self.git("commit", "-m", "Fixture: broken baseline gate", cwd=source)
        self.write("existing.txt", "user data\n")
        before = self.snapshot()
        result = self.run_bootstrap(source=source)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(before, self.snapshot(), "a failing gate must not leave a partial install")
        self.assertNotIn("AI-Forward installed:", result.stdout)

    def test_git_subdirectory_installs_at_repo_root_preserving_dirty_index_identity(self):
        self.git("init")
        self.git("remote", "add", "origin", "https://example.invalid/canonical-app.git")
        self.write("app.txt", "base\n")
        self.write("spikes/tracked.txt", "keep tracked probe\n")
        self.git("add", ".")
        self.git("commit", "-m", "Disposable target baseline")
        head = self.git("rev-parse", "HEAD")
        self.write("app.txt", "staged changes\n")
        self.git("add", "app.txt")
        self.write("app.txt", "unstaged changes\n")
        self.write("untracked.txt", "untracked data\n")
        index = (self.target / ".git/index").read_bytes()
        config = (self.target / ".git/config").read_bytes()
        child = self.target / "src"
        child.mkdir()
        result = self.run_bootstrap(cwd=child)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue((self.target / "AGENTS.md").is_file())
        self.assertFalse((child / "AGENTS.md").exists())
        self.assertEqual(head, self.git("rev-parse", "HEAD"))
        self.assertEqual(index, (self.target / ".git/index").read_bytes())
        self.assertEqual(config, (self.target / ".git/config").read_bytes())
        self.assertEqual("unstaged changes\n", (self.target / "app.txt").read_text(encoding="utf-8"))
        self.assertEqual("untracked data\n", (self.target / "untracked.txt").read_text(encoding="utf-8"))
        self.assertTrue((self.target / "AGENTS.md").read_text(encoding="utf-8").startswith("# canonical-app\n"))
        self.assertNotIn("\nspikes/\n", (self.target / ".gitignore").read_text(encoding="utf-8"))

    @unittest.skipIf(os.name == "nt", "Windows symlink creation requires privileges")
    def test_managed_symlink_parent_is_refused_before_external_or_partial_writes(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "sentinel.txt").write_text("must survive\n", encoding="utf-8", newline="\n")
        (self.target / ".github").symlink_to(outside, target_is_directory=True)
        before = self.snapshot()
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("symlink", result.stderr.lower())
        self.assertEqual(before, self.snapshot())
        self.assertEqual(["sentinel.txt"], sorted(p.name for p in outside.iterdir()))

    def test_success_exit_with_incomplete_deployment_is_not_accepted(self):
        source = self.clone_source()
        script = source / "pack/scripts/pack-apply.py"
        script.write_text(script.read_text(encoding="utf-8").replace("        self.agents()", "        if self.dry:\n            self.agents()"), encoding="utf-8", newline="\n")
        self.git("add", "pack/scripts/pack-apply.py", cwd=source)
        self.git("commit", "-m", "Fixture: apply omits knowledge", cwd=source)
        self.write("user.txt", "keep\n")
        before = self.snapshot()
        result = self.run_bootstrap(source=source)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("verification", result.stderr.lower())
        self.assertEqual(before, self.snapshot())

    def test_promotion_io_failure_rolls_back_new_files_and_restores_user_bytes(self):
        spec = importlib.util.spec_from_file_location("bootstrap_under_test", SCRIPT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.write("z-existing.txt", "old user bytes\n")
        stage = self.base / "stage"
        (stage / "nested").mkdir(parents=True)
        (stage / "nested/aa-new.txt").write_text("new\n", encoding="utf-8", newline="\n")
        (stage / "z-existing.txt").write_text("replacement\n", encoding="utf-8", newline="\n")
        before = self.snapshot()
        original_copy = module.shutil.copy2
        failed = []
        def failing_copy(source, destination, *args, **kwargs):
            if Path(destination) == self.target / "z-existing.txt" and not failed:
                failed.append(True)
                raise OSError("injected disk failure")
            return original_copy(source, destination, *args, **kwargs)
        with mock.patch.object(module.shutil, "copy2", side_effect=failing_copy):
            with self.assertRaises((module.BootstrapError, OSError)):
                paths = {"nested/aa-new.txt", "z-existing.txt"}
                module.promote(stage, self.target, module.inventory(self.target, paths), paths)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(["z-existing.txt"], sorted(p.name for p in self.target.iterdir()))

    def test_local_managed_front_door_deviation_is_not_silently_erased(self):
        first = self.run_bootstrap()
        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        path = self.target / "AGENTS.md"
        path.write_text(path.read_text(encoding="utf-8").replace("<!-- AI-FORWARD-PACK:END -->",
                        "Local managed-block deviation.\n<!-- AI-FORWARD-PACK:END -->"), encoding="utf-8", newline="\n")
        before = self.snapshot()
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("managed block", result.stderr.lower())
        self.assertEqual(before, self.snapshot())

    def test_repeat_install_is_byte_idempotent_and_reports_current_state(self):
        first = self.run_bootstrap()
        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        skill = self.target / ".claude/skills/also/SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "\nLocal skill extension.\n", encoding="utf-8", newline="\n")
        before = self.snapshot()
        mtimes = {p: p.stat().st_mtime_ns for p in self.target.rglob("*") if p.is_file()}
        result = self.run_bootstrap()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        after = self.snapshot()
        self.assertEqual(before, after)
        self.assertEqual(mtimes, {p: p.stat().st_mtime_ns for p in self.target.rglob("*") if p.is_file()})
        self.assertIn("already current", result.stdout)
        self.assertIn("KEEP", result.stdout)

    def test_requested_nondefault_branch_updates_using_history_and_preserves_deviations(self):
        source = self.clone_source()
        baseline = self.git("rev-parse", "HEAD", cwd=source)
        self.git("checkout", "-b", "preview", cwd=source)
        install = source / "pack/adapters/INSTALL.md"
        revision_match = re.search(r"(?m)^revision:\s*(\d+)", install.read_text(encoding="utf-8"))
        assert revision_match is not None
        revision = int(revision_match.group(1))
        install.write_text(re.sub(r"(?m)^revision:\s*\d+", f"revision: {revision + 1}", install.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        also = source / "pack/commands/also/SKILL.md"
        also.write_text(also.read_text(encoding="utf-8").replace("# ", "New upstream instruction.\n\n# ", 1), encoding="utf-8", newline="\n")
        self.git("add", "pack", cwd=source)
        self.git("commit", "-m", "Fixture: preview revision", cwd=source)
        preview = self.git("rev-parse", "HEAD", cwd=source)
        self.git("checkout", "--detach", baseline, cwd=source)
        first = self.run_bootstrap(source=source)
        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        local = self.target / ".claude/skills/also/SKILL.md"
        local.write_text(local.read_text(encoding="utf-8") + "\nLocal extension must survive.\n", encoding="utf-8", newline="\n")
        result = self.run_bootstrap("--ref", "preview", source=source)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("updated", result.stdout)
        self.assertIn("MERGE", result.stdout)
        self.assertIn("Local extension must survive.", local.read_text(encoding="utf-8"))
        self.assertIn("New upstream instruction.", local.read_text(encoding="utf-8"))
        receipt = json.loads((self.target / "docs/ai-forward-pack/bootstrap-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(preview, receipt["source_commit"])
        self.assertEqual(revision + 1, receipt["pack_revision"])
        before = self.snapshot()
        refusal = self.run_bootstrap("--ref", baseline, source=source)
        self.assertNotEqual(0, refusal.returncode)
        self.assertEqual(before, self.snapshot())

    def test_conflict_is_actionable_without_any_partial_install(self):
        self.write(".claude/skills/implement/SKILL.md", "unrelated user instruction\n")
        self.write("user.txt", "must survive\n")
        before = self.snapshot()
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(before, self.snapshot())
        self.assertIn("CONFLICT", result.stderr)
        self.assertIn(".claude/skills/implement/SKILL.md", result.stderr)
        self.assertIn("reconcile", result.stderr)
        self.assertLess(len(result.stderr), 4000)

    def test_target_change_during_preflight_is_refused_instead_of_overwritten(self):
        spec = importlib.util.spec_from_file_location("bootstrap_under_test", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.write("user.txt", "original\n")
        paths = {"user.txt"}
        before = module.inventory(self.target, paths)
        stage = self.base / "stage"
        stage.mkdir()
        (stage / "user.txt").write_text("planned replacement\n", encoding="utf-8", newline="\n")
        self.write("user.txt", "concurrent user changes\n")
        with self.assertRaises(module.BootstrapError):
            module.promote(stage, self.target, before, paths)
        self.assertEqual("concurrent user changes\n", (self.target / "user.txt").read_text(encoding="utf-8"))

    def test_explicit_target_installs_there_without_changing_invocation_directory(self):
        invocation = self.base / "other"
        invocation.mkdir()
        result = self.run_bootstrap("--target", str(self.target), cwd=invocation)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue((self.target / "AGENTS.md").is_file())
        self.assertEqual([], list(invocation.iterdir()))

    def test_explicit_git_subdirectory_is_refused_not_silently_redirected(self):
        self.git("init")
        self.write("user.txt", "preserve\n")
        child = self.target / "src"
        child.mkdir()
        before = self.snapshot()
        result = self.run_bootstrap("--target", str(child))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Git root", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_ambient_git_path_overrides_cannot_redirect_installation(self):
        other = self.base / "other-repository"
        other.mkdir()
        self.git("init", cwd=other)
        (other / "user.txt").write_text("other repository data\n", encoding="utf-8", newline="\n")
        self.env["GIT_DIR"] = str(other / ".git")
        self.env["GIT_WORK_TREE"] = str(other)
        result = self.run_bootstrap()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue((self.target / "AGENTS.md").exists())
        self.assertFalse((other / "AGENTS.md").exists())
        self.assertEqual("other repository data\n", (other / "user.txt").read_text(encoding="utf-8"))

    def test_promotion_checks_installed_bytes_not_just_successful_copy_calls(self):
        spec = importlib.util.spec_from_file_location("bootstrap_under_test", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.write("user.txt", "old bytes\n")
        stage = self.base / "stage"
        stage.mkdir()
        (stage / "user.txt").write_text("new bytes\n", encoding="utf-8", newline="\n")
        before = self.snapshot()
        original_copy = module.shutil.copy2
        def dropped_copy(source, destination, *args, **kwargs):
            if Path(source) == stage / "user.txt":
                return str(destination)
            return original_copy(source, destination, *args, **kwargs)
        with mock.patch.object(module.shutil, "copy2", side_effect=dropped_copy):
            with self.assertRaises(module.BootstrapError):
                paths = {"user.txt"}
                module.promote(stage, self.target, module.inventory(self.target, paths), paths)
        self.assertEqual(before, self.snapshot())

    def test_managed_windows_reparse_attribute_is_refused(self):
        spec = importlib.util.spec_from_file_location("bootstrap_under_test", SCRIPT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        parent = self.target / ".github"
        parent.mkdir()
        info = parent.lstat()
        reparse = mock.Mock(st_mode=info.st_mode, st_nlink=info.st_nlink,
                            st_file_attributes=0x400)
        original_lstat = Path.lstat
        def lstat(path, *args, **kwargs):
            return reparse if path == parent else original_lstat(path, *args, **kwargs)
        with mock.patch.object(Path, "lstat", lstat):
            with self.assertRaisesRegex(module.BootstrapError, "reparse"):
                module.validate_paths(self.target, [".github/prompts/implement.prompt.md"])

    @unittest.skipUnless(os.name == "nt", "Native Windows junction fixture")
    def test_managed_windows_junction_is_refused_before_external_writes(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "sentinel.txt").write_text("keep\n", encoding="utf-8", newline="\n")
        linked = subprocess.run(["cmd", "/c", "mklink", "/J", str(self.target / ".github"), str(outside)],
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(0, linked.returncode, linked.stdout + linked.stderr)
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("reparse", result.stderr.lower())
        self.assertEqual(["sentinel.txt"], sorted(path.name for path in outside.iterdir()))

    def test_managed_hardlink_is_refused_before_altering_external_user_file(self):
        external = self.base / "external-instructions.md"
        external.write_text("External instructions must survive.\n", encoding="utf-8", newline="\n")
        os.link(external, self.target / "AGENTS.md")
        before = self.snapshot()
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("hardlink", result.stderr.lower())
        self.assertEqual(before, self.snapshot())
        self.assertEqual("External instructions must survive.\n", external.read_text(encoding="utf-8"))

    def test_existing_project_policies_hooks_instructions_and_docs_are_preserved(self):
        settings = {"permissions": {"allow": ["Read"], "deny": ["Bash(*)"]},
                    "model": "project-model", "skipDangerousModePermissionPrompt": False,
                    "hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "local-start"}]}]}}
        bundle = {"enabled": False, "PreToolUse": [{"hooks": [{"command": "local-ownership"}]}]}
        self.write(".claude/settings.json", json.dumps(settings))
        self.write(".agents/hooks.json", json.dumps({"ownership-guard": bundle}))
        untouched = {".claude/settings.local.json": '{"permissions":{"deny":["Write"]}}\n',
                     ".codex/config.toml": 'model = "custom-model"\n[projects.local]\ntrust_level = "untrusted"\n',
                     ".github/instructions/local.instructions.md": "Project-local instructions.\n",
                     ".github/hooks/local.json": '{"local":true}\n',
                     "docs/index.html": "<html>Existing user explorer</html>\n",
                     "docs/docs-index.js": "window.DOCS_INDEX = {preserved:true};\n",
                     "docs/specs/user.md": "Authored user spec.\n",
                     ".editorconfig": "root = true\n[*]\nindent_size = 7\n"}
        for path, text in untouched.items():
            self.write(path, text)
        self.write("AGENTS.md", "Project instructions before any pack.\n")
        self.write("CLAUDE.md", "Claude-specific local instruction.\n")
        global_before = Path(self.env["GIT_CONFIG_GLOBAL"]).exists()
        result = self.run_bootstrap()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for path, text in untouched.items():
            self.assertEqual(text, (self.target / path).read_text(encoding="utf-8"), path)
        merged = json.loads((self.target / ".claude/settings.json").read_text(encoding="utf-8"))
        for key in ("permissions", "model", "skipDangerousModePermissionPrompt"):
            self.assertEqual(settings[key], merged[key])
        self.assertIn(settings["hooks"]["SessionStart"][0], merged["hooks"]["SessionStart"])
        self.assertEqual(bundle, json.loads((self.target / ".agents/hooks.json").read_text(encoding="utf-8"))["ownership-guard"])
        self.assertIn("Project instructions before any pack.", (self.target / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn("Claude-specific local instruction.", (self.target / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertEqual(global_before, Path(self.env["GIT_CONFIG_GLOBAL"]).exists())

    def test_review_gate_stops_before_converting_or_installing_anything(self):
        self.write("CLAUDE.md", "Keep old Claude instructions.\n")
        self.write("scripts/parity.py", "# CLAUDE.md standing-method parity must match\n")
        before = self.snapshot()
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("REVIEW", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_invalid_hook_settings_stop_before_any_target_writes(self):
        self.write(".claude/settings.json", '{"hooks": {"PreToolUse": "bad shape"}}')
        before = self.snapshot()
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("HOOK-SETTINGS-INVALID", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_linked_worktree_preserves_primary_checkout_identity_and_git_metadata(self):
        primary = self.base / "canonical-primary"
        primary.mkdir()
        self.git("init", cwd=primary)
        (primary / "user.txt").write_text("primary data\n", encoding="utf-8", newline="\n")
        self.git("add", ".", cwd=primary)
        self.git("commit", "-m", "Disposable primary", cwd=primary)
        linked = self.base / "renamed-feature-worktree"
        self.git("worktree", "add", "-b", "feature", str(linked), cwd=primary)
        self.target = linked
        git_pointer = (linked / ".git").read_bytes()
        common_before = {p.relative_to(primary / ".git").as_posix(): p.read_bytes()
                         for p in (primary / ".git").rglob("*") if p.is_file()}
        result = self.run_bootstrap()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue((linked / "AGENTS.md").read_text(encoding="utf-8").startswith("# canonical-primary\n"))
        self.assertFalse((primary / "AGENTS.md").exists())
        self.assertEqual(git_pointer, (linked / ".git").read_bytes())
        self.assertEqual(common_before, {p.relative_to(primary / ".git").as_posix(): p.read_bytes()
                                       for p in (primary / ".git").rglob("*") if p.is_file()})

    def test_missing_git_reports_failure_without_target_writes(self):
        self.env["PATH"] = str(self.base / "no-executables")
        before = self.snapshot()
        result = self.run_bootstrap()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("git", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_remote_exact_merge_commit_not_in_default_clone_is_fetched(self):
        source = self.clone_source()
        baseline = self.git("rev-parse", "HEAD", cwd=source)
        (source / "merge-fixture.txt").write_text("hidden merge object\n", encoding="utf-8", newline="\n")
        self.git("add", "merge-fixture.txt", cwd=source)
        self.git("commit", "-m", "Fixture: pull merge object", cwd=source)
        commit = self.git("rev-parse", "HEAD", cwd=source)
        self.git("update-ref", "refs/pull/1/merge", commit, cwd=source)
        self.git("reset", "--hard", baseline, cwd=source)
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", source.as_uri(), "--ref", commit],
                                cwd=self.target, env=self.env, capture_output=True,
                                text=True, encoding="utf-8", timeout=120)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        receipt = json.loads((self.target / "docs/ai-forward-pack/bootstrap-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(commit, receipt["requested_ref"])
        self.assertEqual(commit, receipt["source_commit"])

    def test_fetch_fallback_does_not_interpret_requested_ref_as_a_refspec(self):
        branch = self.git("branch", "--show-current", cwd=ROOT)
        for ref in (f"refs/heads/{branch}:refs/heads/redirected", "refs/heads/*"):
            with self.subTest(ref=ref):
                before = self.snapshot()
                result = self.run_bootstrap("--ref", ref)
                self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(before, self.snapshot())

    def test_unknown_ref_fails_without_target_writes(self):
        before = self.snapshot()
        result = self.run_bootstrap("--ref", "does-not-exist")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(before, self.snapshot())

    @unittest.skipUnless(shutil.which("uv"), "uv CLI not installed")
    def test_uv_remote_script_one_liner_ignores_project_environment(self):
        self.write("pyproject.toml", "[project]\nname = 'unrelated'\nversion = '0.0.0'\ndependencies = ['nonexistent-bootstrap-project-dependency']\n")
        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass
        handler = functools.partial(QuietHandler, directory=str(ROOT))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/bootstrap.py"
            env = dict(self.env, UV_CACHE_DIR=str(self.base / "uv-cache"))
            result = subprocess.run(["uv", "run", "--no-config", "--no-project", "--script", url,
                                     "--source", str(ROOT)], cwd=self.target, env=env,
                                    capture_output=True, text=True, encoding="utf-8", timeout=120)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertTrue((self.target / "AGENTS.md").is_file())
            self.assertFalse((self.target / ".venv").exists())
            self.assertFalse((self.target / "uv.lock").exists())
            self.assertFalse((self.target / "bootstrap.py").exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_source_checkout_does_not_execute_user_global_git_hooks(self):
        hooks = self.base / "global-hooks"
        hooks.mkdir()
        marker = self.base / "unexpected-hook-side-effect"
        hook = hooks / "post-checkout"
        hook.write_text(f'#!/bin/sh\nprintf unsafe > "{marker.as_posix()}"\n', encoding="utf-8", newline="\n")
        hook.chmod(0o755)
        Path(self.env["GIT_CONFIG_GLOBAL"]).write_text(f'[core]\n    hooksPath = "{hooks.as_posix()}"\n', encoding="utf-8", newline="\n")
        result = self.run_bootstrap()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertFalse(marker.exists(), "installer must not execute global checkout hooks")

    def test_process_timeout_terminates_child_before_late_side_effect(self):
        spec = importlib.util.spec_from_file_location("bootstrap_under_test", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        marker = self.base / "late-child-write"
        child_code = f"import time; from pathlib import Path; time.sleep(1); Path({str(marker)!r}).write_text('late')"
        parent_code = f"import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {child_code!r}]); time.sleep(10)"
        with self.assertRaises(module.BootstrapError):
            module.run([sys.executable, "-c", parent_code], timeout=0.3)
        time.sleep(1.2)
        self.assertFalse(marker.exists(), "timed-out descendants must not continue writing")

    @unittest.skipIf(os.name == "nt", "Named FIFO is a POSIX fixture")
    def test_nonregular_managed_file_is_refused_without_blocking_or_writing(self):
        fifo = self.target / "AGENTS.md"
        os.mkfifo(fifo)
        try:
            result = subprocess.run([sys.executable, str(SCRIPT), "--source", str(ROOT)],
                                    cwd=self.target, env=self.env, capture_output=True,
                                    text=True, timeout=15)
        except subprocess.TimeoutExpired:
            self.fail("bootstrap blocked reading an unsupported FIFO")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("non-regular", result.stderr)
        self.assertLess(len(result.stderr), 500, "managed-path refusal should not dump a source-import traceback")
        self.assertEqual(["AGENTS.md"], sorted(p.name for p in self.target.iterdir()))

    @unittest.skipIf(os.name == "nt", "Named FIFO is a POSIX fixture")
    def test_nonregular_hook_configuration_is_refused_before_open(self):
        spec = importlib.util.spec_from_file_location("bootstrap_under_test", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        (self.target / ".claude").mkdir()
        os.mkfifo(self.target / ".claude/settings.json")
        with mock.patch.dict(os.environ, self.env, clear=True):
            with self.assertRaisesRegex(module.BootstrapError, "non-regular"):
                module.run([sys.executable, str(SCRIPT), "--source", str(ROOT)], cwd=self.target, timeout=6)
        self.assertEqual([".claude"], sorted(path.name for path in self.target.iterdir()))

    def test_bootstrap_obeys_existing_portable_text_io_contract(self):
        spec = importlib.util.spec_from_file_location("portable_io", ROOT / "pack/scripts/verify-portable-text-io.py")
        assert spec and spec.loader
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        self.assertEqual([], gate.scan_source(SCRIPT.read_text(encoding="utf-8")))

    def test_dry_run_performs_no_target_writes(self):
        self.write("pyproject.toml", "[project]\nname = 'unrelated'\nversion = '0.0.0'\n")
        self.write("notes.txt", "preserve me\n")
        before = self.snapshot()
        result = self.run_bootstrap("--dry-run")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertIn("no target writes", result.stdout)
        self.assertIn("ADD", result.stdout)

    def test_fresh_plain_project_installs_actual_pack_surfaces_without_git_init(self):
        self.write("app.txt", "original user work\n")
        result = self.run_bootstrap()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for relative in ("AGENTS.md", "CLAUDE.md", ".claude/skills/implement/SKILL.md",
                         ".github/prompts/implement.prompt.md", ".grok/skills/implement/SKILL.md",
                         ".agents/skills/implement/SKILL.md", "docs/ai-forward-pack/codex.md",
                         ".github/hooks/ai-forward.json", ".grok/hooks/ai-forward.json",
                         ".agents/hooks.json", ".claude/settings.json",
                         "docs/ai-forward-pack/scripts/pack-apply.py"):
            self.assertTrue((self.target / relative).is_file(), relative)
        self.assertEqual("original user work\n", (self.target / "app.txt").read_text(encoding="utf-8"))
        self.assertFalse((self.target / ".git").exists())
        receipt = json.loads((self.target / "docs/ai-forward-pack/bootstrap-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=ROOT), receipt["source_commit"])
        self.assertIsInstance(receipt["pack_revision"], int)
        self.assertIn("/deliver", result.stdout)
        self.assertIn("$deliver", result.stdout)


if __name__ == "__main__":
    unittest.main()
