<#
.SYNOPSIS
  Mede o que a recuperação de documentos devolve depois de uma queda do motor, com o AY aberto como uma pessoa abre
  (sem --norestore, que os outros testes usam).
.DESCRIPTION
  Num perfil descartável, abre um ODT, digita um texto sem salvar e provoca a queda conhecida do motor (diálogo de Link
  fechado pelo robô de teclas do motor; ver docs/RESULTADOS-TESTES.md §9). Depois, faz o que uma pessoa faria:
  responde com Enter (tecla real do Windows) às janelas "Recuperação de documentos" — a de salvamento de emergência,
  no processo que caiu, e a de recuperação, quando o motor reinicia — e confere, no documento reaberto, se o texto
  voltou. Repete -Vezes vezes. O resultado vai para tests\output\interface\recuperacao.json.
  As teclas reais só são enviadas quando a janela em primeiro plano é do AY.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tests\interface\testar_recuperacao.ps1 -Vezes 3
#>
param([string]$Dist = 'E:\AY\dist\AY ESCREVA', [int]$Vezes = 3, [int]$Limite = 240, [switch]$EsperarAutoSalvamento)
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Saida = Join-Path $Raiz 'tests\output\interface'
$Trab = Join-Path $Saida 'trabalho-recuperacao'
New-Item -ItemType Directory -Force $Saida, $Trab | Out-Null
# Extensão de testes empacotada (a mesma de testar_faixa.ps1)
$oxt = Join-Path $Raiz 'out\ay-testes-ui.oxt'
if (Test-Path $oxt) { Remove-Item $oxt }
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$origem = Join-Path $PSScriptRoot 'extensao_testes'
$zip = [IO.Compression.ZipFile]::Open($oxt, 'Create')
try {
  foreach ($arq in Get-ChildItem $origem -Recurse -File) {
    [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $arq.FullName, ($arq.FullName.Substring($origem.Length + 1) -replace '\\', '/'))
  }
} finally { $zip.Dispose() }

Add-Type -TypeDefinition @'
using System; using System.Collections.Generic; using System.Runtime.InteropServices; using System.Text;
public static class JanelasAY {
  delegate bool Proc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(Proc f, IntPtr l);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  [DllImport("user32.dll")] static extern bool AttachThreadInput(uint a, uint b, bool f);
  [DllImport("user32.dll")] static extern bool BringWindowToTop(IntPtr h);
  [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
  public static List<string> Titulos(uint[] pids) {
    var r = new List<string>();
    EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p);
      if (Array.IndexOf(pids, p) >= 0 && IsWindowVisible(h)) { var s = new StringBuilder(300); GetWindowText(h, s, 300); if (s.Length > 0) r.Add(s.ToString()); }
      return true; }, IntPtr.Zero);
    return r;
  }
  // Põe a janela de título indicado em primeiro plano e pressiona Enter, só se ela ficou de fato em primeiro plano
  public static bool Enter(uint[] pids, string inicio) {
    IntPtr alvo = IntPtr.Zero;
    EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p);
      if (Array.IndexOf(pids, p) >= 0 && IsWindowVisible(h)) { var s = new StringBuilder(300); GetWindowText(h, s, 300);
        if (s.ToString().StartsWith(inicio)) { alvo = h; return false; } }
      return true; }, IntPtr.Zero);
    if (alvo == IntPtr.Zero) return false;
    // o Windows só deixa trocar a janela em primeiro plano a quem está ligado à fila de entrada da janela atual
    uint pf; uint tf = GetWindowThreadProcessId(GetForegroundWindow(), out pf); uint eu = GetCurrentThreadId();
    AttachThreadInput(eu, tf, true);
    try { SetForegroundWindow(alvo); BringWindowToTop(alvo); } finally { AttachThreadInput(eu, tf, false); }
    System.Threading.Thread.Sleep(400);
    if (GetForegroundWindow() != alvo) return false;
    keybd_event(0x0D, 0, 0, UIntPtr.Zero); keybd_event(0x0D, 0, 2, UIntPtr.Zero);
    return true;
  }
}
'@

