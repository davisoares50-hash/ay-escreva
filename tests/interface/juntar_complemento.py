# -*- coding: utf-8 -*-
"""Junta ao relatório da bateria (faixa-resultado.json) os resultados de uma execução complementar das fases 12/12b
(ferramentas acrescentadas ou separadas depois da bateria), marcando a origem de cada resultado.

Uso: python juntar_complemento.py <bateria.json> <complemento.json> [<complemento2.json> ...]  > grava faixa-resultado.json
SPDX-License-Identifier: MPL-2.0
"""
import json
import sys
from pathlib import Path

SAIDA = Path(__file__).resolve().parents[2] / 'tests' / 'output' / 'interface' / 'faixa-resultado.json'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    base = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    base.setdefault('ferramentas', {})
    base.setdefault('complementos', [])
    for arq in sys.argv[2:]:
        c = json.loads(Path(arq).read_text(encoding='utf-8-sig'))
        origem = f'complemento de {c.get("inicio") or c.get("data", "?")} ({Path(arq).name})'
        base['complementos'].append(origem)
        for chave, r in (c.get('ferramentas') or {}).items():
            antigo = base['ferramentas'].get(chave)
            if antigo and antigo.get('validado') and not r.get('validado'):
                continue                       # não troca um resultado validado por uma execução que falhou
            r = dict(r, origem=origem)
            base['ferramentas'][chave] = r
            if chave.startswith('(queda)'):
                continue
            f = base['funcoes'].setdefault(chave, {'presente': False, 'acionado': False, 'validado': False, 'detalhes': []})
            if r.get('validado'):
                f['validado'] = True
                f['acionado'] = True
                if r.get('resumo') and r['resumo'] not in f['detalhes']:
                    f['detalhes'].append(r['resumo'])
            base['efeitos'].append({'funcao': f'{chave} (efeito real, {origem})', 'ok': bool(r.get('validado')), 'detalhe': r.get('resumo', '')})
    SAIDA.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding='utf-8')
    fs = base['ferramentas']
    print(f'{SAIDA}: {sum(1 for v in fs.values() if v.get("validado"))} ferramentas validadas de {len(fs)}; '
          f'funções validadas: {sum(1 for v in base["funcoes"].values() if v.get("validado"))}')


if __name__ == '__main__':
    main()
