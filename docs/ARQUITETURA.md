# Decisão de arquitetura do AY ESCREVA

Situação: **decidida e em execução (Etapa 1 concluída)** · Data: 19/10/2026 · Base: LibreOffice 26.8.1.1

## 1. Pergunta

O AY ESCREVA precisa ser um processador de textos completo: paginação real, DOCX e ODT fiéis, tabelas,
imagens, seções, notas, controle de alterações, impressão, acessibilidade, funcionamento offline e instalação
própria. A pergunta foi: **usar o LibreOffice Writer como base (versão derivada ou integração) ou construir um
editor próprio?**

## 2. Opções avaliadas

| | Opção | Em resumo |
|---|---|---|
| A | **Versão derivada do LibreOffice compilada do código-fonte** | Fork do `core` com marca, nome, instalador, interface e correções próprias |
| B | **Distribuição derivada sobre os binários oficiais do LibreOffice + camada AY** | Binários assinados pela TDF sem alteração de código; marca, configuração, interface (.ui), extensão e instalador do AY por cima |
| C | Collabora Office para desktop (interface web do Collabora Online + núcleo LibreOffice) | Interface em HTML/JS num WebView sobre o mesmo motor |
| D | Fork do ONLYOFFICE Desktop Editors | Editor em canvas/JS com OOXML nativo |
| E | Editor próprio (HTML/ProseMirror/TipTap ou nativo) | Escrever motor de layout, paginação e filtros do zero |

## 3. Comparação pelos critérios pedidos

Legenda: ●●● pronto e maduro · ●● existe, com ressalvas · ● parcial · ○ inexistente / a construir

