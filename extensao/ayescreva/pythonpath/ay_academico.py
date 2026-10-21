# -*- coding: utf-8 -*-
"""Formatação de trabalhos acadêmicos (entrega B): analisar, planejar, aplicar e conferir.

- Regras, camadas (norma, instituição, preferência) e parâmetros: dados/perfis_formatacao.json.
- Normas, edições e fontes consultadas: dados/normas.json (docs/NORMAS.md).
- O texto não muda: nenhuma palavra é inserida, apagada ou trocada. Títulos com número digitado mantêm o número;
  maiúsculas dos títulos são só de exibição. Exceção declarada: o parágrafo vazio que recebe o sumário automático.
- Tudo roda na thread principal e "aplicar" é uma única ação de desfazer.
SPDX-License-Identifier: MPL-2.0
"""
import copy
import json
import os
import re
import time

import uno

DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'dados')
_CACHE = {}

# alinhamento (com.sun.star.style.ParagraphAdjust) e unidades (1/100 mm)
ESQ, DIR, JUST, CENTRO = 0, 1, 2, 3
ALINHAMENTOS = {'esquerda': ESQ, 'direita': DIR, 'justificado': JUST, 'centralizado': CENTRO}
NOME_ALINHAMENTO = {v: k for k, v in ALINHAMENTOS.items()}
ESTILO_PRE = 'Título pré-textual'
ESTILO_POS = 'Título pós-textual'
ESTILO_REF = 'Referência'
ESTILO_FONTE = 'Fonte da ilustração'
ESTILO_OBJETO = 'Ilustração'
PAGINA_PRE = 'AY Pré-textual'
PAGINA_TEXTO = 'AY Textual'
PAGINA_ANVERSO = 'AY Seção (anverso)'
ESTILOS_CITACAO = ('Quotations', 'Quote', 'Citação', 'Citações', 'Intense Quote')
ESTILOS_LEGENDA = ('Caption', 'Figure', 'Table', 'Illustration', 'Drawing', 'Text')


def cm(v):
    return int(round(v * 1000))


def pt(v):
    return int(round(v * 2540 / 72))


def _ler(nome):
    if nome not in _CACHE:
        with open(os.path.join(DADOS, nome), encoding='utf-8') as f:
            _CACHE[nome] = json.load(f)
    return _CACHE[nome]


def normas():
    return _ler('normas.json')


def dados_perfis():
    return _ler('perfis_formatacao.json')


def rotulo_norma(nid):
    n = normas()['normas'].get(nid) if nid else None
    return n['rotulo'] if n else ''


def texto_fontes(ids):
    fs = normas()['fontes']
    return '; '.join(fs[i]['nome'] for i in ids if i in fs)


def _norm(t):
    return ' '.join(t.replace(' ', ' ').split()).strip().rstrip(':').strip().upper()


def _mesclar(base, extra):
    r = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(r.get(k), dict):
            r[k] = _mesclar(r[k], v)
        else:
            r[k] = copy.deepcopy(v)
    return r


# parâmetro → regras que ele alimenta (para marcar a camada quando a instituição ou o usuário troca o valor)
PARAM_REGRAS = {
    'papel': ['papel'], 'margens_cm': ['margens'], 'fonte_tamanho': ['fonte_tamanho'],
    'fonte_menor_tamanho': ['fonte_menor_tamanho'], 'fonte_familia': ['fonte_familia'],
    'entrelinhas': ['entrelinhas'], 'recuo_paragrafo_cm': ['recuo_paragrafo'], 'alinhamento': ['alinhamento'],
    'espaco_titulo_pt': ['titulos_espaco'], 'secao_primaria_pagina_nova': ['secao_primaria_pagina'],
    'paginacao': ['paginacao'], 'citacao_recuo_cm': ['citacao_longa'], 'nota_filete_cm': ['notas_rodape'],
    'ponto_apos_indicativo': ['indicativo_numerico'], 'destaques': ['destaques_escolhidos'],
    'referencias_espaco_depois_pt': ['referencias_apresentacao'], 'ilustracao_alinhamento': ['ilustracoes'],
}


def montar_perfil(pid, instituicao=None, opcoes=None):
    """Perfil pronto para uso: parâmetros (base + perfil + instituição + escolhas do usuário) e regras com camada.

    instituicao: {'nome', 'manual': {'titulo', 'edicao', 'url', 'arquivo'}, 'base': id do perfil, 'parametros'}.
    opcoes: escolhas feitas no assistente (preferências do usuário)."""
    d = dados_perfis()
    if pid == 'instituicao':
        if not instituicao:
            raise ValueError('modelo da instituição não definido')
        base_id = instituicao.get('base') or 'trabalho'
    else:
        base_id = pid
    p = d['perfis'][base_id]
    params = _mesclar(d['parametros_base'], p.get('parametros'))
    regras = {r['id']: dict(r) for r in d['regras_base']}
    if p.get('camada_aparencia') == 'preferencia':
        for r in regras.values():
            if r['camada'] == 'norma' and r['norma'] == 'NBR14724':
                r['camada'] = 'preferencia'
                r['nota'] = (f'Regra geral da NBR 14724:2024 usada como preferência: a {rotulo_norma(p["norma"])} '
                             'não foi conferida para este ponto.' if base_id == 'relatorio' else
                             'Regra geral da NBR 14724:2024 usada como preferência: a aparência do artigo segue o periódico.')
    if instituicao and pid == 'instituicao':
        for k, v in (instituicao.get('parametros') or {}).items():
            antes = params.get(k)
            params[k] = _mesclar(antes, v) if isinstance(v, dict) and isinstance(antes, dict) else v
            for rid in PARAM_REGRAS.get(k, []):
                r = regras[rid]
                if r['camada'] == 'norma' and antes != params[k]:
                    r['diverge_da_norma'] = True
                r['camada'] = 'instituicao'
    for k, v in (opcoes or {}).items():
        if k not in params or params[k] == v:
            continue
        params[k] = v
        for rid in PARAM_REGRAS.get(k, []):
            r = regras[rid]
            if r['camada'] == 'norma':
                r['diverge_da_norma'] = True
            if r['camada'] != 'instituicao':
                r['camada'] = 'preferencia'
    return {'id': pid, 'base': base_id, 'nome': (instituicao or {}).get('nome') if pid == 'instituicao' else p['nome'],
            'norma': p['norma'], 'descricao': p['descricao'], 'estrutura': p['estrutura'],
            'fontes_estrutura': p.get('fontes_estrutura', []), 'parametros': params, 'regras': regras,
            'instituicao': instituicao if pid == 'instituicao' else None, 'artigo': base_id == 'artigo'}


def origem(regra, perfil):
    """Texto curto de onde a regra vem, como aparece na prévia e no relatório."""
    if regra['camada'] == 'instituicao':
        inst = perfil.get('instituicao') or {}
        man = inst.get('manual') or {}
        t = 'Instituição: ' + (inst.get('nome') or 'modelo da instituição')
        if man.get('titulo'):
            t += f' — {man["titulo"]}' + (f' ({man["edicao"]})' if man.get('edicao') else '')
        if regra.get('diverge_da_norma'):
            t += f'. Diverge da norma ({rotulo_norma(regra["norma"]) or "regra geral"})'
        return t
    if regra['camada'] == 'preferencia':
        t = 'Preferência'
        if regra.get('diverge_da_norma'):
            t += f' do usuário, diferente da norma ({rotulo_norma(regra["norma"])})'
        return t + (f'. {regra["nota"]}' if regra.get('nota') else '')
    t = 'Norma: ' + rotulo_norma(regra['norma'])
    if regra.get('fontes'):
        t += ', conforme ' + ', '.join(normas()['fontes'][f]['nome'].split('.')[0] for f in regra['fontes'])
    return t


# ---------------------------------------------------------------- leitura do documento
def _prop(obj, nome, padrao=None):
    try:
        return obj.getPropertyValue(nome)
    except Exception:
        return padrao


def _estado_direto(obj, nome):
    try:
        return obj.getPropertyState(nome).value == 'DIRECT_VALUE'
    except Exception:
        return False


def _trechos(par):
    """Trechos de texto (não vazios) do parágrafo."""
    r = []
    try:
        e = par.createEnumeration()
        while e.hasMoreElements():
            por = e.nextElement()
            if por.TextPortionType == 'Text' and por.getString().strip():
                r.append(por)
    except Exception:
        pass
    return r


def valores_trechos(par, nome):
    """Valores efetivos de uma propriedade nos trechos do parágrafo (no DOCX a formatação fica nos trechos)."""
    vals = set()
    for por in _trechos(par):
        v = _prop(por, nome)
        v = getattr(v, 'value', v)
        if isinstance(v, float):
            v = round(v, 1)
        if isinstance(v, str):
            v = v.split(';')[0]
        vals.add(v)
    if not vals:
        v = _prop(par, nome)
        vals.add(round(v, 1) if isinstance(v, float) else getattr(v, 'value', v))
    return vals


def _negrito(par):
    if (_prop(par, 'CharWeight', 100.0) or 100.0) >= 150.0:
        return True
    pesos = valores_trechos(par, 'CharWeight')
    return bool(pesos) and all((w or 0) >= 150.0 for w in pesos)


def _tem_objeto(par):
    """Parágrafo com imagem, objeto ou desenho (ancorado no parágrafo ou como caractere)."""
    try:
        e = par.createContentEnumeration('com.sun.star.text.TextContent')
        while e.hasMoreElements():
            o = e.nextElement()
            if any(o.supportsService(s) for s in ('com.sun.star.text.TextGraphicObject', 'com.sun.star.text.TextEmbeddedObject',
                                                    'com.sun.star.drawing.Shape')):
                return True
    except Exception:
        pass
    try:
        e = par.createEnumeration()
        while e.hasMoreElements():
            por = e.nextElement()
            if por.TextPortionType == 'Frame':
                return True
    except Exception:
        pass
    return False


class Elemento:
    __slots__ = ('obj', 'i', 'texto', 'estilo', 'tipo', 'nivel', 'numero', 'separador', 'zona', 'objeto', 'negrito',
                 'recuo_esq', 'rotulo')

    def __init__(self, obj, i):
        self.obj, self.i = obj, i
        self.texto = self.estilo = self.tipo = self.numero = self.separador = self.zona = self.rotulo = ''
        self.nivel = 0
        self.objeto = self.negrito = False
        self.recuo_esq = 0

    def resumo(self, n=60):
        t = ' '.join(self.texto.split())
        return t if len(t) <= n else t[:n - 1] + '…'


