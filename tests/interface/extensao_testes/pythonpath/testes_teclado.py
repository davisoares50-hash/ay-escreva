# -*- coding: utf-8 -*-
"""Navegação só pelo teclado, com teclas reais do Windows (como uma pessoa), na faixa de opções e nos diálogos.

O foco é lido pela árvore de acessibilidade do próprio motor (UNO): o mesmo dado que um leitor de tela recebe, mas
lido de dentro do aplicativo. Isso confere nome e papel do controle focado; NÃO é um teste com leitor de tela.
Foco visível: capturas da janela em cada etapa (tests/output/interface/teclado-*.png), conferidas visualmente.
SPDX-License-Identifier: MPL-2.0
"""
import os
import time
import traceback

import uno

VK = {'F6': 0x75, 'TAB': 0x09, 'ESC': 0x1B, 'ESPACO': 0x20, 'ENTER': 0x0D, 'DIREITA': 0x27, 'ESQUERDA': 0x25,
      'SHIFT': 0x10, 'CTRL': 0x11, 'K': 0x4B, 'ALT': 0x12}


def _log(msg):
    try:
        with open(os.path.join(os.environ.get('TEMP', '.'), 'ay-testes-ui.log'), 'a', encoding='utf-8') as f:
            f.write(time.strftime('%H:%M:%S ') + 'teclado: ' + msg + chr(10))
    except Exception:
        pass


