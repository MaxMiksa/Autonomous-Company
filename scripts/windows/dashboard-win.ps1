param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8787,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "messages-win.ps1")

$repoWin = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$serverScript = Join-Path $repoWin "dashboard\\server.py"
if (-not (Test-Path $serverScript)) {
    throw (Get-AutonomousCompanyMessage -Key 'Dashboard server script not found: {0}' -Values @($serverScript))
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw (Get-AutonomousCompanyMessage -Key 'python not found in PATH.')
}

$url = "http://$BindHost`:$Port"
Write-Host (Get-AutonomousCompanyMessage -Key 'Starting dashboard server: {0}' -Values @($url))
Write-Host (Get-AutonomousCompanyMessage -Key 'Press Ctrl+C in this window to stop.')

if (-not $NoBrowser) {
    Start-Process $url | Out-Null
}

& python $serverScript --host $BindHost --port $Port
exit $LASTEXITCODE
