# -*- coding: utf-8 -*-
"""Conferir referências e conferir consistência (entrega D): regras sem IA, sobre textos de exemplo.

Confere que cada problema plantado é apontado com o parágrafo certo e que trechos corretos NÃO são apontados (falsos
positivos), e que nada é criado ou alterado (as funções só leem).
Uso: python tests/documento/testar_conferencias.py   (qualquer Python 3.9+)
SPDX-License-Identifier: MPL-2.0
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'extensao' / 'ayescreva' / 'pythonpath'))
import ay_consistencia as C  # noqa: E402
import ay_referencias as R  # noqa: E402

itens = []


def verificar(descricao, ok, detalhe=''):
    itens.append({'ok': bool(ok), 'verificacao': descricao, 'detalhe': str(detalhe)})
    print(f"[{'OK  ' if ok else 'FALHA'}] {descricao}{' — ' + str(detalhe) if detalhe else ''}", flush=True)


def P(texto, titulo=False):
    return {'texto': texto, 'titulo': titulo}


TRABALHO = [
    P('1 INTRODUÇÃO', True),                                                                       # 0
    P('Segundo Silva (2019, p. 12), a formação pesa mais que o custo (IBGE, 2020).'),              # 1
    P('Outros autores discordam (SOUZA; LIMA, 2018; PEREIRA et al., 2021).'),                      # 2
    P('Como mostra Costa (2017), o tema é antigo; ver também (OLIVEIRA, 2022).'),                  # 3
    P('A Lei nº 10.406, de 2002, e o ano de (2019) não são citações.'),                            # 4
    P('REFERÊNCIAS', True),                                                                        # 5
    P('COSTA, Ana. Editores livres. 2. ed. São Paulo: Atlas, 2017.'),                              # 6
    P('INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE). Pesquisa. Rio de Janeiro: IBGE, 2020. '
      'Disponível em: https://www.ibge.gov.br/x. Acesso em: 10 mar. 2025.'),                       # 7
    P('PEREIRA, João et al. Formação. Revista X, v. 3, n. 2, p. 1-9, 2021.'),                      # 8
    P('SILVA, Maria. Custos. Brasília: Ed. UnB, 2019.'),                                           # 9
    P('ALMEIDA, Rui. Sem citação no texto. Recife: UFPE, 2015.'),                                  # 10
    P('SOUZA, Paulo; LIMA, Carla. Debate. Curitiba: UFPR, 2018. https://exemplo.org/debate'),      # 11
    P('ZANETTI, Lia. Obra sem data. Natal: EDUFRN.'),                                              # 12
    P('SILVA, Maria. Custos. Brasília: Ed. UnB, 2019.'),                                           # 13 repetida
    P('almeida, rui. começa com minúscula. 2010.'),                                                # 14
    P('APÊNDICE A – Questionário', True),                                                          # 15
]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = R.conferir(TRABALHO)
    txt = lambda par: [x['texto'] for x in a if x['par'] == par]
    i, entradas = R.secao_referencias(TRABALHO)
    verificar('Seção REFERÊNCIAS encontrada e termina no APÊNDICE', i == 5 and entradas == list(range(6, 15)), (i, entradas))
    c1 = R.citacoes(TRABALHO[1]['texto']) + R.citacoes(TRABALHO[2]['texto']) + R.citacoes(TRABALHO[3]['texto'])
    verificar('Citações reconhecidas: narrativa com página, entidade, coautores com ";", et al. e várias na mesma parênteses',
              {(k, y) for k, y, *_ in c1} == {('silva', '2019'), ('ibge', '2020'), ('souza', '2018'), ('pereira', '2021'),
                                              ('costa', '2017'), ('oliveira', '2022')}, [(k, y) for k, y, *_ in c1])
    verificar('Lei com ano e ano solto entre parênteses NÃO viram citação', R.citacoes(TRABALHO[4]['texto']) == [],
              R.citacoes(TRABALHO[4]['texto']))
    verificar('Citação sem referência na lista é apontada no lugar dela: OLIVEIRA (2022)',
              any('OLIVEIRA (2022)' in t for t in txt(3)), txt(3))
    verificar('Citações com referência não são apontadas (Silva, IBGE pela sigla, Souza e Lima, Pereira et al., Costa)',
              not any(x['categoria'] == 'Citação' and x['par'] in (1, 2) for x in a) and not any('COSTA' in t for t in txt(3)),
              [x['texto'] for x in a if x['par'] in (1, 2)])
    verificar('Referência não citada vira só informação (ALMEIDA)', any(x['nivel'] == 'informação' for x in a if x['par'] == 10), txt(10))
    verificar('Documento on-line sem "Disponível em" e sem "Acesso em" é apontado; o completo (IBGE) não',
              any('Disponível em' in t for t in txt(11)) and any('Acesso em' in t for t in txt(11)) and not txt(7), (txt(11), txt(7)))
    verificar('Referência sem ano é apontada (ZANETTI)', any('Sem ano' in t for t in txt(12)), txt(12))
    verificar('Entrada repetida é apontada', any('repetida' in t for t in txt(13)), txt(13))
    verificar('Entrada que começa com minúscula é apontada', any('minúscula' in t for t in txt(14)), txt(14))
    verificar('Ordem alfabética: o desvio é apontado (ZANETTI antes de SILVA)', any('ordem alfabética' in t for t in txt(13)),
              [x['par'] for x in a if 'ordem' in x['texto']])
    sem_secao = R.conferir([P('Texto com citação (SILVA, 2019).')])
    verificar('Citações sem seção REFERÊNCIAS: aviso único', len(sem_secao) == 1 and 'REFERÊNCIAS' in sem_secao[0]['texto'], sem_secao)
    copia = json.dumps(TRABALHO)
    R.conferir(TRABALHO)
    verificar('Conferir referências só lê: os textos não mudam', json.dumps(TRABALHO) == copia)

    DOC = [
        P('1 INTRODUÇÃO', True),
                                                                                                           # 1
        P('Envie um e-mail à equipe. O email deve ter o assunto certo. A COVID-19 mudou tudo; a Covid-19 ainda preocupa.'),
        P('O AVA é usado em sala. O Ambiente Virtual de Aprendizagem (AVA) foi adotado em 2020.'),          # 2
        P('Ele está aqui. Esta é a sala. E é assim que se faz: é simples.'),                                # 3 (e/é: não aponta)
        P('Veja a Figura 1 e a Figura 4. Os dados da Tabela 2 também.'),                                    # 4
        P('Figura 1 – Fluxo'),                                                                              # 5
        P('Figura 3 – Telas'),                                                                              # 6
        P('Tabela 2 – Custos'),                                                                             # 7
        P('O prazo vai até 10/03/2025 e a entrega foi em 5 de abril de 2025; 30% aprovaram, dez por cento não.'),  # 8
        P('Ele disse "sim" e depois “não”.'),                                                               # 9
        P('O Sistema Único de Saúde (SUS) atende. O Sistema Unificado de Saúde (SUS) é outro nome.'),       # 10
        P('REFERÊNCIAS', True),
        P('BRASIL. Lei nº 10.406, de 10 de janeiro de 2002. Diário Oficial, Brasília, 2002.'),
    ]
    c = C.conferir(DOC)
    ct = lambda cat: [x['texto'] for x in c if x['categoria'] == cat]
    verificar('Grafia: "e-mail"/"email" e "COVID-19"/"Covid-19" apontados', any('e-mail' in t and 'email' in t for t in ct('Grafia'))
              and any('COVID-19' in t for t in ct('Grafia')), ct('Grafia'))
    verificar('Grafia: diferenças de acento (e/é, esta/está) e maiúscula de início de frase NÃO são apontadas',
              not any(t for t in ct('Grafia') if '"e"' in t or '"é"' in t or 'esta' in t.lower()), ct('Grafia'))
    verificar('Sigla usada antes de ser definida (AVA) e definida de dois jeitos (SUS)',
              any('AVA é usada antes' in t for t in ct('Sigla')) and any('SUS definida de dois jeitos' in t for t in ct('Sigla')), ct('Sigla'))
    verificar('Numeração: salto nas figuras (falta 2) e "Figura 4" citada sem legenda; Tabela 2 correta não é apontada',
              any('falta figura 2' in t for t in ct('Numeração')) and any('"Figura 4"' in t for t in ct('Numeração'))
              and not any('Tabela 2' in t for t in ct('Numeração')), ct('Numeração'))
    verificar('Datas em formatos diferentes e "%" com "por cento" viram informação', ct('Datas') and ct('Números'), (ct('Datas'), ct('Números')))
    verificar('Aspas retas e curvas misturadas viram informação', ct('Aspas'), ct('Aspas'))
    verificar('A seção REFERÊNCIAS fica de fora da consistência (BRASIL em maiúsculas, data por extenso)',
              not any(x['par'] >= 11 for x in c), [x['par'] for x in c])
    limpo = [P('O sistema funciona bem. Ele envia relatórios por e-mail toda semana.'), P('Figura 1 – Exemplo'),
             P('Como mostra a Figura 1, o sistema é simples.')]
    verificar('Documento consistente: nenhum apontamento', C.conferir(limpo) == [], C.conferir(limpo))

    saida = RAIZ / 'tests' / 'output' / 'documento'
    saida.mkdir(parents=True, exist_ok=True)
    (saida / 'conferencias.json').write_text(json.dumps({'itens': itens}, ensure_ascii=False, indent=1), encoding='utf-8')
    n = sum(1 for x in itens if x['ok'])
    print(f'Conferir referências e consistência: {n}/{len(itens)}')
    return 0 if n == len(itens) else 1


if __name__ == '__main__':
    sys.exit(main())
