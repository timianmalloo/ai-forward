"""Q18 — the harness-adapter conformance suite.

Design: docs/design/coord-federation-phase3.md (Q15, Q16, Q18; H13, H14, B9).

The architecture's condition 2 has been open since /define-architecture: F1 stays open for
any harness until its hook surface is established BY EXECUTION. Spike S14 closed half of it
for Copilot -- it does invoke PreToolUse, 55,541 times in the recorded corpus -- and this
suite is the other half: does our adapter actually SPEAK each harness's envelope?

It caught the thing it was written to catch, before any of it shipped. The two envelopes
are not similar:

  Claude   {"tool_name": "Edit", "tool_input": {"file_path": "src/a.cs"}}
  Copilot  {"hookType": "preToolUse",
            "input": {"cwd": "C:\\repo",
                      "toolCalls": [{"name": "edit",
                                     "args": "{\\"path\\": \\"C:\\\\repo\\\\src\\\\a.cs\\"}"}]}}

Copilot batches N tool calls into ONE invocation, `args` is a JSON STRING rather than an
object, the path field is `path` not `file_path`, and the path is ABSOLUTE. A hook that
reads `tool_input.file_path` finds nothing in a Copilot payload and returns "allow" for
every edit -- a silent no-op wearing the shape of enforcement.

WHAT THIS SUITE STILL CANNOT ASSERT: that Copilot HONOURS a deny. `hook.end` records only
{hookInvocationId, hookType, success} -- never the hook's response -- so the recorded corpus
proves invocation and cannot prove obedience. That is H13, and closing it needs a live
session, which `copilot --plugin-dir` makes possible without touching the user's config.
The suite is written so closing it is RUNNING one test, not writing one.
"""
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = REPO / "pack" / "scripts" / "coord-core.py"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "harness"


def load_module():
    spec = importlib.util.spec_from_file_location("coord_core", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class HarnessCase(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name) / "r"
        (self.repo / ".agents" / "log").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=str(self.repo), check=True)
        self.root = self.repo / ".agents"

    def claim(self, session, path, wi="WI-142"):
        import time
        self.m.append_event(self.root, self.m.make_event(
            kind="claim", session=session, agent=session, wi=wi, path=path,
            ttl=300, at=time.time()))


# --------------------------------------------------------------- parsing

class EnvelopeParsingTests(HarnessCase):
    """The half the recorded corpus CAN establish: do we speak each envelope?"""

    def test_Q18_claude_envelope_yields_the_edited_path(self):
        calls = self.m.parse_hook_request(fixture("claude-pretooluse.json"), self.repo)
        self.assertEqual(calls, [("Edit", "src/Ingest/Reader.cs")])

    def test_Q18_copilot_envelope_yields_the_edited_path(self):
        """The finding this suite exists for. A hook reading tool_input.file_path gets
        NOTHING from this payload and allows the edit."""
        calls = self.m.parse_hook_request(fixture("copilot-pretooluse.json"), self.repo)
        self.assertEqual(len(calls), 1, "the Copilot envelope was not parsed at all")
        tool, path = calls[0]
        self.assertEqual(tool, "edit")
        self.assertEqual(path, "src/Ingest/Reader.cs",
                         "an absolute Copilot path was not made repo-relative")

    def test_Q18_copilot_batches_are_all_parsed(self):
        """Copilot sends N tool calls per invocation; Claude sends one. A parser that
        reads only the first silently ignores the rest of the batch."""
        calls = self.m.parse_hook_request(fixture("copilot-pretooluse-batch.json"), self.repo)
        self.assertEqual(len(calls), 2, "only part of the batch was parsed")
        self.assertEqual([c[1] for c in calls], ["README.md", "src/Ingest/Reader.cs"])

    def test_Q18_non_file_tools_yield_no_path(self):
        """26,210 of the recorded invocations are `powershell` -- the single commonest tool
        call, and the shell-bypass path named as G4. It carries no path and must not be
        invented one."""
        calls = self.m.parse_hook_request(fixture("copilot-pretooluse-shell.json"), self.repo)
        self.assertEqual([c[1] for c in calls], [None])

    def test_args_that_are_not_json_do_not_raise(self):
        payload = fixture("copilot-pretooluse.json")
        payload["input"]["toolCalls"][0]["args"] = "not json at all"
        calls = self.m.parse_hook_request(payload, self.repo)
        self.assertEqual([c[1] for c in calls], [None])


# ------------------------------------------------------- the conformance suite

