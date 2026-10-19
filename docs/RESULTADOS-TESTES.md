# Resultados dos testes — versão 0.2.0 (versão inicial de testes para Windows 11 x64)

Execução: 19/10/2026 · `scripts/testar.ps1` + `tests/interface/testar_faixa.ps1` + `tests/instalacao/testar_instalacao.ps1`
+ `tests/site/testar_fluxo.ps1`
Ambiente: Windows 11 Pro 10.0.26200 x64, Intel Core i5-8500, 16 GB · Motor: LibreOffice 26.8.1.1 (binários oficiais)
Oráculo independente: Microsoft Word 16.0 (instalado na máquina, usado só via automação COM com macros desativadas)

## 1. O que está implementado, compilado e validado

| Componente | Código implementado | Compilação/montagem executada | Funcionamento validado |
|---|---|---|---|
| Obtenção da base (SHA-256, PGP, Authenticode) | sim — `scripts/montar.ps1` | sim | sim: assinatura PGP da chave `C2839ECA…AFEEAEA3` e Authenticode "The Document Foundation" válidas |
| Distribuição AY (poda de idiomas, fontes privadas, runtime VC++) | sim | sim — 797 MB | sim: o motor inicia e edita (testes abaixo) |
| Camada de configuração `ayescreva.xcd` | sim | sim | sim: título "AY ESCREVA", realce→`w:highlight`, faixa AY padrão, segurança de macros |
| Identidade visual | sim — `tools/marca.mjs` | sim | parcial: ícone do lançador, tela de abertura e instalador conferidos; ícone da janela ainda é o da base |
| Lançador `AYEscreva.exe` (0.2.0) | sim — C# | sim — csc do .NET Framework 4.8.1 | sim: abre o aplicativo instalado com perfil próprio |
| Faixa de opções AY (`notebookbar_ayescreva.ui`, 11 abas + 4 contextuais) | sim — `tools/gerar-faixa.mjs` a partir de `ui/abas.json` | sim — 224 botões | sim — §4 (Forma e Visualizar impressão: só conferência visual) |
| Extensão AY (comandos `ayescreva:`, avisos de perdas e de fontes) | sim — `extensao/ayescreva` | sim — empacotada na distribuição | sim — §4 e §5 |
| Instalador Windows 11 x64 (Inno Setup 6.7.3) | sim — `installer/ayescreva.iss` | sim — `AYEscreva-0.2.0-teste-windows11-x64.exe` | sim — §3 |
| Site oficial (prévia local) | sim — `site/`, `tools/gerar-site.mjs` | sim — `out/site` | sim, localmente — §10; **não publicado** |
| Acessibilidade com leitores de tela | — | — | **não validado** (§12) |

## 2. Aceite da Etapa 1 — `tests/uno/aceite_etapa1.py`: **40/40**

Documento criado pelo motor com 5 páginas: título em Título 1, negrito, itálico, sublinhado, tachado, sobrescrito,
cor + 14 pt, realce, fonte diferente, parágrafo centralizado, texto justificado, quebra de página, tabela 4×3,
imagem embutida com texto alternativo, cabeçalho e rodapé com número de página. Salvo em ODT e DOCX, fechado,
reaberto e conferido item a item; exportado para PDF (mesmo número de páginas) e PDF/UA marcado (`/StructTreeRoot`).
O mesmo teste roda com o motor **instalado** pelo instalador (§3).

| Verificação | ODT | DOCX |
|---|---|---|
| Páginas iguais ao original (5) | OK | OK |
| Texto completo e acentuação | OK | OK |
| Estilo Título 1 | OK | OK |
| Negrito, itálico, sublinhado, tachado, sobrescrito | OK | OK |
| Cor e tamanho, fonte do trecho | OK | OK |
| Realce | OK (fundo de caractere) | OK (realce do Word) |
| Alinhamento centralizado | OK | OK |
| Tabela 4×3 com conteúdo | OK | OK |
| Imagem embutida, tamanho e texto alternativo | OK | OK |
| Cabeçalho; rodapé com número de página | OK | OK |
| PDF com o mesmo número de páginas; PDF/UA marcado | OK | OK |