RE_DIGITADO = re.compile(r'^(\d{1,2}(?:\.\d{1,2}){0,5})(\s*[.\-–—)]?)\s+(\S.*)$')
RE_FONTE = re.compile(r'^(Fonte|Fontes|Nota|Notas|Legenda)\s*:')
RE_SUMARIO_MANUAL = re.compile(r'(\.{3,}|…{2,}|\t)\s*\d+\s*$')
RE_APENDICE = re.compile(r'^(APÊNDICE|ANEXO)\s+[A-Z]{1,2}\s*[–—-]\s*\S')


def _re_legenda():
    if 're_legenda' not in _CACHE:
        nomes = '|'.join(re.escape(x) for x in dados_perfis()['designativas'])
        _CACHE['re_legenda'] = re.compile(r'^(%s)\s+(\d+)\s*([–—:\-])\s*\S' % nomes)
    return _CACHE['re_legenda']


class Analise:
    """Partes do documento identificadas (só leitura)."""

    def __init__(self, doc, perfil):
        self.doc, self.perfil = doc, perfil
        self.elementos = []
        self.inicio_textual = None
        self.inicio_pos = None
        self.sumario = None
        self.sumario_manual = False
        self.indice_existente = False
        self.numeracao = 'nenhum'          # 'digitado', 'auto', 'misto' ou 'nenhum'
        self.avisos = []
        t0 = time.time()
        self._ler()
        self._classificar()
        self.segundos = time.time() - t0

    def _ler(self):
        e = self.doc.getText().createEnumeration()
        i = 0
        while e.hasMoreElements():
            o = e.nextElement()
            el = Elemento(o, i)
            if o.supportsService('com.sun.star.text.TextTable'):
                el.tipo = 'tabela'
                el.texto = o.getName()
            elif _prop(o, 'DocumentIndex') is not None:
                el.tipo = 'indice'          # entrada de sumário ou índice gerado: não é conteúdo do autor
                el.texto = o.getString()
            else:
                el.texto = o.getString()
                el.estilo = _prop(o, 'ParaStyleName', '') or ''
                el.nivel = _prop(o, 'OutlineLevel', 0) or 0
                el.rotulo = _prop(o, 'ListLabelString', '') or ''
                el.negrito = _negrito(o)
                el.recuo_esq = _prop(o, 'ParaLeftMargin', 0) or 0
                el.objeto = _tem_objeto(o)
            self.elementos.append(el)
            i += 1
        try:
            idx = self.doc.getDocumentIndexes()
            for k in range(idx.getCount()):
                if idx.getByIndex(k).supportsService('com.sun.star.text.ContentIndex'):
                    self.indice_existente = True
        except Exception:
            pass

    def _classificar(self):
        d = dados_perfis()['titulos_sem_indicativo']
        pre, pos = set(d['pre_textuais']), set(d['pos_textuais'])
        rel = _re_legenda()
        els = self.elementos
        for el in els:
            if el.tipo in ('tabela', 'indice'):
                continue
            t = el.texto.strip()
            if not t:
                el.tipo = 'objeto' if el.objeto else 'vazio'
                continue
            n = _norm(t)
            m_est = re.match(r'^Heading (\d+)$', el.estilo)
            nivel_estilo = int(m_est.group(1)) if m_est else 0
            if not nivel_estilo and el.nivel and el.estilo not in (ESTILO_PRE, ESTILO_POS):
                nivel_estilo = el.nivel
            if len(t) <= 150 and (n in pre or n in pos or RE_APENDICE.match(n)) and not RE_DIGITADO.match(t):
                el.tipo = 'titulo_pre' if n in pre else 'titulo_pos'
                continue
            if el.estilo in (ESTILO_PRE, ESTILO_POS):
                el.tipo = 'titulo_pre' if el.estilo == ESTILO_PRE else 'titulo_pos'
                continue
            m = RE_DIGITADO.match(t) if len(t) <= 200 else None
            if m:
                letras = [c for c in m.group(3) if c.isalpha()]
                titulo_ok = m.group(3)[0].isupper() and not t.endswith(('.', ';', ','))
                if titulo_ok and (nivel_estilo or el.negrito or (letras and all(c.isupper() for c in letras))):
                    el.tipo, el.numero = 'titulo', 'digitado'
                    el.nivel = min(nivel_estilo or len(m.group(1).split('.')), 10) if nivel_estilo else len(m.group(1).split('.'))
                    el.separador = m.group(2).strip()
                    continue
            if nivel_estilo:
                el.tipo, el.nivel = 'titulo', nivel_estilo
                el.numero = 'auto' if el.rotulo.strip() else 'nenhum'
                continue
            if rel.match(t) and len(t) <= 400:
                el.tipo = 'legenda'
                continue
            if RE_FONTE.match(t) and len(t) <= 600:
                el.tipo = 'fonte_legenda'
                continue
            if el.estilo in ESTILOS_CITACAO or el.recuo_esq >= cm(3.0):
                el.tipo = 'citacao'
                continue
            el.tipo = 'objeto' if el.objeto and len(t) < 3 else 'texto'
        # início da parte textual
        titulos1 = [el for el in els if el.tipo == 'titulo' and el.nivel == 1]
        for k, el in enumerate(els):
            if el.tipo == 'titulo_pre' and _norm(el.texto) == 'SUMÁRIO':
                self.sumario = el
                for nxt in els[k + 1:]:
                    if nxt.tipo in ('titulo', 'titulo_pre', 'titulo_pos'):
                        break
                    if nxt.tipo == 'texto' and RE_SUMARIO_MANUAL.search(nxt.texto.rstrip()):
                        self.sumario_manual = True
                break
        if self.perfil['artigo']:
            self.inicio_textual = els[0] if els else None
        else:
            cand = [el for el in titulos1 if self.sumario is None or el.i > self.sumario.i]
            preferidos = [el for el in cand if el.numero in ('digitado', 'auto') or _norm(el.texto).endswith('INTRODUÇÃO')]
            self.inicio_textual = (preferidos or cand or [None])[0]
        ini = self.inicio_textual.i if self.inicio_textual else len(els)
        for el in els:
            if el.i >= ini and el.tipo == 'titulo_pos' and self.inicio_pos is None:
                self.inicio_pos = el.i
        fim_texto = self.inicio_pos if self.inicio_pos is not None else len(els)
        em_ref = False
        for el in els:
            if self.perfil['artigo']:
                el.zona = 'pos' if self.inicio_pos is not None and el.i >= self.inicio_pos else 'textual'
            else:
                el.zona = 'pre' if el.i < ini else ('textual' if el.i < fim_texto else 'pos')
            if el.tipo == 'titulo_pos':
                em_ref = _norm(el.texto) == 'REFERÊNCIAS'
            elif el.tipo in ('titulo', 'titulo_pre'):
                em_ref = False
            elif em_ref and el.tipo in ('texto', 'citacao'):
                el.tipo = 'referencia'
            if el.zona == 'pre' and el.tipo in ('texto', 'citacao', 'titulo'):
                el.tipo = 'pre_texto' if el.tipo != 'titulo' else el.tipo
        nums = {el.numero for el in els if el.tipo == 'titulo' and el.zona != 'pre'}
        nums.discard('')
        if nums == {'digitado'}:
            self.numeracao = 'digitado'
        elif nums == {'auto'}:
            self.numeracao = 'auto'
        elif 'digitado' in nums:
            self.numeracao = 'misto'
        else:
            self.numeracao = 'nenhum'

    def por_tipo(self, *tipos, zona=None):
        return [el for el in self.elementos if el.tipo in tipos and (zona is None or el.zona in (zona if isinstance(zona, tuple) else (zona,)))]

    def contagem(self):
        c = {}
        for el in self.elementos:
            c[el.tipo] = c.get(el.tipo, 0) + 1
        return c


# ---------------------------------------------------------------- estilos
def _familia(doc, nome):
    return doc.getStyleFamilies().getByName(nome)


def _estilo_par(doc, nome, pai='Standard', criar=True):
    fam = _familia(doc, 'ParagraphStyles')
    if fam.hasByName(nome):
        return fam.getByName(nome)
    if not criar:
        return None
    s = doc.createInstance('com.sun.star.style.ParagraphStyle')
    fam.insertByName(nome, s)
    s.setParentStyle(pai)
    return fam.getByName(nome)


def _corpo_nome(doc):
    fam = _familia(doc, 'ParagraphStyles')
    for n in ('Text body', 'Body Text'):
        if fam.hasByName(n):
            return n
    return 'Text body'


def _entrelinhas(prop):
    ls = uno.createUnoStruct('com.sun.star.style.LineSpacing')
    ls.Mode, ls.Height = 0, int(round(prop * 100))
    return ls


def _quebra(nome):
    return uno.Enum('com.sun.star.style.BreakType', nome)


def _postura(italico):
    return uno.Enum('com.sun.star.awt.FontSlant', 'ITALIC' if italico else 'NONE')


def _definir(obj, valores):
    for k, v in valores.items():
        obj.setPropertyValue(k, v)


def _fonte(params):
    return {'CharFontName': params['fonte_familia'], 'CharFontStyleName': '', 'CharFontFamily': 0, 'CharFontPitch': 0}