class ConformanceTests(HarnessCase):
    """Every adapter must pass all of this. Adding a harness = adding a fixture."""

    HARNESSES = ("claude", "copilot")

    def payload(self, harness):
        return fixture("{}-pretooluse.json".format(
            {"claude": "claude", "copilot": "copilot"}[harness]))

    def run_hook(self, payload, session):
        env = dict(os.environ)
        env["AGENT_SESSION"] = session
        env["AGENT_NAME"] = session
        env.pop("COORD_ROOT", None)
        return subprocess.run([sys.executable, str(SCRIPT), "hook"], cwd=str(self.repo),
                              env=env, input=json.dumps(payload), capture_output=True,
                              text=True, timeout=30)

    def decision(self, result, harness):
        self.assertEqual(result.returncode, 0,
                         "{}: the hook must always exit 0".format(harness))
        return self.m.hook_decision_of(json.loads(result.stdout))

    def test_Q18_conformance_denies_a_leased_path(self):
        self.claim("opus", "src/Ingest/**")
        for harness in self.HARNESSES:
            with self.subTest(harness=harness):
                got = self.decision(self.run_hook(self.payload(harness), "copilot"), harness)
                self.assertEqual(got, "deny",
                                 "{}: an edit to another session's lease was allowed"
                                 .format(harness))

    def test_Q18_conformance_allows_the_lease_holder(self):
        self.claim("opus", "src/Ingest/**")
        for harness in self.HARNESSES:
            with self.subTest(harness=harness):
                got = self.decision(self.run_hook(self.payload(harness), "opus"), harness)
                self.assertEqual(got, "allow")

    def test_Q18_conformance_fails_safe_on_a_malformed_payload(self):
        for harness in self.HARNESSES:
            with self.subTest(harness=harness):
                result = self.run_hook({"garbage": True}, "s1")
                self.assertEqual(result.returncode, 0)
                self.assertIn(self.m.hook_decision_of(json.loads(result.stdout)),
                              ("ask", "allow"))

    def test_Q18_conformance_response_is_shaped_for_the_harness(self):
        """A decision the harness cannot read is not a decision. Each adapter renders into
        ITS OWN envelope, and the suite asserts the shape rather than assuming one."""
        self.claim("opus", "src/Ingest/**")
        for harness in self.HARNESSES:
            with self.subTest(harness=harness):
                out = json.loads(self.run_hook(self.payload(harness), "copilot").stdout)
                self.assertTrue(self.m.hook_response_is_valid(out, harness),
                                "{}: response does not match the harness envelope: {}"
                                .format(harness, json.dumps(out)[:200]))

    def test_Q18_conformance_batch_denies_when_any_member_is_refused(self):
        """Copilot batches. If any call in the batch touches another session's lease the
        whole batch is refused -- a false refusal costs a message, a false grant costs a
        merge."""
        self.claim("opus", "src/Ingest/**")
        got = self.decision(
            self.run_hook(fixture("copilot-pretooluse-batch.json"), "copilot"), "copilot")
        self.assertEqual(got, "deny")

    def test_Q18_conformance_reading_a_leased_artifact_is_allowed(self):
        """Reads are parallel; writes serialize. Refusing a `view` of a leased file would be
        both wrong and the fastest way to get the hook switched off. The parser normalises
        the envelope; this policy lives in the hook."""
        self.claim("opus", "README.md")
        payload = fixture("copilot-pretooluse-batch.json")
        payload["input"]["toolCalls"] = [payload["input"]["toolCalls"][0]]   # the `view`
        got = self.decision(self.run_hook(payload, "copilot"), "copilot")
        self.assertEqual(got, "allow", "a read of a leased artifact was refused")

    def test_Q18_conformance_non_file_tool_is_allowed(self):
        self.claim("opus", "src/Ingest/**")
        got = self.decision(
            self.run_hook(fixture("copilot-pretooluse-shell.json"), "copilot"), "copilot")
        self.assertEqual(got, "allow")


# ------------------------------------------------- Q15/Q16: the plugin bundle

