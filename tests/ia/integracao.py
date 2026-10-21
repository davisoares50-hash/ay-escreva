# -*- coding: utf-8 -*-
"""IA local no editor (entrega C): o caminho do painel "Revisão com IA" contra o motor real, por UNO.

Parte A (sem modelo, sempre roda): quais seleções são aceitas; a sugestão aplicada só nas diferenças, numa ação de
desfazer, preservando formatação, estilos de parágrafo e o histórico anterior; como alteração controlada (aceitar e
rejeitar todas); recusa quando o trecho mudou depois do pedido ou quando a sugestão junta parágrafos.
Parte B (com o motor e um modelo baixados): pedido real ao servidor local; o editor segue respondendo enquanto a IA
trabalha; edição do trecho durante a análise bloqueia a aplicação; cancelamento rápido (inclusive antes da primeira
palavra); servidor preso a 127.0.0.1 sem conexões externas; servidor encerrado quando o processo dono termina; memória.

Uso: "dist\\AY ESCREVA\\program\\python.exe" tests\\ia\\integracao.py [--pasta out\\ia] [--modelo qwen3-4b]
Sem o modelo, a parte B aparece como BLOQUEADA (não conta como aprovada).
SPDX-License-Identifier: MPL-2.0
"""
import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'tests' / 'uno'))
sys.path.insert(0, str(RAIZ / 'extensao' / 'ayescreva' / 'pythonpath'))
from ay_uno import Motor, PROGRAMA, SAIDA_TESTES, props, fechar  # noqa: E402
import ay_ia as IA  # noqa: E402
import ay_ia_texto as T  # noqa: E402
import ay_ia_painel as P  # noqa: E402

from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK  # noqa: E402

itens = []


def verificar(descricao, ok, detalhe='', situacao=None):
    situacao = situacao or ('ok' if ok else 'falha')
    itens.append({'ok': situacao == 'ok', 'situacao': situacao, 'verificacao': descricao, 'detalhe': str(detalhe)})
    marca = {'ok': 'OK  ', 'falha': 'FALHA', 'bloqueado': 'BLOQ'}[situacao]
    print(f'[{marca}] {descricao}{" — " + str(detalhe) if detalhe else ""}', flush=True)


def doc_com(mo, paragrafos, estilos=None):
    d = mo.novo()
    t = d.getText()
    for i, p in enumerate(paragrafos):
        if i:
            t.insertControlCharacter(t.getEnd(), PARAGRAPH_BREAK, False)
        t.insertString(t.getEnd(), p, False)
    if estilos:
        e = t.createEnumeration()
        for est in estilos:
            par = e.nextElement()
            if est:
                par.ParaStyleName = est
    return d


def paragrafos(d):
    r = []
    e = d.getText().createEnumeration()
    while e.hasMoreElements():
        p = e.nextElement()
        if p.supportsService('com.sun.star.text.Paragraph'):
            r.append(p)
    return r


def texto(d):
    return '\n'.join(p.getString() for p in paragrafos(d))


def intervalo(d, ini, n, par=0):
    """Cursor sobre n caracteres a partir de ini no parágrafo par (n pode atravessar parágrafos)."""
    p = paragrafos(d)[par]
    c = d.getText().createTextCursorByRange(p.getStart())
    c.goRight(ini, False)
    c.goRight(n, True)
    return c


def selecionar(d, rng):
    d.getCurrentController().select(rng)


def negrito(d, palavra, par=0):
    """Posições (no parágrafo) dos caracteres marcados (sublinhado, para não confundir com o negrito dos títulos)."""
    p = paragrafos(d)[par]
    pos, r = 0, []
    e = p.createEnumeration()
    while e.hasMoreElements():
        por = e.nextElement()
        s = por.getString()
        if por.CharUnderline == 1:
            r.append((pos, pos + len(s), s))
        pos += len(s)
    return r


def titulos_desfazer(d):
    return list(d.getUndoManager().getAllUndoActionTitles())


def despachar(mo, d, comando):
    h = mo.servico('com.sun.star.frame.DispatchHelper')
    h.executeDispatch(d.getCurrentController().getFrame(), comando, '', 0, ())


