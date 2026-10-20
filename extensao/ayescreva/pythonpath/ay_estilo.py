# -*- coding: utf-8 -*-
"""Sugestões de estilo do AY (pt-BR), offline e opcionais: clareza, concisão, formalidade, repetição e
organização. Cada sugestão traz uma explicação curta; nada é aplicado sozinho. Puro Python, sem UNO.
SPDX-License-Identifier: MPL-2.0
"""
import re

PALAVRA = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:-[A-Za-zÀ-ÖØ-öø-ÿ]+)*")
FIM_FRASE = re.compile(r'[.!?…]+["”’»)]*\s+|[.!?…]+["”’»)]*$')

LIMITE_FRASE = 40
LIMITE_PARAGRAFO = 200
JANELA_REPETICAO = 12

# (expressão, sugestão, explicação)
PROLIXAS = [
    (r'a fim de que', 'para que', 'Forma mais curta com o mesmo sentido.'),
    (r'a fim de', 'para', 'Forma mais curta com o mesmo sentido.'),
    (r'devido ao fato de que', 'porque', 'Locução longa; "porque" diz o mesmo.'),
    (r'pelo fato de que', 'porque', 'Locução longa; "porque" diz o mesmo.'),
    (r'em virtude do fato de que', 'porque', 'Locução longa; "porque" diz o mesmo.'),
    (r'no sentido de', 'para', 'Em geral pode ser trocado por "para" ou omitido.'),
    (r'levar em consideração', 'considerar', 'Um verbo só diz o mesmo.'),
    (r'tomar uma decisão', 'decidir', 'Um verbo só diz o mesmo.'),
    (r'(?:fazer|realizar) uma análise', 'analisar', 'Um verbo só diz o mesmo.'),
    (r'(?:fazer|realizar) uma avaliação', 'avaliar', 'Um verbo só diz o mesmo.'),
    (r'nos dias de hoje', 'hoje', 'Forma mais curta com o mesmo sentido.'),
    (r'no presente momento', 'atualmente', 'Forma mais curta com o mesmo sentido.'),
    (r'é importante ressaltar que', '', 'Introdução que costuma poder ser omitida: diga diretamente o que importa.'),
    (r'a nível de', 'em termos de', '"A nível de" é condenado pela norma culta; prefira "em termos de", "no âmbito de" ou "em".'),
]

# (palavra ou expressão, sugestão, explicação)
INFORMAIS = [
    (r'pra', 'para', 'Marca de oralidade; em texto formal use "para".'),
    (r'pro', 'para o', 'Marca de oralidade; em texto formal use "para o".'),
    (r'pros', 'para os', 'Marca de oralidade; em texto formal use "para os".'),
    (r'tá', 'está', 'Marca de oralidade; em texto formal use "está".'),
    (r'tô', 'estou', 'Marca de oralidade; em texto formal use "estou".'),
    (r'né', '', 'Marca de oralidade; em texto formal costuma ser omitida.'),
    (r'a gente', 'nós', 'Em texto formal prefira "nós" (com o verbo na 1ª pessoa do plural).'),
    (r'tipo assim', '', 'Marca de oralidade; em texto formal costuma ser omitida.'),
    (r'vc', 'você', 'Abreviação informal.'),
    (r'tb|tbm', 'também', 'Abreviação informal.'),
    (r'pq', 'porque / por que', 'Abreviação informal; escolha "porque" (explicação) ou "por que" (pergunta).'),
]

FUNCIONAIS = set('''a o as os um uma uns umas de do da dos das em no na nos nas por pelo pela pelos pelas para com sem sob
sobre entre até após ante e ou mas que se como quando onde porque pois nem já não sim mais menos muito muita muitos muitas
pouco pouca ser estar ter haver fazer foi é são era eram está estão tem têm há isso isto aquilo esse essa este esta aquele
aquela seu sua seus suas meu minha nosso nossa ele ela eles elas eu tu você vocês nós lhe lhes me te nos vos também ainda
cada todo toda todos todas outro outra outros outras mesmo mesma qual quais quem cujo cuja sendo sido tendo havia'''.split())


def _achados_expressoes(texto, lista, categoria, regra):
    ocupados = []                      # a expressão mais longa vem antes na lista e "ocupa" o trecho
    for padrao, sugestao, explicacao in lista:
        for m in re.finditer(r'(?<![\wÀ-ÿ])' + padrao + r'(?![\wÀ-ÿ])', texto, re.IGNORECASE):
            if any(m.start() < fim and ini < m.end() for ini, fim in ocupados):
                continue
            ocupados.append((m.start(), m.end()))
            yield {'inicio': m.start(), 'tamanho': m.end() - m.start(), 'nivel': 'estilo', 'categoria': categoria,
                   'original': m.group(0), 'sugestoes': [sugestao] if sugestao else [], 'regra': regra,
                   'mensagem': explicacao}


def frases(texto):
    """(início, fim) de cada frase do parágrafo."""
    inicio = 0
    for m in FIM_FRASE.finditer(texto):
        fim = m.end()
        if texto[inicio:fim].strip():
            yield inicio, fim
        inicio = fim
    if texto[inicio:].strip():
        yield inicio, len(texto)


def analisar(texto):
    """Lista de sugestões de estilo para um parágrafo."""
    achados = []
    achados += _achados_expressoes(texto, PROLIXAS, 'Estilo · concisão', 'ay-concisao')
    achados += _achados_expressoes(texto, INFORMAIS, 'Estilo · formalidade', 'ay-formalidade')
    for ini, fim in frases(texto):
        n = len(PALAVRA.findall(texto[ini:fim]))
        if n > LIMITE_FRASE:
            achados.append({'inicio': ini, 'tamanho': len(texto[ini:fim].rstrip()), 'nivel': 'estilo',
                            'categoria': 'Estilo · clareza', 'original': texto[ini:fim].strip()[:60] + '…',
                            'sugestoes': [], 'regra': 'ay-frase-longa',
                            'mensagem': f'Frase longa ({n} palavras). Frases com mais de {LIMITE_FRASE} palavras costumam ser difíceis de acompanhar; considere dividir.'})
    palavras = list(PALAVRA.finditer(texto))
    vistos = {}
    for i, m in enumerate(palavras):
        w = m.group(0)
        chave = w.lower()
        if len(chave) < 5 or chave in FUNCIONAIS or w[:1].isupper():
            continue
        anterior = vistos.get(chave)
        if anterior is not None and i - anterior <= JANELA_REPETICAO:
            achados.append({'inicio': m.start(), 'tamanho': len(w), 'nivel': 'estilo', 'categoria': 'Estilo · repetição',
                            'original': w, 'sugestoes': [], 'regra': 'ay-repeticao',
                            'mensagem': f'"{w}" aparece de novo a {i - anterior} palavras de distância; considere um sinônimo ou reorganizar a frase.'})
        vistos[chave] = i
    total = len(palavras)
    if total > LIMITE_PARAGRAFO:
        achados.append({'inicio': 0, 'tamanho': min(len(texto), 80), 'nivel': 'estilo', 'categoria': 'Estilo · organização',
                        'original': texto[:60] + '…', 'sugestoes': [], 'regra': 'ay-paragrafo-longo',
                        'mensagem': f'Parágrafo longo ({total} palavras); considere dividir em parágrafos menores, um por ideia.'})
    achados.sort(key=lambda a: a['inicio'])
    return achados
