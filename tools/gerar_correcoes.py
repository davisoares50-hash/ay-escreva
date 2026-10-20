# -*- coding: utf-8 -*-
"""Gera a tabela de correções automáticas INEQUÍVOCAS do AY (extensao/ayescreva/dados/correcoes_pt_BR.json).

Origem: lista de AutoCorreção pt-BR do motor (acor_pt-BR.dat, MPL-2.0), lida da base extraída em _cache\\base.
Cada entrada é conferida no corretor ortográfico do próprio motor (Hunspell) e só é aceita se:
  1. original e correção são palavras simples em minúsculas (sem abreviações, símbolos ou várias palavras);
  2. o original NÃO é palavra válida em pt-BR, pt-PT nem inglês (válida em outro idioma = ambígua; o espanhol fica
     de fora porque o AY só corrige texto marcado como pt-BR e palavras arcaicas como "nao" bloqueariam "não");
  3. a correção é palavra válida em pt-BR;
  4. a diferença é só de acentuação (qualquer tamanho), OU é erro de digitação de até 2 edições, em palavra
     de 4 letras ou mais, e a correção é a PRIMEIRA sugestão do Hunspell para o original.
Segunda classe, "acentuação (dicionário)": radicais do dicionário VERO em minúsculas, com acento, cuja forma sem
acento não é válida em pt-BR, pt-PT nem inglês e corresponde a UM só radical acentuado (ex.: "tambem" → "também").
Nomes próprios (radicais com maiúscula) ficam de fora. As rejeitadas ficam contadas por motivo no arquivo gerado.

Uso: "dist\\AY ESCREVA\\program\\python.exe" tools\\gerar_correcoes.py
SPDX-License-Identifier: MPL-2.0
"""
import json
import re
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'tests' / 'uno'))
from ay_uno import Motor  # noqa: E402

import uno  # noqa: E402

BL = '{http://openoffice.org/2001/block-list}'
PALAVRA = re.compile(r'^[a-zà-öø-ÿ]+$')


def sem_acento(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def distancia(a, b):
    ant = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i]
        for j, cb in enumerate(b, 1):
            atual.append(min(ant[j] + 1, atual[j - 1] + 1, ant[j - 1] + (ca != cb)))
        ant = atual
    return ant[-1]


def locale(lingua, pais):
    loc = uno.createUnoStruct('com.sun.star.lang.Locale')
    loc.Language, loc.Country = lingua, pais
    return loc


