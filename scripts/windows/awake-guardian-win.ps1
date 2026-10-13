param(
    [ValidateSet("start", "stop", "status", "run")]
    [string]$Action = "status",
    [int]$HeartbeatSeconds = 20,
    [ValidateSet("zh-CN", "en")][string]$Language
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "messages-win.ps1")
if ($PSBoundParameters.ContainsKey("Language")) { Initialize-AutonomousCompanyMessages -Language $Language }

$repoWin = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$pidFile = Join-Path $repoWin ".auto-loop-awake.pid"
$stopFile = Join-Path $repoWin ".auto-loop-awake.stop"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

if (-not ("AutonomousCompanySleepGuard.NativeMethods" -as [type])) {
    Add-Type -TypeDefinition @"
using System.Runtime.InteropServices;
namespace AutonomousCompanySleepGuard {
    public static class NativeMethods {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern uint SetThreadExecutionState(uint esFlags);
    }
}
"@
}

$ES_SYSTEM_REQUIRED = [uint32]0x00000001
$ES_AWAYMODE_REQUIRED = [uint32]0x00000040
$ES_CONTINUOUS = [uint32]2147483648
$RUN_FLAGS = $ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_AWAYMODE_REQUIRED

function Get-RunningGuardianProcess {
    if (-not (Test-Path $pidFile)) {
        return $null
    }

    $pidText = [string](Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    $pidText = $pidText.Trim()
    if (-not $pidText) {
        return $null
    }

    $pidValue = 0
    if (-not [int]::TryParse($pidText, [ref]$pidValue)) {
        return $null
    }

    $proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if (-not $proc) {
        return $null
    }

    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $pidValue" -ErrorAction SilentlyContinue).CommandLine
    if ($cmd -and $cmd -match ('(?:^|\s)-File\s+"?' + [regex]::Escape($PSCommandPath) + '"?(?=\s|$)') -and $cmd -match "-Action\s+run") {
        return $proc
    }
    return $null
}

function Clear-StateFiles {
    Remove-Item $pidFile -ErrorAction SilentlyContinue
    Remove-Item $stopFile -ErrorAction SilentlyContinue
}

switch ($Action) {
    "start" {
        $existing = Get-RunningGuardianProcess
        if ($existing) {
            Write-Output (Get-AutonomousCompanyMessage -Key 'Awake guardian already running (PID {0}).' -Values @($existing.Id))
            exit 0
        }

        Remove-Item $stopFile -ErrorAction SilentlyContinue
        $selfPath = $PSCommandPath
        $proc = Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -PassThru -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", ('"' + $selfPath + '"'),
            "-Action", "run",
            "-HeartbeatSeconds", "$HeartbeatSeconds"
        )

        for ($i = 0; $i -lt 20; $i++) {
            Start-Sleep -Milliseconds 200
            $running = Get-RunningGuardianProcess
            if ($running) {
                Write-Output (Get-AutonomousCompanyMessage -Key 'Awake guardian started (PID {0}).' -Values @($running.Id))
                exit 0
            }
        }

        if ($proc -and -not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
        Write-Error (Get-AutonomousCompanyMessage -Key 'Failed to start awake guardian.')
        exit 1
    }

    "run" {
        [System.IO.File]::WriteAllText($pidFile, "$PID`n", $utf8NoBom)
        Remove-Item $stopFile -ErrorAction SilentlyContinue

        try {
            $state = [AutonomousCompanySleepGuard.NativeMethods]::SetThreadExecutionState($RUN_FLAGS)
            if ($state -eq 0) {
                throw (Get-AutonomousCompanyMessage -Key 'SetThreadExecutionState failed at startup.')
            }

            while (-not (Test-Path $stopFile)) {
                Start-Sleep -Seconds $HeartbeatSeconds
                [void][AutonomousCompanySleepGuard.NativeMethods]::SetThreadExecutionState($RUN_FLAGS)
            }
        }
        finally {
            [void][AutonomousCompanySleepGuard.NativeMethods]::SetThreadExecutionState($ES_CONTINUOUS)
            Clear-StateFiles
        }
        exit 0
    }

    "stop" {
        $existing = Get-RunningGuardianProcess
        if (-not $existing) {
            Clear-StateFiles
            Write-Output (Get-AutonomousCompanyMessage -Key 'Awake guardian is not running.')
            exit 0
        }

        [System.IO.File]::WriteAllText($stopFile, "1`n", $utf8NoBom)
        Start-Sleep -Milliseconds 500
        if (-not $existing.HasExited) {
            $owned = Get-RunningGuardianProcess
            if ($owned -and $owned.StartTime -eq $existing.StartTime) {
                Stop-Process -InputObject $owned -Force
                if (-not $owned.WaitForExit(3000)) { throw "Awake guardian cleanup is incomplete." }
            }
        }
        if (Get-RunningGuardianProcess) { throw "Awake guardian is still running." }
        Clear-StateFiles
        Write-Output (Get-AutonomousCompanyMessage -Key 'Awake guardian stopped.')
        exit 0
    }

    "status" {
        $existing = Get-RunningGuardianProcess
        if ($existing) {
            Write-Output "Awake guardian: RUNNING (PID $($existing.Id))"
        } else {
            Write-Output "Awake guardian: STOPPED"
        }
        exit 0
    }
}
