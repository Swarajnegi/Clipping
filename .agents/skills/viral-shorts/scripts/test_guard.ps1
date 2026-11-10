<# LAYER: Engineer. THE BIG PICTURE: exercise policy and real Windows containment without ML.
THE FLOW: deterministic resource scenarios -> bounded native workers -> launcher failure paths.
#>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'run_guarded.ps1')
$script:Passed = 0
function Assert-Guard([bool]$Condition, [string]$Label) {
    if (-not $Condition) { throw "FAIL: $Label" }
    $script:Passed++
    Write-Host "PASS: $Label"
}
function New-Sample([double]$At = 5, [double]$Cpu = 20, [double]$Ram = 6,
    [bool]$AC = $true, [double]$Gpu = 10, [double]$Vram = 5, [double]$Temp = 50) {
    $s = New-Object ClippingGuard.Sample
    $s.At = $At; $s.CpuSeconds = 5; $s.Cpu = $Cpu; $s.RamGiB = $Ram
    $s.OnAC = $AC; $s.GpuPercent = $Gpu; $s.VramGiB = $Vram; $s.Temperature = $Temp
    $s.HardwareThermalSlowdown = $false; $s.SoftwareThermalSlowdown = $false
    return $s
}
foreach ($load in @(50, 60)) {
    $window = New-Object ClippingGuard.Admission
    foreach ($at in @(5, 10, 15, 20, 25, 30)) { $reason = $window.Observe((New-Sample -At $at -Cpu $load), $true) }
    Assert-Guard ($reason -like '*average CPU*') "JARVIS load $load% defers clipping"
    foreach ($at in @(35, 40, 45, 50, 55, 60)) { $reason = $window.Observe((New-Sample -At $at), $true) }
    Assert-Guard ($reason -eq '') 'rolling window recovers when headroom returns'
}
$window = New-Object ClippingGuard.Admission
Assert-Guard ($window.Observe((New-Sample), $true) -like '*30 seconds*') 'one snapshot never admits work'
foreach ($case in @(
    @{name = 'low RAM'; sample = (New-Sample -Ram 3); expected = '*RAM*'},
    @{name = 'low VRAM'; sample = (New-Sample -Vram 2); expected = '*video memory*'},
    @{name = 'battery power'; sample = (New-Sample -AC $false); expected = '*mains*'},
    @{name = 'busy GPU'; sample = (New-Sample -Gpu 31); expected = '*utilization*'},
    @{name = 'hot GPU'; sample = (New-Sample -Temp 80); expected = '*temperature*'}
)) {
    Assert-Guard ($window.Observe($case.sample, $true) -like $case.expected) "$($case.name) blocks admission"
}
foreach ($field in @('Cpu', 'RamGiB', 'OnAC', 'GpuPercent', 'VramGiB', 'Temperature')) {
    $s = New-Sample; $s.$field = $null
    Assert-Guard ($window.Observe($s, $true) -like '*unavailable*') "missing $field fails closed"
}
$s = New-Sample; $s.Cpu = [double]::NaN
Assert-Guard ($window.Observe($s, $true) -like '*unavailable*') 'NaN is not a measurement'
$pressure = New-Object ClippingGuard.Pressure
Assert-Guard ($pressure.Observe((New-Sample -Gpu 100 -Vram 0.1), $true) -eq '') 'own GPU utilization and allocated VRAM do not abort'
Assert-Guard ($pressure.Observe((New-Sample -At 5 -Cpu 95), $true) -eq '') 'brief CPU spike allowed'
Assert-Guard ($pressure.Observe((New-Sample -At 10), $true) -eq '') 'CPU recovery resets pressure timer'
foreach ($at in @(15, 20, 25)) { $reason = $pressure.Observe((New-Sample -At $at -Cpu 95), $true) }
Assert-Guard ($reason -eq '') 'CPU abort waits the full 15 seconds'
Assert-Guard ($pressure.Observe((New-Sample -At 30 -Cpu 95), $true) -like '*CPU*') 'sustained CPU overload aborts'
foreach ($scenario in @('ram', 'heat')) {
    $pressure = New-Object ClippingGuard.Pressure
    foreach ($at in @(5, 10, 15)) {
        $s = New-Sample -At $at
        if ($scenario -eq 'ram') { $s.RamGiB = 1.5 } else { $s.Temperature = 85 }
        $reason = $pressure.Observe($s, $true)
    }
    Assert-Guard ($reason -ne '') "sustained $scenario pressure aborts"
}
$pressure = New-Object ClippingGuard.Pressure
$s = New-Sample; $s.RamGiB = $null
Assert-Guard ($pressure.Observe($s, $false) -like '*unavailable*') 'telemetry loss while running aborts'
Assert-Guard ($pressure.Observe((New-Sample -AC $false), $false) -like '*disconnected*') 'unplugging mains stops clipping'
$pressure = New-Object ClippingGuard.Pressure
Assert-Guard ($pressure.GpuStopTemperature -eq 85 -and -not $pressure.MonitorThermalThrottling) 'default thermal policy remains conservative'
$pressure.GpuStopTemperature = 90; $pressure.MonitorThermalThrottling = $true
foreach ($at in @(5,10,15,20)) { $reason = $pressure.Observe((New-Sample -At $at -Temp 87), $true) }
Assert-Guard ($reason -eq '') 'opt-in monitored render allows stable 87 C with no thermal throttle'
Assert-Guard ($pressure.Observe((New-Sample -At 25 -Temp 90), $true) -eq '') '90 C spike does not immediately cancel monitored render'
Assert-Guard ($pressure.Observe((New-Sample -At 30 -Temp 89), $true) -eq '') 'temperature recovery resets the 90 C timer'
foreach ($at in @(35,40)) { $reason = $pressure.Observe((New-Sample -At $at -Temp 90), $true) }
Assert-Guard ($reason -eq '') 'monitored heat abort waits the full ten seconds'
Assert-Guard ($pressure.Observe((New-Sample -At 45 -Temp 90), $true) -like '*90 C*') 'monitored sustained 90 C aborts'
foreach ($field in @('HardwareThermalSlowdown','SoftwareThermalSlowdown')) {
    $pressure = New-Object ClippingGuard.Pressure; $pressure.GpuStopTemperature = 90; $pressure.MonitorThermalThrottling = $true
    $sample = New-Sample -Temp 70; $sample.$field = $true
    Assert-Guard ($pressure.Observe($sample, $true) -like '*thermal throttling*') "$field aborts immediately on observation"
    $sample.$field = $null
    Assert-Guard ($pressure.Observe($sample, $true) -like '*unavailable*') "missing $field fails closed in monitored render"
    $window = New-Object ClippingGuard.Admission; $window.MonitorThermalThrottling = $true
    Assert-Guard ($window.Observe($sample, $true) -like '*unavailable*') "missing $field blocks monitored admission"
}
Assert-Guard ((ConvertTo-ClippingThrottle 'Active') -eq $true) 'active thermal flag is parsed'
Assert-Guard ((ConvertTo-ClippingThrottle 'Not Active') -eq $false) 'inactive thermal flag is parsed'
$rejected = $false
try { [void](ConvertTo-ClippingThrottle 'N/A') } catch { $rejected = $true }
Assert-Guard $rejected 'unsupported thermal telemetry is rejected rather than treated as inactive'
$probe = New-Object ClippingGuard.Telemetry
[void]$probe.Read(); Start-Sleep -Milliseconds 100
$live = $probe.Read()
Assert-Guard ($null -ne $live.Cpu -and $null -ne $live.RamGiB -and $null -ne $live.OnAC) 'native CPU, RAM and power measurements work'