def main():
    lock = json.loads((RAIZ / 'base' / 'base.lock.json').read_text(encoding='utf-8-sig'))
    dat = RAIZ / '_cache' / 'base' / lock['versao'] / 'share' / 'autocorr' / 'acor_pt-BR.dat'
    with zipfile.ZipFile(dat) as z:
        raiz = ET.fromstring(z.read('DocumentList.xml'))
    entradas = [(b.get(BL + 'abbreviated-name'), b.get(BL + 'name')) for b in raiz.iter(BL + 'block')]
    rejeitadas = Counter()
    aceitas = {}
    classes = Counter()
    with Motor('correcoes') as m:
        # Serviço Hunspell direto: só o dicionário (sem listas do usuário) e sem a sobrecarga isValid(texto, short) do despachante
        sc = m.servico('com.sun.star.linguistic2.SpellChecker')
        ptbr = locale('pt', 'BR')
        outros = [loc for loc in (locale('pt', 'PT'), locale('en', 'US')) if sc.hasLocale(loc)]
        if not sc.hasLocale(ptbr):
            raise SystemExit('corretor pt-BR indisponível no motor')

        vazio = uno.Any('[]com.sun.star.beans.PropertyValue', ())     # sequência vazia tipada (exigida pela ponte UNO)

        def valida(p, loc):
            return uno.invoke(sc, 'isValid', (p, loc, vazio))
        for orig, corr in entradas:
            if orig in aceitas:
                continue
            if not orig or not corr or not PALAVRA.match(orig) or not PALAVRA.match(corr):
                rejeitadas['não é palavra simples em minúsculas (símbolo, abreviação composta, várias palavras)'] += 1
                continue
            if valida(orig, ptbr) or any(valida(orig, loc) for loc in outros):
                rejeitadas['original é palavra válida em pt-BR, pt-PT ou inglês (ambíguo)'] += 1
                continue
            if not valida(corr, ptbr):
                rejeitadas['correção não está no dicionário pt-BR'] += 1
                continue
            if sem_acento(orig) == sem_acento(corr):
                classe = 'acentuação'
            else:
                alt = uno.invoke(sc, 'spell', (orig, ptbr, vazio))
                sugestoes = list(alt.getAlternatives()) if alt is not None else []
                if len(orig) >= 4 and distancia(orig, corr) <= 2 and sugestoes[:1] == [corr]:
                    classe = 'digitação'
                else:
                    rejeitadas['não é inequívoco (abreviação, distância grande ou não é a 1ª sugestão do dicionário)'] += 1
                    continue
            aceitas[orig] = (corr, classe)
        # Segunda classe: acentuação a partir dos radicais do dicionário
        dic = RAIZ / '_cache' / 'base' / lock['versao'] / 'share' / 'extensions' / 'dict-pt-BR' / 'pt_BR.dic'
        grupos = {}
        for linha in dic.read_text(encoding='utf-8-sig').splitlines()[1:]:
            radical = linha.split('/', 1)[0].strip()
            if len(radical) >= 3 and PALAVRA.match(radical) and sem_acento(radical) != radical:
                grupos.setdefault(sem_acento(radical), set()).add(radical)
        for chave, formas in grupos.items():
            if chave in aceitas:
                continue
            if len(formas) != 1:
                rejeitadas['acentuação (dicionário): mais de uma forma acentuada possível'] += 1
                continue
            if valida(chave, ptbr) or any(valida(chave, loc) for loc in outros):
                rejeitadas['acentuação (dicionário): forma sem acento também é válida'] += 1
                continue
            aceitas[chave] = (next(iter(formas)), 'acentuação (dicionário)')
        classes = Counter(c for _, c in aceitas.values())
        aceitas = {k: v for k, (v, _c) in aceitas.items()}
        idiomas = ['pt-BR'] + [f'{loc.Language}-{loc.Country}' for loc in outros]
    saida = RAIZ / 'extensao' / 'ayescreva' / 'dados' / 'correcoes_pt_BR.json'
    saida.parent.mkdir(parents=True, exist_ok=True)
    dados = {
        'descricao': 'Correções automáticas inequívocas do AY ESCREVA (pt-BR). Gerado por tools/gerar_correcoes.py; não editar à mão.',
        'origem': f'acor_pt-BR.dat do LibreOffice {lock["versaoCompleta"]} (MPL-2.0), conferido no Hunspell do próprio motor',
        'gerado_em': date.today().isoformat(),
        'motor': lock['versaoCompleta'],
        'dicionarios_conferidos': idiomas,
        'criterios': [
            'original e correção são palavras simples em minúsculas',
            'original não é palavra válida em ' + ', '.join(idiomas),
            'correção é palavra válida em pt-BR',
            'diferença só de acentuação, ou erro de digitação de até 2 edições (palavra com 4+ letras) em que a correção é a 1ª sugestão do Hunspell',
            'acentuação (dicionário): radical VERO minúsculo e acentuado cuja forma sem acento é inválida e corresponde a um único radical',
        ],
        'totais': {'entradas_da_base': len(entradas), 'aceitas': len(aceitas), 'por_classe': dict(classes),
                   'rejeitadas_por_motivo': dict(rejeitadas)},
        'correcoes': dict(sorted(aceitas.items())),
    }
    texto = json.dumps({k: v for k, v in dados.items() if k != 'correcoes'}, ensure_ascii=False, indent=1)
    texto = texto[:-2] + ',\n "correcoes": ' + json.dumps(dados['correcoes'], ensure_ascii=False, separators=(',', ':')) + '\n}\n'
    saida.write_text(texto, encoding='utf-8')
    print(f'{len(aceitas)} correções aceitas de {len(entradas)} ({dict(classes)}); rejeitadas: {dict(rejeitadas)}')
    print(f'gravado em {saida}')


if __name__ == '__main__':
    main()
