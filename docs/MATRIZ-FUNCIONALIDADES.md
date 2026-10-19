# Matriz de funcionalidades do AY ESCREVA

> Gerado por `tests/uno/comandos.py` a partir de `ui/abas.json` em 2026-10-19. Não editar à mão.

**Como ler as colunas**

- **Implementação na base**: *Na base (comando verificado)* quer dizer que o comando existe no motor e o quadro do
  Writer devolveu um despachante para ele no teste automático; não quer dizer que o botão já esteja na faixa do AY.
  *Lacuna* quer dizer que não há comando pronto: o caminho previsto está na coluna de lacunas e dependências.
- **Validado por**: teste automatizado que exercitou a função de ponta a ponta (via API, sem clicar no botão).
  Vazio = ainda não validado.
- **Faixa AY**: estado do botão na faixa de opções própria do AY. Na Etapa 1 as funções com comando da base estão acessíveis pelos
  menus e pela faixa por abas da base; as lacunas não estão acessíveis. As abas AY, na ordem pedida, são a Etapa 3.
- **Prioridade**: P0 = Etapas 1-2, P1 = Etapa 3, P2 = Etapa 4, P3 = avaliar.

**Resumo**: Lacuna: 11 · Na base (comando verificado): 219 · Total: 230


## ARQUIVO

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
| Documento | Novo documento | `.uno:AddDirect` | Novo | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Abre documento de texto em branco |  |
| Documento | Modelos | `.uno:NewDoc` | Gerenciar modelos | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Abre o gerenciador de modelos e cria documento a partir de um modelo |  |
| Documento | Abrir | `.uno:Open` | Abrir... | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P0 | Abre DOCX, ODT, DOC, RTF e TXT locais |  |
| Documento | Recentes | `.uno:RecentFileList` | Documentos recentes | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Lista os documentos recentes do perfil local |  |
| Documento | Salvar | `.uno:Save` | Salvar | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Salva no formato atual com aviso para formatos não nativos |  |
| Documento | Salvar como | `.uno:SaveAs` | Salvar como... | Na base (comando verificado) | aceite_etapa1, ida_e_volta | Pendente (Etapa 3) | P0 | Salva em ODT, DOCX, DOC, RTF ou TXT |  |
| Documento | Salvar uma cópia | `.uno:SaveACopy` | Salvar uma cópia... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Grava cópia sem trocar o documento aberto |  |
| Documento | Recarregar | `.uno:Reload` | Recarregar | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Recarrega a última versão salva |  |
| Documento | Fechar | `.uno:CloseDoc` | Fechar | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Fecha o documento perguntando se há alterações |  |
| Exportar e imprimir | Exportar PDF (opções) | `.uno:ExportToPDF` | Exportar como PDF... | Na base (comando verificado) | aceite_etapa1 (PDF e PDF/UA) | Pendente (Etapa 3) | P0 | Exporta PDF, PDF/A e PDF/UA marcado |  |
| Exportar e imprimir | Exportar PDF direto | `.uno:ExportDirectToPDF` | Exportar diretamente como PDF | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P1 | Exporta PDF com as opções padrão |  |
| Exportar e imprimir | Imprimir | `.uno:Print` | Imprimir... | Na base (comando verificado) | impressao | Pendente (Etapa 3) | P0 | Imprime pela fila do sistema com prévia no diálogo |  |
| Exportar e imprimir | Visualizar impressão | `.uno:PrintPreview` | Visualizar impressão | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Mostra prévia paginada antes de imprimir |  |
| Informações | Propriedades | `.uno:SetDocumentProperties` | Propriedades... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Edita título, autor, palavras-chave e mostra estatísticas |  |
| Informações | Versões | `.uno:VersionDialog` | Versões... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Salva e compara versões dentro do ODT |  |
| Informações | Assinatura digital | `.uno:Signature` | Assinaturas digitais... | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Assina com certificado local do usuário |  |
| Informações | Configurações | `.uno:OptionsTreeDialog` | Opções... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Abre as opções do aplicativo |  |
| Informações | Recuperação de documentos | — |  | Lacuna |  | Pendente (Etapa 3) | P1 | Após falha, oferece recuperar; pelo menu, lista cópias de segurança e de recuperação | A recuperação automática após falha já está ativa (configurada a cada 5 min) e a cópia de segurança ao salvar também; falta um comando de menu para abrir as cópias. Implementar como extensão AY. |

