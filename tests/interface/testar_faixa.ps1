<#
.SYNOPSIS
  Testa a faixa de opções do AY ESCREVA pela interface, de dentro do aplicativo (UITest).
.DESCRIPTION
  Cria perfis descartáveis, instala neles a extensão de testes (tests\interface\extensao_testes), abre o AY e
  espera o relatório. Nada é instalado no perfil real do usuário. Usa diálogos de arquivo do próprio
  aplicativo (não os do Windows) para que o teste consiga fechá-los.
    Fase 1: documento ODT de trabalho — presença de todos os botões, efeitos conferidos, acionamento genérico,
            abas contextuais e Salvar em ODT.
    Fase 2: DOCX de compatibilidade aberto na inicialização — aviso de fontes substituídas e aviso de perdas
            ao salvar em DOCX (com cópia em ODT).
    Fase 3: outro DOCX alterado, fechado pela faixa com "Salvar" na pergunta — aviso de perdas, gravação e
            fechamento da janela.
  O relatório final (tests\output\interface\faixa-resultado.json) junta as três fases.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tests\interface\testar_faixa.ps1
  powershell -ExecutionPolicy Bypass -File tests\interface\testar_faixa.ps1 -Somente texto,tabela   # depuração
#>
param([string]$Dist = 'E:\AY\dist\AY ESCREVA', [int]$Limite = 2400, [string]$Somente, [string]$Documento)
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Saida = Join-Path $Raiz 'tests\output\interface'
$Trab = Join-Path $Saida 'trabalho'
New-Item -ItemType Directory -Force $Saida, $Trab | Out-Null
Get-ChildItem $Trab -Force | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue

# Extensão de testes empacotada (.oxt = zip, nomes com "/" — o .NET Framework usaria "\")
$oxt = Join-Path $Raiz 'out\ay-testes-ui.oxt'
if (Test-Path $oxt) { Remove-Item $oxt }
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$origem = Join-Path $PSScriptRoot 'extensao_testes'
$zip = [IO.Compression.ZipFile]::Open($oxt, 'Create')
try {
  foreach ($arq in Get-ChildItem $origem -Recurse -File) {
    $nome = $arq.FullName.Substring($origem.Length + 1) -replace '\\', '/'
    [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $arq.FullName, $nome)
  }
} finally { $zip.Dispose() }

$mapa = Join-Path $Raiz 'out\faixa\mapa.json'
& node.exe (Join-Path $Raiz 'tools\gerar-faixa.mjs') (Join-Path $Raiz 'ui\abas.json') (Join-Path $Dist 'share\config\soffice.cfg\modules\swriter\ui\notebookbar_ayescreva.ui') (Join-Path $Dist 'share\config\images_colibre.zip') '-' $mapa | Out-Null

