# Revisão de texto, Assistente AY e IA local — decisões técnicas

Verificado em 20/10/2026. Este documento registra **o que foi decidido, por quê e com base em quê**. O que ainda
depende de teste está marcado como decisão preliminar.

## 1. Princípios

1. O editor funciona inteiro **sem IA e sem internet**. Revisão ortográfica e gramatical básica é offline.
2. Nada sai do computador automaticamente: nem documentos, nem trechos, nem diagnósticos. Uma integração
   remota futura será opcional e dirá antes o destino, o conteúdo enviado e o custo.
3. O texto do documento é **dado a analisar**, nunca instrução para o aplicativo (ver §5.4).
4. Toda alteração automática pode ser desfeita (Ctrl+Z) e é desligável. Alterações substanciais mostram
   original × proposta antes de aplicar.
5. Separar sempre: implementado, testado e limitação conhecida.

## 2. O que o motor já oferece (inspecionado em `dist/AY ESCREVA/share`)

| Componente | Versão / origem | Licença | O que faz | Uso no AY |
|---|---|---|---|---|
| Hunspell + dicionário pt-BR VERO | extensão `dict-pt-BR` 3.3.0 | LGPLv3 / MPL | ortografia, sugestões, sublinhado vermelho | **Ortografia** (detecção) |
| Lightproof pt-BR (Raimundo Moura, 2013) | mesma extensão | MPL 1.1 / GPLv3+ / LGPLv3+ | 26 categorias de regras com explicação curta: crase, maiúsculas, palavras duplicadas, parênteses e aspas, espaços, pontuação, "há/a", "mal/mau", "meio/meia", concordância verbal, colocação pronominal, pronomes, porquês, parônimos, compostos, pleonasmos, gerundismo, cacofonia | **Gramática e pontuação** e parte do **Estilo** |
| Lista de AutoCorreção pt-BR | `share/autocorr/acor_pt-BR.dat` (3.403 entradas) | MPL 2.0 | troca ao digitar, sem proteções; mistura erros de digitação, abreviações ("vc"→"você"), regras de símbolos e trocas de várias palavras | dividida: símbolos continuam no motor; palavras viram a tabela filtrada do AY (§3.1) |
| Sinônimos e hifenização pt-BR | mesma extensão | LGPL / MPL | — | sem mudança |

Teste de protótipo (20/10/2026): digitar `nao ` num documento virou `Não` pela AutoCorreção da base, sem
nenhuma regra de proteção. Por isso a troca de palavras passa para o mecanismo do AY.

## 3. Correção em três níveis independentes

Configuração por usuário (perfil local), com padrões: Ortografia **ligada**, Correção automática **ligada**,
Gramática e pontuação **ligada**, Estilo **desligado**.

### 3.1 Ortografia

- **Detecção**: Hunspell pt-BR, como hoje (sublinhado vermelho), offline.
- **Correção automática** (mecanismo do AY, extensão em Python):
  - age **só quando a palavra termina** (espaço, Enter, Tab ou pontuação), nunca no meio da palavra;
  - a troca entra no histórico como uma ação própria ("Correção automática do AY: nao → não"): **Ctrl+Z**
    desfaz só a correção; o cursor permanece onde estava;
  - usa só a **tabela de casos inequívocos** gerada por `tools/gerar_correcoes.py` (88.589 entradas em
    20/10/2026: 271 de acentuação e 762 de digitação vindas de `acor_pt-BR.dat`, e 87.556 de acentuação vindas dos
    radicais do dicionário VERO), conferida no próprio Hunspell. Uma entrada da lista da base só entra se:
    1. a palavra original **não** existe no dicionário pt-BR, nem no pt-PT ou inglês instalados (palavra válida em
       outro idioma é ambígua; o espanhol ficou de fora porque o AY só corrige texto marcado pt-BR e palavras
       arcaicas como "nao" — um tipo de navio — bloqueariam a correção mais comum);
    2. a correção existe no dicionário pt-BR;
    3. a diferença é só de acentuação **ou** é um erro de digitação pequeno (até 2 edições) em que a
       correção é a **primeira sugestão** do Hunspell;
    4. original e correção são palavras simples em minúsculas (sem abreviações como "vc", sem várias
       palavras, sem símbolos).
    A classe "acentuação (dicionário)" usa radicais minúsculos e acentuados do VERO cuja forma sem acento é
    inválida em pt-BR, pt-PT e inglês e corresponde a um único radical (ex.: "tambem" → "também"; "musica",
    "agua" e "analise" ficam de fora porque também são formas verbais válidas). Formas flexionadas que não são
    radicais ("estao") não entram: ficam só sublinhadas.
  - **nunca troca**: palavras com maiúscula no meio da frase (nomes próprios), siglas (todas maiúsculas),
    palavras com dígitos, ponto, barra, sublinhado, @ ou "://" (termos técnicos, números, datas, endereços),
    trechos entre aspas ou em estilo de citação, texto marcado em outro idioma, palavras do dicionário
    pessoal e palavras marcadas "não corrigir novamente";
  - ao desfazer uma correção, o AY pergunta numa barra de informação se deve deixar de corrigir aquela
    palavra ("Não corrigir novamente").
