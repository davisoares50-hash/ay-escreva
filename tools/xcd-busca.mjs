// Busca propriedades de configuração nos arquivos .xcd do LibreOffice e imprime o caminho completo.
// Uso: node xcd-busca.mjs <arquivo.xcd> <nome1> [nome2 ...]
// Ex.: node xcd-busca.mjs main.xcd DisableMacrosExecution MacroSecurityLevel
import { readFileSync } from 'node:fs';

const [arquivo, ...nomes] = process.argv.slice(2);
if (!arquivo || nomes.length === 0) {
  console.error('uso: node xcd-busca.mjs <arquivo.xcd> <nome> [...]');
  process.exit(2);
}
const xml = readFileSync(arquivo, 'utf8');
const alvo = new Set(nomes);
const pilha = [];
const re = /<(\/?)(oor:component-schema|oor:component-data|component|templates|group|set|node|prop|node-ref)\b([^>]*?)(\/?)>/g;
let m;
while ((m = re.exec(xml))) {
  const [, fecha, tag, attrs, auto] = m;
  if (fecha) { pilha.pop(); continue; }
  const nome = /oor:name="([^"]*)"/.exec(attrs)?.[1] ?? '';
  const pacote = /oor:package="([^"]*)"/.exec(attrs)?.[1];
  const rotulo = pacote ? `${pacote}.${nome}` : (tag === 'templates' ? '[templates]' : tag === 'component' ? '' : nome);
  if (tag === 'prop' && alvo.has(nome)) {
    const tipo = /oor:type="([^"]*)"/.exec(attrs)?.[1] ?? '';
    const tipoComp = pilha.some(p => p.tag === 'oor:component-schema') ? 'schema' : 'dados';
    const trecho = xml.slice(m.index, m.index + 220).replace(/\s+/g, ' ');
    console.log(`[${tipoComp}] /${[...pilha.map(p => p.rotulo).filter(Boolean), nome].join('/')} ${tipo}\n    ${trecho}`);
  }
  if (!auto) pilha.push({ tag, rotulo });
}
