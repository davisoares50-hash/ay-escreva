<#
  Atualização de ponta a ponta pelo próprio AY (entrega E): o AY instalado fecha, instala a versão nova e se reabre.

  1. Instala a versão anterior (-Anterior) e grava preferências no perfil real; deixa dois documentos em Documentos.
  2. Abre o AY instalado e, por UNO, chama ay_atualizacao.instalar() — o mesmo código do botão "Baixar e instalar" depois
     do download conferido —, com o instalador novo (-Nova) numa pasta de atualizações.
  3. Confere: o AY fechou, a versão nova foi instalada (registro e extensão), o AY abriu de novo sozinho, as preferências
     e os documentos continuam iguais. Depois desinstala e devolve o perfil que já existia na máquina.
  A busca e a conferência do arquivo de versões assinado são testadas em tests\atualizacao\testar_verificacao.py.
  SPDX-License-Identifier: MPL-2.0
#>
param([Parameter(Mandatory)][string]$Anterior, [Parameter(Mandatory)][string]$Nova, [string]$Saida)
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $Saida) { $Saida = Join-Path $Raiz 'tests\output\atualizacao-pelo-ay' }
New-Item -ItemType Directory -Force $Saida | Out-Null
$Anterior = (Resolve-Path $Anterior).Path; $Nova = (Resolve-Path $Nova).Path
$VersaoNova = ([regex]'AYEscreva-([0-9.]+)-').Match((Split-Path $Nova -Leaf)).Groups[1].Value
$AppId = '{4555F5FD-202B-4A8C-A427-E4CB4FDA6816}_is1'
$ChaveDesinst = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppId"
$PastaApp = Join-Path $env:LOCALAPPDATA 'Programs\AY ESCREVA'
$Perfil = Join-Path $env:APPDATA 'AYEscreva'
$Docs = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'AY-teste-atualizacao'
$itens = New-Object System.Collections.ArrayList
function Verificar([string]$descricao, [bool]$ok, [string]$detalhe = '') {
  [void]$itens.Add([ordered]@{ ok = $ok; verificacao = $descricao; detalhe = $detalhe })
  Write-Host ("[{0}] {1}{2}" -f $(if ($ok) { 'OK  ' } else { 'FALHA' }), $descricao, $(if ($detalhe) { " — $detalhe" } else { '' })) -ForegroundColor $(if ($ok) { 'Green' } else { 'Red' })
}
function Perfil-Uno([string]$modo, [string]$rotulo) {
  $json = Join-Path $Saida "perfil-$rotulo-$modo.json"
  $env:PYTHONIOENCODING = 'utf-8'
  & (Join-Path $PastaApp 'program\python.exe') (Join-Path $PSScriptRoot 'perfil_usuario.py') $modo (Join-Path $Perfil '1') $json 2>&1 | Out-Null
  if (Test-Path $json) { return Get-Content $json -Raw -Encoding UTF8 | ConvertFrom-Json }
  return $null
}
function Hashes { Get-ChildItem $Docs -File | ForEach-Object { "$($_.Name)=$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)" } }
function Desinstalar {
  $u = Join-Path $PastaApp 'unins000.exe'
  if (Test-Path $u) { Start-Process $u -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -Wait }
  $fim = (Get-Date).AddSeconds(180)
  while ((Get-Date) -lt $fim -and ((Test-Path (Join-Path $PastaApp 'program')) -or (Test-Path $ChaveDesinst))) { Start-Sleep -Seconds 1 }
}

if (Test-Path $ChaveDesinst) { throw 'Há um AY ESCREVA instalado: desinstale antes (o teste instala e desinstala).' }
$guarda = Join-Path $Saida 'perfil-guardado'
if (Test-Path $guarda) { Remove-Item $guarda -Recurse -Force }
$havia = Test-Path $Perfil
if ($havia) { Copy-Item $Perfil $guarda -Recurse }
New-Item -ItemType Directory -Force $Docs | Out-Null
Copy-Item (Join-Path $Raiz 'tests\fixtures\compatibilidade-ooxml.docx') (Join-Path $Docs 'relatorio.docx')
Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') (Join-Path $Docs 'trabalho.odt')
$hashes = Hashes
$pastaAtualizacoes = Join-Path $Saida 'atualizacoes'
New-Item -ItemType Directory -Force $pastaAtualizacoes | Out-Null
$novaLocal = Join-Path $pastaAtualizacoes (Split-Path $Nova -Leaf)
Copy-Item $Nova $novaLocal -Force

