@echo off
title Contador de Ovos
cd /d "%~dp0"

REM Unico ponto de entrada: abre o Chrome na tela de carregamento
REM e sobe processador + BFF + gateway + site em segundo plano.
python "%~dp0scripts\launcher\server.py"
if errorlevel 1 (
  echo.
  echo Falha ao iniciar o Contador de Ovos.
  echo Verifique se o Python esta instalado e no PATH.
  pause
)
