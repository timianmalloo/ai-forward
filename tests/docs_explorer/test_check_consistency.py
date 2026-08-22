import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tools" / "check-consistency.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_consistency", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_unreleased_revision_does_not_require_reference_proof(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, released="")
            findings = []
            with mock.patch.object(self.module, "ROOT", str(root)), mock.patch.object(
                self.module, "PACK", str(root / "pack")
            ):
                self.module.check_release_gate(findings)

        self.assertEqual([], findings)

    def test_released_revision_requires_reference_proof_or_deviation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, released="2026-07-10")
            findings = []
            with mock.patch.object(self.module, "ROOT", str(root)), mock.patch.object(
                self.module, "PACK", str(root / "pack")
            ):
                self.module.check_release_gate(findings)

        self.assertEqual(1, len(findings))
        self.assertIn("CLI and browser benchmark proof", findings[0])

    def test_cli_reference_proof_without_browser_proof_does_not_clear_release_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, released="2026-07-10")
            proof = root / "docs" / "proof" / "docs-context-benchmark.reference.json"
            proof.parent.mkdir(parents=True)
            proof.write_text(
                json.dumps(self._reference_proof()),
                encoding="utf-8",
            )
            findings = []
            with mock.patch.object(self.module, "ROOT", str(root)), mock.patch.object(
                self.module, "PACK", str(root / "pack")
            ):
                self.module.check_release_gate(findings)

        self.assertEqual(1, len(findings))
        self.assertIn("CLI and browser benchmark proof", findings[0])

    def test_matching_cli_and_browser_reference_proofs_clear_release_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, released="2026-07-10")
            proof_dir = root / "docs" / "proof"
            proof_dir.mkdir(parents=True)
            (proof_dir / "docs-context-benchmark.reference.json").write_text(
                json.dumps(self._reference_proof()),
                encoding="utf-8",
            )
            (proof_dir / "docs-explorer-browser-benchmark.reference.json").write_text(
                json.dumps(self._browser_reference_proof()),
                encoding="utf-8",
            )
            findings = []
            with mock.patch.object(self.module, "ROOT", str(root)), mock.patch.object(
                self.module, "PACK", str(root / "pack")
            ):
                self.module.check_release_gate(findings)

        self.assertEqual([], findings)

    def test_mismatched_reference_proof_does_not_clear_release_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, released="2026-07-10")
            proof = root / "docs" / "proof" / "docs-context-benchmark.reference.json"
            proof.parent.mkdir(parents=True)
            invalid = self._reference_proof()
            invalid["corpus"]["sha256"] = "wrong-corpus-fingerprint"
            proof.write_text(
                json.dumps(invalid),
                encoding="utf-8",
            )
            findings = []
            with mock.patch.object(self.module, "ROOT", str(root)), mock.patch.object(
                self.module, "PACK", str(root / "pack")
            ):
                self.module.check_release_gate(findings)

        self.assertEqual(1, len(findings))
        self.assertIn("CLI and browser benchmark proof", findings[0])

    def test_mismatched_browser_reference_proof_does_not_clear_release_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, released="2026-07-10")
            proof_dir = root / "docs" / "proof"
            proof_dir.mkdir(parents=True)
            (proof_dir / "docs-context-benchmark.reference.json").write_text(
                json.dumps(self._reference_proof()),
                encoding="utf-8",
            )
            invalid = self._browser_reference_proof()
            invalid["summary"]["initialSpatialP75Milliseconds"] = 501.0
            (proof_dir / "docs-explorer-browser-benchmark.reference.json").write_text(
                json.dumps(invalid),
                encoding="utf-8",
            )
            findings = []
            with mock.patch.object(self.module, "ROOT", str(root)), mock.patch.object(
                self.module, "PACK", str(root / "pack")
            ):
                self.module.check_release_gate(findings)

        self.assertEqual(1, len(findings))
        self.assertIn("CLI and browser benchmark proof", findings[0])

    def test_browser_reference_proof_without_raw_samples_does_not_clear_release_gate(self):
        proof = self._browser_reference_proof()
        del proof["samples"]

        self.assertFalse(self.module._valid_browser_reference_benchmark(proof))

    def test_contradictory_browser_samples_do_not_clear_release_gate(self):
        proof = self._browser_reference_proof()
        failing = {
            "usable2dShellMilliseconds": 5000.0,
            "selectionSearchMilliseconds": 500.0,
            "initial2dLayoutMilliseconds": 1500.0,
            "initialSpatialMilliseconds": 1500.0,
            "minimumOrbitFramesPerSecond": 10.0,
        }
        proof["samples"] = {
            "cold": [dict(failing) for _ in range(5)],
            "warm": [dict(failing) for _ in range(5)],
        }

        self.assertFalse(self.module._valid_browser_reference_benchmark(proof))

    def test_browser_reference_proof_requires_exact_sample_cardinality(self):
        proof = self._browser_reference_proof()

        for cold_count, warm_count in ((4, 5), (5, 4), (6, 5), (5, 6)):
            with self.subTest(cold=cold_count, warm=warm_count):
                mutated = json.loads(json.dumps(proof))
                mutated["samples"]["cold"] = mutated["samples"]["cold"][:cold_count]
                if cold_count > 5:
                    mutated["samples"]["cold"].append(
                        dict(mutated["samples"]["cold"][0])
                    )
                mutated["samples"]["warm"] = mutated["samples"]["warm"][:warm_count]
                if warm_count > 5:
                    mutated["samples"]["warm"].append(
                        dict(mutated["samples"]["warm"][0])
                    )
                self.assertFalse(
                    self.module._valid_browser_reference_benchmark(mutated)
                )

    def test_browser_reference_proof_rejects_non_finite_raw_metrics(self):
        proof = self._browser_reference_proof()

        for value in (float("nan"), float("inf"), float("-inf"), "not-a-number"):
            with self.subTest(value=value):
                mutated = json.loads(json.dumps(proof))
                mutated["samples"]["cold"][0]["selectionSearchMilliseconds"] = value
                self.assertFalse(
                    self.module._valid_browser_reference_benchmark(mutated)
                )

    def test_browser_reference_proof_rejects_environment_contract_drift(self):
        proof = self._browser_reference_proof()

        for field, value in (
            ("viewport", {"width": 1440, "height": 1000}),
            ("deviceScaleFactor", 2),
            ("gpuMode", "hardware"),
            ("orbitFrameWindowMilliseconds", 500),
        ):
            with self.subTest(field=field):
                mutated = json.loads(json.dumps(proof))
                mutated["environment"][field] = value
                self.assertFalse(
                    self.module._valid_browser_reference_benchmark(mutated)
                )

    def test_browser_reference_proof_rejects_rewritten_distribution_summary(self):
        proof = self._browser_reference_proof()
        proof["summary"]["distributions"]["selectionSearchMilliseconds"]["p50"] = 1.0

        self.assertFalse(self.module._valid_browser_reference_benchmark(proof))

    def test_contradictory_reference_proof_does_not_clear_release_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, released="2026-07-10")
            proof = root / "docs" / "proof" / "docs-context-benchmark.reference.json"
            proof.parent.mkdir(parents=True)
            contradictory = self._reference_proof()
            contradictory["summary"]["p75WallMilliseconds"] = 999999
            contradictory["summary"]["maxPeakWorkingSetBytes"] = 999999999
            proof.write_text(json.dumps(contradictory), encoding="utf-8")
            findings = []
            with mock.patch.object(self.module, "ROOT", str(root)), mock.patch.object(
                self.module, "PACK", str(root / "pack")
            ):
                self.module.check_release_gate(findings)

        self.assertEqual(1, len(findings))
        self.assertIn("CLI and browser benchmark proof", findings[0])

    def test_accepted_human_deviation_clears_release_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, released="2026-07-10")
            self._write_deviation(root, approved_by="@maintainer")
            findings = []
            with mock.patch.object(self.module, "ROOT", str(root)), mock.patch.object(
                self.module, "PACK", str(root / "pack")
            ):
                self.module.check_release_gate(findings)

        self.assertEqual([], findings)

    def test_automation_approvers_cannot_accept_reference_deviation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, released="2026-07-10")
            note = root / "docs" / "notes" / "docs-explorer-reference-performance-deviation.md"
            for approver in (
                "@copilot",
                "@Copilot",
                "@COPILOT",
                "@copilot-swe-agent",
                "@github-actions",
                "@dependabot",
                "@renovate",
                "@release-bot[bot]",
            ):
                with self.subTest(approver=approver):
                    self._write_deviation(root, approved_by=approver)
                    self.assertFalse(
                        self.module._accepted_reference_deviation(note, revision=17)
                    )

    def test_reference_deviation_requires_every_acceptance_field(self):
        valid = {
            "status": "accepted",
            "revision": "17",
            "decision": "accept-reference-performance-risk",
            "approved_by": "@maintainer",
        }
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, released="2026-07-10")
            note = root / "docs" / "notes" / "docs-explorer-reference-performance-deviation.md"
            for missing in valid:
                with self.subTest(missing=missing):
                    fields = valid.copy()
                    fields[missing] = ""
                    self._write_deviation(root, **fields)
                    self.assertFalse(
                        self.module._accepted_reference_deviation(note, revision=17)
                    )

    def test_reference_deviation_rejects_wrong_revision(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, released="2026-07-10")
            note = self._write_deviation(root, revision="16")

            self.assertFalse(self.module._accepted_reference_deviation(note, revision=17))

    @staticmethod
    def _write_deviation(
        root,
        status="accepted",
        revision="17",
        decision="accept-reference-performance-risk",
        approved_by="@maintainer",
    ):
        note = root / "docs" / "notes" / "docs-explorer-reference-performance-deviation.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(
            "---\n"
            f"status: {status}\n"
            f"revision: '{revision}'\n"
            f"decision: {decision}\n"
            f"approved-by: '{approved_by}'\n"
            "---\n",
            encoding="utf-8",
        )
        return note

    @staticmethod
    def _root(temp, released):
        root = Path(temp)
        install = root / "pack" / "adapters" / "INSTALL.md"
        install.parent.mkdir(parents=True)
        install.write_text(
            f"---\nrevision: 17\nreleased: '{released}'\n---\n",
            encoding="utf-8",
        )
        return root

    @staticmethod
    def _reference_proof():
        return {
            "schemaVersion": "docs-context-benchmark/v1",
            "passed": True,
            "localThresholdsPassed": True,
            "referenceBudgetProved": True,
            "environment": {
                "architecture": "X64",
                "windowsCaption": "Microsoft Windows Server 2022 Datacenter",
                "logicalProcessors": 4,
                "python": "Python 3.11.9",
                "referenceEnvironmentMatched": True,
                "azureReferenceMetadata": {
                    "vmSize": "Standard_D4s_v5",
                    "offer": "WindowsServer",
                    "osType": "Windows",
                },
            },
            "corpus": {
                "artifacts": 2000,
                "relationships": 20000,
                "admittedSourceBytes": 64 * 1024 * 1024,
                "seed": 20260710,
                "sha256": "f055e195583abdd97d673032a5e78ad89155f1adff1a8c4d324bddf8ca0a43b1",
            },
            "thresholds": {
                "p75WallMilliseconds": 2000.0,
                "peakWorkingSetBytes": 256 * 1024 * 1024,
            },
            "summary": {
                "p75WallMilliseconds": 1999.0,
                "maxPeakWorkingSetBytes": 128 * 1024 * 1024,
            },
        }

    @staticmethod
    def _browser_reference_proof():
        return {
            "schemaVersion": "docs-explorer-browser-benchmark/v1",
            "passed": True,
            "localThresholdsPassed": True,
            "referenceBudgetProved": True,
            "environment": {
                "architecture": "X64",
                "windowsCaption": "Microsoft Windows Server 2022 Datacenter",
                "logicalProcessors": 4,
                "playwright": "1.61.1",
                "browserName": "chromium",
                "chromiumBuild": "145.0.7632.6",
                "headless": True,
                "gpuMode": "swiftshader",
                "launchFlags": [
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-extensions",
                    "--disable-renderer-backgrounding",
                    "--use-angle=swiftshader",
                ],
                "viewport": {"width": 1366, "height": 768},
                "deviceScaleFactor": 1,
                "cpuSlowdown": 4,
                "orbitFrameWindowMilliseconds": 1000,
                "referenceEnvironmentMatched": True,
                "azureReferenceMetadata": {
                    "vmSize": "Standard_D4s_v5",
                    "offer": "WindowsServer",
                    "osType": "Windows",
                },
            },
            "corpus": {
                "artifacts": 500,
                "relationships": 1000,
                "surfaces": 100,
                "seed": 20260710,
                "sha256": "f4b34a29d2f836957f7fe24d0424444ac515881b6618cdfdd759a302ccb3cdef",
            },
            "runs": {"cold": 5, "warm": 5},
            "thresholds": {
                "usable2dShellP75Milliseconds": 2000.0,
                "selectionSearchP75Milliseconds": 100.0,
                "initial2dLayoutP75Milliseconds": 500.0,
                "initialSpatialP75Milliseconds": 500.0,
                "minimumOrbitFramesPerSecond": 30.0,
            },
            "summary": {
                "usable2dShellP75Milliseconds": 1500.0,
                "selectionSearchP75Milliseconds": 80.0,
                "initial2dLayoutP75Milliseconds": 400.0,
                "initialSpatialP75Milliseconds": 450.0,
                "minimumOrbitFramesPerSecond": 45.0,
                "distributions": {
                    "usable2dShellMilliseconds": {
                        "p50": 1500.0,
                        "p75": 1500.0,
                        "max": 1500.0,
                    },
                    "selectionSearchMilliseconds": {
                        "p50": 80.0,
                        "p75": 80.0,
                        "max": 80.0,
                    },
                    "initial2dLayoutMilliseconds": {
                        "p50": 400.0,
                        "p75": 400.0,
                        "max": 400.0,
                    },
                    "initialSpatialMilliseconds": {
                        "p50": 450.0,
                        "p75": 450.0,
                        "max": 450.0,
                    },
                    "heapDeltaBytes": {
                        "p50": 1024.0,
                        "p75": 1024.0,
                        "max": 1024.0,
                    },
                },
            },
            "samples": {
                "cold": [
                    {
                        "usable2dShellMilliseconds": 1500.0,
                        "selectionSearchMilliseconds": 80.0,
                        "initial2dLayoutMilliseconds": 400.0,
                        "initialSpatialMilliseconds": 450.0,
                        "minimumOrbitFramesPerSecond": 45.0,
                        "heapDeltaBytes": 1024.0,
                        "cacheMode": "cold",
                    }
                    for _ in range(5)
                ],
                "warm": [
                    {
                        "usable2dShellMilliseconds": 1500.0,
                        "selectionSearchMilliseconds": 80.0,
                        "initial2dLayoutMilliseconds": 400.0,
                        "initialSpatialMilliseconds": 450.0,
                        "minimumOrbitFramesPerSecond": 45.0,
                        "heapDeltaBytes": 1024.0,
                        "cacheMode": "warm",
                    }
                    for _ in range(5)
                ],
            },
        }