## PÁGINA INICIAL

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
| Área de transferência | Colar | `.uno:Paste` | Colar | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Cola mantendo formatação |  |
| Área de transferência | Colar especial | `.uno:PasteSpecial` | Colar especial... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Cola como texto sem formatação e outros formatos |  |
| Área de transferência | Recortar | `.uno:Cut` | Cortar | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Recorta a seleção |  |
| Área de transferência | Copiar | `.uno:Copy` | Copiar | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Copia a seleção |  |
| Área de transferência | Pincel de formatação | `.uno:FormatPaintbrush` | Clonar formatação | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Copia a formatação para outro trecho |  |
| Fonte | Fonte | `.uno:CharFontName` | Nome da fonte | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Lista fontes instaladas e as fontes do AY |  |
| Fonte | Tamanho | `.uno:FontHeight` | Tamanho da fonte | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Define tamanho em pontos |  |
| Fonte | Aumentar fonte | `.uno:Grow` | Aumentar tamanho | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Aumenta o tamanho |  |
| Fonte | Diminuir fonte | `.uno:Shrink` | Diminuir tamanho | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Diminui o tamanho |  |
| Fonte | Negrito | `.uno:Bold` | Negrito | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Ctrl+N; preservado em ODT e DOCX |  |
| Fonte | Itálico | `.uno:Italic` | Itálico | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Ctrl+I; preservado em ODT e DOCX |  |
| Fonte | Sublinhado | `.uno:Underline` | Sublinhado | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Ctrl+S; preservado em ODT e DOCX |  |
| Fonte | Tachado | `.uno:Strikeout` | Tachado | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Preservado em ODT e DOCX |  |
| Fonte | Sobrescrito | `.uno:SuperScript` | Sobrescrito | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Preservado em ODT e DOCX |  |
| Fonte | Subscrito | `.uno:SubScript` | Subscrito | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Preservado em ODT e DOCX |  |
| Fonte | Cor da fonte | `.uno:FontColor` | Cor da fonte | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Preservada em ODT e DOCX |  |
| Fonte | Realce | `.uno:CharBackColor` | Cor de destaque de caracteres | Na base (comando verificado) | aceite_etapa1 (realce no DOCX) | Pendente (Etapa 3) | P0 | Vira realce (w:highlight) no DOCX |  |
| Fonte | Limpar formatação | `.uno:ResetAttributes` | Limpar formatação direta | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Remove formatação direta |  |
| Fonte | Caractere (diálogo) | `.uno:FontDialog` | Caractere... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Todas as opções de caractere |  |
| Parágrafo | Alinhar à esquerda | `.uno:LeftPara` | Alinhar à esquerda | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Preservado em ODT e DOCX |  |
| Parágrafo | Centralizar | `.uno:CenterPara` | Centralizar | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Preservado em ODT e DOCX |  |
| Parágrafo | Alinhar à direita | `.uno:RightPara` | Alinhar à direita | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Preservado em ODT e DOCX |  |
| Parágrafo | Justificar | `.uno:JustifyPara` | Justificado | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Preservado em ODT e DOCX |  |
| Parágrafo | Aumentar recuo | `.uno:IncrementIndent` | Aumentar recuo | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Altera o recuo à esquerda |  |
| Parágrafo | Diminuir recuo | `.uno:DecrementIndent` | Diminuir recuo | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Altera o recuo à esquerda |  |
| Parágrafo | Espaçamento entre linhas | `.uno:LineSpacing` | Entrelinhas | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Simples, 1,15, 1,5, duplo e personalizado |  |
| Parágrafo | Aumentar espaço entre parágrafos | `.uno:ParaspaceIncrease` | Aumentar espaçamento entre parágrafos | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Altera espaço antes/depois |  |
| Parágrafo | Diminuir espaço entre parágrafos | `.uno:ParaspaceDecrease` | Diminuir espaçamento entre parágrafos | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Altera espaço antes/depois |  |
| Parágrafo | Marcadores | `.uno:DefaultBullet` | Listas não ordenadas | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P0 | Lista com marcadores preservada em DOCX |  |
| Parágrafo | Numeração | `.uno:DefaultNumbering` | Lista ordenada | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P0 | Lista numerada preservada em DOCX |  |
| Parágrafo | Lista multinível | `.uno:SetOutline` | Formato dos tópicos | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Numeração de títulos e listas em níveis |  |
| Parágrafo | Parágrafo (diálogo) | `.uno:ParagraphDialog` | Parágrafo... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Recuos, espaçamento, fluxo e tabulações |  |
| Parágrafo | Marcas de formatação | `.uno:ControlCodes` | Marcas de formatação | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Mostra ¶, espaços e tabulações |  |
| Estilos | Galeria de estilos | `.uno:StyleApply` | Estilo do parágrafo | Na base (comando verificado) | aceite_etapa1 (Título 1) | Pendente (Etapa 3) | P0 | Aplica Título 1..n, Corpo de texto etc. |  |
| Estilos | Painel de estilos | `.uno:DesignerDialog` | Gerenciar estilos | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Cria e modifica estilos |  |
| Edição | Localizar e substituir | `.uno:SearchDialog` | Localizar e substituir... | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Busca com expressões regulares e formatação |  |
| Edição | Selecionar tudo | `.uno:SelectAll` | Selecionar tudo | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Seleciona o documento |  |

