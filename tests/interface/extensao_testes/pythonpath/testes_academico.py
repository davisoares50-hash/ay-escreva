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
            subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(raiz, 'tests', 'captura_dialogo.ps1'),
                            '-Titulo', titulo, '-Saida', saida], capture_output=True, text=True, timeout=60)
        except Exception:
            pass
        return os.path.exists(saida)

    def _estado_doc(self, doc):
        def f():
            return doc.isModified(), hashlib.sha256(doc.getText().getString().encode('utf-8')).hexdigest(), doc.getURL()
        return self.no_principal(f)

    def _componente_atual(self):
        return self.no_principal(lambda: self.desktop.getCurrentComponent())

    # ---------- Formatar trabalho acadêmico ----------
    def academico_formatar(self):
        original = self.doc
        antes = self._estado_doc(original)
        self._abrir_async('ayescreva:FormatarTrabalho')
        d = self._esperar_dialogo('formatar')
        self.efeito('Formatar trabalho acadêmico abre pela aba Referências (comando)', d is not None)
        if d is None:
            return
        sem, nomes = self._nomes_acessiveis(d)
        self._capturar('Formatar trabalho acadêmico', 'dialogo-formatar')
        self.efeito('Acessibilidade: controles do diálogo Formatar com nome acessível', not sem,
                    'sem nome: ' + (', '.join(sem) or 'nenhum') + ' | perfil="' + nomes.get('perfil', '') + '" copia="' + nomes.get('copia', '') + '"')
        perfis = self.no_principal(lambda: d.c('perfil').getItemCount())
        self.no_principal(lambda: setattr(d.m('copia'), 'State', 1))
        self.efeito('Diálogo mostra os cinco perfis (TCC, projeto, artigo, relatório, instituição) e a cópia marcada',
                    perfis == 5 and self.no_principal(lambda: d.m('copia').State) == 1, f'{perfis} perfis')
        self.acionar_teclado(d.c('previa'))
        pv = self._esperar_dialogo('previa', 60)
        n_mud = self.no_principal(lambda: d_mud(pv)) if pv else 0
        if pv:
            self._capturar('Prévia — o que vai mudar', 'dialogo-previa')
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
        conformes = [x for x in linhas if x.startswith('✓')]
        falhas = [x for x in linhas if x.startswith('✗')]
        self.efeito('Aplicar numa cópia: relatório de conformidade aparece com as regras conferidas',
                    rel is not None and len(linhas) >= 15 and any('Margens' in x for x in conformes) and 'cópia sem título' in topo,
                    f'{len(conformes)} conformes, {len(falhas)} não conformes: {"; ".join(falhas)[:200]}')
        if rel is not None:
            sem, _ = self._nomes_acessiveis(rel)
            self._capturar('Relatório de conformidade', 'dialogo-relatorio')
            self.efeito('Acessibilidade: controles do relatório com nome acessível', not sem, 'sem nome: ' + (', '.join(sem) or 'nenhum'))
            self.acionar_teclado(rel.c('fechar'))
        self._sem_dialogos()
        copia = self._componente_atual()
        depois = self._estado_doc(original)

        def info_copia():
            primeiro = copia.getText().createEnumeration().nextElement()
            return copia.getURL(), primeiro.PageStyleName, copia.getDocumentIndexes().getCount(), copia.getUndoManager().isUndoPossible()
        url, estilo, indices, desfazivel = self.no_principal(info_copia)
        self.efeito('Original intacto (texto, arquivo e "modificado") e a cópia sem título formatada',
                    depois == antes and url == '' and estilo == 'AY Pré-textual' and indices >= 1, f'cópia: estilo {estilo}, índices {indices}')
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
        finally:
            self.frame = quadro_original
            self.no_principal(lambda: (copia.setModified(False), copia.close(True)))
            time.sleep(0.5)
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
