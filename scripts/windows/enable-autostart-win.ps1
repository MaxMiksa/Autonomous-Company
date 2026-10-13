param(
    [string]$Distro = "Ubuntu",
    [string]$TaskName = "AutonomousCompany-WSL-Start"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "messages-win.ps1")

if (-not (Get-Command schtasks.exe -ErrorAction SilentlyContinue)) {
    throw (Get-AutonomousCompanyMessage -Key 'schtasks.exe not found.')
}

$repoWin = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$startScript = Join-Path $repoWin "scripts\\windows\\start-win.ps1"
if (-not (Test-Path $startScript)) {
    throw (Get-AutonomousCompanyMessage -Key 'scripts/windows/start-win.ps1 not found: {0}' -Values @($startScript))
}

$taskAction = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File ""$startScript"" -Distro ""$Distro"""
$createOutput = & schtasks.exe /Create /TN $TaskName /SC ONLOGON /TR $taskAction /RL LIMITED /F 2>&1
if ($createOutput) {
    foreach ($line in $createOutput) {
        Write-Host $line
    }
}

if ($LASTEXITCODE -ne 0) {
    if (($createOutput -join "`n") -match "Access is denied") {
        throw (Get-AutonomousCompanyMessage -Key 'Failed to create task due to permission error. Run PowerShell as Administrator and retry.')
    }
    throw (Get-AutonomousCompanyMessage -Key 'Failed to create/update scheduled task: {0}' -Values @($TaskName))
}

Write-Host (Get-AutonomousCompanyMessage -Key 'Autostart enabled: {0}' -Values @($TaskName))
Write-Host "Action: $taskAction"