- **Ignorar** usa a lista "Ignorar tudo" do motor (vale na sessão); **Adicionar ao dicionário** usa o
  dicionário pessoal do motor (`standard.dic` no perfil); **Não corrigir novamente** fica na configuração do AY.
- As entradas de **símbolos** da AutoCorreção da base continuam ativas (`(C)`→©, `--`→–, `...`→…): a
  montagem gera um `acor_pt-BR.dat` só com elas.

### 3.2 Gramática e pontuação

Lightproof pt-BR continua como verificador gramatical do motor (sublinhado azul, menu de contexto, diálogo
Ortografia e gramática). O AY liga e desliga as categorias pelo nível: **Gramática e pontuação** = crase,
maiúsculas, duplicadas, parênteses/aspas, espaços, aspas, apóstrofo, reticências, há/a, mal/mau, meio/meia,
concordância verbal, colocação pronominal, pronomes, porquês, parônimos, compostos. Cada ocorrência traz a
explicação curta do próprio Lightproof.

### 3.3 Estilo (opcional, desligado por padrão)

- Categorias de estilo do Lightproof: pleonasmos, gerundismo, cacofonia.
- Regras do AY (offline, com explicação curta, só no painel): **clareza** (frase com mais de 40 palavras),
  **concisão** (expressões prolixas: "a fim de que" → "para que", "devido ao fato de que" → "porque"…),
  **formalidade** (marcas de oralidade: "pra", "tá", "né", "a gente"…), **repetição** (mesma palavra de
  conteúdo repetida em sequência próxima), **organização** (parágrafo com mais de 200 palavras).
- Sugestões de estilo nunca são aplicadas sozinhas.

## 4. Painel lateral "Assistente AY" e aba Revisão

- Painel da barra lateral do motor (deck próprio), criado em Python pela extensão (`Sidebar.xcu`,
  `Factories.xcu`). Protótipo validado em 20/10/2026.
- Seções: **Revisão do texto** (níveis, correção automática, Verificar seleção / Verificar documento, lista de
  ocorrências com Aplicar, Ignorar, Adicionar ao dicionário, Não corrigir novamente e explicação),
  **Correções automáticas recentes** (desfazer uma a uma) e **IA local** (estado; só ganha botões quando a
  entrega C estiver implementada).
- A análise do documento roda em segundo plano, com progresso e **Cancelar**; a digitação continua livre.
- **Modelo de execução (decidido por teste, 20/10/2026):** o documento só é lido e marcado **na thread
  principal**, em fatias de ~20 ms; uma **thread de trabalho** recebe apenas o texto dos parágrafos e consulta os
  serviços de língua (Hunspell, Lightproof, regras de estilo), como o verificador gramatical do próprio motor faz
  na thread dele. Motivo: num protótipo, uma thread Python que editou o documento logo depois de ele abrir travou
  o motor e a interface parou de responder; nenhuma thread Python do AY toca o documento.
- Custos medidos (i5-8500, 60 parágrafos de ~30 palavras): ler e marcar < 1 ms por parágrafo; ortografia 0,2 ms
  com cache (gerar sugestões custa dezenas de ms, por isso elas só são buscadas ao escolher a ocorrência);
  gramática e estilo do Lightproof ≈ 94 ms por parágrafo (≈ 10 parágrafos por segundo, fora da interface).
- Largura: a janela do painel nasce com a largura mínima (240 px) e a barra lateral a alarga até a área visível;
  `_redimensionar` reparte a largura entre as duas colunas de botões. Motivo (conferido por captura de tela e pela
  árvore de acessibilidade, 20/10/2026): com a largura do `Painel.xdl` (320 px), a janela pedia mais que a área
  visível da barra lateral (275 px) e a coluna da direita ficava cortada. O teste da fase 5 confere que a janela
  cabe na área visível.
- Aba **Revisão**: grupo "Assistente AY" com Assistente AY, Verificar documento e Opções de correção.
- Acessibilidade: rótulos com teclas de acesso, ordem de tabulação, nomes acessíveis nos controles; teste com
  teclado real (robô do toolkit) e leitura da árvore de acessibilidade.

## 5. IA local (decisão preliminar — confirmar com testes na entrega C)

### 5.1 Requisitos

