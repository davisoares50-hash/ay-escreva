// Comparação visual de dois PDFs, página a página.
// Renderiza cada página (pdf.js + @napi-rs/canvas), compara com pixelmatch e grava:
//   <saida>/<rotulo>.json            resumo (páginas, % de pixels diferentes por página)
//   <saida>/<rotulo>-pNN.png         imagem lado a lado (A | B | diferença) das páginas que diferem
// Uso: node comparar-pdf.mjs <a.pdf> <b.pdf> <pasta-saida> <rotulo> [dpi=60] [limiar%=0.5]
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { createRequire } from 'node:module';
import { createCanvas } from '@napi-rs/canvas';
import pixelmatch from 'pixelmatch';
import { PNG } from 'pngjs';
import * as pdfjs from 'pdfjs-dist/legacy/build/pdf.mjs';

const require = createRequire(import.meta.url);
const fontes = join(dirname(require.resolve('pdfjs-dist/package.json')), 'standard_fonts') + '/';

const [arqA, arqB, saida, rotulo, dpiTxt = '60', limiarTxt = '0.5'] = process.argv.slice(2);
if (!arqA || !arqB || !saida || !rotulo) {
  console.error('uso: node comparar-pdf.mjs <a.pdf> <b.pdf> <saida> <rotulo> [dpi] [limiar%]');
  process.exit(2);
}
const escala = Number(dpiTxt) / 72;
const limiar = Number(limiarTxt);
mkdirSync(saida, { recursive: true });

async function abrir(arq) {
  const data = new Uint8Array(readFileSync(arq));
  return pdfjs.getDocument({ data, standardFontDataUrl: fontes, verbosity: 0, isEvalSupported: false }).promise;
}

async function renderizar(pdf, n) {
  const pagina = await pdf.getPage(n);
  const vp = pagina.getViewport({ scale: escala });
  const canvas = createCanvas(Math.ceil(vp.width), Math.ceil(vp.height));
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  await pagina.render({ canvasContext: ctx, viewport: vp }).promise;
  return { canvas, w: canvas.width, h: canvas.height, data: ctx.getImageData(0, 0, canvas.width, canvas.height).data };
}

const a = await abrir(arqA);
const b = await abrir(arqB);
const resumo = { a: arqA, b: arqB, dpi: Number(dpiTxt), paginasA: a.numPages, paginasB: b.numPages, paginas: [] };
const n = Math.min(a.numPages, b.numPages);
for (let i = 1; i <= n; i++) {
  const ra = await renderizar(a, i);
  const rb = await renderizar(b, i);
  const w = Math.max(ra.w, rb.w), h = Math.max(ra.h, rb.h);
  // Normaliza para o mesmo tamanho (fundo branco) antes de comparar
  const norm = (r) => {
    const c = createCanvas(w, h); const x = c.getContext('2d');
    x.fillStyle = '#ffffff'; x.fillRect(0, 0, w, h); x.drawImage(r.canvas, 0, 0);
    return { c, d: x.getImageData(0, 0, w, h).data };
  };
  const na = norm(ra), nb = norm(rb);
  const diff = new PNG({ width: w, height: h });
  const dif = pixelmatch(na.d, nb.d, diff.data, w, h, { threshold: 0.1 });
  const pct = (100 * dif) / (w * h);
  const item = { pagina: i, tamanhoA: [ra.w, ra.h], tamanhoB: [rb.w, rb.h], pixelsDiferentes: dif, percentual: Number(pct.toFixed(3)) };
  if (pct > limiar || ra.w !== rb.w || ra.h !== rb.h) {
    const lado = createCanvas(w * 3 + 20, h); const x = lado.getContext('2d');
    x.fillStyle = '#888'; x.fillRect(0, 0, lado.width, h);
    x.drawImage(na.c, 0, 0); x.drawImage(nb.c, w + 10, 0);
    const dc = createCanvas(w, h); const dx = dc.getContext('2d');
    const img = dx.createImageData(w, h); img.data.set(diff.data); dx.putImageData(img, 0, 0);
    x.drawImage(dc, 2 * w + 20, 0);
    const nome = `${rotulo}-p${String(i).padStart(2, '0')}.png`;
    writeFileSync(join(saida, nome), lado.toBuffer('image/png'));
    item.imagem = nome;
  }
  resumo.paginas.push(item);
}
resumo.maiorDiferenca = resumo.paginas.reduce((m, p) => Math.max(m, p.percentual), 0);
resumo.mediaDiferenca = Number((resumo.paginas.reduce((s, p) => s + p.percentual, 0) / Math.max(1, n)).toFixed(3));
writeFileSync(join(saida, `${rotulo}.json`), JSON.stringify(resumo, null, 2));
console.log(JSON.stringify({ rotulo, paginasA: resumo.paginasA, paginasB: resumo.paginasB, maior: resumo.maiorDiferenca, media: resumo.mediaDiferenca }));
