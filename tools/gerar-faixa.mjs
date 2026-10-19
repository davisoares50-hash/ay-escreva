// Gera a faixa de opções do AY ESCREVA (notebookbar_ayescreva.ui) a partir de ui/abas.json.
//
// Regras:
//  - abas na ordem do arquivo; abas contextuais (Tabela, Imagem, Forma, Visualizar impressão) só aparecem
//    no contexto correspondente;
//  - só vira botão a função que tem comando do motor (comando) ou comando da extensão AY (comandoAY) e
//    não está marcada com botao=false. Funções pendentes NÃO aparecem (nada de botão decorativo);
//  - comandos com seta de lista usam GtkMenuToolButton apenas quando marcados com "lista": a seta precisa
//    de um controlador que a preencha, senão seria decorativa;
//  - ícones de comandos AY são conferidos no tema de ícones da base.
//
// Uso: node gerar-faixa.mjs <abas.json> <saida.ui> [tema-icones.zip]
// SPDX-License-Identifier: MPL-2.0
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

const [entrada, saida, temaZip, abaAtivaArg, saidaMapa] = process.argv.slice(2);
const abaAtiva = abaAtivaArg && abaAtivaArg !== '-' ? abaAtivaArg : null;  // só para capturas de inspeção
// Mapa comando -> caixa de botões e posição, usado pelos testes pela interface (tests/interface)
const mapa = [];
let abaCorrente = null;
if (!entrada || !saida) {
  console.error('uso: node gerar-faixa.mjs <abas.json> <saida.ui> [tema-icones.zip]');
  process.exit(2);
}
const def = JSON.parse(readFileSync(entrada, 'utf8'));

// Lista os nomes de um .zip lendo o diretório central (sem dependências externas)
function nomesNoZip(arquivo) {
  const b = readFileSync(arquivo);
  let eocd = -1;
  for (let i = b.length - 22; i >= Math.max(0, b.length - 65557); i--) { if (b.readUInt32LE(i) === 0x06054b50) { eocd = i; break; } }
  if (eocd < 0) throw new Error('zip sem diretório central');
  const total = b.readUInt16LE(eocd + 10);
  let p = b.readUInt32LE(eocd + 16);
  const nomes = new Set();
  for (let k = 0; k < total; k++) {
    const n = b.readUInt16LE(p + 28), e = b.readUInt16LE(p + 30), c = b.readUInt16LE(p + 32);
    nomes.add(b.toString('utf8', p + 46, p + 46 + n));
    p += 46 + n + e + c;
  }
  return nomes;
}
let icones = null;
if (temaZip) {
  try { icones = nomesNoZip(temaZip); } catch (e) { console.log(`AVISO: não foi possível ler ${temaZip}: ${e.message}`); }
}
const ICONE_RESERVA = 'cmd/lc_helpindex.png';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
let seq = 0;
const novoId = (p) => `${p}${++seq}`;
const avisos = [];

function comandoDo(item) { return item.comando || item.comandoAY || null; }
function visivel(item) { return item.botao !== false && !!comandoDo(item); }

function botao(item, ind) {
  const cmd = comandoDo(item);
  const classe = item.lista ? 'GtkMenuToolButton' : 'GtkToolButton';
  const id = novoId('btn');
  const p = [
    `${ind}<object class="${classe}" id="${id}">`,
    `${ind}  <property name="visible">True</property>`,
    `${ind}  <property name="can-focus">False</property>`,
    `${ind}  <property name="action-name">${esc(cmd)}</property>`,
  ];
  if (!item.comando && item.comandoAY) {
    // Comandos da extensão AY não têm rótulo/ícone no registro do motor: definidos aqui
    let icone = item.icone || ICONE_RESERVA;
    if (icones && !icones.has(icone)) { avisos.push(`ícone ausente no tema: ${icone} (${item.funcao}); usando ${ICONE_RESERVA}`); icone = ICONE_RESERVA; }
    p.push(`${ind}  <property name="label">${esc(item.funcao)}</property>`);
    p.push(`${ind}  <property name="tooltip-text">${esc(item.funcao)}</property>`);
    p.push(`${ind}  <property name="icon-name">${esc(icone)}</property>`);
  }
  p.push(`${ind}  <property name="use-underline">True</property>`);
  p.push(`${ind}</object>`);
  return p.join('\n');
}