$scratch = Join-Path 'D:\J.A.R.V.I.S\Clipping\.runtime\guard-tests' ([Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($scratch)
$source = Join-Path $scratch 'worker.cs'
$worker = Join-Path $scratch 'worker.exe'
@'
using System;
using System.Diagnostics;
using System.Text;
using System.Threading;
class Worker {
    static void Burn(int ms) {
        Stopwatch clock = Stopwatch.StartNew();
        Thread[] threads = new Thread[Environment.ProcessorCount];
        for (int n = 0; n < threads.Length; n++) {
            threads[n] = new Thread(delegate() { double x = 1; while (clock.ElapsedMilliseconds < ms) x = Math.Sqrt(x + 1); });
            threads[n].Start();
        }
        foreach (Thread thread in threads) thread.Join();
    }
    static void Main(string[] args) {
        Console.WriteLine("PID=" + Process.GetCurrentProcess().Id);
        if (args[0] == "args") {
            for (int n = 1; n < args.Length; n++) Console.WriteLine(Convert.ToBase64String(Encoding.UTF8.GetBytes(args[n])));
        } else if (args[0] == "tree" || args[0] == "orphan" || args[0] == "burntree") {
            ProcessStartInfo info = new ProcessStartInfo(Process.GetCurrentProcess().MainModule.FileName,
                args[0] == "burntree" ? "burn" : "sleep");
            info.UseShellExecute = false; info.CreateNoWindow = true;
            Process child = Process.Start(info);
            Console.WriteLine("CHILD=" + child.Id); Console.Out.Flush();
            if (args[0] == "orphan") return;
            if (args[0] == "burntree") { Burn(6000); child.WaitForExit(); }
            else Thread.Sleep(30000);
        } else if (args[0] == "burn") Burn(6000);
        else if (args[0] == "fail") Environment.Exit(9);
        else { Console.Out.Flush(); Thread.Sleep(30000); }
    }
}
'@ | Set-Content -LiteralPath $source -Encoding UTF8
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $compiler /nologo /target:exe "/out:$worker" $source
if ($LASTEXITCODE -ne 0) { throw 'Fixture compiler failed' }
try {
    function Get-Command { [pscustomobject]@{Source = 'D:\J.A.R.V.I.S\.runtime\nonexistent-gpu-query.exe'} }
    $sample = Get-ClippingSample $probe $true 0
    Assert-Guard ($null -eq $sample.GpuPercent -and $sample.Error) 'failed GPU query start returns unavailable telemetry'
    function Get-Command { [pscustomobject]@{Source = $worker} }
    $queryTimer = [Diagnostics.Stopwatch]::StartNew()
    $sample = Get-ClippingSample $probe $true 0
    Assert-Guard ($sample.Error -like '*timed out*' -and $queryTimer.Elapsed.TotalSeconds -lt 10) 'hung GPU query is terminated within its bounded timeout'
} finally { Remove-Item -LiteralPath Function:Get-Command }
function Start-Fixture([ClippingGuard.Tree]$Tree, [string[]]$Arguments, [string]$Label) {
    $out = Join-Path $scratch ($Label + '.out')
    $err = Join-Path $scratch ($Label + '.err')
    $Tree.Start($worker, $Arguments, $scratch, $out, $err)
    return $out
}
function Wait-Fixture([ClippingGuard.Tree]$Tree) {
    $watch = [Diagnostics.Stopwatch]::StartNew()
    while (-not $Tree.RootExited -and $watch.Elapsed.TotalSeconds -lt 15) { Start-Sleep -Milliseconds 50 }
    Assert-Guard $Tree.RootExited 'bounded worker exited'
}
function Stop-Fixture([ClippingGuard.Tree]$Tree) {
    if ($Tree.Active -ne 0) { $Tree.Stop() }
    $watch = [Diagnostics.Stopwatch]::StartNew()
    while ($Tree.Active -ne 0 -and $watch.Elapsed.TotalSeconds -lt 5) { Start-Sleep -Milliseconds 50 }
    Assert-Guard ($Tree.Active -eq 0) 'whole owned process tree cleaned up'
}
function Read-FixtureLog([string]$Path) {
    $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
    $reader = New-Object IO.StreamReader($stream)
    try { return $reader.ReadToEnd() } finally { $reader.Dispose(); $stream.Dispose() }
}

$tree = New-Object ClippingGuard.Tree
try {
    Assert-Guard ($tree.CpuLimitPercent -eq 25) 'Windows reports an enabled 25% CPU hard cap'
    $arguments = @('args', '', 'two words', 'quote"inside', 'ends with slash\', 'semi; dollar$(test)', ([string][char]0x0939 + [char]0x093f))
    $out = Start-Fixture $tree $arguments 'arguments'
    Wait-Fixture $tree
    $lines = @(Get-Content -LiteralPath $out | Where-Object { -not $_.StartsWith('PID=') })
    $matches = $lines.Count -eq $arguments.Count - 1
    for ($i = 1; $i -lt $arguments.Count; $i++) {
        $decoded = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($lines[$i - 1]))
        $matches = $matches -and ($decoded -ceq $arguments[$i])
    }
    Assert-Guard $matches 'argument array preserves empty strings, quotes, Unicode and shell characters'
    Assert-Guard ($tree.ExitCode -eq 0) 'native exit status preserved'
} finally { Stop-Fixture $tree; $tree.Dispose() }

$unrelated = Start-Process -FilePath $worker -ArgumentList 'sleep' -WindowStyle Hidden -PassThru
$tree = New-Object ClippingGuard.Tree
try {
    $out = Start-Fixture $tree @('tree') 'cancel'
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $childId = 0
    do {
        $contents = Read-FixtureLog $out
        if ($contents -match 'CHILD=(\d+)') { $childId = [int]$Matches[1]; break }
        Start-Sleep -Milliseconds 50
    } while ($watch.Elapsed.TotalSeconds -lt 5)
    Assert-Guard ($childId -ne 0 -and $tree.Contains($childId)) 'child process automatically joins the job'
    $root = Get-Process -Id $tree.Pid
    Assert-Guard ($root.PriorityClass -eq 'BelowNormal') 'below-normal priority is applied before worker execution'
    Stop-Fixture $tree
    Assert-Guard (-not $unrelated.HasExited) 'unrelated process survives cancellation'
} finally {
    Stop-Fixture $tree; $tree.Dispose()
    if (-not $unrelated.HasExited) { $unrelated.Kill(); $unrelated.WaitForExit() }
    $unrelated.Dispose()
}

# A six-second capped workload is the only CPU exercise; no models or GPU work run.
if ($live.Cpu -le 40 -and $live.RamGiB -ge 4) {
    $tree = New-Object ClippingGuard.Tree
    try {
        $watch = [Diagnostics.Stopwatch]::StartNew()
        [void](Start-Fixture $tree @('burntree') 'cap')
        Wait-Fixture $tree
        $fraction = $tree.CpuSeconds / ($watch.Elapsed.TotalSeconds * [Environment]::ProcessorCount)
        Assert-Guard ($fraction -gt 0.01 -and $fraction -lt 0.31) "aggregate parent+child CPU stays capped (measured $([Math]::Round(100*$fraction, 1))%)"
    } finally { Stop-Fixture $tree; $tree.Dispose() }
} else { throw 'Machine lacks headroom for the bounded CPU-cap fixture; rerun when idle' }

# Substitute only layout and admission in this test scope; production CLI has no bypass flags.
function Get-ClippingLayout([string]$Root) { return [pscustomobject]@{status = 'layout_complete'} }
function Wait-ClippingHeadroom([bool]$UseGpu, [int]$Device, [int]$WaitSeconds, [string]$SamplesPath) {
    return [pscustomobject]@{ready = $true; reason = ''}
}
$root = Join-Path $scratch 'pipeline'; [void][IO.Directory]::CreateDirectory($root)
$savedThreads = $env:OMP_NUM_THREADS
$result = Invoke-ClippingRun $root $worker @('fail') $false 0 1 10
Assert-Guard ($result.exit_code -eq 9 -and $result.status -eq 'failed' -and $result.cleanup_confirmed) 'launcher preserves worker failures without retry'
Assert-Guard ($env:OMP_NUM_THREADS -eq $savedThreads) 'launcher restores thread environment'
$result = Invoke-ClippingRun $root $worker @('tree') $false 0 1 1
Assert-Guard ($result.exit_code -eq 124 -and $result.cleanup_confirmed) 'execution timeout cleans descendants'
$result = Invoke-ClippingRun $root $worker @('orphan') $false 0 1 10
Assert-Guard ($result.exit_code -eq 76 -and $result.cleanup_confirmed) 'orphaned descendant prevents false success'
$lockPath = Join-Path $root '.runtime\clipping-guard.lock'
$held = [IO.File]::Open($lockPath, 'OpenOrCreate', 'ReadWrite', 'None')
try {
    $result = Invoke-ClippingRun $root $worker @('fail') $false 0 1 1
    Assert-Guard ($result.exit_code -eq 75) 'concurrent caller cannot start a second operation'
} finally { $held.Dispose() }
$result = Invoke-ClippingRun $root $worker @('args', 'ok') $false 0 1 10
Assert-Guard ($result.status -eq 'worker_succeeded' -and $result.cleanup_confirmed) 'lock released after cleanup and next stage can run'

$abruptRoot = Join-Path $scratch 'abrupt-pipeline'
[void][IO.Directory]::CreateDirectory($abruptRoot)
$abruptScript = Join-Path $scratch 'abrupt.ps1'
$launcher = Join-Path $PSScriptRoot 'run_guarded.ps1'
@'
param($Launcher, $Root, $Worker)
. $Launcher
function Get-ClippingLayout([string]$Root) { [pscustomobject]@{status='layout_complete'} }
function Wait-ClippingHeadroom([bool]$UseGpu, [int]$Device, [int]$WaitSeconds, [string]$SamplesPath) {
    [pscustomobject]@{ready=$true; reason=''}
}
Invoke-ClippingRun $Root $Worker @('tree') $false 0 1 30 | ConvertTo-Json
'@ | Set-Content -LiteralPath $abruptScript -Encoding ASCII
$hostExe = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$hostArguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $abruptScript, $launcher, $abruptRoot, $worker)
$hostCommand = ($hostArguments | ForEach-Object { [ClippingGuard.Tree]::Quote($_) }) -join ' '
$hostProcess = Start-Process -FilePath $hostExe -ArgumentList $hostCommand -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $scratch 'abrupt.out') -RedirectStandardError (Join-Path $scratch 'abrupt.err')
try {
    $deadline = [Diagnostics.Stopwatch]::StartNew(); $ownedIds = @(); $pendingRecords = @()
    do {
        $logs = @(Get-ChildItem -LiteralPath $abruptRoot -Filter stdout.log -Recurse -ErrorAction SilentlyContinue)
        if ($logs.Count) {
            $text = Read-FixtureLog $logs[0].FullName
            if ($text -match 'CHILD=') {
                $ownedIds = @([regex]::Matches($text, '(?:PID|CHILD)=(\d+)') | ForEach-Object { [int]$_.Groups[1].Value } | Select-Object -Unique)
            }
        }
        if ($ownedIds.Count -ge 2) { break }
        Start-Sleep -Milliseconds 100
    } while ($deadline.Elapsed.TotalSeconds -lt 10 -and -not $hostProcess.HasExited)
    Assert-Guard ($ownedIds.Count -ge 2) 'separate launcher starts the contained parent and child'
    $pendingRecords = @(Get-ChildItem -LiteralPath $abruptRoot -Filter pending.json -Recurse)
    $record = Get-Content -LiteralPath $pendingRecords[0].FullName -Raw | ConvertFrom-Json
    $hostProcess.Kill(); $hostProcess.WaitForExit()
    $deadline.Restart()
    do {
        $alive = @(Get-Process -Id $ownedIds -ErrorAction SilentlyContinue)
        if (-not $alive.Count) { break }
        Start-Sleep -Milliseconds 100
    } while ($deadline.Elapsed.TotalSeconds -lt 5)
    Assert-Guard ($alive.Count -eq 0 -and [ClippingGuard.Tree]::Remaining($record.job_name) -eq 0) 'hard launcher termination kills the complete job automatically'
    $result = Invoke-ClippingRun $abruptRoot $worker @('args', 'after-cancel') $false 0 1 10
    Assert-Guard ($result.status -eq 'worker_succeeded') 'next launch verifies interrupted cleanup and recovers the released lock'
    Assert-Guard (-not (Test-Path -LiteralPath $pendingRecords[0].FullName)) 'verified interrupted cleanup record is retired'
    $recovered = Get-Content -LiteralPath (Join-Path $pendingRecords[0].DirectoryName 'result.json') -Raw | ConvertFrom-Json
    Assert-Guard ($recovered.status -eq 'interrupted_recovered' -and $recovered.cleanup_confirmed -and $recovered.exit_code -eq 130) 'recovery receipt records interruption and verified cleanup accurately'
} finally {
    if (-not $hostProcess.HasExited) { $hostProcess.Kill(); $hostProcess.WaitForExit() }
    $hostProcess.Dispose()
}

