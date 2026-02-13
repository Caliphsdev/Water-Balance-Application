#define AppName "Water Balance Dashboard"
#define AppVersion "1.0.18"
#define AppPublisher "Two Rivers Platinum"
#define AppExeName "WaterBalanceDashboard.exe"
#define AppId "{{B6D7890D-9D39-4F3D-9F4D-9C0C3F7A2D11}}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\WaterBalanceDashboard
DefaultGroupName={#AppName}
OutputDir=dist\installer
OutputBaseFilename=WaterBalanceDashboard-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\..\src\ui\resources\icons\Water Balance.ico
UninstallDisplayIcon={app}\{#AppExeName}
DisableProgramGroupPage=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\..\dist\WaterBalanceDashboard\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "third_party\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /passive /norestart"; StatusMsg: "Installing Microsoft Visual C++ Runtime..."; Check: VCRedistNeedsInstall
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
function VCRedistNeedsInstall: Boolean;
var
	Installed: Cardinal;
begin
	Result := not RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) or (Installed = 0);
end;
