$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$windowsRoot = Join-Path $repoRoot 'scripts/windows'
. (Join-Path $windowsRoot 'messages-win.ps1')
$catalogPath = Join-Path $repoRoot 'i18n/windows-messages.json'
$utf8 = New-Object System.Text.UTF8Encoding($false, $true)
$catalog = ConvertFrom-Json -InputObject $utf8.GetString([System.IO.File]::ReadAllBytes($catalogPath))
$originalLanguage = [Environment]::GetEnvironmentVariable('AUTONOMOUS_COMPANY_LANGUAGE')
$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$testRoot = Join-Path $tempRoot ('autonomous-company-messages-' + [guid]::NewGuid())
$null = New-Item -ItemType Directory -Path $testRoot
$localPath = Join-Path $testRoot '.autonomous-company.local'
$brokenCatalogPath = Join-Path $testRoot 'broken-catalog.json'
$script:checks = 0
$script:failures = @()
$missingWsl = 'wsl.exe not found. Enable WSL first.'
$script:fixtureSystemLanguage = 'zh-CN'
function Get-AutonomousCompanySystemLanguage { return $script:fixtureSystemLanguage }

function Assert-Equal {
    param($Actual, $Expected)
    if ($Actual -cne $Expected) { throw "Expected <$Expected>, got <$Actual>." }
}

function Invoke-MessageCheck {
    param([string]$Name, [scriptblock]$Body)
    $script:checks++
    try {
        Remove-Item Env:AUTONOMOUS_COMPANY_LANGUAGE -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $localPath -ErrorAction SilentlyContinue
        $script:fixtureSystemLanguage = 'zh-CN'
        & $Body
        Write-Host "PASS: $Name"
    } catch {
        $script:failures += "${Name}: $_"
    }
}

