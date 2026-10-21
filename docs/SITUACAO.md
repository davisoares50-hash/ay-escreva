# Situação do projeto AY ESCREVA — lista única

> Gerado por `tools/gerar-situacao.mjs` em 21/10/2026, a partir de `docs/situacao-base.json` (itens do
> pedido original e das entregas, com a evidência de cada um) e de `docs/MATRIZ-FUNCIONALIDADES.md` (ferramentas da faixa,
> geradas pelos testes). Não editar à mão.

Versão pública: **0.2.0**. Versão de testes local mais recente: **0.7.0**
(`out\instalador\AYEscreva-0.7.0-teste-windows11-x64.exe`).

| Situação | Requisitos e entregas | Ferramentas da faixa |
|---|---|---|
| ✅ Concluído e testado | 31 | 69 |
| 🟡 Implementado sem validação completa | 8 | 176 |
| ⬜ Ainda não implementado | 10 | 4 |

Legenda: **concluído e testado** = há teste automatizado que conferiu o efeito (pela interface ou pela API do motor);
**implementado sem validação completa** = existe e foi acionado ou conferido só em parte; **ainda não implementado** =
não existe nesta versão.

## Requisitos do produto

| Item | Situação | Evidência ou pendência |
|---|---|---|
| Gratuito, sem mensalidade, avaliação ou bloqueio pago | ✅ Concluído e testado | Não há cobrança, chave nem bloqueio no código (licença MPL-2.0); download do site sem login testado (RESULTADOS §10, 25/25). A IA local também é gratuita, sem assinatura nem chave. |
| Sem conta obrigatória | ✅ Concluído e testado | O aplicativo instalado abre e edita sem conta (instalação 19/19); o site não pede login. |
| Editar, abrir, salvar, imprimir e exportar offline | ✅ Concluído e testado | Testes pela interface com 0 conexões de rede para fora do computador; aceite 40/40; impressão 4/4. |
| Documentos locais por padrão | ✅ Concluído e testado | Salvar grava no disco local (aceite 40/40); nada vai para servidores. |
| Nome, logotipo, ícones e identidade próprios | 🟡 Implementado sem validação completa | Nome, logotipo, tela de abertura, faixa e instalador próprios; o ícone da janela ainda é o da base (exige compilar o motor, Nível 2). |

## Sistemas e arquiteturas

Só há uma máquina disponível (Windows 11 Pro x64, Intel Core i5-8500). Testes em outros sistemas exigem equipamento que não está disponível: ficam como pendências.

| Item | Situação | Evidência ou pendência |
|---|---|---|
| Windows 11 x64 | ✅ Concluído e testado | Instalar, abrir, usar, atualizar de versão anterior e desinstalar (instalação 19/19, atualização 14/14) e bateria completa. |
| Windows 10 x64 | ⬜ Ainda não implementado | O instalador de testes exige Windows 11; falta um Windows 10 limpo para liberar e testar (sem máquina disponível). |
| Windows em ARM64 | ⬜ Ainda não implementado | Não montado nem testado (sem máquina ARM). |
| Versões antigas do Windows (7, 8.1) e 32 bits | ⬜ Ainda não implementado | Não avaliado nesta máquina; limites ainda não documentados com teste. |
| macOS | ⬜ Ainda não implementado | Não montado nem testado (sem Mac). |
| Linux | ⬜ Ainda não implementado | Não montado nem testado. |

## Acessibilidade

