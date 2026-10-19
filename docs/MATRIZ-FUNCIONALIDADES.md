# Matriz de funcionalidades do AY ESCREVA

> Gerado por `tests/uno/comandos.py` a partir de `ui/abas.json`, do mapa da faixa e do teste pela interface de 2026-10-19T19:45:29, em 2026-10-19. Não editar à mão.

**Como ler as colunas**

- **Comando encontrado**: o comando existe no motor (o quadro do Writer devolveu um despachante, ou há controlador de menu) — verificado em `tests/uno/comandos.py`. Não diz nada sobre botão.
- **Funcionalidade implementada**: há um botão na faixa de opções do AY ligado a esse comando (ou a função é oferecida por outro controle, indicado). *Confirmado pela interface* = o teste dentro do aplicativo encontrou o botão na aba (`tests/interface`).
- **Funcionamento validado**: *Pela interface* = o teste clicou no botão da faixa, confirmou o comando disparado e conferiu o efeito no documento ou na exibição. *Acionado pela interface* = o clique disparou o comando certo (e o diálogo/lista que abriu foi registrado), mas o efeito não tem verificação automática. *Por API* = a função foi exercitada de ponta a ponta pelos testes de documento, sem clicar no botão.
- **Prioridade**: P0 = Etapas 1-2, P1 = Etapa 3, P2 = Etapa 4, P3 = avaliar.

**Resumo** (239 funções): comando encontrado 233 · implementadas 233 (botão confirmado pela interface: 210) · validadas pela interface 35 · só acionadas pela interface 113 · validadas por API 49 · pendentes 6


## Arquivo

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
| Novo | Novo documento | `.uno:AddDirect` | Sim | Sim — botão na faixa (confirmado pela interface) | Por API: aceite_etapa1 | P0 | Abre documento de texto em branco |  |
| Novo | Modelos | `.uno:NewDoc` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Abre o gerenciador de modelos e cria documento a partir de um modelo |  |
| Documento | Abrir | `.uno:Open` | Sim | Sim — botão na faixa (confirmado pela interface) | Por API: ida_e_volta | P0 | Abre DOCX, ODT, DOC, RTF e TXT locais |  |
| Documento | Recentes | `.uno:Open` | Sim | Sim, por outro controle (seta do botão Abrir) | Por API: ida_e_volta | P1 | Lista os documentos recentes do perfil local |  |
| Documento | Salvar | `.uno:Save` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ODT gravado pelo botão Salvar, sem aviso (formato nativo) · Por API: aceite_etapa1 | P0 | Salva no formato atual; avisa possíveis perdas antes de salvar fora do ODT |  |
| Documento | Salvar como | `.uno:SaveAs` | Sim | Sim — botão na faixa (confirmado pela interface) | Por API: aceite_etapa1, ida_e_volta | P0 | Salva em ODT, DOCX, DOC, RTF ou TXT com aviso de perdas |  |
| Documento | Salvar uma cópia | `.uno:SaveACopy` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Grava cópia sem trocar o documento aberto |  |
| Documento | Recarregar | `.uno:Reload` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Recarrega a última versão salva |  |
| Documento | Fechar | `.uno:CloseDoc` | Sim | Sim — botão na faixa (confirmado pela interface) | Por API: aceite_etapa1 | P0 | Fecha o documento perguntando se há alterações |  |
| Exportar e imprimir | Exportar PDF | `.uno:ExportToPDF` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Opções do PDF" (fechado pelo teste) (efeito não conferido) · Por API: aceite_etapa1 (PDF e PDF/UA) | P0 | Exporta PDF, PDF/A e PDF/UA marcado |  |
| Exportar e imprimir | Exportar PDF direto | `.uno:ExportDirectToPDF` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Exportar" (fechado pelo teste) (efeito não conferido) · Por API: aceite_etapa1 | P1 | Exporta PDF com as opções padrão |  |
| Exportar e imprimir | Imprimir | `.uno:Print` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Imprimir" (fechado pelo teste) (efeito não conferido) · Por API: impressao | P0 | Imprime pela fila do sistema |  |
| Exportar e imprimir | Visualizar impressão | `.uno:PrintPreview` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P0 | Mostra prévia paginada antes de imprimir |  |
| Informações | Propriedades | `.uno:SetDocumentProperties` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Propriedades de “faixa-teste”" (fechado pelo teste) (efeito não conferido) | P1 | Edita título, autor, palavras-chave e mostra estatísticas |  |
| Informações | Versões | `.uno:VersionDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo " faixa-teste" (fechado pelo teste) (efeito não conferido) | P2 | Salva e compara versões dentro do ODT |  |
| Informações | Assinatura digital | `.uno:Signature` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Confirmação" (fechado pelo teste) (efeito não conferido) | P3 | Assina com certificado local do usuário |  |
| Informações | Recuperação de documentos | `ayescreva:Recuperacao` | Sim (extensão AY) | Sim — botão na faixa (confirmado pela interface) | Pela interface: abriria backup (arquivo existe; abertura simulada no teste) | P1 | Abre as pastas de cópias de segurança e de recuperação automática do perfil | A recuperação após falha é automática (oferecida ao reabrir); este botão dá acesso manual às cópias. |
| Informações | Configurações | `.uno:OptionsTreeDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Opções - AY ESCREVA - Dados do usuário" (fechado pelo teste) (efeito não conferido) | P1 | Abre as opções do aplicativo |  |