## INSERIR

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
| Páginas | Capa | `.uno:TitlePageDialog` | Página de rosto... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Insere página de rosto com estilo próprio | A base oferece o diálogo de páginas de título; uma galeria de capas prontas (como no Word) será feita com modelos AY. |
| Páginas | Página em branco | — |  | Lacuna |  | Pendente (Etapa 3) | P1 | Insere uma página vazia no ponto do cursor | Sem comando único na base (equivale a duas quebras de página). Implementar como comando da extensão AY. |
| Páginas | Quebra de página | `.uno:InsertPagebreak` | Inserir quebra de página | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Ctrl+Enter; preservada em DOCX |  |
| Páginas | Quebras (página, coluna, linha) | `.uno:InsertBreak` | Quebra manual... | Na base (comando verificado) | ida_e_volta (3 seções) | Pendente (Etapa 3) | P1 | Inclui quebra com troca de estilo de página |  |
| Páginas | Seção | `.uno:InsertSection` | Seção... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Seção com colunas e proteção |  |
| Tabelas e ilustrações | Tabela | `.uno:InsertTable` | Inserir tabela... | Na base (comando verificado) | aceite_etapa1, ida_e_volta (mescladas) | Pendente (Etapa 3) | P0 | Insere tabela; preservada em ODT e DOCX |  |
| Tabelas e ilustrações | Imagem | `.uno:InsertGraphic` | Figura... | Na base (comando verificado) | aceite_etapa1 | Pendente (Etapa 3) | P0 | Insere imagem embutida com texto alternativo |  |
| Tabelas e ilustrações | Formas | `.uno:BasicShapes` | Formas simples | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Retângulos, elipses, setas etc. |  |
| Tabelas e ilustrações | Caixa de texto | `.uno:DrawText` | Caixa de texto | Na base (comando verificado) | ida_e_volta (caixa de texto) | Pendente (Etapa 3) | P1 | Caixa de texto exportada como forma DOCX |  |
| Tabelas e ilustrações | Quadro | `.uno:InsertFrame` | Quadro... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Quadro de texto posicionável |  |
| Tabelas e ilustrações | Gráfico | `.uno:InsertObjectChart` | Gráfico... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Gráfico com dados internos |  |
| Tabelas e ilustrações | Fontwork (texto artístico) | `.uno:FontworkGalleryFloater` | Fontwork... | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Texto decorativo |  |
| Links | Link | `.uno:HyperlinkDialog` | Hiperlink... | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P0 | Hiperlink exige Ctrl+clique e não é acessado ao abrir |  |
| Links | Indicador | `.uno:InsertBookmark` | Marca-páginas... | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P1 | Preservado em DOCX |  |
| Links | Referência cruzada | `.uno:InsertReferenceField` | Referência... | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P1 | Preservada em DOCX |  |
| Links | Comentário | `.uno:InsertAnnotation` | Anotação | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P0 | Preservado em ODT e DOCX |  |
| Cabeçalho e rodapé | Cabeçalho | `.uno:InsertPageHeader` | Cabeçalho | Na base (comando verificado) | aceite_etapa1, ida_e_volta | Pendente (Etapa 3) | P0 | Ativa cabeçalho do estilo de página |  |
| Cabeçalho e rodapé | Rodapé | `.uno:InsertPageFooter` | Rodapé | Na base (comando verificado) | aceite_etapa1, ida_e_volta | Pendente (Etapa 3) | P0 | Ativa rodapé do estilo de página |  |
| Cabeçalho e rodapé | Número de página | `.uno:PageNumberWizard` | Número da página... | Na base (comando verificado) | aceite_etapa1 (campo de página) | Pendente (Etapa 3) | P0 | Insere número de página com posição e formato |  |
| Texto e símbolos | Campos | `.uno:InsertFieldCtrl` | Campo | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Data, hora, autor, título, contagem de páginas |  |
| Texto e símbolos | Data | `.uno:InsertDateField` | Data (fixa) | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Campo de data |  |
| Texto e símbolos | Símbolo | `.uno:CharmapControl` | Caractere especial... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Símbolos recentes e caracteres especiais |  |
| Texto e símbolos | Equação | `.uno:InsertObjectStarMath` | Objeto de fórmula... | Na base (comando verificado) | ida_e_volta (OMML) | Pendente (Etapa 3) | P2 | Equação editável; OMML do DOCX importado vira equação | Editor de equações usa a sintaxe da base (não o editor do Word); exportação para OMML coberta pelo filtro. |

