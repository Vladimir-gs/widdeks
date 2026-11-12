# Compila Widdeks.exe (onedir) en dist\Widdeks\
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    python -m pip install -r requirements-build.txt
    python -m PyInstaller widdeks.spec --noconfirm --clean

    $exe = Join-Path $root "dist\Widdeks\Widdeks.exe"
    if (-not (Test-Path $exe)) {
        throw "No se genero $exe"
    }

    & $exe --selftest
    if ($LASTEXITCODE -ne 0) {
        throw "El autodiagnostico del ejecutable fallo (ver %LOCALAPPDATA%\Widdeks\selftest.json)"
    }

    Write-Host ""
    Write-Host "Build OK: $exe" -ForegroundColor Green
} finally {
    Pop-Location
}
