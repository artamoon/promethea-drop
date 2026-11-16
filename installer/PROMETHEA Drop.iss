; PROMETHEA Drop per-user installer. SANDBOX_TEST builds an isolated smoke-test installer.
#define AppVersion "0.1.0"
#ifndef BuildDir
  #define BuildDir "..\dist\PrometheaDrop"
#endif

[Setup]
#ifdef SANDBOX_TEST
AppId={{D2C173A4-B445-46E2-A9DC-E7F41B6A459D}
CreateUninstallRegKey=no
#else
AppId={{CE1510EC-8C83-46EE-9898-9DD12C4069A4}
#endif
AppName=PROMETHEA Drop
AppVersion={#AppVersion}
AppPublisher=PROMETHEA
DefaultDirName={localappdata}\Programs\PROMETHEA Drop
DefaultGroupName=PROMETHEA Drop
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\installer
OutputBaseFilename=PROMETHEA-Drop-Setup-{#AppVersion}-preview
SetupIconFile=..\promethea\assets\promethea.ico
UninstallDisplayIcon={app}\PrometheaDrop.exe
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
CloseApplicationsFilter=PrometheaDrop.exe
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

#ifndef SANDBOX_TEST
[Tasks]
Name: "autostart"; Description: "Start PROMETHEA Drop when I sign in"; Flags: unchecked
Name: "contextmenu"; Description: "Add PROMETHEA Drop to the file context menu"; Flags: unchecked
Name: "sendto"; Description: "Add PROMETHEA Drop to Send To"; Flags: unchecked
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
#endif

[Files]
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\NOTICE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\third-party-licenses\*"; DestDir: "{app}\third-party-licenses"; Flags: recursesubdirs ignoreversion

#ifndef SANDBOX_TEST
[Icons]
Name: "{userprograms}\PROMETHEA Drop"; Filename: "{app}\PrometheaDrop.exe"
Name: "{userdesktop}\PROMETHEA Drop"; Filename: "{app}\PrometheaDrop.exe"; Tasks: desktopicon
Name: "{usersendto}\PROMETHEA Drop"; Filename: "{app}\PrometheaDrop.exe"; Tasks: sendto

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "PROMETHEA Drop"; ValueData: """{app}\PrometheaDrop.exe"" --quiet"; Tasks: autostart; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\*\shell\PrometheaDrop"; ValueType: string; ValueName: "MUIVerb"; ValueData: "PROMETHEA Drop…"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\*\shell\PrometheaDrop"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\PrometheaDrop.exe"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\PrometheaDrop"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Player"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\PrometheaDrop\command"; ValueType: string; ValueName: ""; ValueData: """{app}\PrometheaDrop.exe"" ""%1"""; Tasks: contextmenu

[Run]
Filename: "{app}\PrometheaDrop.exe"; Description: "Launch PROMETHEA Drop"; Flags: nowait postinstall skipifsilent
#endif
