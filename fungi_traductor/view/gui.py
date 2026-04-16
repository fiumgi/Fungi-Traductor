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

    def __init__(self):
        super().__init__()
        self.title("🍄 Fungi Traductor")
        self.geometry("960x620")
        self.minsize(740, 520)
        self.configure(bg=BG)
        self.resizable(True, True)

        # Estado
        self._font_size = 12
        self.auto_enabled = False

        # Mapas idioma
        self._from_map: dict[str, str] = {}
        self._to_map:   dict[str, str] = {}

        # Estilo global (evita recrearlo muchas veces)
        self._init_styles()

        # Layout
        for row, w in enumerate([0, 0, 0, 0, 1, 0]):
            self.rowconfigure(row, weight=w)
        self.columnconfigure(0, weight=1)

        self._build_header()
        self._build_sep(row=1)
        self._build_lang_bar()
        self._build_sep(row=3)
        self._build_panels()
        self._build_bottom()

        self.after(100, self.input_text.focus_set)

    # ── UI ───────────────────────────────────────────────────────────────

    def _init_styles(self):
        style = ttk.Style()
        style.configure(
            "TCombobox",
            fieldbackground=PANEL,
            foreground=TEXT,
            background=PANEL
        )

    def _build_header(self):
        f = tk.Frame(self, bg=BG, pady=16)
        f.grid(row=0, column=0, sticky="ew", padx=30)
        f.columnconfigure(0, weight=1)

        tk.Label(f, text="🍄 Fungi Traductor",
                 font=FONT_TITLE, bg=BG, fg=TEXT).grid(row=0, column=0, sticky="w")

        self.status_lbl = tk.Label(f, text="● iniciando…",
                                  font=FONT_SMALL, bg=BG, fg=SUBTEXT)
        self.status_lbl.grid(row=0, column=1, sticky="e")

    def _build_sep(self, row: int):
        tk.Frame(self, bg=BORDER, height=1).grid(
            row=row, column=0, sticky="ew", padx=20)

    def _build_lang_bar(self):
        bar = tk.Frame(self, bg=BG, pady=8)
        bar.grid(row=2, column=0, sticky="ew", padx=30)

        tk.Label(bar, text="De:", font=FONT_LABEL,
                 bg=BG, fg=SUBTEXT).pack(side="left", padx=(0, 4))

        self.from_combo = ttk.Combobox(bar, state="readonly", width=20,
                                      font=FONT_LABEL)
        self.from_combo.pack(side="left", padx=(0, 4))

        self.btn_swap = self._mk_btn(bar, "⇄", padx=8, pady=3,
                                    font=("Georgia", 14, "bold"), fg=ACCENT)
        self.btn_swap.pack(side="left", padx=6)

        tk.Label(bar, text="A:", font=FONT_LABEL,
                 bg=BG, fg=SUBTEXT).pack(side="left", padx=(4, 4))

        self.to_combo = ttk.Combobox(bar, state="readonly", width=20,
                                    font=FONT_LABEL)
        self.to_combo.pack(side="left", padx=(0, 14))

        self.btn_detect = self._mk_btn(bar, "🔍 Detectar",
                                      font=FONT_SMALL, padx=10, pady=4)
        self.btn_detect.pack(side="left", padx=4)

        self.btn_tts = self._mk_btn(bar, "🔊 Leer",
                                   font=FONT_SMALL, padx=10, pady=4)
        self.btn_tts.pack(side="right", padx=4)

        self.btn_auto = self._mk_btn(bar, "⚡ Auto: OFF",
                                    font=FONT_SMALL, padx=10, pady=4)
        self.btn_auto.pack(side="right", padx=4)

    def _build_panels(self):
        panels = tk.Frame(self, bg=BG)
        panels.grid(row=4, column=0, sticky="nsew", padx=30, pady=(8, 4))

        panels.columnconfigure(0, weight=1)
        panels.columnconfigure(1, weight=0)
        panels.columnconfigure(2, weight=1)
        panels.rowconfigure(1, weight=1)

        self.lbl_src = tk.Label(panels, text="Texto original",
                               font=FONT_LABEL, bg=BG, fg=SUBTEXT)
        self.lbl_dst = tk.Label(panels, text="Traducción",
                               font=FONT_LABEL, bg=BG, fg=SUBTEXT)

        self.lbl_src.grid(row=0, column=0, sticky="w")
        self.lbl_dst.grid(row=0, column=2, sticky="w")

        lf = tk.Frame(panels, bg=PANEL,
                      highlightbackground=BORDER, highlightthickness=1)
        lf.grid(row=1, column=0, sticky="nsew")

        self.input_text = tk.Text(
            lf, font=("Courier New", self._font_size),
            bg=PANEL, fg=TEXT, insertbackground=ACCENT,
            relief="flat", padx=12, pady=10,
            wrap="word", undo=True,
        )
        self.input_text.pack(expand=True, fill="both")

        tk.Label(panels, text="→", font=("Georgia", 20),
                 bg=BG, fg=SUBTEXT).grid(row=1, column=1)

        rf = tk.Frame(panels, bg=PANEL,
                      highlightbackground=BORDER, highlightthickness=1)
        rf.grid(row=1, column=2, sticky="nsew")

        self.output_text = tk.Text(
            rf, font=("Courier New", self._font_size),
            bg=PANEL, fg=SUCCESS, state="disabled",
            relief="flat", padx=12, pady=10,
            wrap="word",
        )
        self.output_text.pack(expand=True, fill="both")

    def _build_bottom(self):
        bottom = tk.Frame(self, bg=BG, pady=10)
        bottom.grid(row=5, column=0, sticky="ew", padx=30)

        self.char_lbl = tk.Label(bottom, text="0 caracteres",
                                font=FONT_LABEL, bg=BG, fg=SUBTEXT)
        self.char_lbl.pack(side="left")

        self.detect_lbl = tk.Label(bottom, text="",
                                  font=FONT_SMALL, bg=BG, fg=WARN)
        self.detect_lbl.pack(side="left", padx=10)

        self.btn_clear = self._mk_btn(bottom, "Limpiar")
        self.btn_copy = self._mk_btn(bottom, "Copiar")

        self.btn_translate = tk.Button(
            bottom, text="Traducir  Ctrl+↵",
            bg=ACCENT, fg="#fff", relief="flat",
        )

        self.btn_translate.pack(side="right", padx=5)
        self.btn_copy.pack(side="right", padx=5)
        self.btn_clear.pack(side="right", padx=5)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _mk_btn(self, parent, text, *, font=FONT_BTN, fg=SUBTEXT,
                padx=16, pady=7):
        return tk.Button(
            parent, text=text, font=font,
            bg=PANEL, fg=fg, relief="flat",
            padx=padx, pady=pady, cursor="hand2"
        )

    # ── API CONTROLADOR ───────────────────────────────────────────────────

    def set_status(self, msg: str, level: str = "info"):
        color = _STATUS_COLORS.get(level, SUBTEXT)
        self.status_lbl.config(text=msg, fg=color)

    def set_auto(self, enabled: bool):
        self.auto_enabled = enabled
        if enabled:
            self.btn_auto.config(text="⚡ Auto: ON", fg=SUCCESS)
        else:
            self.btn_auto.config(text="⚡ Auto: OFF", fg=SUBTEXT)

    def bind_auto_toggle(self, callback):
        self.btn_auto.config(command=callback)

    def bind_input_change(self, callback):
        def wrapper(event):
            if self.input_text.edit_modified():
                callback(event)
                self.input_text.edit_modified(False)
        self.input_text.bind("<<Modified>>", wrapper)

    def get_input(self):
        return self.input_text.get("1.0", "end-1c")

    def set_input(self, text: str):
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", text)

    def set_output(self, text: str):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.config(state="disabled")

    def get_output(self) -> str:
        return self.output_text.get("1.0", "end-1c")

    def populate_from(self, items: list[tuple[str, str]]):
        self._from_map = {f"{name} ({code})": code for code, name in items}
        self.from_combo["values"] = sorted(self._from_map)

    def populate_to(self, items: list[tuple[str, str]]):
        self._to_map = {f"{name} ({code})": code for code, name in items}
        self.to_combo["values"] = sorted(self._to_map)

    def select_from(self, code: str | None):
        if not code:
            return
        label = next((item for item in self._from_map if item.endswith(f"({code})")), None)
        if label:
            self.from_combo.set(label)

    def select_to(self, code: str | None):
        if not code:
            return
        label = next((item for item in self._to_map if item.endswith(f"({code})")), None)
        if label:
            self.to_combo.set(label)

    def get_from_code(self) -> str:
        return self._from_map.get(self.from_combo.get(), "en")

    def get_to_code(self) -> str:
        return self._to_map.get(self.to_combo.get(), "es")
