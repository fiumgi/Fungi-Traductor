#!/usr/bin/env bash
# ============================================================
#  build_exe.sh — Empaqueta Fungi Traductor (Linux / macOS)
#  Requisito: pip install pyinstaller
# ============================================================

set -e

echo ""
echo " ============================================"
echo "  Fungi Traductor — Empaquetador Linux/macOS"
echo " ============================================"
echo ""

# Instalar PyInstaller si no está
if ! pip show pyinstaller &>/dev/null; then
    echo " Instalando PyInstaller..."
    pip install pyinstaller
fi

# Limpiar builds anteriores
rm -rf build dist

# Empaquetar
pyinstaller \
  --onefile \
  --windowed \
  --name "FungiTraductor" \
  --hidden-import "argostranslate" \
  --hidden-import "langdetect" \
  --hidden-import "pyttsx3" \
  app.py

echo ""
if [ -f "dist/FungiTraductor" ]; then
    echo " [OK] Binario generado: dist/FungiTraductor"
else
    echo " [ERROR] No se encontró el binario. Revisa los mensajes anteriores."
    exit 1
fi
echo ""
