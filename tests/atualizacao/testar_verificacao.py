# -*- coding: utf-8 -*-
"""Verificar atualizações (entrega E): assinatura, conferências de segurança, download e roteiro de instalação.

Usa uma chave de teste temporária (a chave real do projeto nunca é tocada) e um servidor HTTP local que faz o papel do
site e do GitHub; o código testado é o mesmo do diálogo, com o endereço, o prefixo e a chave passados como parâmetro.
Também consulta o endereço real do site oficial (hoje ainda sem arquivo de versões publicado).
Uso: "dist\\AY ESCREVA\\program\\python.exe" tests\\atualizacao\\testar_verificacao.py
SPDX-License-Identifier: MPL-2.0
"""
import hashlib
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'extensao' / 'ayescreva' / 'pythonpath'))
import ay_atualizacao as A  # noqa: E402
import ay_ed25519 as E  # noqa: E402
import ay_ia as IA  # noqa: E402

itens = []
TMP = Path(tempfile.mkdtemp(prefix='ay-atualizacao-'))
SITE = TMP / 'site'


def verificar(descricao, ok, detalhe=''):
    itens.append({'ok': bool(ok), 'verificacao': descricao, 'detalhe': str(detalhe)})
    print(f"[{'OK  ' if ok else 'FALHA'}] {descricao}{' — ' + str(detalhe) if detalhe else ''}", flush=True)


class Site(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SITE), **kw)

    def log_message(self, *a):
        pass


def ler_local(url, limite=A.LIMITE_MANIFESTO):
    """Mesmo papel de A.buscar, sem a exigência de https (o servidor de teste é http em 127.0.0.1)."""
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.read(limite + 1)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise A.SemInformacao('ainda não há informação de atualização publicada')
        raise