| Item | Situação | Evidência ou pendência |
|---|---|---|
| Navegação por teclado nos diálogos e painéis do AY | ✅ Concluído e testado | Foco inicial, Tab e Shift+Tab e teclas de acesso sem repetição conferidos nos diálogos Formatar, Modelo da instituição e Gerenciar IA local; botões dos painéis acionados com teclado real (RESULTADOS §4, §5.3, §5.5). |
| Navegação por teclado nos painéis de IA e diálogos novos (D e E) | ✅ Concluído e testado | Botões acionados com teclado real; Tab/Shift+Tab e teclas de acesso conferidos em Gerenciar IA local, Conferir referências e Verificar atualizações. |
| Navegação por teclado na faixa de opções (Alt, F6, setas) | 🟡 Implementado sem validação completa | A faixa vem da base com suporte a teclado; não há teste automatizado de ponta a ponta. |
| Leitor de tela: Narrador (Windows) | 🟡 Implementado sem validação completa | Com o Narrador ligado, nomes, papéis e foco de botões, campos e listas do painel Revisão com IA e de 4 diálogos conferidos pela interface MSAA (5/5). Não confere o áudio falado nem a navegação completa por voz. O botão de menu da barra lateral (do motor) não tem nome. |
| Leitores de tela NVDA e JAWS | ⬜ Ainda não implementado | Não instalados neste computador; instalar programas de terceiros depende de autorização. Teste pendente. |
| Escala de exibição 100 % (a deste computador) | ✅ Concluído e testado | Diálogos e painéis sem texto cortado, sem sobreposição e cabendo na tela (8/8, fase 9). Textos apertados encontrados e corrigidos (Cancelar download; botões do Assistente AY). |
| Escalas de exibição 125 %, 150 % e 200 % | ⬜ Ainda não implementado | Trocar a escala do Windows é configuração do sistema: o teste está pronto (tests\interface\conferir_escala.ps1) e roda depois que a escala for trocada em Configurações › Sistema › Tela. |

## Documentos e confiabilidade

| Item | Situação | Evidência ou pendência |
|---|---|---|
| Ler e gravar DOCX e ODT | ✅ Concluído e testado | Aceite 40/40; ida e volta com documento representativo e variantes do Word, sem perda de texto (RESULTADOS §2, §11). |
| Exportar PDF (inclusive PDF/UA) | ✅ Concluído e testado | Aceite 40/40; PDF com o mesmo número de páginas. |
| DOC, RTF e TXT | ✅ Concluído e testado | Ida e volta testada; 7 incompatibilidades registradas em RESULTADOS §11 e em Ajuda › Limitações. |
| Preservar estilos, tabelas, imagens, seções, notas e comentários | ✅ Concluído e testado | Comparação estrutural e visual antes e depois de salvar (RESULTADOS §11), com as diferenças conhecidas listadas. |
| Aviso de incompatibilidade antes de salvar em formato com perdas | ✅ Concluído e testado | Aviso de perdas ao salvar em DOCX validado pela interface (botão Salvar, Salvar como e fechar › Salvar). |
| Salvar uma cópia com o aviso de perdas | 🟡 Implementado sem validação completa | Usa o mesmo código de Salvar como (testado), mas não tem teste próprio. |
| Desfazer e refazer | ✅ Concluído e testado | Confiabilidade 19/19; formatação acadêmica desfaz e refaz por inteiro (38/38). |
| Recuperação após falha e salvamento seguro | ✅ Concluído e testado | Recuperação 7/7 (queda forçada do motor); salvamento seguro com falha e interrupção da gravação (19/19). |
| Substituição de fontes informada | ✅ Concluído e testado | Aviso de fontes substituídas validado pela interface. |
| Não executar macros nem carregar recursos externos | ✅ Concluído e testado | Segurança 4/4 (macro não executa, com controle positivo; imagem remota não é baixada). |
| Não enviar documentos a servidores sem autorização | ✅ Concluído e testado | 0 conexões externas nos testes pela interface; a IA roda em 127.0.0.1 com chave e modo offline (RESULTADOS §5.5). |

## Janela principal e faixa de opções

