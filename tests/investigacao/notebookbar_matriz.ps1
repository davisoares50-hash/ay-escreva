<#
.SYNOPSIS
  Roda notebookbar_cenario.py em várias combinações e coleta, para cada queda, o registro "Application Error"
  do Windows (módulo com falha, deslocamento e código da exceção).
#>
param([string[]]$Programas, [switch]$ComInterface)
$ErrorActionPreference = 'Continue'
$Programas = @($Programas | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$script = Join-Path $PSScriptRoot 'notebookbar_cenario.py'
$env:PYTHONIOENCODING = 'utf-8'
$odt = Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt'
$docx = Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.docx'
$macro = Join-Path $Raiz 'tests\output\seguranca\com-macro.odt'
$cenarios = @(
  @{ modo = "Default"; headless = "1"; oculto = "0"; arquivo = "-"; macro = "3" },
  @{ modo = "notebookbar.ui"; headless = "1"; oculto = "1"; arquivo = "-"; macro = "3" },
  @{ modo = "notebookbar.ui"; headless = "1"; oculto = "0"; arquivo = "-"; macro = "3" },
  @{ modo = "notebookbar.ui"; headless = "1"; oculto = "0"; arquivo = $odt; macro = "3" },
  @{ modo = "notebookbar.ui"; headless = "1"; oculto = "0"; arquivo = $docx; macro = "3" },
  @{ modo = "Default"; headless = "1"; oculto = "0"; arquivo = $macro; macro = "3" },
  @{ modo = "notebookbar.ui"; headless = "1"; oculto = "0"; arquivo = $macro; macro = "3" },
  @{ modo = "notebookbar.ui"; headless = "1"; oculto = "0"; arquivo = $macro; macro = "4" }
)
if ($ComInterface) { $cenarios += @{ modo = 'notebookbar.ui'; headless = '0'; oculto = '0' } }
$resultado = @()
foreach ($prog in $Programas) {
  foreach ($c in $cenarios) {
    $inicio = Get-Date
    $py = Join-Path $prog 'python.exe'
    if ($c.arquivo -ne '-') { Remove-Item (Join-Path (Split-Path $c.arquivo) '.~lock.*') -Force -ErrorAction SilentlyContinue }
    $saida = & $py $script $c.modo $c.headless $c.oculto 0 $c.arquivo $c.macro 2>&1 | ForEach-Object { "$_" }
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
    $r = [ordered]@{ instalacao = (Split-Path -Leaf (Split-Path -Parent $prog)); modo = $c.modo; headless = $c.headless; oculto = $c.oculto; arquivo = (Split-Path -Leaf $c.arquivo); macro = $c.macro; resultado = $linha; falhaWindows = $falha }
    $resultado += $r
    Write-Host ("{0,-11} {1,-15} oculto={2} arq={3,-18} macro={4} -> {5} {6}" -f $r.instalacao, $r.modo, $r.oculto, $r.arquivo, $r.macro, ($linha -replace 'RESULTADO: ','' -replace ' \(.*',''), $falha)
  }
}
$resultado | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Raiz 'tests\output\investigacao-notebookbar.json')
