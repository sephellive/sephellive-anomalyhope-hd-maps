[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$GamePath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [string]$ArchivePath,

    [string]$TexconvPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$temporaryRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("anomalyhope-maps-" + [guid]::NewGuid().ToString('N'))
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$python = Get-Command python.exe -ErrorAction Stop

try {
    if ([string]::IsNullOrWhiteSpace($TexconvPath)) {
        $TexconvPath = (Get-Command texconv.exe -ErrorAction Stop).Source
    }
    $resolvedGame = (Resolve-Path -LiteralPath $GamePath).Path
    $resolvedTexconv = (Resolve-Path -LiteralPath $TexconvPath).Path
    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
    if (Test-Path -LiteralPath $resolvedOutput) {
        throw "OutputPath must not already exist: $resolvedOutput"
    }

    & $python.Source -c 'from PIL import Image' 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw 'Pillow is missing. Run: python -m pip install -r requirements.txt'
    }

    & (Join-Path $PSScriptRoot 'extract_anomaly_resources.ps1') `
        -GamePath $resolvedGame -OutputPath $temporaryRoot
    if ($LASTEXITCODE -ne 0) { throw 'Map resource extraction failed.' }

    & $python.Source (Join-Path $PSScriptRoot 'upscale_maps.py') `
        --extracted-root $temporaryRoot `
        --manifest (Join-Path $repositoryRoot 'assets\manifest\maps.json') `
        --output-root $resolvedOutput `
        --texconv $resolvedTexconv
    if ($LASTEXITCODE -ne 0) { throw 'HD map build failed.' }

    & $python.Source (Join-Path $PSScriptRoot 'validate_map_build.py') `
        --manifest (Join-Path $repositoryRoot 'assets\manifest\maps.json') `
        --output-root $resolvedOutput
    if ($LASTEXITCODE -ne 0) { throw 'HD map validation failed.' }

    if (-not [string]::IsNullOrWhiteSpace($ArchivePath)) {
        $resolvedArchive = [System.IO.Path]::GetFullPath($ArchivePath)
        $archiveParent = Split-Path -Parent $resolvedArchive
        New-Item -ItemType Directory -Path $archiveParent -Force | Out-Null
        Compress-Archive -Path (Join-Path $resolvedOutput 'gamedata') -DestinationPath $resolvedArchive -Force
        Write-Host "MO2 archive: $resolvedArchive"
    }
    Write-Host "MO2-ready add-on: $resolvedOutput"
}
finally {
    if (Test-Path -LiteralPath $temporaryRoot) {
        Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
    }
}
