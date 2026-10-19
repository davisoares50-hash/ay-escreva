<#
.SYNOPSIS
  Testa o fluxo do site como uma pessoa faria: acessar → baixar → conferir SHA-256 → instalar → abrir.

.DESCRIPTION
  - Abre a página inicial e segue o botão "Baixar gratuitamente".
  - Na página Baixar, pega o link do botão principal e o SHA-256 mostrado na página.
  - Visita todas as páginas internas e confere que todo link de download responde (nenhum link fictício) e que
    as plataformas marcadas "Em desenvolvimento" não têm botão de download.
  - Baixa o instalador para uma pasta nova e vazia, confere o SHA-256 com o da página e com o SHA256SUMS da versão.
  - Entrega o arquivo baixado ao teste de instalação (tests\instalacao\testar_instalacao.ps1): instala, abre pela
    interface, cria/salva/reabre/exporta com o motor instalado e desinstala.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tests\site\testar_fluxo.ps1 -Site http://127.0.0.1:8737/
  powershell -ExecutionPolicy Bypass -File tests\site\testar_fluxo.ps1 -Site https://<dono>.github.io/<nome>/
#>
param([string]$Site = 'http://127.0.0.1:8737/', [switch]$SemInstalar)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Saida = Join-Path $Raiz 'tests\output\site'
New-Item -ItemType Directory -Force $Saida | Out-Null
if (-not $Site.EndsWith('/')) { $Site += '/' }
$base = [Uri]$Site
$itens = New-Object System.Collections.ArrayList
function Verificar([string]$descricao, [bool]$ok, [string]$detalhe = '') {
  [void]$itens.Add([ordered]@{ ok = $ok; verificacao = $descricao; detalhe = $detalhe })
  $m = if ($ok) { 'OK  ' } else { 'FALHA' }
  Write-Host ("[{0}] {1}{2}" -f $m, $descricao, $(if ($detalhe) { " — $detalhe" } else { '' })) -ForegroundColor $(if ($ok) { 'Green' } else { 'Red' })
}
function Absoluto([Uri]$pagina, [string]$href) { [Uri]::new($pagina, [Net.WebUtility]::HtmlDecode($href)) }
function Pagina([Uri]$u) { Invoke-WebRequest $u -UseBasicParsing -TimeoutSec 30 }

# ---------------------------------------------------------------------------
Write-Host "Site: $Site"
$ini = Pagina $base
Verificar 'página inicial responde' ($ini.StatusCode -eq 200) "HTTP $($ini.StatusCode)"
Verificar 'endereço usa HTTPS (exigido na publicação; a prévia local usa HTTP)' ($base.Scheme -eq 'https') $base.Scheme
$m = [regex]::Match($ini.Content, '<a[^>]*href="([^"]+)"[^>]*>(?:(?!</a>).)*?Baixar gratuitamente', 'Singleline')
Verificar 'botão "Baixar gratuitamente" na página inicial' $m.Success $(if ($m.Success) { $m.Groups[1].Value } else { '' })
$urlBaixar = Absoluto $base $m.Groups[1].Value
$pb = Pagina $urlBaixar
Verificar 'página Baixar responde' ($pb.StatusCode -eq 200) $urlBaixar.AbsoluteUri

$principal = [regex]::Match($pb.Content, '<div class="download-principal">.*?<a class="botao" href="([^"]+)" download>', 'Singleline')
Verificar 'botão principal de download na página Baixar' $principal.Success $(if ($principal.Success) { $principal.Groups[1].Value } else { '' })
$hashPagina = [regex]::Match($pb.Content, '<code class="hash" id="hash-win11">([0-9a-fA-F]{64})</code>').Groups[1].Value.ToLowerInvariant()
Verificar 'SHA-256 publicado na página Baixar' ($hashPagina.Length -eq 64) $hashPagina
$sums = [regex]::Match($pb.Content, 'href="([^"]+)">Arquivo SHA256SUMS')
Verificar 'link para o SHA256SUMS da versão' $sums.Success
Verificar 'aviso de instalador sem assinatura digital na página Baixar' ($pb.Content -match 'Sem assinatura digital')

# Plataformas em desenvolvimento não podem ter botão de download
$blocos = [regex]::Matches($pb.Content, '<div class="plataforma" data-plataforma="([^"]+)">(.*?)</div>\s*</div>', 'Singleline')
foreach ($b in $blocos) {
  $id = $b.Groups[1].Value; $tem = $b.Groups[2].Value -match '<a [^>]*download'
  $dev = $b.Groups[2].Value -match 'Em desenvolvimento'
  if ($id -eq 'windows11-x64') { Verificar "plataforma $id disponível com botão de download" ($tem -and -not $dev) }
  else { Verificar "plataforma $id em desenvolvimento, sem botão de download" ($dev -and -not $tem) }
}

