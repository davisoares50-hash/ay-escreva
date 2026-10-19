// Monta uma prancha com a faixa de opções recortada de cada captura (inspeção visual rápida).
// Uso: node prancha-faixa.mjs <pasta-capturas> <saida.png> [alturaRecorte=180] [larguraRecorte=1600]
import { readdirSync } from 'node:fs';
import { join } from 'node:path';
import { writeFileSync } from 'node:fs';
import { createCanvas, loadImage } from '@napi-rs/canvas';

const [pasta, saida, altTxt = '180', largTxt = '1600'] = process.argv.slice(2);
const alt = Number(altTxt), larg = Number(largTxt);
const arquivos = readdirSync(pasta).filter((f) => f.endsWith('.png')).sort();
const rotulo = 22;
const c = createCanvas(larg, arquivos.length * (alt + rotulo));
const x = c.getContext('2d');
x.fillStyle = '#ffffff'; x.fillRect(0, 0, c.width, c.height);
let y = 0;
for (const f of arquivos) {
  const img = await loadImage(join(pasta, f));
  x.fillStyle = '#0A5C4C'; x.fillRect(0, y, larg, rotulo);
  x.fillStyle = '#ffffff'; x.font = 'bold 14px sans-serif'; x.fillText(f.replace('.png', ''), 8, y + 16);
  x.drawImage(img, 0, 30, larg, alt, 0, y + rotulo, larg, alt);
  y += alt + rotulo;
}
writeFileSync(saida, c.toBuffer('image/png'));
console.log(`prancha: ${saida} (${arquivos.length} abas)`);
