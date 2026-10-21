# -*- coding: utf-8 -*-
"""Entrega D no editor, por UNO, com o motor e o modelo reais (Gemma 4 E2B em out\\ia).

  - quais parágrafos a revisão do documento inteiro analisa (títulos, referências, campos e notas ficam de fora);
  - revisão de vários parágrafos com o modelo e aplicação de uma sugestão escolhida, com desfazer;
  - "Sugerir títulos": títulos reais do modelo, limpos; inserir como título (estilo do título anterior) e trocar um
    título existente, cada um numa ação de desfazer; nada inventado (números/siglas novos recusados);
  - "Explicar" e "Apontar inconsistências": só leitura (o documento não muda);
  - "Conferir referências" e "Conferir consistência" num documento de verdade, com "Ir para" selecionando o trecho.
Uso: "dist\\AY ESCREVA\\program\\python.exe" tests\\ia\\integracao_d.py
SPDX-License-Identifier: MPL-2.0
"""
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'tests' / 'uno'))
sys.path.insert(0, str(RAIZ / 'tests' / 'ia'))
sys.path.insert(0, str(RAIZ / 'extensao' / 'ayescreva' / 'pythonpath'))
from ay_uno import Motor, SAIDA_TESTES, fechar  # noqa: E402
import ay_consistencia as C  # noqa: E402
import ay_ia as IA  # noqa: E402
import ay_ia_painel as P  # noqa: E402
import ay_ia_texto as T  # noqa: E402
import ay_referencias as R  # noqa: E402
from integracao import doc_com, paragrafos, texto, selecionar, intervalo  # noqa: E402

itens = []
medidas = {}


def verificar(descricao, ok, detalhe='', situacao=None):
    situacao = situacao or ('ok' if ok else 'falha')
    itens.append({'ok': situacao == 'ok', 'situacao': situacao, 'verificacao': descricao, 'detalhe': str(detalhe)})
    marca = {'ok': 'OK  ', 'falha': 'FALHA', 'bloqueado': 'BLOQ'}[situacao]
    print(f'[{marca}] {descricao}{" — " + str(detalhe) if detalhe else ""}', flush=True)


TRABALHO = [
    ('1 INTRODUÇÃO', 'Heading 1'),
    ('Os dados mostra que a maioria dos participantes concordaram com a proposta, segundo Silva (2019).', None),
    ('Curto demais.', None),
    ('A pesquisa foi feita em 2024 com 120 servidores e a equipe entregou o relatorio a diretora.', None),
    ('2 MÉTODO', 'Heading 1'),
    ('Os questionários foram aplicados entre março e maio, e as respostas foram analizadas pela equipe.', None),
    ('Este parágrafo tem uma nota de rodapé e fica de fora da revisão automática.', None),
    ('REFERÊNCIAS', 'Heading 1'),
    ('SILVA, Maria. Custos. Brasília: Ed. UnB, 2019.', None),
    ('SOUZA, Paulo. Debate. Curitiba: UFPR, 2018.', None),
]