## Página Inicial

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
| Área de transferência | Colar | `.uno:Paste` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P0 | Cola mantendo formatação; seta com opções |  |
| Área de transferência | Recortar | `.uno:Cut` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P0 | Recorta a seleção |  |
| Área de transferência | Copiar | `.uno:Copy` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P0 | Copia a seleção |  |
| Área de transferência | Pincel de formatação | `.uno:FormatPaintbrush` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Copia a formatação para outro trecho |  |
| Área de transferência | Colar especial | `.uno:PasteSpecial` | Sim | Sim, por outro controle (seta do botão Colar) | Não validado | P1 | Cola como texto sem formatação e outros formatos |  |
| Fonte | Fonte | `.uno:CharFontName` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Caractere" (fechado pelo teste) (efeito não conferido) · Por API: aceite_etapa1 | P0 | Lista fontes instaladas e as fontes do AY |  |
| Fonte | Tamanho | `.uno:FontHeight` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: aceite_etapa1 | P0 | Define tamanho em pontos |  |
| Fonte | Aumentar fonte | `.uno:Grow` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: CharHeight=14.0 depois do clique | P1 | Aumenta o tamanho |  |
| Fonte | Diminuir fonte | `.uno:Shrink` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: CharHeight=10.0 depois do clique | P1 | Diminui o tamanho |  |
| Fonte | Negrito | `.uno:Bold` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: CharWeight=150.0 depois do clique · Por API: aceite_etapa1 | P0 | Preservado em ODT e DOCX |  |
| Fonte | Itálico | `.uno:Italic` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: CharPosture=ITALIC depois do clique · Por API: aceite_etapa1 | P0 | Preservado em ODT e DOCX |  |
| Fonte | Sublinhado | `.uno:Underline` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: CharUnderline=1 depois do clique · Por API: aceite_etapa1 | P0 | Preservado em ODT e DOCX |  |
| Fonte | Tachado | `.uno:Strikeout` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: CharStrikeout=1 depois do clique · Por API: aceite_etapa1 | P0 | Preservado em ODT e DOCX |  |
| Fonte | Subscrito | `.uno:SubScript` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: CharEscapement=-14000 depois do clique | P0 | Preservado em ODT e DOCX |  |
| Fonte | Sobrescrito | `.uno:SuperScript` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: CharEscapement=14000 depois do clique · Por API: aceite_etapa1 | P0 | Preservado em ODT e DOCX |  |
| Fonte | Cor da fonte | `.uno:Color` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P0 | Preservada em ODT e DOCX |  |
| Fonte | Realce | `.uno:CharBackColor` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: aceite_etapa1 (realce no DOCX) | P0 | Vira realce (w:highlight) no DOCX |  |
| Fonte | Limpar formatação | `.uno:ResetAttributes` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: CharWeight=100.0 depois do clique | P1 | Remove formatação direta |  |
| Fonte | Caractere (diálogo) | `.uno:FontDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Caractere" (fechado pelo teste) (efeito não conferido) | P1 | Todas as opções de caractere |  |
| Parágrafo | Marcadores | `.uno:DefaultBullet` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: NumberingIsNumber=True depois do clique · Por API: ida_e_volta | P0 | Lista com marcadores preservada em DOCX |  |
| Parágrafo | Numeração | `.uno:DefaultNumbering` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: NumberingIsNumber=True depois do clique · Por API: ida_e_volta | P0 | Lista numerada preservada em DOCX |  |
| Parágrafo | Lista multinível | `.uno:SetOutline` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Marcadores e numeração" (fechado pelo teste) (efeito não conferido) | P1 | Numeração de títulos e listas em níveis |  |
| Parágrafo | Diminuir recuo | `.uno:DecrementIndent` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ParaLeftMargin=0 depois do clique | P0 | Altera o recuo à esquerda |  |
| Parágrafo | Aumentar recuo | `.uno:IncrementIndent` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ParaLeftMargin=1251 depois do clique | P0 | Altera o recuo à esquerda |  |
| Parágrafo | Marcas de formatação | `.uno:ControlCodes` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ShowNonprintingCharacters: False → True | P1 | Mostra ¶, espaços e tabulações |  |
| Parágrafo | Alinhar à esquerda | `.uno:LeftPara` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ParaAdjust=0 depois do clique | P0 | Preservado em ODT e DOCX |  |
| Parágrafo | Centralizar | `.uno:CenterPara` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ParaAdjust=3 depois do clique · Por API: aceite_etapa1 | P0 | Preservado em ODT e DOCX |  |
| Parágrafo | Alinhar à direita | `.uno:RightPara` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ParaAdjust=1 depois do clique | P0 | Preservado em ODT e DOCX |  |
| Parágrafo | Justificar | `.uno:JustifyPara` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ParaAdjust=2 depois do clique · Por API: aceite_etapa1 | P0 | Preservado em ODT e DOCX |  |
| Parágrafo | Espaçamento entre linhas | `.uno:LineSpacing` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu lista "" (fechado pelo teste) (efeito não conferido) | P0 | Simples, 1,15, 1,5, duplo e personalizado |  |
| Parágrafo | Aumentar espaço entre parágrafos | `.uno:ParaspaceIncrease` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Altera espaço antes/depois |  |
| Parágrafo | Diminuir espaço entre parágrafos | `.uno:ParaspaceDecrease` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Altera espaço antes/depois |  |
| Parágrafo | Parágrafo (diálogo) | `.uno:ParagraphDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Parágrafo" (fechado pelo teste) (efeito não conferido) | P1 | Recuos, espaçamento, fluxo e tabulações |  |
| Estilos | Estilo do parágrafo | `.uno:StyleApply` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: aceite_etapa1 (Título 1) | P0 | Aplica Título 1..n, Corpo de texto etc. |  |
| Estilos | Painel de estilos | `.uno:DesignerDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Cria e modifica estilos |  |
| Edição | Localizar e substituir | `.uno:SearchDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu janela não modal "" (fechado pelo teste) (efeito não conferido) | P0 | Busca com expressões regulares e formatação |  |
| Edição | Selecionar tudo | `.uno:SelectAll` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Seleciona o documento |  |