## 3. Instalador e instalação — `tests/instalacao/testar_instalacao.ps1`: **18/18**

Arquivo: `out\instalador\AYEscreva-0.2.0-teste-windows11-x64.exe` · 208 MB (217.994.462 bytes) · SHA-256 `d2ba364d4fac8f6d24bf4308c02937abffa681be2222ad4f27d89051d58636e6` · **sem assinatura digital**.

| Verificação | Resultado |
|---|---|
| SHA-256 do instalador confere com o arquivo .sha256 | OK — d2ba364d4fac8f6d24bf4308c02937abffa681be2222ad4f27d89051d58636e6 |
| assinatura digital do instalador (esperado: sem assinatura nesta versão) | OK — NotSigned |
| instalador terminou com código 0 | OK — código 0, 74 s |
| programa instalado em %LOCALAPPDATA%\Programs\AY ESCREVA | OK |
| motor instalado | OK |
| tamanho instalado | OK — 805 MB |
| atalho no menu Iniciar | OK |
| registro de desinstalação | OK — AY ESCREVA 0.2.0 (testes) \| versão 0.2.0 |
| "Abrir com" oferece o AY ESCREVA para .docx | OK |
| janela principal aberta pelo lançador instalado | OK — Sem título 1 — AY ESCREVA Writer |
| aceite (criar, formatar, tabela, imagem, salvar, fechar, reabrir, PDF) com o motor instalado | OK — Aceite da Etapa 1: 40/40 (saída em tests/output/instalacao/aceite-motor-instalado.txt) |
| pasta do programa removida | OK |
| atalho removido | OK |
| registro de desinstalação removido | OK |
| entrada "Abrir com" removida | OK |
| perfil do usuário preservado (%APPDATA%\AYEscreva) | OK |
| outras instalações do LibreOffice e associações de arquivo intactas | OK — perfil, registro (HKCU/HKLM) e associações iguais antes × depois |
| perfil do LibreOffice idêntico, arquivo por arquivo (SHA-256) — perfil simulado, sem LibreOffice nesta máquina | OK — 2 arquivo(s) conferido(s); alterados/removidos: 0; novos: 0 |

O teste roda instalação e desinstalação silenciosas, por usuário (sem administrador). Como não há LibreOffice
nesta máquina, ele cria um perfil simulado em `%APPDATA%\LibreOffice` antes de instalar, confere por SHA-256
que nenhum arquivo dele mudou depois de instalar, abrir, usar e desinstalar o AY, e o remove no fim. As
associações de arquivo escolhidas pelo usuário (`UserChoice`) também são comparadas antes × depois. O AY só se
oferece em "Abrir com" e não toma para si a associação padrão.

## 4. Testes pela interface — `tests/interface/testar_faixa.ps1`

Rodam **dentro do aplicativo**, com a faixa AY na tela, usando o UITest do próprio motor (o mesmo mecanismo dos
testes de interface do LibreOffice), numa extensão de testes instalada só em perfis descartáveis. Cada botão é
clicado na faixa; o teste confere qual comando o botão disparou e, nas funções principais, o efeito no documento.
Diálogos e listas abertos pelos botões são registrados e fechados.

| Medida | Resultado |
|---|---|
| Funções com botão nas 11 abas e nas contextuais Tabela e Imagem (as testadas) | 210 |
| Botão presente na aba certa | 210/210 |
| Acionadas pelo clique (comando disparado conferido; diálogo ou lista registrado e fechado) | 148 |
| Validadas pelo efeito no documento ou na exibição | 35 |
| Efeitos conferidos (inclui abas contextuais, avisos e salvamento) | 40/40 |
| Diálogos e listas abertos pelos botões e fechados pelo teste | 45 |
| Erros do teste · quedas do motor | 0 · 0 |
| Duração | fase 1: 19:45:29–19:51:40; fase 2: 19:51:54–19:52:12; fase 3: 19:52:27–19:52:43 |