## DESENHAR

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
| Ferramentas | Caneta (linha à mão livre) | `.uno:Freeline_Unfilled` | Linha a mão livre | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Desenha traço com mouse ou caneta; salvo como forma em ODT e DOCX |  |
| Ferramentas | Forma livre preenchida | `.uno:Freeline` | Linha a mão livre, preenchida | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Desenha forma fechada |  |
| Ferramentas | Linha | `.uno:Line` | Inserir linha | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Linha reta |  |
| Ferramentas | Curva | `.uno:Bezier_Unfilled` | Curva | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Curva de Bézier |  |
| Ferramentas | Selecionar traços | `.uno:SelectObject` | Selecionar | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Seleciona traços e formas |  |
| Ferramentas | Marca-texto | — |  | Lacuna |  | Pendente (Etapa 3) | P2 | Traço largo e translúcido sobre o texto | Sem ferramenta própria na base; implementar como predefinição de traço (cor amarela, transparência, espessura) via extensão AY. |
| Ferramentas | Borracha | — |  | Lacuna |  | Pendente (Etapa 3) | P3 | Apaga traços passando o cursor | A base só exclui o traço selecionado (.uno:Delete). Borracha por arrasto exige código C++ na versão derivada. |
| Ferramentas | Sensibilidade à pressão da caneta | — |  | Lacuna |  | Pendente (Etapa 3) | P3 | Espessura varia com a pressão | Não suportado pela base; tinta do Word (InkML) é importada como imagem ou forma, sem pressão. |
| Traço | Cor do traço | `.uno:XLineColor` | Cor da linha | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Altera a cor da linha selecionada |  |
| Traço | Espessura e estilo | `.uno:FormatLine` | Linha... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Espessura, estilo e transparência |  |
| Traço | Agrupar | `.uno:FormatGroup` | Agrupar | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Agrupa traços |  |
| Traço | Excluir traço | `.uno:Delete` | Excluir conteúdo... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Remove o traço selecionado |  |

## DESIGN

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
| Formatação do documento | Temas, cores e fontes do documento | `.uno:ThemeDialog` | Tema... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Aplica tema de cores ao documento |  |
| Formatação do documento | Conjuntos de estilos | `.uno:LoadStyles` | Carregar estilos do modelo | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Importa estilos de um modelo | A base importa estilos de modelos; a galeria visual de conjuntos (como no Word) será feita com modelos AY. |
| Plano de fundo da página | Marca-d'água | `.uno:Watermark` | Marca d'água... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Marca-d'água de texto preservada em DOCX |  |
| Plano de fundo da página | Cor da página | `.uno:PageDialog` | Estilo de página... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Cor de fundo do estilo de página (aba Área) |  |
| Plano de fundo da página | Bordas de página | `.uno:PageDialog` | Estilo de página... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Bordas do estilo de página (aba Bordas) |  |

## LAYOUT

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
| Configurar página | Margens | `.uno:PageMargin` | Margens da página | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Predefinições e personalizadas |  |
| Configurar página | Orientação | `.uno:Orientation` | Orientação | Na base (comando verificado) | ida_e_volta (paisagem) | Pendente (Etapa 3) | P0 | Retrato/paisagem por seção |  |
| Configurar página | Tamanho do papel | `.uno:AttributePageSize` | Tamanho da página | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | A4, Carta, Ofício etc. |  |
| Configurar página | Colunas | `.uno:PageColumnType` | Colunas da página | Na base (comando verificado) | ida_e_volta (2 colunas) | Pendente (Etapa 3) | P1 | 1 a 3 colunas; preservadas em DOCX |  |
| Configurar página | Quebras de página e seção | `.uno:InsertBreak` | Quebra manual... | Na base (comando verificado) | ida_e_volta (3 seções) | Pendente (Etapa 3) | P1 | Quebra com novo estilo de página = seção do Word |  |
| Configurar página | Hifenização | `.uno:Hyphenate` | Hifenização... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Hifenização pt-BR |  |
| Configurar página | Numeração de linhas | `.uno:LineNumberingDialog` | Numeração de linhas... | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Numera linhas |  |
| Configurar página | Estilo de página (diálogo) | `.uno:PageDialog` | Estilo de página... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Todas as opções de página |  |
| Parágrafo | Recuos e espaçamento | `.uno:ParagraphDialog` | Parágrafo... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Recuos e espaços antes/depois |  |
| Organizar objetos | Sem quebra automática | `.uno:WrapOff` | Nenhum | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Texto acima e abaixo do objeto |  |
| Organizar objetos | Quebra automática | `.uno:WrapOn` | Paralelo | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Texto em volta do objeto |  |
| Organizar objetos | Quebra ideal | `.uno:WrapIdeal` | Ideal | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Texto no lado mais largo |  |
| Organizar objetos | Atrás/na frente do texto | `.uno:WrapThrough` | Através | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Objeto sobre o texto |  |
| Organizar objetos | Trazer para frente | `.uno:BringToFront` | Trazer para a frente | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Ordem de sobreposição |  |
| Organizar objetos | Enviar para trás | `.uno:SendToBack` | Enviar para trás | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Ordem de sobreposição |  |
| Organizar objetos | Ancorar à página | `.uno:SetAnchorToPage` | Na página | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Posição fixa na página |  |
| Organizar objetos | Ancorar ao parágrafo | `.uno:SetAnchorToPara` | No parágrafo | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Objeto acompanha o parágrafo |  |
| Organizar objetos | Ancorar como caractere | `.uno:SetAnchorToChar` | Como caractere | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Objeto em linha com o texto |  |
| Organizar objetos | Alinhar objetos | `.uno:ObjectAlignLeft` | Esquerda | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Alinha objetos entre si |  |
| Organizar objetos | Girar | `.uno:ToggleObjectRotateMode` | Girar | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Rotação livre |  |

