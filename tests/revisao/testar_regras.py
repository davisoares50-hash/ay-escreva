# -*- coding: utf-8 -*-
"""Testes das regras puras da revisão (sem o aplicativo): decisão da correção automática com todas as proteções,
conteúdo da tabela de casos inequívocos e sugestões de estilo.

Uso: "dist\\AY ESCREVA\\program\\python.exe" tests\\revisao\\testar_regras.py
SPDX-License-Identifier: MPL-2.0
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'extensao' / 'ayescreva' / 'pythonpath'))
import ay_correcao  # noqa: E402
import ay_estilo  # noqa: E402

itens = []


def verificar(descricao, ok, detalhe=''):
    itens.append({'ok': bool(ok), 'verificacao': descricao, 'detalhe': str(detalhe)})
    print(f"[{'OK  ' if ok else 'FALHA'}] {descricao}{' — ' + str(detalhe) if detalhe else ''}")


def main():
    tab = ay_correcao.Tabela(ay_correcao.caminho_padrao())
    dados = json.loads(Path(ay_correcao.caminho_padrao()).read_text(encoding='utf-8'))
    verificar('tabela carregada, com origem e critérios registrados', len(tab) > 1000 and dados['criterios'] and dados['origem'],
              f'{len(tab)} correções; {dados["totais"]["por_classe"]}')
    simples = re.compile(r'^[a-zà-öø-ÿ]+$')
    verificar('tabela só tem palavras simples em minúsculas (sem abreviações, símbolos ou várias palavras)',
              all(simples.match(k) and simples.match(v) for k, v in tab.correcoes.items()))
    for ausente in ('vc', 'tbm', 'pq', 'so', 'ate', 'e', 'esta', 'musica', 'agua'):
        if ausente in tab.correcoes:
            verificar(f'"{ausente}" fora da tabela (abreviação ou palavra válida)', False, tab.correcoes[ausente])
    verificar('abreviações e palavras válidas ficam fora da tabela (vc, tbm, pq, so, ate, e, esta, musica, agua)',
              not any(k in tab.correcoes for k in ('vc', 'tbm', 'pq', 'so', 'ate', 'e', 'esta', 'musica', 'agua')))

    def d(palavra, **kw):
        base = {'inicio_de_frase': False, 'prefixo': 'Texto ', 'idioma_ptbr': True, 'nao_corrigir': (), 'valida': None}
        base.update(kw)
        return ay_correcao.decidir(palavra, tab, **base)

    casos = [
        ('nao', {}, 'não', 'acentuação no meio da frase'),
        ('voce', {}, 'você', 'acentuação'),
        ('tambem', {}, 'também', 'acentuação vinda do dicionário'),
        ('geito', {}, 'jeito', 'erro de digitação inequívoco'),
        ('Nao', {'inicio_de_frase': True}, 'Não', 'início de frase mantém a maiúscula'),
        ('Nao', {}, None, 'maiúscula no meio da frase = nome próprio'),
        ('NAO', {'inicio_de_frase': True}, None, 'sigla'),
        ('naO', {}, None, 'grafia mista (termo técnico ou marca)'),
        ('nao2', {}, None, 'com dígito'),
        ('12/10/2025', {}, None, 'data'),
        ('3,5', {}, None, 'número'),
        ('nao', {'prefixo': 'Ele disse “eu '}, None, 'dentro de citação (aspas curvas)'),
        ('nao', {'prefixo': 'Ele disse "eu '}, None, 'dentro de citação (aspas retas)'),
        ('nao', {'prefixo': 'Ele disse “sim” e '}, 'não', 'depois de uma citação fechada volta a corrigir'),
        ('nao', {'idioma_ptbr': False}, None, 'texto marcado em outro idioma'),
        ('nao', {'nao_corrigir': {'nao'}}, None, '"não corrigir novamente"'),
        ('geito', {'valida': lambda p: True}, None, 'palavra do dicionário pessoal'),
        ('nao', {'estilo_protegido': True}, None, 'estilo de citação ou código'),
        ('casa', {}, None, 'palavra correta não muda'),
        ('esta', {}, None, 'palavra válida ambígua (esta/está) não muda'),
    ]
    for palavra, kw, esperado, descricao in casos:
        res, motivo = d(palavra, **kw)
        verificar(f'correção: {descricao} ("{palavra}" → {esperado!r})', res == esperado, f'{res!r} ({motivo})')

    t = ('Eu vou pra casa a fim de que possamos conversar, né. Devido ao fato de que choveu, ficamos. '
         'A análise mostrou que a análise anterior estava errada.')
    achados = ay_estilo.analisar(t)
    regras = {(a['regra'], a['original'].lower()) for a in achados}
    verificar('estilo: formalidade ("pra", "né")', ('ay-formalidade', 'pra') in regras and ('ay-formalidade', 'né') in regras)
    verificar('estilo: concisão ("a fim de que", "devido ao fato de que")',
              ('ay-concisao', 'a fim de que') in regras and ('ay-concisao', 'devido ao fato de que') in regras)
    verificar('estilo: "a fim de que" não gera também "a fim de" no mesmo trecho',
              sum(1 for a in achados if a['regra'] == 'ay-concisao' and a['inicio'] == t.index('a fim de que')) == 1)
    verificar('estilo: repetição próxima ("análise")', any(a['regra'] == 'ay-repeticao' and a['original'] == 'análise' for a in achados))
    verificar('estilo: toda sugestão tem explicação', all(a['mensagem'] for a in achados))
    longa = ' '.join(['palavra'] * 45) + '.'
    verificar('estilo: frase com mais de 40 palavras', any(a['regra'] == 'ay-frase-longa' for a in ay_estilo.analisar(longa)))
    verificar('estilo: texto limpo sem sugestões', ay_estilo.analisar('O relatório foi entregue ontem.') == [])
    verificar('estilo: "para" e "propor" não confundem com "pra"/"pro"',
              not any(a['regra'] == 'ay-formalidade' for a in ay_estilo.analisar('Vou para a reunião propor um plano.')))

    ok = sum(1 for i in itens if i['ok'])
    saida = RAIZ / 'tests' / 'output' / 'revisao'
    saida.mkdir(parents=True, exist_ok=True)
    (saida / 'regras.json').write_text(json.dumps({'itens': itens}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Regras da revisão: {ok}/{len(itens)} verificações aprovadas')
    return 0 if ok == len(itens) else 1


if __name__ == '__main__':
    sys.exit(main())
