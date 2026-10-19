// Gera a página "Atalhos de teclado" do AY ESCREVA a partir da configuração REAL do motor
// (Accelerators + rótulos pt-BR dos comandos), para que a ajuda nunca mostre atalho inexistente.
// Uso: node gerar-atalhos.mjs <pasta share/registry da distribuição> <saida.html>
// SPDX-License-Identifier: MPL-2.0
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';

const [registro, saida] = process.argv.slice(2);
const arquivos = ['main.xcd', 'writer.xcd', 'res/registry_pt-BR.xcd', 'Langpack-pt-BR.xcd', 'ayescreva.xcd']
  .map((f) => join(registro, f)).filter(existsSync);

// Percorre os dados (component-data) e chama visitante(caminho, propriedade, valoresPorIdioma)
function percorrer(texto, componente, visitante) {
  const re = /<(\/?)(oor:component-data|node|prop|value)\b([^>]*?)(\/?)>|([^<]+)/g;
  const pilha = [];
  let dentro = false, prop = null, lang = null, valores = null, m;
  while ((m = re.exec(texto))) {
    const [, fecha, tag, attrs, auto, txt] = m;
    if (txt !== undefined) {
      if (prop && lang !== null) valores[lang] = (valores[lang] || '') + txt;
      continue;
    }
    const nome = /oor:name="([^"]*)"/.exec(attrs || '')?.[1];
    if (tag === 'oor:component-data') {
      if (fecha) { dentro = false; pilha.length = 0; } else dentro = nome === componente;
      continue;
    }
    if (!dentro) continue;
    if (tag === 'node') { if (fecha) pilha.pop(); else if (!auto) pilha.push(nome); }
    else if (tag === 'prop') {
      if (fecha) { visitante(pilha.slice(), prop, valores); prop = null; }
      else if (auto) visitante(pilha.slice(), nome, {});
      else { prop = nome; valores = {}; }
    } else if (tag === 'value') {
      if (fecha) lang = null;
      else if (!auto) lang = /xml:lang="([^"]*)"/.exec(attrs || '')?.[1] || 'padrao';
    }
  }
}
const desfaz = (s) => s.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'");
const escolher = (v) => desfaz((v['pt-BR'] ?? v['en-US'] ?? v.padrao ?? Object.values(v)[0] ?? '').trim());

// Rótulos dos comandos
const rotulos = new Map();
for (const comp of ['GenericCommands', 'WriterCommands']) {
  for (const f of arquivos) {
    percorrer(readFileSync(f, 'utf8'), comp, (caminho, prop, v) => {
      if (caminho[0] === 'UserInterface' && caminho[1] === 'Commands' && caminho.length === 3 && prop === 'Label') {
        const r = escolher(v); if (r) rotulos.set(caminho[2], r.replace(/~/g, ''));
      }
    });
  }
}
// Atalhos: global e do Writer (o do Writer prevalece)
const atalhos = new Map();
for (const f of arquivos) {
  percorrer(readFileSync(f, 'utf8'), 'Accelerators', (caminho, prop, v) => {
    if (caminho[0] !== 'PrimaryKeys' || prop !== 'Command') return;
    let escopo = null, tecla = null;
    if (caminho[1] === 'Global' && caminho.length === 3) { escopo = 'Global'; tecla = caminho[2]; }
    if (caminho[1] === 'Modules' && caminho[2] === 'com.sun.star.text.TextDocument' && caminho.length === 4) { escopo = 'Writer'; tecla = caminho[3]; }
    if (!escopo) return;
    const cmd = escolher(v);
    if (!cmd) return;
    const ant = atalhos.get(tecla);
    if (!ant || escopo === 'Writer' || ant.escopo === 'Global') atalhos.set(tecla, { escopo, cmd });
  });
}

const NOMES = { MOD1: 'Ctrl', MOD2: 'Alt', SHIFT: 'Shift', MOD3: 'Ctrl', ESCAPE: 'Esc', RETURN: 'Enter', SPACE: 'Espaço', BACKSPACE: 'Backspace',
  DELETE: 'Delete', INSERT: 'Insert', TAB: 'Tab', UP: '↑', DOWN: '↓', LEFT: '←', RIGHT: '→', HOME: 'Home', END: 'End', PAGEUP: 'Page Up',
  PAGEDOWN: 'Page Down', ADD: '+', SUBTRACT: '-', MULTIPLY: '*', DIVIDE: '/', POINT: '.', COMMA: ',', LESS: '<', GREATER: '>', EQUAL: '=',
  BRACKETLEFT: '[', BRACKETRIGHT: ']', SEMICOLON: ';', QUOTELEFT: '`', TILDE: '~', QUOTERIGHT: "'", CONTEXTMENU: 'Menu' };
