// Gera os ativos de identidade visual do AY ESCREVA a partir de uma única definição.
// Todo texto é convertido em contornos (via opentype.js), então os SVGs não dependem de fontes instaladas.
//
// Uso: node marca.mjs <fonte-negrito.ttf> <fonte-regular.ttf> <pasta-de-saida>
// Saída:
//   icone.svg, ayescreva.ico, icone-<n>.png      ícone do aplicativo
//   intro.png, intro-highres.png                 tela de abertura (splash)
//   about.svg                                    imagem da janela "Sobre"
//   logo.svg, logo_inverted.svg,
//   logo-sc.svg, logo-sc_inverted.svg            logotipo horizontal (Central de Início, temas claro/escuro)
//   instalador-topo.png, instalador-lateral.png  imagens do assistente de instalação
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import opentype from 'opentype.js';
import { Resvg } from '@resvg/resvg-js';

const [fonteNegrito, fonteRegular, saida = '../out/marca'] = process.argv.slice(2);
if (!fonteNegrito || !fonteRegular) {
  console.error('uso: node marca.mjs <fonte-negrito.ttf> <fonte-regular.ttf> [saida]');
  process.exit(2);
}
mkdirSync(saida, { recursive: true });

const carregar = (p) => { const b = readFileSync(p); return opentype.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength)); };
const negrito = carregar(fonteNegrito);
const regular = carregar(fonteRegular);

export const COR = {
  verde: '#11806A',
  verdeEscuro: '#0A5C4C',
  amarelo: '#F5C443',
  tinta: '#1E2A28',
  cinza: '#5B6664',
  branco: '#FFFFFF',
};

// Converte texto em <path>; retorna o elemento e a largura em unidades do SVG.
function texto(fonte, conteudo, x, linhaBase, tamanho, cor, espacamento = 0) {
  let cursor = x;
  const partes = [];
  for (const ch of conteudo) {
    const g = fonte.charToGlyph(ch);
    partes.push(g.getPath(cursor, linhaBase, tamanho).toPathData(2));
    cursor += (g.advanceWidth / fonte.unitsPerEm) * tamanho + espacamento;
  }
  return { svg: `<path fill="${cor}" d="${partes.join(' ')}"/>`, largura: cursor - x - espacamento };
}

function larguraTexto(fonte, conteudo, tamanho, espacamento = 0) {
  return texto(fonte, conteudo, 0, 0, tamanho, '#000', espacamento).largura;
}

// Ícone: quadrado arredondado verde-tinta, monograma "AY" branco e a "linha de escrita" amarela.
function iconeGrupo(x, y, lado) {
  const s = lado / 256;
  const tam = 132;
  const larg = larguraTexto(negrito, 'AY', tam, -4);
  const mono = texto(negrito, 'AY', (256 - larg) / 2, 168, tam, COR.branco, -4);
  return `<g transform="translate(${x} ${y}) scale(${s})">
  <defs><linearGradient id="fundoIcone" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="${COR.verde}"/><stop offset="1" stop-color="${COR.verdeEscuro}"/></linearGradient></defs>
  <rect x="8" y="8" width="240" height="240" rx="56" fill="url(#fundoIcone)"/>
  ${mono.svg}
  <rect x="58" y="192" width="140" height="18" rx="9" fill="${COR.amarelo}"/>
</g>`;
}

const svg = (w, h, corpo, titulo = 'AY ESCREVA') =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img"><title>${titulo}</title>${corpo}</svg>\n`;

function png(svgTexto, largura) {
  return new Resvg(svgTexto, { fitTo: { mode: 'width', value: largura }, font: { loadSystemFonts: false } }).render().asPng();
}

// --- Ícone ---------------------------------------------------------------
const iconeSvg = svg(256, 256, iconeGrupo(0, 0, 256));
writeFileSync(join(saida, 'icone.svg'), iconeSvg);
const tamanhosIco = [16, 20, 24, 32, 40, 48, 64, 128, 256];
const pngsIco = tamanhosIco.map((n) => {
  const dados = png(iconeSvg, n);
  writeFileSync(join(saida, `icone-${n}.png`), dados);
  return { n, dados };
});
// ICO com entradas PNG (suportado desde o Windows Vista).
{
  const cab = Buffer.alloc(6 + 16 * pngsIco.length);
  cab.writeUInt16LE(0, 0); cab.writeUInt16LE(1, 2); cab.writeUInt16LE(pngsIco.length, 4);
  let desloc = cab.length;
  pngsIco.forEach(({ n, dados }, i) => {
    const o = 6 + 16 * i;
    cab.writeUInt8(n >= 256 ? 0 : n, o); cab.writeUInt8(n >= 256 ? 0 : n, o + 1);
    cab.writeUInt8(0, o + 2); cab.writeUInt8(0, o + 3);
    cab.writeUInt16LE(1, o + 4); cab.writeUInt16LE(32, o + 6);
    cab.writeUInt32LE(dados.length, o + 8); cab.writeUInt32LE(desloc, o + 12);
    desloc += dados.length;
  });
  writeFileSync(join(saida, 'ayescreva.ico'), Buffer.concat([cab, ...pngsIco.map((p) => p.dados)]));
}

