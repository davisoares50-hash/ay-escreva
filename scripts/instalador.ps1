<#
.SYNOPSIS
  Gera o instalador do AY ESCREVA para Windows x64 (Inno Setup 6) e, opcionalmente, um pacote portátil .zip.

.DESCRIPTION
  Requer a distribuição montada (scripts\montar.ps1) e o compilador do Inno Setup 6 (ISCC.exe).
  Para instalar o Inno Setup (licença gratuita):  winget install --id JRSoftware.InnoSetup -e
  O instalador sai em out\instalador\AYEscreva-<versão>-<canal>-windows11-x64.exe, sem assinatura de código
  (veja docs\COMPILACAO.md, seção "Assinatura").

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\instalador.ps1
  powershell -ExecutionPolicy Bypass -File scripts\instalador.ps1 -Portatil
#>
[CmdletBinding()]
param([switch]$Portatil, [string]$Iscc, [string]$Canal = 'teste')
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent $PSScriptRoot
$Dist = Join-Path $Raiz 'dist\AY ESCREVA'
if (-not (Test-Path (Join-Path $Dist 'AYEscreva.exe'))) { throw "Distribuição não encontrada em $Dist. Rode scripts\montar.ps1 antes." }
# Versão pública em três partes (0.1.0); o lançador usa quatro (0.1.0.0) como versão de arquivo
$Versao = ((Get-Content (Join-Path $Dist 'ay-escreva.json') -Raw -Encoding UTF8 | ConvertFrom-Json).versao -split '\.')[0..2] -join '.'
$SaidaInst = Join-Path $Raiz 'out\instalador'
New-Item -ItemType Directory -Force $SaidaInst | Out-Null

if (-not $Iscc) {
  $candidatos = @(
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe')
  )
  $Iscc = $candidatos | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $Iscc) {
  throw "ISCC.exe (Inno Setup 6) não encontrado. Instale com: winget install --id JRSoftware.InnoSetup -e"
}

Write-Host "Compilando instalador $Versao com $Iscc"
& $Iscc /Qp "/DVersao=$Versao" "/DCanal=$Canal" "/DDist=$Dist" "/DMarca=$(Join-Path $Raiz 'out\marca')" "/DSaida=$SaidaInst" (Join-Path $Raiz 'installer\ayescreva.iss')
if ($LASTEXITCODE) { throw "ISCC falhou ($LASTEXITCODE)" }
$exe = Get-ChildItem $SaidaInst -Filter "AYEscreva-$Versao-$Canal-windows11-x64.exe" | Select-Object -First 1
$hash = (Get-FileHash -Algorithm SHA256 $exe.FullName).Hash.ToLowerInvariant()
"$hash *$($exe.Name)" | Set-Content -Encoding ASCII "$($exe.FullName).sha256"
Write-Host ("Instalador: {0} ({1:N0} MB)  SHA-256 {2}" -f $exe.FullName, ($exe.Length / 1MB), $hash) -ForegroundColor Green

if ($Portatil) {
  $zip = Join-Path $SaidaInst "AYEscreva-$Versao-$Canal-windows11-x64-portatil.zip"
  if (Test-Path $zip) { Remove-Item $zip }
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [IO.Compression.ZipFile]::CreateFromDirectory($Dist, $zip, [IO.Compression.CompressionLevel]::Optimal, $true)
  Write-Host "Pacote portátil: $zip"
}
