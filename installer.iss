; Inno Setup Script for E.V3 Desktop Companion
; Creates a professional Windows installer

#define MyAppName "E.V3 Desktop Companion"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "E.V3 Project"
#define MyAppURL "https://github.com/yourusername/E.V3"
#define MyAppExeName "EV3Companion.exe"
#define MyAppServiceExe "EV3Service.exe"

[Setup]
AppId={{E3V3-DESK-COMP-0001-000000000001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\E.V3
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer
OutputBaseFilename=EV3_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "installservice"; Description: "Install as Windows Service (auto-start with Windows)"; GroupDescription: "Service Options:"

[Files]
Source: "dist\EV3_Package\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\EV3_Package\{#MyAppServiceExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\EV3_Package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Start E.V3"; Filename: "{app}\Start_EV3.bat"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppServiceExe}"; Parameters: "install"; StatusMsg: "Installing Windows Service..."; Flags: runhidden; Tasks: installservice
Filename: "net"; Parameters: "start EV3CompanionService"; StatusMsg: "Starting service..."; Flags: runhidden; Tasks: installservice
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "net"; Parameters: "stop EV3CompanionService"; Flags: runhidden
Filename: "{app}\{#MyAppServiceExe}"; Parameters: "remove"; Flags: runhidden

[Code]
procedure InitializeWizard;
begin
  WizardForm.LicenseAcceptedRadio.Checked := True;
end;