def valores_estilos(doc, params):
    """Valores de cada estilo de parágrafo que a regra define (para planejar, aplicar e conferir)."""
    p = params
    f = _fonte(p)
    menor = float(p['fonte_menor_tamanho'])
    esp_tit = pt(p['espaco_titulo_pt'])
    al_ilu = ALINHAMENTOS.get(p['ilustracao_alinhamento'], CENTRO)
    v = {
        'Standard': dict(f, CharHeight=float(p['fonte_tamanho'])),
        _corpo_nome(doc): dict(f, CharHeight=float(p['fonte_tamanho']), ParaLineSpacing=_entrelinhas(p['entrelinhas']),
                               ParaAdjust=ALINHAMENTOS.get(p['alinhamento'], JUST), ParaLastLineAdjust=ESQ,
                               ParaFirstLineIndent=cm(p['recuo_paragrafo_cm']), ParaLeftMargin=0, ParaRightMargin=0,
                               ParaTopMargin=0, ParaBottomMargin=0, CharColor=-1),
        'Quotations': dict(f, CharHeight=menor, ParaLineSpacing=_entrelinhas(1.0), ParaAdjust=JUST, ParaLastLineAdjust=ESQ,
                           ParaLeftMargin=cm(p['citacao_recuo_cm']), ParaRightMargin=0, ParaFirstLineIndent=0,
                           ParaTopMargin=pt(12), ParaBottomMargin=pt(12), CharColor=-1),
        'Footnote': dict(f, CharHeight=menor, ParaLineSpacing=_entrelinhas(1.0), ParaAdjust=JUST, ParaLastLineAdjust=ESQ),
        'Caption': dict(f, CharHeight=menor, ParaLineSpacing=_entrelinhas(1.0), ParaAdjust=al_ilu, ParaFirstLineIndent=0,
                        ParaLeftMargin=0, ParaTopMargin=pt(6), ParaBottomMargin=pt(3), CharPosture=_postura(False), CharColor=-1),
        ESTILO_FONTE: dict(f, CharHeight=menor, ParaLineSpacing=_entrelinhas(1.0), ParaAdjust=al_ilu, ParaFirstLineIndent=0,
                           ParaLeftMargin=0, ParaTopMargin=pt(3), ParaBottomMargin=pt(6), CharColor=-1),
        ESTILO_OBJETO: dict(ParaAdjust=al_ilu, ParaFirstLineIndent=0, ParaLeftMargin=0, ParaRightMargin=0,
                            ParaLineSpacing=_entrelinhas(1.0), ParaTopMargin=0, ParaBottomMargin=0, ParaKeepTogether=True),
        ESTILO_REF: dict(f, CharHeight=float(p['fonte_tamanho']), ParaLineSpacing=_entrelinhas(1.0), ParaAdjust=ESQ,
                         ParaFirstLineIndent=0, ParaLeftMargin=0, ParaTopMargin=0,
                         ParaBottomMargin=pt(p['referencias_espaco_depois_pt']), CharColor=-1),
        'Header': dict(f, CharHeight=menor),
        'Contents Heading': dict(f, CharHeight=float(p['fonte_tamanho']), CharWeight=150.0, CharCaseMap=1, ParaAdjust=CENTRO),
    }
    sem_ind = dict(f, CharHeight=float(p['fonte_tamanho']), CharWeight=150.0, CharCaseMap=1, CharPosture=_postura(False),
                   ParaAdjust=CENTRO, ParaFirstLineIndent=0, ParaLeftMargin=0, ParaTopMargin=0, ParaBottomMargin=esp_tit,
                   ParaLineSpacing=_entrelinhas(p['entrelinhas']), CharColor=-1)
    v[ESTILO_PRE] = dict(sem_ind, OutlineLevel=0)
    v[ESTILO_POS] = dict(sem_ind, OutlineLevel=1)
    for dq in p['destaques'][:5]:
        n = dq['nivel']
        h = dict(f, CharHeight=float(p['fonte_tamanho']), CharWeight=150.0 if dq['negrito'] else 100.0,
                 CharPosture=_postura(dq['italico']), CharCaseMap=1 if dq['maiusculas'] else 0, CharColor=-1,
                 ParaAdjust=ESQ, ParaFirstLineIndent=0, ParaLeftMargin=0, ParaTopMargin=esp_tit, ParaBottomMargin=esp_tit,
                 ParaLineSpacing=_entrelinhas(p['entrelinhas']), ParaKeepTogether=True, ParaSplit=False)
        v[f'Heading {n}'] = h
        v[f'Contents {n}'] = dict(f, CharHeight=float(p['fonte_tamanho']), CharWeight=h['CharWeight'],
                                  CharPosture=h['CharPosture'], CharCaseMap=h['CharCaseMap'])
    return v


def _igual(a, b):
    if hasattr(a, 'Mode') and hasattr(b, 'Mode'):
        return a.Mode == b.Mode and a.Height == b.Height
    if hasattr(a, 'value') and hasattr(b, 'value'):
        return a.value == b.value
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) < 0.05
        except Exception:
            return False
    return a == b


def _mostrar(nome, v):
    if hasattr(v, 'Mode'):
        return f'entrelinhas {v.Height / 100:.2g}'.replace('.', ',') if v.Mode == 0 else f'entrelinhas fixas {v.Height / 1000:.2f} cm'
    if hasattr(v, 'value'):
        return {'ITALIC': 'itálico', 'NONE': 'sem itálico'}.get(v.value, v.value)
    if nome == 'CharWeight':
        return 'negrito' if v >= 150 else 'sem negrito'
    if nome == 'CharCaseMap':
        return 'maiúsculas' if v == 1 else 'como digitado'
    if nome in ('ParaAdjust', 'ParaLastLineAdjust'):
        return NOME_ALINHAMENTO.get(v, str(v))
    if nome == 'CharHeight':
        return f'{v:g} pt'
    if nome.startswith('Para') and isinstance(v, int):
        return f'{v / 1000:.2f} cm'.replace('.', ',')
    if nome == 'CharColor':
        return 'cor automática' if v == -1 else f'cor #{v:06x}'
    return str(v)


NOMES_PROP = {'CharFontName': 'fonte', 'CharHeight': 'tamanho', 'ParaLineSpacing': 'entrelinhas', 'ParaAdjust': 'alinhamento',
              'ParaFirstLineIndent': 'recuo da 1ª linha', 'ParaLeftMargin': 'recuo à esquerda', 'ParaTopMargin': 'espaço antes',
              'ParaBottomMargin': 'espaço depois', 'CharWeight': 'negrito', 'CharPosture': 'itálico', 'CharCaseMap': 'maiúsculas',
              'CharColor': 'cor', 'OutlineLevel': 'nível no sumário'}
NOMES_ESTILO = {'Standard': 'Padrão', 'Text body': 'Corpo do texto', 'Body Text': 'Corpo do texto', 'Quotations': 'Citação',
                'Footnote': 'Nota de rodapé', 'Caption': 'Legenda', 'Header': 'Cabeçalho (número de página)',
                'Contents Heading': 'Título do sumário'}


def nome_estilo(n):
    if n.startswith('Heading '):
        return 'Título ' + n.split()[1]
    if n.startswith('Contents '):
        return 'Sumário ' + n.split()[1]
    return NOMES_ESTILO.get(n, n)


# ---------------------------------------------------------------- planejar
class Mudanca:
    __slots__ = ('grupo', 'descricao', 'regra', 'detalhe')

    def __init__(self, grupo, descricao, regra=None, detalhe=''):
        self.grupo, self.descricao, self.regra, self.detalhe = grupo, descricao, regra, detalhe


class Plano:
    def __init__(self, doc, perfil, analise, opcoes_aplicacao):
        self.doc, self.perfil, self.analise = doc, perfil, analise
        self.op = opcoes_aplicacao
        self.mudancas = []
        self.avisos = []

    def add(self, *a, **k):
        self.mudancas.append(Mudanca(*a, **k))


def _estilo_pagina_em(doc, el):
    return _prop(el.obj, 'PageStyleName', '') or 'Standard'


def planejar(doc, perfil, numeracao=None, inserir_sumario=True):
    """O que 'aplicar' vai fazer, com origem de cada mudança. Não altera o documento."""
    a = Analise(doc, perfil)
    p = perfil['parametros']
    numeracao = numeracao or ('manter' if a.numeracao in ('digitado', 'misto', 'auto') else 'automatica')
    plano = Plano(doc, perfil, a, {'numeracao': numeracao, 'inserir_sumario': inserir_sumario})
    R = perfil['regras']
    # página
    pags = sorted({_estilo_pagina_em(doc, el) for el in a.elementos[:1]} | {
        _prop(el.obj, 'PageDescName', '') for el in a.elementos if el.tipo != 'tabela' and _prop(el.obj, 'PageDescName', '')})
    fam = _familia(doc, 'PageStyles')
    for n in pags:
        if not fam.hasByName(n):
            continue
        s = fam.getByName(n)
        atual = (f'{s.Width / 1000:.1f} × {s.Height / 1000:.1f} cm; margens sup. {s.TopMargin / 1000:.2f}, esq. '
                 f'{s.LeftMargin / 1000:.2f}, inf. {s.BottomMargin / 1000:.2f}, dir. {s.RightMargin / 1000:.2f} cm').replace('.', ',')
        plano.add('Página', f'Estilo de página "{n}": {atual}', 'margens')
    m = p['margens_cm']
    plano.add('Página', (f'Novos estilos "{PAGINA_PRE}" (sem número) e "{PAGINA_TEXTO}" (número no canto superior '
                         f'{"direito; no verso, esquerdo" if p["frente_e_verso"] else "direito"}): A4, margens superior '
                         f'{m["superior"]:g}, esquerda {m["esquerda"]:g}, inferior {m["inferior"]:g} e direita {m["direita"]:g} cm'
                         + ('; frente e verso (margens espelhadas)' if p['frente_e_verso'] else '')).replace('.', ','),
              'margens')
    if a.inicio_textual is not None and not perfil['artigo']:
        desc = (f'Numeração de página a partir de "{a.inicio_textual.resumo(50)}"; páginas anteriores contadas e sem número'
                + ('; a capa fica fora da contagem' if p['capa_fora_da_contagem'] else '')
                + ('; a ficha catalográfica fica fora da contagem' if p['ficha_fora_da_contagem'] else ''))
        plano.add('Página', desc, 'paginacao')
    elif perfil['artigo']:
        plano.add('Página', 'Numeração de página desde a primeira página', 'paginacao')
    else:
        plano.avisos.append('Não encontrei o início da parte textual (um título de seção primária como "1 INTRODUÇÃO"). '
                            'A numeração das páginas não será configurada.')
    filete = round(p['nota_filete_cm'], 1)
    plano.add('Página', f'Filete das notas de rodapé com {filete:g} cm'.replace('.', ','), 'notas_rodape')
    # estilos
    fam_p = _familia(doc, 'ParagraphStyles')
    for nome, vals in valores_estilos(doc, p).items():
        s = fam_p.getByName(nome) if fam_p.hasByName(nome) else None
        difs = []
        for k, v in vals.items():
            if k in ('CharFontStyleName', 'CharFontFamily', 'CharFontPitch', 'ParaLastLineAdjust', 'ParaKeepTogether', 'ParaSplit'):
                continue
            atual = _prop(s, k) if s is not None else None
            if s is None or not _igual(atual, v):
                difs.append(f'{NOMES_PROP.get(k, k)}: {_mostrar(k, atual) if s is not None and atual is not None else "—"} → {_mostrar(k, v)}')
        if difs:
            plano.add('Estilos', f'{nome_estilo(nome)}' + (' (novo)' if s is None else '') + ': ' + '; '.join(difs))
    # parágrafos
    c = a.contagem()
    tit = a.por_tipo('titulo', zona=('textual', 'pos'))
    if tit:
        niveis = sorted({el.nivel for el in tit})
        plano.add('Parágrafos', f'{len(tit)} título(s) de seção nos estilos Título {", ".join(map(str, niveis))}', 'destaque_gradativo')
    if max([el.nivel for el in tit] or [0]) > 5:
        plano.avisos.append('Há títulos abaixo da seção quinária (nível 6 ou mais); a NBR 6024 limita a numeração a cinco níveis.')
    if numeracao == 'manter':
        plano.add('Numeração', ('Títulos com número digitado: o número fica como está e a numeração automática dos títulos é desligada'
                                if a.numeracao in ('digitado', 'misto') else 'Numeração dos títulos mantida como está'), 'indicativo_numerico')
    else:
        plano.add('Numeração', 'Numeração automática dos títulos: 1, 1.1, 1.1.1… em algarismos arábicos, separada do título por um espaço'
                  + (', com ponto depois do número (escolha da instituição)' if p['ponto_apos_indicativo'] else ''), 'indicativo_numerico')
    sem = a.por_tipo('titulo_pre', 'titulo_pos')
    if sem:
        plano.add('Parágrafos', f'{len(sem)} título(s) sem indicativo numérico centralizados ({", ".join(sorted({_norm(e.texto)[:20] for e in sem})[:6])})',
                  'titulos_sem_indicativo')
    corpo = a.por_tipo('texto', zona='textual')
    if corpo:
        plano.add('Parágrafos', f'{len(corpo)} parágrafo(s) de texto no estilo Corpo do texto (fonte, tamanho, entrelinhas, recuo e '
                  'alinhamento postos pelo estilo; negrito, itálico e sublinhado de trechos preservados)', 'entrelinhas')
    for tipo, desc, rid in (('citacao', 'citação(ões) longa(s) no estilo Citação', 'citacao_longa'),
                            ('referencia', 'referência(s) no estilo Referência (o conteúdo não muda)', 'referencias_apresentacao'),
                            ('legenda', 'identificação(ões) de ilustração ou tabela no estilo Legenda', 'ilustracoes'),
                            ('fonte_legenda', 'fonte(s) de ilustração ou tabela no estilo Fonte da ilustração', 'ilustracoes'),
                            ('objeto', 'parágrafo(s) com imagem ou objeto no estilo Ilustração (mesmo alinhamento das legendas)', 'ilustracoes')):
        if c.get(tipo):
            plano.add('Parágrafos', f'{c[tipo]} {desc}', rid)
    if a.sumario is not None and not a.indice_existente and not a.sumario_manual and inserir_sumario:
        plano.add('Campos', 'Sumário automático inserido depois do título SUMÁRIO (gerado dos títulos; atualizável)', 'sumario')
    plano.add('Campos', 'Sumários e índices existentes atualizados', 'sumario')
    if a.sumario_manual:
        plano.avisos.append('O sumário parece digitado à mão (pontilhado e números de página). Ele não será trocado: '
                            'apague-o e use Referências › Sumário e índices para ter o sumário automático.')
    pre_outros = a.por_tipo('pre_texto')
    if pre_outros:
        plano.avisos.append(f'{len(pre_outros)} parágrafo(s) antes da parte textual (capa, folha de rosto, resumo etc.) '
                            'recebem só a fonte e o tamanho do estilo Padrão (alinhamento, negrito e espaços ficam como estão); confira-os.')
    longas = [el for el in corpo if el.texto.lstrip().startswith(('“', '"')) and len(el.texto) > 250]
    if longas:
        plano.avisos.append(f'{len(longas)} parágrafo(s) longo(s) entre aspas podem ser citações com mais de três linhas '
                            '(recuo de 4 cm, sem aspas). O AY não muda o texto: confira e aplique o estilo Citação.')
    return plano


