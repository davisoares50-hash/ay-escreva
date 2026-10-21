# -*- coding: utf-8 -*-
"""Diálogo de apontamentos (entrega D): "Conferir referências" e "Conferir consistência".

Mostra a lista do que foi encontrado, o detalhe de cada item e "Ir para" (seleciona o trecho no documento). Não altera
o documento: as correções ficam com a pessoa.
SPDX-License-Identifier: MPL-2.0
"""
import traceback

import ay_dialogos as D

registrar = print


def mostrar(ctx, frame, titulo, explicacao, achados, pars, vazio):
    """achados: [{'nivel', 'categoria', 'texto', 'par', 'ini', 'fim'}]; pars: parágrafos de coletar()."""
    doc = frame.getController().getModel()
    import ay_referencias as R
    avisos = sum(1 for a in achados if a['nivel'] == 'aviso')
    infos = len(achados) - avisos
    d = D.Dialogo(ctx, titulo, 400, 246, nome='achados')
    d.add('FixedText', 'explica', 6, 4, 388, 28, MultiLine=True, Label=explicacao)
    resumo = (f'{avisos} aviso(s) e {infos} informação(ões).' if achados else vazio)
    d.add('FixedText', 'resumo', 6, 34, 388, 10, Label=resumo)
    d.rotulo('r_lista', 6, 46, 200, '~Apontamentos:')
    rotulos = [f'{"▲" if a["nivel"] == "aviso" else "i"} {a["categoria"]}: {a["texto"]}' for a in achados]
    d.add('ListBox', 'lista', 6, 58, 388, 96, StringItemList=tuple(rotulos), Border=1)
    d.rotulo('r_detalhe', 6, 158, 200, '~Detalhe e trecho:')
    d.add('Edit', 'detalhe', 6, 170, 388, 50, MultiLine=True, ReadOnly=True, VScroll=True, Border=1)

    def atual():
        i = d.c('lista').getSelectedItemPos()
        return achados[i] if 0 <= i < len(achados) else None

    def mostrar_item():
        a = atual()
        if a is None:
            d.m('detalhe').Text = ''
            return
        t = pars[a['par']]['texto']
        trecho = t[max(0, a['ini'] - 60):a['fim'] + 60]
        d.m('detalhe').Text = (f'{a["categoria"]} ({a["nivel"]}): {a["texto"]}\n\nNo parágrafo {a["par"] + 1}: '
                               f'{"…" if a["ini"] > 60 else ""}{trecho}{"…" if a["fim"] + 60 < len(t) else ""}')
        d.m('ir').Enabled = True

    def ir():
        a = atual()
        if a is None:
            return
        try:
            R.ir_para(doc, pars[a['par']], a['ini'], a['fim'])
        except Exception:
            registrar('achados ir para: ' + traceback.format_exc())

    d.botao('ir', 6, 226, 90, '~Ir para o trecho', ir)
    d.botao('fechar', 334, 226, 60, '~Fechar', lambda: d.fechar(None), padrao=True)
    d.ao_mudar('lista', mostrar_item)

    def iniciar():
        d.m('ir').Enabled = False
        if achados:
            d.c('lista').selectItemPos(0, True)
            mostrar_item()
    d.executar(frame.getContainerWindow(), iniciar)


def conferir_referencias(ctx, frame):
    import ay_referencias as R
    doc = frame.getController().getModel()
    pars = R.coletar(doc)
    achados = R.conferir(pars)
    registrar(f'conferir referências: {len(achados)} apontamento(s)')
    mostrar(ctx, frame, 'Conferir referências',
            'Confere as citações do texto (autor-data) com a lista de REFERÊNCIAS e a apresentação básica de cada entrada '
            '(ano, "Disponível em" e "Acesso em", ordem, repetições). O AY não cria, completa nem corrige referências: os '
            'dados vêm da obra consultada.', achados, pars,
            'Nenhum problema encontrado nas regras conferidas (isso não substitui a revisão pela NBR 6023).')


def conferir_consistencia(ctx, frame):
    import ay_consistencia as C
    import ay_referencias as R
    doc = frame.getController().getModel()
    pars = R.coletar(doc)
    achados = C.conferir(pars)
    registrar(f'conferir consistência: {len(achados)} apontamento(s)')
    mostrar(ctx, frame, 'Conferir consistência',
            'Procura o mesmo termo escrito de jeitos diferentes, siglas usadas antes de serem definidas, numeração de figuras '
            'e tabelas, e formatos de data, porcentagem e aspas misturados. Nada é mudado: use "Ir para" e decida.',
            achados, pars, 'Nenhuma inconsistência encontrada nas regras conferidas.')
