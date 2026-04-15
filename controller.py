"""
controller.py — Conecta la vista con el modelo.
Gestiona eventos, debounce, swap, TTS, detección y ajuste de fuente.
Patrón MVC · Fungi Traductor
"""
import threading


class TranslatorController:
    """
    El controlador no hereda de nada de tkinter.
    Recibe la vista y el modelo en el constructor y los conecta.
    """

    _DEBOUNCE_MS = 700   # ms de espera antes de auto-traducir

    def __init__(self, view, model):
        self.view  = view
        self.model = model

        self._auto_on       = False
        self._debounce_id   = None

        self._wire_events()
        self._boot()

    # ── Arranque ──────────────────────────────────────────────────────────

    def _boot(self):
        """Carga paquetes en hilo de fondo para no bloquear la UI."""
        threading.Thread(target=self._load_packages, daemon=True).start()

    def _load_packages(self):
        def on_st(msg, lvl):
            self.view.after(0, lambda m=msg, l=lvl: self.view.set_status(m, l))

        ok = self.model.init_packages(on_st)
        if not ok:
            return

        # Poblar combobox DE con idiomas únicos de origen
        pairs = self.model.available_pairs()
        from_items = self._unique_from(pairs)
        self.view.after(0, lambda: self._populate_ui(from_items, pairs))

        # Instalar par por defecto EN→ES
        ok2 = self.model.ensure_pair("en", "es", on_st)
        if ok2:
            self.model.ready = True
            self.view.after(0, lambda: self.view.set_status("● listo", "ok"))
        else:
            self.view.after(0, lambda: self.view.set_status("⚠ par EN→ES no disponible", "warn"))

    def _populate_ui(self, from_items, all_pairs):
        self.view.populate_from(from_items)
        self.view.select_from("en")
        # Poblar to_combo según from=en
        to_items = self._to_for("en", all_pairs)
        self.view.populate_to(to_items)
        self.view.select_to("es")
        self._update_panel_labels()

    @staticmethod
    def _unique_from(pairs) -> list[tuple[str, str]]:
        seen: dict[str, str] = {}
        for fc, _, fn, _ in pairs:
            seen[fc] = fn
        return list(seen.items())

    @staticmethod
    def _to_for(from_code: str, pairs) -> list[tuple[str, str]]:
        seen: dict[str, str] = {}
        for fc, tc, _, tn in pairs:
            if fc == from_code:
                seen[tc] = tn
        return list(seen.items())

    # ── Conexión de eventos ───────────────────────────────────────────────

    def _wire_events(self):
        v = self.view
        v.btn_translate.config(command=self.translate)
        v.btn_swap.config(command=self.swap)
        v.btn_clear.config(command=self.clear)
        v.btn_copy.config(command=self.copy)
        v.btn_detect.config(command=self.detect_language)
        v.btn_tts.config(command=self.speak)
        v.btn_auto.config(command=self.toggle_auto)

        # Teclado
        v.input_text.bind("<Control-Return>", lambda e: (self.translate(), "break")[1])
        v.input_text.bind("<KeyRelease>",      self._on_key)

        # Ajuste de fuente (Windows/Mac usa MouseWheel; Linux usa Button-4/5)
        for widget in (v.input_text, v.output_text):
            widget.bind("<Control-MouseWheel>", self._on_scroll)
            widget.bind("<Control-Button-4>",
                        lambda e: self.view.update_font_size(+1))
            widget.bind("<Control-Button-5>",
                        lambda e: self.view.update_font_size(-1))

        # Cambios en combos
        v.from_combo.bind("<<ComboboxSelected>>", self._on_from_changed)
        v.to_combo.bind("<<ComboboxSelected>>",   self._on_to_changed)

    # ── Traducción ────────────────────────────────────────────────────────

    def translate(self, event=None):
        if not self.model.ready:
            self.view.set_status("⏳ modelo aún cargando…", "warn")
            return "break"

        text = self.view.get_input().strip()
        if not text:
            return "break"

        from_code = self.view.get_from_code()
        to_code   = self.view.get_to_code()

        self.view.btn_translate.config(state="disabled", text="Traduciendo…")
        self.view.set_output("…")

        def work():
            def on_st(msg, lvl):
                self.view.after(0, lambda m=msg, l=lvl: self.view.set_status(m, l))

            ok = self.model.ensure_pair(from_code, to_code, on_st)
            if not ok:
                self.view.after(0, lambda: self.view.set_output(
                    "[Par de idiomas no disponible]"))
                self._reset_btn()
                return
            try:
                result = self.model.translate(text, from_code, to_code)
                self.view.after(0, lambda r=result: self.view.set_output(r))
                self.view.after(0, lambda: self.view.set_status("● listo", "ok"))
            except Exception as exc:
                self.view.after(0, lambda e=exc: self.view.set_output(f"[Error: {e}]"))
                self.view.after(0, lambda e=exc: self.view.set_status(f"✗ {e}", "error"))
            finally:
                self._reset_btn()

        threading.Thread(target=work, daemon=True).start()
        return "break"

    def _reset_btn(self):
        self.view.after(0, lambda: self.view.btn_translate.config(
            state="normal", text="Traducir  Ctrl+↵"))

    # ── Auto-traducción con debounce ──────────────────────────────────────

    def _on_key(self, event=None):
        # Actualizar contador
        n = len(self.view.get_input())
        self.view.char_lbl.config(
            text=f"{n} carácter{'es' if n != 1 else ''}")

        if self._auto_on:
            if self._debounce_id:
                self.view.after_cancel(self._debounce_id)
            self._debounce_id = self.view.after(self._DEBOUNCE_MS, self.translate)

    def toggle_auto(self):
        self._auto_on = not self._auto_on
        if self._auto_on:
            self.view.btn_auto.config(text="⚡ Auto: ON",  fg="#43e97b")
        else:
            self.view.btn_auto.config(text="⚡ Auto: OFF", fg="#7a7f96")
            if self._debounce_id:
                self.view.after_cancel(self._debounce_id)
                self._debounce_id = None

    # ── Swap de idiomas ───────────────────────────────────────────────────

    def swap(self):
        """Intercambia DE ↔ A y sus textos, luego re-traduce."""
        old_from = self.view.get_from_code()
        old_to   = self.view.get_to_code()
        src_text = self.view.get_input().strip()
        out_text = self.view.get_output().strip()

        # Remontar combobox DE con los idiomas de A (y viceversa)
        pairs = self.model.available_pairs()
        new_from_items = self._to_for(old_to, pairs)   # "from" pasa a ser el viejo "to"
        # Si no hay pares desde old_to, usar todos
        if not new_from_items:
            new_from_items = self._unique_from(pairs)

        self.view.populate_from(new_from_items)
        self.view.select_from(old_to)

        new_to_items = self._to_for(old_to, pairs)
        if not new_to_items:
            new_to_items = self._to_for(old_from, pairs)

        self.view.populate_to(self._to_for(old_to, pairs) or [(old_from, old_from)])
        self.view.select_to(old_from)

        # Intercambiar contenido de los paneles
        self.view.set_input(out_text)
        self.view.set_output(src_text)
        self._update_panel_labels()

        # Re-traducir si hay texto
        if out_text:
            self.translate()

    # ── Detección de idioma ───────────────────────────────────────────────

    def detect_language(self):
        text = self.view.get_input().strip()
        if not text:
            self.view.detect_lbl.config(text="")
            return

        code = self.model.detect(text)
        if code:
            current = self.view.get_from_code()
            icon    = "✓" if code == current else "⚠"
            self.view.detect_lbl.config(
                text=f"🔍 Detectado: {code}  {icon}")
        else:
            self.view.detect_lbl.config(
                text="🔍 langdetect no disponible — pip install langdetect")

    # ── TTS ───────────────────────────────────────────────────────────────

    def speak(self):
        text = self.view.get_output().strip()
        if not text:
            return
        to_code = self.view.get_to_code()
        self.view.set_status("🔊 leyendo…", "info")
        self.model.speak(text, to_code)
        self.view.after(2500, lambda: self.view.set_status("● listo", "ok"))

    # ── Limpiar / Copiar ──────────────────────────────────────────────────

    def clear(self):
        self.view.set_input("")
        self.view.set_output("")
        self.view.char_lbl.config(text="0 caracteres")
        self.view.detect_lbl.config(text="")

    def copy(self):
        text = self.view.get_output().strip()
        if text:
            self.view.clipboard_clear()
            self.view.clipboard_append(text)
            self.view.set_status("✔ copiado al portapapeles", "ok")
            self.view.after(2000, lambda: self.view.set_status("● listo", "ok"))

    # ── Cambios de idioma ─────────────────────────────────────────────────

    def _on_from_changed(self, event=None):
        from_code = self.view.get_from_code()
        pairs     = self.model.available_pairs()
        to_items  = self._to_for(from_code, pairs)
        if to_items:
            self.view.populate_to(to_items)
            # Mantener el mismo "to" si es posible
            current_to = self.view.get_to_code()
            if not self.view.select_to(current_to):
                self.view.select_to(to_items[0][0])
        self._update_panel_labels()
        self._ensure_pair_bg()

    def _on_to_changed(self, event=None):
        self._update_panel_labels()
        self._ensure_pair_bg()

    def _ensure_pair_bg(self):
        """Instala el par en background si no está disponible."""
        fc = self.view.get_from_code()
        tc = self.view.get_to_code()

        def install():
            def on_st(msg, lvl):
                self.view.after(0, lambda m=msg, l=lvl: self.view.set_status(m, l))
            ok = self.model.ensure_pair(fc, tc, on_st)
            if ok:
                self.model.ready = True
                self.view.after(0, lambda: self.view.set_status("● listo", "ok"))

        threading.Thread(target=install, daemon=True).start()

    def _update_panel_labels(self):
        self.view.lbl_src.config(text=f"Texto en {self.view.from_combo.get()}")
        self.view.lbl_dst.config(text=f"Traducción en {self.view.to_combo.get()}")

    # ── Ajuste de fuente ──────────────────────────────────────────────────

    def _on_scroll(self, event):
        delta = +1 if event.delta > 0 else -1
        self.view.update_font_size(delta)