try {
  if (Test-Path $Perfil) { Remove-Item $Perfil -Recurse -Force }
  $p = Start-Process $Anterior -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER', "/LOG=`"$(Join-Path $Saida 'instalacao-anterior.log')`"" -Wait -PassThru
  $versaoAnterior = (Get-ItemProperty $ChaveDesinst -ErrorAction SilentlyContinue).DisplayVersion
  Verificar 'Versão anterior instalada' ($p.ExitCode -eq 0 -and $versaoAnterior) "código $($p.ExitCode); $versaoAnterior"
  $g = Perfil-Uno 'gravar' 'anterior'
  Verificar 'Preferências gravadas no perfil (dicionário pessoal, unidade de medida)' ($g -and $g.dicionario -and $g.unidade_mm) ($g | ConvertTo-Json -Compress)

  # o AY instalado é aberto e a atualização é pedida a ele (o mesmo código do botão "Baixar e instalar")
  $pipe = 'ay_atualiza_' + [guid]::NewGuid().ToString('N').Substring(0, 6)
  $ay = Start-Process (Join-Path $PastaApp 'program\soffice.exe') -ArgumentList '--writer', '--norestore', '--nologo', "--accept=pipe,name=$pipe;urp;" -PassThru
  $script = Join-Path $Saida 'pedir_atualizacao.py'
  @"
import sys, time
sys.path.insert(0, r'$Raiz\extensao\ayescreva\pythonpath')
import uno
from com.sun.star.connection import NoConnectException
local = uno.getComponentContext()
res = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local)
fim = time.time() + 90
while True:
    try:
        ctx = res.resolve('uno:pipe,name=$pipe;urp;StarOffice.ComponentContext'); break
    except NoConnectException:
        if time.time() > fim: raise
        time.sleep(0.5)
time.sleep(4)
import ay_atualizacao as A
A.registrar = print
print('roteiro', A.instalar(ctx, r'$novaLocal'), flush=True)
"@ | Set-Content -Encoding UTF8 $script
  $t0 = Get-Date
  & (Join-Path $PastaApp 'program\python.exe') $script 2>&1 | Out-File -Encoding utf8 (Join-Path $Saida 'pedir_atualizacao.log')
  $fechou = $ay.WaitForExit(60000)
  Verificar 'O AY fecha sozinho ao instalar (depois de conferir que não há documentos com alterações)' $fechou (Get-Content (Join-Path $Saida 'pedir_atualizacao.log') -Raw)

  # o roteiro instala a nova por cima e reabre o AY
  $fim = (Get-Date).AddSeconds(420); $versao = $null
  while ((Get-Date) -lt $fim) {
    $versao = (Get-ItemProperty $ChaveDesinst -ErrorAction SilentlyContinue).DisplayVersion
    if ($versao -like "$VersaoNova*" -and -not (Get-Process | Where-Object { $_.Path -eq $novaLocal -or $_.ProcessName -like 'AYEscreva-*' })) { break }
    Start-Sleep -Seconds 2
  }
  $ext = Join-Path $PastaApp 'share\extensions\ayescreva'
  $verExt = ([xml](Get-Content (Join-Path $ext 'description.xml') -Raw -Encoding UTF8)).description.version.value
  Verificar "A versão nova é instalada por cima ($VersaoNova)" ($versao -like "$VersaoNova*" -and $verExt -eq $VersaoNova) "registro $versao; extensão $verExt; $([int]((Get-Date) - $t0).TotalSeconds) s"
  $reaberto = $null; $fim = (Get-Date).AddSeconds(90)
  while ((Get-Date) -lt $fim -and -not $reaberto) {
    $reaberto = Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$PastaApp*" } | Select-Object -First 1
    Start-Sleep -Seconds 2
  }
  Verificar 'Depois de instalar, o AY abre de novo sozinho' ([bool]$reaberto) $(if ($reaberto) { "pid $($reaberto.Id)" } else { 'não reabriu' })
  Start-Sleep -Seconds 8
  Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$PastaApp*" } | ForEach-Object { [void]$_.CloseMainWindow(); [void]$_.WaitForExit(20000); if (-not $_.HasExited) { $_.Kill() } }
  $k = Perfil-Uno 'conferir' 'nova'
  Verificar 'Preferências preservadas e recursos novos registrados' ($k -and $k.dicionario -and $k.unidade_mm -and $k.comandos_entrega_b -and $k.comandos_entrega_c -and $k.versao_extensao -eq $VersaoNova) ($k | ConvertTo-Json -Compress)
  Verificar 'Documentos do usuário intactos' ((Compare-Object $hashes (Hashes)) -eq $null)
  Verificar 'Registro da instalação feita pelo roteiro (sem perguntas)' (Test-Path (Join-Path $pastaAtualizacoes 'instalacao.log')) (Join-Path $pastaAtualizacoes 'instalacao.log')
} finally {
  Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$PastaApp*" } | Stop-Process -Force -ErrorAction SilentlyContinue
  if (Test-Path $ChaveDesinst) { Desinstalar }
  if (Test-Path $Perfil) { Remove-Item $Perfil -Recurse -Force }
  if ($havia) { Copy-Item $guarda $Perfil -Recurse; Remove-Item $guarda -Recurse -Force }
  Remove-Item $Docs -Recurse -Force -ErrorAction SilentlyContinue
}
$ok = @($itens | Where-Object { $_.ok }).Count
[ordered]@{ data = (Get-Date -Format s); anterior = (Split-Path $Anterior -Leaf); nova = (Split-Path $Nova -Leaf); itens = $itens } |
  ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Saida 'resultado.json')
Write-Host "`nAtualização pelo AY: $ok/$($itens.Count) verificações aprovadas"
if ($ok -ne $itens.Count) { exit 1 }
