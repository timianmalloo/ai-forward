"""Cross-platform P2/P3 controls (class PLAT-A; docs/plans/cross-platform-readiness.md).

Observed RED before the sweeps they pin (2026-09-19, this worktree): the subprocess-encoding
gate found 21 text-mode calls decoding with the locale codec; the portable-text-I/O gate found
30 sites - text writes with the platform newline, printing CLIs with no console guard, and
`mkstemp(text=True)`. pack-doctor passed a repo whose .gitattributes declared the coord merge
drivers with no `eol=lf` rule. pack-apply deployed no .gitattributes or .editorconfig at all.
"""
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"
UTF8 = SCRIPTS / "verify-subprocess-utf8.py"
TEXTIO = SCRIPTS / "verify-portable-text-io.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def run(script, *args, cwd=REPO):
    return subprocess.run([sys.executable, str(script), *args], cwd=str(cwd), capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=120)


class SubprocessUtf8GateTests(unittest.TestCase):
    def test_self_test_proves_it_can_fail(self):
        proc = run(UTF8, "--self-test")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_the_pack_states_every_encoding(self):
        proc = run(UTF8)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_a_locale_decoded_call_is_a_finding(self):
        m = load(UTF8, "verify_subprocess_utf8")
        src = 'import subprocess\nsubprocess.run(["git"], capture_output=True, text=True)\n'
        self.assertEqual([f[0] for f in m.scan_source(src, "x.py")], [2])
        ok = 'import subprocess\nsubprocess.run(["git"], capture_output=True, text=True, encoding="utf-8")\n'
        self.assertEqual(m.scan_source(ok, "x.py"), [])


class PortableTextIoGateTests(unittest.TestCase):
    def test_self_test_proves_it_can_fail(self):
        proc = run(TEXTIO, "--self-test")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_the_pack_writes_lf_and_guards_its_consoles(self):
        proc = run(TEXTIO)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_shapes(self):
        m = load(TEXTIO, "verify_portable_text_io")
        self.assertEqual([f[0] for f in m.scan_source('open("a", "w", encoding="utf-8")\n')], [1])
        self.assertEqual(m.scan_source('open("a", "w", encoding="utf-8", newline="\\n")\n'), [])
        self.assertEqual(m.scan_source('open("a", "wb")\n'), [])
        self.assertEqual([f[0] for f in m.scan_source('p.write_text("x", encoding="utf-8")\n')], [1])
        self.assertEqual([f[0] for f in m.scan_source("import tempfile\ntempfile.mkstemp(text=True)\n")], [2])
        self.assertEqual([f[1][:6] for f in m.scan_source('if __name__ == "__main__":\n    print(1)\n')], ["prints"])


class DoctorRequiresEolRuleTests(unittest.TestCase):
    def setUp(self):
        self.d = load(SCRIPTS / "pack-doctor.py", "pack_doctor_p3")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "docs" / "ai-forward-pack" / "scripts").mkdir(parents=True)
        (self.root / "docs" / "ai-forward-pack" / "scripts" / "coord-core.py").write_text("# stub\n", encoding="utf-8", newline="\n")
        (self.root / ".agents").mkdir()
        (self.root / ".agents" / "artifacts.yml").write_text(
            "docs/docs-index.js: derived python3 x.py derive\ndocs/audit/audit-log.jsonl: register\n",
            encoding="utf-8", newline="\n")

    def test_drivers_declared_without_eol_rule_fail(self):
        (self.root / ".gitattributes").write_text("docs/audit/audit-log.jsonl merge=coord-register\n",
                                                  encoding="utf-8", newline="\n")
        result = self.d.check_coordination(str(self.root))
        self.assertEqual(result["status"], self.d.FAIL, result)
        self.assertIn("eol=lf", result["detail"])

    def test_drivers_with_eol_rule_do_not_fail_for_that_reason(self):
        (self.root / ".gitattributes").write_text(
            "* text=auto eol=lf\ndocs/audit/audit-log.jsonl merge=coord-register\n",
            encoding="utf-8", newline="\n")
        result = self.d.check_coordination(str(self.root))
        self.assertNotIn("eol=lf", result["detail"])


class PackApplyShipsLineEndingPolicyTests(unittest.TestCase):
    def setUp(self):
        self.apply = load(SCRIPTS / "pack-apply.py", "pack_apply_p3")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.target = pathlib.Path(self.tmp.name)

    def applier(self, dry=False):
        return self.apply.Applier(str(REPO / "pack"), str(self.target), dry=dry, install=True,
                                  baselines=False, project="P3 fixture")

    def test_gitattributes_is_created_with_the_lf_rule(self):
        app = self.applier()
        app._gitattributes()
        text = (self.target / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("* text=auto eol=lf", text)
        self.assertTrue(any(r["path"] == ".gitattributes" and r["action"] in ("CREATE", "UPDATE") for r in app.rows))

    def test_existing_gitattributes_is_appended_never_rewritten(self):
        (self.target / ".gitattributes").write_text("*.psd binary\n", encoding="utf-8", newline="\n")
        self.applier()._gitattributes()
        text = (self.target / ".gitattributes").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("*.psd binary\n"))
        self.assertIn("* text=auto eol=lf", text)
        app = self.applier()
        app._gitattributes()
        self.assertTrue(any(r["path"] == ".gitattributes" and r["action"] == "UNCHANGED" for r in app.rows))

    def test_editorconfig_is_created_once_and_never_overwritten(self):
        self.applier()._editorconfig()
        path = self.target / ".editorconfig"
        self.assertIn("end_of_line = lf", path.read_text(encoding="utf-8"))
        path.write_text("root = true\n# mine\n", encoding="utf-8", newline="\n")
        app = self.applier()
        app._editorconfig()
        self.assertEqual("root = true\n# mine\n", path.read_text(encoding="utf-8"))
        self.assertTrue(any(r["path"] == ".editorconfig" and r["action"] == "SKIP" for r in app.rows))


if __name__ == "__main__":
    unittest.main()
