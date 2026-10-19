<#
.SYNOPSIS
  Testa o instalador do AY ESCREVA de ponta a ponta: instalar, abrir, criar/salvar/reabrir, desinstalar.

.DESCRIPTION
  - Fotografa antes e depois o estado de outras instalações do LibreOffice (perfil, registro, associações),
    para comprovar que nada delas é alterado.
  - Instala por usuário em modo silencioso (sem administrador), confere arquivos, atalho, registro de
    desinstalação e a entrada "Abrir com".
  - Abre o aplicativo instalado pela interface (lançador) e confere a janela.
  - Roda o teste de aceite (criar documento de várias páginas, formatar, tabela, imagem, salvar, fechar,
    reabrir, PDF) usando o motor INSTALADO.
  - Desinstala em modo silencioso e confere que programa, atalho e registros sumiram; o perfil do usuário
    (%APPDATA%\AYEscreva) é preservado de propósito.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tests\instalacao\testar_instalacao.ps1 -Instalador out\instalador\AYEscreva-0.1.0-teste-windows11-x64.exe
#>
param([Parameter(Mandatory)] [string]$Instalador, [string]$Saida)
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $Saida) { $Saida = Join-Path $Raiz 'tests\output\instalacao' }
New-Item -ItemType Directory -Force $Saida | Out-Null
$Instalador = (Resolve-Path $Instalador).Path
$AppId = '{4555F5FD-202B-4A8C-A427-E4CB4FDA6816}_is1'
$ChaveDesinst = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppId"
$PastaApp = Join-Path $env:LOCALAPPDATA 'Programs\AY ESCREVA'
$Atalho = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\AY ESCREVA.lnk'
$itens = New-Object System.Collections.ArrayList
function Verificar([string]$descricao, [bool]$ok, [string]$detalhe = '') {
  [void]$itens.Add([ordered]@{ ok = $ok; verificacao = $descricao; detalhe = $detalhe })
  $m = if ($ok) { 'OK  ' } else { 'FALHA' }
  Write-Host ("[{0}] {1}{2}" -f $m, $descricao, $(if ($detalhe) { " — $detalhe" } else { '' })) -ForegroundColor $(if ($ok) { 'Green' } else { 'Red' })
}

function Foto-LibreOffice {
  $f = [ordered]@{}
  foreach ($p in @("$env:APPDATA\LibreOffice", "$env:ProgramFiles\LibreOffice", "${env:ProgramFiles(x86)}\LibreOffice")) {
    if (Test-Path $p) {
      $arqs = Get-ChildItem $p -Recurse -File -ErrorAction SilentlyContinue
      $f[$p] = '{0} arquivos, {1} bytes, última alteração {2}' -f $arqs.Count, ($arqs | Measure-Object Length -Sum).Sum, (($arqs | Sort-Object LastWriteTime | Select-Object -Last 1).LastWriteTime)
    } else { $f[$p] = 'ausente' }
  }
  foreach ($k in @('HKCU:\Software\LibreOffice', 'HKLM:\SOFTWARE\LibreOffice')) {
    $f[$k] = if (Test-Path $k) { (Get-ChildItem $k -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count.ToString() + ' subchaves' } else { 'ausente' }
  }
  foreach ($ext in '.docx', '.odt', '.doc', '.rtf') {
    $padrao = (Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\$ext\UserChoice" -ErrorAction SilentlyContinue).ProgId
    $f["padrao$ext"] = if ($padrao) { $padrao } else { '(sem escolha do usuário)' }
    $ow = Get-Item "HKCU:\Software\Classes\$ext\OpenWithProgids" -ErrorAction SilentlyContinue
    $f["abrirCom$ext"] = if ($ow) { ($ow.GetValueNames() | Where-Object { $_ -ne 'AYEscreva.Documento' } | Sort-Object) -join ',' } else { '' }
  }
  $f
}

# ---------------------------------------------------------------------------
Write-Host "Instalador: $Instalador"
$hash = (Get-FileHash -Algorithm SHA256 $Instalador).Hash.ToLowerInvariant()
$arqHash = "$Instalador.sha256"
if (Test-Path $arqHash) {
  $esperado = ((Get-Content $arqHash -Raw).Trim() -split '\s+')[0]
  Verificar 'SHA-256 do instalador confere com o arquivo .sha256' ($hash -eq $esperado) $hash
}
$sig = Get-AuthenticodeSignature $Instalador
Verificar 'assinatura digital do instalador (esperado: sem assinatura nesta versão)' ($sig.Status -eq 'NotSigned') "$($sig.Status)"
if (Test-Path $ChaveDesinst) { throw 'O AY ESCREVA já está instalado para este usuário; desinstale antes do teste.' }

$antes = Foto-LibreOffice
$antes | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Saida 'libreoffice-antes.json')

# ---------------------------------------------------------------------------
Write-Host "`n== Instalação silenciosa por usuário"
$log = Join-Path $Saida 'instalacao.log'
$sw = [Diagnostics.Stopwatch]::StartNew()
$p = Start-Process $Instalador -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER', '/TASKS="associar"', "/LOG=`"$log`"" -Wait -PassThru
Verificar 'instalador terminou com código 0' ($p.ExitCode -eq 0) "código $($p.ExitCode), $([math]::Round($sw.Elapsed.TotalSeconds)) s"
Verificar 'programa instalado em %LOCALAPPDATA%\Programs\AY ESCREVA' (Test-Path (Join-Path $PastaApp 'AYEscreva.exe'))
Verificar 'motor instalado' (Test-Path (Join-Path $PastaApp 'program\soffice.exe'))
$tam = (Get-ChildItem $PastaApp -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
Verificar 'tamanho instalado' ($tam -gt 500) ('{0:N0} MB' -f $tam)
Verificar 'atalho no menu Iniciar' (Test-Path $Atalho)
$reg = Get-ItemProperty $ChaveDesinst -ErrorAction SilentlyContinue
Verificar 'registro de desinstalação' ($null -ne $reg) "$($reg.DisplayName) | versão $($reg.DisplayVersion)"
$ow = Get-Item 'HKCU:\Software\Classes\.docx\OpenWithProgids' -ErrorAction SilentlyContinue
Verificar '"Abrir com" oferece o AY ESCREVA para .docx' ($ow -and ($ow.GetValueNames() -contains 'AYEscreva.Documento'))

# ---------------------------------------------------------------------------
Write-Host "`n== Abertura pela interface"
Start-Process (Join-Path $PastaApp 'AYEscreva.exe')
$janela = $null
$fim = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $fim -and -not $janela) {
  Start-Sleep -Milliseconds 500
  $janela = Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*AY ESCREVA*' -and $_.Path -like "$PastaApp*" } | Select-Object -First 1
}
Verificar 'janela principal aberta pelo lançador instalado' ($null -ne $janela) $(if ($janela) { $janela.MainWindowTitle } else { 'não encontrada em 90 s' })
if ($janela) {
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Raiz 'tests\captura_janela.ps1') -Saida (Join-Path $Saida 'janela-instalado.png') -Esperar 10 | Out-Null
  Start-Sleep -Seconds 2
  [void]$janela.CloseMainWindow()
  if (-not $janela.WaitForExit(30000)) { $janela.Kill() }
}

