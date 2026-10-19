# -*- coding: utf-8 -*-
"""Gera documentos DOCX de teste escritos diretamente em OOXML (WordprocessingML), sem usar o motor do AY.

Assim o teste de ida e volta não mede o motor contra ele mesmo. O arquivo cobre os recursos que
mais costumam quebrar na troca de documentos:
  cabeçalhos e rodapés (incluindo primeira página diferente), campos PAGE/NUMPAGES, três seções
  (retrato, paisagem com duas colunas, retrato com numeração reiniciada), notas de rodapé e de fim,
  alterações controladas (inserção, exclusão, formatação), comentários, listas numeradas e com
  marcadores, tabela com células mescladas e linha de cabeçalho repetida, imagem com texto alternativo,
  caixa de texto (forma), equação OMML, sumário, indicador e referência cruzada, hiperlink externo,
  fontes ausentes (para testar substituição) e estilos personalizados.

Uso: python gerar_docx.py <pasta-de-saida> <imagem.png>
SPDX-License-Identifier: MPL-2.0
"""
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

W = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
     'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
     'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
     'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
     'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
     'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
     'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
     'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
     'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14"')
DATA = '2026-10-01T09:00:00Z'
REVISORA = 'Revisora Ana'


def run(texto, rpr=''):
    t = escape(texto)
    esp = ' xml:space="preserve"' if texto != texto.strip() else ''
    return f'<w:r>{f"<w:rPr>{rpr}</w:rPr>" if rpr else ""}<w:t{esp}>{t}</w:t></w:r>'


def par(conteudo, estilo=None, ppr_extra=''):
    ppr = (f'<w:pStyle w:val="{estilo}"/>' if estilo else '') + ppr_extra
    return f'<w:p>{f"<w:pPr>{ppr}</w:pPr>" if ppr else ""}{conteudo}</w:p>'


def campo(instr, resultado):
    return (f'<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
            f'<w:r><w:fldChar w:fldCharType="separate"/></w:r>{run(resultado)}<w:r><w:fldChar w:fldCharType="end"/></w:r>')


LOREM = ('Este parágrafo de enchimento serve para ocupar espaço na página e permitir conferir '
         'quebras, numeração, cabeçalhos e rodapés depois de abrir e salvar o documento. '
         'Acentos: ação, coração, pão, você, avó; símbolos: “aspas”, travessão — e reticências…')


