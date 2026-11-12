$ErrorActionPreference = "Stop"

$src = $PSScriptRoot
$dst = Join-Path $env:LOCALAPPDATA "Programs\Widdeks"
$oldDst = Join-Path $env:LOCALAPPDATA "Programs\RelojWidget"
$runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$runName = "Widdeks"
$oldRunName = "Reloj Widget"
$programs = [Environment]::GetFolderPath("Programs")

$pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $pythonw -or -not (Test-Path $pythonw)) {
    Write-Host "ERROR: no se encontro pythonw.exe en el PATH." -ForegroundColor Red
    Write-Host "Instala Python 3 y volve a intentarlo."
    exit 1
}

Write-Host "Instalando Widdeks en $dst ..."

Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" |
    Where-Object { $_.CommandLine -match "clock\.py|panel\.py|widdeks\.py" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 500

New-Item -ItemType Directory -Path $dst -Force | Out-Null

Copy-Item (Join-Path $src "widdeks.py") $dst -Force
$fontsDst = Join-Path $dst "fonts"
if (Test-Path $fontsDst) { Remove-Item $fontsDst -Recurse -Force }
Copy-Item (Join-Path $src "fonts") $fontsDst -Recurse -Force

$clockSources = @((Join-Path $oldDst "clock_config.json"), (Join-Path $src "clock_config.json"))
$clockCfg = $clockSources | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($clockCfg) { Copy-Item $clockCfg (Join-Path $dst "clock_config.json") -Force }

$panelSources = @((Join-Path $src "panel_config.json"), (Join-Path $oldDst "panel_config.json"))
$panelCfg = $panelSources | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($panelCfg) { Copy-Item $panelCfg (Join-Path $dst "panel_config.json") -Force }

Remove-Item (Join-Path $dst "__pycache__") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $dst "widget_error.log") -Force -ErrorAction SilentlyContinue

$app = Join-Path $dst "widdeks.py"

Remove-ItemProperty -Path $runKey -Name $oldRunName -ErrorAction SilentlyContinue
New-ItemProperty -Path $runKey -Name $runName -PropertyType String `
    -Value ('"{0}" "{1}"' -f $pythonw, $app) -Force | Out-Null

Remove-Item (Join-Path $programs "Reloj Widget.lnk") -Force -ErrorAction SilentlyContinue
$lnkPath = Join-Path $programs "Widdeks.lnk"
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut($lnkPath)
$lnk.TargetPath = $pythonw
$lnk.Arguments = ('"{0}"' -f $app)
$lnk.WorkingDirectory = $dst
$lnk.WindowStyle = 7
$lnk.Description = "Reloj y panel de escritorio"
$lnk.Save()

if (Test-Path $oldDst) { Remove-Item $oldDst -Recurse -Force -ErrorAction SilentlyContinue }

Start-Process -FilePath $pythonw -ArgumentList ('"{0}"' -f $app) -WorkingDirectory $dst -WindowStyle Hidden
Start-Sleep -Milliseconds 1500

Write-Host ""
Write-Host "Listo. Instalado en: $dst" -ForegroundColor Green
Write-Host "Arranque automatico: Administrador de tareas > Aplicaciones > Inicio (nombre 'Widdeks')."
Write-Host "Acceso directo en el menu Inicio: 'Widdeks'."
Write-Host "Para desinstalar: ejecuta desinstalar.bat"
