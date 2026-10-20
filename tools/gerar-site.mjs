// Gera o site oficial do AY ESCREVA (out/site) a partir de site/, ui/abas.json, dos resultados dos testes
// e do instalador real. Falha se faltar arquivo de versão marcada como disponível, se sobrar marcador {{...}}
// ou se algum link interno estiver quebrado.
//
// Uso: node gerar-site.mjs [--modo local|github] [--saida ../out/site] [--repositorio dono/nome]
//   local  = prévia: o instalador é copiado para downloads/<versão>/ dentro do site
//   github = publicação: links para os arquivos da versão no GitHub Releases (config.json: repositorio)
// SPDX-License-Identifier: MPL-2.0
import { readFileSync, writeFileSync, mkdirSync, existsSync, copyFileSync, readdirSync, rmSync, statSync, createReadStream } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { createCanvas, loadImage } from '@napi-rs/canvas';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = resolve(AQUI, '..');
const arg = (n, p) => { const i = process.argv.indexOf(n); return i > 0 ? process.argv[i + 1] : p; };
// JSON gravado pelo PowerShell 5.1 vem com BOM
const lerJson = (arquivo) => JSON.parse(readFileSync(arquivo, 'utf8').replace(/^﻿/, ''));
const config = lerJson(join(RAIZ, 'site/config.json'));
// --repositorio dono/nome substitui o de config.json (usado por scripts/publicar-site.ps1)
if (arg('--repositorio')) {
  config.repositorio = arg('--repositorio');
  const [dono, nome] = config.repositorio.split('/');
  config.urlProjeto = `https://github.com/${config.repositorio}`;
  config.urlSite = `https://${dono.toLowerCase()}.github.io/${nome}/`;
}
const modo = arg('--modo', config.modo);
const SAIDA = resolve(arg('--saida', join(RAIZ, 'out/site')));
const versoes = lerJson(resolve(arg('--versoes', join(RAIZ, 'site/versoes.json'))));
const abas = lerJson(join(RAIZ, 'ui/abas.json'));
const resultadoFaixa = existsSync(join(RAIZ, 'tests/output/interface/faixa-resultado.json'))
  ? lerJson(join(RAIZ, 'tests/output/interface/faixa-resultado.json')) : null;

if (modo === 'github' && !config.repositorio) throw new Error('modo github exige "repositorio" (dono/nome) em site/config.json');

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
const dataLonga = (iso) => { const [a, m, d] = iso.split('-').map(Number); return `${d} de ${MESES[m - 1]} de ${a}`; };
const mb = (b) => `${(b / 1024 / 1024).toFixed(0)} MB`;
async function sha256(arquivo) {
  return new Promise((ok, erro) => {
    const h = createHash('sha256');
    createReadStream(arquivo).on('data', (d) => h.update(d)).on('end', () => ok(h.digest('hex'))).on('error', erro);
  });
}

rmSync(SAIDA, { recursive: true, force: true });
mkdirSync(join(SAIDA, 'assets/img/abas'), { recursive: true });
mkdirSync(join(SAIDA, 'assets/fontes'), { recursive: true });

// ---- Arquivos estáticos e fontes (servidas pelo próprio site) ----
for (const f of ['estilo.css', 'site.js']) copyFileSync(join(RAIZ, 'site/assets', f), join(SAIDA, 'assets', f));
const fontes = join(RAIZ, 'dist/AY ESCREVA/share/fonts/truetype');
for (const f of ['Rubik-Bold.ttf', 'Rubik-Regular.ttf']) copyFileSync(join(fontes, f), join(SAIDA, 'assets/fontes', f));
// A OFL exige que o aviso de copyright e a licença acompanhem a fonte redistribuída
copyFileSync(join(RAIZ, 'site/assets/fontes/OFL.txt'), join(SAIDA, 'assets/fontes/OFL.txt'));
const marca = join(RAIZ, 'out/marca');
copyFileSync(join(marca, 'icone.svg'), join(SAIDA, 'assets/img/icone.svg'));
copyFileSync(join(marca, 'icone-32.png'), join(SAIDA, 'assets/img/icone-32.png'));
copyFileSync(join(marca, 'icone-256.png'), join(SAIDA, 'assets/img/icone-256.png'));