## Inserir

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
| Páginas | Capa | `.uno:TitlePageDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Páginas de rosto" (fechado pelo teste) (efeito não conferido) | P2 | Insere página de rosto com estilo próprio | A base oferece o diálogo de páginas de título; uma galeria de capas prontas (como no Word) será feita com modelos AY. |
| Páginas | Página em branco | `ayescreva:PaginaEmBranco` | Sim (extensão AY) | Sim — botão na faixa (confirmado pela interface) | Pela interface: paginas: 2 → 4 | P1 | Insere uma página vazia no ponto do cursor |  |
| Páginas | Quebra de página | `.uno:InsertPagebreak` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: paginas: 1 → 2 · Por API: aceite_etapa1 | P0 | Preservada em DOCX |  |
| Páginas | Quebras (página, coluna, linha) | `.uno:InsertBreak` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Inserir quebra" (fechado pelo teste) (efeito não conferido) · Por API: ida_e_volta (3 seções) | P1 | Inclui quebra com troca de estilo de página |  |
| Páginas | Seção | `.uno:InsertSection` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Inserir seção" (fechado pelo teste) (efeito não conferido) | P1 | Seção com colunas e proteção |  |
| Tabelas | Tabela | `.uno:InsertTable` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: aceite_etapa1, ida_e_volta (mescladas) | P0 | Insere tabela; preservada em ODT e DOCX |  |
| Ilustrações | Imagem | `.uno:InsertGraphic` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Inserir figura" (fechado pelo teste) (efeito não conferido) · Por API: aceite_etapa1 | P0 | Insere imagem embutida com texto alternativo |  |
| Ilustrações | Formas | `.uno:BasicShapes` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Retângulos, elipses, setas etc. |  |
| Ilustrações | Gráfico | `.uno:InsertObjectChart` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Gráfico com dados internos |  |
| Ilustrações | Fontwork (texto artístico) | `.uno:FontworkGalleryFloater` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu janela não modal "Galeria do Fontwork" (fechado pelo teste) (efeito não conferido) | P3 | Texto decorativo |  |
| Links e comentários | Link | `.uno:HyperlinkDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu janela não modal "" (fechado pelo teste) (efeito não conferido) · Por API: ida_e_volta | P0 | Hiperlink exige Ctrl+clique e não é acessado ao abrir |  |
| Links e comentários | Indicador | `.uno:InsertBookmark` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Marca-páginas" (fechado pelo teste) (efeito não conferido) · Por API: ida_e_volta | P1 | Preservado em DOCX |  |
| Links e comentários | Referência cruzada | `.uno:InsertReferenceField` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "" (fechado pelo teste) (efeito não conferido) · Por API: ida_e_volta | P1 | Preservada em DOCX |  |
| Links e comentários | Comentário | `.uno:InsertAnnotation` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: comentarios: 0 → 1 · Por API: ida_e_volta | P0 | Preservado em ODT e DOCX |  |
| Cabeçalho e rodapé | Cabeçalho | `.uno:InsertPageHeader` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: aceite_etapa1, ida_e_volta | P0 | Ativa cabeçalho do estilo de página |  |
| Cabeçalho e rodapé | Rodapé | `.uno:InsertPageFooter` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: aceite_etapa1, ida_e_volta | P0 | Ativa rodapé do estilo de página |  |
| Cabeçalho e rodapé | Número de página | `.uno:PageNumberWizard` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Assistente de numeração de página" (fechado pelo teste) (efeito não conferido) · Por API: aceite_etapa1 (campo de página) | P0 | Insere número de página com posição e formato |  |
| Texto | Caixa de texto | `.uno:DrawText` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: ida_e_volta (caixa de texto) | P1 | Caixa de texto exportada como forma DOCX |  |
| Texto | Quadro | `.uno:InsertFrame` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Quadro de texto posicionável |  |
| Texto | Campos | `.uno:InsertFieldCtrl` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu janela não modal "" (fechado pelo teste) (efeito não conferido) | P1 | Data, hora, autor, título, contagem de páginas |  |
| Texto | Data | `.uno:InsertDateField` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Campo de data |  |
| Símbolos | Equação | `.uno:InsertObjectStarMath` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: ida_e_volta (OMML) | P2 | Equação editável; OMML do DOCX importado vira equação | Editor de equações usa a sintaxe da base (não o editor do Word); exportação para OMML coberta pelo filtro. |
| Símbolos | Símbolo | `.uno:CharmapControl` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Símbolos recentes e caracteres especiais |  |

