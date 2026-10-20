# -*- coding: utf-8 -*-
"""Testes pela interface da revisão de texto do AY (entrega A), de dentro do aplicativo.

Digitação real pelo robô do toolkit (o mesmo caminho do teclado), efeitos conferidos no documento. Toda alteração
do documento feita pelo próprio teste roda na thread principal (no_principal): chamadas UNO de uma thread Python
durante a carga do documento travaram o motor (docs/REVISAO-E-IA.md §4).
SPDX-License-Identifier: MPL-2.0
"""
import ctypes
import os
import re
import threading
import time
import traceback

import uno

PARAGRAFO = 0                         # com.sun.star.text.ControlCharacter.PARAGRAPH_BREAK
TEXTO_PAINEL = ('Isso foi um teste com palavrass erradas. Fui a praia há dois anos atrás. '
                'Eu vou pra casa a fim de que possamos conversar.')


def _codigo(ch):
    if 'a' <= ch <= 'z':
        return 512 + ord(ch) - ord('a'), 0
    if 'A' <= ch <= 'Z':
        return 512 + ord(ch) - ord('A'), 1
    if '0' <= ch <= '9':
        return 256 + ord(ch) - ord('0'), 0
    return {' ': (1284, 0), '.': (1291, 0), ',': (1292, 0)}.get(ch, (0, 0))


def memoria_mb():
    class PMC(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong), ('PeakWorkingSetSize', ctypes.c_size_t),
                    ('WorkingSetSize', ctypes.c_size_t), ('a', ctypes.c_size_t), ('b', ctypes.c_size_t),
                    ('c', ctypes.c_size_t), ('d', ctypes.c_size_t), ('PagefileUsage', ctypes.c_size_t),
                    ('PeakPagefileUsage', ctypes.c_size_t)]
    k32 = ctypes.windll.kernel32
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    pmc = PMC()
    pmc.cb = ctypes.sizeof(PMC)
    k32.K32GetProcessMemoryInfo(ctypes.c_void_p(k32.GetCurrentProcess()), ctypes.byref(pmc), pmc.cb)
    return round(pmc.WorkingSetSize / 2**20), round(pmc.PeakWorkingSetSize / 2**20)


