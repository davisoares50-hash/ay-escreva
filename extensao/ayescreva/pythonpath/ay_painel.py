# -*- coding: utf-8 -*-
"""Painel lateral "Assistente AY" (barra lateral do motor). Todas as ações rodam na thread principal.
SPDX-License-Identifier: MPL-2.0
"""
import time
import traceback

import uno
import unohelper
from com.sun.star.awt import XActionListener, XItemListener, XWindowListener
from com.sun.star.lang import XComponent, XServiceInfo
from com.sun.star.ui import XSidebarPanel, XToolPanel, XUIElement, XUIElementFactory

import ay_revisao
from ay_revisao import Analise, Revisao, despachar, estado_comando

XDL = 'vnd.sun.star.extension://br.ayescreva.extensao/Painel.xdl'
DECK = 'AssistenteAYDeck'
COMANDO_DECK = '.uno:SidebarDeck.' + DECK
BOTOES = ('verificar_selecao', 'verificar_documento', 'cancelar', 'aplicar', 'ignorar', 'adicionar', 'nao_corrigir',
          'reverter', 'nao_corrigir_recente', 'dicionario', 'autocorrecao')
CAIXAS = ('ortografia', 'correcao', 'gramatica', 'estilo')
LARGURA_TOTAL = ('titulo_revisao', 'ortografia', 'correcao', 'gramatica', 'estilo', 'situacao', 'rotulo_lista',
                 'ocorrencias', 'detalhe', 'titulo_recentes', 'recentes', 'titulo_ia', 'ia_estado')
COLUNA_ESQ = ('verificar_selecao', 'aplicar', 'adicionar', 'reverter', 'dicionario')
COLUNA_DIR = ('verificar_documento', 'ignorar', 'nao_corrigir', 'nao_corrigir_recente', 'autocorrecao')
CURTO = {'ortografia': 'Ortografia', 'gramatica': 'Gramática', 'estilo': 'Estilo'}
PS_X, PS_WIDTH = 1, 4


class _Ouvinte(unohelper.Base, XActionListener, XItemListener, XWindowListener):
    def __init__(self, painel):
        self.painel = painel

    def actionPerformed(self, ev):
        self.painel.executar('_botao_' + ev.ActionCommand)

    def itemStateChanged(self, ev):
        self.painel.executar('_item_' + ev.Source.getModel().Name, ev)

    def windowResized(self, ev):
        self.painel.executar('_redimensionar')

    def windowMoved(self, ev): pass
    def windowShown(self, ev): pass
    def windowHidden(self, ev): pass
    def disposing(self, ev): pass


