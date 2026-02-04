<#
Create a reproducibility tarball containing results, data, manifests, and scripts.

Usage:
  .\scripts\create_repro_bundle.ps1
#>
Param(
    [string]$Out = 'reproducibility_bundle.zip'
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $root\.. | Out-Null

if(Test-Path $Out){ Remove-Item $Out -Force }

$items = @(
    'results',
    'data',
    'ml/models',
    'cluster',
    'chaos',
    'scripts',
    'docs',
    'Dockerfile.tfbase'
)

Write-Host "Creating $Out with: $($items -join ', ')"
Compress-Archive -Path $items -DestinationPath $Out -Force
Write-Host "Wrote: $(Resolve-Path $Out)"
Pop-Location | Out-Null