Efeitos conferidos (amostra): Negrito, Itálico, Sublinhado, Tachado, Sobrescrito, Subscrito, Aumentar fonte, Diminuir fonte, Limpar formatação, Centralizar, Alinhar à direita, Justificar, Alinhar à esquerda, Aumentar recuo, Diminuir recuo, Marcadores, Numeração, Marcas de formatação, Quebra de página, Página em branco, Comentário, Nota de rodapé, Nota de fim, Controlar alterações, Régua, Página inteira, 100%, Largura da página, Guia de utilização do AY, Atalhos de teclado, Limitações conhecidas, Recuperação de documentos, Relatório de diagnóstico, Aba contextual Tabela, Inserir linha abaixo, Aba contextual Imagem, Salvar, Aviso de substituição de fontes, Aviso de perdas ao salvar em DOCX, Aviso de formato ao fechar e salvar DOCX. As 62 funções não acionadas genericamente ficam de fora de propósito (fechar, abrir, salvar como, recortar/colar, tela inteira, mala direta, aceitar/rejeitar tudo etc.) ou são listas suspensas; elas aparecem como "não validado" na matriz.

Fases: (1) documento ODT de trabalho — botões das 11 abas, abas contextuais Tabela e Imagem e Salvar em ODT;
(2) DOCX representativo aberto na inicialização — aviso de fontes e aviso de perdas ao salvar em DOCX pela faixa;
(3) outro DOCX alterado, fechado pela faixa com "Salvar" na pergunta.

Limites deste teste: as abas contextuais **Forma** e **Visualizar impressão** foram conferidas só visualmente
(capturas em `tests/output/interface/abas/`), sem clique automatizado. Nos comandos de Ajuda que abrem uma página
no navegador do sistema (guia, atalhos, limitações, recuperação), o teste confere que o arquivo existe e que o
comando o abriria, mas simula a abertura para não abrir janelas fora do aplicativo. Quando um botão abre outra
janela de documento (ex.: Ajuda › Créditos), o teste registra a janela, fecha-a e volta ao documento de teste.

## 5. Avisos de perdas e de fontes (extensão AY)

| Situação | Comportamento | Validado |
|---|---|---|
| Salvar um documento DOCX/DOC/RTF/TXT | diálogo "Salvar em DOCX: possíveis perdas" com a lista do que pode se perder **neste** documento; opções: salvar no formato, salvar em ODT, cancelar; caixa "guardar também uma cópia completa em ODT" marcada | pelo botão da faixa: DOCX gravado e cópia ODT criada. Atalho Ctrl+S e menu passam pelo mesmo interceptador do quadro, mas não foram testados |
| Fechar um documento alterado e escolher "Salvar" | mesmo diálogo; depois de salvar, a janela fecha (o AY informa o resultado ao motor) | pela interface: DOCX gravado, cópia ODT, janela fechada |
| Salvar como / Salvar uma cópia em formato não nativo | seletor de arquivo do AY e o mesmo diálogo de perdas | código implementado; **não** exercitado pelo teste da interface (seletor de arquivo) |
| Abrir documento com fonte não instalada | barra de informação "Fontes substituídas" com a lista e botão Detalhes | pela interface |
| Já confirmou o formato neste documento | não pergunta de novo até fechar o documento | código implementado |

Quando não há perda específica conhecida, o diálogo aparece assim mesmo, dizendo que nenhuma perda específica foi
encontrada mas que recursos sem equivalente podem ser convertidos. Não há promessa de compatibilidade total.

## 6. Impressão — `tests/uno/impressao.py`: **4/4**

Impressão real pela fila do Windows na impressora virtual "Microsoft Print to PDF" (o teste aborta antes de
imprimir se essa impressora não estiver selecionada, para nunca usar uma impressora física): arquivo gerado, é PDF,
5 páginas impressas = 5 páginas do documento.

## 7. Segurança — `tests/uno/seguranca.py`: **4/4**

| Verificação | Resultado |
|---|---|
| Controle positivo: macro executa quando forçada pela API (prova que o teste detecta execução) | OK |
| Macro Basic no evento "ao abrir" **não** executa na abertura normal | OK |
| … nem aprovando confirmações (`USE_CONFIG_APPROVE_CONFIRMATION`) | OK |
| DOCX com imagem vinculada a servidor HTTP local: **0** requisições ao abrir e exportar PDF | OK |
| (informativo) pedido explícito de "atualizar vínculos": também 0 requisições | bloqueio total hoje; não há como autorizar por documento |

