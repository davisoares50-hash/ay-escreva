# Testes manuais pendentes — escala de tela e leitor de tela

Estes testes precisam de uma pessoa diante da tela. Os testes automáticos só rodaram em **100 %** (a escala deste
computador) e conferem o **nome acessível** dos controles, não a experiência de quem usa leitor de tela. Por isso
125 %, 150 %, 200 % e o uso com leitor de tela continuam **pendentes** em `docs/SITUACAO.md` até alguém fazer o que
está abaixo e registrar o resultado. Simulação ou teste em 100 % não aprova nenhuma outra escala.

Use o instalador da versão em teste e um documento qualquer com algumas páginas (por exemplo, um TCC em DOCX).

## 1. Escalas de 125 %, 150 % e 200 % (≈15 min por escala)

> **Situação em 29/10/2026:** 125 % e 150 % conferidos e aprovados pela pessoa responsável (RESULTADOS-TESTES.md §14.1).
> Falta só **200 %**.

**Trocar a escala:** Configurações do Windows › Sistema › Tela › **Escala** › escolha 125 %. Feche e abra o AY de
novo depois de trocar (o AY lê a escala ao abrir). No fim, volte para a escala de antes.

Em cada escala, confira e anote **sim/não** (e tire uma captura com Win+Shift+S quando algo estiver errado):

| # | O que olhar | Como |
|---|---|---|
| 1 | Faixa de opções: rótulos inteiros, ícones nítidos, nada sobreposto | Passe por todas as abas, de Arquivo a Ajuda |
| 2 | Abas contextuais aparecem e cabem | Clique numa tabela, numa imagem e numa forma |
| 3 | Painel **Assistente AY** sem botões cortados | Revisão › Assistente AY › Verificar documento |
| 4 | Painel **Revisão com IA** sem texto cortado | Revisão › Revisão com IA (com ou sem a IA instalada) |
| 5 | Diálogos cabem na tela, com os botões OK/Cancelar visíveis | Referências › Formatar trabalho acadêmico (e Prévia…); Arquivo › Galeria de modelos; Revisão › Gerenciar IA local; Ajuda › Verificar atualizações |
| 6 | Textos dos diálogos sem cortes nem sobreposição | Os mesmos do item 5 |
| 7 | Texto do documento nítido e régua alinhada | Role o documento; zoom 100 % |
| 8 | Barra de status legível (páginas, palavras, idioma, zoom) | Parte de baixo da janela |

**Ajuda automática (opcional):** com a escala já trocada, rode na pasta do projeto

```powershell
powershell -ExecutionPolicy Bypass -File tests\interface\conferir_escala.ps1
```

Ele confere texto cortado, sobreposição e tamanho dos diálogos do AY nessa escala e grava capturas em
`tests\output\interface\escala-<escala>-*.png`. O resultado dele ajuda, mas **não substitui** a conferência visual
acima: só marque a escala como aprovada depois de olhar a faixa e os diálogos.

**Registrar:** em `docs/RESULTADOS-TESTES.md`, seção "Escala de tela", uma linha por escala: data, escala, itens 1 a 8
(sim/não) e o problema encontrado.

## 2. Leitor de tela (≈20 min)

O teste automático confirmou que os controles têm **nome** (o que o leitor de tela anuncia) e que o Narrador recebe
esses nomes. Falta alguém **usar** o AY com o leitor e ouvir o resultado. Use o **Narrador** (Ctrl+Win+Enter liga e
desliga) e, se tiver, o **NVDA** (gratuito, nvaccess.org).

Só com o teclado (sem mouse), anote **sim/não** para cada item:

| # | Tarefa | Esperado |
|---|---|---|
| 1 | Abrir o AY e escrever uma frase | O leitor lê o que você digita |
| 2 | F6 até a faixa; setas entre as abas; Tab entre os botões | O leitor diz o nome da aba e de cada botão |
| 3 | Aplicar negrito a uma palavra pela faixa (Tab até "Negrito", Espaço) | O leitor anuncia o botão e o estado |
| 4 | Esc volta ao texto | O leitor volta a ler o documento |
| 5 | Revisão › Assistente AY › Verificar documento; Tab pela lista | O leitor lê a palavra, a sugestão e os botões |
| 6 | Referências › Formatar trabalho acadêmico; Tab e Shift+Tab; Esc | O leitor lê cada controle; Esc fecha |
| 7 | Ajuda › Verificar atualizações; Tab até "Verificar agora"; Esc | Idem |
| 8 | Salvar como DOCX (Ctrl+Shift+S) até o aviso de perdas | O leitor lê o aviso e os botões |

**Registrar:** em `docs/RESULTADOS-TESTES.md`, seção "Leitor de tela": data, leitor e versão, itens 1 a 8 (sim/não),
e o que foi lido de forma confusa ou não foi lido.

## 3. Só teclado, sem leitor de tela (≈10 min)

O teste automático com teclas reais confirmou: F6 leva às abas da faixa, as setas trocam de aba, Esc fecha os diálogos
e o foco volta ao texto, e a ordem do Tab em Propriedades, Galeria de modelos e Verificar atualizações. Ficou para uma
pessoa conferir (anote **sim/não**):

| # | Tarefa | Esperado |
|---|---|---|
| 1 | Selecione uma palavra; F6 até as abas; Tab até "Negrito"; Espaço | a palavra fica em negrito; dá para ver qual botão está com o foco |
| 2 | Com o foco na faixa, Esc | anote se o foco volta ao texto; se não, F6 (ou Shift+F6) deve voltar |
| 3 | Referências › Formatar trabalho acadêmico; Tab e Shift+Tab por todos os controles; Esc | a ordem segue a tela, de cima para baixo; o controle com foco aparece realçado |
| 4 | O mesmo em Referências › Conferir referências e em Ajuda › Verificar atualizações | idem |
| 5 | Página Inicial › Caractere e Parágrafo (diálogos); Ctrl+Page Down troca de guia; Tab percorre a guia; Esc | idem |
| 6 | Ctrl+K (Link); Tab pelos campos; Esc | idem |
| 7 | Nos diálogos do AY (Galeria, Formatar, Verificar atualizações): o botão com foco aparece realçado? | sim — desde 29/10/2026 o botão com foco fica com o rótulo sublinhado (antes, o contorno não aparecia) |

**Registrar:** em `docs/RESULTADOS-TESTES.md` §14: data, itens 1 a 7 (sim/não) e o que estiver difícil de usar só com
o teclado.

## 4. Duas ferramentas que o teste automático não consegue conferir (≈3 min)

> **Situação em 29/10/2026:** as duas conferidas pela pessoa responsável — funcionaram, sem queda.

No teste automático, escolher o valor nestas duas ferramentas derrubou o motor (a escolha é feita por entrada
simulada; §9 de RESULTADOS-TESTES). Com o mouse ou o teclado de verdade, confira:

| # | Tarefa | Esperado |
|---|---|---|
| 1 | Página Inicial › Espaçamento entre linhas › Duplo; depois Ctrl+Z | o parágrafo fica com espaço duplo; Ctrl+Z volta; o AY não fecha |
| 2 | Design › Cor e bordas da página › guia Bordas › uma borda predefinida › OK; depois Ctrl+Z | a página ganha borda; o AY não fecha |

Se o AY fechar, anote o que estava fazendo: é o mesmo defeito do motor, agora com uso real.
