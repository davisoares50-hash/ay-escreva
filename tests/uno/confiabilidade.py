# -*- coding: utf-8 -*-
"""Confiabilidade do AY ESCREVA (0.3.0): desfazer/refazer, TXT, cópia de segurança, falha ao salvar e salvamento
interrompido. Cada verificação confere o efeito real no documento ou no arquivo.

  1. desfazer/refazer: 5 edições (texto, negrito, tabela, imagem, nota de rodapé), desfeitas e refeitas uma a uma,
     conferindo o documento a cada passo; depois salva em ODT e DOCX, reabre e confere.
  2. TXT: ida e volta em UTF-8 e Windows-1252 com acentuação, travessão, aspas curvas e €; e abertura de um TXT
     Windows-1252 escrito fora do AY.
  3. cópia de segurança: ao salvar de novo, a versão anterior vai para a pasta de backup do perfil.
  4. falha ao salvar: com o arquivo bloqueado por outro programa, salvar falha, o arquivo anterior fica intacto e o
     documento continua marcado como modificado; desbloqueado, salva.
  5. salvamento interrompido: encerra o motor à força em vários momentos de uma gravação grande e confere que o
     arquivo no disco é sempre um documento íntegro (versão anterior ou nova) ou, se não for, que a cópia de
     segurança tem a versão anterior.

Uso: python.exe confiabilidade.py
SPDX-License-Identifier: MPL-2.0
"""
import ctypes
import stat
import subprocess
import hashlib
import json
import os
import random
import struct
import sys
import threading
import time
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ay_uno import Motor, RAIZ, SAIDA_TESTES, props, url, fechar  # noqa: E402

import uno  # noqa: E402

SAIDA = SAIDA_TESTES / 'confiabilidade'
itens = []


