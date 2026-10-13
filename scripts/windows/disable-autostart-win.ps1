param(
    [string]$TaskName = "AutonomousCompany-WSL-Start"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "messages-win.ps1")

if (-not (Get-Command schtasks.exe -ErrorAction SilentlyContinue)) {
    throw (Get-AutonomousCompanyMessage -Key 'schtasks.exe not found.')
}

& schtasks.exe /Query /TN $TaskName | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host (Get-AutonomousCompanyMessage -Key 'Autostart task not found: {0}' -Values @($TaskName))
    exit 0
}

$deleteOutput = & schtasks.exe /Delete /TN $TaskName /F 2>&1
if ($deleteOutput) {
    foreach ($line in $deleteOutput) {
        Write-Host $line
    }
}

if ($LASTEXITCODE -ne 0) {
    if (($deleteOutput -join "`n") -match "Access is denied") {
        throw (Get-AutonomousCompanyMessage -Key 'Failed to delete task due to permission error. Run PowerShell as Administrator and retry.')
    }
    throw (Get-AutonomousCompanyMessage -Key 'Failed to delete scheduled task: {0}' -Values @($TaskName))
}

Write-Host (Get-AutonomousCompanyMessage -Key 'Autostart disabled: {0}' -Values @($TaskName))