def corpo():
    p = []
    # Sumário (campo TOC com resultado em cache)
    p.append(par(run('Relatório de compatibilidade AY ESCREVA'), 'Title'))
    p.append(par(run('Sumário'), 'TOCHeading'))
    p.append(f'<w:p><w:pPr><w:pStyle w:val="TOC1"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9350"/></w:tabs></w:pPr>'
             f'<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u </w:instrText></w:r>'
             f'<w:r><w:fldChar w:fldCharType="separate"/></w:r>{run("1 Introdução")}<w:r><w:tab/></w:r>{run("1")}</w:p>')
    p.append(f'<w:p><w:pPr><w:pStyle w:val="TOC1"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9350"/></w:tabs></w:pPr>'
             f'{run("2 Seção em paisagem")}<w:r><w:tab/></w:r>{run("2")}</w:p>')
    p.append(f'<w:p><w:pPr><w:pStyle w:val="TOC1"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9350"/></w:tabs></w:pPr>'
             f'{run("3 Anexo")}<w:r><w:tab/></w:r>{run("1")}<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')

    # Introdução: indicador, nota de rodapé, comentário, alterações controladas
    p.append(par('<w:bookmarkStart w:id="10" w:name="_RefIntroducao"/>' + run('Introdução') + '<w:bookmarkEnd w:id="10"/>', 'Heading1'))
    p.append(par(run('Texto com nota de rodapé') +
                 '<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteReference w:id="1"/></w:r>' +
                 run(' e outra nota') +
                 '<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteReference w:id="2"/></w:r>' +
                 run(', além de uma nota de fim') +
                 '<w:r><w:rPr><w:rStyle w:val="EndnoteReference"/></w:rPr><w:endnoteReference w:id="1"/></w:r>' + run('.')))
    p.append(par('<w:commentRangeStart w:id="0"/>' + run('Este trecho tem um comentário da revisão.') +
                 '<w:commentRangeEnd w:id="0"/><w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="0"/></w:r>'))
    p.append(par(run('Alterações controladas: texto original') +
                 f'<w:ins w:id="101" w:author="{REVISORA}" w:date="{DATA}">{run(" com inserção rastreada")}</w:ins>' +
                 run(', ') +
                 f'<w:del w:id="102" w:author="{REVISORA}" w:date="{DATA}"><w:r><w:delText xml:space="preserve">trecho excluído rastreado, </w:delText></w:r></w:del>' +
                 '<w:r><w:rPr><w:b/><w:rPrChange w:id="103" w:author="' + REVISORA + '" w:date="' + DATA + '"><w:rPr/></w:rPrChange></w:rPr><w:t>formatação rastreada</w:t></w:r>' +
                 run(' e fim da frase.')))
    p.append(par(run('Hiperlink externo (não deve ser acessado ao abrir): ') +
                 '<w:hyperlink r:id="rIdLink"><w:r><w:rPr><w:rStyle w:val="Hyperlink"/></w:rPr><w:t>exemplo.com.br</w:t></w:r></w:hyperlink>'))
    p.append(par(run('Referência cruzada para a seção ') + campo('REF _RefIntroducao \\h', 'Introdução') + run('.')))
    p.append(par(run('Texto em fonte ausente para testar substituição.', '<w:rFonts w:ascii="Fonte Inexistente AY" w:hAnsi="Fonte Inexistente AY"/>')))
    p.append(par(run('Texto em Calibri (substituível por Carlito).', '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>')))
    p.append(par(run('Uma citação em estilo personalizado do documento.'), 'CitacaoAY'))

    # Listas
    for i, item in enumerate(['Primeiro item numerado', 'Segundo item numerado', 'Terceiro item numerado']):
        p.append(par(run(item), 'ListParagraph', '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'))
    p.append(par(run('Subitem com marcador'), 'ListParagraph', '<w:numPr><w:ilvl w:val="1"/><w:numId w:val="1"/></w:numPr>'))
    for item in ['Marcador A', 'Marcador B']:
        p.append(par(run(item), 'ListParagraph', '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr>'))

    # Equação OMML: x = (a + b) / 2
    p.append(par(run('Equação: ') +
                 '<m:oMath><m:r><m:t>x=</m:t></m:r><m:f><m:num><m:r><m:t>a+b</m:t></m:r></m:num><m:den><m:r><m:t>2</m:t></m:r></m:den></m:f></m:oMath>'))

    # Imagem embutida com texto alternativo
    p.append(par('<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="1440000" cy="1440000"/>'
                 '<wp:docPr id="1" name="Imagem 1" descr="Logotipo AY ESCREVA (texto alternativo)"/>'
                 '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
                 '<pic:nvPicPr><pic:cNvPr id="1" name="logo.png" descr="Logotipo AY ESCREVA (texto alternativo)"/><pic:cNvPicPr/></pic:nvPicPr>'
                 '<pic:blipFill><a:blip r:embed="rIdImg"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                 '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="1440000" cy="1440000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
                 '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>', ppr_extra='<w:jc w:val="center"/>'))
    p.append(par(run('Figura 1 – Logotipo'), 'Caption', '<w:jc w:val="center"/>'))

    # Caixa de texto (forma DrawingML) ancorada
    p.append(par('<w:r><w:drawing><wp:anchor distT="0" distB="0" distL="114300" distR="114300" simplePos="0" relativeHeight="2" '
                 'behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1"><wp:simplePos x="0" y="0"/>'
                 '<wp:positionH relativeFrom="column"><wp:posOffset>3600000</wp:posOffset></wp:positionH>'
                 '<wp:positionV relativeFrom="paragraph"><wp:posOffset>0</wp:posOffset></wp:positionV>'
                 '<wp:extent cx="1800000" cy="540000"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapSquare wrapText="bothSides"/>'
                 '<wp:docPr id="2" name="Caixa de texto 1"/><wp:cNvGraphicFramePr/>'
                 '<a:graphic><a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"><wps:wsp>'
                 '<wps:cNvSpPr txBox="1"/><wps:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="1800000" cy="540000"/></a:xfrm>'
                 '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="FFF4CC"/></a:solidFill>'
                 '<a:ln w="12700"><a:solidFill><a:srgbClr val="11806A"/></a:solidFill></a:ln></wps:spPr>'
                 '<wps:txbx><w:txbxContent>' + par(run('Caixa de texto')) + '</w:txbxContent></wps:txbx>'
                 '<wps:bodyPr rot="0" vert="horz" wrap="square" lIns="91440" tIns="45720" rIns="91440" bIns="45720" anchor="t"/>'
                 '</wps:wsp></a:graphicData></a:graphic></wp:anchor></w:drawing></w:r>' + run('Parágrafo com caixa de texto ancorada à direita.')))

    # Tabela com cabeçalho repetido, célula mesclada horizontal e vertical
    borda = '<w:tblBorders>' + ''.join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="555555"/>' for b in
                                       ('top', 'left', 'bottom', 'right', 'insideH', 'insideV')) + '</w:tblBorders>'
    cel = lambda t, extra='', larg=2400: f'<w:tc><w:tcPr><w:tcW w:w="{larg}" w:type="dxa"/>{extra}</w:tcPr>{par(run(t))}</w:tc>'
    linhas = ['<w:tr><w:trPr><w:tblHeader/></w:trPr>' + cel('Região', '<w:shd w:val="clear" w:color="auto" w:fill="DDEFEA"/>') +
              cel('Vendas (mesclado)', '<w:gridSpan w:val="2"/><w:shd w:val="clear" w:color="auto" w:fill="DDEFEA"/>', 4800) +
              cel('Obs.', '<w:shd w:val="clear" w:color="auto" w:fill="DDEFEA"/>') + '</w:tr>']
    for i, reg in enumerate(['Norte', 'Nordeste', 'Sudeste', 'Sul', 'Centro-Oeste']):
        obs = cel('Mesclada vertical', '<w:vMerge w:val="restart"/>') if i == 0 else cel('', '<w:vMerge/>')
        linhas.append(f'<w:tr>{cel(reg)}{cel(str(100 + i * 7))}{cel(str(200 + i * 11))}{obs}</w:tr>')
    grade = ''.join('<w:gridCol w:w="2400"/>' for _ in range(4))
    p.append(f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="9600" w:type="dxa"/>{borda}</w:tblPr>'
             f'<w:tblGrid>{grade}</w:tblGrid>{"".join(linhas)}</w:tbl>')
    for _ in range(3):
        p.append(par(run(LOREM)))

    # Fim da seção 1 (retrato, primeira página diferente)
    sec1 = ('<w:sectPr><w:headerReference w:type="default" r:id="rIdH1"/><w:headerReference w:type="first" r:id="rIdH2"/>'
            '<w:footerReference w:type="default" r:id="rIdF1"/><w:footerReference w:type="first" r:id="rIdF1"/>'
            '<w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1418" w:right="1134" w:bottom="1418" w:left="1701" w:header="709" w:footer="709" w:gutter="0"/>'
            '<w:cols w:space="708"/><w:titlePg/></w:sectPr>')
    p.append(par(run(LOREM), ppr_extra=sec1))

    # Seção 2: paisagem, duas colunas
    p.append(par(run('Seção em paisagem'), 'Heading1'))
    for _ in range(8):
        p.append(par(run(LOREM)))
    sec2 = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdF1"/><w:type w:val="nextPage"/>'
            '<w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/><w:pgMar w:top="1134" w:right="1418" w:bottom="1134" w:left="1418" w:header="709" w:footer="709" w:gutter="0"/>'
            '<w:cols w:num="2" w:space="708"/></w:sectPr>')
    p.append(par(run(LOREM), ppr_extra=sec2))

    # Seção 3: retrato, numeração reiniciada em 1
    p.append(par(run('Anexo'), 'Heading1'))
    p.append(par(run('Nesta seção a numeração das páginas recomeça em 1.')))
    for _ in range(4):
        p.append(par(run(LOREM)))
    p.append(par(run('FIM DO DOCUMENTO DE COMPATIBILIDADE')))
    sec3 = ('<w:sectPr><w:headerReference w:type="default" r:id="rIdH1"/><w:footerReference w:type="default" r:id="rIdF1"/>'
            '<w:footnotePr><w:numFmt w:val="decimal"/></w:footnotePr><w:endnotePr><w:numFmt w:val="lowerRoman"/></w:endnotePr>'
            '<w:type w:val="nextPage"/><w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1418" w:right="1134" w:bottom="1418" w:left="1701" w:header="709" w:footer="709" w:gutter="0"/>'
            '<w:pgNumType w:start="1"/><w:cols w:space="708"/></w:sectPr>')
    return f'<w:body>{"".join(p)}{sec3}</w:body>'


