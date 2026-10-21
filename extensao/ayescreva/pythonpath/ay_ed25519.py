# -*- coding: utf-8 -*-
"""Verificação de assinaturas Ed25519 (RFC 8032), em Python puro, para conferir o arquivo de versões das atualizações.

O AY só verifica (nunca assina): a chave privada do projeto fica fora do repositório, com quem publica as versões, e a
assinatura é feita por tools/gerar-manifesto.mjs (Node.js, módulo crypto). Esta implementação segue o código de
referência da RFC 8032, seção 6, e é conferida com os vetores de teste da RFC e com assinaturas do Node.js
(tests/atualizacao/testar_atualizacao.py).
SPDX-License-Identifier: MPL-2.0
"""
import hashlib

P = 2 ** 255 - 19
L = 2 ** 252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
I = pow(2, (P - 1) // 4, P)


def _xrecover(y):
    xx = (y * y - 1) * pow(D * y * y + 1, P - 2, P)
    x = pow(xx, (P + 3) // 8, P)
    if (x * x - xx) % P != 0:
        x = x * I % P
    if x % 2 != 0:
        x = P - x
    return x


_BY = 4 * pow(5, P - 2, P) % P
_B = (_xrecover(_BY) % P, _BY, 1, _xrecover(_BY) * _BY % P)      # ponto base em coordenadas estendidas (X, Y, Z, T)


def _somar(p, q):
    a = (p[1] - p[0]) * (q[1] - q[0]) % P
    b = (p[1] + p[0]) * (q[1] + q[0]) % P
    c = 2 * p[3] * q[3] * D % P
    d = 2 * p[2] * q[2] % P
    e, f, g, h = b - a, d - c, d + c, b + a
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _multiplicar(s, p):
    q = (0, 1, 1, 0)                     # elemento neutro
    while s > 0:
        if s & 1:
            q = _somar(q, p)
        p = _somar(p, p)
        s >>= 1
    return q


def _iguais(p, q):
    return (p[0] * q[2] - q[0] * p[2]) % P == 0 and (p[1] * q[2] - q[1] * p[2]) % P == 0


def _descomprimir(s):
    if len(s) != 32:
        raise ValueError('ponto com tamanho errado')
    y = int.from_bytes(s, 'little')
    sinal = y >> 255
    y &= (1 << 255) - 1
    if y >= P:
        raise ValueError('ponto inválido')
    xx = (y * y - 1) * pow(D * y * y + 1, P - 2, P) % P
    if xx == 0:
        if sinal:
            raise ValueError('ponto inválido')
        x = 0
    else:
        x = pow(xx, (P + 3) // 8, P)
        if (x * x - xx) % P != 0:
            x = x * I % P
        if (x * x - xx) % P != 0:
            raise ValueError('ponto fora da curva')
        if x & 1 != sinal:
            x = P - x
    return (x, y, 1, x * y % P)


def verificar(chave_publica, mensagem, assinatura):
    """True se `assinatura` (64 bytes) é a assinatura Ed25519 de `mensagem` pela `chave_publica` (32 bytes)."""
    try:
        if len(chave_publica) != 32 or len(assinatura) != 64:
            return False
        a = _descomprimir(chave_publica)
        r = _descomprimir(assinatura[:32])
        s = int.from_bytes(assinatura[32:], 'little')
        if s >= L:
            return False
        h = int.from_bytes(hashlib.sha512(assinatura[:32] + chave_publica + mensagem).digest(), 'little') % L
        return _iguais(_multiplicar(s, _B), _somar(r, _multiplicar(h, a)))
    except (ValueError, TypeError):
        return False
