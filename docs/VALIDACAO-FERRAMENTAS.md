# Validação das ferramentas da faixa pelo efeito real

> Gerado por `tests/interface/relatorio_ferramentas.py` em 2026-10-22 a partir do teste pela interface de 2026-10-22T13:44:57 (fases 12 e 12b de `tests/interface/testar_faixa.ps1`). Não editar à mão.

Cada ferramenta: o documento é limpo e preparado, o teste **clica no botão da faixa**; quando abre um diálogo, os campos são
preenchidos pelos controles do próprio diálogo e ele é confirmado com **Enter do teclado de verdade**. O **efeito** é conferido
no documento pela API do motor; **Ctrl+Z** (o mesmo comando do teclado) tem de voltar ao estado anterior e **refazer**, ao
efeito; por fim o documento é **salvo em ODT e em DOCX, fechado e reaberto**, e o efeito é conferido no arquivo reaberto.
"—" = não se aplica (a ferramenta só muda a exibição ou a seleção, ou não altera o arquivo). As ferramentas com diálogo
rodam cada uma num aplicativo próprio (fase 12b): se o motor cair, a queda fica registrada só naquela ferramenta.

**Resumo:** 92 de 93 ferramentas testadas com efeito, desfazer/refazer e ODT conferidos; 2 com queda do motor durante o teste.