# ---------------------------------------------------------------------------
Write-Host "`n== Links de download em todas as páginas"
$visitadas = @{}; $fila = New-Object System.Collections.Queue; $fila.Enqueue($base)
$downloads = @{}
while ($fila.Count) {
  $u = $fila.Dequeue(); $chave = $u.GetLeftPart([UriPartial]::Path)
  if ($visitadas.ContainsKey($chave)) { continue }
  $visitadas[$chave] = $true
  $r = Pagina $u
  foreach ($a in [regex]::Matches($r.Content, '<a\s[^>]*href="([^"#]+)(?:#[^"]*)?"[^>]*>')) {
    $alvo = Absoluto $u $a.Groups[1].Value
    if ($alvo.Host -ne $base.Host -and $alvo.AbsolutePath -notmatch '/releases/download/') { continue }
    if ($alvo.AbsolutePath -match '\.(exe|msi|dmg|pkg|AppImage|deb|rpm|zip|txt)$') { $downloads[$alvo.AbsoluteUri] = $u.AbsoluteUri }
    elseif ($alvo.Host -eq $base.Host -and $alvo.AbsolutePath.StartsWith($base.AbsolutePath) -and $alvo.AbsolutePath -match '(/|\.html)$') { $fila.Enqueue($alvo) }
  }
}
Verificar 'páginas internas visitadas' ($visitadas.Count -ge 6) "$($visitadas.Count) páginas"
foreach ($d in $downloads.Keys | Sort-Object) {
  try {
    $h = Invoke-WebRequest $d -Method Head -UseBasicParsing -TimeoutSec 30
    $tam = $h.Headers['Content-Length']
    Verificar "download responde: $(Split-Path -Leaf ([Uri]$d).AbsolutePath)" ($h.StatusCode -eq 200) "HTTP $($h.StatusCode), $tam bytes (em $($downloads[$d]))"
  } catch { Verificar "download responde: $d" $false "$($_.Exception.Message) (em $($downloads[$d]))" }
}

# ---------------------------------------------------------------------------
Write-Host "`n== Baixar e conferir"
$urlArq = Absoluto $urlBaixar $principal.Groups[1].Value
$pasta = Join-Path $env:TEMP ('ay-fluxo-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory $pasta | Out-Null
$arq = Join-Path $pasta ([Uri]::UnescapeDataString((Split-Path -Leaf $urlArq.AbsolutePath)))
$sw = [Diagnostics.Stopwatch]::StartNew()
Invoke-WebRequest $urlArq -OutFile $arq -UseBasicParsing -TimeoutSec 600
Verificar 'instalador baixado pelo botão principal' (Test-Path $arq) ('{0} — {1:N1} MB em {2:N0} s' -f (Split-Path -Leaf $arq), ((Get-Item $arq).Length / 1MB), $sw.Elapsed.TotalSeconds)
Verificar 'nome do arquivo identifica a versão de testes para Windows 11 x64' ((Split-Path -Leaf $arq) -match '^AYEscreva-\d+\.\d+\.\d+-teste-windows11-x64\.exe$') (Split-Path -Leaf $arq)
$hash = (Get-FileHash -Algorithm SHA256 $arq).Hash.ToLowerInvariant()
Verificar 'SHA-256 do arquivo baixado = SHA-256 da página' ($hash -eq $hashPagina) $hash
$txt = (Invoke-WebRequest (Absoluto $urlBaixar $sums.Groups[1].Value) -UseBasicParsing -TimeoutSec 30).Content
if ($txt -is [byte[]]) { $txt = [Text.Encoding]::UTF8.GetString($txt) }
$linha = ($txt -split "`n" | Where-Object { $_ -match [regex]::Escape((Split-Path -Leaf $arq)) } | Select-Object -First 1)
Verificar 'SHA-256 do arquivo baixado = SHA256SUMS da versão' ($linha -and ($linha.Trim() -split '\s+')[0].ToLowerInvariant() -eq $hash) "$linha".Trim()
$sig = Get-AuthenticodeSignature $arq
Verificar 'assinatura digital (esperado nesta versão: sem assinatura, como a página avisa)' ($sig.Status -eq 'NotSigned') "$($sig.Status)"

# ---------------------------------------------------------------------------
$codigoInst = $null
if (-not $SemInstalar) {
  Write-Host "`n== Instalar, abrir, usar e desinstalar o arquivo baixado"
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Raiz 'tests\instalacao\testar_instalacao.ps1') -Instalador $arq -Saida (Join-Path $Saida 'instalacao')
  $codigoInst = $LASTEXITCODE
  $ri = Get-Content (Join-Path $Saida 'instalacao\resultado.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  $ok = @($ri.itens | Where-Object ok).Count
  Verificar 'instalação, abertura, uso e desinstalação do arquivo baixado' ($codigoInst -eq 0) "$ok/$(@($ri.itens).Count) verificações do teste de instalação"
}
Remove-Item -Recurse -Force $pasta -ErrorAction SilentlyContinue

$falhas = @($itens | Where-Object { -not $_.ok -and $_.verificacao -notlike 'endereço usa HTTPS*' })
[ordered]@{ site = $Site; data = (Get-Date).ToString('s'); arquivo = (Split-Path -Leaf $arq); sha256 = $hash; itens = $itens } |
  ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $Saida 'fluxo.json')
Write-Host ("`nFluxo do site: {0}/{1} verificações aprovadas{2}" -f @($itens | Where-Object ok).Count, $itens.Count, $(if ($base.Scheme -ne 'https') { ' (HTTPS só se aplica ao site publicado)' } else { '' }))
if ($falhas.Count) { exit 1 }
