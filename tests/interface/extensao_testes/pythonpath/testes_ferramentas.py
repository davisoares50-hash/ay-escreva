# -*- coding: utf-8 -*-
"""Validação das ferramentas da faixa pelo efeito no documento (fase 12 de tests/interface/testar_faixa.ps1).

Para cada ferramenta: limpa o documento e prepara o que ela precisa (texto, tabela, imagem, forma, alterações
controladas...), clica no botão da faixa e, quando o botão abre um diálogo ou lista, escolhe uma opção pelos controles
do próprio diálogo (UITest); confere o efeito pela API do documento; desfaz (o mesmo comando do Ctrl+Z) e confere que
voltou ao estado anterior; refaz e confere o efeito de novo. Quando o efeito fica no arquivo, grava uma cópia em ODT e
outra em DOCX (storeToURL, sem mudar o documento aberto), reabre cada uma escondida e confere o efeito nela.

Clicar no botão não basta: sem a conferência do efeito, a ferramenta fica "acionada" com a limitação explicada.
Resultados em self.res['ferramentas'][<Aba › Função>] e, para a matriz, em self.res['funcoes'].
SPDX-License-Identifier: MPL-2.0
"""
import os
import tempfile
import time
import traceback

import uno
import unohelper
from com.sun.star.beans import PropertyValue
from com.sun.star.frame import XStatusListener


def _log(msg):
    try:
        with open(os.path.join(os.environ.get('TEMP', '.'), 'ay-testes-ui.log'), 'a', encoding='utf-8') as f:
            f.write(time.strftime('%H:%M:%S ') + 'ferramentas: ' + msg + chr(10))
    except Exception:
        pass


def _pv(nome, valor):
    p = PropertyValue()
    p.Name, p.Value = nome, valor
    return p


def _estado(obj):
    try:
        return {p.Name: p.Value for p in obj.getState()}
    except Exception:
        return {}


def _enum(tipo, valor):
    return uno.Enum(tipo, valor)


def _val(x):
    """Valor comparável: enums viram o nome, structs simples viram tupla."""
    return getattr(x, 'value', x)


class _Ouvinte(unohelper.Base, XStatusListener):
    def __init__(self):
        self.estado = None

    def statusChanged(self, ev):
        self.estado = ev.State if ev.IsEnabled else ('desabilitado', ev.State)

    def disposing(self, ev):
        pass


# Janelas não modais: fecham pelo mesmo comando que as abriu
NAO_MODAIS = {'.uno:SearchDialog', '.uno:InsertIndexesEntry', '.uno:AcceptTrackedChanges', '.uno:InsertAuthoritiesEntry',
              '.uno:SpellingAndGrammarDialog', '.uno:HyperlinkDialog', '.uno:Navigator', '.uno:FontworkGalleryFloater'}

ANCORA_DOCX = ('o DOCX não tem âncora "na página" nem "no parágrafo" como o ODT: ao reabrir, a imagem flutuante fica presa '
               'a um caractere, com a mesma posição na página')

FORMATOS = {'odt': ('writer8', '.odt'), 'docx': ('MS Word 2007 XML', '.docx')}


class Caso:
    """Uma ferramenta a validar.
    prep()            -> contexto (prepara o documento já limpo)
    ler(doc, ctx)     -> estado comparável (precisa funcionar no documento reaberto: localizar por nome/índice/texto)
    ok(antes, depois) -> o efeito esperado aconteceu
    acionar(b, ctx)   -> o que fazer depois do clique (escolher na lista, responder o diálogo); padrão: só o clique
    desfazer          -> conferir desfazer/refazer (None = não se aplica, ex.: só muda a exibição)
    formatos          -> formatos em que o efeito deve sobreviver a salvar, fechar e reabrir
    limite_formato    -> {formato: motivo} para perdas próprias do formato (registradas, sem esconder o resultado)
    """

    def __init__(self, aba, comando, oque, prep, ler, ok, acionar=None, desfazer=True, formatos=('odt', 'docx'),
                 limite_formato=None, espera=1.2, igual=None, funcao=None, tambem=(), prep_diag=(), registrar_como=None,
                 desfazer_real=False, ident=None):
        self.aba, self.comando, self.oque = aba, comando, oque
        self.prep_diag = prep_diag
        self.registrar_como = registrar_como
        self.desfazer_real = desfazer_real          # Ctrl+Z / Ctrl+Y do teclado de verdade em vez do comando
        self.ident = ident or f'{aba}:{comando}'
        self.funcao, self.tambem = funcao, tambem
        self.prep, self.ler, self.ok, self.acionar = prep, ler, ok, acionar
        self.desfazer, self.formatos, self.limite_formato = desfazer, formatos, limite_formato or {}
        self.espera = espera
        self.igual = igual or (lambda a, b: a == b)


