# Identidade visual do AY ESCREVA

Fonte única: [`tools/marca.mjs`](../tools/marca.mjs). Todos os ativos são gerados por ele em `out/marca/`
durante `scripts/montar.ps1`; o texto vira contornos, então os SVGs não dependem de fontes instaladas.

| Elemento | Valor |
|---|---|
| Símbolo | quadrado arredondado verde-tinta com o monograma "AY" branco e uma "linha de escrita" amarela |
| Verde-tinta | `#11806A` → `#0A5C4C` (degradê vertical) |
| Amarelo | `#F5C443` |
| Texto escuro / secundário | `#1E2A28` / `#5B6664` |
| Tipografia | Rubik Bold (nome) e Rubik Regular (descrição), SIL OFL 1.1 |

| Arquivo gerado | Uso |
|---|---|
| `ayescreva.ico` (16–256 px), `icone-*.png`, `icone.svg` | lançador, atalhos, instalador, desinstalação |
| `intro.png`, `intro-highres.png` | tela de abertura (geometria da barra de progresso casada com `soffice.ini`) |
| `about.svg` | janela "Sobre" |
| `logo.svg`, `logo_inverted.svg`, `logo-sc*.svg` | Central de Início e outros pontos, temas claro e escuro |
| `instalador-lateral*.bmp`, `instalador-topo*.bmp` | assistente do Inno Setup (1× e 2×) |

Ainda **não** rebrandeados no Nível 1: ícone da janela e da barra de tarefas (recursos compilados no motor)
e ícones de tipo de documento. Isso fica para o Nível 2, ver [ARQUITETURA.md](../docs/ARQUITETURA.md).