## REFERÊNCIAS

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
| Sumário | Sumário automático | `.uno:InsertMultiIndex` | Sumário, índice ou bibliografia... | Na base (comando verificado) | ida_e_volta (sumário) | Pendente (Etapa 3) | P1 | Gera sumário a partir dos títulos; preservado em DOCX |  |
| Sumário | Atualizar sumário | `.uno:UpdateCurIndex` | Índice atual | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Atualiza números de página e entradas |  |
| Sumário | Atualizar todos os índices | `.uno:UpdateAllIndexes` | Índices e sumários | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Atualiza sumários, listas e índices |  |
| Notas | Nota de rodapé | `.uno:InsertFootnote` | Nota de rodapé | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P0 | Preservada em ODT e DOCX |  |
| Notas | Nota de fim | `.uno:InsertEndnote` | Notas de fim | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P0 | Preservada em ODT e DOCX |  |
| Notas | Configurar notas | `.uno:FootnoteDialog` | Configurações de notas de rodapé / notas de fim... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Numeração, posição e separador |  |
| Citações e bibliografia | Inserir citação | `.uno:InsertAuthoritiesEntry` | Citação... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Entrada bibliográfica no texto |  |
| Citações e bibliografia | Banco de dados bibliográfico | `.uno:BibliographyComponent` | Banco de dados bibliográficos | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Gerencia fontes locais |  |
| Citações e bibliografia | Bibliografia | `.uno:InsertMultiIndex` | Sumário, índice ou bibliografia... | Na base (comando verificado) | ida_e_volta (sumário) | Pendente (Etapa 3) | P2 | Índice do tipo Bibliografia | Mesmo diálogo do sumário (escolher o tipo). Estilos ABNT exigem modelo AY. |
| Legendas | Inserir legenda | `.uno:InsertCaptionDialog` | Legenda... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Figura/Tabela numeradas |  |
| Legendas | Lista de figuras | `.uno:InsertMultiIndex` | Sumário, índice ou bibliografia... | Na base (comando verificado) | ida_e_volta (sumário) | Pendente (Etapa 3) | P2 | Índice do tipo Ilustrações |  |
| Legendas | Referência cruzada | `.uno:InsertReferenceField` | Referência... | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P1 | Referência a títulos, legendas e indicadores |  |
| Índice remissivo | Marcar entrada | `.uno:InsertIndexesEntry` | Entrada de índice... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Marca termo para o índice |  |
| Índice remissivo | Inserir índice remissivo | `.uno:InsertMultiIndex` | Sumário, índice ou bibliografia... | Na base (comando verificado) | ida_e_volta (sumário) | Pendente (Etapa 3) | P2 | Índice do tipo Alfabético |  |
| Índice remissivo | Atualizar campos | `.uno:UpdateFields` | Atualizar  campos | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Atualiza campos do documento |  |

