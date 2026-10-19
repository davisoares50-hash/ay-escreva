# -*- coding: utf-8 -*-
"""Testes da faixa de opções do AY ESCREVA executados DENTRO do aplicativo, pela interface (UITest).

Instalada só em perfis descartáveis de teste (tests/interface/testar_faixa.ps1). Não faz nada se a variável
AY_TESTE_UI_SPEC não estiver definida.

Como funciona: o serviço org.libreoffice.uitest.UITest (o mesmo usado nos testes de interface do LibreOffice)
dá acesso aos componentes da janela pelos ids do arquivo .ui. O gerador da faixa (tools/gerar-faixa.mjs)
produz um mapa comando -> caixa de botões e posição. Para cada botão o teste:
  1. seleciona a aba no controle de abas e confere que a página certa ficou visível;
  2. confere que a caixa de botões existe, está visível e tem o item;           -> "presente"
  3. clica no item (como um clique do mouse) e lê qual comando o botão disparou; -> "acionado"
  4. deixa a interface processar o comando e confere o efeito no documento ou na exibição -> "validado"
Diálogos e listas abertos pelos botões são registrados e fechados com Esc.

Tudo roda na thread principal (sem threads auxiliares, que causavam impasse entre o bloqueio do Python e o
da interface); as esperas usam XReschedule para a interface continuar processando eventos.
Por que dentro do processo: comandar a interface a partir de outro processo pela ponte UNO derruba o motor
de forma intermitente quando a faixa por abas está na tela (investigação em docs/RESULTADOS-TESTES.md).
SPDX-License-Identifier: MPL-2.0
"""
import json
import os
import threading
import time
import traceback

import uno
import unohelper
from com.sun.star.awt import XCallback
from com.sun.star.beans import PropertyValue
from com.sun.star.task import XJob

# Não acionados no teste genérico: fecham/reiniciam, abrem programas externos, mexem na área de transferência
# do usuário, dependem de dados externos ou têm teste específico. Continuam verificados como "presente".
NAO_ACIONAR = {'.uno:CloseDoc', '.uno:CloseWin', '.uno:NewWindow', '.uno:SafeMode', '.uno:Reload', '.uno:HelpIndex',
               '.uno:Cut', '.uno:Copy', '.uno:Paste', '.uno:BrowseView', '.uno:FullScreen',
               '.uno:AddDirect', '.uno:Open', '.uno:NewDoc', '.uno:Save', '.uno:SaveAs', '.uno:SaveACopy',
               '.uno:DeleteAllNotes', '.uno:SelectAll', '.uno:ChangeTheme',
               '.uno:MailMergeWizard', '.uno:MailMergeCreateDocuments', '.uno:MailMergeSaveDocuments',
               '.uno:MailMergePrintDocuments', '.uno:ViewDataSourceBrowser', '.uno:ChangeDatabaseField',
               '.uno:BibliographyComponent', '.uno:Sidebar', '.uno:Navigator',
               '.uno:AcceptAllTrackedChanges', '.uno:RejectAllTrackedChanges', '.uno:ProtectTraceChangeMode',
               '.uno:PrintPreview', '.uno:Delete', '.uno:ShowWhitespace',
               '.uno:CompareDocuments', '.uno:MergeDocuments'}  # exigem um segundo documento (seletor de arquivo)


# Comandos que abrem janelas NÃO modais (abrem e fecham pelo mesmo comando): o teste aciona de novo para fechar
ALTERNA_JANELA = {'.uno:SpellingAndGrammarDialog', '.uno:AcceptTrackedChanges', '.uno:SearchDialog',
                  '.uno:HyperlinkDialog', '.uno:FontworkGalleryFloater', '.uno:InsertIndexesEntry',
                  '.uno:InsertAuthoritiesEntry', '.uno:Navigator', '.uno:InsertFieldCtrl'}


def _log(msg):
    try:
        with open(os.path.join(os.environ.get('TEMP', '.'), 'ay-testes-ui.log'), 'a', encoding='utf-8') as f:
            f.write(time.strftime('%H:%M:%S ') + msg + chr(10))
    except Exception:
        pass


def _pv(nome, valor):
    p = PropertyValue()
    p.Name, p.Value = nome, valor
    return p


def _props(**kw):
    return tuple(_pv(k, v) for k, v in kw.items())


def _estado(obj):
    try:
        return {p.Name: p.Value for p in obj.getState()}
    except Exception:
        return {}


class Chamada(unohelper.Base, XCallback):
    def __init__(self, f):
        self.f = f

    def notify(self, dados):
        try:
            self.f()
        except Exception:
            _log('callback: ' + traceback.format_exc()[-800:])


