"""
app.py — Punto de entrada de Fungi Traductor.

Uso:
    python app.py

Requiere:
    pip install -r requirements.txt
"""
from view       import TranslatorView
from model      import TranslatorModel
from controller import TranslatorController


def main():
    view       = TranslatorView()
    model      = TranslatorModel()
    _ctrl      = TranslatorController(view, model)  # conecta todo
    view.mainloop()


if __name__ == "__main__":
    main()