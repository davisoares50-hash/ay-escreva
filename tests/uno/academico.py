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
import re
import struct
import subprocess
import sys
import time
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ay_uno import Motor, RAIZ, SAIDA_TESTES, paginas_pdf, props, url, salvar, fechar  # noqa: E402

sys.path.insert(0, str(RAIZ / 'extensao' / 'ayescreva' / 'pythonpath'))
import ay_academico as A  # noqa: E402

sys.path.insert(0, str(RAIZ / 'extensao' / 'ayescreva'))
import ayescreva as AY  # noqa: E402  (caminho real de gravação do AY: _guardar)

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
            if o.getPropertyValue('DocumentIndex') is not None:
                continue
            pars.append((o.ParaStyleName, o.getPropertyValue('PageDescName') or '', o.getPropertyValue('PageNumberOffset'), round(o.CharHeight, 1),
                         {5: 0, 6: 1}.get(o.ParaAdjust, o.ParaAdjust)))
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


ESPERADOS_OK = ('papel', 'margens', 'fonte_tamanho', 'fonte_menor', 'entrelinhas', 'entrelinhas_excecoes', 'titulos_espaco',
                'secao_primaria_pagina', 'indicativo_numerico', 'destaque_gradativo', 'titulos_sem_indicativo', 'paginacao',
                'notas_rodape', 'ilustracoes', 'referencias_apresentacao', 'sumario', 'fonte_familia', 'cor_texto')


def estado_original(doc):
    """O que formatar uma cópia não pode tocar no original: texto, "modificado" e histórico de desfazer/refazer."""
    um = doc.getUndoManager()
    return {'texto': doc.getText().getString(), 'modificado': doc.isModified(), 'url': doc.getURL(),
            'historico': um.getAllUndoActionTitles(), 'refazer': um.getAllRedoActionTitles()}


def estado(doc, perfil):
    """Conteúdo, estilos, sumário, numeração exibida dos títulos e relatório de conformidade."""
    inst = instantaneo(doc)
    a = A.Analise(doc, perfil)
    numeros = {}
    for el in a.por_tipo('titulo', 'titulo_pos', zona=('textual', 'pos')):
        numeros[' '.join(el.texto.split())] = A._numero_exibido(doc, a, el)
    return {'conteudo': sem_vazios(inst['paragrafos']), 'notas': inst['notas'], 'imagens': inst['imagens'],
            'formatacao': formatacao(doc), 'sumario': [el.texto for el in a.elementos if el.tipo == 'indice'],
            'numeros': numeros, 'paginas': doc.getCurrentController().getPropertyValue('PageCount'),
            'situacoes': situacoes(A.conferir(doc, perfil, a))}


def diferencas(e1, e2, chaves=None):
    r = {}
    for k in chaves or e1:
        if e1.get(k) != e2.get(k):
            if isinstance(e1.get(k), dict):
                r[k] = {kk: (e1[k].get(kk), e2[k].get(kk)) for kk in set(e1[k]) | set(e2.get(k) or {}) if e1[k].get(kk) != (e2.get(k) or {}).get(kk)}
            else:
                r[k] = (str(e1.get(k))[:120], str(e2.get(k))[:120])
    return json.dumps(r, ensure_ascii=False, default=str)[:700]


RE_SUMARIO = re.compile(r'^(.*?)[\s.…]*?\t?\s*(\d+)$')


def sumario_numeros(linhas):
    """{'1 INTRODUÇÃO': 5, ...} a partir das entradas do sumário (texto do título + tabulação + página)."""
    r = {}
    for linha in linhas:
        if '\t' in linha:
            titulo, _, num = linha.rpartition('\t')
            if num.strip().isdigit():
                r[' '.join(titulo.split())] = int(num)
    return r


def pdf_paginas(pdf):
    saida = subprocess.run(['node', str(RAIZ / 'tools' / 'pdf-texto.mjs'), str(pdf)], capture_output=True, text=True, encoding='utf-8',
                           cwd=str(RAIZ / 'tools'), timeout=120)
    return json.loads(saida.stdout)


