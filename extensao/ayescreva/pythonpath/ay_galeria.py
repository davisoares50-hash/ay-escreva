# -*- coding: utf-8 -*-
"""Diálogos da galeria de modelos e de "Salvar como modelo". O conteúdo dos modelos está em ay_modelos.py.
SPDX-License-Identifier: MPL-2.0
"""
import os

import ay_dialogos as D
import ay_modelos as M

registrar = print
FORMATO = ('Modelo é a aparência e a estrutura; formato é como o arquivo é gravado. O documento criado não tem título: '
           'ao salvar, escolha ODT (padrão aberto) ou DOCX (Word). Os campos entre colchetes são controles de conteúdo: '
           'um clique seleciona o texto e o que você digitar o substitui (no Word, viram espaços reservados).')


def _janela(frame):
    return frame.getContainerWindow()


def galeria(ctx, frame):
    """Comando ayescreva:Galeria."""
    while True:
        r = _dialogo(ctx, frame)
        if r is None:
            return
        acao, valor = r
        if acao == 'criar':
            M.criar(ctx, valor)
            return
        if acao == 'pessoal':
            M.criar_de_pessoal(ctx, valor)
            return
        if acao == 'salvar':
            salvar_modelo(ctx, frame)
        elif acao == 'remover':
            nome = os.path.splitext(os.path.basename(valor))[0]
            if D.mensagem(ctx, _janela(frame), 'Remover modelo pessoal', f'Remover o modelo pessoal "{nome}"? O arquivo .ott será apagado '
                          'da pasta de modelos do AY; documentos já criados com ele não mudam.', 'QUERYBOX', 3) == 2:
                M.remover_pessoal(ctx, valor)
        elif acao == 'pasta':
            shell = D.servico(ctx, 'com.sun.star.system.SystemShellExecute')
            shell.execute(M.pasta_pessoal(ctx), '', 0)


def _dialogo(ctx, frame):
    pessoais = M.pessoais(ctx)
    entradas = [('modelo', m) for m in M.MODELOS] + [('pessoal', p) for p in pessoais]
    nomes = [m['nome'] for m in M.MODELOS] + [f'Personalizado: {n}' for n, _ in pessoais]
    d = D.Dialogo(ctx, 'Galeria de modelos', 360, 250, nome='galeria')
    d.rotulo('r_lista', 6, 4, 140, '~Modelos:')
    d.add('ListBox', 'lista', 6, 18, 140, 186, StringItemList=tuple(nomes), Border=1)
    d.rotulo('r_desc', 152, 4, 202, '~Sobre o modelo:')
    d.add('Edit', 'descricao', 152, 18, 202, 110, MultiLine=True, ReadOnly=True, VScroll=True, Border=1)
    d.add('FixedText', 'formato', 152, 132, 202, 72, MultiLine=True, Label=FORMATO)

    def atual():
        i = d.c('lista').getSelectedItemPos()
        return entradas[i] if 0 <= i < len(entradas) else None

    def mostrar():
        e = atual()
        if e is None:
            return
        tipo, v = e
        if tipo == 'modelo':
            camada = 'norma oficial' if v['camada'] == 'norma' else 'sem norma oficial (preferência do AY)'
            d.m('descricao').Text = f'{v["descricao"]}\n\nOrigem ({camada}): {v["origem"]}.'
        else:
            d.m('descricao').Text = f'Modelo pessoal salvo por você.\n\nArquivo: {v[1]}'
        d.m('remover').Enabled = tipo == 'pessoal'

    def criar():
        e = atual()
        if e is None:
            return
        d.fechar(('criar', e[1]['id']) if e[0] == 'modelo' else ('pessoal', e[1][1]))

    def remover():
        e = atual()
        if e is not None and e[0] == 'pessoal':
            d.fechar(('remover', e[1][1]))

    d.botao('criar', 6, 230, 90, '~Criar documento', criar, padrao=True)
    d.botao('salvar', 100, 230, 116, 'Salvar documento ~atual como modelo…', lambda: d.fechar(('salvar', None)))
    d.botao('pasta', 220, 210, 80, 'Abrir ~pasta', lambda: d.fechar(('pasta', None)))
    d.botao('remover', 220, 230, 80, 'Re~mover pessoal', remover)
    d.botao('fechar', 304, 230, 50, '~Fechar', lambda: d.fechar(None))
    d.ao_mudar('lista', mostrar)

    def iniciar():
        d.c('lista').selectItemPos(0, True)
        mostrar()
    return d.executar(_janela(frame), iniciar)


def _dialogo_nome(ctx, frame, nome):
    d = D.Dialogo(ctx, 'Salvar como modelo', 260, 92, nome='salvar_modelo')
    d.rotulo('r_nome', 6, 6, 60, '~Nome do modelo:')
    d.add('Edit', 'nome', 70, 6, 184, 14, Text=nome[:80])
    d.add('FixedText', 'nota', 6, 24, 248, 44, MultiLine=True,
          Label='O modelo é gravado como modelo ODT (.ott) na pasta de modelos do AY, no seu perfil, e aparece na galeria como '
                '"Personalizado". O documento aberto continua o mesmo e no mesmo formato.')
    d.botao('salvar', 140, 72, 56, '~Salvar', lambda: d.fechar(d.c('nome').getText()), padrao=True)
    d.botao('cancelar', 200, 72, 54, '~Cancelar', lambda: d.fechar(None))
    return d.executar(_janela(frame))


def salvar_modelo(ctx, frame):
    """Comando ayescreva:SalvarModelo: grava o documento atual como modelo pessoal (.ott); o documento não muda."""
    doc = frame.getController().getModel()
    nome = (doc.getDocumentProperties().Title or '').strip()
    while True:
        nome = _dialogo_nome(ctx, frame, nome)
        if nome is None:
            return None
        try:
            caminho = M.salvar_como_modelo(ctx, doc, nome)
        except FileExistsError:
            if D.mensagem(ctx, _janela(frame), 'Salvar como modelo', f'Já existe um modelo pessoal chamado "{nome.strip()}". Substituir?',
                          'QUERYBOX', 3) != 2:
                continue
            caminho = M.salvar_como_modelo(ctx, doc, nome, substituir=True)
        except ValueError as e:
            D.mensagem(ctx, _janela(frame), 'Salvar como modelo', f'Nome inválido: {e}.', 'WARNINGBOX')
            continue
        D.mensagem(ctx, _janela(frame), 'Salvar como modelo', f'Modelo salvo: {os.path.basename(caminho)}. Ele aparece na galeria de modelos.')
        return caminho
