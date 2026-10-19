// Servidor estático mínimo para a prévia local do site (sem dependências).
// Uso: node servir-site.mjs [pasta=../out/site] [porta=8737]
// SPDX-License-Identifier: MPL-2.0
import { createServer } from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { join, resolve, extname, normalize } from 'node:path';

const pasta = resolve(process.argv[2] || new URL('../out/site', import.meta.url).pathname.replace(/^\/(\w:)/, '$1'));
const porta = Number(process.argv[3] || 8737);
const TIPOS = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.ttf': 'font/ttf', '.txt': 'text/plain; charset=utf-8',
  '.exe': 'application/vnd.microsoft.portable-executable', '.json': 'application/json' };

createServer((req, res) => {
  let caminho = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (caminho.endsWith('/')) caminho += 'index.html';
  const arquivo = normalize(join(pasta, caminho));
  if (!arquivo.startsWith(pasta)) { res.writeHead(403).end(); return; }
  if (!existsSync(arquivo) || !statSync(arquivo).isFile()) {
    res.writeHead(404, { 'Content-Type': TIPOS['.html'] });
    createReadStream(join(pasta, '404.html')).pipe(res);
    return;
  }
  const tipo = TIPOS[extname(arquivo).toLowerCase()] || 'application/octet-stream';
  const cab = { 'Content-Type': tipo, 'Content-Length': statSync(arquivo).size, 'X-Content-Type-Options': 'nosniff' };
  if (extname(arquivo) === '.exe') cab['Content-Disposition'] = `attachment; filename="${caminho.split('/').pop()}"`;
  res.writeHead(200, cab);
  if (req.method === 'HEAD') { res.end(); return; }
  createReadStream(arquivo).pipe(res);
}).listen(porta, '127.0.0.1', () => console.log(`Prévia do site: http://127.0.0.1:${porta}/  (pasta ${pasta})`));