Execução local, sem conta e sem chave; download opcional com tamanho, requisitos e pasta mostrados antes;
cancelar e remover; CPU como base, GPU opcional; licença que permita distribuir e usar como o AY usa.

### 5.2 Motor de execução

**llama.cpp** (licença MIT, `ggml-org/llama.cpp`): roda modelos GGUF em CPU (x64 com AVX/AVX2/AVX-512 escolhidos
em tempo de execução) e em GPU por Vulkan (AMD/Intel/NVIDIA) ou CUDA. O AY usará o `llama-server` como
**processo separado** ligado só a `127.0.0.1`, porta aleatória e chave local, iniciado e encerrado pelo AY.
Vantagens: não trava a interface, cancelamento real (encerrar a requisição/processo), memória liberada ao
desligar. A versão exata do binário será fixada e conferida por SHA-256 na entrega C.

### 5.3 Modelos candidatos

| Modelo | Licença (cartão oficial) | Tamanho | Observação |
|---|---|---|---|
| Qwen3-4B | Apache 2.0 | 4,0 B parâmetros; GGUF Q4 ≈ 2,5 GB | "100+ idiomas"; contexto 32K; modo sem raciocínio recomendado para edição |
| Qwen3.5 2B / 4B (mar/2026) | Apache 2.0 (segundo cobertura secundária; conferir o cartão oficial) | 2B / 4B | família mais nova; confirmar desempenho em pt-BR |
| Gemma 4 E2B / E4B | Apache 2.0 (cartão oficial) | 2,3 B / 4,5 B efetivos; contexto 128K | "140+ idiomas", feito para execução local |
| Phi-4-mini | MIT | 3,8 B | alternativa |
| Tucano 2 (0,5–3,7 B) | a confirmar | — | treinado para português; avaliar se a qualidade de edição compensa o tamanho |

Não foi encontrado comparativo confiável **em português** para modelos de 1–4 B em CPU (só leaderboards gerais
ou de português europeu). Por isso a escolha será feita com um **conjunto de testes do AY em pt-BR**:
correção, clareza, formalização, simplificação, resumo e sugestão de títulos; medindo preservação de números,
nomes, citações e referências, aderência ao formato de resposta, tempo até a primeira palavra, palavras por
segundo e memória no computador de referência (i5-8500, 16 GB, sem GPU dedicada). A recomendação padrão será um
modelo de ~2–4 B quantizado (Q4), com opção "leve" menor; o AY não promete o mesmo desempenho em todo computador.

### 5.4 Segurança contra instruções dentro do documento

- O texto do documento vai ao modelo **delimitado como dado**, com instrução fixa de só reescrever/analisar.
- O modelo **não tem ferramentas**: não executa comandos, não abre arquivos, não acessa a rede. O processo
  `llama-server` só escuta em `127.0.0.1`; o AY não oferece a ele nenhuma função externa.
- A resposta é tratada como **proposta de texto**: o AY mostra original × proposta, confere se números,
  citações entre aspas, referências e campos foram preservados, e só aplica com confirmação, como alteração
  controlada quando possível.

## 6. Formatação ABNT (entrega B) — como as regras serão registradas

Conferência das normas feita em 20/10/2026 no catálogo oficial da ABNT: edições, datas, fontes e o que não pôde
ser conferido estão em [NORMAS.md](NORMAS.md). Os textos completos das normas são **pagos e protegidos**: o AY
registra, para cada regra, a norma, a edição, a origem da informação e a data da verificação, e separa
**norma**, **instituição** e **preferência** (`dados/perfis_formatacao.json`).

Desenho (0.4.0):

- **Motor** `ay_academico.py` (sem interface, testado por UNO): *analisar* identifica as partes do documento
  (títulos com estilo ou com número digitado, títulos sem indicativo, citações já recuadas, referências,
  legendas e fontes de ilustrações e tabelas, início da parte textual); *planejar* lista o que vai mudar (de →
  para, regra, camada, origem); *aplicar* faz tudo numa única ação de desfazer; *conferir* gera o relatório de
  conformidade (conforme, não conforme, aviso, não verificável, não se aplica).
- **Estilos e campos reais:** página (A4, margens, cabeçalho com campo de número de página), estilos de parágrafo
  (corpo, títulos 1–5 com destaque gradativo, citação, nota, legenda, referência, títulos sem indicativo),
  numeração de capítulos do documento e sumário automático. A formatação direta que contraria a regra (fonte,
  tamanho, entrelinhas, recuo, alinhamento) é removida; negrito, itálico e sublinhado de trechos ficam.
- **O texto não muda:** nenhuma palavra é inserida, apagada ou trocada; títulos com número digitado mantêm o
  número (a numeração automática fica desligada nesses títulos); maiúsculas dos títulos são só de exibição.
  Exceção declarada: ao inserir o sumário automático, o AY cria um parágrafo vazio para ele.
