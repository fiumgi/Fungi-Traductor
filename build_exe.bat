@echo off

echo ============================================
echo  Fungi Traductor — Build EXE
echo ============================================

pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    pip install pyinstaller
)

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

pyinstaller ^
  --onefile ^
  --windowed ^
  --name "FungiTraductor" ^
  --hidden-import argostranslate ^
  --hidden-import langdetect ^
  --hidden-import pyttsx3 ^
  app.py

echo.
if exist dist\FungiTraductor.exe (
    echo [OK] EXE generado en dist\
) else (
    echo [ERROR] Falló build
)
pause