param(
    [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$RhinoInstallDirectory = (Join-Path $env:ProgramFiles 'Rhino 8'),
    [string]$OutputDirectoryOverride = '',
    [switch]$ProbeWriteAccess
)
$ErrorActionPreference = 'Stop'
$checks = [Collections.Generic.List[object]]::new()
function Add-Check([string]$Name, [string]$State, [string]$Detail) {
    $checks.Add([pscustomobject]@{ Name = $Name; State = $State; Detail = $Detail })
}
try {
    $packagePath = [IO.Path]::GetFullPath($PackageRoot)
    $pluginPath = Join-Path $packagePath 'plugin'
    $manifest = Get-Content -LiteralPath (Join-Path $packagePath 'pilot_manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($entry in $manifest.files.PSObject.Properties) {
        $target = [IO.Path]::GetFullPath((Join-Path $packagePath $entry.Name))
        if (-not $target.StartsWith($packagePath.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Manifest path escapes package' }
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { Add-Check ('Package:' + $entry.Name) 'FAIL' 'Missing file'; continue }
        $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
        Add-Check ('Package:' + $entry.Name) $(if ($hash -eq $entry.Value) { 'PASS' } elseif ($entry.Name -eq 'plugin/hub.config.json') { 'WARN' } else { 'FAIL' }) 'SHA-256 comparison; local configuration changes require review'
    }
    $assembly = [Reflection.AssemblyName]::GetAssemblyName((Join-Path $pluginPath 'EnvironmentalHub.Plugin.rhp'))
    Add-Check 'PluginVersion' $(if ($assembly.Version.ToString() -eq '0.8.7.0') { 'PASS' } else { 'FAIL' }) $assembly.Version.ToString()
    $rhinoCommon = Join-Path $RhinoInstallDirectory 'System/RhinoCommon.dll'
    if (Test-Path -LiteralPath $rhinoCommon -PathType Leaf) {
        $rhinoVersion = [Reflection.AssemblyName]::GetAssemblyName($rhinoCommon).Version
        Add-Check 'RhinoVersion' $(if ($rhinoVersion.ToString() -eq $manifest.runtime_baseline.rhino_assembly) { 'PASS' } else { 'WARN' }) ('Installed=' + $rhinoVersion + '; tested=' + $manifest.runtime_baseline.rhino_assembly)
    } else { Add-Check 'RhinoVersion' 'FAIL' 'RhinoCommon.dll missing; specify RhinoInstallDirectory' }
    foreach ($name in @('Grasshopper.dll', 'GH_IO.dll')) {
        $target = Join-Path $RhinoInstallDirectory ('Plug-ins/Grasshopper/' + $name)
        Add-Check $name $(if (Test-Path -LiteralPath $target -PathType Leaf) { 'PASS' } else { 'FAIL' }) $target
    }
    $config = Get-Content -LiteralPath (Join-Path $pluginPath 'hub.config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $objects = [Environment]::ExpandEnvironmentVariables($config.UserObjectDirectory)
    $dependencies = Get-Content -LiteralPath (Join-Path $packagePath 'dependencies.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($component in $dependencies.user_objects) {
        $target = Join-Path $objects $component.file
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { Add-Check $component.id 'FAIL' ('Missing ' + $target); continue }
        $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
        Add-Check $component.id $(if ($hash -eq $component.sha256) { 'PASS' } else { 'WARN' }) 'Installed Ladybug user-object compared with tested baseline; differences require native revalidation'
    }
    $radiance = [Environment]::ExpandEnvironmentVariables($config.RadianceBinDirectory)
    foreach ($name in @('gendaymtx.exe', 'rtrace.exe')) {
        $target = Join-Path $radiance $name
        Add-Check $name $(if (Test-Path -LiteralPath $target -PathType Leaf) { 'PASS' } else { 'FAIL' }) $target
    }
    $output = [Environment]::ExpandEnvironmentVariables($config.OutputDirectory)
    if ($OutputDirectoryOverride) { $output = $OutputDirectoryOverride }
    if (-not [IO.Path]::IsPathRooted($output)) { $output = Join-Path $pluginPath $output }
    $output = [IO.Path]::GetFullPath($output)
    if ($ProbeWriteAccess) {
        $probe = $null
        try {
            [IO.Directory]::CreateDirectory($output) | Out-Null
            $probe = Join-Path $output ('hub-write-probe-' + [Guid]::NewGuid().ToString('N') + '.tmp')
            [IO.File]::WriteAllText($probe, 'Environmental Hub write probe')
            Add-Check 'OutputWriteAccess' 'PASS' $output
        } catch { Add-Check 'OutputWriteAccess' 'FAIL' $_.Exception.Message }
        finally { if ($probe -and (Test-Path -LiteralPath $probe -PathType Leaf)) { Remove-Item -LiteralPath $probe } }
    } else { Add-Check 'OutputWriteAccess' 'NOT_TESTED' ('Use -ProbeWriteAccess; resolved=' + $output) }
    Add-Check 'NativeRhinoRuntime' 'NOT_TESTED' 'Load plugin in Rhino using .NET 8; run pilot acceptance. File checks do not prove GH/Python imports or solver execution.'
} catch { Add-Check 'ReadinessConfiguration' 'FAIL' $_.Exception.Message }
$failures = @($checks | Where-Object State -eq 'FAIL').Count
$warnings = @($checks | Where-Object State -eq 'WARN').Count
[pscustomobject]@{
    Version = '0.8.7'; Scope = 'Static package/dependency checks and optional output write probe; not native runtime acceptance'
    Status = $(if ($failures) { 'BLOCKED' } elseif ($warnings) { 'REVIEW_REQUIRED' } else { 'READY_FOR_NATIVE_TRIAL' })
    Failures = $failures; Warnings = $warnings; OutputDirectoryOverride = $OutputDirectoryOverride; Checks = $checks.ToArray()
} | ConvertTo-Json -Depth 6
if ($failures) { exit 1 }
