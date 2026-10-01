from concurrent.futures import CancelledError
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock
import threading

import pytest

from fungi_traductor.model.translator import TranslatorModel


@pytest.fixture
def model():
    model = TranslatorModel()
    model._trans_mod = SimpleNamespace(translate=Mock(side_effect=lambda text, *_: text))
    return model


def fake_argos(monkeypatch, package):
    argos = ModuleType("argostranslate")
    argos.package = package
    argos.translate = ModuleType("argostranslate.translate")
    monkeypatch.setitem(__import__("sys").modules, "argostranslate", argos)
    monkeypatch.setitem(__import__("sys").modules, "argostranslate.package", package)
    monkeypatch.setitem(__import__("sys").modules, "argostranslate.translate", argos.translate)


def test_offline_initialization_without_an_index(monkeypatch, tmp_path):
    package = ModuleType("argostranslate.package")
    package.settings = SimpleNamespace(local_package_index=tmp_path / "missing.json")
    package.update_package_index = Mock(side_effect=OSError("offline"))
    package.get_available_packages = Mock(side_effect=FileNotFoundError("missing index"))
    package.get_installed_packages = Mock(return_value=[
        SimpleNamespace(from_code="en", to_code="es", from_name="English", to_name="Spanish")
    ])
    fake_argos(monkeypatch, package)
    model = TranslatorModel()
    statuses = []

    assert model.init_packages(lambda *args: statuses.append(args))
    assert model.ready
    assert model.installed_pairs() == [("en", "es", "English", "Spanish")]
    assert any(level == "warn" for _, level in statuses)
    # Argos retries recursively when its index is absent.
    package.get_available_packages.assert_not_called()


def test_corrupt_index_does_not_disable_installed_packages(monkeypatch, tmp_path):
    index = tmp_path / "index.json"
    index.write_text("invalid", encoding="utf-8")
    package = ModuleType("argostranslate.package")
    package.settings = SimpleNamespace(local_package_index=index)
    package.update_package_index = Mock()
    package.get_available_packages = Mock(side_effect=ValueError("invalid index"))
    package.get_installed_packages = Mock(return_value=[])
    fake_argos(monkeypatch, package)
    model = TranslatorModel()

    assert model.init_packages(Mock())
    assert model.available_pairs() == []


def test_non_translation_packages_are_not_language_pairs(model):
    model._available = [
        SimpleNamespace(type="sbd"),
        SimpleNamespace(type="translate", from_code="en", to_code="es",
                        from_name="English", to_name="Spanish"),
    ]
    assert model.available_pairs() == [("en", "es", "English", "Spanish")]


@pytest.mark.parametrize("separator", ["\n", "\n\n\n", "\r\n", "\r", "\n \n"])
def test_long_translation_preserves_paragraph_separators(model, separator):
    text = "\n" + "a" * 1700 + separator + "b" * 1700 + "\n\n"
    assert model.translate(text, "en", "es") == text


@pytest.mark.parametrize("text", [
    "word " * 2000,
    "Sentence one. Sentence two! " * 400,
    "x" * 10000,
    "\t" + "large " * 1200 + " \t",
], ids=["words", "sentences", "no_spaces", "leading_and_trailing_spaces"])
def test_single_long_paragraph_is_translated_in_bounded_chunks(model, text):
    assert model.translate(text, "en", "es") == text
    assert all(len(call.args[0]) <= 3000 for call in model._trans_mod.translate.call_args_list)


def test_cache_is_bounded_after_many_long_documents(model):
    for i in range(240):
        model.translate("a" * 1700 + str(i) + "\n" + "b" * 1700 + str(i), "en", "es")
    assert len(model._translation_cache) <= 50


def test_cached_translations_use_both_language_codes(model):
    model.translate("hello", "en", "es")
    model.translate("hello", "en", "es")
    model.translate("hello", "en", "fr")
    assert model._trans_mod.translate.call_count == 2


def test_cancellation_stops_between_chunks(model):
    cancelled = threading.Event()

    def translate(text, *_):
        cancelled.set()
        return text

    model._trans_mod.translate.side_effect = translate
    with pytest.raises(CancelledError):
        model.translate("a" * 1700 + "\n" + "b" * 1700, "en", "es", cancel_evt=cancelled)
    assert model._trans_mod.translate.call_count == 1


def test_translation_already_cancelled_does_not_run(model):
    cancelled = threading.Event()
    cancelled.set()
    with pytest.raises(CancelledError):
        model.translate("hello", "en", "es", cancel_evt=cancelled)
    model._trans_mod.translate.assert_not_called()


def test_concurrent_requests_only_install_a_package_once(model, tmp_path):
    package_path = tmp_path / "package.argosmodel"
    package_path.write_bytes(b"test")
    installed = []
    download_started = threading.Event()
    release_download = threading.Event()
    second_read = threading.Event()
    reads = 0

    def download():
        download_started.set()
        assert release_download.wait(timeout=5)
        return package_path

    def get_installed():
        nonlocal reads
        reads += 1
        if reads == 2:
            second_read.set()
        return list(installed)

    package = SimpleNamespace(from_code="en", to_code="es", download=Mock(side_effect=download))
    model._available = [package]
    model._pkg_mod = SimpleNamespace(
        get_installed_packages=get_installed,
        install_from_path=lambda _: installed.append(package),
    )
    results = []

    def install():
        results.append(model.ensure_pair("en", "es", Mock()))

    workers = [threading.Thread(target=install) for _ in range(2)]
    workers[0].start()
    assert download_started.wait(timeout=5)
    workers[1].start()
    # Sin el lock, el segundo hilo también comienza la descarga pendiente.
    second_read.wait(timeout=0.1)
    release_download.set()
    for worker in workers:
        worker.join(timeout=5)
        assert not worker.is_alive()
    assert results == [True, True]
    package.download.assert_called_once()


@pytest.mark.parametrize("detected, expected", [("zh-cn", "zh"), ("zh-tw", "zt")])
def test_detected_chinese_codes_match_argos_packages(model, monkeypatch, detected, expected):
    pytest.importorskip("langdetect")
    monkeypatch.setattr("langdetect.detect_langs",
                        lambda _: [SimpleNamespace(lang=detected, prob=1.0)])
    assert model.detect("你好世界，欢迎使用翻译器") == expected


def test_tts_reports_backend_failures_to_the_interface(model, monkeypatch):
    engine = Mock()
    engine.runAndWait.side_effect = RuntimeError("No audio driver")
    pyttsx3 = SimpleNamespace(init=Mock(return_value=engine))
    monkeypatch.setitem(__import__("sys").modules, "pyttsx3", pyttsx3)
    model._tts_voice_cache = []
    status = Mock()
    worker = model.speak("hello", "en", on_status=status)
    worker.join(timeout=5)
    assert not worker.is_alive()
    status.assert_called_once_with("✗ error TTS: No audio driver", "error")
    engine.stop.assert_called_once()


def test_tts_completes_when_voices_have_not_been_loaded_yet(model, monkeypatch):
    engine = Mock()
    engine.getProperty.return_value = [
        SimpleNamespace(id="english", name="English", languages=[b"\x05en"])
    ]
    monkeypatch.setitem(__import__("sys").modules, "pyttsx3",
                        SimpleNamespace(init=Mock(return_value=engine)))
    status = Mock()
    worker = model.speak("hello", "en", on_status=status)
    worker.join(timeout=5)
    assert not worker.is_alive()
    status.assert_called_once_with("● lectura terminada", "ok")
    engine.say.assert_called_once_with("hello")
    engine.setProperty.assert_any_call("voice", "english")
