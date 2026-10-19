<#
.SYNOPSIS
  Roda notebookbar_cenario.py em várias combinações e coleta, para cada queda, o registro "Application Error"
  do Windows (módulo com falha, deslocamento e código da exceção).
#>
param([string[]]$Programas, [switch]$ComInterface)
$ErrorActionPreference = 'Continue'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$script = Join-Path $PSScriptRoot 'notebookbar_cenario.py'
$env:PYTHONIOENCODING = 'utf-8'
$cenarios = @(
  @{ modo = 'Default'; headless = '1'; oculto = '0' },
  @{ modo = 'notebookbar.ui'; headless = '1'; oculto = '1' },
  @{ modo = 'notebookbar.ui'; headless = '1'; oculto = '0' }
)
if ($ComInterface) { $cenarios += @{ modo = 'notebookbar.ui'; headless = '0'; oculto = '0' } }
$resultado = @()
foreach ($prog in $Programas) {
  foreach ($c in $cenarios) {
    $inicio = Get-Date
    $py = Join-Path $prog 'python.exe'
    $saida = & $py $script $c.modo $c.headless $c.oculto 2>&1 | ForEach-Object { "$_" }
    $linha = ($saida | Select-String 'RESULTADO').Line
    Start-Sleep -Seconds 3
    $ev = Get-WinEvent -FilterHashtable @{ LogName = 'Application'; ProviderName = 'Application Error'; StartTime = $inicio } -ErrorAction SilentlyContinue |
      Where-Object { $_.Message -like '*soffice*' } | Select-Object -First 1
    $falha = ''
    if ($ev) {
      $p = $ev.Properties
      # 0 app, 3 módulo, 4 versão do módulo, 6 código da exceção, 7 deslocamento
      $falha = 'módulo {0} {1}, exceção 0x{2:x8}, deslocamento 0x{3:x}' -f $p[3].Value, $p[4].Value, $p[6].Value, $p[7].Value
    }
    $r = [ordered]@{ instalacao = (Split-Path -Leaf (Split-Path -Parent $prog)); modo = $c.modo; headless = $c.headless; oculto = $c.oculto; resultado = $linha; falhaWindows = $falha }
    $resultado += $r
    Write-Host ("{0,-14} {1,-15} headless={2} oculto={3} -> {4} {5}" -f $r.instalacao, $r.modo, $r.headless, $r.oculto, $linha, $falha)
  }
}
$resultado | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Raiz 'tests\output\investigacao-notebookbar.json')
