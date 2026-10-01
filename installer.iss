#define AppName "Fungi Traductor"
#define AppVersion "2.0.0"
#define AppPublisher "fiumgi"
#define AppURL "https://github.com/fiumgi/Fungi-Traductor"

[Setup]
AppId={{E4A95D61-B8EC-4C6F-9B3B-ECA2AE3C7B27}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=FungiTraductor-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#AppName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\FungiTraductor.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Fungi Traductor"; Filename: "{app}\FungiTraductor.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Fungi Traductor"; Filename: "{app}\FungiTraductor.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\FungiTraductor.exe"; Description: "Iniciar {#AppName}"; Flags: nowait postinstall skipifsilent