// --- Logotipo horizontal ---------------------------------------------------
function logotipo(corTexto, corSub) {
  const h = 72;
  const nome = texto(negrito, 'AY ESCREVA', 84, 47, 40, corTexto, 1);
  const sub = texto(regular, 'editor de textos', 86, 66, 14, corSub, 0.5);
  const w = Math.ceil(84 + Math.max(nome.largura, sub.largura) + 8);
  return svg(w, h, iconeGrupo(0, 2, 68) + nome.svg + sub.svg);
}
writeFileSync(join(saida, 'logo.svg'), logotipo(COR.tinta, COR.cinza));
writeFileSync(join(saida, 'logo_inverted.svg'), logotipo(COR.branco, '#C9D3D1'));
writeFileSync(join(saida, 'logo-sc.svg'), logotipo(COR.tinta, COR.cinza));
writeFileSync(join(saida, 'logo-sc_inverted.svg'), logotipo(COR.branco, '#C9D3D1'));

// --- Imagem da janela "Sobre" ---------------------------------------------
{
  const w = 420, h = 400;
  const nome = texto(negrito, 'AY ESCREVA', 0, 0, 44, COR.tinta, 1);
  const xNome = (w - nome.largura) / 2;
  const corpo = `<rect width="${w}" height="${h}" fill="none"/>` + iconeGrupo((w - 220) / 2, 20, 220) +
    texto(negrito, 'AY ESCREVA', xNome, 310, 44, COR.tinta, 1).svg +
    texto(regular, 'Editor de textos livre e gratuito', (w - larguraTexto(regular, 'Editor de textos livre e gratuito', 18)) / 2, 345, 18, COR.cinza).svg;
  writeFileSync(join(saida, 'about.svg'), svg(w, h, corpo));
}

// --- Tela de abertura (splash) ---------------------------------------------
// Geometria casada com soffice.ini: ProgressPosition=176,150 ProgressSize=440,6 (em intro.png 644x199).
export const SPLASH = { w: 644, h: 199, barraX: 176, barraY: 150, barraW: 440, barraH: 6 };
function splash(escala) {
  const { w, h } = SPLASH;
  const corpo = `<rect width="${w}" height="${h}" fill="#FFFFFF"/>` +
    `<rect width="${w}" height="6" fill="${COR.verde}"/>` +
    iconeGrupo(28, 34, 128) +
    texto(negrito, 'AY ESCREVA', 176, 92, 48, COR.tinta, 1.5).svg +
    texto(regular, 'Editor de textos livre e gratuito', 178, 122, 18, COR.cinza).svg;
  return png(svg(w, h, corpo), Math.round(w * escala));
}
writeFileSync(join(saida, 'intro.png'), splash(1));
writeFileSync(join(saida, 'intro-highres.png'), splash(2));

// BMP 24 bits (formato aceito por todas as versões do Inno Setup), fundo branco sob transparências.
function bmp(svgTexto, largura) {
  const r = new Resvg(svgTexto, { fitTo: { mode: 'width', value: largura }, font: { loadSystemFonts: false } }).render();
  const { width: w, height: h, pixels } = r;
  const linha = Math.ceil((w * 3) / 4) * 4;
  const buf = Buffer.alloc(54 + linha * h);
  buf.write('BM', 0); buf.writeUInt32LE(buf.length, 2); buf.writeUInt32LE(54, 10);
  buf.writeUInt32LE(40, 14); buf.writeInt32LE(w, 18); buf.writeInt32LE(h, 22);
  buf.writeUInt16LE(1, 26); buf.writeUInt16LE(24, 28); buf.writeUInt32LE(linha * h, 34);
  buf.writeInt32LE(3780, 38); buf.writeInt32LE(3780, 42);
  for (let y = 0; y < h; y++) {
    const o = 54 + (h - 1 - y) * linha;
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4; const a = pixels[i + 3] / 255;
      const mix = (c) => Math.round(c * a + 255 * (1 - a));
      buf[o + x * 3] = mix(pixels[i + 2]); buf[o + x * 3 + 1] = mix(pixels[i + 1]); buf[o + x * 3 + 2] = mix(pixels[i]);
    }
  }
  return buf;
}

// --- Imagens do instalador (Inno Setup: WizardSmallImageFile 55x55 / WizardImageFile 164x314) ----
writeFileSync(join(saida, 'instalador-topo.png'), png(svg(256, 256, iconeGrupo(0, 0, 256)), 110));
writeFileSync(join(saida, 'instalador-topo.bmp'), bmp(svg(256, 256, iconeGrupo(0, 0, 256)), 55));
writeFileSync(join(saida, 'instalador-topo-2x.bmp'), bmp(svg(256, 256, iconeGrupo(0, 0, 256)), 110));
{
  const w = 164, h = 314;
  const corpo = `<defs><linearGradient id="lat" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${COR.verde}"/><stop offset="1" stop-color="${COR.verdeEscuro}"/></linearGradient></defs>` +
    `<rect width="${w}" height="${h}" fill="url(#lat)"/>` +
    `<g transform="translate(22 40) scale(0.47)"><rect x="0" y="0" width="256" height="256" rx="56" fill="#FFFFFF" fill-opacity="0.12"/></g>` +
    texto(negrito, 'AY', 42, 128, 72, COR.branco, -2).svg +
    `<rect x="44" y="146" width="76" height="10" rx="5" fill="${COR.amarelo}"/>` +
    texto(negrito, 'ESCREVA', (w - larguraTexto(negrito, 'ESCREVA', 22, 1)) / 2, 200, 22, COR.branco, 1).svg;
  writeFileSync(join(saida, 'instalador-lateral.png'), png(svg(w, h, corpo), w * 2));
  writeFileSync(join(saida, 'instalador-lateral.bmp'), bmp(svg(w, h, corpo), w));
  writeFileSync(join(saida, 'instalador-lateral-2x.bmp'), bmp(svg(w, h, corpo), w * 2));
}

console.log(`Ativos de marca gerados em ${saida}`);
