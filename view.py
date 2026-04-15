"""
view.py — Interfaz gráfica de Fungi Traductor.
Solo widgets y helpers visuales; sin lógica de negocio.
Patrón MVC · Fungi Traductor
"""
import tkinter as tk
from tkinter import ttk

# ── Tema ─────────────────────────────────────────────────────────────────────
BG      = "#0f1117"
PANEL   = "#1a1d27"
ACCENT  = "#4f8ef7"
ACCENT2 = "#6c63ff"
TEXT    = "#e8eaf0"
SUBTEXT = "#7a7f96"
BORDER  = "#2a2d3e"
SUCCESS = "#43e97b"
WARN    = "#f7c948"
ERR     = "#ff6b6b"

FONT_MONO  = ("Courier New", 12)
FONT_TITLE = ("Georgia", 20, "bold")
FONT_LABEL = ("Georgia", 10)
FONT_BTN   = ("Georgia", 11, "bold")
FONT_SMALL = ("Georgia",  9)

_STATUS_COLORS = {"info": SUBTEXT, "ok": SUCCESS, "warn": WARN, "error": ERR}


class TranslatorView(tk.Tk):
    """
    Ventana principal.
    Expone widgets públicos y métodos auxiliares para que el Controlador
    los use sin conocer los detalles de implementación de Tkinter.
    """

    def __init__(self):
        super().__init__()
        self.title("🍄 Fungi Traductor")
        self.geometry("960x620")
        self.minsize(740, 520)
        self.configure(bg=BG)
        self.resizable(True, True)

        # Tamaño de fuente actual (ajustable con Ctrl+Rueda)
        self._font_size = 12

        # Mapa interno label→code para los Combobox
        self._from_map: dict[str, str] = {}
        self._to_map:   dict[str, str] = {}

        # ── Layout raíz ───────────────────────────────────────────────────
        # Fila 0 encabezado        fija
        # Fila 1 separador         fija
        # Fila 2 barra de idiomas  fija
        # Fila 3 separador         fija
        # Fila 4 paneles de texto  CRECE ← weight=1
        # Fila 5 barra inferior    fija
        for row, w in enumerate([0, 0, 0, 0, 1, 0]):
            self.rowconfigure(row, weight=w)
        self.columnconfigure(0, weight=1)

        self._build_header()
        self._build_sep(row=1)
        self._build_lang_bar()
        self._build_sep(row=3)
        self._build_panels()
        self._build_bottom()

        # Foco inicial en el área de entrada
        self.after(100, self.input_text.focus_set)

    # ── Encabezado (fila 0) ───────────────────────────────────────────────
    def _build_header(self):
        f = tk.Frame(self, bg=BG, pady=16)
        f.grid(row=0, column=0, sticky="ew", padx=30)
        f.columnconfigure(0, weight=1)

        tk.Label(f, text="🍄 Fungi Traductor",
                 font=FONT_TITLE, bg=BG, fg=TEXT).grid(row=0, column=0, sticky="w")

        self.status_lbl = tk.Label(f, text="● iniciando…",
                                   font=FONT_SMALL, bg=BG, fg=SUBTEXT)
        self.status_lbl.grid(row=0, column=1, sticky="e")

    # ── Separadores ───────────────────────────────────────────────────────
    def _build_sep(self, row: int):
        tk.Frame(self, bg=BORDER, height=1).grid(
            row=row, column=0, sticky="ew", padx=20)

    # ── Barra de idiomas + controles (fila 2) ─────────────────────────────
    def _build_lang_bar(self):
        bar = tk.Frame(self, bg=BG, pady=8)
        bar.grid(row=2, column=0, sticky="ew", padx=30)

        # ── Selector DE ──────────────────────────────────────────────────
        tk.Label(bar, text="De:", font=FONT_LABEL,
                 bg=BG, fg=SUBTEXT).pack(side="left", padx=(0, 4))

        self.from_combo = ttk.Combobox(bar, state="readonly", width=20,
                                       font=FONT_LABEL)
        self._style_combo(self.from_combo)
        self.from_combo.pack(side="left", padx=(0, 4))

        # ── Botón SWAP ⇄ ──────────────────────────────────────────────────
        self.btn_swap = self._mk_btn(bar, "⇄", padx=8, pady=3,
                                     font=("Georgia", 14, "bold"), fg=ACCENT)
        self.btn_swap.pack(side="left", padx=6)

        # ── Selector A ───────────────────────────────────────────────────
        tk.Label(bar, text="A:", font=FONT_LABEL,
                 bg=BG, fg=SUBTEXT).pack(side="left", padx=(4, 4))

        self.to_combo = ttk.Combobox(bar, state="readonly", width=20,
                                     font=FONT_LABEL)
        self._style_combo(self.to_combo)
        self.to_combo.pack(side="left", padx=(0, 14))

        # ── Detectar idioma ───────────────────────────────────────────────
        self.btn_detect = self._mk_btn(bar, "🔍 Detectar", font=FONT_SMALL,
                                       padx=10, pady=4)
        self.btn_detect.pack(side="left", padx=4)

        # ── Derecha: TTS y Auto ───────────────────────────────────────────
        self.btn_tts = self._mk_btn(bar, "🔊 Leer", font=FONT_SMALL,
                                    padx=10, pady=4)
        self.btn_tts.pack(side="right", padx=4)

        self.btn_auto = self._mk_btn(bar, "⚡ Auto: OFF", font=FONT_SMALL,
                                     padx=10, pady=4)
        self.btn_auto.pack(side="right", padx=4)

    # ── Paneles de texto (fila 4) ─────────────────────────────────────────
    def _build_panels(self):
        panels = tk.Frame(self, bg=BG)
        panels.grid(row=4, column=0, sticky="nsew", padx=30, pady=(8, 4))

        panels.columnconfigure(0, weight=1)   # izquierdo crece
        panels.columnconfigure(1, weight=0)   # flecha fija
        panels.columnconfigure(2, weight=1)   # derecho crece
        panels.rowconfigure(0, weight=0)      # etiquetas fijas
        panels.rowconfigure(1, weight=1)      # texto crece

        # Etiquetas dinámicas (el controlador las actualiza al cambiar idioma)
        self.lbl_src = tk.Label(panels, text="Texto original",
                                font=FONT_LABEL, bg=BG, fg=SUBTEXT)
        self.lbl_src.grid(row=0, column=0, sticky="w", pady=(0, 2))

        self.lbl_dst = tk.Label(panels, text="Traducción",
                                font=FONT_LABEL, bg=BG, fg=SUBTEXT)
        self.lbl_dst.grid(row=0, column=2, sticky="w", pady=(0, 2))

        # ── Panel izquierdo ───────────────────────────────────────────────
        lf = tk.Frame(panels, bg=PANEL,
                      highlightbackground=BORDER, highlightthickness=1)
        lf.grid(row=1, column=0, sticky="nsew")
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

        self.input_text = tk.Text(
            lf, font=("Courier New", self._font_size),
            bg=PANEL, fg=TEXT, insertbackground=ACCENT,
            relief="flat", bd=0, padx=12, pady=10,
            wrap="word", selectbackground=ACCENT2, undo=True,
        )
        self.input_text.grid(row=0, column=0, sticky="nsew")

        sb_in = ttk.Scrollbar(lf, orient="vertical",
                              command=self.input_text.yview)
        sb_in.grid(row=0, column=1, sticky="ns")
        self.input_text.configure(yscrollcommand=sb_in.set)

        # ── Flecha central ────────────────────────────────────────────────
        tk.Label(panels, text="→", font=("Georgia", 20),
                 bg=BG, fg=SUBTEXT).grid(row=1, column=1, padx=8)

        # ── Panel derecho ─────────────────────────────────────────────────
        rf = tk.Frame(panels, bg=PANEL,
                      highlightbackground=BORDER, highlightthickness=1)
        rf.grid(row=1, column=2, sticky="nsew")
        rf.rowconfigure(0, weight=1)
        rf.columnconfigure(0, weight=1)

        self.output_text = tk.Text(
            rf, font=("Courier New", self._font_size),
            bg=PANEL, fg=SUCCESS, relief="flat", bd=0,
            padx=12, pady=10, wrap="word",
            state="disabled", selectbackground=ACCENT2,
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

        sb_out = ttk.Scrollbar(rf, orient="vertical",
                               command=self.output_text.yview)
        sb_out.grid(row=0, column=1, sticky="ns")
        self.output_text.configure(yscrollcommand=sb_out.set)

    # ── Barra inferior (fila 5) ───────────────────────────────────────────
    def _build_bottom(self):
        bottom = tk.Frame(self, bg=BG, pady=10)
        bottom.grid(row=5, column=0, sticky="ew", padx=30)
        bottom.columnconfigure(0, weight=1)

        self.char_lbl = tk.Label(bottom, text="0 caracteres",
                                 font=FONT_LABEL, bg=BG, fg=SUBTEXT)
        self.char_lbl.grid(row=0, column=0, sticky="w")

        # Etiqueta de idioma detectado (aparece junto al contador)
        self.detect_lbl = tk.Label(bottom, text="",
                                   font=FONT_SMALL, bg=BG, fg=WARN)
        self.detect_lbl.grid(row=0, column=1, sticky="w", padx=(12, 0))

        self.btn_clear = self._mk_btn(bottom, "Limpiar", padx=14, pady=6)
        self.btn_clear.grid(row=0, column=4, padx=(8, 0))

        self.btn_copy = self._mk_btn(bottom, "Copiar", padx=14, pady=6)
        self.btn_copy.grid(row=0, column=3, padx=(8, 0))

        self.btn_translate = tk.Button(
            bottom, text="Traducir  Ctrl+↵", font=FONT_BTN,
            bg=ACCENT, fg="#fff", activebackground=ACCENT2,
            activeforeground="#fff", relief="flat", bd=0,
            padx=20, pady=7, cursor="hand2",
        )
        self.btn_translate.grid(row=0, column=2, padx=(8, 0))

    # ── Helpers de construcción ───────────────────────────────────────────
    def _mk_btn(self, parent, text, *, font=FONT_BTN, fg=SUBTEXT,
                padx=16, pady=7, **kwargs):
        return tk.Button(
            parent, text=text, font=font,
            bg=PANEL, fg=fg, activebackground=BORDER,
            activeforeground=TEXT, relief="flat", bd=0,
            padx=padx, pady=pady, cursor="hand2", **kwargs
        )

    @staticmethod
    def _style_combo(cb: ttk.Combobox):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TCombobox",
                        fieldbackground=PANEL, background=PANEL,
                        foreground=TEXT, selectbackground=PANEL,
                        selectforeground=ACCENT, arrowcolor=SUBTEXT)

    # ── API pública (usada por el Controlador) ────────────────────────────

    def set_status(self, msg: str, level: str = "info"):
        color = _STATUS_COLORS.get(level, SUBTEXT)
        self.status_lbl.config(text=msg, fg=color)

    def set_output(self, text: str):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.config(state="disabled")

    def get_output(self) -> str:
        return self.output_text.get("1.0", "end-1c")

    def get_input(self) -> str:
        return self.input_text.get("1.0", "end-1c")

    def set_input(self, text: str):
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", text)

    def update_font_size(self, delta: int):
        self._font_size = max(8, min(28, self._font_size + delta))
        f = ("Courier New", self._font_size)
        self.input_text.configure(font=f)
        self.output_text.configure(font=f)

    def populate_from(self, items: list[tuple[str, str]]):
        """
        Rellena el combobox DE.
        items = [(code, display_name), ...]
        """
        self._from_map = {f"{n} ({c})": c for c, n in items}
        labels = sorted(self._from_map)
        self.from_combo["values"] = labels

    def populate_to(self, items: list[tuple[str, str]]):
        """
        Rellena el combobox A.
        items = [(code, display_name), ...]
        """
        self._to_map = {f"{n} ({c})": c for c, n in items}
        labels = sorted(self._to_map)
        self.to_combo["values"] = labels

    def select_from(self, code: str):
        lbl = next((l for l in self._from_map if f"({code})" in l), None)
        if lbl:
            self.from_combo.set(lbl)

    def select_to(self, code: str):
        lbl = next((l for l in self._to_map if f"({code})" in l), None)
        if lbl:
            self.to_combo.set(lbl)

    def get_from_code(self) -> str:
        return self._from_map.get(self.from_combo.get(), "en")

    def get_to_code(self) -> str:
        return self._to_map.get(self.to_combo.get(), "es")