def numeros_no_pdf(paginas, titulos):
    """Para cada título: o número impresso no alto da página em que ele aparece (fora do sumário)."""
    r = {}
    for t in titulos:
        alvo = t.upper()
        for linhas in paginas:
            if any(l.upper() == alvo for l in linhas):
                topo = linhas[0] if linhas else ''
                r[t] = int(topo) if topo.isdigit() else None
                break
    return r


def sumario_no_pdf(paginas):
    """Entradas do sumário no PDF: 'TÍTULO ..... 5' → {'TÍTULO': 5}."""
    for linhas in paginas:
        if linhas and any(l.strip().upper() == 'SUMÁRIO' for l in linhas[:3]):
            r = {}
            for l in linhas:
                m = re.match(r'^(.+?)[\s.…]{3,}(\d+)$', l)
                if m:
                    r[' '.join(m.group(1).split()).upper()] = int(m.group(2))
            return r
    return {}


def conferir_pdf(pdf, e1, paginas_lo, rotulo):
    paginas = pdf_paginas(pdf)
    vazias = [i + 1 for i, linhas in enumerate(paginas) if not linhas]
    impressos = numeros_no_pdf(paginas, list(e1['numeros']))
    esperado = {t.upper(): n for t, n in e1['numeros'].items()}
    no_sumario = sumario_no_pdf(paginas)
    verificar(f'{rotulo}: páginas sem a página em branco automática, números no alto da página e sumário iguais aos do documento',
              not vazias and len(paginas) == paginas_lo - 1 and {t.upper(): n for t, n in impressos.items()} == esperado and no_sumario == esperado,
              f'{len(paginas)} páginas no PDF, {paginas_lo} no motor (com a página em branco automática); impressos {impressos}; sumário {no_sumario}')
    return paginas


IMPRESSORA = 'Microsoft Print to PDF'


def imprimir_pdf(doc, saida):
    """Imprime só na impressora virtual (nunca na padrão): devolve o número de páginas impressas ou None."""
    doc.setPrinter(props(Name=IMPRESSORA))
    if {p.Name: p.Value for p in doc.getPrinter()}.get('Name') != IMPRESSORA:
        return None
    if saida.exists():
        saida.unlink()
    doc.print(props(FileName=str(saida), Wait=True, CopyCount=1))
    limite = time.time() + 90
    while time.time() < limite and (not saida.exists() or saida.stat().st_size == 0):
        time.sleep(0.5)
    time.sleep(1.5)
    return paginas_pdf(saida) if saida.exists() else None


def imprimir(mo, odt, e1):
    d = mo.abrir(odt)
    n_lo = d.getCurrentController().getPropertyValue('PageCount')
    vazias_impressas = d.createInstance('com.sun.star.text.DocumentSettings').getPropertyValue('PrintEmptyPages')
    n = imprimir_pdf(d, SAIDA / 'tcc-impresso-so-frente.pdf')
    if n is None:
        verificar('Impressão só frente: impressora virtual indisponível (não executado)', True, 'Microsoft Print to PDF ausente')
    else:
        verificar('Impressão só frente: a página em branco automática não é impressa (contagem igual à do PDF)',
                  n == n_lo - 1 and vazias_impressas is False, f'{n} páginas impressas; {n_lo} no motor; imprimir páginas vazias = {vazias_impressas}')
    fechar(d)


