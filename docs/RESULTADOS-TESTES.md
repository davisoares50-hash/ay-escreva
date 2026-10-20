# Resultados dos testes — versão 0.3.0 (versão de testes local, em avaliação) · versão pública: 0.2.0

Execução da 0.3.0: 20/10/2026 · `scripts/testar.ps1` + `tests/interface/testar_faixa.ps1` (7 fases) +
`tests/instalacao/testar_instalacao.ps1`. As seções 2–4 e 6–11 valem para as duas versões, salvo indicação; a
publicação (§10) e o fluxo do site referem-se à 0.2.0, a versão pública.
Ambiente: Windows 11 Pro 10.0.26200 x64, Intel Core i5-8500, 16 GB · Motor: LibreOffice 26.8.1.1 (binários oficiais)
Oráculo independente: Microsoft Word 16.0 (instalado na máquina, usado só via automação COM com macros desativadas)

## 1. O que está implementado, compilado e validado

| Componente | Código implementado | Compilação/montagem executada | Funcionamento validado |
|---|---|---|---|
| Obtenção da base (SHA-256, PGP, Authenticode) | sim — `scripts/montar.ps1` | sim | sim: assinatura PGP da chave `C2839ECA…AFEEAEA3` e Authenticode "The Document Foundation" válidas |
| Distribuição AY (poda de idiomas, fontes privadas, runtime VC++) | sim | sim — 797 MB | sim: o motor inicia e edita (testes abaixo) |
| Camada de configuração `ayescreva.xcd` | sim | sim | sim: título "AY ESCREVA", realce→`w:highlight`, faixa AY padrão, segurança de macros |
| Identidade visual | sim — `tools/marca.mjs` | sim | parcial: ícone do lançador, tela de abertura e instalador conferidos; ícone da janela ainda é o da base |
| Lançador `AYEscreva.exe` (0.3.0) | sim — C# | sim — csc do .NET Framework 4.8.1 | sim: abre o aplicativo instalado com perfil próprio |
| Faixa de opções AY (`notebookbar_ayescreva.ui`, 11 abas + 4 contextuais) | sim — `tools/gerar-faixa.mjs` a partir de `ui/abas.json` | sim — 227 botões | sim — §4 (Forma e Visualizar impressão: só conferência visual) |
| Extensão AY (comandos `ayescreva:`, avisos de perdas e de fontes) | sim — `extensao/ayescreva` | sim — empacotada na distribuição | sim — §4 e §5 |
| Instalador Windows 11 x64 (Inno Setup 6.7.3) | sim — `installer/ayescreva.iss` | sim — 0.2.0 (pública) e 0.3.0 (local) | sim — §3 |
| Revisão de texto: correção automática de casos inequívocos, gramática e pontuação, estilo opcional (0.3.0) | sim — `extensao/ayescreva/pythonpath/`, `dados/correcoes_pt_BR.json` | sim | sim — §5.1 |
| Painel lateral "Assistente AY" e grupo na aba Revisão (0.3.0) | sim — `ay_painel.py`, `Painel.xdl`, `Sidebar.xcu` | sim | sim — §5.1 (acessibilidade só pela API; leitores de tela não testados) |
| Confiabilidade: recuperação, salvamento seguro, desfazer/refazer, TXT (0.3.0) | sim — testes `tests/uno/confiabilidade.py`, `recuperacao.py` | — | sim — §5.2 (comportamento do motor, agora com teste) |
| IA local (entrega C) | **não** | — | — |
| Site oficial | sim — `site/`, `tools/gerar-site.mjs` | sim — publicado em https://davisoares50-hash.github.io/ay-escreva/ | sim — fluxo público 25/25, com HTTPS (§10) |
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

## 3. Instalador e instalação — `tests/instalacao/testar_instalacao.ps1`

**0.3.0 (local, 20/10/2026): 19/19** — `out\instalador\AYEscreva-0.3.0-teste-windows11-x64.exe` · 208 MB (218.325.835 bytes) ·
SHA-256 `e280a9139a39d3592b126738607273d6fb613a1fa7a9fa5b17db52f3c0449d5b` · sem assinatura digital. Mesmas verificações da 0.2.0, mais: a extensão instalada traz a revisão
de texto e o painel Assistente AY (versão da extensão 0.3.0).

