# -*- coding: utf-8 -*-
"""Painel "Revisão com IA" e diálogo "Gerenciar IA local" (entrega C).

Fluxo: selecionar um trecho → escolher o pedido → Revisar seleção → a sugestão aparece aos poucos (pode cancelar) →
original e sugestão lado a lado, com avisos de preservação → Aceitar (alteração controlada, uma ação de desfazer)
ou Rejeitar. Se o trecho mudar enquanto a IA trabalha, a sugestão não é aplicada.

Regras: o documento só é lido e alterado na thread principal; a thread de trabalho recebe só texto. Nada vai para
a internet: o servidor de IA roda neste computador em 127.0.0.1, e o download do modelo só acontece pelo diálogo.
SPDX-License-Identifier: MPL-2.0
"""
import json
import os
import shutil
import threading
import time
import traceback

import uno
import unohelper
from com.sun.star.awt import XActionListener, XItemListener, XWindowListener
from com.sun.star.lang import XComponent
from com.sun.star.ui import XSidebarPanel, XToolPanel, XUIElement

import ay_dialogos as D
import ay_ia as IA
import ay_ia_texto as T
import ay_revisao

XDL = 'vnd.sun.star.extension://br.ayescreva.extensao/IA.xdl'
DECK = 'RevisaoIADeck'
COMANDO_DECK = '.uno:SidebarDeck.' + DECK
NO_CONFIG = '/br.ayescreva.Configuracao/IA'
LARGURA_MINIMA = 240
PS_X, PS_WIDTH, PS_SIZE = 1, 4, 12
OCIOSO_S = 600                       # servidor parado depois de 10 min sem uso (libera a memória)
ACOES = tuple(T.ACOES)


def registrar(m):
    ay_revisao.registrar('IA: ' + m)


# ay_ia (rede local, processos) só é carregado quando a pessoa usa a IA: o editor não carrega esses módulos ao iniciar
IA.registrar = registrar