## Desenhar

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
| Ferramentas | Selecionar traços | `.uno:SelectObject` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Seleciona traços e formas |  |
| Ferramentas | Caneta (linha à mão livre) | `.uno:Freeline_Unfilled` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Desenha traço com mouse ou caneta; salvo como forma em ODT e DOCX |  |
| Ferramentas | Forma livre preenchida | `.uno:Freeline` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Desenha forma fechada |  |
| Ferramentas | Linha | `.uno:Line` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Linha reta |  |
| Ferramentas | Curva | `.uno:Bezier_Unfilled` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P3 | Curva de Bézier |  |
| Ferramentas | Marca-texto | — | — | Não — pendente | Não validado | P2 | Traço largo e translúcido sobre o texto | Sem ferramenta própria na base; previsto como predefinição de traço (amarelo, translúcido, largo) na extensão AY. |
| Ferramentas | Borracha | — | — | Não — pendente | Não validado | P3 | Apaga traços passando o cursor | A base só exclui o traço selecionado (botão Excluir traço). Borracha por arrasto exige código C++ (Nível 2). |
| Ferramentas | Sensibilidade à pressão da caneta | — | — | Não — pendente | Não validado | P3 | Espessura varia com a pressão | Não suportado pela base; tinta do Word (InkML) é importada como imagem ou forma, sem pressão. |
| Traço | Cor do traço | `.uno:XLineColor` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Altera a cor da linha selecionada |  |
| Traço | Espessura e estilo | `.uno:FormatLine` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Linha" (fechado pelo teste) (efeito não conferido) | P2 | Espessura, estilo e transparência |  |
| Traço | Agrupar | `.uno:FormatGroup` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P3 | Agrupa traços |  |
| Traço | Excluir traço | `.uno:Delete` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Remove o traço selecionado |  |

## Design

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
| Formatação do documento | Temas, cores e fontes do documento | `.uno:ThemeDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Tema" (fechado pelo teste) (efeito não conferido) | P2 | Aplica tema de cores ao documento |  |
| Formatação do documento | Conjuntos de estilos | `.uno:LoadStyles` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Carregar estilos do modelo" (fechado pelo teste) (efeito não conferido) | P2 | Importa estilos de um modelo | A base importa estilos de modelos; a galeria visual de conjuntos (como no Word) será feita com modelos AY. |
| Plano de fundo da página | Marca-d'água | `.uno:Watermark` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Marca-d'água de texto preservada em DOCX |  |
| Plano de fundo da página | Cor e bordas da página | `.uno:PageDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Estilo de página: Estilo de página Padrão" (fechado pelo teste) (efeito não conferido) | P2 | Cor de fundo (aba Área) e bordas (aba Bordas) do estilo de página |  |
| Plano de fundo da página | Bordas de página | `.uno:PageDialog` | Sim | Sim, por outro controle (botão Cor e bordas da página) | Não validado | P2 | Bordas do estilo de página |  |

