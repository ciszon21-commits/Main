$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$candidatePath = Join-Path $projectRoot 'artifacts\home-build\0.10.7\EnvironmentalHub.Plugin.rhp'
$pluginKey = 'HKCU:\Software\McNeel\Rhinoceros\8.0\Plug-ins\bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f\PlugIn'
$evidenceDir = Join-Path $projectRoot 'docs\evidence\archive_0107'
$backupPath = Join-Path $evidenceDir 'candidate_registration_before.json'
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) { throw 'Candidate missing' }
if ([Reflection.AssemblyName]::GetAssemblyName($candidatePath).Version.ToString() -ne '0.10.7.0') { throw 'Wrong candidate version' }
$previousPath = (Get-ItemProperty -LiteralPath $pluginKey -Name FileName).FileName
if (Test-Path -LiteralPath $backupPath) { throw 'Preserve the first registration backup; do not overwrite it' }
@{date='2026-10-03'; registry_key=$pluginKey; previous_path=$previousPath; candidate_path=$candidatePath; candidate_sha256=(Get-FileHash -LiteralPath $candidatePath -Algorithm SHA256).Hash; scope='One current-user plugin FileName value; candidate QA, not formal deployment'} | ConvertTo-Json | Set-Content -LiteralPath $backupPath -Encoding utf8
Set-ItemProperty -LiteralPath $pluginKey -Name FileName -Value $candidatePath
$actual = (Get-ItemProperty -LiteralPath $pluginKey -Name FileName).FileName
if ($actual -ne $candidatePath) { throw 'Registration readback mismatch' }
@{date='2026-10-03'; registered_path=$actual; formal_version='0.9.2'; candidate_version='0.10.7'; backup='candidate_registration_before.json'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidenceDir 'candidate_registration_after.json') -Encoding utf8
Write-Output 'Candidate 0.10.7 FileName set and verified; current Rhino processes retain their loaded version.'