# ---------------------------------------------------------------- gerente (um por aplicativo)
class Gerente:
    _unico = None

    @classmethod
    def obter(cls, ctx):
        if cls._unico is None:
            cls._unico = cls(ctx)
        return cls._unico

    def __init__(self, ctx):
        self.ctx = ctx
        self.servidor = None
        self.ultimo_uso = 0
        self.ocupado = 0
        self.carregando = False
        self.paineis = []
        self.trava = threading.Lock()
        threading.Thread(target=self._vigiar_ocioso, daemon=True).start()

    # configuração
    def _cfg(self, escrita=False):
        prov = D.servico(self.ctx, 'com.sun.star.configuration.ConfigurationProvider')
        pv = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
        pv.Name, pv.Value = 'nodepath', NO_CONFIG
        tipo = 'com.sun.star.configuration.ConfigurationUpdateAccess' if escrita else 'com.sun.star.configuration.ConfigurationAccess'
        return prov.createInstanceWithArguments(tipo, (pv,))

    def config(self):
        c = self._cfg()
        return {'pasta': c.getPropertyValue('Pasta') or IA.pasta_padrao(), 'modelo': c.getPropertyValue('Modelo') or '',
                'controlada': bool(c.getPropertyValue('ComoAlteracaoControlada'))}

    def gravar(self, **kw):
        c = self._cfg(escrita=True)
        nomes = {'pasta': 'Pasta', 'modelo': 'Modelo', 'controlada': 'ComoAlteracaoControlada'}
        for k, v in kw.items():
            c.setPropertyValue(nomes[k], v)
        c.commitChanges()

    # arquivos
    def caminhos(self, cfg=None):
        cfg = cfg or self.config()
        cat = IA.catalogo()
        motor = os.path.join(cfg['pasta'], 'motor-' + cat['motor']['versao'], cat['motor']['executavel'])
        modelo = next((m for m in cat['modelos'] if m['id'] == cfg['modelo']), None)
        arq = os.path.join(cfg['pasta'], 'modelos', modelo['arquivo']) if modelo else None
        return motor, modelo, arq

    def pronto(self):
        motor, modelo, arq = self.caminhos()
        return bool(modelo) and os.path.exists(motor) and arq is not None and os.path.exists(arq)

    def descricao_estado(self):
        motor, modelo, arq = self.caminhos()
        if not modelo or not (arq and os.path.exists(arq)) or not os.path.exists(motor):
            return ('IA local não instalada (opcional). O editor funciona sem ela. Use "Gerenciar IA local…" para escolher e '
                    'baixar um modelo; nada é enviado para a internet.')
        if self.carregando:
            return f'IA local: carregando {modelo["nome"]} (no primeiro uso pode levar 1 a 2 minutos)…'
        ativo = self.servidor is not None and self.servidor.ativo()
        return f'IA local: {modelo["nome"]} — ' + ('pronta.' if ativo else 'pronta (o modelo carrega no primeiro pedido).')

    # servidor
    def servidor_pronto(self):
        """Na thread de trabalho: inicia o servidor se preciso (pode levar alguns segundos)."""
        with self.trava:
            motor, modelo, arq = self.caminhos()
            if self.servidor is not None and self.servidor.ativo() and self.servidor.modelo == os.path.abspath(arq):
                return self.servidor
            if self.servidor is not None:
                self.servidor.parar()
            threads = max(1, (os.cpu_count() or 2) // 2 + 1)        # deixa núcleos livres para o editor
            self.servidor = IA.Servidor(motor, arq, contexto=4096, threads=threads)
            self.carregando = True
            try:
                self.servidor.iniciar()
            finally:
                self.carregando = False
            registrar(f'servidor iniciado na porta {self.servidor.porta} ({modelo["id"]}, {threads} threads)')
            return self.servidor

    def painel_do_quadro(self, frame):
        return next((p for p in reversed(self.paineis) if p.Frame == frame), None)

    def parar(self):
        with self.trava:
            if self.servidor is not None:
                self.servidor.parar()
                self.servidor = None

    def _vigiar_ocioso(self):
        while True:
            time.sleep(30)
            if (self.servidor is not None and not self.ocupado and self.ultimo_uso
                    and time.time() - self.ultimo_uso > OCIOSO_S):
                registrar('servidor parado por inatividade')
                self.parar()


# ---------------------------------------------------------------- leitura e aplicação no documento (thread principal)
class TrechoInvalido(Exception):
    pass


def ler_selecao(doc):
    """(intervalo, texto normalizado) da seleção, só com texto comum."""
    sel = doc.getCurrentController().getSelection()
    if sel is None or not sel.supportsService('com.sun.star.text.TextRanges') or sel.getCount() != 1:
        raise TrechoInvalido('Selecione um trecho de texto (uma seleção só).')
    rng = sel.getByIndex(0)
    texto = rng.getString().replace('\r\n', '\n')
    if len(texto.strip()) < 3:
        raise TrechoInvalido('Selecione o trecho que a IA deve revisar.')
    if len(texto) > 6000:
        raise TrechoInvalido('Trecho longo demais para a IA local (até cerca de 6.000 caracteres por vez).')
    cur = rng.getText().createTextCursorByRange(rng)
    e = cur.createEnumeration()
    while e.hasMoreElements():
        par = e.nextElement()
        if not par.supportsService('com.sun.star.text.Paragraph'):
            raise TrechoInvalido('O trecho inclui uma tabela; selecione só texto.')
        pe = par.createEnumeration()
        while pe.hasMoreElements():
            por = pe.nextElement()
            if por.TextPortionType not in ('Text', 'SoftPageBreak'):
                raise TrechoInvalido('O trecho tem campo, nota, imagem, marcador ou alteração controlada. Selecione só texto '
                                     'comum (a IA não mexe nesses elementos).')
    return rng, texto


def aplicar(doc, rng, original, sugestao, acao, controlada=True):
    """Aplica só as diferenças, numa ação de desfazer. Confere antes se o trecho ainda é o mesmo."""
    atual = rng.getString().replace('\r\n', '\n')
    if atual != original:
        raise TrechoInvalido('O trecho mudou depois do pedido; a sugestão não foi aplicada. Peça de novo.')
    if original.count('\n') != sugestao.count('\n'):
        raise TrechoInvalido('A sugestão junta ou separa parágrafos; ela não foi aplicada.')
    eds = T.edicoes(original, sugestao)
    um = doc.getUndoManager()
    gravava = doc.RecordChanges
    um.enterUndoContext(f'Sugestão da IA ({T.ACOES[acao][0]})')
    try:
        if controlada:
            doc.RecordChanges = True
        texto = rng.getText()
        for ini, fim, novo in eds:            # da direita para a esquerda: as posições anteriores não mudam
            c = texto.createTextCursorByRange(rng.getStart())
            c.goRight(ini, False)
            c.goRight(fim - ini, True)
            c.setString(novo)
    finally:
        doc.RecordChanges = gravava
        um.leaveUndoContext()
    return len(eds)


# ---------------------------------------------------------------- painel
class _Ouvinte(unohelper.Base, XActionListener, XItemListener, XWindowListener):
    def __init__(self, painel):
        self.p = painel

    def actionPerformed(self, ev):
        self.p.executar('_botao_' + ev.ActionCommand)

    def itemStateChanged(self, ev):
        self.p.executar('_mudou_' + ev.Source.getModel().Name)

    def windowResized(self, ev):
        self.p.executar('_redimensionar')

    def windowMoved(self, ev): pass
    def windowShown(self, ev): pass
    def windowHidden(self, ev): pass
    def disposing(self, ev): pass


class PainelIA(unohelper.Base, XUIElement, XToolPanel, XSidebarPanel, XComponent):
    def __init__(self, ctx, frame, parent, url):
        self.ctx, self.Frame, self.ResourceURL = ctx, frame, url
        self.Type = uno.getConstantByName('com.sun.star.ui.UIElementType.TOOLPANEL')
        self.g = Gerente.obter(ctx)
        prov = ay_revisao.servico(ctx, 'com.sun.star.awt.ContainerWindowProvider')
        peer = parent.queryInterface(uno.getTypeByName('com.sun.star.awt.XWindowPeer'))
        self.win = prov.createContainerWindow(XDL, '', peer, None)
        self.altura = self.win.getPosSize().Height
        self.win.setPosSize(0, 0, LARGURA_MINIMA, self.altura, PS_SIZE)
        self.win.setVisible(True)
        self.c = {c.getModel().Name: c for c in self.win.getControls()}
        self.ouvinte = _Ouvinte(self)
        for n in ('pedir', 'cancelar', 'aceitar', 'rejeitar', 'gerenciar'):
            self.c[n].setActionCommand(n)
            self.c[n].addActionListener(self.ouvinte)
        self.c['controlada'].addItemListener(self.ouvinte)
        self.win.addWindowListener(self.ouvinte)
        self.c['acao'].getModel().StringItemList = tuple(T.ACOES[a][0] for a in ACOES)
        self.c['acao'].selectItemPos(0, True)
        self.c['controlada'].getModel().State = 1 if self.g.config()['controlada'] else 0
        self.pedido = None
        self.trecho = None              # (intervalo, original, ação, documento)
        self.sugestao = ''
        self.ouvintes_fim = []
        self.g.paineis.append(self)
        registrar(f'painel {id(self):x} criado ({len(self.g.paineis)} aberto(s))')
        self._redimensionar()
        self.atualizar()
        self._pre_carregar()

    def _pre_carregar(self):
        """Painel aberto com o modelo instalado: o modelo já começa a carregar em segundo plano, para o primeiro
        pedido não esperar a leitura do disco. Fica carregado até 10 minutos sem pedidos."""
        g = self.g
        if not g.pronto() or g.carregando or (g.servidor is not None and g.servidor.ativo()):
            return
        ctx = self.ctx

        def trabalho():
            try:
                g.servidor_pronto()
                g.ultimo_uso = time.time()
            except Exception as e:
                registrar(f'pré-carga do modelo: {e}')
            finally:
                g.carregando = False
            ay_revisao.adiar(ctx, lambda: [p.atualizar() for p in list(g.paineis)])
        g.carregando = True                 # já mostra "carregando" enquanto a thread começa
        self.atualizar()
        threading.Thread(target=trabalho, daemon=True).start()

    # XUIElement / XToolPanel / XSidebarPanel / XComponent
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
        return LARGURA_MINIMA

    def dispose(self):
        registrar(f'painel {id(self):x} descartado')
        if self.pedido is not None:
            self.pedido.cancelar()
        if self in self.g.paineis:
            self.g.paineis.remove(self)

    def addEventListener(self, o):
        self.ouvintes_fim.append(o)

    def removeEventListener(self, o):
        if o in self.ouvintes_fim:
            self.ouvintes_fim.remove(o)

    # utilidades
    def executar(self, metodo, *args):
        try:
            getattr(self, metodo)(*args)
        except TrechoInvalido as e:
            self._estado(str(e))
        except Exception:
            registrar(f'painel {metodo}: ' + traceback.format_exc())
            self._estado('Não foi possível concluir. Detalhes em ayescreva-extensao.log (pasta temporária).')

    def _estado(self, t):
        self.c['estado'].getModel().Label = t

    def _ativar(self, n, sim):
        self.c[n].getModel().Enabled = bool(sim)

    def _redimensionar(self):
        w = self.win.getPosSize().Width
        m = 3
        meia = (w - 3 * m) // 2
        for n in ('estado', 'rotulo_original', 'original', 'rotulo_sugestao', 'sugestao', 'avisos', 'controlada', 'gerenciar'):
            self.c[n].setPosSize(m, 0, max(40, w - 2 * m), 0, PS_X | PS_WIDTH)
        for n in ('pedir', 'aceitar'):
            self.c[n].setPosSize(m, 0, meia, 0, PS_X | PS_WIDTH)
        for n in ('cancelar', 'rejeitar'):
            self.c[n].setPosSize(2 * m + meia, 0, meia, 0, PS_X | PS_WIDTH)
        rot = self.c['rotulo_acao'].getPosSize()
        x = rot.X + rot.Width + m
        self.c['acao'].setPosSize(x, 0, max(40, w - x - m), 0, PS_X | PS_WIDTH)

    def _doc(self):
        return self.Frame.getController().getModel()

    def atualizar(self):
        if self.pedido is None:
            self._estado(self.g.descricao_estado())
        self._ativar('pedir', self.pedido is None)
        self._ativar('cancelar', self.pedido is not None)

    # pedido
    def _botao_pedir(self):
        if self.pedido is not None:            # um pedido por vez (o botão também fica desativado)
            return
        if not self.g.pronto():
            self._estado(self.g.descricao_estado())
            return
        doc = self._doc()
        rng, texto = ler_selecao(doc)
        acao = ACOES[max(0, self.c['acao'].getSelectedItemPos())]
        self.trecho = (rng, texto, acao, doc)
        self.sugestao = ''
        self.c['original'].getModel().Text = texto
        self.c['sugestao'].getModel().Text = ''
        self.c['avisos'].getModel().Label = ''
        self._ativar('aceitar', False)
        self._ativar('rejeitar', False)
        self._estado('Preparando a IA local…')
        mensagens = T.prompt(acao, texto)
        gerente = self.g
        modelo = self.g.caminhos()[1]
        painel = self

        ultimo = [0.0]

        def avancou(t):
            # no máximo ~6 atualizações por segundo na thread principal
            if time.time() - ultimo[0] >= 0.15:
                ultimo[0] = time.time()
                ay_revisao.adiar(painel.ctx, lambda: painel._avancou(t))

        # o pedido existe desde já: Cancelar vale também enquanto o servidor ainda está carregando o modelo
        p = IA.Pedido(None, mensagens, max_tokens=min(2048, 80 + len(texto)), sem_pensar=modelo.get('sem_pensar', True),
                      ao_avancar=avancou, ao_terminar=lambda ped: ay_revisao.adiar(painel.ctx, lambda: painel._terminou(ped)))

        def trabalho():
            # thread de trabalho: só texto e o servidor local; nada do documento
            gerente.ocupado += 1
            try:
                try:
                    p.servidor = gerente.servidor_pronto()
                except Exception as e:
                    registrar(f'pedido {id(p):x}: servidor não iniciou: {e}')
                    ay_revisao.adiar(painel.ctx, lambda msg=f'A IA local não iniciou: {e}': painel._falhou(p, msg))
                    return
                if p.cancelado.is_set():
                    p.medidas['cancelado'] = True
                    ay_revisao.adiar(painel.ctx, lambda: painel._terminou(p))
                    return
                ay_revisao.adiar(painel.ctx, lambda: painel._estado('A IA local está escrevendo… (você pode continuar editando)'))
                p._rodar()
            finally:
                gerente.ocupado -= 1
                gerente.ultimo_uso = time.time()

        self.pedido = p
        registrar(f'pedido {id(p):x}: {acao}, {len(texto)} caracteres (painel {id(self):x})')
        threading.Thread(target=trabalho, daemon=True).start()
        self.atualizar()

    def _avancou(self, t):
        # progresso em texto (lido por leitores de tela): a sugestão aparece aos poucos e o estado conta os caracteres
        self.c['sugestao'].getModel().Text = t
        self._estado(f'A IA local está escrevendo… {len(t)} de ~{len(self.trecho[1])} caracteres (você pode continuar editando)')

    def _falhou(self, ped, msg):
        if ped is not self.pedido:
            return
        self.pedido = None
        self.atualizar()
        self._estado(msg)

    def _terminou(self, ped):
        registrar(f'pedido {id(ped):x}: terminou em {ped.medidas.get("segundos")} s, {len(ped.texto)} caracteres'
                  + (', cancelado' if ped.cancelado.is_set() else '') + (f', erro {ped.erro}' if ped.erro else '')
                  + ('' if ped is self.pedido else ', fora de hora (ignorado)'))
        if ped is not self.pedido:              # término de um pedido que já não é o atual
            return
        self.pedido = None
        self.atualizar()
        if ped.cancelado.is_set():
            self._estado('Pedido cancelado. Nada foi alterado.')
            return
        if ped.erro:
            self._estado(f'A IA local não respondeu: {ped.erro}')
            return
        rng, original, acao, doc = self.trecho
        sug = T.limpar_resposta(ped.texto, original)
        self.sugestao = sug
        self.c['sugestao'].getModel().Text = sug
        probl = T.conferir_preservacao(original, sug, acao)
        if acao != 'resumir' and original.count('\n') != sug.count('\n'):
            probl.append('a sugestão junta ou separa parágrafos')
        mud = T.resumo_mudancas(original, sug)
        seg = f'{ped.medidas.get("segundos", 0):.1f}'.replace('.', ',')
        if sug == original:
            self._estado(f'A IA não sugeriu mudanças ({seg} s).')
            self._ativar('rejeitar', True)
            return
        if acao == 'resumir':
            self.c['avisos'].getModel().Label = ('Resumo: não substitui o trecho. Copie o que quiser usar. '
                                                 + ('Atenção: ' + '; '.join(probl) + '.' if probl else ''))
            self._estado(f'Resumo pronto em {seg} s.')
            self._ativar('rejeitar', True)
            return
        if probl:
            self.c['avisos'].getModel().Label = ('Aceitar bloqueado — a sugestão não preserva o original: ' + '; '.join(probl)
                                                 + '. A IA não pode inventar nem apagar dados.')
            self._estado(f'Sugestão pronta em {seg} s, com problemas.')
            self._ativar('aceitar', False)
        else:
            self.c['avisos'].getModel().Label = (f'{mud["edicoes"]} trecho(s) alterado(s). Números, datas, citações, endereços, siglas '
                                                 'e nomes conferidos: preservados.')
            self._estado(f'Sugestão pronta em {seg} s. Confira e aceite ou rejeite.')
            self._ativar('aceitar', True)
        self._ativar('rejeitar', True)

    def _botao_cancelar(self):
        if self.pedido is not None:
            self.pedido.cancelar()
        self._estado('Cancelando…')

    def _botao_aceitar(self):
        if not self.trecho or not self.sugestao:
            return
        rng, original, acao, doc = self.trecho
        controlada = self.c['controlada'].getModel().State == 1
        n = aplicar(doc, rng, original, self.sugestao, acao, controlada)
        self._limpar()
        self._estado(f'Sugestão aplicada ({n} trecho(s))' + (' como alteração controlada: aceite ou rejeite em Revisão › Alterações. '
                                                              if controlada else '. ') + 'Ctrl+Z desfaz.')

    def _botao_rejeitar(self):
        self._limpar()
        self._estado('Sugestão descartada. Nada foi alterado.')

    def _limpar(self):
        self.trecho, self.sugestao = None, ''
        for n in ('original', 'sugestao'):
            self.c[n].getModel().Text = ''
        self.c['avisos'].getModel().Label = ''
        self._ativar('aceitar', False)
        self._ativar('rejeitar', False)

    def _mudou_controlada(self):
        self.g.gravar(controlada=self.c['controlada'].getModel().State == 1)

    def _botao_gerenciar(self):
        gerenciar(self.ctx, self.Frame)
        for p in list(self.g.paineis):
            p.atualizar()


# ---------------------------------------------------------------- Gerenciar IA local
def _mb(n):
    return f'{n / 2**30:.1f} GB'.replace('.', ',') if n >= 2**30 else f'{n / 2**20:.0f} MB'


def gerenciar(ctx, frame):
    g = Gerente.obter(ctx)
    cat = IA.catalogo()
    cfg = g.config()
    resultados = {}
    try:
        with open(os.path.join(IA.DADOS, 'ia-avaliacao.json'), encoding='utf-8') as f:
            resultados = {r['id']: r for r in json.load(f).get('modelos', [])}
    except Exception:
        pass
    d = D.Dialogo(ctx, 'Gerenciar IA local', 360, 232, nome='gerenciar_ia')
    d.add('FixedText', 'explica', 6, 4, 348, 30, MultiLine=True,
          Label='A IA local é opcional: o editor funciona sem ela. O modelo roda neste computador e nada é enviado para a internet. '
                'O download só acontece quando você pede, vem do endereço oficial de cada modelo e é conferido (SHA-256).')
    d.rotulo('r_modelos', 6, 36, 150, '~Modelos disponíveis:')
    nomes = []
    for m in cat['modelos']:
        nomes.append(m['nome'] + (' — recomendado' if m.get('recomendado') else ''))
    d.add('ListBox', 'modelos', 6, 48, 150, 92, StringItemList=tuple(nomes), Border=1)
    d.rotulo('r_detalhe', 160, 36, 194, '~Sobre o modelo:')
    d.add('Edit', 'detalhe', 160, 48, 194, 92, MultiLine=True, ReadOnly=True, VScroll=True, Border=1)
    d.rotulo('r_pasta', 6, 146, 40, '~Pasta:')
    d.add('Edit', 'pasta', 50, 146, 238, 14, Text=cfg['pasta'])
    d.botao('escolher', 292, 146, 62, 'Escol~her…', lambda: escolher())
    d.add('FixedText', 'espaco', 50, 162, 304, 10)
    # progresso do download em texto (lido por leitores de tela)
    d.add('FixedText', 'situacao', 6, 176, 348, 30, MultiLine=True, Label='Nenhum download em andamento.')
    estado = {'cancelar': None, 'baixando': False}

    def atual():
        i = d.c('modelos').getSelectedItemPos()
        return cat['modelos'][i] if 0 <= i < len(cat['modelos']) else None

    def arquivos(m, pasta):
        motor = os.path.join(pasta, 'motor-' + cat['motor']['versao'], cat['motor']['executavel'])
        return motor, os.path.join(pasta, 'modelos', m['arquivo'])

    def mostrar():
        m = atual()
        if m is None:
            return
        pasta = d.c('pasta').getText().strip() or IA.pasta_padrao()
        motor, arq = arquivos(m, pasta)
        r = resultados.get(m['id'], {})
        linhas = [m['nome'], f'Editor: {m["editor"]} · Licença: {m["licenca"]}', f'Tamanho do download: {_mb(m["tamanho"])}',
                  f'Origem: {m["origem"]}']
        if r:
            linhas.append(f'Medido no computador de testes do AY ({r.get("computador", "")}): {r.get("resumo", "")}')
        linhas.append('Situação: ' + ('instalado' if os.path.exists(arq) else 'não instalado') + (' (em uso)' if cfg['modelo'] == m['id'] and os.path.exists(arq) else ''))
        d.m('detalhe').Text = '\n'.join(linhas)
        try:
            livre = IA.espaco_livre(pasta)
            precisa = m['tamanho'] + (0 if os.path.exists(motor) else cat['motor']['tamanho'])
            d.m('espaco').Label = f'Espaço livre: {_mb(livre)} · este modelo precisa de {_mb(precisa)}'
        except Exception:
            d.m('espaco').Label = ''
        d.m('baixar').Enabled = not estado['baixando'] and not os.path.exists(arq)
        d.m('usar').Enabled = not estado['baixando'] and os.path.exists(arq) and os.path.exists(motor)
        d.m('remover').Enabled = not estado['baixando'] and os.path.exists(arq)
        d.m('cancelar').Enabled = estado['baixando']

    def escolher():
        fp = D.servico(ctx, 'com.sun.star.ui.dialogs.FolderPicker')
        if fp.execute() == 1:
            d.c('pasta').setText(uno.fileUrlToSystemPath(fp.getDirectory()))
            mostrar()

    def baixar():
        m = atual()
        pasta = d.c('pasta').getText().strip() or IA.pasta_padrao()
        motor, arq = arquivos(m, pasta)
        precisa = m['tamanho'] + (0 if os.path.exists(motor) else cat['motor']['tamanho'])
        if IA.espaco_livre(pasta) < precisa + 500 * 2**20:
            D.mensagem(ctx, frame.getContainerWindow(), 'Gerenciar IA local', f'Espaço insuficiente em {pasta}. Escolha outra pasta.', 'WARNINGBOX')
            return
        if D.mensagem(ctx, frame.getContainerWindow(), 'Baixar modelo de IA',
                      f'Baixar {m["nome"]} ({_mb(m["tamanho"])}) de {m["origem"]}'
                      + ('' if os.path.exists(motor) else f' e o motor llama.cpp ({_mb(cat["motor"]["tamanho"])}) do GitHub')
                      + f' para {pasta}? Só os arquivos do modelo e do motor são transferidos; nenhum documento.', 'QUERYBOX', 3) != 2:
            return
        cancelar = threading.Event()
        estado.update(cancelar=cancelar, baixando=True)
        mostrar()

        def progresso(rotulo):
            ultimo = [0.0]

            def f(feito, total):
                if time.time() - ultimo[0] < 0.25 and feito < total:      # no máximo 4 atualizações por segundo
                    return
                ultimo[0] = time.time()
                pct = f' ({100 * feito // total}%)' if total else ''
                texto = f'Baixando {rotulo.lower()}: {_mb(feito)} de {_mb(total)}{pct}. Pode cancelar.'
                ay_revisao.adiar(ctx, lambda: setattr(d.m('situacao'), 'Label', texto))
            return f

        def trabalho():
            try:
                if not os.path.exists(motor):
                    zipf = os.path.join(pasta, 'motor.zip')
                    IA.baixar(cat['motor']['url'], zipf, cat['motor']['sha256'], cat['motor']['tamanho'], progresso('Motor'), cancelar)
                    IA.extrair_motor(zipf, os.path.dirname(motor), _arquivos_motor(zipf))
                    os.remove(zipf)
                IA.baixar(m['url'], arq, m['sha256'], m['tamanho'], progresso('Modelo'), cancelar)
                msg = f'{m["nome"]} baixado e conferido (SHA-256). Clique em "Usar este modelo".'
            except IA.Cancelado:
                msg = 'Download cancelado. Os arquivos parciais foram apagados.'
            except Exception as e:
                msg = f'Falha no download: {e}'
            def fim():
                estado['baixando'] = False
                d.m('situacao').Label = msg
                mostrar()
            ay_revisao.adiar(ctx, fim)
        threading.Thread(target=trabalho, daemon=True).start()

    def cancelar():
        if estado['cancelar'] is not None:
            estado['cancelar'].set()

    def usar():
        m = atual()
        g.parar()
        g.gravar(modelo=m['id'], pasta=d.c('pasta').getText().strip() or IA.pasta_padrao())
        cfg.update(g.config())
        d.m('situacao').Label = f'{m["nome"]} será usado nos próximos pedidos.'
        mostrar()

    def remover():
        m = atual()
        pasta = d.c('pasta').getText().strip() or IA.pasta_padrao()
        _, arq = arquivos(m, pasta)
        if D.mensagem(ctx, frame.getContainerWindow(), 'Remover modelo', f'Apagar {m["arquivo"]} ({_mb(m["tamanho"])}) de {pasta}?',
                      'QUERYBOX', 3) != 2:
            return
        if cfg['modelo'] == m['id']:
            g.parar()
        os.remove(arq)
        d.m('situacao').Label = f'{m["nome"]} removido.'
        mostrar()

    d.botao('baixar', 6, 212, 60, '~Baixar…', baixar)
    d.botao('cancelar', 70, 212, 60, 'Ca~ncelar download', cancelar)
    d.botao('usar', 134, 212, 76, '~Usar este modelo', usar)
    d.botao('remover', 214, 212, 60, '~Remover', remover)
    d.botao('fechar', 294, 212, 60, '~Fechar', lambda: d.fechar(None), padrao=True)
    d.ao_mudar('modelos', mostrar)
    d.ao_digitar('pasta', mostrar)

    def iniciar():
        i = next((k for k, m in enumerate(cat['modelos']) if m['id'] == cfg['modelo']), next((k for k, m in enumerate(cat['modelos']) if m.get('recomendado')), 0))
        d.c('modelos').selectItemPos(i, True)
        mostrar()
    d.executar(frame.getContainerWindow(), iniciar)
    if estado['cancelar'] is not None:
        estado['cancelar'].set()          # fechar o diálogo cancela um download em andamento


def _arquivos_motor(zipf):
    """O servidor e as bibliotecas que ele carrega (DLLs do mesmo pacote)."""
    import zipfile
    with zipfile.ZipFile(zipf) as z:
        return [os.path.basename(n) for n in z.namelist() if n.lower().endswith(('.dll', 'llama-server.exe'))]