def frente_e_verso(mo, docx):
    """Frente e verso: as páginas em branco automáticas (versos) contam e são impressas; o PDF padrão as omite."""
    d = mo.abrir(docx)
    copia = A.copia_sem_titulo(mo.ctx, d, extra=props(Hidden=True))
    fechar(d)
    pfv = A.montar_perfil('trabalho', opcoes={'frente_e_verso': True})
    A.aplicar(copia, A.planejar(copia, pfv))
    e1 = estado(copia, pfv)
    a = A.Analise(copia, pfv)
    impares = [pagina_de(copia, el.obj) % 2 == 1 for el in a.por_tipo('titulo', zona='textual') if el.nivel == 1]
    st = copia.getStyleFamilies().getByName('PageStyles').getByName(A.PAGINA_TEXTO)
    s = e1['situacoes']
    verificar('Frente e verso: margens espelhadas, número à direita no anverso e à esquerda no verso, seções primárias em página ímpar',
              st.PageStyleLayout.value == 'MIRRORED' and not st.HeaderIsShared and all(impares) and s.get('paginacao') == A.OK
              and s.get('margens') == A.OK, f'ímpares {impares}; {e1["numeros"]}')
    cum = copia.getUndoManager()
    cum.undo()
    cum.redo()
    verificar('Frente e verso: desfazer e refazer devolvem o mesmo estado', estado(copia, pfv) == e1)
    n_lo = e1['paginas']
    padrao = salvar(copia, SAIDA / 'tcc-frente-verso.pdf')
    com_brancas = SAIDA / 'tcc-frente-verso-com-brancas.pdf'
    copia.storeToURL(url(com_brancas), props(FilterName='writer_pdf_Export',
                                            FilterData=uno.Any('[]com.sun.star.beans.PropertyValue', props(IsSkipEmptyPages=False))))
    n_padrao, n_brancas = paginas_pdf(padrao), paginas_pdf(com_brancas)
    n_imp = imprimir_pdf(copia, SAIDA / 'tcc-frente-verso-impresso.pdf')
    medidas['frente_e_verso'] = {'paginas_motor': n_lo, 'pdf_padrao': n_padrao, 'pdf_com_brancas': n_brancas, 'impresso': n_imp}
    verificar('Frente e verso: impressão e PDF com páginas em branco têm todas as páginas do motor; o PDF padrão omite as brancas automáticas',
              n_brancas == n_lo and (n_imp is None or n_imp == n_lo) and n_padrao < n_lo, medidas['frente_e_verso'])
    fechar(copia)


def copia_de(mo, doc):
    """Como no aplicativo: a formatação é sempre feita numa cópia sem título (o original fica fechado aqui)."""
    c = A.copia_sem_titulo(mo.ctx, doc, extra=props(Hidden=True))
    fechar(doc)
    return c


