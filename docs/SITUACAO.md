# Situação do projeto AY ESCREVA — lista única

> Gerado por `tools/gerar-situacao.mjs` em 22/10/2026, a partir de `docs/situacao-base.json` (itens do
> pedido original e das entregas, com a evidência de cada um) e de `docs/MATRIZ-FUNCIONALIDADES.md` (ferramentas da faixa,
> geradas pelos testes). Não editar à mão.

Versão pública: **0.2.0**. Versão de testes local mais recente: **0.7.0**
(`out\instalador\AYEscreva-0.7.0-teste-windows11-x64.exe`).

| Situação | Requisitos e entregas | Ferramentas da faixa |
|---|---|---|
| ✅ Concluído e testado | 31 | 172 |
| 🟡 Implementado sem validação completa | 12 | 73 |
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
| Navegação por teclado nos diálogos e painéis do AY | ✅ Concluído e testado | Foco inicial, Tab e Shift+Tab e teclas de acesso sem repetição conferidos nos diálogos Formatar, Modelo da instituição e Gerenciar IA local; botões dos painéis acionados pelo teclado. Esses testes usam teclas SIMULADAS pelo motor (robô de teclas), não o teclado do Windows (RESULTADOS §4, §5.3, §5.5, §14). |
| Navegação por teclado nos painéis de IA e diálogos novos (D e E) | ✅ Concluído e testado | Botões acionados pelo teclado; Tab/Shift+Tab e teclas de acesso conferidos em Gerenciar IA local, Conferir referências e Verificar atualizações, com teclas simuladas pelo motor (robô de teclas) (RESULTADOS §14). |
| Navegação por teclado na faixa de opções e nos diálogos com o teclado real (F6, setas, Tab, Esc, foco visível) | 🟡 Implementado sem validação completa | Teclado real do Windows (fase 11, RESULTADOS §14): F6 leva às abas da faixa (1 toque); setas trocam de aba; Esc fecha 8 diálogos (4 do AY e 4 do motor) e o foco volta ao texto; ordem do Tab/Shift+Tab conferida em Propriedades, Galeria de modelos e Verificar atualizações. Achado: na faixa, Esc não devolve o foco ao texto (F6 continua o ciclo e volta). Inconclusivo, para conferência manual: Tab dentro da aba até os botões; ordem em Formatar, Conferir referências, Caractere, Parágrafo e Link; foco visível nos botões dos diálogos do AY (não aparece nas capturas). Roteiro: docs/TESTES-MANUAIS.md. |
| Leitor de tela: Narrador (Windows) | 🟡 Implementado sem validação completa | Conferido só o que o leitor RECEBE: com o Narrador ligado, nomes, papéis e foco de botões, campos e listas (5/5, lidos pela árvore de acessibilidade). Ninguém usou o AY de fato com o Narrador e ouviu o resultado: roteiro manual em docs/TESTES-MANUAIS.md §2. |
| Leitores de tela NVDA e JAWS | ⬜ Ainda não implementado | Não instalados neste computador; instalar programas de terceiros depende de autorização. Teste pendente. |
| Escala de exibição 100 % (a deste computador) | ✅ Concluído e testado | Diálogos e painéis sem texto cortado, sem sobreposição e cabendo na tela (8/8, fase 9). Textos apertados encontrados e corrigidos (Cancelar download; botões do Assistente AY). |
| Escalas de exibição 125 %, 150 % e 200 % | ⬜ Ainda não implementado | Não aprovado: só houve teste em 100 % (a escala deste computador). Instruções curtas para o teste manual em 125 %, 150 % e 200 % em docs/TESTES-MANUAIS.md §1 (o roteiro tests/interface/conferir_escala.ps1 ajuda, mas não substitui a conferência visual). |

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
| Recuperação após falha e salvamento seguro | 🟡 Implementado sem validação completa | Implementada e testada com o AY aberto como uma pessoa abre (tests/interface/testar_recuperacao.ps1, RESULTADOS §9): na maioria das quedas provocadas o texto não salvo voltou; numa delas o motor caiu de novo durante o salvamento de emergência e o texto se perdeu (sem cópia automática anterior). Informação de recuperação a cada 3 min (antes 5). A recuperação não é garantida e a Ajuda diz isso. Salvamento seguro: confiabilidade 19/19. |
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
| Usar todas as ferramentas da faixa sem queda do motor | 🟡 Implementado sem validação completa | Investigado em 22/10/2026 (RESULTADOS §9): a queda do motor aparece com entrada simulada pelo próprio motor (robô de teclas que solta a tecla numa janela já fechada; cliques e seleções do UITest), inclusive sem Fontwork. Com o robô que só aperta a tecla: 0 quedas em 6; com o teclado real: 0 quedas em 11 execuções de Fontwork → Link. No teste de efeito, 2 ferramentas derrubam o motor quando o valor é escolhido por simulação (Bordas de página, Espaçamento entre linhas): conferência manual pendente. Defeito do motor 26.8.1, sem correção disponível; risco no uso normal não confirmado nem descartado. |
| Ferramentas da faixa pelo efeito real (efeito, desfazer/refazer, ODT e DOCX reabertos) | 🟡 Implementado sem validação completa | 92 de 93 ferramentas testadas validadas (fases 12 e 12b, docs/VALIDACAO-FERRAMENTAS.md); as demais ferramentas da faixa aparecem por aba no fim desta lista, com o motivo quando o efeito não tem conferência automática. Corrigidos: Uma página, Várias páginas e Exibição de livro (estavam desabilitados). |

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
| Instalador Windows 11 x64 por usuário, sem administrador | ✅ Concluído e testado | Instalação 20/20 com o instalador final da 0.7.0 (22/10/2026), inclusive a varredura da chave privada na pasta instalada. |
| Atualizar uma instalação anterior preservando documentos e preferências | ✅ Concluído e testado | Atualização 0.2.0 → 0.7.0 e 0.5.0 → 0.7.0 com o instalador final: 14/14 (preferências, dicionário pessoal e documentos preservados). |
| Atualização pelo próprio AY (Ajuda › Verificar atualizações) | 🟡 Implementado sem validação completa | Funciona de ponta a ponta com o instalador conferido; depende de publicar atualizacoes.json assinado no site oficial (docs/ATUALIZACOES.md). |
| Site oficial com download e SHA-256 | ✅ Concluído e testado | Publicado (versão 0.2.0); fluxo acessar → baixar → conferir → instalar 25/25. |
| Chave privada de assinatura das atualizações protegida | ✅ Concluído e testado | Procurada byte a byte, sem exibi-la (tests/seguranca/procurar_chave_privada.py, com controle positivo): ausente do repositório e de todo o histórico do git, de dist (o que vira o instalador), de out (instaladores, site, prévias), de tests/output, dos registros em TEMP e das conversas de desenvolvimento; a instalação de teste também é varrida. Só a chave pública vai no AY. Cópia de segurança, perda e vazamento: docs/ATUALIZACOES.md. |
| Site preparado para a 0.7.0 (versão de testes, Windows 11 x64) | 🟡 Implementado sem validação completa | Prévia local em out/site-previa-0.7.0: requisitos, limitações, tamanho, SHA-256, instruções, diferença entre assinatura das atualizações e assinatura digital do instalador, IA local (≈3,4 GB, requisitos testados, funções que dependem dela). Não publicado: o gerador recusa o modo de publicação enquanto a 0.7.0 não estiver marcada como publicada. |
| Pacote de distribuição e arquivo de versões assinado da 0.7.0 | 🟡 Implementado sem validação completa | Instalador, NOTAS.md, SHA256SUMS.txt, atualizacoes.json + .sig (assinado com a chave do projeto e conferido com o código de verificação do AY) e site no modo de publicação, prontos em out/ (docs/ATUALIZACOES.md). Nada foi publicado; a 0.2.0 continua sendo a versão pública. |
| Assinatura digital do instalador | ⬜ Ainda não implementado | Sem certificado de assinatura de código; o SmartScreen pode avisar. |
| Pacote MSI para empresas | ⬜ Ainda não implementado | Não feito. |

