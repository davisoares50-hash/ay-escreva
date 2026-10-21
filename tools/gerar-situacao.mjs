// Gera docs/SITUACAO.md: a lista única do projeto em três situações — concluído e testado, implementado sem
// validação completa, ainda não implementado — juntando os itens do pedido original e das entregas
// (docs/situacao-base.json, mantido à mão com a evidência de cada item) com a matriz das ferramentas da faixa
// (docs/MATRIZ-FUNCIONALIDADES.md, gerada pelos testes).
// Uso: node tools/gerar-situacao.mjs
// SPDX-License-Identifier: MPL-2.0
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const base = JSON.parse(fs.readFileSync(path.join(raiz, 'docs', 'situacao-base.json'), 'utf8'));
const matriz = fs.readFileSync(path.join(raiz, 'docs', 'MATRIZ-FUNCIONALIDADES.md'), 'utf8');

const SIT = {
  testado: '✅ Concluído e testado',
  parcial: '🟡 Implementado sem validação completa',
  pendente: '⬜ Ainda não implementado',
};

// ferramentas da faixa, por aba, a partir da matriz gerada pelos testes
const abas = [];
let aba = null;
for (const linha of matriz.split(/\r?\n/)) {
  const t = linha.match(/^## (.+)$/);
  if (t) { aba = { nome: t[1].trim(), itens: [] }; abas.push(aba); continue; }
  if (!aba || !linha.startsWith('| ') || linha.startsWith('| Grupo') || linha.startsWith('|---')) continue;
  const c = linha.split('|').slice(1, -1).map((x) => x.trim());
  if (c.length < 9) continue;
  const [grupo, funcao, comando, encontrado, implementada, validado] = c;
  let sit;
  if (/^Não|pendente/i.test(implementada) || encontrado.startsWith('Não') || comando === '—' || comando === '') sit = 'pendente';
  else if (/Pela interface:|Por API:/.test(validado)) sit = 'testado';
  else sit = 'parcial';
  const como = sit === 'testado' ? (validado.match(/(Pela interface|Por API)[^·]*/) || [''])[0].trim()
    : sit === 'parcial' ? (/Acionado/.test(validado) ? 'botão acionado pela interface; efeito não conferido' : 'botão presente; não validado')
      : (c[8] || 'sem comando no motor');
  aba.itens.push({ grupo, funcao, sit, como: como.replace(/\|/g, '/') });
}

const cont = (itens) => Object.fromEntries(Object.keys(SIT).map((k) => [k, itens.filter((i) => i.sit === k).length]));
const todas = abas.flatMap((a) => a.itens);
const ctot = cont(todas);
const cbase = cont(base.secoes.flatMap((s) => s.itens));

const out = [];
out.push('# Situação do projeto AY ESCREVA — lista única', '');
out.push(`> Gerado por \`tools/gerar-situacao.mjs\` em ${base.atualizado_em}, a partir de \`docs/situacao-base.json\` (itens do`,
  '> pedido original e das entregas, com a evidência de cada um) e de `docs/MATRIZ-FUNCIONALIDADES.md` (ferramentas da faixa,',
  '> geradas pelos testes). Não editar à mão.', '');
out.push(`Versão pública: **${base.versao_publica}**. Versão de testes local mais recente: **${base.versao_local}**`,
  `(\`${base.instalador_local}\`).`, '');
out.push('| Situação | Requisitos e entregas | Ferramentas da faixa |', '|---|---|---|');
for (const k of Object.keys(SIT)) out.push(`| ${SIT[k]} | ${cbase[k]} | ${ctot[k]} |`);
out.push('', 'Legenda: **concluído e testado** = há teste automatizado que conferiu o efeito (pela interface ou pela API do motor);',
  '**implementado sem validação completa** = existe e foi acionado ou conferido só em parte; **ainda não implementado** =',
  'não existe nesta versão.', '');

for (const s of base.secoes) {
  out.push(`## ${s.titulo}`, '');
  if (s.nota) out.push(s.nota, '');
  out.push('| Item | Situação | Evidência ou pendência |', '|---|---|---|');
  for (const i of s.itens) out.push(`| ${i.item} | ${SIT[i.sit]} | ${i.evidencia.replace(/\|/g, '/')} |`);
  out.push('');
}

out.push('## Ferramentas da faixa de opções (pedido original, por aba)', '',
  'Cada função pedida, com o resultado dos testes. Detalhes (comando, critério de aceite) em',
  '[MATRIZ-FUNCIONALIDADES.md](MATRIZ-FUNCIONALIDADES.md). "Implementado sem validação completa" aqui é, na maioria, um',
  'botão que o teste aciona e confirma o comando disparado, sem conferir o efeito no documento. As ferramentas próprias',
  'do AY (Assistente AY, IA local, formatação acadêmica, conferências, atualizações) têm testes dedicados, contados na',
  'seção "Entregas de assistência à escrita" acima.', '');
for (const a of abas) {
  if (!a.itens.length) continue;
  const c = cont(a.itens);
  out.push(`### ${a.nome} — ✅ ${c.testado} · 🟡 ${c.parcial} · ⬜ ${c.pendente}`, '');
  out.push('| Grupo | Função | Situação | Como foi verificado |', '|---|---|---|---|');
  for (const i of a.itens) out.push(`| ${i.grupo} | ${i.funcao} | ${SIT[i.sit]} | ${i.como} |`);
  out.push('');
}
fs.writeFileSync(path.join(raiz, 'docs', 'SITUACAO.md'), out.join('\n'));
console.log('SITUACAO.md:', 'requisitos', cbase, 'ferramentas', ctot);