def variantes(mo, docx, imagem):
    perfil = A.montar_perfil('trabalho')
    # títulos por estilo, sem número: numeração automática
    d = mo.novo()
    montar_tcc(d, imagem, titulos_por_estilo=True)
    d = copia_de(mo, d)
    antes = instantaneo(d)
    plano = A.planejar(d, perfil)
    A.aplicar(d, plano)
    a = A.Analise(d, perfil)
    rotulos = [(el.obj.ListLabelString or '').strip() for el in a.por_tipo('titulo', zona=('textual', 'pos'))]
    e1 = estado(d, perfil)
    um = d.getUndoManager()
    um.undo()
    um.redo()
    verificar('Títulos por estilo sem número: numeração automática 1, 2, 2.1, 3, indicativo conforme, texto igual; desfazer/refazer estável',
              plano.op['numeracao'] == 'automatica' and rotulos == ['1', '2', '2.1', '3'] and e1['situacoes'].get('indicativo_numerico') == A.OK
              and sem_vazios(instantaneo(d)['paragrafos']) == sem_vazios(antes['paragrafos']) and estado(d, perfil) == e1,
              f'{rotulos}; {e1["situacoes"].get("indicativo_numerico")}')
    fechar(d)
    # modelo da instituição
    inst = {'nome': 'Universidade do Exemplo', 'base': 'trabalho',
            'manual': {'titulo': 'Manual de normalização de trabalhos acadêmicos', 'edicao': '2025', 'url': 'https://exemplo.edu.br/manual.pdf'},
            'parametros': {'fonte_familia': 'Arial', 'recuo_paragrafo_cm': 1.5, 'ponto_apos_indicativo': True}}
    pinst = A.montar_perfil('instituicao', instituicao=inst)
    r_ind = pinst['regras']['indicativo_numerico']
    orig = A.origem(r_ind, pinst)
    d = mo.novo()
    montar_tcc(d, imagem, titulos_por_estilo=True)
    d = copia_de(mo, d)
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
    # artigo
    d = mo.novo()
    montar_artigo(d)
    d = copia_de(mo, d)
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
    # documento longo
    d = mo.novo()
    montar_longo(d)
    d = copia_de(mo, d)
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
    e1 = estado(d, perfil)
    medidas['longo_conferir_s'] = round(time.time() - t0, 1)
    medidas['longo_paginas'] = e1['paginas']
    s = e1['situacoes']
    verificar('Documento longo: formatado e conferido (tempos medidos por UNO de outro processo)',
              all(s.get(k) == A.OK for k in ('margens', 'entrelinhas', 'sumario', 'paginacao')),
              f'{medidas["longo_paragrafos"]} parágrafos, {medidas["longo_paginas"]} páginas; analisar {medidas["longo_analisar_s"]} s, '
              f'planejar {medidas["longo_planejar_s"]} s, aplicar {medidas["longo_aplicar_s"]} s, estado e relatório {medidas["longo_conferir_s"]} s')
    um = d.getUndoManager()
    um.undo()
    desfeito = A.Analise(d, perfil).indice_existente is False
    um.redo()
    verificar('Documento longo: desfazer e refazer numa ação, com o mesmo estado (sumário e numeração)',
              desfeito and estado(d, perfil) == e1, diferencas(e1, estado(d, perfil), ('sumario', 'numeros', 'situacoes')))
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
        # relatório antes e prévia: só leitura, sobre o original com uma alteração não salva (e histórico de desfazer)
        d = mo.abrir(docx)
        d.getText().insertString(d.getText().getEnd(), ' Frase acrescentada e ainda não salva.', False)
        orig = estado_original(d)
        rel0 = A.conferir(d, perfil)
        s0 = situacoes(rel0)
        verificar('Relatório antes: margens, tamanho, entrelinhas, sumário e paginação não conformes',
                  all(s0.get(k) == A.FALHA for k in ('margens', 'fonte_tamanho', 'entrelinhas', 'sumario', 'paginacao')), resumo_rel(rel0)[:400])
        t0 = time.time()
        plano0 = A.planejar(d, perfil)
        medidas['planejar_s'] = round(time.time() - t0, 2)
        verificar('Relatório e prévia são só leitura: o original não muda (texto, alteração não salva, "modificado", histórico)',
                  len(plano0.mudancas) >= 10 and estado_original(d) == orig, f'{len(plano0.mudancas)} mudanças; avisos: {len(plano0.avisos)}')
        Path(SAIDA / 'previa.txt').write_text('\n'.join(f'[{m.grupo}] {m.descricao}' + (f'  ({A.origem(perfil["regras"][m.regra], perfil)})' if m.regra else '')
                                                         for m in plano0.mudancas) + '\n\nAvisos:\n' + '\n'.join(plano0.avisos), encoding='utf-8')
        try:
            A.aplicar(d, plano0)
            recusou = False
        except A.HistoricoEmRisco:
            recusou = True
        verificar('O motor recusa formatar um documento com histórico de desfazer (o motor apagaria o histórico)',
                  recusou and estado_original(d) == orig)
        # formatar a cópia
        copia = A.copia_sem_titulo(mo.ctx, d, extra=props(Hidden=True))
        cum = copia.getUndoManager()
        verificar('Cópia sem título: inclui a alteração não salva do original e nasce sem histórico',
                  copia.getURL() == '' and 'Frase acrescentada e ainda não salva' in copia.getText().getString()
                  and not cum.isUndoPossible() and not cum.isRedoPossible())
        antes_conteudo = instantaneo(copia)
        e0 = estado(copia, perfil)
        feito = A.aplicar(copia, A.planejar(copia, perfil))
        medidas['aplicar'] = feito
        e1 = estado(copia, perfil)
        depois = instantaneo(copia)
        verificar('Original intacto depois de formatar a cópia (texto, alteração não salva, "modificado" e histórico)', estado_original(d) == orig,
                  f'histórico do original: {orig["historico"]}')
        verificar('Aplicar não muda o texto: parágrafos, notas, tabela, imagem, comentário e alterações controladas preservados',
                  sem_vazios(depois['paragrafos']) == sem_vazios(antes_conteudo['paragrafos']) and depois['notas'] == antes_conteudo['notas']
                  and depois['imagens'] == antes_conteudo['imagens'] and depois['comentarios'] == antes_conteudo['comentarios']
                  and all(r in depois['redlines'] for r in antes_conteudo['redlines']),
                  f'{len(sem_vazios(depois["paragrafos"]))} parágrafos; notas {len(depois["notas"])}; redlines {depois["redlines"][:3]}')
        s1 = e1['situacoes']
        ruins = {k: s1.get(k) for k in ESPERADOS_OK if s1.get(k) != A.OK}
        verificar('Relatório depois: regras aplicáveis conformes', not ruins, f'{ruins}')
        alin = [p[4] for p in e1['formatacao']['paragrafos'][:9]]
        verificar('Capa e folha de rosto mantêm o alinhamento (centralizado), inclusive o parágrafo que recomeça a contagem',
                  alin == [A.CENTRO] * 7 + [A.ESQ, A.CENTRO], alin)
        verificar('Relatório depois: citação longa entre aspas apontada como aviso (o texto não é mudado)', s1.get('citacao_longa') == A.AVISO)
        verificar('Relatório depois: conteúdo das referências marcado como não avaliado', s1.get('referencias_conteudo') == A.NAO_VERIFICAVEL)
        rel1 = A.conferir(copia, perfil)
        cab = A.cabecalho_relatorio(perfil, rel1)
        grupos = {cid: len(lista) for cid, _, lista in A.agrupar(rel1)}
        org_margens = next(it.origem for it in rel1 if it.regra == 'margens')
        org_fonte = next(it.origem for it in rel1 if it.regra == 'fonte_familia')
        verificar('Relatório distingue regras conferidas, preferências e itens não avaliados, sem afirmar conformidade completa',
                  'NÃO atesta conformidade completa' in cab and grupos['verificada'] >= 15 and grupos['preferencia'] >= 4
                  and grupos['nao_avaliado'] >= 3 and 'texto oficial não consultado' in org_margens and 'guia da PUC-SP (2025)' in org_margens
                  and org_fonte.startswith('Preferência'), f'{grupos}; margens: {org_margens}')
        rel_doc = A.documento_relatorio(mo.desktop, rel1, perfil, 'TCC de teste', extra=props(Hidden=True))
        texto_rel = rel_doc.getText().getString()
        verificar('Documento do relatório: aviso de que não atesta conformidade completa e uma seção por grupo',
                  'NÃO atesta conformidade completa' in texto_rel and all(r in texto_rel for _, r, l in A.agrupar(rel1) if l)
                  and rel_doc.getTextTables().getCount() == sum(1 for _, _, l in A.agrupar(rel1) if l), f'{rel_doc.getTextTables().getCount()} tabelas')
        fechar(rel_doc)
        verificar('Paginação: contagem desde a folha de rosto (capa fora); a introdução, 5ª página contada, mostra 5; sumário com os mesmos números',
                  e1['numeros'].get('1 INTRODUÇÃO') == 5 and [n for _, n in feito.get('recomecos', [])] == [1]
                  and sumario_numeros(e1['sumario']) == {k: v for k, v in e1['numeros'].items()},
                  f'{e1["numeros"]}; sumário {sumario_numeros(e1["sumario"])}')
        # desfazer e refazer (duas vezes)
        titulo_undo = cum.getCurrentUndoActionTitle()
        cum.undo()
        eu = estado(copia, perfil)
        verificar('Desfazer: uma ação devolve a cópia exatamente ao estado de antes (conteúdo, estilos, sumário, numeração, relatório)',
                  eu == e0, f'ação "{titulo_undo}"; diferenças: {diferencas(e0, eu)}')
        cum.redo()
        er = estado(copia, perfil)
        verificar('Refazer: a formatação volta inteira, inclusive o recomeço da contagem (conteúdo, estilos, sumário, numeração, relatório)',
                  er == e1, f'diferenças: {diferencas(e1, er)}')
        cum.undo()
        cum.redo()
        er2 = estado(copia, perfil)
        verificar('Segundo ciclo desfazer/refazer: mesmo estado', er2 == e1, f'diferenças: {diferencas(e1, er2)}')
        # salvar pelo caminho do AY ("Salvar uma cópia"): DOCX com o recomeço direto no parágrafo, ODT com o estilo
        historico, mod = cum.getAllUndoActionTitles(), copia.isModified()
        arquivos = {}
        for ext, filtro in (('docx', 'MS Word 2007 XML'), ('odt', 'writer8')):
            arq = SAIDA / f'tcc-formatado.{ext}'
            AY._guardar(copia, url(arq), filtro, como=False)
            arquivos[ext] = arq
            es = estado(copia, perfil)
            verificar(f'Salvar uma cópia em {ext.upper()} pelo AY: histórico, "modificado" e estado da cópia inalterados',
                      cum.getAllUndoActionTitles() == historico and copia.isModified() == mod and es == e1, diferencas(e1, es))
        with zipfile.ZipFile(arquivos['docx']) as z:
            xml = z.read('word/document.xml').decode('utf-8')
        verificar('DOCX gravado com o recomeço da contagem na seção (pgNumType start=1)', 'w:start="1"' in xml,
                  re.findall(r'<w:pgNumType[^>]*/>', xml))
        fechar(copia)
        fechar(d)
        # fechar, reabrir, exportar PDF
        for ext, arq in arquivos.items():
            d2 = mo.abrir(arq)
            e2 = estado(d2, perfil)
            dif = {k: e2['situacoes'].get(k) for k in ESPERADOS_OK if e2['situacoes'].get(k) != A.OK}
            aviso_docx = ext == 'docx' and dif == {'notas_rodape': A.AVISO}
            verificar(f'{ext.upper()} reaberto: conteúdo, notas, sumário e numeração iguais aos da cópia formatada; regras conformes'
                      + (' (filete das notas: aviso conhecido do DOCX)' if aviso_docx else ''),
                      e2['conteudo'] == e1['conteudo'] and e2['notas'] == e1['notas'] and e2['sumario'] == e1['sumario']
                      and e2['numeros'] == e1['numeros'] and (not dif or aviso_docx), f'{dif}; {diferencas(e1, e2, ("conteudo", "notas", "sumario", "numeros"))}')
            pdf = salvar(d2, SAIDA / f'tcc-formatado-{ext}.pdf')
            paginas_lo = d2.getCurrentController().getPropertyValue('PageCount')
            conferir_pdf(pdf, e1, paginas_lo, f'PDF exportado do {ext.upper()}')
            fechar(d2)
        imprimir(mo, arquivos['odt'], e1)
        frente_e_verso(mo, docx)
        variantes(mo, docx, imagem)
    Path(SAIDA / 'resultado.json').write_text(json.dumps({'itens': itens, 'medidas': medidas}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Formatação acadêmica: {sum(1 for x in itens if x["ok"])}/{len(itens)}')


if __name__ == '__main__':
    main()