**0.2.0 (pública): 18/18** — Arquivo: `out\instalador\AYEscreva-0.2.0-teste-windows11-x64.exe` · 208 MB (217.994.462 bytes) · SHA-256 `d2ba364d4fac8f6d24bf4308c02937abffa681be2222ad4f27d89051d58636e6` · **sem assinatura digital**.

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
| Funções com botão nas 11 abas e nas contextuais Tabela e Imagem (as testadas) | 213 |
| Botão presente na aba certa | 213/213 |
| Acionadas pelo clique (comando disparado conferido; diálogo ou lista registrado e fechado) | 151 |
| Validadas pelo efeito no documento ou na exibição | 35 |
| Efeitos conferidos nas 7 fases (inclui abas contextuais, avisos, salvamento e revisão de texto) | 73/73 |
| Diálogos e listas abertos pelos botões e fechados pelo teste | 47 |
| Erros do teste · quedas do motor · conexões de rede para fora do computador | 0 · 0 · 0 |
| Duração | fase 1: 13:29:00–13:35:25; fase 2: 13:35:39–13:35:57; fase 3: 13:36:12–13:36:28; fase 4: 13:36:41–13:37:02; fase 5: 13:37:14–13:39:03; fase 6: 13:39:15–13:47:27; fase 7: 13:47:43–13:47:59 (0.3.0, 20/10/2026) |

Efeitos conferidos (amostra): Negrito, Itálico, Sublinhado, Tachado, Sobrescrito, Subscrito, Aumentar fonte, Diminuir fonte, Limpar formatação, Centralizar, Alinhar à direita, Justificar, Alinhar à esquerda, Aumentar recuo, Diminuir recuo, Marcadores, Numeração, Marcas de formatação, Quebra de página, Página em branco, Comentário, Nota de rodapé, Nota de fim, Controlar alterações, Régua, Página inteira, 100%, Largura da página, Guia de utilização do AY, Atalhos de teclado, Limitações conhecidas, Recuperação de documentos, Relatório de diagnóstico, Aba contextual Tabela, Inserir linha abaixo, Aba contextual Imagem, Salvar, Aviso de substituição de fontes, Aviso de perdas ao salvar em DOCX, Aviso de formato ao fechar e salvar DOCX. As 62 funções não acionadas genericamente ficam de fora de propósito (fechar, abrir, salvar como, recortar/colar, tela inteira, mala direta, aceitar/rejeitar tudo etc.) ou são listas suspensas; elas aparecem como "não validado" na matriz.

Fases: (1) documento ODT de trabalho — botões das 11 abas, abas contextuais Tabela e Imagem e Salvar em ODT;
(2) DOCX representativo aberto na inicialização — aviso de fontes e aviso de perdas ao salvar em DOCX pela faixa;
(3) outro DOCX alterado, fechado pela faixa com "Salvar" na pergunta; (4) Salvar como DOCX pelo seletor de arquivo do
AY; (5) revisão de texto (digitação real, desfazer, proteções, painel, largura do painel na barra lateral e captura
de tela em `tests/output/interface/painel-assistente.png`); (6) documento longo (3.000 parágrafos); (7) integridade
de DOCX/ODT depois de correções com controle de alterações. Todas as fases são de uma única execução, feita depois
da correção da largura do painel.

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

## 5.1 Revisão de texto e Assistente AY (0.3.0, entrega A)

Regras sem o aplicativo — `tests/revisao/testar_regras.py`: **31/31** (decisão da correção automática com cada
proteção, conteúdo da tabela de casos inequívocos e regras de estilo).

