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


def _conexoes(pid):
    out = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True, text=True, errors='replace').stdout
    escuta, est = [], []
    for linha in out.splitlines():
        c = linha.split()
        if len(c) >= 5 and c[-1] == str(pid):
            (escuta if c[3].upper().startswith(('LISTEN', 'ESCUTA')) else est).append((c[1], c[2]))
    return escuta, est
