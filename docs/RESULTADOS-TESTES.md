# Resultados dos testes — Etapa 1 (e início da Etapa 2)

Execução: 19/10/2026 · `scripts/testar.ps1` (8 etapas, 0 falhas, ~2 min) + `tests/uno/seguranca.py`
Ambiente: Windows 11 Pro 10.0.26200 x64, Intel Core i5-8500, 16 GB · Motor: LibreOffice 26.8.1.1 (binários oficiais)
Oráculo independente: Microsoft Word 16.0 (instalado na máquina, usado só via automação COM com macros desativadas)

## 1. O que está implementado, compilado e validado

| Componente | Código implementado | Compilação/montagem executada | Funcionamento validado |
|---|---|---|---|
| Obtenção da base (SHA-256, PGP, Authenticode) | sim — `scripts/montar.ps1` | sim | sim: assinatura PGP da chave `C2839ECA…AFEEAEA3` e Authenticode "The Document Foundation" válidas |
| Distribuição AY (poda de idiomas, fontes privadas, runtime VC++) | sim | sim — 797 MB (base extraída: 1,5 GB) | sim: o motor inicia e edita (testes abaixo) |
| Camada de configuração `ayescreva.xcd` | sim | sim | sim: título "AY ESCREVA", realce→`w:highlight`, faixa por abas, segurança de macros |
| Identidade visual (ícone, abertura, Sobre, logotipos, imagens do instalador) | sim — `tools/marca.mjs` | sim | parcial: ícone do lançador e tela de abertura conferidos; ícone da janela ainda é o da base |
| Lançador `AYEscreva.exe` | sim — C# | sim — csc do .NET Framework 4.8.1 | sim: abriu DOCX pela linha de comando com perfil próprio |
| Instalador Windows (Inno Setup) | sim — `installer/ayescreva.iss` | **não** — Inno Setup não está instalado nesta máquina | **não** |
| Faixa de opções AY na ordem pedida | não (Etapa 3) — mapeamento pronto em `ui/abas.json` | — | — |
| Extensão AY (comandos que faltam na base) | não (Etapas 3-4) | — | — |
| Testes automatizados | sim — `tests/` | — | executados (abaixo) |

## 2. Aceite da Etapa 1 — `tests/uno/aceite_etapa1.py`: **40/40**

Documento criado pelo motor com 5 páginas: título em Título 1, negrito, itálico, sublinhado, tachado, sobrescrito,
cor + 14 pt, realce, fonte diferente, parágrafo centralizado, texto justificado, quebra de página, tabela 4×3,
imagem embutida com texto alternativo, cabeçalho e rodapé com número de página. Salvo em ODT e DOCX, fechado,
reaberto e conferido item a item; exportado para PDF (mesmo número de páginas) e PDF/UA marcado (`/StructTreeRoot`).

| Verificação | ODT | DOCX |
|---|---|---|
| Páginas iguais ao original (5) | OK | OK |
| Texto completo e acentuação | OK | OK |
| Estilo Título 1 | OK | OK |
| Negrito, itálico, sublinhado, tachado, sobrescrito | OK | OK |
| Cor e tamanho, fonte do trecho | OK | OK |
| Realce | OK (fundo de caractere) | OK (realce do Word, após ajuste da camada AY) |
| Alinhamento centralizado | OK | OK |
| Tabela 4×3 com conteúdo | OK | OK |
| Imagem embutida, tamanho e texto alternativo | OK | OK |
| Cabeçalho; rodapé com número de página | OK | OK |
| PDF com o mesmo número de páginas; PDF/UA marcado | OK | OK |

O mesmo DOCX aberto no Word: 5 páginas, 1 tabela, 1 imagem (`tests/output/word-inventario.json`).

## 3. Impressão — `tests/uno/impressao.py`: **4/4**

Impressão real pela fila do Windows na impressora virtual "Microsoft Print to PDF" (o teste aborta antes de
imprimir se essa impressora não estiver selecionada, para nunca usar uma impressora física): arquivo gerado, é PDF,
5 páginas impressas = 5 páginas do documento.

## 4. Segurança — `tests/uno/seguranca.py`: **4/4**

| Verificação | Resultado |
|---|---|
| Controle positivo: macro executa quando forçada pela API (prova que o teste detecta execução) | OK |
| Macro Basic no evento "ao abrir" **não** executa na abertura normal | OK |
| … nem aprovando confirmações (`USE_CONFIG_APPROVE_CONFIRMATION`) | OK |
| DOCX com imagem vinculada a servidor HTTP local: **0** requisições ao abrir e exportar PDF | OK |
| (informativo) pedido explícito de "atualizar vínculos": também 0 requisições | bloqueio total hoje; não há como autorizar por documento |

## 5. Comandos da matriz — `tests/uno/comandos.py`: **219/219**

230 funções mapeadas nas 11 abas + 3 contextuais; 219 têm comando da base e **todos** foram encontrados no motor em
execução (despachante do quadro do Writer ou controlador de menu); 11 são lacunas sem comando na base, com caminho
previsto. Detalhe: [MATRIZ-FUNCIONALIDADES.md](MATRIZ-FUNCIONALIDADES.md). Isso comprova que o comando existe,
não que o botão já esteja na faixa AY (Etapa 3).