def documento():
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document {W}>{corpo()}</w:document>'


def cabecalho(texto):
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:hdr {W}>'
            f'{par(run(texto), "Header")}</w:hdr>')


def rodape():
    conteudo = par(run('Página ') + campo('PAGE', '1') + run(' de ') + campo('NUMPAGES', '1'), 'Footer', '<w:jc w:val="center"/>')
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:ftr {W}>{conteudo}</w:ftr>'


def notas(tipo):
    tag = 'footnote' if tipo == 'footnotes' else 'endnote'
    ref = 'FootnoteReference' if tag == 'footnote' else 'EndnoteReference'
    estilo = 'FootnoteText' if tag == 'footnote' else 'EndnoteText'
    sep = (f'<w:{tag} w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:{tag}>'
           f'<w:{tag} w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/></w:r></w:p></w:{tag}>')
    textos = ['Primeira nota de rodapé.', 'Segunda nota de rodapé.'] if tag == 'footnote' else ['Nota de fim do documento.']
    itens = ''.join(f'<w:{tag} w:id="{i}"><w:p><w:pPr><w:pStyle w:val="{estilo}"/></w:pPr>'
                    f'<w:r><w:rPr><w:rStyle w:val="{ref}"/></w:rPr><w:{tag}Ref/></w:r>{run(" " + t)}</w:p></w:{tag}>'
                    for i, t in enumerate(textos, 1))
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:{tipo} {W}>{sep}{itens}</w:{tipo}>'