// ---- Imagens reais do aplicativo ----
async function webp(origem, destino, largura, recorte = null) {
  const img = await loadImage(origem);
  const [sx, sy, sw, sh] = recorte || [0, 0, img.width, img.height];
  const altura = Math.round((sh * largura) / sw);
  const c = createCanvas(largura, altura);
  c.getContext('2d').drawImage(img, sx, sy, sw, sh, 0, 0, largura, altura);
  writeFileSync(destino, await c.encode('webp', 86));
  return { largura, altura };
}
const capturas = join(RAIZ, 'tests/output/interface');
await webp(join(capturas, 'abas/02-inicio.png'), join(SAIDA, 'assets/img/tela-inicio.webp'), 1200);
await webp(join(capturas, 'extensao-1.png'), join(SAIDA, 'assets/img/tela-revisao.webp'), 1200);
const imgsAbas = {};
for (const f of readdirSync(join(capturas, 'abas')).filter((f) => f.endsWith('.png'))) {
  const id = f.replace(/^\d+-/, '').replace('.png', '');
  await webp(join(capturas, 'abas', f), join(SAIDA, `assets/img/abas/${id}.webp`), 1200, [0, 30, 1600, 150]);
  imgsAbas[id] = `assets/img/abas/${id}.webp`;
}

// ---- Downloads ----
const atual = versoes.versoes.find((v) => v.versao === versoes.atual);
const arqs = {};
const linhasSums = [];
for (const a of atual.arquivos) {
  const origem = join(RAIZ, 'out/instalador', a.arquivo);
  if (!existsSync(origem)) throw new Error(`instalador da versão ${atual.versao} não encontrado: ${origem}`);
  const tamanho = statSync(origem).size;
  const hash = await sha256(origem);
  let url, urlSums;
  if (modo === 'local') {
    const pasta = join(SAIDA, 'downloads', atual.versao);
    mkdirSync(pasta, { recursive: true });
    copyFileSync(origem, join(pasta, a.arquivo));
    url = `downloads/${atual.versao}/${a.arquivo}`;
    urlSums = `downloads/${atual.versao}/SHA256SUMS.txt`;
  } else {
    url = `https://github.com/${config.repositorio}/releases/download/v${atual.versao}/${a.arquivo}`;
    urlSums = `https://github.com/${config.repositorio}/releases/download/v${atual.versao}/SHA256SUMS.txt`;
  }
  arqs[a.plataforma] = { ...a, tamanho, hash, url, urlSums };
  linhasSums.push(`${hash}  ${a.arquivo}`);
}
if (modo === 'local') writeFileSync(join(SAIDA, 'downloads', atual.versao, 'SHA256SUMS.txt'), linhasSums.join('\n') + '\n');
mkdirSync(join(RAIZ, 'out/publicacao', `v${atual.versao}`), { recursive: true });
writeFileSync(join(RAIZ, 'out/publicacao', `v${atual.versao}`, 'SHA256SUMS.txt'), linhasSums.join('\n') + '\n');
// Notas da versão para o GitHub Releases: novidades, SHA-256, instalação, limitações, licenças e código-fonte
function limitacoesMd() {
  const html = readFileSync(join(RAIZ, 'extensao/ayescreva/ajuda/limitacoes.html'), 'utf8');
  const main = (html.match(/<main>([\s\S]*?)<\/main>/) || [, ''])[1].replace(/<p><a href="guia.html">Voltar ao guia<\/a><\/p>/, '');
  const texto = (s) => s.replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/\s+/g, ' ').trim();
  const linhas = [];
  for (const m of main.matchAll(/<h2>([\s\S]*?)<\/h2>|<li>([\s\S]*?)<\/li>|<p>([\s\S]*?)<\/p>/g)) {
    if (m[1]) linhas.push('', `#### ${texto(m[1])}`, '');
    else linhas.push(m[2] ? `- ${texto(m[2])}` : texto(m[3]));
  }
  return linhas;
}
const urlProjetoNotas = config.urlProjeto || `https://github.com/${config.repositorio || '<dono>/<nome>'}`;
writeFileSync(join(RAIZ, 'out/publicacao', `v${atual.versao}`, 'NOTAS.md'), [
  `**AY ESCREVA ${atual.versao} — ${atual.canal.toLowerCase()}, validada somente no Windows 11 de 64 bits (x64).** ` +
  'Windows 10, Windows em ARM, macOS e Linux ainda estão em desenvolvimento e não têm instalador.', '',
  config.urlSite ? `Site: ${config.urlSite}` : '', '',
  '### Novidades', '',
  ...atual.notas.map((n) => `- ${n}`), '',
  '### Conferir o arquivo (SHA-256)', '',
  '**O instalador ainda não tem assinatura digital.** O Windows pode mostrar "O Windows protegeu o computador" ' +
  '(SmartScreen). Antes de executar, confira o SHA-256 (também no arquivo `SHA256SUMS.txt` desta versão):', '',
  ...linhasSums.map((l) => `    ${l}`), '',
  'No PowerShell, na pasta Downloads:', '',
  ...Object.values(arqs).map((a) => `    Get-FileHash .\\${a.arquivo} -Algorithm SHA256`), '',
  'O resultado deve ser igual ao valor acima (maiúsculas e minúsculas não importam).', '',
  '### Instalar e abrir', '',
  `1. Baixe \`${win0().arquivo}\` (${mb(win0().tamanho)}) e confira o SHA-256.`,
  '2. Abra o arquivo. Se aparecer "O Windows protegeu o computador", clique em **Mais informações** e depois em **Executar assim mesmo**.',
  '3. Siga o instalador. Ele instala só para o seu usuário, sem pedir senha de administrador (cerca de 850 MB livres).',
  '4. Abra pelo menu Iniciar: **AY ESCREVA**. Não precisa de internet nem de conta.',
  '5. Para desinstalar: Configurações › Aplicativos › AY ESCREVA › Desinstalar (seus documentos e o perfil `%APPDATA%\\AYEscreva` são mantidos).', '',
  '### Limitações conhecidas', '',
  ...limitacoesMd(), '',
  '### Licenças e código-fonte', '',
  `- Código do AY ESCREVA: Mozilla Public License 2.0 — ${urlProjetoNotas} (versão marcada \`v${atual.versao}\`).`,
  '- Inclui, sem modificação de código, os binários oficiais do LibreOffice 26.8.1 (The Document Foundation), sob MPL 2.0 com partes ' +
  'em LGPL v3+, Apache 2.0 e outras licenças livres. Código-fonte correspondente: https://download.documentfoundation.org/libreoffice/src/26.8.1/',
  '- Os textos completos das licenças e os avisos de terceiros (LICENSE.html, license.txt, NOTICE, CREDITS.fodt) são instalados com o aplicativo.',
  '- "LibreOffice" é marca da The Document Foundation. O AY ESCREVA é um projeto independente, não endossado pela The Document Foundation.',
  '- O software é fornecido "no estado em que se encontra", sem garantias. Esta é uma versão de testes.', '',
].join('\n'));
function win0() { return arqs['windows11-x64']; }

