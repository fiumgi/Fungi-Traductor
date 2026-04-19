@echo off
setlocal enabledelayedexpansion

echo ============================================
echo  🍄 Fungi Traductor — Build System (Win)
echo ============================================

:: 1. Entorno Virtual
if exist venv\Scripts\activate.bat (
    echo [INFO] Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo [WARN] No se encontro venv\, se usara el Python global.
)

:: 2. Verificar/Instalar PyInstaller
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando PyInstaller...
    python -m pip install pyinstaller
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
  --collect-all argostranslate ^
  --collect-all pyttsx3 ^
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