## 8. Comandos da matriz — `tests/uno/comandos.py`: **233/233**

239 funções mapeadas nas 11 abas + 4 contextuais; 233 têm comando e **todos** foram encontrados no motor em
execução (despachante do quadro do Writer, controlador de menu ou extensão AY); os comandos da visualização de
impressão são conferidos com o documento nessa vista. 6 funções não têm comando e ficam fora da faixa:
marca-texto, borracha, pressão da caneta, revisão gramatical avançada offline, modo de leitura e verificar
atualizações. A matriz completa, com as colunas **comando encontrado / funcionalidade implementada /
funcionamento validado**, está em [MATRIZ-FUNCIONALIDADES.md](MATRIZ-FUNCIONALIDADES.md).

## 9. Investigação: queda do motor com a faixa por abas

Antes de mudar a interface, a falha dos testes com a faixa por abas foi investigada (`tests/investigacao/`).

| Cenário | Resultado |
|---|---|
| Cada combinação isolada (barra clássica × faixa; sem tela × com tela; documento novo, ODT, DOCX, com macro; nível de macro 3 e 4), na base pura 26.8.1 e no AY | 16/16 sem queda (`tests/output/investigacao-notebookbar.json`) |
| Sequência criar documento com macro → salvar → fechar → abrir em quadro visível, **controlada por UNO de outro processo**, com a faixa por abas | cai no 2º passo, na base pura **e** no AY, com e sem modo sem tela: `KERNELBASE.dll`, exceção 0x0, deslocamento `0xc408a`, "Binary URP bridge disposed" |
| A mesma sequência com a barra clássica | 10 passos sem queda |
| Uso só pela interface (abrir pelo lançador, fechar pelo X), 4 tipos de documento | 20 aberturas/fechamentos, sem queda |
| Testes da faixa rodando **dentro** do aplicativo (§4) | sem queda nas três fases |

Conclusão: é uma falha do motor 26.8.1 com automação UNO **externa** e a faixa por abas na tela, não da camada AY.
Os testes com UNO externo continuam com a barra clássica em perfil descartável (o que não comprova a faixa); a
faixa é comprovada pelos testes de dentro do aplicativo. A limitação está documentada em Ajuda › Limitações.

## 10. Site oficial — prévia local e fluxo de download

Prévia gerada por `tools/gerar-site.mjs --modo local` e servida em `http://127.0.0.1:8737/`; conferida no navegador
(desktop e 375 px de largura, sem rolagem horizontal). Teste automático `tests/site/testar_fluxo.ps1`:
**21/22**. A única verificação que falha é a de HTTPS, que não se aplica à prévia local.

