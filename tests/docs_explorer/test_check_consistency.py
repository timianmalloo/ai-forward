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
        self.assertIn("without pinned reference benchmark proof", findings[0])

    def test_matching_reference_proof_clears_release_gate(self):
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
        self.assertIn("without pinned reference benchmark proof", findings[0])

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
        self.assertIn("without pinned reference benchmark proof", findings[0])

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


if __name__ == "__main__":
    unittest.main()
