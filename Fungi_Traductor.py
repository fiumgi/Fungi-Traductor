"""
Traductor EN → ES usando Argos Translate
Requiere: pip install argostranslate
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading


# ── Colores y fuentes ──────────────────────────────────────────────────────────
BG        = "#0f1117"
PANEL     = "#1a1d27"
ACCENT    = "#4f8ef7"
ACCENT2   = "#6c63ff"
TEXT      = "#e8eaf0"
SUBTEXT   = "#7a7f96"
BORDER    = "#2a2d3e"
SUCCESS   = "#43e97b"
FONT_BODY = ("Georgia", 12)
FONT_MONO = ("Courier New", 12)
FONT_TITLE= ("Georgia", 20, "bold")
FONT_LABEL= ("Georgia", 10)
FONT_BTN  = ("Georgia", 11, "bold")


class TranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fungi Traductor  ·  EN → ES")
        self.geometry("860x580")
        self.minsize(700, 480)
        self.configure(bg=BG)
        self.resizable(True, True)

        self._model_ready = False
        self._building_ui()
        self._load_model_async()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _building_ui(self):
        # ── Encabezado ──
        header = tk.Frame(self, bg=BG, pady=18)
        header.pack(fill="x", padx=30)

        tk.Label(header, text="Fungi Traductor",
                 font=FONT_TITLE, bg=BG, fg=TEXT).pack(side="left")

        self.status_dot = tk.Label(header, text="●  cargando modelo…",
                                   font=FONT_LABEL, bg=BG, fg=SUBTEXT)
        self.status_dot.pack(side="right", pady=6)

        # ── Separador ──
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30)

        # ── Etiquetas de idioma ──
        lang_bar = tk.Frame(self, bg=BG, pady=10)
        lang_bar.pack(fill="x", padx=30)

        lang_frame = tk.Frame(lang_bar, bg=PANEL, bd=0, relief="flat",
                              padx=12, pady=6)
        lang_frame.pack(side="left")
        tk.Label(lang_frame, text="English", font=FONT_LABEL,
                 bg=PANEL, fg=ACCENT).pack(side="left", padx=6)
        tk.Label(lang_frame, text="→", font=("Georgia", 14),
                 bg=PANEL, fg=SUBTEXT).pack(side="left", padx=4)
        tk.Label(lang_frame, text="Español", font=FONT_LABEL,
                 bg=PANEL, fg=SUCCESS).pack(side="left", padx=6)

        # ── Paneles de texto ──
        panels = tk.Frame(self, bg=BG)
        panels.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        panels.columnconfigure(0, weight=1)
        panels.columnconfigure(2, weight=1)
        panels.rowconfigure(1, weight=1)

        # etiquetas
        tk.Label(panels, text="Texto en inglés", font=FONT_LABEL,
                 bg=BG, fg=SUBTEXT).grid(row=0, column=0, sticky="w", pady=(4,2))
        tk.Label(panels, text="Traducción al español", font=FONT_LABEL,
                 bg=BG, fg=SUBTEXT).grid(row=0, column=2, sticky="w", pady=(4,2))

        # panel izquierdo
        left_frame = tk.Frame(panels, bg=PANEL,
                              highlightbackground=BORDER,
                              highlightthickness=1)
        left_frame.grid(row=1, column=0, sticky="nsew")

        self.input_text = tk.Text(
            left_frame, font=FONT_MONO, bg=PANEL, fg=TEXT,
            insertbackground=ACCENT, relief="flat", bd=0,
            padx=14, pady=12, wrap="word",
            selectbackground=ACCENT2, selectforeground=TEXT
        )
        self.input_text.pack(fill="both", expand=True)
        self.input_text.bind("<Control-Return>", lambda e: self._translate())

        # flecha central
        tk.Label(panels, text="→", font=("Georgia", 22),
                 bg=BG, fg=SUBTEXT).grid(row=1, column=1, padx=10)

        # panel derecho
        right_frame = tk.Frame(panels, bg=PANEL,
                               highlightbackground=BORDER,
                               highlightthickness=1)
        right_frame.grid(row=1, column=2, sticky="nsew")

        self.output_text = tk.Text(
            right_frame, font=FONT_MONO, bg=PANEL, fg=SUCCESS,
            relief="flat", bd=0, padx=14, pady=12, wrap="word",
            state="disabled", selectbackground=ACCENT2
        )
        self.output_text.pack(fill="both", expand=True)

        # ── Barra inferior ──
        bottom = tk.Frame(self, bg=BG, pady=12)
        bottom.pack(fill="x", padx=30)

        self.char_label = tk.Label(bottom, text="0 caracteres",
                                   font=FONT_LABEL, bg=BG, fg=SUBTEXT)
        self.char_label.pack(side="left")

        # botón limpiar
        btn_clear = tk.Button(
            bottom, text="Limpiar", font=FONT_BTN,
            bg=PANEL, fg=SUBTEXT, activebackground=BORDER,
            activeforeground=TEXT, relief="flat", bd=0,
            padx=16, pady=7, cursor="hand2",
            command=self._clear
        )
        btn_clear.pack(side="right", padx=(8, 0))

        # botón copiar
        btn_copy = tk.Button(
            bottom, text="Copiar", font=FONT_BTN,
            bg=PANEL, fg=SUBTEXT, activebackground=BORDER,
            activeforeground=TEXT, relief="flat", bd=0,
            padx=16, pady=7, cursor="hand2",
            command=self._copy_result
        )
        btn_copy.pack(side="right", padx=(8, 0))

        # botón principal
        self.btn_translate = tk.Button(
            bottom, text="Traducir  ⌘↵", font=FONT_BTN,
            bg=ACCENT, fg="#ffffff", activebackground=ACCENT2,
            activeforeground="#ffffff", relief="flat", bd=0,
            padx=22, pady=8, cursor="hand2",
            command=self._translate
        )
        self.btn_translate.pack(side="right")

        # bind contador
        self.input_text.bind("<KeyRelease>", self._update_counter)

    # ── Modelo ────────────────────────────────────────────────────────────────

    def _load_model_async(self):
        t = threading.Thread(target=self._load_model, daemon=True)
        t.start()

    def _load_model(self):
        try:
            import argostranslate.package
            import argostranslate.translate

            self._set_status("⟳  actualizando índice…", SUBTEXT)
            argostranslate.package.update_package_index()

            available = argostranslate.package.get_available_packages()
            pkg = next(
                (p for p in available
                 if p.from_code == "en" and p.to_code == "es"),
                None
            )

            if pkg is None:
                self._set_status("✗  paquete EN→ES no encontrado", "#ff6b6b")
                return

            installed = argostranslate.package.get_installed_packages()
            already = any(
                p.from_code == "en" and p.to_code == "es"
                for p in installed
            )

            if not already:
                self._set_status("⬇  descargando paquete EN→ES…", SUBTEXT)
                argostranslate.package.install_from_path(pkg.download())

            self._translate_fn = argostranslate.translate.translate
            self._model_ready  = True
            self._set_status("●  listo", SUCCESS)

        except Exception as e:
            self._set_status(f"✗  error: {e}", "#ff6b6b")

    def _set_status(self, msg, color):
        self.after(0, lambda: self.status_dot.config(text=msg, fg=color))

    # ── Acciones ──────────────────────────────────────────────────────────────

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
                    state="normal", text="Traducir  ⌘↵"))

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
            self._set_status("✔  copiado al portapapeles", SUCCESS)
            self.after(2000, lambda: self._set_status("●  listo", SUCCESS))

    def _update_counter(self, *_):
        n = len(self.input_text.get("1.0", "end").strip())
        self.char_label.config(text=f"{n} carácter{'es' if n != 1 else ''}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()
