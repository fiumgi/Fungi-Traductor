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
from collections import OrderedDict
from concurrent.futures import CancelledError
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

# Silenciar logs internos de argostranslate
logging.getLogger("argostranslate").setLevel(logging.WARNING)





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
        self._tts_lock = threading.RLock()
        self._tts_available: bool | None = None
        self._cache_lock = threading.Lock()
        self._translation_lock = threading.Lock()
        self._package_lock = threading.Lock()
        self._translation_cache: OrderedDict[tuple[str, str, str], str] = OrderedDict()
        self._cache_chars = 0

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
        self.ready = False
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
        try:
            # Argos reintenta recursivamente si no existe el índice local.
            index_path = getattr(getattr(pkg_mod, "settings", None), "local_package_index", None)
            if index_path is not None and not Path(index_path).is_file():
                raise FileNotFoundError("No hay un índice local de paquetes")
            self._available = pkg_mod.get_available_packages()
        except Exception as exc:
            self._available = []
            log.warning("No se pudo leer el índice de paquetes: %s", exc)
            on_status("⚠ índice no disponible — usando paquetes locales", "warn")

        try:
            installed_count = len(pkg_mod.get_installed_packages())
        except Exception as exc:
            log.error("No se pudieron leer los paquetes instalados: %s", exc)
            on_status(f"✗ error leyendo paquetes locales: {exc}", "error")
            return False
        log.info(
            f"Índice cargado: {len(self._available)} disponibles, "
            f"{installed_count} instalados"
        )
        if on_progress:
            on_progress("init", 100, "Idiomas listos")
        self.ready = True
        return True

    @staticmethod
    def _package_pairs(packages) -> list[tuple]:
        result = []
        for p in packages:
            if getattr(p, "type", "translate") != "translate":
                continue
            if not getattr(p, "from_code", None) or not getattr(p, "to_code", None):
                continue
            fn = getattr(p, "from_name", None) or p.from_code
            tn = getattr(p, "to_name", None) or p.to_code
            result.append((p.from_code, p.to_code, fn, tn))
        return result

    def available_pairs(self) -> list[tuple]:
        """Devuelve [(from_code, to_code, from_name, to_name), ...]"""
        return self._package_pairs(self._available)

    def installed_pairs(self) -> list[tuple]:
        if not self._pkg_mod:
            return []
        return self._package_pairs(self._pkg_mod.get_installed_packages())

    def ensure_pair(self, from_code: str, to_code: str, on_status, on_progress=None,
                    cancel_evt=None) -> bool:
        """Instala el par si no está instalado. Devuelve True si queda listo."""
        with self._package_lock:
            self._check_cancelled(cancel_evt)
            return self._ensure_pair(from_code, to_code, on_status, on_progress)

    def _ensure_pair(self, from_code, to_code, on_status, on_progress):
        if not self._pkg_mod:
            return False

        installed = self._pkg_mod.get_installed_packages()
        if any(getattr(p, "from_code", None) == from_code
               and getattr(p, "to_code", None) == to_code
               for p in installed):
            if on_progress:
                on_progress("install", 100, f"Paquete {from_code}→{to_code} ya instalado")
            return True

        pkg = next(
            (p for p in self._available
             if getattr(p, "from_code", None) == from_code
             and getattr(p, "to_code", None) == to_code),
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

    @staticmethod
    def _check_cancelled(cancel_evt):
        if cancel_evt is not None and cancel_evt.is_set():
            raise CancelledError()

    def _cache_translation(self, key, result):
        """Limita tanto el número de entradas como el texto retenido en memoria."""
        with self._cache_lock:
            previous = self._translation_cache.pop(key, None)
            if previous is not None:
                self._cache_chars -= len(key[0]) + len(previous)
            size = len(key[0]) + len(result)
            if size <= 2_000_000:
                self._translation_cache[key] = result
                self._cache_chars += size
            max_entries = 50 if len(key[0]) > 1000 else 200
            while self._translation_cache and (
                    len(self._translation_cache) > max_entries or self._cache_chars > 2_000_000):
                old_key, old_result = self._translation_cache.popitem(last=False)
                self._cache_chars -= len(old_key[0]) + len(old_result)

    @staticmethod
    def _translation_chunks(text: str, max_chars: int = 3000):
        """Separa líneas y párrafos largos conservando sus espacios y saltos."""
        chunks = []
        for line in re.split(r"(\r\n|\r|\n)", text):
            while len(line) > max_chars and line.strip():
                window = line[:max_chars + 1]
                boundaries = list(re.finditer(r"[.!?。！？](\s+)", window))
                if boundaries:
                    boundary = boundaries[-1]
                    end, next_start = boundary.start(1), boundary.end(1)
                else:
                    spaces = [match for match in re.finditer(r"\s+", window) if match.start() > 0]
                    if spaces:
                        boundary = spaces[-1]
                        end, next_start = boundary.start(), boundary.end()
                    else:
                        end = next_start = max_chars
                chunks.append((line[:end], True))
                if next_start > end:
                    chunks.append((line[end:next_start], False))
                line = line[next_start:]
            if line:
                chunks.append((line, bool(line.strip())))
        return chunks

    def translate(self, text: str, from_code: str, to_code: str, on_progress=None,
                  cancel_evt=None) -> str:
        trans_mod = self._trans_mod
        if not trans_mod:
            raise RuntimeError("Modelo no inicializado")

        self._check_cancelled(cancel_evt)
        # Evitar que varias solicitudes ejecuten el motor a la vez.
        with self._translation_lock:
            self._check_cancelled(cancel_evt)
            cache_key = (text, from_code, to_code)
            with self._cache_lock:
                if cache_key in self._translation_cache:
                    self._translation_cache.move_to_end(cache_key)
                    return self._translation_cache[cache_key]

            chunks = self._translation_chunks(text) if len(text) > 3000 else [(text, bool(text.strip()))]
            total = sum(translate for _, translate in chunks)
            completed = 0
            results = []
            for chunk, should_translate in chunks:
                self._check_cancelled(cancel_evt)
                if not should_translate:
                    results.append(chunk)
                    continue
                key = (chunk, from_code, to_code)
                with self._cache_lock:
                    translated = self._translation_cache.get(key)
                    if translated is not None:
                        self._translation_cache.move_to_end(key)
                if translated is None:
                    translated = trans_mod.translate(chunk, from_code, to_code)
                    self._check_cancelled(cancel_evt)
                    self._cache_translation(key, translated)
                results.append(translated)
                completed += 1
                if on_progress:
                    on_progress("translate", int(completed / total * 100),
                                f"Traduciendo fragmento {completed}/{total}…")
            self._check_cancelled(cancel_evt)
            result = "".join(results)
            self._cache_translation(cache_key, result)

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
                code = {"zh-cn": "zh", "zh-tw": "zt"}.get(best.lang, best.lang)

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

    def speak(self, text: str, lang: str = "es", voice_id: str | None = None, on_status=None):
        """Reproduce el texto en voz alta en un hilo separado."""
        def _run():
            with self._tts_lock:
                engine = None
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty("rate", 155)
                    chosen_voice_id = self._choose_voice_id(lang, voice_id)
                    if chosen_voice_id:
                        engine.setProperty("voice", chosen_voice_id)
                    engine.say(text)
                    engine.runAndWait()
                    log.info(
                        f"TTS: {len(text)} chars en idioma '{lang}' "
                        f"con voz '{chosen_voice_id or 'automática'}'"
                    )
                    if on_status:
                        on_status("● lectura terminada", "ok")
                except ImportError:
                    log.error("pyttsx3 no instalado — ejecuta: pip install pyttsx3")
                    if on_status:
                        on_status("✗ pyttsx3 no instalado", "error")
                except Exception as exc:
                    log.error(f"Error en TTS: {exc}")
                    if on_status:
                        on_status(f"✗ error TTS: {exc}", "error")
                finally:
                    if engine is not None:
                        try:
                            engine.stop()
                        except Exception as exc:
                            log.warning("No se pudo detener el motor de voz: %s", exc)

        worker = threading.Thread(target=_run, daemon=True)
        worker.start()
        return worker

    def tts_available(self) -> bool:
        """Comprueba una vez que pyttsx3 puede inicializar su backend del sistema."""
        with self._tts_lock:
            if self._tts_available is not None:
                return self._tts_available
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.stop()
                self._tts_available = True
            except Exception as exc:
                log.warning("Backend TTS no disponible: %s", exc)
                self._tts_available = False
            return self._tts_available

    def _load_tts_voices(self) -> list[dict]:
        with self._tts_lock:
            return self._load_tts_voices_locked()

    def _load_tts_voices_locked(self) -> list[dict]:
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