## Ferramentas da faixa de opções (pedido original, por aba)

Cada função pedida, com o resultado dos testes. Detalhes (comando, critério de aceite) em
[MATRIZ-FUNCIONALIDADES.md](MATRIZ-FUNCIONALIDADES.md). "Implementado sem validação completa" aqui é, na maioria, um
botão que o teste aciona e confirma o comando disparado, sem conferir o efeito no documento. As ferramentas próprias
do AY (Assistente AY, IA local, formatação acadêmica, conferências, atualizações) têm testes dedicados, contados na
seção "Entregas de assistência à escrita" acima.

### Arquivo — ✅ 13 · 🟡 7 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Novo | Novo documento | ✅ Concluído e testado | Por API: aceite_etapa1 |
| Novo | Galeria de modelos | ✅ Concluído e testado | Pela interface (teste dedicado): Galeria de modelos abre pela aba Arquivo (comando); Galeria lista ofício, memorando, relatório, currículo, carta, ata e proposta, com origem de cada modelo; Criar documento: ofício novo, sem título e |
| Novo | Modelos | 🟡 Implementado sem validação completa | botão presente; não validado |
| Novo | Salvar como modelo | ✅ Concluído e testado | Pela interface (teste dedicado): Salvar como modelo abre pela aba Arquivo (comando); Salvar como modelo: .ott gravado na pasta de modelos do perfil e listado na galeria |
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
| Informações | Propriedades | ✅ Concluído e testado | Pela interface (efeito real): título do documento pelo diálogo Propriedades: '' → 'Título pelo diálogo'; desfazer não se aplica (só muda a exibição ou a seleção); ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Informações | Versões | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Informações | Assinatura digital | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — exige um certificado digital instalado no Windows |
| Informações | Recuperação de documentos | ✅ Concluído e testado | Pela interface: abriria backup (arquivo existe; abertura simulada no teste) |
| Informações | Configurações | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |

### Página Inicial — ✅ 34 · 🟡 3 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Área de transferência | Colar | ✅ Concluído e testado | Pela interface (efeito real): ocorrências de "zeta" (colado no fim do 2º parágrafo): 1 → 2; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Área de transferência | Recortar | ✅ Concluído e testado | Pela interface (efeito real): ocorrências de "gama": 1 → 0; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Área de transferência | Copiar | ✅ Concluído e testado | Pela interface (efeito real): ocorrências de "beta" depois de copiar pela faixa e colar no fim: 1 → 2; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Área de transferência | Pincel de formatação | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — o formato é aplicado na próxima seleção feita com o mouse; o teste não simula o arraste |
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
| Fonte | Cor da fonte | ✅ Concluído e testado | Pela interface (efeito real): cor da fonte de "teta": -1 → 13181214; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Fonte | Realce | ✅ Concluído e testado | Por API: aceite_etapa1 (realce no DOCX) |
| Fonte | Limpar formatação | ✅ Concluído e testado | Pela interface: CharWeight=100.0 depois do clique |
| Fonte | Caractere (diálogo) | ✅ Concluído e testado | Pela interface (efeito real): tamanho da fonte de "alfa" pelo diálogo Caractere (20 pt): 12.0 → 20.0; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Parágrafo | Marcadores | ✅ Concluído e testado | Pela interface: NumberingIsNumber=True depois do clique |
| Parágrafo | Numeração | ✅ Concluído e testado | Pela interface: NumberingIsNumber=True depois do clique |
| Parágrafo | Lista multinível | ✅ Concluído e testado | Pela interface (efeito real): numeração de tópicos no parágrafo: False → True; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Parágrafo | Diminuir recuo | ✅ Concluído e testado | Pela interface: ParaLeftMargin=0 depois do clique |
| Parágrafo | Aumentar recuo | ✅ Concluído e testado | Pela interface: ParaLeftMargin=1251 depois do clique |
| Parágrafo | Marcas de formatação | ✅ Concluído e testado | Pela interface: ShowNonprintingCharacters: False → True |
| Parágrafo | Alinhar à esquerda | ✅ Concluído e testado | Pela interface: ParaAdjust=0 depois do clique |
| Parágrafo | Centralizar | ✅ Concluído e testado | Pela interface: ParaAdjust=3 depois do clique |
| Parágrafo | Alinhar à direita | ✅ Concluído e testado | Pela interface: ParaAdjust=1 depois do clique |
| Parágrafo | Justificar | ✅ Concluído e testado | Pela interface: ParaAdjust=2 depois do clique |
| Parágrafo | Espaçamento entre linhas | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — escolher o valor na lista pelo teste automático derrubou o motor nas 3 tentativas (entrada simulada, RESULTADOS §9); conferência manual pendente |
| Parágrafo | Aumentar espaço entre parágrafos | ✅ Concluído e testado | Pela interface (efeito real): espaço antes+depois do parágrafo: (0, 0) → (101, 101); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Parágrafo | Diminuir espaço entre parágrafos | ✅ Concluído e testado | Pela interface (efeito real): espaço antes+depois do parágrafo: (499, 499) → (399, 399); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Parágrafo | Parágrafo (diálogo) | ✅ Concluído e testado | Pela interface (efeito real): recuo à esquerda pelo diálogo Parágrafo (2 cm): 0 → 2000; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Estilos | Estilo do parágrafo | ✅ Concluído e testado | Por API: aceite_etapa1 (Título 1) |
| Estilos | Painel de estilos | ✅ Concluído e testado | Pela interface (efeito real): painel Estilos visível na barra lateral: False → True; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Edição | Localizar e substituir | ✅ Concluído e testado | Pela interface (efeito real): Substituir tudo: "gama" → "GAMA-TROCADA": 0 → 1; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Edição | Selecionar tudo | ✅ Concluído e testado | Pela interface (efeito real): tamanho da seleção: (0, 106) → (106, 106); desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |

### Inserir — ✅ 19 · 🟡 4 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Páginas | Capa | ✅ Concluído e testado | Pela interface (efeito real): páginas do documento (página de rosto nova): 1 → 2; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Páginas | Página em branco | ✅ Concluído e testado | Pela interface: paginas: 2 → 4 |
| Páginas | Quebra de página | ✅ Concluído e testado | Pela interface: paginas: 1 → 2 |
| Páginas | Quebras (página, coluna, linha) | ✅ Concluído e testado | Por API: ida_e_volta (3 seções) |
| Páginas | Seção | ✅ Concluído e testado | Pela interface (efeito real): seções no documento: 0 → 1; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Tabelas | Tabela | ✅ Concluído e testado | Por API: aceite_etapa1, ida_e_volta (mescladas) |
| Ilustrações | Imagem | ✅ Concluído e testado | Por API: aceite_etapa1 |
| Ilustrações | Formas | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — a forma é desenhada com o mouse depois da escolha; o teste não simula o traço |
| Ilustrações | Gráfico | ✅ Concluído e testado | Pela interface (efeito real): gráficos na página (objetos incorporados no texto): 0 → 1; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Ilustrações | Fontwork (texto artístico) | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Links e comentários | Link | ✅ Concluído e testado | Por API: ida_e_volta |
| Links e comentários | Indicador | ✅ Concluído e testado | Por API: ida_e_volta |
| Links e comentários | Referência cruzada | ✅ Concluído e testado | Por API: ida_e_volta |
| Links e comentários | Comentário | ✅ Concluído e testado | Pela interface: comentarios: 0 → 1 |
| Cabeçalho e rodapé | Cabeçalho | ✅ Concluído e testado | Por API: aceite_etapa1, ida_e_volta |
| Cabeçalho e rodapé | Rodapé | ✅ Concluído e testado | Por API: aceite_etapa1, ida_e_volta |
| Cabeçalho e rodapé | Número de página | ✅ Concluído e testado | Por API: aceite_etapa1 (campo de página) |
| Texto | Caixa de texto | ✅ Concluído e testado | Por API: ida_e_volta (caixa de texto) |
| Texto | Quadro | ✅ Concluído e testado | Pela interface (efeito real): quadros no documento (no DOCX, viram caixas de texto): 0 → 1; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Texto | Campos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Texto | Data | ✅ Concluído e testado | Pela interface (efeito real): campos de data: 0 → 1; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Símbolos | Equação | ✅ Concluído e testado | Por API: ida_e_volta (OMML) |
| Símbolos | Símbolo | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |

### Desenhar — ✅ 3 · 🟡 6 · ⬜ 3

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Ferramentas | Selecionar traços | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — modo de seleção para o mouse |
| Ferramentas | Caneta (linha à mão livre) | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — desenho à mão livre com o mouse; o teste não simula o traço |
| Ferramentas | Forma livre preenchida | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — desenho à mão livre com o mouse; o teste não simula o traço |
| Ferramentas | Linha | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — desenho com o mouse na página; o teste não simula o traço |
| Ferramentas | Curva | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — desenho com o mouse na página; o teste não simula o traço |
| Ferramentas | Marca-texto | ⬜ Ainda não implementado | Sem ferramenta própria na base; previsto como predefinição de traço (amarelo, translúcido, largo) na extensão AY. |
| Ferramentas | Borracha | ⬜ Ainda não implementado | A base só exclui o traço selecionado (botão Excluir traço). Borracha por arrasto exige código C++ (Nível 2). |
| Ferramentas | Sensibilidade à pressão da caneta | ⬜ Ainda não implementado | Não suportado pela base; tinta do Word (InkML) é importada como imagem ou forma, sem pressão. |
| Traço | Cor do traço | ✅ Concluído e testado | Pela interface (efeito real): cor da linha da forma (preta antes): 0 → 3433892; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Traço | Espessura e estilo | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Traço | Agrupar | ✅ Concluído e testado | Pela interface (efeito real): formas soltas na página: 2 → 1; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Traço | Excluir traço | ✅ Concluído e testado | Pela interface (efeito real): formas na página: 2 → 1; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |

### Design — ✅ 1 · 🟡 4 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Formatação do documento | Temas, cores e fontes do documento | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Formatação do documento | Conjuntos de estilos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — A base importa estilos de modelos; a galeria visual de conjuntos (como no Word) será feita com modelos AY. |
| Plano de fundo da página | Marca-d'água | 🟡 Implementado sem validação completa | Teste de efeito FALHOU: marca-d'água "RASCUNHO": None → 'RASCUNHO'; desfazer FALHOU, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Plano de fundo da página | Cor e bordas da página | ✅ Concluído e testado | Pela interface (efeito real): cor de fundo da página (estilo de página): 'NONE' → 'SOLID'; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Plano de fundo da página | Bordas de página | 🟡 Implementado sem validação completa | botão presente; não validado — escolher a borda predefinida pelo teste automático derrubou o motor (entrada simulada, RESULTADOS §9); a cor da página, no mesmo diálogo, foi validada; conferência manual pendente |