| Item | Situação | Evidência ou pendência |
|---|---|---|
| Faixa por abas na ordem pedida (11 abas) | ✅ Concluído e testado | Cada botão encontrado na aba certa pela interface (RESULTADOS §4); detalhes por função abaixo. |
| Abas contextuais de Tabela e Imagem | ✅ Concluído e testado | Aparecem ao selecionar tabela ou imagem e foram acionadas pela interface. |
| Abas contextuais de Forma e Visualizar impressão | 🟡 Implementado sem validação completa | Conferidas só visualmente (capturas), sem clique automatizado. |
| Barra de título, acesso rápido, réguas, páginas com limites, navegação e barra de status (páginas, palavras, idioma, zoom) | ✅ Concluído e testado | Presentes na janela (capturas); régua, zoom e navegação acionados pela interface. |
| Grupos da faixa se recolhem em janelas estreitas | ⬜ Ainda não implementado | Em janelas estreitas alguns botões ficam fora da área visível (Ajuda › Limitações). |
| Usar todas as ferramentas da faixa sem queda do motor | 🟡 Implementado sem validação completa | Defeito da base (LibreOffice 26.8.1) reproduzido: Galeria do Fontwork e depois Link fecha o aplicativo (3 em 3, também sem a extensão do AY). A recuperação após queda protege o que não foi salvo. RESULTADOS §9. |

## Entregas de assistência à escrita

| Item | Situação | Evidência ou pendência |
|---|---|---|
| Confiabilidade (0.3.0): recuperação, salvamento seguro, desfazer/refazer, TXT | ✅ Concluído e testado | Confiabilidade 19/19, recuperação 7/7. |
| A (0.3.0): revisão de texto, dicionário pessoal, painel Assistente AY | ✅ Concluído e testado | Regras 31/31; pela interface 31/31 (digitação real, proteções, desfazer, painel, documento longo). |
| B (0.4.0): formatar trabalho acadêmico numa cópia, relatório de conformidade, modelo da instituição | ✅ Concluído e testado | 38/38 e 18/18 pela interface. O relatório não atesta conformidade completa: os textos oficiais das normas não foram consultados. |
| B (0.4.0): galeria de modelos e Salvar como modelo | ✅ Concluído e testado | 33/33. |
| C (0.5.0): IA local — revisar, mais claro, mais formal, simplificar, resumir, com comparação, aceitar/rejeitar e desfazer | ✅ Concluído e testado | 12/12 sem modelo, 21/21 no editor com o modelo real, 32/32 na fase 9 pela interface (inclui escala e atualizações). |
| C: download do modelo pelo botão Baixar (progresso, cancelar, continuar, falhas) | ✅ Concluído e testado | Download real pela interface (11/11): 3,4 GB dos endereços oficiais, cancelar, continuar de onde parou, fechar no meio, SHA-256, usar e remover. Falhas simuladas (13/13): queda, servidor sem retomada, arquivo adulterado, 404, 500. |
| D: revisão do documento inteiro, referências, sugestões de títulos, explicações e inconsistências | ✅ Concluído e testado | Regras de referências e consistência 21/21; no editor com o modelo real 12/12; pela interface 12/12. "Apontar inconsistências" pela IA é um apoio fraco (às vezes só repete o trecho; um falso alarme medido). |
| E: verificar atualizações com confirmação, preservando documentos e preferências | 🟡 Implementado sem validação completa | Assinatura e conferências 16/16; documentos não salvos bloqueiam 2/2; atualização de ponta a ponta pelo próprio AY 8/8; pela interface 4/4. Falta publicar o arquivo de versões assinado no site (decisão sua): até lá, "Verificar agora" responde que não há informação publicada. |

## Distribuição

| Item | Situação | Evidência ou pendência |
|---|---|---|
| Instalador Windows 11 x64 por usuário, sem administrador | ✅ Concluído e testado | Instalação 19/19 (0.5.0). |
| Atualizar uma instalação anterior preservando documentos e preferências | ✅ Concluído e testado | Atualização 0.2.0 → 0.5.0 e 0.4.0 → 0.5.0: 14/14. |
| Atualização pelo próprio AY (Ajuda › Verificar atualizações) | 🟡 Implementado sem validação completa | Funciona de ponta a ponta com o instalador conferido; depende de publicar atualizacoes.json assinado no site oficial (docs/ATUALIZACOES.md). |
| Site oficial com download e SHA-256 | ✅ Concluído e testado | Publicado (versão 0.2.0); fluxo acessar → baixar → conferir → instalar 25/25. |
| Assinatura digital do instalador | ⬜ Ainda não implementado | Sem certificado de assinatura de código; o SmartScreen pode avisar. |
| Pacote MSI para empresas | ⬜ Ainda não implementado | Não feito. |

