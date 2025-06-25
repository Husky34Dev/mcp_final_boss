"""
Sistema de formateadores unificado y configurables basado en JSON.
Este es el único formateador del framework que maneja tanto casos configurados
como casos por defecto usando configuración JSON.
"""
import json
import re
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path


class UnifiedFormatter:
    """
    Formateador unificado que lee configuraciones desde JSON y genera markdown.
    Maneja tanto casos configurados como formateo por defecto.
    También permite registro manual de formatters para casos especiales.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el formateador con un archivo de configuración JSON opcional.
        
        Args:
            config_path: Ruta al archivo JSON de configuración (opcional)
        """
        self.config_path = config_path
        self.formatters_config = self._load_config() if config_path else {"formatters": {}}
        # Diccionario para formatters registrados manualmente
        self.manual_formatters: Dict[str, Callable[[Dict[str, Any]], str]] = {}
    
    def register_formatter(self, tool_name: str, formatter_func: Callable[[Dict[str, Any]], str]):
        """
        Registra un formateador manual para una herramienta específica.
        
        Args:
            tool_name: Nombre de la herramienta
            formatter_func: Función que toma los datos y retorna string formateado
        """
        self.manual_formatters[tool_name] = formatter_func
    
    def register_formatters(self, formatters_dict: Dict[str, Callable[[Dict[str, Any]], str]]):
        """
        Registra múltiples formateadores manuales a la vez.
        
        Args:
            formatters_dict: Diccionario de {tool_name: formatter_func}
        """
        self.manual_formatters.update(formatters_dict)
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo JSON."""
        if not self.config_path:
            return {"formatters": {}}
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando configuración de formateadores: {e}")
            return {"formatters": {}}
    
    def get_formatter_function(self, tool_name: str):
        """
        Retorna una función formateadora para la herramienta específica.
        
        Args:
            tool_name: Nombre de la herramienta
            
        Returns:
            Función que toma datos y retorna markdown formateado
        """
        def formatter_func(data: Dict[str, Any]) -> str:
            return self.format_response(tool_name, data)
        
        return formatter_func
    
    def format_response(self, tool_name: str, data: Dict[str, Any]) -> str:
        """
        Formatea una respuesta usando formatters manuales, configuración JSON, o formato por defecto.
        
        Args:
            tool_name: Nombre de la herramienta
            data: Datos de respuesta
            
        Returns:
            String formateado en markdown
        """
        # Primero buscar formateador manual registrado
        if tool_name in self.manual_formatters:
            try:
                return self.manual_formatters[tool_name](data)
            except Exception as e:
                return f"❌ Error en formateador manual para {tool_name}: {e}\n\n{self._default_format(tool_name, data)}"
        
        # Luego buscar en configuración JSON
        config = self.formatters_config.get("formatters", {}).get(tool_name)
        if config:
            try:
                format_type = config.get("format_type", "default")
                
                if format_type == "table":
                    return self._format_table(config, data)
                elif format_type == "single_item":
                    return self._format_single_item(config, data)
                elif format_type == "list":
                    return self._format_list(config, data)
                elif format_type == "cards":
                    return self._format_cards(config, data)
                elif format_type == "success":
                    return self._format_success(config, data)
                else:
                    return self._default_format(tool_name, data)
                    
            except Exception as e:
                return f"❌ Error en formateador configurado para {tool_name}: {e}\n\n{self._default_format(tool_name, data)}"
        
        # Usar formato por defecto
        return self._default_format(tool_name, data)
    
    def _format_table(self, config: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Formatea datos como una tabla markdown."""
        title = config.get("title", "Datos")
        data_key = config.get("data_key", "items")
        empty_message = config.get("empty_message", "No hay datos disponibles.")
        table_config = config.get("table_config", {})
        show_total = config.get("show_total", {})
        
        result = f"## {title}\n\n"
        
        items = data.get(data_key, [])
        if not items:
            return result + empty_message
        
        # Crear tabla
        headers = table_config.get("headers", [])
        columns = table_config.get("columns", [])
        
        if headers and columns:
            # Encabezados
            result += "| " + " | ".join(headers) + " |\n"
            result += "|" + "|".join(["-------"] * len(headers)) + "|\n"
            
            # Filas
            total = 0
            for item in items:
                row = []
                for col in columns:
                    value = item.get(col, "N/A")
                    row.append(str(value))
                    
                    # Calcular total si está configurado
                    if show_total.get("enabled") and col == show_total.get("column"):
                        try:
                            # Limpiar valor numérico
                            clean_value = re.sub(r'[^\d.,]', '', str(value))
                            clean_value = clean_value.replace(',', '.')
                            total += float(clean_value)
                        except (ValueError, TypeError):
                            pass
                
                result += "| " + " | ".join(row) + " |\n"
            
            # Mostrar total si está configurado
            if show_total.get("enabled") and total > 0:
                currency = show_total.get("currency", "")
                result += f"\n**Total:** {total:.2f}{currency}\n"
        
        return result
    
    def _format_single_item(self, config: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Formatea un solo elemento con campos específicos."""
        title = config.get("title", "Información")
        data_key = config.get("data_key", "")
        fields = config.get("fields", [])
        nested_lists = config.get("nested_lists", [])
        
        result = f"## {title}\n\n"
        
        # Si data_key está vacío, usar los datos directamente
        if data_key == "":
            item = data
        else:
            item = data.get(data_key, {})
            
        if not item:
            return result + "No se encontraron datos."
        
        # Crear un layout en lista con mejor separación visual
        for field in fields:
            key = field.get("key")
            label = field.get("label", key)
            icon = field.get("icon", "")
            
            value = item.get(key)
            if value is not None:
                # Formato de lista con mejor espaciado visual
                if icon:
                    result += f"- **{icon} {label}:** {value}\n"
                else:
                    result += f"- **{label}:** {value}\n"
        
        # Manejar listas anidadas si están configuradas
        for nested_list in nested_lists:
            list_key = nested_list.get("key")
            list_title = nested_list.get("title", list_key)
            
            if list_key in item and item[list_key]:
                result += f"\n**{list_title}:**\n"
                for list_item in item[list_key]:
                    result += f"- {list_item}\n"
        
        return result
    
    def _format_list(self, config: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Formatea una lista de elementos."""
        title = config.get("title", "Lista")
        data_key = config.get("data_key", "items")
        item_format = config.get("item_format", "- {}")
        show_count = config.get("show_count", False)
        
        result = f"## {title}\n\n"
        
        # Obtener los items
        items = data.get(data_key, [])
        
        # Si data_key está vacío y data es una lista directamente
        if data_key == "" and isinstance(data, list):
            items = data
        # Si data es una lista directamente (para casos como estado_pagos)
        elif isinstance(data, list):
            items = data
        
        if not items:
            return result + "No hay elementos en la lista."
        
        if show_count:
            result += f"Se encontraron {len(items)} elementos:\n\n"
        
        for item in items:
            # Si el item es un string simple, usarlo directamente
            if isinstance(item, str):
                formatted_item = item_format.format(estado=item) if "{estado}" in item_format else item_format.format(item)
            # Si es un diccionario, usar el template
            elif isinstance(item, dict):
                formatted_item = self._format_template(item_format, item)
            else:
                formatted_item = str(item)
            
            result += formatted_item + "\n"
        
        return result
    
    def _format_cards(self, config: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Formatea datos como tarjetas."""
        title = config.get("title", "Tarjetas")
        data_key = config.get("data_key", "items")
        empty_message = config.get("empty_message", "No hay datos disponibles.")
        card_config = config.get("card_config", {})
        
        result = f"## {title}\n\n"
        
        items = data.get(data_key, [])
        if not items:
            return result + empty_message
        
        for item in items:
            # Título de la tarjeta
            card_title = card_config.get("title", "Elemento")
            formatted_title = self._format_template(card_title, item)
            result += f"### {formatted_title}\n"
            
            # Campos de la tarjeta
            fields = card_config.get("fields", [])
            for field in fields:
                key = field.get("key", "")
                label = field.get("label", key.title())
                value = item.get(key, "N/A")
                result += f"**{label}:** {value}\n"
            
            result += "\n"
        
        return result
    
    def _format_success(self, config: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Formatea un mensaje de éxito."""
        title = config.get("title", "✅ Éxito")
        message_template = config.get("message_template", "Operación completada.")
        show_details = config.get("show_details", False)
        data_key = config.get("data_key", "result")
        
        result = f"## {title}\n\n"
        
        # Mensaje principal
        formatted_message = self._format_template(message_template, data)
        result += formatted_message + "\n"
        
        # Mostrar detalles si está configurado
        if show_details:
            item = data.get(data_key, {})
            if item:
                result += "\n### Detalles:\n"
                for key, value in item.items():
                    result += f"**{key.title()}:** {value}\n"
        
        return result
    
    def _format_template(self, template: str, data: Dict[str, Any]) -> str:
        """
        Formatea una plantilla reemplazando {key} con valores de data.
        
        Args:
            template: Plantilla con placeholders {key}
            data: Datos para reemplazar
            
        Returns:
            String con placeholders reemplazados
        """
        try:
            return template.format(**data)
        except (KeyError, TypeError):
            # Si falla el formateo, intentar reemplazar solo las claves disponibles
            result = template
            for key, value in data.items():
                result = result.replace(f"{{{key}}}", str(value))
            return result
    
    def _default_format(self, tool_name: str, data: Dict[str, Any]) -> str:
        """Formato por defecto inteligente cuando no hay configuración específica."""
        result = f"### Respuesta de {tool_name}\n\n"
        
        if isinstance(data, dict):
            # Casos especiales comunes
            if len(data) == 1 and "message" in data:
                # Respuesta simple con mensaje
                result += data["message"]
            elif len(data) == 1 and "mensaje" in data:
                # Respuesta simple con mensaje en español
                result += data["mensaje"]
            elif "error" in data:
                # Respuesta de error
                result += f"❌ Error: {data['error']}"
            elif "success" in data and data["success"]:
                # Respuesta de éxito
                result += f"✅ {data.get('message', 'Operación completada exitosamente')}"
            else:
                # Formateo genérico de diccionario
                for key, value in data.items():
                    if isinstance(value, (list, dict)):
                        result += f"**{key.title()}:**\n```json\n{json.dumps(value, ensure_ascii=False, indent=2)}\n```\n\n"
                    else:
                        result += f"**{key.title()}:** {value}\n"
        else:
            # Para datos que no son diccionarios
            result += f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
        
        return result.strip()
    
    def get_all_formatters(self) -> Dict[str, Any]:
        """
        Retorna un diccionario con todas las funciones formateadoras configuradas.
        
        Returns:
            Diccionario {tool_name: formatter_function}
        """
        formatters = {}
        
        # Agregar formatters configurados desde JSON
        for tool_name in self.formatters_config.get("formatters", {}).keys():
            formatters[tool_name] = self.get_formatter_function(tool_name)
            
        # Agregar formatters manuales
        formatters.update(self.manual_formatters)
        
        return formatters


# Instancia global del formateador unificado
GLOBAL_FORMATTER = UnifiedFormatter()


def format_tool_response(tool_name: str, data: Dict[str, Any]) -> str:
    """
    Función helper para formatear respuestas de herramientas usando el formateador global.
    
    Args:
        tool_name: Nombre de la herramienta
        data: Datos de respuesta
        
    Returns:
        String formateado
    """
    return GLOBAL_FORMATTER.format_response(tool_name, data)


# Alias para compatibilidad con el nombre anterior
ConfigurableFormatter = UnifiedFormatter
