param(
    [string]$RhinoInstallDirectory = (Join-Path $env:ProgramFiles 'Rhino 8'),
    [string]$LadybugUserObjectDirectory = (Join-Path $env:ProgramFiles 'ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'),
    [string]$RadianceBinDirectory = (Join-Path $env:ProgramFiles 'ladybug_tools/radiance/bin')
)
# Read-only preflight. No install, registry changes, write probe or Rhino launch.
$ErrorActionPreference = 'Stop'
$hubRoot = Split-Path -Parent $PSScriptRoot
$checks = [Collections.Generic.List[object]]::new()
function Add-Check([string]$Name, [string]$State, [string]$Detail) {
    $checks.Add([pscustomobject]@{ Name = $Name; State = $State; Detail = $Detail })
}
Add-Check 'Windows' $(if ($env:OS -eq 'Windows_NT') { 'PASS' } else { 'FAIL' }) 'Rhino/Eto target is Windows / .NET 8'
foreach ($relative in @('System/RhinoCommon.dll', 'System/Eto.dll', 'Plug-ins/Grasshopper/Grasshopper.dll', 'Plug-ins/Grasshopper/GH_IO.dll')) {
    $path = Join-Path $RhinoInstallDirectory $relative
    Add-Check $relative $(if (Test-Path -LiteralPath $path -PathType Leaf) { 'PASS' } else { 'FAIL' }) $path
}
$rhinoCommon = Join-Path $RhinoInstallDirectory 'System/RhinoCommon.dll'
if (Test-Path -LiteralPath $rhinoCommon -PathType Leaf) {
    $version = [Reflection.AssemblyName]::GetAssemblyName($rhinoCommon).Version.ToString()
    Add-Check 'RhinoVersionBaseline' $(if ($version -eq '8.35.26251.13001') { 'PASS' } else { 'WARN' }) ('Installed=' + $version + '; tested=8.35.26251.13001')
}
$sdk = Get-Command dotnet -ErrorAction SilentlyContinue
if ($sdk) {
    # Inspect installed SDK folders without invoking CLI first-run setup.
    $sdkFolder = Join-Path (Split-Path -Parent $sdk.Source) 'sdk'
    $versions = if (Test-Path -LiteralPath $sdkFolder -PathType Container) { @(Get-ChildItem -LiteralPath $sdkFolder -Directory | Select-Object -ExpandProperty Name) } else { @() }
    Add-Check 'DotNet8SDK' $(if (@($versions | Where-Object { $_ -match '^8\.' }).Count) { 'PASS' } else { 'FAIL' }) ($versions -join '; ')
} else { Add-Check 'DotNet8SDK' 'FAIL' 'dotnet SDK command missing' }
$catalog = Get-Content -LiteralPath (Join-Path $hubRoot 'docs/evidence/ladybug_feature_catalog.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$ids = @('LB-001', 'LB-007', 'LB-009', 'LB-011', 'LB-013', 'LB-020', 'LB-033', 'LB-049', 'LB-057', 'LB-061', 'LB-063')
foreach ($component in @($catalog.components | Where-Object { $_.id -in $ids })) {
    $path = Join-Path $LadybugUserObjectDirectory $component.file
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Add-Check $component.id 'FAIL' ('Missing ' + $path); continue }
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    Add-Check $component.id $(if ($hash -eq $component.sha256) { 'PASS' } else { 'WARN' }) 'Installed original user-object compared with source-machine baseline; differences require native regression'
}
foreach ($name in @('gendaymtx.exe', 'rtrace.exe')) {
    $path = Join-Path $RadianceBinDirectory $name
    Add-Check $name $(if (Test-Path -LiteralPath $path -PathType Leaf) { 'PASS' } else { 'WARN' }) 'Required for radiation workflows; Direct Sun Hours uses native CAD intersections'
}
Add-Check 'LadybugPythonImportsAndNativeSolve' 'NOT_TESTED' 'Must verify in new Rhino document on home computer'
Add-Check 'RhinoMCPConnection' 'NOT_TESTED' 'Optional for manual use; required for automated native replay. Do not reuse source-machine slot IDs'
Add-Check 'NotionConnection' 'NOT_TESTED' 'Reconnect with own authenticated account; credentials are excluded'
[pscustomobject]@{
    Scope = 'Read-only dependency preflight; source-machine evidence does not certify home-machine runtime'
    Failures = @($checks | Where-Object State -eq 'FAIL').Count
    Warnings = @($checks | Where-Object State -eq 'WARN').Count
    Checks = $checks.ToArray()
} | ConvertTo-Json -Depth 5
if (@($checks | Where-Object State -eq 'FAIL').Count) { exit 1 }
