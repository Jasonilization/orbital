# Build Orbital for Windows: portable exe via PyInstaller, then a zip.
# Run from a normal PowerShell in the repo root, with a venv active:
#   python -m pip install -e .[package]
#   powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "==> building with PyInstaller"
python -m PyInstaller `
    --noconfirm --clean --windowed `
    --name Orbital `
    --icon assets\icons\Orbital.ico `
    --collect-data orbital `
    orbital\__main__.py

if (-not (Test-Path "dist\Orbital")) {
    Write-Error "build failed: dist\Orbital missing"
}

$version = python -c "import orbital; print(orbital.__version__)"
$zip = "dist\Orbital-$version-win64.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path "dist\Orbital" -DestinationPath $zip
Write-Host "built $zip"
