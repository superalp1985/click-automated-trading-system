; Trading System Installer Script
; Inno Setup Script

#define MyAppName "Automated Trading System"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Trading System"
#define MyAppExeName "start_manual.bat"

[Setup]
; Application information
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Output settings
OutputDir=..\output
OutputBaseFilename=TradingSystem_Setup_v{#MyAppVersion}
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Appearance
WizardStyle=modern
; Privileges
PrivilegesRequired=admin
; Misc
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main application files
Source: "..\source\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Documentation (included in installer)
Source: "..\docs\*.md"; DestDir: "{app}"; Flags: ignoreversion

; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop shortcut - automatically created
Name: "{autodesktop}\一键启动交易系统"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Check if required software is installed (optional)
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // Optional: You can add checks here to verify if MT5/Ollama are installed
  // For now, we let the user install them manually as per requirements
end;