class FerramentasMixin:
    # ---------- infraestrutura ----------------------------------------------------------------
    def _fechar_real(self, quando, comando=None):
        """Fecha o diálogo ou lista aberta. Janelas não modais (Localizar, Marcar entrada, Gerenciar alterações...)
        fecham pelo mesmo comando que as abriu. As demais, com Esc do teclado de verdade (o Esc simulado pelo motor pode
        derrubá-lo, RESULTADOS §9); só se isso falhar, pelo fechamento do teste de interface."""
        j, _t = self.janela_extra()
        if j is None:
            return
        if comando in NAO_MODAIS:
            self._despachar_sinc(comando)
            time.sleep(0.8)
            if self.janela_extra()[0] is None:
                return
        for _ in range(2):
            if not self._teclas_reais(0x1B):
                break
            time.sleep(0.8)
            if self.janela_extra()[0] is None:
                return
        self.fechar_janelas_extras(quando)

    def _despachar_sinc(self, cmd, args=()):
        d = self.smgr.createInstanceWithContext('com.sun.star.frame.DispatchHelper', self.ctx)
        self.no_principal(lambda: d.executeDispatch(self.frame, cmd, '', 0, tuple(args)))

    def _estado_comando(self, cmd):
        """Estado do comando (marcado/desmarcado, valor) como o motor informa à faixa. Roda na thread principal."""
        if True:
            t = self.smgr.createInstanceWithContext('com.sun.star.util.URLTransformer', self.ctx)
            u = uno.createUnoStruct('com.sun.star.util.URL')
            u.Complete = cmd
            _ok, u = t.parseStrict(u)
            disp = self.frame.queryDispatch(u, '', 0)
            if disp is None:
                return 'sem despachante'
            o = _Ouvinte()
            disp.addStatusListener(o, u)
            disp.removeStatusListener(o, u)
            return o.estado

    def _paragrafo_com(self, doc, trecho):
        e = doc.Text.createEnumeration()
        while e.hasMoreElements():
            p = e.nextElement()
            if p.supportsService('com.sun.star.text.Paragraph') and trecho in p.getString():
                return p
        return None

    def _achar(self, doc, trecho):
        b = doc.createSearchDescriptor()
        b.SearchString = trecho
        return doc.findFirst(b)

    def _contar_campos(self, doc, servico):
        n = 0
        e = doc.getTextFields().createEnumeration()
        while e.hasMoreElements():
            if e.nextElement().supportsService(servico):
                n += 1
        return n

    def _contar_texto(self, doc, trecho):
        return doc.Text.getString().count(trecho)

    def _redlines(self, doc):
        try:
            return doc.getRedlines().getCount()
        except Exception:
            e = doc.getRedlines().createEnumeration()
            n = 0
            while e.hasMoreElements():
                e.nextElement()
                n += 1
            return n

    def _formas(self, doc):
        """Formas de desenho (sem quadros, imagens e objetos, que o Writer também põe na página de desenho)."""
        dp = doc.getDrawPage()
        r = []
        for i in range(dp.getCount()):
            s = dp.getByIndex(i)
            if not (s.supportsService('com.sun.star.text.TextFrame') or s.supportsService('com.sun.star.text.TextGraphicObject')
                    or s.supportsService('com.sun.star.text.TextEmbeddedObject')):
                r.append(s)
        return r

    def _imagem(self, doc):
        g = doc.getGraphicObjects()
        return g.getByIndex(0) if g.getCount() else None

    def _tabela(self, doc):
        t = doc.getTextTables()
        return t.getByIndex(0) if t.getCount() else None

    # ---------- documento limpo para cada ferramenta ---------------------------------------------
    def _guardar_pagina(self):
        if getattr(self, '_pagina0', None) is not None:
            return

        def f():
            est = self.doc.getStyleFamilies().getByName('PageStyles').getByName('Standard')
            props = ('LeftMargin', 'RightMargin', 'TopMargin', 'BottomMargin', 'Width', 'Height', 'IsLandscape')
            return {p: est.getPropertyValue(p) for p in props}
        self._pagina0 = self.no_principal(f)

    def _limpar(self):
        self._guardar_pagina()

        def f():
            d = self.doc
            d.setPropertyValue('RecordChanges', False)
            for col in (d.getDocumentIndexes(), d.getTextSections()):
                for i in reversed(range(col.getCount())):
                    try:
                        col.getByIndex(i).dispose()
                    except Exception:
                        pass
            for col in (d.getTextFrames(), d.getGraphicObjects(), d.getEmbeddedObjects(), d.getTextTables()):
                for n in list(col.getElementNames()):
                    try:
                        col.getByName(n).dispose()
                    except Exception:
                        pass
            dp = d.getDrawPage()
            for i in reversed(range(dp.getCount())):
                try:
                    dp.remove(dp.getByIndex(i))
                except Exception:
                    pass
            e = d.getTextFields().createEnumeration()
            campos = []
            while e.hasMoreElements():
                campos.append(e.nextElement())
            for c in campos:
                try:
                    c.dispose()
                except Exception:
                    pass
            d.Text.setString('')
            if self._redlines(d):
                # alterações controladas que sobraram: aceitas pela API do motor (sem diálogo)
                self.smgr.createInstanceWithContext('com.sun.star.frame.DispatchHelper', self.ctx).executeDispatch(
                    self.frame, '.uno:AcceptAllTrackedChanges', '', 0, ())
                d.Text.setString('')
            cur = d.Text.createTextCursor()
            cur.gotoStart(False)
            cur.gotoEnd(True)
            try:
                cur.setAllPropertiesToDefault()
            except Exception:
                pass
            cur.setPropertyValue('ParaStyleName', 'Standard')
            est = d.getStyleFamilies().getByName('PageStyles').getByName('Standard')
            for k, v in self._pagina0.items():
                if est.getPropertyValue(k) != v:
                    est.setPropertyValue(k, v)
            ln = d.getLineNumberingProperties()
            if ln.IsOn:
                ln.IsOn = False
            d.getDocumentProperties().Title = ''
        self.no_principal(f)
        self.preparar_texto()
        try:
            self.no_principal(lambda: self.doc.getUndoManager().clear())
        except Exception:
            pass

    # ---------- preparações ---------------------------------------------------------------------
    def _sel(self, trecho):
        return self.selecionar_texto(trecho)

    def _cursor_em(self, trecho, fim=False):
        def f():
            r = self._achar(self.doc, trecho)
            vc = self.ctrl.getViewCursor()
            vc.gotoRange(r.getEnd() if fim else r.getStart(), False)
        self.no_principal(f)

    def _p_tabela(self, linhas=3, colunas=3, celula='A1', ate=None):
        def f():
            t = self.doc.createInstance('com.sun.star.text.TextTable')
            t.initialize(linhas, colunas)
            self.doc.Text.insertTextContent(self.doc.Text.getEnd(), t, False)
            for i, nome in enumerate(t.getCellNames()):
                t.getCellByName(nome).setString(f'c{i}')
            if ate:
                c = t.createCursorByCellName(celula)
                c.gotoCellByName(ate, True)
                self.ctrl.select(c)
            else:
                self.ctrl.getViewCursor().gotoRange(t.getCellByName(celula).getText().getStart(), False)
            return t.getName()
        nome = self.no_principal(f)
        self.esperar(0.8)
        return nome

    def _p_imagem(self, **props):
        def f():
            prov = self.smgr.createInstanceWithContext('com.sun.star.graphic.GraphicProvider', self.ctx)
            g = prov.queryGraphic((_pv('URL', uno.systemPathToFileUrl(self.spec['imagem'])),))
            img = self.doc.createInstance('com.sun.star.text.TextGraphicObject')
            img.Graphic = g
            img.setPropertyValue('AnchorType', _enum('com.sun.star.text.TextContentAnchorType', 'AT_PARAGRAPH'))
            tam = uno.createUnoStruct('com.sun.star.awt.Size')
            tam.Width, tam.Height = 3000, 3000
            img.setPropertyValue('Size', tam)
            img.setName('ImagemTeste')
            cur = self.doc.Text.createTextCursor()
            cur.gotoStart(False)
            self.doc.Text.insertTextContent(cur, img, False)
            for k, v in props.items():
                img.setPropertyValue(k, v)
            self.ctrl.select(img)
        self.no_principal(f)
        self.esperar(0.8)

    def _p_formas(self, n=1, selecionar=(0,), agrupar=False, cor=None):
        def f():
            formas = []
            for i in range(n):
                s = self.doc.createInstance('com.sun.star.drawing.RectangleShape')
                tam = uno.createUnoStruct('com.sun.star.awt.Size')
                tam.Width, tam.Height = 3000, 2000
                s.setPropertyValue('AnchorType', _enum('com.sun.star.text.TextContentAnchorType', 'AT_PARAGRAPH'))
                cur = self.doc.Text.createTextCursor()
                cur.gotoStart(False)
                self.doc.Text.insertTextContent(cur, s, False)
                s.Size = tam
                pos = uno.createUnoStruct('com.sun.star.awt.Point')
                pos.X, pos.Y = 1000 + i * 1500, 1000 + i * 800
                s.Position = pos
                s.Name = f'FormaTeste{i + 1}'
                if cor:
                    s.FillColor, s.LineColor = cor
                formas.append(s)
            col = self.smgr.createInstanceWithContext('com.sun.star.drawing.ShapeCollection', self.ctx)
            for i in selecionar:
                col.add(formas[i])
            if agrupar:
                g = self.doc.getDrawPage().group(col)
                self.ctrl.select(g)
            elif len(selecionar) == 1:
                self.ctrl.select(formas[selecionar[0]])
            else:
                self.ctrl.select(col)
        self.no_principal(f)
        self.esperar(0.8)

    def _p_alteracoes(self, cursor='inicio'):
        """Uma inserção ("inserção controlada ") no 2º parágrafo e uma exclusão ("gama ") no 1º, gravadas com o controle
        de alterações ligado; depois o controle é desligado."""
        def f():
            d = self.doc
            d.setPropertyValue('RecordChanges', True)
            p1 = self._achar(d, 'gama ')
            p1.setString('')
            p2 = self._achar(d, 'Segundo')
            d.Text.insertString(p2.getStart(), 'inserção controlada ', False)
            d.setPropertyValue('RecordChanges', False)
            vc = self.ctrl.getViewCursor()
            if cursor == 'inicio':
                vc.gotoStart(False)
            elif cursor == 'fim':
                vc.gotoEnd(False)
            elif cursor == 'insercao':
                self.ctrl.select(self._achar(d, 'inserção controlada'))
            elif cursor == 'dentro':                 # cursor dentro da inserção, como depois de clicar nela
                vc.gotoRange(self._achar(d, 'inserção controlada').getStart(), False)
                vc.goRight(3, False)
        self.no_principal(f)
        self.esperar(0.5)

    def _p_comentarios(self, n=2):
        def f():
            for trecho in ('alfa', 'gama', 'zeta')[:n]:
                c = self.doc.createInstance('com.sun.star.text.textfield.Annotation')
                c.Author = 'Teste'
                c.Content = f'Comentário sobre {trecho}'
                r = self._achar(self.doc, trecho)
                self.doc.Text.insertTextContent(r, c, True)
            self.ctrl.getViewCursor().gotoStart(False)
        self.no_principal(f)

    def _p_sumario(self, cursor_no_indice=False):
        def f():
            d = self.doc
            fim = d.Text.getEnd()
            d.Text.insertControlCharacter(fim, 0, False)
            cur = d.Text.createTextCursorByRange(d.Text.getEnd())
            cur.setString('Capítulo de teste do sumário')
            cur.setPropertyValue('ParaStyleName', 'Heading 1')
            idx = d.createInstance('com.sun.star.text.ContentIndex')
            idx.CreateFromOutline = True
            ini = d.Text.createTextCursor()
            ini.gotoStart(False)
            d.Text.insertTextContent(ini, idx, False)
            idx.setPropertyValue('Title', 'Sumário de teste')
            vc = self.ctrl.getViewCursor()
            if cursor_no_indice:
                vc.gotoRange(idx.getAnchor().getStart(), False)
            else:
                vc.gotoEnd(False)
        self.no_principal(f)

    # ---------- leituras (funcionam no documento aberto e no reaberto) -------------------------------
    def _l_texto(self, trecho):
        return lambda d, c: self._contar_texto(d, trecho)

    def _l_char(self, trecho, prop):
        return lambda d, c: _val(self._achar(d, trecho).getPropertyValue(prop))

    def _l_para(self, trecho, *props):
        return lambda d, c: tuple(_val(self._paragrafo_com(d, trecho).getPropertyValue(p)) for p in props)

    def _l_img(self, *props):
        return lambda d, c: tuple(_val(self._imagem(d).getPropertyValue(p)) for p in props) if self._imagem(d) else None

    def _l_tab(self):
        def f(d, c):
            t = self._tabela(d)
            if t is None:
                return None
            return (t.getRows().getCount(), t.getColumns().getCount(), len(t.getCellNames()))
        return f

    # ---------- execução de um caso ---------------------------------------------------------------
    def _arquivo_tmp(self, ext):
        pasta = os.path.join(os.path.dirname(self.saida), 'trabalho', 'ferramentas')
        os.makedirs(pasta, exist_ok=True)
        return os.path.join(pasta, f'caso-{int(time.time() * 1000)}{ext}')

    def _reaberto(self, fmt, ler, ctx):
        filtro, ext = FORMATOS[fmt]
        caminho = self._arquivo_tmp(ext)
        url = uno.systemPathToFileUrl(caminho)
        self.no_principal(lambda: self.doc.storeToURL(url, (_pv('FilterName', filtro), _pv('Overwrite', True))))

        def abrir():
            d = self.desktop.loadComponentFromURL(url, '_blank', 0, (_pv('Hidden', True), _pv('ReadOnly', True)))
            try:
                return ler(d, ctx)
            finally:
                d.close(True)
        try:
            return self.no_principal(abrir, 90)
        finally:
            try:
                os.remove(caminho)
            except OSError:
                pass

    def validar(self, caso):
        b = next((x for x in self.mapa['botoes'] if x['comando'] == caso.comando and x['aba'] == caso.aba
                  and (caso.funcao is None or x['funcao'] == caso.funcao)), None)
        if b is None:
            _log(f'sem botão: {caso.aba} {caso.comando}')
            return
        ch = caso.registrar_como or self.chave(b)
        r = {'comando': caso.comando, 'oque': caso.oque, 'efeito': False, 'desfazer': None, 'refazer': None}
        self.res.setdefault('ferramentas', {})[ch] = r
        try:
            self._limpar()
            ctx = caso.prep()
            antes = self.no_principal(lambda: caso.ler(self.doc, ctx))
            if caso.prep_diag:
                r['estados'] = {c: repr(self.no_principal(lambda c=c: self._estado_comando(c))) for c in caso.prep_diag}
            self.aba_atual = None
            disparado = self.clicar(b)
            r['disparado'] = disparado
            if caso.acionar:
                caso.acionar(b, ctx)
            self.esperar(caso.espera)
            depois = self.no_principal(lambda: caso.ler(self.doc, ctx))
            r['antes'], r['depois'] = repr(antes)[:120], repr(depois)[:120]
            r['efeito'] = bool(caso.ok(antes, depois))
            if r['efeito'] and caso.desfazer:
                self._fechar_real('antes de desfazer', caso.comando)
                try:
                    r['pilha_desfazer'] = list(self.no_principal(lambda: self.doc.getUndoManager().getAllUndoActionTitles()))[:4]
                except Exception:
                    pass
                if caso.desfazer_real:
                    r['ativo_antes_de_desfazer'] = self.no_principal(self._objeto_ativo)
                    self._teclas_reais(0x11, 0x5A)
                else:
                    self._despachar_sinc('.uno:Undo')
                self.esperar(0.5)
                v = self.no_principal(lambda: caso.ler(self.doc, ctx))
                r['desfazer'] = bool(caso.igual(antes, v))
                r['depois_desfazer'] = repr(v)[:120]
                if caso.desfazer_real:
                    self._teclas_reais(0x11, 0x59)
                else:
                    self._despachar_sinc('.uno:Redo')
                self.esperar(0.5)
                v = self.no_principal(lambda: caso.ler(self.doc, ctx))
                r['refazer'] = bool(caso.ok(antes, v))
                r['depois_refazer'] = repr(v)[:120]
            if r['efeito'] and caso.formatos:
                for fmt in caso.formatos:
                    try:
                        v = self._reaberto(fmt, caso.ler, ctx)
                        r[fmt] = bool(caso.ok(antes, v))
                        r[fmt + '_valor'] = repr(v)[:120]
                    except Exception:
                        r[fmt] = False
                        r[fmt + '_valor'] = 'erro: ' + traceback.format_exc()[-300:]
                    if not r[fmt] and fmt in caso.limite_formato:
                        r[fmt + '_limite'] = caso.limite_formato[fmt]
        except Exception:
            r['erro'] = traceback.format_exc()[-900:]
            _log(f'{ch}: erro ' + r['erro'][-300:])
        finally:
            try:
                self._fechar_real('depois da ferramenta', caso.comando)
                self.fechar_outras_janelas()
            except Exception:
                pass
        self._registrar_ferramenta(b, ch, caso, r)

    def _registrar_ferramenta(self, b, ch, caso, r):
        partes = [f'{caso.oque}: {r.get("antes", "?")} → {r.get("depois", "?")}' if r['efeito'] else f'efeito NÃO conferido ({caso.oque}; {r.get("antes", "?")} → {r.get("depois", "?")})']
        if caso.desfazer and r['efeito']:
            partes.append('desfazer ' + ('ok' if r['desfazer'] else 'FALHOU') + ', refazer ' + ('ok' if r['refazer'] else 'FALHOU'))
        elif not caso.desfazer:
            partes.append('desfazer não se aplica (só muda a exibição ou a seleção)')
        for fmt in caso.formatos or ():
            if fmt in r:
                if r[fmt]:
                    partes.append(f'{fmt.upper()}: mantido ao salvar e reabrir')
                else:
                    partes.append(f'{fmt.upper()}: NÃO mantido ({r.get(fmt + "_limite") or r.get(fmt + "_valor", "")})')
        if not caso.formatos:
            partes.append('não fica no arquivo')
        if r.get('erro'):
            partes.append('erro: ' + r['erro'].strip().splitlines()[-1][:160])
        r['resumo'] = '; '.join(partes)
        valido = (r['efeito'] and r['disparado'] == b['comando'] and r['desfazer'] is not False and r['refazer'] is not False
                  and r.get('odt', True) is not False)
        r['validado'] = bool(valido)
        self.res['efeitos'].append({'funcao': f'{ch} (efeito real)', 'ok': bool(valido) or bool(r.get('docx') is False and r['efeito'] and r.get('docx_limite')),
                                    'detalhe': r['resumo']})
        if r.get('disparado') == b['comando']:
            self.registrar(ch, 'acionado', 'clique na faixa disparou ' + b['comando'])
        if valido:
            self.registrar(ch, 'validado', r['resumo'])
        for extra in caso.tambem:            # função oferecida pelo mesmo botão (ex.: Bordas de página)
            self.res['ferramentas'][extra] = dict(r, resumo=f'pelo botão {b["funcao"]}: ' + r['resumo'])
            if valido:
                self.registrar(extra, 'validado', f'pelo botão {b["funcao"]}: ' + r['resumo'])
        _log(f'{"OK " if valido else "FALHA "}{ch}: {r["resumo"]}')

    # ---------- casos ---------------------------------------------------------------------------
    def casos_ferramentas(self):
        T = 'com.sun.star.text.textfield.'
        dif = lambda a, d: d is not None and d != a
        casos = [
            # Página Inicial: área de transferência, cor, espaçamento, seleção, estilos
            Caso('inicio', '.uno:Cut', 'ocorrências de "gama"', lambda: self._sel('gama'), self._l_texto('gama'),
                 lambda a, d: d == a - 1),
            # Copiar: o que o botão pôs na área de transferência é colado no fim do texto (Colar pelo comando) e contado;
            # não depende de ler a área de transferência do Windows (indisponível com a tela bloqueada)
            Caso('inicio', '.uno:Copy', 'ocorrências de "beta" depois de copiar pela faixa e colar no fim', lambda: self._sel('beta'),
                 self._l_texto('beta'), lambda a, d: d == a + 1, desfazer=None, formatos=(), acionar=self._colar_no_fim),
            Caso('inicio', '.uno:Paste', 'ocorrências de "zeta" (colado no fim do 2º parágrafo)', self._p_colar,
                 self._l_texto('zeta'), lambda a, d: d == a + 1),
            Caso('inicio', '.uno:Color', 'cor da fonte de "teta"', lambda: self._sel('teta'), self._l_char('teta', 'CharColor'),
                 lambda a, d: d not in (a, -1)),
            Caso('inicio', '.uno:ParaspaceIncrease', 'espaço antes+depois do parágrafo', lambda: self._sel('alfa'),
                 self._l_para('alfa', 'ParaTopMargin', 'ParaBottomMargin'), lambda a, d: sum(d) > sum(a)),
            Caso('inicio', '.uno:ParaspaceDecrease', 'espaço antes+depois do parágrafo', self._p_espaco,
                 self._l_para('alfa', 'ParaTopMargin', 'ParaBottomMargin'), lambda a, d: sum(d) < sum(a)),
            Caso('inicio', '.uno:SelectAll', 'tamanho da seleção', lambda: self._cursor_em('alfa'),
                 lambda d, c: (len(self._texto_selecionado()), len(d.Text.getString())), lambda a, d: d[0] >= d[1] - 2 and a[0] < d[0],
                 desfazer=None, formatos=()),
            Caso('inicio', '.uno:DesignerDialog', 'painel Estilos visível na barra lateral', lambda: None,
                 lambda d, c: self._deck_ativo('StyleListDeck'), lambda a, d: d is True and a is not True, desfazer=None,
                 formatos=(), acionar=None),
            # Inserir
            Caso('inserir', '.uno:InsertDateField', 'campos de data', lambda: self._cursor_em('mi', fim=True),
                 lambda d, c: self._contar_campos(d, T + 'DateTime'), lambda a, d: d == a + 1),
            # gráfico: sai da edição do gráfico antes de desfazer (com o gráfico em edição, o "desfazer" iria para o gráfico)
            Caso('inserir', '.uno:InsertObjectChart', 'gráficos na página (objetos incorporados no texto)', lambda: self._cursor_em('mi', fim=True),
                 self._l_objetos_na_pagina, lambda a, d: d == a + 1, acionar=self._sair_do_objeto, espera=2.5),
            # Layout: quebra automática, ordem, âncora e alinhamento de objetos (imagem selecionada)
            Caso('layout', '.uno:WrapOff', 'quebra do texto em volta da imagem', lambda: self._p_imagem(TextWrap=_enum('com.sun.star.text.WrapTextMode', 'PARALLEL')),
                 self._l_img('TextWrap'), lambda a, d: d == ('NONE',)),
            Caso('layout', '.uno:WrapOn', 'quebra do texto em volta da imagem', lambda: self._p_imagem(TextWrap=_enum('com.sun.star.text.WrapTextMode', 'NONE')),
                 self._l_img('TextWrap'), lambda a, d: d == ('PARALLEL',)),
            Caso('layout', '.uno:WrapIdeal', 'quebra do texto em volta da imagem', lambda: self._p_imagem(TextWrap=_enum('com.sun.star.text.WrapTextMode', 'NONE')),
                 self._l_img('TextWrap'), lambda a, d: d == ('DYNAMIC',)),
            Caso('layout', '.uno:WrapThrough', 'quebra do texto em volta da imagem', lambda: self._p_imagem(TextWrap=_enum('com.sun.star.text.WrapTextMode', 'NONE')),
                 self._l_img('TextWrap'), lambda a, d: d == ('THROUGH',)),
            Caso('layout', '.uno:BringToFront', 'ordem: a forma 1 fica na frente da 2', lambda: self._p_formas(2, (0,)),
                 self._l_ordem, lambda a, d: d is not None and d[0] > d[1]),
            Caso('layout', '.uno:SendToBack', 'ordem: a forma 2 fica atrás da 1', lambda: self._p_formas(2, (1,)),
                 self._l_ordem, lambda a, d: d is not None and d[1] < d[0]),
            Caso('layout', '.uno:SetAnchorToPage', 'âncora da imagem', lambda: self._p_imagem(),
                 self._l_img('AnchorType'), lambda a, d: d == ('AT_PAGE',), limite_formato={'docx': ANCORA_DOCX}),
            Caso('layout', '.uno:SetAnchorToPara', 'âncora da imagem', lambda: self._p_imagem(AnchorType=_enum('com.sun.star.text.TextContentAnchorType', 'AT_CHARACTER')),
                 self._l_img('AnchorType'), lambda a, d: d == ('AT_PARAGRAPH',), limite_formato={'docx': ANCORA_DOCX}),
            # .uno:SetAnchorToChar é "como caractere" (a imagem vira um caractere da linha); "no caractere" é SetAnchorAtChar
            Caso('layout', '.uno:SetAnchorToChar', 'âncora da imagem (como caractere)', lambda: self._p_imagem(),
                 self._l_img('AnchorType'), lambda a, d: d == ('AS_CHARACTER',)),
            Caso('layout', '.uno:ObjectAlignLeft', 'alinhamento horizontal da imagem', lambda: self._p_imagem(HoriOrient=2),
                 self._l_img('HoriOrient'), lambda a, d: d == (3,)),
            # Referências: atualizar sumário, índices e campos
            Caso('referencias', '.uno:UpdateCurIndex', 'título novo aparece no sumário', lambda: self._p_sumario(True),
                 self._l_sumario, lambda a, d: d is True and a is False),
            Caso('referencias', '.uno:UpdateAllIndexes', 'título novo aparece no sumário', lambda: self._p_sumario(False),
                 self._l_sumario, lambda a, d: d is True and a is False),
            Caso('referencias', '.uno:UpdateFields', 'campo de hora (com segundos) atualizado', self._p_campo_hora,
                 self._l_campo_hora, lambda a, d: bool(a) and bool(d) and d != a, desfazer=None, formatos=(), espera=1.5),
            # Revisão: comentários e controle de alterações
            Caso('revisao', '.uno:DeleteAllNotes', 'comentários', self._p_comentarios,
                 lambda d, c: self._contar_campos(d, T + 'Annotation'), lambda a, d: a == 2 and d == 0),
            Caso('revisao', '.uno:AcceptTrackedChange', 'alterações pendentes e texto inserido', lambda: self._p_alteracoes('dentro'),
                 self._l_alteracoes, lambda a, d: d[0] == a[0] - 1 and d[1] and a[1]),
            Caso('revisao', '.uno:RejectTrackedChange', 'alterações pendentes e texto inserido', lambda: self._p_alteracoes('dentro'),
                 self._l_alteracoes, lambda a, d: d[0] == a[0] - 1 and not d[1]),
            Caso('revisao', '.uno:AcceptAllTrackedChanges', 'alterações pendentes, inserção e exclusão', lambda: self._p_alteracoes(),
                 self._l_alteracoes, lambda a, d: a[0] == 2 and d[0] == 0 and d[1] and not d[2]),
            Caso('revisao', '.uno:RejectAllTrackedChanges', 'alterações pendentes, inserção e exclusão', lambda: self._p_alteracoes(),
                 self._l_alteracoes, lambda a, d: a[0] == 2 and d[0] == 0 and not d[1] and d[2]),
            Caso('revisao', '.uno:NextTrackedChange', 'trecho selecionado', lambda: self._p_alteracoes('inicio'),
                 lambda d, c: self._texto_selecionado(), lambda a, d: d.strip() in ('gama', 'inserção controlada'), desfazer=None, formatos=()),
            Caso('revisao', '.uno:PreviousTrackedChange', 'trecho selecionado', lambda: self._p_alteracoes('fim'),
                 lambda d, c: self._texto_selecionado(), lambda a, d: d.strip() in ('gama', 'inserção controlada'), desfazer=None, formatos=()),
            Caso('revisao', '.uno:ShowTrackedChanges', 'mostrar alterações (estado do comando)', lambda: self._p_alteracoes(),
                 lambda d, c: self._estado_comando('.uno:ShowTrackedChanges'), dif, desfazer=None, formatos=(), acionar=self._repetir_clique),
            Caso('revisao', '.uno:ShowAnnotations', 'mostrar comentários (estado do comando)', lambda: self._p_comentarios(1),
                 lambda d, c: self._estado_comando('.uno:ShowAnnotations'), dif, desfazer=None, formatos=(), acionar=self._repetir_clique),
            Caso('revisao', '.uno:SpellOnline', 'revisão automática (estado do comando)', lambda: None,
                 lambda d, c: self._estado_comando('.uno:SpellOnline'), dif, desfazer=None, formatos=(), acionar=self._repetir_clique),
            # Tabela (aba contextual)
            Caso('tabela', '.uno:InsertRowsBefore', 'linhas, colunas e células', self._p_tabela, self._l_tab(),
                 lambda a, d: d[0] == a[0] + 1),
            Caso('tabela', '.uno:InsertColumnsBefore', 'linhas, colunas e células', self._p_tabela, self._l_tab(),
                 lambda a, d: d[1] == a[1] + 1),
            Caso('tabela', '.uno:InsertColumnsAfter', 'linhas, colunas e células', self._p_tabela, self._l_tab(),
                 lambda a, d: d[1] == a[1] + 1),
            Caso('tabela', '.uno:DeleteRows', 'linhas, colunas e células', self._p_tabela, self._l_tab(),
                 lambda a, d: d[0] == a[0] - 1),
            Caso('tabela', '.uno:DeleteColumns', 'linhas, colunas e células', self._p_tabela, self._l_tab(),
                 lambda a, d: d[1] == a[1] - 1),
            Caso('tabela', '.uno:DeleteTable', 'tabelas no documento', self._p_tabela,
                 lambda d, c: d.getTextTables().getCount(), lambda a, d: a == 1 and d == 0),
            Caso('tabela', '.uno:MergeCells', 'linhas, colunas e células (A1 e B1 selecionadas)', lambda: self._p_tabela(ate='B1'),
                 self._l_tab(), lambda a, d: d[2] == a[2] - 1),
            Caso('tabela', '.uno:SetOptimalColumnWidth', 'separadores das colunas (1ª coluna com texto longo)', self._p_tabela_larguras,
                 self._l_colunas, lambda a, d: d is not None and a is not None and abs(d[0] - a[0]) > 300,
                 igual=lambda a, v: v is not None and all(abs(x - y) <= 5 for x, y in zip(a, v)),
                 limite_formato={}),
            Caso('tabela', '.uno:TableCellBackgroundColor', 'cor de fundo da célula A1', self._p_tabela,
                 lambda d, c: self._tabela(d).getCellByName('A1').BackColor if self._tabela(d) else None, lambda a, d: d not in (a, -1, None)),
            Caso('tabela', '.uno:SelectTable', 'células selecionadas', self._p_tabela,
                 lambda d, c: self._celulas_selecionadas(), lambda a, d: d == 9, desfazer=None, formatos=()),
            # Imagem (aba contextual)
            Caso('imagem', '.uno:RotateLeft', 'rotação da imagem (graus × 10)', self._p_imagem, self._l_rotacao,
                 lambda a, d: d == 900),
            Caso('imagem', '.uno:RotateRight', 'rotação da imagem (graus × 10)', self._p_imagem, self._l_rotacao,
                 lambda a, d: d == 2700),
            Caso('imagem', '.uno:FlipVertical', 'espelhamento vertical', self._p_imagem, self._l_img('VertMirrored'),
                 lambda a, d: d == (True,)),
            Caso('imagem', '.uno:FlipHorizontal', 'espelhamento horizontal (páginas pares e ímpares)', self._p_imagem,
                 self._l_img('HoriMirroredOnEvenPages', 'HoriMirroredOnOddPages'), lambda a, d: d == (True, True)),
            # Forma (aba contextual) e Desenhar
            Caso('forma', '.uno:FillColor', 'cor de preenchimento da forma (branca antes)', lambda: self._p_formas(1, cor=(0xFFFFFF, 0)),
                 lambda d, c: self._forma(d, 1, 'FillColor'), dif),
            Caso('forma', '.uno:FormatGroup', 'formas soltas na página', lambda: self._p_formas(2, (0, 1)),
                 lambda d, c: len(self._formas(d)), lambda a, d: a == 2 and d == 1),
            Caso('forma', '.uno:FormatUngroup', 'formas soltas na página', lambda: self._p_formas(2, (0, 1), agrupar=True),
                 lambda d, c: len(self._formas(d)), lambda a, d: a == 1 and d == 2),
            Caso('desenhar', '.uno:XLineColor', 'cor da linha da forma (preta antes)', lambda: self._p_formas(1, cor=(0xFFFFFF, 0)),
                 lambda d, c: self._forma(d, 1, 'LineColor'), dif),
            Caso('desenhar', '.uno:FormatGroup', 'formas soltas na página', lambda: self._p_formas(2, (0, 1)),
                 lambda d, c: len(self._formas(d)), lambda a, d: a == 2 and d == 1),
            Caso('desenhar', '.uno:Delete', 'formas na página', lambda: self._p_formas(2, (1,)),
                 lambda d, c: len(self._formas(d)), lambda a, d: a == 2 and d == 1),
        ]
        D, ab, dg, cl, es, it = self._dialogo, self._aba, self._digitar, self._clicar, self._d_escolher, self._item
        mm = lambda v: lambda a, d: d is not None and abs(d - v) <= 60          # medidas em 1/100 mm
        casos += [
            # Página Inicial
            Caso('inicio', '.uno:SearchDialog', 'Substituir tudo: "gama" → "GAMA-TROCADA"', lambda: None,
                 self._l_texto('GAMA-TROCADA'), lambda a, d: a == 0 and d == 1,
                 acionar=D(dg('searchterm', 'gama'), dg('replaceterm', 'GAMA-TROCADA'), cl('replaceall'), botao=None, fechar='close')),
            Caso('inicio', '.uno:FontDialog', 'tamanho da fonte de "alfa" pelo diálogo Caractere (20 pt)', lambda: self._sel('alfa'),
                 self._l_char('alfa', 'CharHeight'), lambda a, d: d == 20.0, acionar=D(ab(0), dg('cbWestSize', '20'))),
            Caso('inicio', '.uno:ParagraphDialog', 'recuo à esquerda pelo diálogo Parágrafo (2 cm)', lambda: self._sel('alfa'),
                 lambda d, c: self._paragrafo_com(d, 'alfa').ParaLeftMargin, mm(2000), acionar=D(ab(0), dg('spinED_LEFTINDENT', '2'))),
            Caso('layout', '.uno:ParagraphDialog', 'recuo à esquerda pelo diálogo Parágrafo (2 cm)', lambda: self._sel('alfa'),
                 lambda d, c: self._paragrafo_com(d, 'alfa').ParaLeftMargin, mm(2000), acionar=D(ab(0), dg('spinED_LEFTINDENT', '2'))),
            Caso('inicio', '.uno:SetOutline', 'numeração de tópicos no parágrafo', lambda: self._sel('alfa'),
                 lambda d, c: bool(self._paragrafo_com(d, 'alfa').NumberingIsNumber), lambda a, d: d is True and a is False,
                 acionar=D(es('valueset', 1, 'CHOOSE'))),
            Caso('inicio', '.uno:LineSpacing', 'espaçamento entre linhas (duplo)', lambda: self._sel('alfa'),
                 lambda d, c: self._paragrafo_com(d, 'alfa').ParaLineSpacing.Height, lambda a, d: d == 200 and a != 200,
                 acionar=self._lista_espacamento),
            # Inserir
            Caso('inserir', '.uno:InsertSection', 'seções no documento', lambda: self._cursor_em('faixa.', fim=True),
                 lambda d, c: d.getTextSections().getCount(), lambda a, d: d == a + 1, acionar=D(),
                 limite_formato={'docx': 'o DOCX não tem seções de texto como as do ODT: viram quebras de seção'}),
            Caso('inserir', '.uno:InsertFrame', 'quadros no documento (no DOCX, viram caixas de texto)', lambda: self._cursor_em('faixa.', fim=True),
                 self._l_quadros, lambda a, d: d == a + 1, acionar=D()),
            Caso('inserir', '.uno:TitlePageDialog', 'páginas do documento (página de rosto nova)', lambda: None,
                 lambda d, c: d.getCurrentController().PageCount, lambda a, d: d == a + 1, acionar=D(cl('RB_INSERT_NEW_PAGES'))),
            # Design e Layout: página
            Caso('design', '.uno:PageDialog', 'cor de fundo da página (estilo de página)', lambda: None,
                 lambda d, c: self._l_pagina_fundo_borda(d, c)[0], lambda a, d: d != 'NONE' and a == 'NONE',
                 acionar=D(ab(2), cl('btncolor')), funcao='Cor e bordas da página'),
            Caso('design', '.uno:PageDialog', 'borda da página (estilo de página)', lambda: None,
                 lambda d, c: self._l_pagina_fundo_borda(d, c)[1], lambda a, d: d > 0 and a == 0,
                 acionar=D(ab(6), es('presets', 1, 'CHOOSE')), funcao='Cor e bordas da página',
                 registrar_como='Design › Bordas de página', ident='design:.uno:PageDialog:bordas'),
            Caso('layout', '.uno:PageDialog', 'margem esquerda da página (3 cm)', lambda: None,
                 self._l_margem, mm(3000), acionar=D(ab(1), dg('spinMargLeft', '3'))),
            Caso('layout', '.uno:LineNumberingDialog', 'numeração de linhas ligada', lambda: None,
                 lambda d, c: bool(d.getLineNumberingProperties().IsOn), lambda a, d: d is True and a is False,
                 acionar=D(cl('shownumbering')), desfazer=None),
            Caso('design', '.uno:Watermark', 'marca-d\'água "RASCUNHO"', lambda: None,
                 self._l_marca_dagua, lambda a, d: d == 'RASCUNHO', acionar=D(dg('TextInput', 'RASCUNHO'))),
            # Referências
            # com uma nota no documento (sem notas, o DOCX não guarda a configuração); no DOCX, "a, b, c" do Word volta como
            # "a … z, aa" (CHARS_LOWER_LETTER_N), que é o mesmo comportamento: por isso o critério é "deixou de ser 1, 2, 3"
            Caso('referencias', '.uno:FootnoteDialog', 'tipo de numeração das notas de rodapé', self._p_nota,
                 lambda d, c: d.getFootnoteSettings().NumberingType, lambda a, d: d is not None and d != a,
                 acionar=D(ab(0), es('numberinglb', 2)), desfazer=None),
            Caso('referencias', '.uno:InsertIndexesEntry', 'entradas de índice marcadas', lambda: self._sel('gama'),
                 self._l_marcas_indice, lambda a, d: d == a + 1, acionar=D(cl('insert'), botao=None, fechar='close')),
            # Revisão
            Caso('revisao', '.uno:ProtectTraceChangeMode', 'controle de alterações protegido por senha (senha de teste)', lambda: None,
                 lambda d, c: len(d.getPropertyValue('RedlineProtectionKey')) > 0, lambda a, d: d is True and a is False,
                 acionar=D(dg('pass1ed', 'teste-ay-123'), dg('confirm1ed', 'teste-ay-123')), desfazer=None),
            Caso('revisao', '.uno:AcceptTrackedChanges', 'alterações pendentes (Aceitar todas no diálogo)', lambda: self._p_alteracoes(),
                 self._l_alteracoes, lambda a, d: a[0] == 2 and d[0] == 0, acionar=D(cl('acceptall'), botao=None, fechar='close')),
            # Tabela
            Caso('tabela', '.uno:SplitCell', 'linhas, colunas e células (A1 dividida em 2)', self._p_tabela, self._l_tab(),
                 lambda a, d: d[2] == a[2] + 1, acionar=D()),
            Caso('tabela', '.uno:AutoFormat', 'aparência da tabela (cor da célula A1)', lambda: self._p_tabela(ate='C3'),
                 lambda d, c: self._tabela(d).getCellByName('A1').BackColor if self._tabela(d) else None,
                 lambda a, d: d is not None and d != a, acionar=D(it('formatlb', 2))),
            Caso('tabela', '.uno:SortDialog', 'ordem da 1ª coluna (c, b, a → a, b, c)', self._p_tabela_ordenar,
                 self._l_coluna_a, lambda a, d: d == ('a', 'b', 'c') and a == ('c', 'b', 'a'), acionar=D()),
            Caso('tabela', '.uno:TableDialog', 'alinhamento da tabela (centralizada)', self._p_tabela,
                 lambda d, c: self._tabela(d).HoriOrient if self._tabela(d) else None, lambda a, d: d == 2 and a != 2,
                 acionar=D(ab(0), cl('center'))),
            # Imagem
            Caso('imagem', '.uno:CompressGraphic', 'formato da imagem depois de comprimir em JPEG', self._p_imagem,
                 self._l_tipo_imagem, lambda a, d: d == 'image/jpeg' and a != 'image/jpeg', acionar=D(cl('radio-jpeg'))),
            Caso('imagem', '.uno:InsertCaptionDialog', 'legenda abaixo da imagem', self._p_imagem,
                 self._l_legenda, lambda a, d: d is True and a is False, acionar=D(dg('caption_edit', ' Logo do teste'))),
            Caso('referencias', '.uno:InsertCaptionDialog', 'legenda abaixo da imagem', self._p_imagem,
                 self._l_legenda, lambda a, d: d is True and a is False, acionar=D(dg('caption_edit', ' Logo do teste'))),
            Caso('imagem', '.uno:GraphicDialog', 'nome da imagem pelo diálogo Figura', self._p_imagem,
                 lambda d, c: self._imagem(d).getName() if self._imagem(d) else None, lambda a, d: d == 'ImagemRenomeada',
                 acionar=D(dg('name', 'ImagemRenomeada')), desfazer=None),
            # Forma
            Caso('forma', '.uno:TransformDialog', 'largura da forma (6 cm)', lambda: self._p_formas(1),
                 self._l_largura_forma, mm(6000),
                 acionar=D(dg('width', '6'))),
            Caso('forma', '.uno:FormatArea', 'preenchimento da forma (nenhum)', lambda: self._p_formas(1),
                 lambda d, c: self._forma(d, 1, 'FillStyle'), lambda a, d: d == 'NONE' and a != 'NONE', acionar=D(cl('btnnone'))),
            # Arquivo
            Caso('arquivo', '.uno:SetDocumentProperties', 'título do documento pelo diálogo Propriedades', lambda: None,
                 lambda d, c: d.getDocumentProperties().Title, lambda a, d: d == 'Título pelo diálogo',
                 acionar=D(ab(1), dg('title', 'Título pelo diálogo'), self._d_registrar('title'), confirmar='clique'), desfazer=None),
            # Exibir (só a exibição: sem desfazer e sem arquivo). Por último: Layout da web e Nova janela mudam a vista
            # e abrem outra janela; antes deles, as demais ferramentas rodam com a vista normal
            Caso('exibir', '.uno:ViewBounds', 'limites do texto (estado do comando)', lambda: None,
                 lambda d, c: self._estado_comando('.uno:ViewBounds'), dif, desfazer=None, formatos=(), acionar=self._repetir_clique),
            Caso('exibir', '.uno:GridVisible', 'grade (estado do comando)', lambda: None,
                 lambda d, c: self._estado_comando('.uno:GridVisible'), dif, desfazer=None, formatos=(), acionar=self._repetir_clique),
            Caso('exibir', '.uno:ShowWhitespace', 'ocultar espaço em branco (estado do comando)', lambda: None,
                 lambda d, c: self._estado_comando('.uno:ShowWhitespace'), dif, desfazer=None, formatos=(), acionar=self._repetir_clique),
            Caso('exibir', '.uno:Navigator', 'painel de navegação (estado do comando)', lambda: None,
                 lambda d, c: self._estado_comando('.uno:Navigator'), dif, desfazer=None, formatos=(), acionar=self._repetir_clique),
            Caso('exibir', '.uno:Sidebar', 'barra lateral (estado do comando)', lambda: None,
                 lambda d, c: self._estado_comando('.uno:Sidebar'), dif, desfazer=None, formatos=(), acionar=self._repetir_clique),
            Caso('exibir', '.uno:ControlCodes', 'marcas de formatação na exibição', lambda: None,
                 lambda d, c: self.ctrl.getViewSettings().ShowNonprintingCharacters, dif, desfazer=None, formatos=(),
                 acionar=self._repetir_clique),
            Caso('exibir', '.uno:PrintLayout', 'layout de impressão (sai do layout da web)', lambda: self._despachar_sinc('.uno:BrowseView'),
                 lambda d, c: (self._estado_comando('.uno:PrintLayout'), self._estado_comando('.uno:BrowseView')),
                 lambda a, d: d == (True, False) and a != d, desfazer=None, formatos=()),
            Caso('revisao', '.uno:SidebarDeck.A11yCheckDeck', 'painel Verificar acessibilidade visível na barra lateral', lambda: None,
                 lambda d, c: self._deck_ativo('A11yCheckDeck'), lambda a, d: d is True and a is not True, desfazer=None, formatos=()),
            # Uma página / Várias páginas / Exibição de livro: comando do AY que chama .uno:ViewLayout (colunas, livro)
            Caso('exibir', 'ayescreva:ExibicaoPaginas?colunas=1&livro=0', 'leiaute da exibição (colunas, livro)',
                 lambda: self._p_leiaute(2, True), lambda d, c: self._leiaute(), lambda a, d: d == (1, False) and a != d,
                 desfazer=None, formatos=()),
            Caso('exibir', 'ayescreva:ExibicaoPaginas?colunas=0&livro=0', 'leiaute da exibição (colunas, livro)',
                 lambda: self._p_leiaute(1, False), lambda d, c: self._leiaute(), lambda a, d: d == (0, False) and a != d,
                 desfazer=None, formatos=(), acionar=lambda b, c: self._depois(lambda: self._p_leiaute(1, False))),
            Caso('exibir', 'ayescreva:ExibicaoPaginas?colunas=2&livro=1', 'leiaute da exibição (colunas, livro)',
                 lambda: self._p_leiaute(1, False), lambda d, c: self._leiaute(), lambda a, d: d == (2, True) and a != d,
                 desfazer=None, formatos=(), acionar=lambda b, c: self._depois(lambda: self._p_leiaute(1, False))),
            Caso('exibir', '.uno:BrowseView', 'layout da web (estado do comando)', lambda: None,
                 lambda d, c: self._estado_comando('.uno:BrowseView'), dif, desfazer=None, formatos=(),
                 acionar=lambda b, c: self._depois(lambda: self._despachar_sinc('.uno:PrintLayout'))),
            Caso('exibir', '.uno:NewWindow', 'janelas abertas do documento', lambda: None,
                 lambda d, c: self._janelas_do_doc(), lambda a, d: d == a + 1, desfazer=None, formatos=()),
        ]
        return casos

    # ---------- diálogos: preencher pelos controles do próprio diálogo e confirmar -------------------
    def _esperar_janela(self, segundos=6.0, tipo='dialogo'):
        fim = time.time() + segundos
        while time.time() < fim:
            j, t = self.janela_extra()
            if j is not None and (tipo is None or t == tipo):
                time.sleep(0.6)
                return self.janela_extra()[0]
            time.sleep(0.25)
        return None

    def _preencher(self, acoes, tipo):
        """Executa as ações no diálogo aberto. As referências do teste ao diálogo são soltas aqui, com ele ainda aberto:
        nenhuma fica viva quando ele fecha (soltar depois, fora da linha principal, é arriscado; RESULTADOS §9)."""
        j = self._esperar_janela(tipo=tipo)
        if j is None:
            return False
        for a in acoes:
            a(j)
            time.sleep(0.3)
        return True

    def _clicar_no_dialogo(self, nome):
        j = self.janela_extra()[0]
        if j is None or nome not in set(j.getChildren()):
            return False
        botao = j.getChild(nome)
        j = None
        botao.executeAction('CLICK', ())
        return True

    def _dialogo(self, *acoes, botao='ok', fechar=None, tipo='dialogo', confirmar='enter'):
        """acionar(): espera o diálogo, executa as ações (cada uma recebe o diálogo) e confirma: com Enter do teclado de
        verdade (padrão; o botão padrão é o OK) ou com clique no botão (`confirmar='clique'`). `fechar` = botão que fecha
        depois (diálogos que ficam abertos, como Localizar e substituir)."""
        def acionar(b, ctx):
            if not self._preencher(acoes, tipo):
                raise RuntimeError('o diálogo não abriu')
            if botao:
                # Enter real, como uma pessoa: o clique simulado no OK às vezes derruba o motor (RESULTADOS §9).
                # Se o diálogo não fechar, clica no botão.
                if confirmar == 'enter':
                    self._teclas_reais(0x0D)
                    time.sleep(1.2)
                if self.janela_extra()[0] is not None:
                    self._clicar_no_dialogo(botao)
                    time.sleep(1.0)
            if fechar:
                self._teclas_reais(0x1B)          # janela não modal: Esc real
                time.sleep(0.8)
                if self.janela_extra()[0] is not None:
                    self._clicar_no_dialogo(fechar)
                    time.sleep(0.8)
        return acionar

    @staticmethod
    def _aba(pos):
        return lambda j: j.getChild('tabcontrol').executeAction('SELECT', (_pv('POS', str(pos)),))

    @staticmethod
    def _digitar(nome, texto):
        def f(j):
            c = j.getChild(nome)
            c.executeAction('TYPE', (_pv('KEYCODE', 'CTRL+A'),))
            c.executeAction('TYPE', (_pv('TEXT', texto),))
        return f

    @staticmethod
    def _clicar(nome):
        return lambda j: j.getChild(nome).executeAction('CLICK', ())

    @staticmethod
    def _d_escolher(nome, pos, acao='SELECT'):
        return lambda j: j.getChild(nome).executeAction(acao, (_pv('POS', str(pos)),))

    @staticmethod
    def _item(nome, pos):
        return lambda j: j.getChild(nome).getChild(str(pos)).executeAction('SELECT', ())

    # ---------- auxiliares dos casos --------------------------------------------------------------
    def _p_nota(self):
        def f():
            n = self.doc.createInstance('com.sun.star.text.Footnote')
            self.doc.Text.insertTextContent(self._achar(self.doc, 'faixa.').getEnd(), n, False)
            n.getText().setString('Nota de teste')
        self.no_principal(f)

    def _l_objetos_na_pagina(self, d, c):
        """Objetos incorporados que estão de fato no documento (na página de desenho). A coleção getEmbeddedObjects()
        pode continuar contando um objeto desfeito, guardado para o refazer."""
        dp = d.getDrawPage()
        n = 0
        for i in range(dp.getCount()):
            if dp.getByIndex(i).supportsService('com.sun.star.text.TextEmbeddedObject'):
                n += 1
        _log(f'objetos na página: {n}; coleção de objetos incorporados: {d.getEmbeddedObjects().getCount()}')
        return n

    def _objeto_ativo(self):
        """O que está selecionado/ativo na janela do documento (para saber se o gráfico ainda está em edição)."""
        try:
            c = self.frame.getController()
            sel = c.getSelection()
            return f'{c.getImplementationName()} | seleção {getattr(sel, "ImplementationName", type(sel).__name__)}'
        except Exception as e:
            return f'erro: {e}'

    def _leiaute(self):
        """(colunas, livro) do leiaute da exibição, como o controle da barra de status informa. Thread principal."""
        st = self._estado_comando('.uno:ViewLayout')
        try:
            v = {p.Name: p.Value for p in st}
            return (int(v.get('Columns')), bool(v.get('BookMode')))
        except Exception:
            return repr(st)[:80]

    def _p_leiaute(self, colunas, livro):
        pv = (_pv('ViewLayout.Columns', uno.Any('short', colunas)), _pv('ViewLayout.BookMode', livro))
        self._despachar_sinc('.uno:ViewLayout', pv)
        time.sleep(0.5)

    def _l_largura_forma(self, d, c):
        for s in self._formas(d):
            if s.Name == 'FormaTeste1':
                return s.getSize().Width
        f = self._formas(d)
        return f[0].getSize().Width if f else None

    def _d_registrar(self, nome):
        """Ação de diálogo que só registra o texto do campo (diagnóstico de campos que não chegam ao documento)."""
        def f(j):
            _log(f'campo {nome} depois de digitar: {_estado(j.getChild(nome)).get("Text")!r}')
        return f

    def _l_quadros(self, d, c):
        """Quadros do texto; no DOCX reaberto, um quadro pode voltar como forma com caixa de texto (TextBox)."""
        caixas = 0
        dp = d.getDrawPage()
        for i in range(dp.getCount()):
            s = dp.getByIndex(i)
            try:
                if not s.supportsService('com.sun.star.text.TextFrame') and s.getPropertyValue('TextBox'):
                    caixas += 1
            except Exception:
                pass
        # uma caixa de texto do motor é forma + quadro ligados: conta uma vez só
        return max(d.getTextFrames().getCount(), caixas)

    def _estilo_pagina(self, d):
        return d.getStyleFamilies().getByName('PageStyles').getByName('Standard')

    def _l_pagina_fundo_borda(self, d, c):
        e = self._estilo_pagina(d)
        return (_val(e.FillStyle), e.LeftBorder.OuterLineWidth + e.LeftBorder.InnerLineWidth)

    def _l_margem(self, d, c):
        return self._estilo_pagina(d).LeftMargin

    def _l_marca_dagua(self, d, c):
        dp = d.getDrawPage()
        for i in range(dp.getCount()):
            s = dp.getByIndex(i)
            if s.Name.startswith('PowerPlusWaterMarkObject'):
                return s.getString()
        return None

    def _l_marcas_indice(self, d, c):
        n = 0
        e = d.Text.createEnumeration()
        while e.hasMoreElements():
            p = e.nextElement()
            if not p.supportsService('com.sun.star.text.Paragraph'):
                continue
            pe = p.createEnumeration()
            while pe.hasMoreElements():
                t = pe.nextElement()
                # uma marca sobre um trecho tem duas partes (início e fim): conta só o início (ou a marca recolhida)
                if t.TextPortionType == 'DocumentIndexMark' and (t.IsCollapsed or t.IsStart):
                    n += 1
        return n

    def _p_tabela_larguras(self):
        nome = self._p_tabela(ate='C3')

        def f():
            t = self.doc.getTextTables().getByName(nome)
            t.getCellByName('A1').setString('texto bem mais comprido na primeira coluna da tabela de teste')
        self.no_principal(f)
        return nome

    def _p_campo_hora(self):
        def f():
            d = self.doc
            loc = uno.createUnoStruct('com.sun.star.lang.Locale')
            loc.Language, loc.Country = 'pt', 'BR'
            fmts = d.getNumberFormats()
            chave = fmts.queryKey('HH:MM:SS', loc, False)
            if chave == -1:
                chave = fmts.addNew('HH:MM:SS', loc)
            c = d.createInstance('com.sun.star.text.textfield.DateTime')
            c.IsDate = False
            c.IsFixed = False
            c.NumberFormat = chave
            d.Text.insertTextContent(d.Text.getEnd(), c, False)
        self.no_principal(f)
        time.sleep(2.2)                          # o relógio anda; o campo só muda quando os campos são atualizados

    def _l_campo_hora(self, d, c):
        e = d.getTextFields().createEnumeration()
        while e.hasMoreElements():
            x = e.nextElement()
            if x.supportsService('com.sun.star.text.textfield.DateTime') and not x.IsDate:
                return x.getAnchor().getString()
        return None

    def _l_rotacao(self, d, c):
        """Rotação em graus × 10. No DOCX reaberto, a imagem girada pode voltar como forma de imagem (RotateAngle em
        centésimos de grau) em vez de imagem do texto."""
        img = self._imagem(d)
        if img is not None:
            return img.GraphicRotation
        dp = d.getDrawPage()
        for i in range(dp.getCount()):
            s = dp.getByIndex(i)
            if s.supportsService('com.sun.star.drawing.GraphicObjectShape'):
                return round(s.RotateAngle / 10) % 3600
        return None

    def _p_tabela_ordenar(self):
        def f():
            t = self.doc.createInstance('com.sun.star.text.TextTable')
            t.initialize(3, 2)
            self.doc.Text.insertTextContent(self.doc.Text.getEnd(), t, False)
            for i, v in enumerate(('c', 'b', 'a')):
                t.getCellByName(f'A{i + 1}').setString(v)
                t.getCellByName(f'B{i + 1}').setString(str(i))
            cur = t.createCursorByCellName('A1')
            cur.gotoCellByName('B3', True)
            self.ctrl.select(cur)
        self.no_principal(f)
        self.esperar(0.8)

    def _l_coluna_a(self, d, c):
        t = self._tabela(d)
        return tuple(t.getCellByName(f'A{i}').getString() for i in (1, 2, 3)) if t else None

    def _l_tipo_imagem(self, d, c):
        img = self._imagem(d)
        if img is None:
            return None
        return img.Graphic.getPropertyValue('MimeType') if img.Graphic is not None else None

    def _l_legenda(self, d, c):
        fr = d.getTextFrames()
        for n in fr.getElementNames():
            if 'Logo do teste' in fr.getByName(n).getText().getString():
                return True
        # no DOCX reaberto, imagem e legenda podem voltar como forma (ou grupo) com texto
        dp = d.getDrawPage()
        pilha = [dp.getByIndex(i) for i in range(dp.getCount())]
        while pilha:
            s = pilha.pop()
            try:
                if 'Logo do teste' in (s.getString() or ''):
                    return True
            except Exception:
                pass
            if s.supportsService('com.sun.star.drawing.GroupShape'):
                pilha.extend(s.getByIndex(i) for i in range(s.getCount()))
        return 'Logo do teste' in d.Text.getString()

    def _lista_espacamento(self, b, ctx):
        """Lista de espaçamento entre linhas: escolhe "Duplo" na caixa da lista e fecha a lista com Esc."""
        j = self._esperar_janela(tipo=None)
        if j is None:
            raise RuntimeError('a lista não abriu')
        j.getChild('linespacing').executeAction('SELECT', (_pv('TEXT', 'Duplo'),))
        time.sleep(0.8)
        self._fechar_real('lista de espaçamento')

    def _depois(self, f):
        """Guarda uma ação para desfazer a mudança de exibição depois da leitura (ver _repetir_clique)."""
        self._restaurar = f

    def _repetir_clique(self, b, ctx):
        """Ferramentas que alternam um estado: depois da leitura, o próprio botão é clicado de novo para voltar."""
        self._restaurar = lambda: (self.clicar(b), self.esperar(0.6))

    def _area_transferencia(self):
        if True:
            cb = self.smgr.createInstanceWithContext('com.sun.star.datatransfer.clipboard.SystemClipboard', self.ctx)
            c = cb.getContents()
            for fl in c.getTransferDataFlavors():
                if fl.MimeType.startswith('text/plain'):
                    v = c.getTransferData(fl)
                    return v if isinstance(v, str) else bytes(v.value).decode('utf-16-le', 'replace').rstrip('\x00')
            return None

    def _colar_no_fim(self, b, ctx):
        time.sleep(0.5)
        self._cursor_em('faixa.', fim=True)
        self._despachar_sinc('.uno:Paste')

    def _p_colar(self):
        self._sel('zeta')
        self._despachar_sinc('.uno:Copy')
        self._cursor_em('faixa.', fim=True)

    def _p_espaco(self):
        def f():
            p = self._paragrafo_com(self.doc, 'alfa')
            p.ParaTopMargin, p.ParaBottomMargin = 500, 500
        self.no_principal(f)
        self._sel('alfa')

    def _texto_selecionado(self):
        s = self.ctrl.getSelection()
        try:
            return ''.join(s.getByIndex(i).getString() for i in range(s.getCount()))
        except Exception:
            return getattr(s, 'String', '') or ''

    def _deck_ativo(self, nome):
        sb = self.ctrl.getSidebar()
        if sb is None or not sb.isVisible():
            return False
        try:
            return sb.getDecks().getByName(nome).isActive()
        except Exception:
            return None

    def _sair_do_objeto(self, b, ctx):
        """O gráfico abre em modo de edição; volta ao texto como uma pessoa faria: Esc duas vezes (sai da edição do
        gráfico e tira a seleção do objeto)."""
        self.esperar(2.0)
        for _ in range(2):
            self._teclas_reais(0x1B)
            time.sleep(0.8)

        def desativar():
            # se as teclas não chegaram (outra janela em primeiro plano), sai da edição como um clique fora do gráfico:
            # o objeto volta ao estado "em execução" (EmbedStates.RUNNING = 1), sem edição na página
            estados = []
            objs = self.doc.getEmbeddedObjects()
            for i in range(objs.getCount()):
                eo = objs.getByIndex(i).getExtendedControlOverEmbeddedObject()
                if eo is not None:
                    estados.append(eo.getCurrentState())
                    if eo.getCurrentState() > 1:
                        eo.changeState(1)
            self.ctrl.select(self._achar(self.doc, 'alfa'))
            return estados
        try:
            _log(f'gráfico: estados do objeto antes de sair da edição: {self.no_principal(desativar)}')
        except Exception:
            _log('gráfico: ' + traceback.format_exc()[-300:])

    def _l_ordem(self, d, c):
        z = {}
        for s in self._formas(d):
            if s.Name in ('FormaTeste1', 'FormaTeste2'):
                z[s.Name] = s.ZOrder
        return (z.get('FormaTeste1'), z.get('FormaTeste2')) if len(z) == 2 else None

    def _forma(self, d, n, prop):
        for s in self._formas(d):
            if s.Name == f'FormaTeste{n}':
                return _val(s.getPropertyValue(prop))
        f = self._formas(d)
        return _val(f[0].getPropertyValue(prop)) if f else None

    def _l_sumario(self, d, c):
        idx = d.getDocumentIndexes()
        if not idx.getCount():
            return None
        return 'Capítulo de teste do sumário' in idx.getByIndex(0).getAnchor().getString()

    def _p_campo_titulo(self):
        def f():
            d = self.doc
            d.getDocumentProperties().Title = 'Título antigo'
            c = d.createInstance('com.sun.star.text.textfield.docinfo.Title')
            d.Text.insertTextContent(d.Text.getEnd(), c, False)
            d.getTextFields().refresh()
            d.getDocumentProperties().Title = 'Título novo'
        self.no_principal(f)

    def _l_campo_titulo(self, d, c):
        e = d.getTextFields().createEnumeration()
        while e.hasMoreElements():
            x = e.nextElement()
            if x.supportsService('com.sun.star.text.textfield.docinfo.Title'):
                return x.getAnchor().getString()
        return None

    def _l_alteracoes(self, d, c):
        t = d.Text.getString()
        # a exclusão pendente continua no texto até ser aceita; "gama " some ao aceitar e volta a ser texto comum ao rejeitar
        return (self._redlines(d), 'inserção controlada' in t, 'gama' in t)

    def _l_colunas(self, d, c):
        t = self._tabela(d)
        if t is None:
            return None
        return tuple(s.Position for s in t.TableColumnSeparators)

    def _celulas_selecionadas(self):
        sel = self.ctrl.getSelection()
        for nome in ('getRangeName',):
            if hasattr(sel, nome):
                return self._contar_intervalo(sel.getRangeName())
        try:
            return self._contar_intervalo(sel.RangeName)
        except Exception:
            return getattr(sel, 'ImplementationName', '?')

    def _contar_intervalo(self, nome):
        import re
        a, b = nome.split(':')
        ca, la = re.match(r'([A-Z]+)(\d+)', a).groups()
        cb, lb = re.match(r'([A-Z]+)(\d+)', b).groups()
        return (ord(cb) - ord(ca) + 1) * (int(lb) - int(la) + 1)

    def _colunas_vista(self):
        return self.ctrl.getViewSettings().getPropertyValue('ViewLayoutColumns')

    def _livro_vista(self):
        return self.ctrl.getViewSettings().getPropertyValue('ViewLayoutBookMode')

    def _janelas_do_doc(self):
        n = 0
        quadros = self.desktop.getFrames()
        for i in range(quadros.getCount()):
            c = quadros.getByIndex(i).getController()
            if c is not None and c.getModel() == self.doc:
                n += 1
        return n

    # ---------- passo da fase 12 ----------------------------------------------------------------
    def validar_ferramentas(self):
        # depuração: só alguns comandos (no spec ou em AY_FERRAMENTAS, separados por vírgula)
        so = self.spec.get('ferramentas') or [x for x in os.environ.get('AY_FERRAMENTAS', '').split(',') if x]
        # na bateria, as ferramentas com diálogo rodam isoladas (fase 12b): AY_FERRAMENTAS_EXCETO as tira desta fase
        exceto = [x for x in os.environ.get('AY_FERRAMENTAS_EXCETO', '').split(',') if x]
        for caso in self.casos_ferramentas():
            if (so and caso.comando not in so and caso.ident not in so) or caso.comando in exceto or caso.ident in exceto:
                continue
            self._restaurar = None
            self.validar(caso)
            if self._restaurar:
                try:
                    self._restaurar()
                except Exception:
                    _log('restaurar: ' + traceback.format_exc()[-300:])
                self._restaurar = None
        self._resumo_ferramentas()

    def _resumo_ferramentas(self):
        fs = self.res.get('ferramentas', {})
        ok = sum(1 for r in fs.values() if r.get('validado'))
        _log(f'resumo: {ok}/{len(fs)} ferramentas com efeito conferido')

    # ---------- exploração: o que cada botão abre (nomes dos controles) ----------------------------
    def explorar_ferramentas(self):
        alvos = [
            ('inicio', '.uno:SetOutline', None), ('inicio', '.uno:LineSpacing', None), ('inicio', '.uno:FontDialog', None),
            ('inicio', '.uno:ParagraphDialog', None), ('inicio', '.uno:SearchDialog', None), ('inicio', '.uno:PasteSpecial', 'copiar'),
            ('inserir', '.uno:InsertSection', None), ('inserir', '.uno:InsertFrame', None), ('inserir', '.uno:TitlePageDialog', None),
            ('inserir', '.uno:InsertFieldCtrl', None), ('inserir', '.uno:CharmapControl', None), ('design', '.uno:Watermark', None),
            ('design', '.uno:PageDialog', None), ('layout', '.uno:PageMargin', None), ('layout', '.uno:AttributePageSize', None),
            ('layout', '.uno:LineNumberingDialog', None), ('layout', '.uno:Hyphenate', None), ('referencias', '.uno:FootnoteDialog', None),
            ('referencias', '.uno:InsertIndexesEntry', None), ('revisao', '.uno:ProtectTraceChangeMode', None),
            ('revisao', '.uno:SetLanguageAllTextMenu', None), ('revisao', '.uno:WordCountDialog', None),
            ('revisao', '.uno:AcceptTrackedChanges', 'alteracoes'), ('tabela', '.uno:SplitCell', 'tabela'),
            ('tabela', '.uno:SetBorderStyle', 'tabela'), ('tabela', '.uno:AutoFormat', 'tabela'), ('tabela', '.uno:SortDialog', 'tabela'),
            ('tabela', '.uno:TableDialog', 'tabela'), ('imagem', '.uno:CompressGraphic', 'imagem'),
            ('imagem', '.uno:InsertCaptionDialog', 'imagem'), ('imagem', '.uno:GraphicDialog', 'imagem'),
            ('forma', '.uno:TransformDialog', 'forma'), ('forma', '.uno:FormatArea', 'forma'), ('arquivo', '.uno:SetDocumentProperties', None),
        ]
        preps = {None: lambda: None, 'tabela': self._p_tabela, 'imagem': self._p_imagem, 'forma': lambda: self._p_formas(1),
                 'alteracoes': self._p_alteracoes, 'copiar': lambda: (self._sel('beta'), self._despachar_sinc('.uno:Copy'))}
        self.res.setdefault('exploracao', [])
        for aba, cmd, prep in alvos:
            try:
                self._limpar()
                preps[prep]()
                b = self.botao(cmd, aba)
                self.aba_atual = None
                disparado = self.clicar(b)
                time.sleep(1.8)
                j, tipo = self.janela_extra()
                item = {'comando': cmd, 'disparado': disparado, 'tipo': tipo}
                if j is not None:
                    item['titulo'] = _estado(j).get('Text', '')
                    filhos = list(j.getChildren())
                    item['filhos'] = filhos[:300]
                    item['n'] = len(filhos)
                _log(f'explorar {cmd}: {tipo} "{item.get("titulo", "")}" {item.get("n", 0)} controles')
                self.res['exploracao'].append(item)
            except Exception:
                _log(f'explorar {cmd}: ' + traceback.format_exc()[-400:])
                self.res['exploracao'].append({'comando': cmd, 'erro': traceback.format_exc()[-300:]})
            try:
                self._fechar_real('depois da exploração', cmd)
                self.fechar_outras_janelas()
            except Exception:
                pass
        # propriedades de exibição disponíveis (para as ferramentas da aba Exibir)
        try:
            self.res['propriedades_vista'] = self.no_principal(
                lambda: [p.Name for p in self.ctrl.getViewSettings().getPropertySetInfo().getProperties()])
        except Exception:
            pass
