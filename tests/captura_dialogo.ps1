<#
.SYNOPSIS
  Captura em PNG uma janela do AY ESCREVA cujo título contém o texto indicado (PrintWindow), para conferência visual.
.EXAMPLE
  powershell -File tests\captura_dialogo.ps1 -Titulo 'Formatar trabalho' -Saida tests\output\interface\formatar.png
#>
param([Parameter(Mandatory)][string]$Titulo, [Parameter(Mandatory)][string]$Saida, [int]$Esperar = 10)
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class Dlg {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr p);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  public static List<string> Titulos = new List<string>();
  public static IntPtr Achar(string parte) {
    IntPtr achado = IntPtr.Zero;
    Titulos.Clear();
    EnumWindows(delegate (IntPtr h, IntPtr p) {
      if (!IsWindowVisible(h)) return true;
      var sb = new StringBuilder(512);
      GetWindowTextW(h, sb, 512);
      string t = sb.ToString();
      if (t.Length > 0) Titulos.Add(t);
      if (achado == IntPtr.Zero && t.IndexOf(parte, StringComparison.OrdinalIgnoreCase) >= 0) achado = h;
      return true;
    }, IntPtr.Zero);
    return achado;
  }
}
'@
[void][Dlg]::SetProcessDPIAware()
$fim = (Get-Date).AddSeconds($Esperar)
$h = [IntPtr]::Zero
while ((Get-Date) -lt $fim -and $h -eq [IntPtr]::Zero) {
  $h = [Dlg]::Achar($Titulo)
  if ($h -eq [IntPtr]::Zero) { Start-Sleep -Milliseconds 300 }
}
if ($h -eq [IntPtr]::Zero) { throw ("Janela com '$Titulo' no título não encontrada. Visíveis: " + ([Dlg]::Titulos -join ' | ')) }
Start-Sleep -Milliseconds 800
$r = New-Object Dlg+RECT
[void][Dlg]::GetWindowRect($h, [ref]$r)
$w = $r.R - $r.L; $a = $r.B - $r.T
$bmp = New-Object System.Drawing.Bitmap $w, $a
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
[void][Dlg]::PrintWindow($h, $hdc, 2)
$g.ReleaseHdc($hdc)
$g.Dispose()
New-Item -ItemType Directory -Force (Split-Path $Saida) | Out-Null
$bmp.Save($Saida, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
"Captura: $Saida ($w x $a)"