| Verificação | Resultado |
|---|---|
| tabela carregada, com origem e critérios registrados | OK — 88589 correções; {'digitação': 762, 'acentuação': 271, 'acentuação (dicionário)': 87556} |
| tabela só tem palavras simples em minúsculas (sem abreviações, símbolos ou várias palavras) | OK |
| abreviações e palavras válidas ficam fora da tabela (vc, tbm, pq, so, ate, e, esta, musica, agua) | OK |
| correção: acentuação no meio da frase ("nao" → 'não') | OK — 'não' (tabela de casos inequívocos) |
| correção: acentuação ("voce" → 'você') | OK — 'você' (tabela de casos inequívocos) |
| correção: acentuação vinda do dicionário ("tambem" → 'também') | OK — 'também' (tabela de casos inequívocos) |
| correção: erro de digitação inequívoco ("geito" → 'jeito') | OK — 'jeito' (tabela de casos inequívocos) |
| correção: início de frase mantém a maiúscula ("Nao" → 'Não') | OK — 'Não' (tabela de casos inequívocos) |
| correção: maiúscula no meio da frase = nome próprio ("Nao" → None) | OK — None (maiúscula no meio da frase (nome próprio)) |
| correção: sigla ("NAO" → None) | OK — None (sigla) |
| correção: grafia mista (termo técnico ou marca) ("naO" → None) | OK — None (grafia com maiúsculas no meio (termo técnico ou marca)) |
| correção: com dígito ("nao2" → None) | OK — None (tem dígito, símbolo ou pontuação (número, data, termo técnico, endereço)) |
| correção: data ("12/10/2025" → None) | OK — None (tem dígito, símbolo ou pontuação (número, data, termo técnico, endereço)) |
| correção: número ("3,5" → None) | OK — None (tem dígito, símbolo ou pontuação (número, data, termo técnico, endereço)) |
| correção: dentro de citação (aspas curvas) ("nao" → None) | OK — None (dentro de citação) |
| correção: dentro de citação (aspas retas) ("nao" → None) | OK — None (dentro de citação) |
| correção: depois de uma citação fechada volta a corrigir ("nao" → 'não') | OK — 'não' (tabela de casos inequívocos) |
| correção: texto marcado em outro idioma ("nao" → None) | OK — None (texto em outro idioma) |
| correção: "não corrigir novamente" ("nao" → None) | OK — None (marcada "não corrigir novamente") |
| correção: palavra do dicionário pessoal ("geito" → None) | OK — None (palavra aceita pelo dicionário (inclui o dicionário pessoal)) |
| correção: estilo de citação ou código ("nao" → None) | OK — None (estilo de citação, código ou texto pré-formatado) |
| correção: palavra correta não muda ("casa" → None) | OK — None (sem correção inequívoca) |
| correção: palavra válida ambígua (esta/está) não muda ("esta" → None) | OK — None (sem correção inequívoca) |
| estilo: formalidade ("pra", "né") | OK |
| estilo: concisão ("a fim de que", "devido ao fato de que") | OK |
| estilo: "a fim de que" não gera também "a fim de" no mesmo trecho | OK |
| estilo: repetição próxima ("análise") | OK |
| estilo: toda sugestão tem explicação | OK |
| estilo: frase com mais de 40 palavras | OK |
| estilo: texto limpo sem sugestões | OK |
| estilo: "para" e "propor" não confundem com "pra"/"pro" | OK |

Pela interface, de dentro do aplicativo (fases 5 a 7 de `tests/interface/testar_faixa.ps1`): **31/31**.
A digitação usa o robô do toolkit (o mesmo caminho do teclado); os botões do painel são acionados com Espaço
depois de receberem o foco, como alguém que usa só o teclado. Fases: 5 (13:37:14–13:39:03), 6 (13:39:15–13:47:27), 7 (13:47:43–13:47:59).

