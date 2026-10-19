# AY ESCREVA

Editor de textos gratuito, instalável e em português do Brasil, com experiência próxima à do Microsoft Word e
identidade própria. Sem mensalidade, sem conta, offline e com documentos locais.

**Estado:** Etapa 1 concluída e validada no Windows 11 x64; Etapa 2 em andamento. Veja [docs/PLANO.md](docs/PLANO.md).

## Arquitetura em uma frase

O AY ESCREVA é uma **versão derivada do LibreOffice**. Usa o motor do Writer (paginação, DOCX/ODT/DOC/RTF,
tabelas, notas, controle de alterações, impressão, PDF, acessibilidade) a partir dos binários oficiais
assinados, e põe por cima a camada própria: nome, identidade visual, perfil isolado, políticas de segurança,
pt-BR, interface por abas, lançador e instalador. A compilação do motor a partir do código-fonte (Nível 2)
fica para quando forem necessárias mudanças em C++. Justificativa e comparação com as alternativas em
[docs/ARQUITETURA.md](docs/ARQUITETURA.md).

## Uso rápido (Windows 10/11 x64)

```powershell
cd tools; npm ci; cd ..
powershell -ExecutionPolicy Bypass -File scripts\montar.ps1     # monta dist\AY ESCREVA (≈15 min na 1ª vez)
powershell -ExecutionPolicy Bypass -File scripts\testar.ps1     # testes automatizados (≈2 min)
& "dist\AY ESCREVA\AYEscreva.exe"
```

Detalhes, requisitos, instalador e compilação do motor: [docs/COMPILACAO.md](docs/COMPILACAO.md).

## Resultados atuais

| Teste | Resultado |
|---|---|
| Aceite da Etapa 1 (várias páginas, formatação, tabela, imagem, salvar/fechar/reabrir ODT e DOCX, PDF e PDF/UA) | 40/40 |
| Impressão real pela fila do Windows (impressora virtual) | 4/4 |
| Segurança (macro não executa, com controle positivo; imagem remota não é baixada) | 4/4 |
| Comandos das 11 abas + 3 contextuais encontrados no motor | 219/219 (+11 lacunas mapeadas) |
| Ida e volta com documento OOXML representativo + variantes DOCX/DOC/RTF/ODT do Word | sem perda de texto; 7 incompatibilidades documentadas |

Relatório completo, inclusive o que **não** foi validado: [docs/RESULTADOS-TESTES.md](docs/RESULTADOS-TESTES.md).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `base/` | versão fixada do motor (URLs, SHA-256, chave PGP) |
| `layer/` | arquivos sobrepostos à base (`share/registry/ayescreva.xcd`) |
| `launcher/` | lançador `AYEscreva.exe` (C#) |
| `ui/abas.json` | fonte única das abas, comandos, prioridades e critérios de aceite |
| `tools/` | geração da identidade visual, busca de configuração, comparação visual de PDFs |
| `scripts/` | `montar.ps1`, `testar.ps1`, `instalador.ps1` |
| `tests/` | testes UNO (Python do próprio motor), gerador de DOCX representativo, oráculo Word, captura de tela |
| `installer/` | script do Inno Setup e licença exibida no instalador |
| `docs/` | arquitetura, matriz, plano, compilação, resultados, licenças |
| `_cache/`, `dist/`, `out/`, `tests/output/` | gerados (fora do controle de versão) |

## Licença

Código do projeto: MPL-2.0. O motor (LibreOffice) é distribuído sem alterações sob as licenças dele.
"LibreOffice" é marca da The Document Foundation; o AY ESCREVA é um projeto independente.
Veja [docs/LICENCAS.md](docs/LICENCAS.md).
