# Licenças, marcas e obrigações

## Código do AY ESCREVA

Tudo o que o projeto escreve (lançador, camada de configuração, interface `.ui`, extensão, identidade visual,
scripts, testes e documentação) é licenciado sob a **Mozilla Public License 2.0** (MPL-2.0), a mesma licença
principal do motor. A faixa `notebookbar_ayescreva.ui` é gerada por `tools/gerar-faixa.mjs` a partir de
`ui/abas.json` e usa as classes da base e os ícones do tema Colibre (CC0); fica, como o restante, sob MPL-2.0.

## Motor (LibreOffice 26.8.1.1, binários oficiais sem modificação de código)

| Obrigação | Como o AY cumpre |
|---|---|
| MPL-2.0 §3.2: informar como obter o código-fonte dos arquivos cobertos distribuídos em forma executável | `installer/LICENCA.txt` e esta página apontam o código exato: <https://download.documentfoundation.org/libreoffice/src/26.8.1/> |
| LGPLv3+ (partes da base): permitir substituir as bibliotecas e oferecer o código | as bibliotecas ficam como arquivos separados em `program/`; mesmo endereço de código-fonte |
| Manter avisos de licença e créditos | `LICENSE.html`, `license.txt`, `NOTICE` e `CREDITS.fodt` são distribuídos intactos; acessíveis em Ajuda > Licenças |
| Componentes de terceiros (ICU, NSS, Python, fontes OFL etc.) | listados em `LICENSE.html` da base, distribuído intacto |

## Marca

- "LibreOffice" e "The Document Foundation" são marcas da TDF. O AY **não** usa esses nomes ou logotipos como
  marca própria, não se apresenta como produto da TDF e identifica o fornecedor como "Projeto AY ESCREVA"
  (`version.ini` e `ooVendor`).
- A atribuição ("inclui o LibreOffice", créditos e licenças) é mantida, como exigem as licenças.
- Se o Nível 2 modificar código, os binários passam a ser do AY. A assinatura da TDF deixa de valer para esses
  arquivos e eles devem ser assinados pelo projeto.

## Identidade visual do AY

O logotipo, o ícone e as imagens são gerados por `tools/marca.mjs`. As letras são contornos da fonte **Rubik**
(SIL Open Font License 1.1, incluída na base), e a OFL permite usar contornos de glifos em logotipos.
Nome, cores e símbolo pertencem ao projeto AY ESCREVA.

## Site oficial

- Código e textos do site (`site/`, `tools/gerar-site.mjs`): MPL-2.0, como o restante do projeto.
- A fonte Rubik do site é servida pelo próprio site (sem Google Fonts nem outro recurso externo), sob a SIL Open
  Font License 1.1; o aviso está na página Licenças do site.
- As capturas de tela do site são do próprio AY ESCREVA (os ícones Colibre da base são CC0, de Andreas Kainz).

## Ferramentas de geração (não distribuídas no produto)

| Ferramenta | Licença | Uso no projeto | Custo |
|---|---|---|---|
| Inno Setup 6.7.3 (instalado por `winget`, por usuário) | licença própria de Jordan Russell: "Permission is granted to anyone to use this software for any purpose, including commercial applications", com obrigação de manter avisos | compilar o instalador | gratuito, sem licença paga para este uso |
| GitHub Pages e GitHub Releases (planejados para a publicação) | termos do GitHub | hospedar o site e os instaladores | plano gratuito; ver [SITE.md](SITE.md) |

## Dependências de desenvolvimento (não distribuídas no produto)

`tools/package.json`: `@resvg/resvg-js` (MPL-2.0), `@napi-rs/canvas` (MIT), `pdfjs-dist` (Apache-2.0),
`pixelmatch` (ISC), `pngjs` (MIT), `opentype.js` (MIT).
