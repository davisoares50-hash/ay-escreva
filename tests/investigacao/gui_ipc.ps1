<#
.SYNOPSIS
  Investigação: usa o AY ESCREVA só pela interface (sem ponte UNO), como um usuário.
  Abre documentos pelo lançador (equivale a clicar duas vezes no Explorador) e fecha cada janela com
  WM_CLOSE (equivale ao X). Verifica se o motor continua vivo e se houve queda registrada no Windows.
#>
param([string]$App = 'E:\AY\dist\AY ESCREVA\AYEscreva.exe', [int]$Ciclos = 5, [string[]]$Arquivos)
$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $Arquivos) {
  $Arquivos = @((Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt'), (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.docx'), (Join-Path $Raiz 'tests\output\seguranca\com-macro.odt'), (Join-Path $Raiz 'tests\fixtures\compatibilidade-ooxml.docx'))
}
Add-Type @'
using System; using System.Text; using System.Collections.Generic; using System.Runtime.InteropServices;
public static class Jan2 {
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr p);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  public static List<KeyValuePair<IntPtr,string>> Janelas(uint pid) {
    var r = new List<KeyValuePair<IntPtr,string>>();
    EnumWindows((h, p) => { uint q; GetWindowThreadProcessId(h, out q);
      if (q == pid && IsWindowVisible(h)) { var sb = new StringBuilder(512); GetWindowText(h, sb, 512); if (sb.Length > 0) r.Add(new KeyValuePair<IntPtr,string>(h, sb.ToString())); }
      return true; }, IntPtr.Zero);
    return r;
  }
}
'@
function Motor { Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$(Split-Path $App)*" } | Select-Object -First 1 }
function Esperar-Janela([int]$procId, [string]$parte, [int]$seg = 60) {
  $fim = (Get-Date).AddSeconds($seg)
  while ((Get-Date) -lt $fim) {
    $j = [Jan2]::Janelas([uint32]$procId) | Where-Object { $_.Value -like "*$parte*" } | Select-Object -First 1
    if ($j) { return $j }
    Start-Sleep -Milliseconds 300
  }
  return $null
}
$inicio = Get-Date
# Documento âncora: fica aberto o tempo todo para que fechar as outras janelas não encerre o aplicativo
$ancora = Join-Path $env:TEMP 'ay-ancora.odt'
Copy-Item (Join-Path $Raiz 'tests\output\etapa1\teste-etapa1.odt') $ancora -Force
Start-Process $App -ArgumentList "`"$ancora`""
$fim = (Get-Date).AddSeconds(60); while (-not (Motor) -and (Get-Date) -lt $fim) { Start-Sleep -Milliseconds 300 }
$m = Motor
$base = Esperar-Janela $m.Id 'ay-ancora'
Write-Host "Motor PID $($m.Id); janela inicial: $($base.Value)"
$ok = 0
for ($i = 1; $i -le $Ciclos; $i++) {
  foreach ($arq in $Arquivos) {
    Remove-Item (Join-Path (Split-Path $arq) '.~lock.*') -Force -ErrorAction SilentlyContinue
    Start-Process $App -ArgumentList "`"$arq`""
    $j = Esperar-Janela $m.Id ([IO.Path]::GetFileName($arq))
    if (-not $j) { Write-Host "ciclo $i : janela de $([IO.Path]::GetFileName($arq)) não apareceu"; break }
    Start-Sleep -Milliseconds 1500
    [void][Jan2]::PostMessage($j.Key, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)   # WM_CLOSE
    $fimF = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $fimF -and ([Jan2]::Janelas([uint32]$m.Id) | Where-Object { $_.Key -eq $j.Key })) { Start-Sleep -Milliseconds 300 }
    if ($m.HasExited) { Write-Host "ciclo $i : MOTOR CAIU após $([IO.Path]::GetFileName($arq))"; break }
    $ok++
  }
  if ($m.HasExited) { break }
}
$vivo = -not $m.HasExited
$quedas = @(Get-WinEvent -FilterHashtable @{ LogName = 'Application'; ProviderName = 'Application Error'; StartTime = $inicio } -ErrorAction SilentlyContinue | Where-Object { $_.Message -like '*soffice*' })
Write-Host ("RESULTADO GUI: {0} aberturas/fechamentos; motor vivo={1}; quedas registradas={2}" -f $ok, $vivo, $quedas.Count)
if ($vivo) { foreach ($j in [Jan2]::Janelas([uint32]$m.Id)) { [void][Jan2]::PostMessage($j.Key, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) }; [void]$m.WaitForExit(30000) }