class Painel(unohelper.Base, XUIElement, XToolPanel, XSidebarPanel, XComponent):
    def __init__(self, ctx, frame, parent, url):
        self.ctx = ctx
        self.Frame = frame
        self.ResourceURL = url
        self.Type = uno.getConstantByName('com.sun.star.ui.UIElementType.TOOLPANEL')
        self.revisao = Revisao.obter(ctx)
        prov = ay_revisao.servico(ctx, 'com.sun.star.awt.ContainerWindowProvider')
        peer = parent.queryInterface(uno.getTypeByName('com.sun.star.awt.XWindowPeer'))
        self.win = prov.createContainerWindow(XDL, '', peer, None)
        self.win.setVisible(True)
        self.c = {c.getModel().Name: c for c in self.win.getControls()}
        self.ouvinte = _Ouvinte(self)
        for nome in BOTOES:
            self.c[nome].setActionCommand(nome)
            self.c[nome].addActionListener(self.ouvinte)
        for nome in CAIXAS + ('ocorrencias', 'recentes'):
            self.c[nome].addItemListener(self.ouvinte)
        self.win.addWindowListener(self.ouvinte)
        self.altura = self.win.getPosSize().Height
        self.analise = None
        self.achados = []
        self.ouvintes_fim = []
        self.revisao.paineis.append(self)
        self.atualizar()
        pedido = self.revisao.retirar_pedido(self.Frame)
        if pedido:
            ay_revisao.adiar(ctx, lambda: self.iniciar_analise(pedido == 'selecao'))
        ay_revisao.registrar('painel Assistente AY criado')

    # ---------- XUIElement / XToolPanel / XSidebarPanel / XComponent ----------
    def getRealInterface(self):
        return self

    def getWindow(self):
        return self.win

    def createAccessible(self, pai):
        return self.win.getAccessibleContext() if hasattr(self.win, 'getAccessibleContext') else None

    def getHeightForWidth(self, largura):
        ls = uno.createUnoStruct('com.sun.star.ui.LayoutSize')
        ls.Minimum = ls.Maximum = ls.Preferred = self.altura
        return ls

    def getMinimalWidth(self):
        return 240

    def dispose(self):
        if self.analise:
            self.analise.cancelar()
        if self in self.revisao.paineis:
            self.revisao.paineis.remove(self)

    def addEventListener(self, o):
        self.ouvintes_fim.append(o)

    def removeEventListener(self, o):
        if o in self.ouvintes_fim:
            self.ouvintes_fim.remove(o)

    # ---------- utilidades ----------
    def executar(self, metodo, *args):
        if ay_revisao.DEPURAR:
            ay_revisao.registrar('painel: ' + metodo)
        try:
            getattr(self, metodo)(*args)
        except Exception:
            ay_revisao.registrar(f'painel {metodo}: ' + traceback.format_exc())
            self._situacao('Não foi possível concluir a ação. Detalhes em ayescreva-extensao.log (pasta temporária).')

    def _doc(self):
        return self.Frame.getController().getModel()

    def _situacao(self, texto):
        self.c['situacao'].getModel().Label = texto

    def _ativar(self, nome, sim):
        self.c[nome].getModel().Enabled = bool(sim)

    def _redimensionar(self):
        tam = self.win.getPosSize()
        w = tam.Width
        m = 3
        meia = (w - 3 * m) // 2
        for nome in LARGURA_TOTAL:
            self.c[nome].setPosSize(m, 0, max(40, w - 2 * m), 0, PS_X | PS_WIDTH)
        for nome in COLUNA_ESQ:
            self.c[nome].setPosSize(m, 0, meia, 0, PS_X | PS_WIDTH)
        for nome in COLUNA_DIR:
            self.c[nome].setPosSize(2 * m + meia, 0, meia, 0, PS_X | PS_WIDTH)
        canc = self.c['cancelar'].getPosSize().Width
        self.c['cancelar'].setPosSize(w - m - canc, 0, 0, 0, PS_X)
        self.c['progresso'].setPosSize(m, 0, max(40, w - 3 * m - canc), 0, PS_X | PS_WIDTH)
        rot = self.c['rotulo_sugestao'].getPosSize()
        x = rot.X + rot.Width + m
        self.c['sugestoes'].setPosSize(x, 0, max(40, w - x - m), 0, PS_X | PS_WIDTH)

    def atualizar(self):
        cfg = self.revisao.config
        orto = estado_comando(self.ctx, self.Frame, '.uno:SpellOnline')
        self.c['ortografia'].getModel().State = 1 if orto in (True, None) else 0
        self.c['correcao'].getModel().State = 1 if cfg['CorrecaoAutomatica'] else 0
        self.c['gramatica'].getModel().State = 1 if cfg['Gramatica'] else 0
        self.c['estilo'].getModel().State = 1 if cfg['Estilo'] else 0
        doc = self._doc()
        itens = [r for r in self.revisao.recentes if r['doc'] == doc]
        self.recentes_visiveis = itens
        modelo = self.c['recentes'].getModel()
        modelo.StringItemList = tuple(f'{r["hora"]}  {r["original"]} → {r["correcao"]}' for r in itens)
        self._ativar('reverter', False)
        self._ativar('nao_corrigir_recente', False)

    # ---------- níveis ----------
    def _item_ortografia(self, ev):
        quer = self.c['ortografia'].getModel().State == 1
        if estado_comando(self.ctx, self.Frame, '.uno:SpellOnline') != quer:
            despachar(self.ctx, self.Frame, '.uno:SpellOnline')

    def _item_correcao(self, ev):
        self.revisao.gravar_config(CorrecaoAutomatica=self.c['correcao'].getModel().State == 1)

    def _item_gramatica(self, ev):
        self.revisao.gravar_config(Gramatica=self.c['gramatica'].getModel().State == 1)
        self._reverificar_sublinhado()

    def _item_estilo(self, ev):
        self.revisao.gravar_config(Estilo=self.c['estilo'].getModel().State == 1)
        self._reverificar_sublinhado()

    def _reverificar_sublinhado(self):
        # O motor guarda o resultado da verificação por parágrafo; desligar e religar força refazer com as novas regras
        if estado_comando(self.ctx, self.Frame, '.uno:SpellOnline'):
            despachar(self.ctx, self.Frame, '.uno:SpellOnline')
            despachar(self.ctx, self.Frame, '.uno:SpellOnline')

    # ---------- análise ----------
    def iniciar_analise(self, selecao):
        if self.analise:
            self.analise.cancelar()
        self.achados = []
        self.c['ocorrencias'].getModel().StringItemList = ()
        self._mostrar_achado(None)
        ctrl = self.Frame.getController()
        self.analise = Analise(self.revisao, ctrl.getModel(), ctrl, selecao, self._progresso, self._terminar,
                               ortografia=self.c['ortografia'].getModel().State == 1)
        self._ativar('cancelar', True)
        self.c['progresso'].getModel().ProgressValue = 0
        self._situacao('Verificando a seleção…' if selecao else 'Verificando o documento… você pode continuar escrevendo.')
        self.analise.iniciar()

    def _botao_verificar_selecao(self):
        self.iniciar_analise(True)

    def _botao_verificar_documento(self):
        self.iniciar_analise(False)

    def _botao_cancelar(self):
        if self.analise:
            self.analise.cancelar()

    def _progresso(self, analise):
        if analise is not self.analise:
            return
        if analise.total:
            self.c['progresso'].getModel().ProgressValue = min(99, int(100 * analise.feitos / max(1, analise.total)))
        self._situacao(f'Verificando… {analise.feitos} parágrafo(s), {len(analise.achados)} ocorrência(s) até agora.')

    def _terminar(self, analise, cancelado):
        if analise is not self.analise:
            return
        self._ativar('cancelar', False)
        self.achados = analise.achados
        self._listar()
        por = {}
        for a in self.achados:
            por[CURTO[a['nivel']]] = por.get(CURTO[a['nivel']], 0) + 1
        resumo = ', '.join(f'{n} {k.lower()}' for k, n in por.items()) or 'nenhuma ocorrência'
        notas = []
        if analise.nao_mapeados:
            notas.append(f'{analise.nao_mapeados} perto de campos ou notas não marcada(s)')
        if analise.outros_idiomas:
            notas.append(f'{analise.outros_idiomas} parágrafo(s) em outro idioma ignorado(s)')
        dur = time.time() - analise.inicio
        estado = 'Cancelado' if cancelado else 'Concluído'
        self.c['progresso'].getModel().ProgressValue = 0 if cancelado else 100
        self._situacao(f'{estado}: {resumo} em {analise.feitos} parágrafo(s), {dur:.1f} s.' + (' ' + '; '.join(notas) + '.' if notas else ''))
        self.ultima = {'cancelado': cancelado, 'achados': len(self.achados), 'paragrafos': analise.feitos, 'segundos': round(dur, 2)}

    def _listar(self):
        itens = []
        for a in self.achados:
            sug = f' → {a["sugestoes"][0]}' if a['sugestoes'] else ''
            itens.append(f'{CURTO[a["nivel"]]} · {a["original"][:40]}{sug}')
        self.c['ocorrencias'].getModel().StringItemList = tuple(itens)
        if self.achados:
            self.c['ocorrencias'].selectItemPos(0, True)
            self._mostrar_achado(0)
        else:
            self._mostrar_achado(None)

    def _atual(self):
        pos = self.c['ocorrencias'].getSelectedItemPos()
        return (pos, self.achados[pos]) if 0 <= pos < len(self.achados) else (-1, None)

    def _item_ocorrencias(self, ev):
        pos, _ = self._atual()
        self._mostrar_achado(pos if pos >= 0 else None, selecionar_no_texto=True)

    def _mostrar_achado(self, pos, selecionar_no_texto=False):
        a = self.achados[pos] if pos is not None and 0 <= pos < len(self.achados) else None
        if a is not None and a['sugestoes'] is None:
            a['sugestoes'] = self.revisao.sugestoes(a['original'], a['locale'])
        self.c['detalhe'].getModel().Label = (f'{a["categoria"]}: “{a["original"][:60]}”. {a["mensagem"]}' if a else '')
        self.c['sugestoes'].getModel().StringItemList = tuple(a['sugestoes']) if a else ()
        if a and a['sugestoes']:
            self.c['sugestoes'].selectItemPos(0, True)
        self._ativar('aplicar', bool(a and a['sugestoes']))
        self._ativar('ignorar', bool(a))
        self._ativar('adicionar', bool(a and a['nivel'] == 'ortografia'))
        self._ativar('nao_corrigir', bool(a and a['nivel'] == 'ortografia'))
        if a and selecionar_no_texto:
            try:
                self.Frame.getController().select(a['faixa'])
            except Exception:
                pass

    def _remover(self, condicao):
        pos, _ = self._atual()
        self.achados = [a for a in self.achados if not condicao(a)]
        self._listar()
        if self.achados:
            novo = min(max(pos, 0), len(self.achados) - 1)
            self.c['ocorrencias'].selectItemPos(novo, True)
            self._mostrar_achado(novo, selecionar_no_texto=True)

    def _botao_aplicar(self):
        pos, a = self._atual()
        if a is None:
            return
        sug = self.c['sugestoes'].getSelectedItem() or (a['sugestoes'][0] if a['sugestoes'] else '')
        if not sug:
            return
        if ay_revisao.aplicar_sugestao(self._doc(), a, sug):
            self._remover(lambda x: x is a)
            self._situacao(f'Aplicado: “{a["original"]}” → “{sug}” (Ctrl+Z desfaz).')
        else:
            self._situacao('O trecho mudou desde a verificação; verifique de novo.')

    def _botao_ignorar(self):
        pos, a = self._atual()
        if a is None:
            return
        if a['nivel'] == 'ortografia':
            self.revisao.ignorar_tudo(a['original'])
            self._remover(lambda x: x['nivel'] == 'ortografia' and x['original'] == a['original'])
        else:
            self.revisao.ignorados.add((a['regra'], a['original']))
            self._remover(lambda x: (x['regra'], x['original']) == (a['regra'], a['original']))
        self._situacao(f'Ignorado nesta sessão: “{a["original"]}”.')

    def _botao_adicionar(self):
        pos, a = self._atual()
        if a is None or a['nivel'] != 'ortografia':
            return
        self.revisao.adicionar_ao_dicionario(a['original'])
        self._remover(lambda x: x['nivel'] == 'ortografia' and x['original'] == a['original'])
        self._situacao(f'“{a["original"]}” adicionada ao dicionário pessoal.')

    def _botao_nao_corrigir(self):
        pos, a = self._atual()
        if a is None:
            return
        self.revisao.nao_corrigir(a['original'])
        self._situacao(f'A correção automática não vai mais trocar “{a["original"]}”.')

    # ---------- correções automáticas recentes ----------
    def _recente(self):
        pos = self.c['recentes'].getSelectedItemPos()
        return self.recentes_visiveis[pos] if 0 <= pos < len(self.recentes_visiveis) else None

    def _item_recentes(self, ev):
        r = self._recente()
        self._ativar('reverter', bool(r))
        self._ativar('nao_corrigir_recente', bool(r))
        if r:
            try:
                self.Frame.getController().select(r['faixa'])
            except Exception:
                pass

    def _botao_reverter(self):
        r = self._recente()
        if r and not self.revisao.reverter(r):
            self._situacao('O texto mudou depois da correção; nada foi alterado.')

    def _botao_nao_corrigir_recente(self):
        r = self._recente()
        if r:
            self.revisao.nao_corrigir(r['original'])
            self._situacao(f'A correção automática não vai mais trocar “{r["original"]}”.')

    # ---------- dicionário e opções ----------
    def _botao_dicionario(self):
        dialogo_dicionario(self.ctx, self.Frame, self.revisao)

    def _botao_autocorrecao(self):
        despachar(self.ctx, self.Frame, '.uno:AutoCorrectDlg')


