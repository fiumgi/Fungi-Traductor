import json
import threading
from unittest.mock import Mock, patch


def drain(controller):
    controller._drain_ui_queue()


def test_saved_language_pair_is_restored_after_population(controller, tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"last_from": "fr", "last_to": "en"}), encoding="utf-8")
    controller._get_config_path = lambda: path
    controller.view.populate_from([])
    controller.view.populate_to([])

    controller._load_config()
    controller._populate_language_lists()
    assert controller.view.source == "fr"
    assert controller.view.target == "en"


def test_installed_languages_remain_available_without_an_index(controller):
    controller.model.available_pairs.return_value = []
    controller.model.installed_pairs.return_value = [("en", "es", "English", "Spanish")]
    controller._init_state = "offline"
    controller._populate_language_lists()
    assert controller.view.source == "en"
    assert controller.view.target == "es"


def test_queued_updates_do_not_drop_the_final_result(controller):
    for i in range(80):
        controller._set_status(str(i))
    controller.model.translate.return_value = "resultado"
    event = threading.Event()
    controller._current_translate_evt = event
    controller._translate_async("text", "en", "es", event)
    drain(controller)
    assert controller.view.output == "resultado"
    controller.view.set_status.assert_any_call("● traducción lista", "ok")


def test_results_queued_before_editing_are_discarded(controller):
    controller.model.translate.return_value = "obsolete"
    event = threading.Event()
    controller._current_translate_evt = event
    controller._translate_async("old", "en", "es", event)
    controller.view.input = "new"
    controller._on_input_change()
    drain(controller)
    assert controller.view.output != "obsolete"
    assert event.is_set()


def test_cancelled_worker_does_not_enable_controls_for_a_new_request(controller):
    old = threading.Event()
    current = threading.Event()
    controller._current_translate_evt = current

    def install(*args, **kwargs):
        old.set()
        return True

    controller.model.ensure_pair.side_effect = install
    controller._translate_async("old", "en", "es", old)
    controller._toggle_ui = Mock()
    controller.view.set_loading.reset_mock()
    drain(controller)
    controller._toggle_ui.assert_not_called()
    controller.view.set_loading.assert_not_called()


def test_invalid_pair_does_not_leave_the_interface_disabled(controller):
    event = threading.Event()
    controller._current_translate_evt = event
    controller._translate_async("text", "en", "invalid", event)
    controller._toggle_ui = Mock()
    drain(controller)
    controller._toggle_ui.assert_called_with(True)


def test_typing_stays_available_during_translation(controller):
    controller.view.input = "hello"
    with patch("fungi_traductor.controller.app_controller.threading.Thread"):
        controller.translate()
    assert controller.view.input_text.config.call_args.kwargs["state"] == "normal"
    assert controller.view.btn_clear.config.call_args.kwargs["state"] == "normal"


def test_disabling_auto_cancels_the_pending_timer(controller):
    controller.view.set_auto(True)
    controller._schedule_translate()
    timer = controller._translate_timer
    controller.toggle_auto()
    assert timer not in controller.view.timers
    assert controller._translate_timer is None


def test_clear_cancels_pending_work_and_allows_same_text_again(controller):
    controller.view.set_auto(True)
    controller.view.input = "hello"
    with patch("fungi_traductor.controller.app_controller.threading.Thread"):
        controller.translate()
    event = controller._current_translate_evt
    controller.clear()
    assert event.is_set()
    assert controller._translate_timer is None
    controller.view.input = "hello"
    controller._on_input_change()
    assert controller._translate_timer is not None


def test_swap_without_a_reverse_pair_preserves_text_and_languages(controller):
    controller.view.select_from("fr")
    controller._refresh_targets(preferred_code="en")
    controller.view.input = "bonjour"
    controller.view.output = "hello"
    controller.swap_languages()
    assert (controller.view.source, controller.view.target) == ("fr", "en")
    assert (controller.view.input, controller.view.output) == ("bonjour", "hello")


def test_initialization_failure_always_finishes_loading(controller):
    controller.model.init_packages.side_effect = RuntimeError("broken engine")
    controller._initialize_async()
    drain(controller)
    controller.view.set_loading.assert_called_with(False)
    assert controller._init_state == "error"


def test_missing_optional_features_stay_disabled_after_translation(controller):
    with patch.dict("sys.modules", {"pyttsx3": None, "langdetect": None}):
        controller._check_optional_deps()
    controller._toggle_ui(True)
    assert controller.view.btn_tts.config.call_args.kwargs["state"] == "disabled"
    assert controller.view.btn_detect.config.call_args.kwargs["state"] == "disabled"


def test_tts_backend_probe_failure_disables_only_tts(controller):
    controller.model.tts_available.return_value = False

    with patch.dict("sys.modules", {"pyttsx3": Mock(), "langdetect": Mock()}):
        controller._check_optional_deps()
    controller._toggle_ui(True)

    assert controller.view.btn_tts.config.call_args.kwargs["state"] == "disabled"
    assert controller.view.btn_detect.config.call_args.kwargs["state"] != "disabled"


def test_tts_does_not_read_tk_widgets_from_a_worker(controller):
    controller.view.output = "hola"
    main_thread = threading.get_ident()
    original = controller.view.get_output

    def get_output():
        assert threading.get_ident() == main_thread
        return original()

    controller.view.get_output = get_output
    controller._text_to_speech_async()
    controller.model.speak.assert_called_once()


def test_closed_controller_stops_polling(controller, tmp_path):
    controller._get_config_path = lambda: tmp_path / "config.json"
    controller._schedule_ui_queue_poll()
    controller.on_close()
    timers = dict(controller.view.timers)
    drain(controller)
    assert controller.view.timers == timers == {}


def test_invalid_saved_language_codes_do_not_break_population(controller, tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"last_from": [], "last_to": {}}), encoding="utf-8")
    controller._get_config_path = lambda: path
    controller._load_config()
    controller._populate_language_lists()
    assert controller.view.source == "es"
    assert controller.view.target == "en"
