param()
$ErrorActionPreference = 'Stop'
$hubRoot = Split-Path -Parent $PSScriptRoot
$releaseRoot = Join-Path $hubRoot 'artifacts\releases\0.3.0'
$releasePath = Join-Path $releaseRoot 'EnvironmentalHub.Plugin.rhp'
$releaseManifest = Get-Content -LiteralPath (Join-Path $releaseRoot 'release_manifest.json') -Raw | ConvertFrom-Json
foreach ($entry in $releaseManifest.files.PSObject.Properties) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $releaseRoot $entry.Name) -Algorithm SHA256).Hash
    if ($actual -ne $entry.Value) { throw "Release hash mismatch: $($entry.Name)" }
}
$version = [Reflection.AssemblyName]::GetAssemblyName($releasePath).Version.ToString()
if ($version -ne '0.3.0.0') { throw "Unexpected release version: $version" }
$registrationKeys = @(
    'Registry::HKEY_LOCAL_MACHINE\Software\McNeel\Rhinoceros\8.0\Plug-Ins\bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f\PlugIn',
    'Registry::HKEY_CURRENT_USER\Software\McNeel\Rhinoceros\8.0\Plug-Ins\bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f\PlugIn'
)
$previousPaths = @($registrationKeys | ForEach-Object {
    $prior = (Get-ItemProperty -LiteralPath $_ -Name FileName).FileName
    if ($prior -ne $releasePath -and $prior -ne (Join-Path $hubRoot 'artifacts\runtime-v3\EnvironmentalHub.Plugin.rhp')) {
        throw "Unexpected existing plugin path: $prior"
    }
    [pscustomobject]@{ RegistryKey = $_; FileName = $prior }
})
$backupPath = Join-Path $hubRoot ('docs\evidence\release_registration_backup_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.json')
$previousPaths | ConvertTo-Json | Set-Content -LiteralPath $backupPath -Encoding utf8
foreach ($key in $registrationKeys) {
    Set-ItemProperty -LiteralPath $key -Name FileName -Value $releasePath
}
foreach ($key in $registrationKeys) {
    if ((Get-ItemProperty -LiteralPath $key -Name FileName).FileName -ne $releasePath) { throw 'Registration readback mismatch' }
}
[pscustomobject]@{ Version = $version; Path = $releasePath; RegistrationReadback = 'PASS'; Backup = $backupPath } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $hubRoot 'docs\evidence\release_registration_updated.json') -Encoding utf8
Write-Output 'Updated both existing Environmental Hub FileName registrations to verified 0.3.0 release.'