| Critério | A / B (LibreOffice) | C (Collabora desktop) | D (ONLYOFFICE) | E (editor próprio) |
|---|---|---|---|---|
| Paginação real, cabeçalhos/rodapés por seção | ●●● motor do Writer | ●●● mesmo motor | ●●● | ○ — HTML não pagina; exigiria motor de layout próprio |
| DOCX leitura/escrita | ●● muito bom, com diferenças conhecidas (ver [RESULTADOS-TESTES](RESULTADOS-TESTES.md)) | ●● mesmo filtro | ●●● formato interno é OOXML | ○ anos de trabalho para fidelidade mínima |
| ODT | ●●● formato nativo | ●●● | ●● conversão | ○ |
| DOC, RTF, TXT | ●● filtros maduros, limitações documentadas | ●● | ●● | ○ |
| Tabelas (mescladas, cabeçalho repetido) | ●●● | ●●● | ●●● | ● |
| Imagens, formas, caixas de texto | ●●● | ●●● | ●●● | ● |
| Seções, colunas, orientação mista | ●●● | ●●● | ●●● | ○ |
| Notas de rodapé e de fim | ●●● | ●●● | ●●● | ○ |
| Controle de alterações, comentários, comparação | ●●● | ●●● | ●● | ○ |
| Impressão pelo sistema, prévia | ●●● nativa | ●● pelo WebView | ●● | ● |
| PDF, PDF/A, PDF/UA marcado | ●●● | ●●● | ●● | ● |
| Ortografia pt-BR offline | ●●● Hunspell + VERO | ●●● | ●● | ● |
| Acessibilidade (leitores de tela no Windows) | ●● ponte IAccessible2/MSAA nativa (NVDA); verificador de acessibilidade | ● interface web; área do documento em canvas | ● canvas | ● depende do que for construído |
| Teclado, escalas de exibição, tema escuro | ●● | ●● | ●● | ● |
| Mala direta, envelopes, etiquetas | ●●● | ●● | ● | ○ |
| Licença e identidade própria | ●●● MPL-2.0 (+ LGPLv3+); marca "LibreOffice" não pode ser usada, o que é exatamente o que queremos (nome próprio) | ●●● MPL-2.0 | ✖ AGPLv3 com termo §7(b) exigindo manter o logotipo original; disputado pela FSF ([LWN](https://lwn.net/Articles/1067771/)) — incompatível com "identidade própria" sem risco jurídico | ●●● livre escolha |
| Manutenção | A: ●● rebase semestral de patches; B: ●●● trocar versão fixada | ● dois repositórios (core + online), produto novo e ainda sem suporte corporativo | ● | ○ equipe grande por anos |
| Empacotamento Windows/macOS/Linux | A: MSI/DMG/DEB/RPM próprios do build; B: instalador AY sobre binários oficiais | ●● Store/Flathub | ●● | ● |
| Windows 10 | ●●● (26.8 exige Windows 10+) | ✖ relatado como Windows 11 apenas no lançamento | ●● | — |

**Conclusão:** só A/B entrega já, de forma verificável, as funções de um processador de textos completo com
licença que permite nome e identidade próprios. E foi descartada: um editor HTML não oferece paginação,
seções, notas, controle de alterações nem fidelidade DOCX equivalentes, e construir isso seria o projeto inteiro.
C é promissora pela interface parecida com o Office, mas é nova, depende de dois repositórios e coloca o
documento num canvas web, o que piora a acessibilidade com leitores de tela. D tem o melhor DOCX, mas a cláusula
de logotipo conflita com a exigência de identidade própria.

## 4. Recomendação: versão derivada do LibreOffice em dois níveis

### Nível 1 — Distribuição derivada (Etapas 1 a 3, **em uso agora**)

```
AY ESCREVA (Windows x64)
├── AYEscreva.exe              lançador próprio (C#, .NET Framework 4.8, ícone e metadados AY)
├── program/                   binários oficiais LibreOffice 26.8.1.1 (assinados pela TDF, SHA-256 fixado)
│   ├── bootstrap.ini          ► perfil próprio %APPDATA%\AYEscreva\1 (não conflita com LibreOffice instalado)
│   ├── version.ini            ► fornecedor "Projeto AY ESCREVA", URLs de atualização vazias
│   ├── soffice.ini            ► tela de abertura AY, sem coleta de despejos de falha
│   ├── intro*.png, shell/*.svg► identidade visual AY (tela de abertura, Sobre, Central de Início)
│   └── msvcp140.dll …         runtime do Visual C++ ao lado dos executáveis
└── share/
    ├── registry/ayescreva.xcd ► camada de configuração AY (nome, segurança, recuperação, interface, idioma)
    ├── fonts/truetype/        fontes da base registradas de forma privada (sem instalar no sistema)
    └── extensions/            só dicionários pt-BR, pt-PT, en, es
```

O que muda em relação à base, sem tocar no código C++:

| Área | Como | Arquivo |
|---|---|---|
| Nome do produto nas janelas | `org.openoffice.Setup/Product/ooName = AY ESCREVA` | `layer/share/registry/ayescreva.xcd` |
| Perfil de usuário isolado | `UserInstallation=$SYSUSERCONFIG/AYEscreva/1` | `program/bootstrap.ini` (ajustado por `scripts/montar.ps1`) |
| Macros nunca executadas | nível de segurança 3 travado + lista de locais confiáveis vazia e travada | `ayescreva.xcd` |
| Sem recursos externos automáticos | bloqueio de links de documentos não confiáveis (travado); vínculos só sob pergunta | `ayescreva.xcd` |
| Sem envio de dados | relatório de falhas desligado e travado; verificação de atualização da base removida (`onlineupdate.xcd`), sem URLs em `version.ini`; extensão de publicação em wiki removida | `ayescreva.xcd`, `montar.ps1` |
| Recuperação e salvamento seguro | informação de recuperação a cada 5 min; cópia de segurança ao salvar | `ayescreva.xcd` |
| pt-BR | interface pt-BR, idioma padrão dos documentos pt-BR, ajuda offline pt-BR | `ayescreva.xcd`, helppack |
| Interface por abas | faixa própria `notebookbar_ayescreva.ui`, gerada de `ui/abas.json` por `tools/gerar-faixa.mjs`, na ordem pedida; modo "AY ESCREVA" registrado em `ToolbarMode` e padrão | `ayescreva.xcd`, `ui/abas.json`, `tools/gerar-faixa.mjs` |
| Compatibilidade Word | realce exportado como realce do Word, não sombreamento | `ayescreva.xcd` |
| Comandos que faltam na base | extensão UNO própria (Python), protocolo `ayescreva:`: página em branco, recuperação de documentos, guia, atalhos, limitações e diagnóstico | `extensao/ayescreva/` |
| Avisos de perda e de fontes | a extensão intercepta Salvar, Salvar como e Salvar uma cópia (`XDispatchProviderInterceptor`) e, em formato não nativo, lista as perdas possíveis no documento e oferece ODT ou cópia em ODT; ao abrir, mostra uma barra de informação com as fontes substituídas | `extensao/ayescreva/ayescreva.py` |

Atualização da base: trocar a versão em `base/base.lock.json` (URL + SHA-256), rodar `scripts/montar.ps1` e
`scripts/testar.ps1`. Como não há patch de código, não há conflito de rebase.

Limites do Nível 1, que motivam o Nível 2:

- Ícone da janela e da barra de tarefas ainda é o do Writer da base; o agrupamento na barra de tarefas usa o
  AppUserModelID da base. O título da janela é "… — AY ESCREVA Writer".
- O executável do motor continua `soffice.exe`; textos internos de "Sobre/Créditos" citam o LibreOffice, o que
  é correto como atribuição.
- A automação UNO **externa** (outro processo controlando o motor) com a faixa por abas na tela pode derrubar o
  motor 26.8.1 (falha em `KERNELBASE.dll`, deslocamento `0xc408a`), inclusive na base sem alterações. O uso pela
  interface e o código que roda dentro do aplicativo (extensão, testes pela interface) não apresentaram o problema.
  Os testes que usam UNO externo rodam com a barra clássica num perfil descartável.
- Correções de compatibilidade que exigem C++ (ex.: página em branco automática no reinício de numeração,
  borracha de traços, pressão da caneta) não são possíveis.

### Nível 2 — Fork de código (Etapa 4 em diante, quando houver ambiente de compilação)

Repositório `ay-core` derivado de `git.libreoffice.org/core`, **branch `ay-26.8` sobre a tag
`libreoffice-26.8.x.y`**, com uma fila pequena de commits próprios:

| Parte modificada | Onde no código | Para quê |
|---|---|---|
| Nome, fornecedor, marca | `configure` com `--with-product-name="AY ESCREVA" --with-vendor="Projeto AY ESCREVA" --with-branding=<pasta>` | nome em todo o produto, imagens próprias (`intro.png`, `about.svg`, `logo.svg`) |
| Ícones de janela e AppUserModelID | `vcl/win`, `sysui/desktop/icons`, `desktop/win32` | ícone AY na barra de tarefas e agrupamento próprio |
| Instalador MSI próprio | `instsetoo_native/util/openoffice.lst` (UpgradeCode, nomes), `scp2/` (atalhos, associações) | MSI com identidade AY para implantação corporativa |
| Interface | `sw/uiconfig/swriter/ui/notebookbar_ayescreva.ui`, `officecfg/registry/data/org/openoffice/Office/UI/ToolbarMode.xcu` | faixa de opções AY embutida |
| Correções de compatibilidade | `sw/source/core/layout/` etc. | ex.: opção para não inserir página em branco automática em documentos Word |
| Desenho à mão | `svx/`, `sw/source/uibase/` | borracha por arrasto, marca-texto, pressão |

Manutenção: cada nova versão estável da base (fevereiro e agosto) → `git rebase` da fila AY sobre a nova tag,
rodar `make check` nos módulos afetados e a bateria `scripts/testar.ps1`; correções genéricas são enviadas ao
upstream (Gerrit do LibreOffice) para encolher a fila. Requisitos de compilação estão em
[COMPILACAO.md](COMPILACAO.md#nível-2--compilar-o-motor-do-código-fonte).

## 5. Segurança e privacidade (configuração efetiva)

| Requisito | Configuração | Verificado |
|---|---|---|
| Não executar macros | `MacroSecurityLevel=3` (finalizado), `SecureURL` vazio (finalizado) | **Validado** (`tests/uno/seguranca.py`): ODT com macro Basic no evento "ao abrir" não executa na abertura normal nem aprovando confirmações; controle positivo (execução forçada pela API) executa, provando que o teste detecta execução |
| Não carregar recursos externos | `BlockUntrustedRefererLinks=true` (finalizado); `Writer/Content/Update/Link=1` (pergunta) | **Validado**: DOCX com imagem vinculada a servidor HTTP local gerou 0 requisições ao abrir e exportar PDF. Observação: mesmo um pedido explícito de atualização de vínculos gerou 0 requisições; ainda não se sabe se o bloqueio vem da política ou do filtro DOCX. Hoje não há como autorizar o carregamento por documento (lacuna da Etapa 4) |
| Não enviar conteúdo | `CrashReport=false` (finalizado), `CrashDumpEnable=false`, atualização da base removida | por configuração; auditoria de rede com captura de tráfego durante uso interativo: **pendente** |
| Documentos locais | perfil e documentos no disco; sem conta | — |

Escolha de política: `DisableMacrosExecution=true` também bloquearia macros, mas faz o motor exibir o aviso
"Macros desativadas" em **todo** documento, até sem macros (`sfx2/source/view/viewfrm.cxx`). Com o nível 3 e
nenhum local confiável o efeito é o mesmo para documentos, e o aviso só aparece quando há macros.

## 6. Fontes consultadas (outubro de 2026)

- Versões e arquivos oficiais: <https://download.documentfoundation.org/libreoffice/stable/26.8.1/>
- Fim do suporte a Windows 7/8/8.1 e 32 bits descontinuado na 25.8: [The Register](https://theregister.com/2025/06/16/libreoffice_ditch_windows), [Winaero](https://winaero.com/libreoffice-25-8-will-completely-drop-support-for-windows-7-8-8-1), [Computerworld](https://www.computerworld.com/article/4047794/libreoffice-cuts-off-32-bit-support-in-new-release.html)
- Compilação no Windows: <https://wiki.documentfoundation.org/Development/BuildingOnWindows>
- Opções de marca do `configure` (branch `libreoffice-26-8`): `--with-product-name`, `--with-vendor`, `--with-branding` em <https://raw.githubusercontent.com/LibreOffice/core/libreoffice-26-8/configure.ac>
- Collabora Office para desktop: [Collabora](https://www.collaboraonline.com/blog/collabora-online-now-available-on-desktop/), [igor'sLAB](https://www.igorslab.de/en/collabora-office-brings-modern-libreoffice-technology-completely-offline-to-the-desktop-for-the-first-time/)
- Cláusula de logotipo do ONLYOFFICE: [LWN](https://lwn.net/Articles/1067771/), [ie-forum](https://ie-forum.nl/artikelen/the-logo-trap-onlyoffice-s-agplv3-gambit-and-what-it-means-for-free-and-open-source-compliance)
- Ponte de acessibilidade do Windows: <https://docs.libreoffice.org/winaccessibility.html>
- LanguageTool local no Writer: [It's FOSS](https://itsfoss.com/libreoffice-languagetool/)
- Política de marca da TDF (derivados devem usar nome próprio): [listarchives.tdf.io](https://listarchives.tdf.io/i/fiAOfkmyI8WojfgUNultbSpJ), [LWN](https://lwn.net/Articles/536126/)
- Comportamento de página em branco no reinício de numeração: [Ask LibreOffice](https://ask.libreoffice.org/t/writer-page-numbering-is-wrong-one-number-up/81691), [tdf#126284](https://libreoffice.org/get-help/bug/show_activity.cgi?id=126284)
- Código-fonte conferido diretamente: `configmgr/source/xcdparser.cxx`, `sfx2/source/notebookbar/SfxNotebookBar.cxx`, `sfx2/source/view/viewfrm.cxx`, `vcl/win/gdi/salfont.cxx`, `desktop/source/splash/splash.cxx`, `sw/inc/linkenum.hxx` (branch `libreoffice-26-8`)
