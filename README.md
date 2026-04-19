# 🍄 Fungi Traductor

![Fungi Traductor Icon](fungi_traductor/assets/icon.png)

Traductor offline de alto rendimiento con interfaz gráfica moderna, diseñado para ofrecer privacidad total y velocidad. Basado en el motor de **Argos Translate**, permite traducir textos sin conexión a internet entre múltiples idiomas.

---

## ✨ Características Premium

- **🌐 100% Offline**: Tus datos nunca salen de tu equipo. Privacidad garantizada.
- **⚡ Auto-Traducción Inteligente**: Traduce en tiempo real mientras escribes (con sistema de *debouncing* para evitar sobrecarga).
- **🔊 Lectura por Voz (TTS)**: Motor de voz integrado con soporte para múltiples voces.
- **🔍 Detección de Idioma**: Identificación automática del idioma de entrada mediante `langdetect`.
- **🎨 Interfaz Adaptativa**: Diseño oscuro (Dark Mode) nítido gracias al soporte de **High DPI Awareness** (evita el desenfoque en Windows).
- **📦 Distribución Moderna**: Compatible con `pipx` para uso global y scripts de compilación para crear ejecutables independientes.

---

## 🚀 Instalación y Uso

### 1. Vía pipx (Recomendado)
Para usar el traductor como una aplicación global en tu terminal:

```bash
pipx install git+https://github.com/fiumgi/Fungi-Traductor.git
```

Una vez instalado, simplemente escribe:
```bash
fungi-traductor
```

### 2. Para Desarrolladores (Código Fuente)
1. Clona el repositorio:
   ```bash
   git clone https://github.com/fiumgi/Fungi-Traductor.git
   cd Fungi-Traductor
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta la aplicación:
   ```bash
   python app.py
   ```

---

## 🛠️ Creación de Ejecutables (Build)

Si prefieres generar un archivo `.exe` o un binario de Linux que no requiera instalar Python:

- **Windows**: Ejecuta el archivo `build_exe.bat`.
- **Linux**: Ejecuta `./build_exe.sh` (asegúrate de darle permisos: `chmod +x build_exe.sh`).

El resultado aparecerá en la carpeta `dist/`.

---

## 🧱 Estructura del Proyecto

```text
Fungi-Traductor/
├── fungi_traductor/          # Núcleo del paquete Python
│   ├── assets/               # Recursos visuales (iconos, imágenes)
│   ├── controller/           # Controlador principal (Lógica MVC)
│   ├── model/                # Motores de traducción y voz
│   ├── view/                 # Diseño de la interfaz (Tkinter)
│   ├── __init__.py           # Inicializador de paquete
│   └── __main__.py           # Punto de entrada para ejecución modular
├── app.py                    # Wrapper para ejecución directa
├── build_exe.bat             # Script de compilación (Windows)
├── build_exe.sh              # Script de compilación (Linux)
├── pyproject.toml            # Configuración de empaquetado y pipx
├── requirements.txt          # Dependencias del proyecto
└── README.md                 # Documentación (este archivo)
```

---

## ⚠️ Requisitos y Solución de Problemas

- **Python**: Versión 3.10 o superior.
- **Linux**: Si encuentras errores de interfaz o de voz, instala las dependencias del sistema:
  - `sudo apt install python3-tk` (Interfaz gráfica)
  - `sudo apt install espeak` (Motor de voz)

---

## 🙏 Créditos

Este proyecto es posible gracias a la comunidad de código abierto:
- [Argos Translate](https://github.com/argosopentech/argos-translate)
- [langdetect](https://pypi.org/project/langdetect/)
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3)

Desarrollado con Amor❤️ por **fiumgi**.
