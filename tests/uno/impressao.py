# -*- coding: utf-8 -*-
"""Teste de impressão do AY ESCREVA pela fila do Windows, sem papel.

Usa exclusivamente a impressora virtual "Microsoft Print to PDF" com saída em arquivo.
Se essa impressora não estiver selecionada após setPrinter, o teste é abortado ANTES de imprimir,
para nunca enviar o trabalho à impressora padrão (que pode ser física).

Uso: python.exe impressao.py <documento> <saida.pdf>
SPDX-License-Identifier: MPL-2.0
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ay_uno import Motor, Relatorio, props, fechar, paginas, paginas_pdf  # noqa: E402

IMPRESSORA = 'Microsoft Print to PDF'


def main():
    doc_entrada, saida = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
    saida.parent.mkdir(parents=True, exist_ok=True)
    if saida.exists():
        saida.unlink()
    rel = Relatorio('Impressão')
    with Motor('impressao') as motor:
        doc = motor.abrir(doc_entrada)
        n = paginas(doc)
        doc.setPrinter(props(Name=IMPRESSORA))
        atual = {p.Name: p.Value for p in doc.getPrinter()}.get('Name')
        if not rel.verificar('impressora virtual selecionada', atual == IMPRESSORA, f'selecionada: {atual}'):
            fechar(doc)
            print('Abortado: a impressora virtual não foi selecionada; nada foi impresso.')
            return rel.finalizar()
        doc.print(props(FileName=str(saida), Wait=True, CopyCount=1))
        limite = time.time() + 60
        while time.time() < limite and (not saida.exists() or saida.stat().st_size == 0):
            time.sleep(0.5)
        time.sleep(1)
        ok = saida.exists() and saida.stat().st_size > 0
        rel.verificar('trabalho de impressão gerou arquivo', ok, f'{saida.stat().st_size if ok else 0} bytes')
        if ok:
            cab = saida.read_bytes()[:5]
            rel.verificar('saída da impressora é PDF', cab == b'%PDF-', repr(cab))
            np = paginas_pdf(saida)
            rel.verificar('páginas impressas = páginas do documento', np == n, f'{np} impressas, {n} no documento')
        fechar(doc)
    return rel.finalizar()


if __name__ == '__main__':
    sys.exit(main())
