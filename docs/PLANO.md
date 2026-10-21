# Plano de execução do AY ESCREVA

Legenda: ✅ concluído e validado · 🟡 em andamento / parcial · ⬜ não iniciado

Versão pública: **0.2.0, versão inicial de testes para Windows 11 x64** (validada somente nesse sistema). Versões de testes locais: **0.3.0** (confiabilidade + entrega A), **0.4.0** (entrega B) e **0.5.0** (entrega C, IA local opcional).

## Etapa 1 — Base técnica compilável e prova de edição real ✅

| Entrega | Situação | Evidência |
|---|---|---|
| Inspeção do ambiente e decisão de arquitetura | ✅ | [ARQUITETURA.md](ARQUITETURA.md) |
| Base fixada e verificada (SHA-256, PGP, Authenticode) | ✅ | `base/base.lock.json`, `scripts/montar.ps1` |
| Distribuição AY montada (nome, perfil próprio, segurança, pt-BR) | ✅ | `dist/AY ESCREVA` |
| Identidade visual própria | ✅ | `tools/marca.mjs`, `branding/README.md` |
| Lançador próprio compilado | ✅ | `launcher/AYEscreva.cs` → `AYEscreva.exe` |
| **Aceite**: documento de várias páginas, formatação, tabela, imagem, salvar, fechar, reabrir, PDF | ✅ 40/40 | [RESULTADOS-TESTES.md §2](RESULTADOS-TESTES.md) |
| Matriz de funcionalidades com verificação de comandos | ✅ | [MATRIZ-FUNCIONALIDADES.md](MATRIZ-FUNCIONALIDADES.md) |
| Instalador Windows 11 x64 (Inno Setup, por usuário) compilado e testado: instalar, abrir, criar/salvar/reabrir, desinstalar, sem tocar em outras instalações do LibreOffice | ✅ | `scripts/instalador.ps1`, `tests/instalacao/testar_instalacao.ps1`, [RESULTADOS §3](RESULTADOS-TESTES.md) |

## Etapa 2 — Abrir, editar, salvar, reabrir, imprimir e exportar 🟡

Já validado: ida e volta DOCX/ODT/DOC/RTF com documentos representativos (estrutura e comparação visual),
impressão real pela fila do Windows, exportação PDF e PDF/UA, macros bloqueadas, recursos remotos bloqueados.

- [x] Aviso **específico** antes de salvar em formato com perda: o AY lista as perdas possíveis no documento
      (ex.: RTF perde seções e níveis de tópico) e oferece salvar assim mesmo, salvar em ODT ou salvar e guardar
      também uma cópia completa em ODT. Vale para Salvar, Salvar como e Salvar uma cópia. Validado pela faixa
      (Arquivo › Salvar com um DOCX).
- [x] Aviso de **fontes substituídas** ao abrir (barra de informação com a lista). Validado pela interface.
- [x] Ao fechar um documento alterado e escolher "Salvar" na pergunta, aparece o mesmo aviso de perdas e a janela
      fecha depois de salvar. Validado pela interface ([RESULTADOS §5](RESULTADOS-TESTES.md)).
- [x] Salvar como com o aviso de perdas: teste pela interface (seletor de arquivo do AY → DOCX → aviso → DOCX e
      cópia ODT). "Salvar uma cópia" usa o mesmo caminho de código, sem teste próprio.
- [x] **Recuperação após falha**: queda forçada com dois documentos alterados; o salvamento automático real gravou a
      recuperação, a janela de recuperação apareceu e os dois voltaram com as alterações (`tests/uno/recuperacao.py`).
- [x] **Salvamento seguro**: cópia de segurança da versão anterior; falha de gravação (arquivo protegido) não
      altera o arquivo e não perde a alteração; o processo que grava (soffice.bin) encerrado à força 4 vezes, 3
      delas no meio da gravação de um ODT de 52 MB — o arquivo ficou sempre íntegro (`tests/uno/confiabilidade.py`).
- [x] Desfazer/refazer: 5 edições (texto, negrito, tabela, imagem, nota) desfeitas e refeitas, salvas em ODT e DOCX.
- [x] TXT: ida e volta em UTF-8 e Windows-1252, inclusive arquivo Windows-1252 escrito por outro programa.
- [ ] Ampliar o corpus: documentos reais anonimizados (ABNT, contratos, ofícios), DOCX produzidos por Word 2007,
      2010, 2016/365 e Google Docs.

## Etapa 3 — Interface por abas conectada aos comandos 🟡

- [x] `notebookbar_ayescreva.ui` gerada de `ui/abas.json` (`tools/gerar-faixa.mjs`), com as abas na ordem
      Arquivo, Página Inicial, Inserir, Desenhar, Design, Layout, Referências, Correspondência, Revisão, Exibir,
      Ajuda e as contextuais Tabela, Imagem, Forma e Visualizar impressão. Só entram botões com comando real.
