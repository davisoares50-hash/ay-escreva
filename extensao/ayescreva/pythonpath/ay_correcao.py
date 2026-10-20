# -*- coding: utf-8 -*-
"""Correção automática de casos inequívocos (pt-BR): decisão pura, sem UNO, testável fora do aplicativo.

A tabela vem de dados/correcoes_pt_BR.json (tools/gerar_correcoes.py). A decisão recebe a palavra que acabou de
ser digitada e o contexto; devolve a correção ou o motivo de não corrigir. Nunca corrige: nomes próprios
(maiúscula no meio da frase), siglas, grafias mistas, palavras com dígitos ou símbolos, citações, texto em outro
idioma, palavras do dicionário pessoal e palavras marcadas "não corrigir novamente".
SPDX-License-Identifier: MPL-2.0
"""
import json
import os
import re

LETRAS = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ]+$")
# Fechamento de aspas que conta como citação aberta no parágrafo
ABERTURAS = {'“': '”', '«': '»', '‘': '’'}


class Tabela:
    """Carrega a tabela sob demanda (o arquivo tem ~2,5 MB)."""

    def __init__(self, caminho):
        self.caminho = caminho
        self._dados = None

    @property
    def correcoes(self):
        if self._dados is None:
            with open(self.caminho, encoding='utf-8') as f:
                self._dados = json.load(f)
        return self._dados['correcoes']

    def get(self, chave):
        return self.correcoes.get(chave)

    def __len__(self):
        return len(self.correcoes)


def caminho_padrao():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dados', 'correcoes_pt_BR.json')


def em_citacao(prefixo):
    """O texto do parágrafo antes da palavra deixa uma citação aberta? (aspas curvas, angulares ou retas)."""
    for abre, fecha in ABERTURAS.items():
        if prefixo.count(abre) > prefixo.count(fecha):
            return True
    return prefixo.count('"') % 2 == 1


def ajustar_caixa(modelo, correcao):
    if modelo[:1].isupper():
        return correcao[:1].upper() + correcao[1:]
    return correcao


def decidir(palavra, tabela, *, inicio_de_frase, prefixo='', idioma_ptbr=True, nao_corrigir=(), valida=None,
            estilo_protegido=False):
    """Devolve (correção, motivo). correção é None quando não se deve corrigir; motivo explica a decisão."""
    if not palavra:
        return None, 'vazia'
    if not idioma_ptbr:
        return None, 'texto em outro idioma'
    if estilo_protegido:
        return None, 'estilo de citação, código ou texto pré-formatado'
    if em_citacao(prefixo):
        return None, 'dentro de citação'
    if not LETRAS.match(palavra):
        return None, 'tem dígito, símbolo ou pontuação (número, data, termo técnico, endereço)'
    if len(palavra) > 1 and palavra.isupper():
        return None, 'sigla'
    if any(c.isupper() for c in palavra[1:]):
        return None, 'grafia com maiúsculas no meio (termo técnico ou marca)'
    if palavra[0].isupper() and not inicio_de_frase:
        return None, 'maiúscula no meio da frase (nome próprio)'
    base = palavra.lower()
    if base in nao_corrigir:
        return None, 'marcada "não corrigir novamente"'
    correcao = tabela.get(base)
    if correcao is None:
        return None, 'sem correção inequívoca'
    if valida is not None and valida(palavra):
        return None, 'palavra aceita pelo dicionário (inclui o dicionário pessoal)'
    return ajustar_caixa(palavra, correcao), 'tabela de casos inequívocos'
