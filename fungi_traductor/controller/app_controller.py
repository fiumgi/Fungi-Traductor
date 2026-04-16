class TranslatorController:
    def __init__(self, view, model):
        self.view = view
        self.model = model

        # Conectar botones
        self.view.btn_translate.config(command=self.translate)
        self.view.btn_detect.config(command=self.detect_language)
        self.view.btn_tts.config(command=self.text_to_speech)
        self.view.btn_swap.config(command=self.swap_languages)
        self.view.btn_clear.config(command=self.clear)
        self.view.btn_copy.config(command=self.copy)

    # ── INICIALIZACIÓN ─────────────────────────────────────────

    def initialize(self):
        def on_status(msg, level):
            self.view.set_status(msg, level)

        # Inicializar modelo (Argos packages)
        self.model.init_packages(on_status)

        # Poblar idiomas
        self._populate_language_lists()

    def _populate_language_lists(self):
        pairs = self.model.available_pairs()

        from_langs = {(src_code, src_name) for src_code, _, src_name, _ in pairs}
        to_langs   = {(tgt_code, tgt_name) for _, tgt_code, _, tgt_name in pairs}

        self.view.populate_from(sorted(from_langs))
        self.view.populate_to(sorted(to_langs))

        # valores por defecto
        self.view.select_from("es")
        self.view.select_to("en")

    # ── FUNCIONES ─────────────────────────────────────────────

    def translate(self):
        text = self.view.get_input()
        src = self.view.get_from_code()
        tgt = self.view.get_to_code()

        if not text.strip():
            return

        try:
            result = self.model.translate(text, src, tgt)
            self.view.set_output(result)
            self.view.set_status("● traducción lista", "ok")
        except Exception as e:
            self.view.set_status(f"● error: {e}", "error")

    def detect_language(self):
        text = self.view.get_input()

        if not text.strip():
            return

        try:
            lang = self.model.detect(text)
            if not lang:
                self.view.set_status("● no se pudo detectar el idioma", "warn")
                return
            self.view.select_from(lang)
            self.view.set_status(f"● detectado: {lang}", "info")
        except Exception as e:
            self.view.set_status(f"● error detección: {e}", "error")

    def text_to_speech(self):
        text = self.view.get_output()

        if not text.strip():
            return

        try:
            self.model.speak(text)
        except Exception as e:
            self.view.set_status(f"● error TTS: {e}", "error")

    def swap_languages(self):
        try:
            src = self.view.get_from_code()
            tgt = self.view.get_to_code()

            input_text = self.view.get_input()
            output_text = self.view.get_output()

            self.view.select_from(tgt)
            self.view.select_to(src)

            self.view.set_input(output_text)
            self.view.set_output(input_text)

        except Exception as e:
            self.view.set_status(f"● error swap: {e}", "error")

    def clear(self):
        self.view.set_input("")
        self.view.set_output("")
        self.view.set_status("● limpio", "info")

    def copy(self):
        text = self.view.get_output()

        if not text:
            return

        self.view.clipboard_clear()
        self.view.clipboard_append(text)
        self.view.set_status("● copiado", "ok")
