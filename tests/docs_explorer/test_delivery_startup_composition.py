"""Installed startup reachability is distinct from same-task checkpoint continuity.

These use real local bootstrap, audit/compiler/delivery CLIs and fresh hook
subprocesses; synthetic reviewer receipts test mechanics, not native host consent.
"""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Literal, overload
import unittest

import test_delivery as _delivery_fixture

ROOT = Path(__file__).resolve().parents[2]


class DeliveryStartupCompositionTests(unittest.TestCase):
    setUp = _delivery_fixture.DeliveryTests.setUp
    write = _delivery_fixture.DeliveryTests.write
    facts = _delivery_fixture.DeliveryTests.facts
    start = _delivery_fixture.DeliveryTests.start
    receipt = _delivery_fixture.DeliveryTests.receipt

    tmp: tempfile.TemporaryDirectory
    repo: Path
    state_root: Path
    audit: Path
    compiled_id: str

    @overload
    def run_cli(self, *args: Any, ok: Literal[True] = True) -> dict[str, Any]: ...

    @overload
    def run_cli(self, *args: Any, ok: Literal[False]) -> subprocess.CompletedProcess[str]: ...

    def run_cli(self, *args: Any, ok: bool = True) -> dict[str, Any] | subprocess.CompletedProcess[str]:
        if args and args[0] != "route" and getattr(self, "state_root", None):
            args = (*args, "--state-root", self.state_root)
        result = subprocess.run([sys.executable, "-B", str(self.script), *map(str, args)],
                                cwd=self.repo, text=True, encoding="utf-8", capture_output=True,
                                env=self.env, timeout=60)
        if ok:
            self.assertEqual(0, result.returncode, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(0, result.returncode, result.stdout)
        return result

    def install(self, plain=False):
        if plain:
            shutil.rmtree(self.repo / ".git")
            self.state_root = Path(self.tmp.name) / "delivery-state"
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_") and key not in {"AGENT_SESSION", "AGENT_HOST"}}
        (self.repo / "app.py").write_text("def value(): return 1\n", encoding="utf-8")
        (self.repo / "src/nested").mkdir(parents=True)
        # The bootstrap's --source clones committed HEAD, not this candidate tree.
        # Exercise the real canonical applier directly so staged repairs are installed.
        result = subprocess.run([sys.executable, "-B", str(ROOT / "pack/scripts/pack-apply.py"),
                                 "apply", "--install", "--source", str(ROOT),
                                 "--target", str(self.repo), "--json"], cwd=self.repo, env=self.env,
                                text=True, encoding="utf-8", capture_output=True, timeout=60)
        self.assertEqual(0, result.returncode, result.stderr)
        self.script = self.repo / "docs/ai-forward-pack/scripts/delivery.py"
        self.hook = self.repo / "docs/ai-forward-pack/hooks/session-start.py"
        self.assertEqual(not plain, (self.repo / ".git").exists())

    def hook_start(self, cwd, session="startup", process_cwd=None):
        result = subprocess.run([sys.executable, "-B", str(self.hook), "--host", "grok"],
                                cwd=process_cwd or self.repo, env=self.env,
                                input=json.dumps({"sessionId": session, "workspaceRoot": str(cwd)}),
                                text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        audit_root = cwd / "docs" if (cwd / "docs/audit").is_dir() else cwd / ".agents/log"
        marker = audit_root / "audit/.run-starts.json"
        self.assertIn("__harness__:" + session, json.loads(marker.read_text(encoding="utf-8")))
        return marker

    def reviewed_permission_pause(self):
        self.start(contract_tier="T1", design_ready=True)
        proof = self.write("real-path.json", {"command": "from app import value; assert value() == 1"})
        result = subprocess.run([sys.executable, "-B", "-c", proof.read_text() and
                                 "from app import value; assert value() == 1"],
                                cwd=self.repo, env=self.env, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        pending = self.run_cli("complete", "--task", "demo", "--stage", "implement",
                               "--actor", "author", "--evidence", proof)
        ready = self.run_cli("resume", "--task", "demo", "--receipt",
                             self.receipt(pending, actor="reviewer", source="reviewer-report"))
        self.assertEqual("verify", ready["next"])
        return self.run_cli("pause", "--task", "demo", "--kind", "permission",
                            "--authority", "human", "--question", "Run the scoped verification?")

    def test_descendant_ignore_refresh_does_not_override_explicit_root_declination(self):
        ignored = "docs/audit/.run-starts.json"
        (self.repo / ".gitignore").write_text("# pack-apply: decline " + ignored + "\n!" + ignored + "\n",
                                              encoding="utf-8")
        self.install()
        marker = self.repo / ignored
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("{}", encoding="utf-8")
        result = subprocess.run(["git", "check-ignore", "--quiet", str(marker)],
                                cwd=self.repo, env=self.env, capture_output=True)
        self.assertEqual(1, result.returncode, "descendant patterns must not reverse root opt-outs")

    def test_installer_ignores_only_descendant_duration_marker_names(self):
        self.install()
        expected = []
        durable = []
        for child in ("", "src/nested/"):
            for store in ("docs/audit/", ".agents/log/audit/"):
                folder = self.repo / (child + store)
                folder.mkdir(parents=True, exist_ok=True)
                for suffix in (".run-starts.json", ".run-starts.json.tmp"):
                    path = folder / suffix
                    path.write_text("{}", encoding="utf-8")
                    expected.append(path)
                for name in ("audit-log.jsonl", "durable-record.json", ".run-starts.json.backup"):
                    path = folder / name
                    path.write_text("{}", encoding="utf-8")
                    durable.append(path)
        for path in expected:
            with self.subTest(marker=path.relative_to(self.repo)):
                result = subprocess.run(["git", "check-ignore", "--quiet", str(path)],
                                        cwd=self.repo, env=self.env, capture_output=True)
                self.assertEqual(0, result.returncode, "installed policy misses " + str(path))
        for path in durable:
            with self.subTest(durable=path.relative_to(self.repo)):
                result = subprocess.run(["git", "check-ignore", "--quiet", str(path)],
                                        cwd=self.repo, env=self.env, capture_output=True)
                self.assertEqual(1, result.returncode, "durable child audit files must stay visible")

    def test_preexisting_child_markers_update_without_rebinding_review(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                if plain:
                    self.repo = Path(self.tmp.name) / "plain"
                    self.repo.mkdir()
                    (self.repo / ".git").mkdir()
                self.install(plain)
                child = self.repo / "src/nested"
                marker = self.hook_start(child, "before-task")
                # A tracked marker still has runtime semantics; an ignore rule alone
                # cannot fix Git cached bytes. Use --force only in this disposable test.
                if not plain:
                    subprocess.run(["git", "add", "--force", str(marker)], cwd=self.repo,
                                   env=self.env, check=True, capture_output=True)
                paused = self.reviewed_permission_pause()
                self.hook_start(child, "new-session")
                status = self.run_cli("status", "--task", "demo")
                self.assertEqual(paused["snapshot"], status["snapshot"])
                self.assertEqual(paused["gate"], status["gate"])
                resumed = self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(paused))
                self.assertEqual("verify", resumed["next"])
                # Durable sibling and real application changes remain product drift.
                record = marker.parent / "durable-record.json"
                record.write_text('{"observed":"durable"}', encoding="utf-8")
                self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
                record.unlink()
                (self.repo / "app.py").write_text("def value(): return 0\n", encoding="utf-8")
                self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_child_opted_in_audit_root_keeps_same_task_and_symlinks_protected(self):
        self.install(plain=True)
        child = self.repo / "src/nested"
        (child / "docs/audit").mkdir(parents=True)
        marker = self.hook_start(child, "opted-in")
        self.assertEqual(child / "docs/audit/.run-starts.json", marker)
        paused = self.reviewed_permission_pause()
        self.hook_start(child, "second-opted-in")
        self.assertEqual(paused["snapshot"], self.run_cli("status", "--task", "demo")["snapshot"])
        # A symlink bearing the marker name is not a regular runtime store.
        outside = Path(self.tmp.name) / "outside-marker.json"
        outside.write_text("{}", encoding="utf-8")
        marker.unlink()
        try:
            marker.symlink_to(outside)
        except OSError:
            if os.name == "nt":
                self.skipTest("Host does not permit symlink creation")
            raise
        self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_git_ignored_child_marker_symlink_is_not_runtime_state(self):
        self.install()
        child = self.repo / "src/nested"
        marker = self.hook_start(child, "before-link")
        paused = self.reviewed_permission_pause()
        outside = Path(self.tmp.name) / "outside-marker.json"
        outside.write_text("{}", encoding="utf-8")
        marker.unlink()
        try:
            marker.symlink_to(outside)
        except OSError:
            if os.name == "nt":
                self.skipTest("Host does not permit symlink creation")
            raise
        self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)

    def test_installed_marker_directory_durable_bytes_invalidate_checkpoint(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                if plain:
                    self.repo = Path(self.tmp.name) / "plain"
                    self.repo.mkdir()
                    (self.repo / ".git").mkdir()
                self.install(plain)
                # Persisted host argv does not carry the test runner's -B flag.
                self.env["PYTHONDONTWRITEBYTECODE"] = "1"
                child = self.repo / "src/nested"
                paused = self.reviewed_permission_pause()
                checkpoint = next(Path(paused["local_area"]).rglob("demo.json"))
                before = checkpoint.read_bytes()
                config = json.loads((self.repo / ".grok/hooks/ai-forward.json").read_text(encoding="utf-8"))
                command = config["hooks"]["SessionStart"][0]["hooks"][0]["command"]
                launch = (["pwsh", "-NoProfile", "-Command", command] if os.name == "nt"
                          else ["sh", "-c", command])
                for process_cwd in (self.repo, child):
                    session = "directory-control-" + process_cwd.name
                    result = subprocess.run(launch, cwd=process_cwd, env=self.env,
                                            input=json.dumps({"sessionId": session, "cwd": str(child)}),
                                            capture_output=True, text=True, encoding="utf-8", timeout=30)
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                    marker = child / ".agents/log/audit/.run-starts.json"
                    self.assertIn("__harness__:" + session, json.loads(marker.read_text(encoding="utf-8")))
                    self.assertEqual(paused["snapshot"], self.run_cli("status", "--task", "demo")["snapshot"])
                original = marker.read_bytes()
                marker.unlink()
                marker.mkdir()
                durable = marker / "durable.json"
                durable.write_text('{"durable":"original"}', encoding="utf-8")
                if not plain:
                    ignored = subprocess.run(["git", "check-ignore", "--quiet", str(durable)],
                                             cwd=self.repo, env=self.env, capture_output=True)
                    self.assertEqual(0, ignored.returncode, "exercise actual installed marker ignore")
                self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
                durable.write_text('{"durable":"changed product bytes"}', encoding="utf-8")
                self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
                self.assertEqual(before, checkpoint.read_bytes())
                durable.unlink()
                marker.rmdir()
                marker.write_bytes(original)
                restored = self.run_cli("status", "--task", "demo")
                self.assertEqual(paused["snapshot"], restored["snapshot"])
                self.assertEqual(paused["gate"], restored["gate"])
                self.assertEqual(before, checkpoint.read_bytes())
                resumed = self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(paused))
                self.assertEqual("verify", resumed["next"])

    @unittest.skipUnless(os.name == "posix", "FIFO and Unix socket fixtures require POSIX")
    def test_installed_git_nonregular_marker_candidates_invalidate_checkpoint(self):
        for shape in ("fifo", "socket", "negated-empty-directory"):
            with self.subTest(shape=shape):
                if shape != "fifo":
                    self.repo = Path(self.tmp.name) / shape
                    self.repo.mkdir()
                    subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
                if shape == "negated-empty-directory":
                    ignored = "docs/audit/.run-starts.json"
                    (self.repo / ".gitignore").write_text(
                        "# pack-apply: decline " + ignored + "\n!" + ignored + "\n", encoding="utf-8")
                self.install()
                self.env["PYTHONDONTWRITEBYTECODE"] = "1"
                child = self.repo if shape == "negated-empty-directory" else self.repo / "src/nested"
                if shape == "negated-empty-directory":
                    (child / "docs/audit").mkdir(parents=True)
                config = json.loads((self.repo / ".grok/hooks/ai-forward.json").read_text(encoding="utf-8"))
                command = config["hooks"]["SessionStart"][0]["hooks"][0]["command"]
                result = subprocess.run(["sh", "-c", command], cwd=self.repo, env=self.env,
                    input=json.dumps({"sessionId": "before-" + shape, "cwd": str(child)}),
                    capture_output=True, text=True, encoding="utf-8", timeout=30)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                store = "docs/audit" if shape == "negated-empty-directory" else ".agents/log/audit"
                marker = child / store / ".run-starts.json"
                self.assertIn("__harness__:before-" + shape, json.loads(marker.read_text(encoding="utf-8")))
                original = marker.read_bytes()
                paused = self.reviewed_permission_pause()
                checkpoint = next(Path(paused["local_area"]).rglob("demo.json"))
                before = checkpoint.read_bytes()
                marker.unlink()
                if shape == "fifo":
                    os.mkfifo(marker)
                elif shape == "socket":
                    # Bind a relative path to avoid Unix socket pathname-length limits.
                    subprocess.run([sys.executable, "-B", "-c",
                        "import socket,sys; s=socket.socket(socket.AF_UNIX); s.bind(sys.argv[1]); s.close()",
                        marker.name], cwd=marker.parent, env=self.env, check=True, timeout=30)
                else:
                    marker.mkdir()
                    ignored_result = subprocess.run(["git", "check-ignore", "--quiet", str(marker)],
                        cwd=self.repo, env=self.env, capture_output=True)
                    self.assertEqual(1, ignored_result.returncode, "retain declared root negation")
                for script in (self.script, ROOT / "pack/scripts/delivery.py"):
                    with self.subTest(helper=str(script)):
                        result = subprocess.run([sys.executable, "-B", str(script), "status",
                            "--repo", str(self.repo), "--task", "demo"], cwd=self.repo, env=self.env,
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
                        self.assertNotEqual(0, result.returncode, result.stdout)
                        self.assertIn("input drift:", result.stderr)
                self.assertEqual(before, checkpoint.read_bytes())
                if shape == "negated-empty-directory":
                    marker.rmdir()
                else:
                    marker.unlink()
                marker.write_bytes(original)
                restored = self.run_cli("status", "--task", "demo")
                self.assertEqual(paused["snapshot"], restored["snapshot"])
                self.assertEqual(paused["gate"], restored["gate"])
                self.assertEqual(before, checkpoint.read_bytes())
                resumed = self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(paused))
                self.assertEqual("verify", resumed["next"])

    def test_installed_empty_marker_directories_invalidate_checkpoint(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                if plain:
                    self.repo = Path(self.tmp.name) / "plain"
                    self.repo.mkdir()
                    (self.repo / ".git").mkdir()
                self.install(plain)
                paused = self.reviewed_permission_pause()
                checkpoint = next(Path(paused["local_area"]).rglob("demo.json"))
                before = checkpoint.read_bytes()
                for prefix in ("", "src/nested/"):
                    for store in ("docs/audit/", ".agents/log/audit/"):
                        for suffix in (".run-starts.json", ".run-starts.json.tmp"):
                            with self.subTest(marker=prefix + store + suffix):
                                marker = self.repo / (prefix + store + suffix)
                                marker.parent.mkdir(parents=True, exist_ok=True)
                                for preexisting in (False, True):
                                    if preexisting:
                                        marker.write_text("{}", encoding="utf-8")
                                        self.run_cli("status", "--task", "demo")
                                        marker.unlink()
                                    marker.mkdir()
                                    if not plain:
                                        ignored = subprocess.run(["git", "check-ignore", "--quiet", str(marker)],
                                                                 cwd=self.repo, env=self.env, capture_output=True)
                                        self.assertEqual(0, ignored.returncode)
                                    self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
                                    self.assertEqual(before, checkpoint.read_bytes())
                                    marker.rmdir()
                                    self.assertEqual(paused["snapshot"], self.run_cli("status", "--task", "demo")["snapshot"])
                self.assertEqual(before, checkpoint.read_bytes())

    def test_installed_directory_checkpoint_binds_durable_children_not_other_ignored_logs(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                if plain:
                    self.repo = Path(self.tmp.name) / "plain"
                    self.repo.mkdir()
                    (self.repo / ".git").mkdir()
                self.install(plain)
                marker = self.repo / "src/nested/.agents/log/audit/.run-starts.json"
                marker.mkdir(parents=True)
                durable = marker / "durable.json"
                durable.write_text('{"durable":"reviewed"}', encoding="utf-8")
                unrelated = marker.parent.parent / "ordinary-ignored"
                if not plain:
                    with (self.repo / ".gitignore").open("a", encoding="utf-8") as ignore:
                        ignore.write("\nsrc/nested/.agents/log/ordinary-ignored/\n")
                    unrelated.mkdir()
                    (unrelated / "durable.json").write_text("ignored before task", encoding="utf-8")
                paused = self.reviewed_permission_pause()
                checkpoint = next(Path(paused["local_area"]).rglob("demo.json"))
                before = checkpoint.read_bytes()
                if not plain:
                    (unrelated / "durable.json").write_text("still ordinary ignored state", encoding="utf-8")
                    self.assertEqual(paused["snapshot"], self.run_cli("status", "--task", "demo")["snapshot"])
                durable.write_text('{"durable":"changed"}', encoding="utf-8")
                self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
                self.assertEqual(before, checkpoint.read_bytes())
                durable.write_text('{"durable":"reviewed"}', encoding="utf-8")
                self.assertEqual(paused["snapshot"], self.run_cli("status", "--task", "demo")["snapshot"])
                # A duration-looking leaf inside a marker-shaped directory is
                # durable too: its ancestor did not receive a regular-file exemption.
                nested = marker / "docs/audit/.run-starts.json"
                nested.parent.mkdir(parents=True)
                nested.write_text("durable, despite the suffix", encoding="utf-8")
                self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
                nested.unlink()
                shutil.rmtree(marker / "docs")
                for name in ("audit-log.jsonl", ".run-starts.json.backup"):
                    sibling = marker.parent / name
                    sibling.write_text("durable sibling", encoding="utf-8")
                    self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
                    sibling.unlink()
                self.assertEqual(before, checkpoint.read_bytes())

    def test_installed_marker_directory_symlinks_remain_checked(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                if plain:
                    self.repo = Path(self.tmp.name) / "plain"
                    self.repo.mkdir()
                    (self.repo / ".git").mkdir()
                self.install(plain)
                marker = self.hook_start(self.repo / "src/nested", "before-directory-link")
                paused = self.reviewed_permission_pause()
                checkpoint = next(Path(paused["local_area"]).rglob("demo.json"))
                before = checkpoint.read_bytes()
                original = marker.read_bytes()
                outside = Path(self.tmp.name) / ("outside-directory-" + str(plain))
                outside.mkdir()
                (outside / "durable.json").write_text("not a duration store", encoding="utf-8")
                marker.unlink()
                try:
                    marker.symlink_to(outside, target_is_directory=True)
                except OSError:
                    if os.name == "nt":
                        self.skipTest("Host does not permit symlink creation")
                    raise
                self.assertIn("input drift:", self.run_cli("status", "--task", "demo", ok=False).stderr)
                self.assertEqual(before, checkpoint.read_bytes())
                marker.unlink()
                marker.write_bytes(original)
                self.assertEqual(paused["snapshot"], self.run_cli("status", "--task", "demo")["snapshot"])
                self.assertEqual(before, checkpoint.read_bytes())

    def test_installed_tracked_temporary_markers_consumed_by_startup_reuse_checkpoint(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                if plain:
                    self.repo = Path(self.tmp.name) / "plain"
                    self.repo.mkdir()
                    (self.repo / ".git").mkdir()
                self.install(plain)
                self.env["PYTHONDONTWRITEBYTECODE"] = "1"
                temporaries = []
                for cwd in (self.repo, self.repo / "src/nested"):
                    # Opt in independently at root and child to cover both stores.
                    (cwd / "docs/audit").mkdir(parents=True, exist_ok=True)
                    for store in ("docs/audit", ".agents/log/audit"):
                        marker = cwd / store / ".run-starts.json.tmp"
                        marker.parent.mkdir(parents=True, exist_ok=True)
                        marker.write_text("{}", encoding="utf-8")
                        temporaries.append(marker)
                if not plain:
                    subprocess.run(["git", "add", "--force", *map(str, temporaries)],
                                   cwd=self.repo, env=self.env, check=True, capture_output=True)
                paused = self.reviewed_permission_pause()
                checkpoint = next(Path(paused["local_area"]).rglob("demo.json"))
                before = checkpoint.read_bytes()
                config = json.loads((self.repo / ".grok/hooks/ai-forward.json").read_text(encoding="utf-8"))
                command = config["hooks"]["SessionStart"][0]["hooks"][0]["command"]
                launch = (["pwsh", "-NoProfile", "-Command", command] if os.name == "nt"
                          else ["sh", "-c", command])
                for cwd in (self.repo, self.repo / "src/nested"):
                    for opted_in in (True, False):
                        if not opted_in:
                            shutil.rmtree(cwd / "docs/audit")
                        result = subprocess.run(launch, cwd=self.repo, env=self.env,
                                                input=json.dumps({"sessionId": "tracked-tmp-" + cwd.name,
                                                                  "cwd": str(cwd)}), capture_output=True,
                                                text=True, encoding="utf-8", timeout=30)
                        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                        store = "docs/audit" if opted_in else ".agents/log/audit"
                        self.assertFalse((cwd / store / ".run-starts.json.tmp").exists(), "hook must consume tracked tmp")
                        self.assertTrue((cwd / store / ".run-starts.json").is_file())
                        with self.subTest(cwd=cwd.relative_to(self.repo), opted_in=opted_in):
                            status = self.run_cli("status", "--task", "demo")
                            self.assertEqual(paused["snapshot"], status["snapshot"])
                            self.assertEqual(paused["gate"], status["gate"])
                            self.assertEqual(before, checkpoint.read_bytes())
                resumed = self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(paused))
                self.assertEqual("verify", resumed["next"])

    def test_explicit_child_marker_inputs_still_refuse_drift(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                if plain:
                    self.repo = Path(self.tmp.name) / "plain"
                    self.repo.mkdir()
                    (self.repo / ".git").mkdir()
                self.install(plain)
                child = self.repo / "src/nested"
                marker = self.hook_start(child, "before-input")
                self.start(contract_tier="T1", design_ready=True)
                self.run_cli("start", "--task", "explicit", "--facts", self.facts(design_ready=True),
                             "--audit-root", self.audit, "--compiled-id", self.compiled_id, "--input", marker)
                self.hook_start(child, "after-input")
                self.assertIn("input drift:", self.run_cli("status", "--task", "explicit", ok=False).stderr)

    def test_exact_persisted_startup_commands_reach_hook_from_root_and_child(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                if plain:
                    self.repo = Path(self.tmp.name) / "plain"
                    self.repo.mkdir()
                    (self.repo / ".git").mkdir()
                self.install(plain)
                commands = []
                for host, path, event in (
                    ("claude", ".claude/settings.json", "SessionStart"),
                    ("grok", ".grok/hooks/ai-forward.json", "SessionStart"),
                ):
                    config = json.loads((self.repo / path).read_text(encoding="utf-8"))
                    commands.append((host, config["hooks"][event][0]["hooks"][0]["command"]))
                copilot = json.loads((self.repo / ".github/hooks/ai-forward.json").read_text(encoding="utf-8"))
                arm = "powershell" if os.name == "nt" else "bash"
                commands.append(("copilot", copilot["hooks"]["sessionStart"][0][arm]))
                agy = json.loads((self.repo / ".agents/hooks.json").read_text(encoding="utf-8"))
                commands.append(("agy", agy["session-start"]["PreInvocation"][0]["command"]))
                for process_cwd in (self.repo, self.repo / "src/nested"):
                    for host, command in commands:
                        # AGY's measured native Windows contract is Git root/.agents;
                        # its single command field cannot share sh/PowerShell quoting.
                        # R5's demonstrated plain child is Grok, not an AGY profile.
                        if host == "agy" and process_cwd != self.repo:
                            continue
                        with self.subTest(host=host, process_cwd=process_cwd):
                            session = host + "-" + process_cwd.name
                            if host == "agy":
                                payload = {"conversationId": session, "workspacePaths": [str(process_cwd)],
                                           "invocationNum": 1}
                            elif host in {"grok", "copilot"}:
                                payload = {"hookEventName": "sessionStart", "sessionId": session,
                                           "cwd": str(process_cwd), "workspaceRoot": str(process_cwd)}
                            else:
                                payload = {"hook_event_name": "SessionStart", "session_id": session,
                                           "cwd": str(process_cwd)}
                            env = dict(self.env, CLAUDE_PROJECT_DIR=str(self.repo),
                                       GROK_WORKSPACE_ROOT=str(self.repo))
                            if os.name == "nt":
                                launch = (["pwsh", "-NoProfile", "-Command", command] if host != "agy"
                                          else "cmd /d /c " + command)
                            else:
                                launch = ["sh", "-c", command]
                            result = subprocess.run(launch, cwd=process_cwd, env=env,
                                                    input=json.dumps(payload), text=True, encoding="utf-8",
                                                    capture_output=True, timeout=30)
                            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                            marker = process_cwd / ".agents/log/audit/.run-starts.json"
                            self.assertTrue(marker.is_file(), "process argv did not reach installed hook")
                            self.assertIn("__harness__:" + session,
                                          json.loads(marker.read_text(encoding="utf-8")))
                self.assertEqual(not plain, (self.repo / ".git").exists())

    def test_startup_command_remains_relocatable_and_refuses_unrelated_git_child(self):
        self.install(plain=True)
        config = json.loads((self.repo / ".grok/hooks/ai-forward.json").read_text(encoding="utf-8"))
        command = config["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        relocated = self.repo.with_name("relocated project ' ` ;")
        self.repo.rename(relocated)
        self.repo = relocated
        child = self.repo / "src/nested"
        for native in ("sh", "pwsh"):
            if not shutil.which(native):
                continue
            with self.subTest(native=native):
                launch = [native, "-c", command] if native == "sh" else [native, "-NoProfile", "-Command", command]
                result = subprocess.run(launch, cwd=child, env=self.env,
                    input=json.dumps({"sessionId": native, "cwd": str(child)}), capture_output=True,
                    text=True, encoding="utf-8", timeout=30)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                marker = child / ".agents/log/audit/.run-starts.json"
                self.assertIn("__harness__:" + native, json.loads(marker.read_text(encoding="utf-8")))
        # The nearest Git boundary is not authority to execute an ancestor pack.
        nested = self.repo / "unrelated/nested"
        nested.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(nested.parent)], check=True, env=self.env)
        result = subprocess.run(["sh", "-c", command], cwd=nested, env=self.env,
            input=json.dumps({"sessionId": "outside", "cwd": str(nested)}), capture_output=True,
            text=True, encoding="utf-8", timeout=30)
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertFalse((nested / ".agents/log/audit/.run-starts.json").exists())

    def test_refresh_preserves_custom_copilot_bundle_and_migrates_known_startup(self):
        self.install()
        target = self.repo / ".github/hooks/ai-forward.json"
        current = json.loads(target.read_text(encoding="utf-8"))
        old = ("git -c alias.aif-hook=!sh aif-hook docs/ai-forward-pack/hooks/run-hook.sh "
               "session-start.py --host copilot")
        handler = current["hooks"]["sessionStart"][0]
        handler.update(bash=old, powershell=old, timeoutSec=27)
        current["custom"] = {"unchanged": True}
        current["hooks"]["sessionStart"].append({"type": "command", "bash": "my-wrapper " + old,
                                                "powershell": "my-wrapper " + old})
        target.write_text(json.dumps(current), encoding="utf-8")
        args = [sys.executable, "-B", str(ROOT / "pack/scripts/pack-apply.py"), "apply", "--install",
                "--source", str(ROOT), "--target", str(self.repo), "--json"]
        result = subprocess.run(args, cwd=self.repo, env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        observed = json.loads(target.read_text(encoding="utf-8"))
        source = json.loads((ROOT / "pack/adapters/hooks/copilot.ai-forward-hooks.json").read_text())
        expected = source["hooks"]["sessionStart"][0]
        self.assertEqual(expected["bash"], observed["hooks"]["sessionStart"][0]["bash"])
        self.assertEqual(expected["powershell"], observed["hooks"]["sessionStart"][0]["powershell"])
        self.assertEqual(27, observed["hooks"]["sessionStart"][0]["timeoutSec"])
        self.assertEqual(current["custom"], observed["custom"])
        self.assertEqual(current["hooks"]["sessionStart"][1], observed["hooks"]["sessionStart"][1])
        before = target.read_bytes()
        result = subprocess.run(args, cwd=self.repo, env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, target.read_bytes())

    def test_refresh_migrates_only_exact_startup_commands(self):
        import runpy
        merges = runpy.run_path(str(ROOT / "pack/scripts/pack-apply.py"))
        source = json.loads((ROOT / "pack/adapters/hooks/claude-code.settings.hooks.json").read_text())
        new = source["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        old = ("git -c alias.aif-hook=!sh aif-hook docs/ai-forward-pack/hooks/run-hook.sh "
               "session-start.py --host claude")
        wrapped = "my-wrapper " + old
        config = {"permissions": {"allow": ["Read"]}, "env": {"custom": "unchanged"},
                  "hooks": {"SessionStart": [{"matcher": "custom", "hooks": [
                      {"type": "command", "command": old, "timeout": 29},
                      {"type": "command", "command": wrapped},
                      {"type": "command", "command": old, "args": ["--custom"]}]}]}}
        merged = json.loads(merges["merge_claude_settings"](json.dumps(source), json.dumps(config)))
        handlers = merged["hooks"]["SessionStart"][0]["hooks"]
        self.assertEqual(new, handlers[0]["command"])
        self.assertEqual(29, handlers[0]["timeout"])
        self.assertEqual(wrapped, handlers[1]["command"])
        self.assertEqual(old, handlers[2]["command"])
        self.assertEqual(config["permissions"], merged["permissions"])
        self.assertEqual(config["env"], merged["env"])
        self.assertEqual("custom", merged["hooks"]["SessionStart"][0]["matcher"])
        self.assertEqual(merged, json.loads(merges["merge_claude_settings"](json.dumps(source), json.dumps(merged))))
        self.assertNotIn("PreToolUse", config["hooks"], "fixture never opts into ownership")
        self.assertFalse(any("coord-core.py" in h["command"] for entry in merged["hooks"]["PreToolUse"]
                             for h in entry["hooks"]), "refresh must not opt into ownership")

    def test_root_process_child_payload_preserves_reviewed_same_task(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                # Each project gets its own real installed helper and task store.
                if plain:
                    self.repo = Path(self.tmp.name) / "plain"
                    self.repo.mkdir()
                    (self.repo / ".git").mkdir()
                self.install(plain)
                paused = self.reviewed_permission_pause()
                for cwd in (self.repo, self.repo / "src/nested"):
                    self.hook_start(cwd, "continuation")
                    status = self.run_cli("status", "--task", "demo")
                    self.assertEqual(paused["snapshot"], status["snapshot"])
                    self.assertEqual(paused["gate"], status["gate"])
                    self.assertEqual(paused["completed"], status["completed"])
                resumed = self.run_cli("resume", "--task", "demo", "--receipt", self.receipt(paused))
                self.assertEqual("verify", resumed["next"])
                self.assertEqual(paused["completed"], resumed["completed"])
                self.assertEqual(paused["snapshot"], resumed["snapshot"])
                self.assertEqual(str(self.repo.resolve()), resumed["identity"]["root"])


if __name__ == "__main__":
    unittest.main()
