# Keep this script ASCII so Windows PowerShell 5.1 reads it without a BOM.
# User-visible text lives in the UTF-8 catalog; native tool output is untouched.

function Assert-AutonomousCompanyNamespace {
    param([string]$RepoRoot = (Join-Path $PSScriptRoot '../..'))
    if (Test-Path -LiteralPath (Join-Path $RepoRoot '.autonomous-company-migration-in-progress.json')) {
        throw 'Namespace migration is in progress; complete or roll it back before starting.'
    }
    $oldKeys = @([Environment]::GetEnvironmentVariables().Keys | Where-Object { $_.StartsWith('AUTO_COMPANY_') })
    if ($oldKeys.Count -gt 0) { throw 'Legacy environment names require one-time migration before use.' }
    if (Get-ChildItem -LiteralPath $RepoRoot -Force -Filter '.auto-company*' -ErrorAction SilentlyContinue) {
        throw 'Old Auto-Company state requires scripts/migrate-name.py before use.'
    }
    foreach ($name in @('.auto-loop.env', '.autonomous-company.local')) {
        $file = Join-Path $RepoRoot $name
        if ((Test-Path -LiteralPath $file -PathType Leaf) -and
            ([IO.File]::ReadAllText($file) -match '(?m)^AUTO_COMPANY_[A-Z0-9_]*=')) {
            throw 'Legacy configuration keys require one-time migration before use.'
        }
    }
}

function Get-AutonomousCompanySystemLanguage {
    try {
        # CurrentUICulture can inherit a hosting shell's language instead of the
        # Windows user's display language. Query the same OS API as the runtime.
        if (-not ('AutonomousCompany.Localization.NativeMethods' -as [type])) {
            Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
namespace AutonomousCompany.Localization {
    public static class NativeMethods {
        [DllImport("kernel32.dll")]
        public static extern ushort GetUserDefaultUILanguage();
    }
}
'@
        }
        $languageId = [AutonomousCompany.Localization.NativeMethods]::GetUserDefaultUILanguage()
        $cultureName = [System.Globalization.CultureInfo]::GetCultureInfo([int]$languageId).Name
        if ($cultureName -imatch '^zh(?:-|$)') { return 'zh-CN' }
    } catch {
        # Use a readable fallback if the Windows UI language is unavailable.
    }
    return 'en'
}

