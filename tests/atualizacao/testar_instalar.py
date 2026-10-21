# -*- coding: utf-8 -*-
"""Instalar uma atualização (entrega E), pelo motor: documentos com alterações não salvas bloqueiam a instalação.

  - com um documento alterado e não salvo: recusa, dizendo qual documento salvar; nada é fechado nem executado;
  - depois de salvar: prepara o roteiro de instalação (aqui não é executado: o teste de ponta a ponta, que fecha o AY,
    instala e reabre, é tests/instalacao/testar_atualizar_pelo_ay.ps1).
Uso: "dist\\AY ESCREVA\\program\\python.exe" tests\\atualizacao\\testar_instalar.py
SPDX-License-Identifier: MPL-2.0
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'tests' / 'uno'))
sys.path.insert(0, str(RAIZ / 'extensao' / 'ayescreva' / 'pythonpath'))
from ay_uno import Motor, SAIDA_TESTES, salvar, fechar  # noqa: E402
import ay_atualizacao as A  # noqa: E402

itens = []


def verificar(descricao, ok, detalhe=''):
    itens.append({'ok': bool(ok), 'verificacao': descricao, 'detalhe': str(detalhe)})
    print(f"[{'OK  ' if ok else 'FALHA'}] {descricao}{' — ' + str(detalhe) if detalhe else ''}", flush=True)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    A.registrar = lambda m: None
    saida = SAIDA_TESTES / 'atualizacao'
    saida.mkdir(parents=True, exist_ok=True)
    instalador = saida / 'AYEscreva-9.9.9-teste-windows11-x64.exe'
    instalador.write_bytes(b'MZ teste')
    with Motor('atualizacao') as mo:
        d = mo.novo()
        d.getText().setString('Texto que ainda não foi salvo.')
        try:
            A.instalar(mo.ctx, str(instalador), executar=False)
            r = None
        except A.Recusado as e:
            r = str(e)
        verificar('Documento com alteração não salva: a instalação é recusada e o documento é citado; nada é fechado',
                  r and 'salve ou feche' in r and not d.isModified() is False and mo.proc.poll() is None, r)
        arq = salvar(d, saida / 'salvo-antes-de-atualizar.odt')
        d.storeAsURL(arq.resolve().as_uri(), ())
        roteiro = A.instalar(mo.ctx, str(instalador), executar=False)
        txt = Path(roteiro).read_text(encoding='mbcs')
        verificar('Documentos salvos: o roteiro de instalação é preparado com o instalador conferido e a reabertura do AY',
                  str(instalador) in txt and 'AYEscreva.exe' in txt and mo.proc.poll() is None, roteiro)
        fechar(d)
    (saida / 'instalar.json').write_text(json.dumps({'itens': itens}, ensure_ascii=False, indent=1), encoding='utf-8')
    n = sum(1 for x in itens if x['ok'])
    print(f'Instalar atualização: {n}/{len(itens)}')
    return 0 if n == len(itens) else 1


if __name__ == '__main__':
    sys.exit(main())