- [x] Modo "AY ESCREVA" registrado em `ToolbarMode` e padrão.
- [x] Extensão AY (UNO em Python, protocolo `ayescreva:`): página em branco, recuperação de documentos, guia,
      atalhos, limitações, diagnóstico; avisos de perdas e de fontes.
- [x] Teste pela interface (de dentro do aplicativo, com o UITest do motor): presença de cada botão, acionamento,
      efeito conferido nas funções principais, abas contextuais Tabela e Imagem. Resultados em
      [RESULTADOS §4](RESULTADOS-TESTES.md). Forma e Visualizar impressão: só conferência visual por enquanto.
- [x] Investigação da queda com a faixa por abas: falha do motor 26.8.1 com automação UNO **externa**,
      reproduzida também na base pura; o uso pela interface e os testes de dentro do aplicativo não caem.
- [ ] Funções ainda sem comando (ficam fora da faixa e aparecem como "em desenvolvimento" no site): marca-texto,
      borracha, pressão da caneta, revisão gramatical avançada offline, modo de leitura, verificar atualizações.
- [ ] Recolhimento automático dos grupos em janelas estreitas (o contêiner da base recolhia tudo; hoje os grupos
      ficam fixos).
- [ ] Atalhos com paridade ao Word pt-BR (Ctrl+N negrito, Ctrl+B salvar): hoje seguem o padrão do motor
      (lista em Ajuda › Atalhos de teclado).
- [ ] Acessibilidade: NVDA e Narrador lendo abas, grupos e botões; navegação só por teclado (F6, Alt, setas);
      escalas 100/125/150/200 %; tema claro/escuro. **Não validado.**

## Etapa 4 — Recursos avançados ⬜

- [ ] Modelos AY: Normal (fonte, espaçamentos), capas, conjuntos de estilos, ABNT (trabalhos acadêmicos).
- [ ] DESENHAR: predefinições de caneta e marca-texto; avaliar borracha por arrasto e pressão (Nível 2).
- [ ] Mala direta: teste com CSV e planilha; envelopes e etiquetas Pimaco.
- [x] Revisão gramatical offline: decidido usar o Lightproof pt-BR já incluído no motor, com categorias ligadas
      por nível pelo AY ([REVISAO-E-IA.md §3](REVISAO-E-IA.md)); LanguageTool (Java) fica como avaliação futura.
- [ ] Autorização por documento para conteúdo externo (hoje bloqueado sempre).
- [ ] Nível 2 (fork de código): ícones de janela e AppUserModelID próprios, MSI próprio, correção da página em
      branco automática (I1) como opção de compatibilidade, correção da queda com automação UNO externa.

## Etapa 5 — Compatibilidade, instaladores e distribuição 🟡

- [x] Site oficial (prévia local funcional): download real do instalador validado, SHA-256, aviso de ausência de
      assinatura, demais sistemas "Em desenvolvimento", instruções, versões, limitações, ajuda, privacidade e
      licenças ([SITE.md](SITE.md)). Teste do fluxo acessar → baixar → conferir → instalar → abrir:
      `tests/site/testar_fluxo.ps1`.
- [x] Publicação da 0.2.0 (autorizada em 20/10/2026): repositório público, instalador no GitHub Releases
      (pré-lançamento v0.2.0, com SHA-256, instruções, limitações e licenças) e site no GitHub Pages com HTTPS
      ([RESULTADOS §10](RESULTADOS-TESTES.md)). Só recursos gratuitos, sem cobrança.
- [ ] Windows 10 (22H2) limpo: instalar e repetir os testes; só então liberar no site.
- [ ] MSI para implantação corporativa (WiX, ou o MSI do Nível 2).
- [ ] Assinatura de código.
- [ ] Windows ARM64 (hardware real), macOS (assinatura e notarização) e Linux (AppImage/Flatpak).
- [ ] Atualização opcional do AY: consulta só quando o usuário pede, sem enviar conteúdo.
- [ ] Bateria de compatibilidade em CI (GitHub Actions `windows-latest`) com o corpus da Etapa 2.

## Assistência de escrita, modelos e atualizações (pedido de 20/10/2026)

Visão: escrever normalmente, abrir documentos do Word, corrigir erros, melhorar a redação e aplicar um modelo de
formatação sem configurar cada detalhe — com as mesmas abas, assistência na aba **Revisão** e no painel lateral
**Assistente AY**, offline primeiro e IA local opcional. Decisões técnicas e fontes em
[REVISAO-E-IA.md](REVISAO-E-IA.md). Cada entrega gera um instalador de testes; a versão pública (0.2.0) continua
disponível até a avaliação da seguinte.