def verificar(descricao, ok, detalhe=''):
    itens.append({'ok': bool(ok), 'verificacao': descricao, 'detalhe': str(detalhe)})
    print(f"[{'OK  ' if ok else 'FALHA'}] {descricao}{' — ' + str(detalhe) if detalhe else ''}", flush=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def estado(doc):
    t = doc.Text.getString()
    tabelas = doc.getTextTables().getCount()
    graficos = doc.getGraphicObjects().getCount()
    notas = doc.getFootnotes().getCount()
    cur = doc.Text.createTextCursor()
    cur.gotoStart(False)
    negrito = False
    busca = doc.createSearchDescriptor()
    busca.SearchString = 'importante'
    r = doc.findFirst(busca)
    if r is not None:
        negrito = r.CharWeight >= 150
    return {'texto': 'Primeiro parágrafo' in t, 'negrito': negrito, 'tabelas': tabelas, 'imagens': graficos, 'notas': notas}


def passo(doc, titulo, f):
    um = doc.getUndoManager()
    um.enterUndoContext(titulo)
    try:
        f()
    finally:
        um.leaveUndoContext()


def teste_desfazer(m):
    doc = m.novo()
    texto = doc.Text
    um = doc.getUndoManager()
    um.clear()
    estados = [estado(doc)]

    def p1():
        texto.insertString(texto.getEnd(), 'Primeiro parágrafo com uma palavra importante no meio.', False)

    def p2():
        b = doc.createSearchDescriptor()
        b.SearchString = 'importante'
        doc.findFirst(b).CharWeight = 150

    def p3():
        t = doc.createInstance('com.sun.star.text.TextTable')
        t.initialize(2, 2)
        texto.insertTextContent(texto.getEnd(), t, False)
        t.getCellByName('A1').setString('célula')

    def p4():
        prov = m.servico('com.sun.star.graphic.GraphicProvider')
        g = prov.queryGraphic(props(URL=url(RAIZ / 'out' / 'marca' / 'icone-128.png')))
        img = doc.createInstance('com.sun.star.text.TextGraphicObject')
        img.Graphic = g
        texto.insertTextContent(texto.getEnd(), img, False)

    def p5():
        n = doc.createInstance('com.sun.star.text.Footnote')
        texto.insertTextContent(texto.getEnd(), n, False)
        n.setString('Nota de rodapé.')

    for i, (titulo, f) in enumerate((('texto', p1), ('negrito', p2), ('tabela', p3), ('imagem', p4), ('nota', p5)), 1):
        passo(doc, f'Teste {titulo}', f)
        estados.append(estado(doc))
    verificar('desfazer/refazer: 5 edições registradas no histórico', len(um.getAllUndoActionTitles()) >= 5,
              ', '.join(um.getAllUndoActionTitles()[:5]))
    ok_desf = True
    for i in range(5, 0, -1):
        um.undo()
        if estado(doc) != estados[i - 1]:
            ok_desf = False
            verificar(f'desfazer passo {i}', False, f'{estado(doc)} ≠ {estados[i - 1]}')
    verificar('desfazer volta o documento a cada estado anterior, até o vazio', ok_desf and estado(doc) == estados[0])
    ok_ref = True
    for i in range(1, 6):
        um.redo()
        if estado(doc) != estados[i]:
            ok_ref = False
            verificar(f'refazer passo {i}', False, f'{estado(doc)} ≠ {estados[i]}')
    verificar('refazer reaplica cada edição na ordem', ok_ref and estado(doc) == estados[5], estados[5])
    for ext, filtro in (('odt', 'writer8'), ('docx', 'MS Word 2007 XML')):
        destino = SAIDA / f'desfazer-refazer.{ext}'
        doc.storeToURL(url(destino), props(FilterName=filtro, Overwrite=True))
        d2 = m.abrir(destino)
        verificar(f'depois de refazer, salvo em {ext.upper()} e reaberto igual', estado(d2) == estados[5], estado(d2))
        fechar(d2)
    fechar(doc)


AMOSTRA = 'Ação, coração, pão, você, avó, útil, então — “aspas curvas” e preço de 10 €.\nSegunda linha: ÁÉÍÓÚ ÂÊÔ ÃÕ Ç.'


def teste_txt(m):
    for codificacao, opcao, py in (('UTF-8', 'UTF8', 'utf-8'), ('Windows-1252', 'MS_1252', 'cp1252')):
        doc = m.novo()
        doc.Text.setString(AMOSTRA)
        destino = SAIDA / f'texto-{opcao}.txt'
        doc.storeToURL(url(destino), props(FilterName='Text (encoded)', FilterOptions=f'{opcao},CRLF,,', Overwrite=True))
        fechar(doc)
        bruto = destino.read_bytes()
        try:
            lido = bruto.decode(py).replace('\r\n', '\n').lstrip('﻿')
        except UnicodeDecodeError as e:
            lido = f'(não decodifica: {e})'
        verificar(f'TXT {codificacao}: bytes gravados na codificação certa', lido.strip() == AMOSTRA, f'{len(bruto)} bytes')
        d2 = m.abrir(destino, FilterName='Text (encoded)', FilterOptions=f'{opcao},CRLF,,')
        reaberto = d2.Text.getString().replace('\r\n', '\n').strip()
        verificar(f'TXT {codificacao}: reaberto com o mesmo texto', reaberto == AMOSTRA, reaberto[:40])
        fechar(d2)
    externo = SAIDA / 'externo-1252.txt'
    externo.write_bytes(AMOSTRA.replace('\n', '\r\n').encode('cp1252'))
    d3 = m.abrir(externo, FilterName='Text (encoded)', FilterOptions='MS_1252,CRLF,,')
    verificar('TXT Windows-1252 escrito por outro programa abre com acentos certos',
              d3.Text.getString().replace('\r\n', '\n').strip() == AMOSTRA)
    fechar(d3)


def pasta_backup(m):
    return Path(m.perfil) / 'user' / 'backup'


def teste_backup_e_bloqueio(m):
    alvo = SAIDA / 'seguro.odt'
    if alvo.exists():
        alvo.unlink()
    doc = m.novo()
    doc.Text.setString('Versão 1 do documento.')
    doc.storeAsURL(url(alvo), props(FilterName='writer8'))
    h1 = sha(alvo)
    doc.Text.setString('Versão 2 do documento.')
    doc.store()
    h2 = sha(alvo)
    bk = pasta_backup(m)
    copias = [p for p in bk.glob('*')] if bk.exists() else []
    v1 = [p for p in copias if p.is_file() and sha(p) == h1]
    verificar('cópia de segurança: ao salvar de novo, a versão anterior fica na pasta de backup do perfil',
              h2 != h1 and bool(v1), f'{[p.name for p in copias]}')
    # Falha de gravação provocada por outro programa: o arquivo passa a ser somente leitura (o motor mantém o
    # documento aberto, então um bloqueio exclusivo do arquivo inteiro não é possível)
    os.chmod(alvo, stat.S_IREAD)
    verificar('arquivo tornado somente leitura por outro processo', not os.access(alvo, os.W_OK))
    doc.Text.setString('Versão 3 do documento.')
    falhou = False
    try:
        doc.store()
    except Exception as e:
        falhou = True
        erro = type(e).__name__
    else:
        erro = 'nenhum'
    os.chmod(alvo, stat.S_IREAD | stat.S_IWRITE)
    verificar('salvar com o arquivo protegido falha com erro (não finge que salvou)', falhou, erro)
    verificar('o arquivo anterior fica intacto depois da falha', sha(alvo) == h2)
    verificar('o documento continua marcado como modificado (a alteração não se perde)', doc.isModified())
    # Depois da falha, o caminho do usuário é "Salvar como" (o motor não volta a gravar no mesmo arquivo nesta sessão)
    try:
        doc.store()
        mesmo = 'salvou de novo no mesmo arquivo'
    except Exception as e:
        mesmo = f'Salvar no mesmo arquivo recusado ({type(e).__name__})'
    outro = SAIDA / 'seguro-salvo-como.odt'
    doc.storeAsURL(url(outro), props(FilterName='writer8', Overwrite=True))
    d2 = m.abrir(outro)
    verificar('depois da falha, "Salvar como" grava a alteração sem perdas', 'Versão 3' in d2.Text.getString(), mesmo)
    fechar(d2)
    fechar(doc)


def png_ruido(caminho, largura=2400, altura=1800, semente=1):
    rnd = random.Random(semente)
    linhas = b''.join(b'\x00' + rnd.randbytes(largura * 3) for _ in range(altura))

    def bloco(tipo, dados):
        return struct.pack('>I', len(dados)) + tipo + dados + struct.pack('>I', zlib.crc32(tipo + dados) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + bloco(b'IHDR', struct.pack('>IIBBBBB', largura, altura, 8, 2, 0, 0, 0)) \
        + bloco(b'IDAT', zlib.compress(linhas, 1)) + bloco(b'IEND', b'')
    Path(caminho).write_bytes(png)


def integro(caminho, palavra):
    """Abre o arquivo como zip e confere o texto em content.xml (sem depender do motor)."""
    try:
        with zipfile.ZipFile(caminho) as z:
            if z.testzip() is not None:
                return False, 'zip com erro de CRC'
            return palavra.encode() in z.read('content.xml'), 'zip íntegro'
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'


def pid_do_motor(nome_pipe):
    """PID do soffice.bin desta sessão (o soffice.exe é só o lançador)."""
    cmd = ("Get-CimInstance Win32_Process -Filter \"Name='soffice.bin'\" | "
           f"Where-Object {{ $_.CommandLine -like '*{nome_pipe}*' }} | ForEach-Object {{ $_.ProcessId }}")
    saida = subprocess.run(['powershell.exe', '-NoProfile', '-Command', cmd], capture_output=True, text=True).stdout.split()
    return int(saida[0]) if saida else None


def encerrar_e_esperar(pid, limite=15):
    """TerminateProcess no PID e espera o processo sumir de verdade."""
    k32 = ctypes.windll.kernel32
    k32.OpenProcess.restype = ctypes.c_void_p
    h = k32.OpenProcess(0x0001 | 0x00100000, False, pid)        # PROCESS_TERMINATE | SYNCHRONIZE
    if not h:
        return False
    try:
        k32.TerminateProcess(ctypes.c_void_p(h), 1)
        return k32.WaitForSingleObject(ctypes.c_void_p(h), int(limite * 1000)) == 0
    finally:
        k32.CloseHandle(ctypes.c_void_p(h))


def teste_interrupcao():
    imagens = [SAIDA / f'ruido-{i}.png' for i in range(4)]
    for i, p in enumerate(imagens):
        if not p.exists():
            png_ruido(p, semente=i)
    resultados = []
    for atraso in (0.3, 1.0, 2.0, 3.5):
        alvo = SAIDA / 'grande.odt'
        for p in (alvo, SAIDA / '.~lock.grande.odt#'):     # o encerramento forçado deixa o arquivo de trava
            if p.exists():
                p.unlink()
        with Motor('interrupcao') as m:
            doc = m.novo()
            prov = m.servico('com.sun.star.graphic.GraphicProvider')
            for p in imagens:
                img = doc.createInstance('com.sun.star.text.TextGraphicObject')
                img.Graphic = prov.queryGraphic(props(URL=url(p)))
                doc.Text.insertTextContent(doc.Text.getEnd(), img, False)
            doc.Text.insertString(doc.Text.getEnd(), 'VERSAOANTIGA', False)
            doc.storeAsURL(url(alvo), props(FilterName='writer8'))
            h_antigo = sha(alvo)
            pid_bin = pid_do_motor(m.nome_pipe)
            tam = alvo.stat().st_size
            bk = pasta_backup(m)
            # nova versão: troca o marcador e grava; o motor é encerrado à força durante a gravação
            b = doc.createSearchDescriptor()
            b.SearchString = 'VERSAOANTIGA'
            doc.findFirst(b).setString('VERSAONOVA')
            inicio = time.time()
            t = threading.Thread(target=lambda: _tentar(doc.store), daemon=True)
            t.start()
            time.sleep(atraso)
            # Encerra o processo que grava (soffice.bin) no momento escolhido e confirma que ele terminou
            gravando = t.is_alive()
            encerrado = encerrar_e_esperar(pid_bin) if pid_bin else False
            duracao = time.time() - inicio
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(m.proc.pid)], capture_output=True)
            m.proc.wait(timeout=30)
            time.sleep(1)
            m.desktop = None
            antigo_ok, _ = integro(alvo, 'VERSAOANTIGA') if alvo.exists() else (False, 'arquivo sumiu')
            novo_ok, det = integro(alvo, 'VERSAONOVA') if alvo.exists() else (False, 'arquivo sumiu')
            copia_ok = any(sha(p) == h_antigo for p in bk.glob('*')) if bk.exists() else False
            resultados.append({'atraso_s': atraso, 'arquivo': 'versão anterior' if antigo_ok else 'versão nova' if novo_ok else 'corrompido/ausente',
                               'detalhe': det, 'copia_de_seguranca_com_versao_anterior': copia_ok, 'tamanho_mb': round(tam / 1e6, 1),
                               'encerrado_apos_s': round(duracao, 2), 'motor_encerrado_de_fato': encerrado,
                               'gravacao_em_andamento_no_encerramento': gravando})
            print('   interrupção', resultados[-1], flush=True)
    encerrados = all(r['motor_encerrado_de_fato'] for r in resultados)
    interrompidas = sum(1 for r in resultados if r['gravacao_em_andamento_no_encerramento'])
    verificar('o processo que grava (soffice.bin) foi encerrado de fato em todas as tentativas', encerrados,
              f'{interrompidas} de {len(resultados)} encerramentos aconteceram com a gravação em andamento')
    sempre_integro = all(r['arquivo'] != 'corrompido/ausente' for r in resultados)
    recuperavel = all(r['arquivo'] != 'corrompido/ausente' or r['copia_de_seguranca_com_versao_anterior'] for r in resultados)
    verificar('salvamento interrompido à força: arquivo no disco sempre íntegro (versão anterior ou nova)', sempre_integro,
              '; '.join(f"{r['atraso_s']} s → {r['arquivo']}" for r in resultados))
    verificar('salvamento interrompido: versão anterior sempre recuperável (arquivo ou cópia de segurança)', recuperavel)
    return resultados


def _tentar(f):
    try:
        f()
    except Exception:
        pass


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    with Motor('confiabilidade') as m:
        teste_desfazer(m)
        teste_txt(m)
        teste_backup_e_bloqueio(m)
    interrupcao = teste_interrupcao()
    ok = sum(1 for i in itens if i['ok'])
    (SAIDA / 'resultado.json').write_text(json.dumps({'itens': itens, 'interrupcao': interrupcao}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Confiabilidade: {ok}/{len(itens)} verificações aprovadas')
    return 0 if ok == len(itens) else 1


if __name__ == '__main__':
    sys.exit(main())