## Layout

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
| Configurar página | Margens | `.uno:PageMargin` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P0 | Predefinições e personalizadas |  |
| Configurar página | Orientação | `.uno:Orientation` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: ida_e_volta (paisagem) | P0 | Retrato/paisagem |  |
| Configurar página | Tamanho do papel | `.uno:AttributePageSize` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P0 | A4, Carta, Ofício etc. |  |
| Configurar página | Colunas | `.uno:PageColumnType` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: ida_e_volta (2 colunas) | P1 | 1 a 3 colunas; preservadas em DOCX |  |
| Configurar página | Quebras de página e seção | `.uno:InsertBreak` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: ida_e_volta (3 seções) | P1 | Quebra com novo estilo de página = seção do Word |  |
| Configurar página | Hifenização | `.uno:Hyphenate` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Hifenização pt-BR |  |
| Configurar página | Numeração de linhas | `.uno:LineNumberingDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Numeração de linhas" (fechado pelo teste) (efeito não conferido) | P3 | Numera linhas |  |
| Configurar página | Estilo de página (diálogo) | `.uno:PageDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Estilo de página: Estilo de página Padrão" (fechado pelo teste) (efeito não conferido) | P1 | Todas as opções de página |  |
| Parágrafo | Recuos e espaçamento | `.uno:ParagraphDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Recuos e espaços antes/depois |  |
| Organizar | Sem quebra automática | `.uno:WrapOff` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Texto acima e abaixo do objeto |  |
| Organizar | Quebra automática | `.uno:WrapOn` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Texto em volta do objeto |  |
| Organizar | Quebra ideal | `.uno:WrapIdeal` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Texto no lado mais largo |  |
| Organizar | Atrás/na frente do texto | `.uno:WrapThrough` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Objeto sobre o texto |  |
| Organizar | Trazer para frente | `.uno:BringToFront` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Ordem de sobreposição |  |
| Organizar | Enviar para trás | `.uno:SendToBack` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Ordem de sobreposição |  |
| Organizar | Ancorar à página | `.uno:SetAnchorToPage` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Posição fixa na página |  |
| Organizar | Ancorar ao parágrafo | `.uno:SetAnchorToPara` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Objeto acompanha o parágrafo |  |
| Organizar | Ancorar como caractere | `.uno:SetAnchorToChar` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Objeto em linha com o texto |  |
| Organizar | Alinhar objetos | `.uno:ObjectAlignLeft` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P3 | Alinha objetos entre si |  |
| Organizar | Girar | `.uno:ToggleObjectRotateMode` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P3 | Rotação livre |  |

## Referências

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
| Sumário | Sumário e índices | `.uno:InsertMultiIndex` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: ida_e_volta (sumário) | P1 | Gera sumário a partir dos títulos (também bibliografia, ilustrações e índice remissivo, escolhendo o tipo); preservado em DOCX |  |
| Sumário | Atualizar sumário | `.uno:UpdateCurIndex` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Atualiza números de página e entradas |  |
| Sumário | Atualizar todos os índices | `.uno:UpdateAllIndexes` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Atualiza sumários, listas e índices |  |
| Notas | Nota de rodapé | `.uno:InsertFootnote` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: notasRodape: 0 → 1 · Por API: ida_e_volta | P0 | Preservada em ODT e DOCX |  |
| Notas | Nota de fim | `.uno:InsertEndnote` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: notasFim: 0 → 1 · Por API: ida_e_volta | P0 | Preservada em ODT e DOCX |  |
| Notas | Configurar notas | `.uno:FootnoteDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Configurações de notas de rodapé e notas de fim" (fechado pelo teste) (efeito não conferido) | P2 | Numeração, posição e separador |  |
| Citações e bibliografia | Inserir citação | `.uno:InsertAuthoritiesEntry` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu janela não modal "" (fechado pelo teste) (efeito não conferido) | P2 | Entrada bibliográfica no texto |  |
| Citações e bibliografia | Banco de dados bibliográfico | `.uno:BibliographyComponent` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P3 | Gerencia fontes locais |  |
| Citações e bibliografia | Bibliografia | `.uno:InsertMultiIndex` | Sim | Sim, por outro controle (botão Sumário e índices, tipo Bibliografia) | Por API: ida_e_volta (sumário) | P2 | Índice do tipo Bibliografia | Estilos ABNT exigem modelo AY. |
| Legendas | Inserir legenda | `.uno:InsertCaptionDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Inserir legenda" (fechado pelo teste) (efeito não conferido) | P1 | Figura/Tabela numeradas |  |
| Legendas | Lista de figuras | `.uno:InsertMultiIndex` | Sim | Sim, por outro controle (botão Sumário e índices, tipo Índice de ilustrações) | Por API: ida_e_volta (sumário) | P2 | Índice do tipo Ilustrações |  |
| Legendas | Referência cruzada | `.uno:InsertReferenceField` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: ida_e_volta | P1 | Referência a títulos, legendas e indicadores |  |
| Índice remissivo | Marcar entrada | `.uno:InsertIndexesEntry` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu janela não modal "" (fechado pelo teste) (efeito não conferido) | P2 | Marca termo para o índice |  |
| Índice remissivo | Inserir índice remissivo | `.uno:InsertMultiIndex` | Sim | Sim, por outro controle (botão Sumário e índices, tipo Índice alfabético) | Por API: ida_e_volta (sumário) | P2 | Índice do tipo Alfabético |  |
| Índice remissivo | Atualizar campos | `.uno:UpdateFields` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Atualiza campos do documento |  |

## Correspondência

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
| Criar | Envelopes | `.uno:InsertEnvelope` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Envelope" (fechado pelo teste) (efeito não conferido) | P2 | Envelope com remetente e destinatário |  |
| Criar | Etiquetas | `.uno:InsertLabels` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Etiquetas" (fechado pelo teste) (efeito não conferido) | P2 | Folha de etiquetas (Pimaco/Avery) |  |
| Iniciar mala direta | Assistente de mala direta | `.uno:MailMergeWizard` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Importa destinatários (CSV, planilha) e gera documentos |  |
| Iniciar mala direta | Selecionar destinatários | `.uno:ChangeDatabaseField` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Troca a fonte de dados |  |
| Iniciar mala direta | Exibir fonte de dados | `.uno:ViewDataSourceBrowser` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Mostra registros e permite arrastar campos |  |
| Iniciar mala direta | Inserir campo de mesclagem | `.uno:InsertFieldCtrl` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu janela não modal "" (fechado pelo teste) (efeito não conferido) | P2 | Campos do banco de dados |  |
| Visualizar resultados | Primeiro registro | `.uno:MailMergeFirstEntry` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Prévia |  |
| Visualizar resultados | Registro anterior | `.uno:MailMergePrevEntry` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Prévia |  |
| Visualizar resultados | Próximo registro | `.uno:MailMergeNextEntry` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Prévia |  |
| Visualizar resultados | Último registro | `.uno:MailMergeLastEntry` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Prévia |  |
| Concluir | Gerar documentos | `.uno:MailMergeCreateDocuments` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Documento único com todos os registros |  |
| Concluir | Salvar documentos mesclados | `.uno:MailMergeSaveDocuments` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Um arquivo por registro ou arquivo único |  |
| Concluir | Imprimir documentos mesclados | `.uno:MailMergePrintDocuments` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Impressão em lote |  |
| Concluir | Enviar por e-mail | `.uno:MailMergeEmailDocuments` | Sim | Sim, por outro controle (fora da faixa por decisão de privacidade) | Não validado | P3 | Só com servidor configurado pelo usuário | Exige SMTP configurado pelo usuário; fica fora da faixa por padrão (o produto não envia nada sem autorização). |

## Revisão

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
| Revisão de texto | Ortografia e gramática | `.uno:SpellingAndGrammarDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu janela não modal "" (fechado pelo teste) (efeito não conferido) | P0 | Dicionário pt-BR offline (VERO) |  |
| Revisão de texto | Revisão automática | `.uno:SpellOnline` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P0 | Sublinha erros durante a digitação |  |
| Revisão de texto | Sinônimos | `.uno:ThesaurusDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Dicionário de sinônimos (Português (Brasil))" (fechado pelo teste) (efeito não conferido) | P1 | Dicionário de sinônimos pt-BR |  |
| Revisão de texto | Contagem de palavras | `.uno:WordCountDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P0 | Palavras e caracteres da seleção e do documento |  |
| Revisão de texto | Idioma do texto | `.uno:SetLanguageAllTextMenu` | Sim | Sim, por outro controle (clique no idioma, na barra de status) | Não validado | P1 | Define idioma da seleção/documento |  |
| Revisão de texto | Verificar acessibilidade | `.uno:SidebarDeck.A11yCheckDeck` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Aponta imagens sem texto alternativo, títulos etc. |  |
| Revisão de texto | Revisão gramatical offline avançada | — | — | Não — pendente | Não validado | P3 | Avaliar LanguageTool local e Lightproof pt-BR | Avaliação separada: LanguageTool local exige Java e servidor local (300 MB). |
| Comentários | Novo comentário | `.uno:InsertAnnotation` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) · Por API: ida_e_volta | P0 | Preservado em DOCX com autor e data |  |
| Comentários | Excluir todos os comentários | `.uno:DeleteAllNotes` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Remove comentários |  |
| Comentários | Mostrar comentários | `.uno:ShowAnnotations` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Mostra/oculta a margem de comentários |  |
| Controle de alterações | Controlar alterações | `.uno:TrackChanges` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: RecordChanges=True · Por API: ida_e_volta | P0 | Grava inserções, exclusões e formatação com autor |  |
| Controle de alterações | Mostrar alterações | `.uno:ShowTrackedChanges` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Alterna exibição |  |
| Controle de alterações | Gerenciar alterações | `.uno:AcceptTrackedChanges` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu janela não modal "" (fechado pelo teste) (efeito não conferido) | P1 | Lista e filtra alterações |  |
| Controle de alterações | Proteger controle de alterações | `.uno:ProtectTraceChangeMode` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P3 | Exige senha para desligar |  |
| Alterações | Aceitar | `.uno:AcceptTrackedChange` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P0 | Aceita a alteração atual |  |
| Alterações | Rejeitar | `.uno:RejectTrackedChange` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P0 | Rejeita a alteração atual |  |
| Alterações | Alteração anterior | `.uno:PreviousTrackedChange` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Navega |  |
| Alterações | Próxima alteração | `.uno:NextTrackedChange` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Navega |  |
| Alterações | Aceitar todas | `.uno:AcceptAllTrackedChanges` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P0 | Aceita todas |  |
| Alterações | Rejeitar todas | `.uno:RejectAllTrackedChanges` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P0 | Rejeita todas |  |
| Comparar | Comparar documentos | `.uno:CompareDocuments` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Gera alterações controladas a partir de duas versões |  |
| Comparar | Combinar documentos | `.uno:MergeDocuments` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P3 | Junta revisões de cópias |  |

