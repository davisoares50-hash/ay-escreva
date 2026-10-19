# Licenças, marcas e obrigações

## Código do AY ESCREVA

Tudo o que o projeto escreve (lançador, camada de configuração, interface `.ui`, extensão, identidade visual,
scripts, testes e documentação) é licenciado sob a **Mozilla Public License 2.0** (MPL-2.0), a mesma licença
principal do motor. Arquivos derivados de arquivos da base, como a futura `notebookbar_ayescreva.ui` gerada
a partir das `.ui` da base, **precisam** permanecer sob MPL-2.0.

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

## Dependências de desenvolvimento (não distribuídas no produto)

`tools/package.json`: `@resvg/resvg-js` (MPL-2.0), `@napi-rs/canvas` (MIT), `pdfjs-dist` (Apache-2.0),
`pixelmatch` (ISC), `pngjs` (MIT), `opentype.js` (MIT).
