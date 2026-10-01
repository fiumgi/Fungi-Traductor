from unittest.mock import Mock, patch
import tkinter as tk

import pytest

from fungi_traductor.controller.app_controller import TranslatorController
from fungi_traductor.view.gui import TranslatorView


@pytest.fixture
def view():
    try:
        view = TranslatorView()
    except tk.TclError as exc:
        if "display" in str(exc).lower():
            pytest.skip("Tk requires a display; run the GUI tests with Xvfb")
        raise
    view.update()
    yield view
    for timer in view.tk.call("after", "info"):
        view.tk.call("after", "cancel", timer)
    view.destroy()


def test_typing_after_clear_while_focused_is_visible_to_the_controller(view):
    view.input_text.focus_force()
    view.update()
    view.set_input("previous text")
    view.set_input("")
    view.input_text.insert("end", "new input")
    assert view.get_input() == "new input"


def test_translate_shortcut_runs_once_and_does_not_insert_a_newline(view):
    callback = Mock()
    view.btn_translate.config(command=callback)
    view.input_text.focus_force()
    view.update()
    view.set_input("hello")
    view.input_text.event_generate("<Control-Return>")
    view.update()
    callback.assert_called_once()
    assert view.get_input() == "hello"


def test_clear_shortcut_runs_once(view):
    callback = Mock()
    view.btn_clear.config(command=callback)
    view.input_text.focus_force()
    view.update()
    view.input_text.event_generate("<Control-l>")
    view.update()
    callback.assert_called_once()


def test_loaded_file_is_inserted_even_when_controls_are_disabled(view, tmp_path):
    model = Mock()
    model.available_pairs.return_value = [("en", "es", "English", "Spanish")]
    model.installed_pairs.return_value = []
    model.list_voices.return_value = []
    ctrl = TranslatorController(view, model)
    ctrl._init_state = "ready"
    ctrl._populate_language_lists()
    path = tmp_path / "input.txt"
    path.write_text("loaded file content", encoding="utf-8")
    view.ask_open_file = Mock(return_value=str(path))
    with patch("fungi_traductor.controller.app_controller.threading.Thread"):
        ctrl._on_open_file()
    ctrl._open_file_async(str(path), "en")
    ctrl._drain_ui_queue()
    assert view.get_input() == "loaded file content"
    ctrl._closed = True


def test_progress_stops_animating_after_switching_to_a_percentage(view):
    view.set_loading(True, mode="indeterminate")
    view.set_loading(True, mode="determinate", value=25)
    view.after(40, view.quit)
    view.mainloop()
    assert float(view.progress_track["value"]) == 25
