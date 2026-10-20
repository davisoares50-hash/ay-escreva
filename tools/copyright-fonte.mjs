// Mostra os avisos de copyright e de licença gravados numa fonte (tabela "name": IDs 0, 13 e 14).
// Uso: node copyright-fonte.mjs <fonte.ttf>
// SPDX-License-Identifier: MPL-2.0
import { readFileSync } from 'node:fs';
import opentype from 'opentype.js';

const b = readFileSync(process.argv[2]);
const f = opentype.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength));
const n = f.names;
const t = (x) => (x ? (x.en || Object.values(x)[0]) : '');
console.log(JSON.stringify({ familia: t(n.fontFamily), copyright: t(n.copyright), licenca: t(n.license), urlLicenca: t(n.licenseURL) }, null, 2));
