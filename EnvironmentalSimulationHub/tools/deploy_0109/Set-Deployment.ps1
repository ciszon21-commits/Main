param([switch]$Rollback)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$evidence = Join-Path $projectRoot 'docs\evidence\deploy_0109'
$release = Join-Path $projectRoot 'artifacts\releases\0.10.9'
$candidate = Join-Path $release 'EnvironmentalHub.Plugin.rhp'
if ($Rollback) {
    & (Join-Path $PSScriptRoot 'Repair-Registration.ps1') -Rollback
    return
}
if (Get-Process -Name Rhino -ErrorAction SilentlyContinue) { throw 'Rhino is running; preserve loaded state and stop registration update' }
$acceptance = Get-Content -LiteralPath (Join-Path $projectRoot 'docs\evidence\visual_0109\acceptance.json') -Raw | ConvertFrom-Json
if ($acceptance.AssemblyVersion -ne '0.10.9.0' -or $acceptance.Build.Errors -ne 0 -or $acceptance.PresentationChecks -ne 18 -or $acceptance.BrowserChecks -ne 10) { throw 'Candidate checks missing' }
$build = Join-Path $projectRoot 'artifacts\company-build\0.10.9'
$names = @('EnvironmentalHub.Plugin.rhp','EnvironmentalHub.Core.dll','EnvironmentalHub.Adapters.dll','hub.config.json')
$hashes = [ordered]@{}
New-Item -ItemType Directory -Path $release -Force | Out-Null
foreach ($name in $names) {
    $source = Join-Path $build $name
    $destination = Join-Path $release $name
    $digest = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    if (Test-Path -LiteralPath $destination) {
        if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -ne $digest) { throw 'Immutable release file differs' }
    } else { Copy-Item -LiteralPath $source -Destination $destination }
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -ne $digest) { throw 'Copy verification failed' }
    $hashes[$name] = $digest.ToLower()
}
if ([Reflection.AssemblyName]::GetAssemblyName($candidate).Version.ToString() -ne '0.10.9.0') { throw 'Wrong version' }
$manifestPath = Join-Path $release 'release_manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath)) {
    @{version='0.10.9';files=$hashes;runtime_verification='Pending fresh Rhino load';webview='Experimental, disabled by default';formal_acceptance='0.9.2; function coverage unchanged'} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
}
& (Join-Path $PSScriptRoot 'Repair-Registration.ps1')
