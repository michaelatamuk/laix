$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$script:failures = @()

function Run-Step {
    param([string]$Name, [string]$Directory, [scriptblock]$Command)
    Write-Host ""
    Write-Host ("=== " + $Name + " ===") -ForegroundColor Cyan
    Push-Location $Directory
    try {
        & $Command
        if ($LASTEXITCODE -ne 0) {
            $script:failures += $Name
            Write-Host ("FAILED: " + $Name) -ForegroundColor Red
        }
    }
    catch {
        $script:failures += $Name
        Write-Host ("FAILED: " + $Name + " - " + $_.Exception.Message) -ForegroundColor Red
    }
    finally {
        Pop-Location
    }
}

Run-Step 'python laix' "$root\python\laix" { py -m pytest -q }
Run-Step 'typescript laix' "$root\typescript\laix" { npm.cmd test }
Run-Step 'typescript conformance' "$root\typescript\laix" { npm.cmd run conformance }
Run-Step 'typescript example attention' "$root" { node --experimental-strip-types examples/typescript/bill_due.mts }
Run-Step 'typescript example action' "$root" { node --experimental-strip-types examples/typescript/action.mts }
Run-Step 'typescript example record' "$root" { node --experimental-strip-types examples/typescript/record.mts }

if ($script:failures.Count -gt 0) {
    Write-Host ""
    Write-Host ("Failed steps: " + ($script:failures -join ', ')) -ForegroundColor Red
    exit 1
}
Write-Host ""
Write-Host "All checks pass." -ForegroundColor Green
