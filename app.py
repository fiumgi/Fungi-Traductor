from fungi_traductor.view.gui import TranslatorView # importamos la vista del traductor
from fungi_traductor.model.translator import TranslatorModel # importamos el modelo del traductor
from fungi_traductor.controller.app_controller import TranslatorController # importamos el controlador del traductor


def main(): # función principal del programa
    view  = TranslatorView() 
    model = TranslatorModel()
    _ctrl = TranslatorController(view, model)
    _ctrl.initialize()
    view.mainloop()


if __name__ == "__main__": # si el archivo se ejecuta directamente, se llama a la función main
    main()
