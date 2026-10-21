<#
  Leitor de tela disponível no Windows (Narrador) e o que ele recebe do AY.

  -Acao iniciar : liga o Narrador (ele fala; o teste desliga no fim).
  -Acao ler     : lê pela interface de acessibilidade MSAA — a que o motor expõe aos leitores de tela (com
                  IAccessible2) — as janelas do AY (processo soffice.bin) cujo título contém -Titulo, e grava em -Saida
                  o nome, o papel, se recebe foco pelo teclado, se está ativo e se está visível de cada elemento.
  -Acao parar   : desliga o Narrador pelo atalho do Windows (Ctrl + Windows + Enter).
  SPDX-License-Identifier: MPL-2.0
#>
param([ValidateSet('iniciar', 'ler', 'parar')][string]$Acao, [string]$Saida, [string]$Titulo, [int]$Profundidade = 16)
$ErrorActionPreference = 'Stop'
switch ($Acao) {
  'iniciar' {
    if (-not (Get-Process Narrator -ErrorAction SilentlyContinue)) { Start-Process "$env:WINDIR\System32\Narrator.exe" }
    Start-Sleep -Seconds 8
    "Narrador: $([bool](Get-Process Narrator -ErrorAction SilentlyContinue))"
  }
  'parar' {
    # o Narrador roda com privilégio elevado (não aceita ser encerrado por outro programa): desliga pelo mesmo atalho
    # que a pessoa usa, Ctrl + Windows + Enter
    if (Get-Process Narrator -ErrorAction SilentlyContinue) {
      Add-Type -Namespace AY -Name Teclado -MemberDefinition '[DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, System.UIntPtr dwExtraInfo);'
      foreach ($t in 0x11, 0x5B, 0x0D) { [AY.Teclado]::keybd_event($t, 0, 0, [UIntPtr]::Zero) }
      Start-Sleep -Milliseconds 150
      foreach ($t in 0x0D, 0x5B, 0x11) { [AY.Teclado]::keybd_event($t, 0, 2, [UIntPtr]::Zero) }
      Start-Sleep -Seconds 4
    }
    "Narrador ativo: $([bool](Get-Process Narrator -ErrorAction SilentlyContinue))"
  }
  'ler' {
    Add-Type -Path (Join-Path $PSScriptRoot 'Msaa.cs') -ReferencedAssemblies Accessibility
    Add-Type -Namespace AY -Name Janelas -MemberDefinition @'
public delegate bool Visitar(System.IntPtr h, System.IntPtr p);
[DllImport("user32.dll")] public static extern bool EnumWindows(Visitar f, System.IntPtr p);
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(System.IntPtr h, out uint pid);
[DllImport("user32.dll")] public static extern bool IsWindowVisible(System.IntPtr h);
[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(System.IntPtr h, System.Text.StringBuilder s, int n);
'@
    $pids = @(Get-Process soffice.bin -ErrorAction SilentlyContinue | ForEach-Object Id)
    $achadas = New-Object System.Collections.ArrayList
    [void][AY.Janelas]::EnumWindows({ param($h, $p)
        $id = 0; [void][AY.Janelas]::GetWindowThreadProcessId($h, [ref]$id)
        if ($pids -contains $id -and [AY.Janelas]::IsWindowVisible($h)) {
          $sb = New-Object System.Text.StringBuilder 512; [void][AY.Janelas]::GetWindowText($h, $sb, 512)
          if ($sb.Length -and (-not $Titulo -or $sb.ToString() -like "*$Titulo*")) { [void]$achadas.Add(@($h, $sb.ToString())) }
        }
        $true }, [IntPtr]::Zero)
    $itens = New-Object System.Collections.ArrayList
    foreach ($par in $achadas) {
      foreach ($n in [Msaa]::Listar($par[0], $Profundidade)) {
        [void]$itens.Add([ordered]@{ janela = $par[1]; nome = $n.Nome; tipo = $n.Papel; teclado = (($n.Estado -band 0x100000) -ne 0);
                                     ativo = (-not $n.Desativado); visivel = $n.Visivel; atalho = $n.Atalho })
      }
    }
    [ordered]@{ janelas = @($achadas | ForEach-Object { $_[1] }); narrador = [bool](Get-Process Narrator -ErrorAction SilentlyContinue);
                itens = $itens } | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $Saida
    "lidos: $($itens.Count) elementos em $($achadas.Count) janela(s)"
  }
}
