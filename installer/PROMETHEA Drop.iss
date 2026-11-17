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
DisableWelcomePage=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\installer
OutputBaseFilename=PROMETHEA-Drop-Setup-{#AppVersion}-preview
SetupIconFile=..\promethea\assets\promethea.ico
UninstallDisplayIcon={app}\PrometheaDrop.exe
LicenseFile=..\LICENSE
#ifdef SANDBOX_TEST
Compression=none
SolidCompression=no
#else
Compression=lzma2
SolidCompression=yes
#endif
WizardStyle=modern dark includetitlebar
WizardBackColor=#1C1C1C
WizardImageFile=assets\wizard.png
WizardImageBackColor=#1C1C1C
WizardSmallImageFile=assets\wizard-small.png
WizardSmallImageBackColor=#1C1C1C
CloseApplications=yes
CloseApplicationsFilter=PrometheaDrop.exe
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
english.StartAtLogin=Start PROMETHEA Drop when I sign in
russian.StartAtLogin=Запускать PROMETHEA Drop при входе в Windows
english.ContextMenu=Add PROMETHEA Drop to the file context menu
russian.ContextMenu=Добавить PROMETHEA Drop в контекстное меню файлов
english.SendTo=Add PROMETHEA Drop to Send To
russian.SendTo=Добавить PROMETHEA Drop в меню «Отправить»
english.DesktopIcon=Create a desktop shortcut
russian.DesktopIcon=Создать ярлык на рабочем столе
english.LaunchApp=Launch PROMETHEA Drop
russian.LaunchApp=Запустить PROMETHEA Drop

#ifndef SANDBOX_TEST
[Tasks]
Name: "autostart"; Description: "{cm:StartAtLogin}"; Flags: unchecked
Name: "contextmenu"; Description: "{cm:ContextMenu}"; Flags: unchecked
Name: "sendto"; Description: "{cm:SendTo}"; Flags: unchecked
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; Flags: unchecked
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
Filename: "{app}\PrometheaDrop.exe"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent
#endif