# ---------------------------------------------------------------- aplicar
def _limpar_direto(par, nomes):
    for n in nomes:
        try:
            if _estado_direto(par, n):
                par.setPropertyToDefault(n)
        except Exception:
            pass


PARA_DIRETOS = ('ParaLineSpacing', 'ParaAdjust', 'ParaLastLineAdjust', 'ParaFirstLineIndent', 'ParaLeftMargin',
                'ParaRightMargin', 'ParaTopMargin', 'ParaBottomMargin', 'CharFontName', 'CharHeight', 'CharFontStyleName',
                'CharFontFamily', 'CharFontPitch')
CHAR_DIRETOS = ('CharFontName', 'CharHeight', 'CharFontStyleName', 'CharFontFamily', 'CharFontPitch')


def _limpar_trechos(par, nomes, inteiro=()):
    """Remove formatação direta de fonte e tamanho dos trechos; 'inteiro': só quando o mesmo valor cobre o parágrafo todo."""
    try:
        e = par.createEnumeration()
        trechos = []
        while e.hasMoreElements():
            por = e.nextElement()
            if por.TextPortionType == 'Text' and por.getString():
                trechos.append(por)
    except Exception:
        return
    for por in trechos:
        _limpar_direto(por, nomes)
    for n in inteiro:
        vals = set()
        diretos = 0
        for por in trechos:
            if _estado_direto(por, n):
                diretos += 1
                v = por.getPropertyValue(n)
                vals.add(getattr(v, 'value', v))
        if trechos and diretos == len(trechos) and len(vals) == 1:
            for por in trechos:
                _limpar_direto(por, (n,))


def _numeracao_capitulos(doc, params, ligada):
    regras = doc.getChapterNumberingRules()
    sufixo = '.' if params['ponto_apos_indicativo'] else ''
    for nivel in range(regras.getCount()):
        atuais = {pv.Name: pv.Value for pv in regras.getByIndex(nivel)}
        novo = dict(atuais)
        if nivel < 5:
            novo['HeadingStyleName'] = f'Heading {nivel + 1}'
            if ligada:
                # ListFormat explícito: nas versões novas do motor ele vale sobre Prefix/Suffix
                formato = '.'.join(f'%{k}%' for k in range(1, nivel + 2)) + sufixo
                novo.update(NumberingType=4, ParentNumbering=nivel + 1, Prefix='', Suffix=sufixo, ListFormat=formato, LabelFollowedBy=1,
                            PositionAndSpaceMode=1, IndentAt=0, FirstLineIndent=0, ListtabStopPosition=0, StartWith=1)
            else:
                novo.update(NumberingType=5, Prefix='', Suffix='', ListFormat='')
        pvs = []
        for k, v in novo.items():
            pv = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
            pv.Name, pv.Value = k, v
            pvs.append(pv)
        uno.invoke(regras, 'replaceByIndex', (nivel, uno.Any('[]com.sun.star.beans.PropertyValue', tuple(pvs))))


def _valores_pagina(base, params, cabecalho, lado=None):
    """Propriedades do estilo de página pela regra: (propriedades gerais, propriedades do cabeçalho)."""
    m = params['margens_cm']
    pag = params['paginacao']
    paisagem = base is not None and base.Width > base.Height
    larg, alt = cm(params['papel']['largura_cm']), cm(params['papel']['altura_cm'])
    v = {'IsLandscape': paisagem, 'Width': alt if paisagem else larg, 'Height': larg if paisagem else alt,
         'LeftMargin': cm(m['esquerda']), 'RightMargin': cm(m['direita']), 'BottomMargin': cm(m['inferior']),
         'PageStyleLayout': uno.Enum('com.sun.star.style.PageStyleLayout',
                                     ('RIGHT' if lado == 'direita' else 'MIRRORED') if params['frente_e_verso'] else 'ALL')}
    mancha = (v['Width'] - v['LeftMargin'] - v['RightMargin']) / 1000
    v.update(FootnoteLineRelativeWidth=max(1, min(100, int(round(params['nota_filete_cm'] / mancha * 100)))),
             FootnoteLineAdjust=0, FootnoteLineWeight=18, FootnoteLineTextDistance=pt(4), FootnoteLineDistance=pt(6))
    if cabecalho:
        borda = cm(pag['distancia_borda_cm'])
        v['TopMargin'] = borda
        cab = {'HeaderIsOn': True, 'HeaderIsDynamicHeight': False, 'HeaderBodyDistance': cm(0.4),
               'HeaderHeight': max(cm(0.6), cm(m['superior']) - borda), 'HeaderIsShared': not params['frente_e_verso']}
    else:
        v['TopMargin'] = cm(m['superior'])
        cab = {'HeaderIsOn': False}
    return v, cab


def _preparar_pagina(doc, nome, base, params, cabecalho, lado=None, seguinte=None):
    """Fase fora do desfazer. No motor, ligar o cabeçalho ou mudar um estilo de página já existente apaga o histórico
    de desfazer; criar um estilo novo com as propriedades já definidas não apaga. Por isso os estilos do AY são novos
    (os do documento não mudam) e só o cabeçalho é ligado depois."""
    fam = _familia(doc, 'PageStyles')
    vals, cab = _valores_pagina(base, params, cabecalho, lado)
    if seguinte:
        vals['FollowStyle'] = seguinte
    if not fam.hasByName(nome):
        s = doc.createInstance('com.sun.star.style.PageStyle')
        for k, v in vals.items():
            try:
                s.setPropertyValue(k, v)
            except Exception:
                pass
        fam.insertByName(nome, s)
    s = fam.getByName(nome)
    for k, v in list(vals.items()) + list(cab.items()):
        try:
            if not _igual(s.getPropertyValue(k), v):
                s.setPropertyValue(k, v)
        except Exception:
            pass
    if base is not None and _prop(base, 'FooterIsOn') and not s.FooterIsOn:
        s.FooterIsOn = True
        try:
            s.FooterText.copyText(base.FooterText)
        except Exception:
            pass
    return s


def _preparar_paginas(doc, plano):
    """Cria os estilos de página do AY (fase fora do desfazer) e devolve o que a fase com desfazer precisa."""
    a, perfil = plano.analise, plano.perfil
    p = perfil['parametros']
    fam_pag = _familia(doc, 'PageStyles')
    els = [el for el in a.elementos if el.tipo not in ('tabela', 'indice')]
    base_nome = _estilo_pagina_em(doc, els[0]) if els else 'Standard'
    base = fam_pag.getByName(base_nome) if fam_pag.hasByName(base_nome) else None
    primaria_nova = p['secao_primaria_pagina_nova'] and not perfil['artigo']
    cabecalhos = [PAGINA_TEXTO]
    if not perfil['artigo']:
        _preparar_pagina(doc, PAGINA_PRE, base, p, cabecalho=False)
    _preparar_pagina(doc, PAGINA_TEXTO, base, p, cabecalho=True)
    if p['frente_e_verso'] and primaria_nova:
        _preparar_pagina(doc, PAGINA_ANVERSO, base, p, cabecalho=True, lado='direita', seguinte=PAGINA_TEXTO)
        cabecalhos.append(PAGINA_ANVERSO)
    # outros estilos de página usados no documento (ex.: páginas em paisagem): cópia do AY com as margens da regra
    copias = {}
    for el in els:
        n = _prop(el.obj, 'PageDescName', '')
        if not n or n in (PAGINA_PRE, PAGINA_TEXTO, PAGINA_ANVERSO) or n == base_nome or n.startswith('AY '):
            continue
        if fam_pag.hasByName(n) and n not in copias:
            com_numero = el.zona != 'pre' or perfil['artigo']
            copia = f'AY {n}'
            _preparar_pagina(doc, copia, fam_pag.getByName(n), p, cabecalho=com_numero)
            copias[n] = copia
            if com_numero:
                cabecalhos.append(copia)
    return {'base': base_nome, 'copias': copias, 'cabecalhos': cabecalhos, 'primaria_nova': primaria_nova}