## 6. Interface (verificação visual) — `tests/output/janela-etapa1b.png`

Janela aberta pelo `AYEscreva.exe` com um DOCX: título "teste-etapa1.docx — AY ESCREVA Writer"; interface em
pt-BR; faixa por abas da base (Arquivo, Início, Inserir, Leiaute, Referências, Revisar, Exibir…); régua; página
com limites; barra lateral; barra de status com "Página 1 de 5", "2.073 palavras, 12.148 caracteres",
"Português (Brasil)" e zoom 100%. **Ainda não** é a faixa AY na ordem pedida, e o ícone da janela é o da base.

## 7. Documentos representativos — ida e volta

Entrada principal: `tests/fixtures/compatibilidade-ooxml.docx`, escrito diretamente em OOXML por
`tests/fixtures/gerar_docx.py` (não pelo motor). Contém 3 seções (retrato com primeira página diferente; paisagem
com 2 colunas; retrato com numeração reiniciada), cabeçalhos/rodapés com PAGE e NUMPAGES, 2 notas de rodapé, 1 nota
de fim, 1 comentário, 3 alterações controladas (inserção, exclusão, formatação), sumário, indicador e referência
cruzada, hiperlink externo, listas numeradas e com marcadores, tabela com mesclagem horizontal/vertical e
cabeçalho repetido, imagem com texto alternativo, caixa de texto, equação OMML, fonte inexistente e Calibri.
O Word abriu o arquivo sem reparos e contou: 4 páginas, 3 seções, 1 tabela, 3 notas, 1 comentário, 3 revisões.
Variantes salvas pelo próprio Word: DOCX, DOC, RTF, ODT e PDF de referência.

### 7.1 Estrutura (inventário antes × depois de salvar e reabrir no AY)

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

### 7.2 Visual (PDF do original × PDF da cópia reaberta, 60 dpi, % de pixels diferentes)

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

## 8. Incompatibilidades encontradas

| # | Situação | Efeito | Origem | Encaminhamento |
|---|---|---|---|---|
| I1 | Seção que reinicia a numeração em 1 cai em página par | O motor insere uma página em branco automática: o campo NUMPAGES mostra "de 5" num documento que o Word mostra com 4 páginas; o PDF exportado tem 4 páginas; a impressão pode incluir a página em branco | comportamento do motor ([Ask LibreOffice](https://ask.libreoffice.org/t/writer-page-numbering-is-wrong-one-number-up/81691), [tdf#126284](https://libreoffice.org/get-help/bug/show_activity.cgi?id=126284)) | correção em C++ no Nível 2 (opção de compatibilidade para documentos Word) e proposta ao upstream |
| I2 | Salvar em RTF | Perde quebra de seção com mudança de orientação e o nível de tópico dos títulos (sumário deixa de atualizar) | filtro de exportação RTF | avisar ao salvar em RTF e sugerir DOCX/ODT; RTF fica "suporte básico" |
| I3 | ODT → DOCX com seção em paisagem de 2 colunas | Refluxo das colunas e uma página a menos | exportação DOCX de seções/colunas | investigar na Etapa 4 com mais amostras |
| I4 | DOC → DOCX | Quadro vira forma, uma seção de texto a mais; 2,4 % de diferença visual | conversão entre modelos de seção | aceitável; monitorar |
| I5 | Fonte ausente no sistema | Substituída sem aviso ao usuário (o teste detecta: "Fonte Inexistente AY") | comportamento padrão do motor | aviso explícito ao abrir + relatório de substituições (Etapa 4) |
| I6 | Word × AY, mesmo DOCX | Mesmo número de páginas e conteúdo; quebras de linha, fonte da equação e cores de revisão diferem; 4 % em média | motores de layout diferentes | esperado; não prometer igualdade de pixels com o Word |
| I7 | Comentários no PDF | O PDF do AY não mostra comentários por padrão (o do Word mostra em linha) | opção de exportação | expor a opção "comentários na margem" no Exportar PDF |

## 9. O que **não** foi validado (limites declarados)

- Somente Windows 11 x64 nesta máquina. **Windows 10 não testado** (a base exige Windows 10+, segundo o próprio MSI).
- Windows ARM64 e x86 32 bits: a base publica pacotes, mas nada foi montado nem testado (ver [PLANO.md](PLANO.md#plataformas)).
- macOS e Linux: não montados nem testados.
- Leitores de tela (NVDA, Narrador, JAWS), navegação só por teclado e escalas de 125–200 %: **não testados**.
- Instalador: escrito, **não compilado** (falta o Inno Setup). Sem assinatura de código.
- Teste de imagem remota cobre só o filtro DOCX e imagem vinculada; outros tipos de recurso externo (OLE/DDE,
  fontes remotas, modelos remotos) não foram testados.
- Máquina sem Microsoft Office (para ver a substituição de Calibri por Carlito): não testada.
- O motor cai quando o modo **sem tela (headless)** cria um quadro visível com a faixa por abas; os testes que
  precisam de quadro visível trocam o perfil descartável para a barra clássica. No aplicativo com interface não
  ocorreu, mas convém investigar antes da Etapa 3.