## Ferramentas da faixa de opções (pedido original, por aba)

Cada função pedida, com o resultado dos testes. Detalhes (comando, critério de aceite) em
[MATRIZ-FUNCIONALIDADES.md](MATRIZ-FUNCIONALIDADES.md). "Implementado sem validação completa" aqui é, na maioria, um
botão que o teste aciona e confirma o comando disparado, sem conferir o efeito no documento. As ferramentas próprias
do AY (Assistente AY, IA local, formatação acadêmica, conferências, atualizações) têm testes dedicados, contados na
seção "Entregas de assistência à escrita" acima.

### Arquivo — ✅ 10 · 🟡 10 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Novo | Novo documento | ✅ Concluído e testado | Por API: aceite_etapa1 |
| Novo | Galeria de modelos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Novo | Modelos | 🟡 Implementado sem validação completa | botão presente; não validado |
| Novo | Salvar como modelo | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Documento | Abrir | ✅ Concluído e testado | Por API: ida_e_volta |
| Documento | Recentes | ✅ Concluído e testado | Por API: ida_e_volta |
| Documento | Salvar | ✅ Concluído e testado | Pela interface: ODT gravado pelo botão Salvar, sem aviso (formato nativo) |
| Documento | Salvar como | ✅ Concluído e testado | Por API: aceite_etapa1, ida_e_volta |
| Documento | Salvar uma cópia | 🟡 Implementado sem validação completa | botão presente; não validado |
| Documento | Recarregar | 🟡 Implementado sem validação completa | botão presente; não validado |
| Documento | Fechar | ✅ Concluído e testado | Por API: aceite_etapa1 |
| Exportar e imprimir | Exportar PDF | ✅ Concluído e testado | Por API: aceite_etapa1 (PDF e PDF/UA) |
| Exportar e imprimir | Exportar PDF direto | ✅ Concluído e testado | Por API: aceite_etapa1 |
| Exportar e imprimir | Imprimir | ✅ Concluído e testado | Por API: impressao |
| Exportar e imprimir | Visualizar impressão | 🟡 Implementado sem validação completa | botão presente; não validado |
| Informações | Propriedades | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Informações | Versões | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Informações | Assinatura digital | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Informações | Recuperação de documentos | ✅ Concluído e testado | Pela interface: abriria backup (arquivo existe; abertura simulada no teste) |
| Informações | Configurações | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |

### Página Inicial — ✅ 22 · 🟡 15 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Área de transferência | Colar | 🟡 Implementado sem validação completa | botão presente; não validado |
| Área de transferência | Recortar | 🟡 Implementado sem validação completa | botão presente; não validado |
| Área de transferência | Copiar | 🟡 Implementado sem validação completa | botão presente; não validado |
| Área de transferência | Pincel de formatação | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Área de transferência | Colar especial | 🟡 Implementado sem validação completa | botão presente; não validado |
| Fonte | Fonte | ✅ Concluído e testado | Por API: aceite_etapa1 |
| Fonte | Tamanho | ✅ Concluído e testado | Por API: aceite_etapa1 |
| Fonte | Aumentar fonte | ✅ Concluído e testado | Pela interface: CharHeight=14.0 depois do clique |
| Fonte | Diminuir fonte | ✅ Concluído e testado | Pela interface: CharHeight=10.0 depois do clique |
| Fonte | Negrito | ✅ Concluído e testado | Pela interface: CharWeight=150.0 depois do clique |
| Fonte | Itálico | ✅ Concluído e testado | Pela interface: CharPosture=ITALIC depois do clique |
| Fonte | Sublinhado | ✅ Concluído e testado | Pela interface: CharUnderline=1 depois do clique |
| Fonte | Tachado | ✅ Concluído e testado | Pela interface: CharStrikeout=1 depois do clique |
| Fonte | Subscrito | ✅ Concluído e testado | Pela interface: CharEscapement=-14000 depois do clique |
| Fonte | Sobrescrito | ✅ Concluído e testado | Pela interface: CharEscapement=14000 depois do clique |
| Fonte | Cor da fonte | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Fonte | Realce | ✅ Concluído e testado | Por API: aceite_etapa1 (realce no DOCX) |
| Fonte | Limpar formatação | ✅ Concluído e testado | Pela interface: CharWeight=100.0 depois do clique |
| Fonte | Caractere (diálogo) | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Parágrafo | Marcadores | ✅ Concluído e testado | Pela interface: NumberingIsNumber=True depois do clique |
| Parágrafo | Numeração | ✅ Concluído e testado | Pela interface: NumberingIsNumber=True depois do clique |
| Parágrafo | Lista multinível | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Parágrafo | Diminuir recuo | ✅ Concluído e testado | Pela interface: ParaLeftMargin=0 depois do clique |
| Parágrafo | Aumentar recuo | ✅ Concluído e testado | Pela interface: ParaLeftMargin=1251 depois do clique |
| Parágrafo | Marcas de formatação | ✅ Concluído e testado | Pela interface: ShowNonprintingCharacters: False → True |
| Parágrafo | Alinhar à esquerda | ✅ Concluído e testado | Pela interface: ParaAdjust=0 depois do clique |
| Parágrafo | Centralizar | ✅ Concluído e testado | Pela interface: ParaAdjust=3 depois do clique |
| Parágrafo | Alinhar à direita | ✅ Concluído e testado | Pela interface: ParaAdjust=1 depois do clique |
| Parágrafo | Justificar | ✅ Concluído e testado | Pela interface: ParaAdjust=2 depois do clique |
| Parágrafo | Espaçamento entre linhas | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Parágrafo | Aumentar espaço entre parágrafos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Parágrafo | Diminuir espaço entre parágrafos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Parágrafo | Parágrafo (diálogo) | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Estilos | Estilo do parágrafo | ✅ Concluído e testado | Por API: aceite_etapa1 (Título 1) |
| Estilos | Painel de estilos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Edição | Localizar e substituir | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Edição | Selecionar tudo | 🟡 Implementado sem validação completa | botão presente; não validado |

### Inserir — ✅ 14 · 🟡 9 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Páginas | Capa | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Páginas | Página em branco | ✅ Concluído e testado | Pela interface: paginas: 2 → 4 |
| Páginas | Quebra de página | ✅ Concluído e testado | Pela interface: paginas: 1 → 2 |
| Páginas | Quebras (página, coluna, linha) | ✅ Concluído e testado | Por API: ida_e_volta (3 seções) |
| Páginas | Seção | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Tabelas | Tabela | ✅ Concluído e testado | Por API: aceite_etapa1, ida_e_volta (mescladas) |
| Ilustrações | Imagem | ✅ Concluído e testado | Por API: aceite_etapa1 |
| Ilustrações | Formas | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Ilustrações | Gráfico | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Ilustrações | Fontwork (texto artístico) | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Links e comentários | Link | ✅ Concluído e testado | Por API: ida_e_volta |
| Links e comentários | Indicador | ✅ Concluído e testado | Por API: ida_e_volta |
| Links e comentários | Referência cruzada | ✅ Concluído e testado | Por API: ida_e_volta |
| Links e comentários | Comentário | ✅ Concluído e testado | Pela interface: comentarios: 0 → 1 |
| Cabeçalho e rodapé | Cabeçalho | ✅ Concluído e testado | Por API: aceite_etapa1, ida_e_volta |
| Cabeçalho e rodapé | Rodapé | ✅ Concluído e testado | Por API: aceite_etapa1, ida_e_volta |
| Cabeçalho e rodapé | Número de página | ✅ Concluído e testado | Por API: aceite_etapa1 (campo de página) |
| Texto | Caixa de texto | ✅ Concluído e testado | Por API: ida_e_volta (caixa de texto) |
| Texto | Quadro | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Texto | Campos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Texto | Data | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Símbolos | Equação | ✅ Concluído e testado | Por API: ida_e_volta (OMML) |
| Símbolos | Símbolo | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |

### Desenhar — ✅ 0 · 🟡 9 · ⬜ 3

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Ferramentas | Selecionar traços | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Ferramentas | Caneta (linha à mão livre) | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Ferramentas | Forma livre preenchida | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Ferramentas | Linha | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Ferramentas | Curva | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Ferramentas | Marca-texto | ⬜ Ainda não implementado | Sem ferramenta própria na base; previsto como predefinição de traço (amarelo, translúcido, largo) na extensão AY. |
| Ferramentas | Borracha | ⬜ Ainda não implementado | A base só exclui o traço selecionado (botão Excluir traço). Borracha por arrasto exige código C++ (Nível 2). |
| Ferramentas | Sensibilidade à pressão da caneta | ⬜ Ainda não implementado | Não suportado pela base; tinta do Word (InkML) é importada como imagem ou forma, sem pressão. |
| Traço | Cor do traço | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Traço | Espessura e estilo | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Traço | Agrupar | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Traço | Excluir traço | 🟡 Implementado sem validação completa | botão presente; não validado |

### Design — ✅ 0 · 🟡 5 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Formatação do documento | Temas, cores e fontes do documento | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Formatação do documento | Conjuntos de estilos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Plano de fundo da página | Marca-d'água | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Plano de fundo da página | Cor e bordas da página | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Plano de fundo da página | Bordas de página | 🟡 Implementado sem validação completa | botão presente; não validado |

### Layout — ✅ 3 · 🟡 17 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Configurar página | Margens | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Configurar página | Orientação | ✅ Concluído e testado | Por API: ida_e_volta (paisagem) |
| Configurar página | Tamanho do papel | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Configurar página | Colunas | ✅ Concluído e testado | Por API: ida_e_volta (2 colunas) |
| Configurar página | Quebras de página e seção | ✅ Concluído e testado | Por API: ida_e_volta (3 seções) |
| Configurar página | Hifenização | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Configurar página | Numeração de linhas | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Configurar página | Estilo de página (diálogo) | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Parágrafo | Recuos e espaçamento | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Organizar | Sem quebra automática | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Organizar | Quebra automática | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Organizar | Quebra ideal | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Organizar | Atrás/na frente do texto | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Organizar | Trazer para frente | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Organizar | Enviar para trás | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Organizar | Ancorar à página | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Organizar | Ancorar ao parágrafo | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Organizar | Ancorar como caractere | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Organizar | Alinhar objetos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Organizar | Girar | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |

### Referências — ✅ 7 · 🟡 12 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Trabalho acadêmico | Formatar trabalho acadêmico | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Trabalho acadêmico | Relatório de conformidade | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Trabalho acadêmico | Conferir referências | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Trabalho acadêmico | Conferir consistência | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Sumário | Sumário e índices | ✅ Concluído e testado | Por API: ida_e_volta (sumário) |
| Sumário | Atualizar sumário | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Sumário | Atualizar todos os índices | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Notas | Nota de rodapé | ✅ Concluído e testado | Pela interface: notasRodape: 0 → 1 |
| Notas | Nota de fim | ✅ Concluído e testado | Pela interface: notasFim: 0 → 1 |
| Notas | Configurar notas | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Citações e bibliografia | Inserir citação | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Citações e bibliografia | Banco de dados bibliográfico | 🟡 Implementado sem validação completa | botão presente; não validado |
| Citações e bibliografia | Bibliografia | ✅ Concluído e testado | Por API: ida_e_volta (sumário) |
| Legendas | Inserir legenda | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Legendas | Lista de figuras | ✅ Concluído e testado | Por API: ida_e_volta (sumário) |
| Legendas | Referência cruzada | ✅ Concluído e testado | Por API: ida_e_volta |
| Índice remissivo | Marcar entrada | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Índice remissivo | Inserir índice remissivo | ✅ Concluído e testado | Por API: ida_e_volta (sumário) |
| Índice remissivo | Atualizar campos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |

### Correspondência — ✅ 0 · 🟡 14 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Criar | Envelopes | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Criar | Etiquetas | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Iniciar mala direta | Assistente de mala direta | 🟡 Implementado sem validação completa | botão presente; não validado |
| Iniciar mala direta | Selecionar destinatários | 🟡 Implementado sem validação completa | botão presente; não validado |
| Iniciar mala direta | Exibir fonte de dados | 🟡 Implementado sem validação completa | botão presente; não validado |
| Iniciar mala direta | Inserir campo de mesclagem | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Visualizar resultados | Primeiro registro | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Visualizar resultados | Registro anterior | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Visualizar resultados | Próximo registro | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Visualizar resultados | Último registro | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Concluir | Gerar documentos | 🟡 Implementado sem validação completa | botão presente; não validado |
| Concluir | Salvar documentos mesclados | 🟡 Implementado sem validação completa | botão presente; não validado |
| Concluir | Imprimir documentos mesclados | 🟡 Implementado sem validação completa | botão presente; não validado |
| Concluir | Enviar por e-mail | 🟡 Implementado sem validação completa | botão presente; não validado |

### Revisão — ✅ 2 · 🟡 24 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Assistente AY | Assistente AY | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Assistente AY | Verificar documento | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Assistente AY | Correção automática | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| IA local | Revisão com IA | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| IA local | Gerenciar IA local | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Revisão de texto | Ortografia e gramática | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Revisão de texto | Revisão automática | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Revisão de texto | Sinônimos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Revisão de texto | Contagem de palavras | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Revisão de texto | Idioma do texto | 🟡 Implementado sem validação completa | botão presente; não validado |
| Revisão de texto | Verificar acessibilidade | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Comentários | Novo comentário | ✅ Concluído e testado | Por API: ida_e_volta |
| Comentários | Excluir todos os comentários | 🟡 Implementado sem validação completa | botão presente; não validado |
| Comentários | Mostrar comentários | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Controle de alterações | Controlar alterações | ✅ Concluído e testado | Pela interface: RecordChanges=True |
| Controle de alterações | Mostrar alterações | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Controle de alterações | Gerenciar alterações | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Controle de alterações | Proteger controle de alterações | 🟡 Implementado sem validação completa | botão presente; não validado |
| Alterações | Aceitar | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Alterações | Rejeitar | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Alterações | Alteração anterior | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Alterações | Próxima alteração | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Alterações | Aceitar todas | 🟡 Implementado sem validação completa | botão presente; não validado |
| Alterações | Rejeitar todas | 🟡 Implementado sem validação completa | botão presente; não validado |
| Comparar | Comparar documentos | 🟡 Implementado sem validação completa | botão presente; não validado |
| Comparar | Combinar documentos | 🟡 Implementado sem validação completa | botão presente; não validado |