def _cabecalho_numero(doc, texto, alinhamento):
    texto.setString('')
    cur = texto.createTextCursor()
    cur.setPropertyValue('ParaStyleName', 'Header')
    cur.setPropertyValue('ParaAdjust', alinhamento)
    campo = doc.createInstance('com.sun.star.text.TextField.PageNumber')
    campo.NumberingType = 4
    campo.SubType = uno.Enum('com.sun.star.text.PageNumberType', 'CURRENT')
    texto.insertTextContent(cur, campo, False)


def _pagina_fisica(doc, el):
    try:
        ctrl = doc.getCurrentController()
        ctrl.getPropertyValue('PageCount')
        vc = ctrl.getViewCursor()
        guardado = vc.getStart()
        vc.gotoRange(el.obj.getStart(), False)
        n = vc.getPage()
        vc.gotoRange(guardado, False)
        return n
    except Exception:
        return None


def _pagina_de(doc, el):
    try:
        ctrl = doc.getCurrentController()
        vc = ctrl.getViewCursor()
        guardado = vc.getStart()
        vc.gotoRange(el.obj.getAnchor() if el.tipo == 'tabela' else el.obj.getStart(), False)
        n = vc.getPage()
        vc.gotoRange(guardado, False)
        return n
    except Exception:
        return None


def _primeiro_na_pagina(doc, a, n):
    """Primeiro elemento (do autor) que começa na página física n ou depois."""
    try:
        doc.getCurrentController().getPropertyValue('PageCount')
    except Exception:
        pass
    for el in a.elementos:
        if el.tipo == 'indice':
            continue
        pg = _pagina_de(doc, el)
        if pg is not None and pg >= n:
            return el
    return None


def _recomecar(el, estilo, numero):
    try:
        el.obj.setPropertyValues(('PageDescName', 'PageNumberOffset'), (estilo, numero))
    except Exception:
        el.obj.setPropertyValue('PageDescName', estilo)
        el.obj.setPropertyValue('PageNumberOffset', numero)


def _numero_exibido(doc, a, alvo):
    """Número de página que aparece no elemento: último recomeço antes dele + páginas físicas desde o recomeço."""
    pg_alvo = _pagina_de(doc, alvo)
    if pg_alvo is None:
        return None
    base_el, base_n = None, None
    for el in a.elementos[:alvo.i + 1]:
        if el.tipo in ('indice',):
            continue
        off = _prop(el.obj, 'PageNumberOffset', None)
        if off and _prop(el.obj, 'PageDescName', ''):
            base_el, base_n = el, off
    if base_el is None:
        return pg_alvo
    pg_base = _pagina_de(doc, base_el)
    return base_n + pg_alvo - pg_base if pg_base is not None else None


def aplicar(doc, plano, titulo_desfazer=None):
    """Aplica o plano numa única ação de desfazer. Devolve um resumo do que foi feito."""
    a, perfil = plano.analise, plano.perfil
    p = perfil['parametros']
    um = doc.getUndoManager()
    titulo_desfazer = titulo_desfazer or f'Formatar trabalho acadêmico ({perfil["nome"]})'
    feito = {'estilos': 0, 'paragrafos': 0, 'sumario_inserido': False, 'pagina_inicial_exibida': None, 'segundos': 0.0}
    t0 = time.time()
    havia_historico = um.isUndoPossible()
    paginas = _preparar_paginas(doc, plano)
    feito['historico_apagado'] = havia_historico and not um.isUndoPossible()
    um.enterUndoContext(titulo_desfazer)
    doc.lockControllers()
    try:
        # estilos de parágrafo
        fam = _familia(doc, 'ParagraphStyles')
        corpo = _corpo_nome(doc)
        pais = {ESTILO_PRE: 'Heading', ESTILO_POS: 'Heading', ESTILO_REF: 'Standard', ESTILO_FONTE: 'Caption', ESTILO_OBJETO: 'Standard'}
        for nome, vals in valores_estilos(doc, p).items():
            s = _estilo_par(doc, nome, pai=pais.get(nome, 'Standard'))
            for k, v in vals.items():
                try:
                    s.setPropertyValue(k, v)
                except Exception:
                    pass
            feito['estilos'] += 1
        for cat in ('Figure', 'Table', 'Illustration', 'Drawing', 'Text'):
            if fam.hasByName(cat):
                s = fam.getByName(cat)
                for k in ('CharHeight', 'ParaLineSpacing', 'ParaAdjust', 'CharFontName', 'CharPosture'):
                    try:
                        s.setPropertyToDefault(k)
                    except Exception:
                        pass
        h1 = fam.getByName('Heading 1')
        primaria_nova = p['secao_primaria_pagina_nova'] and not perfil['artigo']
        for nome in (ESTILO_PRE, ESTILO_POS):
            fam.getByName(nome).BreakType = _quebra('PAGE_BEFORE' if primaria_nova else 'NONE')
        # numeração dos títulos
        _numeracao_capitulos(doc, p, plano.op['numeracao'] == 'automatica')
        for n in range(1, 6):
            # títulos ligados a uma lista importada do Word (ex.: WWNum3) voltam para a numeração de capítulos ("Outline")
            s = fam.getByName(f'Heading {n}')
            try:
                if s.getPropertyValue('NumberingStyleName') not in ('', 'Outline'):
                    s.setPropertyValue('NumberingStyleName', 'Outline')
            except Exception:
                pass
        # número de página (campo) no cabeçalho dos estilos de página do AY
        fam_pag = _familia(doc, 'PageStyles')
        els = a.elementos
        for nome in paginas['cabecalhos']:
            s = fam_pag.getByName(nome)
            _cabecalho_numero(doc, s.HeaderText, DIR)
            if p['frente_e_verso'] and not s.HeaderIsShared:
                _cabecalho_numero(doc, s.HeaderTextLeft, ESQ)
        if primaria_nova:
            if p['frente_e_verso']:
                h1.BreakType = _quebra('NONE')
                h1.PageDescName = PAGINA_ANVERSO
            else:
                h1.BreakType = _quebra('PAGE_BEFORE')
                try:
                    if h1.PageDescName:
                        h1.setPropertyToDefault('PageDescName')
                except Exception:
                    pass
        else:
            h1.BreakType = _quebra('NONE')
        # trocas de estilo de página já existentes no documento: para os estilos do AY
        for el in els:
            if el.tipo in ('tabela', 'indice'):
                continue
            n = _prop(el.obj, 'PageDescName', '')
            if not n:
                continue
            if n == paginas['base']:
                el.obj.PageDescName = PAGINA_PRE if el.zona == 'pre' and not perfil['artigo'] else PAGINA_TEXTO
            elif n in paginas['copias']:
                el.obj.PageDescName = paginas['copias'][n]
        # parágrafos
        for el in els:
            if el.tipo == 'tabela':
                continue
            alvo = None
            if el.tipo == 'titulo' and el.zona in ('textual', 'pos') and el.nivel <= 10:
                alvo = f'Heading {min(el.nivel, 10)}'
            elif el.tipo == 'titulo_pre':
                alvo = ESTILO_PRE
            elif el.tipo == 'titulo_pos':
                alvo = ESTILO_POS
            elif el.tipo == 'texto' and el.zona == 'textual':
                alvo = corpo
            elif el.tipo == 'citacao' and el.zona == 'textual':
                alvo = 'Quotations'
            elif el.tipo == 'referencia':
                alvo = ESTILO_REF
            elif el.tipo == 'legenda':
                alvo = el.estilo if el.estilo in ESTILOS_LEGENDA else 'Caption'
            elif el.tipo == 'fonte_legenda':
                alvo = ESTILO_FONTE
            elif el.tipo == 'objeto' and el.zona != 'pre':
                alvo = ESTILO_OBJETO
            elif el.tipo == 'pre_texto':
                # capa, folha de rosto, resumo: só a letra (tamanho 12 em todo o trabalho, inclusive capa); o resto fica
                _limpar_direto(el.obj, CHAR_DIRETOS)
                _limpar_trechos(el.obj, CHAR_DIRETOS)
                continue
            if alvo is None:
                continue
            par = el.obj
            par.setPropertyValue('ParaStyleName', alvo)
            _limpar_direto(par, PARA_DIRETOS)
            if el.tipo in ('titulo', 'titulo_pre', 'titulo_pos'):
                _limpar_direto(par, ('CharWeight', 'CharPosture', 'CharCaseMap', 'CharColor', 'BreakType'))
                _limpar_trechos(par, CHAR_DIRETOS, inteiro=('CharWeight', 'CharCaseMap', 'CharColor', 'CharPosture'))
            else:
                _limpar_trechos(par, CHAR_DIRETOS)
            if el.tipo == 'titulo' and plano.op['numeracao'] == 'manter' and el.numero == 'digitado':
                try:
                    par.setPropertyValue('NumberingIsNumber', False)
                except Exception:
                    pass
            feito['paragrafos'] += 1
        # referências separadas por parágrafo vazio: sem espaço depois (o vazio já separa)
        refs = a.por_tipo('referencia')
        if refs and any(els[r.i + 1].tipo == 'vazio' for r in refs if r.i + 1 < len(els)):
            fam.getByName(ESTILO_REF).ParaBottomMargin = 0
        # quebras de página: primeira página e início da parte textual
        if els and not perfil['artigo']:
            primeiro = els[0].obj
            primeiro.setPropertyValue('PageDescName', PAGINA_PRE)
            if a.inicio_textual is not None:
                a.inicio_textual.obj.setPropertyValue('PageDescName', PAGINA_ANVERSO if p['frente_e_verso'] and primaria_nova else PAGINA_TEXTO)
        elif els:
            els[0].obj.setPropertyValue('PageDescName', PAGINA_TEXTO)
        # sumário automático
        if a.sumario is not None and not a.indice_existente and not a.sumario_manual and plano.op['inserir_sumario']:
            texto = doc.getText()
            cur = texto.createTextCursorByRange(a.sumario.obj.getEnd())
            texto.insertControlCharacter(cur, 0, False)
            novo = cur.getStart()
            # ao dividir o parágrafo, o objeto antigo fica com a parte nova (vazia): religa o elemento ao título
            volta = texto.createTextCursorByRange(novo)
            if volta.gotoPreviousParagraph(False):
                volta.gotoEndOfParagraph(True)
                en = volta.createEnumeration()
                if en.hasMoreElements():
                    a.sumario.obj = en.nextElement()
            cur.setPropertyValue('ParaStyleName', 'Standard')
            for k in ('BreakType', 'PageDescName'):
                try:
                    cur.setPropertyToDefault(k)
                except Exception:
                    pass
            idx = doc.createInstance('com.sun.star.text.ContentIndex')
            idx.CreateFromOutline = True
            idx.Level = 5
            idx.Title = ''
            texto.insertTextContent(novo, idx, False)
            feito['sumario_inserido'] = True
    finally:
        doc.unlockControllers()
    try:
        idxs = doc.getDocumentIndexes()
        for k in range(idxs.getCount()):
            idxs.getByIndex(k).update()
        doc.getTextFields().refresh()
        # contagem de páginas: a folha de rosto é a página 1 (capa fora); a ficha catalográfica pode ficar fora também.
        # Recomeçar com 1 logo depois da capa troca a paridade: o motor insere uma página em branco automática (o verso
        # da capa, certo em frente e verso). Só frente: essas páginas não são impressas; o PDF já não as exporta.
        if a.inicio_textual is not None and not perfil['artigo']:
            recomecos = []
            if p['capa_fora_da_contagem']:
                rosto = _primeiro_na_pagina(doc, a, 2)
                if rosto is not None:
                    _recomecar(rosto, PAGINA_PRE if rosto.zona == 'pre' else _prop(rosto.obj, 'PageDescName', '') or PAGINA_TEXTO, 1)
                    recomecos.append((rosto, 1))
            if p['ficha_fora_da_contagem']:
                base = recomecos[-1][0] if recomecos else (a.elementos[0] if a.elementos else None)
                pg = _pagina_fisica(doc, base) if base is not None else None
                apos = _primeiro_na_pagina(doc, a, pg + 2) if pg else None
                if apos is not None:
                    _recomecar(apos, PAGINA_PRE if apos.zona == 'pre' else _prop(apos.obj, 'PageDescName', '') or PAGINA_TEXTO, 2)
                    recomecos.append((apos, 2))
            if recomecos and not p['frente_e_verso']:
                try:
                    doc.createInstance('com.sun.star.text.DocumentSettings').setPropertyValue('PrintEmptyPages', False)
                except Exception:
                    pass
            feito['recomecos'] = [(el.resumo(40), n) for el, n in recomecos]
            feito['pagina_inicial_exibida'] = _numero_exibido(doc, a, a.inicio_textual)
            for k in range(idxs.getCount()):
                idxs.getByIndex(k).update()
    finally:
        um.leaveUndoContext()
    feito['segundos'] = round(time.time() - t0, 2)
    return feito