## CORRESPONDÊNCIA

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
| Criar | Envelopes | `.uno:InsertEnvelope` | Envelope... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Envelope com remetente e destinatário |  |
| Criar | Etiquetas | `.uno:InsertLabels` | Inserir etiquetas | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Folha de etiquetas (Pimaco/Avery) |  |
| Mala direta | Assistente de mala direta | `.uno:MailMergeWizard` | Assistente de mala direta... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Importa destinatários (CSV, planilha) e gera documentos |  |
| Mala direta | Selecionar destinatários | `.uno:ChangeDatabaseField` | Trocar banco de dados... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Troca a fonte de dados |  |
| Mala direta | Exibir fonte de dados | `.uno:ViewDataSourceBrowser` | Fontes de dados | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Mostra registros e permite arrastar campos |  |
| Mala direta | Inserir campo de mesclagem | `.uno:InsertFieldCtrl` | Campo | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Campos do banco de dados |  |
| Mala direta | Primeiro registro | `.uno:MailMergeFirstEntry` | Primeiro registro da mala direta | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Prévia |  |
| Mala direta | Registro anterior | `.uno:MailMergePrevEntry` | Registro anterior da mala direta | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Prévia |  |
| Mala direta | Próximo registro | `.uno:MailMergeNextEntry` | Próximo registro da mala direta | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Prévia |  |
| Mala direta | Último registro | `.uno:MailMergeLastEntry` | Último registro da mala direta | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Prévia |  |
| Mala direta | Gerar documentos | `.uno:MailMergeCreateDocuments` | Editar documentos individuais | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Documento único com todos os registros |  |
| Mala direta | Salvar documentos mesclados | `.uno:MailMergeSaveDocuments` | Salvar documentos mesclados | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Um arquivo por registro ou arquivo único |  |
| Mala direta | Imprimir documentos mesclados | `.uno:MailMergePrintDocuments` | Imprimir documentos mesclados | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Impressão em lote |  |
| Mala direta | Enviar por e-mail | `.uno:MailMergeEmailDocuments` | Enviar mensagens por e-mail | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Só com servidor configurado pelo usuário | Exige SMTP configurado pelo usuário; fica oculto por padrão (o produto não envia nada sem autorização). |

## REVISÃO

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
| Revisão de texto | Ortografia e gramática | `.uno:SpellingAndGrammarDialog` | Ortografia… | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Dicionário pt-BR offline (VERO) |  |
| Revisão de texto | Revisão automática | `.uno:SpellOnline` | Verificação ortográfica automática | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Sublinha erros durante a digitação |  |
| Revisão de texto | Sinônimos | `.uno:ThesaurusDialog` | Dicionário de sinônimos... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Dicionário de sinônimos pt-BR |  |
| Revisão de texto | Idioma do texto | `.uno:SetLanguageAllTextMenu` | Para todo o texto | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Define idioma da seleção/documento |  |
| Revisão de texto | Contagem de palavras | `.uno:WordCountDialog` | Contagem de palavras... | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Palavras e caracteres da seleção e do documento |  |
| Revisão de texto | Verificar acessibilidade | `.uno:SidebarDeck.A11yCheckDeck` | Abrir painel de verificação de acessibilidade | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Aponta imagens sem texto alternativo, títulos etc. |  |
| Revisão de texto | Revisão gramatical offline avançada | — |  | Lacuna |  | Pendente (Etapa 3) | P3 | Avaliar LanguageTool local e Lightproof pt-BR | Avaliação separada: LanguageTool local exige Java e servidor local (300 MB); a base já traz verificação gramatical básica para pt-BR no dicionário. |
| Comentários | Novo comentário | `.uno:InsertAnnotation` | Anotação | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P0 | Preservado em DOCX com autor e data |  |
| Comentários | Excluir todos os comentários | `.uno:DeleteAllNotes` | Excluir todas as anotações | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Remove comentários |  |
| Comentários | Mostrar comentários | `.uno:ShowAnnotations` | Anotações | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Mostra/oculta a margem de comentários |  |
| Controle de alterações | Controlar alterações | `.uno:TrackChanges` | Registrar | Na base (comando verificado) | ida_e_volta | Pendente (Etapa 3) | P0 | Grava inserções, exclusões e formatação com autor |  |
| Controle de alterações | Mostrar alterações | `.uno:ShowTrackedChanges` | Mostrar | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Alterna exibição |  |
| Controle de alterações | Alteração anterior | `.uno:PreviousTrackedChange` | Anterior | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Navega |  |
| Controle de alterações | Próxima alteração | `.uno:NextTrackedChange` | Próxima | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Navega |  |
| Controle de alterações | Aceitar | `.uno:AcceptTrackedChange` | Aceitar | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Aceita a alteração atual |  |
| Controle de alterações | Rejeitar | `.uno:RejectTrackedChange` | Rejeitar | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Rejeita a alteração atual |  |
| Controle de alterações | Aceitar todas | `.uno:AcceptAllTrackedChanges` | Aceitar todas | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Aceita todas |  |
| Controle de alterações | Rejeitar todas | `.uno:RejectAllTrackedChanges` | Rejeitar todas | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Rejeita todas |  |
| Controle de alterações | Gerenciar alterações | `.uno:AcceptTrackedChanges` | Gerenciar... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Lista e filtra alterações |  |
| Controle de alterações | Proteger controle de alterações | `.uno:ProtectTraceChangeMode` | Proteger... | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Exige senha para desligar |  |
| Comparar | Comparar documentos | `.uno:CompareDocuments` | Comparar documento... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Gera alterações controladas a partir de duas versões |  |
| Comparar | Combinar documentos | `.uno:MergeDocuments` | Mesclar documento... | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Junta revisões de cópias |  |

