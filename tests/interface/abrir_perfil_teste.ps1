<#
.SYNOPSIS
  Abre o AY ESCREVA (distribuição em dist\) com um perfil descartável e captura a janela.
  Não usa nem altera o perfil real do usuário.
#>
param([string]$Programa = 'E:\AY\dist\AY ESCREVA\program', [string]$Documento, [string]$Saida = 'E:\AY\tests\output\interface\janela.png', [int]$Esperar = 8, [switch]$ManterAberto)
$ErrorActionPreference = 'Stop'
$perfil = Join-Path $env:TEMP ('ay-ui-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
$url = 'file:///' + ($perfil -replace '\\', '/')
$args = @("-env:UserInstallation=$url", '--norestore', '--nologo')
if ($Documento) { $args += "`"$Documento`"" } else { $args += '--writer' }
Start-Process (Join-Path $Programa 'soffice.exe') -ArgumentList $args | Out-Null
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path (Split-Path -Parent $PSScriptRoot) 'captura_janela.ps1') -Saida $Saida -Esperar 60
Start-Sleep -Seconds 1
if (-not $ManterAberto) {
  Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*AY ESCREVA*' } | ForEach-Object { [void]$_.CloseMainWindow(); [void]$_.WaitForExit(20000) }
  Remove-Item -Recurse -Force $perfil -ErrorAction SilentlyContinue
}
