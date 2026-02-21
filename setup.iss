; AutoGPT Trading System Installer Script
; Inno Setup Script

#define MyAppName "AutoGPT Trading System"
#define MyAppVersion "1.0"
#define MyAppPublisher "AutoGPT Trading"
#define MyAppURL "https://example.com"
#define MyAppExeName "web_interface.py"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{A8F2E9D1-3B4C-5D6E-7F8A-9B0C1D2E3F4A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\TradingSystem
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Output settings
OutputDir=Desktop
OutputBaseFilename=AutoGPT_Trading_System_Setup
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Appearance
WizardStyle=modern
; Privileges
PrivilegesRequired=admin
; Uninstaller
UninstallDisplayIcon={app}\web_interface.py

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main Python files
Source: "E:\TradingSystem\autogpt_trading.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\executor_agent.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\web_interface.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\window_manager.py"; DestDir: "{app}"; Flags: ignoreversion

; Configuration files
Source: "E:\TradingSystem\config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\mt5_positions.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\market_cache.json"; DestDir: "{app}"; Flags: ignoreversion

; Start scripts
Source: "E:\TradingSystem\start_manual.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\start_trading_fixed.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\start_trading_simple.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\start_trading_simple_fixed.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\start_trading.bat"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "E:\TradingSystem\commands.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\commands_help.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\executor_changes_20260220_2224.txt"; DestDir: "{app}"; Flags: ignoreversion

; Test files
Source: "E:\TradingSystem\test_all_endpoints.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\TradingSystem\test_log_sending.py"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\start_trading_simple.bat"
Name: "{autoprograms}\{#MyAppName} - Manual Start"; Filename: "{app}\start_manual.bat"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\start_trading_simple.bat"; Tasks: desktopicon

[Run]
Filename: "{app}\start_trading_simple.bat"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
// Custom code to check for prerequisites
function InitializeSetup(): Boolean;
var
  PythonInstalled: Boolean;
  ErrorMsg: String;
begin
  Result := True;
  ErrorMsg := '';
  
  // Check for Python 3.9+
  PythonInstalled := FileExists(ExpandConstant('{pf}\Python312\python.exe')) or 
                     FileExists(ExpandConstant('{pf}\Python311\python.exe')) or
                     FileExists(ExpandConstant('{pf}\Python310\python.exe')) or
                     FileExists(ExpandConstant('{pf}\Python39\python.exe')) or
                     FileExists(ExpandConstant('{pf}\Python38\python.exe'));
  
  if not PythonInstalled then
  begin
    ErrorMsg := 'Python 3.9+ is not installed.' + #13#10;
    ErrorMsg := ErrorMsg + 'Please download from: https://www.python.org/downloads/' + #13#10;
  end;
  
  if (ErrorMsg <> '') then
  begin
    MsgBox('Prerequisites not met:' + #13#10 + #13#10 + ErrorMsg, mbError, MB_OK);
    Result := False;
  end;
end;
