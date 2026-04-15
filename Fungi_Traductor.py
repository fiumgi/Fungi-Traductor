# Traductor ingles → español, usando Argos Translate
# Requiere: pip install argostranslate

import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Colores y fuentes
BG      = "#0f1117"
PANEL   = "#1a1d27"
ACCENT  = "#4f8ef7"
ACCENT2 = "#6c63ff"
TEXT    = "#e8eaf0"
SUBTEXT = "#7a7f96"
BORDER  = "#2a2d3e"
SUCCESS = "#43e97b"

FONT_BODY  = ("Georgia", 12)
FONT_MONO  = ("Courier New", 12)
FONT_TITLE = ("Georgia", 20, "bold")
FONT_LABEL = ("Georgia", 10)
FONT_BTN   = ("Georgia", 11, "bold")


class TranslatorApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Fungi Traductor · EN → ES")
        self.geometry("860x580")
        self.minsize(700, 480)
        self.configure(bg=BG)
        self.resizable(True, True)

        #    Configurar filas del root 
        # Fila 0: encabezado        → altura fija
        # Fila 1: separador         → altura fija
        # Fila 2: barra de idiomas  → altura fija
        # Fila 3: paneles de texto  → CRECE con la ventana  (weight=1)
        # Fila 4: barra inferior    → altura fija
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=1)   # <── se estira verticalmente
        self.rowconfigure(4, weight=0)

        # Columna única que ocupa todo el ancho disponible
        self.columnconfigure(0, weight=1)

        self._model_ready = False
        self._building_ui()
        self._load_model_async()

    #   UI 
    def _building_ui(self):

        #    Fila 0: Encabezado 
        header = tk.Frame(self, bg=BG, pady=18)
        header.grid(row=0, column=0, sticky="ew", padx=30)

        # El encabezado también usa columnconfigure para que su contenido
        # se distribuya correctamente al redimensionar
        header.columnconfigure(0, weight=1)

        tk.Label(header, text="Fungi Traductor",
                 font=FONT_TITLE, bg=BG, fg=TEXT).grid(row=0, column=0, sticky="w")

        self.status_dot = tk.Label(header, text="● cargando modelo…",
                                   font=FONT_LABEL, bg=BG, fg=SUBTEXT)
        self.status_dot.grid(row=0, column=1, sticky="e", pady=6)

        #    Fila 1: Separador 
        tk.Frame(self, bg=BORDER, height=1).grid(
            row=1, column=0, sticky="ew", padx=30)

        #    Fila 2: Barra de idiomas
        lang_bar = tk.Frame(self, bg=BG, pady=10)
        lang_bar.grid(row=2, column=0, sticky="ew", padx=30)

        lang_frame = tk.Frame(lang_bar, bg=PANEL, bd=0, relief="flat",
                               padx=12, pady=6)
        lang_frame.pack(side="left")

        tk.Label(lang_frame, text="English",  font=FONT_LABEL,
                 bg=PANEL, fg=ACCENT).pack(side="left", padx=6)
        tk.Label(lang_frame, text="→", font=("Georgia", 14),
                 bg=PANEL, fg=SUBTEXT).pack(side="left", padx=4)
        tk.Label(lang_frame, text="Español",  font=FONT_LABEL,
                 bg=PANEL, fg=SUCCESS).pack(side="left", padx=6)

        #    Fila 3: Paneles de texto (se redimensionan)
        panels = tk.Frame(self, bg=BG)
        panels.grid(row=3, column=0, sticky="nsew", padx=30, pady=(0, 10))

        # Las dos columnas de texto crecen igual; la columna central (flecha)
        # permanece fija.
        panels.columnconfigure(0, weight=1)   # panel izquierdo  ← crece
        panels.columnconfigure(1, weight=0)   # flecha central    ← fija
        panels.columnconfigure(2, weight=1)   # panel derecho     ← crece

        # La fila de los Text widgets crece verticalmente
        panels.rowconfigure(0, weight=0)      # etiquetas          ← fija
        panels.rowconfigure(1, weight=1)      # áreas de texto     ← crece

        # Etiquetas de columna
        tk.Label(panels, text="Texto en inglés", font=FONT_LABEL,
                 bg=BG, fg=SUBTEXT).grid(row=0, column=0, sticky="w", pady=(4, 2))
        tk.Label(panels, text="Traducción al español", font=FONT_LABEL,
                 bg=BG, fg=SUBTEXT).grid(row=0, column=2, sticky="w", pady=(4, 2))

        # Panel izquierdo
        left_frame = tk.Frame(panels, bg=PANEL,
                               highlightbackground=BORDER,
                               highlightthickness=1)
        left_frame.grid(row=1, column=0, sticky="nsew")
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)

        self.input_text = tk.Text(
            left_frame, font=FONT_MONO, bg=PANEL, fg=TEXT,
            insertbackground=ACCENT, relief="flat", bd=0,
            padx=14, pady=12, wrap="word",
            selectbackground=ACCENT2, selectforeground=TEXT
        )
        self.input_text.grid(row=0, column=0, sticky="nsew")
        self.input_text.bind("<Control-Return>", lambda e: self._translate())

        # Flecha central
        tk.Label(panels, text="→", font=("Georgia", 22),
                 bg=BG, fg=SUBTEXT).grid(row=1, column=1, padx=10)

        # Panel derecho
        right_frame = tk.Frame(panels, bg=PANEL,
                                highlightbackground=BORDER,
                                highlightthickness=1)
        right_frame.grid(row=1, column=2, sticky="nsew")
        right_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)

        self.output_text = tk.Text(
            right_frame, font=FONT_MONO, bg=PANEL, fg=SUCCESS,
            relief="flat", bd=0, padx=14, pady=12, wrap="word",
            state="disabled", selectbackground=ACCENT2
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

        #    Fila 4: Barra inferior
        bottom = tk.Frame(self, bg=BG, pady=12)
        bottom.grid(row=4, column=0, sticky="ew", padx=30)
        bottom.columnconfigure(0, weight=1)   # empuja los botones a la derecha

        self.char_label = tk.Label(bottom, text="0 caracteres",
                                   font=FONT_LABEL, bg=BG, fg=SUBTEXT)
        self.char_label.grid(row=0, column=0, sticky="w")

        # Botón Limpiar
        btn_clear = tk.Button(
            bottom, text="Limpiar", font=FONT_BTN,
            bg=PANEL, fg=SUBTEXT, activebackground=BORDER,
            activeforeground=TEXT, relief="flat", bd=0,
            padx=16, pady=7, cursor="hand2",
            command=self._clear
        )
        btn_clear.grid(row=0, column=3, padx=(8, 0))

        # Botón Copiar
        btn_copy = tk.Button(
            bottom, text="Copiar", font=FONT_BTN,
            bg=PANEL, fg=SUBTEXT, activebackground=BORDER,
            activeforeground=TEXT, relief="flat", bd=0,
            padx=16, pady=7, cursor="hand2",
            command=self._copy_result
        )
        btn_copy.grid(row=0, column=2, padx=(8, 0))

        # Botón Traducir
        self.btn_translate = tk.Button(
            bottom, text="Traducir ⌘↵", font=FONT_BTN,
            bg=ACCENT, fg="#ffffff", activebackground=ACCENT2,
            activeforeground="#ffffff", relief="flat", bd=0,
            padx=22, pady=8, cursor="hand2",
            command=self._translate
        )
        self.btn_translate.grid(row=0, column=1, padx=(8, 0))

        # Contador de caracteres
        self.input_text.bind("<KeyRelease>", self._update_counter)

    #    Modelo
    def _load_model_async(self):
        t = threading.Thread(target=self._load_model, daemon=True)
        t.start()

    def _load_model(self):
        try:
            import argostranslate.package
            import argostranslate.translate

            self._set_status("⟳ actualizando índice…", SUBTEXT)
            argostranslate.package.update_package_index()
            available = argostranslate.package.get_available_packages()

            pkg = next(
                (p for p in available
                 if p.from_code == "en" and p.to_code == "es"),
                None
            )
            if pkg is None:
                self._set_status("✗ paquete EN→ES no encontrado", "#ff6b6b")
                return

            installed = argostranslate.package.get_installed_packages()
            already = any(
                p.from_code == "en" and p.to_code == "es"
                for p in installed
            )
            if not already:
                self._set_status("⬇ descargando paquete EN→ES…", SUBTEXT)
                argostranslate.package.install_from_path(pkg.download())

            self._translate_fn = argostranslate.translate.translate
            self._model_ready = True
            self._set_status("● listo", SUCCESS)

        except Exception as e:
            self._set_status(f"✗ error: {e}", "#ff6b6b")

    def _set_status(self, msg, color):
        self.after(0, lambda: self.status_dot.config(text=msg, fg=color))

    #    Acciones 
    def _translate(self):
        if not self._model_ready:
            messagebox.showinfo("Espera", "El modelo aún se está cargando.")
            return
        src = self.input_text.get("1.0", "end").strip()
        if not src:
            return

        self.btn_translate.config(state="disabled", text="Traduciendo…")
        self._set_output("…")

        def work():
            try:
                result = self._translate_fn(src, "en", "es")
                self.after(0, lambda: self._set_output(result))
            except Exception as e:
                self.after(0, lambda: self._set_output(f"[Error: {e}]"))
            finally:
                self.after(0, lambda: self.btn_translate.config(
                    state="normal", text="Traducir ⌘↵"))

        threading.Thread(target=work, daemon=True).start()

    def _set_output(self, text):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.config(state="disabled")

    def _clear(self):
        self.input_text.delete("1.0", "end")
        self._set_output("")
        self._update_counter()

    def _copy_result(self):
        result = self.output_text.get("1.0", "end").strip()
        if result:
            self.clipboard_clear()
            self.clipboard_append(result)
            self._set_status("✔ copiado al portapapeles", SUCCESS)
            self.after(2000, lambda: self._set_status("● listo", SUCCESS))

    def _update_counter(self, *_):
        n = len(self.input_text.get("1.0", "end").strip())
        self.char_label.config(text=f"{n} carácter{'es' if n != 1 else ''}")


# Entry point
if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()