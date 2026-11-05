@echo off
REM VINT Match - inicia o app no Windows (deixe esta janela aberta enquanto usa)
chcp 65001 >nul
cd /d "%~dp0"
title VINT Match

if exist .venv\Scripts\python.exe goto deps
echo Criando ambiente Python (.venv)...
where py >nul 2>nul
if %errorlevel%==0 (py -3 -m venv .venv) else (python -m venv .venv)
if not exist .venv\Scripts\python.exe goto erro_python

:deps
echo Conferindo dependencias (a primeira vez demora alguns minutos)...
.venv\Scripts\python.exe -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto erro_pip
if not exist .env copy .env.example .env >nul

.venv\Scripts\python.exe start_server.py %*
echo.
echo O servidor parou. O registro completo esta em logs\servidor.log
pause
exit /b

:erro_python
echo.
echo ERRO: nao encontrei o Python. Instale o Python 3.10+ (python.org, marque "Add Python to PATH") e rode de novo.
pause
exit /b 1

:erro_pip
echo.
echo ERRO ao instalar as dependencias. Copie a mensagem acima e envie para o time.
pause
exit /b 1