class DeployedAgentParityTests(unittest.TestCase):
    """FR-032. The source counts matched while `.github/agents` shipped 11 of 23 personas for
    twelve revisions, because every check counted SOURCES. These assert the DEPLOYED surfaces."""

    def setUp(self):
        self.module = load_module()

    def _root(self, temp, claude=12, copilot=11, deployed_claude=23, deployed_copilot=23,
              copilot_tools=False):
        root = Path(temp)
        for n in range(claude):
            d = root / "pack" / "adapters" / "claude-code" / "agents"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"peer{n}.md").write_text("---\nname: peer\ntools: [read]\n---\nx\n", encoding="utf-8")
        for n in range(copilot):
            d = root / "pack" / "adapters" / "copilot" / "agents"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"adv{n}_agent.md").write_text("---\nname: adv\n---\nx\n", encoding="utf-8")
        for n in range(deployed_claude):
            d = root / ".claude" / "agents"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"a{n}.md").write_text("---\nname: a\n---\nx\n", encoding="utf-8")
        for n in range(deployed_copilot):
            d = root / ".github" / "agents"
            d.mkdir(parents=True, exist_ok=True)
            body = "---\nname: a\n" + ("tools: [read]\n" if copilot_tools else "") + "---\nx\n"
            (d / f"a{n}.agent.md").write_text(body, encoding="utf-8")
        return root

    def _run(self, root):
        findings = []
        truth = {"cc_agents": ["p%d" % n for n in range(12)],
                 "cop_agents": ["a%d" % n for n in range(11)]}
        with mock.patch.object(self.module, "ROOT", str(root)), mock.patch.object(
            self.module, "PACK", str(root / "pack")
        ):
            self.module.check_deployed_agent_parity(truth, findings)
        return findings

    def test_matched_surfaces_are_clean(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(self._run(self._root(temp)), [])

    def test_missing_copilot_agent_is_reported(self):
        """The exact defect FR-032 fixed: Copilot short of the source count."""
        with tempfile.TemporaryDirectory() as temp:
            findings = self._run(self._root(temp, deployed_copilot=11))
            self.assertTrue(findings, "a 12-persona shortfall on the Copilot surface must fail")
            self.assertTrue(any(".github/agents" in f for f in findings), findings)

    def test_missing_claude_agent_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            findings = self._run(self._root(temp, deployed_claude=22))
            self.assertTrue(findings)

    def test_leaked_tools_line_on_copilot_surface_is_reported(self):
        """INSTALL requires the `tools:` line be stripped at the Copilot boundary."""
        with tempfile.TemporaryDirectory() as temp:
            findings = self._run(self._root(temp, copilot_tools=True))
            self.assertTrue(findings, "a leaked tools: line must fail")
            self.assertTrue(any("tools:" in f for f in findings), findings)


class DirectiveRangeTests(unittest.TestCase):
    """FR-035. `S1-S18` was cited against a standard defining S10, in ~30 files."""

    def setUp(self):
        self.module = load_module()

    def _root(self, temp, highest=10, cited=10):
        root = Path(temp)
        k = root / "pack" / "knowledge"
        k.mkdir(parents=True, exist_ok=True)
        body = "\n".join(f"**S{n} \u2014 directive {n}.** text" for n in range(1, highest + 1))
        (k / "specification-standards.md").write_text(body, encoding="utf-8")
        c = root / "pack" / "commands" / "specify"
        c.mkdir(parents=True, exist_ok=True)
        (c / "SKILL.md").write_text(
            f"Authority: specification-standards.md (S1\u2013S{cited}).\n", encoding="utf-8")
        return root

    def _run(self, root):
        findings = []
        with mock.patch.object(self.module, "ROOT", str(root)), mock.patch.object(
            self.module, "PACK", str(root / "pack")
        ):
            self.module.check_directive_ranges(findings)
        return findings

    def test_accurate_range_is_clean(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(self._run(self._root(temp, highest=10, cited=10)), [])

    def test_citation_that_outruns_the_standard_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            findings = self._run(self._root(temp, highest=10, cited=18))
            self.assertTrue(findings, "S1-S18 against an S10 standard must fail")
            self.assertIn("S10", findings[0])

    def test_shorter_subrange_is_legitimate_and_not_flagged(self):
        """`CI1-CI6` against a CI12 standard is a deliberate sub-range, not a defect."""
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(self._run(self._root(temp, highest=10, cited=6)), [])

class ProofCoverageTests(unittest.TestCase):
    """FR-049 / class RIG-C, fourth occurrence. FR-046 raised 'a deployed control with no
    test' and only the named instance was fixed; the class was never swept, so five scripts
    and three skills shipped unproven — including the two whose defects propagate across the
    whole fleet. This tests the CONTROL, because a control with no test is exactly the thing
    it exists to forbid.

    Two of these are regression guards for false verdicts caught while building it: a prose
    mention must not certify a script, and a `.js` require must not be missed."""

    def setUp(self):
        self.module = load_module()

    def _root(self, temp, scripts=(), tests=(), cases=(), skills=()):
        root = Path(temp)
        (root / "pack" / "scripts").mkdir(parents=True)
        (root / "pack" / "evals" / "cases").mkdir(parents=True)
        (root / "tests").mkdir()
        for name in scripts:
            (root / "pack" / "scripts" / name).write_text("# script\n", encoding="utf-8")
        for name, body in tests:
            (root / "tests" / name).write_text(body, encoding="utf-8")
        for name, skill in cases:
            (root / "pack" / "evals" / "cases" / name).write_text(
                json.dumps({"skill": skill, "id": name[:-5], "prompt": "p", "assertions": []}),
                encoding="utf-8")
        for name in skills:
            (root / "pack" / "commands" / name).mkdir(parents=True)
            (root / "pack" / "commands" / name / "SKILL.md").write_text("# s\n", encoding="utf-8")
        return root

    def _run(self, root, truth):
        findings = []
        with mock.patch.object(self.module, "ROOT", str(root)), \
             mock.patch.object(self.module, "PACK", str(root / "pack")):
            self.module.check_proof_coverage(truth, findings)
        return findings

    def test_an_untested_script_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, scripts=["lonely.py"])
            findings = self._run(root, {"scripts": ["lonely.py"], "skills": []})
            self.assertEqual(1, len(findings), findings)
            self.assertIn("lonely", findings[0])

    def test_a_referenced_script_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, scripts=["covered.py"],
                              tests=[("test_x.py", 'SCRIPT = "covered.py"\n')])
            self.assertEqual([], self._run(root, {"scripts": ["covered.py"], "skills": []}))

    def test_a_prose_mention_does_not_count_as_proof(self):
        """The false negative that nearly shipped: `dream` was certified because the word
        appears in an unrelated docstring. A gate satisfiable by prose is not a gate."""
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(
                temp, scripts=["dream.py"],
                tests=[("test_x.py", '"""The corpus /dream consolidates over."""\n')])
            findings = self._run(root, {"scripts": ["dream.py"], "skills": []})
            self.assertEqual(1, len(findings),
                             "a comment mentioning the name must not certify the script")

    def test_a_javascript_require_counts_as_proof(self):
        """The false positive that nearly shipped: hard-coding `.py` reported a genuinely
        tested `.js` module as unproven. A gate that cries wolf gets allowlisted into
        silence — the same failure wearing a hat."""
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(
                temp, scripts=["core.js"],
                tests=[("core.test.js", 'const c = require("../../pack/scripts/core.js");\n')])
            self.assertEqual([], self._run(root, {"scripts": ["core.js"], "skills": []}))

    def test_a_skill_without_an_eval_case_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, skills=["orphan"])
            findings = self._run(root, {"scripts": [], "skills": ["orphan"]})
            self.assertEqual(1, len(findings), findings)
            self.assertIn("orphan", findings[0])

    def test_a_skill_with_an_eval_case_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, skills=["good"], cases=[("good-01.json", "good")])
            self.assertEqual([], self._run(root, {"scripts": [], "skills": ["good"]}))

    def test_coverage_is_derived_from_the_case_body_not_its_filename(self):
        """A case filename can disagree with the skill it exercises (ui-craft-detection-01
        declares skill `ui-design`). Deriving from the declared field is the robust read."""
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, skills=["real"], cases=[("unrelated-name.json", "real")])
            self.assertEqual([], self._run(root, {"scripts": [], "skills": ["real"]}))

    def test_a_malformed_eval_case_is_reported_rather_than_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, skills=["s"], cases=[("s-01.json", "s")])
            (root / "pack" / "evals" / "cases" / "broken.json").write_text("{oops", encoding="utf-8")
            findings = self._run(root, {"scripts": [], "skills": ["s"]})
            self.assertTrue(any("broken.json" in f for f in findings), findings)

    def test_the_lists_are_derived_so_a_new_script_cannot_ship_unproven(self):
        """The CTRL-D lesson: a hand-maintained list IS the blind spot. Adding a script must
        be noticed by the gate without anyone editing the gate."""
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp, scripts=["a.py", "brand-new.py"],
                              tests=[("test_a.py", 'S = "a.py"\n')])
            findings = self._run(root, {"scripts": ["a.py", "brand-new.py"], "skills": []})
            self.assertTrue(any("brand-new" in f for f in findings), findings)


if __name__ == "__main__":
    unittest.main()
