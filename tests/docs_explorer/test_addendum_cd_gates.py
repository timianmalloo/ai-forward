"""The four gate scripts lifted from the Addenda C/D programme, each proven two ways.

`run-verify-gates.py` (DC-113's loop form), `conductor-join.py` (the join as a script),
`verify-no-conflict-markers.py` (DC-136) and `verify-no-new-console-launches.py` (DC-170)
each carry a --self-test. A self-test is only evidence if it can go red, so every script is
also MUTATED here in the way its control exists to catch, and the self-test must fail on
the mutant (DC-104: a control that cannot fail is not a control).
"""
import io
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "pack" / "scripts"

GATES = ["run-verify-gates.py", "conductor-join.py", "verify-no-conflict-markers.py",
         "verify-no-new-console-launches.py"]

# (the line the control depends on, the line that disables it)
MUTATIONS = {
    "run-verify-gates.py": ("failures += 0 if ok else 1", "failures += 0"),
    "verify-no-conflict-markers.py": ('MARKERS = ("<<<<<<<", ">>>>>>>", "|||||||")',
                                      'MARKERS = ("\\x00never",)'),
    "verify-no-new-console-launches.py": ('COMMENT = re.compile(r"^\\s*(//|#|\\*|--)")',
                                          'COMMENT = re.compile(r"")'),
    "conductor-join.py": ('j.run(3, "no conflict markers", [PY, _sibling("verify-no-conflict-markers.py")])',
                          'j.run(3, "no conflict markers", [PY, _sibling("verify-no-conflict-markers.py")], allow=(0, 1))'),
}


def run(path, *args, cwd=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, str(path), *args], cwd=str(cwd or ROOT),
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=env, timeout=180)


class EverySelfTestIsGreenOnTheShippedScript(unittest.TestCase):
    def test_self_tests_pass(self):
        for name in GATES:
            with self.subTest(script=name):
                result = run(SCRIPTS / name, "--self-test")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("OK", result.stdout)


class EverySelfTestGoesRedOnItsMutant(unittest.TestCase):
    """The scripts are copied as a set (they resolve siblings by path) and one line is broken."""

    def test_mutants_fail_their_own_self_test(self):
        for name, (old, new) in MUTATIONS.items():
            with self.subTest(script=name):
                tmp = tempfile.mkdtemp()
                try:
                    for f in os.listdir(SCRIPTS):
                        if (SCRIPTS / f).is_file():
                            shutil.copy(SCRIPTS / f, tmp)
                    path = pathlib.Path(tmp) / name
                    text = io.open(path, encoding="utf-8").read()
                    self.assertIn(old, text, "the mutation target moved; update MUTATIONS")
                    io.open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
                    result = run(path, "--self-test")
                    self.assertNotEqual(result.returncode, 0,
                                        name + " self-test stayed green on a broken script:\n"
                                        + result.stdout + result.stderr)
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)


class TheGateRunnerRunsThePackGatesOnThisRepo(unittest.TestCase):
    def test_the_runner_finds_and_runs_the_pack_gates(self):
        result = run(SCRIPTS / "run-verify-gates.py", "--dir", "pack/scripts",
                     "--args", "verify-no-new-console-launches.py=--root-dir pack --root-dir tools")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("verify-no-conflict-markers.py", result.stdout)
        self.assertIn("verify-no-new-console-launches.py", result.stdout)
        self.assertNotIn("run-verify-gates.py", result.stdout.split("gate(s) in")[1].split("\n", 1)[1],
                         "the runner must not run itself")


class TheHelpTextsSurviveALegacyConsole(unittest.TestCase):
    def test_help_under_cp1252(self):
        for name in GATES:
            with self.subTest(script=name):
                env = dict(os.environ, PYTHONIOENCODING="cp1252")
                result = subprocess.run([sys.executable, str(SCRIPTS / name), "--help"],
                                        capture_output=True, text=True, encoding="utf-8",
                                        errors="replace", env=env, timeout=60)
                self.assertEqual(result.returncode, 0, result.stderr[-400:])


if __name__ == "__main__":
    unittest.main()