| Verificação | Resultado |
|---|---|
| Correção automática ao digitar (nao, voce, tambem) | OK — 'Eu não sei se você vem também. ' |
| Cursor preservado: o texto seguinte entra depois da palavra corrigida | OK — 'e você vem também. X' |
| Digitação rápida: todas as palavras corrigidas, nenhuma letra perdida | OK — 'não você também jeito ' |
| Nada muda enquanto a palavra ainda está sendo digitada | OK — 'naoo' |
| Ctrl+Z desfaz só a correção (o espaço digitado fica) | OK — 'Ele disse não ' → 'Ele disse nao ' |
| Ao desfazer, o AY oferece "Não corrigir novamente" (barra de informação) | OK |
| "Não corrigir novamente" fica gravado e é respeitado | OK — 'Outra vez nao ' |
| Removida da lista, a palavra volta a ser corrigida | OK — 'De novo não ' |
| Proteções: nome próprio, sigla, grafia mista, data, palavra com número e citação não mudam | OK — 'Ontem o Voce, a NAO e o naO viram 12/10/2025 e nao2; ele disse “nao sei” e saiu. ' |
| Texto marcado em inglês não é corrigido | OK — 'I said nao ' |
| Palavra do dicionário pessoal não é corrigida | OK — 'Tem geito ' |
| Correção automática pode ser desligada | OK — 'Sem correcao nao ' |
| Painel Assistente AY abre pela aba Revisão (comando "Assistente AY") | OK |
| Acessibilidade: listas anunciadas pelo próprio rótulo (não pelo título do painel) | OK — ocorrencias="Ocorrências encontradas:"; sugestoes="Sugestão:"; recentes="Correções automáticas recentes:" |
| Acessibilidade: controles do painel com nome acessível | OK — sem nome: nenhum \| verificar_documento="Verificar documento" papel=44 desc=""; estilo="Estilo: clareza, concisão, formalidade, repetição" papel=4 desc=""; ocorrencias="Ocorrências encontradas:" papel=40 desc=""; sugestoe |
| Verificar documento pelo teclado: erro de ortografia listado com sugestões | OK — {'cancelado': False, 'achados': 16, 'paragrafos': 58, 'segundos': 7.16}; sugestões: ['palavras', 'palavrasse', 'palavrais'] |
| Gramática e pontuação: ocorrências com explicação curta | OK — “não”: Iniciar com maiúscula?; “naoo”: Iniciar com maiúscula? |
| Estilo desligado por padrão: nenhuma sugestão de estilo | OK — 0 sugestão(ões) de estilo |
| Estilo ligado pelo teclado: concisão, formalidade e pleonasmo sugeridos | OK — Estilo · repetição: “trecho”; Estilo · repetição: “trecho”; Estilo · repetição: “trecho”; Estilo · repetição: “trecho”; Estilo · repetição: “trecho”; Estilo · repetição: “trecho” |
| Aplicar troca o trecho pela sugestão no documento | OK — sugestão 'palavras' |
| Desfazer volta o texto original | OK |
| Ignorar tira a palavra das verificações seguintes | OK |
| Adicionar ao dicionário pessoal grava a palavra e ela deixa de ser apontada | OK |
| Painel cabe na largura visível da barra lateral (nenhum botão cortado) | OK — janela 275 px, área visível 275 px |
| Digitar durante a verificação: o texto entra e é corrigido | OK — 'itação. Não ' |
| Cancelar interrompe a verificação | OK — {'cancelado': True, 'achados': 31, 'paragrafos': 61, 'segundos': 8.75}; 1.19 s até parar |
| Interface responde durante a verificação (atraso médio < 0,2 s e 95% < 0,4 s) | OK — durante: média 0.069 s, 95% até 0.167 s, pior 0.167 s (18 medições) \| sem verificação: média 0.014 s, 95% até 0.038 s, pior 0.047 s (25 medições) |
| Documento longo verificado por completo | OK — {'cancelado': False, 'achados': 1500, 'paragrafos': 3000, 'segundos': 461.34}; memória do processo 406 → 601 MB (pico 601 MB) |
| Com controle de alterações ligado, a correção fica registrada como alteração | OK — 3 → 4 alterações; 'Texto controlado: não ' |
| DOCX com tabela, imagem, notas, comentário e alterações salvo e reaberto íntegro depois das correções | OK — antes {'tabelas': 1, 'imagens': 1, 'notas': 2, 'notas_fim': 1, 'comentarios': 1, 'alteracoes': 4} \| reaberto {'tabelas': 1, 'imagens': 1, 'notas': 2, 'notas_fim': 1, 'comentarios': 1, 'alteracoes': 4} |
| ODT com tabela, imagem, notas, comentário e alterações salvo e reaberto íntegro depois das correções | OK — antes {'tabelas': 1, 'imagens': 1, 'notas': 2, 'notas_fim': 1, 'comentarios': 1, 'alteracoes': 4} \| reaberto {'tabelas': 1, 'imagens': 1, 'notas': 2, 'notas_fim': 1, 'comentarios': 1, 'alteracoes': 4} |

Documento longo (3.000 parágrafos, ~90 mil palavras): 3000 parágrafos em 461.34 s, 1500 ocorrências; memória do processo 406 → 601 MB (pico 601 MB); atraso da interface durante a verificação: média 0.069 s, pior 0.167 s. A gramática (Lightproof) responde por quase todo o tempo (~95 ms por parágrafo neste computador).

Sem internet: durante todas as fases da interface, nenhuma conexão TCP do motor para fora do computador (0 encontradas). Não há modelo de IA instalado nesta versão; a revisão acima não depende de nenhum.

