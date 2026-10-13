param(
    [string]$TaskName = "AutonomousCompany-WSL-Start"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "messages-win.ps1")

if (-not (Get-Command schtasks.exe -ErrorAction SilentlyContinue)) {
    throw (Get-AutonomousCompanyMessage -Key 'schtasks.exe not found.')
}

$queryOutput = & schtasks.exe /Query /TN $TaskName /V /FO LIST 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Autostart: NOT CONFIGURED ($TaskName)"
    exit 0
}

foreach ($line in $queryOutput) {
    Write-Host $line
}
Write-Host "Autostart: CONFIGURED ($TaskName)"