function Initialize-AutonomousCompanyMessages {
    param(
        [string]$RepoRoot = (Join-Path $PSScriptRoot '../..'),
        [string]$Language,
        [string]$CatalogPath
    )

    $script:AutonomousCompanyMessageLanguage = 'en'
    $script:AutonomousCompanyMessageCatalog = $null
    try {
        # Read the same shared state as the runtime. Legacy guardian arguments
        # are display fallbacks only; they cannot override a product or setting.
        $fallbackLanguage = $null
        if ($PSBoundParameters.ContainsKey('Language')) {
            if ($Language -ieq 'en') { $fallbackLanguage = 'en' }
            elseif ($Language -ieq 'zh-CN') { $fallbackLanguage = 'zh-CN' }
            else { throw 'Invalid language.' }
        }
        $settings = @{}
        $localPath = Join-Path $RepoRoot '.autonomous-company.local'
        if (Test-Path -LiteralPath $localPath) {
            $item = Get-Item -LiteralPath $localPath -Force -ErrorAction Stop
            if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
                throw 'Local configuration must not be a symlink.'
            }
            $utf8 = New-Object System.Text.UTF8Encoding($false, $true)
            $localText = $utf8.GetString([System.IO.File]::ReadAllBytes($localPath))
            foreach ($line in ($localText -split '\r\n|\n|\r')) {
                if (-not $line.Trim() -or $line.TrimStart().StartsWith('#')) { continue }
                if ($line -cnotmatch '^([A-Z][A-Z0-9_]*)=(.*)$') {
                    throw 'Invalid local configuration.'
                }
                if ($settings.ContainsKey($Matches[1])) { throw 'Duplicate local setting.' }
                $settings[$Matches[1]] = $Matches[2]
            }
        }
        if ($settings.ContainsKey('AUTONOMOUS_COMPANY_LANGUAGE') -and
            $settings['AUTONOMOUS_COMPANY_LANGUAGE'] -cnotin @('zh-CN', 'en')) {
            throw 'Invalid language.'
        }
        $productKeys = @($settings.Keys | Where-Object { $_.StartsWith('AUTONOMOUS_COMPANY_PRODUCT_') })
        if ($productKeys.Count -gt 0) {
            if ($productKeys.Count -ne 3 -or -not $settings.ContainsKey('AUTONOMOUS_COMPANY_LANGUAGE') -or
                $settings['AUTONOMOUS_COMPANY_PRODUCT_ID'] -cnotmatch '^[0-9a-f]{32}$' -or
                $settings['AUTONOMOUS_COMPANY_PRODUCT_STATUS'] -cne 'active' -or
                $settings['AUTONOMOUS_COMPANY_PRODUCT_LANGUAGE'] -cnotin @('zh-CN', 'en')) {
                throw 'Invalid product language state.'
            }
            $selected = $settings['AUTONOMOUS_COMPANY_PRODUCT_LANGUAGE']
        } elseif ($settings.ContainsKey('AUTONOMOUS_COMPANY_LANGUAGE')) {
            $selected = $settings['AUTONOMOUS_COMPANY_LANGUAGE']
        } elseif ($null -ne $fallbackLanguage) {
            $selected = $fallbackLanguage
        } else {
            $selected = [Environment]::GetEnvironmentVariable('AUTONOMOUS_COMPANY_LANGUAGE')
            if ($null -eq $selected) {
                $selected = Get-AutonomousCompanySystemLanguage
            }
        }
        if ($selected -cnotin @('zh-CN', 'en')) { throw 'Invalid language.' }
        $script:AutonomousCompanyMessageLanguage = $selected
    } catch {
        # English is the original diagnostic text. Let the runtime report its
        # own invalid configuration rather than fail while rendering an error.
        $script:AutonomousCompanyMessageLanguage = 'en'
    }

    try {
        if (-not $CatalogPath) { $CatalogPath = Join-Path $RepoRoot 'i18n/windows-messages.json' }
        $utf8 = New-Object System.Text.UTF8Encoding($false, $true)
        $catalogText = $utf8.GetString([System.IO.File]::ReadAllBytes($CatalogPath))
        $script:AutonomousCompanyMessageCatalog = ConvertFrom-Json -InputObject $catalogText -ErrorAction Stop
    } catch {
        # The English key is also the fallback when a catalog is unavailable.
        $script:AutonomousCompanyMessageCatalog = $null
    }
}

function Get-AutonomousCompanyMessage {
    param(
        [Parameter(Mandatory = $true)][string]$Key,
        [object[]]$Values = @()
    )

    $template = $Key
    if ($null -ne $script:AutonomousCompanyMessageCatalog) {
        $entry = $script:AutonomousCompanyMessageCatalog.PSObject.Properties[$Key]
        if ($null -ne $entry -and $null -ne $entry.Value) {
            $translation = $entry.Value.PSObject.Properties[$script:AutonomousCompanyMessageLanguage]
            if ($null -ne $translation -and $translation.Value -is [string] -and
                -not [string]::IsNullOrWhiteSpace($translation.Value)) {
                # A stale/broken translation must not drop diagnostic values.
                $expected = @([regex]::Matches($Key, '\{[0-9]+\}') | ForEach-Object { $_.Value } | Sort-Object -Unique)
                $actual = @([regex]::Matches($translation.Value, '\{[0-9]+\}') | ForEach-Object { $_.Value } | Sort-Object -Unique)
                if (($expected -join '|') -ceq ($actual -join '|')) {
                    $template = $translation.Value
                }
            }
        }
    }
    # One pass and a match evaluator keep $, braces, paths and untrusted native
    # diagnostics literal; neither shell expansion nor format-string evaluation.
    $resolvedValues = $Values
    return [regex]::Replace($template, '\{([0-9]+)\}', [System.Text.RegularExpressions.MatchEvaluator]{
        param($match)
        $index = 0
        if ([int]::TryParse($match.Groups[1].Value, [ref]$index) -and $index -lt $resolvedValues.Count) {
            return [string]$resolvedValues[$index]
        }
        return $match.Value
    })
}

Initialize-AutonomousCompanyMessages