class RevisaoMixin:
    # ---------- infraestrutura ----------
    def no_principal(self, f, limite=60):
        feito = threading.Event()
        res = {}

        def g():
            try:
                res['v'] = f()
            except Exception:
                res['e'] = traceback.format_exc()
            finally:
                feito.set()
        self.postar(g)
        if not feito.wait(limite):
            raise RuntimeError('a thread principal não respondeu em %d s' % limite)
        if 'e' in res:
            raise RuntimeError(res['e'][-800:])
        return res.get('v')

    def rev(self):
        import ay_revisao
        return ay_revisao.Revisao.obter(self.ctx)

    def efeito(self, funcao, ok, detalhe=''):
        self.res['efeitos'].append({'funcao': funcao, 'ok': bool(ok), 'detalhe': str(detalhe)})
        self._log_rev(f'{"OK" if ok else "FALHA"} {funcao}: {detalhe}')

    def _log_rev(self, m):
        try:
            with open(os.path.join(os.environ.get('TEMP', '.'), 'ay-testes-ui.log'), 'a', encoding='utf-8') as f:
                f.write(time.strftime('%H:%M:%S ') + 'revisão: ' + m + chr(10))
        except Exception:
            pass

    def _robo(self):
        tk = self.smgr.createInstanceWithContext('com.sun.star.awt.Toolkit', self.ctx)
        return tk.queryInterface(uno.getTypeByName('com.sun.star.awt.XToolkitRobot'))

    def focar_documento(self):
        def f():
            self.frame.activate()
            self.frame.getContainerWindow().setFocus()
            self.frame.getComponentWindow().setFocus()
        self.no_principal(f)
        time.sleep(0.3)

    def digitar(self, texto, intervalo=0.05):
        robo = self._robo()
        janela = self.frame.getContainerWindow()
        for ch in texto:
            codigo, shift = _codigo(ch)
            ev = uno.createUnoStruct('com.sun.star.awt.KeyEvent')
            ev.Source, ev.KeyCode, ev.KeyChar, ev.Modifiers = janela, codigo, ch, shift
            robo.keyPress(ev)
            robo.keyRelease(ev)
            time.sleep(intervalo)
        time.sleep(0.8)                     # a correção é aplicada no ciclo seguinte da interface

    def ctrl_z(self):
        robo = self._robo()
        ev = uno.createUnoStruct('com.sun.star.awt.KeyEvent')
        ev.Source, ev.KeyCode, ev.KeyChar, ev.Modifiers = self.frame.getContainerWindow(), 537, chr(26), 2
        robo.keyPress(ev)
        robo.keyRelease(ev)
        time.sleep(0.8)

    def acionar_teclado(self, controle):
        """Foca o controle do painel e pressiona Espaço de verdade (como alguém usando só o teclado)."""
        self.no_principal(lambda: controle.setFocus())
        time.sleep(0.3)
        robo = self._robo()
        ev = uno.createUnoStruct('com.sun.star.awt.KeyEvent')
        ev.Source, ev.KeyCode, ev.KeyChar = controle.getPeer(), 1284, ' '
        robo.keyPress(ev)
        robo.keyRelease(ev)
        time.sleep(0.4)

    def nova_linha(self, lingua='pt', pais='BR', texto=''):
        def f():
            t = self.doc.Text
            t.insertControlCharacter(t.getEnd(), PARAGRAFO, False)
            c = t.createTextCursorByRange(t.getEnd())
            par = c.createEnumeration().nextElement()
            loc = uno.createUnoStruct('com.sun.star.lang.Locale')
            loc.Language, loc.Country = lingua, pais
            par.CharLocale = loc
            if texto:
                t.insertString(t.getEnd(), texto, False)
            self.ctrl.getViewCursor().gotoEnd(False)
        self.no_principal(f)
        self.focar_documento()

    def ultima_linha(self):
        def f():
            c = self.doc.Text.createTextCursorByRange(self.doc.Text.getEnd())
            c.gotoStartOfParagraph(True)
            return c.getString()
        return self.no_principal(f)

    def despachar(self, comando):
        d = self.smgr.createInstanceWithContext('com.sun.star.frame.DispatchHelper', self.ctx)
        self.no_principal(lambda: d.executeDispatch(self.frame, comando, '', 0, ()))

    # ---------- correção automática ----------
    def revisao_digitacao(self):
        rev = self.rev()
        self.no_principal(lambda: rev.gravar_config(CorrecaoAutomatica=True))
        self.nova_linha()
        self.digitar('Eu nao sei se voce vem tambem. ')
        linha = self.ultima_linha()
        self.efeito('Correção automática ao digitar (nao, voce, tambem)', linha.startswith('Eu não sei se você vem também.'), repr(linha))
        self.digitar('X')
        linha = self.ultima_linha()
        self.efeito('Cursor preservado: o texto seguinte entra depois da palavra corrigida', linha.endswith('também. X'), repr(linha[-20:]))
        self.nova_linha()
        self.digitar('nao voce tambem geito ', intervalo=0.005)
        linha = self.ultima_linha()
        self.efeito('Digitação rápida: todas as palavras corrigidas, nenhuma letra perdida', linha == 'não você também jeito ', repr(linha))
        self.nova_linha()
        self.digitar('naoo')
        linha = self.ultima_linha()
        self.efeito('Nada muda enquanto a palavra ainda está sendo digitada', linha == 'naoo', repr(linha))

    def revisao_desfazer(self):
        rev = self.rev()
        self.nova_linha()
        self.digitar('Ele disse nao ')
        antes = self.ultima_linha()
        self.ctrl_z()
        depois = self.ultima_linha()
        self.efeito('Ctrl+Z desfaz só a correção (o espaço digitado fica)', antes == 'Ele disse não ' and depois == 'Ele disse nao ',
                    f'{antes!r} → {depois!r}')
        barra = self.no_principal(lambda: bool(self.ctrl.hasInfobar('ay-desfeita')))
        self.efeito('Ao desfazer, o AY oferece "Não corrigir novamente" (barra de informação)', barra)
        self.despachar('ayescreva:NaoCorrigir?palavra=nao')          # o mesmo comando do botão da barra
        lembrado = 'nao' in rev.config['NaoCorrigir']
        self.nova_linha()
        self.digitar('Outra vez nao ')
        linha = self.ultima_linha()
        self.efeito('"Não corrigir novamente" fica gravado e é respeitado', lembrado and linha == 'Outra vez nao ', repr(linha))
        self.no_principal(lambda: rev.remover_nao_corrigir('nao'))
        self.nova_linha()
        self.digitar('De novo nao ')
        self.efeito('Removida da lista, a palavra volta a ser corrigida', self.ultima_linha() == 'De novo não ', repr(self.ultima_linha()))

    def revisao_protecoes(self):
        rev = self.rev()
        self.nova_linha()
        self.digitar('Ontem o Voce, a NAO e o naO viram 12/10/2025 e nao2; ele disse "nao sei" e saiu. ')
        linha = self.ultima_linha()
        intactos = all(t in linha for t in ('Voce', 'NAO', 'naO', '12/10/2025', 'nao2')) and bool(re.search(r'[“"]nao sei[”"]', linha))
        self.efeito('Proteções: nome próprio, sigla, grafia mista, data, palavra com número e citação não mudam', intactos, repr(linha))
        self.nova_linha('en', 'US')
        self.digitar('I said nao ')
        self.efeito('Texto marcado em inglês não é corrigido', self.ultima_linha() == 'I said nao ', repr(self.ultima_linha()))
        self.no_principal(lambda: rev.adicionar_ao_dicionario('geito'))
        self.nova_linha()
        self.digitar('Tem geito ')
        linha = self.ultima_linha()
        self.no_principal(lambda: rev.remover_do_dicionario('geito'))
        self.efeito('Palavra do dicionário pessoal não é corrigida', linha == 'Tem geito ', repr(linha))
        self.no_principal(lambda: rev.gravar_config(CorrecaoAutomatica=False))
        self.nova_linha()
        self.digitar('Sem correcao nao ')
        linha = self.ultima_linha()
        self.no_principal(lambda: rev.gravar_config(CorrecaoAutomatica=True))
        self.efeito('Correção automática pode ser desligada', linha == 'Sem correcao nao ', repr(linha))

    # ---------- painel ----------
    def _painel(self, abrir=True):
        rev = self.rev()
        p = rev.painel_do_quadro(self.frame)
        if p is None and abrir:
            self.despachar('ayescreva:Assistente')
            limite = time.time() + 10
            while time.time() < limite and p is None:
                time.sleep(0.3)
                p = rev.painel_do_quadro(self.frame)
        return p

    def _verificar(self, painel, limite=120):
        painel.ultima = None
        self.acionar_teclado(painel.c['verificar_documento'])
        fim = time.time() + limite
        while time.time() < fim and painel.ultima is None:
            time.sleep(0.2)
        return painel.ultima

    def _escolher(self, painel, cond):
        idx = next((i for i, a in enumerate(painel.achados) if cond(a)), -1)
        if idx >= 0:
            self.no_principal(lambda: (painel.c['ocorrencias'].selectItemPos(idx, True), painel._mostrar_achado(idx, True)))
        return idx

    def revisao_painel(self):
        rev = self.rev()
        self.no_principal(lambda: rev.gravar_config(Estilo=False, Gramatica=True))
        self.nova_linha(texto=TEXTO_PAINEL)
        painel = self._painel()
        self.efeito('Painel Assistente AY abre pela aba Revisão (comando "Assistente AY")', painel is not None)
        if painel is None:
            return

        def nomes():
            r = {}
            tipos = [t.typeName for t in painel.c['verificar_documento'].getPeer().getTypes()] if hasattr(painel.c['verificar_documento'].getPeer(), 'getTypes') else []
            r['_tipos'] = (' '.join(x.split('.')[-1] for x in tipos)[:300], 0, '')
            for n, ctl in painel.c.items():
                try:
                    ac = ctl.getAccessibleContext()          # o controle UNO expõe a acessibilidade da janela
                    nome = ac.getAccessibleName()
                    if not nome and hasattr(ctl, 'getAccessibleContext'):
                        nome = ctl.getAccessibleContext().getAccessibleName()
                    r[n] = (nome, ac.getAccessibleRole(), ac.getAccessibleDescription())
                except Exception as e:
                    r[n] = ('', -1, str(e)[:80])
            return r
        acc = self.no_principal(nomes)
        interativos = [n for n in ('ortografia', 'correcao', 'gramatica', 'estilo', 'verificar_selecao', 'verificar_documento',
                                   'cancelar', 'aplicar', 'ignorar', 'adicionar', 'nao_corrigir', 'reverter',
                                   'nao_corrigir_recente', 'dicionario', 'autocorrecao', 'ocorrencias', 'sugestoes', 'recentes')]
        sem_nome = [n for n in interativos if not acc.get(n, ('',))[0]]
        self._log_rev('tipos do par: ' + acc['_tipos'][0])
        rotulos = {'ocorrencias': 'Ocorrências', 'sugestoes': 'Sugestão', 'recentes': 'recentes'}
        errados = [n for n, r in rotulos.items() if r.lower() not in acc.get(n, ('',))[0].replace('~', '').lower()]
        self.efeito('Acessibilidade: listas anunciadas pelo próprio rótulo (não pelo título do painel)', not errados,
                    '; '.join(f'{n}="{acc.get(n, ("",))[0]}"' for n in rotulos))
        self.efeito('Acessibilidade: controles do painel com nome acessível', not sem_nome,
                    'sem nome: ' + (', '.join(sem_nome) or 'nenhum') + ' | ' + '; '.join(f'{n}="{acc[n][0]}" papel={acc[n][1]} desc="{str(acc[n][2])[:40]}"' for n in ('verificar_documento', 'estilo', 'ocorrencias', 'sugestoes') if n in acc))
        ult = self._verificar(painel)
        self._escolher(painel, lambda a: a['original'] == 'palavrass')     # as sugestões vêm ao escolher
        achados = list(painel.achados)
        orto = [a for a in achados if a['nivel'] == 'ortografia' and a['original'] == 'palavrass']
        gram = [a for a in achados if a['nivel'] == 'gramatica']
        est = [a for a in achados if a['nivel'] == 'estilo']
        self.efeito('Verificar documento pelo teclado: erro de ortografia listado com sugestões', bool(orto and orto[0]['sugestoes']),
                    f'{ult}; sugestões: {orto[0]["sugestoes"] if orto else "-"}')
        self.efeito('Gramática e pontuação: ocorrências com explicação curta', bool(gram) and all(a['mensagem'] for a in gram),
                    '; '.join(f'“{a["original"]}”: {a["mensagem"][:70]}' for a in gram[:4]))
        self.efeito('Estilo desligado por padrão: nenhuma sugestão de estilo', not est, f'{len(est)} sugestão(ões) de estilo')
        self.acionar_teclado(painel.c['estilo'])
        ligado = rev.config['Estilo']
        self._verificar(painel)
        est = [a for a in painel.achados if a['nivel'] == 'estilo']
        origs = {a['original'].lower() for a in est}
        self.efeito('Estilo ligado pelo teclado: concisão, formalidade e pleonasmo sugeridos', ligado and 'pra' in origs and 'a fim de que' in origs,
                    '; '.join(f'{a["categoria"]}: “{a["original"]}”' for a in est[:6]))
        idx = self._escolher(painel, lambda a: a['original'] == 'palavrass')
        sug = painel.achados[idx]['sugestoes'][0] if idx >= 0 else None
        self.acionar_teclado(painel.c['aplicar'])
        linha = self.ultima_linha()
        self.efeito('Aplicar troca o trecho pela sugestão no documento', idx >= 0 and 'palavrass' not in linha and sug in linha, f'sugestão {sug!r}')
        self.no_principal(lambda: self.doc.getUndoManager().undo())
        self.efeito('Desfazer volta o texto original', 'palavrass' in self.ultima_linha())
        self._verificar(painel)
        self._escolher(painel, lambda a: a['original'] == 'palavrass')
        self.acionar_teclado(painel.c['ignorar'])
        self._verificar(painel)
        self.efeito('Ignorar tira a palavra das verificações seguintes', not any(a['original'] == 'palavrass' for a in painel.achados))
        self.nova_linha(texto='Uma palavra inventada: zorbaquim.')
        self._verificar(painel)
        self._escolher(painel, lambda a: a['original'] == 'zorbaquim')
        self.acionar_teclado(painel.c['adicionar'])
        no_dic = 'zorbaquim' in self.no_principal(rev.palavras_pessoais)
        self._verificar(painel)
        some = not any(a['original'] == 'zorbaquim' for a in painel.achados)
        self.no_principal(lambda: rev.remover_do_dicionario('zorbaquim'))
        self.efeito('Adicionar ao dicionário pessoal grava a palavra e ela deixa de ser apontada', no_dic and some)
        self.no_principal(lambda: rev.gravar_config(Estilo=False))

    # ---------- perfil de desempenho ----------
    def revisao_perfil(self):
        """Mede, na thread principal, quanto custa cada parte da análise de um parágrafo (60 parágrafos)."""
        rev = self.rev()

        def medir():
            loc = uno.createUnoStruct('com.sun.star.lang.Locale')
            loc.Language, loc.Country = 'pt', 'BR'
            rev.preparar_lightproof(loc)
            t = {'enumerar_e_ler': 0.0, 'mapear': 0.0}
            tempos = {}
            enum = self.doc.Text.createEnumeration()
            n = 0
            achados = 0
            while enum.hasMoreElements() and n < 60:
                a = time.perf_counter()
                par = enum.nextElement()
                texto = par.getString()
                ploc = par.CharLocale
                t['enumerar_e_ler'] += time.perf_counter() - a
                res = rev.achados_paragrafo(texto, ploc, True, tempos, sugestoes=False)
                a = time.perf_counter()
                for x in res:
                    r = self.doc.Text.createTextCursorByRange(par.getStart())
                    r.goRight(x['inicio'], False)
                    r.goRight(x['tamanho'], True)
                    r.getString()
                t['mapear'] += time.perf_counter() - a
                achados += len(res)
                n += 1
            t.update(tempos)
            return n, achados, {k: round(v / max(1, n) * 1000, 1) for k, v in t.items()}, rev._lp_direto is not None
        n, achados, ms, direto = self.no_principal(medir, 300)
        self.efeito('Perfil de desempenho da análise (ms por parágrafo)', True, f'{n} parágrafos, {achados} ocorrências, Lightproof direto={direto}: {ms}')
        self.res.setdefault('medidas', {})['perfil_ms_por_paragrafo'] = ms

    # ---------- documento longo ----------
    def revisao_longo(self):
        rev = self.rev()
        self.no_principal(lambda: rev.gravar_config(Estilo=False))
        painel = self._painel()
        if painel is None:
            self.efeito('Documento longo: painel', False)
            return
        mem0 = memoria_mb()

        def pulsos(lista, parar):
            while not parar.is_set():
                t = time.time()
                feito = threading.Event()
                self.postar(lambda: feito.set())
                feito.wait(10)
                lista.append(time.time() - t)
                time.sleep(0.1)

        def resumo(lista):
            if not lista:
                return None
            o = sorted(lista)
            return {'n': len(o), 'media': sum(o) / len(o), 'p95': o[min(len(o) - 1, int(0.95 * len(o)))], 'pior': o[-1]}
        def medir(segundos):
            lista, parar_m = [], threading.Event()
            t = threading.Thread(target=pulsos, args=(lista, parar_m), daemon=True)
            t.start()
            time.sleep(segundos)
            parar_m.set()
            t.join(5)
            return lista
        # Referência: documento aberto, nada rodando. Depois, a mesma medida com a verificação em andamento, sem
        # outras ações (pular para o fim de um documento de 300 páginas força o motor a paginar tudo, o que atrasa
        # a interface por si só).
        self.no_principal(lambda: self.ctrl.getViewCursor().gotoEnd(False))
        time.sleep(2.0)
        base = medir(3.0)
        painel.ultima = None
        self.acionar_teclado(painel.c['verificar_documento'])
        time.sleep(1.0)
        latencias = medir(3.0)
        self.focar_documento()
        self.digitar(' nao ')
        durante = self.ultima_linha()
        self.efeito('Digitar durante a verificação: o texto entra e é corrigido', durante.lower().endswith(' não '), repr(durante[-12:]))
        t0 = time.time()
        self.acionar_teclado(painel.c['cancelar'])
        while time.time() - t0 < 5 and painel.ultima is None:
            time.sleep(0.1)
        cancelado = bool(painel.ultima and painel.ultima['cancelado'])
        self.efeito('Cancelar interrompe a verificação', cancelado, f'{painel.ultima}; {time.time() - t0:.2f} s até parar')
        rb, rv = resumo(base), resumo(latencias)
        fmt = lambda r: f"média {r['media']:.3f} s, 95% até {r['p95']:.3f} s, pior {r['pior']:.3f} s ({r['n']} medições)" if r else 'sem medições'
        self.efeito('Interface responde durante a verificação (atraso médio < 0,2 s e 95% < 0,4 s)',
                    bool(rv) and rv['media'] < 0.2 and rv['p95'] < 0.4, f'durante: {fmt(rv)} | sem verificação: {fmt(rb)}')
        media = rv['media'] if rv else None
        pior = rv['pior'] if rv else None
        ult = self._verificar(painel, limite=600)
        mem1 = memoria_mb()
        self.efeito('Documento longo verificado por completo', bool(ult and not ult['cancelado']),
                    f'{ult}; memória do processo {mem0[0]} → {mem1[0]} MB (pico {mem1[1]} MB)')
        self.res.setdefault('medidas', {})['documento_longo'] = {'resultado': ult, 'memoria_mb_antes': mem0, 'memoria_mb_depois': mem1,
                                                                  'latencia_media_s': media, 'latencia_pior_s': pior,
                                                                  'latencia_durante': rv, 'latencia_sem_verificacao': rb}

    # ---------- integridade ----------
    def _inventario(self, doc):
        def f():
            comentarios = 0
            e = doc.getTextFields().createEnumeration()
            while e.hasMoreElements():
                if e.nextElement().supportsService('com.sun.star.text.textfield.Annotation'):
                    comentarios += 1
            red = 0
            e = doc.getRedlines().createEnumeration()
            while e.hasMoreElements():
                e.nextElement()
                red += 1
            return {'tabelas': doc.getTextTables().getCount(), 'imagens': doc.getGraphicObjects().getCount(),
                    'notas': doc.getFootnotes().getCount(), 'notas_fim': doc.getEndnotes().getCount(),
                    'comentarios': comentarios, 'alteracoes': red}
        return self.no_principal(f)

    def revisao_integridade(self):
        inv0 = self._inventario(self.doc)
        self.no_principal(lambda: setattr(self.doc, 'RecordChanges', True))
        self.nova_linha()
        self.digitar('Texto controlado: nao ')
        linha = self.ultima_linha()
        inv1 = self._inventario(self.doc)
        self.efeito('Com controle de alterações ligado, a correção fica registrada como alteração',
                    'não' in linha and inv1['alteracoes'] > inv0['alteracoes'], f'{inv0["alteracoes"]} → {inv1["alteracoes"]} alterações; {linha!r}')
        pasta = os.path.dirname(uno.fileUrlToSystemPath(self.doc.getURL()))
        for ext, filtro in (('docx', 'MS Word 2007 XML'), ('odt', 'writer8')):
            destino = os.path.join(pasta, f'integridade.{ext}')
            url = uno.systemPathToFileUrl(destino)
            self.no_principal(lambda: self.doc.storeToURL(url, (self._pv('FilterName', filtro), self._pv('Overwrite', True))))

            def reabrir():
                return self.desktop.loadComponentFromURL(url, '_blank', 0, (self._pv('Hidden', True),))
            d2 = self.no_principal(reabrir)
            inv2 = self._inventario(d2)
            texto = self.no_principal(lambda: d2.Text.getString())
            self.no_principal(lambda: d2.close(True))
            iguais = all(inv2[k] == inv1[k] for k in ('tabelas', 'imagens', 'notas', 'notas_fim', 'comentarios'))
            self.efeito(f'{ext.upper()} com tabela, imagem, notas, comentário e alterações salvo e reaberto íntegro depois das correções',
                        iguais and inv2['alteracoes'] >= inv0['alteracoes'] and 'Texto controlado:' in texto and 'não' in texto,
                        f'antes {inv1} | reaberto {inv2}')

    @staticmethod
    def _pv(nome, valor):
        p = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
        p.Name, p.Value = nome, valor
        return p
