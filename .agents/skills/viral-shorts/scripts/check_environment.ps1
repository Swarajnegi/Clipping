param(
    [string]$PipelineRoot = 'D:\J.A.R.V.I.S\Clipping',
    [switch]$SkipResourceCheck
)

$ErrorActionPreference = 'Stop'
$storageRoot = [IO.Path]::GetFullPath('D:\J.A.R.V.I.S').TrimEnd('\')
$clipRoot = [IO.Path]::GetFullPath($PipelineRoot).TrimEnd('\')

function Test-StoragePath([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    try { $full = [IO.Path]::GetFullPath($Path) } catch { return $false }
    return $full.StartsWith($storageRoot + '\', [StringComparison]::OrdinalIgnoreCase)
}

if (-not (Test-StoragePath $clipRoot)) {
    throw 'The clipping root must stay under D:\J.A.R.V.I.S.'
}

$requiredFiles = @('package.json', 'scripts\prep.py', 'scripts\sheet.py',
    'scripts\build.py', 'scripts\outliers.py', 'scripts\results.py', 'scripts\common.py',
    'scripts\voice.py', 'scripts\track.py', 'scripts\check_dependencies.py', 'requirements.txt',
    'requirements.lock.txt', 'remotion.config.ts', 'src\index.ts',
    'node_modules\@remotion\cli\remotion-cli.js',
    'node_modules\.remotion\chrome-headless-shell\win64\chrome-headless-shell-win64\chrome-headless-shell.exe',
    'models\whisper-small\model.bin', 'models\whisper-small\restoration.json',
    'models\kokoro-v1.0.onnx', 'models\voices-v1.0.bin', 'models\face_detection_yunet_2023mar.onnx')
$missing = @($requiredFiles | Where-Object {
    -not (Test-Path -LiteralPath (Join-Path $clipRoot $_) -PathType Leaf)
})
$python = Join-Path $clipRoot '.venv\Scripts\python.exe'
$pythonPresent = Test-Path -LiteralPath $python -PathType Leaf
$tools = @()
foreach ($name in @('node', 'npm', 'ffmpeg', 'ffprobe', 'yt-dlp')) {
    $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    $candidates = switch ($name) {
        'node' { Join-Path $clipRoot '.runtime\node\node.exe' }
        'npm' { Join-Path $clipRoot '.runtime\node\npm.cmd' }
        'ffmpeg' { Join-Path $clipRoot '.runtime\ffmpeg\bin\ffmpeg.exe' }
        'ffprobe' { Join-Path $clipRoot '.runtime\ffmpeg\bin\ffprobe.exe' }
        'yt-dlp' { Join-Path $clipRoot '.venv\Scripts\yt-dlp.exe' }
    }
    $usable = @(@($candidates) + @($command.Source) | Where-Object {
        (Test-StoragePath $_) -and (Test-Path -LiteralPath $_ -PathType Leaf)
    })
    $tools += [pscustomobject]@{
        name = $name
        available_on_d = ($usable.Count -gt 0)
        path = if ($usable.Count -gt 0) { $usable[0] } else { $null }
        ignored_outside_d = if ($command -and -not (Test-StoragePath $command.Source)) {
            $command.Source
        } else { $null }
    }
}

$cacheNames = @('TEMP', 'TMP', 'PIP_CACHE_DIR', 'HF_HOME', 'HF_HUB_CACHE',
    'TORCH_HOME', 'XDG_CACHE_HOME', 'UV_CACHE_DIR', 'npm_config_cache')
$caches = @($cacheNames | ForEach-Object {
    $value = [Environment]::GetEnvironmentVariable($_, 'Process')
    [pscustomobject]@{name = $_; path = $value; under_d = (Test-StoragePath $value)}
})
$nodeModules = Test-Path -LiteralPath (Join-Path $clipRoot 'node_modules') -PathType Container
$blocking = @()
$dependencyMetadata = $null
if ($pythonPresent -and (Test-Path -LiteralPath (Join-Path $clipRoot 'scripts\check_dependencies.py')) -and
    (Test-Path -LiteralPath (Join-Path $clipRoot 'requirements.lock.txt'))) {
    try {
        $dependencyMetadata = (& $python -B (Join-Path $clipRoot 'scripts\check_dependencies.py')) | ConvertFrom-Json
        if ($LASTEXITCODE -ne 0 -or -not $dependencyMetadata.ready) {
            $blocking += 'Clipping dependency versions are missing or differ from requirements.lock.txt.'
        }
    } catch { $blocking += "Dependency metadata check failed: $($_.Exception.Message)" }
}
if (-not (Test-Path -LiteralPath $clipRoot -PathType Container)) { $blocking += 'Pipeline folder is missing.' }
if ($missing.Count -gt 0) { $blocking += 'Pipeline source/manifest files are missing.' }
if (-not $pythonPresent) { $blocking += 'The dedicated Clipping .venv is missing.' }
if (-not $nodeModules) { $blocking += 'Clipping node_modules is missing.' }
if (@($tools | Where-Object { -not $_.available_on_d }).Count -gt 0) { $blocking += 'Required D-drive command locations are missing.' }
if (@($caches | Where-Object { -not $_.under_d }).Count -gt 0) { $blocking += 'Source D:\J.A.R.V.I.S\.runtime\environment.ps1 to bind all caches/temp paths to D.' }
$guardFiles = @('run_guarded.ps1', 'guard_native.cs')
if (@($guardFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $_) -PathType Leaf) }).Count) {
    $blocking += 'Clipping resource guard is missing.'
}
$resources = $null
if (-not $SkipResourceCheck) {
    try {
        $resourceJson = (& (Join-Path $PSScriptRoot 'run_guarded.ps1') -Mode Check -Workload Gpu) -join "`n"
        $resources = $resourceJson | ConvertFrom-Json
    } catch {
        $resources = [pscustomobject]@{ready = $false; reason = "Resource check failed: $($_.Exception.Message)"}
    }
}

[pscustomobject]@{
    status = if ($blocking.Count) { 'blocked' } elseif ($null -ne $resources -and -not $resources.ready) { 'deferred' } else { 'layout_complete' }
    pipeline_root = $clipRoot
    python = $python
    venv_present = $pythonPresent
    missing_files = $missing
    node_modules_present = $nodeModules
    commands = $tools
    caches = $caches
    watch_helper_present = (Test-Path -LiteralPath (Join-Path $clipRoot '.runtime\claude-video\skills\watch\scripts\watch.py') -PathType Leaf)
    dependencies_verified = $false
    dependency_metadata = $dependencyMetadata
    render_verified = $false
    runtime_verification_receipt = (Join-Path $clipRoot '.runtime\pipeline-restore\verification.json')
    resource_guard_present = (@($guardFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $_) -PathType Leaf) }).Count -eq 0)
    resources = $resources
    resource_check_skipped = [bool]$SkipResourceCheck
    blocking_issues = $blocking
} | ConvertTo-Json -Depth 7

if ($blocking.Count) { exit 1 }
if ($null -ne $resources -and -not $resources.ready) { exit 75 }
exit 0
