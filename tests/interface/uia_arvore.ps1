<#
.SYNOPSIS
  Lista o que a UI Automation do Windows (a mesma camada usada por leitores de tela) enxerga na janela do
  AY ESCREVA: abas, grupos e botões da faixa de opções, com nome, tipo e estado.
.DESCRIPTION
  O motor só ativa a ponte de acessibilidade quando detecta tecnologia assistiva; para testes automatizados a
  variável SAL_FORCE_IACCESSIBLE2=1 força a ativação (documentado em docs.libreoffice.org/winaccessibility).
#>
param([string]$App = 'E:\AY\dist\AY ESCREVA\AYEscreva.exe', [string]$Documento, [string]$Saida, [int]$Profundidade = 12, [switch]$ManterAberto)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $Saida) { $Saida = Join-Path $Raiz 'tests\output\interface\arvore.txt' }
New-Item -ItemType Directory -Force (Split-Path $Saida) | Out-Null
$env:SAL_FORCE_IACCESSIBLE2 = '1'
$args = @(); if ($Documento) { $args += "`"$Documento`"" }
if ($args) { Start-Process $App -ArgumentList $args } else { Start-Process $App }
$raizUia = [Windows.Automation.AutomationElement]::RootElement
$cond = New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ClassNameProperty, 'SALFRAME')
$jan = $null; $fim = (Get-Date).AddSeconds(60)
while (-not $jan -and (Get-Date) -lt $fim) {
  Start-Sleep -Milliseconds 500
  $jan = $raizUia.FindAll([Windows.Automation.TreeScope]::Children, $cond) | Where-Object { $_.Current.Name -like '*AY ESCREVA*' } | Select-Object -First 1
}
if (-not $jan) { throw 'janela não encontrada' }
Start-Sleep -Seconds 4
$linhas = New-Object Collections.Generic.List[string]
$walker = [Windows.Automation.TreeWalker]::RawViewWalker
# Primeira consulta desperta a ponte de acessibilidade do motor; aguarda e lê de novo
[void]$jan.FindAll([Windows.Automation.TreeScope]::Descendants, [Windows.Automation.Condition]::TrueCondition).Count
Start-Sleep -Seconds 3
function Visitar($el, [int]$nivel) {
  if ($nivel -gt $Profundidade) { return }
  $c = $el.Current
  $tipo = $c.ControlType.ProgrammaticName -replace 'ControlType\.', ''
  $linhas.Add(('{0}{1} "{2}" [{3}] id={4}' -f ('  ' * $nivel), $tipo, $c.Name, $c.ClassName, $c.AutomationId))
  $f = $walker.GetFirstChild($el)
  while ($f) { Visitar $f ($nivel + 1); $f = $walker.GetNextSibling($f) }
}
Visitar $jan 0
$linhas | Set-Content -Encoding UTF8 $Saida
"Elementos: $($linhas.Count) -> $Saida"
if (-not $ManterAberto) {
  $p = Get-Process soffice.bin | Where-Object { $_.MainWindowHandle -eq $jan.Current.NativeWindowHandle } | Select-Object -First 1
  if ($p) { [void]$p.CloseMainWindow(); [void]$p.WaitForExit(20000) }
}
