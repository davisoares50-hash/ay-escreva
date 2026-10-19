# -*- coding: utf-8 -*-
"""Teste de aceite da Etapa 1 do AY ESCREVA.

Critério: criar um documento com várias páginas, formatar texto, inserir uma tabela e uma imagem,
salvar, fechar, reabrir e exportar para PDF — em ODT e em DOCX.

Uso:  "dist\\AY ESCREVA\\program\\python.exe" tests\\uno\\aceite_etapa1.py
SPDX-License-Identifier: MPL-2.0
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ay_uno import Motor, Relatorio, SAIDA_TESTES, RAIZ, props, url, salvar, fechar, paginas, paginas_pdf  # noqa: E402

from com.sun.star.awt import Size  # noqa: E402
from com.sun.star.awt.FontWeight import BOLD, NORMAL  # noqa: E402
from com.sun.star.awt.FontSlant import ITALIC  # noqa: E402
from com.sun.star.awt.FontUnderline import SINGLE as SUBLINHADO_SIMPLES  # noqa: E402
from com.sun.star.awt.FontStrikeout import SINGLE as TACHADO_SIMPLES  # noqa: E402
from com.sun.star.style.BreakType import PAGE_BEFORE  # noqa: E402
# ParaAdjust é "short" na API (valores de com.sun.star.style.ParagraphAdjust)
CENTER, BLOCK = 3, 2
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK  # noqa: E402
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER  # noqa: E402

PASTA = SAIDA_TESTES / 'etapa1'
IMAGEM = RAIZ / 'out' / 'marca' / 'icone-256.png'

TITULO = 'Relatório de teste do AY ESCREVA'
VERMELHO = 0xC00000
AMARELO = 0xFFFF00

PARAGRAFO = ('O AY ESCREVA é um editor de textos livre, gratuito e em português do Brasil. '
             'Este parágrafo existe para ocupar espaço e forçar a criação de várias páginas, '
             'de modo que a paginação, os cabeçalhos, os rodapés e a numeração de páginas possam '
             'ser conferidos depois de salvar, fechar e reabrir o documento. Acentuação: ação, '
             'coração, pão, você, avó, útil, então — e também “aspas” e travessões.')


def escrever(texto, cursor, conteudo, quebra=True, **fmt):
    for k, v in fmt.items():
        cursor.setPropertyValue(k, v)
    texto.insertString(cursor, conteudo, False)
    for k in fmt:
        cursor.setPropertyToDefault(k)
    if quebra:
        texto.insertControlCharacter(cursor, PARAGRAPH_BREAK, False)


def criar_documento(motor):
    doc = motor.novo()
    texto = doc.Text
    c = texto.createTextCursor()

    # Cabeçalho e rodapé com número de página
    estilo = doc.StyleFamilies.getByName('PageStyles').getByName('Standard')
    estilo.HeaderIsOn = True
    estilo.FooterIsOn = True
    estilo.HeaderText.setString('AY ESCREVA — documento de teste')
    rodape = estilo.FooterText
    rc = rodape.createTextCursor()
    rodape.insertString(rc, 'Página ', False)
    campo = doc.createInstance('com.sun.star.text.TextField.PageNumber')
    campo.NumberingType = 4  # ARABIC
    campo.SubType = 1        # CURRENT
    rodape.insertTextContent(rc, campo, False)

    # Título
    c.ParaStyleName = 'Heading 1'
    escrever(texto, c, TITULO)
    c.ParaStyleName = 'Text body'

    # Formatação de caracteres
    escrever(texto, c, 'Formatação: ', quebra=False)
    escrever(texto, c, 'trecho em negrito', quebra=False, CharWeight=BOLD)
    escrever(texto, c, ', ', quebra=False)
    escrever(texto, c, 'trecho em itálico', quebra=False, CharPosture=ITALIC)
    escrever(texto, c, ', ', quebra=False)
    escrever(texto, c, 'trecho sublinhado', quebra=False, CharUnderline=SUBLINHADO_SIMPLES)
    escrever(texto, c, ', ', quebra=False)
    escrever(texto, c, 'trecho tachado', quebra=False, CharStrikeout=TACHADO_SIMPLES)
    escrever(texto, c, ', x', quebra=False)
    escrever(texto, c, '2', quebra=False, CharEscapement=33, CharEscapementHeight=58)
    escrever(texto, c, ', ', quebra=False)
    escrever(texto, c, 'trecho vermelho 14 pt', quebra=False, CharColor=VERMELHO, CharHeight=14.0)
    escrever(texto, c, ', ', quebra=False)
    escrever(texto, c, 'trecho realçado', quebra=False, CharBackColor=AMARELO)
    escrever(texto, c, ' e ', quebra=False)
    escrever(texto, c, 'trecho em Liberation Sans', quebra=False, CharFontName='Liberation Sans')
    escrever(texto, c, '.')

    c.ParaAdjust = CENTER
    escrever(texto, c, 'Parágrafo centralizado.')
    c.ParaAdjust = BLOCK
    for i in range(1, 19):
        escrever(texto, c, f'{i}. {PARAGRAFO}')
    c.setPropertyToDefault('ParaAdjust')

    # Tabela 4x3
    c.ParaStyleName = 'Heading 2'
    c.BreakType = PAGE_BEFORE
    escrever(texto, c, 'Tabela e imagem')
    c.setPropertyToDefault('BreakType')
    c.ParaStyleName = 'Text body'
    tabela = doc.createInstance('com.sun.star.text.TextTable')
    tabela.initialize(4, 3)
    texto.insertTextContent(c, tabela, False)
    tabela.Name = 'TabelaTeste'
    dados = [('Item', 'Quantidade', 'Preço'), ('Caderno', '2', 'R$ 15,90'),
             ('Caneta', '10', 'R$ 2,50'), ('Régua', '1', 'R$ 4,00')]
    for li, linha in enumerate(dados):
        for co, valor in enumerate(linha):
            tabela.getCellByName(f'{"ABC"[co]}{li + 1}').setString(valor)

    # Imagem embutida, ancorada como caractere, com texto alternativo
    escrever(texto, c, 'Imagem abaixo:')
    provedor = motor.servico('com.sun.star.graphic.GraphicProvider')
    grafico = provedor.queryGraphic(props(URL=url(IMAGEM)))
    img = doc.createInstance('com.sun.star.text.TextGraphicObject')
    img.Graphic = grafico
    img.AnchorType = AS_CHARACTER
    img.Size = Size(4000, 4000)
    texto.insertTextContent(c, img, False)
    img.Name = 'ImagemTeste'
    img.Description = 'Logotipo do AY ESCREVA'
    texto.insertControlCharacter(c, PARAGRAPH_BREAK, False)

    for i in range(19, 31):
        escrever(texto, c, f'{i}. {PARAGRAFO}')
    escrever(texto, c, 'FIM DO DOCUMENTO DE TESTE', quebra=False)
    return doc


def achar(doc, trecho):
    busca = doc.createSearchDescriptor()
    busca.SearchString = trecho
    return doc.findFirst(busca)


def verificar_documento(rel, doc, rotulo, paginas_esperadas):
    p = paginas(doc)
    rel.verificar(f'{rotulo}: várias páginas', p >= 3 and p == paginas_esperadas, f'{p} páginas (original: {paginas_esperadas})')
    corpo = doc.Text.getString()
    rel.verificar(f'{rotulo}: texto completo preservado', TITULO in corpo and 'FIM DO DOCUMENTO DE TESTE' in corpo and '30. O AY ESCREVA' in corpo)
    rel.verificar(f'{rotulo}: acentuação preservada', 'ação, coração, pão, você, avó' in corpo and '“aspas”' in corpo)

    par = doc.Text.createEnumeration().nextElement()
    rel.verificar(f'{rotulo}: título com estilo Título 1', par.ParaStyleName == 'Heading 1', par.ParaStyleName)

    r = achar(doc, 'trecho em negrito')
    rel.verificar(f'{rotulo}: negrito', r is not None and r.CharWeight == BOLD)
    r = achar(doc, 'trecho em itálico')
    rel.verificar(f'{rotulo}: itálico', r is not None and r.CharPosture == ITALIC)
    r = achar(doc, 'trecho sublinhado')
    rel.verificar(f'{rotulo}: sublinhado', r is not None and r.CharUnderline == SUBLINHADO_SIMPLES)
    r = achar(doc, 'trecho tachado')
    rel.verificar(f'{rotulo}: tachado', r is not None and r.CharStrikeout == TACHADO_SIMPLES)
    r = achar(doc, 'trecho vermelho 14 pt')
    rel.verificar(f'{rotulo}: cor e tamanho', r is not None and r.CharColor == VERMELHO and abs(r.CharHeight - 14.0) < 0.01,
                  f'cor={hex(r.CharColor) if r else None} tam={r.CharHeight if r else None}')
    r = achar(doc, 'trecho realçado')
    realce = (r.CharHighlight, r.CharBackColor) if r is not None else None
    rel.verificar(f'{rotulo}: realce', r is not None and AMARELO in realce, f'realce/fundo={realce}')
    r = achar(doc, 'trecho em Liberation Sans')
    rel.verificar(f'{rotulo}: fonte do trecho', r is not None and r.CharFontName == 'Liberation Sans', r.CharFontName if r else '')
    r = achar(doc, 'Parágrafo centralizado.')
    rel.verificar(f'{rotulo}: alinhamento centralizado', r is not None and r.ParaAdjust == CENTER)
    r = achar(doc, '2, trecho vermelho')
    if r is not None:
        r.collapseToStart()
        r.goRight(1, True)
    rel.verificar(f'{rotulo}: sobrescrito', r is not None and r.CharEscapement > 0, f'escapement={r.CharEscapement if r else None}')

    tabelas = doc.TextTables
    ok_tab = tabelas.Count == 1
    if ok_tab:
        t = tabelas.getByIndex(0)
        ok_tab = (t.Rows.Count == 4 and t.Columns.Count == 3 and t.getCellByName('A1').getString() == 'Item'
                  and t.getCellByName('C4').getString() == 'R$ 4,00')
    rel.verificar(f'{rotulo}: tabela 4x3 com conteúdo', ok_tab)

    graficos = doc.GraphicObjects
    ok_img = graficos.Count == 1
    detalhe = ''
    if ok_img:
        g = graficos.getByIndex(0)
        tam = g.Graphic.Size100thMM if g.Graphic else None
        detalhe = f'descr="{g.Description}" tam={g.Size.Width}x{g.Size.Height}'
        ok_img = g.Graphic is not None and g.Description == 'Logotipo do AY ESCREVA' and abs(g.Size.Width - 4000) < 50
    rel.verificar(f'{rotulo}: imagem embutida com texto alternativo', ok_img, detalhe)

    estilo = doc.StyleFamilies.getByName('PageStyles').getByName('Standard')
    rel.verificar(f'{rotulo}: cabeçalho', estilo.HeaderIsOn and 'AY ESCREVA' in estilo.HeaderText.getString())
    campos = [f for f in _enumerar(doc.TextFields) if f.supportsService('com.sun.star.text.TextField.PageNumber')]
    rel.verificar(f'{rotulo}: rodapé com número de página', estilo.FooterIsOn and len(campos) >= 1)


def _enumerar(acesso):
    e = acesso.createEnumeration()
    while e.hasMoreElements():
        yield e.nextElement()


def main():
    rel = Relatorio('Aceite da Etapa 1')
    PASTA.mkdir(parents=True, exist_ok=True)
    resultado = {}
    with Motor('aceite1') as motor:
        doc = criar_documento(motor)
        pags = paginas(doc)
        rel.verificar('documento criado com várias páginas', pags >= 3, f'{pags} páginas')
        arq_odt = salvar(doc, PASTA / 'teste-etapa1.odt')
        arq_docx = salvar(doc, PASTA / 'teste-etapa1.docx')
        fechar(doc)
        rel.verificar('salvou ODT e DOCX', arq_odt.stat().st_size > 0 and arq_docx.stat().st_size > 0,
                      f'odt={arq_odt.stat().st_size} B, docx={arq_docx.stat().st_size} B')

        for arq in (arq_odt, arq_docx):
            rotulo = arq.suffix[1:].upper()
            doc = motor.abrir(arq)
            verificar_documento(rel, doc, rotulo, pags)
            pdf = salvar(doc, PASTA / f'{arq.stem}-{rotulo.lower()}.pdf')
            np = paginas_pdf(pdf)
            rel.verificar(f'{rotulo}: exportou PDF com o mesmo número de páginas', pdf.read_bytes()[:5] == b'%PDF-' and np == pags,
                          f'{np} páginas no PDF')
            # Exportação com marcação de acessibilidade (PDF/UA)
            pdfua = salvar(doc, PASTA / f'{arq.stem}-{rotulo.lower()}-pdfua.pdf', FilterData=uno_pdfua())
            rel.verificar(f'{rotulo}: exportou PDF marcado (PDF/UA)', b'/StructTreeRoot' in pdfua.read_bytes())
            resultado[rotulo] = {'paginas': paginas(doc), 'pdf': str(pdf)}
            fechar(doc)
    codigo = rel.finalizar()
    (PASTA / 'resultado.json').write_text(json.dumps({'itens': [
        {'ok': ok, 'verificacao': d, 'detalhe': det} for ok, d, det in rel.itens], 'documentos': resultado},
        ensure_ascii=False, indent=2), encoding='utf-8')
    return codigo


def uno_pdfua():
    import uno
    return uno.Any('[]com.sun.star.beans.PropertyValue', props(PDFUACompliance=True, UseTaggedPDF=True))


if __name__ == '__main__':
    sys.exit(main())
