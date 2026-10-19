<#
.SYNOPSIS
  Lista a árvore de acessibilidade MSAA da janela do AY ESCREVA (o que um leitor de tela enxerga).
#>
param([string]$App = 'E:\AY\dist\AY ESCREVA\AYEscreva.exe', [string]$Documento, [string]$Saida, [int]$Profundidade = 14, [switch]$ManterAberto)
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $Saida) { $Saida = Join-Path $Raiz 'tests\output\interface\arvore-msaa.txt' }
New-Item -ItemType Directory -Force (Split-Path $Saida) | Out-Null
Add-Type -Path (Join-Path $PSScriptRoot 'Msaa.cs') -ReferencedAssemblies Accessibility
if ($Documento) { Start-Process $App -ArgumentList "`"$Documento`"" } else { Start-Process $App }
$p = $null; $fim = (Get-Date).AddSeconds(60)
while (-not $p -and (Get-Date) -lt $fim) { Start-Sleep -Milliseconds 500; $p = Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*AY ESCREVA*' } | Select-Object -First 1 }
if (-not $p) { throw 'janela não encontrada' }
Start-Sleep -Seconds 5
$nos = [Msaa]::Listar($p.MainWindowHandle, $Profundidade)
$nos | ForEach-Object { '{0}{1} "{2}"{3}{4}' -f ('  ' * $_.Nivel), $_.Papel, $_.Nome, $(if (-not $_.Visivel) { ' (invisível)' } else { '' }), $(if ($_.Atalho.Trim()) { " [$($_.Atalho -replace '[\r\n]+', ' ')]" } else { '' }) } | Set-Content -Encoding UTF8 $Saida
"Elementos: $($nos.Count) -> $Saida"
if (-not $ManterAberto) { [void]$p.CloseMainWindow(); [void]$p.WaitForExit(20000) }
