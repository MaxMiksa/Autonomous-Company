param(
    [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "messages-win.ps1")
$script:LastWslExitCode = 0

function Assert-WslAvailable {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
        throw (Get-AutonomousCompanyMessage -Key 'wsl.exe not found. Enable WSL first.')
    }
}

function Get-RepoPaths {
    $repoWin = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
    $repoWinForWsl = $repoWin -replace "\\", "/"
    $repoWslRaw = & wsl.exe -d $Distro wslpath -a "$repoWinForWsl"
    if (-not $repoWslRaw) {
        throw (Get-AutonomousCompanyMessage -Key 'Failed to convert repository path to WSL path.')
    }
    $repoWsl = $repoWslRaw.Trim()
    if (-not $repoWsl) {
        throw (Get-AutonomousCompanyMessage -Key 'Failed to convert repository path to WSL path.')
    }
    return @{
        RepoWin = $repoWin
        RepoWsl = $repoWsl
    }
}

function Invoke-WslCommand {
    param(
        [Parameter(Mandatory = $true)][string]$RepoWsl,
        [Parameter(Mandatory = $true)][string]$Command,
        [switch]$IgnoreExitCode
    )

    $output = & wsl.exe -d $Distro --cd $RepoWsl bash -lc $Command 2>&1
    $code = $LASTEXITCODE
    $script:LastWslExitCode = $code
    if ($output) {
        foreach ($line in $output) {
            Write-Output $line
        }
    }
    if (-not $IgnoreExitCode -and $code -ne 0) {
        throw (Get-AutonomousCompanyMessage -Key 'WSL command failed ({0}): {1}' -Values @($code, $Command))
    }
}

function Get-AutostartTaskState {
    if (-not (Get-Command cmd.exe -ErrorAction SilentlyContinue)) {
        return "unavailable"
    }

    & cmd.exe /c "schtasks /Query /TN ""AutonomousCompany-WSL-Start"" /FO LIST >nul 2>&1"
    $code = $LASTEXITCODE
    if ($code -eq 0) {
        return "configured"
    }
    if ($code -eq 1) {
        return "not_configured"
    }
    return "unknown"
}

Assert-WslAvailable
$paths = Get-RepoPaths
$repoWin = $paths.RepoWin
$repoWsl = $paths.RepoWsl

Write-Output "=== Windows Guardian ==="
$awakeScript = Join-Path $repoWin "scripts\\windows\\awake-guardian-win.ps1"
if (Test-Path $awakeScript) {
    & $awakeScript -Action status
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Awake guardian status command returned non-zero."
    }
} else {
    Write-Output "Awake guardian script not found."
}

Write-Output ""
Write-Output "=== WSL Keepalive Anchor ==="
$anchorScript = Join-Path $repoWin "scripts\\windows\\wsl-anchor-win.ps1"
if (Test-Path $anchorScript) {
    & $anchorScript -Action status -Distro $Distro -RepoWsl $repoWsl
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "WSL anchor status command returned non-zero."
    }
} else {
    Write-Output "WSL anchor script not found."
}

Write-Output ""
Write-Output "=== Windows Autostart Task ==="
switch (Get-AutostartTaskState) {
    "configured" { Write-Output "Autostart: CONFIGURED (AutonomousCompany-WSL-Start)" }
    "not_configured" { Write-Output "Autostart: NOT CONFIGURED" }
    "unavailable" { Write-Output "Autostart: schtasks unavailable" }
    default { Write-Output "Autostart: UNKNOWN (query failed)" }
}

Write-Output ""
Write-Output "=== WSL Daemon (systemd --user) ==="
Invoke-WslCommand -RepoWsl $repoWsl -Command "systemctl --user cat autonomous-company.service >/dev/null 2>&1" -IgnoreExitCode
if ($script:LastWslExitCode -eq 0) {
    Invoke-WslCommand -RepoWsl $repoWsl -Command "systemctl --user is-active autonomous-company.service || true" -IgnoreExitCode
    Invoke-WslCommand -RepoWsl $repoWsl -Command "systemctl --user show autonomous-company.service -p MainPID -p ActiveState -p SubState --no-pager" -IgnoreExitCode
} else {
    Write-Output "autonomous-company.service: not installed"
}

Write-Output ""
Write-Output "=== Loop Status (monitor.sh) ==="
Invoke-WslCommand -RepoWsl $repoWsl -Command "make status" -IgnoreExitCode

exit 0
