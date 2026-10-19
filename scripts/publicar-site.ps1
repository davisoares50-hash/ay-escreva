<#
.SYNOPSIS
  Publica uma versão do AY ESCREVA: instalador no GitHub Releases e site no GitHub Pages (ambos gratuitos).

.DESCRIPTION
  SEM -Executar (padrão), nada é enviado: o script confere os pré-requisitos, gera o site em modo de publicação
  em out\site-publicacao e mostra exatamente o que faria.
  COM -Executar (só com autorização do responsável pelo projeto):
    1. cria o repositório público, se não existir, e envia o branch main (-CriarRepositorio);
    2. cria a versão v<versão> no Releases (pré-lançamento) com o instalador e o SHA256SUMS.txt;
    3. confere por HTTPS que o arquivo publicado tem o mesmo SHA-256 do arquivo local;
    4. publica out\site-publicacao no branch gh-pages e ativa o GitHub Pages;
    5. espera o site responder e roda o teste do fluxo (tests\site\testar_fluxo.ps1) no endereço publicado.
  Não contrata serviço pago: repositório público, Releases e Pages são gratuitos (limites em docs\SITE.md).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\publicar-site.ps1 -Repositorio davisoares50-hash/ay-escreva
  powershell -ExecutionPolicy Bypass -File scripts\publicar-site.ps1 -Repositorio davisoares50-hash/ay-escreva -CriarRepositorio -Executar
