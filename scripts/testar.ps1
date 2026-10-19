<#
.SYNOPSIS
  Executa a bateria de testes do AY ESCREVA sobre a distribuição montada em dist\.

.DESCRIPTION
  1. aceite_etapa1   criar documento de várias páginas, formatar, tabela, imagem, salvar (ODT/DOCX),
                     fechar, reabrir, conferir e exportar PDF e PDF/UA
  2. impressao       imprime pela fila do Windows somente na impressora virtual "Microsoft Print to PDF"
  3. seguranca       macro no evento "ao abrir" não executa (com controle positivo) e imagem remota não é baixada
  4. fixtures        gera o DOCX representativo escrito diretamente em OOXML
  5. interface       (só com -ComInterface; ≈25 min) testes pela faixa de opções, de dentro do aplicativo
                     (tests\interface\testar_faixa.ps1); alimenta a coluna "Funcionamento validado" da matriz
  6. comandos        confere cada comando da matriz (ui\abas.json) no motor e regenera a matriz
  7. word            (opcional, se o Microsoft Word estiver instalado) inventário independente e variantes DOC/RTF/ODT/PDF
  8. ida_e_volta     abre -> salva (DOCX, ODT, formato original) -> reabre, compara a estrutura
  9. visual          compara os PDFs página a página (pixels) e gera imagens das diferenças
  Os resultados ficam em tests\output\ e o resumo em tests\output\resumo.json.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\testar.ps1
  powershell -ExecutionPolicy Bypass -File scripts\testar.ps1 -SemWord -SemImpressao
  powershell -ExecutionPolicy Bypass -File scripts\testar.ps1 -ComInterface
#>
[CmdletBinding()]
param(
  [string]$Dist,
  [switch]$SemWord,
  [switch]$SemImpressao,
  [switch]$ComInterface
)
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent $PSScriptRoot
if (-not $Dist) { $Dist = Join-Path $Raiz 'dist\AY ESCREVA' }
$Py = Join-Path $Dist 'program\python.exe'
if (-not (Test-Path $Py)) { throw "Distribuição não encontrada em $Dist. Rode scripts\montar.ps1 antes." }
$Saida = Join-Path $Raiz 'tests\output'
$Fx = Join-Path $Raiz 'tests\fixtures'
New-Item -ItemType Directory -Force $Saida | Out-Null
$env:PYTHONIOENCODING = 'utf-8'
$resumo = [ordered]@{ inicio = (Get-Date).ToString('s'); etapas = [ordered]@{} }

function Etapa([string]$nome, [scriptblock]$bloco) {
  Write-Host "`n==> $nome" -ForegroundColor Cyan
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $global:LASTEXITCODE = 0
  try { & $bloco; $ok = ($LASTEXITCODE -eq 0) } catch { Write-Host $_ -ForegroundColor Red; $ok = $false }
  $resumo.etapas[$nome] = [ordered]@{ ok = $ok; segundos = [math]::Round($sw.Elapsed.TotalSeconds, 1) }
  Write-Host ("    {0} ({1:N1} s)" -f ($(if ($ok) { 'OK' } else { 'FALHOU' }), $sw.Elapsed.TotalSeconds)) -ForegroundColor $(if ($ok) { 'Green' } else { 'Red' })
}

Etapa 'marca' { Push-Location (Join-Path $Raiz 'tools'); try { & node.exe marca.mjs (Join-Path $Dist 'share\fonts\truetype\Rubik-Bold.ttf') (Join-Path $Dist 'share\fonts\truetype\Rubik-Regular.ttf') (Join-Path $Raiz 'out\marca') } finally { Pop-Location } }
Etapa 'aceite_etapa1' { & $Py (Join-Path $Raiz 'tests\uno\aceite_etapa1.py') }
if (-not $SemImpressao) {
  Etapa 'impressao' {
    if (-not (Get-Printer -Name 'Microsoft Print to PDF' -ErrorAction SilentlyContinue)) { Write-Host 'Impressora virtual ausente: etapa ignorada.'; return }
    & $Py (Join-Path $Raiz 'tests\uno\impressao.py') (Join-Path $Saida 'etapa1\teste-etapa1.docx') (Join-Path $Saida 'impressao\teste-etapa1-impresso.pdf')
  }
}
Etapa 'seguranca' { Remove-Item (Join-Path $Saida 'seguranca\.~lock.*') -Force -ErrorAction SilentlyContinue; & $Py (Join-Path $Raiz 'tests\uno\seguranca.py') }
Etapa 'fixtures' { & $Py (Join-Path $Fx 'gerar_docx.py') $Fx (Join-Path $Raiz 'out\marca\icone-128.png') }
if ($ComInterface) {
  Etapa 'interface' { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Raiz 'tests\interface\testar_faixa.ps1') -Dist $Dist }
}
Etapa 'comandos' { & $Py (Join-Path $Raiz 'tests\uno\comandos.py') }

$entradas = @(Join-Path $Fx 'compatibilidade-ooxml.docx')
$temWord = $false
if (-not $SemWord) { try { $null = [type]::GetTypeFromProgID('Word.Application'); $temWord = [bool][type]::GetTypeFromProgID('Word.Application') } catch {} }
if ($temWord) {
  Etapa 'word' {
    $lista = @((Join-Path $Fx 'compatibilidade-ooxml.docx'), (Join-Path $Saida 'etapa1\teste-etapa1.docx')) -join ','
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Raiz 'tests\word\inventario_word.ps1') -Arquivos $lista -Json (Join-Path $Saida 'word-inventario.json') -Variantes (Join-Path $Fx 'word')
  }
}
foreach ($e in 'docx', 'doc', 'rtf', 'odt') {
  $v = Join-Path $Fx "word\compatibilidade-ooxml-word.$e"
  if (Test-Path $v) { $entradas += $v }
}
Etapa 'ida_e_volta' { & $Py (Join-Path $Raiz 'tests\uno\ida_e_volta.py') (Join-Path $Saida 'ida-e-volta') @entradas }

Etapa 'visual' {
  $iv = Join-Path $Saida 'ida-e-volta'
  $vis = Join-Path $Saida 'visual'
  New-Item -ItemType Directory -Force $vis | Out-Null
  $cmp = Join-Path $Raiz 'tools\comparar-pdf.mjs'
  $falhou = $false
  foreach ($orig in Get-ChildItem $iv -Filter '*.original.pdf') {
    $nome = $orig.Name -replace '\.original\.pdf$', ''
    foreach ($copia in Get-ChildItem $iv -Filter "$nome.salvo.*.pdf") {
      & node.exe $cmp $orig.FullName $copia.FullName $vis ($copia.BaseName) 60 0.5
      if ($LASTEXITCODE) { $falhou = $true }
    }
  }
  $refWord = Join-Path $Fx 'word\compatibilidade-ooxml-word.pdf'
  if (Test-Path $refWord) { & node.exe $cmp $refWord (Join-Path $iv 'compatibilidade-ooxml-docx.original.pdf') $vis 'word-vs-ay' 60 0.5 }
  if ($falhou) { $global:LASTEXITCODE = 1 }
}

$resumo.fim = (Get-Date).ToString('s')
$resumo | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $Saida 'resumo.json')
$falhas = @($resumo.etapas.GetEnumerator() | Where-Object { -not $_.Value.ok })
Write-Host ("`nEtapas: {0} | falhas: {1}" -f $resumo.etapas.Count, $falhas.Count) -ForegroundColor $(if ($falhas.Count) { 'Red' } else { 'Green' })
if ($falhas.Count) { exit 1 }