# ---------------------------------------------------------------- trabalhar numa cópia
def copia_sem_titulo(ctx, doc, extra=None):
    """Abre uma cópia sem título do documento (o original não muda) e a devolve. 'extra': PropertyValues da abertura."""
    import tempfile
    pasta = tempfile.mkdtemp(prefix='ay-copia-')
    caminho = os.path.join(pasta, 'copia.odt')
    u = uno.systemPathToFileUrl(caminho)
    pv = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
    pv.Name, pv.Value = 'FilterName', 'writer8'
    doc.storeToURL(u, (pv,))
    desk = ctx.getServiceManager().createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
    t = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
    t.Name, t.Value = 'AsTemplate', True
    nova = desk.loadComponentFromURL(u, '_blank', 0, (t,) + tuple(extra or ()))
    try:
        os.remove(caminho)
        os.rmdir(pasta)
    except Exception:
        pass
    return nova


# ---------------------------------------------------------------- conferir
OK, FALHA, AVISO, NAO_VERIFICAVEL, NAO_SE_APLICA = 'conforme', 'não conforme', 'aviso', 'não verificável', 'não se aplica'


class Item:
    __slots__ = ('regra', 'titulo', 'situacao', 'detalhe', 'camada', 'origem', 'locais')

    def __init__(self, regra, titulo, situacao, detalhe, camada, origem_txt, locais=None):
        self.regra, self.titulo, self.situacao, self.detalhe = regra, titulo, situacao, detalhe
        self.camada, self.origem, self.locais = camada, origem_txt, locais or []


def _alin(par):
    """Alinhamento do parágrafo; o DOCX traz 'início' (5) e 'fim' (6), que em texto da esquerda para a direita são
    esquerda e direita."""
    v = _prop(par, 'ParaAdjust', ESQ)
    return {5: ESQ, 6: DIR}.get(v, v)


def _inicia_pagina(par):
    q = _prop(par, 'BreakType')
    return bool(_prop(par, 'PageDescName', '')) or (q is not None and q.value in ('PAGE_BEFORE', 'PAGE_BOTH'))


def _ls(par):
    v = _prop(par, 'ParaLineSpacing')
    return (v.Mode, v.Height) if v is not None else (None, None)


def _pars_texto(xtexto):
    e = xtexto.createEnumeration()
    while e.hasMoreElements():
        o = e.nextElement()
        if o.supportsService('com.sun.star.text.Paragraph'):
            yield o


def _tem_campo_pagina(xtexto):
    try:
        for par in _pars_texto(xtexto):
            e = par.createEnumeration()
            while e.hasMoreElements():
                por = e.nextElement()
                if por.TextPortionType == 'TextField' and por.TextField.supportsService('com.sun.star.text.TextField.PageNumber'):
                    return par
    except Exception:
        pass
    return None


