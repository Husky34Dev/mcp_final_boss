"""
Utilidad para completar argumentos de herramientas usando el contexto conversacional.
Permite ampliar la lógica para otros campos clave fácilmente.
"""
from typing import Dict, Any

PLACEHOLDER_DNI_VALUES = {
    "dni", "dni del abonado", "your dni", "dni_value", "", None
}

class ToolArgsCompleter:
    """
    Clase utilitaria para completar argumentos de herramientas usando el contexto.
    Se puede ampliar para otros campos clave (nombre, póliza, etc).
    """
    def __init__(self, context):
        self.context = context

    def complete(self, args: Dict[str, Any]) -> Dict[str, Any]:
        args = dict(args)  # Copia defensiva
        # Completar DNI si es un placeholder y hay uno en el contexto
        if 'dni' in args and (str(args['dni']).lower() in PLACEHOLDER_DNI_VALUES):
            dni_ctx = self.context.get('dni')
            if dni_ctx:
                args['dni'] = dni_ctx
        # Aquí puedes añadir más lógica para otros campos clave
        return args