### Layout — ✅ 16 · 🟡 4 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Configurar página | Margens | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Configurar página | Orientação | ✅ Concluído e testado | Por API: ida_e_volta (paisagem) |
| Configurar página | Tamanho do papel | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Configurar página | Colunas | ✅ Concluído e testado | Por API: ida_e_volta (2 colunas) |
| Configurar página | Quebras de página e seção | ✅ Concluído e testado | Por API: ida_e_volta (3 seções) |
| Configurar página | Hifenização | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Configurar página | Numeração de linhas | ✅ Concluído e testado | Pela interface (efeito real): numeração de linhas ligada: False → True; desfazer não se aplica (só muda a exibição ou a seleção); ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Configurar página | Estilo de página (diálogo) | ✅ Concluído e testado | Pela interface (efeito real): margem esquerda da página (3 cm): 2000 → 3000; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Parágrafo | Recuos e espaçamento | ✅ Concluído e testado | Pela interface (efeito real): recuo à esquerda pelo diálogo Parágrafo (2 cm): 0 → 2000; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Organizar | Sem quebra automática | ✅ Concluído e testado | Pela interface (efeito real): quebra do texto em volta da imagem: ('PARALLEL',) → ('NONE',); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Organizar | Quebra automática | ✅ Concluído e testado | Pela interface (efeito real): quebra do texto em volta da imagem: ('NONE',) → ('PARALLEL',); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Organizar | Quebra ideal | ✅ Concluído e testado | Pela interface (efeito real): quebra do texto em volta da imagem: ('NONE',) → ('DYNAMIC',); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Organizar | Atrás/na frente do texto | ✅ Concluído e testado | Pela interface (efeito real): quebra do texto em volta da imagem: ('NONE',) → ('THROUGH',); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Organizar | Trazer para frente | ✅ Concluído e testado | Pela interface (efeito real): ordem: a forma 1 fica na frente da 2: (0, 1) → (1, 0); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Organizar | Enviar para trás | ✅ Concluído e testado | Pela interface (efeito real): ordem: a forma 2 fica atrás da 1: (0, 1) → (1, 0); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Organizar | Ancorar à página | ✅ Concluído e testado | Pela interface (efeito real): âncora da imagem: ('AT_PARAGRAPH',) → ('AT_PAGE',); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: NÃO mantido (o DOCX não tem âncora "na página" nem "no parágrafo" como o ODT: ao reabrir, a imagem flutuante fica presa a um caractere, com a mesma posição na página) |
| Organizar | Ancorar ao parágrafo | ✅ Concluído e testado | Pela interface (efeito real): âncora da imagem: ('AT_CHARACTER',) → ('AT_PARAGRAPH',); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: NÃO mantido (o DOCX não tem âncora "na página" nem "no parágrafo" como o ODT: ao reabrir, a imagem flutuante fica presa a um caractere, com a mesma posição na página) |
| Organizar | Ancorar como caractere | ✅ Concluído e testado | Pela interface (efeito real): âncora da imagem (como caractere): ('AT_PARAGRAPH',) → ('AS_CHARACTER',); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Organizar | Alinhar objetos | ✅ Concluído e testado | Pela interface (efeito real): alinhamento horizontal da imagem: (2,) → (3,); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Organizar | Girar | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — a rotação é feita com o mouse nas alças do objeto |

### Referências — ✅ 16 · 🟡 3 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Trabalho acadêmico | Formatar trabalho acadêmico | ✅ Concluído e testado | Pela interface (teste dedicado): Formatar trabalho acadêmico abre pela aba Referências (comando); Prévia pelo teclado: lista do que vai mudar, sem alterar o documento; Aplicar numa cópia: relatório de conformidade aparece com as regr |
| Trabalho acadêmico | Relatório de conformidade | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Trabalho acadêmico | Conferir referências | ✅ Concluído e testado | Pela interface (teste dedicado): Conferir referências: lista o problema plantado, "Ir para" seleciona o trecho, controles com nome acessível |
| Trabalho acadêmico | Conferir consistência | ✅ Concluído e testado | Pela interface (teste dedicado): Conferir consistência: lista o problema plantado, "Ir para" seleciona o trecho, controles com nome acessível |
| Sumário | Sumário e índices | ✅ Concluído e testado | Por API: ida_e_volta (sumário) |
| Sumário | Atualizar sumário | ✅ Concluído e testado | Pela interface (efeito real): título novo aparece no sumário: False → True; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Sumário | Atualizar todos os índices | ✅ Concluído e testado | Pela interface (efeito real): título novo aparece no sumário: False → True; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Notas | Nota de rodapé | ✅ Concluído e testado | Pela interface: notasRodape: 0 → 1 |
| Notas | Nota de fim | ✅ Concluído e testado | Pela interface: notasFim: 0 → 1 |
| Notas | Configurar notas | ✅ Concluído e testado | Pela interface (efeito real): tipo de numeração das notas de rodapé: 4 → 1; desfazer não se aplica (só muda a exibição ou a seleção); ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Citações e bibliografia | Inserir citação | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Citações e bibliografia | Banco de dados bibliográfico | 🟡 Implementado sem validação completa | botão presente; não validado — abre o banco de dados bibliográfico em outra janela; sem efeito no documento |
| Citações e bibliografia | Bibliografia | ✅ Concluído e testado | Por API: ida_e_volta (sumário) |
| Legendas | Inserir legenda | ✅ Concluído e testado | Pela interface (efeito real): legenda abaixo da imagem: False → True; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Legendas | Lista de figuras | ✅ Concluído e testado | Por API: ida_e_volta (sumário) |
| Legendas | Referência cruzada | ✅ Concluído e testado | Por API: ida_e_volta |
| Índice remissivo | Marcar entrada | ✅ Concluído e testado | Pela interface (efeito real): entradas de índice marcadas: 0 → 1; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Índice remissivo | Inserir índice remissivo | ✅ Concluído e testado | Por API: ida_e_volta (sumário) |
| Índice remissivo | Atualizar campos | ✅ Concluído e testado | Pela interface (efeito real): campo de hora (com segundos) atualizado: '14:19:39' → '14:19:41'; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |

### Correspondência — ✅ 0 · 🟡 14 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Criar | Envelopes | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Criar | Etiquetas | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Iniciar mala direta | Assistente de mala direta | 🟡 Implementado sem validação completa | botão presente; não validado — exige uma fonte de dados (planilha ou banco) cadastrada |
| Iniciar mala direta | Selecionar destinatários | 🟡 Implementado sem validação completa | botão presente; não validado — exige uma fonte de dados cadastrada |
| Iniciar mala direta | Exibir fonte de dados | 🟡 Implementado sem validação completa | botão presente; não validado — exige uma fonte de dados cadastrada |
| Iniciar mala direta | Inserir campo de mesclagem | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Visualizar resultados | Primeiro registro | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — exige uma fonte de dados cadastrada |
| Visualizar resultados | Registro anterior | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — exige uma fonte de dados cadastrada |
| Visualizar resultados | Próximo registro | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — exige uma fonte de dados cadastrada |
| Visualizar resultados | Último registro | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido — exige uma fonte de dados cadastrada |
| Concluir | Gerar documentos | 🟡 Implementado sem validação completa | botão presente; não validado — exige uma fonte de dados cadastrada |
| Concluir | Salvar documentos mesclados | 🟡 Implementado sem validação completa | botão presente; não validado — exige uma fonte de dados cadastrada |
| Concluir | Imprimir documentos mesclados | 🟡 Implementado sem validação completa | botão presente; não validado — exige uma fonte de dados cadastrada e uma impressora |
| Concluir | Enviar por e-mail | 🟡 Implementado sem validação completa | botão presente; não validado — Exige SMTP configurado pelo usuário; fica fora da faixa por padrão (o produto não envia nada sem autorização).; exige uma fonte de dados cadastrada e uma conta de e-mail configurada |

### Revisão — ✅ 20 · 🟡 6 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Assistente AY | Assistente AY | ✅ Concluído e testado | Pela interface (teste dedicado): Painel Assistente AY abre pela aba Revisão (comando "Assistente AY"); Acessibilidade: listas anunciadas pelo próprio rótulo (não pelo título do painel); Acessibilidade: controles do painel com nome ac |
| Assistente AY | Verificar documento | ✅ Concluído e testado | Pela interface (teste dedicado): Verificar documento pelo teclado: erro de ortografia listado com sugestões; Cancelar interrompe a verificação; Documento longo verificado por completo |
| Assistente AY | Correção automática | ✅ Concluído e testado | Pela interface (teste dedicado): Correção automática ao digitar (nao, voce, tambem); Ctrl+Z desfaz só a correção (o espaço digitado fica); Proteções: nome próprio, sigla, grafia mista, data, palavra com número e citação não mudam; Co |
| IA local | Revisão com IA | ✅ Concluído e testado | Pela interface (teste dedicado): Painel Revisão com IA abre pela aba Revisão (comando "Revisão com IA"); Revisar seleção pelo teclado: a IA trabalha em segundo plano e a digitação no documento continua; Aceitar aplica como alteração |
| IA local | Gerenciar IA local | ✅ Concluído e testado | Pela interface (teste dedicado): Gerenciar IA local abre pelo painel (teclado); Gerenciar IA local: modelos com licença, tamanho, origem e espaço livre; explica que é opcional e local; Gerenciar IA local fecha sem baixar nada |
| Revisão de texto | Ortografia e gramática | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Revisão de texto | Revisão automática | ✅ Concluído e testado | Pela interface (efeito real): revisão automática (estado do comando): True → False; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Revisão de texto | Sinônimos | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Revisão de texto | Contagem de palavras | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Revisão de texto | Idioma do texto | 🟡 Implementado sem validação completa | botão presente; não validado |
| Revisão de texto | Verificar acessibilidade | ✅ Concluído e testado | Pela interface (efeito real): painel Verificar acessibilidade visível na barra lateral: False → True; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Comentários | Novo comentário | ✅ Concluído e testado | Por API: ida_e_volta |
| Comentários | Excluir todos os comentários | ✅ Concluído e testado | Pela interface (efeito real): comentários: 2 → 0; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Comentários | Mostrar comentários | ✅ Concluído e testado | Pela interface (efeito real): mostrar comentários (estado do comando): True → False; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Controle de alterações | Controlar alterações | ✅ Concluído e testado | Pela interface: RecordChanges=True |
| Controle de alterações | Mostrar alterações | ✅ Concluído e testado | Pela interface (efeito real): mostrar alterações (estado do comando): True → False; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Controle de alterações | Gerenciar alterações | ✅ Concluído e testado | Pela interface (efeito real): alterações pendentes (Aceitar todas no diálogo): (2, True, True) → (0, True, False); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Controle de alterações | Proteger controle de alterações | ✅ Concluído e testado | Pela interface (efeito real): controle de alterações protegido por senha (senha de teste): False → True; desfazer não se aplica (só muda a exibição ou a seleção); ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Alterações | Aceitar | ✅ Concluído e testado | Pela interface (efeito real): alterações pendentes e texto inserido: (2, True, True) → (1, True, True); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Alterações | Rejeitar | ✅ Concluído e testado | Pela interface (efeito real): alterações pendentes e texto inserido: (2, True, True) → (1, False, True); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Alterações | Alteração anterior | ✅ Concluído e testado | Pela interface (efeito real): trecho selecionado: '' → 'inserção controlada '; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Alterações | Próxima alteração | ✅ Concluído e testado | Pela interface (efeito real): trecho selecionado: '' → 'gama '; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Alterações | Aceitar todas | ✅ Concluído e testado | Pela interface (efeito real): alterações pendentes, inserção e exclusão: (2, True, True) → (0, True, False); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Alterações | Rejeitar todas | ✅ Concluído e testado | Pela interface (efeito real): alterações pendentes, inserção e exclusão: (2, True, True) → (0, False, True); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
| Comparar | Comparar documentos | 🟡 Implementado sem validação completa | botão presente; não validado |
| Comparar | Combinar documentos | 🟡 Implementado sem validação completa | botão presente; não validado |