def comentarios():
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:comments {W}>'
            f'<w:comment w:id="0" w:author="{REVISORA}" w:date="{DATA}" w:initials="RA">'
            f'{par(run("Verificar este parágrafo antes da entrega."), "CommentText")}</w:comment></w:comments>')


def estilos():
    def est(tipo, sid, nome, extra='', base=None, prox=None):
        return (f'<w:style w:type="{tipo}" w:styleId="{sid}"><w:name w:val="{nome}"/>'
                + (f'<w:basedOn w:val="{base}"/>' if base else '') + (f'<w:next w:val="{prox}"/>' if prox else '')
                + f'<w:qFormat/>{extra}</w:style>')
    s = [
        '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Times New Roman"/>'
        '<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="pt-BR" w:eastAsia="en-US" w:bidi="ar-SA"/></w:rPr></w:rPrDefault>'
        '<w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="259" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>',
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>',
        est('paragraph', 'Title', 'Title', '<w:rPr><w:sz w:val="48"/><w:color w:val="0A5C4C"/></w:rPr>', 'Normal', 'Normal'),
        est('paragraph', 'Heading1', 'heading 1', '<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr>'
            '<w:rPr><w:b/><w:sz w:val="32"/><w:color w:val="11806A"/></w:rPr>', 'Normal', 'Normal'),
        est('paragraph', 'Heading2', 'heading 2', '<w:pPr><w:keepNext/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="26"/></w:rPr>', 'Normal', 'Normal'),
        est('paragraph', 'TOCHeading', 'TOC Heading', '<w:rPr><w:b/><w:sz w:val="28"/></w:rPr>', 'Heading1', 'Normal'),
        est('paragraph', 'TOC1', 'toc 1', '<w:pPr><w:spacing w:after="100"/></w:pPr>', 'Normal', 'Normal'),
        est('paragraph', 'ListParagraph', 'List Paragraph', '<w:pPr><w:ind w:left="720"/><w:contextualSpacing/></w:pPr>', 'Normal'),
        est('paragraph', 'Caption', 'caption', '<w:rPr><w:i/><w:sz w:val="18"/></w:rPr>', 'Normal', 'Normal'),
        est('paragraph', 'Header', 'header', '', 'Normal'),
        est('paragraph', 'Footer', 'footer', '', 'Normal'),
        est('paragraph', 'FootnoteText', 'footnote text', '<w:rPr><w:sz w:val="20"/></w:rPr>', 'Normal'),
        est('paragraph', 'EndnoteText', 'endnote text', '<w:rPr><w:sz w:val="20"/></w:rPr>', 'Normal'),
        est('paragraph', 'CommentText', 'annotation text', '<w:rPr><w:sz w:val="20"/></w:rPr>', 'Normal'),
        est('paragraph', 'CitacaoAY', 'Citação AY', '<w:pPr><w:ind w:left="1134" w:right="1134"/><w:jc w:val="both"/></w:pPr>'
            '<w:rPr><w:i/><w:color w:val="5B6664"/></w:rPr>', 'Normal', 'Normal'),
        est('character', 'FootnoteReference', 'footnote reference', '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr>'),
        est('character', 'EndnoteReference', 'endnote reference', '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr>'),
        est('character', 'CommentReference', 'annotation reference', '<w:rPr><w:sz w:val="16"/></w:rPr>'),
        est('character', 'Hyperlink', 'Hyperlink', '<w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr>'),
        '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:tblPr><w:tblBorders>'
        + ''.join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="auto"/>' for b in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'))
        + '</w:tblBorders></w:tblPr></w:style>',
    ]
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:styles {W}>{"".join(s)}</w:styles>'


