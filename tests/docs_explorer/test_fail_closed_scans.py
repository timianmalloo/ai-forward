"""CTRL-G. A scan that renders a verdict over a corpus never skips an item it could not read.

`except OSError: continue` around a read, an lstat failure reported as "not a regular file",
and an `os.walk` with no `onerror` each drop an item without a trace. The surface limit failed
open that way (docs/investigations/surface-limit-flake.md), and seven shipped gates passed files
they never read. The rule: only a path that does not exist (`FileNotFoundError`, or
`NotADirectoryError` when a parent is a file) may be skipped silently;
any other failure is a finding, or the enumeration declares itself best-effort with
`# skip-ok: <reason>` on the handler or walk line.

The control is an AST rule, not a text match: a text rule hit 59 handlers, about half of them
the stdout-reconfigure boilerplate, and missed every helper a corpus loop calls.
"""
import ast
import builtins
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"
ENUMERATORS = {"walk", "rglob", "glob", "iglob", "scandir", "listdir", "iterdir"}
# FileNotFoundError and NotADirectoryError (a parent is a file) both mean "the path does not exist":
# the one legitimate silent skip. Everything else could hide a real item.
BROAD = {"OSError", "IOError", "EnvironmentError", "Exception", "BaseException", "PermissionError",
         "IsADirectoryError", "InterruptedError", "BlockingIOError", "TimeoutError"}


def _name(node):
    return node.attr if isinstance(node, ast.Attribute) else getattr(node, "id", "")


def _receiver(call):
    return _name(call.func.value) if isinstance(call.func, ast.Attribute) else ""


