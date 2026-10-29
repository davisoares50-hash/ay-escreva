# -*- coding: utf-8 -*-
"""Montagem de diálogos do AY em código (unidades de diálogo), com ordem de tabulação na ordem de inclusão.

Os testes pela interface encontram o diálogo aberto em ATUAL e acionam os controles na thread principal.
SPDX-License-Identifier: MPL-2.0
"""
import unohelper
from com.sun.star.awt import XActionListener, XFocusListener, XItemListener, XTextListener
from com.sun.star.awt.FontUnderline import BOLD as SUBLINHADO_GROSSO

ATUAL = []          # diálogos abertos (o mais recente por último), para os testes pela interface

# Controles que ganham realce ao receber o foco do teclado
REALCE_TIPOS = ('com.sun.star.awt.UnoControlButtonModel', 'com.sun.star.awt.UnoControlCheckBoxModel',
                'com.sun.star.awt.UnoControlRadioButtonModel')


class _RealceFoco(unohelper.Base, XFocusListener):
    """Foco visível: no tema do Windows 11, o motor quase não marca o botão com foco (teste manual de 29/10/2026,
    RESULTADOS §14). Enquanto o controle tem o foco, o rótulo ganha sublinhado grosso; ao sair, volta ao normal.
    O sublinhado não muda a largura do texto (nada é cortado), não muda o nome lido pelo leitor de tela e funciona em
    tema claro e escuro."""

    def __init__(self, modelo):
        self.modelo = modelo

    def focusGained(self, ev):
        try:
            self.modelo.FontUnderline = SUBLINHADO_GROSSO
        except Exception:
            pass

    def focusLost(self, ev):
        # sem sublinhado (FontUnderline.NONE); "voltar ao padrão" deixava o sublinhado desenhado no botão
        try:
            self.modelo.FontUnderline = 0
        except Exception:
            pass

    def disposing(self, ev):
        pass


def realcar_foco(container):
    """Liga o realce do foco aos botões e caixas de marcação de um diálogo ou painel do AY (XControlContainer)."""
    for c in container.getControls():
        try:
            if any(c.getModel().supportsService(t) for t in REALCE_TIPOS):
                c.addFocusListener(_RealceFoco(c.getModel()))
        except Exception:
            pass


def servico(ctx, nome):
    return ctx.getServiceManager().createInstanceWithContext(nome, ctx)


class _Acao(unohelper.Base, XActionListener):
    def __init__(self, f):
        self.f = f

    def actionPerformed(self, ev):
        self.f()

    def disposing(self, ev):
        pass


class _Item(unohelper.Base, XItemListener):
    def __init__(self, f):
        self.f = f

    def itemStateChanged(self, ev):
        self.f()

    def disposing(self, ev):
        pass


class _Texto(unohelper.Base, XTextListener):
    def __init__(self, f):
        self.f = f

    def textChanged(self, ev):
        self.f()

    def disposing(self, ev):
        pass


class Dialogo:
    def __init__(self, ctx, titulo, largura, altura, nome='dialogo'):
        self.ctx = ctx
        self.nome = nome
        self.dm = servico(ctx, 'com.sun.star.awt.UnoControlDialogModel')
        self.dm.Width, self.dm.Height, self.dm.Title = largura, altura, titulo
        self.dm.Name = nome
        self.tab = 0
        self.dlg = None
        self.resultado = None
        self._acoes = []

    def add(self, tipo, nome, x, y, w, h, **pr):
        m = self.dm.createInstance('com.sun.star.awt.UnoControl' + tipo + 'Model')
        m.PositionX, m.PositionY, m.Width, m.Height = x, y, w, h
        m.TabIndex = self.tab          # rótulos também: a ordem de tabulação liga o rótulo ao controle (acessibilidade)
        self.tab += 1
        for k, v in pr.items():
            setattr(m, k, v)
        self.dm.insertByName(nome, m)
        return m

    def rotulo(self, nome, x, y, w, texto, h=10, **pr):
        return self.add('FixedText', nome, x, y + 2, w, h, Label=texto, **pr)

    def botao(self, nome, x, y, w, texto, f=None, padrao=False, h=14):
        self.add('Button', nome, x, y, w, h, Label=texto, DefaultButton=padrao)
        if f is not None:
            self._acoes.append(('acao', nome, f))

    def ao_mudar(self, nome, f):
        self._acoes.append(('item', nome, f))

    def ao_digitar(self, nome, f):
        self._acoes.append(('texto', nome, f))

    def c(self, nome):
        return self.dlg.getControl(nome)

    def m(self, nome):
        return self.dm.getByName(nome)

    def fechar(self, resultado=None):
        self.resultado = resultado
        self.dlg.endExecute()

    def executar(self, janela_pai, ao_abrir=None):
        self.dlg = servico(self.ctx, 'com.sun.star.awt.UnoControlDialog')
        self.dlg.setModel(self.dm)
        for tipo, nome, f in self._acoes:
            ctl = self.dlg.getControl(nome)
            if tipo == 'acao':
                ctl.addActionListener(_Acao(f))
            elif tipo == 'item':
                ctl.addItemListener(_Item(f))
            else:
                ctl.addTextListener(_Texto(f))
        self.dlg.createPeer(servico(self.ctx, 'com.sun.star.awt.Toolkit'), janela_pai)
        realcar_foco(self.dlg)
        if ao_abrir:
            ao_abrir()
        ATUAL.append(self)
        try:
            self.dlg.execute()
        finally:
            if self in ATUAL:
                ATUAL.remove(self)
            self.dlg.dispose()
        return self.resultado


def mensagem(ctx, janela_pai, titulo, texto, tipo='INFOBOX', botoes=1):
    """Caixa de mensagem; botoes: 1 = OK, 2 = OK/Cancelar, 3 = Sim/Não. Devolve o código do botão."""
    from com.sun.star.awt.MessageBoxType import INFOBOX, WARNINGBOX, QUERYBOX, ERRORBOX
    tipos = {'INFOBOX': INFOBOX, 'WARNINGBOX': WARNINGBOX, 'QUERYBOX': QUERYBOX, 'ERRORBOX': ERRORBOX}
    tk = servico(ctx, 'com.sun.star.awt.Toolkit')
    caixa = tk.createMessageBox(janela_pai, tipos[tipo], botoes, titulo, texto)
    ATUAL.append(caixa)
    try:
        return caixa.execute()
    finally:
        if caixa in ATUAL:
            ATUAL.remove(caixa)
