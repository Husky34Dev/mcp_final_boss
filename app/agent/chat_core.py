# chat_core.py
import json
import httpx
import logging
import sys
from typing import Any, Dict, List, Optional, TypedDict, cast

from groq import Groq
from groq.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam
)

from config import GROQ_API_KEY, MODEL, TOOL_URL_TEMPLATE
from app.tools.tools import fetch_tools
from app.utils.formatter import format_tool_response
from app.utils.context_validator import ContextValidator

# Configuración del logger
logger = logging.getLogger("chat_agent")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("chat_agent.log", encoding="utf-8")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger.addHandler(sh)

class ChatAgent:
    def __init__(self, tools: Optional[List[str]] = None, context: Optional[Dict[str, Any]] = None, system_prompt: Optional[str] = None):
        logger.debug(f"[INIT] Inicializando ChatAgent con tools={tools}, context={context}, system_prompt={system_prompt}")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.context = context if context is not None else {}
        self.context_validator = ContextValidator()
        
        # Inicialización de herramientas
        all_tools = fetch_tools()
        selected = tools if tools else [tool["name"] for tool in all_tools]
        self.active_tools = [t for t in all_tools if t["name"] in selected]
        self.tool_names = [tool["name"] for tool in self.active_tools]
        logger.debug(f"[INIT] Herramientas activas: {self.tool_names}")
        
        # Configuración de herramientas para Groq
        self.groq_tools: List[Any] = cast(List[Any], [
            {"type": "function", "function": {"name": tool["name"], "description": tool["description"], "parameters": tool["input_schema"]}}
            for tool in self.active_tools
        ])
        
        # Configuración del prompt de sistema
        default_system_prompt = (
            "Eres un asistente de soporte interno para operadores de una compañía de servicios. "
            "\n\nREGLAS CRÍTICAS:"
            "\n1. NUNCA generes o inventes datos. Todos los datos deben venir de las herramientas disponibles."
            "\n2. SIEMPRE usa una herramienta cuando necesites obtener datos."
            "\n3. Si una consulta requiere datos y no puedes obtenerlos, indica que no puedes acceder a esa información."
            "\n4. Formatea las respuestas en Markdown profesional."
            "\n5. IMPORTANTE: Cuando te pidan 'todos los datos', usa SÓLO la herramienta datos_abonado."
            "\n6. NO LLAMES a múltiples herramientas en secuencia a menos que la consulta específicamente lo requiera."
            "\n7. Si necesitas datos específicos:"
            "\n   - Para datos generales: usa SOLO datos_abonado"
            "\n   - Para facturas pendientes: usa SOLO facturas_pendientes"
            "\n   - Para todas las facturas: usa SOLO todas_las_facturas"
            "\n   - Para dirección: usa SOLO direccion_abonado"
            "\n   - Para incidencias: usa SOLO incidencias_por_dni"
            "\n8. CRÍTICO: En consultas referenciales (ej: 'sus facturas', 'y ahora dame...'), "
            "\n   usa SIEMPRE el DNI del contexto actual y NO el de consultas anteriores."
        )
        
        # Revertir completamente el manejo de system_message y messages_history
        self.system_message = {
            "role": "system",
            "content": system_prompt if system_prompt else default_system_prompt
        }
        self.messages_history: List[Dict[str, str]] = []

    def _validate_tool_calls(self, tool_calls: List[Any], user_input: str) -> Optional[str]:
        """Valida las llamadas a herramientas para evitar llamadas múltiples innecesarias."""
        if not tool_calls:
            return None
            
        tool_names = [call.function.name for call in tool_calls]
        logger.debug(f"[TOOL] Validando llamadas: {tool_names}")
            
        # Para consultas generales, forzar uso de datos_abonado
        if self.context_validator.is_general_query(user_input):
            logger.debug("[TOOL] Detectada consulta general")
            if "datos_abonado" not in tool_names or len(tool_names) > 1:
                logger.warning("[TOOL] Consulta general debe usar solo datos_abonado")
                return "Para consultas generales, por favor usa solo la herramienta datos_abonado."
            return None
            
        # Si hay más de una llamada, verificar si son realmente necesarias
        if len(tool_calls) > 1:
            logger.warning(f"[TOOL] Múltiples llamadas detectadas: {tool_names}")
            
            # Evitar mezclar herramientas de diferentes tipos
            factura_tools = {"facturas_pendientes", "todas_las_facturas", "deuda_total"}
            incidencia_tools = {"incidencias_por_dni", "incidencias_por_ubicacion"}
            
            if any(t in tool_names for t in factura_tools) and any(t in tool_names for t in incidencia_tools):
                logger.warning("[TOOL] Mezclando tipos de consulta")
                return "Por favor, separa las consultas de facturas e incidencias en preguntas diferentes."
                
            # Si hay más de 2 llamadas del mismo tipo, probablemente es innecesario
            if len(set(tool_names).intersection(factura_tools)) > 2 or len(set(tool_names).intersection(incidencia_tools)) > 2:
                logger.warning(f"[TOOL] Demasiadas llamadas del mismo tipo")
                return "Por favor, sé más específico en tu consulta. ¿Qué información exactamente necesitas?"
                
        return None

    def _validate_tool_arguments(self, args: Dict[str, Any], tool_name: str, user_input: str) -> tuple[Dict[str, Any], Optional[str]]:
        """
        Valida y normaliza los argumentos antes de llamar a una herramienta.
        
        Args:
            args: Argumentos de la herramienta
            tool_name: Nombre de la herramienta
            user_input: Mensaje del usuario para detectar si es referencial
        """
        logger.debug(f"[TOOL] Validando argumentos para {tool_name}: {args}")
        
        # Determinar si es una consulta referencial
        is_referential = self.context_validator.is_referential_query(user_input)
        if is_referential:
            logger.debug("[TOOL] Detectada consulta referencial - Forzando DNI del contexto")
            
        return self.context_validator.validate_dni(args, self.context, is_referential)

    def _execute_tool(self, tool_call: Any, user_input: str) -> tuple[Optional[str], Optional[Dict]]:
        """
        Ejecuta una llamada a herramienta y retorna el resultado.
        
        Args:
            tool_call: Llamada a la herramienta de Groq
            user_input: Mensaje original del usuario para validación de contexto
        """
        try:
            args = json.loads(tool_call.function.arguments)
            logger.debug(f"[TOOL] Argumentos parseados para {tool_call.function.name}: {args}")
            
            args, error = self._validate_tool_arguments(args, tool_call.function.name, user_input)
            if error:
                return error, None
                
            tool = next((t for t in self.active_tools if t["name"] == tool_call.function.name), None)
            if not tool:
                return f"❌ Herramienta no encontrada: {tool_call.function.name}", None
                
            logger.debug(f"[TOOL] Llamando endpoint: {tool['endpoint']} con args: {args}")
            r = httpx.post(TOOL_URL_TEMPLATE.format(tool["endpoint"]), json=args)
            r.raise_for_status()
            tool_response = r.json()
            logger.debug(f"[TOOL] Respuesta de {tool_call.function.name}: {tool_response}")
            
            content = format_tool_response(tool_call.function.name, tool_response)
            return content, tool_response
                
        except Exception as e:
            logger.error(f"[ERROR] Error ejecutando herramienta {tool_call.function.name}: {e}")
            return f"❌ Error al ejecutar herramienta {tool_call.function.name}: {e}", None

    def handle_message_with_context(self, user_input: str) -> tuple[str, Optional[Dict]]:
        """Procesa un mensaje del usuario y retorna la respuesta junto con cualquier dato adicional."""
        logger.debug(f"[HANDLE] Mensaje recibido: {user_input}")

        # Actualizar contexto y mensaje
        user_input, context_updated = self.context_validator.update_context(user_input, self.context)
        logger.debug(f"[HANDLE] Contexto actualizado: {self.context}")
        if not context_updated:
            return "Por favor, proporciona la información necesaria para procesar tu consulta.", None
            
        # Añadir mensaje del usuario al historial
        self.messages_history.append({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[self.system_message] + self.messages_history,
                tools=self.groq_tools,
                tool_choice="required",  # Forzar uso de herramientas
                max_tokens=1024,
            )
            
            msg = response.choices[0].message
            tool_calls = getattr(msg, "tool_calls", None)
            
            if tool_calls:
                logger.debug(f"[HANDLE] Tool calls solicitados: {[call.function.name for call in tool_calls]}")
                
                if error := self._validate_tool_calls(tool_calls, user_input):
                    return error, None
                    
                content, response = self._execute_tool(tool_calls[0], user_input)
                if content:
                    self.messages_history.append({"role": "assistant", "content": content})
                    return content, response
                else:
                    return "❌ Error ejecutando la herramienta.", None
            else:
                return "❌ No se pudo determinar qué herramienta usar. Por favor, sé más específico.", None
                
        except Exception as e:
            logger.error(f"[ERROR] Error general: {e}")
            return f"❌ Error: {e}", None

    def handle_message(self, message: str) -> str:
        """Wrapper simple para handle_message_with_context que solo retorna la respuesta."""
        response, _ = self.handle_message_with_context(message)
        return response