function tecla(nome) {
  const partes = nome.split('_');
  const base = partes.shift();
  const mods = ['MOD1', 'MOD2', 'SHIFT'].filter((m) => partes.includes(m)).map((m) => NOMES[m]);
  return [...mods, NOMES[base] || base].join('+');
}
function descrever(cmd) {
  const [c, q] = cmd.split('?');
  let r = rotulos.get(c) || c.replace('.uno:', '');
  if (q) {
    const estilo = /Style:string=([^&]+)/.exec(q)?.[1];
    if (estilo) r = `${r}: ${decodeURIComponent(estilo)}`;
  }
  return r;
}
const linhas = [...atalhos.entries()]
  .map(([k, { escopo, cmd }]) => ({ tecla: tecla(k), acao: descrever(cmd), cmd, escopo }))
  .filter((l) => !/^\.uno:(Macro|BasicIDE)/.test(l.cmd))
  .sort((a, b) => a.tecla.localeCompare(b.tecla, 'pt-BR'));

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const html = `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Atalhos de teclado — AY ESCREVA</title>
<style>
:root{--verde:#11806A;--tinta:#1E2A28;--cinza:#5B6664;--fundo:#fff;--linha:#E3E8E7}
@media (prefers-color-scheme:dark){:root{--tinta:#E8EEEC;--cinza:#A9B4B2;--fundo:#141A19;--linha:#2A3533}}
body{font-family:"Segoe UI",system-ui,sans-serif;margin:0;background:var(--fundo);color:var(--tinta)}
header{background:var(--verde);color:#fff;padding:20px 24px}h1{margin:0;font-size:24px}
main{max-width:980px;margin:0 auto;padding:16px 24px}
input{width:100%;padding:10px 12px;font-size:16px;border:1px solid var(--linha);border-radius:8px;box-sizing:border-box;background:transparent;color:inherit}
table{width:100%;border-collapse:collapse;margin-top:12px}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--linha);vertical-align:top}
kbd{font-family:Consolas,monospace;background:rgba(17,128,106,.12);border:1px solid rgba(17,128,106,.35);border-radius:4px;padding:1px 6px;white-space:nowrap}
.nota{color:var(--cinza);font-size:14px}
</style></head><body>
<header><h1>Atalhos de teclado</h1><div>AY ESCREVA — gerado da configuração instalada (${linhas.length} atalhos)</div></header>
<main>
<p class="nota">Estes são os atalhos que funcionam nesta versão. Eles seguem o padrão do motor de documentos e <strong>não</strong> são idênticos aos do Word em português (por exemplo, negrito é <kbd>Ctrl+B</kbd>, não Ctrl+N). Você pode mudá-los em Arquivo › Configurações › Personalizar › Teclado. Pressione <kbd>Alt</kbd> para ver as teclas de acesso das abas.</p>
<label for="busca">Procurar atalho ou comando</label>
<input id="busca" type="search" placeholder="ex.: negrito, salvar, Ctrl+S" autocomplete="off">
<table><thead><tr><th scope="col">Tecla</th><th scope="col">Ação</th></tr></thead><tbody id="lista">
${linhas.map((l) => `<tr><td><kbd>${esc(l.tecla)}</kbd></td><td>${esc(l.acao)}</td></tr>`).join('\n')}
</tbody></table>
</main>
<script>
const b=document.getElementById('busca');b.addEventListener('input',()=>{const t=b.value.toLowerCase();for(const tr of document.querySelectorAll('#lista tr')){tr.hidden=t&&!tr.textContent.toLowerCase().includes(t);}});
</script>
</body></html>
`;
mkdirSync(dirname(saida), { recursive: true });
writeFileSync(saida, html);
console.log(`Atalhos: ${linhas.length} -> ${saida}`);
for (const k of ['B_MOD1', 'I_MOD1', 'U_MOD1', 'S_MOD1', 'N_MOD1', 'P_MOD1', 'Z_MOD1']) {
  const a = atalhos.get(k); console.log(`  ${tecla(k)} = ${a ? descrever(a.cmd) : '(nenhum)'}`);
}
