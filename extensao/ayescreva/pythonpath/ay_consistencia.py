# -*- coding: utf-8 -*-
"""Conferir consistência do documento (entrega D), por regras fixas, sem IA; o AY só aponta e leva ao trecho.

  - o mesmo termo escrito de jeitos diferentes: com e sem hífen ("e-mail"/"email"), maiúscula e minúscula no meio da
    frase ("Internet"/"internet", "COVID-19"/"Covid-19"); diferenças de acento NÃO entram (mudam o sentido: e/é);
  - sigla usada antes de ser definida, ou definida de dois jeitos;
  - numeração de figuras, tabelas, quadros e gráficos: repetida, com salto, ou citada no texto sem existir;
  - datas em formatos diferentes (10/03/2025, 10 de março de 2025, 2025-03-10);
  - "%" e "por cento" no mesmo documento; aspas retas e curvas misturadas.
A seção REFERÊNCIAS fica de fora (lá, maiúsculas e grafias seguem a NBR 6023). Tabelas, notas e caixas de texto
também ficam de fora nesta versão.
SPDX-License-Identifier: MPL-2.0
"""
import re
from collections import Counter, defaultdict

import ay_referencias as R

RE_PALAVRA = re.compile(r"[\wÀ-ÿ][\wÀ-ÿ'’-]*[\wÀ-ÿ]|[\wÀ-ÿ]")
RE_DEF_SIGLA = re.compile(r"((?:[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ'’-]*\s+(?:(?:de|da|do|das|dos|e|para|em)\s+)?){2,})\(([A-Z]{2,}[A-Za-z0-9]*)\)")
RE_SIGLA = re.compile(r'\b[A-Z]{2,}[A-Z0-9]*\b')
RE_LEGENDA = re.compile(r'^\s*(Figura|Tabela|Quadro|Gráfico)\s+(\d+)\b')
RE_CHAMADA = re.compile(r'\b(Figura|Tabela|Quadro|Gráfico)\s+(\d+)\b')
MESES = 'janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro'
FORMATOS_DATA = {'dia/mês/ano (10/03/2025)': re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b'),
                 'por extenso (10 de março de 2025)': re.compile(rf'\b\d{{1,2}}º?\s+de\s+(?:{MESES})\s+de\s+\d{{4}}\b', re.I),
                 'ano-mês-dia (2025-03-10)': re.compile(r'\b\d{4}-\d{2}-\d{2}\b')}
SIGLAS_COMUNS = {'PDF', 'DOCX', 'ODT', 'DOC', 'RTF', 'TXT', 'HTML', 'URL', 'CPF', 'CNPJ', 'CEP', 'RG', 'ABNT', 'NBR', 'ISO', 'ISBN',
                 'ISSN', 'DOI', 'EUA', 'ONU', 'OK', 'TV', 'PC', 'CD', 'DVD', 'USB', 'IA', 'II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX',
                 'XI', 'XII', 'XX', 'XXI', 'LTDA', 'SA'}


def _inicio_de_frase(texto, pos):
    antes = texto[:pos].rstrip()
    return not antes or antes[-1] in '.!?:;—–-\n' or antes.endswith('"') or antes.endswith('“')


