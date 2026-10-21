param(
    [Parameter(Mandatory = $true)]
    [string]$GamePath,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

$game = (Resolve-Path -LiteralPath $GamePath).Path
$output = [System.IO.Path]::GetFullPath($OutputPath)
$converter = Join-Path $game 'tools\converter.exe'
$configArchive = Join-Path $game 'db\configs\configs.db0'
$uiArchive = Join-Path $game 'db\textures\textures_ui.db0'
$textureArchives = Get-ChildItem (Join-Path $game 'db\textures') -File -Filter '*.db*'

if (-not (Test-Path -LiteralPath $converter -PathType Leaf)) {
    throw "Anomaly converter.exe was not found under $game\tools"
}
if (-not (Test-Path -LiteralPath $configArchive -PathType Leaf)) {
    throw "Required Anomaly archive is missing: $configArchive"
}
if (-not (Test-Path -LiteralPath $uiArchive -PathType Leaf)) {
    throw "Required Anomaly archive is missing: $uiArchive"
}
if (Test-Path -LiteralPath $output) {
    throw "Output path must not already exist: $output"
}
if ($output.StartsWith($game + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output path must be outside the Anomaly installation.'
}

$metadataRoot = Join-Path $output 'metadata'
$mapOutput = $output
$globalOutput = $output
New-Item -ItemType Directory -Path $metadataRoot,$output -Force | Out-Null

$configOutput = $metadataRoot
& $converter -unpack -xdb $configArchive -dir $configOutput
if ($LASTEXITCODE -ne 0) {
    throw "Failed to extract $configArchive (exit $LASTEXITCODE)"
}

$globalFilter = '\ui\ui_global_map.dds'
& $converter -unpack -xdb $uiArchive -flt $globalFilter -dir $globalOutput
if ($LASTEXITCODE -ne 0) {
    throw "Failed to extract $globalFilter from $uiArchive (exit $LASTEXITCODE)"
}

$foundMaps = @{}
foreach ($archive in $textureArchives) {
    $indexPath = Join-Path $metadataRoot $archive.Name
    New-Item -ItemType Directory -Path $indexPath | Out-Null
    & $converter -unpack -xdb $archive.FullName -flt '.thm' -dir $indexPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to index $($archive.Name) (exit $LASTEXITCODE)"
    }

    $thumbnails = Get-ChildItem $indexPath -Recurse -File -Filter '*.thm' |
        Where-Object { $_.Directory.Name -ieq 'map' }
    foreach ($thumbnail in $thumbnails) {
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($thumbnail.Name)
        $filename = "$stem.dds"
        if ($foundMaps.ContainsKey($filename)) {
            throw "Duplicate map texture name found in multiple archives: $filename"
        }
        $foundMaps[$filename] = $archive.FullName
    }
}

foreach ($filename in ($foundMaps.Keys | Sort-Object)) {
    $filter = "\map\$filename"
    & $converter -unpack -xdb $foundMaps[$filename] -flt $filter -dir $mapOutput
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to extract $filter from $($foundMaps[$filename]) (exit $LASTEXITCODE)"
    }
}

$expected = @(
    (Join-Path $configOutput 'configs\game_maps_single.ltx'),
    (Join-Path $globalOutput 'textures\ui\ui_global_map.dds')
)
foreach ($path in $expected) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Extraction completed but expected resource was not found: $path"
    }
}
$mapCount = (Get-ChildItem (Join-Path $mapOutput 'textures\map') -Recurse -File -Filter '*.dds' | Measure-Object).Count
if ($mapCount -ne $foundMaps.Count) {
    throw "Extracted $mapCount map DDS files, but indexed $($foundMaps.Count) map textures."
}

Write-Output "Indexed $($foundMaps.Count) local map textures. Resources extracted to $output"
