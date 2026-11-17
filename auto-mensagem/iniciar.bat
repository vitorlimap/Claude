@echo off
title Robo de mensagem (F1 para parar)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0robo-mensagem.ps1" %*
echo.
pause
