"""
view.py — Interfaz gráfica de Fungi Traductor.
Solo widgets y helpers visuales; sin lógica de negocio.
Patrón MVC · Fungi Traductor

OPTIMIZACIONES:
- Caché de estilos para evitar recrearlos
- Actualización eficiente de UI
- Bindings optimizados
"""
import os
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

def resource_path(relative_path):
    """Obtener ruta absoluta para recursos, funciona para dev, PyInstaller y pipx"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    
    # Subir tres niveles desde fungi_traductor/view/gui.py para llegar a la raíz del proyecto/paquete
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    full_path = os.path.join(base_path, relative_path)
    
    if os.path.exists(full_path):
        return full_path
    
    # Fallback al directorio de trabajo actual
    return os.path.join(os.path.abspath("."), relative_path)

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

        # Icono de ventana
        try:
            icon_path = resource_path(os.path.join("fungi_traductor", "assets", "icon.png"))
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.iconphoto(True, img)
        except Exception:
            pass

        # Estado
        self._font_size = 12
        self.auto_enabled = False
        
        # Cache para evitar actualizaciones innecesarias
        self._last_status = ""
        self._last_status_level = ""
        self._loading_active = False

        # Mapas idioma
        self._from_map: dict[str, str] = {}
        self._to_map:   dict[str, str] = {}
        self._voice_map: dict[str, str | None] = {}

        # Estilo global (evita recrearlo muchas veces)
        self._init_styles()

        # Layout
        for row, w in enumerate([0, 0, 0, 0, 0, 1, 0]):
            self.rowconfigure(row, weight=w)
        self.columnconfigure(0, weight=1)

        self._build_header()
        self._build_sep(row=1)
        self._build_lang_bar()
        self._build_progress_row()
        self._build_sep(row=4)
        self._build_panels()
        self._build_bottom()

        # Vincular eventos de teclado para mayor rapidez
        self.bind('<Control-Return>', lambda e: self._trigger_translate())
        self.bind('<Control-l>', lambda e: self.btn_clear.invoke())
        
        # También vincular directamente al widget de texto para asegurar que funcione con foco
        self.input_text.bind('<Control-Return>', lambda e: self._trigger_translate())
        self.input_text.bind('<Control-l>', lambda e: self.btn_clear.invoke())
        
        self.protocol("WM_DELETE_WINDOW", self._on_close_clicked)
        self._on_close_callback = None
        
        self.after(100, self.input_text.focus_set)

    # ── UI ───────────────────────────────────────────────────────────

    def _init_styles(self):
        """Inicializar estilos ttk una sola vez"""
        style = ttk.Style()
        
        # Forzar tema 'clam' para mejor soporte de colores personalizados
        if "clam" in style.theme_names():
            style.theme_use("clam")
        
        # Configuración base para Combobox
        style.configure(
            "TCombobox",
            fieldbackground=PANEL,
            foreground=TEXT,
            background=BORDER,
            arrowcolor=TEXT,
            bordercolor=BORDER,
            darkcolor=PANEL,
            lightcolor=PANEL,
        )
        
        # Mapa de estados para asegurar visibilidad constante
        style.map("TCombobox",
            fieldbackground=[("readonly", PANEL), ("disabled", PANEL), ("active", PANEL)],
            foreground=[("readonly", TEXT), ("disabled", SUBTEXT), ("active", TEXT)],
            arrowcolor=[("disabled", BORDER), ("active", ACCENT)]
        )

        style.configure(
            "Loading.Horizontal.TProgressbar",
            troughcolor=PANEL,
            background=ACCENT,
            bordercolor=BORDER,
            lightcolor=ACCENT,
            darkcolor=ACCENT,
        )

        # Estilo para Scrollbars
        style.configure(
            "TScrollbar",
            gripcount=0,
            background=PANEL,
            troughcolor=BG,
            bordercolor=BORDER,
            darkcolor=PANEL,
            lightcolor=PANEL,
            arrowcolor=SUBTEXT
        )
        style.map("TScrollbar",
            background=[("active", BORDER), ("disabled", PANEL)],
            arrowcolor=[("active", ACCENT)]
        )

    def _trigger_translate(self):
        """Trigger para traducción vía teclado"""
        if hasattr(self, 'btn_translate'):
            self.btn_translate.invoke()

    def _build_header(self):
        f = tk.Frame(self, bg=BG, pady=16)
        f.grid(row=0, column=0, sticky="ew", padx=30)
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=0)

        tk.Label(f, text="🍄 Fungi Traductor",
                 font=FONT_TITLE, bg=BG, fg=TEXT).grid(row=0, column=0, sticky="w")

        status_box = tk.Frame(f, bg=BG)
        status_box.grid(row=0, column=1, sticky="e")

        self.status_lbl = tk.Label(status_box, text="● iniciando…",
                                  font=FONT_SMALL, bg=BG, fg=SUBTEXT)
        self.status_lbl.pack(anchor="e")

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

    def _build_progress_row(self):
        row = tk.Frame(self, bg=BG)
        row.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 6))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=0)

        self.progress_row = row
        self.progress_track = ttk.Progressbar(
            row,
            mode="indeterminate",
            style="Loading.Horizontal.TProgressbar",
        )
        self.progress_track.grid(row=0, column=0, sticky="ew")

        self.progress_detail_lbl = tk.Label(
            row,
            text="",
            font=FONT_SMALL,
            bg=BG,
            fg=SUBTEXT,
            padx=12,
        )
        self.progress_detail_lbl.grid(row=0, column=1, sticky="e")
        self.progress_row.grid_remove()

    def _build_panels(self):
        panels = tk.Frame(self, bg=BG)
        panels.grid(row=5, column=0, sticky="nsew", padx=30, pady=(8, 4))

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
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        
        # Scrollbar para entrada
        in_scroll = ttk.Scrollbar(lf, orient="vertical", command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=in_scroll.set)
        in_scroll.pack(side="right", fill="y")
        self.input_text.pack(side="left", expand=True, fill="both")

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
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=BORDER,
        )
        
        # Scrollbar para salida
        out_scroll = ttk.Scrollbar(rf, orient="vertical", command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=out_scroll.set)
        out_scroll.pack(side="right", fill="y")
        self.output_text.pack(side="left", expand=True, fill="both")

    def _build_bottom(self):
        bottom = tk.Frame(self, bg=BG, pady=10)
        bottom.grid(row=6, column=0, sticky="ew", padx=30)

        self.char_lbl = tk.Label(bottom, text="0 caracteres",
                                font=FONT_LABEL, bg=BG, fg=SUBTEXT)
        self.char_lbl.pack(side="left")

        self.detect_lbl = tk.Label(bottom, text="",
                                  font=FONT_SMALL, bg=BG, fg=WARN)
        self.detect_lbl.pack(side="left", padx=10)

        tk.Label(bottom, text="Voz:", font=FONT_SMALL,
                 bg=BG, fg=SUBTEXT).pack(side="left", padx=(12, 4))

        self.voice_combo = ttk.Combobox(bottom, state="readonly", width=28,
                                        font=FONT_SMALL)
        self.voice_combo.pack(side="left")

        self.btn_clear = self._mk_btn(bottom, "Limpiar")
        self.btn_copy = self._mk_btn(bottom, "Copiar")
        self.btn_open = self._mk_btn(bottom, "📁 Abrir")
        self.btn_save = self._mk_btn(bottom, "💾 Guardar")

        self.btn_translate = tk.Button(
            bottom, text="Traducir  Ctrl+↵",
            bg=ACCENT, fg="#fff", relief="flat",
        )

        self.btn_translate.pack(side="right", padx=5)
        self.btn_save.pack(side="right", padx=5)
        self.btn_copy.pack(side="right", padx=5)
        self.btn_open.pack(side="right", padx=5)
        self.btn_clear.pack(side="right", padx=5)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _mk_btn(self, parent, text, *, font=FONT_BTN, fg=SUBTEXT,
                padx=16, pady=7):
        return tk.Button(
            parent, text=text, font=font,
            bg=PANEL, fg=fg, relief="flat",
            padx=padx, pady=pady, cursor="hand2"
        )

    # ── API CONTROLADOR ───────────────────────────────────────────────

    def set_status(self, msg: str, level: str = "info"):
        """Versión optimizada: solo actualiza si cambió"""
        if msg == self._last_status and level == self._last_status_level:
            return
        
        self._last_status = msg
        self._last_status_level = level
        color = _STATUS_COLORS.get(level, SUBTEXT)
        self.status_lbl.config(text=msg, fg=color)

    def set_loading(self, active: bool, mode: str = "indeterminate",
                    value: float | None = None, detail: str = ""):
        """Versión optimizada: evita cambios innecesarios"""
        if active == self._loading_active:
            # Solo actualizar detalles si está activo
            if active:
                self.progress_track.configure(mode=mode)
                self.progress_detail_lbl.config(text=detail)
                if mode != "indeterminate":
                    progress_value = 0 if value is None else value
                    self.progress_track.configure(value=progress_value, maximum=100)
            return
        
        self._loading_active = active
        self.progress_track.configure(mode=mode)
        self.progress_detail_lbl.config(text=detail)

        if active:
            if not self.progress_row.winfo_ismapped():
                self.progress_row.grid()
            if mode == "indeterminate":
                self.progress_track.start(10)
            else:
                progress_value = 0 if value is None else value
                self.progress_track.stop()
                self.progress_track.configure(value=progress_value, maximum=100)
        else:
            self.progress_track.stop()
            self.progress_track.configure(value=0, maximum=100)
            self.progress_detail_lbl.config(text="")
            if self.progress_row.winfo_ismapped():
                self.progress_row.grid_remove()

    def set_auto(self, enabled: bool):
        if enabled:
            self.btn_auto.config(text="⚡ Auto: ON", fg=SUCCESS)
        else:
            self.btn_auto.config(text="⚡ Auto: OFF", fg=SUBTEXT)
        self.auto_enabled = enabled

    def bind_auto_toggle(self, callback):
        self.btn_auto.config(command=callback)

    def bind_from_change(self, callback):
        self.from_combo.bind("<<ComboboxSelected>>", callback)

    def bind_to_change(self, callback):
        self.to_combo.bind("<<ComboboxSelected>>", callback)

    def bind_voice_change(self, callback):
        self.voice_combo.bind("<<ComboboxSelected>>", callback)

    def bind_input_change(self, callback):
        def wrapper(event):
            if self.input_text.edit_modified():
                callback(event)
                self.input_text.edit_modified(False)
        self.input_text.bind("<<Modified>>", wrapper)

    def bind_close(self, callback):
        self._on_close_callback = callback

    def _on_close_clicked(self):
        if self._on_close_callback:
            self._on_close_callback()
        else:
            self.destroy()

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

    def ask_open_file(self) -> str | None:
        """Abre un diálogo para seleccionar un archivo o imagen"""
        from tkinter import filedialog
        return filedialog.askopenfilename(
            title="Abrir archivo o imagen",
            filetypes=[
                ("Archivos soportados", "*.txt *.pdf *.docx *.odt *.png *.jpg *.jpeg"),
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("Archivos de texto", "*.txt"),
                ("Archivos PDF", "*.pdf"),
                ("Archivos Word", "*.docx"),
                ("Archivos OpenDocument", "*.odt"),
                ("Todos los archivos", "*.*")
            ]
        )

    def ask_save_file(self, default_name: str = "traduccion") -> str | None:
        """Abre un diálogo para guardar la traducción en múltiples formatos"""
        from tkinter import filedialog
        return filedialog.asksaveasfilename(
            title="Guardar traducción",
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[
                ("Archivo de texto", "*.txt"),
                ("Archivo PDF", "*.pdf"),
                ("Documento Word", "*.docx"),
                ("Documento OpenDocument", "*.odt")
            ]
        )

    def get_output(self) -> str:
        return self.output_text.get("1.0", "end-1c")

    def set_char_count(self, count: int):
        """Actualiza el contador de caracteres en la parte inferior"""
        self.char_lbl.config(text=f"{count} caracteres")

    def populate_from(self, items: list[tuple[str, str]]):
        current = self.from_combo.get()
        self._from_map = {f"{name} ({code})": code for code, name in items}
        values = sorted(self._from_map)
        self.from_combo["values"] = values
        if current in self._from_map:
            self.from_combo.set(current)
        else:
            self.from_combo.set("")

    def populate_to(self, items: list[tuple[str, str]]):
        current = self.to_combo.get()
        self._to_map = {f"{name} ({code})": code for code, name in items}
        values = sorted(self._to_map)
        self.to_combo["values"] = values
        if current in self._to_map:
            self.to_combo.set(current)
        else:
            self.to_combo.set("")

    def populate_voices(self, items: list[tuple[str | None, str]]):
        current = self.voice_combo.get()
        values = [label for _, label in items]
        self._voice_map = {label: voice_id for voice_id, label in items}
        self.voice_combo["values"] = values
        if current in self._voice_map:
            self.voice_combo.set(current)
        elif values:
            self.voice_combo.set(values[0])
        else:
            self.voice_combo.set("")

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

    def get_selected_voice_id(self) -> str | None:
        return self._voice_map.get(self.voice_combo.get())

    def select_voice(self, voice_id: str | None):
        label = next((item for item, mapped_id in self._voice_map.items() if mapped_id == voice_id), None)
        if label:
            self.voice_combo.set(label)
