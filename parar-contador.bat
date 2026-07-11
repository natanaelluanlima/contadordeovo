@echo off
cd /d "%~dp0"
REM Encerramento de emergencia (o fluxo normal e o botao Desligar no sistema).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\parar-contador.ps1"
REM Tambem tenta avisar o launcher, se ainda estiver ativo.
powershell -NoProfile -Command "try { Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8010/api/shutdown' -TimeoutSec 2 | Out-Null } catch {}"
echo Contador encerrado.
timeout /t 2 >nul
