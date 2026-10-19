; AY ESCREVA - instalador da versão inicial de testes para Windows 11 x64 (Inno Setup 6)
; Gerado por scripts\instalador.ps1 a partir de dist\AY ESCREVA.
; Instala por usuário (sem administrador) por padrão; o assistente permite instalar para todos.
; SPDX-License-Identifier: MPL-2.0

#ifndef Versao
  #define Versao "0.1.0"
#endif
#ifndef Canal
  #define Canal "teste"
#endif
#ifndef Dist
  #define Dist "..\dist\AY ESCREVA"
#endif
#ifndef Marca
  #define Marca "..\out\marca"
#endif
#ifndef Saida
  #define Saida "..\out\instalador"
#endif

[Setup]
; Identificador fixo do produto: não alterar entre versões (permite atualização no lugar)
AppId={{4555F5FD-202B-4A8C-A427-E4CB4FDA6816}
AppName=AY ESCREVA
AppVersion={#Versao}
AppVerName=AY ESCREVA {#Versao} (versão inicial de testes)
AppPublisher=Projeto AY ESCREVA
AppCopyright=Projeto AY ESCREVA - MPL-2.0
VersionInfoVersion={#Versao}
VersionInfoProductName=AY ESCREVA
VersionInfoDescription=Instalador do AY ESCREVA {#Versao} - versao inicial de testes para Windows 11 x64
DefaultDirName={autopf}\AY ESCREVA
DefaultGroupName=AY ESCREVA
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Versão inicial de testes: só Windows 11 (build 22000+) foi validado. O motor aceitaria Windows 10, mas o
; suporte só será declarado depois de testado.
MinVersion=10.0.22000
LicenseFile=LICENCA.txt
SetupIconFile={#Marca}\ayescreva.ico
WizardImageFile={#Marca}\instalador-lateral.bmp,{#Marca}\instalador-lateral-2x.bmp
WizardSmallImageFile={#Marca}\instalador-topo.bmp,{#Marca}\instalador-topo-2x.bmp
WizardStyle=modern
UninstallDisplayIcon={app}\AYEscreva.exe
UninstallDisplayName=AY ESCREVA {#Versao} (testes)
OutputDir={#Saida}
OutputBaseFilename=AYEscreva-{#Versao}-{#Canal}-windows11-x64
Compression=lzma2/max
SolidCompression=yes
LZMANumBlockThreads=4
ChangesAssociations=yes
CloseApplications=yes
RestartApplications=no
; Assinatura de código (quando houver certificado): configure a ferramenta "assinar" no ISCC e descomente
; SignTool=assinar $f
; SignedUninstaller=yes

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Messages]
ptbr.WelcomeLabel2=Este assistente vai instalar o AY ESCREVA {#Versao} no seu computador.%n%nEsta é uma VERSÃO INICIAL DE TESTES, validada somente no Windows 11 x64. Algumas ferramentas ainda estão em desenvolvimento; a lista está em "Limitações conhecidas", no menu Ajuda e no site.%n%nO AY ESCREVA é gratuito, funciona sem internet e não exige conta.

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"
Name: "associar"; Description: "Oferecer o AY ESCREVA em ""Abrir com"" para .docx, .odt, .doc, .rtf e .txt"; GroupDescription: "Arquivos:"

[Files]
Source: "{#Dist}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\AY ESCREVA"; Filename: "{app}\AYEscreva.exe"; Comment: "Editor de textos AY ESCREVA"
Name: "{autodesktop}\AY ESCREVA"; Filename: "{app}\AYEscreva.exe"; Tasks: desktopicon

[Registry]
; Tipo de documento do AY (não toma o programa padrão do usuário; só aparece em "Abrir com")
Root: HKA; Subkey: "Software\Classes\AYEscreva.Documento"; ValueType: string; ValueName: ""; ValueData: "Documento de texto"; Flags: uninsdeletekey; Tasks: associar
Root: HKA; Subkey: "Software\Classes\AYEscreva.Documento\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\AYEscreva.exe,0"; Tasks: associar
Root: HKA; Subkey: "Software\Classes\AYEscreva.Documento\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\AYEscreva.exe"" ""%1"""; Tasks: associar
Root: HKA; Subkey: "Software\Classes\.docx\OpenWithProgids"; ValueType: string; ValueName: "AYEscreva.Documento"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associar
Root: HKA; Subkey: "Software\Classes\.odt\OpenWithProgids"; ValueType: string; ValueName: "AYEscreva.Documento"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associar
Root: HKA; Subkey: "Software\Classes\.doc\OpenWithProgids"; ValueType: string; ValueName: "AYEscreva.Documento"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associar
Root: HKA; Subkey: "Software\Classes\.rtf\OpenWithProgids"; ValueType: string; ValueName: "AYEscreva.Documento"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associar
Root: HKA; Subkey: "Software\Classes\.txt\OpenWithProgids"; ValueType: string; ValueName: "AYEscreva.Documento"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associar
Root: HKA; Subkey: "Software\Classes\Applications\AYEscreva.exe"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "AY ESCREVA"; Flags: uninsdeletekey; Tasks: associar
Root: HKA; Subkey: "Software\Classes\Applications\AYEscreva.exe\SupportedTypes"; ValueType: string; ValueName: ".docx"; ValueData: ""; Tasks: associar
Root: HKA; Subkey: "Software\Classes\Applications\AYEscreva.exe\SupportedTypes"; ValueType: string; ValueName: ".odt"; ValueData: ""; Tasks: associar
Root: HKA; Subkey: "Software\Classes\Applications\AYEscreva.exe\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\AYEscreva.exe"" ""%1"""; Tasks: associar

[Run]
Filename: "{app}\AYEscreva.exe"; Description: "Abrir o AY ESCREVA"; Flags: nowait postinstall skipifsilent

; O perfil do usuário (%APPDATA%\AYEscreva) guarda preferências, dicionário pessoal e cópias de recuperação.
; Ele NÃO é apagado na desinstalação, para não perder dados do usuário.
