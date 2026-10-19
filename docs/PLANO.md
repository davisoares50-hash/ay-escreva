# Plano de execução do AY ESCREVA

Legenda: ✅ concluído e validado · 🟡 em andamento / parcial · ⬜ não iniciado

## Etapa 1 — Base técnica compilável e prova de edição real ✅

| Entrega | Situação | Evidência |
|---|---|---|
| Inspeção do ambiente e decisão de arquitetura | ✅ | [ARQUITETURA.md](ARQUITETURA.md) |
| Base fixada e verificada (SHA-256, PGP, Authenticode) | ✅ | `base/base.lock.json`, `scripts/montar.ps1` |
| Distribuição AY montada (nome, perfil próprio, segurança, pt-BR, interface por abas da base) | ✅ | `dist/AY ESCREVA` (797 MB) |
| Identidade visual própria | ✅ | `tools/marca.mjs`, `branding/README.md` |
| Lançador próprio compilado | ✅ | `launcher/AYEscreva.cs` → `AYEscreva.exe` |
| **Aceite**: documento de várias páginas, formatação, tabela, imagem, salvar, fechar, reabrir, PDF | ✅ 40/40 | [RESULTADOS-TESTES.md §2](RESULTADOS-TESTES.md#2-aceite-da-etapa-1--testsunoaceite_etapa1py-4040) |
| Matriz de funcionalidades com verificação de comandos | ✅ 219/219 | [MATRIZ-FUNCIONALIDADES.md](MATRIZ-FUNCIONALIDADES.md) |
| Instalador Windows | 🟡 script pronto, não compilado (falta Inno Setup) | `installer/ayescreva.iss` |

## Etapa 2 — Abrir, editar, salvar, reabrir, imprimir e exportar 🟡

Já validado: ida e volta DOCX/ODT/DOC/RTF com documentos representativos (estrutura e comparação visual),
impressão real pela fila do Windows, exportação PDF e PDF/UA, macros bloqueadas, recursos remotos bloqueados.

Pendente:

- [ ] Aviso **específico** antes de salvar em formato com perda. Hoje o aviso é genérico ("manter formato
      atual?", da base); a meta é listar o que será perdido no formato escolhido (ex.: RTF perde seções e níveis
      de tópico — incompatibilidade I2) e oferecer "Salvar uma cópia em ODT". Implementação: extensão AY ouvindo
      o evento `OnSaveAs`/`OnSave` e inspecionando o documento.
- [ ] Aviso de **fontes substituídas** ao abrir (I5), com a lista e a fonte usada no lugar.
- [ ] Teste de **recuperação após falha**: encerrar o processo com documento modificado e conferir a oferta de
      recuperação na reabertura.
- [ ] Teste de **salvamento seguro**: falha simulada no meio da gravação não pode corromper o arquivo anterior;
      conferir a cópia em `%APPDATA%\AYEscreva\1\user\backup`.
- [ ] Desfazer/refazer: teste automatizado de uma sequência de edições.
- [ ] TXT: ida e volta com codificação UTF-8 e Windows-1252.
- [ ] Ampliar o corpus: documentos reais anonimizados (ABNT, contratos, ofícios), DOCX produzidos por Word 2007,
      2010, 2016/365 e Google Docs.

## Etapa 3 — Interface por abas conectada aos comandos ⬜

- [ ] Gerar `notebookbar_ayescreva.ui` a partir de `ui/abas.json`, com as abas na ordem do produto: ARQUIVO,
      PÁGINA INICIAL, INSERIR, DESENHAR, DESIGN, LAYOUT, REFERÊNCIAS, CORRESPONDÊNCIA, REVISÃO, EXIBIR, AJUDA,
      e contextuais TABELA, IMAGEM e FORMA.
- [ ] Registrar o modo "AY ESCREVA" em `ToolbarMode` e torná-lo padrão.
- [ ] Extensão AY (UNO em Python, protocolo `ayescreva:`) para as lacunas: página em branco, modo de leitura,
      recuperação de documentos, guia, atalhos, diagnóstico, marca-texto.
- [ ] Atalhos com paridade ao Word pt-BR (Ctrl+N negrito, Ctrl+I itálico, Ctrl+S sublinhado, Ctrl+B salvar):
      conferir os atalhos que a base usa em pt-BR e ajustar na camada AY onde divergirem.
- [ ] Teste: cada botão da faixa dispara o comando esperado; nenhum botão sem comando (botões de lacunas
      ficam ocultos ou marcados "em breve", nunca decorativos).
- [ ] Acessibilidade: navegação só por teclado (F6, Alt, setas), NVDA e Narrador lendo abas, grupos e botões;
      escalas 100/125/150/200 %; tema claro/escuro.
- [ ] Investigar a queda do motor no modo sem tela com a faixa por abas (ver RESULTADOS §9).

## Etapa 4 — Recursos avançados ⬜

- [ ] Modelos AY: Normal (fonte, espaçamentos), capas, conjuntos de estilos, ABNT (trabalhos acadêmicos).
- [ ] DESENHAR: predefinições de caneta e marca-texto; avaliar borracha por arrasto e pressão (Nível 2).
- [ ] Mala direta: teste com CSV e planilha; envelopes e etiquetas Pimaco.
- [ ] Revisão gramatical offline: avaliar LanguageTool local (Java, servidor em `localhost`) × Lightproof pt-BR.
- [ ] Autorização por documento para conteúdo externo (hoje bloqueado sempre).
- [ ] Nível 2 (fork de código): ícones de janela e AppUserModelID próprios, MSI próprio, correção da página em
      branco automática (I1) como opção de compatibilidade.

## Etapa 5 — Testes de compatibilidade e instaladores ⬜

- [ ] Instalador Inno Setup compilado e testado (instalar, abrir, associar, desinstalar) em Windows 10 e 11 limpos.
- [ ] MSI para implantação corporativa (WiX, ou o MSI do Nível 2).
- [ ] Assinatura de código.
- [ ] Windows ARM64 (hardware real), macOS (assinatura e notarização) e Linux (AppImage/Flatpak).
- [ ] Atualização opcional do AY: consulta só quando o usuário pede, sem enviar conteúdo.
- [ ] Bateria de compatibilidade em CI (GitHub Actions `windows-latest`) com o corpus da Etapa 2.

## Plataformas

Veja [COMPILACAO.md § Outras plataformas](COMPILACAO.md#outras-plataformas).