$rodadas = @()
for ($n = 1; $n -le $Vezes; $n++) {
  $perfil = Join-Path $env:TEMP ("ay-recuperacao-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
  New-Item -ItemType Directory -Force (Join-Path $perfil 'user') | Out-Null
  @'
<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.Common/Misc"><prop oor:name="UseSystemFileDialog" oor:op="fuse"><value>false</value></prop></item>
<item oor:path="/org.openoffice.Setup/Office"><prop oor:name="ooSetupInstCompleted" oor:op="fuse"><value>true</value></prop></item>
</oor:items>
'@ | Set-Content -Encoding UTF8 (Join-Path $perfil 'user\registrymodifications.xcu')
  $url = 'file:///' + ($perfil -replace '\\', '/')
  & (Join-Path $Dist 'program\unopkg.com') add --suppress-license "-env:UserInstallation=$url" $oxt
  $doc = Join-Path $Trab "recuperacao-$n.odt"
  # trava deixada por uma rodada anterior que caiu ("Documento em uso" ao abrir)
  Get-ChildItem $Trab -Force -Filter '.~lock.*' | Remove-Item -Force
  Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') $doc -Force
  $resultado = Join-Path $Trab "resultado-$n.json"
  Remove-Item $resultado -ErrorAction SilentlyContinue
  $spec = Join-Path $Trab "spec-$n.json"
  [ordered]@{ abas = (Join-Path $Raiz 'ui\abas.json'); mapa = (Join-Path $Raiz 'out\faixa\mapa.json'); saida = $resultado
              imagem = (Join-Path $Raiz 'out\marca\icone-64.png'); somente = @('queda_recuperacao')
              esperar_autosalvamento = [bool]$EsperarAutoSalvamento } | ConvertTo-Json | Set-Content -Encoding UTF8 $spec
  Remove-Item "$resultado.primeira" -ErrorAction SilentlyContinue
  $env:AY_TESTE_UI_SPEC = $spec
  $inicio = Get-Date
  $eventos = New-Object System.Collections.Generic.List[string]
  Start-Process (Join-Path $Dist 'program\soffice.exe') -ArgumentList "-env:UserInstallation=$url", '--nologo', "`"$doc`"" | Out-Null
  $fim = (Get-Date).AddSeconds($Limite + $(if ($EsperarAutoSalvamento) { 480 } else { 0 })); $vistos = @{}; $enter = 0; $ultimoEnter = Get-Date '2000-01-01'
  $semProcesso = $null; $reaberto = $false
  while ((Get-Date) -lt $fim -and -not (Test-Path $resultado)) {
    Start-Sleep -Milliseconds 700
    $pids = [uint32[]]@(Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -ge $inicio.AddSeconds(-2) } | ForEach-Object Id)
    if (-not $pids.Count) {
      # o motor caiu e não reiniciou sozinho: a pessoa abre o AY de novo (sem o documento; só a recuperação pode trazê-lo)
      if (-not $semProcesso) { $semProcesso = Get-Date }
      if (-not $reaberto -and ((Get-Date) - $semProcesso).TotalSeconds -gt 15 -and (Test-Path "$resultado.primeira")) {
        $reaberto = $true; $eventos.Add("$((Get-Date).ToString('HH:mm:ss')) o motor não reiniciou; AY aberto de novo pela pessoa")
        Start-Process (Join-Path $Dist 'program\soffice.exe') -ArgumentList "-env:UserInstallation=$url", '--nologo' | Out-Null
        $fim = (Get-Date).AddSeconds(120)
      }
      continue
    }
    $semProcesso = $null
    foreach ($t in [JanelasAY]::Titulos($pids)) { if (-not $vistos[$t]) { $vistos[$t] = $true; $eventos.Add("$((Get-Date).ToString('HH:mm:ss')) janela: $t") } }
    if (((Get-Date) - $ultimoEnter).TotalSeconds -gt 3 -and [JanelasAY]::Enter($pids, 'Recupera')) {
      $enter++; $ultimoEnter = Get-Date; $eventos.Add("$((Get-Date).ToString('HH:mm:ss')) Enter (tecla real) na janela de recuperação")
      $vistos = @{}
    }
  }
  Start-Sleep -Seconds 5
  Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -ge $inicio.AddSeconds(-2) } | ForEach-Object { if (-not $_.WaitForExit(20000)) { $_.Kill() } }
  Remove-Item Env:\AY_TESTE_UI_SPEC
  $r = if (Test-Path $resultado) { Get-Content $resultado -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }
  $rec = @($r.efeitos | Where-Object { $_.funcao -like 'Recupera*' })
  $semQueda = @($r.efeitos | Where-Object { $_.funcao -like 'Queda provocada*' })
  $situacao = if ($rec.Count -and $rec[0].ok) { 'recuperado' } elseif ($semQueda.Count) { 'sem queda' } else { 'não recuperado' }
  if ($reaberto) { $situacao += ' (depois de abrir o AY de novo)' }
  $rodadas += [ordered]@{ rodada = $n; situacao = $situacao; enter = $enter; reaberto = $reaberto; copia_automatica_s = $r.copia_automatica_s
                          eventos = $eventos.ToArray(); detalhe = $(if ($rec.Count) { $rec[0].detalhe } else { '' }) }
  Write-Host "rodada ${n}: $situacao (Enter: $enter) $(if ($rec.Count) { $rec[0].detalhe })"
  $eventos | ForEach-Object { Write-Host "   $_" }
  Remove-Item -Recurse -Force $perfil -ErrorAction SilentlyContinue
}
$nome = if ($EsperarAutoSalvamento) { 'recuperacao-com-copia-automatica.json' } else { 'recuperacao.json' }
[ordered]@{ data = (Get-Date).ToString('s'); intervalo_min = 3; esperar_copia_automatica = [bool]$EsperarAutoSalvamento; rodadas = $rodadas } | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Saida $nome)
