# Site oficial e distribuição

O site apresenta o AY ESCREVA e distribui o instalador gratuitamente. O aplicativo continua sendo usado no
computador da pessoa; o site é só o canal de download.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `site/modelo.html` | moldura comum (topo, aviso de versão de testes, rodapé) |
| `site/paginas/*.html` | conteúdo das páginas (início, baixar, instalar, ajuda, privacidade, licenças) |
| `site/assets/` | estilo, script (menu e sugestão de download) — sem bibliotecas nem recursos externos |
| `site/versoes.json` | versões, notas, arquivos por plataforma e estado de cada sistema |
| `site/config.json` | modo de publicação (`local` ou `github`), repositório e endereços |
| `tools/gerar-site.mjs` | gera `out/site/` |
| `tools/servir-site.mjs` | servidor da prévia local (`http://127.0.0.1:8737/`) |

Gerado automaticamente a cada build:

- **Recursos**: lista, aba por aba, a partir de `ui/abas.json`. O selo "testado" aparece só nas funções cujo
  efeito foi conferido pelo teste pela interface (`tests/output/interface/faixa-resultado.json`). Funções sem
  comando aparecem como "Em desenvolvimento".
- **Versões**: notas de `site/versoes.json`; **limitações** copiadas de `extensao/ayescreva/ajuda/limitacoes.html`,
  o mesmo arquivo que o aplicativo abre offline.
- **Downloads**: tamanho e SHA-256 calculados do arquivo real em `out/instalador/`. O gerador falha se o
  instalador de uma versão marcada como disponível não existir, se sobrar marcador `{{...}}` ou se houver
  link interno quebrado.
- **Imagens**: capturas reais do aplicativo (`tests/output/interface/`), convertidas para WebP.

## Prévia local

```powershell
cd tools
node gerar-site.mjs --modo local          # copia o instalador para out/site/downloads/<versão>/ + SHA256SUMS.txt
node servir-site.mjs ..\out\site 8737     # http://127.0.0.1:8737/
```

## Hospedagem gratuita escolhida (verificada em 19/10/2026)

| Parte | Serviço | Limites oficiais | Custo |
|---|---|---|---|
| Páginas do site | GitHub Pages (repositório público) | site publicado até 1 GB; banda "suave" de 100 GB/mês; até 10 builds/h; não pode ser usado para negócio comercial ([docs](https://docs.github.com/pages/getting-started-with-github-pages/github-pages-limits)) | gratuito |
| Instaladores e `SHA256SUMS.txt` | GitHub Releases | cada arquivo abaixo de 2 GiB; "sem limite de tamanho total nem de banda" ([docs](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)) | gratuito |

Os dois servem por HTTPS. O site em si fica bem abaixo de 1 GB porque os instaladores não ficam no Pages, e
sim no Releases. Se o tráfego do site passar dos 100 GB/mês de forma contínua, o GitHub pode pedir mudança;
alternativas gratuitas a avaliar nesse caso: Cloudflare Pages (site) mantendo os instaladores no Releases.
Nenhum serviço pago é contratado e nenhuma cobrança automática é ativada.

## Testar o fluxo do site

```powershell
powershell -ExecutionPolicy Bypass -File tests\site\testar_fluxo.ps1 -Site http://127.0.0.1:8737/
```

Abre a página inicial, segue "Baixar gratuitamente", baixa pelo botão principal para uma pasta vazia, confere o
SHA-256 com o da página e com o `SHA256SUMS.txt`, visita todas as páginas e confere que cada link de download
responde e que os sistemas "Em desenvolvimento" não têm botão; depois instala o arquivo baixado, abre, usa e
desinstala (`tests\instalacao\testar_instalacao.ps1`). Resultado em `tests\output\site\fluxo.json`.

## Publicar (precisa de autorização explícita do responsável pelo projeto)

Tudo está pronto em `scripts\publicar-site.ps1`. Sem `-Executar` ele só simula: confere os pré-requisitos,
gera o site em modo de publicação (`out\site-publicacao`, links para o GitHub Releases) e mostra os comandos.

```powershell
# simulação (não envia nada)
powershell -ExecutionPolicy Bypass -File scripts\publicar-site.ps1 -Repositorio davisoares50-hash/ay-escreva
# publicação real, depois da autorização
powershell -ExecutionPolicy Bypass -File scripts\publicar-site.ps1 -Repositorio davisoares50-hash/ay-escreva -CriarRepositorio -Executar
```

Com `-Executar`: cria o repositório público (com `-CriarRepositorio`) e envia o branch `main`; cria a versão
`v<versão>` no Releases como pré-lançamento, com o instalador, o `SHA256SUMS.txt` e as notas
(`out\publicacao\v<versão>\NOTAS.md`); baixa o arquivo publicado e confere o SHA-256; envia o site para o branch
`gh-pages` e ativa o Pages; espera o site responder e roda `tests\site\testar_fluxo.ps1` no endereço publicado
(HTTPS). Requer o GitHub CLI (`gh`) autenticado na conta dona do repositório; o commit do site usa o endereço
"noreply" do GitHub, não o e-mail pessoal.

**Estado (20/10/2026): 0.2.0 publicada** com autorização do responsável.

| O quê | Endereço |
|---|---|
| Site (GitHub Pages, HTTPS obrigatório) | https://davisoares50-hash.github.io/ay-escreva/ |
| Instalador (GitHub Releases, sem login) | https://github.com/davisoares50-hash/ay-escreva/releases/download/v0.2.0/AYEscreva-0.2.0-teste-windows11-x64.exe |
| Versão e notas | https://github.com/davisoares50-hash/ay-escreva/releases/tag/v0.2.0 |
| Repositório | https://github.com/davisoares50-hash/ay-escreva |

Fluxo público testado (acessar, baixar, conferir o SHA-256, instalar, abrir, desinstalar): ver
[RESULTADOS-TESTES.md §10](RESULTADOS-TESTES.md). Opcionais ainda não feitos: domínio próprio e certificado de
assinatura de código.

## Lançar uma nova versão

1. Atualizar a versão em `launcher/AYEscreva.cs` e montar (`scripts/montar.ps1`), testar (`scripts/testar.ps1`,
   `tests/interface/testar_faixa.ps1`) e gerar o instalador (`scripts/instalador.ps1`).
2. Validar a instalação (`tests/instalacao/testar_instalacao.ps1`).
3. Em `site/versoes.json`: nova entrada no topo de `versoes`, atualizar `atual`; mudar uma plataforma para
   `"status": "disponivel"` **somente** depois de testada nela.
4. Atualizar `extensao/ayescreva/ajuda/limitacoes.html` (vira a seção de limitações do site).
5. Gerar a prévia (`node tools\gerar-site.mjs --modo local`), rodar `tests\site\testar_fluxo.ps1` e, com
   autorização, `scripts\publicar-site.ps1 -Repositorio <dono>/<nome> -Executar` (cria a versão no Releases,
   atualiza o Pages e testa o fluxo publicado). Os links de download são gerados de `site/versoes.json` e apontam
   para `https://github.com/<dono>/<nome>/releases/download/v<versão>/<arquivo>`; versões antigas continuam no
   Releases e listadas na página Versões.
