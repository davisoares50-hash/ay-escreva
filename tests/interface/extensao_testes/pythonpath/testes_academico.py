# -*- coding: utf-8 -*-
"""Testes pela interface da entrega B: "Formatar trabalho acadêmico" (opções, prévia, aplicar numa cópia, relatório,
desfazer pelo teclado) e galeria de modelos (criar documento, salvar como modelo).

Os diálogos do AY são modais e rodam na thread principal; o teste os abre de forma assíncrona, encontra-os em
ay_dialogos.ATUAL e aciona os botões com foco + Espaço reais (robô do toolkit), como alguém usando só o teclado.
SPDX-License-Identifier: MPL-2.0
"""
import hashlib
import os
import time

import uno


class AcademicoMixin:
    def _abrir_async(self, comando, frame=None):
        d = self.smgr.createInstanceWithContext('com.sun.star.frame.DispatchHelper', self.ctx)
        alvo = frame or self.frame
        self.postar(lambda: d.executeDispatch(alvo, comando, '', 0, ()))

    def _esperar_dialogo(self, nome, limite=20):
        import ay_dialogos
        fim = time.time() + limite
        while time.time() < fim:
            for d in list(ay_dialogos.ATUAL):
                if getattr(d, 'nome', None) == nome and getattr(d, 'dlg', None) is not None:
                    time.sleep(0.5)
                    return d
            time.sleep(0.2)
        return None

    def _sem_dialogos(self, limite=10):
        import ay_dialogos
        fim = time.time() + limite
        while time.time() < fim and ay_dialogos.ATUAL:
            time.sleep(0.2)
        return not ay_dialogos.ATUAL

    def _nomes_acessiveis(self, d):
        def f():
            r = {}
            for n in d.dm.getElementNames():
                m = d.dm.getByName(n)
                if m.supportsService('com.sun.star.awt.UnoControlFixedTextModel') or m.supportsService('com.sun.star.awt.UnoControlGroupBoxModel'):
                    continue
                try:
                    r[n] = d.c(n).getAccessibleContext().getAccessibleName()
                except Exception as e:
                    r[n] = ''
            return r
        nomes = self.no_principal(f)
        return [n for n, v in nomes.items() if not (v or '').strip()], nomes

    def _capturar(self, titulo, nome):
        """Imagem do diálogo (pelo título) em tests/output/interface/<nome>.png, para conferência visual."""
        import subprocess
        raiz = os.path.dirname(os.path.dirname(self.spec['abas']))
        saida = os.path.join(raiz, 'tests', 'output', 'interface', nome + '.png')
        try:
            r = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(raiz, 'tests', 'captura_dialogo.ps1'),
                                '-Titulo', titulo, '-Saida', saida], capture_output=True, text=True, timeout=60)
            self._log_rev(f'captura {nome}: ' + (r.stdout or r.stderr).strip()[-300:])
        except Exception as e:
            self._log_rev(f'captura {nome}: {e}')
        return os.path.exists(saida)

    def _estado_doc(self, doc):
        def f():
            um = doc.getUndoManager()
            return (doc.isModified(), hashlib.sha256(doc.getText().getString().encode('utf-8')).hexdigest(), doc.getURL(),
                    um.getAllUndoActionTitles(), um.getAllRedoActionTitles())
        return self.no_principal(f)

    def ctrl_y(self):
        robo = self._robo()
        ev = uno.createUnoStruct('com.sun.star.awt.KeyEvent')
        ev.Source, ev.KeyCode, ev.KeyChar, ev.Modifiers = self.frame.getContainerWindow(), 536, chr(25), 2
        robo.keyPress(ev)
        robo.keyRelease(ev)
        time.sleep(0.8)

    def _componente_atual(self):
        return self.no_principal(lambda: self.desktop.getCurrentComponent())

    # ---------- Formatar trabalho acadêmico ----------
    def academico_formatar(self):
        original = self.doc
        # uma alteração digitada e não salva: o original tem histórico de desfazer que não pode se perder
        self.no_principal(lambda: self.ctrl.getViewCursor().gotoEnd(False))
        self.focar_documento()
        self.digitar(' Frase digitada antes de formatar.')
        antes = self._estado_doc(original)
        self._abrir_async('ayescreva:FormatarTrabalho')
        d = self._esperar_dialogo('formatar')
        self.efeito('Formatar trabalho acadêmico abre pela aba Referências (comando)', d is not None)
        if d is None:
            return
        sem, nomes = self._nomes_acessiveis(d)
        self._capturar('Formatar trabalho', 'dialogo-formatar')
        self.efeito('Acessibilidade: controles do diálogo Formatar com nome acessível', not sem,
                    'sem nome: ' + (', '.join(sem) or 'nenhum') + ' | perfil="' + nomes.get('perfil', '') + '"')
        perfis = self.no_principal(lambda: d.c('perfil').getItemCount())
        nota = self.no_principal(lambda: d.m('nota_copia').Label)
        self.efeito('Diálogo mostra os cinco perfis e informa que a formatação é sempre feita numa cópia (sem opção no original)',
                    perfis == 5 and 'cópia sem título' in nota and 'copia' not in d.dm.getElementNames(), f'{perfis} perfis')
        self.acionar_teclado(d.c('previa'))
        pv = self._esperar_dialogo('previa', 60)
        n_mud = self.no_principal(lambda: d_mud(pv)) if pv else 0
        if pv:
            self._capturar('o que vai mudar', 'dialogo-previa')
        self.efeito('Prévia pelo teclado: lista do que vai mudar, sem alterar o documento',
                    pv is not None and n_mud >= 10 and self._estado_doc(original) == antes, f'{n_mud} mudanças')
        if pv is None:
            return
        self.acionar_teclado(pv.c('voltar'))
        d2 = self._esperar_dialogo('formatar')
        if d2 is None:
            self.efeito('Voltar da prévia reabre o diálogo', False)
            return
        self.acionar_teclado(d2.c('aplicar'))
        rel = self._esperar_dialogo('relatorio', 120)
        linhas = self.no_principal(lambda: tuple(rel.m('itens').StringItemList)) if rel else ()
        topo = self.no_principal(lambda: rel.m('cabecalho').Label) if rel else ''
        conformes = [x for x in linhas if x.strip().startswith('✓')]
        falhas = [x for x in linhas if x.strip().startswith('✗')]
        self.efeito('Aplicar numa cópia: relatório de conformidade aparece com as regras conferidas',
                    rel is not None and len(linhas) >= 15 and any('Margens' in x for x in conformes) and 'cópia sem título' in topo.lower(),
                    f'{len(conformes)} conformes, {len(falhas)} não conformes: {"; ".join(falhas)[:200]}')
        if rel is not None:
            sem, _ = self._nomes_acessiveis(rel)
            self._capturar('de conformidade', 'dialogo-relatorio')
            self.efeito('Acessibilidade: controles do relatório com nome acessível', not sem, 'sem nome: ' + (', '.join(sem) or 'nenhum'))
            self.acionar_teclado(rel.c('fechar'))
        self._sem_dialogos()
        copia = self._componente_atual()
        depois = self._estado_doc(original)

        def info_copia():
            primeiro = copia.getText().createEnumeration().nextElement()
            return copia.getURL(), primeiro.PageStyleName, copia.getDocumentIndexes().getCount(), copia.getUndoManager().isUndoPossible()
        url, estilo, indices, desfazivel = self.no_principal(info_copia)
        self.efeito('Original intacto (texto com a frase não salva, arquivo, "modificado" e histórico de desfazer) e a cópia sem título formatada',
                    depois == antes and antes[0] and len(antes[3]) >= 1 and url == '' and estilo == 'AY Pré-textual' and indices >= 1,
                    f'histórico do original: {antes[3][:2]}; cópia: estilo {estilo}, índices {indices}')

        def sumario_intro():
            idx = copia.getDocumentIndexes()
            if idx.getCount() == 0:
                return None
            linhas = idx.getByIndex(0).getAnchor().getString().splitlines()
            return next((l for l in linhas if l.startswith('1 INTRODUÇÃO')), None)
        intro = self.no_principal(sumario_intro)
        # Ctrl+Z na cópia desfaz a formatação inteira (uma ação)
        janela_copia = self.no_principal(lambda: copia.getCurrentController().getFrame())
        quadro_original = self.frame
        self.frame = janela_copia
        try:
            self.focar_documento()
            self.ctrl_z()
            time.sleep(1.0)
            estilo2, indices2 = self.no_principal(lambda: (copia.getText().createEnumeration().nextElement().PageStyleName,
                                                            copia.getDocumentIndexes().getCount()))
            self.efeito('Ctrl+Z pelo teclado na cópia desfaz a formatação inteira', desfazivel and estilo2 != 'AY Pré-textual' and indices2 == 0,
                        f'estilo da 1ª página {estilo2}; índices {indices2}')
            self.ctrl_y()
            time.sleep(1.0)
            estilo3 = self.no_principal(lambda: copia.getText().createEnumeration().nextElement().PageStyleName)
            intro3 = self.no_principal(sumario_intro)
            self.efeito('Ctrl+Y pelo teclado refaz a formatação inteira, com a mesma numeração no sumário',
                        estilo3 == 'AY Pré-textual' and intro is not None and intro3 == intro, f'antes: {intro!r}; refeito: {intro3!r}')
        finally:
            self.frame = quadro_original
            self.no_principal(lambda: (copia.setModified(False), copia.close(True)))
            time.sleep(0.5)
            self.focar_documento()

    # ---------- teclado: foco, tabulação e teclas de acesso ----------
    def _teclado_dialogo(self, d, primeiro, segundo, rotulo):
        """Foco inicial no primeiro controle, Tab vai ao seguinte (rótulos são pulados), Shift+Tab volta; teclas de acesso únicas."""
        FOCADO = uno.getConstantByName('com.sun.star.accessibility.AccessibleStateType.FOCUSED')

        def tem_foco(ac, nivel=0):
            # estados acessíveis: conjunto de bits (versões novas do motor) ou objeto com contains()
            st = ac.getAccessibleStateSet()
            foco = bool(st & FOCADO) if isinstance(st, int) else st.contains(FOCADO)
            if foco:
                return True
            if nivel < 3:          # lista suspensa: o foco fica na parte de dentro (campo ou lista)
                for k in range(min(ac.getAccessibleChildCount(), 8)):
                    if tem_foco(ac.getAccessibleChild(k).getAccessibleContext(), nivel + 1):
                        return True
            return False

        def focado():
            for n in d.dm.getElementNames():
                try:
                    ctl = d.c(n)
                    if ctl.getPeer() is not None and (ctl.hasFocus() or tem_foco(ctl.getAccessibleContext())):
                        return n
                except Exception:
                    pass
            return None

        def mnemonicos():
            vistos, repetidos = {}, []
            for n in d.dm.getElementNames():
                m = d.dm.getByName(n)
                rot = getattr(m, 'Label', '') if hasattr(m, 'Label') else ''
                if '~' in (rot or ''):
                    letra = rot[rot.index('~') + 1].lower()
                    if letra in vistos:
                        repetidos.append(f'{letra}: {vistos[letra]} / {n}')
                    vistos[letra] = n
            return repetidos
        inicial = self.no_principal(focado)
        robo = self._robo()

        def tab(shift=False):
            ev = uno.createUnoStruct('com.sun.star.awt.KeyEvent')
            ev.Source = d.dlg.getPeer()
            ev.KeyCode, ev.KeyChar, ev.Modifiers = 1282, chr(9), 1 if shift else 0
            robo.keyPress(ev)
            robo.keyRelease(ev)
            time.sleep(0.4)
        tab()
        depois_tab = self.no_principal(focado)
        tab(shift=True)
        volta = self.no_principal(focado)
        rep = self.no_principal(mnemonicos)
        self.efeito(f'Teclado em "{rotulo}": foco inicial em {primeiro}, Tab vai a {segundo}, Shift+Tab volta; teclas de acesso sem repetição',
                    inicial == primeiro and depois_tab == segundo and volta == primeiro and not rep,
                    f'inicial {inicial}, Tab {depois_tab}, Shift+Tab {volta}; repetidas: {rep}')

    # ---------- modelo da instituição ----------
    def academico_instituicao(self):
        self._abrir_async('ayescreva:FormatarTrabalho')
        d = self._esperar_dialogo('formatar')
        if d is None:
            self.efeito('Modelo da instituição: diálogo Formatar abre', False)
            return
        self._teclado_dialogo(d, 'perfil', 'fonte', 'Formatar trabalho acadêmico')
        self.acionar_teclado(d.c('instituicao'))
        i = self._esperar_dialogo('instituicao')
        self.efeito('Modelo da instituição abre pelo botão do diálogo Formatar', i is not None)
        if i is None:
            return
        self._capturar('Modelo da institui', 'dialogo-instituicao')
        sem, _ = self._nomes_acessiveis(i)
        self._teclado_dialogo(i, 'nome', 'man_titulo', 'Modelo da instituição')

        def preencher():
            i.c('nome').setText('Universidade do Teste')
            i.c('fonte').setText('Arial')
            i.m('ponto').State = 1
            # o ouvinte de digitação atualiza a prévia; a caixa de marcação, ao mudar o estado pelo modelo, não avisa
            i.c('tamanho').setText('11')
        self.no_principal(preencher)
        time.sleep(0.6)
        self.acionar_teclado(i.c('ponto'))          # Espaço desmarca e o ouvinte atualiza a prévia
        self.acionar_teclado(i.c('ponto'))          # e marca de novo
        dif = self.no_principal(lambda: tuple(i.m('diferencas').StringItemList))
        texto = ' | '.join(dif)
        self.efeito('Modelo da instituição: prévia mostra cada mudança, o valor do perfil base e a divergência da norma; controles com nome acessível',
                    'Fonte: Arial (perfil base: Times New Roman)' in texto and 'diverge da norma (NBR 6024:2012)' in texto
                    and 'Tamanho da letra: 11 pt' in texto and not sem, texto[:300] + (f'; sem nome: {sem}' if sem else ''))
        self.acionar_teclado(i.c('cancelar'))
        d2 = self._esperar_dialogo('formatar')
        if d2 is not None:
            self.acionar_teclado(d2.c('fechar'))
        self._sem_dialogos()
        self.focar_documento()

    # ---------- galeria de modelos ----------
    def academico_galeria(self):
        self._abrir_async('ayescreva:Galeria')
        g = self._esperar_dialogo('galeria')
        self.efeito('Galeria de modelos abre pela aba Arquivo (comando)', g is not None)
        if g is None:
            return
        sem, _ = self._nomes_acessiveis(g)
        self._capturar('Galeria de modelos', 'dialogo-galeria')
        itens = self.no_principal(lambda: tuple(g.m('lista').StringItemList))
        desc = self.no_principal(lambda: g.m('descricao').Text)
        self.efeito('Galeria lista ofício, memorando, relatório, currículo, carta, ata e proposta, com origem de cada modelo',
                    len(itens) >= 7 and 'Manual de Redação' in desc and not sem, f'{len(itens)} modelos; sem nome acessível: {sem}')
        self.acionar_teclado(g.c('criar'))
        self._sem_dialogos()
        time.sleep(1.0)
        novo = self._componente_atual()

        def info():
            return novo.getURL(), novo.getDocumentProperties().Title, 'OFÍCIO Nº' in novo.getText().getString(), novo.isModified()
        url, titulo, tem, mod = self.no_principal(info)
        self.efeito('Criar documento: ofício novo, sem título e sem alterações pendentes', url == '' and tem and not mod, titulo)
        self.no_principal(lambda: novo.close(True))
        time.sleep(0.5)
        self.focar_documento()

    def academico_salvar_modelo(self):
        self._abrir_async('ayescreva:SalvarModelo')
        s = self._esperar_dialogo('salvar_modelo')
        self.efeito('Salvar como modelo abre pela aba Arquivo (comando)', s is not None)
        if s is None:
            return
        self.no_principal(lambda: s.c('nome').setText('Modelo do teste pela interface'))
        self.acionar_teclado(s.c('salvar'))
        # mensagem "Modelo salvo": Enter pelo robô
        time.sleep(1.5)
        tk = self.smgr.createInstanceWithContext('com.sun.star.awt.Toolkit', self.ctx)
        self.tecla_robo(1280, tk.getActiveTopWindow())
        self._sem_dialogos()
        import ay_modelos
        lista = self.no_principal(lambda: ay_modelos.pessoais(self.ctx))
        caminho = next((c for n, c in lista if n == 'Modelo do teste pela interface'), None)
        self.efeito('Salvar como modelo: .ott gravado na pasta de modelos do perfil e listado na galeria',
                    caminho is not None and os.path.exists(caminho), caminho)
        if caminho:
            self.no_principal(lambda: ay_modelos.remover_pessoal(self.ctx, caminho))


def d_mud(pv):
    return pv.c('mudancas').getItemCount()
