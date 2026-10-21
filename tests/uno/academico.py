# -*- coding: utf-8 -*-
"""Formatar trabalho acadêmico (entrega B, 0.4.0): análise, prévia, aplicação, desfazer e relatório de conformidade.

Documento de teste montado aqui, como um TCC digitado no Word: capa, folha de rosto, resumo, abstract, sumário vazio,
títulos com número digitado em negrito, texto em Calibri 11 com entrelinhas 1,08, citação recuada 3,5 cm, nota de
rodapé, tabela e imagem com identificação e fonte, parágrafo longo entre aspas, referências justificadas em 1,5,
apêndice, alteração controlada e comentário; números, datas, nomes próprios, siglas e citações no texto.

  1. análise: partes identificadas no DOCX e no ODT;
  2. relatório antes: não conformidades esperadas;
  3. prévia: lista de mudanças, sem alterar o documento;
  4. aplicação: texto, notas, tabelas, imagens, alterações controladas e comentários preservados; relatório depois;
  5. desfazer: uma ação volta tudo; refazer reaplica;
  6. salvar em DOCX e ODT e reabrir: conformidade mantida;
  7. trabalhar numa cópia: original intacto;
  8. variantes: títulos por estilo (numeração automática), frente e verso, modelo da instituição, artigo;
  9. documento longo: tempos de análise e aplicação.

Uso: "dist\\AY ESCREVA\\program\\python.exe" tests\\uno\\academico.py
SPDX-License-Identifier: MPL-2.0
"""
import hashlib
import json
import struct
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ay_uno import Motor, RAIZ, SAIDA_TESTES, props, url, salvar, fechar  # noqa: E402

sys.path.insert(0, str(RAIZ / 'extensao' / 'ayescreva' / 'pythonpath'))
import ay_academico as A  # noqa: E402

import uno  # noqa: E402

SAIDA = SAIDA_TESTES / 'academico'
itens = []
medidas = {}


def verificar(descricao, ok, detalhe=''):
    itens.append({'ok': bool(ok), 'verificacao': descricao, 'detalhe': str(detalhe)})
    print(f"[{'OK  ' if ok else 'FALHA'}] {descricao}{' — ' + str(detalhe) if detalhe else ''}", flush=True)