def n_alteracoes(d):
    e = d.getRedlines().createEnumeration()
    n = 0
    while e.hasMoreElements():
        e.nextElement()
        n += 1
    return n


def recusa(f):
    try:
        f()
        return None
    except P.TrechoInvalido as e:
        return str(e)


# ---------------------------------------------------------------- parte A
ORIG = 'Eu nao sei se voce vem tambem, mas a reuniao e as 14h com o IBGE.'
SUG = 'Eu não sei se você vem também, mas a reunião é às 14h com o IBGE.'


def parte_a(mo):
    # seleções aceitas e recusadas
    d = doc_com(mo, [ORIG, 'Segundo parágrafo com nota.', 'Terceiro parágrafo.'])
    t = d.getText()
    selecionar(d, intervalo(d, 0, 0))
    r1 = recusa(lambda: P.ler_selecao(d))
    nota = d.createInstance('com.sun.star.text.Footnote')
    p2 = paragrafos(d)[1]
    t.insertTextContent(p2.getEnd(), nota, False)
    nota.getText().setString('Fonte da nota.')
    selecionar(d, intervalo(d, 0, len('Segundo parágrafo com nota.') + 1, par=1))
    r2 = recusa(lambda: P.ler_selecao(d))
    campo = d.createInstance('com.sun.star.text.TextField.PageNumber')
    campo.NumberingType = 4
    campo.SubType = uno_enum('com.sun.star.text.PageNumberType', 'CURRENT')
    p3 = paragrafos(d)[2]
    t.insertTextContent(p3.getEnd(), campo, False)
    selecionar(d, intervalo(d, 0, len('Terceiro parágrafo.') + 1, par=2))
    r3 = recusa(lambda: P.ler_selecao(d))
    selecionar(d, intervalo(d, 0, len(ORIG)))
    rng, lido = P.ler_selecao(d)
    verificar('Seleção: vazia, com nota de rodapé ou com campo é recusada com explicação; texto comum é aceito',
              r1 and r2 and r3 and lido == ORIG, f'vazia: {r1!r}; nota: {r2!r}; campo: {r3!r}')
    fechar(d)

    tab = doc_com(mo, ['Antes da tabela.'])
    tb = tab.createInstance('com.sun.star.text.TextTable')
    tb.initialize(2, 2)
    tab.getText().insertTextContent(tab.getText().getEnd(), tb, False)
    tb.getCellByName('A1').setString('célula')
    selecionar(tab, tb.getCellRangeByName('A1:B2'))
    r4 = recusa(lambda: P.ler_selecao(tab))
    verificar('Seleção de células de tabela é recusada', bool(r4), r4)
    fechar(tab)

    # aplicar só as diferenças, numa ação de desfazer, preservando o negrito e o histórico anterior
    d = doc_com(mo, [ORIG, 'Outro parágrafo que não muda.'], estilos=['Heading 1', None])
    b = intervalo(d, ORIG.index('sei'), 3)
    b.CharUnderline = 1
    titulos0 = titulos_desfazer(d)
    selecionar(d, intervalo(d, 0, len(ORIG)))
    rng, lido = P.ler_selecao(d)
    n = P.aplicar(d, rng, lido, SUG, 'revisar', controlada=False)
    titulos1 = titulos_desfazer(d)
    neg = negrito(d, 'sei')
    verificar('Aceitar: o parágrafo fica igual à sugestão e o resto do documento não muda',
              texto(d) == SUG + '\nOutro parágrafo que não muda.', f'{n} trechos alterados')
    verificar('Aceitar: só as palavras mudadas são substituídas (o sublinhado de "sei" e o estilo Título 1 continuam)',
              neg == [(SUG.index('sei'), SUG.index('sei') + 3, 'sei')] and paragrafos(d)[0].ParaStyleName == 'Heading 1', neg)
    verificar('Aceitar: entra no histórico como uma única ação de desfazer, sem apagar as anteriores',
              len(titulos1) == len(titulos0) + 1 and titulos1[0].startswith('Sugestão da IA') and titulos1[1:] == titulos0,
              f'{len(titulos0)} → {len(titulos1)}: {titulos1[:2]}')
    um = d.getUndoManager()
    um.undo()
    t_desfeito, neg_desfeito = texto(d), negrito(d, 'sei')
    um.redo()
    t_refeito = texto(d)
    um.undo()
    um.undo()                       # a ação anterior (o sublinhado) continua desfazível
    sem_negrito = negrito(d, 'sei')
    verificar('Desfazer volta exatamente ao original (texto e sublinhado); Refazer reaplica; a ação anterior também desfaz',
              t_desfeito == ORIG + '\nOutro parágrafo que não muda.' and neg_desfeito == [(ORIG.index('sei'), ORIG.index('sei') + 3, 'sei')]
              and t_refeito.startswith(SUG) and sem_negrito == [], f'sublinhado após desfazer duas vezes: {sem_negrito}')
    fechar(d)

    # troca dentro de uma palavra em negrito mantém o negrito
    d = doc_com(mo, [ORIG])
    intervalo(d, ORIG.index('voce'), 4).CharUnderline = 1
    selecionar(d, intervalo(d, 0, len(ORIG)))
    rng, lido = P.ler_selecao(d)
    P.aplicar(d, rng, lido, SUG, 'revisar', controlada=False)
    neg = negrito(d, 'você')
    verificar('Palavra corrigida dentro de um trecho sublinhado continua sublinhada', neg == [(SUG.index('você'), SUG.index('você') + 4, 'você')], neg)
    fechar(d)

    # alteração controlada: aceitar todas dá a sugestão; rejeitar todas volta ao original
    for acao, esperado in (('.uno:AcceptAllTrackedChanges', SUG), ('.uno:RejectAllTrackedChanges', ORIG)):
        d = doc_com(mo, [ORIG])
        selecionar(d, intervalo(d, 0, len(ORIG)))
        rng, lido = P.ler_selecao(d)
        n = P.aplicar(d, rng, lido, SUG, 'revisar', controlada=True)
        alt = n_alteracoes(d)
        gravando = d.RecordChanges
        despachar(mo, d, acao)
        verificar(f'Como alteração controlada: {alt} marcas para {n} trechos; gravação de alterações volta como estava; '
                  + ('aceitar todas dá a sugestão' if esperado == SUG else 'rejeitar todas volta ao original'),
                  alt >= n and not gravando and texto(d) == esperado, texto(d))
        fechar(d)

    # o trecho mudou depois do pedido
    d = doc_com(mo, [ORIG])
    selecionar(d, intervalo(d, 0, len(ORIG)))
    rng, lido = P.ler_selecao(d)
    intervalo(d, ORIG.index('mas'), 0).setString('X')
    mudou = texto(d)
    r = recusa(lambda: P.aplicar(d, rng, lido, SUG, 'revisar', controlada=False))
    verificar('Trecho editado durante a análise: a sugestão não é aplicada e o documento fica como o usuário deixou',
              bool(r) and texto(d) == mudou and not d.getUndoManager().getCurrentUndoActionTitle().startswith('Sugestão'), r)
    fechar(d)

    # sugestão que junta parágrafos
    d = doc_com(mo, ['Primeiro paragrafo.', 'Segundo paragrafo.'])
    selecionar(d, intervalo(d, 0, len('Primeiro paragrafo.') + 1 + len('Segundo paragrafo.')))
    rng, lido = P.ler_selecao(d)
    r = recusa(lambda: P.aplicar(d, rng, lido, 'Primeiro parágrafo. Segundo parágrafo.', 'revisar'))
    verificar('Sugestão que junta parágrafos não é aplicada', bool(r) and texto(d) == 'Primeiro paragrafo.\nSegundo paragrafo.', r)
    # dois parágrafos, estilos diferentes, correções nos dois
    paragrafos(d)[0].ParaStyleName = 'Heading 2'
    rng, lido = P.ler_selecao(d)
    P.aplicar(d, rng, lido, 'Primeiro parágrafo.\nSegundo parágrafo.', 'revisar', controlada=False)
    ps = paragrafos(d)
    verificar('Seleção de dois parágrafos: correções nos dois, cada um mantém seu estilo',
              texto(d) == 'Primeiro parágrafo.\nSegundo parágrafo.' and ps[0].ParaStyleName == 'Heading 2'
              and ps[1].ParaStyleName != 'Heading 2', [p.ParaStyleName for p in ps])
    fechar(d)