def conferir(doc, perfil, analise=None):
    """Relatório de conformidade: um item por regra, com situação, detalhe, camada e origem."""
    a = analise or Analise(doc, perfil)
    p = perfil['parametros']
    R = perfil['regras']
    itens = []

    def add(rid, situacao, detalhe='', locais=None, titulo=None):
        r = R[rid]
        if r['camada'] == 'preferencia' and situacao == FALHA:
            situacao = AVISO
        itens.append(Item(rid, titulo or r['titulo'], situacao, detalhe, r['camada'], origem(r, perfil), locais))

    els = a.elementos
    fam_pag = _familia(doc, 'PageStyles')
    usados = []
    for el in els:
        if el.tipo == 'tabela':
            continue
        n = _prop(el.obj, 'PageStyleName', '')
        if n and n not in usados:
            usados.append(n)
    estilos_pag = [(n, fam_pag.getByName(n)) for n in usados if fam_pag.hasByName(n)]
    # papel e margens
    erros_papel = [n for n, s in estilos_pag if sorted((s.Width, s.Height)) != sorted((cm(p['papel']['largura_cm']), cm(p['papel']['altura_cm'])))
                   and abs(min(s.Width, s.Height) - cm(21.0)) > 50]
    add('papel', FALHA if erros_papel else OK, ('Estilos de página fora do A4: ' + ', '.join(erros_papel)) if erros_papel else
        f'{len(estilos_pag)} estilo(s) de página em A4')
    m = p['margens_cm']
    ruins = []
    for n, s in estilos_pag:
        topo = s.TopMargin + (s.HeaderHeight if s.HeaderIsOn else 0)
        if s.Width > s.Height:
            continue
        valores = {'superior': topo, 'esquerda': s.LeftMargin, 'inferior': s.BottomMargin + (s.FooterHeight if s.FooterIsOn else 0),
                   'direita': s.RightMargin}
        dif = [f'{k} {v / 1000:.2f} cm (pede {m[k]:g})'.replace('.', ',') for k, v in valores.items() if abs(v - cm(m[k])) > 60]
        if dif:
            ruins.append(f'"{n}": ' + ', '.join(dif))
    add('margens', FALHA if ruins else OK, '; '.join(ruins) if ruins else 'Margens conferidas em ' + ', '.join(f'"{n}"' for n, _ in estilos_pag))
    # corpo do texto
    corpo = a.por_tipo('texto', zona='textual')
    if corpo:
        tam = [el for el in corpo if any(abs((v or 0) - p['fonte_tamanho']) > 0.05 for v in valores_trechos(el.obj, 'CharHeight'))]
        add('fonte_tamanho', FALHA if tam else OK, f'{len(corpo) - len(tam)} de {len(corpo)} parágrafos de texto com {p["fonte_tamanho"]} pt',
            [el.i for el in tam[:20]])
        fam_ = [el for el in corpo if valores_trechos(el.obj, 'CharFontName') != {p['fonte_familia']}]
        add('fonte_familia', FALHA if fam_ else OK, f'{len(corpo) - len(fam_)} de {len(corpo)} parágrafos de texto em {p["fonte_familia"]}',
            [el.i for el in fam_[:20]])
        ent = [el for el in corpo if _ls(el.obj) != (0, int(round(p['entrelinhas'] * 100)))]
        add('entrelinhas', FALHA if ent else OK, f'{len(corpo) - len(ent)} de {len(corpo)} parágrafos de texto com entrelinhas '
            f'{p["entrelinhas"]:g}'.replace('.', ','), [el.i for el in ent[:20]])
        cor = [el for el in corpo if any(v not in (-1, 0, None) for v in valores_trechos(el.obj, 'CharColor'))]
        add('cor_texto', FALHA if cor else OK, f'{len(cor)} parágrafo(s) de texto com trechos em cor diferente de preto/automática',
            [el.i for el in cor[:20]])
    else:
        for rid in ('fonte_tamanho', 'fonte_familia', 'entrelinhas', 'cor_texto'):
            add(rid, NAO_SE_APLICA, 'Nenhum parágrafo de texto identificado na parte textual.')
    # letra menor e espaço simples nas exceções
    menores, simples_ruins, tamanhos = [], [], set()
    notas = doc.getFootnotes()
    pars_nota = []
    for k in range(notas.getCount()):
        pars_nota.extend(_pars_texto(notas.getByIndex(k)))
    grupos = [('nota', pars_nota), ('citação', [el.obj for el in a.por_tipo('citacao', zona='textual')]),
              ('legenda', [el.obj for el in a.por_tipo('legenda')]), ('fonte', [el.obj for el in a.por_tipo('fonte_legenda')])]
    for nome, pars in grupos:
        for par in pars:
            h = max(v or 0 for v in valores_trechos(par, 'CharHeight'))
            tamanhos.add(round(h, 1))
            if h >= p['fonte_tamanho'] - 0.05:
                menores.append(nome)
            if _ls(par) != (0, 100):
                simples_ruins.append(nome)
    pag_par = None
    for n, s in estilos_pag:
        if s.HeaderIsOn:
            pag_par = _tem_campo_pagina(s.HeaderText) or pag_par
    if pag_par is not None:
        h = _prop(pag_par, 'CharHeight', 0) or 0
        tamanhos.add(round(h, 1))
        if h >= p['fonte_tamanho'] - 0.05:
            menores.append('paginação')
    if not tamanhos:
        add('fonte_menor', NAO_SE_APLICA, 'Sem notas, citações longas, legendas nem paginação para conferir.')
    else:
        unif = len(tamanhos) == 1
        det = f'tamanhos usados: {", ".join(f"{t:g}" for t in sorted(tamanhos))} pt'
        if menores:
            add('fonte_menor', FALHA, f'Não estão em letra menor: {", ".join(sorted(set(menores)))}; {det}')
        elif not unif:
            add('fonte_menor', FALHA, f'Letra menor, mas não uniforme: {det}')
        else:
            add('fonte_menor', OK, det)
    refs = a.por_tipo('referencia')
    for el in refs:
        if _ls(el.obj) != (0, 100):
            simples_ruins.append('referência')
    add('entrelinhas_excecoes', FALHA if simples_ruins else (OK if (tamanhos or refs) else NAO_SE_APLICA),
        ('Sem espaço simples: ' + ', '.join(f'{simples_ruins.count(x)} {x}' for x in sorted(set(simples_ruins)))) if simples_ruins else
        'Notas, citações longas, legendas, fontes e referências em espaço simples')
    # títulos
    tit = a.por_tipo('titulo', zona=('textual', 'pos'))
    if tit:
        # antes do título só conta quando há texto acima na mesma página (título que abre a página não tem o que separar)
        sem_esp = [el for el in tit if (_prop(el.obj, 'ParaTopMargin', 0) or 0) < pt(10) and not _inicia_pagina(el.obj)
                   and not (el.i > 0 and els[el.i - 1].tipo == 'vazio')
                   or (_prop(el.obj, 'ParaBottomMargin', 0) or 0) < pt(10) and not (el.i + 1 < len(els) and els[el.i + 1].tipo == 'vazio')]
        add('titulos_espaco', FALHA if sem_esp else OK, f'{len(tit) - len(sem_esp)} de {len(tit)} títulos com espaço antes e depois',
            [el.i for el in sem_esp[:20]])
        if perfil['artigo'] or not p['secao_primaria_pagina_nova']:
            add('secao_primaria_pagina', NAO_SE_APLICA, 'Este perfil não pede página nova para as seções primárias.')
        else:
            prim = [el for el in tit if el.nivel == 1]
            sem_q = [el for el in prim if (_prop(el.obj, 'BreakType', None) is None or _prop(el.obj, 'BreakType').value not in ('PAGE_BEFORE', 'PAGE_BOTH'))
                     and not _prop(el.obj, 'PageDescName', '')]
            add('secao_primaria_pagina', FALHA if sem_q else OK, f'{len(prim) - len(sem_q)} de {len(prim)} seções primárias em página nova',
                [el.i for el in sem_q[:20]])
        # indicativo numérico
        probl = []
        for el in tit:
            if el.numero == 'digitado':
                if el.separador and not p['ponto_apos_indicativo']:
                    probl.append((el, f'sinal "{el.separador}" entre o número e o título'))
            elif el.numero == 'nenhum':
                rot = (_prop(el.obj, 'ListLabelString', '') or '').strip()
                if not rot:
                    probl.append((el, 'sem indicativo numérico'))
            if el.nivel > 5:
                probl.append((el, 'abaixo da seção quinária'))
        if not probl:
            rotulos = [(_prop(el.obj, 'ListLabelString', '') or '').strip() for el in tit if el.numero != 'digitado']
            ruins_rot = [r for r in rotulos if r and not re.fullmatch(r'\d+(\.\d+)*' + (r'\.' if p['ponto_apos_indicativo'] else ''), r)]
            if ruins_rot:
                probl.append((tit[0], f'numeração automática fora do padrão arábico: {", ".join(ruins_rot[:3])}'))
        add('indicativo_numerico', FALHA if probl else OK, '; '.join(f'"{el.resumo(30)}": {m_}' for el, m_ in probl[:6]) if probl else
            f'{len(tit)} títulos com indicativo arábico, separado por espaço', [el.i for el, _ in probl[:20]])
        assin = {}
        for el in tit:
            if el.nivel > 5:
                continue
            o = el.obj
            assin.setdefault(el.nivel, set()).add(((_prop(o, 'CharWeight', 100) or 100) >= 150, getattr(_prop(o, 'CharPosture'), 'value', ''),
                                                  _prop(o, 'CharCaseMap', 0) or 0, round(_prop(o, 'CharHeight', 0) or 0, 1)))
        incons = [n for n, s in assin.items() if len(s) > 1]
        unicos = {n: next(iter(s)) for n, s in assin.items() if len(s) == 1}
        iguais = len(set(unicos.values())) < len(unicos)
        add('destaque_gradativo', FALHA if incons or iguais else OK,
            (f'Níveis com destaques diferentes entre si: {incons}' if incons else '') + (' Dois níveis com o mesmo destaque.' if iguais else '')
            or f'{len(unicos)} nível(is) com destaques distintos')
    else:
        for rid in ('titulos_espaco', 'secao_primaria_pagina', 'indicativo_numerico', 'destaque_gradativo'):
            add(rid, NAO_SE_APLICA if perfil['artigo'] else FALHA, 'Nenhum título de seção identificado na parte textual.')
    sem = a.por_tipo('titulo_pre', 'titulo_pos')
    ruins = [el for el in sem if _alin(el.obj) != CENTRO or (_prop(el.obj, 'ListLabelString', '') or '').strip()]
    pre_no_sumario = [el for el in a.por_tipo('titulo_pre') if (_prop(el.obj, 'OutlineLevel', 0) or 0) > 0]
    add('titulos_sem_indicativo', (FALHA if ruins or pre_no_sumario else OK) if sem else NAO_SE_APLICA,
        (f'{len(ruins)} não centralizado(s) ou numerado(s). ' if ruins else '') +
        (f'{len(pre_no_sumario)} título(s) pré-textual(is) entrariam no sumário.' if pre_no_sumario else '') or f'{len(sem)} título(s) centralizados, sem número',
        [el.i for el in (ruins + pre_no_sumario)[:20]])
    # paginação
    if perfil['artigo']:
        ok_pg = any(s.HeaderIsOn and _tem_campo_pagina(s.HeaderText) is not None for _, s in estilos_pag)
        add('paginacao', OK if ok_pg else FALHA, 'Número de página no cabeçalho' if ok_pg else 'Sem número de página no cabeçalho')
    elif a.inicio_textual is None:
        add('paginacao', FALHA, 'Início da parte textual não identificado (título de seção primária).')
    else:
        probl = []
        pre_estilo = _prop(els[0].obj, 'PageStyleName', '') if els and els[0].tipo != 'tabela' else ''
        if pre_estilo and fam_pag.hasByName(pre_estilo):
            s = fam_pag.getByName(pre_estilo)
            if (s.HeaderIsOn and _tem_campo_pagina(s.HeaderText) is not None) or (s.FooterIsOn and _tem_campo_pagina(s.FooterText) is not None):
                probl.append('as páginas pré-textuais mostram número')
        txt_estilo = _prop(a.inicio_textual.obj, 'PageStyleName', '')
        s = fam_pag.getByName(txt_estilo) if txt_estilo and fam_pag.hasByName(txt_estilo) else None
        par_num = _tem_campo_pagina(s.HeaderText) if s is not None and s.HeaderIsOn else None
        if par_num is None:
            probl.append('a parte textual não tem número de página no cabeçalho')
        else:
            if _alin(par_num) != DIR:
                probl.append('número de página não está à direita')
            if abs(s.TopMargin - cm(p['paginacao']['distancia_borda_cm'])) > 60:
                probl.append(f'número a {s.TopMargin / 1000:.2f} cm da borda superior (pede 2 cm)'.replace('.', ','))
            if p['frente_e_verso'] and not s.HeaderIsShared:
                esq = _tem_campo_pagina(s.HeaderTextLeft)
                if esq is None or _alin(esq) != ESQ:
                    probl.append('no verso, o número não está à esquerda')
        # contagem: com a capa fora, a folha de rosto (primeiro conteúdo depois da capa) recomeça com 1
        if p['capa_fora_da_contagem']:
            rosto = _primeiro_na_pagina(doc, a, 2)
            if rosto is None or _prop(rosto.obj, 'PageNumberOffset', None) != 1 or not _prop(rosto.obj, 'PageDescName', ''):
                probl.append('a capa entra na contagem: a folha de rosto não recomeça com o número 1')
        if p['ficha_fora_da_contagem']:
            offs = [el for el in a.elementos if el.tipo not in ('indice',) and _prop(el.obj, 'PageNumberOffset', None) == 2]
            if not offs:
                probl.append('a ficha catalográfica entra na contagem')
        if (_prop(a.inicio_textual.obj, 'PageNumberOffset', None) or 0) > 2:
            probl.append('a numeração recomeça na parte textual, em vez de seguir a contagem desde a folha de rosto')
        exibida = _numero_exibido(doc, a, a.inicio_textual)
        det = f'A parte textual ("{a.inicio_textual.resumo(30)}") mostra o número {exibida}; a contagem começa na ' + (
            'folha de rosto (capa fora)' if p['capa_fora_da_contagem'] else 'primeira página')
        add('paginacao', FALHA if probl else OK, '; '.join(probl) + ('. ' if probl else '') + det)
    # notas de rodapé
    if pars_nota:
        probl = []
        if any((_prop(x, 'CharHeight', 0) or 0) >= p['fonte_tamanho'] - 0.05 for x in pars_nota):
            probl.append('letra não é menor que a do texto')
        if any(_ls(x) != (0, 100) for x in pars_nota):
            probl.append('não estão em espaço simples')
        docx = (doc.getURL() or '').lower().endswith('.docx')
        aviso_docx = ''
        for n, s in estilos_pag:
            mancha = (s.Width - s.LeftMargin - s.RightMargin) / 1000
            rel = _prop(s, 'FootnoteLineRelativeWidth', 25) or 25
            larg = rel * mancha / 100
            if abs(larg - p['nota_filete_cm']) > 0.4 and s.Width < s.Height:
                if docx and rel == 25:
                    # o DOCX guarda só o separador padrão do Word, sem comprimento; ao abrir, o motor mostra 25% da mancha
                    aviso_docx = (f'Arquivo DOCX: o filete é o separador padrão do Word, sem comprimento gravado no arquivo; '
                                  f'o AY o mostra com {larg:.1f} cm'.replace('.', ',') + '. Confira o comprimento no programa '
                                  'que vai gerar o PDF ou salve em ODT.')
                else:
                    probl.append(f'filete com {larg:.1f} cm em "{n}" (pede 5 cm)'.replace('.', ','))
        add('notas_rodape', FALHA if probl else (AVISO if aviso_docx else OK),
            '; '.join(dict.fromkeys(probl)) or aviso_docx or f'{notas.getCount()} nota(s) conferida(s)')
    else:
        add('notas_rodape', NAO_SE_APLICA, 'Documento sem notas de rodapé.')
    # citações
    cits = a.por_tipo('citacao', zona='textual')
    longas = [el for el in corpo if el.texto.lstrip().startswith(('“', '"')) and len(el.texto) > 250]
    if cits:
        ruins = [el for el in cits if abs((_prop(el.obj, 'ParaLeftMargin', 0) or 0) - cm(p['citacao_recuo_cm'])) > 60]
        add('citacao_longa', FALHA if ruins else (AVISO if longas else OK),
            (f'{len(ruins)} citação(ões) sem recuo de 4 cm. ' if ruins else f'{len(cits)} citação(ões) com recuo de 4 cm. ')
            + (f'{len(longas)} parágrafo(s) longo(s) entre aspas podem ser citações longas sem formatação.' if longas else ''),
            [el.i for el in (ruins + longas)[:20]])
    else:
        add('citacao_longa', AVISO if longas else NAO_SE_APLICA,
            f'{len(longas)} parágrafo(s) longo(s) entre aspas podem ser citações longas sem formatação.' if longas else
            'Nenhuma citação longa identificada (estilo Citação ou recuo de 3 cm ou mais).', [el.i for el in longas[:20]])
    # ilustrações e tabelas
    probl, locais, total = [], [], 0

    def vizinho(i, passo):
        j = i + passo
        while 0 <= j < len(els) and els[j].tipo == 'vazio':
            j += passo
        return els[j] if 0 <= j < len(els) else None

    for el in els:
        if el.tipo in ('tabela', 'objeto') or (el.tipo == 'texto' and el.objeto):
            total += 1
            antes, depois = vizinho(el.i, -1), vizinho(el.i, 1)
            if not (antes is not None and antes.tipo == 'legenda'):
                probl.append(f'{"tabela" if el.tipo == "tabela" else "ilustração"} sem identificação acima')
                locais.append(el.i)
            if not (depois is not None and depois.tipo == 'fonte_legenda'):
                probl.append(f'{"tabela" if el.tipo == "tabela" else "ilustração"} sem fonte abaixo')
                locais.append(el.i)
    try:
        quadros = doc.getTextFrames()
        for k in range(quadros.getCount()):
            q = quadros.getByIndex(k)
            pars = list(_pars_texto(q.getText()))
            idx_obj = [n for n, x in enumerate(pars) if _tem_objeto(x)]
            idx_leg = [n for n, x in enumerate(pars) if _re_legenda().match(x.getString().strip())]
            if idx_obj:
                total += 1
                if idx_leg and idx_leg[0] > idx_obj[0]:
                    probl.append('legenda abaixo da ilustração (dentro de um quadro); a norma pede a identificação acima')
                elif not idx_leg:
                    probl.append('ilustração em quadro sem identificação')
    except Exception:
        pass
    legs = a.por_tipo('legenda') + a.por_tipo('fonte_legenda')
    alins = {_alin(el.obj) for el in legs + [o for o in a.por_tipo('objeto') if o.zona != 'pre']}
    if len(alins) > 1:
        probl.append('alinhamento das legendas não é uniforme')
    if total or legs:
        resumo = {}
        for x in probl:
            resumo[x] = resumo.get(x, 0) + 1
        add('ilustracoes', FALHA if probl else OK, '; '.join(f'{n}× {x}' for x, n in resumo.items()) or f'{total} ilustração(ões) e tabela(s) com identificação e fonte',
            locais[:20])
    else:
        add('ilustracoes', NAO_SE_APLICA, 'Documento sem ilustrações nem tabelas.')
    # referências
    if refs:
        ruins = [el for el in refs if _alin(el.obj) != ESQ or _ls(el.obj) != (0, 100)]
        separadas = all((_prop(el.obj, 'ParaBottomMargin', 0) or 0) >= pt(8) or (el.i + 1 < len(els) and els[el.i + 1].tipo == 'vazio')
                        for el in refs[:-1])
        add('referencias_apresentacao', FALHA if ruins or not separadas else OK,
            (f'{len(ruins)} referência(s) não alinhada(s) à esquerda ou sem espaço simples. ' if ruins else '') +
            ('Referências não separadas por um espaço em branco.' if not separadas else '') or f'{len(refs)} referência(s) conferida(s)',
            [el.i for el in ruins[:20]])
    else:
        add('referencias_apresentacao', FALHA if any('REFERÊNCIAS' in g for g in perfil['estrutura']['obrigatorios']) else NAO_SE_APLICA,
            'Nenhuma referência identificada depois do título REFERÊNCIAS.')
    add('referencias_conteudo', NAO_VERIFICAVEL, 'Confira cada referência pela NBR 6023:2025. O AY não cria, completa nem corrige dados de referências.')
    # sumário
    if a.sumario is None:
        add('sumario', FALHA if any('SUMÁRIO' in g for g in perfil['estrutura']['obrigatorios']) else NAO_SE_APLICA, 'Título SUMÁRIO não encontrado.')
    elif a.sumario_manual:
        add('sumario', AVISO, 'Sumário digitado à mão: troque pelo sumário automático (Referências › Sumário e índices).', [a.sumario.i])
    elif not a.indice_existente:
        add('sumario', FALHA, 'Título SUMÁRIO sem sumário automático depois dele.', [a.sumario.i])
    else:
        add('sumario', OK, 'Sumário automático presente (atualize antes de entregar).')
    # estrutura
    titulos_doc = {_norm(el.texto) for el in a.por_tipo('titulo_pre', 'titulo_pos', 'titulo', 'texto', 'pre_texto') if len(el.texto) < 80}
    for grupo in perfil['estrutura']['obrigatorios']:
        achou = any(any(t == g or t.startswith(g + ':') for t in titulos_doc) for g in grupo)
        if not achou and 'PALAVRAS-CHAVE' in grupo:
            achou = any(_norm(el.texto).startswith('PALAVRAS-CHAVE') for el in els if el.tipo != 'tabela')
        itens.append(Item('estrutura', f'Elemento: {grupo[0].capitalize()}', OK if achou else FALHA,
                          'encontrado' if achou else f'não encontrei o título {" ou ".join(grupo)}', 'norma',
                          'Norma: ' + rotulo_norma(perfil['norma']) + (', conforme ' + ', '.join(normas()['fontes'][f]['nome'].split('.')[0]
                                                                          for f in perfil['fontes_estrutura']) if perfil['fontes_estrutura'] else '')))
    for nv in perfil['estrutura']['nao_verificaveis']:
        itens.append(Item('estrutura', f'Elemento: {nv}', NAO_VERIFICAVEL, 'confira manualmente', 'norma', 'Norma: ' + rotulo_norma(perfil['norma'])))
    # preferências sem conferência automática
    for rid in ('fonte_menor_tamanho', 'recuo_paragrafo', 'alinhamento', 'destaques_escolhidos'):
        r = R[rid]
        itens.append(Item(rid, r['titulo'], NAO_VERIFICAVEL if r['camada'] != 'preferencia' else 'preferência', r['regra'], r['camada'], origem(r, perfil)))
    return itens