## EXIBIR

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
| Modos | Layout de impressão | `.uno:PrintLayout` | Normal | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Páginas com limites visíveis |  |
| Modos | Layout da web | `.uno:BrowseView` | Página internet | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Texto sem paginação |  |
| Modos | Modo de leitura | — |  | Lacuna |  | Pendente (Etapa 3) | P2 | Leitura em tela cheia, sem faixa de opções, páginas lado a lado | A base tem tela inteira (.uno:FullScreen) e exibição de livro (.uno:ShowBookview); um modo de leitura dedicado será um comando da extensão AY que combina os dois e bloqueia edição. |
| Modos | Tela inteira | `.uno:FullScreen` | Tela inteira | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Esconde barras |  |
| Zoom | Zoom | `.uno:Zoom` | Zoom... | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Diálogo de zoom |  |
| Zoom | 100% | `.uno:Zoom100Percent` | 100% | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Zoom real |  |
| Zoom | Página inteira | `.uno:ZoomPage` | Página inteira | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Ajusta à página |  |
| Zoom | Largura da página | `.uno:ZoomPageWidth` | Largura da página | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Ajusta à largura |  |
| Zoom | Uma página | `.uno:ShowSinglePage` | Uma página | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Uma página por linha |  |
| Zoom | Várias páginas | `.uno:ShowTwoPages` | Duas páginas | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Páginas lado a lado |  |
| Zoom | Exibição de livro | `.uno:ShowBookview` | Visualização de livro | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Páginas espelhadas |  |
| Mostrar | Régua | `.uno:Ruler` | Réguas | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Mostra/oculta a régua |  |
| Mostrar | Painel de navegação | `.uno:Navigator` | Navegador | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Títulos, tabelas, imagens e comentários |  |
| Mostrar | Barra lateral | `.uno:Sidebar` | Barra lateral | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Propriedades, estilos e galeria |  |
| Mostrar | Marcas de formatação | `.uno:ControlCodes` | Marcas de formatação | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Mostra ¶ |  |
| Mostrar | Limites do texto | `.uno:ViewBounds` | Limites de texto (descontinuado) | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Mostra margens |  |
| Mostrar | Grade | `.uno:GridVisible` | Exibir grade | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Grade de alinhamento |  |
| Mostrar | Ocultar espaço em branco | `.uno:ShowWhitespace` | Espaços em branco | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Oculta margens superior/inferior |  |
| Janela e tema | Nova janela | `.uno:NewWindow` | Nova janela | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Segunda janela do mesmo documento |  |
| Janela e tema | Fechar janela | `.uno:CloseWin` | Fechar janela | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Fecha a janela atual |  |
| Janela e tema | Alternar entre janelas | `.uno:WindowList` | Janela | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Lista janelas abertas |  |
| Janela e tema | Tema claro/escuro | `.uno:ChangeTheme` | Modo escuro | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Segue o sistema ou força claro/escuro |  |

## AJUDA

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
| Ajuda | Ajuda offline | `.uno:HelpIndex` | Ajuda do AY ESCREVA | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Abre a ajuda local em pt-BR (sem internet) |  |
| Ajuda | Guia de utilização do AY | — |  | Lacuna |  | Pendente (Etapa 3) | P1 | Guia próprio do AY, offline | Conteúdo próprio a escrever e comando da extensão AY para abri-lo. |
| Ajuda | Atalhos de teclado | — |  | Lacuna |  | Pendente (Etapa 3) | P1 | Lista de atalhos em pt-BR | Sem tela de atalhos na base (só personalização em Ferramentas > Personalizar). Gerar página própria a partir da configuração. |
| Sobre | Sobre o AY ESCREVA | `.uno:About` | Sobre o AY ESCREVA | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Mostra versão, base e licenças |  |
| Sobre | Licenças | `.uno:ShowLicense` | Informações sobre a licença | Na base (comando verificado) |  | Pendente (Etapa 3) | P0 | Texto das licenças (MPL, LGPL e terceiros) |  |
| Sobre | Créditos | `.uno:ShowCredits` | Créditos do AY ESCREVA | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Créditos da base |  |
| Diagnóstico | Reiniciar em modo de segurança | `.uno:SafeMode` | Reiniciar em modo de reparo... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Restaura perfil e desativa extensões |  |
| Diagnóstico | Relatório de diagnóstico | — |  | Lacuna |  | Pendente (Etapa 3) | P2 | Gera arquivo local com versão, sistema e configuração (sem conteúdo de documentos) | Comando da extensão AY. |
| Diagnóstico | Verificar atualizações (opcional) | — |  | Lacuna |  | Pendente (Etapa 3) | P2 | Só consulta quando o usuário pede; nunca envia conteúdo | A verificação da base está desligada. Implementar consulta própria do AY. |

