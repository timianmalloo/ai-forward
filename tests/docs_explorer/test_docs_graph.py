import ast
import concurrent.futures
import hashlib
import importlib.util
import io
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "pack" / "scripts" / "docs-graph.py"
TRAVERSAL_FIXTURE = REPO / "tests" / "docs_explorer" / "traversal-policy-v1.json"
TRAVERSAL_RUNNER = REPO / "tests" / "docs_explorer" / "traversal_parity_runner.js"


def load_module():
    spec = importlib.util.spec_from_file_location("docs_graph", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class DocsGraphTests(unittest.TestCase):
    def test_rollup_writes_utf8_when_console_encoding_cannot_encode_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            (root / "design.md").write_text(
                """---
id: design-unicode
title: Unicode design
type: design
status: accepted
owner: "@maintainers"
tags: [test]
links: []
review-by: 2099-01-01
summary: Exercises Unicode rollup output.
---

# Unicode design

## Adversarial analysis (STRIDE-lite)

| Boundary | STRIDE | Disposition | Control | Negative test |
|---|---|---|---|---|
| source → sink | **T** | mitigate | validate | rejects invalid input |
""",
                encoding="utf-8",
            )
            environment = {**os.environ, "PYTHONIOENCODING": "cp1252"}

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "rollup",
                    "--heading",
                    "Adversarial analysis (STRIDE-lite)",
                    "--type",
                    "design",
                ],
                capture_output=True,
                env=environment,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
            self.assertIn("source → sink", result.stdout.decode("utf-8"))

    def test_traversal_policies_match_javascript_for_shared_fixture(self):
        module = load_module()
        fixture = json.loads(TRAVERSAL_FIXTURE.read_text(encoding="utf-8"))
        by_id = {artifact["id"]: artifact for artifact in fixture["artifacts"]}

        for policy, rules in fixture["policies"].items():
            with self.subTest(policy=policy):
                original = module.POLICIES.get(policy)
                module.POLICIES[policy] = rules
                try:
                    for hops in range(3):
                        python_paths = module.traverse_context(
                            by_id, fixture["rootId"], policy, hops
                        )[3]
                        javascript_paths = self._javascript_paths(
                            fixture["artifacts"], fixture["rootId"], rules, hops
                        )
                        self.assertEqual(python_paths, javascript_paths)
                finally:
                    if original is None:
                        module.POLICIES.pop(policy, None)
                    else:
                        module.POLICIES[policy] = original

    def test_seeded_traversal_property_cases_match_javascript(self):
        module = load_module()
        randomizer = random.Random(0xA1F0)
        relations = ["implements", "depends-on", "tested-by", "documents"]
        directions = ["outbound", "inbound"]

        for case_number in range(16):
            node_count = randomizer.randint(2, 18)
            ids = [f"node-{ordinal:02d}" for ordinal in range(node_count)]
            artifacts = [
                {
                    "id": artifact_id,
                    "title": artifact_id,
                    "type": "doc",
                    "status": "accepted",
                    "links": [],
                }
                for artifact_id in ids
            ]
            seen = set()
            for _ in range(randomizer.randint(node_count, node_count * 4)):
                source = randomizer.choice(artifacts)
                target = randomizer.choice(ids + ["missing"])
                relation = randomizer.choice(relations)
                key = (source["id"], relation, target)
                if key in seen:
                    continue
                seen.add(key)
                source["links"].append({"to": target, "rel": relation})
            randomizer.shuffle(artifacts)
            for artifact in artifacts:
                randomizer.shuffle(artifact["links"])
            rules = [
                {"rel": relation, "direction": direction, "priority": priority}
                for priority, relation in enumerate(randomizer.sample(relations, len(relations)))
                for direction in randomizer.sample(directions, len(directions))
            ]
            root_id = randomizer.choice(ids)
            by_id = {artifact["id"]: artifact for artifact in artifacts}
            module.POLICIES["property-test"] = rules

            for hops in range(3):
                with self.subTest(case=case_number, hops=hops):
                    python_paths = module.traverse_context(
                        by_id, root_id, "property-test", hops
                    )[3]
                    javascript_paths = self._javascript_paths(
                        artifacts, root_id, rules, hops
                    )
                    self.assertEqual(python_paths, javascript_paths)
                    self.assertEqual(
                        len({path["to"] for path in python_paths}),
                        len(python_paths),
                    )

        module.POLICIES.pop("property-test", None)

    @staticmethod
    def _javascript_paths(artifacts, root_id, rules, hops):
        completed = subprocess.run(
            ["node", str(TRAVERSAL_RUNNER)],
            input=json.dumps(
                {
                    "artifacts": artifacts,
                    "rootId": root_id,
                    "rules": rules,
                    "hops": hops,
                }
            ),
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(completed.stdout)

    def test_extract_mermaid_blocks_does_not_bleed_titles(self):
        module = load_module()
        text = """# Document

## First flow

```mermaid
flowchart LR
  A --> B
```

Some prose.

## Second flow
```mermaid
sequenceDiagram
  A->>B: Hi
```
"""

        diagrams = module.extract_mermaid_blocks(text)

        self.assertEqual(
            [
                ("First flow", "flowchart LR\n  A --> B"),
                ("Second flow", "sequenceDiagram\n  A->>B: Hi"),
            ],
            diagrams,
        )

    def test_context_packet_is_deterministic_and_bounded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            self._write_artifact(
                root / "root.md",
                artifact_id="root",
                title="Root",
                links=[{"to": "child", "rel": "depends-on"}],
                body="## Contract\n\nRetry contract is authoritative.\n",
            )
            self._write_artifact(
                root / "child.md",
                artifact_id="child",
                title="Child",
                links=[{"to": "root", "rel": "tested-by"}],
                body="## Proof\n\nThe retry boundary is tested.\n",
            )

            first = self._run_context(root, "root", max_bytes=8192)
            second = self._run_context(root, "root", max_bytes=8192)

            self.assertEqual(first, second)
            self.assertEqual("grounding-packet/v1", first["schemaVersion"])
            self.assertEqual("root", first["rootId"])
            self.assertLessEqual(first["budget"]["bytesUsed"], 8192)
            self.assertEqual(
                ["root", "child"],
                list(dict.fromkeys(chunk["artifactId"] for chunk in first["chunks"])),
            )
            self.assertEqual(64, len(first["graphSha256"]))
            self.assertTrue(all(len(chunk["sha256"]) == 64 for chunk in first["chunks"]))

    def test_context_hash_and_paths_are_stable_for_relative_and_absolute_roots(self):
        with tempfile.TemporaryDirectory(dir=REPO) as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            self._write_artifact(
                root / "root.md",
                artifact_id="root",
                title="Root",
                links=[],
                body="## Contract\n\nStable checkout identity.\n",
            )
            relative_root = root.relative_to(REPO)

            relative = self._run_context(relative_root, "root", max_bytes=8192)
            absolute = self._run_context(root.resolve(), "root", max_bytes=8192)

            self.assertEqual(relative["graphSha256"], absolute["graphSha256"])
            self.assertEqual(
                [chunk["path"] for chunk in relative["chunks"]],
                [chunk["path"] for chunk in absolute["chunks"]],
            )
            self.assertEqual("docs/root.md", relative["chunks"][0]["path"])

    def test_derive_and_context_use_the_same_graph_snapshot_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            self._write_artifact(
                root / "root.md",
                artifact_id="root",
                title="Root",
                links=[],
                body="## Contract\n\nOne canonical graph identity.\n",
            )
            derive = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "derive",
                    "--project",
                    "Stable Project",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, derive.returncode, derive.stderr)
            index_text = (root / "docs-index.js").read_text(encoding="utf-8")
            index = json.loads(index_text.split("window.DOCS_INDEX = ", 1)[1].rsplit(";", 1)[0])

            packet = self._run_context(root, "root", max_bytes=8192)

            self.assertEqual("Stable Project", packet["coverage"]["roots"][0])
            self.assertEqual(index["graphSha256"], packet["graphSha256"])

    def test_derive_discovers_safe_html_surfaces_without_changing_graph_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            (root / "audit").mkdir(parents=True)
            (root / "design").mkdir()
            (root / "_site").mkdir()
            (root / "ai-forward-pack" / "templates").mkdir(parents=True)
            self._write_artifact(
                root / "audit" / "audit-log.md",
                artifact_id="audit-log",
                title="Audit Log",
                links=[],
                body="## Audit\n\nDurable history.\n",
            )
            (root / "index.html").write_text(
                "<html><head><title>Portal</title></head></html>",
                encoding="utf-8",
            )
            (root / "audit" / "index.html").write_text(
                "<html><head><title>Audit &amp; Change Log</title></head></html>",
                encoding="utf-8",
            )
            (root / "design" / "theme-preview.html").write_text(
                "<html><body>Preview</body></html>",
                encoding="utf-8",
            )
            (root / "_site" / "index.html").write_text(
                "<html><head><title>Documentation Bundle</title></head></html>",
                encoding="utf-8",
            )
            (root / "ai-forward-pack" / "templates" / "hidden.html").write_text(
                "<html><head><title>Template</title></head></html>",
                encoding="utf-8",
            )

            module = load_module()
            module.cmd_derive(
                SimpleNamespace(
                    root=str(root),
                    project="Portal",
                    generator="test",
                    out=None,
                )
            )
            first = json.loads(
                (root / "docs-index.js")
                .read_text(encoding="utf-8")
                .split("window.DOCS_INDEX = ", 1)[1]
                .rsplit(";", 1)[0]
            )
            first_hash = first["graphSha256"]
            (root / "audit" / "index.html").write_text(
                "<html><head><title>Renamed audit surface</title></head></html>",
                encoding="utf-8",
            )
            module.cmd_derive(
                SimpleNamespace(
                    root=str(root),
                    project="Portal",
                    generator="test",
                    out=None,
                )
            )
            second = json.loads(
                (root / "docs-index.js")
                .read_text(encoding="utf-8")
                .split("window.DOCS_INDEX = ", 1)[1]
                .rsplit(";", 1)[0]
            )

            self.assertEqual(first_hash, second["graphSha256"])
            self.assertEqual(module.SURFACE_LIMIT, first["limits"]["surfaces"])
            self.assertEqual(
                [
                    "docs/audit/index.html",
                    "docs/_site/index.html",
                    "docs/design/theme-preview.html",
                ],
                [surface["path"] for surface in first["surfaces"]],
            )
            self.assertEqual(
                ["audit", "documentation", "design-preview"],
                [surface["kind"] for surface in first["surfaces"]],
            )
            self.assertEqual("Audit & Change Log", first["surfaces"][0]["title"])
            self.assertEqual("audit-log", first["surfaces"][0]["artifactId"])
            self.assertEqual("Theme Preview", first["surfaces"][2]["title"])
            self.assertNotIn("docs/index.html", [surface["path"] for surface in first["surfaces"]])
            self.assertFalse(
                any("templates" in surface["path"] for surface in first["surfaces"])
            )

    def test_html_surface_discovery_preserves_script_shaped_titles_as_data(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            (root / "tool.html").write_text(
                "<title><script>window.__surfaceOwned = true</script></title>",
                encoding="utf-8",
            )

            surfaces = module.discover_html_surfaces(str(root), [])

        self.assertEqual(
            "window.__surfaceOwned = true",
            surfaces[0]["title"],
        )

    def test_html_surface_discovery_uses_first_non_empty_title(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            (root / "tool.html").write_text(
                "<title>   </title><title>First title</title><title>Second title</title>",
                encoding="utf-8",
            )

            module = load_module()
            surfaces = module.discover_html_surfaces(str(root), [])

        self.assertEqual("First title", surfaces[0]["title"])

    def test_html_surface_discovery_fails_closed_above_surface_limit(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            for index in range(module.SURFACE_LIMIT + 1):
                (root / f"tool-{index:03d}.html").write_text(
                    f"<title>Tool {index}</title>",
                    encoding="utf-8",
                )

            with self.assertRaises(module.DocsGraphError) as captured:
                module.discover_html_surfaces(str(root), [])

        self.assertEqual("SURFACE_LIMIT_EXCEEDED", captured.exception.code)
        self.assertEqual(4, captured.exception.exit_code)

    def test_html_surface_discovery_rejects_non_regular_files_without_reading_them(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            path = root / "linked.html"
            path.write_text("not read", encoding="utf-8")
            fake_stat = SimpleNamespace(
                st_mode=module.stat.S_IFLNK,
                st_file_attributes=0,
            )
            with mock.patch.object(module.os, "lstat", return_value=fake_stat), mock.patch(
                "builtins.open", side_effect=AssertionError("symlink should not be opened")
            ):
                surfaces = module.discover_html_surfaces(str(root), [])

        self.assertEqual([], surfaces)

    def test_context_include_changes_matches_public_paths_for_absolute_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            (root / "audit").mkdir(parents=True)
            self._write_artifact(root / "root.md", "root", "Root", [], "## Root\n\nBody.\n")
            (root / "audit" / "change-log.jsonl").write_text(
                json.dumps(
                    {
                        "id": "cl-0001",
                        "datetime": "2026-07-10T00:00:00Z",
                        "summary": "Changed root.",
                        "artifacts": ["docs/root.md"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = self._run_raw(root.resolve(), "--id", "root", "--include-changes")

            self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
            packet = json.loads(result.stdout.decode("utf-8"))
            self.assertEqual(["cl-0001"], [change["id"] for change in packet["changes"]])

    def test_context_include_changes_excludes_superseded_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            (root / "audit").mkdir(parents=True)
            self._write_artifact(root / "root.md", "root", "Root", [], "## Root\n\nBody.\n")
            entries = [
                {
                    "id": "cl-0001",
                    "datetime": "2026-07-09T00:00:00Z",
                    "summary": "Old decision.",
                    "artifacts": ["docs/root.md"],
                },
                {
                    "id": "cl-0002",
                    "datetime": "2026-07-10T00:00:00Z",
                    "summary": "Replacement decision.",
                    "artifacts": ["docs/root.md"],
                    "supersedes": "cl-0001",
                },
            ]
            (root / "audit" / "change-log.jsonl").write_text(
                "".join(json.dumps(entry) + "\n" for entry in entries),
                encoding="utf-8",
            )

            packet = json.loads(
                self._run_raw(root, "--id", "root", "--include-changes").stdout.decode("utf-8")
            )

            self.assertEqual(["cl-0002"], [change["id"] for change in packet["changes"]])

    def test_context_error_uses_stderr_only_and_stable_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "context",
                    "--id",
                    "missing",
                    "--policy",
                    "grounding",
                    "--hops",
                    "1",
                    "--max-bytes",
                    "4096",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(2, result.returncode)
            self.assertEqual("", result.stdout)
            error = json.loads(result.stderr)
            self.assertEqual("docs-graph-error/v1", error["schemaVersion"])
            self.assertEqual("ROOT_NOT_FOUND", error["error"]["code"])

    def test_context_rejects_duplicate_typed_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            links = [
                {"to": "child", "rel": "depends-on"},
                {"to": "child", "rel": "depends-on"},
            ]
            self._write_artifact(root / "root.md", "root", "Root", links, "# Root\n")
            self._write_artifact(root / "child.md", "child", "Child", [], "# Child\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "context",
                    "--id",
                    "root",
                    "--policy",
                    "grounding",
                    "--hops",
                    "1",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(3, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertEqual("GRAPH_INVALID", json.loads(result.stderr)["error"]["code"])

    def test_analyze_reports_missing_id_without_crashing(self):
        module = load_module()
        problems = []

        by_id, inbound, stale, flagged, orphans = module.analyze(
            [{"_path": "docs/invalid.md", "links": [], "status": "draft"}],
            problems,
        )

        self.assertEqual({}, by_id)
        self.assertEqual({}, inbound)
        self.assertEqual([], stale)
        self.assertEqual([], flagged)
        self.assertEqual([], orphans)

    def test_derive_excludes_artifacts_missing_required_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            (root / "invalid.md").write_text(
                "---\ntitle: Missing identity\ntype: doc\nstatus: draft\nlinks: []\n---\nBody\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "derive",
                    "--project",
                    "Malformed fixture",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            index_text = (root / "docs-index.js").read_text(encoding="utf-8")
            index = json.loads(
                index_text.split("window.DOCS_INDEX = ", 1)[1].rsplit(";", 1)[0]
            )
            self.assertEqual([], index["artifacts"])

    def test_derive_fails_closed_above_relationship_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            module = load_module()
            links = [
                {"to": f"target-{index}", "rel": "depends-on"}
                for index in range(module.RELATIONSHIP_LIMIT + 1)
            ]
            self._write_artifact(root / "root.md", "root", "Root", links, "Body\n")

            with self.assertRaisesRegex(module.DocsGraphError, "relationship limit"):
                module.cmd_derive(
                    SimpleNamespace(
                        root=str(root),
                        project="Fixture",
                        generator="test",
                        out=str(root / "docs-index.js"),
                    )
                )

    def test_derive_fails_closed_above_total_source_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            module = load_module()
            self._write_artifact(root / "root.md", "root", "Root", [], "Body\n")

            with mock.patch.object(module, "SOURCE_TOTAL_LIMIT", 1):
                with self.assertRaisesRegex(module.DocsGraphError, "source byte limit"):
                    module.cmd_derive(
                        SimpleNamespace(
                            root=str(root),
                            project="Fixture",
                            generator="test",
                            out=str(root / "docs-index.js"),
                        )
                    )

    def test_derive_fails_closed_above_serialized_index_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            module = load_module()
            self._write_artifact(root / "root.md", "root", "Root", [], "Body\n")

            with mock.patch.object(module, "INDEX_BYTE_LIMIT", 1):
                with self.assertRaisesRegex(module.DocsGraphError, "serialized index limit"):
                    module.cmd_derive(
                        SimpleNamespace(
                            root=str(root),
                            project="Fixture",
                            generator="test",
                            out=str(root / "docs-index.js"),
                        )
                    )

    def test_context_discards_untraversed_bodies_after_hashing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            self._write_artifact(
                root / "root.md",
                "root",
                "Root",
                [{"to": "child", "rel": "depends-on"}],
                "## Root\n\nStable root snapshot.\n",
            )
            self._write_artifact(
                root / "child.md",
                "child",
                "Child",
                [],
                "## Child\n\nStable child snapshot.\n",
            )
            self._write_artifact(
                root / "detached.md",
                "detached",
                "Detached",
                [],
                "## Detached\n\nNot in the grounding traversal.\n",
            )
            module = load_module()
            verified_open = module._open_verified_binary
            reads = []

            def counted(path, *args, **kwargs):
                resolved = Path(path)
                if resolved.suffix == ".md":
                    reads.append(resolved.stem)
                return verified_open(path, *args, **kwargs)

            with mock.patch.object(module, "_open_verified_binary", side_effect=counted):
                packet = module.cmd_context(self._context_args(root))

            self.assertEqual(2, reads.count("root"))
            self.assertEqual(2, reads.count("child"))
            self.assertEqual(1, reads.count("detached"))
            for artifact_id in ("root", "child"):
                source = module.normalized_source(
                    module._read_source_bounded(root / f"{artifact_id}.md", artifact_id)[0]
                )
                self.assertTrue(
                    any(
                        chunk["artifactId"] == artifact_id
                        and chunk["text"] in source
                        for chunk in packet["chunks"]
                    )
                )
            self.assertFalse(
                any(chunk["artifactId"] == "detached" for chunk in packet["chunks"])
            )

    def test_context_cli_emits_opt_in_phase_timings_without_changing_packet(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            self._write_artifact(
                root / "root.md",
                "root",
                "Root",
                [],
                "## Root\n\nStable root snapshot.\n",
            )

            baseline = self._run_raw(
                root,
                "--id",
                "root",
                "--policy",
                "grounding",
                "--hops",
                "2",
                "--max-bytes",
                "8192",
            )
            result = self._run_raw(
                root,
                "--id",
                "root",
                "--policy",
                "grounding",
                "--hops",
                "2",
                "--max-bytes",
                "8192",
                "--timings",
            )

        self.assertEqual(0, baseline.returncode, baseline.stderr.decode("utf-8"))
        self.assertEqual(b"", baseline.stderr)
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
        self.assertEqual(baseline.stdout, result.stdout)
        packet = json.loads(result.stdout.decode("utf-8"))
        diagnostics = json.loads(result.stderr.decode("utf-8"))
        self.assertEqual("grounding-packet/v1", packet["schemaVersion"])
        self.assertEqual("docs-context-timings/v1", diagnostics["schemaVersion"])
        self.assertEqual(
            {"scan", "traverse", "chunk", "serialize", "total"},
            set(diagnostics["phasesMilliseconds"]),
        )
        self.assertTrue(
            all(
                value >= 0
                for value in diagnostics["phasesMilliseconds"].values()
            )
        )

    def test_index_readers_close_existing_index_files(self):
        module = load_module()
        index = {
            "project": "Example",
            "artifacts": [
                {
                    "id": "root",
                    "status": "accepted",
                    "owner": "@owner",
                    "reviewBy": "2099-01-01",
                    "summary": "Test artifact.",
                }
            ],
        }
        source = "window.DOCS_INDEX = {0};".format(json.dumps(index))
        opened = mock.mock_open(read_data=source)
        artifact = {
            "id": "root",
            "status": "accepted",
            "owner": "@owner",
            "review-by": "2099-01-01",
            "summary": "Test artifact.",
        }

        with mock.patch.object(module.os.path, "exists", return_value=True), mock.patch(
            "builtins.open", opened
        ):
            project = module.project_identity("docs")
            drift = module.index_drift(
                SimpleNamespace(root="docs", out=None),
                [artifact],
            )

        self.assertEqual("Example", project)
        self.assertEqual([], drift)
        self.assertEqual(2, opened.return_value.__enter__.call_count)
        self.assertEqual(2, opened.return_value.__exit__.call_count)

    def test_context_rejects_source_changed_between_graph_hash_and_chunking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            source_path = root / "root.md"
            self._write_artifact(
                source_path,
                "root",
                "Root",
                [],
                "## Root\n\nInitial snapshot.\n",
            )
            module = load_module()
            traverse = module.traverse_context

            def mutate_after_traversal(*args, **kwargs):
                result = traverse(*args, **kwargs)
                source_path.write_text(
                    source_path.read_text(encoding="utf-8").replace(
                        "Initial snapshot.", "Mutated snapshot."
                    ),
                    encoding="utf-8",
                )
                return result

            with mock.patch.object(
                module, "traverse_context", side_effect=mutate_after_traversal
            ):
                with self.assertRaises(module.DocsGraphError) as raised:
                    module.cmd_context(self._context_args(root))

            self.assertEqual("SOURCE_CHANGED_DURING_READ", raised.exception.code)

    def test_derive_rejects_frontmatter_changed_between_metadata_and_source_reads(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            source_path = root / "root.md"
            self._write_artifact(
                source_path,
                "root",
                "Root",
                [],
                "## Root\n\nInitial snapshot.\n",
            )
            module = load_module()
            scan = module.scan

            def mutate_after_metadata(*args, **kwargs):
                result = scan(*args, **kwargs)
                source_path.write_text(
                    source_path.read_text(encoding="utf-8").replace(
                        'title: "Root"', 'title: "Changed"'
                    ),
                    encoding="utf-8",
                )
                return result

            with mock.patch.object(module, "scan", side_effect=mutate_after_metadata):
                with self.assertRaises(module.DocsGraphError) as raised:
                    module.cmd_derive(
                        SimpleNamespace(
                            root=str(root),
                            project="Snapshot",
                            generator="test",
                            out=None,
                        )
                    )

            self.assertEqual("SOURCE_CHANGED_DURING_READ", raised.exception.code)

    def test_derive_revalidates_the_complete_corpus_before_atomic_replace(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            first_path = root / "a.md"
            second_path = root / "b.md"
            output_path = root / "docs-index.js"
            self._write_artifact(first_path, "a", "A", [], "## A\n\nInitial A.\n")
            self._write_artifact(second_path, "b", "B", [], "## B\n\nInitial B.\n")
            output_path.write_text("sentinel", encoding="utf-8")
            module = load_module()
            read_source = module._read_source_bounded
            reads = []

            def mutate_first_after_second_snapshot(path, artifact_id):
                result = read_source(path, artifact_id)
                reads.append(artifact_id)
                if reads == ["a", "b"]:
                    first_path.write_text(
                        first_path.read_text(encoding="utf-8").replace(
                            "Initial A.", "Mutated A."
                        ),
                        encoding="utf-8",
                    )
                return result

            with mock.patch.object(
                module,
                "_read_source_bounded",
                side_effect=mutate_first_after_second_snapshot,
            ):
                with self.assertRaises(module.DocsGraphError) as raised:
                    module.cmd_derive(
                        SimpleNamespace(
                            root=str(root),
                            project="Snapshot",
                            generator="test",
                            out=str(output_path),
                        )
                    )

            self.assertEqual("SOURCE_CHANGED_DURING_READ", raised.exception.code)
            self.assertEqual("sentinel", output_path.read_text(encoding="utf-8"))

    def test_same_size_source_swap_is_rejected_before_bytes_are_trusted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_path = root / "source.md"
            replacement_path = root / "replacement.md"
            source_path.write_text("original", encoding="utf-8")
            replacement_path.write_text("replaced", encoding="utf-8")
            module = load_module()
            real_open = module.os.open
            swapped = False

            def swap_before_open(path, flags):
                nonlocal swapped
                if not swapped and Path(path) == source_path:
                    os.replace(replacement_path, source_path)
                    swapped = True
                return real_open(path, flags)

            with mock.patch.object(module.os, "open", side_effect=swap_before_open):
                with self.assertRaises(module.DocsGraphError) as raised:
                    module._read_source_bounded(str(source_path), "source")

            self.assertEqual("SOURCE_CHANGED_DURING_READ", raised.exception.code)

    def test_parallel_context_scan_bounds_workers_and_preserves_path_order(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            for index in range(17):
                self._write_artifact(
                    root / f"{index:02d}.md",
                    f"artifact-{index:02d}",
                    f"Artifact {index:02d}",
                    [],
                    f"## Artifact {index:02d}\n",
                )
            module = load_module()
            real_executor = module.concurrent.futures.ThreadPoolExecutor
            real_read = module._read_context_candidate
            worker_counts = []

            class CapturingExecutor:
                def __init__(self, max_workers):
                    worker_counts.append(max_workers)
                    self.inner = real_executor(max_workers=max_workers)

                def __enter__(self):
                    self.inner.__enter__()
                    return self

                def __exit__(self, *args):
                    return self.inner.__exit__(*args)

                def map(self, function, candidates):
                    return self.inner.map(function, candidates)

            def complete_out_of_order(candidate):
                relative_path = candidate[0][1]
                time.sleep((17 - int(Path(relative_path).stem)) * 0.001)
                return real_read(candidate)

            with mock.patch.object(
                module.concurrent.futures,
                "ThreadPoolExecutor",
                CapturingExecutor,
            ), mock.patch.object(
                module,
                "_read_context_candidate",
                side_effect=complete_out_of_order,
            ):
                artifacts, problems, _, _ = module.scan_context(str(root))

            self.assertEqual([], problems)
            self.assertEqual([16], worker_counts)
            self.assertEqual(
                [f"artifact-{index:02d}" for index in range(17)],
                [artifact["id"] for artifact in artifacts],
            )

    def test_python_38_syntax_floor(self):
        source = SCRIPT.read_text(encoding="utf-8")

        ast.parse(source, filename=str(SCRIPT), feature_version=(3, 8))

    def test_canonical_json_and_hash_match_independent_fixtures(self):
        module = load_module()
        fixture = json.loads(
            (REPO / "tests" / "docs_explorer" / "canonical-hash-v1.json").read_text(
                encoding="utf-8"
            )
        )

        for vector in fixture["vectors"]:
            canonical = module.canonical_json(vector["value"])
            self.assertEqual(vector["canonical"], canonical, vector["name"])
            self.assertEqual(
                vector["sha256"],
                hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                vector["name"],
            )

    def test_context_output_is_utf8_and_frontmatter_is_not_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            self._write_artifact(
                root / "root.md",
                "root",
                "Racine é",
                [],
                "## Résumé\n\nCafé et naïveté.\n",
            )

            result = self._run_raw(
                root,
                "--id",
                "root",
                "--query",
                "café",
                "--max-bytes",
                "8192",
            )

            self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
            self.assertEqual(b"", result.stderr)
            packet = json.loads(result.stdout.decode("utf-8"))
            evidence = "\n".join(chunk["text"] for chunk in packet["chunks"])
            self.assertIn("Café", evidence)
            self.assertNotIn("owner:", evidence)
            self.assertNotIn("review-by:", evidence)

    def test_oversized_unicode_line_is_split_on_utf8_boundaries(self):
        module = load_module()
        source = "## Long\n\n" + ("😀" * 40000)
        artifact = {"id": "root", "_path": "docs/root.md", "title": "Root"}

        chunks = module.markdown_chunks(artifact, source, 0, -1, [])

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            encoded = chunk["text"].encode("utf-8")
            self.assertLessEqual(len(encoded), module.CONTEXT_LIMITS["chunkBytes"])
            self.assertEqual(chunk["sha256"], hashlib.sha256(encoded).hexdigest())

    def test_request_validation_error_precedence_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            cases = [
                (["--id", "missing", "--max-bytes", "1"], 2, "BUDGET_OUT_OF_RANGE"),
                (["--id", "missing", "--policy", "unknown"], 2, "POLICY_UNSUPPORTED"),
                (["--id", "missing", "--hops", "3"], 2, "HOPS_OUT_OF_RANGE"),
                (["--id", "missing"], 2, "ROOT_NOT_FOUND"),
            ]
            for arguments, expected_exit, expected_code in cases:
                with self.subTest(code=expected_code):
                    result = self._run_raw(root, *arguments)
                    self.assertEqual(expected_exit, result.returncode)
                    self.assertEqual(b"", result.stdout)
                    self.assertEqual(
                        expected_code,
                        json.loads(result.stderr.decode("utf-8"))["error"]["code"],
                    )

    def test_resource_limits_have_exact_n_minus_one_n_n_plus_one_oracles(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            self._write_artifact(
                root / "root.md",
                "root",
                "Root",
                [{"to": "child", "rel": "depends-on"}],
                "## Root\n\nBody.\n",
            )
            self._write_artifact(
                root / "child.md", "child", "Child", [], "## Child\n\nBody.\n"
            )
            source_sizes = [
                len(path.read_bytes()) for path in (root / "root.md", root / "child.md")
            ]
            module = load_module()
            generated_chunks = sum(
                len(
                    module.markdown_chunks(
                        {"id": path.stem, "_path": f"docs/{path.name}"},
                        module.normalized_source(path.read_text(encoding="utf-8")),
                        0,
                        0,
                        [],
                    )
                )
                for path in (root / "root.md", root / "child.md")
            )
            scenarios = [
                ("artifacts", 2, "SCAN_LIMIT_EXCEEDED"),
                ("relationships", 1, "SCAN_LIMIT_EXCEEDED"),
                ("fileBytes", max(source_sizes), "SOURCE_FILE_TOO_LARGE"),
                ("admittedSourceBytes", sum(source_sizes), "SCAN_LIMIT_EXCEEDED"),
                ("generatedChunks", generated_chunks, "SCAN_LIMIT_EXCEEDED"),
            ]

            for name, boundary, expected in scenarios:
                for delta in (-1, 0, 1):
                    with self.subTest(limit=name, delta=delta):
                        current = load_module()
                        with mock.patch.dict(
                            current.CONTEXT_LIMITS, {name: boundary + delta}
                        ):
                            if delta == -1:
                                with self.assertRaises(
                                    current.DocsGraphError
                                ) as raised:
                                    current.cmd_context(self._context_args(root))
                                self.assertEqual(expected, raised.exception.code)
                            else:
                                packet = current.cmd_context(self._context_args(root))
                                self.assertEqual(2, packet["coverage"]["artifactsScanned"])
                                self.assertEqual(
                                    1, packet["coverage"]["relationshipsScanned"]
                                )

    def test_packet_envelope_accepts_exact_budget_and_rejects_one_byte_less(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            self._write_artifact(
                root / "root.md", "root", "Root", [], "## Root\n\nBody.\n"
            )
            module = load_module()
            with mock.patch.object(module, "PACKET_MIN_BYTES", 1), mock.patch.object(
                module, "markdown_chunks", return_value=[]
            ):
                packet = module.cmd_context(self._context_args(root, max_bytes=100000))
                boundary = packet["budget"]["bytesUsed"]
                while True:
                    packet = module.cmd_context(
                        self._context_args(root, max_bytes=boundary)
                    )
                    updated = packet["budget"]["bytesUsed"]
                    if updated == boundary:
                        break
                    boundary = updated
                self.assertEqual(boundary, packet["budget"]["bytesUsed"])
                accepted = module.cmd_context(
                    self._context_args(root, max_bytes=boundary + 1)
                )
                self.assertLessEqual(accepted["budget"]["bytesUsed"], boundary + 1)
                with self.assertRaises(module.DocsGraphError) as raised:
                    module.cmd_context(
                        self._context_args(root, max_bytes=boundary - 1)
                    )
            self.assertEqual("BUDGET_TOO_SMALL", raised.exception.code)

    def test_envelope_and_budget_errors_beat_generated_chunk_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            self._write_artifact(root / "root.md", "root", "Root", [], "## Root\n\nBody.\n")

            module = load_module()
            args = self._context_args(root, max_bytes=100)
            with mock.patch.object(module, "PACKET_MIN_BYTES", 1), mock.patch.dict(
                module.CONTEXT_LIMITS, {"generatedChunks": 0}
            ):
                with self.assertRaises(module.DocsGraphError) as raised:
                    module.cmd_context(args)
            self.assertEqual("BUDGET_TOO_SMALL", raised.exception.code)

            module = load_module()
            args = self._context_args(root, max_bytes=100)
            with mock.patch.object(module, "PACKET_MIN_BYTES", 1), mock.patch.object(
                module, "PACKET_MAX_BYTES", 100
            ), mock.patch.dict(module.CONTEXT_LIMITS, {"generatedChunks": 0}):
                with self.assertRaises(module.DocsGraphError) as raised:
                    module.cmd_context(args)
            self.assertEqual("ENVELOPE_TOO_LARGE", raised.exception.code)

    def test_scan_rejects_symlink_sources_without_following_them(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "linked.md"
            path.write_text("not read", encoding="utf-8")
            fake_stat = SimpleNamespace(
                st_mode=module.stat.S_IFLNK,
                st_file_attributes=0,
            )
            with mock.patch.object(module.os, "lstat", return_value=fake_stat), mock.patch(
                "builtins.open", side_effect=AssertionError("symlink should not be opened")
            ):
                artifacts, problems = module.scan(str(root), metadata_only=True)

        self.assertEqual([], artifacts)
        self.assertEqual("graph source is not a regular file", problems[0]["problem"])

    def test_scan_rejects_directory_symlink_without_traversing_outside_root(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "docs"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            self._write_artifact(
                outside / "escaped.md",
                "escaped",
                "Escaped",
                [],
                "## Escaped\n\nOutside root.\n",
            )
            link = root / "linked-directory"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"directory symlinks unavailable: {exc}")

            artifacts, problems = module.scan(str(root), metadata_only=True)

        self.assertEqual([], artifacts)
        self.assertTrue(
            any(
                problem["file"].endswith("linked-directory")
                and problem["problem"] == "graph directory escapes the approved root"
                for problem in problems
            )
        )

    def test_windows_reparse_attribute_is_treated_as_an_escape_boundary(self):
        module = load_module()
        fake_stat = SimpleNamespace(st_file_attributes=0x400)

        with mock.patch.object(module.os, "lstat", return_value=fake_stat):
            self.assertTrue(module._is_reparse_point("junction"))

    def test_atomic_append_rejects_link_destination_before_rewrite(self):
        module = load_module()
        fake_stat = SimpleNamespace(
            st_mode=module.stat.S_IFLNK,
            st_file_attributes=0,
        )

        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "health-history.jsonl"
            with mock.patch.object(module.os.path, "lexists", return_value=True), mock.patch.object(
                module.os, "stat", return_value=fake_stat
            ), mock.patch.object(
                module, "_atomic_write_text", side_effect=AssertionError("must not rewrite")
            ):
                with self.assertRaises(module.DocsGraphError) as raised:
                    module._atomic_append_text(destination, "{}\n")

        self.assertEqual("SOURCE_WRITE_REJECTED", raised.exception.code)

    def test_atomic_append_serializes_concurrent_writers_without_losing_lines(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "health-history.jsonl"
            lines = [json.dumps({"writer": index}) + "\n" for index in range(24)]

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                list(executor.map(lambda line: module._atomic_append_text(destination, line), lines))

            actual = destination.read_text(encoding="utf-8").splitlines()

        self.assertEqual(24, len(actual))
        self.assertEqual(set(range(24)), {json.loads(line)["writer"] for line in actual})

    def test_stub_rejects_malformed_link_argument(self):
        module = load_module()
        args = SimpleNamespace(
            link=["missing-relation"],
            id="stub",
            title="Stub",
            type="doc",
            status="draft",
            owner="@owner",
            tag=[],
            review_days=90,
            summary="Stub.",
            file="unused.md",
        )

        with self.assertRaisesRegex(SystemExit, "to:rel"):
            module.cmd_stub(args)

    def test_error_writer_redacts_complex_details_and_caps_output(self):
        module = load_module()
        target = SimpleNamespace(buffer=io.BytesIO())
        error = module.DocsGraphError(
            "INTERNAL_ERROR",
            "An unexpected internal error occurred.",
            {"exceptionType": "RuntimeError", "secret": {"token": "do-not-emit"}},
            1,
        )

        with mock.patch.object(module.sys, "stderr", target):
            module.write_context_error(error)

        payload = json.loads(target.buffer.getvalue().decode("utf-8"))
        self.assertEqual("RuntimeError", payload["error"]["details"]["exceptionType"])
        self.assertNotIn("secret", payload["error"]["details"])
        self.assertLessEqual(
            len(target.buffer.getvalue()), module.CONTEXT_LIMITS["stderrBytes"]
        )

    def test_context_internal_error_does_not_emit_exception_message_secrets_or_paths(self):
        module = load_module()
        stderr = SimpleNamespace(buffer=io.BytesIO())
        stdout = SimpleNamespace(buffer=io.BytesIO())
        seeded_path = r"C:\Users\private-user\repo\secret.md"
        seeded_token = "ghp_seeded-secret-token"
        seeded_user = "private-user"
        failure = RuntimeError(
            f"failed for {seeded_user} at {seeded_path} using {seeded_token}"
        )

        with mock.patch.object(module, "cmd_context", side_effect=failure), mock.patch.object(
            module.sys,
            "argv",
            ["docs-graph.py", "context", "--id", "root"],
        ), mock.patch.object(module.sys, "stderr", stderr), mock.patch.object(
            module.sys, "stdout", stdout
        ):
            exit_code = module.main()

        raw = stderr.buffer.getvalue().decode("utf-8")
        payload = json.loads(raw)
        self.assertEqual(1, exit_code)
        self.assertEqual("INTERNAL_ERROR", payload["error"]["code"])
        self.assertEqual(
            "RuntimeError", payload["error"]["details"]["exceptionType"]
        )
        self.assertNotIn(seeded_path, raw)
        self.assertNotIn(seeded_token, raw)
        self.assertNotIn(seeded_user, raw)

    def _run_context(self, root, artifact_id, max_bytes):
        result = self._run_raw(
            root,
            "--id",
            artifact_id,
            "--query",
            "retry contract",
            "--policy",
            "grounding",
            "--hops",
            "2",
            "--max-bytes",
            str(max_bytes),
        )
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
        self.assertEqual(b"", result.stderr)
        return json.loads(result.stdout.decode("utf-8"))

    def _run_raw(self, root, *arguments):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(root),
                "context",
                *arguments,
            ],
            capture_output=True,
            check=False,
        )

    def _context_args(self, root, max_bytes=8192):
        return SimpleNamespace(
            root=str(root),
            id="root",
            query="",
            policy="grounding",
            hops=2,
            max_bytes=max_bytes,
            include_changes=False,
        )

    def _write_artifact(self, path, artifact_id, title, links, body):
        link_lines = "\n".join(
            f"  - {{ to: {link['to']}, rel: {link['rel']} }}" for link in links
        )
        links_block = f"links:\n{link_lines}" if links else "links: []"
        path.write_text(
            f"""---
id: {artifact_id}
title: "{title}"
type: design
status: accepted
owner: "@owner"
tags: [test]
{links_block}
review-by: 2099-01-01
review-suggested: []
summary: >-
  Test artifact.
---

{body}""",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
