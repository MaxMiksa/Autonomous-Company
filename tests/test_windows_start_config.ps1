$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../scripts/windows/messages-win.ps1')
$scriptPath = Join-Path $PSScriptRoot '../scripts/windows/start-win.ps1'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path $scriptPath).Path, [ref]$tokens, [ref]$parseErrors
)
if ($parseErrors.Count -ne 0) { throw ($parseErrors | Out-String) }
$languageFunction = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'ConvertTo-RuntimeLanguage'
}, $true)
. ([scriptblock]::Create($languageFunction.Extent.Text))
foreach ($value in @('en', 'EN', 'En')) {
    if ((ConvertTo-RuntimeLanguage $value) -cne 'en') { throw "Noncanonical language: $value" }
}
foreach ($value in @('zh-CN', 'zh-cn', 'ZH-CN')) {
    if ((ConvertTo-RuntimeLanguage $value) -cne 'zh-CN') { throw "Noncanonical language: $value" }
}
$functionAst = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Write-AutoLoopEnv'
}, $true)
# Load only this pure configuration function; never invoke WSL or services.
. ([scriptblock]::Create($functionAst.Extent.Text))
$serviceFunction = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Start-AutonomousCompanyService'
}, $true)
. ([scriptblock]::Create($serviceFunction.Extent.Text))
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('autonomous-company-env-' + [guid]::NewGuid())
$null = New-Item -ItemType Directory -Path $testRoot
try {
    $envFile = Join-Path $testRoot '.auto-loop.env'
    $localPath = Join-Path $testRoot '.autonomous-company.local'
    $initial = "# operator settings`nUSAGE_HARD_LIMIT_USD=12`nCODEX_SANDBOX_MODE=read-only`nMODEL=old`nAUTONOMOUS_COMPANY_LANGUAGE=zh-CN`n"
    [System.IO.File]::WriteAllText($envFile, $initial)
    Write-AutoLoopEnv -RepoWin $testRoot
    if ([System.IO.File]::ReadAllText($envFile) -cne $initial) {
        throw 'Start without explicit settings changed the existing environment.'
    }
    Write-AutoLoopEnv -RepoWin $testRoot -EnvLines @('MODEL=new model', 'CLAUDE_BIN=/home/user name/claude')
    $updated = [System.IO.File]::ReadAllText($envFile)
    foreach ($required in @('USAGE_HARD_LIMIT_USD=12', 'CODEX_SANDBOX_MODE=read-only',
                           'MODEL="new model"', 'CLAUDE_BIN="/home/user name/claude"', 'AUTONOMOUS_COMPANY_LANGUAGE=zh-CN')) {
        if (-not $updated.Contains($required)) { throw "Missing preserved/quoted setting: $required" }
    }
    if ($updated.Contains('MODEL=old')) { throw 'Explicit MODEL override was not applied.' }
    $rejected = $false
    try { Write-AutoLoopEnv -RepoWin $testRoot -EnvLines @("MODEL=ok`nENGINE=unsafe") }
    catch { $rejected = $true }
    if (-not $rejected) { throw 'Multiline environment injection was accepted.' }
    if ([System.IO.File]::ReadAllText($envFile) -cne $updated) {
        throw 'Rejected input modified the environment.'
    }
    $script:serviceInstalled = $false
    $script:serviceMismatched = $false
    $script:languageSetFails = $false
    $script:serviceCommands = [System.Collections.Generic.List[string]]::new()
    function Invoke-WslCommand {
        param([string]$RepoWsl, [string]$Command, [switch]$IgnoreExitCode)
        $script:serviceCommands.Add($Command)
        if ($Command -like 'systemctl --user cat*') {
            if ($script:serviceInstalled) { return 0 }
            return 1
        }
        if ($Command -like '*dashboard-wsl.sh check' -and $script:serviceMismatched) {
            throw 'WorkingDirectory mismatch'
        }
        if ($Command -cmatch '^python3 scripts/core/localization.py set --language (en|zh-CN)$') {
            if ($script:languageSetFails) { throw 'Language configuration rejected' }
            if ($script:serviceInstalled -and -not $script:serviceCommands.Contains('bash scripts/wsl/dashboard-wsl.sh check')) {
                throw 'Language was saved before installed service ownership was checked.'
            }
            $nextLanguage = $Matches[1]
            $local = if (Test-Path -LiteralPath $localPath) { [System.IO.File]::ReadAllText($localPath) } else { '' }
            $local = [regex]::Replace($local, '(?m)^AUTONOMOUS_COMPANY_LANGUAGE=[^\r\n]*(?:\r?\n|$)', '')
            [System.IO.File]::WriteAllText($localPath, "AUTONOMOUS_COMPANY_LANGUAGE=$nextLanguage`n" + $local)
        }
        if ($Command -eq 'make install' -or $Command -like '*dashboard-wsl.sh start') {
            $contents = [System.IO.File]::ReadAllText($envFile)
            if (-not $contents.Contains('ENGINE="codex"') -or
                -not $contents.Contains('USAGE_HARD_LIMIT_USD=12')) {
                throw 'Install/start ran before the selected engine and existing budget were persisted.'
            }
            if (-not (Test-Path -LiteralPath $localPath) -or
                -not ([System.IO.File]::ReadAllText($localPath)).Contains('AUTONOMOUS_COMPANY_LANGUAGE=en')) {
                throw 'Install/start ran before the global language preference was persisted.'
            }
            if (-not $contents.Contains('AUTONOMOUS_COMPANY_LANGUAGE=zh-CN')) {
                throw 'Existing service language was unexpectedly rewritten.'
            }
        }
        return 0
    }
    Start-AutonomousCompanyService -RepoWin $testRoot -RepoWsl '/fixture' -EnvLines @('ENGINE=codex') -Language EN
    if (-not $script:serviceCommands.Contains('make install')) { throw 'First install was not exercised.' }
    $beforeMismatch = [System.IO.File]::ReadAllText($envFile)
    $localBeforeMismatch = [System.IO.File]::ReadAllText($localPath)
    $script:serviceInstalled = $true
    $script:serviceMismatched = $true
    $script:serviceCommands.Clear()
    $rejected = $false
    try { Start-AutonomousCompanyService -RepoWin $testRoot -RepoWsl '/fixture' -EnvLines @('ENGINE=claude') -Language zh-CN }
    catch { $rejected = $true }
    if (-not $rejected -or [System.IO.File]::ReadAllText($envFile) -cne $beforeMismatch -or
        [System.IO.File]::ReadAllText($localPath) -cne $localBeforeMismatch) {
        throw 'Mismatched installed service was allowed to change configuration.'
    }
    if ($script:serviceCommands.Contains('make install') -or
        $script:serviceCommands.Contains('bash scripts/wsl/dashboard-wsl.sh start')) {
        throw 'Mismatched installed service was controlled.'
    }
    if (@($script:serviceCommands | Where-Object { $_ -like 'python3 scripts/core/localization.py set*' }).Count) {
        throw 'Mismatched installed service attempted to change the global language.'
    }
    $script:serviceMismatched = $false
    $script:serviceCommands.Clear()
    $script:languageSetFails = $true
    $rejected = $false
    try { Start-AutonomousCompanyService -RepoWin $testRoot -RepoWsl '/fixture' -EnvLines @('ENGINE=claude') -Language en }
    catch { $rejected = $true }
    if (-not $rejected -or [System.IO.File]::ReadAllText($envFile) -cne $beforeMismatch -or
        $script:serviceCommands.Contains('bash scripts/wsl/dashboard-wsl.sh start')) {
        throw 'A failed global language update changed service configuration or started the service.'
    }
    $script:languageSetFails = $false
    $script:serviceCommands.Clear()
    $pinned = "AUTONOMOUS_COMPANY_LANGUAGE=zh-CN`nAUTONOMOUS_COMPANY_PRODUCT_ID=0123456789abcdef0123456789abcdef`nAUTONOMOUS_COMPANY_PRODUCT_LANGUAGE=zh-CN`nAUTONOMOUS_COMPANY_PRODUCT_STATUS=active`n"
    [System.IO.File]::WriteAllText($localPath, $pinned)
    Start-AutonomousCompanyService -RepoWin $testRoot -RepoWsl '/fixture' -Language en
    if ($script:AutonomousCompanyMessageLanguage -cne 'zh-CN' -or
        [System.IO.File]::ReadAllText($localPath) -cne $pinned.Replace('AUTONOMOUS_COMPANY_LANGUAGE=zh-CN', 'AUTONOMOUS_COMPANY_LANGUAGE=en') -or
        [System.IO.File]::ReadAllText($envFile) -cne $beforeMismatch) {
        throw 'Changing the next preference changed the current product or service environment.'
    }
    $script:serviceCommands.Clear()
    Start-AutonomousCompanyService -RepoWin $testRoot -RepoWsl '/fixture'
    if ($script:AutonomousCompanyMessageLanguage -cne 'zh-CN' -or
        @($script:serviceCommands | Where-Object { $_ -like 'python3 scripts/core/localization.py set*' }).Count) {
        throw 'Restart reset the product language or rewrote the global preference.'
    }
    Write-Host 'PASS: explicit Windows config merge, preserved budgets/safety, and multiline rejection'
    Write-Host 'PASS: first install sees central preference; mismatched ownership causes no config/control writes'
    Write-Host 'PASS: failed central setting blocks service changes and startup'
    Write-Host 'PASS: current product language survives future preference changes and restart'
} finally {
    # The GUID directory was created above and contains only this test's fixture.
    Remove-Item -LiteralPath $envFile -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $localPath -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $testRoot
}
