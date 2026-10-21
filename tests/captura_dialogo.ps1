<#
.SYNOPSIS
  Captura em PNG uma janela de diálogo do AY ESCREVA pelo título exato (PrintWindow), para conferência visual.
.EXAMPLE
  powershell -File tests\captura_dialogo.ps1 -Titulo 'Formatar trabalho acadêmico' -Saida tests\output\interface\formatar.png
#>
param([Parameter(Mandatory)][string]$Titulo, [Parameter(Mandatory)][string]$Saida, [int]$Esperar = 10)
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class Dlg {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr FindWindowW(string cls, string titulo);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
'@
[void][Dlg]::SetProcessDPIAware()
$fim = (Get-Date).AddSeconds($Esperar)
$h = [IntPtr]::Zero
while ((Get-Date) -lt $fim -and $h -eq [IntPtr]::Zero) {
  $h = [Dlg]::FindWindowW($null, $Titulo)
  if ($h -eq [IntPtr]::Zero) { Start-Sleep -Milliseconds 300 }
}
if ($h -eq [IntPtr]::Zero) { throw "Janela '$Titulo' não encontrada" }
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
