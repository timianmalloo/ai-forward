import json
import os
import shutil
import subprocess
import sys
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HARNESS = os.path.join(ROOT, "tests", "docs_explorer", "benchmark_docs_context.ps1")
GENERATOR = os.path.join(ROOT, "tests", "docs_explorer", "generate_benchmark_corpus.py")


@unittest.skipUnless(os.name == "nt" and shutil.which("pwsh"), "PowerShell watchdog test requires Windows")
class BenchmarkHarnessTests(unittest.TestCase):
    def test_percentile_uses_nearest_rank_boundaries(self):
        result = self._run_imported(
            "$values = [double[]](1..10); "
            "@{p50=(Get-Percentile -Values $values -Percentile 0.50); "
            "p75=(Get-Percentile -Values $values -Percentile 0.75); "
            "p100=(Get-Percentile -Values $values -Percentile 1.0)} "
            "| ConvertTo-Json -Compress"
        )

        self.assertEqual({"p50": 5.0, "p75": 8.0, "p100": 10.0}, result)

    def test_reference_environment_requires_exact_host_and_azure_metadata(self):
        result = self._run_imported(
            "$azure = [pscustomobject]@{vmSize='Standard_D4s_v5'; "
            "offer='WindowsServer'; osType='Windows'}; "
            "$candidate = Test-ReferenceHostCandidate "
            "-PythonVersion 'Python 3.11.9' -ProcessorCount 4 "
            "-Architecture 'X64' -WindowsCaption 'Microsoft Windows Server 2022 Datacenter'; "
            "$wrongPython = Test-ReferenceHostCandidate "
            "-PythonVersion 'Python 3.12.0' -ProcessorCount 4 "
            "-Architecture 'X64' -WindowsCaption 'Microsoft Windows Server 2022 Datacenter'; "
            "$matched = Test-ReferenceEnvironmentMatch -HostCandidate $candidate -AzureMetadata $azure; "
            "$wrongVm = Test-ReferenceEnvironmentMatch -HostCandidate $candidate "
            "-AzureMetadata ([pscustomobject]@{vmSize='Standard_D2s_v5'; offer='WindowsServer'; osType='Windows'}); "
            "@{candidate=$candidate; wrongPython=$wrongPython; matched=$matched; wrongVm=$wrongVm} "
            "| ConvertTo-Json -Compress"
        )

        self.assertEqual(
            {
                "candidate": True,
                "wrongPython": False,
                "matched": True,
                "wrongVm": False,
            },
            result,
        )

    def test_context_timing_diagnostics_are_validated_and_summarized(self):
        result = self._run_imported(
            "$timings = ConvertFrom-ContextTimings -Json "
            "'{\"schemaVersion\":\"docs-context-timings/v1\","
            "\"phasesMilliseconds\":{\"scan\":10,\"traverse\":2,\"chunk\":3,"
            "\"serialize\":4,\"total\":20}}'; "
            "$runs = @("
            "[pscustomobject]@{phasesMilliseconds=$timings},"
            "[pscustomobject]@{phasesMilliseconds=[pscustomobject]@{"
            "scan=30;traverse=4;chunk=5;serialize=8;total=50}}"
            "); "
            "$summary = Get-PhaseSummary -Runs $runs; "
            "@{scan=$summary.scan; total=$summary.total} | ConvertTo-Json -Depth 4 -Compress"
        )

        self.assertEqual({"p50": 10.0, "p75": 30.0, "max": 30.0}, result["scan"])
        self.assertEqual({"p50": 20.0, "p75": 50.0, "max": 50.0}, result["total"])

    def test_watchdog_fixture_timeout_kills_tree_without_output(self):
        completed = subprocess.run(
            [
                "pwsh",
                "-NoProfile",
                "-File",
                HARNESS,
                "-SelfTest",
                "-WatchdogSeconds",
                "0.5",
                "-Python",
                sys.executable,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["passed"])
        self.assertTrue(result["timedOut"])
        self.assertEqual(result["stdoutBytes"], 0)
        self.assertEqual(result["stderrBytes"], 0)
        self.assertEqual(result["survivingPids"], [])

    def test_corpus_seed_changes_the_deterministic_fixture(self):
        import tempfile

        with tempfile.TemporaryDirectory() as workspace:
            hashes = []
            for seed in (7, 11):
                corpus = os.path.join(workspace, "corpus-{0}".format(seed))
                completed = subprocess.run(
                    [
                        sys.executable,
                        GENERATOR,
                        "--root",
                        corpus,
                        "--artifacts",
                        "20",
                        "--relationships",
                        "200",
                        "--bytes",
                        str(2 * 1024 * 1024),
                        "--seed",
                        str(seed),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                hashes.append(json.loads(completed.stdout)["sha256"])

        self.assertNotEqual(hashes[0], hashes[1])

    def _run_imported(self, expression):
        command = ". '{0}' -ImportOnly; {1}".format(
            HARNESS.replace("'", "''"),
            expression,
        )
        completed = subprocess.run(
            ["pwsh", "-NoProfile", "-Command", command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)


if __name__ == "__main__":
    unittest.main()
