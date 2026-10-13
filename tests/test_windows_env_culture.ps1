param([ValidateSet('tr-TR', 'en-US')][string]$CultureName)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../scripts/windows/messages-win.ps1')
if (-not $CultureName) {
    # PowerShell caches compiled regexes across culture changes. Give each
    # culture a fresh process, using the same PowerShell edition as this test.
    $powershellPath = (Get-Process -Id $PID).Path
    $failedCultures = @()
    foreach ($name in @('tr-TR', 'en-US')) {
        & $powershellPath -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath -CultureName $name
        if ($LASTEXITCODE -ne 0) { $failedCultures += $name }
    }
    Write-Host "Windows culture checks: $(2 - $failedCultures.Count) passed, $($failedCultures.Count) failed, 0 skipped"
    if ($failedCultures.Count) { throw "Culture checks failed: $($failedCultures -join ', ')" }
    return
}
$scriptPath = (Resolve-Path (Join-Path $PSScriptRoot '../scripts/windows/start-win.ps1')).Path
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    $scriptPath, [ref]$tokens, [ref]$parseErrors
)
if ($parseErrors.Count -ne 0) { throw ($parseErrors | Out-String) }
$functionAst = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Write-AutoLoopEnv'
}, $true)
if (-not $functionAst) { throw 'Missing Write-AutoLoopEnv function.' }
# Exercise the real merge function without starting WSL, guardians, or services.
. ([scriptblock]::Create($functionAst.Extent.Text))
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('autonomous-company-culture-' + [guid]::NewGuid())
$null = New-Item -ItemType Directory -Path $testRoot
$envFile = Join-Path $testRoot '.auto-loop.env'
$originalCulture = [System.Threading.Thread]::CurrentThread.CurrentCulture
$failures = @()
try {
    foreach ($cultureName in @($CultureName)) {
        try {
            [System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::GetCultureInfo($cultureName)
            $preserved = @('# operator settings', '', 'USAGE_HARD_LIMIT_USD=12',
                'CODEX_SANDBOX_MODE=read-only', 'custom_setting=keep me', 'i_local=keep too')
            $initial = $preserved + @('ENGINE=old', 'ENGINE=older', 'LOOP_INTERVAL=10',
                'CYCLE_TIMEOUT_SECONDS=300', 'CLAUDE_PERMISSION_MODE=old', 'MODEL=old')
            [System.IO.File]::WriteAllLines($envFile, $initial)
            foreach ($run in 1..3) {
                $updates = @("ENGINE=engine-$run", "LOOP_INTERVAL=$($run * 30)",
                    "CYCLE_TIMEOUT_SECONDS=$($run * 900)", "CLAUDE_PERMISSION_MODE=mode-$run", "MODEL=model $run")
                Write-AutoLoopEnv -RepoWin $testRoot -EnvLines $updates
                $actual = [System.IO.File]::ReadAllLines($envFile)
                $expectedUpdates = @($updates | Sort-Object | ForEach-Object {
                    $key, $value = $_ -split '=', 2
                    $key + '="' + $value + '"'
                })
                $expected = $preserved + $expectedUpdates
                if (($actual -join "`n") -cne ($expected -join "`n")) {
                    throw "Run $run did not replace existing keys exactly once and preserve unrelated lines. Actual: $($actual -join ' | ')"
                }
                # Reapplying identical settings must also leave the file stable.
                $beforeRepeat = [System.IO.File]::ReadAllText($envFile)
                Write-AutoLoopEnv -RepoWin $testRoot -EnvLines $updates
                if ([System.IO.File]::ReadAllText($envFile) -cne $beforeRepeat) {
                    throw "Run $run appended duplicate keys on an identical write."
                }
                Write-AutoLoopEnv -RepoWin $testRoot
                if ([System.IO.File]::ReadAllText($envFile) -cne $beforeRepeat) {
                    throw "Run $run changed settings with no explicit overrides."
                }
            }
            Write-Host "PASS: $cultureName repeated merges replace keys once and preserve operator settings"
        } catch {
            $failures += "${cultureName}: $_"
        } finally {
            [System.Threading.Thread]::CurrentThread.CurrentCulture = $originalCulture
        }
    }
} finally {
    [System.Threading.Thread]::CurrentThread.CurrentCulture = $originalCulture
    # Delete only this test's known file and its empty GUID directory.
    Remove-Item -LiteralPath $envFile -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $testRoot
}
if ($failures.Count) { throw ($failures -join "`n") }