SIMBOLOS = {OK: '✓', FALHA: '✗', AVISO: '!', NAO_VERIFICAVEL: '?', NAO_SE_APLICA: '–', 'preferência': '·'}
CAMADAS = {'norma': 'Norma', 'instituicao': 'Instituição', 'preferencia': 'Preferência'}


def linha_item(it):
    return f'{SIMBOLOS.get(it.situacao, " ")} {it.titulo} — {it.situacao}'


def detalhe_item(it, perfil):
    r = perfil['regras'].get(it.regra)
    partes = [f'{it.titulo}: {it.situacao}.']
    if it.detalhe:
        partes.append(it.detalhe)
    if r is not None and it.regra != 'estrutura':
        partes.append(f'Regra: {r["regra"]}')
    partes.append(f'Camada: {CAMADAS.get(it.camada, it.camada)}. Origem: {it.origem}.')
    if it.locais:
        partes.append(f'{len(it.locais)} local(is) no documento: use "Ir para".')
    return '\n'.join(partes)


def cabecalho_relatorio(perfil):
    return (f'Perfil: {perfil["nome"]} ({rotulo_norma(perfil["norma"])}). Normas conferidas no catálogo da ABNT em '
            f'{_data_br(normas()["verificado_em"])}. O texto das normas é vendido pela ABNT: as regras vêm de guias públicos '
            'de bibliotecas (ver Ajuda). Confira com a norma oficial e com o manual da sua instituição.')


def _data_br(iso):
    a, m, d = iso.split('-')
    return f'{d}/{m}/{a}'


def documento_relatorio(desktop, itens, perfil, nome_documento='', extra=()):
    """Novo documento (sem título) com o relatório de conformidade, para imprimir ou guardar."""
    rel = desktop.loadComponentFromURL('private:factory/swriter', '_blank', 0, tuple(extra))
    texto = rel.getText()
    cur = texto.createTextCursor()

    def par(t, estilo='Standard'):
        cur.setPropertyValue('ParaStyleName', estilo)
        texto.insertString(cur, t, False)
        texto.insertControlCharacter(cur, 0, False)
    par('Relatório de conformidade', 'Title')
    if nome_documento:
        par(f'Documento: {nome_documento}')
    par(f'Gerado em {time.strftime("%d/%m/%Y %H:%M")} pelo AY ESCREVA.')
    par(cabecalho_relatorio(perfil))
    c = resumo_itens(itens)
    par('Resumo: ' + ', '.join(f'{n} {k}' for k, n in c.items()) + '.')
    tab = rel.createInstance('com.sun.star.text.TextTable')
    tab.initialize(len(itens) + 1, 5)
    texto.insertTextContent(cur, tab, False)
    for col, t in enumerate(('Regra', 'Situação', 'Camada', 'Origem', 'Detalhe')):
        tab.getCellByPosition(col, 0).setString(t)
    for lin, it in enumerate(itens, 1):
        for col, t in enumerate((it.titulo, it.situacao, CAMADAS.get(it.camada, it.camada), it.origem, it.detalhe)):
            tab.getCellByPosition(col, lin).setString(t or '')
    rel.setModified(False)
    return rel


def resumo_itens(itens):
    c = {}
    for it in itens:
        c[it.situacao] = c.get(it.situacao, 0) + 1
    return c


def ir_para(doc, analise, i):
    """Seleciona no documento o elemento de índice i (para "Ir para" no relatório)."""
    el = analise.elementos[i]
    ctrl = doc.getCurrentController()
    if el.tipo == 'tabela':
        ctrl.select(el.obj)
    else:
        ctrl.select(el.obj.getStart())
        vc = ctrl.getViewCursor()
        vc.gotoRange(el.obj.getEnd(), True)