# ---------------------------------------------------------------------------
Write-Host "`n== Criar, salvar, reabrir e exportar com o motor instalado"
$env:PYTHONIOENCODING = 'utf-8'
$pyInst = Join-Path $PastaApp 'program\python.exe'
$saidaAceite = & $pyInst (Join-Path $Raiz 'tests\uno\aceite_etapa1.py') 2>&1 | ForEach-Object { "$_" }
$saidaAceite | Set-Content -Encoding UTF8 (Join-Path $Saida 'aceite-motor-instalado.txt')
$resumo = $saidaAceite | Select-String 'verificações aprovadas' | Select-Object -Last 1
Verificar 'aceite (criar, formatar, tabela, imagem, salvar, fechar, reabrir, PDF) com o motor instalado' ($LASTEXITCODE -eq 0) "$resumo"

# ---------------------------------------------------------------------------
Write-Host "`n== Desinstalação silenciosa"
$desinst = Join-Path $PastaApp 'unins000.exe'
Start-Process $desinst -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -Wait
$fim = (Get-Date).AddSeconds(180)
while ((Get-Date) -lt $fim -and ((Test-Path (Join-Path $PastaApp 'program')) -or (Test-Path $ChaveDesinst))) { Start-Sleep -Seconds 1 }
Verificar 'pasta do programa removida' (-not (Test-Path (Join-Path $PastaApp 'program')))
Verificar 'atalho removido' (-not (Test-Path $Atalho))
Verificar 'registro de desinstalação removido' (-not (Test-Path $ChaveDesinst))
$ow = Get-Item 'HKCU:\Software\Classes\.docx\OpenWithProgids' -ErrorAction SilentlyContinue
Verificar 'entrada "Abrir com" removida' (-not ($ow -and ($ow.GetValueNames() -contains 'AYEscreva.Documento')))
Verificar 'perfil do usuário preservado (%APPDATA%\AYEscreva)' (Test-Path (Join-Path $env:APPDATA 'AYEscreva\1'))

$depois = Foto-LibreOffice
$depois | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Saida 'libreoffice-depois.json')
$difs = @($antes.Keys | Where-Object { $antes[$_] -ne $depois[$_] } | ForEach-Object { "$_ : '$($antes[$_])' -> '$($depois[$_])'" })
Verificar 'outras instalações do LibreOffice e associações de arquivo intactas' ($difs.Count -eq 0) $(if ($difs.Count) { $difs -join '; ' } else { (($antes.GetEnumerator() | Select-Object -First 3 | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join '; ') })

$falhas = @($itens | Where-Object { -not $_.ok })
[ordered]@{ instalador = $Instalador; sha256 = $hash; data = (Get-Date).ToString('s'); itens = $itens } | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $Saida 'resultado.json')
Write-Host ("`nInstalação: {0}/{1} verificações aprovadas" -f ($itens.Count - $falhas.Count), $itens.Count)
if ($falhas.Count) { exit 1 }
