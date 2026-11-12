$ErrorActionPreference = "SilentlyContinue"

$dst = Join-Path $env:LOCALAPPDATA "Programs\Widdeks"
$oldDst = Join-Path $env:LOCALAPPDATA "Programs\RelojWidget"
$programs = [Environment]::GetFolderPath("Programs")

Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" |
    Where-Object { $_.CommandLine -match "Widdeks|RelojWidget|clock\.py|panel\.py|widdeks\.py" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "Widdeks"
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "Reloj Widget"
Remove-Item (Join-Path $programs "Widdeks.lnk") -Force
Remove-Item (Join-Path $programs "Reloj Widget.lnk") -Force

Set-Location $env:TEMP
Start-Sleep -Milliseconds 400
Remove-Item $dst -Recurse -Force
Remove-Item $oldDst -Recurse -Force

Write-Host ""
Write-Host "Widdeks desinstalado." -ForegroundColor Green