# An occupied pending job must never be inferred safe from the old launcher exiting.
$tree = New-Object ClippingGuard.Tree
try {
    [void](Start-Fixture $tree @('sleep') 'pending')
    $pendingDir = Join-Path $root '.runtime\guard\interrupted'
    [void][IO.Directory]::CreateDirectory($pendingDir)
    $pendingPath = Join-Path $pendingDir 'pending.json'
    Write-ClippingJson $pendingPath @{job_name = $tree.Name}
    $result = Invoke-ClippingRun $root $worker @('args') $false 0 1 1
    Assert-Guard ($result.exit_code -eq 70 -and -not $tree.RootExited) 'unconfirmed cleanup blocks admission without killing the old job'
    Stop-Fixture $tree
    $result = Invoke-ClippingRun $root $worker @('args', 'recovered') $false 0 1 10
    Assert-Guard ($result.status -eq 'worker_succeeded' -and -not (Test-Path $pendingPath)) 'confirmed empty job permits recovery'
} finally { Stop-Fixture $tree; $tree.Dispose() }

$cancelRoot = Join-Path $scratch 'cancel-pipeline'; [void][IO.Directory]::CreateDirectory($cancelRoot)
$pipeline = [PowerShell]::Create()
$cancelBody = @'
param($Launcher, $Root, $Worker)
. $Launcher
function Get-ClippingLayout([string]$Root) { [pscustomobject]@{status='layout_complete'} }
function Wait-ClippingHeadroom([bool]$UseGpu, [int]$Device, [int]$WaitSeconds, [string]$SamplesPath) {
    [pscustomobject]@{ready=$true; reason=''}
}
Invoke-ClippingRun $Root $Worker @('tree') $false 0 1 30
'@
try {
    [void]$pipeline.AddScript($cancelBody).AddArgument($launcher).AddArgument($cancelRoot).AddArgument($worker)
    $operation = $pipeline.BeginInvoke()
    $deadline = [Diagnostics.Stopwatch]::StartNew(); $started = $false
    do {
        $logs = @(Get-ChildItem -LiteralPath $cancelRoot -Filter stdout.log -Recurse -ErrorAction SilentlyContinue)
        if ($logs.Count -and (Read-FixtureLog $logs[0].FullName) -match 'CHILD=') { $started = $true; break }
        Start-Sleep -Milliseconds 100
    } while ($deadline.Elapsed.TotalSeconds -lt 10 -and -not $operation.IsCompleted)
    Assert-Guard $started 'PowerShell cancellation fixture starts contained workers'
    $pipeline.Stop()
    $receipt = Get-ChildItem -LiteralPath $cancelRoot -Filter result.json -Recurse | Select-Object -First 1
    $cancelled = Get-Content -LiteralPath $receipt.FullName -Raw | ConvertFrom-Json
    Assert-Guard ($cancelled.exit_code -eq 130 -and $cancelled.status -eq 'cancelled' -and $cancelled.cleanup_confirmed) 'PowerShell cancellation persists cleanup confirmation'
    $result = Invoke-ClippingRun $cancelRoot $worker @('args', 'after-stop') $false 0 1 10
    Assert-Guard ($result.status -eq 'worker_succeeded') 'PowerShell cancellation releases the operation lock'
} finally { $pipeline.Dispose() }

