param(
    [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "messages-win.ps1")

function Assert-WslAvailable {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
        throw (Get-AutonomousCompanyMessage -Key 'wsl.exe not found. Enable WSL first.')
    }
}

Assert-WslAvailable

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

& wsl.exe -d $Distro --cd $repoWsl bash -lc "make last"
exit $LASTEXITCODE
