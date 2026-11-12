# Compila Widdeks.exe (onedir) y el instalador en dist\
param(
    [switch]$SkipInstaller
)

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
    Write-Host "Build OK: $exe" -ForegroundColor Green

    if (-not $SkipInstaller) {
        $iscc = @(
            (Get-Command iscc.exe -ErrorAction SilentlyContinue).Source,
            (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
            "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            "C:\Program Files\Inno Setup 6\ISCC.exe"
        ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

        if (-not $iscc) {
            throw "No se encontro ISCC.exe. Instala Inno Setup 6: winget install JRSoftware.InnoSetup"
        }

        & $iscc "installer\widdeks.iss"
        if ($LASTEXITCODE -ne 0) {
            throw "Fallo la compilacion del instalador."
        }
        Write-Host "Instalador OK: dist\installer" -ForegroundColor Green
    }
} finally {
    Pop-Location
}