## TABELA (contextual)

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
|  | Inserir linha acima | `.uno:InsertRowsBefore` | Linhas acima | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Insere linha |  |
|  | Inserir linha abaixo | `.uno:InsertRowsAfter` | Linhas abaixo | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Insere linha |  |
|  | Inserir coluna à esquerda | `.uno:InsertColumnsBefore` | Colunas antes | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Insere coluna |  |
|  | Inserir coluna à direita | `.uno:InsertColumnsAfter` | Colunas após | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Insere coluna |  |
|  | Excluir linhas | `.uno:DeleteRows` | Linhas | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Exclui linhas |  |
|  | Excluir colunas | `.uno:DeleteColumns` | Colunas | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Exclui colunas |  |
|  | Excluir tabela | `.uno:DeleteTable` | Tabela | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Exclui a tabela |  |
|  | Mesclar células | `.uno:MergeCells` | Mesclar células | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Mescla preservada em DOCX |  |
|  | Dividir células | `.uno:SplitCell` | Dividir células... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Divide células |  |
|  | Ajustar largura das colunas | `.uno:SetOptimalColumnWidth` | Largura ideal da coluna | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Largura ideal |  |
|  | Bordas | `.uno:SetBorderStyle` | Bordas (tecle Shift para sobrescrever) | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Bordas preservadas em DOCX |  |
|  | Sombreamento | `.uno:TableCellBackgroundColor` | Cor do plano de fundo das células da tabela | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Cor de fundo da célula |  |
|  | Estilos de tabela | `.uno:AutoFormat` | Estilos de autoformatação... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Formatos prontos |  |
|  | Classificar | `.uno:SortDialog` | Ordenar... | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Ordena linhas |  |
|  | Propriedades da tabela | `.uno:TableDialog` | Propriedades... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Largura, alinhamento, cabeçalho repetido |  |
|  | Selecionar tabela | `.uno:SelectTable` | Tabela | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Seleciona a tabela |  |

## IMAGEM (contextual)

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
|  | Recortar | `.uno:Crop` | Recortar | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Recorte preservado em DOCX |  |
|  | Texto alternativo | `.uno:ObjectTitleDescription` | Texto alternativo... | Na base (comando verificado) | aceite_etapa1, ida_e_volta | Pendente (Etapa 3) | P0 | Descrição preservada em ODT e DOCX |  |
|  | Trocar imagem | `.uno:ChangePicture` | Substituir... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Mantém tamanho e posição |  |
|  | Compactar imagem | `.uno:CompressGraphic` | Comprimir... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Reduz tamanho do arquivo |  |
|  | Salvar imagem | `.uno:SaveGraphic` | Salvar... | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Exporta a imagem |  |
|  | Girar à esquerda | `.uno:RotateLeft` | Girar 90° à esquerda | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | 90° |  |
|  | Girar à direita | `.uno:RotateRight` | Girar 90° à direita | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | 90° |  |
|  | Espelhar vertical | `.uno:FlipVertical` | Inverter verticalmente | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Espelha |  |
|  | Espelhar horizontal | `.uno:FlipHorizontal` | Inverter horizontalmente | Na base (comando verificado) |  | Pendente (Etapa 3) | P3 | Espelha |  |
|  | Propriedades da imagem | `.uno:GraphicDialog` | Propriedades... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Tamanho, posição e quebra |  |
|  | Legenda | `.uno:InsertCaptionDialog` | Legenda... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Figura numerada |  |

## FORMA (contextual)

| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |
|---|---|---|---|---|---|---|---|---|---|
|  | Preenchimento | `.uno:FillColor` | Cor do preenchimento | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Cor de preenchimento |  |
|  | Área | `.uno:FormatArea` | Área... | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Gradiente, padrão, transparência |  |
|  | Linha | `.uno:FormatLine` | Linha... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Contorno |  |
|  | Posição e tamanho | `.uno:TransformDialog` | Posição e tamanho... | Na base (comando verificado) |  | Pendente (Etapa 3) | P1 | Posição exata |  |
|  | Agrupar | `.uno:FormatGroup` | Agrupar | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Agrupa formas |  |
|  | Desagrupar | `.uno:FormatUngroup` | Desagrupar | Na base (comando verificado) |  | Pendente (Etapa 3) | P2 | Desagrupa |  |
