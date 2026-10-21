# -*- coding: utf-8 -*-
"""Conferir referências (entrega D): citações do texto × lista de referências, por regras fixas, sem IA.

O AY só aponta e leva ao trecho: nunca cria, completa nem corrige uma referência (os dados vêm da obra consultada).
Confere:
  - citação no texto (autor-data, NBR 10520) sem referência correspondente na lista;
  - referência na lista que não é citada no texto (informação);
  - referência sem ano identificável (nem "[s. d.]");
  - documento on-line sem "Disponível em:" ou sem "Acesso em:" (NBR 6023);
  - entrada que começa com minúscula, entradas repetidas, fora da ordem alfabética;
  - mesmo autor e ano em obras diferentes sem letra (2019a, 2019b).
As funções trabalham sobre textos de parágrafos (testáveis sem o motor); coletar() lê o documento.
SPDX-License-Identifier: MPL-2.0
"""
import re
import unicodedata

TITULOS_REFERENCIAS = ('referencias', 'referencias bibliograficas', 'bibliografia', 'referencias e bibliografia', 'obras citadas')
RE_ANO = re.compile(r'(?<![\d/.,])(1[5-9]\d\d|20\d\d)([a-z])?(?![\d])')
RE_SEM_DATA = re.compile(r'\[?\s*s\.\s*d\.\s*\]?', re.I)
RE_URL = re.compile(r'\b(?:https?://|www\.)\S+', re.I)
RE_PARENTESES = re.compile(r'\(([^()]{2,200})\)')
RE_NARRATIVA = re.compile(r"\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ'’-]+(?:\s+(?:e|&)\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ'’-]+)?(?:\s+et\s+al\.)?)"
                          r"\s*\((\d{4}[a-z]?)(?:\s*,\s*p\.\s*[\d\-–]+)?\)")
NAO_AUTORES = {'figura', 'tabela', 'quadro', 'grafico', 'gráfico', 'anexo', 'apendice', 'apêndice', 'lei', 'art', 'artigo',
               'janeiro', 'fevereiro', 'marco', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro',
               'novembro', 'dezembro', 'em', 'no', 'na', 'de', 'do', 'da', 'ate', 'até', 'desde', 'entre', 'segundo', 'conforme'}


def norm(t):
    t = unicodedata.normalize('NFD', t or '')
    return ''.join(c for c in t if unicodedata.category(c) != 'Mn').lower().strip()


def chave_autor(autor):
    """Sobrenome ou entidade que identifica a obra: 'SILVA', 'Silva et al.', 'BRASIL. Ministério…' → 'silva'/'brasil'."""
    a = re.sub(r'\bet\s+al\.?', '', autor).strip()
    a = re.split(r'[,.;]|\s+(?:e|&)\s+', a)[0]
    return norm(a).split()[0] if norm(a).split() else ''


def citacoes(texto):
    """Citações autor-data do parágrafo: [(chave_autor, ano, início, fim, como aparece)]."""
    achadas = []
    for m in RE_PARENTESES.finditer(texto):
        dentro = m.group(1)
        if not RE_ANO.search(dentro):
            continue
        pendentes = []
        for seg in dentro.split(';'):
            a = RE_ANO.search(seg)
            if not a:
                if seg.strip():
                    pendentes.append(seg.strip())       # coautor: (SILVA; SOUZA, 2019)
                continue
            antes = seg[:a.start()].strip().rstrip(',').strip()
            palavras = antes.split()
            # "(conforme SILVA, 2019)": o autor começa na primeira palavra com inicial maiúscula
            k0 = next((n for n, w in enumerate(palavras) if w[:1].isupper()), len(palavras))
            autor = pendentes[0] if pendentes else ' '.join(palavras[k0:])
            pendentes = []
            k = chave_autor(autor)
            if k and k not in NAO_AUTORES and not k[0].isdigit() and autor[:1].isupper():
                achadas.append((k, a.group(1) + (a.group(2) or ''), m.start(), m.end(), m.group(0)))
    for m in RE_NARRATIVA.finditer(texto):
        k = chave_autor(m.group(1))
        if k and k not in NAO_AUTORES and not any(c[2] <= m.start(2) < c[3] for c in achadas):
            achadas.append((k, m.group(2), m.start(), m.end(), m.group(0)))
    return achadas


def chaves_referencia(entrada):
    """(chaves do autor/entidade, anos) de uma entrada da lista de referências."""
    primeira = re.split(r'[.]\s', entrada, maxsplit=1)[0]
    chaves = {chave_autor(entrada)}
    sigla = re.search(r'\(([A-Z]{2,}[A-Z0-9]*)\)', primeira)
    if sigla:
        chaves.add(norm(sigla.group(1)))
    anos = {a.group(1) + (a.group(2) or '') for a in RE_ANO.finditer(entrada)}
    anos |= {a.group(1) for a in RE_ANO.finditer(entrada)}
    return {c for c in chaves if c}, anos


def e_titulo_referencias(texto):
    return norm(texto).rstrip(':').strip() in TITULOS_REFERENCIAS