const win = arqs['windows11-x64'];
const plataformasHtml = versoes.plataformas.map((p) => {
  const disp = p.status === 'disponivel' && arqs[p.id];
  const estado = disp ? '<span class="estado estado-disponivel">Disponível</span>' : '<span class="estado estado-dev">Em desenvolvimento</span>';
  const acao = disp
    ? `<a class="botao botao-pequeno" href="${esc(arqs[p.id].url)}" download>Baixar (${mb(arqs[p.id].tamanho)})</a>`
    : '<span class="botao botao-pequeno" aria-disabled="true">Ainda não disponível</span>';
  const detalhe = disp ? `Versão ${esc(atual.versao)} · ${esc(arqs[p.id].arquivo)} · SHA-256 <code>${arqs[p.id].hash.slice(0, 16)}…</code>` : esc(p.nota || '');
  return `      <div class="plataforma" data-plataforma="${esc(p.id)}">
        <div><h3>${esc(p.nome)} <span class="miudo">${esc(p.detalhe)}</span>${estado}</h3><p class="miudo">${detalhe}</p></div>
        <div>${acao}</div>
      </div>`;
}).join('\n');

// ---- Recursos (a partir da faixa e dos testes pela interface) ----
const funcoesTeste = resultadoFaixa?.funcoes || {};
function recursosHtml() {
  const blocos = [];
  for (const a of [...abas.abas, ...abas.contextuais]) {
    const itens = (a.grupos || [{ itens: a.itens }]).flatMap((g) => g.itens);
    const disponiveis = itens.filter((i) => (i.comando || i.comandoAY));
    const pendentes = itens.filter((i) => !(i.comando || i.comandoAY));
    const li = disponiveis.map((i) => {
      const t = funcoesTeste[`${a.rotulo} › ${i.funcao}`];
      const selo = t?.validado ? ' <span class="testado" title="Efeito conferido em teste automatizado pela interface">testado</span>' : '';
      const via = i.botao === false ? ` <span class="miudo">(${esc(i.via)})</span>` : '';
      return `<li>${esc(i.funcao)}${via}${selo}</li>`;
    }).join('');
    const pend = pendentes.length ? `<p class="pendente"><strong>Em desenvolvimento:</strong> ${pendentes.map((i) => esc(i.funcao)).join(', ')}.</p>` : '';
    const img = imgsAbas[a.id] ? `<img class="faixa-img" src="${imgsAbas[a.id]}" width="1200" height="113" alt="Faixa de opções do AY ESCREVA com a aba ${esc(a.rotulo)} aberta.">` : '';
    const ctx = a.contexto ? ' <span class="miudo">(aba contextual)</span>' : '';
    blocos.push(`<section class="recursos-aba" id="aba-${esc(a.id)}"><h2>${esc(a.rotulo)}${ctx}</h2>${img}<ul>${li}</ul>${pend}</section>`);
  }
  const total = Object.values(funcoesTeste).filter((f) => f.validado).length;
  const nota = resultadoFaixa
    ? `<p class="miudo">“testado” = efeito conferido em teste automatizado que clica no botão da faixa (${total} funções). As demais estão na faixa e ligadas a comandos do motor; o efeito delas ainda não tem teste automatizado próprio.</p>`
    : '';
  return `<section class="secao"><div class="largura"><h1>Recursos</h1><p class="chamada">Ferramentas disponíveis na versão ${esc(atual.versao)}, aba por aba, na mesma ordem da faixa de opções. Itens em desenvolvimento estão indicados.</p>${nota}${blocos.join('\n')}</div></section>`;
}