function caixa(itens, estilo, ind, opcoes = {}) {
  const id = novoId('tb');
  itens.forEach((it, k) => mapa.push({ aba: abaCorrente.id, rotuloAba: abaCorrente.rotulo, funcao: it.funcao, comando: comandoDo(it), caixa: id, posicao: k }));
  const linhas = [
    `${ind}<object class="sfxlo-NotebookbarToolBox" id="${id}">`,
    `${ind}  <property name="visible">True</property>`,
    `${ind}  <property name="can-focus">False</property>`,
    `${ind}  <property name="toolbar-style">${estilo}</property>`,
    `${ind}  <property name="show-arrow">False</property>`,
  ];
  if (opcoes.grande) linhas.push(`${ind}  <property name="icon_size">3</property>`);
  if (opcoes.valign) linhas.push(`${ind}  <property name="valign">${opcoes.valign}</property>`, `${ind}  <property name="vexpand">True</property>`);
  for (const it of itens) {
    linhas.push(`${ind}  <child>`, botao(it, ind + '    '), `${ind}    <packing>`,
      `${ind}      <property name="expand">False</property>`, `${ind}      <property name="homogeneous">False</property>`,
      `${ind}    </packing>`, `${ind}  </child>`);
  }
  linhas.push(`${ind}</object>`);
  return linhas.join('\n');
}

function anexar(conteudo, col, linha, ind, largura = 1, altura = 1) {
  return [`${ind}<child>`, conteudo, `${ind}  <packing>`,
    `${ind}    <property name="left-attach">${col}</property>`, `${ind}    <property name="top-attach">${linha}</property>`,
    largura > 1 ? `${ind}    <property name="width">${largura}</property>` : null,
    altura > 1 ? `${ind}    <property name="height">${altura}</property>` : null,
    `${ind}  </packing>`, `${ind}</child>`].filter(Boolean).join('\n');
}

function grupo(g, ind) {
  const itens = g.itens.filter(visivel);
  if (itens.length === 0) return null;
  const idGrade = novoId('grp');
  const idRotulo = novoId('lbl');
  const filhos = [];
  let col = 0;
  // Botões grandes: um por coluna, ocupando duas linhas
  for (const it of itens.filter((i) => i.grande)) {
    filhos.push(anexar(caixa([it], 'both', ind + '    ', { grande: true, valign: 'center' }), col++, 0, ind + '  ', 1, 2));
  }
  const pequenos = itens.filter((i) => !i.grande);
  if (g.linhas) {
    // Linhas explícitas (ex.: Fonte e Parágrafo): cada linha é uma caixa de ícones
    const porNome = new Map(pequenos.map((i) => [comandoDo(i).replace(/^\.uno:/, ''), i]));
    const usados = new Set();
    g.linhas.forEach((nomes, li) => {
      const linhaItens = nomes.map((n) => porNome.get(n)).filter(Boolean);
      linhaItens.forEach((i) => usados.add(i));
      if (linhaItens.length) filhos.push(anexar(caixa(linhaItens, 'icons', ind + '    '), col, li, ind + '  '));
    });
    const sobras = pequenos.filter((i) => !usados.has(i));
    if (sobras.length) avisos.push(`grupo ${g.rotulo}: itens fora das linhas: ${sobras.map((s) => s.funcao).join(', ')}`);
    col++;
  } else if (g.compacto) {
    const porLinha = Math.ceil(pequenos.length / 2) || 1;
    for (let li = 0; li * porLinha < pequenos.length; li++) {
      filhos.push(anexar(caixa(pequenos.slice(li * porLinha, (li + 1) * porLinha), 'icons', ind + '    '), col, li, ind + '  '));
    }
    if (pequenos.length) col++;
  } else {
    // Pilhas de até 3 botões pequenos com ícone e texto, como no Word
    for (let i = 0; i < pequenos.length; i += 3) {
      const pilha = pequenos.slice(i, i + 3);
      const idPilha = novoId('pilha');
      const inner = [`${ind}    <object class="GtkBox" id="${idPilha}">`, `${ind}      <property name="visible">True</property>`,
        `${ind}      <property name="can-focus">False</property>`, `${ind}      <property name="orientation">vertical</property>`,
        `${ind}      <property name="valign">start</property>`];
      pilha.forEach((it, k) => {
        inner.push(`${ind}      <child>`, caixa([it], 'both-horiz', ind + '        '), `${ind}        <packing>`,
          `${ind}          <property name="expand">False</property>`, `${ind}          <property name="fill">True</property>`,
          `${ind}          <property name="position">${k}</property>`, `${ind}        </packing>`, `${ind}      </child>`);
      });
      inner.push(`${ind}    </object>`);
      filhos.push(anexar(inner.join('\n'), col++, 0, ind + '  ', 1, 2));
    }
  }
  const largura = Math.max(col, 1);
  // Rótulo do grupo
  filhos.push(anexar([`${ind}    <object class="GtkLabel" id="${idRotulo}">`, `${ind}      <property name="visible">True</property>`,
    `${ind}      <property name="can-focus">False</property>`, `${ind}      <property name="valign">end</property>`,
    `${ind}      <property name="vexpand">True</property>`, `${ind}      <property name="label">${esc(g.rotulo)}</property>`,
    `${ind}      <attributes>`, `${ind}        <attribute name="style" value="italic"/>`, `${ind}        <attribute name="scale" value="0.9"/>`,
    `${ind}      </attributes>`, `${ind}      <accessibility>`, `${ind}        <relation type="label-for" target="${idGrade}"/>`,
    `${ind}      </accessibility>`, `${ind}    </object>`].join('\n'), 0, 2, ind + '  ', largura, 1));
  // Separador vertical
  filhos.push(anexar([`${ind}    <object class="GtkSeparator">`, `${ind}      <property name="visible">True</property>`,
    `${ind}      <property name="can-focus">False</property>`, `${ind}      <property name="orientation">vertical</property>`,
    `${ind}    </object>`].join('\n'), largura, 0, ind + '  ', 1, 3));
  return [`${ind}<object class="GtkGrid" id="${idGrade}">`, `${ind}  <property name="visible">True</property>`,
    `${ind}  <property name="can-focus">False</property>`, `${ind}  <property name="margin-start">4</property>`,
    `${ind}  <property name="margin-end">2</property>`, `${ind}  <property name="margin-top">4</property>`,
    `${ind}  <property name="margin-bottom">4</property>`, `${ind}  <property name="row-spacing">2</property>`,
    `${ind}  <property name="column-spacing">2</property>`, ...filhos,
    `${ind}  <accessibility>`, `${ind}    <relation type="labelled-by" target="${idRotulo}"/>`, `${ind}  </accessibility>`,
    `${ind}</object>`].join('\n');
}