$originalSample = ${function:Get-ClippingSample}
try {
    $script:PressureTime = 0
    function Get-ClippingSample($Probe, [bool]$UseGpu, [int]$Device) {
        $script:PressureTime += 15
        return New-Sample -At $script:PressureTime -Cpu 95
    }
    $result = Invoke-ClippingRun $root $worker @('tree') $false 0 1 30
    Assert-Guard ($result.status -eq 'resource_abort' -and $result.exit_code -eq 76 -and $result.cleanup_confirmed) 'runtime pressure monitor aborts the actual contained stage'
    function Get-ClippingSample($Probe, [bool]$UseGpu, [int]$Device) {
        $s = New-Sample; $s.RamGiB = $null; return $s
    }
    $result = Invoke-ClippingRun $root $worker @('tree') $false 0 1 30
    Assert-Guard ($result.status -eq 'resource_abort' -and $result.reason -like '*unavailable*' -and $result.cleanup_confirmed) 'runtime telemetry loss cleans the actual contained stage'
} finally { ${function:Get-ClippingSample} = $originalSample }

function Wait-ClippingHeadroom([bool]$UseGpu, [int]$Device, [int]$WaitSeconds, [string]$SamplesPath) {
    return [pscustomobject]@{ready = $false; reason = 'waiting for average CPU <=40%'}
}
$result = Invoke-ClippingRun $root $worker @('args') $false 0 1 1
Assert-Guard ($result.exit_code -eq 75 -and $result.status -eq 'deferred') 'admission timeout returns deferred without launching'
Assert-Guard (@(Get-ChildItem -LiteralPath (Join-Path $root '.runtime\guard') -Filter pending.json -Recurse).Count -eq 0) 'no pending cleanup records after normal paths'
Write-Host "Clipping guard: $script:Passed checks passed. Evidence: $scratch"
