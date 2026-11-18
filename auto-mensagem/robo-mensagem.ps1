# ============================================================================
#  Robo de mensagem: cola um texto numa janela especifica e aperta Enter
#  em intervalos aleatorios (3 a 7 min, com segundos quebrados).
#  Para: depois de 6 horas OU quando voce apertar F1.
#
#  Uso:   iniciar.bat            -> roda normalmente
#         iniciar.bat -Listar    -> so mostra os titulos das janelas abertas
# ============================================================================
param([switch]$Listar)

# ======================= CONFIGURACAO (edite aqui) ==========================
$TituloJanela = "Claude"   # parte do titulo da janela alvo (sem diferenciar maiusculas)

$Mensagem = 'manda, crie mais TT, e suba os campos da segunda, se não tiver mande da primeira ou use os recursos do herói. Se ele estiver parado e sem aventura mande ele pra aventura e/ou matar animais em oásis'

$MinSegundos     = 180.0   # 3 min
$MaxSegundos     = 420.0   # 7 min
$DuracaoHoras    = 6
$EnviarAoIniciar = $true   # $true = manda a 1a mensagem logo ao iniciar

# Clicar na caixa de texto antes de colar (bom para apps de chat, onde a
# caixa fica embaixo). Clica no meio da largura, X pixels acima da borda de baixo.
$ClicarNoCampo          = $true
$CliqueDistanciaDoFundo = 120
# ============================================================================

Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class W {
  [DllImport("user32.dll")] public static extern bool   SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool   ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool   IsIconic(IntPtr h);
  [DllImport("user32.dll")] public static extern bool   IsWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern short  GetAsyncKeyState(int k);
  [DllImport("user32.dll")] public static extern void   keybd_event(byte vk, byte sc, uint f, UIntPtr e);
  [DllImport("user32.dll")] public static extern bool   GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool   SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void   mouse_event(uint f, int x, int y, uint d, UIntPtr e);
  public struct RECT { public int Left, Top, Right, Bottom; }
}
"@

function Log($txt, $cor = "Gray") {
    Write-Host ("[{0:HH:mm:ss}] {1}" -f (Get-Date), $txt) -ForegroundColor $cor
}

function JanelasAbertas($filtro) {
    Get-Process | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$filtro*" }
}

function F1Apertado {
    return (([W]::GetAsyncKeyState(0x70) -band 0x8000) -ne 0)
}

# Espera N segundos mostrando contagem; retorna $false se apertou F1 ou acabou o tempo
function Aguardar([double]$seg) {
    $fim = (Get-Date).AddSeconds($seg)
    while ((Get-Date) -lt $fim) {
        if (F1Apertado)                   { Write-Host ""; Log "F1 apertado - parando." Yellow; return $false }
        if ((Get-Date) -ge $script:Prazo) { Write-Host ""; Log "Chegou ao limite de $DuracaoHoras horas - parando." Yellow; return $false }
        $rest = $fim - (Get-Date)
        Write-Host ("`r   proximo envio em {0:mm\:ss}   (F1 para parar)   " -f $rest) -NoNewline
        Start-Sleep -Milliseconds 100
    }
    Write-Host ""
    return $true
}

# Traz a janela para frente e confirma que ela realmente esta em foco
function Focar([IntPtr]$h) {
    if ([W]::IsIconic($h)) { [W]::ShowWindow($h, 9) | Out-Null; Start-Sleep -Milliseconds 300 }
    # toque no ALT libera o Windows a trocar o foco para outra janela
    [W]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero)
    [W]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)
    [W]::SetForegroundWindow($h) | Out-Null
    Start-Sleep -Milliseconds 500
    return ([W]::GetForegroundWindow() -eq $h)
}