### Exibir — ✅ 16 · 🟡 5 · ⬜ 1

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
| Modos de exibição | Layout de impressão | ✅ Concluído e testado | Pela interface (efeito real): layout de impressão (sai do layout da web): (False, True) → (True, False); desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Modos de exibição | Layout da web | ✅ Concluído e testado | Pela interface (efeito real): layout da web (estado do comando): False → True; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Modos de exibição | Tela inteira | 🟡 Implementado sem validação completa | botão presente; não validado |
| Modos de exibição | Modo de leitura | ⬜ Ainda não implementado | Hoje: Tela inteira + Exibição de livro. Modo de leitura dedicado (sem edição) previsto na extensão AY. |
| Zoom | Zoom | 🟡 Implementado sem validação completa | botão acionado pela interface; efeito não conferido |
| Zoom | 100% | ✅ Concluído e testado | Pela interface: ZoomType=3 ZoomValue=100 |
| Zoom | Página inteira | ✅ Concluído e testado | Pela interface: ZoomType=2 ZoomValue=68 |
| Zoom | Largura da página | ✅ Concluído e testado | Pela interface: ZoomType=1 ZoomValue=223 |
| Zoom | Uma página | ✅ Concluído e testado | Pela interface (efeito real): leiaute da exibição (colunas, livro): (2, True) → (1, False); desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Zoom | Várias páginas | ✅ Concluído e testado | Pela interface (efeito real): leiaute da exibição (colunas, livro): (1, False) → (0, False); desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Zoom | Exibição de livro | ✅ Concluído e testado | Pela interface (efeito real): leiaute da exibição (colunas, livro): (1, False) → (2, True); desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Mostrar | Régua | ✅ Concluído e testado | Pela interface: ShowRulers: True → False |
| Mostrar | Painel de navegação | ✅ Concluído e testado | Pela interface (efeito real): painel de navegação (estado do comando): False → True; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Mostrar | Barra lateral | ✅ Concluído e testado | Pela interface (efeito real): barra lateral (estado do comando): True → False; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Mostrar | Marcas de formatação | ✅ Concluído e testado | Pela interface (efeito real): marcas de formatação na exibição: False → True; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Mostrar | Limites do texto | ✅ Concluído e testado | Pela interface (efeito real): limites do texto (estado do comando): True → False; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Mostrar | Grade | ✅ Concluído e testado | Pela interface (efeito real): grade (estado do comando): False → True; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Mostrar | Ocultar espaço em branco | ✅ Concluído e testado | Pela interface (efeito real): ocultar espaço em branco (estado do comando): True → False; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Janela e tema | Nova janela | ✅ Concluído e testado | Pela interface (efeito real): janelas abertas do documento: 1 → 2; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |
| Janela e tema | Fechar janela | 🟡 Implementado sem validação completa | botão presente; não validado |
| Janela e tema | Alternar entre janelas | 🟡 Implementado sem validação completa | botão presente; não validado |
| Janela e tema | Tema claro/escuro | 🟡 Implementado sem validação completa | botão presente; não validado — muda o tema de todo o aplicativo (preferência do usuário) |

### Ajuda — ✅ 5 · 🟡 5 · ⬜ 0

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
| Diagnóstico | Reiniciar em modo de segurança | 🟡 Implementado sem validação completa | botão presente; não validado — reinicia o aplicativo; não pode ser conferido de dentro do teste |
| Diagnóstico | Verificar atualizações (opcional) | ✅ Concluído e testado | Pela interface (teste dedicado): Verificar atualizações abre pela aba Ajuda; Verificar agora consulta o site oficial em segundo plano; sem versão assinada publicada, explica e não oferece download |

