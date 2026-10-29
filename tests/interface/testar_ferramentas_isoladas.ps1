<#
.SYNOPSIS
  Ferramentas da faixa com diálogo, cada uma num aplicativo novo (fase 12b da bateria).
.DESCRIPTION
  Alguns diálogos do motor derrubam o aplicativo quando o teste mexe neles por entrada simulada (RESULTADOS §9).
  Rodando cada ferramenta num aplicativo próprio, uma queda fica registrada só para aquela ferramenta (como falha,
  com a contagem de quedas), e as outras continuam sendo testadas. Para cada comando, roda
  testar_faixa.ps1 -Somente ferramentas com AY_FERRAMENTAS=<comando> e junta os resultados em
  tests\output\interface\ferramentas-isoladas.json.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tests\interface\testar_ferramentas_isoladas.ps1
  powershell -ExecutionPolicy Bypass -File tests\interface\testar_ferramentas_isoladas.ps1 -Comandos .uno:PageDialog -Vezes 2
#>
param([string[]]$Comandos, [int]$Vezes = 1, [int]$Limite = 900, [string]$Dist = 'E:\AY\dist\AY ESCREVA')
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if ($Comandos -and $Comandos.Count -eq 1 -and $Comandos[0] -like '*,*') { $Comandos = @($Comandos[0] -split ',') }   # -File junta a lista
if (-not $Comandos) {
  $Comandos = @(Get-Content (Join-Path $PSScriptRoot 'ferramentas-com-dialogo.txt') -Encoding UTF8 | Where-Object { $_ -and -not $_.StartsWith('#') })
}
$Saida = Join-Path $Raiz 'tests\output\interface'
$todos = [ordered]@{}
$execucoes = @()
foreach ($cmd in $Comandos) {
  for ($v = 1; $v -le $Vezes; $v++) {
    $env:AY_FERRAMENTAS = $cmd
    $inicio = Get-Date
    # avisos do Python na saída de erro não podem interromper o roteiro (no PowerShell 5.1 viram erro com 'Stop')
    $ErrorActionPreference = 'Continue'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'testar_faixa.ps1') -Dist $Dist -Somente ferramentas -Limite $Limite *> $null
    $ErrorActionPreference = 'Stop'
    Remove-Item Env:\AY_FERRAMENTAS
    $r = Get-Content (Join-Path $Saida 'faixa-resultado.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $semRelatorio = -not $r.ferramentas
    $motivo = if ($semRelatorio) { "$(@($r.erros)[0])" } else { '' }
    # queda do motor (código C0000409) × tempo esgotado (o teste esperou o computador ficar ocioso além do limite)
    $caiu = $semRelatorio -and $motivo -like '*queda do motor*'
    $execucoes += [ordered]@{ comando = $cmd; vez = $v; inicio = $inicio.ToString('s'); queda = $caiu; sem_relatorio = $semRelatorio; motivo = $motivo }
    if ($semRelatorio) {
      Write-Host "$cmd (vez $v): $motivo"
      continue
    }
    foreach ($p in $r.ferramentas.PSObject.Properties) {
      if (-not $todos.Contains($p.Name) -or -not $todos[$p.Name].validado) { $todos[$p.Name] = $p.Value }
      Write-Host ("{0} (vez {1}): {2}" -f $p.Name, $v, $(if ($p.Value.validado) { 'OK — ' } else { 'FALHA — ' }) + $p.Value.resumo)
    }
  }
}
# comandos que caíram em todas as vezes: registrados como falha, com o motivo
foreach ($cmd in $Comandos) {
  $exs = @($execucoes | Where-Object { $_.comando -eq $cmd })
  $quedas = @($exs | Where-Object { $_.queda }).Count
  $semRel = @($exs | Where-Object { $_.sem_relatorio }).Count
  if ($semRel -and -not @($todos.Values | Where-Object { $_.comando -eq $cmd }).Count) {
    $texto = if ($quedas) { "o motor caiu durante o teste em $quedas de $($exs.Count) execuções (entrada simulada nos controles do diálogo; RESULTADOS §9)" }
             else { "sem resultado: $(@($exs | Where-Object { $_.sem_relatorio })[0].motivo)" }
    $todos["(queda) $cmd"] = [ordered]@{ comando = $cmd; validado = $false; efeito = $false; queda = [bool]$quedas; resumo = $texto }
  }
}
[ordered]@{ data = (Get-Date).ToString('s'); execucoes = $execucoes; ferramentas = $todos } | ConvertTo-Json -Depth 6 |
  Set-Content -Encoding UTF8 (Join-Path $Saida 'ferramentas-isoladas.json')
$ok = @($todos.Values | Where-Object { $_.validado }).Count
Write-Host "`nFerramentas isoladas: $ok/$($todos.Count) validadas; quedas: $(@($execucoes | Where-Object { $_.queda }).Count) em $($execucoes.Count) execuções"
