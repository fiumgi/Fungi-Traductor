# 🍄 Fungi Traductor

![Fungi Traductor Icon](fungi_traductor/assets/icon.png)

Traductor offline de alto rendimiento con interfaz gráfica moderna, diseñado para ofrecer privacidad total, velocidad y una experiencia de usuario fluida. Basado en el motor de **Argos Translate**, permite traducir textos sin conexión a internet entre múltiples idiomas.

---

## ✨ Características Premium

- **🌐 100% Offline**: Privacidad garantizada. Tus textos nunca salen de tu equipo.
- **⚡ Auto-Traducción Inteligente**: Traduce en tiempo real mientras escribes, ahora con **Caché de resultados** para respuestas instantáneas.
- **🔊 Lectura por Voz (TTS)**: Motor de voz integrado con soporte para múltiples idiomas y protección contra hilos concurrentes.
- **🔍 Detección Automática**: Identifica el idioma de entrada automáticamente usando `langdetect` y una base de datos de pistas optimizada.
- **⌨️ Atajos de Teclado**: 
  - `Ctrl + Enter`: Traducir manualmente.
  - `Ctrl + L`: Limpiar paneles de texto.
- **🎨 Interfaz Adaptativa**: Diseño oscuro (Dark Mode) con **High DPI Awareness** para máxima nitidez en todas las pantallas.
- **🚀 Rendimiento Optimizado**:
  - **Cancelación en Vuelo**: Cancela hilos de traducción antiguos al seguir escribiendo para ahorrar CPU.

---

## 🚀 Instalación y Uso

### 1. Vía pipx (Recomendado)
Para usar el traductor como una aplicación global en tu sistema:

```bash
pipx install git+https://github.com/fiumgi/Fungi-Traductor.git
```

Luego ejecuta desde cualquier lugar:
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
│   ├── controller/           # Controlador (Lógica de eventos)
│   ├── model/                # Modelos de traducción, TTS y hints
│   ├── view/                 # Interfaz gráfica (Tkinter)
│   ├── __init__.py           # Inicializador de paquete
│   └── __main__.py           # Punto de entrada para ejecución modular
├── app.py                    # Script de inicio rápido (wrapper)
├── build_exe.bat             # Script de construcción (Windows)
├── build_exe.sh              # Script de construcción (Linux)
├── pyproject.toml            # Configuración de empaquetado y pipx
├── requirements.txt          # Dependencias del proyecto
└── README.md                 # Documentación del proyecto
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
- [platformdirs](https://github.com/platformdirs/platformdirs)
Desarrollado con Amor❤️ por **fiumgi**.
