# -*- coding: utf-8 -*-
"""Diagnóstico da queda do motor "Galeria do Fontwork e depois Link" (RESULTADOS §9).

Cada variação roda num aplicativo novo (testar_faixa.ps1 -Somente diag_…), porque uma queda encerra o processo.
As janelas são abertas por despacho de comando (sem clicar na faixa), salvo indicação, e fechadas com Esc pelo robô do
toolkit; no fim, o passo registra se o motor continua respondendo.
SPDX-License-Identifier: MPL-2.0
"""
import os
import time

import uno

ESC, ENTER = 1281, 1280


def _log(msg):
    try:
        with open(os.path.join(os.environ.get('TEMP', '.'), 'ay-testes-ui.log'), 'a', encoding='utf-8') as f:
            f.write(time.strftime('%H:%M:%S ') + msg + chr(10))
    except Exception:
        pass


def _titulo(j):
    try:
        return {p.Name: p.Value for p in j.getState()}.get('Text', '')
    except Exception:
        return ''


class DiagnosticoMixin:
    def _vivo(self):
        try:
            return self.no_principal(lambda: self.doc.getText() is not None, 15)
        except Exception:
            return False

    def _tecla_topo(self, codigo):
        tk = self.smgr.createInstanceWithContext('com.sun.star.awt.Toolkit', self.ctx)
        self.tecla_robo(codigo, tk.getActiveTopWindow())

    def _abrir_e_fechar(self, comando, espera=2.0, tecla=ESC, rotulo=None):
        self.selecionar_texto('alfa')
        _log(f'diag: despacha {comando}')
        self._abrir_async(comando)
        time.sleep(espera)
        j, tipo = self.janela_extra()
        titulo = _titulo(j) if j is not None else ''
        _log(f'diag: {rotulo or comando} abriu {tipo} "{titulo}"; fecha com {"Esc" if tecla == ESC else "Enter"}')
        self._tecla_topo(tecla)
        time.sleep(espera)
        _log(f'diag: {comando} fechado')
        return titulo

    def _diag(self, nome, passos):
        self._diag_problemas = []
        for p in passos:
            p()
        time.sleep(2)
        vivo = self._vivo()
        _log(f'diag {nome}: motor {"respondendo" if vivo else "NÃO responde"}; problemas: {self._diag_problemas}')
        self.efeito(f'Diagnóstico {nome}: o motor continua respondendo', vivo and not self._diag_problemas,
                    '; '.join(self._diag_problemas) or f'{len(passos)} janelas abertas e fechadas')

    # variações
    def diag_despacho(self):
        self._diag('Fontwork → Link (despacho de comando)', [
            lambda: self._abrir_e_fechar('.uno:FontworkGalleryFloater'), lambda: self._abrir_e_fechar('.uno:HyperlinkDialog')])

    def diag_espera_longa(self):
        self._diag('Fontwork → 10 s → Link', [
            lambda: self._abrir_e_fechar('.uno:FontworkGalleryFloater', espera=10), lambda: self._abrir_e_fechar('.uno:HyperlinkDialog')])

    def diag_inserir_fontwork(self):
        self._diag('Fontwork inserido (Enter) → Link', [
            lambda: self._abrir_e_fechar('.uno:FontworkGalleryFloater', tecla=ENTER), lambda: self._abrir_e_fechar('.uno:HyperlinkDialog')])

    def diag_outro_dialogo(self):
        self._diag('Fontwork → Inserir tabela → Propriedades', [
            lambda: self._abrir_e_fechar('.uno:FontworkGalleryFloater'), lambda: self._abrir_e_fechar('.uno:InsertTable'),
            lambda: self._abrir_e_fechar('.uno:SetDocumentProperties')])

    def diag_link_antes(self):
        self._diag('Link → Fontwork → Link', [
            lambda: self._abrir_e_fechar('.uno:HyperlinkDialog'), lambda: self._abrir_e_fechar('.uno:FontworkGalleryFloater'),
            lambda: self._abrir_e_fechar('.uno:HyperlinkDialog')])

    def diag_fontwork_duas(self):
        self._diag('Fontwork → Fontwork', [
            lambda: self._abrir_e_fechar('.uno:FontworkGalleryFloater'), lambda: self._abrir_e_fechar('.uno:FontworkGalleryFloater')])

    def diag_galeria_link(self):
        self._diag('Galeria de imagens (Gallery) → Link', [
            lambda: self._abrir_e_fechar('.uno:Gallery'), lambda: self._abrir_e_fechar('.uno:HyperlinkDialog')])

    def diag_fontwork_editar_link(self):
        self._diag('Fontwork → Editar hiperlink (outro comando de link)', [
            lambda: self._abrir_e_fechar('.uno:FontworkGalleryFloater'), lambda: self._abrir_e_fechar('.uno:EditHyperlink')])

    def _galeria_repetida(self, nome, fechar, vezes=5):
        def ciclo():
            for i in range(vezes):
                _log(f'diag: galeria {i + 1}/{vezes}')
                fechar()
        self._diag(nome, [ciclo, lambda: time.sleep(4), lambda: self._abrir_e_fechar('.uno:SetDocumentProperties')])

    def diag_galeria_esc5(self):
        self._galeria_repetida('Galeria do Fontwork 5 vezes, Esc', lambda: self._abrir_e_fechar('.uno:FontworkGalleryFloater'))

    def diag_galeria_cancelar5(self):
        def cancelar():
            self.selecionar_texto('alfa')
            self._abrir_async('.uno:FontworkGalleryFloater')
            time.sleep(2)
            j, tipo = self.janela_extra()
            filhos = set(j.getChildren()) if j is not None else set()
            _log(f'diag: galeria aberta ({tipo}); botões: {sorted(b for b in filhos if "cancel" in b.lower() or b in ("ok", "close"))}')
            if 'cancel' in filhos:
                j.getChild('cancel').executeAction('CLICK', ())
            time.sleep(2)
            _log('diag: galeria fechada por Cancelar')
        self._galeria_repetida('Galeria do Fontwork 5 vezes, Cancelar', cancelar)

    def diag_galeria_inserir5(self):
        self._galeria_repetida('Galeria do Fontwork 5 vezes, Enter (insere)',
                               lambda: self._abrir_e_fechar('.uno:FontworkGalleryFloater', tecla=ENTER))

    def diag_api_fontwork(self):
        """Estilos do Fontwork pela API da galeria (sem a janela da galeria) e cópia de um deles para o documento."""
        import uno
        from com.sun.star.beans import NamedValue

        def explorar():
            arg = NamedValue()
            arg.Name, arg.Value = 'ProvideHiddenThemes', True
            prov = self.smgr.createInstanceWithArgumentsAndContext('com.sun.star.gallery.GalleryThemeProvider', (arg,), self.ctx)
            achados = []
            for nome in prov.getElementNames():
                tema = prov.getByName(nome)
                tipos = [tema.getByIndex(i).GalleryItemType for i in range(tema.getCount())]
                achados.append(f'{nome}={tema.getCount()} (desenhos {tipos.count(3)})')
            _log('diag: temas ' + '; '.join(achados))
            tema = next((prov.getByName(n) for n in prov.getElementNames() if 'fontwork' in n.lower()), None)
            if tema is None:
                return 'sem tema fontwork'
            item = tema.getByIndex(0)
            info = [f'{k}={getattr(item, k, None)!r}'[:80] for k in ('GalleryItemType', 'URL', 'Title')]
            desenho = item.Drawing
            _log(f'diag: item 0 {info}; desenho {desenho is not None}; miniatura {item.Thumbnail is not None}')
            if desenho is None:
                return 'item sem desenho'
            pag = desenho.getDrawPages().getByIndex(0)
            forma = pag.getByIndex(0)
            _log(f'diag: forma {forma.getShapeType()} tamanho {forma.Size.Width}x{forma.Size.Height}')
            nova = self.doc.createInstance('com.sun.star.drawing.CustomShape')
            nova.Size = forma.Size
            self.doc.Text.insertTextContent(self.doc.Text.getEnd(), nova, False)
            copiadas, falhas = 0, []
            info_dest = nova.getPropertySetInfo()
            for p in forma.getPropertySetInfo().getProperties():
                if p.Attributes & 16 or not info_dest.hasPropertyByName(p.Name):   # READONLY
                    continue
                if p.Name in ('AnchorType', 'AnchorPosition', 'Position', 'ZOrder', 'TextFrames', 'Name', 'NavigationOrder'):
                    continue
                try:
                    nova.setPropertyValue(p.Name, forma.getPropertyValue(p.Name))
                    copiadas += 1
                except Exception as e:
                    falhas.append(p.Name)
            nova.setString('Fontwork')
            geo = {g.Name: g.Value for g in nova.CustomShapeGeometry}
            return f'{tema.getCount()} estilos; forma copiada ({copiadas} propriedades; falharam {falhas[:6]}); tipo {geo.get("Type")}'
        r = self.no_principal(explorar, 60)
        _log(f'diag: API fontwork: {r}')
        self._diag(f'API da galeria do Fontwork ({r})', [lambda: self._abrir_e_fechar('.uno:SetDocumentProperties'),
                                                         lambda: self._abrir_e_fechar('.uno:HyperlinkDialog'),
                                                         lambda: self._abrir_e_fechar('.uno:SetDocumentProperties')])

    # ---------- teclas reais do Windows (como uma pessoa), em vez do robô do motor ou do UITest ----------
    def _primeiro_plano(self):
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        pid = wintypes.DWORD()
        u.GetWindowThreadProcessId(u.GetForegroundWindow(), ctypes.byref(pid))
        return pid.value == os.getpid()

    @staticmethod
    def tela_bloqueada():
        """A sessão do Windows está bloqueada (tela de bloqueio): nenhuma tecla real chega a programa algum."""
        import ctypes
        from ctypes import wintypes
        u, k = ctypes.windll.user32, ctypes.windll.kernel32
        h = u.OpenInputDesktop(0, False, 0x0100)          # DESKTOP_SWITCHDESKTOP: falha na tela de credenciais
        if not h:
            return True
        u.CloseDesktop(h)
        # no Windows 11 a tela de bloqueio (LockApp.exe) fica na mesma área de trabalho, em primeiro plano
        pid = wintypes.DWORD()
        u.GetWindowThreadProcessId(u.GetForegroundWindow(), ctypes.byref(pid))
        hp = k.OpenProcess(0x1000, False, pid.value)       # PROCESS_QUERY_LIMITED_INFORMATION
        if not hp:
            return False
        try:
            buf = ctypes.create_unicode_buffer(520)
            n = wintypes.DWORD(520)
            if k.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(n)):
                return buf.value.lower().endswith('\\lockapp.exe')
        finally:
            k.CloseHandle(hp)
        return False

    @staticmethod
    def _ocioso_s():
        """Segundos desde a última tecla ou movimento de mouse no computador (GetLastInputInfo)."""
        import ctypes

        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_uint)]
        li = LASTINPUTINFO()
        li.cbSize = ctypes.sizeof(li)
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(li)):
            return 0.0
        return ((ctypes.windll.kernel32.GetTickCount() - li.dwTime) & 0xFFFFFFFF) / 1000.0

    def _trazer_para_frente(self):
        """Põe em primeiro plano a janela ativa deste aplicativo (o diálogo aberto, se houver, ou o documento)."""
        import ctypes
        from ctypes import wintypes
        u, k = ctypes.windll.user32, ctypes.windll.kernel32
        janelas = []
        PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def cada(h, _l):
            pid = wintypes.DWORD()
            u.GetWindowThreadProcessId(h, ctypes.byref(pid))
            if pid.value == os.getpid() and u.IsWindowVisible(h) and not u.GetWindow(h, 4):    # GW_OWNER
                janelas.append(h)
            return True
        u.EnumWindows(PROC(cada), 0)
        if not janelas:
            return False
        if u.IsIconic(janelas[0]):
            u.ShowWindow(janelas[0], 9)              # SW_RESTORE: a janela estava minimizada
        alvo = u.GetLastActivePopup(janelas[0]) or janelas[0]
        t_frente = u.GetWindowThreadProcessId(u.GetForegroundWindow(), None)
        t_eu = k.GetCurrentThreadId()
        u.AttachThreadInput(t_eu, t_frente, True)
        try:
            u.SetForegroundWindow(alvo)
            u.BringWindowToTop(alvo)
        finally:
            u.AttachThreadInput(t_eu, t_frente, False)
        _log(f'diag: janela {alvo:#x} trazida para a frente ({len(janelas)} janelas do AY)')
        return True

    def _teclas_reais(self, *vks):
        """Pressiona as teclas (códigos virtuais do Windows) na ordem e solta na ordem inversa, pelo próprio Windows.
        Só envia se a janela em primeiro plano for deste aplicativo (as teclas nunca vão para outro programa)."""
        import ctypes
        u = ctypes.windll.user32
        if self.tela_bloqueada():
            self._bloqueio = True
            _log(f'diag: teclas {vks} NÃO enviadas: a tela do Windows está bloqueada')
            return False
        if not self._primeiro_plano():
            # o AY saiu do primeiro plano: alguém pode estar usando o computador. Só traz o AY de volta depois de
            # 30 s sem teclado e mouse (até 10 min), para não roubar o foco de quem está trabalhando
            fim = time.time() + 600
            avisou = False
            while self._ocioso_s() < 30 and time.time() < fim:
                if not avisou:
                    _log('diag: computador em uso; esperando 30 s sem teclado e mouse para trazer o AY para a frente')
                    avisou = True
                time.sleep(2)
            self._trazer_para_frente()
            time.sleep(0.5)
        if not self._primeiro_plano():
            _log(f'diag: teclas {vks} NÃO enviadas: o AY não está em primeiro plano')
            self.res['avisos'].append('diagnóstico: o AY não estava em primeiro plano; teclas reais não enviadas')
            return False
        for vk in vks:
            u.keybd_event(vk, 0, 0, 0)
            time.sleep(0.05)
        for vk in reversed(vks):
            u.keybd_event(vk, 0, 2, 0)     # KEYEVENTF_KEYUP
            time.sleep(0.05)
        return True

    def _real(self, rotulo, abrir, fechar_vk=0x1B, espera=2.0):
        """Abre, confere que a janela abriu, fecha com a tecla real e confere que fechou. Um passo que não pôde ser
        feito (janela não abriu, teclas não enviadas, janela continuou aberta) vira problema no resultado do passo."""
        self.selecionar_texto('alfa')
        _log(f'diag real: abre {rotulo}')
        abrir()
        time.sleep(espera)
        j, tipo = self.janela_extra()
        _log(f'diag real: {rotulo} abriu {tipo} "{_titulo(j) if j is not None else ""}"; tecla real {fechar_vk:#x}')
        problemas = self.__dict__.setdefault('_diag_problemas', [])
        if j is None:
            problemas.append(f'{rotulo}: a janela não abriu')
            return
        if not self._teclas_reais(fechar_vk):
            problemas.append(f'{rotulo}: teclas reais não enviadas (AY fora do primeiro plano)')
            return
        time.sleep(espera)
        j, tipo = self.janela_extra()
        if j is not None:
            problemas.append(f'{rotulo}: continuou aberta depois da tecla ("{_titulo(j)}")')
        _log(f'diag real: {rotulo} fechado')

    def _link_ctrl_k(self):
        self._teclas_reais(0x11, 0x4B)      # Ctrl+K, atalho do Link no Writer

    def diag_real_fontwork_link(self):
        self._diag('teclas reais: Fontwork, Esc, Ctrl+K, Esc, Propriedades, Esc', [
            lambda: self._real('Galeria do Fontwork', lambda: self._abrir_async('.uno:FontworkGalleryFloater')),
            lambda: self._real('Link (Ctrl+K)', self._link_ctrl_k),
            lambda: self._real('Propriedades', lambda: self._abrir_async('.uno:SetDocumentProperties'))])

    def diag_real_link(self):
        self._diag('teclas reais, sem Fontwork: Ctrl+K, Esc, Propriedades, Esc, Ctrl+K, Esc', [
            lambda: self._real('Link (Ctrl+K)', self._link_ctrl_k),
            lambda: self._real('Propriedades', lambda: self._abrir_async('.uno:SetDocumentProperties')),
            lambda: self._real('Link (Ctrl+K)', self._link_ctrl_k)])

    def diag_robo_link(self):
        self._diag('robô do motor, sem Fontwork: Link, Esc, Propriedades, Esc, Link, Esc', [
            lambda: self._abrir_e_fechar('.uno:HyperlinkDialog'), lambda: self._abrir_e_fechar('.uno:SetDocumentProperties'),
            lambda: self._abrir_e_fechar('.uno:HyperlinkDialog')])

    def diag_real_faixa(self):
        """Como uma pessoa: clique no botão da faixa, Esc real; clique no Link da faixa, Esc real."""
        if self.tela_bloqueada():
            self.efeito('Diagnóstico faixa + teclas reais: Fontwork e Link', False, 'BLOQUEADO: a tela do Windows estava '
                        'bloqueada; teclas reais não chegam a nenhum programa')
            return
        def pela_faixa(comando):
            return lambda: self.clicar(next(x for x in self.mapa['botoes'] if x['comando'] == comando))
        self._diag('faixa + teclas reais: Fontwork, Esc, Link, Esc, Fontwork, Esc, Link, Esc', [
            lambda: self._real('Galeria do Fontwork (faixa)', pela_faixa('.uno:FontworkGalleryFloater')),
            lambda: self._real('Link (faixa)', pela_faixa('.uno:HyperlinkDialog')),
            lambda: self._real('Galeria do Fontwork (faixa)', pela_faixa('.uno:FontworkGalleryFloater')),
            lambda: self._real('Link (faixa)', pela_faixa('.uno:HyperlinkDialog'))])

    # ---------- recuperação depois de uma queda (tests/interface/testar_recuperacao.ps1) ----------
    MARCADOR = 'AY-RECUPERACAO-1 texto digitado e não salvo'
    MARCADOR2 = 'AY-RECUPERACAO-2 digitado depois da cópia automática'

    def _pasta_copias(self):
        ps = self.smgr.createInstanceWithContext('com.sun.star.util.PathSettings', self.ctx)
        return uno.fileUrlToSystemPath(ps.Backup)

    def queda_recuperacao(self):
        """1ª execução: digita um texto sem salvar e provoca a queda do motor (Link fechado pelo robô de teclas, o gatilho
        conhecido). Com "esperar_autosalvamento", espera a cópia automática de recuperação e digita um 2º texto antes da
        queda. 2ª execução (o motor reinicia, ou é aberto de novo, e recupera o documento): confere o que voltou."""
        estado = self.saida + '.primeira'
        texto = self.no_principal(lambda: self.doc.Text.getString())
        if os.path.exists(estado):
            m1, m2 = self.MARCADOR in texto, self.MARCADOR2 in texto
            info = self.no_principal(lambda: (self.doc.getURL(), self.doc.isModified(), self.doc.getTitle()))
            _log(f'diag recuperação: documento reaberto; texto 1: {m1}; texto 2: {m2}; {info}')
            self.res['recuperacao'] = {'texto1': m1, 'texto2': m2, 'documento': info[2], 'modificado': info[1]}
            self.efeito('Recuperação depois da queda: o texto digitado e não salvo voltou', m1,
                        f'texto 1: {"voltou" if m1 else "perdido"}; texto 2: {"voltou" if m2 else "perdido"}; documento {info[2]}')
            return
        open(estado, 'w').close()
        self.no_principal(lambda: self.doc.Text.insertString(self.doc.Text.getStart(), self.MARCADOR + '. ', False))
        _log('diag recuperação: texto 1 digitado, sem salvar')
        if self.spec.get('esperar_autosalvamento'):
            pasta = self._pasta_copias()
            inicio = time.time()
            achou = None
            while time.time() - inicio < 480 and not achou:
                time.sleep(5)
                try:
                    achou = next((n for n in os.listdir(pasta) if os.path.getmtime(os.path.join(pasta, n)) > inicio), None)
                except OSError:
                    pass
            _log(f'diag recuperação: cópia automática {"gravada em " + str(round(time.time() - inicio)) + " s: " + achou if achou else "NÃO gravada em 480 s"}')
            self.res['copia_automatica_s'] = round(time.time() - inicio) if achou else None
            self.no_principal(lambda: self.doc.Text.insertString(self.doc.Text.getEnd(), ' ' + self.MARCADOR2 + '.', False))
            _log('diag recuperação: texto 2 digitado, sem salvar')
        _log('diag recuperação: provocando a queda')
        for i in range(10):
            self._abrir_e_fechar('.uno:HyperlinkDialog')
            j, _t = self.janela_extra()
            if j is not None and 'Recupera' in _titulo(j):
                _log('diag recuperação: diálogo de recuperação aberto no processo que caiu')
                time.sleep(60)
                return
        self.efeito('Queda provocada para o teste de recuperação', False, 'o motor não caiu em 10 tentativas')

    # ---------- hipótese: o robô solta a tecla numa janela que a própria tecla acabou de fechar ----------
    def _tecla_topo_so_apertar(self, codigo):
        import uno as _uno
        tk = self.smgr.createInstanceWithContext('com.sun.star.awt.Toolkit', self.ctx)
        robo = tk.queryInterface(_uno.getTypeByName('com.sun.star.awt.XToolkitRobot'))
        ev = _uno.createUnoStruct('com.sun.star.awt.KeyEvent')
        ev.Source = tk.getActiveTopWindow()
        ev.KeyCode = codigo
        ev.KeyChar = {1281: chr(27), 1280: chr(13)}.get(codigo, chr(0))
        robo.keyPress(ev)
        ev = None

    def _abrir_e_fechar_so_apertar(self, comando, espera=2.0):
        self.selecionar_texto('alfa')
        _log(f'diag: despacha {comando} (robô só aperta)')
        self._abrir_async(comando)
        time.sleep(espera)
        aberta = self.janela_extra()[0] is not None
        _log(f'diag: {comando} aberta={aberta}; Esc só com keyPress')
        self._tecla_topo_so_apertar(ESC)
        time.sleep(espera)
        if self.janela_extra()[0] is not None:
            self.__dict__.setdefault('_diag_problemas', []).append(f'{comando}: continuou aberta')
        _log(f'diag: {comando} fechado')

    def diag_robo_so_apertar(self):
        self._diag('robô só aperta (sem soltar): Link, Esc, Propriedades, Esc, Link, Esc', [
            lambda: self._abrir_e_fechar_so_apertar('.uno:HyperlinkDialog'),
            lambda: self._abrir_e_fechar_so_apertar('.uno:SetDocumentProperties'),
            lambda: self._abrir_e_fechar_so_apertar('.uno:HyperlinkDialog')])

    def diag_espacamento_teclado(self):
        """Lista de "Espaçamento entre linhas" só com teclado real: registra o foco ao abrir e a cada Tab."""
        self.selecionar_texto('alfa')
        b = next(x for x in self.mapa['botoes'] if x['comando'] == '.uno:LineSpacing')
        self.aba_atual = None
        self.clicar(b)
        time.sleep(1.5)
        caminho = [self._foco()]
        for _ in range(8):
            self._teclas_reais(0x09)
            time.sleep(0.4)
            caminho.append(self._foco())
        _log(f'diag espaçamento: foco ao abrir e a cada Tab: {caminho}')
        self._teclas_reais(0x1B)
        time.sleep(0.8)
        self.res.setdefault('diag', {})['espacamento'] = caminho
        self.efeito('Diagnóstico: foco na lista de espaçamento entre linhas', True, str(caminho))

    def diag_estados_vista(self):
        """Estado (habilitado/marcado) dos comandos de exibição de páginas, para escolher os que funcionam no editor."""
        cands = ('.uno:ShowSinglePage', '.uno:ShowTwoPages', '.uno:ShowMultiplePages', '.uno:ShowBookview', '.uno:SinglePageView',
                 '.uno:MultiPageView', '.uno:BookView', '.uno:ViewLayout', '.uno:BrowseView', '.uno:PrintLayout', '.uno:Zoom',
                 '.uno:ZoomPage', '.uno:SinglePage', '.uno:TwoPages', '.uno:BookMode')
        estados = {c: repr(self.no_principal(lambda c=c: self._estado_comando(c))) for c in cands}
        _log(f'diag estados da vista: {estados}')
        self.res.setdefault('diag', {})['estados_vista'] = estados
        self.efeito('Diagnóstico: estados dos comandos de exibição de páginas', True, str(estados))

    def diag_viewlayout(self):
        """Qual forma de chamar .uno:ViewLayout muda a exibição (uma página, várias, livro)."""
        from com.sun.star.beans import PropertyValue

        def pv(n, v):
            p = PropertyValue()
            p.Name, p.Value = n, v
            return p
        tent = [
            ('url curto', '.uno:ViewLayout?Columns:short=2&BookMode:boolean=false', ()),
            ('url com prefixo', '.uno:ViewLayout?ViewLayout.Columns:short=2&ViewLayout.BookMode:boolean=false', ()),
            ('args com prefixo', '.uno:ViewLayout', (pv('ViewLayout.Columns', uno.Any('short', 2)), pv('ViewLayout.BookMode', True))),
            ('args curtos', '.uno:ViewLayout', (pv('Columns', uno.Any('short', 0)), pv('BookMode', False))),
        ]
        d = self.smgr.createInstanceWithContext('com.sun.star.frame.DispatchHelper', self.ctx)
        res = []
        for nome, url, args in tent:
            self.no_principal(lambda: d.executeDispatch(self.frame, '.uno:ViewLayout?Columns:short=1&BookMode:boolean=false', '', 0, ()))
            time.sleep(0.5)
            antes = repr(self.no_principal(lambda: self._estado_comando('.uno:ViewLayout')))
            self.no_principal(lambda: d.executeDispatch(self.frame, url, '', 0, args))
            time.sleep(0.8)
            depois = repr(self.no_principal(lambda: self._estado_comando('.uno:ViewLayout')))
            res.append((nome, antes[-120:], depois[-120:]))
        _log(f'diag viewlayout: {res}')
        self.res.setdefault('diag', {})['viewlayout'] = res
        self.efeito('Diagnóstico: formas de chamar .uno:ViewLayout', True, str(res))

    def diag_foco(self):
        """Por que a leitura do foco pela árvore de acessibilidade volta vazia: registra o que existe no caminho."""
        def f():
            A = 'com.sun.star.accessibility.'
            info = {}
            tk = self.smgr.createInstanceWithContext('com.sun.star.awt.Toolkit', self.ctx)
            top = tk.getActiveTopWindow()
            info['top'] = None if top is None else top.getImplementationName() if hasattr(top, 'getImplementationName') else type(top).__name__
            for nome, janela in (('ativa', top), ('documento', self.frame.getContainerWindow())):
                if janela is None:
                    continue
                acc = janela.queryInterface(uno.getTypeByName(A + 'XAccessible'))
                info[nome + '_xaccessible'] = acc is not None
                if acc is not None:
                    c = acc.getAccessibleContext()
                    st = c.getAccessibleStateSet()
                    info[nome + '_raiz'] = (c.getAccessibleRole(), c.getAccessibleName(), type(st).__name__, st if isinstance(st, int) else '?',
                                            c.getAccessibleChildCount())
            info['FOCUSED'] = uno.getConstantByName(A + 'AccessibleStateType.FOCUSED')
            return info
        info = self.no_principal(f)
        _log(f'diag foco: {info}')
        self.res.setdefault('diag', {})['foco'] = {k: str(v) for k, v in info.items()}
        self.efeito('Diagnóstico: leitura do foco pela acessibilidade', True, str(info))

    def diag_foco_uitest(self):
        """Ler o foco pelo estado dos controles no UITest (HasFocus): quanto custa e o que aparece."""
        inicio = time.time()
        t = self.ui.getTopFocusWindow()
        filhos = list(t.getChildren())
        focados = []
        for cid in filhos:
            try:
                st = {p.Name: p.Value for p in t.getChild(cid).getState()}
            except Exception:
                continue
            if st.get('HasFocus') == 'true':
                focados.append((cid, st.get('WindowType'), st.get('Text', '')[:40], st.get('CurrSelectedItemText', '')))
        info = {'filhos': len(filhos), 'segundos': round(time.time() - inicio, 2), 'focados': focados,
                'estado_topo': sorted({p.Name for p in t.getState()})[:40]}
        _log(f'diag foco uitest: {info}')
        self.res.setdefault('diag', {})['foco_uitest'] = str(info)
        self.efeito('Diagnóstico: foco pelo UITest', True, str(info))
