<#
.SYNOPSIS
  Monta a distribuição do AY ESCREVA para Windows x64 a partir da base fixada em base\base.lock.json.

.DESCRIPTION
  1. Baixa os pacotes oficiais da base (se ainda não estiverem em _cache) e confere o SHA-256 fixado.
     Se o gpg estiver disponível, confere também a assinatura PGP da The Document Foundation.
  2. Extrai os pacotes MSI por instalação administrativa (msiexec /a), sem instalar nada no sistema.
  3. Copia a base para dist\, move as fontes para uso privado, copia o runtime do Visual C++ ao lado
     dos executáveis e remove idiomas, dicionários e componentes de rede que o AY não usa.
  4. Aplica a camada AY (layer\), a identidade visual (tools\marca.mjs) e ajusta os arquivos .ini.
  5. Compila o lançador AYEscreva.exe com o csc do .NET Framework 4.x.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\montar.ps1
#>
[CmdletBinding()]
param(
  [string]$Saida,
  [switch]$SemAssinaturaPGP
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$Raiz = Split-Path -Parent $PSScriptRoot
if (-not $Saida) { $Saida = Join-Path $Raiz 'dist\AY ESCREVA' }
$Lock = Get-Content (Join-Path $Raiz 'base\base.lock.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Cache = Join-Path $Raiz '_cache'
$Downloads = Join-Path $Cache 'downloads'
$Base = Join-Path $Cache ('base\' + $Lock.versao)
$Marca = Join-Path $Raiz 'out\marca'
$VersaoAY = (Select-String -Path (Join-Path $Raiz 'launcher\AYEscreva.cs') -Pattern 'Versao = "([0-9.]+)"').Matches[0].Groups[1].Value

function Etapa($texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }
function Robo([string]$de, [string]$para, [string[]]$extra) {
  $a = @($de, $para, '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/R:1', '/W:1') + $extra
  & robocopy.exe @a | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "robocopy falhou ($LASTEXITCODE): $de -> $para" }
}

# ---------------------------------------------------------------------------
Etapa "Base $($Lock.produto) $($Lock.versao): download e verificação"
New-Item -ItemType Directory -Force $Downloads | Out-Null
$gpg = $null
if (-not $SemAssinaturaPGP) {
  foreach ($c in @('gpg.exe', "$env:ProgramFiles\Git\usr\bin\gpg.exe")) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { $gpg = $cmd.Source; break }
  }
}
foreach ($arq in $Lock.arquivos) {
  $destino = Join-Path $Downloads $arq.nome
  if (-not (Test-Path $destino)) {
    Write-Host "Baixando $($arq.nome)..."
    & curl.exe -sSL --fail -o $destino $arq.url
    if ($LASTEXITCODE -ne 0) { throw "Falha ao baixar $($arq.url)" }
  }
  $hash = (Get-FileHash -Algorithm SHA256 $destino).Hash.ToLowerInvariant()
  if ($hash -ne $arq.sha256) { throw "SHA-256 divergente para $($arq.nome): $hash (esperado $($arq.sha256))" }
  Write-Host "SHA-256 ok: $($arq.nome)"
  $sig = Get-AuthenticodeSignature $destino
  if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -ne $Lock.authenticode) {
    throw "Assinatura Authenticode inesperada em $($arq.nome): $($sig.Status) $($sig.SignerCertificate.Subject)"
  }
  if ($gpg) {
    $asc = "$destino.asc"
    if (-not (Test-Path $asc)) { & curl.exe -sSL --fail -o $asc ($arq.url + '.asc') }
    $pastaGpg = Join-Path $Cache 'gnupg'
    New-Item -ItemType Directory -Force $pastaGpg | Out-Null
    # O gpg do Git para Windows (MSYS) só entende caminhos no formato /e/pasta/arquivo.
    $msys = $gpg -like '*\usr\bin\gpg.exe'
    function CaminhoGpg([string]$p) { if ($msys) { '/' + $p.Substring(0, 1).ToLower() + ($p.Substring(2) -replace '\\', '/') } else { $p } }
    $fp = $Lock.chavePGP.fingerprint
    $chave = Join-Path $Cache 'tdf-chave.asc'
    # O gpg escreve diagnósticos no stderr; no PowerShell 5.1 isso não pode virar erro fatal.
    $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
      $temChave = & $gpg --homedir (CaminhoGpg $pastaGpg) --batch --list-keys $fp 2>&1 | Out-String
      if ($temChave -notmatch $fp) {
        & curl.exe -sSL --fail -o $chave "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0x$fp"
        & $gpg --homedir (CaminhoGpg $pastaGpg) --batch --import (CaminhoGpg $chave) 2>&1 | Out-Null
      }
      $saidaGpg = & $gpg --homedir (CaminhoGpg $pastaGpg) --batch --status-fd 1 --verify (CaminhoGpg $asc) (CaminhoGpg $destino) 2>&1 | Out-String
    } finally { $ErrorActionPreference = $eap }
    if ($saidaGpg -notmatch "VALIDSIG $fp") { throw "Assinatura PGP inválida em $($arq.nome)" }
    Write-Host "PGP ok: $($arq.nome) ($fp)"
  }
}

