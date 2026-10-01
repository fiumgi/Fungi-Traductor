#!/usr/bin/env bash
# Fungi Traductor — Build Script for Linux
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo " 🍄 Fungi Traductor — Build System (Linux)"
echo "============================================"

# 0. Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 no está instalado o no se encuentra en el PATH."
    exit 1
fi

# 1. Entorno Virtual
if [ ! -f "venv/bin/activate" ]; then
    echo "[INFO] Creando entorno virtual en venv/..."
    python3 -m venv venv
fi
echo "[INFO] Activando entorno virtual..."
source venv/bin/activate
PYTHON_BIN="python"

# 2. Instalar y verificar todas las dependencias del proyecto
echo "[INFO] Verificando dependencias del proyecto..."
"$PYTHON_BIN" -m pip install -r requirements.txt

# 3. Limpieza previa
echo "[INFO] Limpiando builds anteriores..."
rm -rf build dist FungiTraductor.spec

# 4. Compilación
echo "[INFO] Iniciando empaquetado (esto puede tardar)..."
"$PYTHON_BIN" -m PyInstaller \
  --onefile \
  --windowed \
  --name "FungiTraductor" \
  --hidden-import argostranslate \
  --hidden-import langdetect \
  --hidden-import pyttsx3 \
  --hidden-import pyttsx3.drivers \
  --hidden-import pyttsx3.drivers.espeak \
  --hidden-import fitz \
  --hidden-import docx \
  --hidden-import fpdf \
  --hidden-import odf \
  --hidden-import pytesseract \
  --hidden-import PIL \
  --collect-all argostranslate \
  --collect-all pyttsx3 \
  --collect-all fitz \
  --collect-all docx \
  --collect-all fpdf \
  --collect-all odf \
  --add-data "fungi_traductor/assets:fungi_traductor/assets" \
  --clean \
  app.py

# 5. Resultado
if [ -f "dist/FungiTraductor" ]; then
    echo "============================================"
    echo " [OK] PROCESO COMPLETADO"
    echo " Ejecutable en: dist/FungiTraductor"
    echo "============================================"
else
    echo "============================================"
    echo " [ERROR] El build ha fallado."
    echo "============================================"
    exit 1
fi
