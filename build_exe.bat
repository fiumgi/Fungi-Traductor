@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
if errorlevel 1 (
    echo [ERROR] No se pudo acceder al directorio del proyecto.
    exit /b 1
)

echo ============================================
echo  🍄 Fungi Traductor — Build System (Win)
echo ============================================

:: 1. Entorno Virtual
if not exist venv\Scripts\python.exe (
    echo [INFO] Creando entorno virtual en venv\...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        exit /b 1
    )
)
echo [INFO] Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] No se pudo activar el entorno virtual.
    exit /b 1
)

:: 2. Instalar y verificar todas las dependencias del proyecto
echo [INFO] Verificando dependencias del proyecto...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias.
    exit /b 1
)

:: 3. Limpieza previa
echo [INFO] Limpiando carpetas de build anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist FungiTraductor.spec del /f /q FungiTraductor.spec

:: 4. Compilación
echo [INFO] Iniciando empaquetado (PyInstaller)...
echo [HINT] Esto puede tardar varios minutos dependiendo de tu PC.

python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --name "FungiTraductor" ^
  --hidden-import argostranslate ^
  --hidden-import langdetect ^
  --hidden-import pyttsx3 ^
  --hidden-import pyttsx3.drivers ^
  --hidden-import pyttsx3.drivers.sapi5 ^
  --hidden-import fitz ^
  --hidden-import docx ^
  --hidden-import fpdf ^
  --hidden-import odf ^
  --hidden-import pytesseract ^
  --hidden-import PIL ^
  --collect-all argostranslate ^
  --collect-all pyttsx3 ^
  --collect-all fitz ^
  --collect-all docx ^
  --collect-all fpdf ^
  --collect-all odf ^
  --add-data "fungi_traductor/assets;fungi_traductor/assets" ^
  --clean ^
  app.py

:: 5. Resultado
echo.
if exist dist\FungiTraductor.exe (
    echo ============================================
    echo  [OK] PROCESO COMPLETADO
    echo  Ejecutable en: dist\FungiTraductor.exe
    echo ============================================
) else (
    echo ============================================
    echo  [ERROR] El build ha fallado.
    echo  Revisa los mensajes de arriba para mas info.
    echo ============================================
)

pause