def secao_referencias(pars):
    """pars: [{'texto', 'titulo'}]. Devolve (índice do título REFERÊNCIAS, [índices das entradas]) ou (None, [])."""
    for i, p in enumerate(pars):
        if e_titulo_referencias(p['texto']):
            entradas = []
            for j in range(i + 1, len(pars)):
                t = pars[j]['texto'].strip()
                if pars[j].get('titulo') or re.match(r'(APÊNDICE|ANEXO|GLOSSÁRIO|ÍNDICE)\b', t):
                    break
                if t:
                    entradas.append(j)
            return i, entradas
    return None, []


def conferir(pars):
    """Achados: [{'nivel': 'aviso'|'informação', 'categoria', 'texto', 'par', 'ini', 'fim'}]."""
    achados = []

    def add(nivel, categoria, texto, par, ini=0, fim=None):
        achados.append({'nivel': nivel, 'categoria': categoria, 'texto': texto, 'par': par, 'ini': ini,
                        'fim': fim if fim is not None else len(pars[par]['texto']) if par is not None else 0})
    i_titulo, entradas = secao_referencias(pars)
    lista = set(entradas)
    cits = []
    for i, p in enumerate(pars):
        if i in lista or i == i_titulo or p.get('titulo'):
            continue
        for c in citacoes(p['texto']):
            cits.append((i,) + c)
    if i_titulo is None:
        if cits:
            add('aviso', 'Referências', f'Há {len(cits)} citação(ões) no texto, mas não foi encontrada a seção REFERÊNCIAS.', cits[0][0],
                cits[0][3], cits[0][4])
        return achados
    refs = []
    vistos = {}
    anterior = None
    for j in entradas:
        t = pars[j]['texto'].strip()
        chaves, anos = chaves_referencia(t)
        refs.append((j, chaves, anos))
        if not RE_ANO.search(t) and not RE_SEM_DATA.search(t):
            add('aviso', 'Referência', 'Sem ano identificável (nem "[s. d.]"): confira a data da obra.', j)
        if RE_URL.search(t):
            if 'disponivel em' not in norm(t):
                add('aviso', 'Referência', 'Documento on-line sem "Disponível em:" antes do endereço (NBR 6023).', j)
            if 'acesso em' not in norm(t):
                add('aviso', 'Referência', 'Documento on-line sem "Acesso em:" e a data de acesso (NBR 6023).', j)
        if t[:1].islower():
            add('aviso', 'Referência', 'A entrada começa com letra minúscula: deve começar pelo sobrenome (em maiúsculas), pela '
                                       'entidade ou pelo título.', j)
        n = re.sub(r'\W+', ' ', norm(t)).strip()
        if n in vistos:
            add('aviso', 'Referência', 'Entrada repetida na lista.', j)
        vistos[n] = j
        if anterior is not None and n[:40] < anterior[:40]:
            add('aviso', 'Referência', 'Fora da ordem alfabética (no sistema autor-data, a lista segue a ordem alfabética).', j)
        anterior = n
    # mesmo autor e mesmo ano em obras diferentes, sem letra
    por_autor_ano = {}
    for j, chaves, anos in refs:
        for k in chaves:
            for a in anos:
                if a.isdigit():
                    por_autor_ano.setdefault((k, a), []).append(j)
    for (k, a), js in sorted(por_autor_ano.items()):
        js = sorted(set(js))
        if len(js) > 1 and not any(f'{a}{l}' in pars[j]['texto'] for j in js for l in 'abcdef'):
            add('aviso', 'Referência', f'{len(js)} obras do mesmo autor ({k.upper()}) em {a}: diferencie com {a}a, {a}b… na lista e '
                                       'nas citações.', js[1])
    # citações × lista
    citadas = set()
    for i, k, ano, ini, fim, como in cits:
        ref = [j for j, chaves, anos in refs if k in chaves and (ano in anos or ano[:4] in anos)]
        if ref:
            citadas.update(ref)
        else:
            add('aviso', 'Citação', f'{como} é citado no texto, mas não há referência de {k.upper()} ({ano}) na lista.', i, ini, fim)
    for j, chaves, anos in refs:
        if j not in citadas and cits:
            add('informação', 'Referência', 'Está na lista, mas nenhuma citação no texto foi associada a ela (confira se é '
                                            'citada de outra forma).', j)
    return achados


def coletar(doc):
    """Parágrafos do corpo do texto: [{'texto', 'titulo', 'obj'}] (tabelas, notas e caixas de texto ficam de fora)."""
    pars = []
    e = doc.getText().createEnumeration()
    while e.hasMoreElements():
        p = e.nextElement()
        if not p.supportsService('com.sun.star.text.Paragraph'):
            continue
        nivel = 0
        try:
            nivel = p.OutlineLevel
        except Exception:
            pass
        estilo = (p.ParaStyleName or '').lower()
        pars.append({'texto': p.getString(), 'titulo': nivel > 0 or estilo.startswith(('heading', 'título', 'titulo')), 'obj': p})
    return pars


def ir_para(doc, par, ini=0, fim=None):
    """Seleciona o trecho achado no documento."""
    p = par['obj']
    c = p.getText().createTextCursorByRange(p.getStart())
    c.goRight(ini, False)
    c.goRight(max(0, (fim if fim is not None else len(par['texto'])) - ini), True)
    doc.getCurrentController().select(c)
    return c
