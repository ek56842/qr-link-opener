$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot 'build-venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    throw 'build-venv was not found. Follow the README to create it first.'
}

$version = (& $python -c "from app import APP_VERSION; print(APP_VERSION)").Trim()
$distPath = Join-Path $projectRoot 'dist'
$buildId = Get-Date -Format 'yyyyMMddHHmmss'
$workPath = Join-Path $projectRoot "build-$buildId"
$appPath = Join-Path $projectRoot 'app.py'
$portablePath = Join-Path $projectRoot "dist\QR-Link-Opener-$version-portable.exe"

& $python -m PyInstaller --noconfirm --clean --windowed --onefile `
    --name "QR-Link-Opener-$version-portable" `
    --collect-all cv2 `
    --distpath $distPath `
    --workpath $workPath `
    $appPath

Write-Host "Portable executable created: $portablePath"
