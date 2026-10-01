from unittest.mock import Mock

import pytest

from fungi_traductor.controller.app_controller import TranslatorController


class FakeView:
    """Stateful view without Tk; language selections follow the real comboboxes."""

    def __init__(self):
        self.auto_enabled = False
        self.source = None
        self.target = None
        self.input = ""
        self.output = ""
        self.from_items = {}
        self.to_items = {}
        self.timers = {}
        for name in [
            "btn_translate", "btn_detect", "btn_tts", "btn_swap_center", "btn_clear",
            "btn_copy", "btn_open", "btn_save", "btn_auto", "input_text",
            "lbl_src", "lbl_dst",
        ]:
            setattr(self, name, Mock())
        self.from_combo = Mock()
        self.from_combo.get.side_effect = lambda: self.from_items.get(self.source, "")
        self.to_combo = Mock()
        self.to_combo.get.side_effect = lambda: self.to_items.get(self.target, "")
        for name in [
            "bind_auto_toggle", "bind_input_change", "bind_from_change", "bind_to_change",
            "bind_voice_change", "bind_close", "set_status", "set_loading",
            "populate_voices", "select_voice", "set_char_count", "set_button_enabled",
            "set_tooltip", "geometry", "destroy",
        ]:
            setattr(self, name, Mock())

        self.geometry.return_value = "960x620"

    def get_input(self):
        return self.input

    def get_output(self):
        return self.output

    def set_input(self, text):
        self.input = text

    def set_output(self, text):
        self.output = text

    def get_from_code(self):
        return self.source or "en"

    def get_to_code(self):
        return self.target or "es"

    def populate_from(self, items):
        self.from_items = dict(items)
        if self.source not in self.from_items:
            self.source = None

    def populate_to(self, items):
        self.to_items = dict(items)
        if self.target not in self.to_items:
            self.target = None

    def select_from(self, code):
        if code in self.from_items:
            self.source = code

    def select_to(self, code):
        if code in self.to_items:
            self.target = code

    def get_selected_voice_id(self):
        return None

    def set_auto(self, enabled):
        self.auto_enabled = enabled

    def after(self, delay, callback):
        timer = f"timer-{len(self.timers)}"
        self.timers[timer] = (delay, callback)
        return timer

    def after_cancel(self, timer):
        self.timers.pop(timer, None)


@pytest.fixture
def controller():
    view = FakeView()
    model = Mock()
    model.available_pairs.return_value = [
        ("en", "es", "English", "Spanish"), ("es", "en", "Spanish", "English"),
        ("fr", "en", "French", "English"),
    ]
    model.installed_pairs.return_value = []
    model.list_voices.return_value = []
    ctrl = TranslatorController(view, model)
    ctrl._init_state = "ready"
    ctrl._populate_language_lists()
    return ctrl
