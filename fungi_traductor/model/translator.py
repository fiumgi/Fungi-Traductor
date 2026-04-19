"""
model.py — Lógica de traducción, TTS y detección de idioma.
Patrón MVC · Fungi Traductor
"""
import logging
import re
import threading
import sys
import os
from pathlib import Path
from .hints import _SHORT_TEXT_EXACT_HINTS, _SHORT_TEXT_WORD_HINTS, _LANGUAGE_NAME_HINTS

# ── Logging ───────────────────────────────────────────────────────────────────
def _get_log_path():
    """Determina una ruta de log que sea siempre escribible"""
    try:
        from platformdirs import user_log_dir
        log_dir = Path(user_log_dir("FungiTraductor", "fiumgi"))
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "fungi_traductor.log"
    except Exception:
        # Fallback si platformdirs no está disponible o falla
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent / "fungi_traductor.log"
        return Path(__file__).parent / "fungi_traductor.log"

try:
    logging.basicConfig(
        filename=_get_log_path(),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
except Exception:
    # Si falla el archivo (permisos), loguear a consola
    logging.basicConfig(
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
        self._tts_voice_cache: list[dict] | None = None
        self._tts_lock = threading.Lock()
        self._translation_cache = {}  # {(text, from, to): result}

    def _check_system_proxy(self):
        """Detecta si hay un proxy configurado en el sistema"""
        try:
            import urllib.request
            proxies = urllib.request.getproxies()
            if proxies:
                # Retorna una cadena simple si hay proxies (http, https, etc)
                return ", ".join(proxies.keys())
        except Exception:
            pass
        return None

    # ── Inicialización ────────────────────────────────────────────────────────

    def init_packages(self, on_status, on_progress=None) -> bool:
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

        if on_progress:
            on_progress("init", 10, "Cargando motor de traduccion…")

        self._pkg_mod   = pkg_mod
        self._trans_mod = trans_mod

        on_status("⟳ actualizando índice de paquetes…", "info")
        if on_progress:
            on_progress("init", 35, "Actualizando indice de paquetes…")
        try:
            pkg_mod.update_package_index()
        except Exception as exc:
            proxy = self._check_system_proxy()
            log.warning(f"Sin conexión o error de red: {exc}")
            msg = "⚠ sin conexión — usando paquetes locales"
            if proxy:
                msg += " (detectado proxy corporativo)"
            on_status(msg, "warn")

        if on_progress:
            on_progress("init", 75, "Leyendo idiomas disponibles…")
        self._available = pkg_mod.get_available_packages()
        installed_count = len(pkg_mod.get_installed_packages())
        log.info(
            f"Índice cargado: {len(self._available)} disponibles, "
            f"{installed_count} instalados"
        )
        if on_progress:
            on_progress("init", 100, "Idiomas listos")
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

    def ensure_pair(self, from_code: str, to_code: str, on_status, on_progress=None) -> bool:
        """Instala el par si no está instalado. Devuelve True si queda listo."""
        if not self._pkg_mod:
            return False

        installed = self._pkg_mod.get_installed_packages()
        if any(p.from_code == from_code and p.to_code == to_code
               for p in installed):
            if on_progress:
                on_progress("install", 100, f"Paquete {from_code}→{to_code} ya instalado")
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
            if on_progress:
                on_progress("install", 15, f"Preparando {from_code}→{to_code}…")
            on_status(f"⬇ instalando {from_code}→{to_code} (~50 MB), paciencia…", "info")
            if on_progress:
                on_progress("install", 40, f"Descargando paquete {from_code}→{to_code}…")
            package_path = pkg.download()
            if on_progress:
                on_progress("install", 80, f"Instalando paquete {from_code}→{to_code}…")
            self._pkg_mod.install_from_path(package_path)
            
            # Limpiar archivo temporal después de instalar
            try:
                if os.path.exists(package_path):
                    os.remove(package_path)
            except Exception as e:
                log.warning(f"No se pudo eliminar paquete temporal: {e}")

            log.info(f"Instalado: {from_code}→{to_code}")
            if on_progress:
                on_progress("install", 100, f"Paquete {from_code}→{to_code} listo")
            return True
        except Exception as exc:
            proxy = self._check_system_proxy()
            msg = f"✗ error instalando paquete: {exc}"
            if proxy:
                msg += f" (revisa el proxy corporativo: {proxy})"
            log.error(msg)
            on_status(msg, "error")
            return False

    # ── Traducción ────────────────────────────────────────────────────────────

    def translate(self, text: str, from_code: str, to_code: str) -> str:
        if not self._trans_mod:
            raise RuntimeError("Modelo no inicializado")
        
        cache_key = (text, from_code, to_code)
        if cache_key in self._translation_cache:
            log.info(f"Caché hit: {len(text)} chars {from_code}→{to_code}")
            return self._translation_cache[cache_key]

        result = self._trans_mod.translate(text, from_code, to_code)
        
        # Guardar en caché y limitar tamaño (p.ej. 100 entradas)
        if len(self._translation_cache) >= 100:
            # Eliminar la entrada más vieja (primera insertada)
            oldest_key = next(iter(self._translation_cache))
            del self._translation_cache[oldest_key]
        
        self._translation_cache[cache_key] = result
        log.info(f"Traducidos {len(text)} chars  {from_code}→{to_code} (Guardado en caché)")
        return result

    # ── Detección de idioma ───────────────────────────────────────────────────

    def detect(self, text: str) -> str | None:
        """
        Devuelve el código ISO del idioma detectado (p.ej. 'en', 'es'),
        o None si langdetect no está instalado o falla.
        """
        try:
            from langdetect import DetectorFactory, detect_langs

            DetectorFactory.seed = 0
            normalized = self._normalize_text(text)
            code = self._detect_short_text_language(normalized)
            if code is None:
                langs = detect_langs(text)
                if not langs:
                    return None

                best = langs[0]
                if self._is_detection_ambiguous(normalized, best.prob):
                    log.info(f"Detección ambigua para texto corto: {langs}")
                    return None
                code = best.lang

            log.info(f"Idioma detectado: {code}")
            return code
        except ImportError:
            log.warning("langdetect no instalado — ejecuta: pip install langdetect")
            return None
        except Exception as exc:
            log.warning(f"langdetect falló: {exc}")
            return None

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def _detect_short_text_language(self, normalized: str) -> str | None:
        if not normalized:
            return None

        if normalized in _SHORT_TEXT_EXACT_HINTS:
            return _SHORT_TEXT_EXACT_HINTS[normalized]

        words = re.findall(r"[a-zA-ZÀ-ÿ']+", normalized)
        if not words:
            return None

        if len(normalized) > 24 and len(words) > 3:
            return None

        best_lang = None
        best_score = 0
        for lang, hints in _SHORT_TEXT_WORD_HINTS.items():
            score = sum(1 for word in words if word in hints)
            if score > best_score:
                best_lang = lang
                best_score = score

        if best_score == len(words):
            return best_lang
        if best_score >= 2:
            return best_lang
        return None

    @staticmethod
    def _is_detection_ambiguous(normalized: str, probability: float) -> bool:
        words = re.findall(r"[a-zA-ZÀ-ÿ']+", normalized)
        return len(normalized) <= 24 and len(words) <= 3 and probability < 0.90

    # ── TTS ───────────────────────────────────────────────────────────────────

    def list_voices(self, preferred_lang: str | None = None) -> list[tuple[str, str]]:
        voices = self._load_tts_voices()
        ranked = sorted(
            voices,
            key=lambda voice: (
                -self._voice_score(voice, preferred_lang),
                voice["name"].lower(),
                voice["id"].lower(),
            ),
        )
        return [(voice["id"], voice["label"]) for voice in ranked]

    def speak(self, text: str, lang: str = "es", voice_id: str | None = None):
        """Reproduce el texto en voz alta en un hilo separado."""
        def _run():
            with self._tts_lock:
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty("rate", 155)
                    chosen_voice_id = self._choose_voice_id(lang, voice_id)
                    if chosen_voice_id:
                        engine.setProperty("voice", chosen_voice_id)
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
                    log.info(
                        f"TTS: {len(text)} chars en idioma '{lang}' "
                        f"con voz '{chosen_voice_id or 'automática'}'"
                    )
                except ImportError:
                    log.error("pyttsx3 no instalado — ejecuta: pip install pyttsx3")
                except Exception as exc:
                    log.error(f"Error en TTS: {exc}")

        threading.Thread(target=_run, daemon=True).start()

    def _load_tts_voices(self) -> list[dict]:
        # Reutilizar cache si ya está cargado
        if self._tts_voice_cache is not None:
            return self._tts_voice_cache

        try:
            import pyttsx3
        except ImportError:
            self._tts_voice_cache = []
            return self._tts_voice_cache

        try:
            engine = pyttsx3.init()
            voices = []
            # Optimización: procesar voces una sola vez
            for voice in engine.getProperty("voices"):
                languages = [str(item).lower() for item in (getattr(voice, "languages", None) or [])]
                name = getattr(voice, "name", voice.id)
                label = f"{name} ({voice.id})"
                voices.append({
                    "id": voice.id,
                    "name": name,
                    "label": label,
                    "languages": languages,
                })
            engine.stop()
            # Ordenar una sola vez por rendimiento
            self._tts_voice_cache = voices
        except Exception as exc:
            log.warning(f"No se pudieron cargar voces TTS: {exc}")
            self._tts_voice_cache = []

        return self._tts_voice_cache

    def _choose_voice_id(self, lang: str, preferred_voice_id: str | None = None) -> str | None:
        voices = self._load_tts_voices()
        if not voices:
            return None

        if preferred_voice_id and any(voice["id"] == preferred_voice_id for voice in voices):
            return preferred_voice_id

        best_voice = max(voices, key=lambda voice: self._voice_score(voice, lang), default=None)
        if not best_voice:
            return None
        return best_voice["id"]

    def _voice_score(self, voice: dict, lang: str | None) -> int:
        if not lang:
            return 0

        lang = lang.lower()
        score = 0
        voice_id = voice["id"].lower()
        voice_name = voice["name"].lower()
        voice_langs = voice["languages"]
        hints = _LANGUAGE_NAME_HINTS.get(lang, {lang})

        if any(lang in item for item in voice_langs):
            score += 120
        if any(hint in voice_id for hint in hints):
            score += 80
        if any(hint in voice_name for hint in hints):
            score += 70
        if lang == "en" and ("zira" in voice_name or "david" in voice_name or "english" in voice_name):
            score += 40
        return score
