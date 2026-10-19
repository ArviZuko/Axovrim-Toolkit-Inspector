; ==============================================================================
; AXOVRIM — AI-Powered Toolkit Quality Inspection System
; Inno Setup 6 Installer Compilation Script
; Target OS: Windows 10 / 11 (64-bit Architecture)
; Default Destination: C:\Program Files\AXOVRIM
; ==============================================================================

#define AppName "AXOVRIM"
#define AppVersion "1.0.0"
#define AppPublisher "SmartLab - AXOVRIM Metrology Team"
#define AppExeName "AXOVRIM.exe"
#define AppSourceDir "..\AXOVRIM_GoogleDrive_Upload\05. Application"
#define AppGuid "{{D37F2C0B-4819-4A9B-89B7-23A44F5EE82A}"

[Setup]
; Unique application identifier for Windows Add/Remove Programs
AppId={#AppGuid}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}

; Default installation folder: C:\Program Files\AXOVRIM on 64-bit Windows
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes

; Output settings: Store installer in the Windows_Installer folder
OutputDir=.
OutputBaseFilename=AXOVRIM_Setup
SetupIconFile=app_icon.ico

; Compression configuration: High ratio LZMA2 solid compression
Compression=lzma2/normal
SolidCompression=yes

; Administrative privileges required for C:\Program Files\ installation
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; 64-bit architecture enforcement
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Wizard configuration
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
WizardStyle=modern

; Uninstaller metadata
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} Quality Inspection System

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Dirs]
; Ensure application root and persistent runtime data directories have user-modify permissions
; This prevents PermissionError on C:\Program Files\ when running inspections, reports, and calibration
Name: "{app}"; Permissions: users-modify
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\data\calibration"; Permissions: users-modify
Name: "{app}\data\inspections"; Permissions: users-modify
Name: "{app}\data\layouts"; Permissions: users-modify
Name: "{app}\output"; Permissions: users-modify
Name: "{app}\Reports"; Permissions: users-modify
Name: "{app}\Excel Sheet"; Permissions: users-modify

[Files]
; --- Authoritative Application Executable ---
Source: "{#AppSourceDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; --- Internal Bundled Python Runtimes, AI Engines (PyTorch, Ultralytics, pyrealsense2, PyQt5), & MSVC DLLs ---
Source: "{#AppSourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- Trained Deep Learning AI Models ---
Source: "{#AppSourceDir}\Models\*"; DestDir: "{app}\Models"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- Ground-Truth Reference Excel Workbooks (Dynamic Metrology & Expected Component Counts) ---
Source: "{#AppSourceDir}\Excel Sheet\*"; DestDir: "{app}\Excel Sheet"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- Application & Model Configuration Files ---
Source: "{#AppSourceDir}\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- Camera Calibration & Geometric Layout Profiles ---
Source: "{#AppSourceDir}\data\calibration\*"; DestDir: "{app}\data\calibration"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#AppSourceDir}\data\layouts\*"; DestDir: "{app}\data\layouts"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- UI Branding & Documentation Assets ---
Source: "{#AppSourceDir}\Smartlab Logo.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#AppSourceDir}\README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#AppSourceDir}\app_health.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#AppSourceDir}\model_status.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#AppSourceDir}\verification_report.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

; --- Optional External Dependency Installer (included only if present in dependencies folder) ---
#if FileExists("dependencies\vc_redist.x64.exe")
Source: "dependencies\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
#endif

[Icons]
; Start Menu shortcuts
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\app_icon.ico"; Comment: "AI-Powered Toolkit Quality Inspection System"
Name: "{group}\AXOVRIM Quick Start Guide"; Filename: "{app}\README.txt"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"; IconFilename: "{uninstallexe}"; Comment: "Uninstall AXOVRIM Application"

; Desktop shortcut (optional via Task)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon; Comment: "AI-Powered Toolkit Quality Inspection System"

[Run]
; Launch option on the finish screen
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"

[Code]
// =============================================================================
// Pascal Script: System Prerequisite Checks & Dependency Handling
// =============================================================================

function IsVCRedistInstalled(): Boolean;
var
  Installed: Cardinal;
begin
  Result := False;
  // Check standard x64 registry key for Visual C++ 2015-2022 Redistributable
  if RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) then
  begin
    Result := (Installed = 1);
  end
  else if RegQueryDWordValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) then
  begin
    Result := (Installed = 1);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  DepInstallerPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    DepInstallerPath := ExpandConstant('{tmp}\vc_redist.x64.exe');
    
    // If the dependency installer was packaged into {tmp}, execute it
    if FileExists(DepInstallerPath) then
    begin
      // Official Microsoft parameters for VC++ Redistributable:
      // /install - Perform installation
      // /quiet - Run silently without UI
      // /norestart - Suppress any unexpected reboot during setup
      WizardForm.StatusLabel.Caption := 'Installing system runtime dependencies...';
      
      if not Exec(DepInstallerPath, '/install /quiet /norestart', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
      begin
        MsgBox('Warning: Failed to launch dependency installer (vc_redist.x64.exe).' + #13#10 +
               'SysErrorMessage: ' + SysErrorMessage(ResultCode) + #13#10#13#10 +
               'Note: AXOVRIM already bundles necessary VC++ runtime DLLs in its _internal folder.', 
               mbInformation, MB_OK);
      end
      else if (ResultCode <> 0) and (ResultCode <> 3010) and (ResultCode <> 1638) then
      begin
        // 0 = Success, 3010 = Reboot required, 1638 = Newer version already installed
        MsgBox('Dependency installer returned exit code ' + IntToStr(ResultCode) + '.' + #13#10 +
               'Note: AXOVRIM bundles standalone runtime DLLs, but if startup issues occur, ' +
               'please install the Visual C++ 2015-2022 x64 Redistributable manually.',
               mbInformation, MB_OK);
      end;
    end
    else
    begin
      // Standalone bundled mode:
      // AXOVRIM already encapsulates vcruntime140.dll, vcruntime140_threads.dll, msvcp140.dll, 
      // MSVCP140_ATOMIC_WAIT.dll, ucrtbase.dll, and pyrealsense2 directly in {app}\_internal.
      Log('Standalone mode: All runtime DLLs are pre-bundled in _internal directory.');
    end;
  end;
end;