| Verificação | Resultado |
|---|---|
| página inicial responde | OK — HTTP 200 |
| endereço usa HTTPS (exigido na publicação; a prévia local usa HTTP) | FALHA — http |
| botão "Baixar gratuitamente" na página inicial | OK — baixar.html |
| página Baixar responde | OK — http://127.0.0.1:8737/baixar.html |
| botão principal de download na página Baixar | OK — downloads/0.2.0/AYEscreva-0.2.0-teste-windows11-x64.exe |
| SHA-256 publicado na página Baixar | OK — d2ba364d4fac8f6d24bf4308c02937abffa681be2222ad4f27d89051d58636e6 |
| link para o SHA256SUMS da versão | OK |
| aviso de instalador sem assinatura digital na página Baixar | OK |
| plataforma windows11-x64 disponível com botão de download | OK |
| plataforma windows10-x64 em desenvolvimento, sem botão de download | OK |
| plataforma windows-arm64 em desenvolvimento, sem botão de download | OK |
| plataforma macos em desenvolvimento, sem botão de download | OK |
| plataforma linux em desenvolvimento, sem botão de download | OK |
| páginas internas visitadas | OK — 9 páginas |
| download responde: AYEscreva-0.2.0-teste-windows11-x64.exe | OK — HTTP 200, 217994462 bytes (em http://127.0.0.1:8737/baixar.html) |
| download responde: SHA256SUMS.txt | OK — HTTP 200, 106 bytes (em http://127.0.0.1:8737/baixar.html) |
| instalador baixado pelo botão principal | OK — AYEscreva-0.2.0-teste-windows11-x64.exe — 207,9 MB em 1 s |
| nome do arquivo identifica a versão de testes para Windows 11 x64 | OK — AYEscreva-0.2.0-teste-windows11-x64.exe |
| SHA-256 do arquivo baixado = SHA-256 da página | OK — d2ba364d4fac8f6d24bf4308c02937abffa681be2222ad4f27d89051d58636e6 |
| SHA-256 do arquivo baixado = SHA256SUMS da versão | OK — d2ba364d4fac8f6d24bf4308c02937abffa681be2222ad4f27d89051d58636e6  AYEscreva-0.2.0-teste-windows11-x64.exe |
| assinatura digital (esperado nesta versão: sem assinatura, como a página avisa) | OK — NotSigned |
| instalação, abertura, uso e desinstalação do arquivo baixado | OK — 17/17 verificações do teste de instalação |

Publicação: `scripts/publicar-site.ps1` simulado sem enviar nada (gera `out/site-publicacao` com os links do
GitHub Releases). **O site não foi publicado**: falta a autorização para criar o repositório público e publicar.

## 11. Documentos representativos — ida e volta

Entrada principal: `tests/fixtures/compatibilidade-ooxml.docx`, escrito diretamente em OOXML por
`tests/fixtures/gerar_docx.py` (não pelo motor). Contém 3 seções (retrato com primeira página diferente; paisagem
com 2 colunas; retrato com numeração reiniciada), cabeçalhos/rodapés com PAGE e NUMPAGES, 2 notas de rodapé, 1 nota
de fim, 1 comentário, 3 alterações controladas (inserção, exclusão, formatação), sumário, indicador e referência
cruzada, hiperlink externo, listas numeradas e com marcadores, tabela com mesclagem horizontal/vertical e
cabeçalho repetido, imagem com texto alternativo, caixa de texto, equação OMML, fonte inexistente e Calibri.
O Word abriu o arquivo sem reparos e contou: 4 páginas, 3 seções, 1 tabela, 3 notas, 1 comentário, 3 revisões.
Variantes salvas pelo próprio Word: DOCX, DOC, RTF, ODT e PDF de referência.

### 11.1 Estrutura (inventário antes × depois de salvar e reabrir no AY)

| Entrada | → DOCX | → ODT | → formato original |
|---|---|---|---|
| DOCX escrito à mão | só a contagem de campos de página muda (4→6: rodapé da 1ª página duplicado) | idêntico | — |
| DOCX salvo pelo Word | idem | idêntico | — |
| DOC salvo pelo Word | nomes de estilos de página, quadro→forma, seções de texto 1→2 | idêntico | DOC: idêntico |
| RTF salvo pelo Word | campos, páginas 6→5, quadro | idêntico | RTF: **perde 1 quebra de seção e o nível de tópico dos 4 títulos** |
| ODT salvo pelo Word | estilos de página, páginas 6→5, quebras de página, seções | idêntico | — |

Em **todas** as rodadas: nenhuma palavra perdida ou acrescentada; notas, comentário, tabela, hiperlink, indicador,
sumário e cabeçalhos preservados; alterações controladas preservadas com autor (exceto no ODT gerado pelo Word,
que já chega sem elas — comportamento do Word ao exportar ODT).

### 11.2 Visual (PDF do original × PDF da cópia reaberta, 60 dpi, % de pixels diferentes)

| Rodada | Páginas | Maior diferença | Média |
|---|---|---|---|
| DOCX → DOCX | 4 = 4 | 0,27 % | 0,07 % |
| DOCX → ODT | 4 = 4 | 0 % | 0 % |
| DOCX (Word) → DOCX | 4 = 4 | 0,26 % | 0,07 % |
| DOC → DOC | 4 = 4 | 0,01 % | 0,00 % |
| DOC → DOCX | 4 = 4 | 2,39 % | 0,86 % |
| DOC → ODT | 4 = 4 | 0,97 % | 0,24 % |
| RTF → DOCX | 5 → 4 | 0,18 % | 0,07 % |
| RTF → ODT | 5 = 5 | 0 % | 0 % |
| RTF → RTF | 5 = 5 | 4,50 % | 1,78 % |
| ODT (Word) → DOCX | 5 → 4 | 8,63 % | 3,69 % |
| ODT (Word) → ODT | 5 = 5 | 0 % | 0 % |
| **Word × AY** (mesmo DOCX, motores diferentes) | 4 = 4 | 6,45 % | 4,02 % |

Imagens lado a lado (original | cópia | diferença) em `tests/output/visual/*.png`.

### 11.3 Incompatibilidades encontradas

| # | Situação | Efeito | Origem | Encaminhamento |
|---|---|---|---|---|
| I1 | Seção que reinicia a numeração em 1 cai em página par | O motor insere uma página em branco automática: o campo NUMPAGES mostra "de 5" num documento que o Word mostra com 4 páginas; o PDF exportado tem 4 páginas; a impressão pode incluir a página em branco | comportamento do motor ([Ask LibreOffice](https://ask.libreoffice.org/t/writer-page-numbering-is-wrong-one-number-up/81691), [tdf#126284](https://libreoffice.org/get-help/bug/show_activity.cgi?id=126284)) | correção em C++ no Nível 2 (opção de compatibilidade para documentos Word) e proposta ao upstream |
| I2 | Salvar em RTF | Perde quebra de seção com mudança de orientação e o nível de tópico dos títulos (sumário deixa de atualizar) | filtro de exportação RTF | **aviso implementado** (§5) ao salvar em RTF, com opção de ODT; RTF fica "suporte básico" |
| I3 | ODT → DOCX com seção em paisagem de 2 colunas | Refluxo das colunas e uma página a menos | exportação DOCX de seções/colunas | listado no aviso de perdas ao salvar em DOCX; investigar com mais amostras |
| I4 | DOC → DOCX | Quadro vira forma, uma seção de texto a mais; 2,4 % de diferença visual | conversão entre modelos de seção | aceitável; monitorar |
| I5 | Fonte ausente no sistema | Substituída por fonte parecida | comportamento padrão do motor | **aviso implementado** ao abrir (§5); o nome original é mantido no arquivo |
| I6 | Word × AY, mesmo DOCX | Mesmo número de páginas e conteúdo; quebras de linha, fonte da equação e cores de revisão diferem; 4 % em média | motores de layout diferentes | esperado; não prometer igualdade de pixels com o Word |
| I7 | Comentários no PDF | O PDF do AY não mostra comentários por padrão (o do Word mostra em linha) | opção de exportação | expor a opção "comentários na margem" no Exportar PDF |

## 12. O que **não** foi validado (limites declarados)

- Somente **Windows 11 x64** nesta máquina. Windows 10 não testado (o instalador exige Windows 11).
- Windows ARM64, x86 32 bits, macOS e Linux: não montados nem testados.
- **Leitores de tela** (NVDA, Narrador, JAWS), navegação só por teclado na faixa e escalas de 125–200 %: não
  testados. A árvore de acessibilidade (MSAA) da janela foi lida por script, mas a ponte de acessibilidade do
  motor só nasce quando um leitor de tela a pede, e a leitura externa variou entre execuções; falta o teste com
  NVDA e Narrador.
- Os controles do diálogo de perdas do AY não aparecem por nome para o UITest (o teste usa Enter real); a leitura
  desse diálogo por leitor de tela não foi conferida.
- Salvar como e Salvar uma cópia com o diálogo de perdas do AY: código implementado, sem teste automatizado pela
  interface (o teste não opera o seletor de arquivo).
- Instalador sem assinatura de código: o SmartScreen pode avisar "editor desconhecido".
- Recuperação após falha, salvamento seguro com falha simulada e desfazer/refazer: sem teste automatizado ainda.
- Teste de imagem remota cobre só o filtro DOCX e imagem vinculada; outros tipos de recurso externo (OLE/DDE,
  fontes remotas, modelos remotos) não foram testados.
- Máquina sem Microsoft Office (para ver a substituição de Calibri por Carlito): não testada.
- Site: testado só na prévia local (HTTP em 127.0.0.1); HTTPS e o download pelo GitHub Releases só poderão ser
  testados depois da publicação.