## Exibir

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
| Modos de exibição | Layout de impressão | `.uno:PrintLayout` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P0 | Páginas com limites visíveis |  |
| Modos de exibição | Layout da web | `.uno:BrowseView` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P3 | Texto sem paginação |  |
| Modos de exibição | Tela inteira | `.uno:FullScreen` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Esconde barras |  |
| Modos de exibição | Modo de leitura | — | — | Não — pendente | Não validado | P2 | Leitura em tela cheia, sem faixa de opções, páginas lado a lado | Hoje: Tela inteira + Exibição de livro. Modo de leitura dedicado (sem edição) previsto na extensão AY. |
| Zoom | Zoom | `.uno:Zoom` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Zoom e leiaute" (fechado pelo teste) (efeito não conferido) | P0 | Diálogo de zoom |  |
| Zoom | 100% | `.uno:Zoom100Percent` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ZoomType=3 ZoomValue=100 | P1 | Zoom real |  |
| Zoom | Página inteira | `.uno:ZoomPage` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ZoomType=2 ZoomValue=70 | P1 | Ajusta à página |  |
| Zoom | Largura da página | `.uno:ZoomPageWidth` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ZoomType=1 ZoomValue=223 | P1 | Ajusta à largura |  |
| Zoom | Uma página | `.uno:ShowSinglePage` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Uma página por linha |  |
| Zoom | Várias páginas | `.uno:ShowTwoPages` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Páginas lado a lado |  |
| Zoom | Exibição de livro | `.uno:ShowBookview` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Páginas espelhadas |  |
| Mostrar | Régua | `.uno:Ruler` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: ShowRulers: True → False | P0 | Mostra/oculta a régua |  |
| Mostrar | Painel de navegação | `.uno:Navigator` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Títulos, tabelas, imagens e comentários |  |
| Mostrar | Barra lateral | `.uno:Sidebar` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Propriedades, estilos e galeria |  |
| Mostrar | Marcas de formatação | `.uno:ControlCodes` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P1 | Mostra ¶ |  |
| Mostrar | Limites do texto | `.uno:ViewBounds` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P2 | Mostra margens |  |
| Mostrar | Grade | `.uno:GridVisible` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface (efeito não conferido) | P3 | Grade de alinhamento |  |
| Mostrar | Ocultar espaço em branco | `.uno:ShowWhitespace` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P3 | Oculta margens superior/inferior |  |
| Janela e tema | Nova janela | `.uno:NewWindow` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Segunda janela do mesmo documento |  |
| Janela e tema | Fechar janela | `.uno:CloseWin` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Fecha a janela atual |  |
| Janela e tema | Alternar entre janelas | `.uno:WindowList` | Sim | Sim, por outro controle (menu ≡ > Janela) | Não validado | P2 | Lista janelas abertas |  |
| Janela e tema | Tema claro/escuro | `.uno:ChangeTheme` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Segue o sistema ou força claro/escuro |  |