class Executor(unohelper.Base, XJob):
    def __init__(self, ctx, *args):
        self.ctx = ctx

    def execute(self, args):
        # Disparada pelo evento OnLoad: o ambiente da tarefa traz o documento carregado ("Model")
        spec = os.environ.get('AY_TESTE_UI_SPEC')
        modelo = None
        for a in args:
            if a.Name == 'Environment':
                for e in a.Value:
                    if e.Name == 'Model':
                        modelo = e.Value
        _log(f'execute: spec={spec} modelo={"sim" if modelo is not None else "não"}')
        if spec and modelo is not None and not getattr(Executor, '_iniciado', False):
            Executor._iniciado = True
            try:
                Teste(self.ctx, spec, modelo).iniciar()
            except Exception:
                _log('falha ao iniciar: ' + traceback.format_exc()[-1000:])
        return None


class Teste:
    def __init__(self, ctx, spec, modelo):
        self.ctx = ctx
        self.doc = modelo
        self.spec = json.load(open(spec, encoding='utf-8-sig'))
        self.mapa = json.load(open(self.spec['mapa'], encoding='utf-8-sig'))
        self.saida = self.spec['saida']
        self.res = {'inicio': time.strftime('%Y-%m-%dT%H:%M:%S'), 'abas': [], 'funcoes': {}, 'dialogos': [],
                    'efeitos': [], 'avisos': [], 'erros': []}
        self.smgr = ctx.ServiceManager
        self.desktop = self.smgr.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
        self.async_ = self.smgr.createInstanceWithContext('com.sun.star.awt.AsyncCallback', ctx)
        self.ui = self.smgr.createInstanceWithContext('org.libreoffice.uitest.UITest', ctx)
        self.aba_atual = None

    # ---------- execução e esperas ---------------------------------------------------------------
    def postar(self, f):
        self.async_.addCallback(Chamada(f), uno.Any('void', None))

    def iniciar(self):
        # O UITest executa cada ação na thread principal e espera o término: por isso a sequência de testes
        # roda numa thread própria (chamar executeAction da thread principal trava o aplicativo).
        threading.Thread(target=self.executar, daemon=True).start()

    def esperar(self, segundos):
        """Espera com a thread principal livre para processar a interface (diálogos, comandos, listas)."""
        time.sleep(segundos)

    def executar(self):
        try:
            self.esperar(4)
            self.preparar()
            passos = self.plano()
            _log(f'passos planejados: {len(passos)}')
            for n, (f, espera) in enumerate(passos, 1):
                if n <= 15:
                    _log(f'passo {n}: esperar {espera}')
                self.esperar(espera)
                if n <= 15:
                    _log(f'passo {n}: fechar extras')
                self.fechar_janelas_extras('antes do passo seguinte')
                if n <= 15:
                    _log(f'passo {n}: executar')
                try:
                    f()
                except Exception:
                    self.res['erros'].append(traceback.format_exc()[-1200:])
                    _log('erro: ' + traceback.format_exc()[-500:])
                if n % 25 == 0:
                    _log(f'passos: {n}/{len(passos)}')
        except Exception:
            self.res['erros'].append(traceback.format_exc()[-1500:])
            _log('falha geral: ' + traceback.format_exc()[-800:])
        self.concluir()

    # ---------- janelas ----------------------------------------------------------------------
    def topo(self):
        return self.ui.getTopFocusWindow()

    def principal(self):
        for tentativa in range(4):
            t = self.topo()
            if 'ContextContainer' in t.getChildren():
                return t
            titulo = _estado(t).get('Text', '')
            if tentativa < 2:
                # Diálogo ou lista aberta por um comando anterior: Esc
                self.res['avisos'].append(f'foco fora da janela principal ("{titulo}"); Esc enviado')
                try:
                    t.executeAction('TYPE', (_pv('KEYCODE', 'ESC'),))
                except Exception:
                    pass
            else:
                # Janela não modal (painel, navegador, galeria): devolve o foco à janela do documento
                self.res['avisos'].append(f'janela não modal "{titulo}" com o foco; foco devolvido ao documento')
                try:
                    self.frame.activate()
                    self.frame.getContainerWindow().setFocus()
                    self.frame.getComponentWindow().setFocus()
                except Exception:
                    pass
            time.sleep(0.5)
        return None

    def janela_extra(self):
        """Janela em foco que não é a do documento (diálogo ou lista suspensa), ou (None, None)."""
        try:
            flut = self.ui.getFloatWindow()
            if flut is not None:
                return flut, 'lista'
        except Exception:
            pass
        try:
            t = self.topo()
            if 'ContextContainer' not in t.getChildren():
                return t, 'dialogo'
        except Exception:
            pass
        return None, None

    def fechar_janelas_extras(self, quando, funcao=None, tecla='ESC'):
        for _ in range(3):
            j, tipo = self.janela_extra()
            if j is None:
                return False
            titulo = _estado(j).get('Text', '')
            if funcao:
                if not any(d['funcao'] == funcao and d['titulo'] == titulo for d in self.res['dialogos']):
                    self.res['dialogos'].append({'funcao': funcao, 'titulo': titulo, 'tipo': tipo})
            else:
                self.res['avisos'].append(f'{tipo} "{titulo}" ainda aberto {quando}; fechado com Esc')
            try:
                filhos = set(j.getChildren()) if tipo == 'dialogo' else set()
                botao = next((b for b in ('cancel', 'close', 'no', 'btnCancel', 'cancelbutton') if b in filhos), None)
                if tecla == 'ESC' and botao:
                    # Como nos testes de interface do LibreOffice: fecha pelo botão Cancelar/Fechar do diálogo
                    j.getChild(botao).executeAction('CLICK', ())
                elif tecla == 'ESC' and tipo == 'lista':
                    # Listas suspensas da faixa ignoram o Esc do UITest: tecla real pelo robô do toolkit
                    self.tecla_robo(1281)    # com.sun.star.awt.Key.ESCAPE
                else:
                    j.executeAction('TYPE', (_pv('KEYCODE', tecla),))
            except Exception as e:
                self.res['avisos'].append(f'não foi possível fechar "{titulo}": {e}')
                return False
            time.sleep(0.3)
            if tecla != 'ESC':
                return True
        # Último recurso: encerra o diálogo ativo pelo toolkit
        try:
            tk = self.smgr.createInstanceWithContext('com.sun.star.awt.Toolkit', self.ctx)
            ativa = tk.getActiveTopWindow()
            dlg = ativa.queryInterface(uno.getTypeByName('com.sun.star.awt.XDialog')) if ativa is not None else None
            if dlg is not None and ativa != self.frame.getContainerWindow():
                self.res['avisos'].append(f'diálogo "{dlg.getTitle()}" encerrado pelo toolkit')
                dlg.endExecute()
        except Exception:
            pass
        return True

    def tecla_robo(self, codigo, janela=None):
        """Pressiona e solta uma tecla real (XToolkitRobot) na janela indicada (padrão: a do documento)."""
        tk = self.smgr.createInstanceWithContext('com.sun.star.awt.Toolkit', self.ctx)
        robo = tk.queryInterface(uno.getTypeByName('com.sun.star.awt.XToolkitRobot'))
        ev = uno.createUnoStruct('com.sun.star.awt.KeyEvent')
        # A janela do documento recebe a tecla; o VCL entrega o Esc primeiro à lista suspensa aberta
        ev.Source = janela or self.frame.getContainerWindow()
        ev.KeyCode = codigo
        ev.KeyChar = {1281: chr(27), 1280: chr(13)}.get(codigo, chr(0))
        robo.keyPress(ev)
        robo.keyRelease(ev)

    def vigiar(self, funcao, segundos=2.0, tecla='ESC', ao_achar=None):
        """Depois de um clique: espera até `segundos` por um diálogo ou lista aberta pelo comando; registra e
        fecha (Esc) ou responde (outra tecla). Roda na thread de testes; a interface segue na principal."""
        limite = time.time() + segundos
        time.sleep(0.6)
        while time.time() < limite:
            j, tipo = self.janela_extra()
            if j is not None:
                time.sleep(0.4)          # deixa o diálogo terminar de abrir
                j, tipo = self.janela_extra()
                if j is not None and ao_achar:
                    ao_achar(j)
                return self.fechar_janelas_extras('', funcao, tecla)
            time.sleep(0.25)
        return False

    def responder_dialogo(self, funcao, segundos, botao, ao_achar=None):
        """Espera o diálogo aberto por um comando e clica no botão `botao` (nome do controle). Se o nome não
        estiver exposto ao UITest, pressiona Enter real pelo robô do toolkit (aciona o botão padrão)."""
        limite = time.time() + segundos
        time.sleep(0.6)
        while time.time() < limite:
            j, tipo = self.janela_extra()
            if j is not None and tipo == 'dialogo':
                time.sleep(0.4)
                titulo = _estado(j).get('Text', '')
                self.res['dialogos'].append({'funcao': funcao, 'titulo': titulo, 'tipo': tipo})
                if ao_achar:
                    ao_achar(j)
                filhos = set(j.getChildren())
                if botao in filhos:
                    j.getChild(botao).executeAction('CLICK', ())
                    _log(f'diálogo "{titulo}": botão {botao}')
                else:
                    tk = self.smgr.createInstanceWithContext('com.sun.star.awt.Toolkit', self.ctx)
                    self.tecla_robo(1280, tk.getActiveTopWindow())
                    _log(f'diálogo "{titulo}": Enter pelo robô (controles: {", ".join(sorted(filhos))})')
                return True
            time.sleep(0.25)
        return False

    # ---------- faixa -------------------------------------------------------------------------
    def aba_info(self, id_ou_rotulo):
        return next(a for a in self.mapa['abas'] if a['id'] == id_ou_rotulo or a['rotulo'] == id_ou_rotulo)

    def selecionar_aba(self, id_ou_rotulo):
        a = self.aba_info(id_ou_rotulo)
        p = self.principal()
        if p is None:
            raise RuntimeError('janela do documento não está em foco')
        p.getChild('ContextContainer').executeAction('SELECT', (_pv('POS', str(a['posicao'])),))
        self.aba_atual = a['id']
        self.esperar(0.4)
        return a

    def pagina_visivel(self, id_aba):
        p = self.principal()
        if p is None or ('pagina-' + id_aba) not in p.getChildren():
            return False
        return _estado(p.getChild('pagina-' + id_aba)).get('ReallyVisible') == 'true'

    def botao(self, cmd, aba=None):
        return next((b for b in self.mapa['botoes'] if b['comando'] == cmd and (aba is None or b['aba'] == aba)), None)

    def clicar(self, b):
        """Clica no item da caixa de botões e devolve o comando que o botão disparou."""
        if self.aba_atual != b['aba']:
            self.selecionar_aba(b['aba'])
        caixa = self.principal().getChild(b['caixa'])
        caixa.executeAction('CLICK', (_pv('POS', str(b['posicao'])),))
        return _estado(caixa).get('CurrSelectedItemCommand', '')

    def chave(self, b):
        return f"{b['rotuloAba']} › {b['funcao']}"

    def registro(self, chave):
        return self.res['funcoes'].setdefault(chave, {'presente': False, 'acionado': False, 'validado': False, 'detalhes': []})

    def registrar(self, chave, nivel, detalhe=''):
        f = self.registro(chave)
        f[nivel] = True
        if detalhe and detalhe not in f['detalhes']:
            f['detalhes'].append(detalhe)

    # ---------- preparação --------------------------------------------------------------------
    def preparar(self):
        _log('preparar')
        self.ctrl = self.doc.getCurrentController()
        self.frame = self.ctrl.getFrame()
        self.esperar(2.0)
        self.res['documento'] = self.doc.getURL()

    def selecionar_texto(self, trecho):
        busca = self.doc.createSearchDescriptor()
        busca.SearchString = trecho
        r = self.doc.findFirst(busca)
        if r is not None:
            self.ctrl.select(r)
        return r

    def plano(self):
        passos = []
        somente = self.spec.get('somente')
        if somente:
            # Modo de depuração: só os passos pedidos (ex.: ["tabela", "salvar_odt", "docx"])
            mapa_passos = {'texto': [(self.preparar_texto, 0.2)], 'tabela': [(self.contexto_tabela, 0.5)],
                           'imagem': [(self.contexto_imagem, 0.5)], 'salvar_odt': [(self.efeito_salvar_odt, 0.5)],
                           'docx': [(self.abrir_docx, 1.0), (self.verificar_aviso_fontes, 3.0), (self.efeito_salvar_docx, 1.0)],
                           # Fase 2: o DOCX é o documento aberto na inicialização (uma só janela, foco garantido)
                           'docx_inicial': [(self.verificar_aviso_fontes, 3.0), (self.efeito_salvar_docx, 1.0)],
                           # Fechar um DOCX alterado e escolher Salvar na pergunta (caminho que não passa pelo botão)
                           'fechar_docx': [(self.efeito_fechar_docx, 1.0)]}
            for nome in somente:
                passos.extend(mapa_passos[nome])
            return passos

        def P(f, espera=0.2):
            passos.append((f, espera))
        for a in [a for a in self.mapa['abas'] if not a['contextual']]:
            P(lambda a=a: self.conferir_aba(a))
        P(self.preparar_texto)
        for cmd, prop, lig, desl in (('.uno:Bold', 'CharWeight', 150.0, 100.0), ('.uno:Italic', 'CharPosture', 'ITALIC', 'NONE'),
                                     ('.uno:Underline', 'CharUnderline', 1, 0), ('.uno:Strikeout', 'CharStrikeout', 1, 0)):
            P(lambda c=cmd, p=prop, v=lig: self.efeito_selecao(c, 'beta', p, lambda x, v=v: x == v or getattr(x, 'value', None) == v))
            P(lambda c=cmd, p=prop, v=desl: self.efeito_selecao(c, 'beta', p, lambda x, v=v: x == v or getattr(x, 'value', None) == v, False))
        P(lambda: self.efeito_selecao('.uno:SuperScript', 'gama', 'CharEscapement', lambda x: x > 0))
        P(lambda: self.efeito_selecao('.uno:SubScript', 'delta', 'CharEscapement', lambda x: x < 0))
        P(lambda: self.efeito_selecao('.uno:Grow', 'zeta', 'CharHeight', lambda x: x > 12.0))
        P(lambda: self.efeito_selecao('.uno:Shrink', 'eta', 'CharHeight', lambda x: x < 12.0))
        P(lambda: self.efeito_selecao('.uno:Bold', 'iota', 'CharWeight', lambda x: x == 150.0, False))
        P(lambda: self.efeito_selecao('.uno:ResetAttributes', 'iota', 'CharWeight', lambda x: x == 100.0))
        for cmd, val in (('.uno:CenterPara', 3), ('.uno:RightPara', 1), ('.uno:JustifyPara', 2), ('.uno:LeftPara', 0)):
            P(lambda c=cmd, v=val: self.efeito_selecao(c, 'alfa', 'ParaAdjust', lambda x, v=v: int(x) == v))
        P(lambda: self.efeito_selecao('.uno:IncrementIndent', 'alfa', 'ParaLeftMargin', lambda x: x > 0))
        P(lambda: self.efeito_selecao('.uno:DecrementIndent', 'alfa', 'ParaLeftMargin', lambda x: x == 0))
        P(lambda: self.efeito_selecao('.uno:DefaultBullet', 'alfa', 'NumberingIsNumber', lambda x: bool(x)))
        P(lambda: self.efeito_selecao('.uno:DefaultBullet', 'alfa', 'NumberingIsNumber', lambda x: not x, False))
        P(lambda: self.efeito_selecao('.uno:DefaultNumbering', 'alfa', 'NumberingIsNumber', lambda x: bool(x)))
        P(lambda: self.efeito_selecao('.uno:DefaultNumbering', 'alfa', 'NumberingIsNumber', lambda x: not x, False))
        P(lambda: self.efeito_vista('.uno:ControlCodes', 'ShowNonprintingCharacters'))
        P(lambda: self.efeito_vista('.uno:ControlCodes', 'ShowNonprintingCharacters', False))
        P(lambda: self.efeito_contagem('.uno:InsertPagebreak', 'paginas', 1))
        P(lambda: self.efeito_contagem('ayescreva:PaginaEmBranco', 'paginas', 2))
        P(lambda: self.efeito_contagem('.uno:InsertAnnotation', 'comentarios', 1, aba='inserir'))
        P(lambda: self.efeito_contagem('.uno:InsertFootnote', 'notasRodape', 1))
        P(lambda: self.efeito_contagem('.uno:InsertEndnote', 'notasFim', 1))
        P(lambda: self.efeito_doc('.uno:TrackChanges', 'RecordChanges', lambda x: bool(x)))
        P(lambda: self.efeito_doc('.uno:TrackChanges', 'RecordChanges', lambda x: not x, False))
        P(lambda: self.efeito_vista('.uno:Ruler', 'ShowRulers'))
        P(lambda: self.efeito_vista('.uno:Ruler', 'ShowRulers', False))
        P(lambda: self.efeito_zoom('.uno:ZoomPage', lambda v: v.ZoomType == 2))
        P(lambda: self.efeito_zoom('.uno:Zoom100Percent', lambda v: v.ZoomValue == 100))
        P(lambda: self.efeito_zoom('.uno:ZoomPageWidth', lambda v: v.ZoomType in (1, 4)))
        for cmd, nome in (('ayescreva:Guia', 'guia.html'), ('ayescreva:Atalhos', 'atalhos.html'),
                          ('ayescreva:Limitacoes', 'limitacoes.html'), ('ayescreva:Recuperacao', 'backup')):
            P(lambda c=cmd, n=nome: self.efeito_log(c, n))
        P(self.efeito_diagnostico)
        for b in self.mapa['botoes']:
            if self.aba_info(b['aba'])['contextual'] or b['comando'] in NAO_ACIONAR:
                continue
            P(lambda b=b: self.acionar_generico(b))
        P(lambda: self.fechar_outras_janelas())   # volta ao documento do teste antes das abas contextuais
        P(self.contexto_tabela)
        P(self.contexto_imagem)
        P(self.efeito_salvar_odt)
        # O aviso de fontes e o aviso de perdas ao salvar DOCX rodam na fase 2 (tests/interface/testar_faixa.ps1)
        return passos

    # ---------- verificações ------------------------------------------------------------------
    def conferir_aba(self, a):
        if not a['contextual']:
            self.selecionar_aba(a['id'])
            self.esperar(0.3)
        p = self.principal()
        filhos = set(p.getChildren())
        pagina = 'pagina-' + a['id']
        existe = pagina in filhos
        visivel = existe and _estado(p.getChild(pagina)).get('ReallyVisible') == 'true'
        self.res['abas'].append({'posicao': a['posicao'], 'rotulo': a['rotulo'], 'paginaExiste': existe, 'paginaVisivelAgora': visivel})
        for b in [x for x in self.mapa['botoes'] if x['aba'] == a['id']]:
            ch = self.chave(b)
            if b['caixa'] not in filhos:
                self.registro(ch)['detalhes'].append('caixa de botões não encontrada na janela')
                continue
            st = _estado(p.getChild(b['caixa']))
            if int(st.get('ItemCount', '0')) > b['posicao']:
                self.registrar(ch, 'presente', f"na aba {a['rotulo']} (caixa {b['caixa']}, item {b['posicao']})")
            else:
                self.registro(ch)['detalhes'].append(f"caixa {b['caixa']} sem o item {b['posicao']}")

    def resultado(self, b, ok, detalhe, disparado, registrar=True):
        if not registrar:
            return
        ch = self.chave(b)
        self.res['efeitos'].append({'funcao': ch, 'ok': bool(ok), 'detalhe': detalhe, 'comandoDisparado': disparado})
        if disparado == b['comando']:
            self.registrar(ch, 'acionado', 'clique na faixa disparou ' + disparado)
            if ok:
                self.registrar(ch, 'validado', detalhe)

    def preparar_texto(self):
        t = self.doc.Text
        t.setString('')
        cur = t.createTextCursor()
        t.insertString(cur, 'alfa beta gama delta épsilon zeta eta teta iota capa lambda mi', False)
        t.insertControlCharacter(cur, 0, False)
        t.insertString(cur, 'Segundo parágrafo para os testes da faixa.', False)
        self.selecionar_texto('alfa')

    def efeito_selecao(self, cmd, trecho, prop, cond, registrar=True):
        b = self.botao(cmd)
        self.selecionar_texto(trecho)
        disparado = self.clicar(b)
        self.esperar(0.8)
        v = self.selecionar_texto(trecho).getPropertyValue(prop)
        self.resultado(b, cond(v), f'{prop}={getattr(v, "value", v)} depois do clique', disparado, registrar)

    def contar(self, oque):
        if oque == 'paginas':
            return self.ctrl.getPropertyValue('PageCount')
        if oque == 'comentarios':
            e = self.doc.TextFields.createEnumeration()
            n = 0
            while e.hasMoreElements():
                if e.nextElement().supportsService('com.sun.star.text.textfield.Annotation'):
                    n += 1
            return n
        return {'notasRodape': self.doc.Footnotes.Count, 'notasFim': self.doc.Endnotes.Count}[oque]

    def efeito_contagem(self, cmd, oque, delta, aba=None):
        b = self.botao(cmd, aba)
        self.selecionar_texto('lambda')
        self.ctrl.getViewCursor().collapseToEnd()
        antes = self.contar(oque)
        disparado = self.clicar(b)
        self.esperar(1.5)
        depois = self.contar(oque)
        self.resultado(b, depois - antes >= delta, f'{oque}: {antes} → {depois}', disparado)
        self.selecionar_texto('alfa')

    def efeito_doc(self, cmd, prop, cond, registrar=True):
        b = self.botao(cmd)
        disparado = self.clicar(b)
        self.esperar(0.8)
        v = self.doc.getPropertyValue(prop)
        self.resultado(b, cond(v), f'{prop}={v}', disparado, registrar)

    def efeito_vista(self, cmd, prop, registrar=True):
        b = self.botao(cmd)
        antes = self.ctrl.getViewSettings().getPropertyValue(prop)
        disparado = self.clicar(b)
        self.esperar(0.8)
        depois = self.ctrl.getViewSettings().getPropertyValue(prop)
        self.resultado(b, antes != depois, f'{prop}: {antes} → {depois}', disparado, registrar)

    def efeito_zoom(self, cmd, cond):
        b = self.botao(cmd)
        disparado = self.clicar(b)
        self.esperar(0.8)
        vs = self.ctrl.getViewSettings()
        self.resultado(b, cond(vs), f'ZoomType={vs.ZoomType} ZoomValue={vs.ZoomValue}', disparado)

    def _log_ay(self):
        try:
            return open(os.path.join(os.environ.get('TEMP', '.'), 'ayescreva-extensao.log'), encoding='utf-8').read()
        except Exception:
            return ''

    def efeito_log(self, cmd, trecho):
        b = self.botao(cmd)
        antes = len(self._log_ay())
        disparado = self.clicar(b)
        self.esperar(0.8)
        novo = self._log_ay()[antes:]
        ok = 'abrir:' in novo and trecho in novo and '(existe)' in novo
        self.resultado(b, ok, f'abriria {trecho} (arquivo existe; abertura simulada no teste)' if ok else novo.strip()[-200:], disparado)

    def efeito_diagnostico(self):
        b = self.botao('ayescreva:Diagnostico')
        subst = self.smgr.createInstanceWithContext('com.sun.star.util.PathSubstitution', self.ctx)
        alvo = os.path.join(uno.fileUrlToSystemPath(subst.substituteVariables('$(user)', True)), 'diagnostico-ay-escreva.txt')
        if os.path.exists(alvo):
            os.remove(alvo)
        disparado = self.clicar(b)
        self.esperar(1.5)
        ok = os.path.exists(alvo) and 'relatório de diagnóstico' in open(alvo, encoding='utf-8-sig').read()
        self.resultado(b, ok, 'relatório criado no perfil, sem conteúdo de documentos', disparado)

    def acionar_generico(self, b):
        ch = self.chave(b)
        if self.registro(ch).get('acionado'):
            return
        self.selecionar_texto('alfa')
        antes = len(self.res['dialogos'])
        disparado = self.clicar(b)
        if b['comando'] in ALTERNA_JANELA:
            time.sleep(1.5)
            j, _t = self.janela_extra()
            titulo = _estado(j).get('Text', '') if j is not None else ''
            self.res['dialogos'].append({'funcao': ch, 'titulo': titulo, 'tipo': 'janela não modal'})
            # Aciona o mesmo comando outra vez (alterna a janela) para fechá-la
            desp = self.smgr.createInstanceWithContext('com.sun.star.frame.DispatchHelper', self.ctx)
            desp.executeDispatch(self.frame, b['comando'], '', 0, ())
            time.sleep(0.8)
        self.vigiar(ch)
        if disparado == b['comando']:
            self.registrar(ch, 'acionado', 'clique na faixa disparou ' + disparado)
        else:
            self.registro(ch)['detalhes'].append(f'clique disparou "{disparado}" (esperado {b["comando"]})')
        novos = [d for d in self.res['dialogos'][antes:] if d['funcao'] == ch]
        if novos:
            self.registrar(ch, 'acionado', f'abriu {novos[0]["tipo"]} "{novos[0]["titulo"]}" (fechado pelo teste)')
        self.fechar_outras_janelas(ch)
        if self.principal() is None:
            self.fechar_janelas_extras('depois do acionamento')
        try:
            self.selecionar_texto('alfa')
        except Exception:
            pass

    def fechar_outras_janelas(self, ch=None):
        """Fecha janelas de documento abertas por um comando (novo documento, licença, etiquetas...) e devolve o
        foco ao documento do teste; sem isso, os cliques seguintes iriam para a faixa da outra janela."""
        quadros = self.desktop.getFrames()
        outros = [quadros.getByIndex(i) for i in range(quadros.getCount())]
        outros = [f for f in outros if f != self.frame]
        if not outros:
            return []
        titulos = []
        for f in outros:
            try:
                titulos.append(f.getTitle())
            except Exception:
                titulos.append('')

        def fechar():
            for f in outros:
                try:
                    ctrl = f.getController()
                    m = ctrl.getModel() if ctrl is not None else None
                    if m is not None and m != self.doc:
                        m.setModified(False)
                        m.close(True)
                    else:
                        f.close(True)      # outra vista do mesmo documento, ou quadro sem documento
                except Exception:
                    _log('fechar janela: ' + traceback.format_exc()[-300:])
            self.frame.activate()
            self.frame.getContainerWindow().setFocus()
        self.postar(fechar)            # na thread principal, como um clique do usuário
        self.esperar(1.5)
        _log(f'janelas abertas por {ch}: {titulos} (fechadas)')
        if ch:
            self.registrar(ch, 'acionado', f'abriu a janela "{titulos[0]}" (fechada pelo teste)')
        return titulos

    def contexto_tabela(self):
        t = self.doc.createInstance('com.sun.star.text.TextTable')
        t.initialize(2, 2)
        self.doc.Text.insertTextContent(self.doc.Text.getEnd(), t, False)
        # Cursor de texto dentro da célula A1 (como o usuário clicando na tabela)
        self.ctrl.getViewCursor().gotoRange(t.getCellByName('A1').getText().getStart(), False)
        self.esperar(1.5)
        ok = self.pagina_visivel('tabela') or self._selecionar_e_ver('tabela')
        self.res['efeitos'].append({'funcao': 'Aba contextual Tabela', 'ok': bool(ok), 'detalhe': 'aparece com o cursor numa tabela'})
        if ok:
            for b in [x for x in self.mapa['botoes'] if x['aba'] == 'tabela']:
                self.registrar(self.chave(b), 'presente', 'aba contextual visível com o cursor na tabela')
            bi = self.botao('.uno:InsertRowsAfter', 'tabela')
            linhas = t.Rows.Count
            disparado = self.clicar(bi)
            self.esperar(2.0)
            _log(f'tabela: linhas {linhas} -> {t.Rows.Count}; cursor na tabela={self.ctrl.getViewCursor().TextTable is not None}')
            self.resultado(bi, t.Rows.Count == linhas + 1, f'linhas: {linhas} → {t.Rows.Count}', disparado)
        self.selecionar_texto('alfa')

    def _selecionar_e_ver(self, id_aba):
        try:
            self.selecionar_aba(id_aba)
            return self.pagina_visivel(id_aba)
        except Exception:
            return False

    def contexto_imagem(self):
        prov = self.smgr.createInstanceWithContext('com.sun.star.graphic.GraphicProvider', self.ctx)
        g = prov.queryGraphic(_props(URL=uno.systemPathToFileUrl(self.spec['imagem'])))
        img = self.doc.createInstance('com.sun.star.text.TextGraphicObject')
        img.Graphic = g
        self.doc.Text.insertTextContent(self.doc.Text.getEnd(), img, False)
        self.ctrl.select(img)
        self.esperar(1.5)
        ok = self.pagina_visivel('imagem') or self._selecionar_e_ver('imagem')
        self.res['efeitos'].append({'funcao': 'Aba contextual Imagem', 'ok': bool(ok), 'detalhe': 'aparece com uma imagem selecionada'})
        if ok:
            for b in [x for x in self.mapa['botoes'] if x['aba'] == 'imagem']:
                self.registrar(self.chave(b), 'presente', 'aba contextual visível com a imagem selecionada')
        self.selecionar_texto('alfa')

    def efeito_salvar_odt(self):
        b = self.botao('.uno:Save')
        caminho = uno.fileUrlToSystemPath(self.doc.getURL())
        self.doc.Text.getEnd().setString(' (alterado pelo teste da faixa)')
        antes = os.path.getmtime(caminho)
        self.esperar(1.1)
        disparado = self.clicar(b)
        self.esperar(2.5)
        _log(f'salvar odt: url={self.doc.getURL()} mtime {antes} -> {os.path.getmtime(caminho)}; modificado={self.doc.isModified()}; somenteLeitura={self.doc.isReadonly()}')
        ok = os.path.getmtime(caminho) > antes and not self.doc.isModified()
        self.resultado(b, ok, 'ODT gravado pelo botão Salvar, sem aviso (formato nativo)', disparado)

    def abrir_docx(self):
        self.doc = self.desktop.loadComponentFromURL(uno.systemPathToFileUrl(self.spec['docx']), '_blank', 0, _props(Hidden=False))
        self.ctrl = self.doc.getCurrentController()
        self.frame = self.ctrl.getFrame()
        self.aba_atual = None
        self.esperar(2.0)
        # Leva o foco para a janela do DOCX (a janela anterior pode continuar com o foco)
        for _ in range(5):
            try:
                self.frame.activate()
                self.frame.getContainerWindow().setFocus()
                self.frame.getComponentWindow().setFocus()
            except Exception:
                pass
            self.esperar(0.6)
            titulo = _estado(self.topo()).get('Text', '')
            if 'compatibilidade' in titulo:
                break
        _log(f'janela em foco após abrir o DOCX: {titulo!r}')

    def verificar_aviso_fontes(self):
        ok = bool(self.ctrl.hasInfobar('ay-fontes'))
        self.res['efeitos'].append({'funcao': 'Aviso de substituição de fontes', 'ok': ok, 'detalhe': 'faixa "Fontes substituídas" exibida ao abrir o DOCX'})

    def efeito_salvar_docx(self):
        b = self.botao('.uno:Save')
        caminho = uno.fileUrlToSystemPath(self.doc.getURL())
        copia_odt = caminho.rsplit('.', 1)[0] + '.odt'
        if os.path.exists(copia_odt):
            os.remove(copia_odt)
        antes = os.path.getmtime(caminho)
        self.doc.Text.getEnd().setString(' (alterado)')
        self.esperar(1.1)
        visto = {}

        def anotar(j):
            visto['titulo'] = _estado(j).get('Text', '')
            _log(f'salvar docx: diálogo "{visto["titulo"]}"')
        _log('salvar docx: clique')
        disparado = self.clicar(b)
        _log(f'salvar docx: clicado ({disparado})')
        # Botão padrão do diálogo do AY: "Salvar em DOCX" (cópia em ODT marcada)
        self.responder_dialogo('Arquivo › Salvar (DOCX)', 8.0, 'formato', anotar)
        self.esperar(5.0)
        gravou = os.path.getmtime(caminho) > antes
        ok = visto.get('titulo', '').startswith('Salvar em DOCX') and gravou and os.path.exists(copia_odt)
        self.res['efeitos'].append({'funcao': 'Aviso de perdas ao salvar em DOCX', 'ok': bool(ok), 'comandoDisparado': disparado,
                                    'detalhe': f"diálogo \"{visto.get('titulo')}\"; DOCX gravado={gravou}; cópia ODT={os.path.exists(copia_odt)}"})

    def efeito_fechar_docx(self):
        """Fecha o DOCX alterado pela faixa e escolhe Salvar na pergunta; registra qual aviso de formato aparece."""
        b = self.botao('.uno:CloseDoc')
        caminho = uno.fileUrlToSystemPath(self.doc.getURL())
        antes = os.path.getmtime(caminho)
        self.doc.Text.getEnd().setString(' (alterado antes de fechar)')
        self.esperar(1.1)
        vistos = []

        def anotar(j):
            vistos.append(_estado(j).get('Text', ''))
            _log(f'fechar docx: diálogo "{vistos[-1]}"')
        _log('fechar docx: clique')
        self.clicar(b)
        _log('fechar docx: clicado')
        self.responder_dialogo('Arquivo › Fechar (DOCX alterado)', 8.0, 'save', anotar)
        _log('fechar docx: pergunta respondida')
        # Depois de "Salvar": aviso do AY (lista de perdas) ou aviso genérico do motor (manter formato)
        self.responder_dialogo('Arquivo › Fechar › Salvar (DOCX)', 6.0, 'save', anotar)
        self.esperar(5.0)
        gravou = os.path.getmtime(caminho) > antes
        aviso = vistos[1] if len(vistos) > 1 else ''
        try:
            self.doc.getURL()
            fechou = False
        except Exception:
            fechou = True       # modelo descartado: a janela fechou depois de salvar
        self.res['efeitos'].append({'funcao': 'Aviso de formato ao fechar e salvar DOCX', 'ok': bool(gravou and aviso and fechou),
                                    'detalhe': f'diálogos: {vistos}; DOCX gravado={gravou}; documento fechado={fechou}; aviso de formato="{aviso}"'})

    def concluir(self):
        self.res['fim'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        with open(self.saida, 'w', encoding='utf-8') as f:
            json.dump(self.res, f, ensure_ascii=False, indent=2)
        _log('concluído')
        comps = self.desktop.getComponents().createEnumeration()
        while comps.hasMoreElements():
            c = comps.nextElement()
            try:
                c.setModified(False)
            except Exception:
                pass
        self.postar(lambda: self.desktop.terminate())


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(Executor, 'br.ayescreva.testes.Executor', ('com.sun.star.task.Job',))
