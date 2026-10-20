# Plano de execução do AY ESCREVA

Legenda: ✅ concluído e validado · 🟡 em andamento / parcial · ⬜ não iniciado

Entrega atual: **0.2.0, versão inicial de testes para Windows 11 x64** (validada somente nesse sistema).

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
- [ ] Salvar como / Salvar uma cópia com o aviso de perdas: teste automatizado pela interface (seletor de arquivo).
- [ ] Teste de **recuperação após falha**: encerrar o processo com documento modificado e conferir a oferta de
      recuperação na reabertura.
- [ ] Teste de **salvamento seguro**: falha simulada no meio da gravação não pode corromper o arquivo anterior;
      conferir a cópia em `%APPDATA%\AYEscreva\1\user\backup`.
- [ ] Desfazer/refazer: teste automatizado de uma sequência de edições.
- [ ] TXT: ida e volta com codificação UTF-8 e Windows-1252.
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
- [ ] Revisão gramatical offline: avaliar LanguageTool local (Java, servidor em `localhost`) × Lightproof pt-BR.
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

## Próximo marco

A publicação da 0.2.0 (versão de testes, só Windows 11 x64) não encerra o projeto. Próxima versão:

**0.3.0 — fechamento da Etapa 2 e acessibilidade da faixa**: recuperação após falha, salvamento seguro e
desfazer/refazer com testes automatizados; teste de Salvar como / Salvar uma cópia com o aviso de perdas;
clique automatizado nas abas Forma e Visualizar impressão; validação com NVDA e Narrador e por teclado;
recolhimento dos grupos em janelas estreitas; teste em Windows 10 limpo.

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
