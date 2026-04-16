## 🍄 Fungi Traductor 

Traductor offline con interfaz gráfica construido con argostranslate + Tkinter.  
Arquitectura MVC modular, redimensionable y multi-idioma.

---

## 🚀 Instalación rápida

git clone https://github.com/fiumgi/Fungi-Traductor.

cd Fungi-Traductor.

pip install -r requirements.txt.

python app.py.

---

## ✨ Funcionalidades

| Función | Descripción |
|--------|------------|
| Multi-idioma | Combobox con idiomas disponibles |
| Swap ⇄ | Intercambia idiomas y textos |
| Scrollbars | Paneles con desplazamiento |
| Auto-traducción | Botón ⚡ Auto (debounce) |
| Detección | Usa langdetect |
| TTS | Texto a voz con pyttsx3 |
| Ajuste fuente | Ctrl + rueda |
| Logging | fungi_traductor.log |
| Responsive | UI redimensionable |
Permitir elegir manualmente la voz desde la interfaz.
Mostrar progreso más detallado durante descarga e instalación de paquetes.
---

## 🧱 Estructura del proyecto


Fungi-Traductor/
│
├── fungi_traductor/
│ ├── init.py
│ ├── model/
│ │ └── translator.py
│ ├── view/
│ │ └── gui.py
│ └── controller/
│ └── app_controller.py
│
├── app.py
├── pyproject.toml
├── requirements.txt
├── build_exe.bat
├── build_exe.sh
└── README.md


---

## 📦 Instalar como app (pipx)

pipx:
pipx install git+https://github.com/fiumgi/Fungi-Traductor.git

Luego ejecutar desde cualquier lugar:
fungi-traductor

---

## ⚙️ Crear ejecutable

### Windows
build_exe.bat

### Linux / macOS
chmod +x build_exe.sh
./build_exe.sh

---

## 🔌 Dependencias opcionales

pip install langdetect .
/ detecta el idioma automaticamente 

pip install pyttsx3 .
/ sirve para la opcion de speak

---

## ⚠️ Notas

- No subir `dist/`, `build/`, `__pycache__/`
- Requiere Python 3.10+
