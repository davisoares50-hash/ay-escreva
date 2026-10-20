# -*- coding: utf-8 -*-
"""Revisão de texto do AY integrada ao motor.

- Correção automática ao digitar: decide quando a palavra termina (espaço, Enter, Tab ou pontuação) e aplica no
  ciclo seguinte da interface, como UMA ação de desfazer ("Correção automática do AY: nao → não").
- Ao desfazer uma correção automática, oferece "Não corrigir novamente" numa barra de informação.
- Níveis: Ortografia (sublinhado do motor), Gramática e pontuação e Estilo (categorias do Lightproof pt-BR + regras
  de estilo do AY).
- Análise de seleção/documento para o painel Assistente AY: o documento só é lido e marcado na thread principal,
  em fatias curtas; uma thread de trabalho só analisa TEXTO (serviços de língua), como o verificador gramatical do
  motor. Progresso e cancelamento. Nenhuma thread Python toca o documento (docs/REVISAO-E-IA.md §4).
SPDX-License-Identifier: MPL-2.0
"""
import os
import queue
import re
import sys
import threading
import time
import traceback
from urllib.parse import quote

import uno
import unohelper
from com.sun.star.awt import XCallback, XKeyHandler
from com.sun.star.document import XUndoManagerListener
from com.sun.star.frame import XStatusListener

import ay_correcao
import ay_estilo

NO_CONFIG = '/br.ayescreva.Configuracao/Revisao'
NO_LIGHTPROOF = '/org.openoffice.Lightproof_pt_BR/Leaves/pt_BR'
LIGHTPROOF = 'org.libreoffice.comp.pyuno.Lightproof.pt_BR'
CAT_GRAMATICA = ('grammar', 'cap', 'dup', 'pair', 'spaces', 'spaces2', 'spaces3', 'quotation', 'apostrophe',
                 'ellipsis', 'aha', 'malmau', 'meiameio', 'verbo', 'pronominal', 'pronome', 'porque', 'paronimo',
                 'composto')