def numeracao():
    def nivel(i, fmt, texto, ind):
        return (f'<w:lvl w:ilvl="{i}"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/><w:lvlText w:val="{texto}"/><w:lvlJc w:val="left"/>'
                f'<w:pPr><w:ind w:left="{ind}" w:hanging="360"/></w:pPr>'
                + ('<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:hint="default"/></w:rPr>' if fmt == 'bullet' else '') + '</w:lvl>')
    a1 = nivel(0, 'decimal', '%1.', 720) + nivel(1, 'bullet', '', 1440)
    a2 = nivel(0, 'bullet', '', 720)
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:numbering {W}>'
            f'<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>{a1}</w:abstractNum>'
            f'<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="hybridMultilevel"/>{a2}</w:abstractNum>'
            f'<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num><w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num></w:numbering>')


def configuracoes():
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:settings {W}>'
            '<w:trackRevisions/><w:defaultTabStop w:val="708"/><w:characterSpacingControl w:val="doNotCompress"/>'
            '<w:footnotePr><w:footnote w:id="-1"/><w:footnote w:id="0"/></w:footnotePr>'
            '<w:endnotePr><w:endnote w:id="-1"/><w:endnote w:id="0"/></w:endnotePr>'
            '<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>'
            '</w:settings>')


TIPOS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
<Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>
<Override PartName="/word/endnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.endnotes+xml"/>
<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
<Override PartName="/word/header2.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>'''

RELS_RAIZ = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>'''

RELS_DOC = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rIdNum" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
<Relationship Id="rIdSet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
<Relationship Id="rIdFn" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes" Target="footnotes.xml"/>
<Relationship Id="rIdEn" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/endnotes" Target="endnotes.xml"/>
<Relationship Id="rIdCom" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
<Relationship Id="rIdH1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
<Relationship Id="rIdH2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header2.xml"/>
<Relationship Id="rIdF1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
<Relationship Id="rIdImg" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/logo.png"/>
<Relationship Id="rIdLink" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://exemplo.com.br/" TargetMode="External"/>
</Relationships>'''

CORE = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>Relatório de compatibilidade AY ESCREVA</dc:title><dc:creator>Projeto AY ESCREVA</dc:creator><dc:language>pt-BR</dc:language>
<dcterms:created xsi:type="dcterms:W3CDTF">2026-10-01T09:00:00Z</dcterms:created>
</cp:coreProperties>'''


def gerar(saida, imagem):
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    destino = saida / 'compatibilidade-ooxml.docx'
    partes = {
        '[Content_Types].xml': TIPOS, '_rels/.rels': RELS_RAIZ, 'docProps/core.xml': CORE,
        'word/_rels/document.xml.rels': RELS_DOC, 'word/document.xml': documento(), 'word/styles.xml': estilos(),
        'word/numbering.xml': numeracao(), 'word/settings.xml': configuracoes(),
        'word/footnotes.xml': notas('footnotes'), 'word/endnotes.xml': notas('endnotes'),
        'word/comments.xml': comentarios(), 'word/header1.xml': cabecalho('AY ESCREVA — cabeçalho padrão'),
        'word/header2.xml': cabecalho('Cabeçalho da primeira página'), 'word/footer1.xml': rodape(),
    }
    with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as z:
        for nome, conteudo in partes.items():
            info = zipfile.ZipInfo(nome, date_time=(2026, 10, 1, 9, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, conteudo.encode('utf-8'))
        info = zipfile.ZipInfo('word/media/logo.png', date_time=(2026, 10, 1, 9, 0, 0))
        z.writestr(info, Path(imagem).read_bytes())
    print(f'gerado: {destino}')
    return destino


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    gerar(sys.argv[1], sys.argv[2])