## Ajuda

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
| Ajuda | Guia de utilização do AY | `ayescreva:Guia` | Sim (extensão AY) | Sim — botão na faixa (confirmado pela interface) | Pela interface: abriria guia.html (arquivo existe; abertura simulada no teste) | P1 | Guia próprio do AY, offline |  |
| Ajuda | Atalhos de teclado | `ayescreva:Atalhos` | Sim (extensão AY) | Sim — botão na faixa (confirmado pela interface) | Pela interface: abriria atalhos.html (arquivo existe; abertura simulada no teste) | P1 | Lista de atalhos em pt-BR, offline |  |
| Ajuda | Ajuda do motor (offline) | `.uno:HelpIndex` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Abre a ajuda local em pt-BR (sem internet) |  |
| Ajuda | Limitações conhecidas | `ayescreva:Limitacoes` | Sim (extensão AY) | Sim — botão na faixa (confirmado pela interface) | Pela interface: abriria limitacoes.html (arquivo existe; abertura simulada no teste) | P1 | Lista o que ainda não funciona ou difere do Word |  |
| Sobre | Sobre o AY ESCREVA | `.uno:About` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Sobre o AY ESCREVA" (fechado pelo teste) (efeito não conferido) | P0 | Mostra versão, base e licenças |  |
| Sobre | Licenças | `.uno:ShowLicense` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu dialogo "Licença e informações legais" (fechado pelo teste) (efeito não conferido) | P0 | Texto das licenças (MPL, LGPL e terceiros) |  |
| Sobre | Créditos | `.uno:ShowCredits` | Sim | Sim — botão na faixa (confirmado pela interface) | Acionado pela interface: abriu a janela "CREDITS.fodt (somente leitura) — AY ESCREVA Writer" (fechada pelo teste) (efeito não conferido) | P1 | Créditos da base |  |
| Diagnóstico | Relatório de diagnóstico | `ayescreva:Diagnostico` | Sim (extensão AY) | Sim — botão na faixa (confirmado pela interface) | Pela interface: relatório criado no perfil, sem conteúdo de documentos | P2 | Gera arquivo local com versão, sistema e configuração (sem conteúdo de documentos) |  |
| Diagnóstico | Reiniciar em modo de segurança | `.uno:SafeMode` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Restaura perfil e desativa extensões |  |
| Diagnóstico | Verificar atualizações (opcional) | — | — | Não — pendente | Não validado | P2 | Só consulta quando o usuário pede; nunca envia conteúdo | Depende do endereço definitivo do site; a verificação da base está desligada. |

