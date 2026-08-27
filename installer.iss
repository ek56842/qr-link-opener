#define MyAppName "QR Link Opener"
#ifndef APP_VERSION
  #define APP_VERSION "0.0.0-dev"
#endif
#define MyAppVersion APP_VERSION
#define MyAppExeName "QR-Link-Opener-" + MyAppVersion + "-portable.exe"

[Setup]
AppId={{7E4E30BA-7A55-4CC0-98BE-1D57681A64E4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\QRLinkOpener
DefaultGroupName={#MyAppName}
OutputDir=installer-output
OutputBaseFilename=QR-Link-Opener-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; DestName: "QR Link Opener.exe"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\QR Link Opener.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\QR Link Opener.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "建立桌面捷徑"; GroupDescription: "額外捷徑："
Name: "autostart"; Description: "登入 Windows 後自動啟動"; GroupDescription: "啟動選項："; Flags: checkedonce

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "QRLinkOpener"; ValueData: """{app}\QR Link Opener.exe"""; Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\QR Link Opener.exe"; Description: "立即啟動 {#MyAppName}"; Flags: nowait postinstall skipifsilent
