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
AppVerName=AY ESCREVA {#Versao} (versão de testes)
AppPublisher=Projeto AY ESCREVA
AppCopyright=Projeto AY ESCREVA - MPL-2.0
VersionInfoVersion={#Versao}
VersionInfoProductName=AY ESCREVA
VersionInfoDescription=Instalador do AY ESCREVA {#Versao} - versao de testes para Windows 11 x64
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
ptbr.WelcomeLabel2=Este assistente vai instalar o AY ESCREVA {#Versao} no seu computador.%n%nEsta é uma VERSÃO DE TESTES, validada somente no Windows 11 x64. Algumas ferramentas ainda estão em desenvolvimento; a lista está em "Limitações conhecidas", no menu Ajuda e no site.%n%nO AY ESCREVA é gratuito, funciona sem internet e não exige conta.

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"
Name: "associar"; Description: "Oferecer o AY ESCREVA em ""Abrir com"" para .docx, .odt, .doc, .rtf e .txt"; GroupDescription: "Arquivos:"

[Files]
; caches do Python criados quando a distribuição é usada em testes não entram no instalador
Source: "{#Dist}\*"; DestDir: "{app}"; Excludes: "__pycache__\*,*.pyc"; Flags: ignoreversion recursesubdirs createallsubdirs

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

[Code]
// O Python embutido grava caches (__pycache__) ao lado dos módulos enquanto o AY é usado, quando a pasta do programa
// permite escrita (instalação por usuário). Eles não vêm no instalador, então o desinstalador não os conhece e a pasta
// do programa ficava para trás. Só pastas __pycache__ dentro de {app} são apagadas; atalhos de pasta (pontos de nova
// análise) não são seguidos.
procedure ApagarCachesPython(const Pasta: string);
var
  R: TFindRec;
begin
  if FindFirst(Pasta + '\*', R) then
  try
    repeat
      if (R.Name <> '.') and (R.Name <> '..') and (R.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0)
        and (R.Attributes and FILE_ATTRIBUTE_REPARSE_POINT = 0) then
      begin
        if CompareText(R.Name, '__pycache__') = 0 then
          DelTree(Pasta + '\' + R.Name, True, True, True)
        else
          ApagarCachesPython(Pasta + '\' + R.Name);
      end;
    until not FindNext(R);
  finally
    FindClose(R);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  // antes de o desinstalador remover os arquivos, para que as pastas fiquem vazias e sejam removidas também
  if CurUninstallStep = usUninstall then
    ApagarCachesPython(ExpandConstant('{app}'));
end;