#>
param(
  [Parameter(Mandatory)] [ValidatePattern('^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$')] [string]$Repositorio,
  [switch]$Executar,
  [switch]$CriarRepositorio,
  [switch]$SemTesteDeInstalacao
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Raiz = Split-Path -Parent $PSScriptRoot
$dono, $nome = $Repositorio -split '/'
$urlSite = "https://$($dono.ToLowerInvariant()).github.io/$nome/"
$versoes = Get-Content (Join-Path $Raiz 'site\versoes.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$versao = $versoes.atual
$entrada = $versoes.versoes | Where-Object { $_.versao -eq $versao }
$arquivo = ($entrada.arquivos | Where-Object { $_.plataforma -eq 'windows11-x64' }).arquivo
$exe = Join-Path $Raiz "out\instalador\$arquivo"
$pub = Join-Path $Raiz "out\publicacao\v$versao"
$siteDir = Join-Path $Raiz 'out\site-publicacao'
$tag = "v$versao"
function Passo([string]$t) { Write-Host "`n== $t" -ForegroundColor Cyan }
function Faria([string]$t) { Write-Host "   [simulação] $t" -ForegroundColor Yellow }
function Invocar-Gh { & gh.exe @args; if ($LASTEXITCODE) { throw "gh $($args -join ' ') falhou ($LASTEXITCODE)" } }
# Consulta que pode falhar (ex.: "existe?"): no PowerShell 5.1, stderr de programa externo com Stop vira exceção
function Sonda-Gh { $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'; & gh.exe @args 2>&1 | Out-Null; $ok = ($LASTEXITCODE -eq 0); $ErrorActionPreference = $eap; return $ok }

Passo "Pré-requisitos (versão $versao, $Repositorio)"
if (-not (Test-Path $exe)) { throw "Instalador não encontrado: $exe (rode scripts\instalador.ps1)" }
$hash = (Get-FileHash -Algorithm SHA256 $exe).Hash.ToLowerInvariant()
Write-Host "   instalador: $exe"
Write-Host "   SHA-256:    $hash"
if (-not (Sonda-Gh auth status)) { throw 'GitHub CLI sem login: rode "gh auth login".' }
$existe = Sonda-Gh repo view $Repositorio --json name
Write-Host "   repositório existe: $existe"
if (-not $existe -and -not $CriarRepositorio) { Write-Host '   (use -CriarRepositorio para criá-lo como público)' -ForegroundColor Yellow }
$sujo = git -C $Raiz status --porcelain
if ($sujo) { Write-Host '   aviso: há alterações não registradas em commit; o código publicado será o do último commit.' -ForegroundColor Yellow }

Passo 'Site em modo de publicação'
& node.exe (Join-Path $Raiz 'tools\gerar-site.mjs') --modo github --repositorio $Repositorio --saida $siteDir
if ($LASTEXITCODE) { throw 'gerar-site.mjs falhou' }
Set-Content -Path (Join-Path $siteDir '.nojekyll') -Value '' -Encoding ASCII
foreach ($f in 'SHA256SUMS.txt', 'NOTAS.md') { if (-not (Test-Path (Join-Path $pub $f))) { throw "Falta $pub\$f (gerado por gerar-site.mjs)" } }
$linha = Get-Content (Join-Path $pub 'SHA256SUMS.txt') | Where-Object { $_ -match [regex]::Escape($arquivo) }
if (-not $linha -or (($linha -split '\s+')[0]).ToLowerInvariant() -ne $hash) { throw 'SHA256SUMS.txt não corresponde ao instalador atual' }
Write-Host "   gerado em $siteDir"

# ---------------------------------------------------------------------------
Passo 'Repositório'
if (-not $existe) {
  if (-not $CriarRepositorio) { Faria "repositório $Repositorio não existe; nada será criado sem -CriarRepositorio" }
  elseif (-not $Executar) { Faria "gh repo create $Repositorio --public --source `"$Raiz`" --push" }
  else { Invocar-Gh repo create $Repositorio --public --description 'AY ESCREVA: editor de textos gratuito em português do Brasil' --source $Raiz --remote origin --push }
} else { Write-Host '   já existe' }

Passo "Versão $tag no GitHub Releases"
$titulo = "AY ESCREVA $versao — versão inicial de testes (Windows 11 x64)"
$temRelease = Sonda-Gh release view $tag --repo $Repositorio
if ($temRelease) { Write-Host '   já existe (arquivos não são substituídos; para trocar, crie uma nova versão)' }
elseif (-not $Executar) { Faria "gh release create $tag `"$exe`" `"$pub\SHA256SUMS.txt`" --repo $Repositorio --title `"$titulo`" --notes-file `"$pub\NOTAS.md`" --prerelease" }
else { Invocar-Gh release create $tag $exe (Join-Path $pub 'SHA256SUMS.txt') --repo $Repositorio --title $titulo --notes-file (Join-Path $pub 'NOTAS.md') --prerelease }

$urlArq = "https://github.com/$Repositorio/releases/download/$tag/$arquivo"
if ($Executar) {
  Passo 'Conferência do arquivo publicado (HTTPS)'
  $tmp = Join-Path $env:TEMP ('ay-pub-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
  New-Item -ItemType Directory $tmp | Out-Null
  Invoke-WebRequest $urlArq -OutFile (Join-Path $tmp $arquivo) -UseBasicParsing
  $h2 = (Get-FileHash -Algorithm SHA256 (Join-Path $tmp $arquivo)).Hash.ToLowerInvariant()
  Remove-Item -Recurse -Force $tmp
  if ($h2 -ne $hash) { throw "SHA-256 do arquivo publicado ($h2) difere do local ($hash)" }
  Write-Host "   $urlArq — SHA-256 confere"
} else { Faria "baixar $urlArq e conferir o SHA-256" }

Passo 'Site no GitHub Pages (branch gh-pages)'
if (-not $Executar) {
  Faria "enviar $siteDir para o branch gh-pages de $Repositorio (commit único, substitui o anterior)"
  Faria "gh api -X POST repos/$Repositorio/pages -f source[branch]=gh-pages -f source[path]=/  (se o Pages ainda não estiver ativo)"
} else {
  $tmp = Join-Path $env:TEMP ('ay-pages-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
  Copy-Item -Recurse $siteDir $tmp
  git -C $tmp init -q -b gh-pages
  git -C $tmp add -A
  # Identidade neutra no commit do site (endereço "noreply" do GitHub, não o e-mail pessoal)
  git -C $tmp -c user.name="AY ESCREVA (publicação)" -c user.email="$dono@users.noreply.github.com" commit -q -m "Site do AY ESCREVA $versao"
  # Credencial do gh só para este comando (não altera a configuração global do git)
  git -C $tmp -c credential.helper= -c 'credential.helper=!gh auth git-credential' push -q --force "https://github.com/$Repositorio.git" gh-pages
  if ($LASTEXITCODE) { throw 'git push do gh-pages falhou' }
  Remove-Item -Recurse -Force $tmp
  if (-not (Sonda-Gh api "repos/$Repositorio/pages")) { Invocar-Gh api -X POST "repos/$Repositorio/pages" -f 'source[branch]=gh-pages' -f 'source[path]=/' | Out-Null }
  Write-Host "   enviado; aguardando $urlSite"
  $fim = (Get-Date).AddMinutes(10); $ok = $false
  while ((Get-Date) -lt $fim -and -not $ok) {
    Start-Sleep -Seconds 15
    try { $ok = (Invoke-WebRequest "${urlSite}baixar.html" -UseBasicParsing -TimeoutSec 20).Content -match [regex]::Escape($hash) } catch {}
  }
  if (-not $ok) { throw "O site não respondeu com a versão $versao em 10 min: confira em https://github.com/$Repositorio/settings/pages" }
  Passo 'Teste do fluxo no endereço publicado'
  $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $Raiz 'tests\site\testar_fluxo.ps1'), '-Site', $urlSite)
  if ($SemTesteDeInstalacao) { $a += '-SemInstalar' }
  & powershell.exe @a
  if ($LASTEXITCODE) { throw 'teste do fluxo no site publicado falhou' }
}

Write-Host "`nSite: $urlSite"
Write-Host "Download: $urlArq"
if (-not $Executar) { Write-Host "`nSimulação concluída: nada foi enviado. Para publicar, repita com -Executar (e -CriarRepositorio se o repositório não existir)." -ForegroundColor Yellow }