class _Fechar(unohelper.Base, XActionListener):
    def __init__(self, dialogo, codigo):
        self.dialogo, self.codigo = dialogo, codigo

    def actionPerformed(self, ev):
        self.dialogo.endDialog(self.codigo)

    def disposing(self, ev):
        pass


class _Remover(unohelper.Base, XActionListener):
    def __init__(self, f):
        self.f = f

    def actionPerformed(self, ev):
        try:
            self.f()
        except Exception:
            ay_revisao.registrar('dicionário: ' + traceback.format_exc())

    def disposing(self, ev):
        pass


def dialogo_dicionario(ctx, frame, revisao):
    """Palavras do dicionário pessoal e da lista "não corrigir", com remoção."""
    dm = ay_revisao.servico(ctx, 'com.sun.star.awt.UnoControlDialogModel')
    dm.Width, dm.Height, dm.Title = 260, 190, 'Dicionário pessoal e palavras que não devem ser corrigidas'

    def add(tipo, nome, **pr):
        m = dm.createInstance('com.sun.star.awt.UnoControl' + tipo + 'Model')
        for k, v in pr.items():
            setattr(m, k, v)
        dm.insertByName(nome, m)
    add('FixedText', 'r1', PositionX=6, PositionY=6, Width=120, Height=10, Label='~Dicionário pessoal:')
    add('ListBox', 'pessoal', PositionX=6, PositionY=18, Width=120, Height=130, Border=1)
    add('Button', 'rem1', PositionX=6, PositionY=152, Width=120, Height=14, Label='~Remover do dicionário')
    add('FixedText', 'r2', PositionX=134, PositionY=6, Width=120, Height=10, Label='~Não corrigir automaticamente:')
    add('ListBox', 'naocorr', PositionX=134, PositionY=18, Width=120, Height=130, Border=1)
    add('Button', 'rem2', PositionX=134, PositionY=152, Width=120, Height=14, Label='Re~mover da lista')
    add('Button', 'fechar', PositionX=196, PositionY=170, Width=58, Height=14, Label='~Fechar', DefaultButton=True)
    dlg = ay_revisao.servico(ctx, 'com.sun.star.awt.UnoControlDialog')
    dlg.setModel(dm)

    def preencher():
        dlg.getControl('pessoal').getModel().StringItemList = tuple(revisao.palavras_pessoais())
        dlg.getControl('naocorr').getModel().StringItemList = tuple(sorted(revisao.config['NaoCorrigir']))

    def rem1():
        p = dlg.getControl('pessoal').getSelectedItem()
        if p:
            revisao.remover_do_dicionario(p)
            preencher()

    def rem2():
        p = dlg.getControl('naocorr').getSelectedItem()
        if p:
            revisao.remover_nao_corrigir(p)
            preencher()
    dlg.getControl('rem1').addActionListener(_Remover(rem1))
    dlg.getControl('rem2').addActionListener(_Remover(rem2))
    dlg.getControl('fechar').addActionListener(_Fechar(dlg, 1))
    preencher()
    dlg.createPeer(ay_revisao.servico(ctx, 'com.sun.star.awt.Toolkit'), frame.getContainerWindow())
    dlg.execute()
    dlg.dispose()


class Fabrica(unohelper.Base, XUIElementFactory, XServiceInfo):
    def __init__(self, ctx, *args):
        self.ctx = ctx

    def createUIElement(self, url, args):
        d = {a.Name: a.Value for a in args}
        try:
            return Painel(self.ctx, d.get('Frame'), d.get('ParentWindow'), url)
        except Exception:
            ay_revisao.registrar('fábrica do painel: ' + traceback.format_exc())
            raise

    def getImplementationName(self):
        return 'br.ayescreva.Paineis'

    def supportsService(self, nome):
        return nome == 'com.sun.star.ui.UIElementFactory'

    def getSupportedServiceNames(self):
        return ('com.sun.star.ui.UIElementFactory',)
