# -*- coding: utf-8 -*-
"""Conferência automática dos diálogos e painéis do AY na escala de tela atual (100 %, 125 %, 150 %, 200 %).

Para cada diálogo (Formatar, Prévia, Relatório, Modelo da instituição, Galeria, Gerenciar IA local) e painel
(Assistente AY, Revisão com IA):
  - texto cortado: o tamanho que o próprio controle pede para mostrar o texto (getPreferredSize) é maior que o espaço
    que ele tem (botões, caixas de marcação, rótulos de uma linha);
  - sobreposição: dois controles visíveis ocupando o mesmo lugar (o defeito "bre o modelo" da 0.5.0);
  - cabe na tela: a janela inteira dentro da área de trabalho (sem a barra de tarefas);
e grava uma captura com a escala no nome (tests/output/interface/escala-<escala>-<nome>.png).
A escala do Windows não é trocada pelo teste (é configuração do sistema): ele confere a escala em uso.
SPDX-License-Identifier: MPL-2.0
"""
import ctypes
import time

FOLGA = 2          # px de tolerância de arredondamento
TIPOS_TEXTO = ('Button', 'CheckBox', 'RadioButton', 'FixedText')


def escala_atual():
    """Escala da tela em uso (%), pelo valor que o Windows aplicou à sessão (AppliedDPI: 96 = 100 %, 144 = 150 %)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Control Panel\Desktop\WindowMetrics') as k:
            return round(100 * winreg.QueryValueEx(k, 'AppliedDPI')[0] / 96)
    except OSError:
        try:
            return round(100 * ctypes.windll.user32.GetDpiForSystem() / 96)
        except Exception:
            return None


def _tipo(modelo):
    for t in ('Button', 'CheckBox', 'RadioButton', 'FixedText', 'Edit', 'ListBox', 'ComboBox', 'GroupBox', 'ProgressBar',
              'NumericField', 'FormattedField'):
        if modelo.supportsService(f'com.sun.star.awt.UnoControl{t}Model'):
            return t
    return '?'


def conferir_controles(controles):
    """controles: [(nome, controle)]. Devolve (cortados, sobrepostos) com detalhes legíveis."""
    cortados, caixas = [], []
    for nome, ctl in controles:
        peer = ctl.getPeer()
        if peer is None or (hasattr(peer, 'isVisible') and not peer.isVisible()):
            continue                                   # controles escondidos (ex.: lista de títulos) não contam
        m = ctl.getModel()
        tipo = _tipo(m)
        ps = ctl.getPosSize()
        if ps.Width <= 0 or ps.Height <= 0:
            continue
        if tipo != 'GroupBox':
            caixas.append((nome, tipo, ps.X, ps.Y, ps.Width, ps.Height))
        multilinha = bool(getattr(m, 'MultiLine', False)) if hasattr(m, 'MultiLine') else False
        if tipo in TIPOS_TEXTO and not multilinha and (getattr(m, 'Label', '') or '').strip():
            try:
                minimo = ctl.getMinimumSize()           # o menor tamanho que mostra o texto inteiro
            except Exception:
                continue
            if minimo.Width > ps.Width + FOLGA:
                cortados.append(f'{nome} ({tipo}: precisa de {minimo.Width} px, tem {ps.Width} px)')
    sobrepostos = []
    for i, a in enumerate(caixas):
        for b in caixas[i + 1:]:
            ix = min(a[2] + a[4], b[2] + b[4]) - max(a[2], b[2])
            iy = min(a[3] + a[5], b[3] + b[5]) - max(a[3], b[3])
            if ix > FOLGA and iy > FOLGA:
                sobrepostos.append(f'{a[0]} × {b[0]} ({ix}×{iy} px)')
    return cortados, sobrepostos


class EscalaMixin:
    def _area_trabalho(self):
        tk = self.smgr.createInstanceWithContext('com.sun.star.awt.Toolkit', self.ctx)
        return tk.getWorkArea()

    def _conferir_dialogo(self, d, rotulo, titulo):
        esc = escala_atual()

        def f():
            ctls = [(n, d.c(n)) for n in d.dm.getElementNames()]
            cortados, sobrepostos = conferir_controles(ctls)
            janela = d.dlg.getPeer().getPosSize() if hasattr(d.dlg.getPeer(), 'getPosSize') else d.dlg.getPosSize()
            return cortados, sobrepostos, (janela.X, janela.Y, janela.Width, janela.Height)
        cortados, sobrepostos, (x, y, w, h) = self.no_principal(f)
        area = self.no_principal(self._area_trabalho)
        cabe = w <= area.Width and h <= area.Height
        self._capturar(titulo, f'escala-{esc}-{rotulo}')
        self.res.setdefault('escala', {})[rotulo] = {'escala': esc, 'janela': [w, h], 'area': [area.Width, area.Height],
                                                     'cortados': cortados, 'sobrepostos': sobrepostos}
        self.efeito(f'Escala {esc} %: "{titulo}" sem texto cortado, sem controles sobrepostos e cabendo na tela',
                    not cortados and not sobrepostos and cabe,
                    f'janela {w}×{h} px, área {area.Width}×{area.Height}; cortados: {cortados or "nenhum"}; '
                    f'sobrepostos: {sobrepostos or "nenhum"}')

    def _conferir_painel(self, painel, rotulo):
        esc = escala_atual()
        cortados, sobrepostos = self.no_principal(lambda: conferir_controles(list(painel.c.items())))
        self.res.setdefault('escala', {})[rotulo] = {'escala': esc, 'cortados': cortados, 'sobrepostos': sobrepostos}
        self.efeito(f'Escala {esc} %: painel "{rotulo}" sem texto cortado e sem controles sobrepostos',
                    not cortados and not sobrepostos, f'cortados: {cortados or "nenhum"}; sobrepostos: {sobrepostos or "nenhum"}')

    def escala_dialogos(self):
        self.res.setdefault('medidas_escala', {})['escala'] = escala_atual()
        # Formatar trabalho acadêmico, Prévia, Modelo da instituição e Relatório
        self._abrir_async('ayescreva:FormatarTrabalho')
        d = self._esperar_dialogo('formatar')
        if d is not None:
            self._conferir_dialogo(d, 'formatar', 'Formatar trabalho')
            self.acionar_teclado(d.c('previa'))
            pv = self._esperar_dialogo('previa', 60)
            if pv is not None:
                self._conferir_dialogo(pv, 'previa', 'o que vai mudar')
                self.acionar_teclado(pv.c('voltar'))
            d = self._esperar_dialogo('formatar')
            self.acionar_teclado(d.c('instituicao'))
            i = self._esperar_dialogo('instituicao')
            if i is not None:
                self._conferir_dialogo(i, 'instituicao', 'Modelo da instituição')
                self.acionar_teclado(i.c('cancelar'))
            d = self._esperar_dialogo('formatar')
            self.acionar_teclado(d.c('relatorio'))
            r = self._esperar_dialogo('relatorio', 60)
            if r is not None:
                self._conferir_dialogo(r, 'relatorio', 'Relatório')
                self.acionar_teclado(r.c('fechar'))
            d = self._esperar_dialogo('formatar')
            if d is not None:
                self.acionar_teclado(d.c('fechar'))
            self._sem_dialogos()
        else:
            self.efeito('Escala: diálogo Formatar abre', False)
        # Galeria de modelos
        self._abrir_async('ayescreva:Galeria')
        g = self._esperar_dialogo('galeria')
        if g is not None:
            self._conferir_dialogo(g, 'galeria', 'Galeria')
            self.acionar_teclado(g.c('fechar'))
            self._sem_dialogos()
        else:
            self.efeito('Escala: Galeria abre', False)
        # Painéis e Gerenciar IA local
        p = self._painel_ia()
        if p is not None:
            self._conferir_painel(p, 'Revisão com IA')
            self.acionar_teclado(p.c['gerenciar'])
            gi = self._esperar_dialogo('gerenciar_ia')
            if gi is not None:
                self._conferir_dialogo(gi, 'gerenciar-ia', 'Gerenciar IA local')
                self.acionar_teclado(gi.c('fechar'))
                self._sem_dialogos()
        a = self._painel()
        if a is not None:
            self._conferir_painel(a, 'Assistente AY')
        time.sleep(0.5)

    # ---------- leitor de tela disponível (Narrador) ----------
    def _leitor(self, acao, titulo='', nome=''):
        import json
        import os
        import subprocess
        raiz = os.path.dirname(os.path.dirname(self.spec['abas']))
        script = os.path.join(raiz, 'tests', 'interface', 'leitor_de_tela.ps1')
        saida = os.path.join(raiz, 'tests', 'output', 'interface', f'leitor-{nome or acao}.json')
        args = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script, '-Acao', acao]
        if acao == 'ler':
            args += ['-Saida', saida] + (['-Titulo', titulo] if titulo else [])
        r = subprocess.run(args, capture_output=True, text=True, timeout=240)
        self._log_rev(f'leitor {acao} {nome}: ' + (r.stdout or r.stderr or '').strip()[-300:])
        if acao != 'ler':
            return None
        with open(saida, encoding='utf-8-sig') as f:
            return json.load(f)

    def _conferir_leitura(self, dados, rotulo, esperados):
        itens = dados.get('itens') or []
        nomes = {(i.get('nome') or '').replace('~', '').strip() for i in itens}
        faltam = [e for e in esperados if not any(e in n for n in nomes)]
        # controles acionáveis (botões, campos, listas, caixas) sem nome, dentro do trecho da árvore que vai do primeiro ao
        # último controle esperado (na janela principal, o resto — menus, faixa, barra lateral da base — fica de fora);
        # recipientes (barras, áreas, painéis) são anunciados pelo papel e não precisam de nome
        acionavel = ('botão', 'texto editável', 'lista', 'caixa de', 'opção', 'item de lista')
        pos = [k for k, i in enumerate(itens) if any(e in (i.get('nome') or '') for e in esperados)]
        trecho = itens[min(pos):max(pos) + 1] if pos else itens
        sem_nome = sorted({i.get('tipo') for i in trecho if i.get('teclado') and i.get('visivel', True)
                           and not (i.get('nome') or '').strip() and any(a in (i.get('tipo') or '') for a in acionavel)})
        self.res.setdefault('leitor', {})[rotulo] = {'elementos': len(itens), 'faltam': faltam, 'focaveis_sem_nome': sem_nome}
        self.efeito(f'Narrador: "{rotulo}" anuncia os controles pelo nome (botões, campos, listas)',
                    dados.get('narrador') and itens and not faltam and not sem_nome,
                    f'{len(itens)} elementos lidos; faltam: {faltam or "nenhum"}; focáveis sem nome: {sem_nome or "nenhum"}')

    def leitor_de_tela(self):
        self._leitor('iniciar')
        try:
            p = self._painel_ia()
            if p is not None:
                dados = self._leitor('ler', 'AY ESCREVA', 'painel-ia')
                self._conferir_leitura(dados, 'painel Revisão com IA',
                                       ['Pedido:', 'Pedir à IA', 'Revisar o documento inteiro', 'Cancelar', 'Original:', 'Sugestão:', 'Aplicar como alteração controlada',
                                        'Aceitar', 'Rejeitar', 'Gerenciar IA local'])
                self.acionar_teclado(p.c['gerenciar'])
                gi = self._esperar_dialogo('gerenciar_ia')
                if gi is not None:
                    dados = self._leitor('ler', 'Gerenciar IA local', 'gerenciar-ia')
                    self._conferir_leitura(dados, 'Gerenciar IA local',
                                           ['Modelos disponíveis:', 'Sobre o modelo:', 'Pasta:', 'Escolher', 'Baixar',
                                            'Cancelar download', 'Usar este modelo', 'Remover', 'Fechar'])
                    self.acionar_teclado(gi.c('fechar'))
                    self._sem_dialogos()
            self._abrir_async('ayescreva:FormatarTrabalho')
            d = self._esperar_dialogo('formatar')
            if d is not None:
                dados = self._leitor('ler', 'Formatar trabalho', 'formatar')
                self._conferir_leitura(dados, 'Formatar trabalho acadêmico',
                                       ['Modelo da instituição', 'Prévia', 'Relatório', 'Formatar cópia', 'Fechar'])
                self.acionar_teclado(d.c('fechar'))
                self._sem_dialogos()
            for comando, nome, titulo, esperados in (
                    ('ayescreva:ConferirReferencias', 'achados', 'Conferir referências',
                     ['Apontamentos:', 'Detalhe e trecho:', 'Ir para o trecho', 'Fechar']),
                    ('ayescreva:VerificarAtualizacoes', 'atualizacoes', 'Verificar atualizações',
                     ['Canal:', 'Verificar agora', 'Novidades da versão:', 'Baixar e instalar', 'Cancelar download', 'Fechar'])):
                self._abrir_async(comando)
                d = self._esperar_dialogo(nome)
                if d is None:
                    self.efeito(f'Narrador: {titulo} abre', False)
                    continue
                dados = self._leitor('ler', titulo, nome)
                self._conferir_leitura(dados, titulo, esperados)
                self.acionar_teclado(d.c('fechar'))
                self._sem_dialogos()
        finally:
            self._leitor('parar')

    # ---------- entrega E: Verificar atualizações ----------
    def atualizacoes_dialogo(self):
        self._abrir_async('ayescreva:VerificarAtualizacoes')
        d = self._esperar_dialogo('atualizacoes')
        self.efeito('Verificar atualizações abre pela aba Ajuda', d is not None)
        if d is None:
            return
        inicial = self.no_principal(lambda: d.m('situacao').Label)
        baixar = self.no_principal(lambda: bool(d.m('baixar').Enabled))
        explica = self.no_principal(lambda: d.m('explica').Label)
        self.efeito('Ao abrir, nada é consultado: a consulta só acontece em "Verificar agora"; explica o que é enviado',
                    'Nenhuma consulta' in inicial and not baixar and 'nenhum documento' in explica, inicial)
        sem, _ = self._nomes_acessiveis(d)
        self.efeito('Acessibilidade: controles de Verificar atualizações com nome acessível', not sem, 'sem nome: ' + (', '.join(sem) or 'nenhum'))
        self._teclado_dialogo(d, 'canal', 'verificar', 'Verificar atualizações')
        self._capturar('Verificar atualizações', 'dialogo-atualizacoes')
        self.acionar_teclado(d.c('verificar'))
        fim = time.time() + 60
        sit = ''
        while time.time() < fim:
            sit = self.no_principal(lambda: d.m('situacao').Label)
            if 'Consultando' not in sit and 'Nenhuma consulta' not in sit:
                break
            time.sleep(0.4)
        baixar = self.no_principal(lambda: bool(d.m('baixar').Enabled))
        self.efeito('Verificar agora consulta o site oficial em segundo plano; sem versão assinada publicada, explica e não oferece '
                    'download', ('Não foi possível verificar' in sit or 'já tem a versão' in sit) and not baixar, sit)
        self.acionar_teclado(d.c('fechar'))
        self.efeito('Verificar atualizações fecha sem baixar nada', self._sem_dialogos())
