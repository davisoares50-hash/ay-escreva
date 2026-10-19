<#
.SYNOPSIS
  Oráculo independente: usa o Microsoft Word (se instalado) para inventariar documentos e gerar variantes.

.DESCRIPTION
  Abre cada arquivo no Word via COM, em modo somente leitura, com macros desativadas,
  e registra contagens estruturais (páginas, seções, tabelas, notas, comentários, revisões...).
  Com -Variantes, salva o primeiro arquivo como DOCX/DOC/RTF/ODT/PDF pelo próprio Word,
  para testar a importação de arquivos produzidos por outro editor e ter um PDF de referência.

.EXAMPLE
  powershell -File tests\word\inventario_word.ps1 -Arquivos a.docx,b.docx -Json saida.json
#>
param(
  [Parameter(Mandatory)] [string[]]$Arquivos,
  [string]$Json,
  [string]$Variantes
)
$ErrorActionPreference = 'Stop'
# Com "powershell -File", listas chegam como um único texto separado por vírgulas
$Arquivos = @($Arquivos | ForEach-Object { $_ -split ',' } | Where-Object { $_ })

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0              # wdAlertsNone
$word.AutomationSecurity = 3         # msoAutomationSecurityForceDisable: nenhuma macro executa
$resultado = [ordered]@{ word = $word.Version; documentos = @() }
try {
  foreach ($arq in $Arquivos) {
    $caminho = (Resolve-Path $arq).Path
    $doc = $word.Documents.Open($caminho, $false, $true, $false)  # FileName, ConfirmConversions, ReadOnly, AddToRecentFiles
    try {
      $doc.Repaginate()
      $cab = ''
      try { $cab = $doc.Sections.Item(1).Headers.Item(1).Range.Text.Trim() } catch {}
      $inv = [ordered]@{
        arquivo      = [IO.Path]::GetFileName($caminho)
        paginas      = $doc.ComputeStatistics(2)
        palavras     = $doc.ComputeStatistics(0)
        paragrafos   = $doc.Paragraphs.Count
        secoes       = $doc.Sections.Count
        tabelas      = $doc.Tables.Count
        imagens      = $doc.InlineShapes.Count
        formas       = $doc.Shapes.Count
        notasRodape  = $doc.Footnotes.Count
        notasFim     = $doc.Endnotes.Count
        comentarios  = $doc.Comments.Count
        revisoes     = $doc.Revisions.Count
        campos       = $doc.Fields.Count
        sumarios     = $doc.TablesOfContents.Count
        indicadores  = $doc.Bookmarks.Count
        hiperlinks   = $doc.Hyperlinks.Count
        equacoes     = $doc.OMaths.Count
        itensLista   = $doc.ListParagraphs.Count
        cabecalho1   = $cab
      }
      $resultado.documentos += $inv
      Write-Host ("{0}: {1} páginas, {2} seções, {3} tabelas, {4} notas, {5} comentários, {6} revisões" -f `
        $inv.arquivo, $inv.paginas, $inv.secoes, $inv.tabelas, ($inv.notasRodape + $inv.notasFim), $inv.comentarios, $inv.revisoes)

      if ($Variantes -and $arq -eq $Arquivos[0]) {
        New-Item -ItemType Directory -Force $Variantes | Out-Null
        $base = Join-Path (Resolve-Path $Variantes).Path ([IO.Path]::GetFileNameWithoutExtension($caminho) + '-word')
        # wdFormatXMLDocument=12, wdFormatDocument97=0, wdFormatRTF=6, wdFormatOpenDocumentText=23, wdFormatPDF=17
        # Revisões e comentários em linha (sem painel lateral), como o AY exibe: PDF de referência comparável
        try { $doc.ActiveWindow.View.MarkupMode = 1 } catch {}   # wdInLineRevisions
        foreach ($fmt in @(@{e = '.docx'; f = 12 }, @{e = '.doc'; f = 0 }, @{e = '.rtf'; f = 6 }, @{e = '.odt'; f = 23 }, @{e = '.pdf'; f = 17 })) {
          $doc.SaveAs2($base + $fmt.e, $fmt.f)
          Write-Host "variante: $base$($fmt.e)"
        }
      }
    } finally { $doc.Close([ref]0) }
  }
} finally {
  $word.Quit([ref]0)
  [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
if ($Json) { $resultado | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $Json }
