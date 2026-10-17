param(
    [ValidateSet('127.0.0.1', 'localhost')]
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8810,
    [switch]$NoBrowser,
    [string]$DataDirectory,
    [string[]]$Source = @(),
    [string]$WslDistribution,
    [string]$WslUser
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "messages-win.ps1")

$repoWin = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$serverScript = Join-Path $repoWin "dashboard\\center_server.py"
if (-not (Test-Path $serverScript)) {
    throw (Get-AutonomousCompanyMessage -Key 'Dashboard server script not found: {0}' -Values @($serverScript))
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw (Get-AutonomousCompanyMessage -Key 'python not found in PATH.')
}

$url = "http://$BindHost`:$Port/center"
Write-Host (Get-AutonomousCompanyMessage -Key 'Starting dashboard server: {0}' -Values @($url))
Write-Host (Get-AutonomousCompanyMessage -Key 'Press Ctrl+C in this window to stop.')

if (-not $NoBrowser) {
    Start-Process $url | Out-Null
}

$centerArguments = @($serverScript, '--host', $BindHost, '--port', [string]$Port)
if ($DataDirectory) { $centerArguments += @('--data-dir', $DataDirectory) }
foreach ($centerSource in $Source) { $centerArguments += @('--source', $centerSource) }
if ($WslDistribution) { $centerArguments += @('--wsl-distro', $WslDistribution) }
if ($WslUser) { $centerArguments += @('--wsl-user', $WslUser) }
& python @centerArguments
exit $LASTEXITCODE
