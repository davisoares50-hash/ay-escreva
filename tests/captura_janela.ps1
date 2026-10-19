<#
.SYNOPSIS
  Captura a janela principal do AY ESCREVA (processo soffice.bin) em PNG, para conferência visual.
.DESCRIPTION
  Usa PrintWindow (a janela se desenha num bitmap), que funciona mesmo com a janela coberta e, em geral,
  com a estação bloqueada. Se o resultado vier vazio, recorre à cópia da tela.
.EXAMPLE
  powershell -File tests\captura_janela.ps1 -Saida tests\output\janela.png -Esperar 20
#>
param([string]$Saida = 'tests\output\janela.png', [int]$Esperar = 15, [string]$Titulo = 'AY ESCREVA', [int]$Largura = 1600, [int]$Altura = 1000)
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class Jan {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int a, bool r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
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
$h = $p.MainWindowHandle
[void][Jan]::ShowWindow($h, 9)                    # restaurar (não maximizado), tamanho previsível
[void][Jan]::MoveWindow($h, 0, 0, $Largura, $Altura, $true)
Start-Sleep -Seconds 4
$r = New-Object Jan+RECT
[void][Jan]::GetWindowRect($h, [ref]$r)
$w = $r.R - $r.L; $a = $r.B - $r.T
$bmp = New-Object Drawing.Bitmap $w, $a
$g = [Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
$ok = [Jan]::PrintWindow($h, $hdc, 2)             # PW_RENDERFULLCONTENT
$g.ReleaseHdc($hdc)
# Bitmap todo de uma cor só = captura falhou; tenta a cópia da tela
$c0 = $bmp.GetPixel([int]($w / 2), [int]($a / 3)); $c1 = $bmp.GetPixel([int]($w / 3), [int]($a / 2))
if (-not $ok -or ($c0 -eq $c1 -and $c0.ToArgb() -eq $bmp.GetPixel(5, 5).ToArgb())) {
  [void][Jan]::SetForegroundWindow($h); Start-Sleep -Seconds 1
  $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
  $metodo = 'tela'
} else { $metodo = 'PrintWindow' }
New-Item -ItemType Directory -Force (Split-Path $Saida) | Out-Null
$bmp.Save((Join-Path (Resolve-Path (Split-Path $Saida)).Path (Split-Path $Saida -Leaf)), [Drawing.Imaging.ImageFormat]::Png)
"Título: $($p.MainWindowTitle)"
"Capturado ($metodo): $Saida ($w x $a)"
