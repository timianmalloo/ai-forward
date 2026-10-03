"""Bootstrap preservation and handoff regressions in disposable projects."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "bootstrap.py"


class BootstrapPreservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bootstrap-preservation-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.target = self.base / "project Ω with spaces"
        self.target.mkdir()
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1",
                        GIT_CONFIG_GLOBAL=str(self.base / "global-config"),
                        GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0",
                        PYTHONDONTWRITEBYTECODE="1",
                        GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.invalid",
                        GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.invalid")
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
                    "GIT_NAMESPACE", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS"):
            self.env.pop(key, None)
        self.source_commit = self.git("rev-parse", "HEAD", cwd=ROOT)

    def git(self, *args, cwd=None):
        result = subprocess.run(["git", *args], cwd=cwd or self.target, env=self.env,
                                capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result.stdout.strip()

    def write(self, relative, content):
        path = self.target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def snapshot(self):
        return {path.relative_to(self.target).as_posix():
                (path.stat().st_mode, path.stat().st_mtime_ns,
                 hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None)
                for path in [self.target, *self.target.rglob("*")]}

    def bootstrap(self, *args, source=ROOT):
        return subprocess.run([sys.executable, "-I", "-B", str(SCRIPT),
                               "--source", str(source), "--ref", self.source_commit, *args],
                              cwd=self.target, env=self.env, capture_output=True,
                              text=True, encoding="utf-8", timeout=120)

    def archive_fixture(self, installed=False, archive=b"Previous archive MUST SURVIVE.\n"):
        active = b"Active project instructions.\n"
        self.write("CLAUDE.md", active)
        revision = "pre"
        if installed:
            install = self.git("show", f"{self.source_commit}:pack/adapters/INSTALL.md", cwd=ROOT)
            self.write("docs/ai-forward-pack/INSTALL.md", (install + "\n").encode("utf-8"))
            revision = next(line.split(":", 1)[1].strip() for line in install.splitlines()
                            if line.startswith("revision:"))
        relative = f"docs/ai-forward-pack/retired/CLAUDE.md.rev{revision}.md"
        self.write(relative, archive)
        return relative, active

    def test_differing_regular_archives_refuse_without_any_target_writes(self):
        for installed in (False, True):
            with self.subTest(installed_revision=installed):
                self.target = self.base / ("installed" if installed else "first install")
                self.target.mkdir()
                relative, active = self.archive_fixture(installed=installed)
                before = self.snapshot()
                result = self.bootstrap()
                self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(before, self.snapshot(), "Refusal must preserve the complete target")
                self.assertEqual(active, (self.target / "CLAUDE.md").read_bytes())
                self.assertIn("CONFLICT", result.stderr)
                self.assertIn(relative, result.stderr)
                self.assertIn("reconcile", result.stderr)
                self.assertFalse((self.target / "AGENTS.md").exists())

    def test_identical_regular_archives_install_and_repeat_without_rewriting_archive(self):
        for installed in (False, True):
            with self.subTest(installed_revision=installed):
                self.target = self.base / ("installed identical" if installed else "first identical")
                self.target.mkdir()
                relative, active = self.archive_fixture(installed=installed,
                                                       archive=b"Active project instructions.\n")
                archive = self.target / relative
                before_archive = (archive.read_bytes(), archive.stat().st_mode, archive.stat().st_mtime_ns)
                result = self.bootstrap()
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(before_archive,
                                 (archive.read_bytes(), archive.stat().st_mode, archive.stat().st_mtime_ns))
                self.assertIn("@AGENTS.md", (self.target / "CLAUDE.md").read_text(encoding="utf-8"))
                self.assertEqual(active, archive.read_bytes())
                before_repeat = self.snapshot()
                repeated = self.bootstrap()
                self.assertEqual(0, repeated.returncode, repeated.stdout + repeated.stderr)
                self.assertIn("already current", repeated.stdout)
                self.assertEqual(before_repeat, self.snapshot())

    def test_source_selected_archive_collision_is_not_a_duplicate_backup_path_map(self):
        source = self.base / "source"
        self.git("clone", "--no-hardlinks", "--", str(ROOT), str(source), cwd=self.base)
        self.git("checkout", "--detach", self.source_commit, cwd=source)
        applier = source / "pack/scripts/pack-apply.py"
        original = applier.read_text(encoding="utf-8")
        marker = '"retired",\n                              "CLAUDE.md.rev'
        self.assertEqual(1, original.count(marker))
        applier.write_text(original.replace(marker, '"retired", "source-chosen",\n                              "CLAUDE.md.rev'),
                           encoding="utf-8", newline="\n")
        self.git("add", "pack/scripts/pack-apply.py", cwd=source)
        self.git("commit", "-m", "Fixture: source-selected archive destination", cwd=source)
        self.source_commit = self.git("rev-parse", "HEAD", cwd=source)
        self.write("CLAUDE.md", b"Active project instructions.\n")
        relative = "docs/ai-forward-pack/retired/source-chosen/CLAUDE.md.revpre.md"
        self.write(relative, b"Previous source-chosen archive MUST SURVIVE.\n")
        before = self.snapshot()
        result = self.bootstrap(source=source)
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("CONFLICT", result.stderr)
        self.assertIn(relative, result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_absent_attributes_preserve_configured_product_checkout_policy(self):
        for config in (("core.autocrlf", "true"), ("core.eol", "crlf")):
            with self.subTest(config=config):
                self.target = self.base / config[0]
                self.target.mkdir()
                self.git("init")
                self.git("config", *config)
                global_attributes = self.base / (config[0] + "-attributes")
                global_attributes.write_bytes(b"* text=auto\n")
                self.git("config", "core.attributesFile", str(global_attributes))
                info_attributes = self.write(".git/info/attributes", b"product.txt whitespace=blank-at-eof\n")
                self.write("product.txt", b"Original product.\r\n")
                self.git("add", "product.txt")
                self.git("commit", "-m", "Fixture: existing product policy")
                self.write("product.txt", b"Staged product.\r\n")
                self.git("add", "product.txt")
                product = self.write("product.txt", b"Dirty product.\r\n")
                self.write("src/untracked.txt", b"Untracked product.\r\n")
                self.write(".claude/knowledge/local.md", b"---\nload: reference\n---\nLocal knowledge.\n")
                policy = self.git("check-attr", "text", "eol", "whitespace", "--",
                                  "product.txt", "src/untracked.txt", ".claude/knowledge/local.md")
                originals = {path: path.read_bytes() for path in
                             (product, self.target / "src/untracked.txt", self.target / ".git/config",
                              self.target / ".git/index", info_attributes, global_attributes)}
                head = self.git("rev-parse", "HEAD")
                result = self.bootstrap()
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(policy, self.git("check-attr", "text", "eol", "whitespace", "--",
                                                  "product.txt", "src/untracked.txt", ".claude/knowledge/local.md"))
                self.assertEqual(originals, {path: path.read_bytes() for path in originals})
                self.assertEqual(head, self.git("rev-parse", "HEAD"))
                self.assertEqual(".claude/skills/deliver/SKILL.md: eol: lf",
                                 self.git("check-attr", "eol", "--", ".claude/skills/deliver/SKILL.md"))
                self.git("add", "AGENTS.md", "CLAUDE.md", ".gitattributes")
                self.git("commit", "-m", "Fixture: installed pack and prior staged product")
                checkout = self.base / (config[0] + "-checkout")
                self.git("clone", "--no-checkout", "--", str(self.target), str(checkout), cwd=self.base)
                self.git("config", *config, cwd=checkout)
                self.git("config", "core.attributesFile", str(global_attributes), cwd=checkout)
                self.git("checkout", "--force", "HEAD", cwd=checkout)
                self.assertEqual(b"Staged product.\r\n", (checkout / "product.txt").read_bytes(),
                                 "A future checkout must still obey the project's CRLF policy")
                self.assertNotIn(b"\r\n", (checkout / "AGENTS.md").read_bytes())

    def test_global_and_info_attribute_layers_remain_effective_and_untouched(self):
        for layer in ("global", "info"):
            with self.subTest(attribute_layer=layer):
                self.target = self.base / layer
                self.target.mkdir()
                self.git("init")
                if layer == "global":
                    policy_file = self.base / "global-attributes"
                    policy_file.write_bytes(b"* -text\n")
                    self.git("config", "core.attributesFile", str(policy_file))
                else:
                    policy_file = self.write(".git/info/attributes", b"* -text\n")
                self.write("product.txt", b"Product bytes.\r\n")
                self.write("src/product.txt", b"Nested product bytes.\r\n")
                self.git("add", "product.txt", "src/product.txt")
                self.git("commit", "-m", "Fixture: product attribute layer")
                queried = ("check-attr", "text", "eol", "--", "product.txt", "src/product.txt")
                policy = self.git(*queried)
                preserved_paths = (policy_file, self.target / ".git/config", self.target / ".git/index",
                                   self.target / "product.txt", self.target / "src/product.txt")
                before = {path: (path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns)
                          for path in preserved_paths}
                result = self.bootstrap()
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(policy, self.git(*queried))
                self.assertEqual(before, {path: (path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns)
                                          for path in preserved_paths})
                self.assertEqual(".claude/skills/deliver/SKILL.md: eol: lf",
                                 self.git("check-attr", "eol", "--", ".claude/skills/deliver/SKILL.md"))
                repeat_before = self.snapshot()
                repeated = self.bootstrap()
                self.assertEqual(0, repeated.returncode, repeated.stdout + repeated.stderr)
                self.assertIn("already current", repeated.stdout)
                self.assertEqual(repeat_before, self.snapshot())

    def test_source_skipped_product_files_do_not_receive_pack_attributes(self):
        self.git("init")
        self.git("config", "core.autocrlf", "true")
        product_paths = ("docs/index.html", "docs/docs-index.js", ".editorconfig")
        for relative in product_paths:
            self.write(relative, b"Project-owned content.\r\n")
        policy = self.git("check-attr", "text", "eol", "--", *product_paths)
        before = {relative: (self.target / relative).read_bytes() for relative in product_paths}
        result = self.bootstrap()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(policy, self.git("check-attr", "text", "eol", "--", *product_paths))
        self.assertEqual(before, {relative: (self.target / relative).read_bytes() for relative in product_paths})

    @unittest.skipIf(os.name == "nt", "Literal glob characters are POSIX filename fixtures")
    def test_source_selected_attribute_paths_are_literal_and_root_anchored(self):
        source = self.base / "source"
        self.git("clone", "--no-hardlinks", "--", str(ROOT), str(source), cwd=self.base)
        self.git("checkout", "--detach", self.source_commit, cwd=source)
        name = "literal [a]*? Ω"
        self.git("mv", "pack/commands/also", "pack/commands/" + name, cwd=source)
        self.git("commit", "-m", "Fixture: source-selected literal attribute paths", cwd=source)
        self.source_commit = self.git("rev-parse", "HEAD", cwd=source)
        self.git("init")
        self.git("config", "core.autocrlf", "true")
        product_paths = ("nested/AGENTS.md", ".claude/skills/literal aXX Ω/SKILL.md")
        for relative in product_paths:
            self.write(relative, b"Unrelated product instructions.\r\n")
        policy = self.git("check-attr", "text", "eol", "--", *product_paths)
        result = self.bootstrap(source=source)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(policy, self.git("check-attr", "text", "eol", "--", *product_paths))
        managed = f".claude/skills/{name}/SKILL.md"
        self.assertTrue((self.target / managed).is_file())
        queried = self.git("-c", "core.quotePath=false", "check-attr", "eol", "--", managed)
        self.assertTrue(queried.endswith(": eol: lf"), queried)
        before = self.snapshot()
        repeated = self.bootstrap(source=source)
        self.assertEqual(0, repeated.returncode, repeated.stdout + repeated.stderr)
        self.assertEqual(before, self.snapshot())

    def test_success_handoff_distinguishes_hosts_and_explains_skill_discovery(self):
        result = self.bootstrap()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("Claude Code: /deliver <your goal>", result.stdout)
        self.assertIn("Codex: $deliver <your goal>", result.stdout)
        self.assertIn("Copilot CLI:", result.stdout)
        self.assertIn("Use the /deliver skill to <your goal>", result.stdout)
        self.assertIn("/skills reload", result.stdout)
        self.assertIn("/skills info deliver", result.stdout)
        self.assertIn("Grok Build/Antigravity: select/request the deliver skill", result.stdout)
        self.assertIn("refresh/restart", result.stdout)
        self.assertNotIn("(Claude/Copilot/Grok/Antigravity)", result.stdout)
        self.assertTrue((self.target / "AGENTS.md").is_file())


if __name__ == "__main__":
    unittest.main()