| Entrega | Versão | Conteúdo | Situação |
|---|---|---|---|
| Confiabilidade | 0.3.0 | recuperação após falha, salvamento seguro, desfazer/refazer, TXT UTF-8/Windows-1252, Salvar como com aviso de perdas pela interface | ✅ testes automatizados (versão de testes local) |
| **A** | 0.3.0 | correção ortográfica configurável (detecção + correção automática de casos inequívocos com proteções, desfazer, "não corrigir novamente"), dicionário pessoal, gramática e pontuação (Lightproof com explicação), estilo opcional, painel **Assistente AY** e grupo na aba Revisão | ✅ implementada e testada (versão de testes local, ainda não publicada) |
| **B** | 0.4.0 | assistente "Formatar trabalho acadêmico" (TCC, artigo, projeto, relatório, modelo da instituição) com regras registradas por norma/edição/origem/data, prévia e relatório de conformidade; galeria de modelos (ofício, memorando, relatório, currículo, carta, ata, proposta, personalizado); salvar como modelo | ✅ implementada e testada (versão de testes local 0.4.0, ainda não publicada); formatação sempre numa cópia (no original o motor apagaria o histórico de desfazer); textos oficiais das normas não consultados (regras de guias universitários, com a fonte em cada item) |
| **C** | 0.5.0 | IA local opcional (llama.cpp + modelo com licença permissiva, escolhido por testes em pt-BR): revisar trecho, clareza, formalidade, simplificar, resumir, títulos, explicar, inconsistências; original × proposta; aplicação reversível como alteração controlada | ✅ fluxo completo implementado e testado (versão de testes local 0.5.0): revisar, mais claro, mais formal, simplificar e resumir com Gemma 4 E2B (escolhido por testes em pt-BR) e llama.cpp; títulos, explicar e inconsistências ficam para a entrega D |
| **D** | 0.6.0 | análise de documentos longos em segundo plano, referências estruturadas (sem inventar dados), importação de documento de referência para extrair estilos, mais modelos | ⬜ |
| **E** | 0.7.0 | "Verificar atualizações" (Ajuda): consulta iniciada pelo usuário, canais estável/testes, manifesto assinado, SHA-256, instalação só com confirmação; sem infraestrutura de assinatura, instalação manual pelo site | ⬜ |

Testes exigidos ao longo das entregas: português brasileiro com nomes próprios e termos técnicos; preservação
de números, citações e referências; desfazer/refazer depois de correções e formatação; DOCX e ODT com tabelas,
imagens, notas e alterações controladas; documentos longos e cancelamento; funcionamento sem internet e sem
modelo; memória, tempo de resposta e digitação durante a IA; acessibilidade do painel; integridade depois de
salvar e reabrir.

## Próximo marco

A publicação da 0.2.0 (versão de testes, só Windows 11 x64) não encerra o projeto. Próxima versão:

**0.3.0 — confiabilidade + entrega A: pronta como versão de testes local, aguardando avaliação** (a 0.2.0
continua sendo a versão pública). Depois da avaliação: publicar a 0.3.0 como nova versão de testes.

**0.4.0 — entrega B: pronta como versão de testes local, aguardando avaliação**: "Formatar trabalho acadêmico"
(perfis TCC, artigo, projeto, relatório e modelo da instituição personalizável com prévia das diferenças) sempre
numa cópia sem título, com desfazer/refazer íntegros, relatório de conformidade por categoria (regra conferida,
instituição, preferência, não avaliado) e galeria de modelos com "Salvar como modelo". Resultados em
[RESULTADOS-TESTES.md](RESULTADOS-TESTES.md) §5.3 e §5.4.

**0.5.0 — entrega C: pronta como versão de testes local, aguardando avaliação**: IA local opcional — selecionar
trecho → pedir → original × sugestão com conferência de preservação → aceitar (alteração controlada, uma ação de
desfazer) ou rejeitar; download do modelo opcional e informado; servidor local fechado (127.0.0.1, chave, offline).
Resultados em [RESULTADOS-TESTES.md](RESULTADOS-TESTES.md) §5.5; decisões em [REVISAO-E-IA.md](REVISAO-E-IA.md) §5.

**Próxima: entrega D (0.6.0)** — análise de documentos longos, referências estruturadas, mais pedidos de IA
(títulos, explicar, inconsistências). Continuam previstos em paralelo: clique automatizado nas abas Forma e Visualizar impressão; validação com
NVDA e Narrador; recolhimento dos grupos em janelas estreitas; teste em Windows 10 limpo.

Ainda pendente depois disso (resumo das etapas acima):

| Área | Pendente |
|---|---|
| Funções sem comando (fora da faixa) | marca-texto, borracha, pressão da caneta, revisão gramatical avançada offline, modo de leitura, verificar atualizações |
| Plataformas | Windows 10, Windows em ARM, macOS, Linux — nenhuma testada; o site as mostra como "Em desenvolvimento" |
| Distribuição | assinatura de código do instalador; MSI corporativo; domínio próprio (opcional) |
| Acessibilidade | leitores de tela, só teclado, escalas 125–200 %, temas |
| Compatibilidade | página em branco automática (I1), refluxo de colunas em DOCX (I3), corpus real maior |
| Motor (Nível 2) | ícone e AppUserModelID próprios; correção da queda com automação UNO externa |

## Plataformas

Veja [COMPILACAO.md § Outras plataformas](COMPILACAO.md#outras-plataformas).