### Exibir — ✅ 4 · 🟡 17 · ⬜ 1

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Modos de exibição | Layout de impressão | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Modos de exibição | Layout da web | 🟡 Implementado sem validação completa | botão presente; não validado |
| Modos de exibição | Tela inteira | 🟡 Implementado sem validação completa | botão presente; não validado |
| Modos de exibição | Modo de leitura | ⬜ Ainda não implementado | Hoje: Tela inteira + Exibição de livro. Modo de leitura dedicado (sem edição) previsto na extensão AY. |
| Zoom | Zoom | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Zoom | 100% | ✅ Concluído e testado | Pela interface: ZoomType=3 ZoomValue=100 |
| Zoom | Página inteira | ✅ Concluído e testado | Pela interface: ZoomType=2 ZoomValue=68 |
| Zoom | Largura da página | ✅ Concluído e testado | Pela interface: ZoomType=1 ZoomValue=223 |
| Zoom | Uma página | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Zoom | Várias páginas | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Zoom | Exibição de livro | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Mostrar | Régua | ✅ Concluído e testado | Pela interface: ShowRulers: True → False |
| Mostrar | Painel de navegação | 🟡 Implementado sem validação completa | botão presente; não validado |
| Mostrar | Barra lateral | 🟡 Implementado sem validação completa | botão presente; não validado |
| Mostrar | Marcas de formatação | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Mostrar | Limites do texto | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Mostrar | Grade | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Mostrar | Ocultar espaço em branco | 🟡 Implementado sem validação completa | botão presente; não validado |
| Janela e tema | Nova janela | 🟡 Implementado sem validação completa | botão presente; não validado |
| Janela e tema | Fechar janela | 🟡 Implementado sem validação completa | botão presente; não validado |
| Janela e tema | Alternar entre janelas | 🟡 Implementado sem validação completa | botão presente; não validado |
| Janela e tema | Tema claro/escuro | 🟡 Implementado sem validação completa | botão presente; não validado |

### Ajuda — ✅ 4 · 🟡 6 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Ajuda | Guia de utilização do AY | ✅ Concluído e testado | Pela interface: abriria guia.html (arquivo existe; abertura simulada no teste) |
| Ajuda | Atalhos de teclado | ✅ Concluído e testado | Pela interface: abriria atalhos.html (arquivo existe; abertura simulada no teste) |
| Ajuda | Ajuda do motor (offline) | 🟡 Implementado sem validação completa | botão presente; não validado |
| Ajuda | Limitações conhecidas | ✅ Concluído e testado | Pela interface: abriria limitacoes.html (arquivo existe; abertura simulada no teste) |
| Sobre | Sobre o AY ESCREVA | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Sobre | Licenças | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Sobre | Créditos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Diagnóstico | Relatório de diagnóstico | ✅ Concluído e testado | Pela interface: relatório criado no perfil, sem conteúdo de documentos |
| Diagnóstico | Reiniciar em modo de segurança | 🟡 Implementado sem validação completa | botão presente; não validado |
| Diagnóstico | Verificar atualizações (opcional) | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |

### Tabela (contextual) — ✅ 1 · 🟡 15 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
|  | Inserir linha acima | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Inserir linha abaixo | ✅ Concluído e testado | Pela interface: linhas: 2 → 3 |
|  | Inserir coluna à esquerda | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Inserir coluna à direita | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Excluir linhas | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Excluir colunas | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Excluir tabela | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Mesclar células | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Dividir células | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Ajustar largura das colunas | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Bordas | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Sombreamento | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Estilos de tabela | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Classificar | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Propriedades da tabela | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Selecionar tabela | 🟡 Implementado sem validação completa | botão presente; não validado |

### Imagem (contextual) — ✅ 1 · 🟡 10 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
|  | Recortar | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Texto alternativo | ✅ Concluído e testado | Por API: aceite_etapa1, ida_e_volta |
|  | Trocar imagem | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Compactar imagem | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Salvar imagem | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Girar à esquerda | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Girar à direita | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Espelhar vertical | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Espelhar horizontal | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Propriedades da imagem | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Legenda | 🟡 Implementado sem validação completa | botão presente; não validado |

### Forma (contextual) — ✅ 0 · 🟡 6 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
|  | Preenchimento | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Área | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Linha | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Posição e tamanho | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Agrupar | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Desagrupar | 🟡 Implementado sem validação completa | botão presente; não validado |

### Visualizar impressão (contextual) — ✅ 1 · 🟡 7 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
|  | Imprimir | ✅ Concluído e testado | Por API: impressao |
|  | Fechar visualização | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Primeira página | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Página anterior | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Próxima página | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Última página | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Várias páginas na prévia | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Tela inteira | 🟡 Implementado sem validação completa | botão presente; não validado |