try {
    Invoke-MessageCheck 'Chinese system UI defaults are decoded as UTF-8 in both PowerShell editions' {
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath
        $actual = Get-AutonomousCompanyMessage -Key $missingWsl
        Assert-Equal $actual $catalog.PSObject.Properties[$missingWsl].Value.'zh-CN'
        Assert-Equal ([int]$actual[0]) 0x672A
    }

    Invoke-MessageCheck 'English system UI default is used without saved or legacy language' {
        $script:fixtureSystemLanguage = 'en'
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
    }

    Invoke-MessageCheck 'saved global preference takes precedence over legacy environment' {
        [System.IO.File]::WriteAllText($localPath, "# operator setting`nAUTONOMOUS_COMPANY_LANGUAGE=en`nACTIVE_PROJECT=projects/example`n", $utf8)
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
        $before = [System.IO.File]::ReadAllText($localPath)
        $env:AUTONOMOUS_COMPANY_LANGUAGE = 'zh-CN'
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath -Language zh-CN
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
        Assert-Equal ([System.IO.File]::ReadAllText($localPath)) $before
    }

    Invoke-MessageCheck 'current product language survives preference edits and display overrides' {
        $contents = "AUTONOMOUS_COMPANY_LANGUAGE=en`nAUTONOMOUS_COMPANY_PRODUCT_ID=0123456789abcdef0123456789abcdef`nAUTONOMOUS_COMPANY_PRODUCT_LANGUAGE=zh-CN`nAUTONOMOUS_COMPANY_PRODUCT_STATUS=active`n"
        [System.IO.File]::WriteAllText($localPath, $contents, $utf8)
        $env:AUTONOMOUS_COMPANY_LANGUAGE = 'en'
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath -Language EN
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $catalog.PSObject.Properties[$missingWsl].Value.'zh-CN'
        Assert-Equal ([System.IO.File]::ReadAllText($localPath)) $contents
    }

    Invoke-MessageCheck 'legacy environment applies only without a saved preference or product' {
        $env:AUTONOMOUS_COMPANY_LANGUAGE = 'en'
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
        $script:fixtureSystemLanguage = 'en'
        $env:AUTONOMOUS_COMPANY_LANGUAGE = 'zh-CN'
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $catalog.PSObject.Properties[$missingWsl].Value.'zh-CN'
    }

    Invoke-MessageCheck 'explicit language aliases override display without changing environment' {
        $env:AUTONOMOUS_COMPANY_LANGUAGE = 'zh-CN'
        foreach ($value in @('en', 'EN', 'En')) {
            Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath -Language $value
            Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
        }
        $env:AUTONOMOUS_COMPANY_LANGUAGE = 'en'
        foreach ($value in @('zh-CN', 'zh-cn', 'ZH-CN')) {
            Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath -Language $value
            Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $catalog.PSObject.Properties[$missingWsl].Value.'zh-CN'
        }
        Assert-Equal $env:AUTONOMOUS_COMPANY_LANGUAGE 'en'
    }

    Invoke-MessageCheck 'invalid languages fall back to original English diagnostics' {
        foreach ($value in @('invalid', 'EN', 'zh-cn', ' en ')) {
            $env:AUTONOMOUS_COMPANY_LANGUAGE = $value
            Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath
            Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
        }
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath -Language 'invalid'
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
    }

    Invoke-MessageCheck 'malformed local config stays untouched and cannot execute code' {
        foreach ($contents in @('AUTONOMOUS_COMPANY_LANGUAGE=invalid',
            "AUTONOMOUS_COMPANY_LANGUAGE=zh-CN`nAUTONOMOUS_COMPANY_LANGUAGE=en`n",
            'AUTONOMOUS_COMPANY_LANGUAGE="en"', '$(throw ''must not execute'')',
            'export AUTONOMOUS_COMPANY_LANGUAGE=en', "AUTONOMOUS_COMPANY_LANGUAGE=zh-CN`nnot a setting",
            'AUTONOMOUS_COMPANY_PRODUCT_LANGUAGE=zh-CN',
            "ACTIVE_PROJECT=a`nACTIVE_PROJECT=b",
            "AUTONOMOUS_COMPANY_PRODUCT_ID=0123456789abcdef0123456789abcdef`nAUTONOMOUS_COMPANY_PRODUCT_LANGUAGE=zh-CN`nAUTONOMOUS_COMPANY_PRODUCT_STATUS=active",
            "AUTONOMOUS_COMPANY_LANGUAGE=zh-CN`nAUTONOMOUS_COMPANY_PRODUCT_ID=0123456789abcdef0123456789abcdef`nAUTONOMOUS_COMPANY_PRODUCT_LANGUAGE=zh-CN`nAUTONOMOUS_COMPANY_PRODUCT_STATUS=active`nAUTONOMOUS_COMPANY_PRODUCT_EXTRA=yes",
            "AUTONOMOUS_COMPANY_PRODUCT_ID=not-an-id`nAUTONOMOUS_COMPANY_PRODUCT_LANGUAGE=zh-CN`nAUTONOMOUS_COMPANY_PRODUCT_STATUS=active")) {
            [System.IO.File]::WriteAllText($localPath, $contents, $utf8)
            Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath
            Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
            Assert-Equal ([System.IO.File]::ReadAllText($localPath)) $contents
        }
        [System.IO.File]::WriteAllBytes($localPath, [byte[]]@(0xFF, 0xFE, 0x00))
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
    }

    Invoke-MessageCheck 'saved service settings do not override display selection or get rewritten' {
        $savedPath = Join-Path $testRoot '.auto-loop.env'
        $saved = "AUTONOMOUS_COMPANY_LANGUAGE=en`nUSAGE_HARD_LIMIT_USD=12`n"
        [System.IO.File]::WriteAllText($savedPath, $saved, $utf8)
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $catalog.PSObject.Properties[$missingWsl].Value.'zh-CN'
        Assert-Equal ([System.IO.File]::ReadAllText($savedPath)) $saved
    }

    Invoke-MessageCheck 'unavailable and malformed catalogs retain the original error' {
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath (Join-Path $testRoot 'missing.json')
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
        foreach ($contents in @('{broken json', '{}', '{"wsl.exe not found. Enable WSL first.": {"zh-CN": 7}}',
            '{"wsl.exe not found. Enable WSL first.": {"zh-CN": " "}}')) {
            [System.IO.File]::WriteAllText($brokenCatalogPath, $contents, $utf8)
            Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $brokenCatalogPath
            Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
        }
        [System.IO.File]::WriteAllBytes($brokenCatalogPath, [byte[]]@(0xFF))
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $brokenCatalogPath
        Assert-Equal (Get-AutonomousCompanyMessage -Key $missingWsl) $missingWsl
    }

    Invoke-MessageCheck 'placeholders preserve literal paths, braces, dollar signs and raw errors' {
        $literal = 'C:\repo path\{1}\$HOME\$(throw ''must not execute'')'
        foreach ($language in @('en', 'zh-CN')) {
            Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $catalogPath -Language $language
            $actual = Get-AutonomousCompanyMessage -Key 'WSL command failed ({0}): {1}' -Values @(17, $literal)
            if (-not $actual.Contains($literal) -or -not $actual.Contains('17')) { throw 'Diagnostic content changed.' }
        }
        Assert-Equal (Get-AutonomousCompanyMessage -Key 'Unknown {0}: {1}' -Values @($literal, '$&')) ('Unknown ' + $literal + ': $&')
        Assert-Equal (Get-AutonomousCompanyMessage -Key '{0}/{1}' -Values @(0, '')) '0/'
        Assert-Equal (Get-AutonomousCompanyMessage -Key 'Unknown {9}' -Values @('value')) 'Unknown {9}'
    }

    Invoke-MessageCheck 'broken translated placeholders fall back without losing diagnostics' {
        [System.IO.File]::WriteAllText($brokenCatalogPath, '{"Failure {0}": {"zh-CN": "Failure {1}"}}', $utf8)
        Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $brokenCatalogPath
        Assert-Equal (Get-AutonomousCompanyMessage -Key 'Failure {0}' -Values @('raw error')) 'Failure raw error'
    }

    Invoke-MessageCheck 'blank translations retain the original diagnostic' {
        foreach ($blank in @('', '   ')) {
            $broken = @{ 'Failure' = @{ en = 'Failure'; 'zh-CN' = $blank } } | ConvertTo-Json
            [System.IO.File]::WriteAllText($brokenCatalogPath, $broken, $utf8)
            Initialize-AutonomousCompanyMessages -RepoRoot $testRoot -CatalogPath $brokenCatalogPath -Language 'zh-CN'
            Assert-Equal (Get-AutonomousCompanyMessage -Key 'Failure') 'Failure'
        }
    }

    Invoke-MessageCheck 'every catalog entry has both languages and matching placeholders' {
        foreach ($entry in $catalog.PSObject.Properties) {
            Assert-Equal $entry.Value.en $entry.Name
            if (-not $entry.Value.'zh-CN' -or $entry.Value.'zh-CN' -ceq $entry.Name) { throw "Missing Chinese: $($entry.Name)" }
            $expected = @([regex]::Matches($entry.Name, '\{[0-9]+\}') | ForEach-Object { $_.Value } | Sort-Object)
            $actual = @([regex]::Matches($entry.Value.'zh-CN', '\{[0-9]+\}') | ForEach-Object { $_.Value } | Sort-Object)
            Assert-Equal ($actual -join '|') ($expected -join '|')
        }
    }

    Invoke-MessageCheck 'all Windows message call sites use known catalog entries and parse safely' {
        foreach ($file in (Get-ChildItem -LiteralPath $windowsRoot -Filter '*.ps1')) {
            $tokens = $null
            $parseErrors = $null
            $ast = [System.Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$parseErrors)
            if ($parseErrors.Count) { throw ($parseErrors | Out-String) }
            $calls = $ast.FindAll({ param($node)
                $node -is [System.Management.Automation.Language.CommandAst] -and $node.GetCommandName() -eq 'Get-AutonomousCompanyMessage'
            }, $true)
            foreach ($call in $calls) {
                $key = $call.CommandElements[2].Value
                if (-not $catalog.PSObject.Properties[$key]) { throw "Unknown message in $($file.Name): $key" }
            }
        }
    }

    # Execute real entrypoints in a temporary checkout with a strict WSL mock
    # and inert guardian scripts. No real service, process or engine is invoked.
    $fixtureWindows = Join-Path $testRoot 'scripts/windows'
    $fixtureI18n = Join-Path $testRoot 'i18n'
    $null = New-Item -ItemType Directory -Path $fixtureWindows, $fixtureI18n -Force
    foreach ($name in @('start-win.ps1', 'stop-win.ps1', 'messages-win.ps1')) {
        Copy-Item -LiteralPath (Join-Path $windowsRoot $name) -Destination $fixtureWindows
    }
    Copy-Item -LiteralPath $catalogPath -Destination $fixtureI18n
    $guardian = 'param([string]$Action, [string]$Language, [string]$Distro, [string]$RepoWsl)' + "`n" +
        'Write-Output "GUARDIAN_LANGUAGE=$Language ACTION=$Action"; $global:LASTEXITCODE = 0'
    foreach ($name in @('awake-guardian-win.ps1', 'wsl-anchor-win.ps1')) {
        [System.IO.File]::WriteAllText((Join-Path $fixtureWindows $name), $guardian, $utf8)
    }
    $global:autonomousCompanyMessageWslFixture = @{ FailWsl = $false; LocalPath = $localPath }
    function wsl.exe {
        $callArgs = @($args)
        if ($callArgs[0] -cne '-d' -or $callArgs[1] -cne 'Fixture') { throw 'Unexpected distro.' }
        if ($callArgs[2] -ceq 'wslpath') { $global:LASTEXITCODE = 0; return '/fixture' }
        if ($callArgs[2] -cne '--cd' -or $callArgs[3] -cne '/fixture' -or
            $callArgs[4] -cne 'bash' -or $callArgs[5] -cne '-lc') { throw 'Unexpected WSL invocation.' }
        if ($global:autonomousCompanyMessageWslFixture.FailWsl) {
            $global:LASTEXITCODE = 17
            return 'NATIVE ERROR {0} $HOME /raw path'
        }
        if ($callArgs[6] -cmatch '^python3 scripts/core/localization.py set --language (en|zh-CN)$') {
            $selectedLanguage = $Matches[1]
            $path = $global:autonomousCompanyMessageWslFixture.LocalPath
            $contents = if (Test-Path -LiteralPath $path) { [System.IO.File]::ReadAllText($path) } else { '' }
            $contents = [regex]::Replace($contents, '(?m)^AUTONOMOUS_COMPANY_LANGUAGE=[^\r\n]*(?:\r?\n|$)', '')
            [System.IO.File]::WriteAllText($path, "AUTONOMOUS_COMPANY_LANGUAGE=$selectedLanguage`n" + $contents, (New-Object System.Text.UTF8Encoding($false)))
            $global:LASTEXITCODE = 0
            return
        }
        if ($callArgs[6] -notin @(
            'command -v systemctl >/dev/null 2>&1 && systemctl --user --version >/dev/null 2>&1',
            'systemctl --user cat autonomous-company.service >/dev/null 2>&1',
            'bash scripts/wsl/dashboard-wsl.sh check', 'bash scripts/wsl/dashboard-wsl.sh start',
            'bash scripts/wsl/dashboard-wsl.sh stop')) { throw 'Unexpected WSL command.' }
        $global:LASTEXITCODE = 0
    }

    Invoke-MessageCheck 'real start saves explicit preference centrally and preserves service config byte for byte' {
        $env:AUTONOMOUS_COMPANY_LANGUAGE = 'zh-CN'
        $before = [System.IO.File]::ReadAllText((Join-Path $testRoot '.auto-loop.env'))
        $output = @(& (Join-Path $fixtureWindows 'start-win.ps1') -Distro Fixture -Language EN 6>&1) | Out-String
        if (-not $output.Contains('WSL daemon started: autonomous-company.service') -or
            ($output.Split(@('GUARDIAN_LANGUAGE=en ACTION=start'), [StringSplitOptions]::None).Count - 1) -ne 2) {
            throw "Explicit start language did not reach success/guardians: $output"
        }
        $saved = [System.IO.File]::ReadAllText((Join-Path $testRoot '.auto-loop.env'))
        Assert-Equal $saved $before
        Assert-Equal ([System.IO.File]::ReadAllText($localPath)) "AUTONOMOUS_COMPANY_LANGUAGE=en`n"
        Assert-Equal $env:AUTONOMOUS_COMPANY_LANGUAGE 'zh-CN'
    }

    Invoke-MessageCheck 'real start queues preference for next product and retains pinned current language' {
        $contents = "AUTONOMOUS_COMPANY_LANGUAGE=zh-CN`nAUTONOMOUS_COMPANY_PRODUCT_ID=0123456789abcdef0123456789abcdef`nAUTONOMOUS_COMPANY_PRODUCT_LANGUAGE=zh-CN`nAUTONOMOUS_COMPANY_PRODUCT_STATUS=active`n"
        [System.IO.File]::WriteAllText($localPath, $contents, $utf8)
        $savedPath = Join-Path $testRoot '.auto-loop.env'
        $before = [System.IO.File]::ReadAllText($savedPath)
        $output = @(& (Join-Path $fixtureWindows 'start-win.ps1') -Distro Fixture -Language en 6>&1) | Out-String
        if (-not $output.Contains($catalog.PSObject.Properties['WSL daemon started: autonomous-company.service'].Value.'zh-CN') -or
            ($output.Split(@('GUARDIAN_LANGUAGE=zh-CN ACTION=start'), [StringSplitOptions]::None).Count - 1) -ne 2) {
            throw "Current product language changed: $output"
        }
        Assert-Equal ([System.IO.File]::ReadAllText($localPath)) ($contents.Replace('AUTONOMOUS_COMPANY_LANGUAGE=zh-CN', 'AUTONOMOUS_COMPANY_LANGUAGE=en'))
        Assert-Equal ([System.IO.File]::ReadAllText($savedPath)) $before
    }

    Invoke-MessageCheck 'real start with no override reuses saved service environment unchanged' {
        [System.IO.File]::WriteAllText($localPath, 'AUTONOMOUS_COMPANY_LANGUAGE=zh-CN', $utf8)
        $savedPath = Join-Path $testRoot '.auto-loop.env'
        $before = [System.IO.File]::ReadAllText($savedPath)
        $output = @(& (Join-Path $fixtureWindows 'start-win.ps1') -Distro Fixture 6>&1) | Out-String
        if (-not $output.Contains($catalog.PSObject.Properties['WSL daemon started: autonomous-company.service'].Value.'zh-CN') -or
            -not $output.Contains('GUARDIAN_LANGUAGE=zh-CN ACTION=start')) { throw 'Repository language was not used.' }
        Assert-Equal ([System.IO.File]::ReadAllText($savedPath)) $before
    }

    Invoke-MessageCheck 'real stop localizes the result and passes display language to guardians' {
        $env:AUTONOMOUS_COMPANY_LANGUAGE = 'en'
        $output = @(& (Join-Path $fixtureWindows 'stop-win.ps1') -Distro Fixture 6>&1) | Out-String
        if (-not $output.Contains('WSL daemon stopped: autonomous-company.service') -or
            -not $output.Contains('GUARDIAN_LANGUAGE=en ACTION=stop')) { throw 'Stop result language was not preserved.' }
    }

    Invoke-MessageCheck 'real start preserves raw WSL failure before localized wrapper error' {
        $global:autonomousCompanyMessageWslFixture.FailWsl = $true
        try {
            $output = @(& {
                try { & (Join-Path $fixtureWindows 'start-win.ps1') -Distro Fixture -Language zh-CN }
                catch { Write-Output ('CAUGHT: ' + $_.Exception.Message) }
            } 6>&1) | Out-String
            if (-not $output.Contains('NATIVE ERROR {0} $HOME /raw path') -or
                -not $output.Contains('17') -or -not $output.Contains('command -v systemctl') -or
                -not $output.Contains('CAUGHT: ')) { throw "Raw failure was lost: $output" }
        } finally { $global:autonomousCompanyMessageWslFixture.FailWsl = $false }
    }
} finally {
    if ($null -eq $originalLanguage) { Remove-Item Env:AUTONOMOUS_COMPANY_LANGUAGE -ErrorAction SilentlyContinue }
    else { [Environment]::SetEnvironmentVariable('AUTONOMOUS_COMPANY_LANGUAGE', $originalLanguage) }
    Remove-Variable -Name autonomousCompanyMessageWslFixture -Scope Global -ErrorAction SilentlyContinue
    # Verify the absolute GUID fixture is inside TEMP before recursively deleting.
    $resolvedFixture = (Resolve-Path -LiteralPath $testRoot).Path
    if ($resolvedFixture -cne [System.IO.Path]::GetFullPath($testRoot) -or
        -not $resolvedFixture.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -or
        (Split-Path -Leaf $resolvedFixture) -notmatch '^autonomous-company-messages-[0-9a-f-]+$') {
        throw 'Refusing to remove an unexpected fixture path.'
    }
    Remove-Item -LiteralPath $resolvedFixture -Recurse -Force
}

Write-Host "Windows message checks: $($script:checks - $script:failures.Count) passed, $($script:failures.Count) failed, 0 skipped"
if ($script:failures.Count) { throw ($script:failures -join "`n") }
# The final case deliberately sets a failing native code. Report the assertions'
# result to CI, whose PowerShell wrapper exits with the last native exit code.
$global:LASTEXITCODE = 0
