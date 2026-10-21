# -*- coding: utf-8 -*-
"""Download da IA local (ay_ia.baixar): progresso, cancelamento, retomada, recomeço seguro e falhas.

Usa um servidor HTTP local que simula o que acontece na internet: conexão que cai no meio, servidor que não aceita
retomar (ignora o cabeçalho Range), arquivo adulterado, 404, erro 500 repetido, servidor lento (para cancelar) e
servidor que manda dados demais. O código testado é o mesmo do diálogo "Gerenciar IA local"; só a exigência de https
fica de fora (o servidor de teste é http em 127.0.0.1), e ela é conferida à parte.

Uso: "dist\\AY ESCREVA\\program\\python.exe" tests\\ia\\testar_download.py
SPDX-License-Identifier: MPL-2.0
"""
import hashlib
import http.server
import json
import os
import shutil
import string
import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'extensao' / 'ayescreva' / 'pythonpath'))
import ay_ia as IA  # noqa: E402

SAIDA = RAIZ / 'tests' / 'output' / 'ia' / 'download'
DADOS = os.urandom(8 * 2**20 + 12345)               # 8 MB e pouco
SHA = hashlib.sha256(DADOS).hexdigest()
itens = []
pedidos = []                                         # (caminho, Range) de cada pedido que chegou ao servidor
estado = {'cai': 0, 'erro500': 0}


def verificar(descricao, ok, detalhe=''):
    itens.append({'ok': bool(ok), 'verificacao': descricao, 'detalhe': str(detalhe)})
    print(f"[{'OK  ' if ok else 'FALHA'}] {descricao}{' — ' + str(detalhe) if detalhe else ''}", flush=True)