function Executar-Fase([string]$nome, [string]$documento, [string[]]$passos, [string]$resultado) {
  $perfil = Join-Path $env:TEMP ("ay-faixa-$nome-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
  New-Item -ItemType Directory -Force (Join-Path $perfil 'user') | Out-Null
  @'
<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.Common/Misc"><prop oor:name="UseSystemFileDialog" oor:op="fuse"><value>false</value></prop></item>
<item oor:path="/org.openoffice.Setup/Office"><prop oor:name="ooSetupInstCompleted" oor:op="fuse"><value>true</value></prop></item>
</oor:items>
'@ | Set-Content -Encoding UTF8 (Join-Path $perfil 'user\registrymodifications.xcu')
  $url = 'file:///' + ($perfil -replace '\\', '/')
  & (Join-Path $Dist 'program\unopkg.com') add --suppress-license "-env:UserInstallation=$url" $oxt
  if ($LASTEXITCODE) { throw 'unopkg falhou ao instalar a extensão de testes' }
  Remove-Item $resultado -ErrorAction SilentlyContinue
  $spec = Join-Path $Trab "spec-$nome.json"
  $dados = [ordered]@{ abas = (Join-Path $Raiz 'ui\abas.json'); mapa = $mapa; saida = $resultado; imagem = (Join-Path $Raiz 'out\marca\icone-64.png') }
  if ($passos) { $dados.somente = $passos }
  $dados | ConvertTo-Json | Set-Content -Encoding UTF8 $spec
  $env:AY_TESTE_UI_SPEC = $spec
  $env:AY_SIMULAR_ABERTURA = '1'
  $inicio = Get-Date
  Start-Process (Join-Path $Dist 'program\soffice.exe') -ArgumentList "-env:UserInstallation=$url", '--norestore', '--nologo', "`"$documento`"" | Out-Null
  $fim = (Get-Date).AddSeconds($Limite)
  while ((Get-Date) -lt $fim -and -not (Test-Path $resultado)) { Start-Sleep -Seconds 2 }
  Start-Sleep -Seconds 5
  Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -ge $inicio.AddSeconds(-2) } | ForEach-Object { if (-not $_.WaitForExit(20000)) { $_.Kill() } }
  Remove-Item Env:\AY_TESTE_UI_SPEC, Env:\AY_SIMULAR_ABERTURA
  $quedas = @(Get-WinEvent -FilterHashtable @{ LogName = 'Application'; ProviderName = 'Application Error'; StartTime = $inicio } -ErrorAction SilentlyContinue | Where-Object { $_.Message -like '*soffice*' })
  Remove-Item -Recurse -Force $perfil -ErrorAction SilentlyContinue
  if (-not (Test-Path $resultado)) { throw "Fase ${nome}: sem relatório em $Limite s (quedas registradas: $($quedas.Count))" }
  return $quedas.Count
}

Remove-Item "$env:TEMP\ayescreva-extensao.log" -ErrorAction SilentlyContinue
$odt = Join-Path $Trab 'faixa-teste.odt'
Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') $odt
$docx = Join-Path $Trab 'compatibilidade.docx'
Copy-Item (Join-Path $Raiz 'tests\fixtures\compatibilidade-ooxml.docx') $docx
$resultado = Join-Path $Saida 'faixa-resultado.json'
$passos = if ($Somente) { @($Somente -split ',') } else { $null }

$quedas = Executar-Fase 'f1' $(if ($Documento) { $Documento } else { $odt }) $passos $resultado
if (-not $Somente) {
  $r2 = Join-Path $Saida 'faixa-resultado-fase2.json'
  $quedas += Executar-Fase 'f2' $docx @('docx_inicial') $r2
  # Fase 3: outro DOCX, fechado pela faixa com "Salvar" na pergunta (caminho que não passa pelo botão Salvar)
  $docx3 = Join-Path $Trab 'compatibilidade-fechar.docx'
  Copy-Item (Join-Path $Raiz 'tests\fixtures\compatibilidade-ooxml.docx') $docx3
  $r3 = Join-Path $Saida 'faixa-resultado-fase3.json'
  $quedas += Executar-Fase 'f3' $docx3 @('fechar_docx') $r3
  # Junta os efeitos das fases 2 e 3 no relatório principal
  $a = Get-Content $resultado -Raw -Encoding UTF8 | ConvertFrom-Json
  foreach ($par in @(@('fase2', $r2), @('fase3', $r3))) {
    $b = Get-Content $par[1] -Raw -Encoding UTF8 | ConvertFrom-Json
    $a.efeitos = @($a.efeitos) + @($b.efeitos)
    $a.dialogos = @($a.dialogos) + @($b.dialogos)
    $a.avisos = @($a.avisos) + @($b.avisos)
    $a.erros = @($a.erros) + @($b.erros)
    $a | Add-Member -NotePropertyName $par[0] -NotePropertyValue @{ inicio = $b.inicio; fim = $b.fim } -Force
  }
  $a | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $resultado
}

$r = Get-Content $resultado -Raw -Encoding UTF8 | ConvertFrom-Json
$f = @($r.funcoes.PSObject.Properties | ForEach-Object { $_.Value })
$ef = @($r.efeitos)
"Funções: {0} | presentes: {1} | acionadas: {2} | validadas: {3}" -f $f.Count, @($f | Where-Object presente).Count, @($f | Where-Object acionado).Count, @($f | Where-Object validado).Count
"Efeitos conferidos: {0}/{1} | diálogos abertos e fechados: {2} | avisos: {3} | erros: {4} | quedas: {5}" -f @($ef | Where-Object ok).Count, $ef.Count, @($r.dialogos).Count, @($r.avisos).Count, @($r.erros).Count, $quedas
foreach ($e in $ef | Where-Object { -not $_.ok }) { "  EFEITO NÃO CONFIRMADO: $($e.funcao) — $($e.detalhe)" }
foreach ($e in @($r.erros) | Select-Object -First 5) { "  ERRO: $e" }
if (@($ef | Where-Object { -not $_.ok }).Count -or @($r.erros).Count -or $quedas) { exit 1 }
