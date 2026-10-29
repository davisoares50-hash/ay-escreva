# -*- coding: utf-8 -*-
"""Procura a chave privada de assinatura das atualizações em pastas e no histórico do git, sem nunca exibi-la.

A chave fica fora do repositório (%USERPROFILE%\\.ay-escreva\\chave-atualizacoes-ed25519.pem). Este roteiro lê o
arquivo só para montar o que procurar — o PEM, o DER, a semente (hexadecimal, base64) — e varre cada arquivo byte a byte,
além de qualquer bloco PEM de chave privada. Imprime só caminhos e contagens. Sem a chave neste computador, não procura
o conteúdo (só blocos PEM de chave privada) e diz isso.

Uso (com o Python do AY):
  python procurar_chave_privada.py [--git] rotulo=pasta [rotulo=pasta ...]
Sai com código 1 se encontrar algo.
SPDX-License-Identifier: MPL-2.0
"""
import base64
import os
import re
import subprocess
import sys

CHAVE = os.path.join(os.environ.get('USERPROFILE', ''), '.ay-escreva', 'chave-atualizacoes-ed25519.pem')
# um bloco PEM de verdade: o cabeçalho seguido do conteúdo em base64 (só o texto do cabeçalho aparece, por exemplo,
# como constante dentro das bibliotecas do motor, que leem arquivos PEM, e não é uma chave)
CABECALHO = re.compile(rb'-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----\r?\n[A-Za-z0-9+/=\r\n]{40,}')


def agulhas():
    if not os.path.exists(CHAVE):
        return {}
    pem = open(CHAVE, 'rb').read()
    corpo = ''.join(l.strip() for l in pem.decode('ascii').splitlines() if l.strip() and not l.startswith('-----'))
    der = base64.b64decode(corpo)
    semente = der[-32:]
    return {
        'PEM': corpo.encode(), 'PEM (início)': corpo[:32].encode(), 'DER': der, 'semente': semente,
        'semente hex': semente.hex().encode(), 'semente HEX': semente.hex().upper().encode(),
        'semente base64': base64.b64encode(semente).rstrip(b'='), 'semente base64url': base64.urlsafe_b64encode(semente).rstrip(b'='),
    }


def varrer(raiz, ag):
    achados, arquivos, total = set(), 0, 0
    pular = os.path.join(raiz, '.git').lower()
    for pasta, subpastas, nomes in os.walk(raiz):
        subpastas[:] = [s for s in subpastas if os.path.join(pasta, s).lower() != pular]
        for n in nomes:
            c = os.path.join(pasta, n)
            try:
                with open(c, 'rb') as f:
                    resto = b''
                    while True:
                        bloco = f.read(16 * 2**20)
                        if not bloco:
                            break
                        dados = resto + bloco
                        for nome, a in ag.items():
                            if a in dados:
                                achados.add((c, nome))
                        if CABECALHO.search(dados):
                            achados.add((c, 'bloco PEM de chave privada (qualquer chave)'))
                        resto = dados[-200:]
                        total += len(bloco)
                arquivos += 1
            except OSError:
                pass
    return sorted(achados), arquivos, total


def historico_git(raiz, ag):
    objs = subprocess.run(['git', '-C', raiz, 'cat-file', '--batch-all-objects', '--batch-check'], capture_output=True, text=True).stdout
    blobs = [l.split()[0] for l in objs.splitlines() if len(l.split()) == 3 and l.split()[1] == 'blob']
    p = subprocess.Popen(['git', '-C', raiz, 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    saida, _ = p.communicate(('\n'.join(blobs) + '\n').encode())
    return len(blobs), [n for n, a in ag.items() if a in saida] + (['bloco PEM de chave privada'] if CABECALHO.search(saida) else [])


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ag = agulhas()
    print('chave privada neste computador:', 'sim (procurando o conteúdo dela, sem exibi-lo)' if ag
          else 'não (só blocos PEM de chave privada são procurados)')
    problemas = 0
    for arg in sys.argv[1:]:
        if arg == '--git':
            n, hits = historico_git(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ag)
            print(f'histórico do git: {n} objetos — encontrado: {hits or "nada"}')
            problemas += len(hits)
            continue
        rotulo, _, pasta = arg.partition('=')
        achados, arquivos, total = varrer(pasta, ag)
        print(f'{rotulo}: {arquivos} arquivos, {total / 1e6:.0f} MB — ocorrências: {len(achados)}')
        for c, nome in achados:
            print('   ', c, '→', nome)
        problemas += len(achados)
    return 1 if problemas else 0


if __name__ == '__main__':
    sys.exit(main())