function Enviar([IntPtr]$h) {
    Set-Clipboard -Value $Mensagem
    if ($ClicarNoCampo) {
        $r = New-Object W+RECT
        [W]::GetWindowRect($h, [ref]$r) | Out-Null
        $x = [int](($r.Left + $r.Right) / 2)
        $y = [int]($r.Bottom - $CliqueDistanciaDoFundo)
        [W]::SetCursorPos($x, $y) | Out-Null
        [W]::mouse_event(0x2, 0, 0, 0, [UIntPtr]::Zero)  # botao esquerdo desce
        [W]::mouse_event(0x4, 0, 0, 0, [UIntPtr]::Zero)  # botao esquerdo sobe
        Start-Sleep -Milliseconds 300
    }
    # checagem final: so digita se a janela certa ainda estiver em foco
    if ([W]::GetForegroundWindow() -ne $h) { return $false }
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds 400
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    return $true
}

# ----------------------------------------------------------------------------
if ($Listar) {
    Write-Host "Janelas abertas (use parte do titulo em `$TituloJanela):" -ForegroundColor Cyan
    JanelasAbertas "" | ForEach-Object { "  [{0}]  {1}" -f $_.ProcessName, $_.MainWindowTitle }
    return
}

# Escolhe a janela alvo uma vez e "trava" nela pelo identificador (handle)
$cands = @(JanelasAbertas $TituloJanela)
if ($cands.Count -eq 0) {
    Log "Nenhuma janela com '$TituloJanela' no titulo. Janelas abertas:" Red
    JanelasAbertas "" | ForEach-Object { "  [{0}]  {1}" -f $_.ProcessName, $_.MainWindowTitle }
    Log "Edite `$TituloJanela no topo do script e rode de novo." Red
    return
}
if ($cands.Count -gt 1) {
    Write-Host "Mais de uma janela encontrada:" -ForegroundColor Cyan
    for ($i = 0; $i -lt $cands.Count; $i++) {
        "  {0}) [{1}] {2}" -f ($i + 1), $cands[$i].ProcessName, $cands[$i].MainWindowTitle
    }
    $esc = [int](Read-Host "Numero da janela") - 1
    $alvo = $cands[$esc]
} else { $alvo = $cands[0] }

$hJanela = $alvo.MainWindowHandle
Log ("Janela alvo: [{0}] {1}" -f $alvo.ProcessName, $alvo.MainWindowTitle) Green

$script:Prazo = (Get-Date).AddHours($DuracaoHoras)
Log ("Rodando ate {0:HH:mm:ss} ou ate apertar F1." -f $script:Prazo) Green
[void](F1Apertado)   # limpa estado anterior da tecla

$enviados = 0
$parar    = $false
$primeira = $true

while (-not $parar) {
    if (-not ($primeira -and $EnviarAoIniciar)) {
        $seg = Get-Random -Minimum $MinSegundos -Maximum $MaxSegundos
        Log ("Sorteado: {0}m {1:N1}s" -f [math]::Floor($seg / 60), ($seg % 60)) Cyan
        if (-not (Aguardar $seg)) { break }
    }
    $primeira = $false

    # Tenta ate 6 vezes (10 s entre tentativas) garantir a janela certa
    $ok = $false
    for ($t = 1; $t -le 6 -and -not $ok; $t++) {
        if (-not [W]::IsWindow($hJanela)) {
            Log "A janela alvo foi fechada. Procurando de novo por '$TituloJanela'..." Yellow
            $nova = @(JanelasAbertas $TituloJanela) | Select-Object -First 1
            if ($nova) { $hJanela = $nova.MainWindowHandle; Log "Achei: $($nova.MainWindowTitle)" Green }
        }
        if ([W]::IsWindow($hJanela) -and (Focar $hJanela) -and (Enviar $hJanela)) {
            $ok = $true
            $enviados++
            Log "Mensagem #$enviados enviada." Green
        } else {
            Log "Nao consegui focar a janela certa (tentativa $t/6). Nada foi digitado." Yellow
            if (-not (Aguardar 10)) { $parar = $true; break }
        }
    }
    if (-not $ok -and -not $parar) { Log "Pulei este envio; sigo para o proximo sorteio." Red }
}

Log "Fim. Total de mensagens enviadas: $enviados" Green
