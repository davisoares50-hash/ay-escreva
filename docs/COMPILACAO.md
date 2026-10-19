# Compilação, testes e instaladores

## Nível 1 — distribuição derivada (o que está em uso)

### Requisitos (Windows 10/11 x64)

| Item | Versão usada nesta máquina | Observação |
|---|---|---|
| Windows PowerShell | 5.1 | já vem no Windows |
| curl.exe, msiexec, robocopy | do Windows | já vêm no Windows |
| .NET Framework | 4.8.1 (`csc.exe` em `%WINDIR%\Microsoft.NET\Framework64\v4.0.30319`) | compila o lançador; já vem no Windows 10/11 |
| Node.js | 24.18.0 | ícones/marca e comparação visual de PDFs (`tools/`) |
| Git para Windows | 2.53 | opcional: o `gpg` dele confere a assinatura PGP da base |
| Espaço em disco | ~3 GB na unidade do projeto | download 380 MB + base extraída 1,5 GB + distribuição 0,8 GB |
| Inno Setup | 6.7.3, por usuário (`winget install --id JRSoftware.InnoSetup -e --scope user`) | só para gerar o instalador; licença gratuita, inclusive para uso comercial |
| Microsoft Word | 16.0 | **opcional**, só como oráculo nos testes; o produto não depende dele |

### Passo a passo

```powershell
cd E:\AY\tools
npm ci
cd ..
powershell -ExecutionPolicy Bypass -File scripts\montar.ps1      # baixa, confere, extrai, aplica a camada AY, compila o lançador
powershell -ExecutionPolicy Bypass -File scripts\testar.ps1      # bateria completa (resultados em tests\output)
& "dist\AY ESCREVA\AYEscreva.exe"                                # abre o editor
powershell -ExecutionPolicy Bypass -File scripts\instalador.ps1  # requer Inno Setup 6; -Portatil também gera .zip
```

Opcional: `scripts\testar.ps1 -ComInterface` acrescenta os testes pela faixa de opções (≈25 min).

### Instalador e teste de instalação

`scripts\instalador.ps1` gera `out\instalador\AYEscreva-<versão>-teste-windows11-x64.exe` e o `.sha256` ao lado
(a versão vem de `launcher/AYEscreva.cs`; `-Canal` muda o rótulo "teste"). O instalador é por usuário, sem
administrador, exige Windows 11 (`MinVersion=10.0.22000`) e se identifica como versão inicial de testes.

```powershell
powershell -ExecutionPolicy Bypass -File tests\instalacao\testar_instalacao.ps1 -Instalador out\instalador\AYEscreva-0.2.0-teste-windows11-x64.exe
```

O teste instala em silêncio, confere arquivos, atalho, registro e "Abrir com", abre pela interface, roda o aceite
com o motor instalado, desinstala e compara antes × depois o perfil, o registro e as associações de outras
instalações do LibreOffice. O perfil `%APPDATA%\AYEscreva` é preservado de propósito na desinstalação.

Tempos medidos nesta máquina: `montar.ps1` ≈ 15 min na primeira vez (a cópia de ~20 mil arquivos é lenta com
antivírus ativo); `testar.ps1` ≈ 2 min.

