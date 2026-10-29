// Confere um arquivo de chave privada de atualizações (o original ou uma cópia de segurança) sem mostrar o conteúdo:
// deriva a chave pública e compara com a que vai dentro do AY (extensao/ayescreva/pythonpath/ay_atualizacao.py).
// Também assina e verifica uma mensagem de teste, para confirmar que o arquivo está íntegro.
// Uso: node tools/conferir-chave.mjs [caminho-da-chave.pem]
// SPDX-License-Identifier: MPL-2.0
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const chave = process.argv[2] || path.join(os.homedir(), '.ay-escreva', 'chave-atualizacoes-ed25519.pem');
const codigo = fs.readFileSync(path.join(raiz, 'extensao', 'ayescreva', 'pythonpath', 'ay_atualizacao.py'), 'utf8');
const esperada = (codigo.match(/CHAVE_PUBLICA = bytes\.fromhex\('([0-9a-f]{64})'\)/) || [])[1];
if (!esperada) throw new Error('chave pública não encontrada em ay_atualizacao.py');

let privada;
try {
  privada = crypto.createPrivateKey(fs.readFileSync(chave));
} catch (e) {
  console.error(`não foi possível ler a chave em ${chave}: ${e.code || e.message}`);
  process.exit(2);
}
if (privada.asymmetricKeyType !== 'ed25519') {
  console.error(`o arquivo não é uma chave Ed25519 (tipo ${privada.asymmetricKeyType})`);
  process.exit(2);
}
const publica = crypto.createPublicKey(privada).export({ format: 'der', type: 'spki' }).subarray(-32).toString('hex');
const teste = Buffer.from('conferência da chave do AY ESCREVA');
const integra = crypto.verify(null, teste, crypto.createPublicKey(privada), crypto.sign(null, teste, privada));
console.log(`chave pública derivada: ${publica}`);
console.log(`chave pública do AY:    ${esperada}`);
console.log(integra && publica === esperada ? 'CONFERE: este arquivo assina atualizações que o AY aceita.'
  : 'NÃO CONFERE: este arquivo não serve para assinar atualizações desta versão do AY.');
process.exit(integra && publica === esperada ? 0 : 1);
