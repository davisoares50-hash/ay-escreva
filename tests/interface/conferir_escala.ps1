<#
  Confere os diálogos e painéis do AY na escala de tela que estiver em uso (100 %, 125 %, 150 %, 200 %).

  Como usar para 150 % e 200 %:
    1. Configurações do Windows › Sistema › Tela › Escala: escolha 150 % (ou 200 %).
    2. Rode:  powershell -ExecutionPolicy Bypass -File tests\interface\conferir_escala.ps1
    3. Volte a escala para a de antes.
  O resultado fica em tests\output\interface\escala-<escala>.json e as capturas em
  tests\output\interface\escala-<escala>-<diálogo>.png.

  O teste não muda a escala do Windows (é uma configuração do sistema): ele confere a escala em uso.
  SPDX-License-Identifier: MPL-2.0
#>
param([string]$Dist = 'E:\AY\dist\AY ESCREVA')
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Add-Type -Namespace AY -Name Dpi -MemberDefinition '[DllImport("user32.dll")] public static extern uint GetDpiForSystem();'
$escala = [math]::Round(100 * [AY.Dpi]::GetDpiForSystem() / 96)
Write-Host "Escala da tela em uso: $escala %"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'testar_faixa.ps1') -Dist $Dist -Somente escala -Limite 900
$r = Get-Content (Join-Path $Raiz 'tests\output\interface\faixa-resultado.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$destino = Join-Path $Raiz "tests\output\interface\escala-$escala.json"
$r | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $destino
$ok = @($r.efeitos | Where-Object ok).Count
Write-Host "`nEscala $escala %: $ok/$(@($r.efeitos).Count) conferências aprovadas (detalhes em $destino)"
foreach ($e in @($r.efeitos | Where-Object { -not $_.ok })) { Write-Host "  PROBLEMA: $($e.funcao) — $($e.detalhe)" -ForegroundColor Red }
