$ErrorActionPreference = 'Stop'
$windowsRoot = (Resolve-Path (Join-Path $PSScriptRoot '../scripts/windows')).Path
$global:autonomousCompanyWslPathFixture = @{}
$script:checks = 0
$script:failures = @()

# Model distro-specific mount layouts at the WSL process boundary. No real WSL
# process, service, guardian, or model is started by these tests.
function wsl.exe {
    $callArgs = @($args)
    $global:autonomousCompanyWslPathFixture.wslCalls.Add($callArgs)
    $selected = $global:autonomousCompanyWslPathFixture.defaultDistro
    if ($callArgs[0] -eq '-d') {
        $selected = $callArgs[1]
        $callArgs = @($callArgs | Select-Object -Skip 2)
    }
    if ($callArgs[0] -eq 'wslpath') {
        if ($callArgs.Count -ne 3 -or $callArgs[1] -ne '-a' -or
            $callArgs[2] -cne $global:autonomousCompanyWslPathFixture.expectedWindowsPath) {
            throw 'wslpath did not receive the complete normalized repository path.'
        }
        return "  /mounts/$selected/repo path  "
    }
    if ($callArgs[0] -eq '--cd' -and $callArgs.Count -eq 5 -and
        $callArgs[2] -eq 'bash' -and $callArgs[3] -eq '-lc' -and
        $callArgs[4] -in @('make cycles', 'make last', 'make monitor')) {
        if ($selected -cne $global:autonomousCompanyWslPathFixture.targetDistro -or
            $callArgs[1] -cne "/mounts/$selected/repo path") {
            throw 'The command uses a path resolved in a different distro.'
        }
        $global:LASTEXITCODE = 0
        return
    }
    throw "Unexpected WSL operation: $($callArgs -join ' ')"
}

$scenarios = @(
    @{ Default = 'Ubuntu'; Target = 'Ubuntu' },
    @{ Default = 'docker-desktop'; Target = 'Ubuntu' },
    @{ Default = 'Ubuntu'; Target = 'Debian-Custom' }
)
foreach ($name in @('cycles', 'last', 'monitor', 'status', 'wsl-anchor', 'start', 'stop')) {
    $scriptPath = Join-Path $windowsRoot "$name-win.ps1"
    $tokens = $null
    $parseErrors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile(
        $scriptPath, [ref]$tokens, [ref]$parseErrors
    )
    if ($parseErrors.Count -ne 0) { throw ($parseErrors | Out-String) }
    foreach ($scenario in $scenarios) {
        $script:checks++
        $global:autonomousCompanyWslPathFixture.defaultDistro = $scenario.Default
        $global:autonomousCompanyWslPathFixture.targetDistro = $scenario.Target
        $global:autonomousCompanyWslPathFixture.expectedWindowsPath = (Resolve-Path (Join-Path $windowsRoot '../..')).Path -replace '\\', '/'
        $global:autonomousCompanyWslPathFixture.wslCalls = [System.Collections.Generic.List[object]]::new()
        try {
            & {
                $Distro = $global:autonomousCompanyWslPathFixture.targetDistro
                if ($name -in @('cycles', 'last', 'monitor')) {
                    # These read-only entrypoints also verify the converted path
                    # is forwarded to their subsequent WSL command.
                    & $scriptPath -Distro $Distro
                } else {
                    $functionName = 'Get-RepoPaths'
                    if ($name -eq 'wsl-anchor') { $functionName = 'Resolve-RepoWslPath' }
                    $functionAst = $ast.Find({ param($node)
                        $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
                        $node.Name -eq $functionName
                    }, $true)
                    if (-not $functionAst) { throw "Missing resolver: $functionName" }
                    # Load the actual resolver only, keeping service side effects out.
                    $repoWin = (Resolve-Path (Join-Path $windowsRoot '../..')).Path
                    if ($name -eq 'wsl-anchor') {
                        $resolved = & $functionAst.Body.GetScriptBlock() -RawRepoWsl ''
                    } else {
                        $resolved = (& $functionAst.Body.GetScriptBlock()).RepoWsl
                    }
                    if ($resolved -cne "/mounts/$Distro/repo path") {
                        throw "Wrong distro mount path: $resolved"
                    }
                }
            }
            $expectedCalls = 1
            if ($name -in @('cycles', 'last', 'monitor')) { $expectedCalls = 2 }
            if ($global:autonomousCompanyWslPathFixture.wslCalls.Count -ne $expectedCalls) { throw 'Unexpected WSL call count.' }
            $conversion = $global:autonomousCompanyWslPathFixture.wslCalls[0]
            if ($conversion[0] -ne '-d' -or $conversion[1] -cne $scenario.Target -or
                $conversion[2] -ne 'wslpath') {
                throw 'wslpath did not receive the explicitly selected distro.'
            }
            Write-Host "PASS: $name default=$($scenario.Default) target=$($scenario.Target)"
        } catch {
            $script:failures += "$name default=$($scenario.Default) target=$($scenario.Target): $_"
        }
    }
}

$script:checks++
try {
    $global:autonomousCompanyWslPathFixture.wslCalls.Clear()
    $anchorPath = Join-Path $windowsRoot 'wsl-anchor-win.ps1'
    $anchorAst = [System.Management.Automation.Language.Parser]::ParseFile(
        $anchorPath, [ref]$tokens, [ref]$parseErrors
    )
    $resolver = $anchorAst.Find({ param($node)
        $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
        $node.Name -eq 'Resolve-RepoWslPath'
    }, $true)
    . ([scriptblock]::Create($resolver.Extent.Text))
    if ((Resolve-RepoWslPath -RawRepoWsl '/supplied/repo path') -cne '/supplied/repo path' -or
        $global:autonomousCompanyWslPathFixture.wslCalls.Count -ne 0) {
        throw 'An explicitly supplied WSL path was unnecessarily converted.'
    }
    Write-Host 'PASS: anchor preserves an explicitly supplied WSL path without conversion'
} catch {
    $script:failures += "anchor explicit path: $_"
}

Write-Host "Windows WSL path checks: $($script:checks - $script:failures.Count) passed, $($script:failures.Count) failed, 0 skipped"
Remove-Variable -Name autonomousCompanyWslPathFixture -Scope Global
if ($script:failures.Count) { throw ($script:failures -join "`n") }
