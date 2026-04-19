import threading
from queue import Empty, Queue
from threading import Lock
from collections import defaultdict


class TranslatorController:
    def __init__(self, view, model):
        self.view = view
        self.model = model
        self._pairs_by_source = {}
        self._suspend_auto = False
        self._ui_queue = Queue()
        self._init_state = "idle"
        
        # Cache para evitar búsquedas repetidas
        self._voice_cache = {}
        self._voice_cache_lang = None
        self._last_translate_text = ""
        self._translate_scheduled = False
        self._translate_timer = None
        self._current_translate_evt = None  # Evento para cancelar hilos antiguos
        
        # Lock para operaciones thread-safe
        self._lock = Lock()

        # Conectar botones
        self.view.btn_translate.config(command=self.translate)
        self.view.btn_detect.config(command=self._detect_language_async)
        self.view.btn_tts.config(command=self._text_to_speech_async)
        self.view.btn_swap.config(command=self.swap_languages)
        self.view.btn_clear.config(command=self.clear)
        self.view.btn_copy.config(command=self.copy)
        self.view.bind_auto_toggle(self.toggle_auto)
        self.view.bind_input_change(self._on_input_change)
        self.view.bind_from_change(self._on_from_change)
        self.view.bind_to_change(self._on_to_change)
        self.view.bind_voice_change(self._on_voice_change)
        self.view.bind_close(self.on_close)

    # ── INICIALIZACIÓN ─────────────────────────────────────────

    def _set_status(self, msg, level="info"):
        self._ui_queue.put(("status", msg, level))

    def _set_loading(self, active, mode="indeterminate", value=None, detail=""):
        self._ui_queue.put(("loading", active, mode, value, detail))

    def _apply_status(self, msg, level="info"):
        self.view.set_status(msg, level)

    def initialize(self):
        self._init_state = "loading"
        self._set_loading(True, mode="determinate", value=5, detail="Preparando inicio…")
        self._set_status("● actualizando índice de paquetes…", "info")
        self._schedule_ui_queue_poll()
        threading.Thread(target=self._initialize_async, daemon=True).start()

    def _initialize_async(self):
        # Inicializar modelo (Argos packages)
        if not self.model.init_packages(self._on_init_status, self._on_init_progress):
            self._ui_queue.put(("init_done", False))
            return

        # Poblar idiomas
        self._ui_queue.put(("populate",))
        self._ui_queue.put(("init_done", True))

    def _on_init_status(self, msg, level="info"):
        if level == "warn":
            self._init_state = "offline"
        elif level == "error":
            self._init_state = "error"
        self._set_status(msg, level)

    def _on_init_progress(self, _stage, value, detail):
        self._set_loading(True, mode="determinate", value=value, detail=detail)

    def _on_install_progress(self, _stage, value, detail):
        self._set_loading(True, mode="determinate", value=value, detail=detail)

    def _schedule_ui_queue_poll(self):
        self.view.after(50, self._drain_ui_queue)  # 50ms en lugar de 100ms para más fluidez

    def _drain_ui_queue(self):
        try:
            # Procesar múltiples tareas en una sola pasada
            while True:
                task = self._ui_queue.get_nowait()
                kind = task[0]

                if kind == "status":
                    _, msg, level = task
                    self._apply_status(msg, level)
                elif kind == "loading":
                    _, active, mode, value, detail = task
                    self.view.set_loading(active, mode=mode, value=value, detail=detail)
                elif kind == "populate":
                    self._populate_language_lists()
                elif kind == "init_done":
                    _, success = task
                    self._finish_initialize(success)
                elif kind == "toggle_ui":
                    _, enabled = task
                    self._toggle_ui(enabled)
        except Empty:
            pass
        finally:
            self._schedule_ui_queue_poll()

    def _finish_initialize(self, success):
        self.view.set_loading(False)
        if not success:
            return

        if self._init_state == "offline":
            self._apply_status("⚠ sin conexión — usando paquetes locales", "warn")
        elif self._init_state != "error":
            self._init_state = "ready"
            self._apply_status("● listo", "ok")
        
        self._toggle_ui(True)

    def _populate_language_lists(self):
        """Versión optimizada con mejor gestión de memoria"""
        pairs = self.model.available_pairs()
        from_langs = {}
        pairs_by_source = defaultdict(dict)  # Más eficiente que setdefault

        for src_code, tgt_code, src_name, tgt_name in pairs:
            from_langs[src_code] = src_name
            pairs_by_source[src_code][tgt_code] = tgt_name

        # Cache directo sin lambda innecesarios
        self._pairs_by_source = {}
        for src_code, targets in pairs_by_source.items():
            self._pairs_by_source[src_code] = sorted(
                targets.items(), 
                key=lambda item: (item[1].lower(), item[0])
            )
        
        from_items = sorted(from_langs.items(), key=lambda item: (item[1].lower(), item[0]))
        self.view.populate_from(from_items)

        if not from_items:
            self.view.populate_to([])
            if self._init_state not in {"error", "offline"}:
                self._set_status("● no hay idiomas disponibles", "warn")
            return

        default_source = "es" if "es" in self._pairs_by_source else from_items[0][0]
        self.view.select_from(default_source)
        self._refresh_targets(preferred_code="en")

    def _refresh_targets(self, preferred_code=None):
        src = self.view.get_from_code()
        targets = self._pairs_by_source.get(src, [])

        self.view.populate_to(targets)
        if not targets:
            self._set_status(f"● no hay destinos disponibles para {src}", "warn")
            return

        current_code = self.view.get_to_code()
        available_codes = {code for code, _ in targets}

        if preferred_code in available_codes:
            selected_code = preferred_code
        elif current_code in available_codes:
            selected_code = current_code
        else:
            selected_code = targets[0][0]

        self.view.select_to(selected_code)
        self._refresh_voices()

    def _refresh_voices(self, preferred_voice_id=None):
        """Versión mejorada con caching de voces"""
        lang_code = self.view.get_to_code()
        
        # Cache de voces para evitar recargarlas si el idioma no cambió
        if self._voice_cache_lang != lang_code:
            self._voice_cache_lang = lang_code
            voice_items = [(None, "Automática")]
            voice_items.extend(self.model.list_voices(lang_code))
            self._voice_cache = voice_items
        
        self.view.populate_voices(self._voice_cache)
        
        current_voice_id = self.view.get_selected_voice_id()
        if preferred_voice_id is not None:
            self.view.select_voice(preferred_voice_id)
        elif current_voice_id is not None:
            self.view.select_voice(current_voice_id)
        else:
            self.view.select_voice(None)

    def _on_from_change(self, _event=None):
        previous_target = self.view.get_to_code()
        self._refresh_targets(preferred_code=previous_target)
        if self.view.auto_enabled and self.view.get_input().strip():
            self._schedule_translate()

    def _on_to_change(self, _event=None):
        self._voice_cache_lang = None  # Invalidar cache de voces
        self._refresh_voices()
        if self.view.auto_enabled and self.view.get_input().strip():
            self._schedule_translate()

    def _on_voice_change(self, _event=None):
        if self.view.get_selected_voice_id():
            self._set_status("● voz manual seleccionada", "info")
        else:
            self._set_status("● voz automática activada", "info")

    def _on_input_change(self, _event=None):
        """Versión mejorada con debouncing para auto-traducción"""
        if self._suspend_auto:
            return

        text = self.view.get_input()
        self.view.set_char_count(len(text))

        if self.view.auto_enabled:
            if text.strip():
                # Solo traducir si el texto cambió y no hay traducción pendiente
                if text != self._last_translate_text:
                    self._schedule_translate()
            else:
                self.view.set_output("")
                self._set_status("● limpio", "info")

    def _schedule_translate(self):
        """Debouncing: evita traducir en cada carácter"""
        if self._translate_timer is not None:
            self.view.after_cancel(self._translate_timer)
        
        self._translate_timer = self.view.after(300, self._execute_translate)

    def _execute_translate(self):
        """Ejecuta la traducción con debouncing"""
        self._translate_timer = None
        self.translate()

    def toggle_auto(self):
        enabled = not self.view.auto_enabled
        self.view.set_auto(enabled)
        self._set_status(f"● auto {'activado' if enabled else 'desactivado'}", "info")

        if enabled and self.view.get_input().strip():
            self._schedule_translate()

    # ── FUNCIONES ─────────────────────────────────────────────

    def translate(self):
        """Traducción en hilo separado para no bloquear UI"""
        # Cancelar cualquier temporizador automático pendiente
        if self._translate_timer is not None:
            self.view.after_cancel(self._translate_timer)
            self._translate_timer = None

        text = self.view.get_input()
        src = self.view.get_from_code()
        tgt = self.view.get_to_code()

        if not text.strip():
            return

        if len(text) > 5000:
            self._set_status("● texto largo: la traducción puede tardar", "warn")

        self._toggle_ui(False)
        self._last_translate_text = text
        
        # Cancelar traducción en curso si existe
        if self._current_translate_evt:
            self._current_translate_evt.set()
        
        # Crear nuevo evento para esta traducción
        evt = threading.Event()
        self._current_translate_evt = evt

        # Ejecutar en hilo separado para no bloquear UI
        threading.Thread(
            target=self._translate_async,
            args=(text, src, tgt, evt),
            daemon=True
        ).start()

    def _translate_async(self, text, src, tgt, cancel_evt):
        """Traducción asincrónica en segundo plano"""
        try:
            if cancel_evt.is_set(): return

            valid_targets = {code for code, _ in self._pairs_by_source.get(src, [])}
            if tgt not in valid_targets:
                self._set_status("● combinación de idiomas no disponible", "warn")
                return

            self._set_loading(True, mode="determinate", value=10, detail="Validando paquete…")
            try:
                if cancel_evt.is_set(): return
                if not self.model.ensure_pair(src, tgt, self._set_status, self._on_install_progress):
                    return
                
                if cancel_evt.is_set(): return
                self._set_loading(True, mode="determinate", value=90, detail="Traduciendo texto…")
                result = self.model.translate(text, src, tgt)
                
                if cancel_evt.is_set(): return
                self.view.set_output(result)
                self._set_status("● traducción lista", "ok")
            finally:
                self._set_loading(False)
                self._ui_queue.put(("toggle_ui", True))
        except Exception as e:
            self._set_loading(False)
            self._set_status(f"● error: {e}", "error")
            self._ui_queue.put(("toggle_ui", True))

    def _toggle_ui(self, enabled: bool):
        """Habilita o deshabilita los controles principales de la interfaz"""
        state = "normal" if enabled else "disabled"
        self.view.btn_translate.config(state=state)
        self.view.btn_detect.config(state=state)
        self.view.btn_swap.config(state=state)
        self.view.btn_clear.config(state=state)
        self.view.from_combo.config(state="readonly" if enabled else "disabled")
        self.view.to_combo.config(state="readonly" if enabled else "disabled")
        self.view.input_text.config(state=state)

    def _detect_language_async(self):
        """Detección en hilo separado"""
        self._toggle_ui(False)
        threading.Thread(
            target=self.detect_language,
            daemon=True
        ).start()

    def detect_language(self):
        text = self.view.get_input()

        if not text.strip():
            return

        try:
            current_target = self.view.get_to_code()
            lang = self.model.detect(text)
            if not lang:
                self._set_status("● no se pudo detectar el idioma", "warn")
                return

            if lang not in self._pairs_by_source:
                self._set_status(f"● idioma detectado no disponible: {lang}", "warn")
                return

            self.view.select_from(lang)
            self._refresh_targets(preferred_code=current_target)
            self._set_status(f"● detectado: {lang}", "info")
        except Exception as e:
            self._set_status(f"● error detección: {e}", "error")

    def _text_to_speech_async(self):
        """TTS ya se ejecuta en hilo separado en el modelo, pero añadimos feedback"""
        text = self.view.get_output()
        if not text.strip():
            return
        
        self._set_status("● reproduciendo audio…", "info")
        threading.Thread(
            target=self.text_to_speech,
            daemon=True
        ).start()

    def text_to_speech(self):
        text = self.view.get_output()
        lang = self.view.get_to_code()
        voice_id = self.view.get_selected_voice_id()

        if not text.strip():
            return

        try:
            self.model.speak(text, lang, voice_id)
        except Exception as e:
            self._set_status(f"● error TTS: {e}", "error")

    def swap_languages(self):
        try:
            src = self.view.get_from_code()
            tgt = self.view.get_to_code()

            input_text = self.view.get_input()
            output_text = self.view.get_output()

            self._suspend_auto = True
            self.view.select_from(tgt)
            self._voice_cache_lang = None  # Invalidar cache
            self._refresh_targets(preferred_code=src)

            self.view.set_input(output_text)
            self.view.set_output(input_text)
            self.view.set_char_count(len(output_text))
            self._suspend_auto = False

            if self.view.auto_enabled and output_text.strip():
                self._schedule_translate()

        except Exception as e:
            self._suspend_auto = False
            self._set_status(f"● error swap: {e}", "error")

    def clear(self):
        self._suspend_auto = True
        self.view.set_input("")
        self.view.set_output("")
        self.view.set_char_count(0)
        self._suspend_auto = False
        self._set_status("● limpio", "info")

    def copy(self):
        text = self.view.get_output()
        if text.strip():
            self.view.clipboard_clear()
            self.view.clipboard_append(text)
            self._set_status("● copiado al portapapeles", "ok")

    def on_close(self):
        """Maneja el cierre de la ventana"""
        # Cancelar cualquier traducción en curso
        if self._current_translate_evt:
            self._current_translate_evt.set()
        
        # Detener cualquier timer de debouncing
        if self._translate_timer:
            self.view.after_cancel(self._translate_timer)
            
        self.view.destroy()