// ---- Versões e limitações ----
function versoesHtml() {
  const limHtml = readFileSync(join(RAIZ, 'extensao/ayescreva/ajuda/limitacoes.html'), 'utf8');
  const lim = (limHtml.match(/<main>([\s\S]*?)<\/main>/) || [, ''])[1]
    .replace(/<p><a href="guia.html">Voltar ao guia<\/a><\/p>/, '').replace(/<h2>/g, '<h3>').replace(/<\/h2>/g, '</h3>');
  const lista = versoes.versoes.map((v) => {
    const d = v.publicada && v.versao === atual.versao
      ? Object.values(arqs).map((a) => `<li><a href="${esc(a.url)}">${esc(a.arquivo)}</a> · ${mb(a.tamanho)} · SHA-256 <code>${a.hash}</code> · ${a.assinado ? 'assinado' : 'sem assinatura digital'}</li>`).join('')
      : '';
    return `<article class="cartao" style="margin-bottom:16px"><h2>Versão ${esc(v.versao)} <span class="miudo">· ${esc(v.canal)} · ${dataLonga(v.data)}</span></h2><ul>${v.notas.map((n) => `<li>${esc(n)}</li>`).join('')}</ul>${d ? `<h3>Arquivos</h3><ul>${d}</ul>` : '<p class="miudo">Sem arquivos publicados.</p>'}</article>`;
  }).join('\n');
  return `<section class="secao"><div class="largura"><h1>Versões</h1><p class="chamada">Histórico de versões e limitações conhecidas.</p>${lista}</div></section>
<section class="secao secao-suave" id="limitacoes"><div class="largura"><h2>Limitações conhecidas da versão ${esc(atual.versao)}</h2>${lim}</div></section>`;
}

