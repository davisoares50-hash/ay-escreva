<#
.SYNOPSIS
  Atualização de uma instalação anterior do AY ESCREVA para a versão nova, preservando documentos e preferências.

.DESCRIPTION
  Para cada versão anterior indicada (ex.: 0.2.0 pública e 0.3.0):
    1. instala a versão anterior (silenciosa, por usuário);
    2. grava preferências no perfil real (%APPDATA%\AYEscreva\1): palavra no dicionário pessoal, unidade de medida
       e, se houver, a lista "não corrigir" da revisão de texto (tests\instalacao\perfil_usuario.py);
    3. instala a versão nova por cima;
    4. confere: versão no registro e na extensão, peças novas instaladas, preferências preservadas, comandos novos
       registrados no perfil antigo, documentos do usuário intactos (SHA-256);
    5. desinstala e confere que o programa saiu e que perfil e documentos ficaram.
  O perfil que existia antes do teste é guardado e devolvido no fim; a pasta de documentos de teste é apagada.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tests\instalacao\testar_atualizacao.ps1 -Nova out\instalador\AYEscreva-0.4.0-teste-windows11-x64.exe -Anteriores out\instalador\AYEscreva-0.2.0-teste-windows11-x64.exe,out\instalador\AYEscreva-0.3.0-teste-windows11-x64.exe
