# Busca atualizacoes do repositorio remoto (git pull --ff-only).
param(
    [string]$WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$Agendar,
    [switch]$RemoverAgendamento,
    [int]$IntervaloMinutos = 10,
    [switch]$Silencioso
)

$ErrorActionPreference = "Stop"
$TaskName = "Contador de Ovos - Atualizar Git"
$ScriptPath = $MyInvocation.MyCommand.Path

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"

    $logsDir = Join-Path $WorkspaceRoot "logs"
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
    Add-Content -Path (Join-Path $logsDir "atualizar.log") -Value $line -Encoding UTF8

    if (-not $Silencioso) {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Register-UpdateTask {
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -Silencioso"

    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervaloMinutos) -RepetitionDuration ([TimeSpan]::MaxValue)

    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Atualiza o repositorio contador com git pull --ff-only a cada $IntervaloMinutos minuto(s)." `
        -Force | Out-Null

    Write-Host "Agendamento criado: '$TaskName' (a cada $IntervaloMinutos min)." -ForegroundColor Green
    Write-Host "Para remover: .\scripts\atualizar-contador.ps1 -RemoverAgendamento" -ForegroundColor Cyan
}

function Unregister-UpdateTask {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "Nenhum agendamento encontrado com o nome '$TaskName'." -ForegroundColor Yellow
        return
    }

    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Agendamento '$TaskName' removido." -ForegroundColor Green
}

if ($Agendar) {
    Register-UpdateTask
    exit 0
}

if ($RemoverAgendamento) {
    Unregister-UpdateTask
    exit 0
}

if (-not (Test-Path (Join-Path $WorkspaceRoot ".git"))) {
    $msg = "Pasta nao e um repositorio Git: $WorkspaceRoot"
    Write-Log $msg "Red"
    if (-not $Silencioso) { exit 1 }
    exit 1
}

Push-Location $WorkspaceRoot
try {
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    $remote = "origin"

    git fetch $remote 2>&1 | Out-Null

    $localHead = (git rev-parse HEAD).Trim()
    $remoteHead = (git rev-parse "$remote/$branch" 2>$null).Trim()

    if (-not $remoteHead) {
        Write-Log "Branch remota '$remote/$branch' nao encontrada." "Yellow"
        exit 0
    }

    if ($localHead -eq $remoteHead) {
        Write-Log "Ja esta atualizado ($branch)." "Green"
        exit 0
    }

    $status = git status --porcelain
    if ($status) {
        Write-Log "Ha alteracoes locais nao commitadas. Pull ignorado para evitar conflito." "Yellow"
        Write-Log "Faca commit ou stash antes de atualizar." "Yellow"
        exit 1
    }

    git pull --ff-only $remote $branch 2>&1 | ForEach-Object { Write-Log $_ "Cyan" }
    $newHead = (git rev-parse --short HEAD).Trim()
    Write-Log "Repositorio atualizado ($branch @ $newHead)." "Green"
}
catch {
    Write-Log "Falha ao atualizar: $($_.Exception.Message)" "Red"
    exit 1
}
finally {
    Pop-Location
}
