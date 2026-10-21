# -*- coding: utf-8 -*-
"""Testes pela interface da entrega C: painel "Revisão com IA" e diálogo "Gerenciar IA local".

Sem modelo: o painel explica que a IA é opcional e o editor segue funcionando. Com modelo (pasta e modelo vindos da
especificação do teste): selecionar → Revisar seleção (teclado) → digitar no documento enquanto a IA trabalha →
original e sugestão no painel → Aceitar (alteração controlada) → Ctrl+Z; Rejeitar; Cancelar; trecho alterado
durante a análise; servidor só em 127.0.0.1. Os botões são acionados com foco + Espaço reais (robô do toolkit).
SPDX-License-Identifier: MPL-2.0
"""
import os
import subprocess
import time

FRASE = 'Os dados mostra que a maioria dos participantes concordaram com a proposta em 2024, segundo o IBGE.'
LONGO = ('Tendo em vista a necessidade de que haja a realização da análise dos documentos por parte da equipe, solicita-se '
         'que seja efetuado o envio dos arquivos até o dia 15/11/2026. ') * 6


class IAMixin:
    def _P(self):
        import ay_ia_painel
        return ay_ia_painel

    def _gerente(self):
        return self._P().Gerente.obter(self.ctx)

    def _painel_ia(self):
        g = self._gerente()
        p = g.painel_do_quadro(self.frame)
        if p is None:
            self.despachar('ayescreva:RevisaoIA')
            fim = time.time() + 15
            while time.time() < fim and p is None:
                time.sleep(0.3)
                p = g.painel_do_quadro(self.frame)
        return p

    def _novo_paragrafo(self, texto):
        def f():
            t = self.doc.getText()
            from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
            t.insertControlCharacter(t.getEnd(), PARAGRAPH_BREAK, False)
            t.insertString(t.getEnd(), texto, False)
        self.no_principal(f)
        return self.selecionar_texto(texto[:120] if len(texto) > 120 else texto)

    def _selecionar_paragrafo(self, inicio):
        def f():
            r = self._selecionar(inicio)
            c = self.doc.getText().createTextCursorByRange(r.getStart())
            c.gotoEndOfParagraph(True)
            self.ctrl.select(c)
            return c.getString()
        return self.no_principal(f)

    def _paragrafo(self, inicio):
        def f():
            r = self._selecionar(inicio)
            if r is None:
                return None
            c = self.doc.getText().createTextCursorByRange(r.getStart())
            c.gotoStartOfParagraph(False)
            c.gotoEndOfParagraph(True)
            return c.getString()
        return self.no_principal(f)

    def _alteracoes(self):
        def f():
            e = self.doc.getRedlines().createEnumeration()
            n = 0
            while e.hasMoreElements():
                e.nextElement()
                n += 1
            return n
        return self.no_principal(f)

    def _esperar_ia(self, painel, limite=300):
        fim = time.time() + limite
        while time.time() < fim and painel.pedido is not None:
            time.sleep(0.3)
        time.sleep(0.6)
        return painel.pedido is None

    def _txt(self, painel, nome, prop='Text'):
        return self.no_principal(lambda: getattr(painel.c[nome].getModel(), prop))

    # ---------- sem modelo ----------
    def ia_sem_modelo(self):
        g = self._gerente()
        self.no_principal(lambda: g.gravar(pasta=os.path.join(self.saida, 'ia-vazia'), modelo=''))
        painel = self._painel_ia()
        self.efeito('Painel Revisão com IA abre pela aba Revisão (comando "Revisão com IA")', painel is not None)
        if painel is None:
            return
        self.no_principal(painel.atualizar)
        estado = self._txt(painel, 'estado', 'Label')
        self._novo_paragrafo('Texto para conferir que o editor funciona sem IA.')
        antes = self._paragrafo('Texto para conferir')
        self.acionar_teclado(painel.c['pedir'])
        depois = self._paragrafo('Texto para conferir')
        self.efeito('Sem modelo: o painel explica que a IA é opcional e local; pedir não altera nada',
                    'não instalada' in estado and 'opcional' in estado and antes == depois and painel.pedido is None, estado)
        self.no_principal(lambda: self.ctrl.getViewCursor().gotoEnd(False))
        self.focar_documento()
        self.digitar(' sem IA')
        # a correção automática põe maiúscula depois do ponto ("Sem IA"): a comparação ignora maiúsculas
        self.efeito('Sem modelo: digitação normal no documento', self.ultima_linha().lower().endswith('sem ia'), self.ultima_linha()[-40:])
        sem, nomes = self._nomes_acessiveis_painel(painel)
        self.efeito('Acessibilidade: controles do painel Revisão com IA com nome acessível', not sem,
                    'sem nome: ' + (', '.join(sem) or 'nenhum'))

    def _nomes_acessiveis_painel(self, painel):
        def f():
            r = {}
            for n, ctl in painel.c.items():
                if n.startswith('rotulo') or n in ('estado', 'avisos'):          # rótulos (textos fixos)
                    continue
                peer = ctl.getPeer()
                if peer is not None and hasattr(peer, 'isVisible') and not peer.isVisible():
                    continue                    # escondido (ex.: lista de títulos): o leitor de tela não chega a ele
                try:
                    r[n] = ctl.getAccessibleContext().getAccessibleName()
                except Exception:
                    r[n] = ''
            return r
        nomes = self.no_principal(f)
        return [n for n, v in nomes.items() if not (v or '').strip()], nomes

    # ---------- com modelo ----------
    def ia_fluxo(self):
        pasta, modelo = self.spec.get('ia_pasta'), self.spec.get('ia_modelo')
        g = self._gerente()
        if not pasta or not modelo:
            self.efeito('IA com modelo: pasta e modelo não informados ao teste', False)
            return
        self.no_principal(lambda: g.gravar(pasta=pasta, modelo=modelo, controlada=True))
        painel = self._painel_ia()
        if painel is None:
            self.efeito('Painel Revisão com IA abre', False)
            return
        self.no_principal(painel.atualizar)
        self.efeito('Com modelo instalado: o painel mostra o modelo em uso', g.pronto() and 'pronta' in self._txt(painel, 'estado', 'Label'),
                    self._txt(painel, 'estado', 'Label'))

        # pedido, digitação durante a análise, aceitar como alteração controlada, Ctrl+Z
        self._novo_paragrafo(FRASE)
        self._novo_paragrafo('Anotações:')          # onde a pessoa continua escrevendo enquanto a IA trabalha
        self._selecionar_paragrafo(FRASE[:30])
        t0 = time.time()
        self.acionar_teclado(painel.c['pedir'])
        ocupado = painel.pedido is not None
        self.no_principal(lambda: self.ctrl.getViewCursor().gotoEnd(False))
        self.focar_documento()
        a = time.time()
        self.digitar(' digitando enquanto a IA trabalha', intervalo=0.05)
        digitacao = time.time() - a - 0.8
        digitado = self.ultima_linha().lower().endswith('digitando enquanto a ia trabalha')
        terminou = self._esperar_ia(painel)
        segundos = time.time() - t0
        sug = self._txt(painel, 'sugestao')
        orig = self._txt(painel, 'original')
        avisos = self._txt(painel, 'avisos', 'Label')
        aceitar = self._txt(painel, 'aceitar', 'Enabled')
        self.res.setdefault('medidas_ia', {}).update(pedido_s=round(segundos, 1), digitacao_33_teclas_s=round(digitacao, 2))
        self.efeito('Revisar seleção pelo teclado: a IA trabalha em segundo plano e a digitação no documento continua',
                    ocupado and digitado and digitacao < 33 * 0.05 + 3, f'33 teclas em {digitacao:.1f} s durante a análise')
        self.efeito('Painel mostra original e sugestão, com a conferência de preservação; Aceitar liberado',
                    terminou and orig == FRASE and sug and sug != FRASE and 'mostram' in sug and aceitar and 'preservados' in avisos,
                    f'{segundos:.0f} s: {sug!r} | {avisos}')
        self._capturar('AY ESCREVA', 'painel-ia')
        self.acionar_teclado(painel.c['aceitar'])
        alt = self._alteracoes()
        estado = self._txt(painel, 'estado', 'Label')
        self.efeito('Aceitar aplica como alteração controlada (aceitar ou rejeitar em Revisão › Alterações)',
                    alt > 0 and 'alteração controlada' in estado, f'{alt} marcas; {estado}')
        self.focar_documento()
        self.ctrl_z()
        self.efeito('Ctrl+Z desfaz a sugestão inteira de uma vez', self._alteracoes() == 0 and self._paragrafo(FRASE[:30]) == FRASE,
                    self._paragrafo(FRASE[:30]))

        # rejeitar
        self._selecionar_paragrafo(FRASE[:30])
        self.acionar_teclado(painel.c['pedir'])
        self._esperar_ia(painel)
        self.acionar_teclado(painel.c['rejeitar'])
        self.efeito('Rejeitar descarta a sugestão sem alterar o documento',
                    self._paragrafo(FRASE[:30]) == FRASE and self._alteracoes() == 0 and not self._txt(painel, 'sugestao'),
                    self._txt(painel, 'estado', 'Label'))

        # trecho alterado durante a análise
        self._selecionar_paragrafo(FRASE[:30])
        self.acionar_teclado(painel.c['pedir'])

        def editar():
            r = self._selecionar('maioria')
            r.setString('grande maioria')
        self.no_principal(editar)
        self._esperar_ia(painel)
        if self._txt(painel, 'aceitar', 'Enabled'):
            self.acionar_teclado(painel.c['aceitar'])
        estado = self._txt(painel, 'estado', 'Label')
        self.efeito('Trecho editado durante a análise: a sugestão não é aplicada',
                    'grande maioria dos participantes concordaram' in (self._paragrafo('Os dados mostra') or '') and self._alteracoes() == 0,
                    estado)

        # cancelar
        self._novo_paragrafo(LONGO)
        self._selecionar_paragrafo(LONGO[:40])
        self.acionar_teclado(painel.c['pedir'])
        time.sleep(1.5)
        a = time.time()
        self.acionar_teclado(painel.c['cancelar'])
        self._esperar_ia(painel, 30)
        cancelou = time.time() - a
        estado = self._txt(painel, 'estado', 'Label')
        self.efeito('Cancelar pelo teclado interrompe a IA sem alterar nada', painel.pedido is None and 'cancelado' in estado
                    and self._alteracoes() == 0, f'{cancelou:.1f} s; {estado}')

        # rede: o servidor só fala com este computador
        srv = g.servidor
        pid = srv.pid() if srv is not None else None
        escuta, est = _conexoes(pid) if pid else ([], [])
        self.efeito('Servidor de IA só em 127.0.0.1, sem conexões com outros endereços',
                    pid and escuta and all(x.startswith('127.0.0.1:') for x, _ in escuta) and all(r.startswith('127.0.0.1:') for _, r in est),
                    f'escutando {escuta}; conexões {est}')

    # ---------- Gerenciar IA local ----------
    def ia_gerenciar(self):
        painel = self._painel_ia()
        if painel is None:
            self.efeito('Gerenciar IA local: painel não abriu', False)
            return
        self.acionar_teclado(painel.c['gerenciar'])
        d = self._esperar_dialogo('gerenciar_ia')
        self.efeito('Gerenciar IA local abre pelo painel (teclado)', d is not None)
        if d is None:
            return
        self._capturar('Gerenciar IA local', 'dialogo-gerenciar-ia')
        sem, nomes = self._nomes_acessiveis(d)
        self.efeito('Acessibilidade: controles de Gerenciar IA local com nome acessível', not sem, 'sem nome: ' + (', '.join(sem) or 'nenhum'))
        n = self.no_principal(lambda: d.c('modelos').getItemCount())
        detalhe = self.no_principal(lambda: d.m('detalhe').Text)
        espaco = self.no_principal(lambda: d.m('espaco').Label)
        explica = self.no_principal(lambda: d.m('explica').Label)
        self.efeito('Gerenciar IA local: modelos com licença, tamanho, origem e espaço livre; explica que é opcional e local',
                    n >= 1 and 'Licença' in detalhe and 'Tamanho do download' in detalhe and 'Espaço livre' in espaco
                    and 'opcional' in explica and 'nada é enviado' in explica, f'{n} modelos | {espaco}')
        self._teclado_dialogo(d, 'modelos', 'detalhe', 'Gerenciar IA local')
        self.acionar_teclado(d.c('fechar'))
        self.efeito('Gerenciar IA local fecha sem baixar nada', self._sem_dialogos())

    # ---------- download real pelo botão "Baixar…" ----------
    def _confirmar(self, botao='yes', limite=15):
        """Espera a caixa de pergunta ou aviso abrir e clica no botão pelo nome ('yes', 'no', 'ok'), como a pessoa faria.
        (Enter não serve: na pergunta Sim/Não o botão padrão não é o Sim.)"""
        fim = time.time() + limite
        time.sleep(0.5)
        vistos = set()
        while time.time() < fim:
            try:
                t = self.topo()
                filhos = set(t.getChildren())
                vistos = filhos
                if botao in filhos:
                    t.getChild(botao).executeAction('CLICK', ())
                    time.sleep(0.8)
                    return True
            except Exception:
                pass
            time.sleep(0.3)
        self._log_rev(f'confirmar: botão {botao} não apareceu (controles: {sorted(vistos)[:20]})')
        return False

    def _abrir_gerenciar(self, painel):
        self.acionar_teclado(painel.c['gerenciar'])
        return self._esperar_dialogo('gerenciar_ia')

    def _rotulo(self, d, nome):
        return self.no_principal(lambda: d.m(nome).Label)

    def _baixando(self, d):
        return self.no_principal(lambda: bool(d.m('cancelar').Enabled))

    def _acompanhar(self, d, ate, limite, historico):
        """Lê a situação do download a cada 0,5 s até ate(texto) ser verdadeiro ou o download parar."""
        import ay_dialogos
        fim = time.time() + limite
        texto = ''
        while time.time() < fim:
            if d not in ay_dialogos.ATUAL:
                historico.append('(o diálogo foi fechado)')
                self._log_rev('acompanhar: o diálogo Gerenciar IA local fechou durante a espera')
                return texto
            texto = self._rotulo(d, 'situacao')
            if not historico or historico[-1] != texto:
                historico.append(texto)
            if ate(texto) or (not self._baixando(d) and len(historico) > 2):
                return texto
            time.sleep(0.5)
        return texto

    def ia_download(self):
        import re
        import shutil
        P = self._P()
        IA = P.IA
        g = self._gerente()
        pasta = self.spec.get('ia_pasta_download') or os.path.join(os.path.dirname(self.saida), 'ia-download-teste')
        shutil.rmtree(pasta, ignore_errors=True)
        cat = IA.catalogo()
        m = next(x for x in cat['modelos'] if x.get('recomendado'))
        arq = os.path.join(pasta, 'modelos', m['arquivo'])
        self.no_principal(lambda: g.gravar(pasta=pasta, modelo=''))
        painel = self._painel_ia()
        d = self._abrir_gerenciar(painel)
        if d is None:
            self.efeito('Download real: Gerenciar IA local abre', False)
            return
        detalhe = self.no_principal(lambda: d.m('detalhe').Text)
        self.efeito('Download real: antes, o modelo aparece como não instalado, com tamanho e espaço livre',
                    'Situação: não instalado' in detalhe and 'falta baixar' in self._rotulo(d, 'espaco'), self._rotulo(d, 'espaco'))

        # pasta numa unidade inexistente: aviso na hora, nada é baixado
        livres = [f'{l}:\\' for l in 'ZYXWVUTSRQ' if not os.path.exists(f'{l}:\\')]
        self.no_principal(lambda: d.c('pasta').setText(livres[0] + 'IA'))
        time.sleep(0.6)
        aviso = self._rotulo(d, 'espaco')
        self.acionar_teclado(d.c('baixar'))
        self._confirmar('ok')
        self.efeito('Download real: pasta inválida é avisada e nada começa', 'Pasta inválida' in aviso and not self._baixando(d), aviso)
        self.no_principal(lambda: d.c('pasta').setText(pasta))
        time.sleep(0.6)

        # começa, mostra progresso e é cancelado no meio
        hist = []
        t0 = time.time()
        self.acionar_teclado(d.c('baixar'))
        self._confirmar()
        txt = self._acompanhar(d, lambda t: re.search(r'Baixando modelo: (\d+(,\d)?) (MB|GB)', t) and _mb_de(t) >= 400, 900, hist)
        pct = [int(x) for t in hist if 'Baixando modelo' in t for x in re.findall(r'\((\d+)%\)', t)]
        self.efeito('Download real: progresso em texto, crescente (primeiro o motor, depois o modelo)',
                    any('Baixando motor' in t for t in hist) and pct == sorted(pct) and len(set(pct)) >= 3,
                    f'{len(hist)} mudanças; último: {txt}')
        self.acionar_teclado(d.c('cancelar'))
        fim = time.time() + 30
        while time.time() < fim and self._baixando(d):
            time.sleep(0.3)
        time.sleep(0.8)
        parte1 = IA.tamanho_parcial(arq)
        sit = self._rotulo(d, 'situacao')
        self.efeito('Download real: Cancelar para o download e guarda a parte baixada; o botão vira "Baixar o restante"',
                    not self._baixando(d) and parte1 >= 300 * 2**20 and not os.path.exists(arq) and 'guardados' in sit
                    and 'restante' in self._rotulo(d, 'baixar'), f'{parte1 // 2**20} MB guardados; {sit}')

        # fechar e reabrir: a parte continua lá; continuar e fechar o diálogo no meio
        self.acionar_teclado(d.c('fechar'))
        self._sem_dialogos()
        d = self._abrir_gerenciar(painel)
        detalhe = self.no_principal(lambda: d.m('detalhe').Text)
        self.efeito('Download real: ao reabrir o diálogo, o download incompleto aparece com o que já foi baixado',
                    'download incompleto' in detalhe and 'restante' in self._rotulo(d, 'baixar'), detalhe.splitlines()[-1])
        hist = []
        self.acionar_teclado(d.c('baixar'))
        self._confirmar()
        self._acompanhar(d, lambda t: 'Baixando modelo' in t and _mb_de(t) >= parte1 / 2**20 + 300, 900, hist)
        conferiu = any('Conferindo a parte já baixada' in t for t in hist)
        retomou = [t for t in hist if 'Baixando modelo' in t]
        primeiro = _mb_de(retomou[0]) if retomou else 0
        self.acionar_teclado(d.c('fechar'))
        self._sem_dialogos()
        time.sleep(3)
        parte2 = IA.tamanho_parcial(arq)
        self.efeito('Download real: continuar confere a parte guardada e segue de onde parou (não recomeça do zero)',
                    conferiu and primeiro >= parte1 / 2**20 - 2, f'guardado {parte1 // 2**20} MB; retomou em {primeiro:.0f} MB')
        self.efeito('Download real: fechar o diálogo durante o download interrompe e guarda o que já veio',
                    parte2 > parte1 and not os.path.exists(arq), f'{parte2 // 2**20} MB guardados')

        # concluir: confere o SHA-256, usa o modelo e faz uma revisão
        d = self._abrir_gerenciar(painel)
        hist = []
        self.acionar_teclado(d.c('baixar'))
        self._confirmar()
        txt = self._acompanhar(d, lambda t: 'baixado e conferido' in t or 'Falha' in t or 'não confere' in t, 2400, hist)
        total_s = time.time() - t0
        ok_arq = os.path.exists(arq) and os.path.getsize(arq) == m['tamanho'] and not os.path.exists(arq + '.parcial')
        self.res.setdefault('medidas_ia', {}).update(download_total_s=round(total_s), download_mb=round(m['tamanho'] / 2**20))
        self.efeito('Download real: termina, confere o SHA-256 do catálogo e deixa só o arquivo final',
                    'baixado e conferido' in txt and ok_arq, f'{txt} ({total_s / 60:.1f} min no total, com as interrupções)')
        usar = self.no_principal(lambda: bool(d.m('usar').Enabled))
        self.acionar_teclado(d.c('usar'))
        cfg = self.no_principal(g.config)
        self.efeito('Download real: "Usar este modelo" passa a valer para os pedidos', usar and cfg['modelo'] == m['id'] and cfg['pasta'] == pasta,
                    cfg)
        self.acionar_teclado(d.c('fechar'))
        self._sem_dialogos()
        self._novo_paragrafo('O relatorio foi entregue a coordenação ontem.')
        self._selecionar_paragrafo('O relatorio foi entregue')
        self.acionar_teclado(painel.c['pedir'])
        self._esperar_ia(painel, 600)
        sug = self._txt(painel, 'sugestao')
        self.efeito('Download real: o modelo baixado pelo botão responde a uma revisão', 'relatório' in sug, sug)
        self.acionar_teclado(painel.c['rejeitar'])

        # remover apaga o modelo do disco
        d = self._abrir_gerenciar(painel)
        self.acionar_teclado(d.c('remover'))
        self._confirmar()
        self.efeito('Download real: "Remover" apaga o modelo do disco', not os.path.exists(arq), self._rotulo(d, 'situacao'))
        self.acionar_teclado(d.c('fechar'))
        self._sem_dialogos()
        self.no_principal(g.parar)
        shutil.rmtree(pasta, ignore_errors=True)

    # ---------- entrega D: documento inteiro, títulos, explicar, referências e consistência ----------
    DOC_D = [('1 INTRODUÇÃO', 'Heading 1'),
             ('Os dados mostra que a maioria dos participantes concordaram com a proposta, segundo Silva (2019).', None),
             ('A pesquisa foi feita em 2024 e a equipe entregou o relatorio a diretora no prazo combinado.', None),
             ('Os questionários foram aplicados por e-mail e as respostas foram analizadas pela equipe.', None),
             ('O email de convite explicava o objetivo e o prazo da pesquisa para todos os servidores.', None),
             ('REFERÊNCIAS', 'Heading 1'),
             ('SILVA, Maria. Custos. Brasília: Ed. UnB, 2019.', None),
             ('SOUZA, Paulo. Debate. Curitiba: UFPR, 2018. https://exemplo.org/debate', None)]

    def _preparar_doc_d(self):
        from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK

        def f():
            t = self.doc.getText()
            t.setString('')
            for i, (txt, est) in enumerate(self.DOC_D):
                if i:
                    t.insertControlCharacter(t.getEnd(), PARAGRAPH_BREAK, False)
                t.insertString(t.getEnd(), txt, False)
            e = t.createEnumeration()
            for txt, est in self.DOC_D:
                p = e.nextElement()
                p.ParaStyleName = est or 'Standard'
        self.no_principal(f)

    def _textos(self):
        def f():
            r = []
            e = self.doc.getText().createEnumeration()
            while e.hasMoreElements():
                p = e.nextElement()
                if p.supportsService('com.sun.star.text.Paragraph'):
                    r.append((p.getString(), p.ParaStyleName))
            return r
        return self.no_principal(f)

    def _escolher_acao(self, painel, acao):
        P = self._P()
        i = P.ACOES.index(acao)
        self.no_principal(lambda: painel.c['acao'].selectItemPos(i, True))
        time.sleep(0.3)

    def ia_documento(self):
        pasta, modelo = self.spec.get('ia_pasta'), self.spec.get('ia_modelo')
        g = self._gerente()
        self.no_principal(lambda: g.gravar(pasta=pasta, modelo=modelo, controlada=True))
        self._preparar_doc_d()
        antes = self._textos()
        painel = self._painel_ia()
        if painel is None:
            self.efeito('Entrega D: painel Revisão com IA abre', False)
            return
        self.no_principal(painel.atualizar)

        # revisar o documento inteiro
        t0 = time.time()
        self.acionar_teclado(painel.c['documento'])
        self._esperar_ia(painel, 600)
        est = self._txt(painel, 'estado', 'Label')
        n_lista = self.no_principal(lambda: painel.c['lista'].getItemCount())
        self.res.setdefault('medidas_ia', {}).update(documento_inteiro_s=round(time.time() - t0, 1), documento_sugestoes=n_lista)
        self.efeito('Revisar o documento inteiro (teclado): em segundo plano, com sugestões na lista e o documento sem mudança',
                    'concluída' in est and n_lista >= 2 and self._textos() == antes, f'{n_lista} sugestões; {est}')
        self.no_principal(lambda: (painel.c['lista'].selectItemPos(0, True), painel._mudou_lista()))
        orig, sug = self._txt(painel, 'original'), self._txt(painel, 'sugestao')
        self.acionar_teclado(painel.c['ir'])
        selecionado = self.no_principal(lambda: self.ctrl.getSelection().getByIndex(0).getString())
        self.efeito('Escolher na lista mostra original × sugestão; "Ir ao parágrafo" seleciona o parágrafo no documento',
                    orig and sug and orig != sug and selecionado == orig, selecionado[:60])
        self.acionar_teclado(painel.c['aceitar'])
        alt = self._alteracoes()
        n2 = self.no_principal(lambda: painel.c['lista'].getItemCount())
        self.efeito('Aceitar aplica só aquele parágrafo (alteração controlada) e tira a sugestão da lista',
                    alt > 0 and n2 == n_lista - 1, f'{alt} marcas; lista {n_lista} → {n2}')
        self.focar_documento()
        self.ctrl_z()
        self.efeito('Ctrl+Z desfaz a sugestão aceita da lista', self._alteracoes() == 0 and self._textos() == antes)
        if n2:
            self.no_principal(lambda: (painel.c['lista'].selectItemPos(0, True), painel._mudou_lista()))
            self.acionar_teclado(painel.c['rejeitar'])
            n3 = self.no_principal(lambda: painel.c['lista'].getItemCount())
            self.efeito('Rejeitar tira a sugestão da lista sem mudar o documento', n3 == n2 - 1 and self._textos() == antes)
        # cancelar a revisão do documento
        self.acionar_teclado(painel.c['documento'])
        time.sleep(2.5)
        self.acionar_teclado(painel.c['cancelar'])
        self._esperar_ia(painel, 60)
        est = self._txt(painel, 'estado', 'Label')
        self.efeito('Cancelar a revisão do documento para logo e mantém o documento', 'cancelada' in est and self._textos() == antes, est)

        # sugerir títulos e inserir
        self._selecionar_paragrafo('A pesquisa foi feita em 2024')
        self._escolher_acao(painel, 'titulos')
        self.acionar_teclado(painel.c['pedir'])
        self._esperar_ia(painel, 300)
        opcoes = self.no_principal(lambda: list(painel.c['opcoes'].getModel().StringItemList))
        visivel = self.no_principal(lambda: painel.c['opcoes'].isVisible() if hasattr(painel.c['opcoes'], 'isVisible') else True)
        rot = self._txt(painel, 'aceitar', 'Label')
        self.efeito('Sugerir títulos (teclado): lista de títulos para escolher; o botão vira "Inserir título"',
                    1 <= len(opcoes) <= 3 and 'Inserir' in rot and visivel, opcoes)
        sem, nomes = self._nomes_acessiveis_painel(painel)
        self.efeito('Acessibilidade no modo títulos: a lista de títulos visível tem nome acessível',
                    'opcoes' in nomes and 'opcoes' not in sem, f'opcoes: "{nomes.get("opcoes", "(escondida)")}"; sem nome: {sem}')
        if opcoes:
            self.acionar_teclado(painel.c['aceitar'])
            depois = self._textos()
            inserido = any(t == opcoes[0] and est.startswith(('Heading', 'Título')) for t, est in depois)
            self.focar_documento()
            self.ctrl_z()
            self.efeito('Inserir título cria o título antes do trecho, no estilo dos títulos; Ctrl+Z remove',
                        inserido and self._alteracoes() == 0 and self._textos() == antes, [t for t, _ in depois[:5]])

        # explicar (só leitura)
        self._selecionar_paragrafo('Os dados mostra')
        self._escolher_acao(painel, 'explicar')
        self.acionar_teclado(painel.c['pedir'])
        self._esperar_ia(painel, 300)
        exp = self._txt(painel, 'sugestao')
        avisos = self._txt(painel, 'avisos', 'Label')
        aceitar = self._txt(painel, 'aceitar', 'Enabled')
        self.efeito('Explicar: mostra a explicação, avisa que é só leitura e não deixa aplicar nada',
                    len(exp) > 30 and 'só leitura' in avisos and not aceitar and self._textos() == antes, exp[:120])
        self.acionar_teclado(painel.c['rejeitar'])
        self._escolher_acao(painel, 'revisar')

        # conferir referências e consistência (diálogos)
        for comando, nome, achar in (('ayescreva:ConferirReferencias', 'Conferir referências', 'Disponível em'),
                                     ('ayescreva:ConferirConsistencia', 'Conferir consistência', 'e-mail')):
            self._abrir_async(comando)
            d = self._esperar_dialogo('achados')
            if d is None:
                self.efeito(f'{nome} abre (aba Referências)', False)
                continue
            self._capturar(nome, 'dialogo-' + nome.split()[1].replace('ê', 'e').replace('ó', 'o'))
            itens = self.no_principal(lambda: list(d.m('lista').StringItemList))
            alvo = next((k for k, t in enumerate(itens) if achar in t), 0)
            self.no_principal(lambda: (d.c('lista').selectItemPos(alvo, True), None))
            self.no_principal(lambda: d.m('detalhe').Text)
            self.acionar_teclado(d.c('lista'))
            time.sleep(0.3)
            self.acionar_teclado(d.c('ir'))
            sel = self.no_principal(lambda: self.ctrl.getSelection().getByIndex(0).getString())
            sem, _ = self._nomes_acessiveis(d)
            self.efeito(f'{nome}: lista o problema plantado, "Ir para" seleciona o trecho, controles com nome acessível',
                        any(achar in t for t in itens) and sel and not sem and self._textos() == antes,
                        f'{len(itens)} apontamentos; selecionado: {sel[:50]}; sem nome: {sem}')
            self.acionar_teclado(d.c('fechar'))
            self._sem_dialogos()


def _mb_de(texto):
    """Primeiro valor 'N MB' ou 'N,N GB' do texto de progresso, em MB."""
    import re
    m = re.search(r'(\d+(?:,\d+)?) (MB|GB)', texto or '')
    if not m:
        return 0
    v = float(m.group(1).replace(',', '.'))
    return v * 1024 if m.group(2) == 'GB' else v


def _conexoes(pid):
    out = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True, text=True, errors='replace').stdout
    escuta, est = [], []
    for linha in out.splitlines():
        c = linha.split()
        if len(c) >= 5 and c[-1] == str(pid):
            (escuta if c[3].upper().startswith(('LISTEN', 'ESCUTA')) else est).append((c[1], c[2]))
    return escuta, est