#>
param([Parameter(Mandatory)][string]$Nova, [Parameter(Mandatory)][string[]]$Anteriores, [string]$Saida)
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $Saida) { $Saida = Join-Path $Raiz 'tests\output\atualizacao' }
New-Item -ItemType Directory -Force $Saida | Out-Null
$Nova = (Resolve-Path $Nova).Path
# com -File, uma lista separada por vírgulas chega como um único texto
$Anteriores = @($Anteriores | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$VersaoNova = ([regex]'AYEscreva-([0-9.]+)-').Match((Split-Path $Nova -Leaf)).Groups[1].Value
$AppId = '{4555F5FD-202B-4A8C-A427-E4CB4FDA6816}_is1'
$ChaveDesinst = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppId"
$PastaApp = Join-Path $env:LOCALAPPDATA 'Programs\AY ESCREVA'
$Perfil = Join-Path $env:APPDATA 'AYEscreva'
$Docs = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'AY-teste-atualizacao'
$itens = New-Object System.Collections.ArrayList
function Verificar([string]$descricao, [bool]$ok, [string]$detalhe = '') {
  [void]$itens.Add([ordered]@{ ok = $ok; verificacao = $descricao; detalhe = $detalhe })
  $m = if ($ok) { 'OK  ' } else { 'FALHA' }
  Write-Host ("[{0}] {1}{2}" -f $m, $descricao, $(if ($detalhe) { " — $detalhe" } else { '' })) -ForegroundColor $(if ($ok) { 'Green' } else { 'Red' })
}
function Instalar([string]$exe, [string]$rotulo) {
  $p = Start-Process $exe -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER', '/TASKS="associar"', "/LOG=`"$(Join-Path $Saida "$rotulo.log")`"" -Wait -PassThru
  return $p.ExitCode
}
function Desinstalar {
  $u = Join-Path $PastaApp 'unins000.exe'
  if (Test-Path $u) { Start-Process $u -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -Wait }
  $fim = (Get-Date).AddSeconds(180)
  while ((Get-Date) -lt $fim -and ((Test-Path (Join-Path $PastaApp 'program')) -or (Test-Path $ChaveDesinst))) { Start-Sleep -Seconds 1 }
}
function Perfil-Uno([string]$modo, [string]$rotulo) {
  $json = Join-Path $Saida "perfil-$rotulo-$modo.json"
  $env:PYTHONIOENCODING = 'utf-8'
  & (Join-Path $PastaApp 'program\python.exe') (Join-Path $PSScriptRoot 'perfil_usuario.py') $modo (Join-Path $Perfil '1') $json 2>&1 | Out-Null
  if (Test-Path $json) { return Get-Content $json -Raw -Encoding UTF8 | ConvertFrom-Json }
  return $null
}
function Hashes { Get-ChildItem $Docs -File | ForEach-Object { "$($_.Name)=$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)" } }

if (Test-Path $ChaveDesinst) { throw 'Há um AY ESCREVA instalado: desinstale antes (o teste instala e desinstala versões).' }
# guarda o perfil existente e começa limpo
$guarda = Join-Path $Saida 'perfil-guardado'
if (Test-Path $guarda) { Remove-Item $guarda -Recurse -Force }
$havia = Test-Path $Perfil
if ($havia) { Copy-Item $Perfil $guarda -Recurse }
# documentos do usuário (fora da pasta do programa)
New-Item -ItemType Directory -Force $Docs | Out-Null
Copy-Item (Join-Path $Raiz 'tests\fixtures\compatibilidade-ooxml.docx') (Join-Path $Docs 'relatorio.docx')
Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') (Join-Path $Docs 'trabalho.odt')
$hashes = Hashes

try {
  foreach ($anterior in $Anteriores) {
    $anterior = (Resolve-Path $anterior).Path
    $versao = ([regex]'AYEscreva-([0-9.]+)-').Match((Split-Path $anterior -Leaf)).Groups[1].Value
    Write-Host "`n== $versao -> versão nova"
    if (Test-Path $Perfil) { Remove-Item $Perfil -Recurse -Force }
    $c = Instalar $anterior "instalacao-$versao"
    Verificar "$($versao): instalação da versão anterior" ($c -eq 0 -and (Get-ItemProperty $ChaveDesinst -ErrorAction SilentlyContinue).DisplayVersion -like "$versao*") "código $c"
    $g = Perfil-Uno 'gravar' $versao
    Verificar "$($versao): preferências gravadas no perfil (dicionário pessoal, unidade de medida$(if ($g.nao_corrigir -eq $true) { ', não corrigir' }))" ($g -and $g.dicionario -and $g.unidade_mm) ($g | ConvertTo-Json -Compress)
    $c = Instalar $Nova "atualizacao-$versao"
    $reg = Get-ItemProperty $ChaveDesinst -ErrorAction SilentlyContinue
    $ext = Join-Path $PastaApp 'share\extensions\ayescreva'
    $verExt = ([xml](Get-Content (Join-Path $ext 'description.xml') -Raw -Encoding UTF8)).description.version.value
    $novas = @('pythonpath\ay_academico.py', 'pythonpath\ay_formatar.py', 'pythonpath\ay_modelos.py', 'pythonpath\ay_galeria.py', 'dados\normas.json') | Where-Object { -not (Test-Path (Join-Path $ext $_)) }
    Verificar "$($versao): atualização instalada por cima (código 0, versão no registro e na extensão, peças novas presentes)" ($c -eq 0 -and $reg.DisplayVersion -like "$VersaoNova*" -and $verExt -eq $VersaoNova -and $novas.Count -eq 0) "código $c; registro $($reg.DisplayVersion); extensão $verExt; faltam: $($novas -join ', ')"
    $k = Perfil-Uno 'conferir' $versao
    $ok = $k -and $k.dicionario -and $k.unidade_mm -and $k.comandos_entrega_b -and $k.versao_extensao -eq $VersaoNova
    if ($g.nao_corrigir -eq $true) { $ok = $ok -and ($k.lista_nao_corrigir -contains 'nao') }
    Verificar "$($versao): preferências preservadas e recursos novos registrados no perfil antigo" $ok ($k | ConvertTo-Json -Compress)
    Verificar "$($versao): documentos do usuário intactos depois da atualização" ((Compare-Object $hashes (Hashes)) -eq $null)
    Desinstalar
    Verificar "$($versao): desinstalação remove o programa e o registro" (-not (Test-Path (Join-Path $PastaApp 'program')) -and -not (Test-Path $ChaveDesinst))
    $k2 = Test-Path (Join-Path $Perfil '1\user\wordbook\standard.dic')
    Verificar "$($versao): depois de desinstalar, perfil (com o dicionário pessoal) e documentos continuam" ($k2 -and (Compare-Object $hashes (Hashes)) -eq $null)
  }
} finally {
  if ((Test-Path $ChaveDesinst)) { Desinstalar }
  if (Test-Path $Perfil) { Remove-Item $Perfil -Recurse -Force }
  if ($havia) { Copy-Item $guarda $Perfil -Recurse; Remove-Item $guarda -Recurse -Force }
  Remove-Item $Docs -Recurse -Force -ErrorAction SilentlyContinue
}
$ok = @($itens | Where-Object { $_.ok }).Count
[ordered]@{ data = (Get-Date -Format s); nova = (Split-Path $Nova -Leaf); anteriores = @($Anteriores | ForEach-Object { Split-Path $_ -Leaf }); itens = $itens } |
  ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Saida 'resultado.json')
Write-Host "`nAtualização: $ok/$($itens.Count) verificações aprovadas"
if ($ok -ne $itens.Count) { exit 1 }
