# 🍄 Fungi Traductor v2

Traductor offline con interfaz gráfica construido con **argostranslate** + **Tkinter**.  
Arquitectura MVC, redimensionable, multi-idioma.

---

## Instalación rápida

```bash
git clone https://github.com/fiumgi/Fungi-Traductor
cd Fungi-Traductor
pip install -r requirements.txt
python app.py
```

---

## Funcionalidades

| Función | Descripción |
|---|---|
| **Multi-idioma** | Comboboxes con todos los pares disponibles en Argos Translate |
| **Swap ⇄** | Intercambia idiomas y textos con un clic |
| **Scrollbars** | Barras de desplazamiento en ambos paneles de texto |
| **Auto-traducción** | Botón `⚡ Auto` con debounce de 700 ms |
| **Detección de idioma** | `🔍 Detectar` usa `langdetect` |
| **TTS** | `🔊 Leer` reproduce la traducción con `pyttsx3` |
| **Ajuste de fuente** | `Ctrl + Rueda` del ratón |
| **Logging** | Errores y eventos en `fungi_traductor.log` |
| **Redimensionable** | Todos los paneles crecen con la ventana |

---

## Estructura del proyecto (MVC)

```
fungi_traductor/
├── app.py            # Punto de entrada
├── model.py          # Lógica: traducción, TTS, detección de idioma
├── view.py           # Interfaz gráfica Tkinter
├── controller.py     # Conecta vista y modelo
├── requirements.txt
├── pyproject.toml    # Para distribución con pipx
├── build_exe.bat     # Empaquetar .exe en Windows
└── build_exe.sh      # Empaquetar binario en Linux/macOS
```

---

## Empaquetar como ejecutable

### Windows
```bat
build_exe.bat
```
Genera `dist/FungiTraductor.exe`.

### Linux / macOS
```bash
chmod +x build_exe.sh
./build_exe.sh
```
Genera `dist/FungiTraductor`.

---

## Instalar con pipx

```bash
# Desde el directorio del proyecto
pipx install .

# Ejecutar desde cualquier lugar
fungi-traductor
```

---

## Dependencias opcionales

```bash
pip install langdetect   # detección automática de idioma
pip install pyttsx3      # texto a voz (offline)
```

Si no están instaladas, las funciones correspondientes mostrarán un aviso pero **el traductor seguirá funcionando**.