function rotuloComMnemonico(texto, letra) {
  if (!letra) return texto;
  const i = texto.toLowerCase().indexOf(letra.toLowerCase());
  return i < 0 ? texto : texto.slice(0, i) + '~' + texto.slice(i);
}

function aba(a, posicao, ind) {
  abaCorrente = { id: a.id, rotulo: a.rotulo, posicao };
  const grupos = (a.grupos || [{ rotulo: a.rotulo, itens: a.itens }]).map((g) => grupo(g, ind + '        ')).filter(Boolean);
  const idPag = `pagina-${a.id}`;
  // Página da aba: caixa horizontal simples. (sfxlo-PriorityMergedHBox recolhia todos os grupos num botão "»";
  // o recolhimento responsivo em janelas estreitas fica como pendência.)
  const corpo = [`${ind}<child>`, `${ind}  <object class="GtkBox" id="${idPag}">`,
    `${ind}    <property name="visible">True</property>`, `${ind}    <property name="can-focus">False</property>`,
    `${ind}    <property name="spacing">0</property>`,
    `${ind}    <child>`, `${ind}      <object class="GtkBox" id="grupos-${a.id}">`,
    `${ind}        <property name="visible">True</property>`, `${ind}        <property name="can-focus">False</property>`];
  grupos.forEach((g, k) => {
    corpo.push(`${ind}        <child>`, g, `${ind}          <packing>`, `${ind}            <property name="expand">False</property>`,
      `${ind}            <property name="fill">True</property>`, `${ind}            <property name="position">${k}</property>`,
      `${ind}          </packing>`, `${ind}        </child>`);
  });
  corpo.push(`${ind}      </object>`, `${ind}      <packing>`, `${ind}        <property name="expand">False</property>`,
    `${ind}        <property name="fill">True</property>`, `${ind}        <property name="position">0</property>`,
    `${ind}      </packing>`, `${ind}    </child>`, `${ind}  </object>`, `${ind}  <packing>`,
    `${ind}    <property name="position">${posicao}</property>`, `${ind}  </packing>`, `${ind}</child>`);
  // Em capturas de inspeção, a aba pedida assume o contexto padrão (abre já selecionada)
  const ehPadrao = abaAtiva ? a.id === abaAtiva : a.padrao;
  const classes = a.contexto && !(abaAtiva && a.id === abaAtiva) ? a.contexto.map((c) => `context-${c}`)
    : ehPadrao ? ['context-default', 'context-any', 'context-Text', 'context-DrawText', 'context-Table', 'context-Graphic', 'context-Draw', 'context-Frame', 'context-OLE', 'context-Form', 'context-Media'] : [];
  const rotulo = [`${ind}<child type="tab">`, `${ind}  <object class="GtkLabel" id="aba-${a.id}">`,
    `${ind}    <property name="visible">True</property>`, `${ind}    <property name="can-focus">False</property>`,
    `${ind}    <property name="label">${esc(rotuloComMnemonico(a.rotulo, a.mnemonico))}</property>`,
    `${ind}    <property name="use-underline">True</property>`];
  if (classes.length) {
    rotulo.push(`${ind}    <style>`, ...classes.map((c) => `${ind}      <class name="${c}"/>`), `${ind}    </style>`);
  }
  rotulo.push(`${ind}  </object>`, `${ind}  <packing>`, `${ind}    <property name="position">${posicao}</property>`,
    `${ind}    <property name="tab-fill">False</property>`, `${ind}  </packing>`, `${ind}</child>`);
  return corpo.join('\n') + '\n' + rotulo.join('\n');
}

