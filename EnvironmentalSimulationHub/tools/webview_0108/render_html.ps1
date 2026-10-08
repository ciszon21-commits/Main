$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$evidenceRoot = Join-Path $projectRoot 'docs/evidence/webview_0108/browser'
$profileRoot = Join-Path $projectRoot 'artifacts/webview_0108/edge-profile-verified'
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null
foreach ($theme in @('light', 'dark')) {
    foreach ($width in @(320, 480)) {
        $sourcePath = Join-Path $projectRoot "docs/evidence/webview_0108/summary-$theme.html"
        $sourceUri = ([Uri]$sourcePath).AbsoluteUri
        $capturePath = Join-Path $evidenceRoot "$width-$theme.png"
        $edgeArgs = @('--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--disable-background-networking', '--disable-component-update', '--disable-sync', '--hide-scrollbars', "--user-data-dir=$profileRoot", "--screenshot=$capturePath", "--window-size=$width,2100", '--virtual-time-budget=1000', $sourceUri)
        $edgeProcess = Start-Process -FilePath 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' -ArgumentList $edgeArgs -WindowStyle Hidden -PassThru -Wait
        if ($edgeProcess.ExitCode -ne 0 -or !(Test-Path -LiteralPath $capturePath)) { throw "HTML capture failed: $width-$theme" }
    }
}
