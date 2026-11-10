<#
LAYER: Engineer.
THE BIG PICTURE: wait for capacity and bound clipping's entire Windows process tree.
THE FLOW: inspect layout -> lock -> sample -> launch in a capped job -> monitor -> clean up.
#>
[CmdletBinding()]
param(
    [ValidateSet('Check', 'Run', 'Wait')][string]$Mode = 'Check',
    [ValidateSet('Gpu', 'Cpu')][string]$Workload = 'Gpu',
    [string]$FilePath,
    [string[]]$ArgumentList = @(),
    [string]$PipelineRoot = 'D:\J.A.R.V.I.S\Clipping',
    [ValidateRange(0, 32)][int]$GpuIndex = 0,
    [ValidateRange(1, 600)][int]$MaxWaitSeconds = 600,
    [ValidateRange(1, 86400)][int]$TimeoutSeconds = 1800,
    [ValidateSet('Conservative', 'MonitoredRender')][string]$ThermalProfile = 'Conservative',
    [switch]$Setup
)

$ErrorActionPreference = 'Stop'
. 'D:\J.A.R.V.I.S\.runtime\environment.ps1'
if (-not ('ClippingGuard.Tree' -as [type])) {
    Add-Type -Path (Join-Path $PSScriptRoot 'guard_native.cs')
}

