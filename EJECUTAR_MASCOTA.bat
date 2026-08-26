@echo off
cd /d "%~dp0"

where pythonw >nul 2>nul
if errorlevel 1 (
    echo.
    echo No se encontro Python con ventana oculta en tu PC.
    echo Instala Python 3 desde python.org y marca "Add Python to PATH".
    echo.
    pause
    exit /b
)

python -c "import PIL" >nul 2>nul
if errorlevel 1 (
    echo Instalando Pillow por primera vez...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo No se pudo instalar Pillow.
        pause
        exit /b
    )
)

start "" pythonw mascota_escritorio.py
exit /b
