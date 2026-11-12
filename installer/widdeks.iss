; Instalador de Widdeks - Inno Setup 6
; Compilar con: iscc installer\widdeks.iss

#define AppName "Widdeks"
#define AppVersion "1.0.0"
#define AppPublisher "Vladimir GS"
#define AppExe "Widdeks.exe"
#define AppId "{{B7E3C2A1-9F4D-4C6B-8A2E-5D1F7C3B9E60}"

[Setup]
SourceDir=..
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppCopyright=Copyright (c) 2026 {#AppPublisher}
DefaultDirName={localappdata}\Programs\Widdeks
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=dist\installer
OutputBaseFilename=Widdeks-Setup-{#AppVersion}
SetupIconFile=clock-widget\assets\widdeks.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
LicenseFile=LICENSE
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
AppMutex=Local\WiddeksApp
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=Instalador de {#AppName}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
VersionInfoCopyright=Copyright (c) 2026 {#AppPublisher}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "autostart"; Description: "Iniciar Widdeks automáticamente al iniciar sesión"; GroupDescription: "Opciones adicionales:"; Flags: checkedonce
Name: "desktopicon"; Description: "Crear un acceso directo en el Escritorio"; GroupDescription: "Opciones adicionales:"

[Files]
Source: "dist\Widdeks\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: files; Name: "{app}\widdeks.py"
Type: files; Name: "{app}\iniciar.vbs"
Type: files; Name: "{app}\widget_error.log"
Type: filesandordirs; Name: "{app}\__pycache__"

[Icons]
Name: "{autoprograms}\Widdeks"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{autodesktop}\Widdeks"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Widdeks"; ValueData: """{app}\{#AppExe}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#AppExe}"; Description: "Iniciar Widdeks"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\Widdeks"
Type: filesandordirs; Name: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    { Limpiar entradas de auto-inicio de versiones anteriores (script .bat). }
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'Widdeks');
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'Reloj Widget');
    DeleteFile(ExpandConstant('{userprograms}\Reloj Widget.lnk'));
  end;
end;
