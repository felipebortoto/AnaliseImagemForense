# ============================================================
#  FORENSIC EXIF ANALYZER — Iniciador Inteligente
#  Uso: .\run.ps1 [-Port 8080] [-NoBrowser] [-Force]
# ============================================================
param(
    [int]   $Port      = 0,        # 0 = detectar porta livre automaticamente
    [switch]$NoBrowser = $false,   # Nao abre o browser automaticamente
    [switch]$Force     = $false    # Mata processos na porta sem perguntar
)

$ErrorActionPreference = "Stop"

# ── Cores para output ──────────────────────────────────────
function Write-Header($msg) { Write-Host "`n  $msg" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "  [OK] $msg"    -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host "  [!]  $msg"    -ForegroundColor Yellow }
function Write-Fail($msg)   { Write-Host "  [X]  $msg"    -ForegroundColor Red }
function Write-Step($msg)   { Write-Host "  -->  $msg"    -ForegroundColor Gray }

Write-Host ""
Write-Host "  ======================================================" -ForegroundColor DarkYellow
Write-Host "   FORENSIC EXIF ANALYZER | OPENSEC" -ForegroundColor Yellow
Write-Host "  ======================================================" -ForegroundColor DarkYellow

# ── 1. Localizar raiz do projeto ───────────────────────────
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}
Set-Location $ProjectRoot
Write-Step "Diretorio do projeto: $ProjectRoot"

# ── 2. Localizar Python do venv ────────────────────────────
Write-Header "Localizando Python..."

$VenvPython = $null
$VenvCandidates = @(
    "$ProjectRoot\.venv\Scripts\python.exe",
    "$ProjectRoot\venv\Scripts\python.exe",
    "$ProjectRoot\.venv\bin\python",
    "$ProjectRoot\venv\bin\python"
)

foreach ($candidate in $VenvCandidates) {
    if (Test-Path $candidate) {
        $VenvPython = $candidate
        Write-Ok "venv encontrado: $candidate"
        break
    }
}

if (-not $VenvPython) {
    Write-Warn "venv nao encontrado. Tentando criar automaticamente..."
    
    # Tenta encontrar python no sistema
    $SystemPython = $null
    foreach ($cmd in @("python3", "python", "py")) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python 3") {
                $SystemPython = $cmd
                break
            }
        } catch {}
    }
    
    if (-not $SystemPython) {
        Write-Fail "Python 3 nao encontrado no sistema."
        Write-Host "  Instale via: https://www.python.org/downloads/" -ForegroundColor Red
        pause; exit 1
    }
    
    Write-Step "Criando venv com $SystemPython..."
    & $SystemPython -m venv .venv
    $VenvPython = "$ProjectRoot\.venv\Scripts\python.exe"
    
    Write-Step "Instalando dependencias..."
    & $VenvPython -m pip install -r requirements.txt --quiet
    Write-Ok "venv criado e dependencias instaladas."
}

# ── 3. Verificar dependencias criticas ─────────────────────
Write-Header "Verificando dependencias..."
$deps = @("fastapi", "uvicorn", "PIL", "folium")
$missing = @()
foreach ($dep in $deps) {
    $check = & $VenvPython -c "import $dep" 2>&1
    if ($LASTEXITCODE -ne 0) { $missing += $dep }
}

if ($missing.Count -gt 0) {
    Write-Warn "Dependencias ausentes: $($missing -join ', '). Instalando..."
    & $VenvPython -m pip install -r requirements.txt --quiet
    Write-Ok "Dependencias instaladas."
} else {
    Write-Ok "Todas as dependencias presentes."
}

# ── 4. Encontrar porta livre ───────────────────────────────
Write-Header "Verificando porta..."

function Test-PortFree([int]$p) {
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $p)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

function Get-ProcessOnPort([int]$p) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
        if ($conns) { return $conns[0].OwningProcess }
    } catch {}
    return $null
}

function Free-Port([int]$p, [bool]$force) {
    $procPid = Get-ProcessOnPort $p
    if ($null -eq $procPid -or $procPid -eq 0) { return $true }
    
    try {
        $proc = Get-Process -Id $procPid -ErrorAction SilentlyContinue
        $procName = if ($proc) { $proc.Name } else { "PID $procPid" }
        
        if (-not $force) {
            $ans = Read-Host "  Porta $p ocupada por '$procName' (PID $procPid). Encerrar? [S/n]"
            if ($ans -match "^[Nn]") { return $false }
        } else {
            Write-Warn "Encerrando '$procName' (PID $procPid) na porta $p..."
        }
        
        Stop-Process -Id $procPid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 800
        Write-Ok "Processo encerrado."
        return $true
    } catch {
        Write-Warn "Nao foi possivel encerrar o processo na porta $p."
        return $false
    }
}

# Determina a porta a usar
if ($Port -eq 0) {
    # Auto-detecta uma porta livre
    $PortCandidates = @(8000, 8080, 8081, 8888, 9000, 9090, 5000, 3000)
    $ChosenPort = $null

    foreach ($p in $PortCandidates) {
        if (Test-PortFree $p) {
            $ChosenPort = $p
            Write-Ok "Porta $p disponivel."
            break
        } else {
            $procPid = Get-ProcessOnPort $p
            if ($null -ne $procPid -and $procPid -ne 0) {
                $freed = Free-Port $p $Force.IsPresent
                if ($freed -and (Test-PortFree $p)) {
                    $ChosenPort = $p
                    break
                }
            }
        }
    }

    if (-not $ChosenPort) {
        Write-Fail "Nenhuma porta disponivel encontrada. Use -Port para especificar uma manualmente."
        pause; exit 1
    }
} else {
    # Usa a porta especificada
    if (-not (Test-PortFree $Port)) {
        $freed = Free-Port $Port $Force.IsPresent
        if (-not $freed -or -not (Test-PortFree $Port)) {
            Write-Fail "Porta $Port ainda ocupada. Tente outra com -Port XXXX"
            pause; exit 1
        }
    }
    $ChosenPort = $Port
    Write-Ok "Porta $ChosenPort disponivel."
}

$Url = "http://127.0.0.1:$ChosenPort"

# ── 5. Abrir browser ───────────────────────────────────────
if (-not $NoBrowser) {
    Write-Header "Abrindo browser..."
    # Aguarda 1.5s para o server subir antes de abrir
    $null = Start-Job -ScriptBlock {
        param($u)
        Start-Sleep -Milliseconds 1500
        Start-Process $u
    } -ArgumentList $Url
    Write-Ok "Browser sera aberto automaticamente em $Url"
}

# ── 6. Iniciar servidor ────────────────────────────────────
Write-Header "Iniciando servidor forense..."
Write-Host ""
Write-Host "  ======================================================" -ForegroundColor DarkYellow
Write-Host "   URL: $Url" -ForegroundColor Yellow
Write-Host "   Pressione Ctrl+C para encerrar o servidor." -ForegroundColor Gray
Write-Host "  ======================================================" -ForegroundColor DarkYellow
Write-Host ""

try {
    & $VenvPython -m uvicorn src.server:app `
        --host 127.0.0.1 `
        --port $ChosenPort `
        --reload `
        --reload-delay 0.5 `
        --log-level info
} catch {
    Write-Fail "Falha ao iniciar o servidor: $_"
    pause; exit 1
}