| Aba | Ferramenta | Efeito conferido | Desfazer / refazer | ODT reaberto | DOCX reaberto | Resultado |
|---|---|---|---|---|---|---|
| Arquivo | Propriedades | título do documento pelo diálogo Propriedades: '' → 'Título pelo diálogo' | — | sim | sim | validada |
| Página Inicial | Aumentar espaço entre parágrafos | espaço antes+depois do parágrafo: (0, 0) → (101, 101) | sim / sim | sim | sim | validada |
| Página Inicial | Caractere (diálogo) | tamanho da fonte de "alfa" pelo diálogo Caractere (20 pt): 12.0 → 20.0 | sim / sim | sim | sim | validada |
| Página Inicial | Colar | ocorrências de "zeta" (colado no fim do 2º parágrafo): 1 → 2 | sim / sim | sim | sim | validada |
| Página Inicial | Copiar | ocorrências de "beta" depois de copiar pela faixa e colar no fim: 1 → 2 | — | — | — | validada |
| Página Inicial | Cor da fonte | cor da fonte de "teta": -1 → 13181214 | sim / sim | sim | sim | validada |
| Página Inicial | Diminuir espaço entre parágrafos | espaço antes+depois do parágrafo: (499, 499) → (399, 399) | sim / sim | sim | sim | validada |
| Página Inicial | Lista multinível | numeração de tópicos no parágrafo: False → True | sim / sim | sim | sim | validada |
| Página Inicial | Localizar e substituir | Substituir tudo: "gama" → "GAMA-TROCADA": 0 → 1 | sim / sim | sim | sim | validada |
| Página Inicial | Painel de estilos | painel Estilos visível na barra lateral: False → True | — | — | — | validada |
| Página Inicial | Parágrafo (diálogo) | recuo à esquerda pelo diálogo Parágrafo (2 cm): 0 → 2000 | sim / sim | sim | sim | validada |
| Página Inicial | Recortar | ocorrências de "gama": 1 → 0 | sim / sim | sim | sim | validada |
| Página Inicial | Selecionar tudo | tamanho da seleção: (0, 106) → (106, 106) | — | — | — | validada |
| Inserir | Capa | páginas do documento (página de rosto nova): 1 → 2 | sim / sim | sim | sim | validada |
| Inserir | Data | campos de data: 0 → 1 | sim / sim | sim | sim | validada |
| Inserir | Gráfico | gráficos na página (objetos incorporados no texto): 0 → 1 | sim / sim | sim | sim | validada |
| Inserir | Quadro | quadros no documento (no DOCX, viram caixas de texto): 0 → 1 | sim / sim | sim | sim | validada |
| Inserir | Seção | seções no documento: 0 → 1 | sim / sim | sim | sim | validada |
| Desenhar | Agrupar | formas soltas na página: 2 → 1 | sim / sim | sim | sim | validada |
| Desenhar | Cor do traço | cor da linha da forma (preta antes): 0 → 3433892 | sim / sim | sim | sim | validada |
| Desenhar | Excluir traço | formas na página: 2 → 1 | sim / sim | sim | sim | validada |
| Design | Cor e bordas da página | cor de fundo da página (estilo de página): 'NONE' → 'SOLID' | sim / sim | sim | sim | validada |
| Design | Marca-d'água | marca-d'água "RASCUNHO": None → 'RASCUNHO' | NÃO / sim | sim | sim | FALHOU |
| Layout | Alinhar objetos | alinhamento horizontal da imagem: (2,) → (3,) | sim / sim | sim | sim | validada |
| Layout | Ancorar ao parágrafo | âncora da imagem: ('AT_CHARACTER',) → ('AT_PARAGRAPH',) | sim / sim | sim | NÃO — o DOCX não tem âncora "na página" nem "no parágrafo" como o ODT: ao reabrir, a imagem flutuante fica presa a um caractere, com a mesma posição na página | validada |
| Layout | Ancorar como caractere | âncora da imagem (como caractere): ('AT_PARAGRAPH',) → ('AS_CHARACTER',) | sim / sim | sim | sim | validada |
| Layout | Ancorar à página | âncora da imagem: ('AT_PARAGRAPH',) → ('AT_PAGE',) | sim / sim | sim | NÃO — o DOCX não tem âncora "na página" nem "no parágrafo" como o ODT: ao reabrir, a imagem flutuante fica presa a um caractere, com a mesma posição na página | validada |
| Layout | Atrás/na frente do texto | quebra do texto em volta da imagem: ('NONE',) → ('THROUGH',) | sim / sim | sim | sim | validada |
| Layout | Enviar para trás | ordem: a forma 2 fica atrás da 1: (0, 1) → (1, 0) | sim / sim | sim | sim | validada |
| Layout | Estilo de página (diálogo) | margem esquerda da página (3 cm): 2000 → 3000 | sim / sim | sim | sim | validada |
| Layout | Numeração de linhas | numeração de linhas ligada: False → True | — | sim | sim | validada |
| Layout | Quebra automática | quebra do texto em volta da imagem: ('NONE',) → ('PARALLEL',) | sim / sim | sim | sim | validada |
| Layout | Quebra ideal | quebra do texto em volta da imagem: ('NONE',) → ('DYNAMIC',) | sim / sim | sim | sim | validada |
| Layout | Recuos e espaçamento | recuo à esquerda pelo diálogo Parágrafo (2 cm): 0 → 2000 | sim / sim | sim | sim | validada |
| Layout | Sem quebra automática | quebra do texto em volta da imagem: ('PARALLEL',) → ('NONE',) | sim / sim | sim | sim | validada |
| Layout | Trazer para frente | ordem: a forma 1 fica na frente da 2: (0, 1) → (1, 0) | sim / sim | sim | sim | validada |
| Referências | Atualizar campos | campo de hora (com segundos) atualizado: '14:19:39' → '14:19:41' | — | — | — | validada |
| Referências | Atualizar sumário | título novo aparece no sumário: False → True | sim / sim | sim | sim | validada |
| Referências | Atualizar todos os índices | título novo aparece no sumário: False → True | sim / sim | sim | sim | validada |
| Referências | Configurar notas | tipo de numeração das notas de rodapé: 4 → 1 | — | sim | sim | validada |
| Referências | Inserir legenda | legenda abaixo da imagem: False → True | sim / sim | sim | sim | validada |
| Referências | Marcar entrada | entradas de índice marcadas: 0 → 1 | sim / sim | sim | sim | validada |
| Revisão | Aceitar | alterações pendentes e texto inserido: (2, True, True) → (1, True, True) | sim / sim | sim | sim | validada |
| Revisão | Aceitar todas | alterações pendentes, inserção e exclusão: (2, True, True) → (0, True, False) | sim / sim | sim | sim | validada |
| Revisão | Alteração anterior | trecho selecionado: '' → 'inserção controlada ' | — | — | — | validada |
| Revisão | Excluir todos os comentários | comentários: 2 → 0 | sim / sim | sim | sim | validada |
| Revisão | Gerenciar alterações | alterações pendentes (Aceitar todas no diálogo): (2, True, True) → (0, True, False) | sim / sim | sim | sim | validada |
| Revisão | Mostrar alterações | mostrar alterações (estado do comando): True → False | — | — | — | validada |
| Revisão | Mostrar comentários | mostrar comentários (estado do comando): True → False | — | — | — | validada |
| Revisão | Proteger controle de alterações | controle de alterações protegido por senha (senha de teste): False → True | — | sim | sim | validada |
| Revisão | Próxima alteração | trecho selecionado: '' → 'gama ' | — | — | — | validada |
| Revisão | Rejeitar | alterações pendentes e texto inserido: (2, True, True) → (1, False, True) | sim / sim | sim | sim | validada |
| Revisão | Rejeitar todas | alterações pendentes, inserção e exclusão: (2, True, True) → (0, False, True) | sim / sim | sim | sim | validada |
| Revisão | Revisão automática | revisão automática (estado do comando): True → False | — | — | — | validada |
| Revisão | Verificar acessibilidade | painel Verificar acessibilidade visível na barra lateral: False → True | — | — | — | validada |
| Exibir | Barra lateral | barra lateral (estado do comando): True → False | — | — | — | validada |
| Exibir | Exibição de livro | leiaute da exibição (colunas, livro): (1, False) → (2, True) | — | — | — | validada |
| Exibir | Grade | grade (estado do comando): False → True | — | — | — | validada |
| Exibir | Layout da web | layout da web (estado do comando): False → True | — | — | — | validada |
| Exibir | Layout de impressão | layout de impressão (sai do layout da web): (False, True) → (True, False) | — | — | — | validada |
| Exibir | Limites do texto | limites do texto (estado do comando): True → False | — | — | — | validada |
| Exibir | Marcas de formatação | marcas de formatação na exibição: False → True | — | — | — | validada |
| Exibir | Nova janela | janelas abertas do documento: 1 → 2 | — | — | — | validada |
| Exibir | Ocultar espaço em branco | ocultar espaço em branco (estado do comando): True → False | — | — | — | validada |
| Exibir | Painel de navegação | painel de navegação (estado do comando): False → True | — | — | — | validada |
| Exibir | Uma página | leiaute da exibição (colunas, livro): (2, True) → (1, False) | — | — | — | validada |
| Exibir | Várias páginas | leiaute da exibição (colunas, livro): (1, False) → (0, False) | — | — | — | validada |
| Tabela | Ajustar largura das colunas | separadores das colunas (1ª coluna com texto longo): (3333, 6666) → (9020, 9510) | sim / sim | sim | sim | validada |
| Tabela | Classificar | ordem da 1ª coluna (c, b, a → a, b, c): ('c', 'b', 'a') → ('a', 'b', 'c') | sim / sim | sim | sim | validada |
| Tabela | Dividir células | linhas, colunas e células (A1 dividida em 2): (3, 3, 9) → (4, 3, 10) | sim / sim | sim | sim | validada |
| Tabela | Estilos de tabela | aparência da tabela (cor da célula A1): -1 → 22941 | sim / sim | sim | sim | validada |
| Tabela | Excluir colunas | linhas, colunas e células: (3, 3, 9) → (3, 2, 6) | sim / sim | sim | sim | validada |
| Tabela | Excluir linhas | linhas, colunas e células: (3, 3, 9) → (2, 3, 6) | sim / sim | sim | sim | validada |
| Tabela | Excluir tabela | tabelas no documento: 1 → 0 | sim / sim | sim | sim | validada |
| Tabela | Inserir coluna à direita | linhas, colunas e células: (3, 3, 9) → (3, 4, 12) | sim / sim | sim | sim | validada |
| Tabela | Inserir coluna à esquerda | linhas, colunas e células: (3, 3, 9) → (3, 4, 12) | sim / sim | sim | sim | validada |
| Tabela | Inserir linha acima | linhas, colunas e células: (3, 3, 9) → (4, 3, 12) | sim / sim | sim | sim | validada |
| Tabela | Mesclar células | linhas, colunas e células (A1 e B1 selecionadas): (3, 3, 9) → (3, 2, 8) | sim / sim | sim | sim | validada |
| Tabela | Propriedades da tabela | alinhamento da tabela (centralizada): 6 → 2 | sim / sim | sim | sim | validada |
| Tabela | Selecionar tabela | células selecionadas: 'SwXTextRanges' → 9 | — | — | — | validada |
| Tabela | Sombreamento | cor de fundo da célula A1: -1 → 16776960 | sim / sim | sim | sim | validada |
| Imagem | Compactar imagem | formato da imagem depois de comprimir em JPEG: 'image/png' → 'image/jpeg' | sim / sim | sim | sim | validada |
| Imagem | Espelhar horizontal | espelhamento horizontal (páginas pares e ímpares): (False, False) → (True, True) | sim / sim | sim | sim | validada |
| Imagem | Espelhar vertical | espelhamento vertical: (False,) → (True,) | sim / sim | sim | NÃO — reaberto: (False,) | validada |
| Imagem | Girar à direita | rotação da imagem (graus × 10): 0 → 2700 | sim / sim | sim | sim | validada |
| Imagem | Girar à esquerda | rotação da imagem (graus × 10): 0 → 900 | sim / sim | sim | sim | validada |
| Imagem | Legenda | legenda abaixo da imagem: False → True | sim / sim | sim | sim | validada |
| Imagem | Propriedades da imagem | nome da imagem pelo diálogo Figura: 'ImagemTeste' → 'ImagemRenomeada' | — | sim | sim | validada |
| Forma | Agrupar | formas soltas na página: 2 → 1 | sim / sim | sim | sim | validada |
| Forma | Desagrupar | formas soltas na página: 1 → 2 | sim / sim | sim | sim | validada |
| Forma | Posição e tamanho | largura da forma (6 cm): 3000 → 6001 | sim / sim | sim | sim | validada |
| Forma | Preenchimento | cor de preenchimento da forma (branca antes): 16777215 → 7512015 | sim / sim | sim | sim | validada |
| Forma | Área | preenchimento da forma (nenhum): 'SOLID' → 'NONE' | sim / sim | sim | sim | validada |