function Test-ClippingStoragePath([string]$Path) {
    if (-not [IO.Path]::IsPathRooted($Path)) { return $false }
    $full = [IO.Path]::GetFullPath($Path)
    return $full.StartsWith('D:\J.A.R.V.I.S\', [StringComparison]::OrdinalIgnoreCase)
}

function ConvertTo-ClippingThrottle([string]$Value) {
    if ($Value.Trim() -eq 'Active') { return $true }
    if ($Value.Trim() -eq 'Not Active') { return $false }
    throw 'GPU thermal-throttling measurement unavailable'
}

function Get-ClippingSample($Probe, [bool]$UseGpu, [int]$Device, [bool]$MonitorThrottle = $false) {
    $sample = $Probe.Read()
    if (-not $UseGpu) { return $sample }
    $query = $null
    $queryStarted = $false
    try {
        $command = Get-Command nvidia-smi.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1
        $query = New-Object Diagnostics.Process
        $query.StartInfo = New-Object Diagnostics.ProcessStartInfo
        $query.StartInfo.FileName = $command.Source
        $fields = 'utilization.gpu,memory.free,temperature.gpu'
        if ($MonitorThrottle) { $fields += ',clocks_event_reasons.hw_thermal_slowdown,clocks_event_reasons.sw_thermal_slowdown' }
        $query.StartInfo.Arguments = "--id=$Device --query-gpu=$fields --format=csv,noheader,nounits"
        $query.StartInfo.UseShellExecute = $false
        $query.StartInfo.CreateNoWindow = $true
        $query.StartInfo.RedirectStandardOutput = $true
        $query.StartInfo.RedirectStandardError = $true
        [void]$query.Start()
        $queryStarted = $true
        $stdout = $query.StandardOutput.ReadToEndAsync()
        $stderr = $query.StandardError.ReadToEndAsync()
        if (-not $query.WaitForExit(5000)) {
            $query.Kill(); [void]$query.WaitForExit(5000)
            throw 'nvidia-smi timed out'
        }
        if ($query.ExitCode -ne 0) { throw 'nvidia-smi failed' }
        $parts = $stdout.Result.Trim().Split(',')
        $expectedParts = if ($MonitorThrottle) { 5 } else { 3 }
        if ($parts.Count -ne $expectedParts) { throw 'unexpected nvidia-smi response' }
        $culture = [Globalization.CultureInfo]::InvariantCulture
        $sample.GpuPercent = [double]::Parse($parts[0].Trim(), $culture)
        $sample.VramGiB = [double]::Parse($parts[1].Trim(), $culture) / 1024
        $sample.Temperature = [double]::Parse($parts[2].Trim(), $culture)
        if ($MonitorThrottle) {
            $sample.HardwareThermalSlowdown = ConvertTo-ClippingThrottle $parts[3]
            $sample.SoftwareThermalSlowdown = ConvertTo-ClippingThrottle $parts[4]
        }
    } catch { $sample.Error = $_.Exception.Message }
    finally {
        if ($null -ne $query) {
            try { if ($queryStarted -and -not $query.HasExited) { $query.Kill(); [void]$query.WaitForExit(5000) } }
            finally { $query.Dispose() }
        }
    }
    return $sample
}

function Write-ClippingJson([string]$Path, $Value) {
    $temporary = $Path + '.tmp'
    [IO.File]::WriteAllText($temporary, ($Value | ConvertTo-Json -Depth 7), (New-Object Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Wait-ClippingHeadroom([bool]$UseGpu, [int]$Device, [int]$WaitSeconds, [string]$SamplesPath, [bool]$MonitorThrottle = $false) {
    $probe = New-Object ClippingGuard.Telemetry
    $window = New-Object ClippingGuard.Admission
    $window.MonitorThermalThrottling = $MonitorThrottle
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $lastReport = -60.0
    do {
        $sample = Get-ClippingSample $probe $UseGpu $Device $MonitorThrottle
        $reason = $window.Observe($sample, $UseGpu)
        if ($SamplesPath) {
            Add-Content -LiteralPath $SamplesPath -Encoding UTF8 -Value ($sample | ConvertTo-Json -Compress)
        }
        if (-not $reason) {
            return [pscustomobject]@{ready = $true; reason = ''; average_cpu = $window.AverageCpu; sample = $sample}
        }
        if ($timer.Elapsed.TotalSeconds - $lastReport -ge 60) {
            Write-Host "Clipping deferred: $reason"
            $lastReport = $timer.Elapsed.TotalSeconds
        }
        $remaining = $WaitSeconds - $timer.Elapsed.TotalSeconds
        if ($remaining -le 0) { break }
        Start-Sleep -Milliseconds ([int]([Math]::Min(5, $remaining) * 1000))
    } while ($true)
    return [pscustomobject]@{ready = $false; reason = $reason; average_cpu = $window.AverageCpu; sample = $sample}
}

function Get-ClippingLayout([string]$Root, [bool]$SetupMode = $false) {
    if ($SetupMode) {
        $missing = @('package.json', 'scripts\common.py' | Where-Object {
            -not (Test-Path -LiteralPath (Join-Path $Root $_) -PathType Leaf)
        })
        return [pscustomobject]@{status = $(if ($missing.Count) {'blocked'} else {'layout_complete'});
            setup_only = $true; missing_files = $missing; dependencies_verified = $false}
    }
    $json = (& (Join-Path $PSScriptRoot 'check_environment.ps1') -PipelineRoot $Root -SkipResourceCheck) -join "`n"
    return $json | ConvertFrom-Json
}

function Invoke-ClippingRun([string]$Root, [string]$Executable, [string[]]$Arguments,
    [bool]$UseGpu, [int]$Device, [int]$WaitSeconds, [int]$RunTimeout, [bool]$SetupMode = $false,
    [ValidateSet('Conservative', 'MonitoredRender')][string]$ThermalProfile = 'Conservative') {
    if ($ThermalProfile -eq 'MonitoredRender' -and -not $UseGpu) { throw 'MonitoredRender requires a GPU workload' }
    if (-not (Test-ClippingStoragePath $Root)) { throw 'Pipeline root must stay under D:\J.A.R.V.I.S.' }
    $layout = Get-ClippingLayout $Root $SetupMode
    if ($layout.status -ne 'layout_complete') {
        return [pscustomobject]@{status = 'blocked'; exit_code = 1; reason = 'Clipping runtime is incomplete'; environment = $layout}
    }
    if (-not (Test-ClippingStoragePath $Executable) -or [IO.Path]::GetExtension($Executable) -ne '.exe' -or
        -not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
        throw 'Supply an existing D:\J.A.R.V.I.S executable and an argument array; shell command strings and .cmd files are not supported.'
    }
    $runtime = Join-Path $Root '.runtime'
    $runs = Join-Path $runtime 'guard'
    [void][IO.Directory]::CreateDirectory($runs)
    $lock = $null
    try {
        try {
            $lock = [IO.File]::Open((Join-Path $runtime 'clipping-guard.lock'), [IO.FileMode]::OpenOrCreate,
                [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
        } catch [IO.IOException] {
            return [pscustomobject]@{status = 'deferred'; exit_code = 75; reason = 'Another clipping operation owns the lock'}
        }
        foreach ($pending in @(Get-ChildItem -LiteralPath $runs -Filter pending.json -Recurse -File)) {
            $record = Get-Content -LiteralPath $pending.FullName -Raw | ConvertFrom-Json
            if ([ClippingGuard.Tree]::Remaining($record.job_name) -ne 0) {
                return [pscustomobject]@{status = 'blocked'; exit_code = 70; reason = 'Previous clipping process-tree cleanup is unconfirmed'; diagnostic = $pending.FullName}
            }
            $previousResult = Join-Path $pending.DirectoryName 'result.json'
            if (Test-Path -LiteralPath $previousResult) {
                $recovered = Get-Content -LiteralPath $previousResult -Raw | ConvertFrom-Json
                if ($recovered.status -eq 'running') {
                    $recovered.status = 'interrupted_recovered'; $recovered.exit_code = 130
                    $recovered.cleanup_confirmed = $true
                    $recovered.reason = 'Launcher interrupted; the next invocation verified its job is empty. Outputs still require validation.'
                    Write-ClippingJson $previousResult $recovered
                }
            }
            Remove-Item -LiteralPath $pending.FullName
        }
        $runDir = Join-Path $runs ([Guid]::NewGuid().ToString('N'))
        [void][IO.Directory]::CreateDirectory($runDir)
        $sampleLog = Join-Path $runDir 'samples.jsonl'
        $resultPath = Join-Path $runDir 'result.json'
        $pendingPath = Join-Path $runDir 'pending.json'
        $result = [ordered]@{status = 'waiting'; exit_code = 75; reason = ''; workload = $(if ($UseGpu) {'Gpu'} else {'Cpu'});
            diagnostic = $runDir; cleanup_confirmed = $true; output_validation_required = $true;
            gpu_index = $Device; cpu_limit_percent = 25; thermal_profile = $ThermalProfile;
            gpu_stop_temperature_c = $(if ($ThermalProfile -eq 'MonitoredRender') {90} else {85}); thermal_warning_count = 0}
        Write-ClippingJson $resultPath $result
        $admission = Wait-ClippingHeadroom $UseGpu $Device $WaitSeconds $sampleLog ($ThermalProfile -eq 'MonitoredRender')
        if (-not $admission.ready) {
            $result.status = 'deferred'; $result.reason = $admission.reason
            Write-ClippingJson $resultPath $result
            return [pscustomobject]$result
        }
        $tree = $null
        $saved = @{}
        try {
            $settings = @{OMP_NUM_THREADS = '2'; MKL_NUM_THREADS = '2'; OPENBLAS_NUM_THREADS = '2';
                NUMEXPR_NUM_THREADS = '2'; VECLIB_MAXIMUM_THREADS = '2'; BLIS_NUM_THREADS = '2';
                RAYON_NUM_THREADS = '2'; TOKENIZERS_PARALLELISM = 'false';
                HF_HUB_DISABLE_XET = '1';
                PATH = ((Join-Path $Root '.runtime\node'), (Join-Path $Root '.runtime\ffmpeg\bin'),
                    (Join-Path $Root '.venv\Scripts'), $env:PATH) -join ';';
                PUPPETEER_CACHE_DIR = (Join-Path $Root '.runtime\browser-cache');
                PLAYWRIGHT_BROWSERS_PATH = (Join-Path $Root '.runtime\browser-cache')}
            if ($UseGpu) { $settings.CUDA_VISIBLE_DEVICES = [string]$Device }
            foreach ($key in $settings.Keys) {
                $saved[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
                [Environment]::SetEnvironmentVariable($key, $settings[$key], 'Process')
            }
            $tree = New-Object ClippingGuard.Tree
            if ($tree.CpuLimitPercent -ne 25) { throw 'Clipping CPU hard cap could not be verified' }
            $saved['CLIPPING_GUARD_JOB'] = [Environment]::GetEnvironmentVariable('CLIPPING_GUARD_JOB', 'Process')
            [Environment]::SetEnvironmentVariable('CLIPPING_GUARD_JOB', $tree.Name, 'Process')
            $saved['CLIPPING_GUARD_WORKLOAD'] = [Environment]::GetEnvironmentVariable('CLIPPING_GUARD_WORKLOAD', 'Process')
            [Environment]::SetEnvironmentVariable('CLIPPING_GUARD_WORKLOAD', $(if ($UseGpu) {'Gpu'} else {'Cpu'}), 'Process')
            Write-ClippingJson $pendingPath @{job_name = $tree.Name}
            $result.status = 'running'; $result.exit_code = 130; $result.cleanup_confirmed = $false
            Write-ClippingJson $resultPath $result
            $tree.Start($Executable, $Arguments, $Root, (Join-Path $runDir 'stdout.log'), (Join-Path $runDir 'stderr.log'))
            Write-Host "Clipping started (PID $($tree.Pid)); tree CPU cap 25%, below-normal priority. Logs: $runDir"
            $probe = New-Object ClippingGuard.Telemetry
            [void]$probe.Read()
            $pressure = New-Object ClippingGuard.Pressure
            $pressure.GpuStopTemperature = $result.gpu_stop_temperature_c
            $pressure.MonitorThermalThrottling = $ThermalProfile -eq 'MonitoredRender'
            $timer = [Diagnostics.Stopwatch]::StartNew()
            $nextSample = 5.0; $nextReport = 60.0; $lastHeatWarning = -60.0
            while (-not $tree.RootExited) {
                if ($timer.Elapsed.TotalSeconds -ge $RunTimeout) {
                    $result.status = 'timeout'; $result.exit_code = 124; $result.reason = 'Stage execution time limit reached'; break
                }
                if ($timer.Elapsed.TotalSeconds -ge $nextSample) {
                    $sample = Get-ClippingSample $probe $UseGpu $Device ($ThermalProfile -eq 'MonitoredRender')
                    Add-Content -LiteralPath $sampleLog -Encoding UTF8 -Value ($sample | ConvertTo-Json -Compress)
                    if ($UseGpu -and $ThermalProfile -eq 'MonitoredRender' -and $sample.Temperature -ge 85 -and
                        $timer.Elapsed.TotalSeconds - $lastHeatWarning -ge 60) {
                        Write-Host "Clipping thermal warning: GPU $($sample.Temperature) C; monitored-render stop is 90 C for 10 seconds or thermal throttling."
                        $lastHeatWarning = $timer.Elapsed.TotalSeconds; $result.thermal_warning_count++
                    }
                    $reason = $pressure.Observe($sample, $UseGpu)
                    if ($reason) { $result.status = 'resource_abort'; $result.exit_code = 76; $result.reason = $reason; break }
                    $nextSample = $timer.Elapsed.TotalSeconds + 5
                }
                if ($timer.Elapsed.TotalSeconds -ge $nextReport) {
                    Write-Host "Clipping running for $([int]$timer.Elapsed.TotalSeconds)s; logs: $runDir"
                    $nextReport = $timer.Elapsed.TotalSeconds + 60
                }
                Start-Sleep -Milliseconds 200
            }
            if ($result.status -eq 'running') {
                $result.worker_exit_code = $tree.ExitCode
                $result.exit_code = [BitConverter]::ToInt32([BitConverter]::GetBytes([uint32]$tree.ExitCode), 0)
                # Console helpers can take a moment to exit after their parent.
                $completion = [Diagnostics.Stopwatch]::StartNew()
                while ($tree.Active -gt 0 -and $completion.Elapsed.TotalSeconds -lt 1) { Start-Sleep -Milliseconds 50 }
                if ($result.exit_code -eq 0 -and $tree.Active -gt 0) {
                    $result.status = 'failed'; $result.exit_code = 76; $result.reason = 'Worker exited with descendants still running'
                } else {
                    $result.status = $(if ($result.exit_code -eq 0) {'worker_succeeded'} else {'failed'})
                    $result.reason = $(if ($result.exit_code -eq 0) {'Validate outputs and actual GPU usage before delivery'} else {'Worker failed; inspect logs. No CPU fallback or automatic retry was attempted.'})
                }
            }
        } catch {
            if ($_.Exception -is [Management.Automation.PipelineStoppedException]) {
                $result.status = 'cancelled'; $result.exit_code = 130; $result.reason = 'Clipping cancelled'
            } else {
                $result.status = 'failed'; $result.exit_code = 70; $result.reason = $_.Exception.Message
            }
        } finally {
            if ($result.status -eq 'running') {
                $result.status = 'cancelled'; $result.exit_code = 130; $result.reason = 'Clipping cancelled'
            }
            try {
                if ($null -ne $tree) {
                    if ($tree.Active -ne 0) { $tree.Stop() }
                    $cleanup = [Diagnostics.Stopwatch]::StartNew()
                    while ($tree.Active -ne 0 -and $cleanup.Elapsed.TotalSeconds -lt 15) { Start-Sleep -Milliseconds 100 }
                    $result.cleanup_confirmed = $tree.Active -eq 0
                    if (-not $result.cleanup_confirmed) { throw 'Process-tree cleanup unconfirmed' }
                    $result.tree_cpu_seconds = $tree.CpuSeconds
                    Remove-Item -LiteralPath $pendingPath -ErrorAction SilentlyContinue
                } else { $result.cleanup_confirmed = $true }
            } catch {
                $result.cleanup_confirmed = $false; $result.status = 'cleanup_unconfirmed'; $result.exit_code = 70
                $result.reason = $_.Exception.Message
            } finally {
                if ($null -ne $tree) { $tree.Dispose() }
                foreach ($key in $saved.Keys) { [Environment]::SetEnvironmentVariable($key, $saved[$key], 'Process') }
                Write-ClippingJson $resultPath $result
            }
        }
        return [pscustomobject]$result
    } finally { if ($null -ne $lock) { $lock.Dispose() } }
}

if ($MyInvocation.InvocationName -ne '.') {
    try {
        if ($Mode -in @('Check', 'Wait')) {
            $wait = if ($Mode -eq 'Wait') { $MaxWaitSeconds } else { 31 }
            $report = Wait-ClippingHeadroom ($Workload -eq 'Gpu') $GpuIndex $wait '' ($ThermalProfile -eq 'MonitoredRender')
            $report | ConvertTo-Json -Depth 7
            if ($report.ready) { exit 0 } else { exit 75 }
        }
    $report = Invoke-ClippingRun $PipelineRoot $FilePath $ArgumentList ($Workload -eq 'Gpu') $GpuIndex $MaxWaitSeconds $TimeoutSeconds ([bool]$Setup) $ThermalProfile
        $report | ConvertTo-Json -Depth 7
        exit $report.exit_code
    } catch {
        [pscustomobject]@{status = 'blocked'; exit_code = 70; reason = $_.Exception.Message} | ConvertTo-Json
        exit 70
    }
}
