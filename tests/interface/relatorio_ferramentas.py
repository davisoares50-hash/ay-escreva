# -*- coding: utf-8 -*-
"""Gera docs/VALIDACAO-FERRAMENTAS.md: uma linha por ferramenta da faixa testada pelo efeito real (fases 12 e 12b de
tests/interface/testar_faixa.ps1), com o efeito conferido, desfazer/refazer e o resultado em ODT e DOCX, mais as
ferramentas que continuam só acionadas e o motivo.

Uso (com o Python do AY): python relatorio_ferramentas.py
SPDX-License-Identifier: MPL-2.0
"""
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'tests' / 'uno'))


def carregar(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8-sig'))
    except Exception:
        return None


def sim_nao(v, motivo=''):
    if v is True:
        return 'sim'
    if v is False:
        return 'NÃO' + (f' — {motivo}' if motivo else '')
    return '—'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    faixa = carregar(RAIZ / 'tests' / 'output' / 'interface' / 'faixa-resultado.json') or {}
    fs = faixa.get('ferramentas') or {}
    from comandos import LIMITACOES  # noqa: E402 (motivos das ferramentas sem conferência automática)
    mapa = carregar(RAIZ / 'out' / 'faixa' / 'mapa.json') or {'botoes': []}
    abas = carregar(RAIZ / 'ui' / 'abas.json')
    ordem = [a['rotulo'] for a in abas['abas']] + [a['rotulo'] for a in abas['contextuais']]
    linhas = []
    for chave, r in fs.items():
        if chave.startswith('(queda)'):
            continue
        aba, _, funcao = chave.partition(' › ')
        linhas.append((ordem.index(aba) if aba in ordem else 99, aba, funcao, r))
    linhas.sort(key=lambda x: (x[0], x[2]))
    quedas = [r for k, r in fs.items() if k.startswith('(queda)')]
    ok = sum(1 for *_x, r in linhas if r.get('validado'))
    out = ['# Validação das ferramentas da faixa pelo efeito real', '',
           f'> Gerado por `tests/interface/relatorio_ferramentas.py` em {date.today().isoformat()} a partir do teste pela interface '
           f'de {faixa.get("inicio", "?")} (fases 12 e 12b de `tests/interface/testar_faixa.ps1`). Não editar à mão.', '',
           'Cada ferramenta: o documento é limpo e preparado, o teste **clica no botão da faixa**; quando abre um diálogo, os campos são',
           'preenchidos pelos controles do próprio diálogo e ele é confirmado com **Enter do teclado de verdade**. O **efeito** é conferido',
           'no documento pela API do motor; **Ctrl+Z** (o mesmo comando do teclado) tem de voltar ao estado anterior e **refazer**, ao',
           'efeito; por fim o documento é **salvo em ODT e em DOCX, fechado e reaberto**, e o efeito é conferido no arquivo reaberto.',
           '"—" = não se aplica (a ferramenta só muda a exibição ou a seleção, ou não altera o arquivo). As ferramentas com diálogo',
           'rodam cada uma num aplicativo próprio (fase 12b): se o motor cair, a queda fica registrada só naquela ferramenta.', '',
           f'**Resumo:** {ok} de {len(linhas)} ferramentas testadas com efeito, desfazer/refazer e ODT conferidos'
           + (f'; {len(quedas)} com queda do motor durante o teste' if quedas else '') + '.', '',
           '| Aba | Ferramenta | Efeito conferido | Desfazer / refazer | ODT reaberto | DOCX reaberto | Resultado |',
           '|---|---|---|---|---|---|---|']
    cel = lambda s: str(s).replace('|', '/').replace('\n', ' ')
    for _o, aba, funcao, r in linhas:
        efeito = f"{r.get('oque', '')}: {r.get('antes', '?')} → {r.get('depois', '?')}" if r.get('efeito') else \
            f"NÃO ({r.get('oque', '')}; {r.get('antes', '?')} → {r.get('depois', '?')})"
        desf = '—' if r.get('desfazer') is None else f"{sim_nao(r.get('desfazer'))} / {sim_nao(r.get('refazer'))}"
        if r.get('desfazer') is False and r.get('pilha_desfazer'):
            desf += f" (pilha: {', '.join(r['pilha_desfazer'][:2])})"
        odt = sim_nao(r.get('odt'), r.get('odt_limite', '')) if 'odt' in r else '—'
        docx = sim_nao(r.get('docx'), r.get('docx_limite') or f"reaberto: {r.get('docx_valor', '')}") if 'docx' in r else '—'
        res = 'validada' if r.get('validado') else ('FALHOU' if not r.get('erro') else 'erro no teste: ' + r['erro'].strip().splitlines()[-1][:120])
        out.append(f'| {cel(aba)} | {cel(funcao)} | {cel(efeito)} | {cel(desf)} | {cel(odt)} | {cel(docx)} | {cel(res)} |')
    if quedas:
        out += ['', '## Quedas do motor durante o teste', '']
        out += [f"- `{r['comando']}`: {r['resumo']}" for r in quedas]
    # ferramentas sem teste de efeito automático, com o motivo conhecido
    testadas = {r.get('comando') for *_x, r in linhas}
    sem = [(b['rotuloAba'], b['funcao'], b['comando']) for b in mapa['botoes'] if b['comando'] in LIMITACOES and b['comando'] not in testadas]
    if sem:
        out += ['', '## Sem conferência automática do efeito (motivo)', '', '| Aba | Ferramenta | Motivo |', '|---|---|---|']
        out += [f'| {a} | {f} | {LIMITACOES[c]} |' for a, f, c in sem]
    destino = RAIZ / 'docs' / 'VALIDACAO-FERRAMENTAS.md'
    destino.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'{destino}: {ok}/{len(linhas)} validadas; quedas {len(quedas)}')


if __name__ == '__main__':
    main()