CAT_ESTILO = ('metric', 'gerund', 'nonmetric')        # pleonasmos, gerundismo, cacofonia
ESTILO_LIGHTPROOF = re.compile(r'pleonasm|gerund|cacofon', re.IGNORECASE)
LIMITES = set(' \t\r\n.,;:!?)]}…”»')
TECLAS_LIMITE = (1280, 1282, 1284)                     # Enter, Tab, Espaço (com.sun.star.awt.Key)
MODIFICADORES_BLOQUEIO = 2 | 4 | 8                     # Ctrl, Alt, Ctrl direito (KeyModifier MOD1|MOD2|MOD3)
TITULO_AUTO = 'Correção automática do AY: '
TITULO_REVISAO = 'Revisão do AY: '
ESTILOS_PROTEGIDOS = ('Quotations', 'Citações', 'Source Text', 'Texto-fonte')
# Texto pré-formatado costuma ser código; num .txt, porém, é o estilo de todo o documento (importação do motor)
ESTILOS_PREFORMATADOS = ('Preformatted Text', 'Texto pré-formatado')
PALAVRA = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['’-][A-Za-zÀ-ÖØ-öø-ÿ]+)*")

registrar = print          # trocado por _log da extensão
DEPURAR = bool(os.environ.get('AY_DEPURAR_REVISAO'))   # testes: registra cada decisão da correção automática


def servico(ctx, nome):
    return ctx.ServiceManager.createInstanceWithContext(nome, ctx)


def props(**kw):
    res = []
    for k, v in kw.items():
        p = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
        p.Name, p.Value = k, v
        res.append(p)
    return tuple(res)


def vazio():
    return uno.Any('[]com.sun.star.beans.PropertyValue', ())


class _Adiado(unohelper.Base, XCallback):
    def __init__(self, f):
        self.f = f

    def notify(self, dados):
        try:
            self.f()
        except Exception:
            registrar('revisão (adiado): ' + traceback.format_exc())


def adiar(ctx, f):
    servico(ctx, 'com.sun.star.awt.AsyncCallback').addCallback(_Adiado(f), uno.Any('void', None))


class _Estado(unohelper.Base, XStatusListener):
    def __init__(self):
        self.estado = None
        self.ativo = False

    def statusChanged(self, ev):
        self.ativo = ev.IsEnabled
        self.estado = ev.State

    def disposing(self, ev):
        pass


def estado_comando(ctx, frame, comando):
    """Estado atual (True/False) de um comando de alternância do motor, como .uno:SpellOnline."""
    u = uno.createUnoStruct('com.sun.star.util.URL')
    u.Complete = comando
    _, u = servico(ctx, 'com.sun.star.util.URLTransformer').parseStrict(u)
    d = frame.queryDispatch(u, '', 0)
    if d is None:
        return None
    o = _Estado()
    d.addStatusListener(o, u)
    d.removeStatusListener(o, u)
    return o.estado if isinstance(o.estado, bool) else None


def despachar(ctx, frame, comando, **args):
    servico(ctx, 'com.sun.star.frame.DispatchHelper').executeDispatch(frame, comando, '', 0, props(**args))


class Teclado(unohelper.Base, XKeyHandler):
    """Observa as teclas do documento; nunca consome a tecla (devolve False)."""

    def __init__(self, revisao, controlador):
        self.revisao = revisao
        self.ctrl = controlador

    def keyPressed(self, ev):
        try:
            if not self.revisao.config['CorrecaoAutomatica'] or ev.Modifiers & MODIFICADORES_BLOQUEIO:
                return False
            ch = getattr(ev.KeyChar, 'value', ev.KeyChar) or ''
            if ev.KeyCode in TECLAS_LIMITE or ch in LIMITES:
                self.revisao.palavra_terminada(self.ctrl)
        except Exception:
            registrar('teclado: ' + traceback.format_exc())
        return False

    def keyReleased(self, ev):
        return False

    def disposing(self, ev):
        pass


class OuvinteDesfazer(unohelper.Base, XUndoManagerListener):
    """Ao desfazer uma correção automática do AY, oferece "Não corrigir novamente"."""

    def __init__(self, revisao, doc):
        self.revisao, self.doc = revisao, doc

    def actionUndone(self, ev):
        try:
            titulo = ev.UndoActionTitle or ''
            if titulo.startswith(TITULO_AUTO):
                original = titulo[len(TITULO_AUTO):].split(' → ')[0]
                self.revisao.oferecer_nao_corrigir(self.doc, original)
        except Exception:
            registrar('desfazer: ' + traceback.format_exc())

    def undoActionAdded(self, ev): pass
    def actionRedone(self, ev): pass
    def allActionsCleared(self, ev): pass
    def redoActionsCleared(self, ev): pass
    def resetAll(self, ev): pass
    def enteredContext(self, ev): pass
    def enteredHiddenContext(self, ev): pass
    def leftContext(self, ev): pass
    def leftHiddenContext(self, ev): pass
    def cancelledContext(self, ev): pass
    def disposing(self, ev): pass


class Revisao:
    """Estado da revisão no processo (uma instância por contexto)."""

    _instancia = None

    @classmethod
    def obter(cls, ctx):
        if cls._instancia is None:
            cls._instancia = cls(ctx)
        return cls._instancia

    def __init__(self, ctx):
        self.ctx = ctx
        self.tabela = ay_correcao.Tabela(ay_correcao.caminho_padrao())
        self.config = self.ler_config()
        self.recentes = []                 # correções automáticas desta sessão (mais recente primeiro)
        self.controladores = []            # controladores com o teclado registrado
        self.documentos = []               # documentos com o ouvinte de desfazer
        self.paineis = []                  # painéis Assistente AY abertos
        self.ouvintes_estado = []          # botões da faixa ligados a "Correção automática"
        self.pedidos = []                  # (quadro, pedido) pendentes até o painel abrir (ex.: "documento")
        self._hunspell = None
        self._lightproof = None
        self._lp_direto = None             # módulo de regras do Lightproof, chamado sem a ponte UNO
        self._lista_dic = None
        self._validas = {}                 # (palavra, língua, país) -> válida? (limpo ao mudar dicionários)
        self.ignorados = set()             # (regra, original) ignorados nesta sessão

    # ---------- configuração ----------
    def ler_config(self):
        padrao = {'CorrecaoAutomatica': True, 'Gramatica': True, 'Estilo': False, 'NaoCorrigir': ()}
        try:
            cfg = servico(self.ctx, 'com.sun.star.configuration.ConfigurationProvider')
            a = cfg.createInstanceWithArguments('com.sun.star.configuration.ConfigurationAccess', props(nodepath=NO_CONFIG))
            return {k: a.getPropertyValue(k) for k in padrao}
        except Exception:
            registrar('config: ' + traceback.format_exc())
            return padrao

    def gravar_config(self, **valores):
        cfg = servico(self.ctx, 'com.sun.star.configuration.ConfigurationProvider')
        a = cfg.createInstanceWithArguments('com.sun.star.configuration.ConfigurationUpdateAccess', props(nodepath=NO_CONFIG))
        for k, v in valores.items():
            if k == 'NaoCorrigir':
                uno.invoke(a, 'setPropertyValue', (k, uno.Any('[]string', tuple(v))))
            else:
                a.setPropertyValue(k, v)
        a.commitChanges()
        self.config = self.ler_config()
        if 'Gramatica' in valores or 'Estilo' in valores:
            self.aplicar_niveis()
        if 'CorrecaoAutomatica' in valores:
            self.notificar_estado()
        self.atualizar_paineis()

    def nao_corrigir(self, palavra):
        palavra = palavra.lower()
        if palavra and palavra not in self.config['NaoCorrigir']:
            self.gravar_config(NaoCorrigir=tuple(self.config['NaoCorrigir']) + (palavra,))

    def remover_nao_corrigir(self, palavra):
        self.gravar_config(NaoCorrigir=tuple(p for p in self.config['NaoCorrigir'] if p != palavra))

    def aplicar_niveis(self):
        """Liga/desliga as categorias do Lightproof pt-BR conforme Gramática e Estilo."""
        try:
            cfg = servico(self.ctx, 'com.sun.star.configuration.ConfigurationProvider')
            a = cfg.createInstanceWithArguments('com.sun.star.configuration.ConfigurationUpdateAccess', props(nodepath=NO_LIGHTPROOF))
            for c in CAT_GRAMATICA:
                a.setPropertyValue(c, '1' if self.config['Gramatica'] else '0')
            for c in CAT_ESTILO:
                a.setPropertyValue(c, '1' if self.config['Estilo'] else '0')
            a.commitChanges()
        except Exception:
            registrar('níveis do Lightproof: ' + traceback.format_exc())

    def notificar_estado(self):
        for ouvinte, url, fonte in list(self.ouvintes_estado):
            try:
                ev = uno.createUnoStruct('com.sun.star.frame.FeatureStateEvent')
                ev.Source, ev.FeatureURL, ev.IsEnabled, ev.Requery = fonte, url, True, False
                ev.State = uno.Any('boolean', bool(self.config['CorrecaoAutomatica']))
                uno.invoke(ouvinte, 'statusChanged', (ev,))
            except Exception:
                self.ouvintes_estado.remove((ouvinte, url, fonte))

    def painel_do_quadro(self, frame):
        return next((p for p in self.paineis if p.Frame == frame), None)

    def pedir(self, frame, pedido):
        self.pedidos = [(f, p) for f, p in self.pedidos if f != frame] + [(frame, pedido)]

    def retirar_pedido(self, frame):
        for i, (f, p) in enumerate(self.pedidos):
            if f == frame:
                del self.pedidos[i]
                return p
        return None

    def atualizar_paineis(self):
        for p in list(self.paineis):
            try:
                p.atualizar()
            except Exception:
                registrar('painel: ' + traceback.format_exc())

    # ---------- registro em documentos ----------
    def preparar_controlador(self, ctrl):
        if ctrl is None or any(c == ctrl for c in self.controladores):
            return
        if not ctrl.getModel().supportsService('com.sun.star.text.TextDocument'):
            return
        self.controladores.append(ctrl)
        ctrl.addKeyHandler(Teclado(self, ctrl))
        doc = ctrl.getModel()
        if not any(d == doc for d in self.documentos):
            self.documentos.append(doc)
            doc.getUndoManager().addUndoManagerListener(OuvinteDesfazer(self, doc))
        registrar(f'revisão preparada ({len(self.controladores)} vista(s))')

    def esquecer_documento(self, doc):
        self.controladores = [c for c in self.controladores if _vivo(c) and c.getModel() != doc]
        self.documentos = [d for d in self.documentos if d != doc]
        self.recentes = [r for r in self.recentes if r['doc'] != doc]

    # ---------- dicionários ----------
    @property
    def hunspell(self):
        if self._hunspell is None:
            # Serviço Hunspell direto: o despachante tem sobrecargas isValid(texto, short) que a ponte não distingue
            self._hunspell = servico(self.ctx, 'com.sun.star.linguistic2.SpellChecker')
        return self._hunspell

    def lista_dicionarios(self):
        if self._lista_dic is None:
            self._lista_dic = servico(self.ctx, 'com.sun.star.linguistic2.DictionaryList')
        return self._lista_dic

    def no_dicionario_do_usuario(self, palavra, locale):
        try:
            return self.lista_dicionarios().queryDictionaryEntry(palavra, locale, True, True) is not None
        except Exception:
            return False

    def palavra_valida(self, palavra, locale):
        chave = (palavra, locale.Language, locale.Country)
        r = self._validas.get(chave)
        if r is None:
            try:
                r = bool(uno.invoke(self.hunspell, 'isValid', (palavra, locale, vazio())))
            except Exception:
                r = True
            if not r:
                r = self.no_dicionario_do_usuario(palavra, locale)   # só para palavras que o dicionário não conhece
            if len(self._validas) > 200000:
                self._validas.clear()
            self._validas[chave] = r
        return r

    def esquecer_palavra(self, palavra):
        for k in [k for k in self._validas if k[0] == palavra]:
            self._validas.pop(k, None)

    def sugestoes(self, palavra, locale, limite=5):
        try:
            alt = uno.invoke(self.hunspell, 'spell', (palavra, locale, vazio()))
            return list(alt.getAlternatives())[:limite] if alt is not None else []
        except Exception:
            return []

    def _dicionario(self, nome, persistente):
        """Dicionário do usuário pelo nome; criado se ainda não existir (perfil novo)."""
        dl = self.lista_dicionarios()
        dic = dl.getDictionaryByName(nome)
        if dic is None:
            url = ''
            if persistente:
                subst = servico(self.ctx, 'com.sun.star.util.PathSubstitution')
                url = subst.substituteVariables('$(user)/wordbook/' + nome, True)
            dic = dl.createDictionary(nome, uno.createUnoStruct('com.sun.star.lang.Locale'),
                                      uno.Enum('com.sun.star.linguistic2.DictionaryType', 'POSITIVE'), url)
            dl.addDictionary(dic)
        if not dic.isActive():
            dic.setActive(True)
        return dic

    def ignorar_tudo(self, palavra):
        self._dicionario('IgnoreAllList', False).add(palavra, False, '')
        self.esquecer_palavra(palavra)

    def dicionario_pessoal(self):
        return self._dicionario('standard.dic', True)

    def adicionar_ao_dicionario(self, palavra):
        dic = self.dicionario_pessoal()
        dic.add(palavra, False, '')
        self.esquecer_palavra(palavra)
        if hasattr(dic, 'store'):
            try:
                dic.store()
            except Exception:
                pass

    def palavras_pessoais(self):
        dic = self.dicionario_pessoal()
        return sorted(e.getDictionaryWord() for e in dic.getEntries()) if dic is not None else []

    def remover_do_dicionario(self, palavra):
        dic = self.dicionario_pessoal()
        self.esquecer_palavra(palavra)
        if dic is not None:
            dic.remove(palavra)
            if hasattr(dic, 'store'):
                try:
                    dic.store()
                except Exception:
                    pass

    # ---------- correção automática ----------
    def palavra_terminada(self, ctrl):
        if ctrl.getModel().isReadonly():
            return
        vc = ctrl.getViewCursor()
        if not vc.isCollapsed():
            return
        texto = vc.getText()
        tc = texto.createTextCursorByRange(vc.getStart())
        if not tc.isEndOfWord():
            if DEPURAR:
                registrar('correção: cursor não está no fim de uma palavra')
            return
        tc.gotoStartOfWord(True)
        palavra = tc.getString()
        if not palavra or len(palavra) > 40:
            return
        inicio = texto.createTextCursorByRange(tc.getStart())
        inicio_frase = bool(inicio.isStartOfSentence())
        pc = texto.createTextCursorByRange(tc.getStart())
        pc.gotoStartOfParagraph(True)
        prefixo = pc.getString()
        loc = tc.CharLocale
        txt = ctrl.getModel().getURL().lower().endswith('.txt')
        protegido = (tc.ParaStyleName in ESTILOS_PROTEGIDOS or (tc.CharStyleName or '') in ESTILOS_PROTEGIDOS
                     or (tc.ParaStyleName in ESTILOS_PREFORMATADOS and not txt) or bool(tc.HyperLinkURL))
        correcao, motivo = ay_correcao.decidir(
            palavra, self.tabela, inicio_de_frase=inicio_frase, prefixo=prefixo,
            idioma_ptbr=(loc.Language == 'pt' and loc.Country in ('BR', '')),
            nao_corrigir=set(self.config['NaoCorrigir']), valida=lambda p: self.no_dicionario_do_usuario(p, loc),
            estilo_protegido=protegido)
        if DEPURAR:
            registrar(f'correção: {palavra!r} → {correcao!r} ({motivo}; início de frase={inicio_frase}; idioma={loc.Language}-{loc.Country})')
        if correcao is None:
            return
        doc = ctrl.getModel()
        # Âncora recolhida no início da palavra: a tecla digitada logo depois (espaço, pontuação) não a estende
        ancora = texto.createTextCursorByRange(tc.getStart())
        adiar(self.ctx, lambda: self._aplicar_correcao(doc, ancora, palavra, correcao))

    def _aplicar_correcao(self, doc, ancora, palavra, correcao):
        # A AutoCorreção do motor pode trocar a 1ª letra (maiúscula no início da frase): a âncora recolhida no
        # início da palavra é empurrada uma posição; por isso confere também uma posição à esquerda.
        atual, faixa = '', None
        for recuo in (0, 1):
            faixa = ancora.getText().createTextCursorByRange(ancora.getStart())
            if recuo and not faixa.goLeft(recuo, False):
                continue
            faixa.goRight(len(palavra), True)
            atual = faixa.getString()
            if atual.lower() == palavra.lower():
                break
        if atual.lower() != palavra.lower():
            if DEPURAR:
                registrar(f'correção: texto mudou antes de aplicar ({atual!r} ≠ {palavra!r})')
            return                                    # o texto mudou antes da correção: não mexe
        correcao = ay_correcao.ajustar_caixa(atual, correcao)
        um = doc.getUndoManager()
        um.enterUndoContext(f'{TITULO_AUTO}{atual} → {correcao}')
        try:
            faixa.setString(correcao)
        finally:
            um.leaveUndoContext()
        ancora = faixa.getText().createTextCursorByRange(faixa.getEnd())
        ancora.goLeft(len(correcao), True)
        self.recentes.insert(0, {'original': atual, 'correcao': correcao, 'faixa': ancora, 'doc': doc,
                                 'hora': time.strftime('%H:%M:%S')})
        del self.recentes[50:]
        self.atualizar_paineis()

    def reverter(self, item):
        """Desfaz uma correção automática da lista (ação própria de desfazer), se o texto ainda for a correção."""
        if item['faixa'].getString() != item['correcao']:
            return False
        um = item['doc'].getUndoManager()
        um.enterUndoContext(f'{TITULO_REVISAO}reverter {item["correcao"]} → {item["original"]}')
        try:
            item['faixa'].setString(item['original'])
        finally:
            um.leaveUndoContext()
        self.recentes.remove(item)
        self.atualizar_paineis()
        return True

    def oferecer_nao_corrigir(self, doc, original):
        try:
            ctrl = doc.getCurrentController()
            sp = uno.createUnoStruct('com.sun.star.beans.StringPair')
            sp.First, sp.Second = 'Não corrigir novamente', 'ayescreva:NaoCorrigir?palavra=' + quote(original)
            if ctrl.hasInfobar('ay-desfeita'):
                ctrl.removeInfobar('ay-desfeita')
            ctrl.appendInfobar('ay-desfeita', 'Correção desfeita:', f'“{original}” foi mantido como você escreveu.',
                               uno.getConstantByName('com.sun.star.frame.InfobarType.INFO'), (sp,), True)
        except Exception:
            registrar('infobar desfazer: ' + traceback.format_exc())

    # ---------- análise para o painel ----------
    @property
    def lightproof(self):
        if self._lightproof is None:
            self._lightproof = servico(self.ctx, LIGHTPROOF)
        return self._lightproof

    def preparar_lightproof(self, loc):
        """Inicializa o Lightproof uma vez pela ponte UNO (carrega opções e o módulo) e passa a chamar as regras
        direto, sem reler a configuração a cada parágrafo."""
        try:
            uno.invoke(self.lightproof, 'doProofreading', (0, 'Teste.', loc, 0, 6, vazio()))
            import lightproof_impl_pt_BR
            self._lp_direto = lightproof_impl_pt_BR if lightproof_impl_pt_BR.SMGR is not None else None
        except Exception:
            self._lp_direto = None
            registrar('lightproof direto indisponível; usando a ponte UNO: ' + traceback.format_exc()[-300:])

    def _proofread(self, texto, loc):
        if self._lp_direto is not None:
            return self._lp_direto.proofread(0, texto, loc, 0, len(texto), ())
        return uno.invoke(self.lightproof, 'doProofreading', (0, texto, loc, 0, len(texto), vazio())).aErrors

    def achados_paragrafo(self, texto, loc, ortografia=True, tempos=None, sugestoes=True):
        """Ocorrências de um parágrafo (posições relativas ao texto). Puro texto + serviços de língua."""
        achados = []
        t0 = time.perf_counter()
        if ortografia:
            for m in PALAVRA.finditer(texto):
                w = m.group(0)
                if len(w) > 1 and w.isupper():
                    continue                                   # siglas
                if not self.palavra_valida(w, loc):
                    achados.append({'inicio': m.start(), 'tamanho': len(w), 'nivel': 'ortografia', 'categoria': 'Ortografia',
                                    'original': w, 'sugestoes': self.sugestoes(w, loc) if sugestoes else None, 'regra': 'ortografia',
                                    'mensagem': 'Palavra não encontrada no dicionário pt-BR nem no dicionário pessoal.'})
        t1 = time.perf_counter()
        if self.config['Gramatica'] or self.config['Estilo']:
            try:
                for e in self._proofread(texto, loc):
                    comentario = (e.aFullComment or e.aShortComment or '').strip()
                    nivel = 'estilo' if ESTILO_LIGHTPROOF.search(comentario + ' ' + (e.aShortComment or '')) else 'gramatica'
                    if (nivel == 'gramatica' and self.config['Gramatica']) or (nivel == 'estilo' and self.config['Estilo']):
                        achados.append({'inicio': e.nErrorStart, 'tamanho': e.nErrorLength, 'nivel': nivel,
                                        'categoria': 'Gramática e pontuação' if nivel == 'gramatica' else 'Estilo',
                                        'original': texto[e.nErrorStart:e.nErrorStart + e.nErrorLength],
                                        'sugestoes': list(e.aSuggestions)[:5], 'regra': 'lightproof:' + (e.aRuleIdentifier or ''),
                                        'mensagem': comentario or 'Possível problema gramatical.'})
            except Exception:
                registrar('lightproof: ' + traceback.format_exc())
        t2 = time.perf_counter()
        if self.config['Estilo']:
            achados += ay_estilo.analisar(texto)
        if tempos is not None:
            t3 = time.perf_counter()
            for k, v in (('ortografia', t1 - t0), ('gramatica', t2 - t1), ('estilo', t3 - t2)):
                tempos[k] = tempos.get(k, 0.0) + v
        return [a for a in achados if (a['regra'], a['original']) not in self.ignorados]


def _vivo(obj):
    try:
        obj.getFrame()
        return True
    except Exception:
        return False


class Analise:
    """Análise de seleção ou documento sem travar a digitação.

    - Thread principal, em fatias de ~20 ms: lê o texto dos parágrafos e marca no documento os trechos achados.
    - Thread de trabalho: só recebe TEXTO e consulta os serviços de língua (Hunspell, Lightproof, regras de estilo),
      como o verificador gramatical do próprio motor faz na thread dele. Ela nunca toca o documento (chamadas UNO
      ao documento a partir de uma thread Python travaram o motor nos testes; ver docs/REVISAO-E-IA.md §4).
    - Cancelar interrompe as duas.
    """

    FATIA = 0.02
    FILA_MAXIMA = 200
    PAUSA = 0.003

    def __init__(self, revisao, doc, ctrl, somente_selecao, ao_progresso, ao_terminar, ortografia=True):
        self.revisao, self.doc, self.ctrl = revisao, doc, ctrl
        self.ao_progresso, self.ao_terminar = ao_progresso, ao_terminar
        self.ortografia = ortografia
        self.cancelado = False
        self.terminou = False
        self.achados = []
        self.feitos = 0
        self.lidos = 0
        self.nao_mapeados = 0
        self.outros_idiomas = 0
        self.inicio = time.time()
        self.tempos = {}
        self.pendentes = {}
        self.textos = queue.Queue()
        self.resultados = queue.Queue()
        self.leitura_concluida = False
        self.trabalho_concluido = False
        self._trava = threading.Lock()
        self._aguardando = False
        loc = uno.createUnoStruct('com.sun.star.lang.Locale')
        loc.Language, loc.Country = 'pt', 'BR'
        revisao.preparar_lightproof(loc)
        self.total = self._estimar() if not somente_selecao else 0
        self.paragrafos = self._selecao() if somente_selecao else self._documento()
        self.trabalhador = threading.Thread(target=self._trabalhar, name='ay-revisao', daemon=True)

    def _estimar(self):
        try:
            for p in self.doc.getDocumentProperties().DocumentStatistics:
                if p.Name == 'ParagraphCount':
                    return int(p.Value)
        except Exception:
            pass
        return 0

    def _documento(self):
        enum = self.doc.Text.createEnumeration()
        while enum.hasMoreElements():
            el = enum.nextElement()
            if el.supportsService('com.sun.star.text.Paragraph'):
                yield self.doc.Text, el
            elif el.supportsService('com.sun.star.text.TextTable'):
                for nome in el.getCellNames():
                    celula = el.getCellByName(nome)
                    e2 = celula.createEnumeration()
                    while e2.hasMoreElements():
                        p = e2.nextElement()
                        if p.supportsService('com.sun.star.text.Paragraph'):
                            yield celula, p

    def _selecao(self):
        sel = self.ctrl.getSelection()
        if sel is None or not hasattr(sel, 'getCount') or sel.getCount() == 0:
            return
        rng = sel.getByIndex(0)
        texto = rng.getText()
        c = texto.createTextCursorByRange(rng.getStart())
        c.gotoStartOfParagraph(False)
        while True:
            p = texto.createTextCursorByRange(c.getStart())
            p.gotoEndOfParagraph(True)
            yield texto, p
            if not c.gotoNextParagraph(False) or texto.compareRegionStarts(c, rng.getEnd()) < 0:
                return

    def iniciar(self):
        # Cada chamada UNO na thread principal solta e retoma o GIL; com a thread de trabalho ocupada, retomar pode
        # esperar o intervalo de troca do Python (5 ms). Durante a análise o intervalo cai para 1 ms.
        self._intervalo = sys.getswitchinterval()
        sys.setswitchinterval(0.001)
        self.trabalhador.start()
        adiar(self.revisao.ctx, self._fatia)

    def cancelar(self):
        self.cancelado = True
        self.textos.put(None)

    # ---------- thread de trabalho: só texto ----------
    def _trabalhar(self):
        while not self.cancelado:
            item = self.textos.get()
            if item is None:
                break
            idx, texto, lingua, pais = item
            loc = uno.createUnoStruct('com.sun.star.lang.Locale')
            loc.Language, loc.Country = lingua, pais
            try:
                achados = self.revisao.achados_paragrafo(texto, loc, self.ortografia, self.tempos, sugestoes=False)
            except Exception:
                registrar('análise (trabalho): ' + traceback.format_exc())
                achados = []
            self.resultados.put((idx, achados))
            self._acordar()
            time.sleep(self.PAUSA)                 # cede o GIL: a digitação (correção automática) usa Python também
        self.resultados.put(None)
        self._acordar()

    def _acordar(self):
        with self._trava:
            if not self._aguardando:
                return
            self._aguardando = False
        adiar(self.revisao.ctx, self._fatia)

    # ---------- thread principal: ler e marcar ----------
    def _fatia(self):
        if self.terminou:
            return
        if self.cancelado:
            self._fim(cancelado=True)
            return
        limite = time.time() + self.FATIA
        fez_algo = False
        try:
            while time.time() < limite and not self.leitura_concluida and self.textos.qsize() < self.FILA_MAXIMA:
                fez_algo = True
                try:
                    texto_obj, par = next(self.paragrafos)
                except StopIteration:
                    self.leitura_concluida = True
                    self.textos.put(None)
                    break
                texto = par.getString()
                if not texto.strip():
                    continue
                loc = par.CharLocale
                if loc.Language != 'pt':
                    self.outros_idiomas += 1
                    continue
                self.pendentes[self.lidos] = (texto_obj, par, texto)
                self.textos.put((self.lidos, texto, loc.Language, loc.Country))
                self.lidos += 1
            while time.time() < limite:
                try:
                    r = self.resultados.get_nowait()
                except queue.Empty:
                    break
                fez_algo = True
                if r is None:
                    self.trabalho_concluido = True
                    break
                idx, achados = r
                texto_obj, par, texto = self.pendentes.pop(idx)
                self._marcar(texto_obj, par, texto, achados)
                self.feitos += 1
        except Exception:
            registrar('análise: ' + traceback.format_exc())
            self.cancelado = True
            self._fim(cancelado=True)
            return
        if self.leitura_concluida and self.trabalho_concluido and not self.pendentes:
            if DEPURAR:
                registrar(f'análise: {self.feitos} parágrafos em {time.time() - self.inicio:.2f} s; tempos {self.tempos}')
            self._fim(cancelado=False)
            return
        self.ao_progresso(self)
        if not self.leitura_concluida or not self.resultados.empty():
            adiar(self.revisao.ctx, self._fatia)
            return
        with self._trava:                       # nada a fazer agora: a thread de trabalho acorda a principal
            if self.resultados.empty():
                self._aguardando = True
                return
        adiar(self.revisao.ctx, self._fatia)

    def _marcar(self, texto_obj, par, texto, achados):
        for a in achados:
            r = texto_obj.createTextCursorByRange(par.getStart())
            r.goRight(a['inicio'], False)
            r.goRight(a['tamanho'], True)
            if r.getString() != texto[a['inicio']:a['inicio'] + a['tamanho']]:
                self.nao_mapeados += 1          # campos/notas deslocam posições: não arrisca editar o lugar errado
                continue
            a['faixa'] = r
            a['locale'] = par.CharLocale
            self.achados.append(a)

    def _fim(self, cancelado):
        self.terminou = True
        self.textos.put(None)
        sys.setswitchinterval(getattr(self, '_intervalo', 0.005))
        self.ao_terminar(self, cancelado=cancelado)


def aplicar_sugestao(doc, achado, sugestao):
    """Troca o trecho da ocorrência pela sugestão, como uma ação de desfazer. Devolve False se o texto mudou."""
    if achado['faixa'].getString() != achado['original']:
        return False
    um = doc.getUndoManager()
    um.enterUndoContext(f'{TITULO_REVISAO}{achado["original"]} → {sugestao}')
    try:
        achado['faixa'].setString(sugestao)
    finally:
        um.leaveUndoContext()
    return True