const todas = [...def.abas, ...def.contextuais];
const ind = '            ';
const paginas = todas.map((a, i) => aba(a, i, ind)).join('\n');
const xml = `<?xml version="1.0" encoding="UTF-8"?>
<!-- Gerado por tools/gerar-faixa.mjs a partir de ui/abas.json. Não editar à mão.
     Faixa de opções do AY ESCREVA. SPDX-License-Identifier: MPL-2.0 -->
<interface domain="sw">
  <requires lib="gtk+" version="3.24"/>
  <object class="GtkGrid" id="NotebookBar">
    <property name="visible">True</property>
    <property name="can-focus">False</property>
    <child>
      <object class="GtkBox" id="box">
        <property name="visible">True</property>
        <property name="can-focus">False</property>
        <property name="margin-start">4</property>
        <property name="margin-end">4</property>
        <property name="margin-top">2</property>
        <property name="margin-bottom">2</property>
        <property name="orientation">vertical</property>
        <child>
          <object class="sfxlo-NotebookbarTabControl" id="ContextContainer">
            <property name="visible">True</property>
            <property name="can-focus">True</property>
            <property name="hexpand">True</property>
${paginas}
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="fill">True</property>
            <property name="position">0</property>
          </packing>
        </child>
      </object>
      <packing>
        <property name="left-attach">0</property>
        <property name="top-attach">0</property>
      </packing>
    </child>
  </object>
</interface>
`;
mkdirSync(dirname(saida), { recursive: true });
writeFileSync(saida, xml);
if (saidaMapa) {
  mkdirSync(dirname(saidaMapa), { recursive: true });
  writeFileSync(saidaMapa, JSON.stringify({ abas: todas.map((a, i) => ({ id: a.id, rotulo: a.rotulo, posicao: i, contextual: !!a.contexto })), botoes: mapa }, null, 2));
}

// Resumo para conferência
const botoes = todas.flatMap((a) => (a.grupos || [{ itens: a.itens }]).flatMap((g) => g.itens)).filter(visivel);
const pendentes = todas.flatMap((a) => (a.grupos || [{ itens: a.itens }]).flatMap((g) => g.itens)).filter((i) => !comandoDo(i));
console.log(`Faixa gerada: ${saida}`);
console.log(`Abas: ${def.abas.map((a) => a.rotulo).join(' | ')}  ·  contextuais: ${def.contextuais.map((a) => a.rotulo).join(', ')}`);
console.log(`Botões: ${botoes.length} (comandos AY: ${botoes.filter((b) => !b.comando).length}) · pendentes fora da faixa: ${pendentes.length}`);
for (const a of avisos) console.log('AVISO: ' + a);