## 5.2 Confiabilidade (0.3.0)

`tests/uno/confiabilidade.py`: **19/19**

| Verificação | Resultado |
|---|---|
| desfazer/refazer: 5 edições registradas no histórico | OK — Teste nota, Teste imagem, Teste tabela, Teste negrito, Teste texto |
| desfazer volta o documento a cada estado anterior, até o vazio | OK |
| refazer reaplica cada edição na ordem | OK — {'texto': True, 'negrito': True, 'tabelas': 1, 'imagens': 1, 'notas': 1} |
| depois de refazer, salvo em ODT e reaberto igual | OK — {'texto': True, 'negrito': True, 'tabelas': 1, 'imagens': 1, 'notas': 1} |
| depois de refazer, salvo em DOCX e reaberto igual | OK — {'texto': True, 'negrito': True, 'tabelas': 1, 'imagens': 1, 'notas': 1} |
| TXT UTF-8: bytes gravados na codificação certa | OK — 141 bytes |
| TXT UTF-8: reaberto com o mesmo texto | OK — Ação, coração, pão, você, avó, útil, ent |
| TXT Windows-1252: bytes gravados na codificação certa | OK — 109 bytes |
| TXT Windows-1252: reaberto com o mesmo texto | OK — Ação, coração, pão, você, avó, útil, ent |
| TXT Windows-1252 escrito por outro programa abre com acentos certos | OK |
| cópia de segurança: ao salvar de novo, a versão anterior fica na pasta de backup do perfil | OK — ['seguro.odt.bak'] |
| arquivo tornado somente leitura por outro processo | OK |
| salvar com o arquivo protegido falha com erro (não finge que salvou) | OK — com.sun.star.task.ErrorCodeIOException |
| o arquivo anterior fica intacto depois da falha | OK |
| o documento continua marcado como modificado (a alteração não se perde) | OK |
| depois da falha, "Salvar como" grava a alteração sem perdas | OK — Salvar no mesmo arquivo recusado (com.sun.star.task.ErrorCodeIOException) |
| o processo que grava (soffice.bin) foi encerrado de fato em todas as tentativas | OK — 3 de 4 encerramentos aconteceram com a gravação em andamento |
| salvamento interrompido à força: arquivo no disco sempre íntegro (versão anterior ou nova) | OK — 0.3 s → versão anterior; 1.0 s → versão anterior; 2.0 s → versão anterior; 3.5 s → versão nova |
| salvamento interrompido: versão anterior sempre recuperável (arquivo ou cópia de segurança) | OK |

Salvamento interrompido (processo que grava, soffice.bin, encerrado à força durante a gravação de um ODT de ~52 MB):

| Encerrado após | Gravação em andamento no encerramento | Arquivo no disco | Cópia de segurança com a versão anterior |
|---|---|---|---|
| 0.48 s | sim | versão anterior (zip íntegro) | ainda não criada |
| 1.13 s | sim | versão anterior (zip íntegro) | ainda não criada |
| 3.02 s | sim | versão anterior (zip íntegro) | sim |
| 3.61 s | não (já tinha terminado) | versão nova (zip íntegro) | sim |

Correção do próprio teste (20/10/2026): a primeira versão encerrava só o lançador `soffice.exe`; o motor
(`soffice.bin`) continuava gravando, então aquele resultado não provava a interrupção. A versão atual encerra o
`soffice.bin` no momento escolhido e confirma que ele terminou antes de examinar o arquivo.

`tests/uno/recuperacao.py` — queda com documentos não salvos e recuperação: **7/7**

| Verificação | Resultado |
|---|---|
| dois documentos alterados e não salvos | OK |
| salvamento automático gravou a recuperação dos dois documentos, com o texto não salvo | OK — 70 s; arquivos: ['existente.odt_001.odt', 'untitled_001.odt'] |
| motor encerrado à força (simulação de queda) | OK |
| lista de recuperação gravada no perfil | OK |
| ao abrir de novo, o AY oferece a recuperação | OK — Recuperação de documentos AY ESCREVA 26.8 |
| documento novo recuperado com o texto não salvo | OK — 2 documento(s) abertos |
| documento existente recuperado com a alteração não salva | OK |