class PluginEmitTests(HarnessCase):
    def run_cli(self, *args):
        env = dict(os.environ)
        env["AGENT_SESSION"] = "s1"; env["AGENT_NAME"] = "s1"
        env.pop("COORD_ROOT", None)
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(self.repo),
                              env=env, capture_output=True, text=True, timeout=30)

    def test_Q15_emitted_plugin_matches_the_recorded_harness_fixture(self):
        """H14 / S14. Copilot consumes the CLAUDE plugin format -- .claude-plugin/plugin.json
        plus hooks/hooks.json with the same matcher/hooks shape -- so ONE bundle serves both.
        That is the finding that made NFR-C1 cheap, and this pins it."""
        out = self.repo / "bundle"
        result = self.run_cli("plugin", "--emit", str(out))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        manifest = json.loads((out / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertIn("name", manifest)
        self.assertIn("version", manifest)

        hooks = json.loads((out / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        entry = hooks["hooks"]["PreToolUse"][0]
        self.assertIn("matcher", entry)
        self.assertEqual(entry["hooks"][0]["type"], "command")
        self.assertIn("command", entry["hooks"][0])

    def test_Q15b_the_command_names_a_bare_interpreter_and_a_bundled_script(self):
        """Proven RED by a live Copilot run, not by reading a schema.

        The first bundle emitted `"C:\\...\\python.exe" "C:/...coord-core.py" hook` -- a
        QUOTED EXECUTABLE. Copilot denied every tool call with "(hook errored)" and the hook
        script never executed at all. The one plugin known to work on this machine quotes its
        script and never its interpreter. So: bare interpreter, quoted ${CLAUDE_PLUGIN_ROOT}
        script, script shipped inside the bundle.
        """
        out = self.repo / "bundle"
        self.assertEqual(self.run_cli("plugin", "--emit", str(out)).returncode, 0)
        command = json.loads((out / "hooks" / "hooks.json").read_text(encoding="utf-8")
                             )["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertFalse(command.startswith('"'),
                         "the executable is quoted; Copilot cannot execute that: " + command)
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", command,
                      "the bundle is pinned to an absolute path instead of relocatable")
        self.assertTrue((out / "hooks" / "hook.py").is_file(),
                        "the command names a bundled script that was not shipped")

    def test_Q15c_the_bundled_launcher_actually_runs_and_answers(self):
        """The launcher is what the harness executes. Run it the way the harness does."""
        import time
        out = self.repo / "bundle"
        self.assertEqual(self.run_cli("plugin", "--emit", str(out)).returncode, 0)
        self.m.append_event(self.root, self.m.make_event(
            kind="claim", session="opus", agent="opus", wi="WI-1",
            path="src/Ingest/**", ttl=300, at=time.time()))

        env = dict(os.environ)
        env["AGENT_SESSION"] = "copilot"; env["AGENT_NAME"] = "copilot"
        env.pop("COORD_ROOT", None)
        result = subprocess.run([sys.executable, str(out / "hooks" / "hook.py")],
                                cwd=str(self.repo), env=env,
                                input=json.dumps(fixture("claude-pretooluse.json")),
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.m.hook_decision_of(json.loads(result.stdout)), "deny",
                         "the bundled launcher did not reach the real decision")

    def test_Q16_emit_does_not_install_or_edit_harness_config(self):
        """A1 / STRIDE B9. A layer that grants itself tool permissions is the elevation it
        exists to prevent. Same rule as `install`, which prints the settings entry rather
        than writing it (Phase 2, P19)."""
        home = pathlib.Path(self.tmp.name) / "home"
        (home / ".copilot").mkdir(parents=True)
        settings = home / ".copilot" / "settings.json"
        settings.write_text('{"enabledPlugins":{}}', encoding="utf-8")
        claude_settings = self.repo / ".claude" / "settings.json"
        claude_settings.parent.mkdir(parents=True, exist_ok=True)
        claude_settings.write_text('{"hooks":{}}', encoding="utf-8")
        before = (settings.read_text(encoding="utf-8"),
                  claude_settings.read_text(encoding="utf-8"))

        out = self.repo / "bundle"
        result = self.run_cli("plugin", "--emit", str(out))
        self.assertEqual(result.returncode, 0)

        self.assertEqual(before, (settings.read_text(encoding="utf-8"),
                                  claude_settings.read_text(encoding="utf-8")),
                         "emit modified a harness config file")
        self.assertIn(str(out), result.stdout, "emit must name what it wrote")
        self.assertNotIn("installed", result.stdout.lower())

    def test_emit_refuses_to_overwrite_a_foreign_directory(self):
        out = self.repo / "bundle"
        (out / ".claude-plugin").mkdir(parents=True)
        (out / ".claude-plugin" / "plugin.json").write_text(
            '{"name":"somebody-elses-plugin"}', encoding="utf-8")
        result = self.run_cli("plugin", "--emit", str(out))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("somebody-elses-plugin",
                      (out / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))


class OpenConditionTests(unittest.TestCase):
    def test_H13_status_is_backed_by_an_executed_session_not_an_assumption(self):
        """The architecture's condition 2, now CLOSED by a live run (2026-08-24).

        Copilot CLI 1.0.80 honoured a deny: a read of an unleased file succeeded, a write to
        a leased one was refused with our four-line reason rendered verbatim into its
        transcript, and the file was unmodified.

        The rule this test really guards is that a harness is only marked `enforcing` when a
        session was actually run -- every status must carry the evidence that earned it, so
        nobody can promote a harness by editing a dict.
        """
        module = load_module()
        for name, status in module.HARNESS_STATUS.items():
            self.assertIn(status["edit_boundary"], ("enforcing", "advisory"), name)
            if status["edit_boundary"] == "enforcing":
                self.assertRegex(
                    status["why"].lower(), r"live|execut|spike|session",
                    "{}: marked enforcing with no executed evidence cited".format(name))
        self.assertEqual(module.HARNESS_STATUS["claude"]["edit_boundary"], "enforcing")
        self.assertEqual(module.HARNESS_STATUS["copilot"]["edit_boundary"], "enforcing")
        self.assertIn("fails open", module.HARNESS_STATUS["copilot"]["why"].lower(),
                      "the timeout residual must stay stated, not disappear with the fix")


if __name__ == "__main__":
    unittest.main()
