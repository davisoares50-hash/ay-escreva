<#
.SYNOPSIS
  Captura a janela principal do AY ESCREVA (processo soffice.bin) em PNG, para conferência visual.
.EXAMPLE
  powershell -File tests\captura_janela.ps1 -Saida tests\output\janela.png -Esperar 20
#>
param([string]$Saida = 'tests\output\janela.png', [int]$Esperar = 15, [string]$Titulo = 'AY ESCREVA')
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class Jan {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
'@
[void][Jan]::SetProcessDPIAware()
$fim = (Get-Date).AddSeconds($Esperar)
$p = $null
while ((Get-Date) -lt $fim) {
  $p = Get-Process soffice.bin -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$Titulo*" } | Select-Object -First 1
  if ($p) { break }
  Start-Sleep -Milliseconds 500
}
if (-not $p) { throw "Janela com título '*$Titulo*' não encontrada" }
Start-Sleep -Seconds 3
[void][Jan]::ShowWindow($p.MainWindowHandle, 3)   # maximizar
[void][Jan]::SetForegroundWindow($p.MainWindowHandle)
Start-Sleep -Seconds 2
$r = New-Object Jan+RECT
[void][Jan]::GetWindowRect($p.MainWindowHandle, [ref]$r)
$w = $r.R - $r.L; $h = $r.B - $r.T
$bmp = New-Object Drawing.Bitmap $w, $h
$g = [Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
New-Item -ItemType Directory -Force (Split-Path $Saida) | Out-Null
$bmp.Save((Join-Path (Resolve-Path (Split-Path $Saida)).Path (Split-Path $Saida -Leaf)), [Drawing.Imaging.ImageFormat]::Png)
"Título: $($p.MainWindowTitle)"
"Capturado: $Saida ($w x $h)"
