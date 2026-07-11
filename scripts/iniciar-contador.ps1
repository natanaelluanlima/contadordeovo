# Inicia o ecossistema Egg (processador, BFF, gateway e site) em segundo plano.
param(
    [string]$WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$JavaHome = $env:JAVA_HOME,
    [switch]$AbrirNavegador
)

$ErrorActionPreference = "Stop"

function Get-JavaHome {
    param([string]$Preferred)
    if ($Preferred -and (Test-Path (Join-Path $Preferred "bin\java.exe"))) {
        return $Preferred
    }
    $candidates = @(
        "C:\Program Files\Zulu\zulu-21",
        "C:\Program Files\Java\jdk-21",
        "C:\Program Files\Eclipse Adoptium\jdk-21*"
    )
    foreach ($candidate in $candidates) {
        $resolved = Get-Item $candidate -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($resolved -and (Test-Path (Join-Path $resolved.FullName "bin\java.exe"))) {
            return $resolved.FullName
        }
    }
    throw "JDK 21 nao encontrado. Defina JAVA_HOME ou instale o Zulu 21."
}

function Test-PortListening {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Start-BackgroundService {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Command,
        [hashtable]$EnvVars = @{}
    )

    $logsDir = Join-Path $WorkspaceRoot "logs"
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
    $logFile = Join-Path $logsDir "$Name.log"

    $envSetup = ($EnvVars.GetEnumerator() | ForEach-Object {
        "`$env:$($_.Key)='$($_.Value -replace "'", "''")'"
    }) -join "; "

    $escapedDir = $WorkingDirectory -replace "'", "''"
    $escapedLog = $logFile -replace "'", "''"

    $scriptParts = @()
    if ($envSetup) { $scriptParts += $envSetup }
    $scriptParts += "Set-Location '$escapedDir'"
    $scriptParts += "$Command 2>&1 | Tee-Object -FilePath '$escapedLog' -Append"
    $script = $scriptParts -join "; "

    $proc = Start-Process powershell.exe `
        -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $script `
        -PassThru -WindowStyle Hidden

    return @{
        Name    = $Name
        Pid     = $proc.Id
        LogFile = $logFile
    }
}

$javaHome = Get-JavaHome -Preferred $JavaHome
$ports = @(9002, 9001, 9000, 8009)
$emUso = $ports | Where-Object { Test-PortListening $_ }
if ($emUso) {
    Write-Host "Atencao: portas ja em uso: $($emUso -join ', ')." -ForegroundColor Yellow
    Write-Host "Use scripts\parar-contador.ps1 para encerrar os servicos antigos." -ForegroundColor Yellow
}

$pythonEgg = Join-Path $WorkspaceRoot "python\egg"
$javaBff = Join-Path $WorkspaceRoot "java\bff"
$javaGateway = Join-Path $WorkspaceRoot "java\gateway"
$reactEgg = Join-Path $WorkspaceRoot "react\egg"
$envFile = Join-Path $reactEgg ".env.local"
$envExample = Join-Path $reactEgg ".env.local.example"
$logsDir = Join-Path $WorkspaceRoot "logs"
$pidFile = Join-Path $logsDir "services.json"

if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
}

if (-not (Test-Path (Join-Path $reactEgg "node_modules"))) {
    Write-Host "Instalando dependencias do site (primeira vez)..." -ForegroundColor Cyan
    Push-Location $reactEgg
    npm install
    Pop-Location
}

Write-Host "Iniciando servicos em segundo plano..." -ForegroundColor Green

$services = @()
$services += Start-BackgroundService -Name "processador" -WorkingDirectory $pythonEgg -Command "python -m egg_counter.processador_main"
Start-Sleep -Seconds 2

# debug=false evita conflito JDWP (porta 5005) entre BFF e gateway no quarkus:dev
$quarkusEnv = @{
    JAVA_HOME = $javaHome
    QUARKUS_ANALYTICS_DISABLED = "true"
}
$services += Start-BackgroundService -Name "bff" -WorkingDirectory $javaBff -Command ".\mvnw.cmd quarkus:dev `"-Ddebug=false`"" -EnvVars $quarkusEnv
Start-Sleep -Seconds 3

$services += Start-BackgroundService -Name "gateway" -WorkingDirectory $javaGateway -Command ".\mvnw.cmd quarkus:dev `"-Ddebug=false`"" -EnvVars $quarkusEnv
Start-Sleep -Seconds 3

$services += Start-BackgroundService -Name "site" -WorkingDirectory $reactEgg -Command "npm run dev"

New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
$services | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8

Write-Host ""
Write-Host "Servicos iniciados em segundo plano (sem janelas extras)." -ForegroundColor Green
Write-Host "Demo: http://localhost:8009/contagem" -ForegroundColor Cyan
Write-Host "Logs: $logsDir" -ForegroundColor Cyan
Write-Host "Aguarde ~1 minuto para o BFF e o gateway terminarem de subir." -ForegroundColor Yellow
Write-Host "Para encerrar: scripts\parar-contador.ps1" -ForegroundColor Yellow

if ($AbrirNavegador) {
    Start-Sleep -Seconds 20
    Start-Process "http://localhost:8009/contagem"
}
