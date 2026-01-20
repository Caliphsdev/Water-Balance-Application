# Inno Setup Script
# Water Balance Application Installer

[Setup]
AppName=Water Balance Application
AppVersion=1.0.0
AppPublisher=TransAfrica Resources
AppPublisherURL=https://transafrica-resources.com
AppSupportURL=https://transafrica-resources.com/support
AppUpdatesURL=https://transafrica-resources.com/updates
DefaultDirName={autopf}\WaterBalance
DefaultGroupName=Water Balance
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer_output
OutputBaseFilename=WaterBalanceSetup_v1.0.0
SetupIconFile=logo\Water Balance.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\WaterBalance.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\WaterBalance\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "INSTALLATION.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Water Balance"; Filename: "{app}\WaterBalance.exe"
Name: "{group}\{cm:UninstallProgram,Water Balance}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Water Balance"; Filename: "{app}\WaterBalance.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Water Balance"; Filename: "{app}\WaterBalance.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\WaterBalance.exe"; Description: "{cm:LaunchProgram,Water Balance}"; Flags: nowait postinstall skipifsilent

[Dirs]
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\config"; Permissions: users-modify
Name: "{app}\reports"; Permissions: users-modify

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create empty log files
    SaveStringToFile(ExpandConstant('{app}\logs\water_balance.log'), '', False);
    SaveStringToFile(ExpandConstant('{app}\logs\errors.log'), '', False);
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  // Check Windows version
  if not IsWindows10OrLater() then
  begin
    MsgBox('This application requires Windows 10 or later.', mbError, MB_OK);
    Result := False;
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: files; Name: "{app}\*.pyc"
Type: files; Name: "{app}\*.log"
