[CmdletBinding()]
param(
    [ValidateRange(1, 100)]
    [int]$Iterations = 10,

    [ValidateRange(0.05, 60)]
    [double]$WatchdogSeconds = 10,

    [string]$Python = "python",

    [string]$OutputPath,

    [switch]$SelfTest,

    [switch]$ImportOnly,

    [switch]$KeepCorpus
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DocsGraph = Join-Path $RepositoryRoot "pack\scripts\docs-graph.py"
$CorpusGenerator = Join-Path $PSScriptRoot "generate_benchmark_corpus.py"
$WatchdogFixture = Join-Path $PSScriptRoot "watchdog_fixture.py"
$TargetWallMilliseconds = 2000.0
$TargetPeakBytes = 256MB
$StandardOutputLimit = 2MB
$StandardErrorLimit = 256KB

Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

public static class BoundedStreamReader
{
    public static async Task<byte[]> ReadAsync(Stream stream, int limit, CancellationToken token)
    {
        using var output = new MemoryStream();
        var buffer = new byte[8192];
        while (true)
        {
            var count = await stream.ReadAsync(buffer, 0, buffer.Length, token).ConfigureAwait(false);
            if (count == 0)
            {
                return output.ToArray();
            }
            if (output.Length + count > limit)
            {
                throw new InvalidDataException("PROCESS_OUTPUT_LIMIT_EXCEEDED");
            }
            output.Write(buffer, 0, count);
        }
    }
}
'@

function Stop-ExactProcessTree {
    param(
        [Parameter(Mandatory)]
        [System.Diagnostics.Process]$Process
    )

    if ($Process.HasExited) {
        return
    }
    $Process.Kill($true)
    if (-not $Process.WaitForExit(10000)) {
        throw "PROCESS_CLEANUP_FAILED: process tree did not exit within 10 seconds"
    }
}

function Invoke-MeasuredProcess {
    param(
        [Parameter(Mandatory)]
        [string]$FileName,

        [Parameter(Mandatory)]
        [string[]]$ArgumentList,

        [Parameter(Mandatory)]
        [double]$TimeoutSeconds,

        [string]$ReadyFilePath
    )

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $FileName
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    foreach ($argument in $ArgumentList) {
        [void]$startInfo.ArgumentList.Add($argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    if (-not $process.Start()) {
        throw "PROCESS_START_FAILED: $FileName"
    }
    $stdoutTask = [BoundedStreamReader]::ReadAsync(
        $process.StandardOutput.BaseStream,
        $StandardOutputLimit,
        [Threading.CancellationToken]::None
    )
    $stderrTask = [BoundedStreamReader]::ReadAsync(
        $process.StandardError.BaseStream,
        $StandardErrorLimit,
        [Threading.CancellationToken]::None
    )
    if ($ReadyFilePath) {
        # Readiness is setup, not part of the measured watchdog window.
        $readyDeadline = [DateTime]::UtcNow.AddSeconds(10)
        $ready = $false
        while (-not $ready -and [DateTime]::UtcNow -lt $readyDeadline) {
            if ($process.WaitForExit(10)) {
                throw "PROCESS_READY_FAILED: process exited before publishing readiness"
            }
            if (Test-Path $ReadyFilePath) {
                try {
                    $readyPids = Get-Content -Raw $ReadyFilePath | ConvertFrom-Json
                    $ready = [int]$readyPids.parent -gt 0 -and
                        [int]$readyPids.child -gt 0 -and
                        [int]$readyPids.parent -ne [int]$readyPids.child
                }
                catch {
                    $ready = $false
                }
            }
        }
        if (-not $ready) {
            Stop-ExactProcessTree -Process $process
            throw "PROCESS_READY_TIMEOUT: process did not publish distinct parent and child PIDs"
        }
        $stopwatch.Restart()
    }
    $peakWorkingSet = 0L
    $timedOut = $false
    try {
        while (-not $process.WaitForExit(10)) {
            if ($stdoutTask.IsFaulted -or $stderrTask.IsFaulted) {
                Stop-ExactProcessTree -Process $process
                break
            }
            $process.Refresh()
            $peakWorkingSet = [Math]::Max($peakWorkingSet, $process.PeakWorkingSet64)
            if ($stopwatch.Elapsed.TotalSeconds -ge $TimeoutSeconds) {
                $timedOut = $true
                Stop-ExactProcessTree -Process $process
                break
            }
        }
        $process.Refresh()
        $peakWorkingSet = [Math]::Max($peakWorkingSet, $process.PeakWorkingSet64)
    }
    finally {
        if (-not $process.HasExited) {
            Stop-ExactProcessTree -Process $process
        }
        $stopwatch.Stop()
    }

    $stdoutBytes = $stdoutTask.GetAwaiter().GetResult()
    $stderrBytes = $stderrTask.GetAwaiter().GetResult()
    $stdout = [Text.Encoding]::UTF8.GetString($stdoutBytes)
    $stderr = [Text.Encoding]::UTF8.GetString($stderrBytes)
    [pscustomobject]@{
        ExitCode = if ($timedOut) { $null } else { $process.ExitCode }
        TimedOut = $timedOut
        WallMilliseconds = $stopwatch.Elapsed.TotalMilliseconds
        PeakWorkingSetBytes = $peakWorkingSet
        Stdout = $stdout
        Stderr = $stderr
        StdoutBytes = $stdoutBytes.Length
        StderrBytes = $stderrBytes.Length
    }
}

function Get-Percentile {
    param(
        [Parameter(Mandatory)]
        [double[]]$Values,

        [Parameter(Mandatory)]
        [double]$Percentile
    )

    $ordered = @($Values | Sort-Object)
    $index = [Math]::Max(0, [Math]::Ceiling($Percentile * $ordered.Count) - 1)
    return [double]$ordered[$index]
}

function ConvertFrom-ContextTimings {
    param(
        [Parameter(Mandatory)]
        [string]$Json
    )

    $diagnostics = $Json | ConvertFrom-Json
    if ($diagnostics.schemaVersion -ne "docs-context-timings/v1") {
        throw "BENCHMARK_TIMINGS_INVALID: unsupported diagnostics schema"
    }
    foreach ($phase in @("scan", "traverse", "chunk", "serialize", "total")) {
        if ($null -eq $diagnostics.phasesMilliseconds.$phase) {
            throw "BENCHMARK_TIMINGS_INVALID: missing phase '$phase'"
        }
    }
    return $diagnostics.phasesMilliseconds
}

function Get-PhaseSummary {
    param(
        [Parameter(Mandatory)]
        [object[]]$Runs
    )

    $summary = [ordered]@{}
    foreach ($phase in @("scan", "traverse", "chunk", "serialize", "total")) {
        $values = [double[]]@(
            $Runs | ForEach-Object { $_.phasesMilliseconds.$phase }
        )
        $summary[$phase] = [ordered]@{
            p50 = [Math]::Round((Get-Percentile -Values $values -Percentile 0.50), 3)
            p75 = [Math]::Round((Get-Percentile -Values $values -Percentile 0.75), 3)
            max = [Math]::Round([double](($values | Measure-Object -Maximum).Maximum), 3)
        }
    }
    return $summary
}

function Test-ReferenceHostCandidate {
    param(
        [Parameter(Mandatory)]
        [string]$PythonVersion,

        [Parameter(Mandatory)]
        [int]$ProcessorCount,

        [Parameter(Mandatory)]
        [string]$Architecture,

        [Parameter(Mandatory)]
        [string]$WindowsCaption
    )

    return (
        $PythonVersion -eq "Python 3.11.9" -and
        $ProcessorCount -eq 4 -and
        $Architecture -eq "X64" -and
        $WindowsCaption -match "Windows Server 2022"
    )
}

function Test-ReferenceEnvironmentMatch {
    param(
        [Parameter(Mandatory)]
        [bool]$HostCandidate,

        [AllowNull()]
        [object]$AzureMetadata
    )

    return (
        $HostCandidate -and
        $null -ne $AzureMetadata -and
        $AzureMetadata.vmSize -eq "Standard_D4s_v5" -and
        $AzureMetadata.offer -eq "WindowsServer" -and
        $AzureMetadata.osType -eq "Windows"
    )
}

function Write-Result {
    param(
        [Parameter(Mandatory)]
        [object]$Result
    )

    $json = $Result | ConvertTo-Json -Depth 12 -Compress
    if ($OutputPath) {
        $parent = Split-Path -Parent $OutputPath
        if ($parent) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        [IO.File]::WriteAllText($OutputPath, $json + [Environment]::NewLine)
    }
    $json
}

if ($ImportOnly) {
    return
}

if ($SelfTest) {
    $pidFile = Join-Path ([IO.Path]::GetTempPath()) ("docs-context-watchdog-{0}.json" -f [guid]::NewGuid())
    try {
        $result = Invoke-MeasuredProcess -FileName $Python -ArgumentList @(
            $WatchdogFixture,
            "--pid-file",
            $pidFile
        ) -TimeoutSeconds $WatchdogSeconds -ReadyFilePath $pidFile
        $pids = if (Test-Path $pidFile) {
            Get-Content -Raw $pidFile | ConvertFrom-Json
        } else {
            $null
        }
        $survivors = @()
        if ($pids) {
            foreach ($processId in @($pids.parent, $pids.child)) {
                if (Get-Process -Id $processId -ErrorAction SilentlyContinue) {
                    $survivors += $processId
                }
            }
        }
        $validPids = $pids -and
            [int]$pids.parent -gt 0 -and
            [int]$pids.child -gt 0 -and
            [int]$pids.parent -ne [int]$pids.child
        $passed = $validPids -and
            $result.TimedOut -and
            $result.StdoutBytes -eq 0 -and
            $result.StderrBytes -eq 0 -and
            $survivors.Count -eq 0
        Write-Result ([ordered]@{
            schemaVersion = "docs-context-watchdog/v1"
            passed = $passed
            watchdogSeconds = $WatchdogSeconds
            timedOut = $result.TimedOut
            stdoutBytes = $result.StdoutBytes
            stderrBytes = $result.StderrBytes
            survivingPids = $survivors
            wallMilliseconds = [Math]::Round($result.WallMilliseconds, 3)
        })
        if (-not $passed) {
            exit 1
        }
        exit 0
    }
    finally {
        Remove-Item -Force -ErrorAction SilentlyContinue $pidFile
    }
}

$corpusRoot = Join-Path ([IO.Path]::GetTempPath()) ("docs-context-corpus-{0}" -f [guid]::NewGuid())
try {
    $generation = Invoke-MeasuredProcess -FileName $Python -ArgumentList @(
        $CorpusGenerator,
        "--root",
        $corpusRoot,
        "--seed",
        "20260710"
    ) -TimeoutSeconds $WatchdogSeconds
    if ($generation.TimedOut -or $generation.ExitCode -ne 0) {
        throw "CORPUS_GENERATION_FAILED: $($generation.Stderr)"
    }
    $manifest = $generation.Stdout | ConvertFrom-Json
    $commandArguments = @(
        $DocsGraph,
        "--root",
        $corpusRoot,
        "context",
        "--id",
        $manifest.rootId,
        "--policy",
        "grounding",
        "--hops",
        "2",
        "--query",
        "grounding project memory",
        "--max-bytes",
        "1048576",
        "--timings"
    )

    $warmup = Invoke-MeasuredProcess -FileName $Python -ArgumentList $commandArguments -TimeoutSeconds $WatchdogSeconds
    if ($warmup.TimedOut -or $warmup.ExitCode -ne 0) {
        throw "BENCHMARK_WARMUP_FAILED: $($warmup.Stderr)"
    }
    $warmupTimings = ConvertFrom-ContextTimings -Json $warmup.Stderr
    $coldStart = [ordered]@{
        wallMilliseconds = [Math]::Round($warmup.WallMilliseconds, 3)
        peakWorkingSetBytes = $warmup.PeakWorkingSetBytes
        packetBytes = $warmup.StdoutBytes
        phasesMilliseconds = $warmupTimings
    }

    $runs = @()
    for ($iteration = 1; $iteration -le $Iterations; $iteration++) {
        $measurement = Invoke-MeasuredProcess -FileName $Python -ArgumentList $commandArguments -TimeoutSeconds $WatchdogSeconds
        if ($measurement.TimedOut) {
            throw "BENCHMARK_TIMEOUT: iteration $iteration exceeded $WatchdogSeconds seconds"
        }
        if ($measurement.ExitCode -ne 0) {
            throw "BENCHMARK_COMMAND_FAILED: iteration $iteration exited $($measurement.ExitCode): $($measurement.Stderr)"
        }
        $packet = $measurement.Stdout | ConvertFrom-Json
        $timings = ConvertFrom-ContextTimings -Json $measurement.Stderr
        $runs += [pscustomobject]@{
            iteration = $iteration
            wallMilliseconds = [Math]::Round($measurement.WallMilliseconds, 3)
            peakWorkingSetBytes = $measurement.PeakWorkingSetBytes
            packetBytes = $measurement.StdoutBytes
            phasesMilliseconds = $timings
            visitedNodes = 1 + @($packet.paths).Count
            visitedEdges = @($packet.paths).Count
            chunksIncluded = $packet.budget.chunksIncluded
            chunksOmitted = $packet.budget.omittedChunkCount
        }
    }

    $walls = [double[]]@($runs | ForEach-Object { $_.wallMilliseconds })
    $peak = [long](($runs | Measure-Object -Property peakWorkingSetBytes -Maximum).Maximum)
    $p50 = Get-Percentile -Values $walls -Percentile 0.50
    $p75 = Get-Percentile -Values $walls -Percentile 0.75
    $maximum = [double](($walls | Measure-Object -Maximum).Maximum)
    $pythonVersion = (& $Python --version 2>&1 | Out-String).Trim()
    $windowsCaption = ""
    $cpu = if ($IsWindows) {
        $windowsCaption = (Get-CimInstance Win32_OperatingSystem | Select-Object -First 1 -ExpandProperty Caption).Trim()
        (Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name).Trim()
    } else {
        [System.Runtime.InteropServices.RuntimeInformation]::OSDescription
    }
    $localThresholdsPassed = $p75 -le $TargetWallMilliseconds -and $peak -le $TargetPeakBytes
    $referenceHostCandidate = Test-ReferenceHostCandidate `
        -PythonVersion $pythonVersion `
        -ProcessorCount ([Environment]::ProcessorCount) `
        -Architecture ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()) `
        -WindowsCaption $windowsCaption
    $azureMetadata = $null
    if ($referenceHostCandidate) {
        try {
            $instanceMetadata = Invoke-RestMethod `
                -Uri "http://169.254.169.254/metadata/instance?api-version=2021-02-01" `
                -Headers @{ Metadata = "true" } `
                -TimeoutSec 2
            $azureMetadata = [ordered]@{
                vmSize = [string]$instanceMetadata.compute.vmSize
                offer = [string]$instanceMetadata.compute.offer
                sku = [string]$instanceMetadata.compute.sku
                osType = [string]$instanceMetadata.compute.osType
            }
        } catch {
            $azureMetadata = $null
        }
    }
    $referenceEnvironmentMatched = Test-ReferenceEnvironmentMatch `
        -HostCandidate $referenceHostCandidate `
        -AzureMetadata $azureMetadata
    $referenceBudgetProved = $referenceEnvironmentMatched -and $localThresholdsPassed
    $result = [ordered]@{
        schemaVersion = "docs-context-benchmark/v1"
        passed = $localThresholdsPassed
        localThresholdsPassed = $localThresholdsPassed
        referenceBudgetProved = $referenceBudgetProved
        environment = [ordered]@{
            os = [System.Runtime.InteropServices.RuntimeInformation]::OSDescription
            architecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
            cpu = $cpu
            windowsCaption = $windowsCaption
            logicalProcessors = [Environment]::ProcessorCount
            python = $pythonVersion
            powershell = $PSVersionTable.PSVersion.ToString()
            referenceEnvironment = "Windows Server 2022 x64; Azure Standard_D4s_v5; CPython 3.11.9"
            referenceEnvironmentMatched = $referenceEnvironmentMatched
            azureReferenceMetadata = $azureMetadata
        }
        command = [ordered]@{
            executable = [IO.Path]::GetFileName($Python)
            arguments = @(
                "pack\scripts\docs-graph.py",
                "--root",
                "<generated-corpus>",
                "context",
                "--id",
                $manifest.rootId,
                "--policy",
                "grounding",
                "--hops",
                "2",
                "--query",
                "grounding project memory",
                "--max-bytes",
                "1048576",
                "--timings"
            )
            watchdogSeconds = $WatchdogSeconds
            iterations = $Iterations
            coldStartIterations = 1
            warmIterations = $Iterations
        }
        corpus = $manifest
        thresholds = [ordered]@{
            p75WallMilliseconds = $TargetWallMilliseconds
            peakWorkingSetBytes = $TargetPeakBytes
        }
        summary = [ordered]@{
            coldStart = $coldStart
            p50WallMilliseconds = [Math]::Round($p50, 3)
            p75WallMilliseconds = [Math]::Round($p75, 3)
            maxWallMilliseconds = [Math]::Round($maximum, 3)
            maxPeakWorkingSetBytes = $peak
            maxPacketBytes = [long](($runs | Measure-Object -Property packetBytes -Maximum).Maximum)
            maxVisitedNodes = [int](($runs | Measure-Object -Property visitedNodes -Maximum).Maximum)
            maxVisitedEdges = [int](($runs | Measure-Object -Property visitedEdges -Maximum).Maximum)
            maxChunksIncluded = [int](($runs | Measure-Object -Property chunksIncluded -Maximum).Maximum)
            maxChunksOmitted = [int](($runs | Measure-Object -Property chunksOmitted -Maximum).Maximum)
            phaseMilliseconds = Get-PhaseSummary -Runs $runs
        }
        runs = $runs
    }
    Write-Result $result
    if (-not $localThresholdsPassed) {
        exit 1
    }
}
finally {
    if (-not $KeepCorpus) {
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $corpusRoot
    }
}