### Tabela (contextual) — ✅ 15 · 🟡 1 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
|  | Inserir linha acima | ✅ Concluído e testado | Pela interface (efeito real): linhas, colunas e células: (3, 3, 9) → (4, 3, 12); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Inserir linha abaixo | ✅ Concluído e testado | Pela interface: linhas: 2 → 3 |
|  | Inserir coluna à esquerda | ✅ Concluído e testado | Pela interface (efeito real): linhas, colunas e células: (3, 3, 9) → (3, 4, 12); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Inserir coluna à direita | ✅ Concluído e testado | Pela interface (efeito real): linhas, colunas e células: (3, 3, 9) → (3, 4, 12); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Excluir linhas | ✅ Concluído e testado | Pela interface (efeito real): linhas, colunas e células: (3, 3, 9) → (2, 3, 6); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Excluir colunas | ✅ Concluído e testado | Pela interface (efeito real): linhas, colunas e células: (3, 3, 9) → (3, 2, 6); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Excluir tabela | ✅ Concluído e testado | Pela interface (efeito real): tabelas no documento: 1 → 0; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Mesclar células | ✅ Concluído e testado | Pela interface (efeito real): linhas, colunas e células (A1 e B1 selecionadas): (3, 3, 9) → (3, 2, 8); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Dividir células | ✅ Concluído e testado | Pela interface (efeito real): linhas, colunas e células (A1 dividida em 2): (3, 3, 9) → (4, 3, 10); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Ajustar largura das colunas | ✅ Concluído e testado | Pela interface (efeito real): separadores das colunas (1ª coluna com texto longo): (3333, 6666) → (9020, 9510); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Bordas | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Sombreamento | ✅ Concluído e testado | Pela interface (efeito real): cor de fundo da célula A1: -1 → 16776960; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Estilos de tabela | ✅ Concluído e testado | Pela interface (efeito real): aparência da tabela (cor da célula A1): -1 → 22941; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Classificar | ✅ Concluído e testado | Pela interface (efeito real): ordem da 1ª coluna (c, b, a → a, b, c): ('c', 'b', 'a') → ('a', 'b', 'c'); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Propriedades da tabela | ✅ Concluído e testado | Pela interface (efeito real): alinhamento da tabela (centralizada): 6 → 2; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Selecionar tabela | ✅ Concluído e testado | Pela interface (efeito real): células selecionadas: 'SwXTextRanges' → 9; desfazer não se aplica (só muda a exibição ou a seleção); não fica no arquivo |

### Imagem (contextual) — ✅ 8 · 🟡 3 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
|  | Recortar | 🟡 Implementado sem validação completa | botão presente; não validado — o recorte é feito com o mouse nas alças da imagem |
|  | Texto alternativo | ✅ Concluído e testado | Por API: aceite_etapa1, ida_e_volta |
|  | Trocar imagem | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Compactar imagem | ✅ Concluído e testado | Pela interface (efeito real): formato da imagem depois de comprimir em JPEG: 'image/png' → 'image/jpeg'; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Salvar imagem | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Girar à esquerda | ✅ Concluído e testado | Pela interface (efeito real): rotação da imagem (graus × 10): 0 → 900; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Girar à direita | ✅ Concluído e testado | Pela interface (efeito real): rotação da imagem (graus × 10): 0 → 2700; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Espelhar vertical | ✅ Concluído e testado | Pela interface (efeito real): espelhamento vertical: (False,) → (True,); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: NÃO mantido ((False,)) |
|  | Espelhar horizontal | ✅ Concluído e testado | Pela interface (efeito real): espelhamento horizontal (páginas pares e ímpares): (False, False) → (True, True); desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Propriedades da imagem | ✅ Concluído e testado | Pela interface (efeito real): nome da imagem pelo diálogo Figura: 'ImagemTeste' → 'ImagemRenomeada'; desfazer não se aplica (só muda a exibição ou a seleção); ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Legenda | ✅ Concluído e testado | Pela interface (efeito real): legenda abaixo da imagem: False → True; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |

### Forma (contextual) — ✅ 5 · 🟡 1 · ⬜ 0

| Grupo | Função | Situação | Como foi verificado |
|---|---|---|---|
|  | Preenchimento | ✅ Concluído e testado | Pela interface (efeito real): cor de preenchimento da forma (branca antes): 16777215 → 7512015; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Área | ✅ Concluído e testado | Pela interface (efeito real): preenchimento da forma (nenhum): 'SOLID' → 'NONE'; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Linha | 🟡 Implementado sem validação completa | botão presente; não validado |
|  | Posição e tamanho | ✅ Concluído e testado | Pela interface (efeito real): largura da forma (6 cm): 3000 → 6001; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Agrupar | ✅ Concluído e testado | Pela interface (efeito real): formas soltas na página: 2 → 1; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |
|  | Desagrupar | ✅ Concluído e testado | Pela interface (efeito real): formas soltas na página: 1 → 2; desfazer ok, refazer ok; ODT: mantido ao salvar e reabrir; DOCX: mantido ao salvar e reabrir |

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
