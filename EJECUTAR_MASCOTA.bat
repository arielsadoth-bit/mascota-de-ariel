@echo off
title Mascota de escritorio - Peluche 10
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo No se encontro Python en tu PC.
    echo Instala Python 3 desde python.org y marca "Add Python to PATH".
    echo.
    pause
    exit /b
)

echo Instalando Pillow si hace falta...
python -m pip install -r requirements.txt

echo.
echo Iniciando mascota...
python mascota_escritorio.py
pause