def conferir(pars):
    """pars: [{'texto', 'titulo'}]. Achados: [{'nivel', 'categoria', 'texto', 'par', 'ini', 'fim'}]."""
    i_ref, entradas = R.secao_referencias(pars)
    fora = set(entradas) | ({i_ref} if i_ref is not None else set())
    corpo = [(i, p['texto']) for i, p in enumerate(pars) if i not in fora and p['texto'].strip()]
    texto_corrido = [(i, t) for i, t in corpo if not pars[i].get('titulo') and not (t.isupper() and len(t) < 80)]
    achados = []

    def add(nivel, categoria, texto, par, ini=0, fim=None):
        achados.append({'nivel': nivel, 'categoria': categoria, 'texto': texto, 'par': par, 'ini': ini,
                        'fim': fim if fim is not None else len(pars[par]['texto'])})

    # 1. grafias diferentes do mesmo termo
    formas = defaultdict(Counter)
    onde = {}
    for i, t in texto_corrido:
        for m in RE_PALAVRA.finditer(t):
            w = m.group(0)
            if len(w) < 3 or w.isdigit():
                continue
            if _inicio_de_frase(t, m.start()) and w[1:] == w[1:].lower():
                continue                               # maiúscula de início de frase não conta
            chave = w.lower().replace('-', '').replace('’', "'")
            formas[chave][w] += 1
            onde.setdefault((chave, w), (i, m.start(), m.end()))
    for chave, c in sorted(formas.items()):
        if len(c) < 2:
            continue
        variantes = sorted(c, key=lambda w: -c[w])
        so_caixa = len({v.lower() for v in variantes}) == 1
        if so_caixa and all(v.isupper() or v[:1].isupper() and v[1:] == v[1:].lower() for v in variantes) and not any(
                ch.isdigit() for ch in chave):
            # "Estado"/"estado": maiúscula no meio da frase pode ser nome próprio; só avisa se for frequente dos dois jeitos
            if min(c.values()) < 2:
                continue
        i, ini, fim = onde[(chave, variantes[-1])]
        desc = ', '.join(f'"{v}" ({c[v]}×)' for v in variantes)
        add('aviso', 'Grafia', f'O mesmo termo aparece escrito de jeitos diferentes: {desc}. Escolha uma forma.', i, ini, fim)

    # 2. siglas
    definicoes = {}
    for i, t in texto_corrido:
        for m in RE_DEF_SIGLA.finditer(t):
            s, extenso = m.group(2), ' '.join(m.group(1).split())
            extenso = re.sub(r'^(?:(?:O|A|Os|As|Um|Uma|No|Na|Nos|Nas|Do|Da|Dos|Das|Pelo|Pela|Ao|À)\s+)+', '', extenso)
            if s in definicoes and R.norm(definicoes[s][0]) != R.norm(extenso):
                add('aviso', 'Sigla', f'{s} definida de dois jeitos: "{definicoes[s][0]}" e "{extenso}".', i, m.start(), m.end())
            definicoes.setdefault(s, (extenso, i, m.start(2)))
    for s, (extenso, i_def, pos_def) in definicoes.items():
        for i, t in texto_corrido:
            if i > i_def:
                break
            for m in RE_SIGLA.finditer(t):
                if m.group(0) == s and (i < i_def or m.start() < pos_def - 1):
                    add('aviso', 'Sigla', f'{s} é usada antes de ser definida ("{extenso} ({s})").', i, m.start(), m.end())
                    break
            else:
                continue
            break

    # 3. numeração de figuras, tabelas, quadros e gráficos
    legendas = defaultdict(list)
    for i, t in corpo:
        m = RE_LEGENDA.match(t)
        if m:
            legendas[m.group(1)].append((int(m.group(2)), i))
    for tipo, lst in legendas.items():
        nums = [n for n, _ in lst]
        for n, c in Counter(nums).items():
            if c > 1:
                i = [j for k, j in lst if k == n][1]
                add('aviso', 'Numeração', f'{tipo} {n} aparece em {c} legendas.', i)
        faltam = sorted(set(range(1, max(nums) + 1)) - set(nums))
        if faltam:
            add('aviso', 'Numeração', f'{tipo}s numeradas com salto: falta {tipo.lower()} ' + ', '.join(map(str, faltam)) + '.', lst[0][1])
    for i, t in texto_corrido:
        if RE_LEGENDA.match(t):
            continue
        for m in RE_CHAMADA.finditer(t):
            tipo, n = m.group(1), int(m.group(2))
            if n not in [k for k, _ in legendas.get(tipo, [])]:
                add('aviso', 'Numeração', f'"{m.group(0)}" é citada no texto, mas não há legenda com esse número.', i, m.start(), m.end())

    # 4. datas, porcentagens e aspas
    usados = {}
    for nome, rx in FORMATOS_DATA.items():
        for i, t in texto_corrido:
            m = rx.search(t)
            if m:
                usados[nome] = (i, m.start(), m.end(), m.group(0))
                break
    if len(usados) > 1:
        primeiro = min(usados.values())
        add('informação', 'Datas', 'Datas escritas em formatos diferentes: ' + '; '.join(f'{k}, ex.: {v[3]}' for k, v in usados.items())
            + '. Use um formato só.', primeiro[0], primeiro[1], primeiro[2])
    pct = [(i, t.find('%')) for i, t in texto_corrido if '%' in t]
    extenso = [(i, R.norm(t).find('por cento')) for i, t in texto_corrido if 'por cento' in R.norm(t)]
    if pct and extenso:
        add('informação', 'Números', 'Porcentagens escritas com "%" e com "por cento" no mesmo documento.', extenso[0][0], extenso[0][1],
            extenso[0][1] + 9)
    retas = [(i, t.find('"')) for i, t in texto_corrido if '"' in t]
    curvas = [i for i, t in texto_corrido if '“' in t or '”' in t]
    if retas and curvas:
        add('informação', 'Aspas', 'Aspas retas (") e curvas (“ ”) misturadas.', retas[0][0], retas[0][1], retas[0][1] + 1)
    return achados