def _is_scanner(tree, source):
    """A module that enumerates files: an os/pathlib/glob listing call, or `git ls-files`."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _name(node.func) in ENUMERATORS and _receiver(node) != "ast":
            return True
    return "ls-files" in source


def _catches_too_much(handler):
    if handler.type is None:
        return True
    caught = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    return any(_name(kind) in BROAD for kind in caught)


def _is_empty(value):
    """None, a falsy constant, or an empty display: a value that stands in for 'nothing found'."""
    if value is None:
        return True
    if isinstance(value, ast.Constant) and value.value in (None, False, "", 0):
        return True
    if isinstance(value, (ast.List, ast.Tuple, ast.Set)) and not value.elts:
        return True
    return isinstance(value, ast.Dict) and not value.keys


def _is_silent(handler):
    if len(handler.body) != 1:
        return False
    statement = handler.body[0]
    if isinstance(statement, (ast.Continue, ast.Pass)):
        return True
    if isinstance(statement, ast.Return):
        return _is_empty(statement.value)
    # `ts = None` / `checked = False`: the item reads as empty and the loop carries on.
    return isinstance(statement, ast.Assign) and _is_empty(statement.value)


def violations(source, filename="<fixture>"):
    """Every CTRL-G shape in one module, as 'file:line reason'."""
    tree = ast.parse(source, filename)
    lines = source.splitlines()

    def declared(lineno):
        return "skip-ok:" in lines[lineno - 1]

    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or declared(node.lineno):
            continue
        if _name(node.func) == "walk" and _receiver(node) == "os" and not any(
                k.arg == "onerror" for k in node.keywords):
            found.add(f"{filename}:{node.lineno} os.walk with no onerror drops unlistable directories")
        if _name(node.func) == "rglob":
            found.add(f"{filename}:{node.lineno} rglob skips unlistable directories (use os.walk(onerror=))")
        # Path.glob and glob.glob/iglob return [] for a directory they cannot list; iterdir raises.
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("glob", "iglob"):
            found.add(f"{filename}:{node.lineno} glob reads an unlistable directory as empty (use iterdir)")
        # Path.walk (3.12) ignores errors unless on_error is given, like os.walk. A bare walk() is a
        # local function, not a listing.
        if (isinstance(node.func, ast.Attribute) and node.func.attr == "walk"
                and _receiver(node) not in ("os", "ast")
                and not any(k.arg == "on_error" for k in node.keywords)):
            found.add(f"{filename}:{node.lineno} Path.walk with no on_error drops unlistable directories")
    if not _is_scanner(tree, source):
        return sorted(found)
    functions = {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    zones = []
    for loop in ast.walk(tree):
        # A loop over a tuple/list/set display is fixed data (sys.stdout, sys.stderr), not a corpus.
        if isinstance(loop, ast.For) and not isinstance(loop.iter, (ast.Tuple, ast.List, ast.Set)):
            zones.append(loop)
            zones.extend(functions[sub.func.id] for sub in ast.walk(loop)
                         if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
                         and sub.func.id in functions)
    for zone in zones:
        for handler in ast.walk(zone):
            if (isinstance(handler, ast.ExceptHandler) and _catches_too_much(handler)
                    and _is_silent(handler) and not declared(handler.lineno)):
                found.add(f"{filename}:{handler.lineno} silently skips an item it could not read")
    return sorted(found)


class FailClosedScanControl(unittest.TestCase):
    def test_no_corpus_scan_skips_an_item_silently(self):
        found = []
        for path in sorted(SCRIPTS.glob("*.py")):
            found.extend(violations(path.read_text(encoding="utf-8"), path.name))
        self.assertEqual([], found, "CTRL-G: record a finding, or declare `# skip-ok: <reason>`")

    def test_the_control_flags_each_shape_and_spares_the_safe_ones(self):
        positives = [
            "import os\nfor d, _, fs in os.walk(r):\n    for f in fs:\n        try:\n            open(f)\n"
            "        except OSError:\n            continue\n",
            "import os\ndef t(p):\n    try:\n        return open(p).read()\n    except (OSError, ValueError):\n"
            "        return None\nfor d, _, fs in os.walk(r, onerror=print):\n    for f in fs:\n        t(f)\n",
            "import os\nfor p in sorted(base.rglob('*')):\n    pass\n",
            "import os\nfor d, _, fs in os.walk(r):\n    pass\n",
            "out = run(['git', 'ls-files'])\nfor rel in out:\n    try:\n        x = open(rel)\n"
            "    except Exception:\n        pass\n",
            "for p in sorted(base.glob('*.jsonl')):\n    pass\n",
            "import glob\nfor p in glob.glob('*.jsonl'):\n    pass\n",
            "for d, _, fs in root.walk():\n    pass\n",
            "import os\nfor d, _, fs in os.walk(r, onerror=print):\n    for f in fs:\n        try:\n"
            "            ts = parse(open(f))\n        except (ValueError, OSError):\n            ts = None\n",
        ]
        negatives = [
            "import os\nfor d, _, fs in os.walk(r, onerror=print):\n    for f in fs:\n        try:\n"
            "            open(f)\n        except FileNotFoundError:\n            continue\n",
            "import os, sys\nos.listdir('.')\nfor s in (sys.stdout, sys.stderr):\n    try:\n"
            "        s.reconfigure(encoding='utf-8')\n    except (ValueError, OSError):\n        pass\n",
            "import ast\nfor node in ast.walk(tree):\n    try:\n        f(node)\n    except OSError:\n        continue\n",
            "import os\nfor d, _, fs in os.walk(r):  # skip-ok: advisory miner\n    pass\n",
            "import os\nfor d, _, fs in os.walk(r, onerror=print):\n    for f in fs:\n        try:\n"
            "            open(f)\n        except OSError:  # skip-ok: best-effort discovery\n            continue\n",
            "def probe(p):\n    try:\n        return open(p).read()\n    except OSError:\n        return None\n",
            "for p in sorted(q for q in base.iterdir() if q.match('*.jsonl')):\n    pass\n",
            "for d, _, fs in root.walk(on_error=print):\n    pass\n",
            "def walk(t):\n    return t\nfor n in walk(tree):\n    pass\n",
            "import os\nfor d, _, fs in os.walk(r, onerror=print):\n    for f in fs:\n        try:\n"
            "            ts = parse(open(f))\n        except ValueError:\n            ts = None\n",
        ]
        for snippet in positives:
            self.assertTrue(violations(snippet), snippet)
        for snippet in negatives:
            self.assertEqual([], violations(snippet), snippet)


def _load(name):
    """A gate under test. FAIL_CLOSED_SCRIPTS points the suite at another tree, which is how the
    pre-fix scripts were shown to fail every test below."""
    path = Path(os.environ.get("FAIL_CLOSED_SCRIPTS", SCRIPTS)) / name
    spec = importlib.util.spec_from_file_location(name[:-3].replace("-", "_") + "_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def _faulty_open(name, error_type):
    """open() of the file whose path ends with `name` raises `error_type`; every other open is real."""
    real, opened = builtins.open, []

    def fake(file, *args, **kwargs):
        if isinstance(file, (str, os.PathLike)) and os.fspath(file).replace("\\", "/").endswith(name):
            opened.append(file)
            raise error_type(2 if error_type is FileNotFoundError else 13, "simulated", os.fspath(file))
        return real(file, *args, **kwargs)

    with mock.patch("builtins.open", fake), mock.patch("io.open", fake):
        yield opened


@contextlib.contextmanager
def _unlistable(name):
    """Listing the directory whose path ends with `name` raises PermissionError. Both listing calls
    are patched: Path.iterdir is os.listdir on 3.12 and os.scandir on 3.13."""
    def denying(real):
        def fake(path=".", *args, **kwargs):
            if os.fspath(path).replace("\\", "/").endswith(name):
                raise PermissionError(13, "simulated", os.fspath(path))
            return real(path, *args, **kwargs)
        return fake

    with mock.patch("os.scandir", denying(os.scandir)), mock.patch("os.listdir", denying(os.listdir)):
        yield


def _write(root, rel, text="clean\n"):
    path = Path(root, rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _git_repo(root, *rels):
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for rel in rels:
        _write(root, rel)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)


def _quiet(call):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return call()


class GatesFailClosedTests(unittest.TestCase):
    """CTRL-G, per site: a file that exists but cannot be read fails the gate; a file that is gone
    is skipped, as before; the faulty file is opened at most once (no retry)."""

    def _verdicts(self, setup, run, target):
        """(exit for PermissionError, opens of the target, exit for FileNotFoundError)."""
        results = []
        for error_type in (PermissionError, FileNotFoundError):
            with tempfile.TemporaryDirectory() as temp:
                setup(Path(temp))
                with _faulty_open(target, error_type) as opened:
                    results.append((_quiet(lambda: run(Path(temp))), len(opened)))
        (denied, opens), (gone, _) = results
        return denied, opens, gone

    def _assert_fails_closed(self, setup, run, target, clean=0):
        denied, opens, gone = self._verdicts(setup, run, target)
        self.assertNotEqual(clean, denied, "an unreadable file passed the gate")
        self.assertLessEqual(opens, 1, "the unreadable file was opened more than once")
        self.assertEqual(clean, gone, "a file gone from the tree must still be skipped")

    def test_marker_lint(self):
        gate = _load("marker-lint.py")
        self._assert_fails_closed(lambda r: (_write(r, "a.py"), _write(r, "b.py")),
                                  lambda r: gate.main(["--root", str(r), "--gate"]), "a.py")

    def test_verify_no_conflict_markers(self):
        gate = _load("verify-no-conflict-markers.py")
        self._assert_fails_closed(lambda r: _git_repo(r, "a.md", "b.md"),
                                  lambda r: gate.main(["--root", str(r)]), "a.md")

    def test_verify_no_machine_paths(self):
        gate = _load("verify-no-machine-paths.py")
        self._assert_fails_closed(lambda r: _git_repo(r, "pack/a.md", "pack/b.md"),
                                  lambda r: gate.main(["--root", str(r)]), "pack/a.md")

    def test_verify_portable_text_io(self):
        gate = _load("verify-portable-text-io.py")
        self._assert_fails_closed(lambda r: (_write(r, "tools/a.py"), _write(r, "tools/b.py")),
                                  lambda r: gate.main(["--root", str(r)]), "tools/a.py")

    def test_verify_subprocess_utf8(self):
        gate = _load("verify-subprocess-utf8.py")
        self._assert_fails_closed(lambda r: (_write(r, "tools/a.py"), _write(r, "tools/b.py")),
                                  lambda r: gate.main(["--root", str(r)]), "tools/a.py")

    def test_scrub(self):
        gate = _load("scrub.py")

        def run(root):
            with mock.patch.object(sys, "argv", ["scrub.py", "--check", str(root)]):
                return gate.main()
        self._assert_fails_closed(lambda r: (_write(r, "a.md"), _write(r, "b.md")), run, "a.md")

    def test_the_committed_secret_scan_reports_an_unreadable_file(self):
        gate = _load("visual-assets-setup.py")
        self._assert_fails_closed(lambda r: (_write(r, "a.md"), _write(r, "b.md")),
                                  lambda r: len(gate.scan_for_committed_secrets(str(r))), "a.md")

    def test_console_launch_gate_reports_a_directory_it_cannot_list(self):
        gate = _load("verify-no-new-console-launches.py")
        with tempfile.TemporaryDirectory() as temp:
            _write(temp, "tests/sub/a.py")
            _write(temp, "tests/b.py")
            with _unlistable("tests/sub"):
                out, _ = gate.findings(Path(temp))
        self.assertTrue(any("tests/sub: could not be listed" in line for line in out), out)

    def test_ruling_citations_stop_on_a_directory_they_cannot_list(self):
        gate = _load("verify-ruling-citations.py")
        with tempfile.TemporaryDirectory() as temp:
            _write(temp, "docs/sub/a.md", "see DR-1\n")
            with _unlistable("docs/sub"), self.assertRaises(PermissionError):
                gate.citations(Path(temp))

    def test_xaml_lint_stops_on_a_directory_it_cannot_list(self):
        gate = _load("xaml-token-lint.py")
        with tempfile.TemporaryDirectory() as temp:
            _write(temp, "ui/sub/a.xaml", "<Grid/>\n")
            with _unlistable("ui/sub"), self.assertRaises(PermissionError):
                gate.expand_paths(Path(temp), ["ui"])

    def test_xaml_lint_lists_what_rglob_listed(self):
        """The walk replaced rglob: same files, sorted, suffix matched in any case, links not followed."""
        gate = _load("xaml-token-lint.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for rel in ("ui/b.xaml", "ui/A.XAML", "ui/sub/c.xaml", "ui/skip.txt"):
                _write(root, rel, "<Grid/>\n")
            _write(root, "outside/d.xaml", "<Grid/>\n")
            try:
                os.symlink(root / "outside", root / "ui" / "linked", target_is_directory=True)
            except OSError:   # no symlink privilege on this Windows account: the order/case half still runs
                pass
            found = [p.relative_to(root.resolve()).as_posix()
                     for p in gate.expand_paths(root, ["ui"])]
        self.assertEqual(["ui/A.XAML", "ui/b.xaml", "ui/sub/c.xaml"], found)

    def test_documented_commands_stop_on_a_directory_they_cannot_list(self):
        gate = _load("verify-documented-commands.py")
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp)
            _write(pack, "commands/sub/SKILL.md")
            with _unlistable("commands/sub"), self.assertRaises(PermissionError):
                gate.documented_files(pack)

    def test_documented_commands_list_what_glob_listed(self):
        gate = _load("verify-documented-commands.py")
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp)
            for rel in ("commands/top.md", "commands/a/SKILL.md", "commands/a/b/deep.md", "commands/a/x.txt",
                        "knowledge/k.md", "knowledge/nested/no.md", "adapters/INSTALL.md",
                        "adapters/OTHER.md", "templates/t.md"):
                _write(pack, rel)
            expected = []
            for pattern in gate.ROOT_GLOBS:
                expected.extend(sorted(p for p in pack.glob(pattern) if p.is_file()))
            self.assertEqual(expected, gate.documented_files(pack))
            self.assertEqual(6, len(expected))

    def test_gate_runner_stops_on_a_gate_directory_it_cannot_list(self):
        gate = _load("run-verify-gates.py")
        with tempfile.TemporaryDirectory() as temp:
            _write(temp, "tools/verify-a.py")
            with _unlistable("tools"), self.assertRaises(PermissionError):
                gate.gates(Path(temp), ["tools"])

    def test_delivery_link_check_does_not_answer_for_a_path_it_cannot_examine(self):
        gate = _load("delivery.py")
        with tempfile.TemporaryDirectory() as temp:
            _write(temp, "a.txt")
            target = os.path.join(temp, "a.txt")

            def denying(real):
                def fake(path, *args, **kwargs):
                    if os.fspath(path) == target:
                        raise PermissionError(13, "simulated", target)
                    return real(path, *args, **kwargs)
                return fake
            # Path.lstat() is os.stat(follow_symlinks=False) on newer Pythons, os.lstat on older.
            with mock.patch("os.lstat", denying(os.lstat)), mock.patch("os.stat", denying(os.stat)), \
                    self.assertRaises(PermissionError):
                gate.is_link(target)
            self.assertFalse(gate.is_link(os.path.join(temp, "gone.txt")))

    def test_pack_apply_read_does_not_mistake_unreadable_for_absent(self):
        gate = _load("pack-apply.py")
        with tempfile.TemporaryDirectory() as temp:
            _write(temp, "a.md")
            with _faulty_open("a.md", PermissionError), self.assertRaises(PermissionError):
                gate.read(os.path.join(temp, "a.md"))
            self.assertIsNone(gate.read(os.path.join(temp, "gone.md")))


if __name__ == "__main__":
    unittest.main()