- **Sempre numa cópia (decisão de 21/10/2026):** no motor, ligar o cabeçalho com o número de página apaga o
  histórico de desfazer inteiro, e isso não tem conserto pela API. Por isso a formatação só é feita numa cópia sem
  título (`copia_sem_titulo`, que inclui as alterações não salvas); o documento aberto, suas alterações não salvas e
  seu histórico não mudam, e `aplicar()` recusa um documento com histórico (`HistoricoEmRisco`). Na cópia, a
  formatação inteira é uma ação de desfazer e refazer.
- **Recomeço da contagem de páginas em estilo:** o recomeço posto direto no parágrafo se perde no Refazer (testado);
  posto num estilo de parágrafo ("… — recomeça em 1"), volta certo. Os filtros do Word só gravam o recomeço direto:
  ao salvar em DOCX/DOC/RTF, o AY copia o recomeço para o parágrafo com o desfazer travado, grava e desfaz a cópia
  (`recomecos_para_docx`); o histórico e o estado "modificado" ficam como deviam.
- **Modelo da instituição:** troca parâmetros (fonte, recuo, alinhamento, margens, destaques, ponto depois do
  indicativo) e registra o manual (título, edição, endereço ou arquivo). Quando a instituição diverge da norma, o
  relatório mostra as duas.
- **Galeria de modelos** `ay_modelos.py`: modelos montados pelo próprio AY em código (sem arquivos binários no
  repositório), com estilos reais e campos de preenchimento como **controles de conteúdo** (no DOCX viram o espaço
  reservado do Word; o campo "JumpEdit" do motor some ao salvar em DOCX, conferido por teste). "Salvar como modelo"
  grava um `.ott` na pasta de modelos do perfil. Modelo (aparência e estrutura) e formato do arquivo (ODT ou DOCX
  ao salvar) aparecem separados na galeria.
- **Achados do motor (testes de 20 e 21/10/2026):** ligar o cabeçalho ou mudar um estilo de página existente pela
  API apaga todo o histórico de desfazer; criar um estilo de página novo com as propriedades já definidas não apaga.
  Recomeçar a numeração com paridade trocada faz o motor inserir uma página em branco automática (não vai para o PDF
  padrão nem para a impressão só de frente; o DOCX guarda só o recomeço). O Refazer não restaura o recomeço direto no
  parágrafo nem o estilo-pai de um estilo criado (os valores postos no estilo antes de inseri-lo voltam). Atribuir um
  estilo que define alinhamento tira o alinhamento direto do parágrafo. Ao dividir um parágrafo, o objeto UNO antigo
  fica com a parte nova. Nas versões novas, `ListFormat` vale sobre prefixo e sufixo da numeração. O AY trata cada um
  (ver `ay_academico.py`); `tests/uno/academico.py` confere a sequência formatar → desfazer → refazer → salvar →
  reabrir → PDF → impressão.

## 7. Atualizações (entrega E) — como garantir a autenticidade

O AY só oferecerá instalar uma atualização que passe por **todas** as verificações:
1. manifesto de versões obtido por HTTPS do canal oficial (GitHub Releases do projeto);
2. manifesto **assinado** (Ed25519, formato minisign) com chave pública embutida no aplicativo;
3. SHA-256 do instalador igual ao do manifesto assinado (e Authenticode, quando houver certificado);
4. confirmação explícita, com documentos abertos salvos ou fechados antes.

Sem a chave de assinatura guardada com segurança pelo responsável, a instalação continua **manual** pelo site
(com SHA-256), e a consulta só informa que há versão nova.

## 8. Fontes consultadas

- Qwen3-4B, cartão oficial: <https://huggingface.co/Qwen/Qwen3-4B> (Apache 2.0, 4,0 B, contexto 32K).
- Gemma 4 E4B, cartão oficial: <https://huggingface.co/google/gemma-4-E4B> (Apache 2.0; E2B 2,3 B e E4B 4,5 B efetivos; 128K).
- Qwen3.5 modelos pequenos (cobertura secundária): <https://artificialanalysis.ai/articles/qwen3-5-small-models>, <https://gigazine.net/gsc_news/en/20260303-qwen-3-5-small>.
- Tucano 2 (português): <https://arxiv.org/abs/2603.03543>.
- Leaderboard de português europeu CLARIN-PT-LDB: <https://arxiv.org/html/2603.12872>.
- llama.cpp (MIT): <https://github.com/ggml-org/llama.cpp>.
- Lightproof pt-BR e VERO: arquivos `README_Lightproof_pt_BR.txt` e `README_pt_BR.txt` da extensão `dict-pt-BR` 3.3.0 distribuída com o motor.
