@echo off
:: ============================================================
::  build_exe.bat — Empaqueta Fungi Traductor como .exe
::  Requisito: pip install pyinstaller
:: ============================================================

echo.
echo  ============================================
echo   Fungi Traductor — Empaquetador Windows
echo  ============================================
echo.

:: Instalar PyInstaller si no está
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  Instalando PyInstaller...
    pip install pyinstaller
)

:: Limpiar builds anteriores
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist

:: Empaquetar
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "FungiTraductor" ^
  --add-data "model.py;." ^
  --add-data "view.py;." ^
  --add-data "controller.py;." ^
  --hidden-import "argostranslate" ^
  --hidden-import "langdetect" ^
  --hidden-import "pyttsx3" ^
  app.py

echo.
if exist "dist\FungiTraductor.exe" (
    echo  [OK] Ejecutable generado: dist\FungiTraductor.exe
) else (
    echo  [ERROR] No se encontro el ejecutable. Revisa los mensajes de arriba.
)
echo.
pause