// ---- Montagem das páginas ----
const modelo = readFileSync(join(RAIZ, 'site/modelo.html'), 'utf8');
const tokens = {
  VERSAO: atual.versao, CANAL: atual.canal.toLowerCase(), DATA_LONGA: dataLonga(atual.data),
  TAMANHO: mb(win.tamanho), ARQUIVO_WIN11: win.arquivo, URL_WIN11: win.url, SHA256_WIN11: win.hash,
  URL_SHA256SUMS: win.urlSums,
  ASSINATURA_WIN11: win.assinado ? 'Assinado' : 'Ainda não assinado (veja o aviso abaixo)',
  REQUISITOS_WIN11: versoes.plataformas.find((p) => p.id === 'windows11-x64').requisitos.map((r) => `<li>${esc(r)}</li>`).join(''),
  TABELA_PLATAFORMAS: plataformasHtml,
  LINK_PROJETO: config.urlProjeto ? `<li><a href="${esc(config.urlProjeto)}">Código-fonte e relatos de problemas</a></li>` : '',
  CANAL_CONTATO: config.urlProjeto ? `Abra um relato na <a href="${esc(config.urlProjeto)}/issues">página do projeto</a>.` : 'O canal público de relatos será publicado junto com o site.',
  FONTE_PROJETO: config.urlProjeto ? `<a href="${esc(config.urlProjeto)}">${esc(config.urlProjeto.replace('https://', ''))}</a>` : 'Será publicado junto com o site',
  NOTA_HTTPS: modo === 'github' ? 'Os arquivos são servidos por HTTPS pelo GitHub Releases.' : 'Prévia local: na publicação, os arquivos são servidos por HTTPS.',
  NOTA_HOSPEDAGEM: modo === 'github'
    ? 'O site e os instaladores são hospedados pelo GitHub (Pages e Releases). Como qualquer servidor, o GitHub recebe dados técnicos das conexões (como endereço IP) segundo a política de privacidade dele; o projeto AY ESCREVA não recebe esses dados.'
    : 'Esta é uma prévia local do site.',
};
const paginas = {
  'index.html': readFileSync(join(RAIZ, 'site/paginas/index.html'), 'utf8'),
  'baixar.html': readFileSync(join(RAIZ, 'site/paginas/baixar.html'), 'utf8'),
  'instalar.html': readFileSync(join(RAIZ, 'site/paginas/instalar.html'), 'utf8'),
  'ajuda.html': readFileSync(join(RAIZ, 'site/paginas/ajuda.html'), 'utf8'),
  'privacidade.html': readFileSync(join(RAIZ, 'site/paginas/privacidade.html'), 'utf8'),
  'licencas.html': readFileSync(join(RAIZ, 'site/paginas/licencas.html'), 'utf8'),
  'recursos.html': `<!-- titulo: Recursos do AY ESCREVA | descricao: Ferramentas disponíveis no AY ESCREVA, aba por aba, com indicação do que foi testado e do que está em desenvolvimento. -->\n${recursosHtml()}`,
  'versoes.html': `<!-- titulo: Versões e limitações — AY ESCREVA | descricao: Histórico de versões do AY ESCREVA, arquivos com SHA-256 e limitações conhecidas. -->\n${versoesHtml()}`,
  '404.html': '<!-- titulo: Página não encontrada — AY ESCREVA | descricao: Página não encontrada. -->\n<section class="secao"><div class="largura"><h1>Página não encontrada</h1><p><a href="index.html">Voltar ao início</a> ou <a href="baixar.html">baixar o AY ESCREVA</a>.</p></div></section>',
};
const erros = [];
for (const [nome, fonte] of Object.entries(paginas)) {
  const meta = /<!--\s*titulo:\s*(.*?)\s*\|\s*descricao:\s*(.*?)\s*-->/.exec(fonte);
  let corpo = fonte.replace(/<!--[\s\S]*?-->\n?/, '');
  let html = modelo.replace('{{CONTEUDO}}', corpo).replace(/{{TITULO}}/g, esc(meta[1])).replace(/{{DESCRICAO}}/g, esc(meta[2]));
  for (const p of ['recursos', 'instalar', 'versoes', 'ajuda', 'baixar']) html = html.replace(`{{ATIVO_${p}}}`, nome === `${p}.html` ? ' aria-current="page"' : '');
  html = html.replace(/{{([A-Z0-9_]+)}}/g, (m, k) => (k in tokens ? tokens[k] : m));
  const sobra = html.match(/{{[A-Z0-9_]+}}/g);
  if (sobra) erros.push(`${nome}: marcadores sem valor ${[...new Set(sobra)].join(', ')}`);
  writeFileSync(join(SAIDA, nome), html);
}
writeFileSync(join(SAIDA, 'robots.txt'), 'User-agent: *\nAllow: /\n');

// ---- Verificação de links internos ----
for (const nome of Object.keys(paginas)) {
  const html = readFileSync(join(SAIDA, nome), 'utf8');
  for (const [, url] of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
    if (/^(https?:|mailto:|#)/.test(url)) continue;
    const caminho = url.split('#')[0].split('?')[0];
    if (caminho && !existsSync(join(SAIDA, caminho))) erros.push(`${nome}: link quebrado ${url}`);
  }
}
if (erros.length) { console.error(erros.join('\n')); process.exit(1); }
console.log(`Site gerado em ${SAIDA} (modo ${modo}) · versão ${atual.versao} · ${win.arquivo} ${mb(win.tamanho)} · SHA-256 ${win.hash}`);
