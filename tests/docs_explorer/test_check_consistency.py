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


if __name__ == "__main__":
    unittest.main()