## Quedas do motor durante o teste

- `.uno:LineSpacing`: o motor caiu durante o teste em 1 de 1 execuções (entrada simulada nos controles do diálogo; RESULTADOS §9)
- `design:.uno:PageDialog:bordas`: o motor caiu durante o teste em 1 de 1 execuções (entrada simulada nos controles do diálogo; RESULTADOS §9)

## Sem conferência automática do efeito (motivo)

| Aba | Ferramenta | Motivo |
|---|---|---|
| Arquivo | Assinatura digital | exige um certificado digital instalado no Windows |
| Página Inicial | Pincel de formatação | o formato é aplicado na próxima seleção feita com o mouse; o teste não simula o arraste |
| Inserir | Formas | a forma é desenhada com o mouse depois da escolha; o teste não simula o traço |
| Desenhar | Selecionar traços | modo de seleção para o mouse |
| Desenhar | Caneta (linha à mão livre) | desenho à mão livre com o mouse; o teste não simula o traço |
| Desenhar | Forma livre preenchida | desenho à mão livre com o mouse; o teste não simula o traço |
| Desenhar | Linha | desenho com o mouse na página; o teste não simula o traço |
| Desenhar | Curva | desenho com o mouse na página; o teste não simula o traço |
| Layout | Girar | a rotação é feita com o mouse nas alças do objeto |
| Referências | Banco de dados bibliográfico | abre o banco de dados bibliográfico em outra janela; sem efeito no documento |
| Correspondência | Assistente de mala direta | exige uma fonte de dados (planilha ou banco) cadastrada |
| Correspondência | Selecionar destinatários | exige uma fonte de dados cadastrada |
| Correspondência | Exibir fonte de dados | exige uma fonte de dados cadastrada |
| Correspondência | Primeiro registro | exige uma fonte de dados cadastrada |
| Correspondência | Registro anterior | exige uma fonte de dados cadastrada |
| Correspondência | Próximo registro | exige uma fonte de dados cadastrada |
| Correspondência | Último registro | exige uma fonte de dados cadastrada |
| Correspondência | Gerar documentos | exige uma fonte de dados cadastrada |
| Correspondência | Salvar documentos mesclados | exige uma fonte de dados cadastrada |
| Correspondência | Imprimir documentos mesclados | exige uma fonte de dados cadastrada e uma impressora |
| Exibir | Tema claro/escuro | muda o tema de todo o aplicativo (preferência do usuário) |
| Ajuda | Reiniciar em modo de segurança | reinicia o aplicativo; não pode ser conferido de dentro do teste |
| Imagem | Recortar | o recorte é feito com o mouse nas alças da imagem |
