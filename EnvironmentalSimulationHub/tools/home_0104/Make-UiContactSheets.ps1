$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$hubRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$uiRoot = Join-Path $hubRoot 'docs/evidence/home_0104/runtime/ui_0101'
$sheetRoot = Join-Path $hubRoot 'docs/evidence/home_0104/ui_review'
New-Item -ItemType Directory -Path $sheetRoot -Force | Out-Null
$capture = Get-Content -LiteralPath (Join-Path $uiRoot 'capture.json') -Raw | ConvertFrom-Json
$font = [Drawing.Font]::new('Arial', 12)
try {
    for ($page = 0; $page -lt [Math]::Ceiling($capture.shots.Count / 4); $page++) {
        $shots = @($capture.shots | Select-Object -Skip ($page * 4) -First 4)
        $width = ($shots | Measure-Object -Property width -Sum).Sum
        $bitmap = [Drawing.Bitmap]::new([int]$width, 795)
        $graphics = [Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.Clear([Drawing.Color]::White)
            $x = 0
            foreach ($shot in $shots) {
                $image = [Drawing.Image]::FromFile($shot.path)
                try {
                    $graphics.DrawString(($shot.module + ' / ' + $shot.width), $font, [Drawing.Brushes]::Black, $x, 4)
                    $graphics.DrawImageUnscaled($image, $x, 30)
                    $x += $shot.width
                } finally { $image.Dispose() }
            }
            $bitmap.Save((Join-Path $sheetRoot ('sheet_{0:D2}.png' -f $page)), [Drawing.Imaging.ImageFormat]::Png)
        } finally { $graphics.Dispose(); $bitmap.Dispose() }
    }
} finally { $font.Dispose() }
