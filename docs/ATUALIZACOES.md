# Publicar uma atualização (entrega E)

"Verificar atualizações" (Ajuda) consulta **só** `https://davisoares50-hash.github.io/ay-escreva/atualizacoes.json` e o arquivo
de assinatura `atualizacoes.json.sig` ao lado. Ele só oferece a versão se:

1. a assinatura Ed25519 do arquivo confere com a chave pública que vai dentro do AY
   (`extensao/ayescreva/pythonpath/ay_atualizacao.py`, `CHAVE_PUBLICA`);
2. o instalador está nas versões publicadas do projeto
   (`https://github.com/davisoares50-hash/ay-escreva/releases/download/v<versão>/AYEscreva-<versão>-….exe`);
3. nome, tamanho e SHA-256 batem; o SHA-256 é conferido de novo depois do download.

## Chave do projeto

- Chave **privada**: `%USERPROFILE%\.ay-escreva\chave-atualizacoes-ed25519.pem` (gerada em 21/10/2026, fora do
  repositório). **Guarde uma cópia em lugar seguro.** Sem ela, nenhuma atualização nova será aceita pelo AY (as pessoas
  teriam de instalar pelo site); com ela, alguém poderia publicar uma atualização falsa — nunca a envie nem a publique.
- Chave **pública**: `ad50bd7986ca377c9335f9846293bcf56c0ac889e6e3bbfaf1b95f6e3f7d8a10` (no código do AY).

## Passos para publicar (depois de decidir publicar uma versão)

```powershell
# 1. gerar o instalador e conferir (scripts/instalador.ps1, testes)
# 2. criar o lançamento v<versão> no GitHub com o instalador anexado (como na 0.2.0)
# 3. gerar e assinar o arquivo de versões:
node tools/gerar-manifesto.mjs --canal testes --instalador out/instalador/AYEscreva-<versão>-teste-windows11-x64.exe --notas "O que mudou…"
# 4. publicar out/atualizacoes/atualizacoes.json e atualizacoes.json.sig na raiz do site oficial
```

Nada disso é feito automaticamente: publicar continua sendo uma decisão de quem mantém o projeto.
