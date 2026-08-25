; Inno Setup script for MediaBulk Pro
#define AppName "MediaBulk Pro"
#define AppVersion "0.1.0"
#define AppExe "MediaBulkPro-Windows-x64.exe"

[Setup]
AppId={{9C3F2A10-7B4E-4C21-9A88-MEDIABULK0001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=MediaBulk Pro Contributors
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=..\dist
OutputBaseFilename=MediaBulkPro-Setup
SetupIconFile=..\assets\icons\mediabulk.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
