#!/usr/bin/env bash
# Fungi Traductor — Build Script for Linux
set -e

echo "============================================"
echo " 🍄 Fungi Traductor — Build System (Linux)"
echo "============================================"

# 0. Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 no está instalado o no se encuentra en el PATH."
    exit 1
fi

# 1. Entorno Virtual
if [ -d "venv" ]; then
    echo "[INFO] Activando entorno virtual..."
    source venv/bin/activate
else
    echo "[WARN] No se encontró la carpeta venv/. Se usará el Python del sistema."
fi

# 2. Verificar/Instalar PyInstaller
if ! python3 -m pip show pyinstaller &>/dev/null; then
    echo "[INFO] Instalando PyInstaller..."
    python3 -m pip install pyinstaller
fi

# 3. Limpieza previa
echo "[INFO] Limpiando builds anteriores..."
rm -rf build dist FungiTraductor.spec

# 4. Compilación
echo "[INFO] Iniciando empaquetado (esto puede tardar)..."
python3 -m PyInstaller \
  --onefile \
  --windowed \
  --name "FungiTraductor" \
  --hidden-import argostranslate \
  --hidden-import langdetect \
  --hidden-import pyttsx3 \
  --hidden-import pyttsx3.drivers \
  --hidden-import pyttsx3.drivers.espeak \
  --collect-all argostranslate \
  --collect-all pyttsx3 \
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