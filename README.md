# AY ESCREVA

Editor de textos gratuito, instalável e em português do Brasil, com experiência próxima à do Microsoft Word e
identidade própria. Sem mensalidade, sem conta, offline e com documentos locais.

**Estado:** 0.2.0, **versão inicial de testes para Windows 11 x64** (o único sistema validado). Windows 10,
macOS e Linux estão em desenvolvimento. Veja [docs/PLANO.md](docs/PLANO.md).

## Arquitetura em uma frase

O AY ESCREVA é uma **versão derivada do LibreOffice**. Usa o motor do Writer (paginação, DOCX/ODT/DOC/RTF,
tabelas, notas, controle de alterações, impressão, PDF, acessibilidade) a partir dos binários oficiais
assinados, e põe por cima a camada própria: nome, identidade visual, perfil isolado, políticas de segurança,
pt-BR, faixa de opções própria, extensão com avisos de perdas e de fontes, lançador e instalador. A compilação
do motor a partir do código-fonte (Nível 2) fica para quando forem necessárias mudanças em C++. Justificativa e
comparação com as alternativas em [docs/ARQUITETURA.md](docs/ARQUITETURA.md).

## Instalar e testar (Windows 11 x64)

1. Rode `out\instalador\AYEscreva-0.2.0-teste-windows11-x64.exe` (por usuário, sem administrador). Como o
   instalador ainda não tem assinatura digital, o SmartScreen pode mostrar "O Windows protegeu o computador":
   confira o SHA-256 (`Get-FileHash <arquivo> -Algorithm SHA256`, comparar com o `.sha256` ao lado) e use
   "Mais informações › Executar assim mesmo".
2. Abra pelo menu Iniciar: **AY ESCREVA**.
3. Teste: escreva, use as abas (Página Inicial, Inserir, Layout…), insira uma tabela e uma imagem, salve em ODT
   (padrão), salve como DOCX (aparece o aviso de possíveis perdas), feche, reabra, exporte PDF (Arquivo).
   Ajuda › Guia, Atalhos e Limitações conhecidas funcionam sem internet.
4. Desinstale em Configurações › Aplicativos (o perfil `%APPDATA%\AYEscreva` é mantido).

## Montar a partir do código (Windows 10/11 x64)

```powershell
cd tools; npm ci; cd ..
powershell -ExecutionPolicy Bypass -File scripts\montar.ps1       # monta dist\AY ESCREVA (≈15 min)
powershell -ExecutionPolicy Bypass -File scripts\testar.ps1       # testes automatizados (≈4 min; -ComInterface: + faixa)
powershell -ExecutionPolicy Bypass -File scripts\instalador.ps1   # out\instalador\AYEscreva-<versão>-teste-windows11-x64.exe
& "dist\AY ESCREVA\AYEscreva.exe"
```

Detalhes, requisitos, instalador e compilação do motor: [docs/COMPILACAO.md](docs/COMPILACAO.md).
Site oficial e publicação de versões: [docs/SITE.md](docs/SITE.md).

## Resultados atuais

| Teste | Resultado |
|---|---|
| Aceite (várias páginas, formatação, tabela, imagem, salvar/fechar/reabrir ODT e DOCX, PDF e PDF/UA) | 40/40 |
| Instalador: instalar, abrir, usar com o motor instalado, desinstalar, perfil do LibreOffice intacto | 18/18 |
| Faixa de opções testada pela interface (de dentro do aplicativo; 11 abas + Tabela e Imagem) | 210/210 botões presentes; 148 acionados; 40/40 efeitos conferidos; 0 quedas |
| Avisos de perdas ao salvar em DOCX (botão e "fechar → Salvar") e de fontes substituídas | validados pela interface |
| Impressão real pela fila do Windows (impressora virtual) | 4/4 |
| Segurança (macro não executa, com controle positivo; imagem remota não é baixada) | 4/4 |
| Comandos das 11 abas + 4 contextuais encontrados no motor | 233/233 (+6 funções pendentes, fora da faixa) |
| Ida e volta com documento OOXML representativo + variantes DOCX/DOC/RTF/ODT do Word | sem perda de texto; 7 incompatibilidades documentadas |
| Site: acessar → baixar → conferir SHA-256 → instalar → abrir (prévia local) | 21/22 (falta só HTTPS, que vale para o site publicado) |

Relatório completo, inclusive o que **não** foi validado (leitores de tela, outros sistemas, assinatura de
código): [docs/RESULTADOS-TESTES.md](docs/RESULTADOS-TESTES.md).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `base/` | versão fixada do motor (URLs, SHA-256, chave PGP) |
| `layer/` | arquivos sobrepostos à base (`share/registry/ayescreva.xcd`) |
| `launcher/` | lançador `AYEscreva.exe` (C#) |
| `ui/abas.json` | fonte única das abas, comandos, prioridades e critérios de aceite |
| `extensao/ayescreva/` | extensão AY: comandos `ayescreva:`, avisos de perdas e de fontes, ajuda offline |
| `site/` | site oficial (páginas, estilo, versões) |
| `tools/` | geração da faixa, do site, da identidade visual e dos atalhos; comparação visual de PDFs |
| `scripts/` | `montar.ps1`, `testar.ps1`, `instalador.ps1`, `publicar-site.ps1` |
| `tests/` | testes UNO, testes pela interface, instalação, fluxo do site, investigação, oráculo Word |
| `installer/` | script do Inno Setup e licença exibida no instalador |
| `docs/` | arquitetura, matriz, plano, compilação, resultados, site, licenças |
| `_cache/`, `dist/`, `out/`, `tests/output/` | gerados (fora do controle de versão) |

## Licença

Código do projeto: MPL-2.0. O motor (LibreOffice) é distribuído sem alterações sob as licenças dele.
"LibreOffice" é marca da The Document Foundation; o AY ESCREVA é um projeto independente.
Veja [docs/LICENCAS.md](docs/LICENCAS.md).
