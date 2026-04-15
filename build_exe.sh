#!/usr/bin/env bash
set -e

echo "Fungi Traductor build..."

if ! pip show pyinstaller &>/dev/null; then
    pip install pyinstaller
fi

rm -rf build dist

pyinstaller \
  --onefile \
  --windowed \
  --name "FungiTraductor" \
  --hidden-import argostranslate \
  --hidden-import langdetect \
  --hidden-import pyttsx3 \
  app.py

echo "Listo: dist/FungiTraductor"