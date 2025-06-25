"""
Manejador de funciones inline en respuestas LLM.
"""
import json
import re
import logging
from typing import Dict, Any, Optional


class FunctionHandler:
    """
    Maneja funciones inline que pueden aparecer en las respuestas del LLM.
    """
    
    def __init__(self, handlers: Dict[str, Any]):
        self.handlers = handlers
        self.logger = logging.getLogger(__name__)
    
    def handle_inline_function(self, content: str) -> Optional[str]:
        """
        Busca y ejecuta funciones inline en el contenido.
        
        Args:
            content: Contenido que puede contener funciones inline
            
        Returns:
            str: Resultado formateado si se encuentra función, None si no
        """
        # Buscar patrón de función inline: {{función_nombre(args)}}
        function_pattern = r'\\{\\{(\\w+)\\(([^)]*)\\)\\}\\}'
        match = re.search(function_pattern, content)
        
        if not match:
            return None
            
        function_name = match.group(1)
        args_str = match.group(2)
        
        # Verificar si tenemos el handler para esta función
        if function_name not in self.handlers:
            self.logger.warning(f"Handler no encontrado para función inline: {function_name}")
            return None
        
        try:
            # Parsear argumentos
            if args_str.strip():
                # Intentar parsear como JSON
                try:
                    args = json.loads(f'[{args_str}]')
                    if len(args) == 1 and isinstance(args[0], dict):
                        kwargs = args[0]
                        result = self.handlers[function_name](**kwargs)
                    else:
                        result = self.handlers[function_name](*args)
                except json.JSONDecodeError:
                    # Si falla el parsing JSON, usar como argumentos de cadena
                    args = [arg.strip().strip('"').strip("'") for arg in args_str.split(',')]
                    result = self.handlers[function_name](*args)
            else:
                # Sin argumentos
                result = self.handlers[function_name]()
            
            # Formatear resultado
            from ..tools.configurable_formatter import format_tool_response
            formatted_result = format_tool_response(function_name, result)
            
            # Reemplazar la función inline con el resultado
            return content.replace(match.group(0), formatted_result)
            
        except Exception as e:
            self.logger.error(f"Error ejecutando función inline {function_name}: {e}")
            error_msg = f"Error ejecutando {function_name}: {str(e)}"
            return content.replace(match.group(0), error_msg)