def gerar(chave, instalador, canal='testes', notas='Novidades de teste.', prefixo=None):
    r = subprocess.run(['node', str(RAIZ / 'tools' / 'gerar-manifesto.mjs'), '--canal', canal, '--instalador', str(instalador),
                        '--notas', notas, '--chave', str(chave), '--saida', str(SITE), '--prefixo', prefixo],
                       capture_output=True, text=True, encoding='utf-8')
    if r.returncode:
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    A.registrar = IA.registrar = lambda m: None
    SITE.mkdir(parents=True)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Site)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{srv.server_address[1]}'
    prefixo = base + '/releases/'
    try:
        # chaves de teste (Node.js gera e assina; o AY só verifica)
        node = ('const c=require("crypto"),fs=require("fs");const k=c.generateKeyPairSync("ed25519");'
                'fs.writeFileSync(process.argv[1],k.privateKey.export({format:"pem",type:"pkcs8"}));'
                'process.stdout.write(k.publicKey.export({format:"der",type:"spki"}).subarray(-32).toString("hex"))')
        chaves = []
        for n in ('a', 'b'):
            arq = TMP / f'chave-{n}.pem'
            pub = subprocess.run(['node', '-e', node, str(arq)], capture_output=True, text=True).stdout
            chaves.append((arq, bytes.fromhex(pub)))
        (chave, pub), (_, outra) = chaves

        # Ed25519: vetores da RFC 8032 e assinatura do Node.js
        v1 = E.verificar(bytes.fromhex('d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a'), b'',
                         bytes.fromhex('e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25b'
                                       'f5f0595bbe24655141438e7a100b'))
        v2 = E.verificar(bytes.fromhex('3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c'), bytes.fromhex('72'),
                         bytes.fromhex('92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c'
                                       '387b2eaeb4302aeeb00d291612bb0c00'))
        v3 = E.verificar(bytes.fromhex('3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c'), bytes.fromhex('73'),
                         bytes.fromhex('92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c'
                                       '387b2eaeb4302aeeb00d291612bb0c00'))
        verificar('Ed25519: vetores de teste da RFC 8032 aceitos; mensagem trocada recusada', v1 and v2 and not v3)

        # instalador falso de uma versão nova, publicado no "GitHub" local
        inst = TMP / 'AYEscreva-9.9.9-teste-windows11-x64.exe'
        inst.write_bytes(os.urandom(11 * 2**20))
        (SITE / 'releases' / 'v9.9.9').mkdir(parents=True)
        shutil.copy(inst, SITE / 'releases' / 'v9.9.9' / inst.name)
        g = gerar(chave, inst, prefixo=prefixo)
        verificar('Gerar o arquivo de versões: assinado pelo Node.js com a chave do projeto (aqui, a de teste)', bytes.fromhex(g['chave_publica']) == pub, g)
        consulta = lambda **kw: A.consultar(kw.pop('versao', '0.6.0'), kw.pop('canal', 'testes'), manifesto=base + '/atualizacoes.json',
                                            chave=kw.pop('chave', pub), prefixo=prefixo, ler=ler_local)
        r = consulta()
        verificar('Versão nova assinada: aceita, com versão, notas, tamanho e SHA-256 do instalador',
                  r['situacao'] == 'nova' and r['versao'] == '9.9.9' and r['notas'] == 'Novidades de teste.'
                  and r['instalador']['sha256'] == hashlib.sha256(inst.read_bytes()).hexdigest(), r['situacao'])
        verificar('Mesma versão instalada: "você já tem a mais recente"', consulta(versao='9.9.9')['situacao'] == 'atual')
        verificar('Canal sem versões publicadas: informado', consulta(canal='estavel')['situacao'] == 'sem_canal')

        def recusa(**kw):
            try:
                consulta(**kw)
                return None
            except A.Recusado as e:
                return str(e)
        verificar('Assinada por outra chave: recusada', 'assinatura' in (recusa(chave=outra) or ''), recusa(chave=outra))
        original = (SITE / 'atualizacoes.json').read_bytes()
        (SITE / 'atualizacoes.json').write_bytes(original.replace(b'"9.9.9"', b'"9.9.8"', 1))
        verificar('Arquivo de versões alterado depois de assinado: recusado', 'assinatura' in (recusa() or ''), recusa())
        (SITE / 'atualizacoes.json').write_bytes(original)
        sig = (SITE / 'atualizacoes.json.sig').read_bytes()
        (SITE / 'atualizacoes.json.sig').unlink()
        verificar('Sem assinatura: recusado', 'assinatura' in (recusa() or ''), recusa())
        (SITE / 'atualizacoes.json.sig').write_bytes(sig)

        # assinado, mas apontando para fora das versões do projeto ou com nome trocado
        for descricao, troca in (('instalador fora das versões publicadas do projeto', {'url': 'https://outro.example/AYEscreva-9.9.9-teste-windows11-x64.exe'}),
                                 ('nome que não corresponde à versão', {'arquivo': 'AYEscreva-1.0.0-teste-windows11-x64.exe',
                                                                       'url': prefixo + 'v9.9.9/AYEscreva-1.0.0-teste-windows11-x64.exe'}),
                                 ('SHA-256 inválido', {'sha256': 'abc'})):
            m = json.loads(original)
            m['canais']['testes']['instalador'].update(troca)
            corpo = (json.dumps(m, indent=2) + '\n').encode()
            (SITE / 'atualizacoes.json').write_bytes(corpo)
            tmp = TMP / 'm.json'
            tmp.write_bytes(corpo)
            assin = subprocess.run(['node', '-e', 'const c=require("crypto"),fs=require("fs");process.stdout.write(c.sign(null,'
                                    'fs.readFileSync(process.argv[2]),c.createPrivateKey(fs.readFileSync(process.argv[1]))).toString("hex"))',
                                    str(chave), str(tmp)], capture_output=True, text=True).stdout
            (SITE / 'atualizacoes.json.sig').write_text(assin)
            verificar(f'Assinado, mas com {descricao}: recusado', recusa() is not None, recusa())
        (SITE / 'atualizacoes.json').write_bytes(original)
        (SITE / 'atualizacoes.json.sig').write_bytes(sig)

        # download do instalador com conferência de SHA-256 (o mesmo código do modelo de IA)
        info = consulta()
        pasta = TMP / 'baixados'
        caminho = A.baixar_instalador(info, pasta=str(pasta), exigir_https=False)
        verificar('Baixar o instalador: arquivo íntegro (SHA-256 do arquivo de versões) na pasta de atualizações',
                  Path(caminho).read_bytes() == inst.read_bytes(), caminho)
        Path(caminho).unlink()
        (SITE / 'releases' / 'v9.9.9' / inst.name).write_bytes(os.urandom(11 * 2**20))
        try:
            A.baixar_instalador(info, pasta=str(pasta), exigir_https=False)
            r = None
        except IA.FalhaDownload as e:
            r = str(e)
        verificar('Instalador trocado no servidor: recusado pelo SHA-256 e apagado', r and 'SHA-256' in r and not any(pasta.iterdir()), r)

        # roteiro de instalação (não é executado aqui)
        rot = A.roteiro_instalacao(str(inst), r'C:\Programas\AY ESCREVA', pasta=str(TMP))
        txt = Path(rot).read_text(encoding='mbcs')
        verificar('Roteiro de instalação: espera o AY fechar, instala por cima sem perguntas (por usuário) e reabre o AY',
                  all(x in txt for x in ('timeout /t 4', str(inst), '/SILENT', '/CURRENTUSER', '/CLOSEAPPLICATIONS', 'AYEscreva.exe')), txt)

        # só https; e o endereço real do site oficial
        try:
            A.buscar('http://davisoares50-hash.github.io/ay-escreva/atualizacoes.json')
            r = None
        except A.Recusado as e:
            r = str(e)
        verificar('Consulta só por https', r is not None, r)
        try:
            A.consultar('0.6.0')
            real = 'consultou'
        except A.SemInformacao as e:
            real = f'SemInformacao: {e}'
        except A.Recusado as e:
            real = f'Recusado: {e}'
        verificar('Endereço real do site oficial: sem arquivo de versões publicado, a resposta é clara e nada muda',
                  real.startswith('SemInformacao'), real)
    finally:
        srv.shutdown()
        shutil.rmtree(TMP, ignore_errors=True)
    saida = RAIZ / 'tests' / 'output' / 'atualizacao'
    saida.mkdir(parents=True, exist_ok=True)
    (saida / 'verificacao.json').write_text(json.dumps({'itens': itens}, ensure_ascii=False, indent=1), encoding='utf-8')
    n = sum(1 for x in itens if x['ok'])
    print(f'Verificar atualizações: {n}/{len(itens)}')
    return 0 if n == len(itens) else 1


if __name__ == '__main__':
    sys.exit(main())
