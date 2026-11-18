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
  repositório). Sem ela, nenhuma atualização nova será aceita pelo AY (as pessoas teriam de instalar pelo site); com
  ela, alguém poderia assinar um arquivo de versões falso — nunca a envie, não a publique e não a cole em conversas,
  relatos de problemas ou registros.
- Chave **pública**: `ad50bd7986ca377c9335f9846293bcf56c0ac889e6e3bbfaf1b95f6e3f7d8a10` (no código do AY,
  `ay_atualizacao.py`). É o único material de assinatura que vai no aplicativo.

### Onde a chave privada NÃO está (conferido em 22/10/2026)

Procura feita sem exibir a chave: o conteúdo do arquivo (PEM, DER, semente em hexadecimal e em base64) e qualquer
cabeçalho `PRIVATE KEY` foram procurados byte a byte.

| Lugar | Resultado |
|---|---|
| Repositório (arquivos de trabalho), `dist\` (o que vira o instalador), `out\` (instaladores, site gerado, prévias), `site\`, `tests\output\` — 37.500 arquivos, 11,6 GB | nenhuma ocorrência |
| Histórico do git (todos os 275 objetos, inclusive os não alcançáveis por ramos) | nenhuma ocorrência |
| Registros do aplicativo e dos testes em `%TEMP%` | nenhuma ocorrência |
| Registros das conversas de desenvolvimento deste projeto | nenhuma ocorrência |
| Instalador | montado só a partir de `dist\` (`installer\ayescreva.iss`, `Source: "{#Dist}\*"`), que está limpo; a instalação feita pelo instalador final (13.960 arquivos) também foi varrida: nenhuma ocorrência (RESULTADOS-TESTES.md §3 e §13) |

Também: o arquivo da chave só pode ser lido pelo seu usuário, pelos administradores e pelo sistema (permissões
padrão do perfil); `tools/gerar-manifesto.mjs` se recusa a assinar com uma chave cuja parte pública não seja a do AY
(evita assinar com uma cópia errada ou com uma chave de teste); o teste `tests/atualizacao/testar_verificacao.py`
confere essa recusa.

### Cópia de segurança protegida

1. Confira o arquivo antes de copiar (mostra só a chave pública derivada, nunca a privada):

   ```powershell
   node tools/conferir-chave.mjs
   ```

2. Faça **duas** cópias cifradas, guardadas em lugares diferentes e fora deste computador — por exemplo, dois pen
   drives guardados em casas diferentes, ou um pen drive e um cofre de senhas:
   - **Pen drive com BitLocker To Go** (Windows Pro): clique com o botão direito no pen drive › *Ativar o BitLocker* ›
     senha longa. Copie o `.pem` para ele. Ou um arquivo **7-Zip com AES-256** e "criptografar nomes de arquivo",
     com senha longa (5 ou mais palavras aleatórias).
   - Guarde a senha num gerenciador de senhas, **não** junto do pen drive.
   - Não guarde a chave sem cifragem em nuvem (OneDrive, Google Drive), e-mail ou mensageiro.
3. Confira cada cópia, abrindo-a e rodando `node tools/conferir-chave.mjs <caminho-da-cópia>`: deve aparecer
   "CONFERE". Depois, ejete o pen drive.
4. Repita a conferência uma vez por ano e sempre que trocar de computador.

### Se a chave for perdida (sem cópia)

Nada de ruim acontece com quem já tem o AY: atualizações falsas continuam impossíveis. Só deixa de ser possível
oferecer atualizações pelo próprio AY às versões já instaladas.

1. Gere uma chave nova (como em 21/10/2026), troque `CHAVE_PUBLICA` em `ay_atualizacao.py` e publique uma versão nova.
2. Avise no site e nas notas da versão: quem tem uma versão anterior precisa baixar e instalar a nova **pelo site**
   uma vez (instalar por cima mantém documentos e preferências). Daí em diante, as atualizações voltam a funcionar.

### Se a chave vazar (ou houver suspeita)

Com a chave, alguém pode assinar um arquivo de versões falso. Para ele ser aceito pelo AY, a pessoa também precisa
publicar no **site oficial** (GitHub Pages do projeto) e pôr o instalador nas **versões do projeto** no GitHub
(Releases) — o AY recusa instaladores de qualquer outro endereço e confere o SHA-256. Ou seja, o vazamento da chave
sozinho não basta, mas tira uma das duas proteções. Então:

1. **Proteja a conta do GitHub** (senha nova, verificação em duas etapas, revise chaves SSH, tokens e colaboradores).
2. **Retire** do site o `atualizacoes.json` e o `.sig` (sem arquivo de versões, o AY responde "nenhuma atualização
   publicada" e não baixa nada) e confira se as versões publicadas no GitHub são as suas (SHA-256).
3. Gere uma chave nova, troque `CHAVE_PUBLICA`, publique a versão nova e avise no site que ela deve ser instalada
   **pelo site** (as versões antigas confiam na chave vazada, e as atualizações passam a valer só a partir da nova).
4. Apague a chave antiga de todas as cópias.

Hoje o AY confia numa única chave pública. Uma melhoria possível (não implementada) é já levar no aplicativo uma
segunda chave pública, de reserva, guardada desligada da internet: perder ou trocar a chave principal deixaria de
exigir a reinstalação pelo site.

## Passos para publicar (depois de decidir publicar uma versão)

```powershell
# 1. gerar o instalador e conferir (scripts/instalador.ps1, testes)
# 2. criar o lançamento v<versão> no GitHub com o instalador anexado (como na 0.2.0)
# 3. gerar e assinar o arquivo de versões:
node tools/gerar-manifesto.mjs --canal testes --instalador out/instalador/AYEscreva-<versão>-teste-windows11-x64.exe --notas "O que mudou…"
# 4. publicar out/atualizacoes/atualizacoes.json e atualizacoes.json.sig na raiz do site oficial
```

Nada disso é feito automaticamente: publicar continua sendo uma decisão de quem mantém o projeto.

## Publicação da 0.7.0 (18/11/2026)

Publicada com autorização do responsável, por `scripts\publicar-site.ps1 -Executar`, a partir destes arquivos de `out\`
(resultados em RESULTADOS-TESTES.md §10):

| Arquivo | Para quê |
|---|---|
| `out\instalador\AYEscreva-0.7.0-teste-windows11-x64.exe` e `.sha256` | instalador correspondente ao código testado |
| `out\publicacao\v0.7.0\NOTAS.md` e `SHA256SUMS.txt` | texto e conferência do lançamento no GitHub (Releases) |
| `out\atualizacoes\atualizacoes.json` e `.sig` | arquivo de versões assinado (canal "testes"), conferido com o código de verificação do AY |
| `out\site-previa-0.7.0\` | prévia local do site (abre direto no navegador) |
| `out\site-publicacao-0.7.0\` | site já gerado no modo de publicação, com os links do GitHub Releases |

Ordem seguida (a mesma para as próximas versões; a versão pública anterior continua no ar até o passo 3):

1. Criar o lançamento `v0.7.0` (pré-lançamento) no GitHub com o instalador e o `SHA256SUMS.txt`, usando `NOTAS.md`.
2. Conferir por HTTPS que o arquivo publicado tem o mesmo SHA-256.
3. Em `site\versoes.json`, marcar a 0.7.0 como `"publicada": true` e publicar o site
   (`scripts\publicar-site.ps1 -Repositorio davisoares50-hash/ay-escreva -Executar`). Antes disso, o gerador do site
   **se recusa** a gerar o modo de publicação da 0.7.0, para que o site não aponte para um arquivo inexistente.
4. `out\atualizacoes\atualizacoes.json` e `.sig` vão para a raiz do site publicado: o script os inclui no envio do site,
   só se anunciarem esta versão, este instalador (SHA-256) e o endereço do lançamento. A partir daí, quem tem a 0.2.0
   **não** recebe a oferta (a 0.2.0 não tem "Verificar atualizações"); quem tiver uma versão de testes com a verificação
   recebe a oferta.
