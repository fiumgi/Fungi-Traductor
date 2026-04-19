"""
hints.py — Diccionarios auxiliares para detección de idioma y nombres.
Parte del modelo de Fungi Traductor.
"""

_SHORT_TEXT_EXACT_HINTS = {
    "hello": "en",
    "hello world": "en",
    "hi": "en",
    "hey": "en",
    "thanks": "en",
    "thank you": "en",
    "good morning": "en",
    "good afternoon": "en",
    "good evening": "en",
    "good night": "en",
    "goodbye": "en",
    "bye": "en",
    "yes": "en",
    "no": "en",
}

_SHORT_TEXT_WORD_HINTS = {
    "en": {
        "hello", "hi", "hey", "thanks", "thank", "you", "please", "good",
        "morning", "afternoon", "evening", "night", "bye", "goodbye",
        "yes", "no", "how", "are", "world",
    },
    "es": {
        "hola", "gracias", "adios", "adiós", "buenos", "dias", "días",
        "buenas", "tardes", "noches", "por", "favor", "si", "sí",
    },
    "it": {
        "ciao", "grazie", "buongiorno", "buonasera", "arrivederci", "per",
        "favore", "si",
    },
    "fr": {
        "bonjour", "merci", "salut", "bonsoir", "au", "revoir", "s'il",
        "plait", "plaît", "oui", "non",
    },
}

_LANGUAGE_NAME_HINTS = {
    "en": {"english", "inglés", "inges", "en-us", "en-gb"},
    "es": {"spanish", "español", "espanol", "castilian"},
    "fr": {"french", "français", "francais"},
    "it": {"italian", "italiano"},
    "de": {"german", "deutsch"},
    "pt": {"portuguese", "português", "portugues"},
}