def pedir(srv, acao, trecho):
    p = IA.Pedido(srv, T.prompt(acao, trecho), max_tokens=T.max_tokens(acao, trecho), sem_pensar=True)
    p._rodar()
    return T.limpar_resposta(p.texto, trecho), p


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    cat = IA.catalogo()
    m = next(x for x in cat['modelos'] if x.get('recomendado'))
    pasta = RAIZ / 'out' / 'ia'
    exe = pasta / f'motor-{cat["motor"]["versao"]}' / cat['motor']['executavel']
    arq = pasta / 'modelos' / m['arquivo']
    with Motor('ia_d') as mo:
        # ---------------- quais parágrafos entram na revisão do documento inteiro
        d = doc_com(mo, [t for t, _ in TRABALHO], [e for _, e in TRABALHO])
        p6 = paragrafos(d)[6]
        nota = d.createInstance('com.sun.star.text.Footnote')
        d.getText().insertTextContent(p6.getEnd(), nota, False)
        itens_doc, pulados = P.candidatos_documento(d)
        nums = [i for i, _, _ in itens_doc]
        verificar('Revisar documento inteiro: entram só parágrafos de texto comum (fora títulos, referências, curtos e com nota)',
                  nums == [1, 3, 5] and pulados == 1, f'parágrafos {nums}; {pulados} com nota pulado(s)')

        # ---------------- referências e consistência num documento de verdade
        pars = R.coletar(d)
        refs = R.conferir(pars)
        sem_cit = [a for a in refs if a['categoria'] == 'Referência' and 'SOUZA' in pars[a['par']]['texto'] and a['nivel'] == 'informação']
        alvo = next((a for a in refs if a['nivel'] == 'informação'), None)
        sel = None
        if alvo:
            R.ir_para(d, pars[alvo['par']], alvo['ini'], alvo['fim'])
            sel = d.getCurrentController().getSelection().getByIndex(0).getString()
        verificar('Conferir referências no documento: SOUZA (não citado) vira informação; Silva (2019) citado não é apontado; '
                  '"Ir para" seleciona a entrada', sem_cit and not any(a['categoria'] == 'Citação' for a in refs)
                  and sel == pars[alvo['par']]['texto'], [a['texto'][:60] for a in refs])
        cons = C.conferir(pars)
        verificar('Conferir consistência no documento sem problemas plantados: nenhum apontamento falso', cons == [], cons)
        antes = texto(d)

        if not exe.exists() or not arq.exists():
            verificar('Parte com o modelo', False, f'motor ou modelo ausente em {pasta}', situacao='bloqueado')
            fechar(d)
            return gravar()
        srv = IA.Servidor(str(exe), str(arq), contexto=4096, threads=4)
        srv.iniciar()
        try:
            # ---------------- revisão de vários parágrafos (o motor da revisão do documento inteiro)
            t0 = time.time()
            sugestoes = []
            for par, txt, cur in itens_doc:
                sug, p = pedir(srv, 'revisar', txt)
                probl = T.conferir_preservacao(txt, sug, 'revisar')
                if sug != txt and not probl:
                    sugestoes.append((par, txt, cur, sug))
            medidas['revisar_3_paragrafos_s'] = round(time.time() - t0, 1)
            verificar('Revisão de vários parágrafos com o modelo: sugestões só onde há erro, todas preservando números e nomes',
                      len(sugestoes) >= 2 and all(s[0] in (1, 3, 5) for s in sugestoes),
                      [(s[0], s[3][:70]) for s in sugestoes] + [f'{medidas["revisar_3_paragrafos_s"]} s'])
            verificar('Revisar documento inteiro e conferências só leem: o documento não mudou até aceitar', texto(d) == antes)
            if sugestoes:
                par, txt, cur, sug = sugestoes[0]
                n = P.aplicar(d, cur, txt, sug, 'revisar', controlada=False)
                aplicado = paragrafos(d)[par].getString()
                outros_iguais = all(paragrafos(d)[i].getString() == TRABALHO[i][0] for i in (3, 5) if i != par)
                d.getUndoManager().undo()
                verificar('Aceitar uma sugestão da lista muda só aquele parágrafo; Ctrl+Z volta', aplicado == sug and outros_iguais
                          and texto(d) == antes, f'{n} trechos no parágrafo {par}')

            # ---------------- sugerir títulos
            alvo_txt = paragrafos(d)[3].getString()
            resp, p = pedir(srv, 'titulos', alvo_txt)
            validos, recusados = T.titulos(resp, alvo_txt)
            medidas['titulos_s'] = p.medidas.get('segundos')
            verificar('Sugerir títulos (modelo real): até 3 títulos limpos, sem número ou sigla que não estejam no trecho',
                      1 <= len(validos) <= 3 and all(len(t) <= 120 and not t.endswith('.') for t in validos), (validos, recusados))
            if validos:
                titulos_antes = d.getUndoManager().getAllUndoActionTitles()
                rng = intervalo(d, 0, len(alvo_txt), par=3)
                como = P.inserir_titulo(d, rng, alvo_txt, validos[0], controlada=False)
                ps = paragrafos(d)
                novo = ps[3]
                ok_ins = (novo.getString() == validos[0] and novo.ParaStyleName == 'Heading 1' and ps[4].getString() == alvo_txt
                          and d.getUndoManager().getAllUndoActionTitles()[0] == 'Título sugerido pela IA'
                          and len(d.getUndoManager().getAllUndoActionTitles()) == len(titulos_antes) + 1)
                d.getUndoManager().undo()
                verificar('Inserir título: novo parágrafo antes do trecho, com o estilo do título anterior (Título 1), uma ação de '
                          'desfazer; Ctrl+Z remove', ok_ins and texto(d) == antes, como)
                rng = intervalo(d, 0, len('2 MÉTODO'), par=4)
                como = P.inserir_titulo(d, rng, '2 MÉTODO', '2 Método da pesquisa', controlada=True)
                trocado = paragrafos(d)[4].getString()          # lido antes de desfazer
                n_alt = d.getRedlines().createEnumeration().hasMoreElements()
                d.getUndoManager().undo()
                verificar('Usar título num trecho que já é título troca o texto dele (como alteração controlada); Ctrl+Z volta',
                          n_alt and 'Método da pesquisa' in trocado and texto(d) == antes, f'{como}; com as marcas: {trocado!r}')
            # ---------------- explicar e inconsistências (só leitura)
            exp, p = pedir(srv, 'explicar', paragrafos(d)[1].getString())
            medidas['explicar_s'] = p.medidas.get('segundos')
            novos = [x for x in T.conferir_preservacao(paragrafos(d)[1].getString(), exp, 'resumir') if 'números' in x]
            verificar('Explicar (modelo real): explicação em português, sem números novos; o documento não muda',
                      len(exp) > 40 and not novos and texto(d) == antes, exp[:200])
            casos = [('A pesquisa ouviu 120 servidores em 2024. Dos 150 servidores entrevistados, 90% aprovaram. '
                      'A coleta terminou em março de 2023, antes do início em 2024.', ('150', '2023')),
                     ('O projeto custou R$ 50 mil, dividido em duas parcelas de R$ 30 mil.', ('30 mil', '50 mil'))]
            achados, explicadas, apontadas = 0, 0, 0
            detalhes = []
            for trecho, dados in casos:
                resp, p = pedir(srv, 'inconsistencias', trecho)
                linhas = T.inconsistencias(resp, trecho)
                explicadas += sum(1 for _, eco in linhas if not eco)
                apontadas += sum(1 for _, eco in linhas if eco)
                if any(any(x in t for x in dados) for t, _ in linhas):
                    achados += 1
                detalhes.append([t[:90] + (' (só apontado)' if eco else '') for t, eco in linhas])
            medidas['inconsistencias'] = {'casos_com_contradicao': len(casos), 'apontados': achados, 'linhas_explicadas': explicadas,
                                          'linhas_so_apontadas': apontadas}
            verificar('Apontar inconsistências (modelo real): aponta os trechos contraditórios nos 2 casos (explicadas e só apontadas '
                      'registradas)', achados == len(casos), f'{achados}/{len(casos)} casos; {explicadas} linha(s) com explicação, '
                      f'{apontadas} só apontando; {detalhes}')
            ok_txt = 'A pesquisa ouviu 120 servidores em 2024, e 90% deles aprovaram a proposta.'
            inc2, p = pedir(srv, 'inconsistencias', ok_txt)
            falsos = T.inconsistencias(inc2, ok_txt)
            medidas['inconsistencias_trecho_coerente'] = [t for t, _ in falsos]
            verificar('Apontar inconsistências num trecho coerente: falso alarme registrado (a IA pode errar; é só leitura)', True,
                      f'{len(falsos)} linha(s) apontada(s): {[t[:80] for t, _ in falsos]}')
        finally:
            srv.parar()
        fechar(d)
    return gravar()


def gravar():
    saida = SAIDA_TESTES / 'ia'
    saida.mkdir(parents=True, exist_ok=True)
    (saida / 'integracao_d.json').write_text(json.dumps({'itens': itens, 'medidas': medidas}, ensure_ascii=False, indent=1),
                                             encoding='utf-8')
    ok = sum(1 for i in itens if i['situacao'] == 'ok')
    print(f'\nEntrega D no editor: {ok}/{len(itens)} aprovadas')
    return 0 if ok == len(itens) else 1


if __name__ == '__main__':
    sys.exit(main())
