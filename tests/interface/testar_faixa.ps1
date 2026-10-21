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
    Fase 4: Arquivo › Salvar como DOCX pelo seletor de arquivo do AY — aviso de perdas, DOCX e cópia em ODT.
  O relatório final (tests\output\interface\faixa-resultado.json) junta as quatro fases.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tests\interface\testar_faixa.ps1
  powershell -ExecutionPolicy Bypass -File tests\interface\testar_faixa.ps1 -Somente texto,tabela   # depuração
#>
param([string]$Dist = 'E:\AY\dist\AY ESCREVA', [int]$Limite = 2400, [string]$Somente, [string]$Documento,
      [string]$IAPasta = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'out\ia'), [string]$IAModelo,
      [switch]$SoFase1)
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

function Executar-Fase([string]$nome, [string]$documento, [string[]]$passos, [string]$resultado, [hashtable]$extra = @{}, [string]$RotuloFalha) {
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
  foreach ($k in $extra.Keys) { $dados[$k] = $extra[$k] }
  $dados | ConvertTo-Json | Set-Content -Encoding UTF8 $spec
  $env:AY_TESTE_UI_SPEC = $spec
  $env:AY_SIMULAR_ABERTURA = '1'
  $env:AY_DEPURAR_REVISAO = '1'
  $inicio = Get-Date
  Start-Process (Join-Path $Dist 'program\soffice.exe') -ArgumentList "-env:UserInstallation=$url", '--norestore', '--nologo', "`"$documento`"" | Out-Null
  $fim = (Get-Date).AddSeconds($Limite)
  while ((Get-Date) -lt $fim -and -not (Test-Path $resultado)) {
    Start-Sleep -Seconds 2
    # Funcionamento offline: nenhuma conexão TCP do motor para fora do computador durante a fase
    $pids = @(Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -ge $inicio.AddSeconds(-2) } | ForEach-Object Id)
    if (-not $pids.Count -and ((Get-Date) - $inicio).TotalSeconds -gt 30) { break }    # o motor da fase terminou ou caiu
    foreach ($c in @(Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $pids -contains $_.OwningProcess })) {
      if ($c.RemoteAddress -notin @('127.0.0.1', '::1', '0.0.0.0', '::')) { $script:Externas["$nome $($c.RemoteAddress):$($c.RemotePort)"] = $true }
    }
  }
  Start-Sleep -Seconds 5
  Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -ge $inicio.AddSeconds(-2) } | ForEach-Object { if (-not $_.WaitForExit(20000)) { $_.Kill() } }
  Remove-Item Env:\AY_TESTE_UI_SPEC, Env:\AY_SIMULAR_ABERTURA, Env:\AY_DEPURAR_REVISAO
  $quedas = @(Get-WinEvent -FilterHashtable @{ LogName = 'Application'; ProviderName = 'Application Error'; StartTime = $inicio } -ErrorAction SilentlyContinue | Where-Object { $_.Message -like '*soffice*' })
  Remove-Item -Recurse -Force $perfil -ErrorAction SilentlyContinue
  if (-not (Test-Path $resultado)) {
    # o motor caiu ou travou: a fase vira uma falha registrada e as fases seguintes continuam (antes, o roteiro parava aqui)
    $msg = "Fase ${nome}: sem relatório em $Limite s (quedas registradas: $($quedas.Count))"
    Write-Warning $msg
    [ordered]@{ inicio = $inicio.ToString('s'); fim = (Get-Date).ToString('s'); abas = @(); funcoes = @{}; dialogos = @(); avisos = @()
                efeitos = @([ordered]@{ funcao = $(if ($RotuloFalha) { $RotuloFalha } else { "Fase $nome completa (o motor terminou ou travou antes do fim)" }); ok = $false; detalhe = $msg })
                erros = @($msg) } | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $resultado
    return [math]::Max(1, $quedas.Count)
  }
  return $quedas.Count
}

Remove-Item "$env:TEMP\ayescreva-extensao.log" -ErrorAction SilentlyContinue
$script:Externas = @{}
$odt = Join-Path $Trab 'faixa-teste.odt'
Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') $odt
$docx = Join-Path $Trab 'compatibilidade.docx'
Copy-Item (Join-Path $Raiz 'tests\fixtures\compatibilidade-ooxml.docx') $docx
$resultado = Join-Path $Saida 'faixa-resultado.json'
$passos = if ($Somente) { @($Somente -split ',') } else { $null }
# IA local (fase 9, ou -Somente ia): modelo recomendado do catálogo, salvo indicação
$cat = Get-Content (Join-Path $Raiz 'extensao\ayescreva\dados\ia.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $IAModelo) { $IAModelo = @($cat.modelos | Where-Object { $_.recomendado })[0].id }
$extraIA = @{ ia_pasta = $IAPasta; ia_modelo = $IAModelo }

$quedas = Executar-Fase 'f1' $(if ($Documento) { $Documento } else { $odt }) $passos $resultado $extraIA
if (-not $Somente -and -not $SoFase1) {
  $r2 = Join-Path $Saida 'faixa-resultado-fase2.json'
  $quedas += Executar-Fase 'f2' $docx @('docx_inicial') $r2
  # Fase 3: outro DOCX, fechado pela faixa com "Salvar" na pergunta (caminho que não passa pelo botão Salvar)
  $docx3 = Join-Path $Trab 'compatibilidade-fechar.docx'
  Copy-Item (Join-Path $Raiz 'tests\fixtures\compatibilidade-ooxml.docx') $docx3
  $r3 = Join-Path $Saida 'faixa-resultado-fase3.json'
  $quedas += Executar-Fase 'f3' $docx3 @('fechar_docx') $r3
  # Fase 4: Salvar como DOCX pela faixa (seletor de arquivo do AY + aviso de perdas)
  $odt4 = Join-Path $Trab 'salvar-como.odt'
  Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') $odt4
  $r4 = Join-Path $Saida 'faixa-resultado-fase4.json'
  $quedas += Executar-Fase 'f4' $odt4 @('salvar_como_docx') $r4
  # Fase 5: revisão de texto (entrega A) — digitação real, desfazer, proteções e painel Assistente AY
  $odt5 = Join-Path $Trab 'revisao.odt'
  Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') $odt5
  $r5 = Join-Path $Saida 'faixa-resultado-fase5.json'
  $quedas += Executar-Fase 'f5' $odt5 @('revisao', 'revisao_captura') $r5
  # Fase 6: documento longo (3.000 parágrafos, ~90 mil palavras): verificação em segundo plano e cancelamento
  $txt6 = Join-Path $Trab 'longo.txt'
  $frases = @('O relatório apresenta os resultados do trimestre e as metas para o próximo período.',
    'A equipe revisou os dados com cuidado, mas encontrou palavrass com erro de digitação.',
    'Os números de 12/10/2025 mostram crescimento de 3,5% em relação ao ano anterior.',
    'Segundo a diretora Ana Souza, a ONU publicou o documento “Relatório Mundial” em 2024.')
  $linhas = for ($i = 1; $i -le 3000; $i++) { "$i. $($frases[$i % 4]) $($frases[($i + 1) % 4])" }
  [IO.File]::WriteAllLines($txt6, $linhas, (New-Object Text.UTF8Encoding($true)))
  $r6 = Join-Path $Saida 'faixa-resultado-fase6.json'
  $quedas += Executar-Fase 'f6' $txt6 @('revisao_longo') $r6
  # Fase 7: integridade — DOCX com tabela, imagem, notas, comentário e alterações, corrigido e salvo em DOCX/ODT
  $docx7 = Join-Path $Trab 'integridade-origem.docx'
  Copy-Item (Join-Path $Raiz 'tests\fixtures\compatibilidade-ooxml.docx') $docx7
  $r7 = Join-Path $Saida 'faixa-resultado-fase7.json'
  $quedas += Executar-Fase 'f7' $docx7 @('revisao_integridade') $r7
  # Fase 8: formatar trabalho acadêmico e galeria de modelos (entrega B), sobre o TCC gerado por tests\uno\academico.py
  $fonte8 = Join-Path $Raiz 'tests\output\academico\tcc-word.docx'
  if (-not (Test-Path $fonte8)) { throw 'Rode antes tests\uno\academico.py: ele gera o TCC de teste usado na fase 8.' }
  $docx8 = Join-Path $Trab 'tcc-interface.docx'
  Copy-Item $fonte8 $docx8
  $r8 = Join-Path $Saida 'faixa-resultado-fase8.json'
  $quedas += Executar-Fase 'f8' $docx8 @('academico') $r8
  # Fase 9: IA local (entrega C) — sem modelo e, se o modelo estiver baixado em $IAPasta, o fluxo completo
  $m9 = @($cat.modelos | Where-Object { $_.id -eq $IAModelo })[0]
  $temModelo = $m9 -and (Test-Path (Join-Path $IAPasta "modelos\$($m9.arquivo)")) -and (Test-Path (Join-Path $IAPasta "motor-$($cat.motor.versao)\$($cat.motor.executavel)"))
  if (-not $temModelo) { Write-Warning "Fase 9: modelo $IAModelo não encontrado em $IAPasta — o fluxo com a IA fica BLOQUEADO (só o caminho sem modelo é testado)" }
  $odt9 = Join-Path $Trab 'ia-interface.odt'
  Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') $odt9
  $r9 = Join-Path $Saida 'faixa-resultado-fase9.json'
  $quedas += Executar-Fase 'f9' $odt9 @($(if ($temModelo) { 'ia' } else { 'ia_basico' }), 'escala', 'atualizacoes') $r9 $extraIA
  # Fase 10: entrega D — revisar o documento inteiro, títulos, explicar, conferir referências e consistência (com o modelo)
  $r10 = Join-Path $Saida 'faixa-resultado-fase10.json'
  $fases = @(@('fase2', $r2), @('fase3', $r3), @('fase4', $r4), @('fase5', $r5), @('fase6', $r6), @('fase7', $r7), @('fase8', $r8), @('fase9', $r9))
  if ($temModelo) {
    $odt10 = Join-Path $Trab 'documento-interface.odt'
    Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') $odt10
    $quedas += Executar-Fase 'f10' $odt10 @('ia_documento') $r10 $extraIA
    $fases += ,@('fase10', $r10)
  } else { Write-Warning 'Fase 10 (entrega D com a IA) BLOQUEADA: sem o modelo em $IAPasta' }
  # Fase 11: falha conhecida do motor (Galeria do Fontwork e depois Link, como uma pessoa faria). Enquanto o motor cair,
  # a fase vira FALHA CONHECIDA no relatório; quando uma versão do motor corrigir, ela passa sozinha (RESULTADOS §9)
  $odt11 = Join-Path $Trab 'falha-conhecida.odt'
  Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') $odt11
  $r11 = Join-Path $Saida 'faixa-resultado-fase11.json'
  $quedas += Executar-Fase 'f11' $odt11 @('seq_fontwork_como_pessoa') $r11 $extraIA 'FALHA CONHECIDA (defeito do motor LibreOffice 26.8.1): Galeria do Fontwork e depois Link fecham o aplicativo'
  $fases += ,@('fase11', $r11)
  # Junta os efeitos das fases 2 a 10 no relatório principal
  $a = Get-Content $resultado -Raw -Encoding UTF8 | ConvertFrom-Json
  foreach ($par in $fases) {
    $b = Get-Content $par[1] -Raw -Encoding UTF8 | ConvertFrom-Json
    $a.efeitos = @($a.efeitos) + @($b.efeitos)
    $a.dialogos = @($a.dialogos) + @($b.dialogos)
    $a.avisos = @($a.avisos) + @($b.avisos)
    $a.erros = @($a.erros) + @($b.erros)
    $a | Add-Member -NotePropertyName $par[0] -NotePropertyValue @{ inicio = $b.inicio; fim = $b.fim } -Force
    if ($b.medidas) { $a | Add-Member -NotePropertyName ('medidas_' + $par[0]) -NotePropertyValue $b.medidas -Force }
  }
  $a | Add-Member -NotePropertyName conexoes_externas -NotePropertyValue @($script:Externas.Keys) -Force
  $a | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $resultado
}

$r = Get-Content $resultado -Raw -Encoding UTF8 | ConvertFrom-Json
$f = @($r.funcoes.PSObject.Properties | ForEach-Object { $_.Value })
$ef = @($r.efeitos)
"Funções: {0} | presentes: {1} | acionadas: {2} | validadas: {3}" -f $f.Count, @($f | Where-Object presente).Count, @($f | Where-Object acionado).Count, @($f | Where-Object validado).Count
"Efeitos conferidos: {0}/{1} | diálogos abertos e fechados: {2} | avisos: {3} | erros: {4} | quedas: {5}" -f @($ef | Where-Object ok).Count, $ef.Count, @($r.dialogos).Count, @($r.avisos).Count, @($r.erros).Count, $quedas
foreach ($e in $ef | Where-Object { -not $_.ok }) { "  EFEITO NÃO CONFIRMADO: $($e.funcao) — $($e.detalhe)" }
foreach ($e in @($r.erros) | Select-Object -First 5) { "  ERRO: $e" }
"Conexões de rede para fora do computador durante os testes: {0}{1}" -f $script:Externas.Count, $(if ($script:Externas.Count) { " (" + (@($script:Externas.Keys) -join ", ") + ")" } else { "" })
if (@($ef | Where-Object { -not $_.ok }).Count -or @($r.erros).Count -or $quedas -or $script:Externas.Count) { exit 1 }
