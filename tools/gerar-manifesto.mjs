// Gera e assina o arquivo de versões que "Verificar atualizações" consulta (atualizacoes.json + atualizacoes.json.sig).
// Não publica nada: os dois arquivos vão para --saida; publicar = copiá-los para o site oficial (docs/ATUALIZACOES.md).
//
// Uso:
//   node tools/gerar-manifesto.mjs --canal testes --instalador out/instalador/AYEscreva-0.7.0-teste-windows11-x64.exe \
//        --notas "O que mudou…" [--chave %USERPROFILE%/.ay-escreva/chave-atualizacoes-ed25519.pem] [--saida out/atualizacoes]
//        [--prefixo https://github.com/davisoares50-hash/ay-escreva/releases/download/]
// A chave privada fica fora do repositório. Os dados de outros canais já presentes em --saida são mantidos.
// SPDX-License-Identifier: MPL-2.0
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, arr) => (a.startsWith('--') ? [...acc, [a.slice(2), arr[i + 1]]] : acc), []));
const canal = args.canal || 'testes';
if (!['testes', 'estavel'].includes(canal)) throw new Error('canal deve ser testes ou estavel');
const instalador = args.instalador;
if (!instalador || !fs.existsSync(instalador)) throw new Error('informe --instalador com o .exe gerado por scripts/instalador.ps1');
const arquivo = path.basename(instalador);
const m = arquivo.match(/^AYEscreva-(\d+\.\d+\.\d+)-[\w.-]+\.exe$/);
if (!m) throw new Error(`nome de instalador inesperado: ${arquivo}`);
const versao = m[1];
const chave = args.chave || path.join(os.homedir(), '.ay-escreva', 'chave-atualizacoes-ed25519.pem');
const saida = args.saida || 'out/atualizacoes';
const prefixo = args.prefixo || 'https://github.com/davisoares50-hash/ay-escreva/releases/download/';

const dados = fs.readFileSync(instalador);
const destino = path.join(saida, 'atualizacoes.json');
let manifesto = { formato: 1, descricao: 'Versões do AY ESCREVA para "Verificar atualizações". Assinado pela chave do projeto.', canais: {} };
if (fs.existsSync(destino)) manifesto = JSON.parse(fs.readFileSync(destino, 'utf8'));
manifesto.canais[canal] = {
  versao,
  data: new Date().toISOString().slice(0, 10),
  notas: args.notas || '',
  pagina: `https://github.com/davisoares50-hash/ay-escreva/releases/tag/v${versao}`,
  instalador: {
    arquivo,
    url: `${prefixo}v${versao}/${arquivo}`,
    tamanho: dados.length,
    sha256: crypto.createHash('sha256').update(dados).digest('hex'),
  },
};
manifesto.gerado_em = new Date().toISOString();
const corpo = Buffer.from(JSON.stringify(manifesto, null, 2) + '\n', 'utf8');
const privada = crypto.createPrivateKey(fs.readFileSync(chave));
const assinatura = crypto.sign(null, corpo, privada);
const publica = crypto.createPublicKey(privada).export({ format: 'der', type: 'spki' }).subarray(-32).toString('hex');
if (!crypto.verify(null, corpo, crypto.createPublicKey(privada), assinatura)) throw new Error('assinatura não confere');
// recusa assinar com uma chave que o AY não aceitaria (cópia errada, chave de teste)
const codigo = fs.readFileSync(new URL('../extensao/ayescreva/pythonpath/ay_atualizacao.py', import.meta.url), 'utf8');
const doAY = (codigo.match(/CHAVE_PUBLICA = bytes\.fromhex\('([0-9a-f]{64})'\)/) || [])[1];
if (publica !== doAY && !args['chave-de-teste']) throw new Error('a chave informada não corresponde à chave pública do AY (use --chave-de-teste 1 só em testes)');
fs.mkdirSync(saida, { recursive: true });
fs.writeFileSync(destino, corpo);
fs.writeFileSync(destino + '.sig', assinatura.toString('hex') + '\n');
console.log(JSON.stringify({ canal, versao, arquivo, saida: destino, chave_publica: publica, sha256: manifesto.canais[canal].instalador.sha256 }));
