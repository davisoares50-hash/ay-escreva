// Gera extensao/ayescreva/dados/ia-avaliacao.json (o resumo que "Gerenciar IA local" mostra para cada modelo)
// a partir de tests/output/ia/avaliacao.json, produzido por tests/ia/avaliar_modelos.py neste computador.
// Uso: node tools/ia-avaliacao.mjs
// SPDX-License-Identifier: MPL-2.0
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const fonte = path.join(raiz, 'tests', 'output', 'ia', 'avaliacao.json');
const destino = path.join(raiz, 'extensao', 'ayescreva', 'dados', 'ia-avaliacao.json');
const a = JSON.parse(fs.readFileSync(fonte, 'utf8'));
const br = (n, casas = 1) => n == null ? '?' : n.toFixed(casas).replace('.', ',');
const modelos = a.resultados.map((r) => ({
  id: r.id,
  computador: a.computador,
  resumo: `${r.aprovados} casos do teste do AY em pt-BR; pedido curto em ~${br(r.tempo_medio_s)} s; ` +
    `~${br(r.tokens_por_s)} tokens/s; memória ~${br(r.memoria_pico_mb / 1024)} GB; ` +
    `carga ${br(r.carga_s, 0)} s no primeiro uso`,
}));
const saida = {
  descricao: 'Medidas da avaliação dos modelos (tests/ia/avaliar_modelos.py) num único computador; outros podem ser mais lentos.',
  medido_em: a.data.slice(0, 10),
  modelos,
};
fs.writeFileSync(destino, JSON.stringify(saida, null, 2) + '\n');
console.log(destino);
for (const m of modelos) console.log(`${m.id}: ${m.resumo}`);
