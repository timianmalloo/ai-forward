"""Generated API pages keep one LF terminator, not new-file whitespace errors."""
import ast
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("api_docs_format", ROOT / "tools/build-api-docs.py")
assert SPEC is not None and SPEC.loader is not None
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)


class ApiGeneratedFormatTests(unittest.TestCase):
    def test_delivery_api_is_owned_by_the_contributor_without_reassigning_existing_apis(self):
        tree = ast.parse('\"\"\"Example module.\"\"\"\n')
        delivery, _, _ = API.render("delivery.py", tree, "pack/scripts/delivery.py")
        existing, _, _ = API.render("audit-log.py", tree, "pack/scripts/audit-log.py")
        self.assertIn('owner: "@ahutanu"', delivery)
        self.assertIn('owner: "@timianmalloo"', existing)

    def test_module_page_has_exactly_one_final_newline(self):
        tree = ast.parse('"""Example stdlib module."""\ndef example():\n    """Return an example."""\n    return 1\n')
        page, _, _ = API.render("example.py", tree, "pack/scripts/example.py")
        self.assertTrue(page.endswith("\n"))
        self.assertFalse(page.endswith("\n\n"), "New generated modules must not create git whitespace errors")