Salvar como pela interface (seletor de arquivo do AY → DOCX → aviso de perdas): OK — diálogos: ['Salvar como', 'Salvar em DOCX: possíveis perdas']; DOCX gravado=True; cópia ODT=True; documento agora é o DOCX=True.

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

## 8. Comandos da matriz — `tests/uno/comandos.py`: **236/236**

241 funções mapeadas nas 11 abas + 4 contextuais; 236 têm comando e **todos** foram encontrados no motor em
execução (despachante do quadro do Writer, controlador de menu ou extensão AY); os comandos da visualização de
impressão são conferidos com o documento nessa vista. 5 funções não têm comando e ficam fora da faixa:
marca-texto, borracha, pressão da caneta, modo de leitura e verificar atualizações (a revisão gramatical offline
passou a ser feita pelo Lightproof pt-BR, ligado pelo AY). A matriz completa, com as colunas **comando encontrado / funcionalidade implementada /
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

**Achado da 0.3.0 (travamento com threads Python):** uma thread Python que edita ou lê o documento enquanto a thread
principal executa código Python (listeners da extensão AY) pode travar o motor; a interface deixa de responder.
Reproduzido de propósito num protótipo (edição logo depois de abrir o documento: a thread principal parou de
atender) e uma vez na bateria completa (fase 4, edição feita pela thread do teste). Consequências:
- no produto, nenhuma thread Python do AY toca o documento: a análise do painel só lê e marca o documento na
  thread principal; a thread de trabalho recebe apenas texto ([REVISAO-E-IA.md §4](REVISAO-E-IA.md));
- nos testes, todo acesso ao documento passou a ser feito na thread principal (`no_principal`), e o executor da
  bateria desiste de uma fase assim que o motor dela termina, em vez de esperar o tempo-limite.

## 10. Site oficial e publicação

Publicado em 20/10/2026, com autorização do responsável, só com recursos gratuitos (repositório público,
GitHub Releases e GitHub Pages; nenhum serviço pago nem cobrança ativada):

- Site: https://davisoares50-hash.github.io/ay-escreva/
- Download direto: https://github.com/davisoares50-hash/ay-escreva/releases/download/v0.2.0/AYEscreva-0.2.0-teste-windows11-x64.exe
- Versão (pré-lançamento): https://github.com/davisoares50-hash/ay-escreva/releases/tag/v0.2.0 — instalador, `SHA256SUMS.txt` e notas com SHA-256,
  instruções de instalação, limitações conhecidas, licenças e código-fonte
- Repositório: https://github.com/davisoares50-hash/ay-escreva (licença MPL-2.0 reconhecida pelo GitHub)

Antes de publicar: auditoria dos arquivos e de todo o histórico do Git (sem credenciais, sem documentos de
teste ou binários, sem dados pessoais). Os commits locais tinham nome e e-mail pessoais nos metadados e foram
regravados, antes do primeiro envio, com o usuário do GitHub e o endereço "noreply"; o mesmo vale para o commit
do site.

HTTPS: o GitHub Pages serve o site com certificado válido e `https_enforced = true`; `http://` responde 301
para `https://`. O instalador é servido pelo GitHub Releases por HTTPS, com `Content-Disposition: attachment`,
e baixa sem login.

Teste do fluxo no endereço público — `tests/site/testar_fluxo.ps1 -Site https://davisoares50-hash.github.io/ay-escreva/`: **25/25**
(acessar → "Baixar gratuitamente" → baixar sem login → conferir SHA-256 → instalar → abrir → usar → desinstalar).

