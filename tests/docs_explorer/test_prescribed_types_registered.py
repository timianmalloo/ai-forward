"""Every frontmatter `type:` a skill or a template prescribes is one the graph validator accepts.

Found 2026-09-19: /prepare-for-coordination's plan schema prescribes `type: plan`; docs-graph.py's
TYPES had no `plan`, so the first plan written to the pack's own schema failed `validate` with
"unknown type: plan". The skill and the validator are both pack source, so the drift is a pack
defect, not a user error. This test pins the union of prescribed types inside the registry.
"""
import importlib.util
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "pack", "scripts", "docs-graph.py")
COMMANDS = os.path.join(ROOT, "pack", "commands")
TEMPLATES = os.path.join(ROOT, "pack", "templates")

_spec = importlib.util.spec_from_file_location("docs_graph", SCRIPT)
_dg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dg)

TYPE_LINE = re.compile(r"^type:\s*([a-z][a-z-]*)\s*$", re.M)


def _prescribed(root, suffixes):
    found = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if not name.endswith(suffixes):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            for m in TYPE_LINE.finditer(text):
                found.setdefault(m.group(1), set()).add(os.path.relpath(path, ROOT))
    return found


class PrescribedTypesAreRegistered(unittest.TestCase):
    def test_skill_and_template_types_are_in_the_registry(self):
        registry = set(_dg.TYPES)
        prescribed = {}
        for t, paths in _prescribed(COMMANDS, (".md",)).items():
            prescribed.setdefault(t, set()).update(paths)
        for t, paths in _prescribed(TEMPLATES, (".md",)).items():
            prescribed.setdefault(t, set()).update(paths)
        self.assertTrue(prescribed, "no prescribed types found - the scan root moved")
        missing = {t: sorted(p) for t, p in prescribed.items() if t not in registry}
        self.assertEqual(missing, {}, f"types prescribed by pack source but unknown to docs-graph.py TYPES: {missing}")

    def test_plan_is_a_registered_type(self):
        self.assertIn("plan", _dg.TYPES)


if __name__ == "__main__":
    unittest.main()