class TecladoMixin:
    # ---------- foco: estado dos controles no UITest (HasFocus) ---------------------------------------
    def _foco(self):
        """(tipo, nome, id) do controle com foco na janela ativa, ou None. Lê o estado "HasFocus" que o UITest informa
        para cada controle (só leitura, sem entrada simulada); na faixa, o nome é o do botão realçado pelo teclado e o da
        aba aberta. Não é o canal do leitor de tela (os nomes acessíveis são conferidos nas fases 5, 8, 9 e 10)."""
        try:
            t = self.ui.getTopFocusWindow()
            filhos = list(t.getChildren())
        except Exception:
            return None
        ids = set(filhos)
        if 'ContextContainer' in ids:
            # janela do documento: abas da faixa, caixas de botões (as do mapa) e o texto, consultados pelo nome
            # "HasFocus" do contêiner das abas continua verdadeiro com o foco num botão dentro dele: o texto e as caixas de
            # botões são consultados antes; as abas só valem se nada dentro delas tem o foco
            for cid in ['writer_edit'] + sorted({b['caixa'] for b in self.mapa['botoes']}) + ['ContextContainer']:
                if cid not in ids:
                    continue
                try:
                    st = {p.Name: p.Value for p in t.getChild(cid).getState()}
                except Exception:
                    continue
                if st.get('HasFocus') == 'true':
                    if cid == 'writer_edit':
                        return ('DOCUMENT', 'texto do documento', cid)
                    if cid == 'ContextContainer':
                        # outro controle da aba (caixa de fonte, de estilo...) com o foco dentro das abas?
                        for outro in filhos:
                            if outro in ('ContextContainer', 'writer_edit') or outro.startswith(('pagina-', 'grupos-', 'box', 'grid', 'grp', 'pilha', 'lbl')):
                                continue
                            try:
                                so = {p.Name: p.Value for p in t.getChild(outro).getState()}
                            except Exception:
                                continue
                            if so.get('HasFocus') == 'true' and so.get('ReallyVisible') == 'true':
                                return ('CONTROLE', so.get('Text') or outro, outro)
                        return ('PAGE_TAB', 'aba ' + self._aba_visivel(t, ids), cid)
                    return ('TOOL_BAR', st.get('CurrSelectedItemText') or st.get('CurrSelectedItemCommand') or cid, cid)
        else:
            ay = self._foco_dialogo_ay()
            if ay:
                return ay
        achado = None
        for cid in filhos:
            try:
                st = {p.Name: p.Value for p in t.getChild(cid).getState()}
            except Exception:
                continue
            if st.get('HasFocus') != 'true':
                continue
            if achado and cid in ('tabcontrol', 'box', 'grid') :
                continue                      # contêiner com um controle já achado dentro: fica o controle
            if cid == 'writer_edit':
                achado = ('DOCUMENT', 'texto do documento', cid)
            elif cid == 'ContextContainer':
                achado = ('PAGE_TAB', st.get('CurrPageTitel') or st.get('CurrPageTitle') or st.get('CurrPageId') or 'abas da faixa', cid)
            elif 'CurrSelectedItemText' in st or 'CurrSelectedItemCommand' in st:
                achado = ('TOOL_BAR', st.get('CurrSelectedItemText') or st.get('CurrSelectedItemCommand') or cid, cid)
            else:
                achado = ('CONTROLE', st.get('Text') or st.get('DisplayText') or cid, cid)
        return achado

    def _aba_visivel(self, t, ids):
        for a in self.mapa['abas']:
            pid = 'pagina-' + a['id']
            if pid in ids:
                try:
                    if {p.Name: p.Value for p in t.getChild(pid).getState()}.get('ReallyVisible') == 'true':
                        return a['rotulo']
                except Exception:
                    pass
        return '?'

    def _foco_dialogo_ay(self):
        """Diálogos do AY são feitos com controles UNO, que o UITest não enxerga por dentro: o foco vem do próprio
        controle (hasFocus), com o nome acessível dele."""
        def f():
            import ay_dialogos
            for d in list(ay_dialogos.ATUAL):
                dlg = getattr(d, 'dlg', None)
                if dlg is None:
                    continue
                for c in dlg.getControls():
                    try:
                        if c.hasFocus():
                            nome = ''
                            try:
                                nome = c.getAccessibleContext().getAccessibleName()
                            except Exception:
                                pass
                            return ('CONTROLE', nome or c.getModel().Name, c.getModel().Name)
                    except Exception:
                        pass
            return None
        try:
            return self.no_principal(f, 15)
        except Exception:
            return None

    def _papel(self, n):
        if not hasattr(self, '_papeis'):
            self._papeis = {}
            for nome in ('PUSH_BUTTON', 'TOGGLE_BUTTON', 'PAGE_TAB', 'PAGE_TAB_LIST', 'TOOL_BAR', 'PANEL', 'DOCUMENT', 'DOCUMENT_TEXT',
                         'PARAGRAPH', 'TEXT', 'COMBO_BOX', 'LIST', 'LIST_ITEM', 'CHECK_BOX', 'RADIO_BUTTON', 'MENU_ITEM', 'MENU',
                         'DIALOG', 'FRAME', 'BUTTON_DROPDOWN', 'BUTTON_MENU', 'TREE', 'TREE_ITEM', 'SPIN_BOX', 'LABEL',
                         'ROOT_PANE', 'TABLE', 'TABLE_CELL', 'SCROLL_PANE', 'EDIT_BAR', 'NOTIFICATION', 'WINDOW', 'FILLER',
                         'GROUP_BOX', 'TEXT_FRAME', 'ICON', 'TOOL_TIP', 'ALERT'):
                try:
                    self._papeis[uno.getConstantByName('com.sun.star.accessibility.AccessibleRole.' + nome)] = nome
                except Exception:
                    pass
        return self._papeis.get(n, str(n))

    def _captura_janela(self, nome):
        try:
            titulo = self.no_principal(lambda: self.frame.getTitle())
            return self._capturar(titulo, 'teclado-' + nome)
        except Exception:
            return False

    def _pressionar(self, *teclas, vezes=1, pausa=0.35):
        for _ in range(vezes):
            if not self._teclas_reais(*[VK[t] for t in teclas]):
                return False
            time.sleep(pausa)
        return True

    # ---------- faixa de opções ----------------------------------------------------------------
    def teclado_faixa(self):
        if self.tela_bloqueada():
            self.efeito('Teclado (teclas reais): faixa de opções (F6, setas, Tab, Espaço, Esc)', False, 'BLOQUEADO: a tela do Windows estava bloqueada; teclas reais não '
                        'chegam a nenhum programa. Rodar de novo com a sessão desbloqueada.')
            return
        reg = self.res.setdefault('teclado', {})
        self.selecionar_texto('beta')
        self.no_principal(lambda: self.frame.getContainerWindow().setFocus())
        time.sleep(0.5)
        reg['inicio'] = self._foco()
        # F6: do documento para a faixa (e para as outras áreas da janela, em ciclo)
        ciclo = []
        na_faixa = None
        for i in range(8):
            if not self._pressionar('F6'):
                break
            fo = self._foco()
            ciclo.append(fo)
            if na_faixa is None and fo and fo[0] in ('PAGE_TAB', 'PAGE_TAB_LIST'):
                na_faixa = i + 1
                break
        reg['f6_ciclo'] = ciclo
        reg['f6_ate_faixa'] = na_faixa
        self._captura_janela('1-f6-aba')
        self.efeito('Teclado (teclas reais): F6 leva o foco do documento às abas da faixa', na_faixa is not None,
                    f'{na_faixa} toque(s) em F6; foco: {ciclo[-1] if ciclo else None}; caminho: {ciclo}'
                    + (f'; leitura do foco: {self.__dict__.get("_foco_diag", [])[:4]}' if na_faixa is None else ''))
        if na_faixa is None:
            self._pressionar('ESC')
            return
        # setas entre abas
        abas = []
        for _ in range(2):
            self._pressionar('DIREITA')
            abas.append(self._foco())
        for _ in range(2):
            self._pressionar('ESQUERDA')
        abas.append(self._foco())
        reg['setas_abas'] = abas
        self.efeito('Teclado (teclas reais): setas passam de uma aba para outra e voltam', len({a for a in abas if a}) >= 2,
                    f'abas com foco: {abas}')
        # Tab entra nos botões da aba aberta; procura "Negrito" e aciona com Espaço
        caminho, achou = [], None
        for i in range(70):
            self._pressionar('TAB', pausa=0.25)
            fo = self._foco()
            caminho.append(fo)
            if fo and 'negrito' in fo[1].lower():
                achou = i + 1
                break
        reg['tab_ate_negrito'] = caminho
        self._captura_janela('2-tab-negrito')
        antes = self.no_principal(lambda: self._selecionar('beta').CharWeight)
        if achou:
            self._pressionar('ESPACO')
            time.sleep(0.6)
        depois = self.no_principal(lambda: self._selecionar_sem_mover('beta').CharWeight)
        self.efeito('Teclado (teclas reais): Tab percorre os botões da aba e Espaço aciona "Negrito" no texto selecionado',
                    bool(achou) and depois == 150.0 and antes != 150.0,
                    f'{achou} toque(s) em Tab até "Negrito"; peso da fonte {antes} → {depois}; ordem: '
                    + ', '.join(f'{x[1]}' for x in caminho[:25] if x))
        # Esc volta ao documento
        self._pressionar('ESC')
        time.sleep(0.4)
        fo = self._foco()
        if fo and fo[0] not in ('DOCUMENT', 'DOCUMENT_TEXT', 'PARAGRAPH'):
            self._pressionar('ESC')
            fo = self._foco()
        reg['esc_volta'] = fo
        self.efeito('Teclado (teclas reais): Esc devolve o foco da faixa ao documento',
                    bool(fo) and fo[0] in ('DOCUMENT', 'DOCUMENT_TEXT', 'PARAGRAPH'), f'foco depois do Esc: {fo}')

    def _selecionar_sem_mover(self, trecho):
        b = self.doc.createSearchDescriptor()
        b.SearchString = trecho
        return self.doc.findFirst(b)

    # ---------- diálogos: foco inicial, ordem, saída com Esc ------------------------------------------
    def teclado_dialogos(self):
        if self.tela_bloqueada():
            self.efeito('Teclado (teclas reais): diálogos (foco inicial, Tab, Shift+Tab, Esc)', False, 'BLOQUEADO: a tela do Windows estava bloqueada; teclas reais não '
                        'chegam a nenhum programa. Rodar de novo com a sessão desbloqueada.')
            return
        dialogos = [('Formatar trabalho acadêmico', 'ayescreva:FormatarTrabalho'), ('Galeria de modelos', 'ayescreva:Galeria'),
                    ('Verificar atualizações', 'ayescreva:VerificarAtualizacoes'), ('Conferir referências', 'ayescreva:ConferirReferencias'),
                    ('Propriedades do documento', '.uno:SetDocumentProperties'), ('Caractere', '.uno:FontDialog'),
                    ('Parágrafo', '.uno:ParagraphDialog'), ('Link (Ctrl+K)', None), ('Inserir tabela', '.uno:InsertTable')]
        reg = self.res.setdefault('teclado', {}).setdefault('dialogos', {})
        for i, (nome, cmd) in enumerate(dialogos, 1):
            try:
                self.selecionar_texto('alfa')
                self.no_principal(lambda: self.frame.getContainerWindow().setFocus())
                time.sleep(0.3)
                if cmd:
                    self._abrir_async(cmd)
                else:
                    self._pressionar('CTRL', 'K')
                time.sleep(2.5)
                j, tipo = self.janela_extra()
                if j is None:
                    reg[nome] = {'abriu': False}
                    self.efeito(f'Teclado (teclas reais) em "{nome}": diálogo abre', False, 'o diálogo não abriu')
                    continue
                inicial = self._foco()
                ordem = [inicial]
                for _ in range(4):
                    self._pressionar('TAB', pausa=0.3)
                    ordem.append(self._foco())
                self._pressionar('SHIFT', 'TAB', pausa=0.3)
                volta = self._foco()
                if i <= 3:
                    self._capturar(_estado_titulo(j), f'teclado-dialogo-{i}')
                self._pressionar('ESC')
                time.sleep(1.2)
                j2, _t = self.janela_extra()
                fechou = j2 is None
                if not fechou:            # alguns diálogos levam o primeiro Esc a uma lista aberta: segundo Esc
                    self._pressionar('ESC')
                    time.sleep(1.0)
                    fechou = self.janela_extra()[0] is None
                depois = self._foco()
                distintos = len({o for o in ordem if o})
                reg[nome] = {'inicial': inicial, 'ordem': ordem, 'shift_tab': volta, 'fechou_com_esc': fechou, 'foco_depois': depois}
                self.efeito(f'Teclado (teclas reais) em "{nome}": foco inicial num controle, Tab avança, Shift+Tab volta, '
                            'Esc fecha e devolve o foco ao documento',
                            bool(inicial and inicial[1]) and distintos >= 3 and volta == ordem[-2] and fechou
                            and bool(depois) and depois[0] in ('DOCUMENT', 'DOCUMENT_TEXT', 'PARAGRAPH'),
                            f'inicial {inicial}; ordem {[o[1] if o else None for o in ordem]}; Shift+Tab → {volta}; '
                            f'Esc fechou: {fechou}; foco depois: {depois}')
            except Exception:
                reg[nome] = {'erro': traceback.format_exc()[-400:]}
                _log(f'{nome}: ' + traceback.format_exc()[-400:])
            self.fechar_janelas_extras('depois do teste de teclado')
            self.fechar_outras_janelas()


def _estado_titulo(j):
    try:
        return {p.Name: p.Value for p in j.getState()}.get('Text', '')
    except Exception:
        return ''
