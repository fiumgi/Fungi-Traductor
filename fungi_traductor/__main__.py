import logging
from fungi_traductor.view.gui import TranslatorView
from fungi_traductor.model.translator import TranslatorModel
from fungi_traductor.controller.app_controller import TranslatorController

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Optimización para Windows: Conciencia de DPI (evita que se vea borroso)
    try:
        from ctypes import windll  # type: ignore
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    view  = TranslatorView() 
    model = TranslatorModel()
    _ctrl = TranslatorController(view, model)
    _ctrl.initialize()
    view.mainloop()

if __name__ == "__main__":
    main()