def png(caminho, w=120, h=80):
    linhas = b''.join(b'\x00' + bytes(v for x in range(w) for v in ((x * 2) % 256, (y * 3) % 256, 140)) for y in range(h))

    def bloco(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    Path(caminho).write_bytes(b'\x89PNG\r\n\x1a\n' + bloco(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                              + bloco(b'IDAT', zlib.compress(linhas)) + bloco(b'IEND', b''))


CORPO = ('O AY ESCREVA foi avaliado em 12/10/2025 por Ana Souza, do IBGE, com 3,5% de variação e 1.234 respostas. '
         'Segundo Silva (2019, p. 12), a interface reduz o retrabalho; Pereira e Lima (2021) chegaram a resultado semelhante '
         'usando a API REST e o protocolo HTTP/2. ')
LONGA = ('A pesquisa mostrou que a adoção de ferramentas livres em instituições públicas depende menos do custo das licenças '
         'e mais da formação das equipes, da compatibilidade com os formatos já usados e do suporte disponível para as '
         'pessoas que escrevem documentos todos os dias, em especial nos setores administrativos (Souza, 2020, p. 45).')
ASPAS = ('“A interoperabilidade entre formatos é o fator que mais pesa na decisão de migrar, porque os documentos '
         'circulam entre órgãos, empresas e cidadãos que usam programas diferentes, e qualquer perda de formatação vira '
         'retrabalho e desconfiança no processo inteiro de adoção” (Lima, 2022, p. 8).')


class Montador:
    def __init__(self, doc):
        self.doc, self.texto = doc, doc.getText()
        self.cur = self.texto.createTextCursor()
        self.primeiro = True

    def par(self, t, estilo='Standard', quebra=False, **direto):
        if not self.primeiro:
            self.texto.insertControlCharacter(self.cur, 0, False)
        self.primeiro = False
        self.cur.setPropertyValue('ParaStyleName', estilo)
        for k in ('BreakType', 'ParaLeftMargin', 'ParaAdjust', 'CharWeight', 'ParaFirstLineIndent'):
            try:
                self.cur.setPropertyToDefault(k)
            except Exception:
                pass
        if quebra:
            self.cur.setPropertyValue('BreakType', uno.Enum('com.sun.star.style.BreakType', 'PAGE_BEFORE'))
        ini = self.cur.getStart()
        self.texto.insertString(self.cur, t, False)
        rng = self.texto.createTextCursorByRange(ini)
        rng.gotoEndOfParagraph(True)
        for k, v in direto.items():
            rng.setPropertyValue(k, v)
        return rng

    def word(self, t, **extra):
        """Parágrafo com a formatação direta típica de um documento do Word (Calibri 11, 1,08, 8 pt depois)."""
        ls = uno.createUnoStruct('com.sun.star.style.LineSpacing')
        ls.Mode, ls.Height = 0, 108
        base = dict(CharFontName='Calibri', CharHeight=11.0, ParaLineSpacing=ls, ParaBottomMargin=A.pt(8))
        base.update(extra)
        return self.par(t, **base)


def montar_tcc(doc, imagem, titulos_por_estilo=False):
    m = Montador(doc)
    C = A.CENTRO
    # capa e folha de rosto
    m.word('UNIVERSIDADE FEDERAL DO EXEMPLO', ParaAdjust=C, CharWeight=150.0)
    m.word('Maria da Silva Souza', ParaAdjust=C)
    m.word('ADOÇÃO DE EDITORES LIVRES NO SERVIÇO PÚBLICO: UM ESTUDO DE CASO', ParaAdjust=C, CharWeight=150.0)
    m.word('São Paulo', ParaAdjust=C)
    m.word('2026', ParaAdjust=C)
    m.word('Maria da Silva Souza', ParaAdjust=C, quebra=True)
    m.word('ADOÇÃO DE EDITORES LIVRES NO SERVIÇO PÚBLICO: UM ESTUDO DE CASO', ParaAdjust=C, CharWeight=150.0)
    m.word('Trabalho de Conclusão de Curso apresentado ao Curso de Administração Pública da Universidade Federal do Exemplo.',
           ParaLeftMargin=A.cm(8))
    m.word('São Paulo, 2026', ParaAdjust=C)
    # pré-textuais
    m.word('RESUMO', ParaAdjust=C, CharWeight=150.0, quebra=True)
    m.word('Este trabalho analisa a adoção de editores livres em três órgãos públicos entre 2023 e 2025.')
    m.word('Palavras-chave: software livre; administração pública; formatos abertos.')
    m.word('ABSTRACT', ParaAdjust=C, CharWeight=150.0, quebra=True)
    m.word('This work analyzes the adoption of free editors in three public bodies between 2023 and 2025.')
    m.word('SUMÁRIO', ParaAdjust=C, CharWeight=150.0, quebra=True)
    # textuais
    def titulo(numero, t, nivel, quebra=False):
        if titulos_por_estilo:
            return m.par(t, estilo=f'Heading {nivel}', quebra=quebra)
        return m.word(f'{numero} {t}', CharWeight=150.0, quebra=quebra)
    titulo('1', 'INTRODUÇÃO', 1, quebra=True)
    r = m.word(CORPO * 2, ParaAdjust=A.JUST)
    fn = doc.createInstance('com.sun.star.text.Footnote')
    doc.getText().insertTextContent(r.getEnd(), fn, False)
    fn.setString('Dados coletados em 2024 pela equipe do projeto, com autorização dos órgãos (Processo nº 23001.000123/2024-11).')
    m.word(CORPO)
    titulo('2', 'REFERENCIAL TEÓRICO', 1, quebra=True)
    titulo('2.1', 'Conceitos básicos', 2)
    m.word(CORPO)
    m.word(LONGA, ParaLeftMargin=A.cm(3.5), CharHeight=11.0)
    m.word(ASPAS)
    m.word('Tabela 1 – Respostas por órgão em 2024')
    tab = doc.createInstance('com.sun.star.text.TextTable')
    tab.initialize(3, 2)
    m.texto.insertControlCharacter(m.cur, 0, False)
    doc.getText().insertTextContent(m.cur, tab, False)
    for cel, val in zip(('A1', 'B1', 'A2', 'B2', 'A3', 'B3'), ('Órgão', 'Respostas', 'Secretaria A', '1.234', 'Secretaria B', '987')):
        tab.getCellByName(cel).setString(val)
    m.cur.gotoEnd(False)
    m.primeiro = True
    m.word('Fonte: Elaborado pela autora (2026).')
    m.word('Figura 1 – Tela do editor em 2025')
    m.par('', estilo='Standard')
    g = doc.createInstance('com.sun.star.text.TextGraphicObject')
    g.Graphic = GRAFICOS.queryGraphic(props(URL=url(imagem)))
    g.AnchorType = uno.Enum('com.sun.star.text.TextContentAnchorType', 'AS_CHARACTER')
    sz = uno.createUnoStruct('com.sun.star.awt.Size')
    sz.Width, sz.Height = 6000, 4000
    g.Size = sz
    doc.getText().insertTextContent(m.cur, g, False)
    m.word('Fonte: Captura de tela feita pela autora (2025).')
    titulo('3', 'CONCLUSÃO', 1, quebra=True)
    m.word('Os resultados indicam que a formação das equipes pesa mais que o custo. Em 2026, 87% dos documentos já usavam ODT.')
    # pós-textuais
    ls15 = uno.createUnoStruct('com.sun.star.style.LineSpacing')
    ls15.Mode, ls15.Height = 0, 150
    m.word('REFERÊNCIAS', ParaAdjust=C, CharWeight=150.0, quebra=True)
    for ref in ('LIMA, J. Interoperabilidade de documentos. 2. ed. Brasília: Enap, 2022.',
                'PEREIRA, A.; LIMA, R. Formatos abertos no governo. Revista do Serviço Público, Brasília, v. 72, n. 1, p. 10-30, 2021.',
                'SILVA, M. Software livre e administração pública. São Paulo: Atlas, 2019.'):
        m.word(ref, ParaAdjust=A.JUST, ParaLineSpacing=ls15)
    m.word('APÊNDICE A – Questionário aplicado', ParaAdjust=C, CharWeight=150.0, quebra=True)
    m.word('1. Qual editor de textos você usa no trabalho?')
    # comentário e alteração controlada
    ann = doc.createInstance('com.sun.star.text.textfield.Annotation')
    ann.Author, ann.Content = 'Orientadora', 'Conferir a data da coleta.'
    doc.getText().insertTextContent(doc.getText().getEnd(), ann, False)
    doc.RecordChanges = True
    fim = doc.getText().getEnd()
    doc.getText().insertString(fim, ' Respostas abertas foram anonimizadas.', False)
    doc.RecordChanges = False
    return doc


GRAFICOS = None


def instantaneo(doc):
    """Conteúdo que a formatação não pode mudar: texto dos parágrafos (fora do sumário gerado), notas, tabelas,
    imagens, comentários e alterações controladas."""
    pars = []
    e = doc.getText().createEnumeration()
    while e.hasMoreElements():
        o = e.nextElement()
        if o.supportsService('com.sun.star.text.TextTable'):
            pars.append('[tabela] ' + '|'.join(o.getCellByName(n).getString() for n in o.getCellNames()))
            continue
        try:
            if o.getPropertyValue('DocumentIndex') is not None:
                continue
        except Exception:
            pass
        pars.append(o.getString())
    notas = [doc.getFootnotes().getByIndex(k).getString() for k in range(doc.getFootnotes().getCount())]
    campos = doc.getTextFields().createEnumeration()
    comentarios = []
    while campos.hasMoreElements():
        f = campos.nextElement()
        if f.supportsService('com.sun.star.text.textfield.Annotation'):
            comentarios.append(f.Content)
    red = []
    try:
        re_ = doc.Redlines.createEnumeration()
        while re_.hasMoreElements():
            r = re_.nextElement()
            red.append((r.getPropertyValue('RedlineType'), r.getPropertyValue('RedlineAuthor')))
    except Exception:
        pass
    return {'paragrafos': pars, 'notas': notas, 'imagens': doc.getGraphicObjects().getCount(), 'comentarios': comentarios,
            'redlines': red}


def sem_vazios(lista):
    return [x for x in lista if x.strip()]


def formatacao(doc):
    """Propriedades que o desfazer precisa restaurar."""
    fam = doc.getStyleFamilies().getByName('ParagraphStyles')
    est = {}
    for n in ('Standard', 'Heading 1', 'Footnote', 'Quotations', 'Caption'):
        s = fam.getByName(n)
        est[n] = (s.CharFontName, round(s.CharHeight, 1), s.ParaLineSpacing.Height, s.ParaAdjust)
    pars = []
    e = doc.getText().createEnumeration()
    while e.hasMoreElements():
        o = e.nextElement()
        if o.supportsService('com.sun.star.text.Paragraph'):
            pars.append((o.ParaStyleName, o.getPropertyValue('PageDescName') or '', round(o.CharHeight, 1)))
    ps = doc.getStyleFamilies().getByName('PageStyles').getByName('Standard')
    return {'estilos': est, 'paragrafos': pars, 'pagina': (ps.TopMargin, ps.LeftMargin, ps.HeaderIsOn),
            'indices': doc.getDocumentIndexes().getCount()}


def situacoes(itens_rel):
    r = {}
    for it in itens_rel:
        r.setdefault(it.regra if it.regra != 'estrutura' else it.titulo, it.situacao)
    return r


def resumo_rel(itens_rel):
    return '; '.join(f'{it.titulo}: {it.situacao}' + (f' ({it.detalhe[:90]})' if it.situacao in (A.FALHA, A.AVISO) else '')
                     for it in itens_rel if it.situacao in (A.FALHA, A.AVISO))


def pagina_de(doc, par):
    vc = doc.getCurrentController().getViewCursor()
    vc.gotoRange(par.getStart(), False)
    return vc.getPage()


def montar_artigo(doc):
    m = Montador(doc)
    m.word('ADOÇÃO DE EDITORES LIVRES NO SERVIÇO PÚBLICO', ParaAdjust=A.CENTRO, CharWeight=150.0)
    m.word('Maria da Silva Souza', ParaAdjust=A.DIR)
    m.word('RESUMO', ParaAdjust=A.CENTRO, CharWeight=150.0)
    m.word('O artigo analisa a adoção de editores livres em três órgãos públicos entre 2023 e 2025.')
    m.word('Palavras-chave: software livre; administração pública.')
    m.word('1 INTRODUÇÃO', CharWeight=150.0)
    m.word(CORPO)
    m.word('2 RESULTADOS', CharWeight=150.0)
    m.word(CORPO)
    m.word('REFERÊNCIAS', ParaAdjust=A.CENTRO, CharWeight=150.0)
    m.word('SILVA, M. Software livre e administração pública. São Paulo: Atlas, 2019.')
    return doc


def montar_longo(doc, secoes=40, por_secao=20):
    m = Montador(doc)
    m.word('UNIVERSIDADE FEDERAL DO EXEMPLO', ParaAdjust=A.CENTRO)
    m.word('SUMÁRIO', ParaAdjust=A.CENTRO, CharWeight=150.0, quebra=True)
    for s in range(1, secoes + 1):
        m.word(f'{s} SEÇÃO PRIMÁRIA NÚMERO {s}', CharWeight=150.0, quebra=True)
        for k in range(por_secao):
            if k == por_secao // 2:
                m.word(f'{s}.1 Subseção da seção {s}', CharWeight=150.0)
            r = m.word(CORPO * 3)
            if k == 3:
                fn = doc.createInstance('com.sun.star.text.Footnote')
                doc.getText().insertTextContent(r.getEnd(), fn, False)
                fn.setString(f'Nota da seção {s}.')
    m.word('REFERÊNCIAS', ParaAdjust=A.CENTRO, CharWeight=150.0, quebra=True)
    for k in range(60):
        m.word(f'AUTOR{k:02d}, A. Título da obra número {k}. São Paulo: Editora, 20{k % 25:02d}.')
    return doc


def variantes(mo, docx, imagem):
    perfil = A.montar_perfil('trabalho')
    # 7. trabalhar numa cópia
    hash_antes = hashlib.sha256(Path(docx).read_bytes()).hexdigest()
    d = mo.abrir(docx)
    antes_c, antes_f = instantaneo(d), formatacao(d)
    copia = A.copia_sem_titulo(mo.ctx, d, extra=props(Hidden=True))
    A.aplicar(copia, A.planejar(copia, perfil))
    sc = situacoes(A.conferir(copia, perfil))
    verificar('Trabalhar numa cópia: a cópia sem título é formatada e o original fica intacto (documento e arquivo)',
              copia.getURL() == '' and sc.get('margens') == A.OK and instantaneo(d) == antes_c and formatacao(d) == antes_f
              and not d.isModified() and hashlib.sha256(Path(docx).read_bytes()).hexdigest() == hash_antes,
              f'cópia: margens {sc.get("margens")}; original modificado: {d.isModified()}')
    fechar(copia)
    fechar(d)
    # 8a. títulos por estilo, sem número: numeração automática
    d = mo.novo()
    montar_tcc(d, imagem, titulos_por_estilo=True)
    antes = instantaneo(d)
    plano = A.planejar(d, perfil)
    A.aplicar(d, plano)
    a = A.Analise(d, perfil)
    rotulos = [(el.obj.ListLabelString or '').strip() for el in a.por_tipo('titulo', zona=('textual', 'pos'))]
    s = situacoes(A.conferir(d, perfil))
    verificar('Títulos por estilo sem número: numeração automática 1, 2, 2.1, 3 e indicativo conforme, texto igual',
              plano.op['numeracao'] == 'automatica' and rotulos == ['1', '2', '2.1', '3'] and s.get('indicativo_numerico') == A.OK
              and sem_vazios(instantaneo(d)['paragrafos']) == sem_vazios(antes['paragrafos']), f'{rotulos}; {s.get("indicativo_numerico")}')
    fechar(d)
    # 8b. frente e verso
    d = mo.abrir(docx)
    pfv = A.montar_perfil('trabalho', opcoes={'frente_e_verso': True})
    feito = A.aplicar(d, A.planejar(d, pfv))
    a = A.Analise(d, pfv)
    impares = [pagina_de(d, el.obj) % 2 == 1 for el in a.por_tipo('titulo', zona='textual') if el.nivel == 1]
    st = d.getStyleFamilies().getByName('PageStyles').getByName(A.PAGINA_TEXTO)
    relfv = A.conferir(d, pfv)
    s = situacoes(relfv)
    verificar('Frente e verso: margens espelhadas, número à direita no anverso e à esquerda no verso, seções primárias em página ímpar',
              st.PageStyleLayout.value == 'MIRRORED' and not st.HeaderIsShared and all(impares) and s.get('paginacao') == A.OK
              and s.get('margens') == A.OK, f'layout {st.PageStyleLayout.value}; ímpares {impares}; {resumo_rel(relfv)[:400]}')
    fechar(d)
    # 8c. modelo da instituição
    inst = {'nome': 'Universidade do Exemplo', 'base': 'trabalho',
            'manual': {'titulo': 'Manual de normalização de trabalhos acadêmicos', 'edicao': '2025', 'url': 'https://exemplo.edu.br/manual.pdf'},
            'parametros': {'fonte_familia': 'Arial', 'recuo_paragrafo_cm': 1.5, 'ponto_apos_indicativo': True}}
    pinst = A.montar_perfil('instituicao', instituicao=inst)
    r_ind = pinst['regras']['indicativo_numerico']
    orig = A.origem(r_ind, pinst)
    d = mo.novo()
    montar_tcc(d, imagem, titulos_por_estilo=True)
    A.aplicar(d, A.planejar(d, pinst))
    a = A.Analise(d, pinst)
    rotulos = [(el.obj.ListLabelString or '').strip() for el in a.por_tipo('titulo', zona=('textual', 'pos'))]
    rel = A.conferir(d, pinst)
    s = situacoes(rel)
    camada_fonte = next(it.camada for it in rel if it.regra == 'fonte_familia')
    verificar('Modelo da instituição: Arial e ponto depois do número aplicados; relatório mostra a instituição e a divergência da norma',
              rotulos == ['1.', '2.', '2.1.', '3.'] and s.get('fonte_familia') == A.OK and s.get('indicativo_numerico') == A.OK
              and r_ind['camada'] == 'instituicao' and 'Diverge da norma' in orig and 'Universidade do Exemplo' in orig and camada_fonte == 'instituicao',
              f'{rotulos}; origem: {orig}')
    fechar(d)
    # 8d. artigo
    d = mo.novo()
    montar_artigo(d)
    part = A.montar_perfil('artigo')
    antes = instantaneo(d)
    A.aplicar(d, A.planejar(d, part))
    rel = A.conferir(d, part)
    s = situacoes(rel)
    camadas = {it.regra: it.camada for it in rel}
    verificar('Artigo: sem página nova por seção, número desde a 1ª página, aparência como preferência e estrutura conferida',
              s.get('secao_primaria_pagina') == A.NAO_SE_APLICA and s.get('paginacao') == A.OK and camadas.get('margens') == 'preferencia'
              and s.get('Elemento: Resumo') == A.OK and s.get('Elemento: Palavras-chave') == A.OK
              and sem_vazios(instantaneo(d)['paragrafos']) == sem_vazios(antes['paragrafos']) and pagina_de(d, d.getText().createEnumeration().nextElement()) == 1,
              {k: v for k, v in s.items() if v in (A.FALHA,)})
    fechar(d)
    # 9. documento longo
    d = mo.novo()
    montar_longo(d)
    t0 = time.time()
    a = A.Analise(d, perfil)
    medidas['longo_paragrafos'] = len(a.elementos)
    medidas['longo_analisar_s'] = round(time.time() - t0, 1)
    t0 = time.time()
    plano = A.planejar(d, perfil)
    medidas['longo_planejar_s'] = round(time.time() - t0, 1)
    feito = A.aplicar(d, plano)
    medidas['longo_aplicar_s'] = feito['segundos']
    t0 = time.time()
    rel = A.conferir(d, perfil)
    medidas['longo_conferir_s'] = round(time.time() - t0, 1)
    medidas['longo_paginas'] = d.getCurrentController().getPropertyValue('PageCount')
    s = situacoes(rel)
    verificar('Documento longo: formatado e conferido (tempos medidos por UNO de outro processo)',
              s.get('margens') == A.OK and s.get('entrelinhas') == A.OK and s.get('sumario') == A.OK and s.get('paginacao') == A.OK,
              f'{medidas["longo_paragrafos"]} parágrafos, {medidas["longo_paginas"]} páginas; analisar {medidas["longo_analisar_s"]} s, '
              f'planejar {medidas["longo_planejar_s"]} s, aplicar {medidas["longo_aplicar_s"]} s, conferir {medidas["longo_conferir_s"]} s'
              + ('' if all(s.get(k) == A.OK for k in ('margens', 'entrelinhas', 'sumario', 'paginacao')) else ' | ' + resumo_rel(rel)[:500]))
    um = d.getUndoManager()
    um.undo()
    verificar('Documento longo: desfazer numa ação', A.Analise(d, perfil).indice_existente is False, um.getAllRedoActionTitles()[:1])
    fechar(d)


def main():
    global GRAFICOS
    SAIDA.mkdir(parents=True, exist_ok=True)
    imagem = SAIDA / 'figura.png'
    png(imagem)
    with Motor('academico') as mo:
        GRAFICOS = mo.servico('com.sun.star.graphic.GraphicProvider')
        doc = mo.novo()
        montar_tcc(doc, imagem)
        docx, odt = salvar(doc, SAIDA / 'tcc-word.docx'), salvar(doc, SAIDA / 'tcc-word.odt')
        fechar(doc)
        perfil = A.montar_perfil('trabalho')
        for caminho in (docx, odt):
            ext = caminho.suffix[1:].upper()
            d = mo.abrir(caminho)
            a = A.Analise(d, perfil)
            c = a.contagem()
            tit = [(el.nivel, el.resumo(25)) for el in a.por_tipo('titulo', zona=('textual', 'pos'))]
            verificar(f'{ext}: títulos com número digitado identificados com o nível', [n for n, _ in tit] == [1, 1, 2, 1] and a.numeracao == 'digitado', tit)
            verificar(f'{ext}: início da parte textual em "1 INTRODUÇÃO"', a.inicio_textual is not None and a.inicio_textual.texto.startswith('1 INTRODUÇÃO'),
                      a.inicio_textual.texto[:30] if a.inicio_textual else None)
            verificar(f'{ext}: títulos sem indicativo, citação, legendas, fontes e referências identificados',
                      c.get('titulo_pre') == 3 and c.get('titulo_pos') == 2 and c.get('citacao') == 1 and c.get('legenda') == 2
                      and c.get('fonte_legenda') == 2 and c.get('referencia') == 3 and a.sumario is not None, c)
            fechar(d)
        # relatório antes, prévia, aplicação
        d = mo.abrir(docx)
        antes_conteudo = instantaneo(d)
        antes_fmt = formatacao(d)
        rel0 = A.conferir(d, perfil)
        s0 = situacoes(rel0)
        verificar('Relatório antes: margens, tamanho, entrelinhas, sumário e paginação não conformes',
                  all(s0.get(k) == A.FALHA for k in ('margens', 'fonte_tamanho', 'entrelinhas', 'sumario', 'paginacao')), resumo_rel(rel0)[:400])
        t0 = time.time()
        plano = A.planejar(d, perfil)
        medidas['planejar_s'] = round(time.time() - t0, 2)
        verificar('Prévia lista mudanças com origem e não altera o documento',
                  len(plano.mudancas) >= 10 and instantaneo(d) == antes_conteudo and formatacao(d) == antes_fmt and not d.isModified(),
                  f'{len(plano.mudancas)} mudanças; avisos: {len(plano.avisos)}')
        Path(SAIDA / 'previa.txt').write_text('\n'.join(f'[{m.grupo}] {m.descricao}' + (f'  ({A.origem(perfil["regras"][m.regra], perfil)})' if m.regra else '')
                                                         for m in plano.mudancas) + '\n\nAvisos:\n' + '\n'.join(plano.avisos), encoding='utf-8')
        feito = A.aplicar(d, plano)
        medidas['aplicar'] = feito
        depois = instantaneo(d)
        verificar('Aplicar não muda o texto: parágrafos, notas, tabela, imagem, comentário e alterações controladas preservados',
                  sem_vazios(depois['paragrafos']) == sem_vazios(antes_conteudo['paragrafos']) and depois['notas'] == antes_conteudo['notas']
                  and depois['imagens'] == antes_conteudo['imagens'] and depois['comentarios'] == antes_conteudo['comentarios']
                  and all(r in depois['redlines'] for r in antes_conteudo['redlines']),
                  f'{len(sem_vazios(depois["paragrafos"]))} parágrafos; notas {len(depois["notas"])}; redlines antes {antes_conteudo["redlines"]} depois {depois["redlines"][:4]}')
        rel1 = A.conferir(d, perfil)
        s1 = situacoes(rel1)
        esperados_ok = ('papel', 'margens', 'fonte_tamanho', 'fonte_menor', 'entrelinhas', 'entrelinhas_excecoes', 'titulos_espaco',
                        'secao_primaria_pagina', 'indicativo_numerico', 'destaque_gradativo', 'titulos_sem_indicativo', 'paginacao',
                        'notas_rodape', 'ilustracoes', 'referencias_apresentacao', 'sumario', 'fonte_familia', 'cor_texto')
        ruins = {k: s1.get(k) for k in esperados_ok if s1.get(k) != A.OK}
        verificar('Relatório depois: regras aplicáveis conformes', not ruins, f'{ruins} | {resumo_rel(rel1)[:500]}')
        verificar('Relatório depois: citação longa entre aspas apontada como aviso (o texto não é mudado)',
                  s1.get('citacao_longa') == A.AVISO, next((it.detalhe for it in rel1 if it.regra == 'citacao_longa'), ''))
        verificar('Relatório depois: conteúdo das referências marcado como não verificável',
                  s1.get('referencias_conteudo') == A.NAO_VERIFICAVEL)
        pag = next(it for it in rel1 if it.regra == 'paginacao')
        verificar('Paginação: contagem desde a folha de rosto (capa fora); a introdução, 5ª página contada, mostra 5',
                  feito.get('pagina_inicial_exibida') == 5 and [n for _, n in feito.get('recomecos', [])] == [1] and pag.situacao == A.OK,
                  f'{feito.get("recomecos")}; {pag.detalhe}')
        # desfazer e refazer
        um = d.getUndoManager()
        titulo_undo = um.getCurrentUndoActionTitle()
        um.undo()
        verificar('Desfazer: uma ação restaura estilos, parágrafos, página e retira o sumário inserido',
                  formatacao(d) == antes_fmt and sem_vazios(instantaneo(d)['paragrafos']) == sem_vazios(antes_conteudo['paragrafos']),
                  f'ação "{titulo_undo}"; dif: ' + json.dumps({k: (antes_fmt[k], formatacao(d)[k]) for k in antes_fmt if antes_fmt[k] != formatacao(d)[k]}, ensure_ascii=False)[:600])
        um.redo()
        rel2 = A.conferir(d, perfil)
        s2 = situacoes(rel2)
        dif2 = {k: s2.get(k) for k in esperados_ok if s2.get(k) != s1.get(k)}
        verificar('Refazer: formatação volta; o reinício da contagem de páginas não volta (limitação do motor) e o relatório aponta isso',
                  set(dif2) == {'paginacao'} and s2.get('paginacao') == A.FALHA,
                  f'{dif2}; {next((it.detalhe for it in rel2 if it.regra == "paginacao"), "")[:160]}')
        fechar(d)
        # salvar e reabrir (a partir de uma aplicação nova)
        d = mo.abrir(docx)
        A.aplicar(d, A.planejar(d, perfil))
        depois = instantaneo(d)
        for ext in ('docx', 'odt'):
            arq = salvar(d, SAIDA / f'tcc-formatado.{ext}')
            d2 = mo.abrir(arq)
            rel3 = A.conferir(d2, perfil)
            s3 = situacoes(rel3)
            dif = {k: s3.get(k) for k in esperados_ok if s3.get(k) != A.OK and not (ext == 'docx' and k == 'notas_rodape' and s3.get(k) == A.AVISO)}
            if dif:
                dif['detalhes'] = resumo_rel(rel3)[:700]
            c2 = instantaneo(d2)
            verificar(f'{ext.upper()} salvo e reaberto: regras continuam conformes e o texto é o mesmo',
                      not dif and sem_vazios(c2['paragrafos']) == sem_vazios(depois['paragrafos']) and c2['notas'] == depois['notas'],
                      dif or f'{len(sem_vazios(c2["paragrafos"]))} parágrafos')
            fechar(d2)
        fechar(d)
        variantes(mo, docx, imagem)
    Path(SAIDA / 'resultado.json').write_text(json.dumps({'itens': itens, 'medidas': medidas}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Formatação acadêmica: {sum(1 for x in itens if x["ok"])}/{len(itens)}')


if __name__ == '__main__':
    main()
