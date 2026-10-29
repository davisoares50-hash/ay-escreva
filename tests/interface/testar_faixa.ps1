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
      [switch]$SoFase1, [switch]$ModoClassico)
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
  if ($ModoClassico) {
    # diagnóstico: barra de ferramentas clássica do motor em vez da faixa por abas
    $xcu = Join-Path $perfil 'user\registrymodifications.xcu'
    $item = '<item oor:path="/org.openoffice.Office.UI.ToolbarMode"><prop oor:name="ActiveWriter" oor:op="fuse"><value>Default</value></prop></item>'
    Set-Content -Encoding UTF8 $xcu ((Get-Content $xcu -Raw).Replace('</oor:items>', $item + [Environment]::NewLine + '</oor:items>'))
  }
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
  $processos = @{}       # cada processo do motor da fase, com o identificador aberto para ler o código de saída depois
  while ((Get-Date) -lt $fim -and -not (Test-Path $resultado)) {
    Start-Sleep -Seconds 2
    foreach ($p in @(Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -ge $inicio.AddSeconds(-2) })) {
      if (-not $processos.ContainsKey($p.Id)) { try { $null = $p.Handle; $processos[$p.Id] = $p } catch {} }
    }
    # Funcionamento offline: nenhuma conexão TCP do motor para fora do computador durante a fase
    $pids = @(Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -ge $inicio.AddSeconds(-2) } | ForEach-Object Id)
    if (-not $pids.Count -and ((Get-Date) - $inicio).TotalSeconds -gt 30) { break }    # o motor da fase terminou ou caiu
    foreach ($c in @(Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $pids -contains $_.OwningProcess })) {
      if ($c.RemoteAddress -notin @('127.0.0.1', '::1', '0.0.0.0', '::')) { $script:Externas["$nome $($c.RemoteAddress):$($c.RemotePort)"] = $true }
    }
  }
  Start-Sleep -Seconds 5
  $encerrados = @()
  Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -ge $inicio.AddSeconds(-2) } | ForEach-Object {
    if (-not $_.WaitForExit(20000)) { $encerrados += $_.Id; $_.Kill() } }
  Remove-Item Env:\AY_TESTE_UI_SPEC, Env:\AY_SIMULAR_ABERTURA, Env:\AY_DEPURAR_REVISAO
  # Queda = processo do motor que terminou com 0xC0000409 (encerramento forçado). O log de eventos do Windows não basta:
  # ele deixa de registrar quedas repetidas com a mesma assinatura.
  $codigos = @(foreach ($p in $processos.Values) { try { $p.WaitForExit(5000) | Out-Null; '{0:X8}' -f $p.ExitCode } catch {} })
  $quedasCodigo = @($codigos | Where-Object { $_ -eq 'C0000409' }).Count
  $eventos = @(Get-WinEvent -FilterHashtable @{ LogName = 'Application'; ProviderName = 'Application Error'; StartTime = $inicio } -ErrorAction SilentlyContinue | Where-Object { $_.Message -like '*soffice*' })
  $nQuedas = [math]::Max($quedasCodigo, $eventos.Count)
  Remove-Item -Recurse -Force $perfil -ErrorAction SilentlyContinue
  if (-not (Test-Path $resultado)) {
    # o motor caiu ou travou: a fase vira uma falha registrada e as fases seguintes continuam (antes, o roteiro parava aqui)
    $como = if ($nQuedas) { "queda do motor (códigos de saída: $($codigos -join ', '))" }
            elseif ($encerrados.Count) { "tempo esgotado: o teste não terminou em $Limite s e o motor foi encerrado pelo roteiro" }
            else { "o motor terminou sem relatório (códigos de saída: $($codigos -join ', '))" }
    $msg = "Fase ${nome}: sem relatório em $Limite s — $como"
    Write-Warning $msg
    [ordered]@{ inicio = $inicio.ToString('s'); fim = (Get-Date).ToString('s'); abas = @(); funcoes = @{}; dialogos = @(); avisos = @()
                efeitos = @([ordered]@{ funcao = $(if ($RotuloFalha) { $RotuloFalha } else { "Fase $nome completa (o motor terminou ou travou antes do fim)" }); ok = $false; detalhe = $msg })
                erros = @($msg) } | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $resultado
    return $nQuedas          # tempo esgotado não conta como queda (a fase já fica registrada como falha)
  }
  return $nQuedas
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
  # Fase 11: Galeria do Fontwork e depois Link pela faixa, fechando cada janela com Esc do teclado de verdade (teclas do
  # Windows, como uma pessoa). Com teclas simuladas pelo motor (robô ou UITest) o motor cai às vezes, até sem o Fontwork;
  # com o teclado real a sequência não reproduziu a queda (RESULTADOS §9). Se cair, a fase registra a queda.
  $odt11 = Join-Path $Trab 'falha-conhecida.odt'
  Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') $odt11
  $r11 = Join-Path $Saida 'faixa-resultado-fase11.json'
  $quedas += Executar-Fase 'f11' $odt11 @('diag_real_faixa', 'teclado') $r11 $extraIA 'QUEDA do motor: Galeria do Fontwork e depois Link, com teclado real (RESULTADOS §9)'
  $fases += ,@('fase11', $r11)
  # Fase 12: ferramentas da faixa pelo efeito no documento, com desfazer/refazer e salvar/reabrir em ODT e DOCX
  $odt12 = Join-Path $Trab 'ferramentas.odt'
  Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') $odt12
  $r12 = Join-Path $Saida 'faixa-resultado-fase12.json'
  $isoladas = @(Get-Content (Join-Path $PSScriptRoot 'ferramentas-com-dialogo.txt') -Encoding UTF8 | Where-Object { $_ -and -not $_.StartsWith('#') })
  $env:AY_FERRAMENTAS_EXCETO = $isoladas -join ','
  $quedas += Executar-Fase 'f12' $odt12 @('ferramentas') $r12
  Remove-Item Env:\AY_FERRAMENTAS_EXCETO
  $fases += ,@('fase12', $r12)
  # Fase 12b: ferramentas com diálogo, cada uma num aplicativo próprio (uma queda fica só naquela ferramenta)
  $resultadoPrincipal = Get-Content $resultado -Raw -Encoding UTF8          # a 12b reescreve faixa-resultado.json a cada ferramenta
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'testar_ferramentas_isoladas.ps1') -Dist $Dist
  Set-Content -Encoding UTF8 $resultado $resultadoPrincipal
  $iso = Get-Content (Join-Path $Saida 'ferramentas-isoladas.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  $quedas += @($iso.execucoes | Where-Object { $_.queda }).Count
  $efeitos12b = @(foreach ($p in $iso.ferramentas.PSObject.Properties) {
    [ordered]@{ funcao = "$($p.Name) (efeito real, aplicativo isolado)"; ok = [bool]$p.Value.validado; detalhe = $p.Value.resumo } })
  $r12b = Join-Path $Saida 'faixa-resultado-fase12b.json'
  [ordered]@{ inicio = $iso.data; fim = $iso.data; efeitos = $efeitos12b; dialogos = @(); avisos = @(); erros = @()
              ferramentas = $iso.ferramentas; funcoes = [ordered]@{} } | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $r12b
  $fases += ,@('fase12b', $r12b)
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
    # fase 12: o resultado por ferramenta (efeito, desfazer, ODT, DOCX) e a validação entram na matriz
    if ($b.ferramentas) {
      if (-not $a.ferramentas) { $a | Add-Member -NotePropertyName ferramentas -NotePropertyValue ([pscustomobject]@{}) -Force }
      foreach ($p in $b.ferramentas.PSObject.Properties) {
        $a.ferramentas | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value -Force
        # a validação de cada ferramenta entra na lista de funções (base da matriz)
        if ($p.Name -like '(queda)*') { continue }
        $alvo = $a.funcoes.PSObject.Properties[$p.Name]
        if (-not $alvo) {
          $a.funcoes | Add-Member -NotePropertyName $p.Name -NotePropertyValue ([pscustomobject]@{ presente = $false; acionado = $false; validado = $false; detalhes = @() })
          $alvo = $a.funcoes.PSObject.Properties[$p.Name]
        }
        if ($p.Value.disparado -eq $p.Value.comando) { $alvo.Value.acionado = $true }
        if ($p.Value.validado) {
          $alvo.Value.validado = $true
          $alvo.Value.detalhes = @(@($alvo.Value.detalhes) + @($p.Value.resumo) | Select-Object -Unique)
        }
      }
    }
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