| Verificação | Resultado |
|---|---|
| página inicial responde | OK — HTTP 200 |
| endereço usa HTTPS (exigido na publicação; a prévia local usa HTTP) | OK — https |
| botão "Baixar gratuitamente" na página inicial | OK — https://github.com/davisoares50-hash/ay-escreva/releases/download/v0.2.0/AYEscreva-0.2.0-teste-windows11-x64.exe |
| o botão da página inicial aponta para o instalador (download direto) | OK — https://github.com/davisoares50-hash/ay-escreva/releases/download/v0.2.0/AYEscreva-0.2.0-teste-windows11-x64.exe |
| página Baixar responde | OK — https://davisoares50-hash.github.io/ay-escreva/baixar.html |
| botão principal de download na página Baixar | OK — https://github.com/davisoares50-hash/ay-escreva/releases/download/v0.2.0/AYEscreva-0.2.0-teste-windows11-x64.exe |
| página inicial e página Baixar levam ao mesmo arquivo | OK |
| SHA-256 publicado na página Baixar | OK — d2ba364d4fac8f6d24bf4308c02937abffa681be2222ad4f27d89051d58636e6 |
| link para o SHA256SUMS da versão | OK |
| aviso de instalador sem assinatura digital na página Baixar | OK |
| plataforma windows11-x64 disponível com botão de download | OK |
| plataforma windows10-x64 em desenvolvimento, sem botão de download | OK |
| plataforma windows-arm64 em desenvolvimento, sem botão de download | OK |
| plataforma macos em desenvolvimento, sem botão de download | OK |
| plataforma linux em desenvolvimento, sem botão de download | OK |
| páginas internas visitadas | OK — 9 páginas |
| download responde: OFL.txt | OK — HTTP 200, 4473 bytes (em https://davisoares50-hash.github.io/ay-escreva/licencas.html) |
| download responde: AYEscreva-0.2.0-teste-windows11-x64.exe | OK — HTTP 200, 217994462 bytes (em https://davisoares50-hash.github.io/ay-escreva/baixar.html) |
| download responde: SHA256SUMS.txt | OK — HTTP 200, 106 bytes (em https://davisoares50-hash.github.io/ay-escreva/baixar.html) |
| instalador baixado pelo botão principal | OK — AYEscreva-0.2.0-teste-windows11-x64.exe — 207,9 MB em 22 s |
| nome do arquivo identifica a versão de testes para Windows 11 x64 | OK — AYEscreva-0.2.0-teste-windows11-x64.exe |
| SHA-256 do arquivo baixado = SHA-256 da página | OK — d2ba364d4fac8f6d24bf4308c02937abffa681be2222ad4f27d89051d58636e6 |
| SHA-256 do arquivo baixado = SHA256SUMS da versão | OK — d2ba364d4fac8f6d24bf4308c02937abffa681be2222ad4f27d89051d58636e6  AYEscreva-0.2.0-teste-windows11-x64.exe |
| assinatura digital (esperado nesta versão: sem assinatura, como a página avisa) | OK — NotSigned |
| instalação, abertura, uso e desinstalação do arquivo baixado | OK — 17/17 verificações do teste de instalação |

Antes da publicação, o mesmo teste passou na prévia local (`http://127.0.0.1:8737/`), menos a verificação de
HTTPS, que só se aplica ao site publicado. A página foi conferida no navegador em largura de computador e de
celular (375 px, sem rolagem horizontal); no celular, os botões "Baixar gratuitamente" levam à página Baixar,
porque o instalador é para Windows 11.

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
- "Salvar uma cópia" com o diálogo de perdas: usa o mesmo código de "Salvar como" (testado pela interface), mas
  não tem teste próprio.
- Instalador sem assinatura de código: o SmartScreen pode avisar "editor desconhecido".
- Painel Assistente AY: nomes acessíveis e operação por teclado conferidos pela API de acessibilidade do motor;
  a leitura do painel por NVDA ou Narrador **não** foi testada.
- Revisão de texto: o painel verifica corpo do texto e tabelas; cabeçalhos, rodapés, notas e caixas de texto
  ficam de fora da lista (o sublinhado do motor continua valendo neles). As regras de gramática e estilo podem
  apontar trechos corretos; não há medida de precisão com um corpus real de textos em pt-BR.
- Desempenho medido só neste computador (i5-8500, 16 GB): ~7,7 min para verificar 3.000 parágrafos em segundo
  plano; durante a verificação o atraso médio da interface sobe de ~14 ms para ~69 ms, e a memória do processo
  sobe até ~200 MB (406 → 601 MB nesta execução; 405 → 454 MB numa execução anterior do mesmo teste). Outros
  computadores podem ser mais lentos.
- IA local (entrega C) não está implementada nesta versão; nenhuma medida de IA foi feita ainda.
- Teste de imagem remota cobre só o filtro DOCX e imagem vinculada; outros tipos de recurso externo (OLE/DDE,
  fontes remotas, modelos remotos) não foram testados.
- Máquina sem Microsoft Office (para ver a substituição de Calibri por Carlito): não testada.
- Site: o fluxo foi testado num único computador (Windows 11), com o navegador embutido e com o PowerShell;
  não foi testado em outros navegadores nem em outras redes.
