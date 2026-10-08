param([switch]$Rollback)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$evidence = Join-Path $projectRoot 'docs\evidence\deploy_0109'
$candidate = Join-Path $projectRoot 'artifacts\releases\0.10.9\EnvironmentalHub.Plugin.rhp'
$previous = Join-Path $projectRoot 'artifacts\releases\0.10.1\EnvironmentalHub.Plugin.rhp'
$backup = Join-Path $evidence 'registration_pair_before.json'
$keys = @(
    'Registry::HKEY_LOCAL_MACHINE\Software\McNeel\Rhinoceros\8.0\Plug-Ins\bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f\PlugIn',
    'Registry::HKEY_CURRENT_USER\Software\McNeel\Rhinoceros\8.0\Plug-Ins\bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f\PlugIn'
)
if (Get-Process Rhino -ErrorAction SilentlyContinue) { throw 'Close Rhino normally before registration changes; never unload or duplicate a live plugin ID' }
if ($Rollback) {
    $saved = Get-Content -LiteralPath $backup -Raw | ConvertFrom-Json
    if ($saved.candidate_path -ne $candidate -or $saved.entries.Count -ne 2) { throw 'Backup mismatch' }
    foreach ($entry in $saved.entries) {
        if ($entry.key -notin $keys -or $entry.previous_path -ne $previous) { throw 'Unexpected backup target' }
        if ((Get-ItemProperty -LiteralPath $entry.key -Name FileName).FileName -ne $candidate) { throw 'Registration changed externally; stop rollback' }
        if ((Get-FileHash -LiteralPath $entry.previous_path -Algorithm SHA256).Hash -ne $entry.previous_sha256) { throw 'Previous binary changed' }
    }
    foreach ($entry in $saved.entries) { Set-ItemProperty -LiteralPath $entry.key -Name FileName -Value $entry.previous_path }
    foreach ($entry in $saved.entries) {
        if ((Get-ItemProperty -LiteralPath $entry.key -Name FileName).FileName -ne $entry.previous_path) { throw 'Rollback readback failed' }
    }
    @{timestamp=[DateTimeOffset]::Now.ToString('o');path=$previous;scope='Both existing registrations for this plugin only'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence 'rollback.json') -Encoding utf8
    Write-Output 'Both existing plugin paths restored; next Rhino launch uses previous release.'
    return
}
$manifest = Get-Content -LiteralPath (Join-Path $projectRoot 'artifacts\releases\0.10.9\release_manifest.json') -Raw | ConvertFrom-Json
foreach ($entry in $manifest.files.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Join-Path (Split-Path $candidate) $entry.Name) -Algorithm SHA256).Hash -ne $entry.Value) { throw 'Package hash mismatch' }
}
if ([Reflection.AssemblyName]::GetAssemblyName($candidate).Version.ToString() -ne '0.10.9.0') { throw 'Wrong assembly version' }
$entries = @($keys | ForEach-Object {
    $current = (Get-ItemProperty -LiteralPath $_ -Name FileName).FileName
    if ($current -ne $previous) { throw 'Unexpected registration; inspect rather than overwrite' }
    @{key=$_;previous_path=$current;previous_sha256=(Get-FileHash -LiteralPath $current -Algorithm SHA256).Hash}
})
if (Test-Path -LiteralPath $backup) { throw 'Keep first paired backup; inspect before retrying' }
@{timestamp=[DateTimeOffset]::Now.ToString('o');candidate_path=$candidate;entries=$entries;scope='Only two existing plugin FileName values; stable GUID and all other values untouched'} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $backup -Encoding utf8
$changed = @()
try {
    foreach ($key in $keys) { Set-ItemProperty -LiteralPath $key -Name FileName -Value $candidate; $changed += $key }
    foreach ($key in $keys) {
        if ((Get-ItemProperty -LiteralPath $key -Name FileName).FileName -ne $candidate) { throw 'Registration readback mismatch' }
    }
} catch {
    foreach ($key in $changed) {
        if ((Get-ItemProperty -LiteralPath $key -Name FileName).FileName -eq $candidate) { Set-ItemProperty -LiteralPath $key -Name FileName -Value $previous }
    }
    throw
}
@{timestamp=[DateTimeOffset]::Now.ToString('o');path=$candidate;keys=$keys;readback='PASS';runtime='Pending fresh Rhino verification';initial_failure='HKCU-only update was overridden by the existing HKLM registration'} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidence 'registration_repaired.json') -Encoding utf8
Write-Output 'Both existing plugin paths verified as 0.10.9. Fresh Rhino verification is still required.'