# ---------------------------------------------------------------------------
Etapa 'Extração administrativa dos pacotes MSI'
if (-not (Test-Path (Join-Path $Base 'program\soffice.exe'))) {
  New-Item -ItemType Directory -Force $Base | Out-Null
  foreach ($arq in $Lock.arquivos) {
    $msi = Join-Path $Downloads $arq.nome
    $p = Start-Process msiexec.exe -Wait -PassThru -ArgumentList @('/a', "`"$msi`"", '/qn', "TARGETDIR=`"$Base`"")
    if ($p.ExitCode -ne 0) { throw "msiexec /a falhou ($($p.ExitCode)) em $($arq.nome)" }
  }
} else { Write-Host "Já extraído em $Base" }

# ---------------------------------------------------------------------------
Etapa "Cópia para $Saida"
if (Test-Path $Saida) { Remove-Item -Recurse -Force $Saida }
New-Item -ItemType Directory -Force $Saida | Out-Null
Robo $Base $Saida @('/XF', '*.msi', '/XD', (Join-Path $Base 'System'), (Join-Path $Base 'System64'), (Join-Path $Base 'Fonts'))
# Fontes da base: registradas de forma privada pelo motor a partir de share\fonts\truetype
Robo (Join-Path $Base 'Fonts') (Join-Path $Saida 'share\fonts\truetype') @()
# Runtime do Visual C++ (implantação local ao lado dos executáveis)
Copy-Item (Join-Path $Base 'System64\*.dll') (Join-Path $Saida 'program') -Force

# ---------------------------------------------------------------------------
Etapa 'Remoção de idiomas e componentes não usados'
$idiomas = @($Lock.idiomasInterface)
$idiomasRes = $idiomas | ForEach-Object { $_ -replace '-', '_' }
Get-ChildItem (Join-Path $Saida 'program\resource') -Directory | Where-Object { $idiomasRes -notcontains $_.Name } | Remove-Item -Recurse -Force
Get-ChildItem (Join-Path $Saida 'share\registry') -Filter 'Langpack-*.xcd' | Where-Object { $idiomas -notcontains ($_.BaseName -replace '^Langpack-', '') } | Remove-Item -Force
Get-ChildItem (Join-Path $Saida 'share\registry\res') -Filter '*.xcd' | Where-Object { $idiomas -notcontains ($_.BaseName -replace '^(fcfg_langpack|registry)_', '') } | Remove-Item -Force
foreach ($pasta in @('share\autotext', 'share\template')) {
  Get-ChildItem (Join-Path $Saida $pasta) -Directory | Where-Object { @('common', 'shellnew', 'wizard') + $idiomas -notcontains $_.Name } | Remove-Item -Recurse -Force
}
Get-ChildItem (Join-Path $Saida 'readmes') -File | Where-Object { $idiomas -notcontains ($_.BaseName -replace '^readme_', '') } | Remove-Item -Force
$dics = @($Lock.dicionarios | ForEach-Object { "dict-$_" })
Get-ChildItem (Join-Path $Saida 'share\extensions') -Directory |
  Where-Object { ($_.Name -like 'dict-*' -and $dics -notcontains $_.Name) -or (@($Lock.removerExtensoes) -contains $_.Name) } |
  Remove-Item -Recurse -Force
foreach ($x in $Lock.removerConfiguracoes) { Remove-Item -Force (Join-Path $Saida "share\registry\$x") -ErrorAction SilentlyContinue }

# ---------------------------------------------------------------------------
Etapa 'Identidade visual'
Push-Location (Join-Path $Raiz 'tools')
try {
  if (-not (Test-Path 'node_modules')) { & npm.cmd ci --no-audit --no-fund; if ($LASTEXITCODE) { throw 'npm ci falhou' } }
  $fontes = Join-Path $Saida 'share\fonts\truetype'
  & node.exe marca.mjs (Join-Path $fontes 'Rubik-Bold.ttf') (Join-Path $fontes 'Rubik-Regular.ttf') $Marca
  if ($LASTEXITCODE) { throw 'Geração da marca falhou' }
} finally { Pop-Location }
Copy-Item (Join-Path $Marca 'intro.png'), (Join-Path $Marca 'intro-highres.png') (Join-Path $Saida 'program') -Force
foreach ($svg in 'about.svg', 'logo.svg', 'logo_inverted.svg', 'logo-sc.svg', 'logo-sc_inverted.svg') {
  Copy-Item (Join-Path $Marca $svg) (Join-Path $Saida "program\shell\$svg") -Force
}
Copy-Item (Join-Path $Marca 'ayescreva.ico') $Saida -Force

# ---------------------------------------------------------------------------
Etapa 'Camada de configuração AY'
Robo (Join-Path $Raiz 'layer') $Saida @()

Etapa 'Faixa de opções AY (gerada de ui\abas.json)'
& node.exe (Join-Path $Raiz 'tools\gerar-faixa.mjs') (Join-Path $Raiz 'ui\abas.json') `
  (Join-Path $Saida 'share\config\soffice.cfg\modules\swriter\ui\notebookbar_ayescreva.ui') `
  (Join-Path $Saida 'share\config\images_colibre.zip') '-' (Join-Path $Raiz 'out\faixa\mapa.json')
if ($LASTEXITCODE) { throw 'Geração da faixa falhou' }

Etapa 'Extensão AY (comandos, avisos de perdas e de fontes, ajuda offline)'
$ext = Join-Path $Saida 'share\extensions\ayescreva'
Robo (Join-Path $Raiz 'extensao\ayescreva') $ext @()
# Página de atalhos gerada da configuração REAL do motor montado (nunca lista atalho inexistente)
& node.exe (Join-Path $Raiz 'tools\gerar-atalhos.mjs') (Join-Path $Saida 'share\registry') (Join-Path $ext 'ajuda\atalhos.html')
if ($LASTEXITCODE) { throw 'Geração da página de atalhos falhou' }

function Definir-Ini([string]$arquivo, [hashtable]$valores) {
  $linhas = [IO.File]::ReadAllLines($arquivo)
  $vistos = @{}
  $novas = foreach ($l in $linhas) {
    if ($l -match '^([^=;\[]+)=') {
      $k = $Matches[1]
      if ($valores.ContainsKey($k)) { $vistos[$k] = $true; "$k=$($valores[$k])"; continue }
    }
    $l
  }
  $faltam = $valores.Keys | Where-Object { -not $vistos.ContainsKey($_) } | ForEach-Object { "$_=$($valores[$_])" }
  [IO.File]::WriteAllLines($arquivo, @($novas) + @($faltam), (New-Object Text.UTF8Encoding($false)))
}
$prog = Join-Path $Saida 'program'
# Perfil de usuário próprio (%APPDATA%\AYEscreva\1): não interfere em um LibreOffice instalado
Definir-Ini (Join-Path $prog 'bootstrap.ini') @{ ProductKey = "AY ESCREVA $VersaoAY"; UserInstallation = '$SYSUSERCONFIG/AYEscreva/1' }
# Sem verificação de atualização da base; fornecedor identificado como o projeto AY
Definir-Ini (Join-Path $prog 'version.ini') @{ Vendor = 'Projeto AY ESCREVA'; UpdateURL = ''; ExtensionUpdateURL = ''; UpdateChannel = ''; UpdateID = '' }
# Tela de abertura (geometria casada com tools\marca.mjs) e sem coleta de despejos de falha
Definir-Ini (Join-Path $prog 'soffice.ini') @{
  CrashDumpEnable = 'false'; Logo = '1'; NativeProgress = 'false'
  ProgressPosition = '176,150'; ProgressSize = '440,6'; ProgressBarColor = '17,128,106'
  ProgressFrameColor = '214,222,220'; ProgressTextColor = '91,102,100'; ProgressTextBaseline = '178'
}

# ---------------------------------------------------------------------------
Etapa 'Lançador AYEscreva.exe'
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path $csc)) { throw "csc.exe não encontrado em $csc (.NET Framework 4.x)" }
& $csc /nologo /target:winexe /optimize+ /utf8output /codepage:65001 `
  "/win32icon:$(Join-Path $Marca 'ayescreva.ico')" "/out:$(Join-Path $Saida 'AYEscreva.exe')" `
  /r:System.Windows.Forms.dll (Join-Path $Raiz 'launcher\AYEscreva.cs')
if ($LASTEXITCODE) { throw 'Compilação do lançador falhou' }

# ---------------------------------------------------------------------------
Etapa 'Manifesto da distribuição'
$manifesto = [ordered]@{
  produto = 'AY ESCREVA'; versao = $VersaoAY; canal = 'versão inicial de testes'; plataformaValidada = 'Windows 11 x64'
  base = [ordered]@{ produto = $Lock.produto; versao = $Lock.versaoCompleta; buildid = $Lock.buildid; codigoFonte = $Lock.codigoFonte }
  montadoEm = (Get-Date).ToString('s')
}
$manifesto | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $Saida 'ay-escreva.json')
Copy-Item (Join-Path $Raiz 'docs\LICENCAS.md') $Saida -Force -ErrorAction SilentlyContinue

$tam = (Get-ChildItem $Saida -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
Write-Host ("`nDistribuição pronta: {0} ({1:N0} MB)" -f $Saida, $tam) -ForegroundColor Green