`montar.ps1` é idempotente: reaproveita o download e a extração em `_cache\` e recria `dist\AY ESCREVA\`
do zero a cada execução. Nada é instalado no sistema (a extração do MSI é administrativa: `msiexec /a`).

### Trocar a versão da base

1. Edite `base/base.lock.json`: `versao`, `versaoCompleta`, `buildid`, URLs e `sha256` dos dois MSI
   (pegue o hash depois de conferir a assinatura `.asc` com a chave `C2839ECAD9408FBE9531C3E9F434A1EFAFEEAEA3`).
2. Rode `montar.ps1` e `testar.ps1`. Se `comandos.py` acusar comando sumido ou renomeado, ajuste `ui/abas.json`.
3. Confira as chaves usadas em `layer/share/registry/ayescreva.xcd` com `node tools/xcd-busca.mjs main.xcd <Nome>`.

### Assinatura de código

O instalador e o `AYEscreva.exe` saem **sem assinatura**; o Windows SmartScreen mostrará aviso de editor
desconhecido. Os binários do motor continuam assinados pela The Document Foundation. Para assinar:
certificado de assinatura de código (OV/EV, ou um programa para projetos livres como o SignPath Foundation),
`signtool sign /fd sha256 /tr <servidor-de-carimbo> /td sha256 <arquivo>` no lançador e, no Inno Setup,
a diretiva `SignTool` (já prevista, comentada, em `installer/ayescreva.iss`).

## Nível 2 — compilar o motor do código-fonte

Ainda **não executado** neste ambiente: não há Visual Studio instalado e a unidade C: tem só ~4,5 GB livres.
O Visual Studio e o SDK do Windows instalam vários GB em C: mesmo quando o código fica em outra unidade.

Procedimento oficial atual ([wiki da TDF](https://wiki.documentfoundation.org/Development/BuildingOnWindows)):

```bat
:: Git Bash
git clone --config protocol.version=2 --config core.autocrlf=false https://git.libreoffice.org/core lo/libo-core
cd lo/libo-core && git checkout -b ay-26.8 libreoffice-26.8.1.1

:: Prompt de comando como administrador (Visual Studio 2022/2026, WSL, Java e dependências)
winget configure -f lo/libo-core/.config/configuration.winget
winget configure -f lo/libo-core/.config/admin_java_and_deps.winget
:: Prompt de comando como usuário normal (Ubuntu no WSL como auxiliar e autogen.input inicial)
winget configure -f lo/libo-core/.config/user_steps.winget
```

`autogen.input` do AY (todas as opções conferidas no `configure.ac` da branch `libreoffice-26-8`):

```
--with-product-name=AY ESCREVA
--with-vendor=Projeto AY ESCREVA
--with-branding=/caminho/para/E/AY/out/marca
--with-lang=pt-BR
--with-myspell-dicts
--with-help=html
--with-visual-studio=2022
--enable-release-build
--disable-cve-tests
```

```bash
# Git Bash, fora do WSL
cd lo/libo-core
./g -z
wsl ./autogen.sh
make
make check        # opcional, longo
instdir/program/soffice --writer
```

Estimativa (não medida aqui): 30–50 GB de disco para código e compilação, e várias horas na primeira
compilação em um processador de 6 núcleos como o desta máquina. O MSI próprio sai do módulo `instsetoo_native`;
o `UpgradeCode` e os nomes do produto ficam em `instsetoo_native/util/openoffice.lst`.

Manutenção do fork: `git rebase` da branch `ay-26.8` sobre cada nova tag `libreoffice-26.8.x.y` (correções) e
migração para `libreoffice-27.2.x` na próxima versão principal; rodar `scripts/testar.ps1` sobre o resultado.

## Outras plataformas

| Plataforma | Pacote oficial da base 26.8.1 | Situação no AY |
|---|---|---|
| Windows 10/11 x64 | MSI x86-64 | **montado e testado (Windows 11)**; Windows 10 não testado |
| Windows 11 ARM64 | MSI aarch64 | não montado: exige entrada própria em `base.lock.json`, o runtime VC++ ARM64 e teste em hardware ARM; o lançador (MSIL) roda no .NET Framework 4.8.1 ARM64 |
| Windows x86 (32 bits) | MSI x86, **descontinuado** desde a 25.8 | não recomendado: tende a ser removido pela base |
| Windows 7/8/8.1 | sem suporte desde a 25.8 (última base: 25.2, sem correções de segurança) | **não suportado**; uma versão "legada" sobre a 25.2 exporia usuários a falhas conhecidas |
| macOS (Intel e Apple Silicon) | DMG x86_64 e aarch64 | não montado. Mesma camada (`share/registry/*.xcd`, imagens de marca) dentro do `.app`; renomear o pacote invalida a assinatura da TDF, então exige assinatura e notarização próprias (conta de desenvolvedor Apple) |
| Linux x86_64/aarch64 | DEB e RPM | não montado. Caminho previsto: AppImage ou Flatpak com a mesma camada; pacotes .deb/.rpm próprios no Nível 2 |
