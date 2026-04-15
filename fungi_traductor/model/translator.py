"""
model.py — Lógica de traducción, TTS y detección de idioma.
Patrón MVC · Fungi Traductor
"""
import logging
import threading
from pathlib import Path

# ── Logging ───────────────────────────────────────────────────────────────────
_log_path = Path(__file__).parent / "fungi_traductor.log"
logging.basicConfig(
    filename=_log_path,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


class TranslatorModel:
    """
    Encapsula argostranslate, langdetect y pyttsx3.
    No importa tkinter ni conoce la vista.
    """

    def __init__(self):
        self._pkg_mod   = None   # argostranslate.package
        self._trans_mod = None   # argostranslate.translate
        self.ready      = False
        self._available: list = []   # paquetes disponibles en el índice

    # ── Inicialización ────────────────────────────────────────────────────────

    def init_packages(self, on_status) -> bool:
        """
        Descarga el índice de paquetes de Argos Translate.
        on_status(msg: str, level: str)  level ∈ {"info","warn","error","ok"}
        """
        try:
            import argostranslate.package as pkg_mod
            import argostranslate.translate as trans_mod
        except ImportError:
            msg = "argostranslate no instalado — ejecuta: pip install argostranslate"
            log.error(msg)
            on_status(msg, "error")
            return False

        self._pkg_mod   = pkg_mod
        self._trans_mod = trans_mod

        on_status("⟳ actualizando índice de paquetes…", "info")
        try:
            pkg_mod.update_package_index()
        except Exception as exc:
            log.warning(f"Sin conexión o error de red: {exc}")
            on_status("⚠ sin conexión — usando paquetes locales", "warn")

        self._available = pkg_mod.get_available_packages()
        installed_count = len(pkg_mod.get_installed_packages())
        log.info(
            f"Índice cargado: {len(self._available)} disponibles, "
            f"{installed_count} instalados"
        )
        return True

    def available_pairs(self) -> list[tuple]:
        """Devuelve [(from_code, to_code, from_name, to_name), ...]"""
        result = []
        for p in self._available:
            fn = getattr(p, "from_name", p.from_code)
            tn = getattr(p, "to_name",   p.to_code)
            result.append((p.from_code, p.to_code, fn, tn))
        return result

    def installed_pairs(self) -> list[tuple]:
        if not self._pkg_mod:
            return []
        result = []
        for p in self._pkg_mod.get_installed_packages():
            fn = getattr(p, "from_name", p.from_code)
            tn = getattr(p, "to_name",   p.to_code)
            result.append((p.from_code, p.to_code, fn, tn))
        return result

    def ensure_pair(self, from_code: str, to_code: str, on_status) -> bool:
        """Instala el par si no está instalado. Devuelve True si queda listo."""
        if not self._pkg_mod:
            return False

        installed = self._pkg_mod.get_installed_packages()
        if any(p.from_code == from_code and p.to_code == to_code
               for p in installed):
            return True

        pkg = next(
            (p for p in self._available
             if p.from_code == from_code and p.to_code == to_code),
            None,
        )
        if pkg is None:
            msg = f"✗ par {from_code}→{to_code} no disponible en el índice"
            log.error(msg)
            on_status(msg, "error")
            return False

        try:
            on_status(f"⬇ instalando {from_code}→{to_code} (~50 MB), paciencia…", "info")
            self._pkg_mod.install_from_path(pkg.download())
            log.info(f"Instalado: {from_code}→{to_code}")
            return True
        except Exception as exc:
            msg = f"✗ error instalando paquete: {exc}"
            log.error(msg)
            on_status(msg, "error")
            return False

    # ── Traducción ────────────────────────────────────────────────────────────

    def translate(self, text: str, from_code: str, to_code: str) -> str:
        if not self._trans_mod:
            raise RuntimeError("Modelo no inicializado")
        result = self._trans_mod.translate(text, from_code, to_code)
        log.info(f"Traducidos {len(text)} chars  {from_code}→{to_code}")
        return result

    # ── Detección de idioma ───────────────────────────────────────────────────

    def detect(self, text: str) -> str | None:
        """
        Devuelve el código ISO del idioma detectado (p.ej. 'en', 'es'),
        o None si langdetect no está instalado o falla.
        """
        try:
            from langdetect import detect
            code = detect(text)
            log.info(f"Idioma detectado: {code}")
            return code
        except ImportError:
            log.warning("langdetect no instalado — ejecuta: pip install langdetect")
            return None
        except Exception as exc:
            log.warning(f"langdetect falló: {exc}")
            return None

    # ── TTS ───────────────────────────────────────────────────────────────────

    def speak(self, text: str, lang: str = "es"):
        """Reproduce el texto en voz alta en un hilo separado."""
        def _run():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty("rate", 155)
                # Intentar seleccionar una voz del idioma correcto
                for v in engine.getProperty("voices"):
                    v_id   = v.id.lower()
                    v_langs = [str(l).lower() for l in (v.languages or [])]
                    if lang.lower() in v_id or any(lang.lower() in l for l in v_langs):
                        engine.setProperty("voice", v.id)
                        break
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                log.info(f"TTS: {len(text)} chars en idioma '{lang}'")
            except ImportError:
                log.error("pyttsx3 no instalado — ejecuta: pip install pyttsx3")
            except Exception as exc:
                log.error(f"Error en TTS: {exc}")

        threading.Thread(target=_run, daemon=True).start()
