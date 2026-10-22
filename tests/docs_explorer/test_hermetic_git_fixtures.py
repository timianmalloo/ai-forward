"""TEST-C. A test never takes refs from the developer checkout it runs in.

A fixture that clones the repository root inherits every tag and branch the developer has
fetched. Since the 2026-10-19 release tag, `clone_source()` copied `v2026.10.19.4` into its
upstream and the test then failed creating that same tag - in every developer clone, never in
CI (which checks out without tags). The rule: a clone of the repo root carries `--no-tags`, and
a named `--ref` (anything but HEAD) is never resolved against the repo root itself.
docs/investigations/bootstrap-release-tag-collision.md.
"""
import ast
from pathlib import Path
import unittest
import warnings

TESTS = Path(__file__).resolve().parents[1]
ROOT_NAMES = {"ROOT", "REPO"}
# Subcommands whose answer depends on which refs (or which branch) the checkout holds.
REF_READS = {"branch", "rev-parse", "tag", "for-each-ref", "describe", "show-ref", "symbolic-ref",
             "rev-list", "merge-base", "name-rev"}


def _is_root_expression(node):
    """ROOT, REPO, str(ROOT), ROOT.as_uri(), str(ROOT.resolve()) - the repo root, in any spelling."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id in ROOT_NAMES:
            return True
    return False


def _strings(elements):
    return [e.value for e in elements if isinstance(e, ast.Constant) and isinstance(e.value, str)]


def _call_arguments(call):
    """The argument elements of a call, flattening one list/tuple literal (subprocess.run([...]))."""
    flat = []
    for argument in call.args:
        if isinstance(argument, (ast.List, ast.Tuple)):
            flat.extend(argument.elts)
        elif isinstance(argument, ast.Starred):
            continue
        else:
            flat.append(argument)
    return flat


def violations(source, filename="<fixture>"):
    """Every TEST-C shape in one test module, as 'file:line reason'."""
    found = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)   # another module's escapes are not ours to judge
        tree = ast.parse(source, filename)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Call, ast.List, ast.Tuple)):
            continue
        elements = _call_arguments(node) if isinstance(node, ast.Call) else list(node.elts)
        words = _strings(elements)
        if "clone" in words and any(_is_root_expression(e) for e in elements):
            if "--no-tags" not in words:
                found.append(f"{filename}:{node.lineno} clones the repo root without --no-tags")
        if isinstance(node, ast.Call) and words and words[0] in REF_READS | {"git"}:
            on_root = any(k.arg == "cwd" and _is_root_expression(k.value) for k in node.keywords) or any(
                isinstance(e, ast.Constant) and e.value == "-C" and i + 1 < len(elements)
                and _is_root_expression(elements[i + 1]) for i, e in enumerate(elements))
            command = [w for w in words if w not in ("git", "-C")]
            if on_root and command and command[0] in REF_READS:
                named = [w for w in command[1:] if not w.startswith("-") and w not in ("HEAD", "--")]
                if named or "--show-current" in command:
                    found.append(f"{filename}:{node.lineno} reads a ref from the developer checkout")
        if isinstance(node, ast.Call) and "--ref" in words:
            index = next(i for i, e in enumerate(elements)
                         if isinstance(e, ast.Constant) and e.value == "--ref")
            ref = elements[index + 1] if index + 1 < len(elements) else None
            if isinstance(ref, ast.Constant) and ref.value == "HEAD":
                continue
            explicit_root = any(
                isinstance(e, ast.Constant) and e.value in ("--source", "--repo")
                and i + 1 < len(elements) and _is_root_expression(elements[i + 1])
                for i, e in enumerate(elements))
            func = node.func
            helper = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            default_root = helper == "run_bootstrap" and not any(k.arg == "source" for k in node.keywords)
            if explicit_root or default_root:
                found.append(f"{filename}:{node.lineno} resolves a named --ref against the repo root")
    return sorted(set(found))


class HermeticGitFixtureControl(unittest.TestCase):
    def test_no_test_takes_refs_from_the_developer_checkout(self):
        found = []
        for path in sorted(TESTS.rglob("*.py")):  # skip-ok: a test-suite scan; an unreadable test fails the read below
            found.extend(violations(path.read_text(encoding="utf-8"), path.relative_to(TESTS).as_posix()))
        self.assertEqual([], found, "TEST-C: build a hermetic origin (clone --no-tags) and name only refs the test created")

    def test_the_control_flags_each_shape_and_spares_the_safe_ones(self):
        positives = {
            'self.git("clone", "--no-hardlinks", str(ROOT), str(source))': 1,
            'subprocess.run(["git", "clone", "-q", "--depth", "1", REPO.as_uri(), str(c)])': 1,
            'self.run_bootstrap("--ref", "does-not-exist")': 1,
            'self.run_bootstrap("--ref", ref)': 1,
            'subprocess.run([exe, SCRIPT, "--source", str(ROOT), "--ref", "preview"])': 1,
            'subprocess.run([exe, SCRIPT, "--repo", ROOT.as_uri(), "--ref", "v1"])': 1,
            'self.git("branch", "--show-current", cwd=ROOT)': 1,
            'subprocess.run(["git", "-C", str(ROOT), "rev-parse", "origin/main"])': 1,
        }
        negatives = [
            'self.git("clone", "--no-tags", "--no-hardlinks", str(ROOT), str(source))',
            'self.git("clone", "--no-hardlinks", str(origin), str(source))',
            'self.run_bootstrap("--ref", "refs/heads/preview", source=source)',
            'self.run_bootstrap("--ref", "HEAD")',
            'subprocess.run([exe, SCRIPT, "--source", str(ROOT), "--ref", "HEAD", "--dry-run"])',
            'self.run_bootstrap()',
            'repo.run("board", "post", "--ref", "DR-3")',
            'self.git("rev-parse", "HEAD", cwd=ROOT)',
            'self.git("ls-files", cwd=ROOT)',
            'self.git("branch", "--show-current", cwd=source)',
            'subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%H", ref, "--", path])',
        ]
        for snippet, expected in positives.items():
            self.assertEqual(expected, len(violations(snippet)), snippet)
        for snippet in negatives:
            self.assertEqual([], violations(snippet), snippet)


if __name__ == "__main__":
    unittest.main()
