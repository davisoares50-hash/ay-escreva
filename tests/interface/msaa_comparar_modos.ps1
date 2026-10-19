<#
.SYNOPSIS
  Compara o que a acessibilidade (MSAA) expõe com a barra clássica e com a faixa por abas,
  usando perfis descartáveis, antes e depois de levar o foco do teclado à faixa (F6).
#>
param([string]$Programa = 'E:\AY\dist\AY ESCREVA\program', [string]$Documento = 'E:\AY\tests\output\etapa1\teste-etapa1.odt')
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Add-Type -Path (Join-Path $PSScriptRoot 'Msaa.cs') -ReferencedAssemblies Accessibility
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class Foco { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); }
'@
$saida = Join-Path $Raiz 'tests\output\interface'
foreach ($modo in 'Default', 'notebookbar.ui') {
  $perfil = Join-Path $env:TEMP ("ay-a11y-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
  New-Item -ItemType Directory -Force (Join-Path $perfil 'user') | Out-Null
  @"
<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.UI.ToolbarMode/Applications/org.openoffice.Office.UI.ToolbarMode:Application['Writer']"><prop oor:name="Active" oor:op="fuse"><value>$modo</value></prop></item>
<item oor:path="/org.openoffice.Setup/Office"><prop oor:name="ooSetupInstCompleted" oor:op="fuse"><value>true</value></prop></item>
</oor:items>
"@ | Set-Content -Encoding UTF8 (Join-Path $perfil 'user\registrymodifications.xcu')
  $url = 'file:///' + ($perfil -replace '\\', '/')
  $p = Start-Process (Join-Path $Programa 'soffice.exe') -ArgumentList "-env:UserInstallation=$url", '--norestore', '--nologo', "`"$Documento`"" -PassThru
  # Como um leitor de tela em execução: consulta a acessibilidade da primeira janela do motor assim que ela
  # existir (tela de abertura inclusive), para que a ponte nasça antes de barras e faixa serem montadas.
  $proc = $null; $fim = (Get-Date).AddSeconds(60)
  while (-not $proc -and (Get-Date) -lt $fim) {
    Start-Sleep -Milliseconds 100
    foreach ($q in Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }) {
      try { [void][Msaa]::Raiz($q.MainWindowHandle) } catch {}
      if ($q.MainWindowTitle -like '*teste-etapa1*') { $proc = $q }
    }
  }
  Start-Sleep -Seconds 5
  $h = $proc.MainWindowHandle
  $antes = [Msaa]::Listar($h, 16)
  [void][Foco]::SetForegroundWindow($h); Start-Sleep -Milliseconds 500
  try { [Windows.Forms.SendKeys]::SendWait('{F6}') } catch { Write-Host "  (F6 não enviado: $($_.Exception.Message))" }; Start-Sleep -Seconds 2
  $depois = [Msaa]::Listar($h, 16)
  $fmt = { param($n) '{0}{1} "{2}"{3}' -f ('  ' * $n.Nivel), $n.Papel, $n.Nome, $(if (-not $n.Visivel) { ' (invisível)' } else { '' }) }
  ($antes | ForEach-Object { & $fmt $_ }) | Set-Content -Encoding UTF8 (Join-Path $saida "msaa-$($modo -replace '\.ui','')-antes.txt")
  ($depois | ForEach-Object { & $fmt $_ }) | Set-Content -Encoding UTF8 (Join-Path $saida "msaa-$($modo -replace '\.ui','')-depois-F6.txt")
  $vis = { param($l) @($l | Where-Object { $_.Visivel -and $_.Papel -notmatch 'menu|separador' }) }
  $botoes = { param($l) @($l | Where-Object { $_.Visivel -and $_.Papel -match 'botão|guia|lista de guias|caixa de combinação|página' }) }
  "{0,-15} visíveis antes={1,4} depois(F6)={2,4} | botões/abas antes={3,4} depois={4,4}" -f $modo, (& $vis $antes).Count, (& $vis $depois).Count, (& $botoes $antes).Count, (& $botoes $depois).Count
  [void]$proc.CloseMainWindow(); [void]$proc.WaitForExit(20000)
  Remove-Item -Recurse -Force $perfil -ErrorAction SilentlyContinue
}
