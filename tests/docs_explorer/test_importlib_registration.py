"""DYNAMIC-IMPORT-MODULE-REGISTRATION. A module made by importlib.util.module_from_spec is put in
sys.modules before it executes.

A module run without its sys.modules entry breaks as soon as it relies on its own import identity:
dataclasses resolves postponed annotations through sys.modules[cls.__module__], so a dataclass in a
manually loaded module raised AttributeError before any of its code ran (upstreamed from CFD-Workbench,
where a real cleanup loader reproduced it). The control is a sweep over every Python SOURCE under pack/:
in each function (or module body), `X = importlib.util.module_from_spec(spec)` is followed by
`sys.modules[spec.name] = X` before `exec_module(X)`. A module_from_spec call in any other shape is a
finding, so every loader found is a loader checked.
"""
import ast
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[2]
PACK = REPO / "pack"


def _is_call(node, attr):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == attr


def _scope_nodes(scope):
    """The nodes of one function or module body, not descending into nested functions or classes."""
    stack = list(ast.iter_child_nodes(scope))
    while stack:
        node = stack.pop()
        yield node
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            stack.extend(ast.iter_child_nodes(node))


def findings(source):
    """Return (loaders found, [line of every unregistered or uncheckable module_from_spec])."""
    tree = ast.parse(source)
    found = sum(1 for node in ast.walk(tree) if _is_call(node, "module_from_spec"))
    checked, bad = set(), []
    scopes = [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    for scope in scopes:
        made, registered, executed = [], [], []
        for node in _scope_nodes(scope):
            if (isinstance(node, ast.Assign) and _is_call(node.value, "module_from_spec")
                    and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
                made.append((node.targets[0].id, node.lineno, node.value.args))
                checked.add(id(node.value))
            if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Name) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Subscript)
                    and isinstance(node.targets[0].value, ast.Attribute) and node.targets[0].value.attr == "modules"):
                key = node.targets[0].slice
                key_spec = (isinstance(key, ast.Attribute) and key.attr == "name"
                            and isinstance(key.value, ast.Name) and key.value.id)
                registered.append((node.value.id, node.lineno, key_spec))
            if _is_call(node, "exec_module") and node.args and isinstance(node.args[0], ast.Name):
                executed.append((node.args[0].id, node.lineno))
        for name, line, spec_args in made:
            spec_name = spec_args[0].id if spec_args and isinstance(spec_args[0], ast.Name) else None
            runs = [run for module, run in executed if module == name and run > line]
            if not runs:
                continue
            first = min(runs)
            if not any(module == name and line < reg < first and key == spec_name
                       for module, reg, key in registered):
                bad.append(line)
    bad += [node.lineno for node in ast.walk(tree) if _is_call(node, "module_from_spec") and id(node) not in checked]
    return found, sorted(bad)


class ImportlibRegistrationTests(unittest.TestCase):
    def test_the_rule_catches_each_unregistered_shape(self):
        head = "import importlib.util, sys\nspec = importlib.util.spec_from_file_location('m', 'm.py')\n"
        good = head + "module = importlib.util.module_from_spec(spec)\nsys.modules[spec.name] = module\nspec.loader.exec_module(module)\n"
        self.assertEqual((1, []), findings(good))
        cases = {
            "unregistered": head + "module = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(module)\n",
            "wrong key": good.replace("sys.modules[spec.name]", "sys.modules['other']"),
            "registered after": head + "module = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(module)\nsys.modules[spec.name] = module\n",
            "another function's registration": ("import importlib.util, sys\n"
                                                "def a(spec):\n    module = importlib.util.module_from_spec(spec)\n    spec.loader.exec_module(module)\n"
                                                "def b(spec, module):\n    sys.modules[spec.name] = module\n    spec.loader.exec_module(module)\n"),
            "uncheckable shape": head + "self.module = importlib.util.module_from_spec(spec)\n",
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                self.assertTrue(findings(source)[1], name + " passed the rule")

    def test_every_pack_loader_registers_before_it_executes(self):
        files = sorted(PACK.rglob("*.py"))
        self.assertTrue(files, "no pack sources found: the sweep would pass vacuously")
        loaders = 0
        for path in files:
            found, bad = findings(path.read_text(encoding="utf-8"))
            loaders += found
            with self.subTest(script=str(path.relative_to(PACK))):
                self.assertEqual([], bad, "{0}: module_from_spec result executed unregistered (or uncheckable)".format(path.name))
        self.assertGreater(loaders, 0, "no loader found: the sweep would pass vacuously")


if __name__ == "__main__":
    unittest.main()
