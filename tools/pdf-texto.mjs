// Texto de um PDF, página a página, em JSON (pdf.js): [["linha 1", "linha 2", ...], ...], linhas de cima para baixo.
// Uso: node tools/pdf-texto.mjs <arquivo.pdf>
// Usado pelos testes para conferir números de página e sumário no PDF exportado ou impresso.
import { readFileSync } from 'node:fs';
import * as pdfjs from 'pdfjs-dist/legacy/build/pdf.mjs';

const arquivo = process.argv[2];
if (!arquivo) {
  console.error('uso: node pdf-texto.mjs <arquivo.pdf>');
  process.exit(2);
}
const doc = await pdfjs.getDocument({ data: new Uint8Array(readFileSync(arquivo)), isEvalSupported: false, verbosity: 0 }).promise;
const paginas = [];
for (let i = 1; i <= doc.numPages; i++) {
  const pg = await doc.getPage(i);
  const tc = await pg.getTextContent();
  const linhas = new Map();
  for (const it of tc.items) {
    if (!it.str) continue;
    const y = Math.round(it.transform[5] / 2) * 2;          // agrupa por linha (2 pt de tolerância)
    if (!linhas.has(y)) linhas.set(y, []);
    linhas.get(y).push([it.transform[4], it.str]);
  }
  const ordenadas = [...linhas.entries()].sort((a, b) => b[0] - a[0])
    .map(([, partes]) => partes.sort((a, b) => a[0] - b[0]).map((p) => p[1]).join('').replace(/\s+/g, ' ').trim())
    .filter((l) => l);
  paginas.push(ordenadas);
}
console.log(JSON.stringify(paginas));