## Tabela (contextual)

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
|  | Inserir linha acima | `.uno:InsertRowsBefore` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Insere linha |  |
|  | Inserir linha abaixo | `.uno:InsertRowsAfter` | Sim | Sim — botão na faixa (confirmado pela interface) | Pela interface: linhas: 2 → 3 | P1 | Insere linha |  |
|  | Inserir coluna à esquerda | `.uno:InsertColumnsBefore` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Insere coluna |  |
|  | Inserir coluna à direita | `.uno:InsertColumnsAfter` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Insere coluna |  |
|  | Excluir linhas | `.uno:DeleteRows` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Exclui linhas |  |
|  | Excluir colunas | `.uno:DeleteColumns` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Exclui colunas |  |
|  | Excluir tabela | `.uno:DeleteTable` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Exclui a tabela |  |
|  | Mesclar células | `.uno:MergeCells` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Mescla preservada em DOCX |  |
|  | Dividir células | `.uno:SplitCell` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Divide células |  |
|  | Ajustar largura das colunas | `.uno:SetOptimalColumnWidth` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Largura ideal |  |
|  | Bordas | `.uno:SetBorderStyle` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Bordas preservadas em DOCX |  |
|  | Sombreamento | `.uno:TableCellBackgroundColor` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Cor de fundo da célula |  |
|  | Estilos de tabela | `.uno:AutoFormat` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Formatos prontos |  |
|  | Classificar | `.uno:SortDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P3 | Ordena linhas |  |
|  | Propriedades da tabela | `.uno:TableDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Largura, alinhamento, cabeçalho repetido |  |
|  | Selecionar tabela | `.uno:SelectTable` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Seleciona a tabela |  |

## Imagem (contextual)

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
|  | Recortar | `.uno:Crop` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Recorte preservado em DOCX |  |
|  | Texto alternativo | `.uno:ObjectTitleDescription` | Sim | Sim — botão na faixa (confirmado pela interface) | Por API: aceite_etapa1, ida_e_volta | P0 | Descrição preservada em ODT e DOCX |  |
|  | Trocar imagem | `.uno:ChangePicture` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Mantém tamanho e posição |  |
|  | Compactar imagem | `.uno:CompressGraphic` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | Reduz tamanho do arquivo |  |
|  | Salvar imagem | `.uno:SaveGraphic` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P3 | Exporta a imagem |  |
|  | Girar à esquerda | `.uno:RotateLeft` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | 90° |  |
|  | Girar à direita | `.uno:RotateRight` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P2 | 90° |  |
|  | Espelhar vertical | `.uno:FlipVertical` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P3 | Espelha |  |
|  | Espelhar horizontal | `.uno:FlipHorizontal` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P3 | Espelha |  |
|  | Propriedades da imagem | `.uno:GraphicDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Tamanho, posição e quebra |  |
|  | Legenda | `.uno:InsertCaptionDialog` | Sim | Sim — botão na faixa (confirmado pela interface) | Não validado | P1 | Figura numerada |  |

## Forma (contextual)

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
|  | Preenchimento | `.uno:FillColor` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P1 | Cor de preenchimento |  |
|  | Área | `.uno:FormatArea` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P2 | Gradiente, padrão, transparência |  |
|  | Linha | `.uno:FormatLine` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P1 | Contorno |  |
|  | Posição e tamanho | `.uno:TransformDialog` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P1 | Posição exata |  |
|  | Agrupar | `.uno:FormatGroup` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P2 | Agrupa formas |  |
|  | Desagrupar | `.uno:FormatUngroup` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P2 | Desagrupa |  |

## Visualizar impressão (contextual)

| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |
|---|---|---|---|---|---|---|---|---|
|  | Imprimir | `.uno:Print` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Por API: impressao | P0 | Imprime a partir da prévia |  |
|  | Fechar visualização | `.uno:ClosePreview` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P0 | Volta à edição |  |
|  | Primeira página | `.uno:GoToStartOfDoc` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P1 | Navega na prévia |  |
|  | Página anterior | `.uno:PageUp` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P1 | Navega na prévia |  |
|  | Próxima página | `.uno:PageDown` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P1 | Navega na prévia |  |
|  | Última página | `.uno:GoToEndOfDoc` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P1 | Navega na prévia |  |
|  | Várias páginas na prévia | `.uno:ShowMultiplePages` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P1 | Escolhe quantas páginas ver |  |
|  | Tela inteira | `.uno:FullScreen` | Sim | Sim — botão na faixa (presença não confirmada pelo teste) | Não validado | P2 | Prévia em tela cheia |  |