def uno_enum(tipo, valor):
    import uno
    return uno.Enum(tipo, valor)


# ---------------------------------------------------------------- parte B
def conexoes(pid):
    """(escutando, estabelecidas) do processo, pelo netstat do Windows."""
    out = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True, text=True, errors='replace').stdout
    escuta, est = [], []
    for linha in out.splitlines():
        c = linha.split()
        if len(c) >= 5 and c[-1] == str(pid):
            (escuta if c[3].upper().startswith('LISTEN') or c[3].upper().startswith('ESCUTA') else est).append((c[1], c[2]))
    return escuta, est


def estat(xs):
    """Mediana, p95 e pior caso em ms."""
    if not xs:
        return {}
    v = sorted(1000 * x for x in xs)
    return {'mediana': round(v[len(v) // 2]), 'p95': round(v[min(len(v) - 1, int(0.95 * len(v)))]), 'max': round(v[-1])}


def requisicao(srv, metodo, caminho, corpo=None, chave=None, origem=None, extra=None):
    import http.client
    c = http.client.HTTPConnection('127.0.0.1', srv.porta, timeout=30)
    cab = {'Content-Type': 'application/json', **(extra or {})}
    if chave:
        cab['Authorization'] = f'Bearer {chave}'
    if origem:
        cab['Origin'] = origem
    c.request(metodo, caminho, body=corpo, headers=cab)
    r = c.getresponse()
    r.read()
    res = r.status, dict(r.getheaders())
    c.close()
    return res


def pedido(srv, acao, trecho, max_tokens=None, sem_pensar=True):
    return IA.Pedido(srv, T.prompt(acao, trecho), max_tokens=max_tokens or min(2048, 80 + len(trecho)), sem_pensar=sem_pensar)


def parte_b(mo, pasta, modelo_id):
    cat = IA.catalogo()
    m = next((x for x in cat['modelos'] if x['id'] == modelo_id), None)
    exe = pasta / f'motor-{cat["motor"]["versao"]}' / cat['motor']['executavel']
    arq = pasta / 'modelos' / m['arquivo'] if m else None
    if m is None or not exe.exists() or not arq.exists():
        verificar('Parte B (com modelo)', False, f'motor ou modelo ausente em {pasta}', situacao='bloqueado')
        return {}
    medidas = {'modelo': m['id']}
    threads = max(1, (os.cpu_count() or 2) // 2 + 1)
    srv = IA.Servidor(str(exe), str(arq), contexto=4096, threads=threads)
    t0 = time.time()
    srv.iniciar()
    medidas['carga_s'] = round(time.time() - t0, 1)
    try:
        escuta, est = conexoes(srv.pid())
        verificar('Servidor local escuta só em 127.0.0.1 e não tem conexões com outros endereços',
                  escuta and all(a.startswith('127.0.0.1:') for a, _ in escuta) and all(r.startswith('127.0.0.1:') for _, r in est),
                  f'escutando {escuta}; conexões {est}')

        # fechado para outros programas e para sites abertos no navegador
        corpo = json.dumps({'messages': [{'role': 'user', 'content': 'oi'}], 'max_tokens': 1}).encode('utf-8')
        sem_chave = requisicao(srv, 'POST', '/v1/chat/completions', corpo)[0]
        chave_errada = requisicao(srv, 'POST', '/v1/chat/completions', corpo, chave='errada')[0]
        slots = requisicao(srv, 'GET', '/slots', chave=srv.chave)[0]
        st, cab = requisicao(srv, 'OPTIONS', '/v1/chat/completions', origem='https://site-qualquer.example',
                             extra={'Access-Control-Request-Method': 'POST'})
        cors = {k.lower(): v for k, v in cab.items()}.get('access-control-allow-origin')
        verificar('Servidor recusa pedidos sem a chave da sessão, não expõe o texto em análise (/slots) e não libera sites',
                  sem_chave == 401 and chave_errada == 401 and slots in (404, 501) and cors not in ('*', 'https://site-qualquer.example'),
                  f'sem chave {sem_chave}; chave errada {chave_errada}; /slots {slots}; CORS para site externo: {cors!r}')

        # pedido real aplicado no documento pelo caminho do painel
        d = doc_com(mo, [ORIG, 'Parágrafo seguinte.'])
        selecionar(d, intervalo(d, 0, len(ORIG)))
        rng, lido = P.ler_selecao(d)
        # o editor segue respondendo: as mesmas edições em outro parágrafo, sem IA (referência) e enquanto a IA trabalha
        p2 = paragrafos(d)[1]
        base = []
        for _ in range(40):
            a = time.time()
            p2.getText().insertString(p2.getEnd(), '.', False)
            base.append(time.time() - a)
            time.sleep(0.05)
        p = pedido(srv, 'revisar', lido, sem_pensar=m.get('sem_pensar', True)).iniciar()
        lat = []
        while p.thread.is_alive():
            a = time.time()
            p2.getText().insertString(p2.getEnd(), '.', False)
            lat.append(time.time() - a)
            time.sleep(0.05)
        sug = T.limpar_resposta(p.texto, lido)
        probl = T.conferir_preservacao(lido, sug, 'revisar')
        medidas.update(revisar_s=p.medidas.get('segundos'), primeiro_token_s=p.medidas.get('primeiro_token_s'),
                       edicao_sem_ia_ms=estat(base), edicao_durante_ia_ms=estat(lat), edicoes_durante_ia=len(lat))
        verificar('Pedido real: sugestão em segundo plano, sem erro, preservando números, siglas e nomes',
                  not p.erro and sug and not probl, f'{p.medidas.get("segundos")} s: {sug!r} {probl or ""}')
        e_sem, e_com = estat(base), estat(lat)
        verificar('Editor responde durante a análise (edições em outro parágrafo): 95% em menos de 150 ms e nenhuma acima de 500 ms',
                  lat and e_com['p95'] < 150 and e_com['max'] < 500,
                  f'sem IA: mediana {e_sem["mediana"]} ms, p95 {e_sem["p95"]}, pior {e_sem["max"]} | durante a IA ({len(lat)} edições): '
                  f'mediana {e_com["mediana"]} ms, p95 {e_com["p95"]}, pior {e_com["max"]}' if lat else 'nenhuma')
        n = P.aplicar(d, rng, lido, sug, 'revisar', controlada=False)
        aplicado = paragrafos(d)[0].getString()
        d.getUndoManager().undo()
        verificar('Pedido real aceito: aplica no parágrafo certo; desfazer volta ao original',
                  aplicado == sug and paragrafos(d)[0].getString() == ORIG and 'não' in sug, f'{n} trechos: {aplicado!r}')

        # edição do trecho durante a análise
        selecionar(d, intervalo(d, 0, len(ORIG)))
        rng, lido = P.ler_selecao(d)
        p = pedido(srv, 'revisar', lido, sem_pensar=m.get('sem_pensar', True)).iniciar()
        time.sleep(0.3)
        intervalo(d, ORIG.index('reuniao'), 0).setString('nova ')
        p.thread.join()
        sug = T.limpar_resposta(p.texto, lido)
        r = recusa(lambda: P.aplicar(d, rng, lido, sug, 'revisar'))
        verificar('Usuário editou o trecho enquanto a IA analisava: a sugestão não é aplicada', bool(r) and 'nova reuniao' in texto(d), r)
        fechar(d)

        # cancelamento: antes da primeira palavra e durante a escrita
        longo = ' '.join([CASO_LONGO] * 8)
        p = pedido(srv, 'clareza', longo, max_tokens=900, sem_pensar=m.get('sem_pensar', True)).iniciar()
        time.sleep(0.3)
        a = time.time()
        p.cancelar()
        p.thread.join(30)
        c1 = time.time() - a
        p = pedido(srv, 'clareza', longo, max_tokens=900, sem_pensar=m.get('sem_pensar', True)).iniciar()
        while p.thread.is_alive() and not p.texto:
            time.sleep(0.05)
        time.sleep(1.0)
        a = time.time()
        p.cancelar()
        p.thread.join(30)
        c2 = time.time() - a
        a = time.time()
        p3 = pedido(srv, 'revisar', 'O relatorio foi entregue.', sem_pensar=m.get('sem_pensar', True)).iniciar()
        p3.thread.join(120)
        depois = time.time() - a
        medidas.update(cancelar_antes_s=round(c1, 2), cancelar_durante_s=round(c2, 2), pedido_depois_s=round(depois, 1))
        verificar('Cancelar responde em menos de 2 s (antes da primeira palavra e durante a escrita) e o pedido seguinte funciona',
                  c1 < 2 and c2 < 2 and not p3.erro and p3.texto, f'antes {c1:.2f} s; durante {c2:.2f} s; pedido seguinte {depois:.1f} s')
        medidas['memoria_mb'], medidas['memoria_pico_mb'] = memoria_mb(srv.pid())
        verificar('Memória do servidor medida', medidas['memoria_pico_mb'] is not None,
                  f'{medidas["memoria_mb"]} MB em uso, pico {medidas["memoria_pico_mb"]} MB')
    finally:
        srv.parar()

    # servidor encerrado junto com o processo dono (Job Object), mesmo sem fechamento normal
    # o python do motor: sys.executable dele aponta para a pasta python-core, não para um executável
    filho = subprocess.Popen([str(PROGRAMA / 'python.exe'), '-I', '-c', FILHO, str(RAIZ / 'extensao' / 'ayescreva' / 'pythonpath'), str(exe), str(arq)],
                             stdout=subprocess.PIPE, text=True)
    # o python.exe do motor é um lançador: o interpretador real (que guarda o "job") é outro processo, e é ele que
    # faz o papel do AY aqui; ele é derrubado com taskkill /F, como numa queda
    dono, pid = (int(x) for x in filho.stdout.readline().split())
    vivo_antes = processo_vivo(pid)
    subprocess.run(['taskkill', '/F', '/PID', str(dono)], capture_output=True)
    filho.kill()
    filho.wait()
    fim = time.time() + 10
    while pid and processo_vivo(pid) and time.time() < fim:
        time.sleep(0.2)
    verificar('Se o processo do AY termina de repente, o servidor de IA termina junto', vivo_antes and not processo_vivo(pid),
              f'pid {pid}: vivo antes {vivo_antes}, depois {processo_vivo(pid) if pid else None}')
    return medidas


CASO_LONGO = ('Tendo em vista a necessidade de que haja a realização da análise dos documentos por parte da equipe, solicita-se '
              'que seja efetuado o envio dos arquivos até o dia 15/11/2026.')

FILHO = r'''
import os, sys, time
sys.path.insert(0, sys.argv[1])
import ay_ia as IA
s = IA.Servidor(sys.argv[2], sys.argv[3], contexto=2048)
s.iniciar()
print(os.getpid(), s.pid(), flush=True)
time.sleep(600)
'''


def processo_vivo(pid):
    out = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/NH'], capture_output=True, text=True, errors='replace').stdout
    return str(pid) in out


def memoria_mb(pid):
    sys.path.insert(0, str(RAIZ / 'tests' / 'ia'))
    from avaliar_modelos import memoria_mb as mm
    return mm(pid)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--pasta', default=str(RAIZ / 'out' / 'ia'))
    ap.add_argument('--modelo', default=None)
    a = ap.parse_args()
    cat = IA.catalogo()
    modelo = a.modelo or next((m['id'] for m in cat['modelos'] if m.get('recomendado')), cat['modelos'][0]['id'])
    medidas = {}
    with Motor('ia') as mo:
        parte_a(mo)
        medidas = parte_b(mo, Path(a.pasta), modelo)
    saida = SAIDA_TESTES / 'ia'
    saida.mkdir(parents=True, exist_ok=True)
    (saida / 'integracao.json').write_text(json.dumps({'itens': itens, 'medidas': medidas}, ensure_ascii=False, indent=1), encoding='utf-8')
    ok = sum(1 for i in itens if i['situacao'] == 'ok')
    bloq = sum(1 for i in itens if i['situacao'] == 'bloqueado')
    print(f'\nIA local no editor: {ok}/{len(itens)} aprovadas' + (f', {bloq} bloqueada(s)' if bloq else ''))
    sys.exit(0 if ok == len(itens) else 1)


if __name__ == '__main__':
    main()