class Servidor(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def do_GET(self):
        caminho = self.path
        faixa = self.headers.get('Range')
        pedidos.append((caminho, faixa))
        if caminho == '/404':
            return self._vazio(404)
        if caminho == '/500':
            estado['erro500'] += 1
            return self._vazio(500)
        corpo = DADOS
        if caminho == '/corrompido':
            corpo = DADOS[:1000] + bytes([DADOS[1000] ^ 0xFF]) + DADOS[1001:]
        if caminho == '/maior':
            corpo = DADOS + b'x' * 4096
        inicio = 0
        if faixa and caminho != '/sem-range':
            inicio = int(faixa.split('=')[1].split('-')[0])
            if inicio >= len(corpo):
                return self._vazio(416)
            self.send_response(206)
            self.send_header('Content-Range', f'bytes {inicio}-{len(corpo) - 1}/{len(corpo)}')
        else:
            self.send_response(200)
        resto = corpo[inicio:]
        self.send_header('Content-Length', str(len(resto)))
        self.end_headers()
        corte = None
        if caminho == '/cai' and estado['cai'] < 2:          # as duas primeiras conexões caem depois de 3 MB
            estado['cai'] += 1
            corte = 3 * 2**20
        enviado = 0
        while enviado < len(resto):
            pedaco = resto[enviado:enviado + 65536]
            if corte is not None and enviado + len(pedaco) > corte:
                self.wfile.write(pedaco[:corte - enviado])
                self.wfile.flush()
                self.connection.shutdown(2)                      # queda da conexão no meio do arquivo
                return
            try:
                self.wfile.write(pedaco)
            except OSError:
                return
            enviado += len(pedaco)
            if caminho == '/lento':
                time.sleep(0.01)

    def _vazio(self, codigo):
        self.send_response(codigo)
        self.send_header('Content-Length', '0')
        self.end_headers()


def baixar(url, destino, **kw):
    kw.setdefault('tamanho', len(DADOS))
    return IA._baixar(url, str(destino), SHA, exigir_https=False, espera=0.05, **kw)


def limpar():
    shutil.rmtree(SAIDA, ignore_errors=True)
    SAIDA.mkdir(parents=True, exist_ok=True)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    IA.registrar = lambda m: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Servidor)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{srv.server_address[1]}'
    arq = SAIDA / 'modelo.gguf'
    parcial = Path(str(arq) + '.parcial')

    # 1. download normal, com progresso
    limpar()
    marcas = []
    baixar(base + '/normal', arq, progresso=lambda f, t, fase: marcas.append((f, t, fase)))
    verificar('Download completo: arquivo final conferido (SHA-256), sem parte sobrando, progresso crescente até 100%',
              arq.read_bytes() == DADOS and not parcial.exists() and marcas and marcas[-1][0] == marcas[-1][1] == len(DADOS)
              and all(a[0] <= b[0] for a, b in zip(marcas, marcas[1:])), f'{len(marcas)} avisos de progresso')

    # 2. cancelar no meio guarda a parte; continuar pede só o restante (Range) e termina
    limpar()
    pedidos.clear()
    cancelar = threading.Event()

    def prog(f, t, fase):
        if f >= 2 * 2**20:
            cancelar.set()
    a = time.time()
    try:
        baixar(base + '/lento', arq, progresso=prog, cancelar=cancelar)
        cancelou = False
    except IA.Cancelado:
        cancelou = True
    t_cancelar = time.time() - a
    guardado = IA.tamanho_parcial(str(arq))
    verificar('Cancelar: para logo, não cria o arquivo final e guarda a parte baixada para continuar',
              cancelou and not arq.exists() and 2 * 2**20 <= guardado < len(DADOS), f'{guardado} bytes guardados; {t_cancelar:.1f} s')
    pedidos.clear()
    fases = []
    baixar(base + '/normal', arq, progresso=lambda f, t, fase: fases.append(fase))
    verificar('Continuar: confere a parte guardada, pede só o restante (Range a partir do byte guardado) e termina íntegro',
              arq.read_bytes() == DADOS and pedidos == [('/normal', f'bytes={guardado}-')] and 'conferindo' in fases,
              pedidos)

    # 3. conexão cai duas vezes: retomadas automáticas, sem baixar de novo o que já veio
    limpar()
    pedidos.clear()
    estado['cai'] = 0
    baixar(base + '/cai', arq)
    faixas = [p[1] for p in pedidos]
    verificar('Queda da conexão: retoma sozinho de onde parou (sem recomeçar) e termina íntegro',
              arq.read_bytes() == DADOS and len(pedidos) == 3 and faixas[0] is None and faixas[1] == f'bytes={3 * 2**20}-'
              and faixas[2] == f'bytes={6 * 2**20}-', faixas)

    # 4. servidor que não aceita retomar: recomeça do zero com segurança (sem misturar pedaços)
    limpar()
    parcial.write_bytes(DADOS[:3 * 2**20])
    pedidos.clear()
    baixar(base + '/sem-range', arq)
    verificar('Servidor que não aceita retomar (responde 200 inteiro): recomeça do zero e o arquivo final é íntegro',
              arq.read_bytes() == DADOS and len(pedidos) == 1, pedidos)

    # 5. parte guardada adulterada no disco: o SHA-256 final reprova e apaga
    limpar()
    parcial.write_bytes(b'\0' * (3 * 2**20))
    try:
        baixar(base + '/normal', arq)
        r = None
    except IA.FalhaDownload as e:
        r = str(e)
    verificar('Parte guardada adulterada: o resultado não confere com o SHA-256, nada vira arquivo final e a parte é apagada',
              r and 'SHA-256' in r and not arq.exists() and not parcial.exists(), r)

    # 6. arquivo adulterado no servidor
    limpar()
    try:
        baixar(base + '/corrompido', arq)
        r = None
    except IA.FalhaDownload as e:
        r = str(e)
    verificar('Arquivo diferente do oficial: recusado pelo SHA-256 e apagado', r and 'SHA-256' in r and not arq.exists() and not parcial.exists(), r)

    # 7. servidor manda dados demais
    limpar()
    try:
        baixar(base + '/maior', arq)
        r = None
    except IA.FalhaDownload as e:
        r = str(e)
    verificar('Servidor manda mais dados que o esperado: recusado e apagado', r and not arq.exists() and not parcial.exists(), r)

    # 8. 404: sem novas tentativas, mensagem clara
    limpar()
    pedidos.clear()
    try:
        baixar(base + '/404', arq)
        r = None
    except IA.FalhaDownload as e:
        r = str(e)
    verificar('Endereço inexistente (404): uma tentativa só, mensagem clara, nada criado', r and '404' in r and len(pedidos) == 1
              and not arq.exists(), r)

    # 9. erro 500 persistente: tenta de novo algumas vezes e desiste guardando o que tiver
    limpar()
    estado['erro500'] = 0
    try:
        baixar(base + '/500', arq)
        r = None
    except IA.FalhaDownload as e:
        r = str(e)
    verificar(f'Servidor com erro 500: {IA.TENTATIVAS} novas tentativas, depois mensagem para tentar mais tarde (nada guardado)',
              r and estado['erro500'] == IA.TENTATIVAS + 1 and 'tente de novo' in r and not parcial.exists(), f'{estado["erro500"]} pedidos; {r}')

    # 10. parte completa guardada (cancelado no fim): só confere, sem rede
    limpar()
    parcial.write_bytes(DADOS)
    pedidos.clear()
    baixar(base + '/normal', arq)
    verificar('Parte já completa (cancelado no último instante): só confere o SHA-256, sem baixar de novo',
              arq.read_bytes() == DADOS and pedidos == [], pedidos)

    # 11. https obrigatório e redirecionamento sem https recusado
    limpar()
    try:
        IA.baixar(base + '/normal', str(arq), SHA, len(DADOS))
        r1 = None
    except ValueError as e:
        r1 = str(e)
    try:
        IA._baixar(base + '/normal', str(arq), SHA, len(DADOS), exigir_https=True)
        r2 = None
    except IA.FalhaDownload as e:
        r2 = str(e)
    verificar('Só https: endereço http recusado; resposta que termina num endereço sem https também', r1 and r2 and not arq.exists(), f'{r1} | {r2}')

    # 12. pasta numa unidade que não existe: erro imediato (antes travava calculando o espaço livre)
    livres = [f'{l}:\\' for l in string.ascii_uppercase if not os.path.exists(f'{l}:\\')]
    a = time.time()
    try:
        IA.espaco_livre(livres[-1] + 'IA')
        r = None
    except ValueError as e:
        r = str(e)
    verificar('Pasta numa unidade inexistente: avisa na hora (sem travar)', r and time.time() - a < 1, r)

    srv.shutdown()
    shutil.rmtree(SAIDA, ignore_errors=True)
    saida = RAIZ / 'tests' / 'output' / 'ia'
    saida.mkdir(parents=True, exist_ok=True)
    (saida / 'download.json').write_text(json.dumps({'itens': itens}, ensure_ascii=False, indent=1), encoding='utf-8')
    n = sum(1 for x in itens if x['ok'])
    print(f'Download da IA: {n}/{len(itens)}')
    return 0 if n == len(itens) else 1


if __name__ == '__main__':
    sys.exit(main())
