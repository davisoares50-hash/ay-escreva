<#
.SYNOPSIS
  Gera uma captura de cada aba da faixa AY (inspeção visual e imagens para o site).
.DESCRIPTION
  Para cada aba, gera uma variante de inspeção da faixa em que aquela aba abre já selecionada,
  abre o AY com perfil descartável, captura a janela e fecha. Ao final restaura a faixa normal.
#>
param([string]$Dist = 'E:\AY\dist\AY ESCREVA', [string]$Documento = 'E:\AY\tests\output\etapa1\teste-etapa1.odt', [string]$Saida = 'E:\AY\tests\output\interface\abas', [string[]]$Abas)
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Abas = @($Abas | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$json = Get-Content (Join-Path $Raiz 'ui\abas.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $Abas) { $Abas = @($json.abas.id) + @($json.contextuais.id) }
$ui = Join-Path $Dist 'share\config\soffice.cfg\modules\swriter\ui\notebookbar_ayescreva.ui'
$tema = Join-Path $Dist 'share\config\images_colibre.zip'
$gerador = Join-Path $Raiz 'tools\gerar-faixa.mjs'
New-Item -ItemType Directory -Force $Saida | Out-Null
$n = 0
foreach ($id in $Abas) {
  $n++
  & node.exe $gerador (Join-Path $Raiz 'ui\abas.json') $ui $tema $id | Out-Null
  $png = Join-Path $Saida ('{0:D2}-{1}.png' -f $n, $id)
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'abrir_perfil_teste.ps1') -Programa (Join-Path $Dist 'program') -Documento $Documento -Saida $png | Select-Object -Last 1
}
& node.exe $gerador (Join-Path $Raiz 'ui\abas.json') $ui $tema | Select-Object -First 1
