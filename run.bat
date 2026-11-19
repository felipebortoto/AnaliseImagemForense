@echo off
chcp 65001 >nul
title FORENSIC EXIF ANALYZER - Iniciando...
echo.
echo   ======================================================
echo    FORENSIC EXIF ANALYZER ^| OPENSEC
echo    Iniciando servidor web...
echo   ======================================================
echo.

REM Muda para o diretório do script
cd /d "%~dp0"

REM Executa o PowerShell com política de execução liberada para este processo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" -Force

pause

