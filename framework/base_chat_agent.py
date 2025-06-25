"""
⚠️ DEPRECATED - ARCHIVO DUPLICADO ⚠️

Este archivo está duplicado con framework/core/agent.py
Use framework/core/agent.BaseAgent en su lugar.

Este archivo será eliminado en futuras versiones.

---

Agente de chat base genérico y reutilizable.
Este módulo contiene la lógica core de conversación que es independiente del dominio.
"""
import json
import logging
import re
from typing import Optional, Dict, Any, List, Callable
from groq import Groq
from framework.tools import format_tool_response
from framework.tool_executor import ToolExecutor  
from framework.inline_function_handler import InlineFunctionHandler
from framework.core.generic_context import GenericConversationContext
from framework.llm_response_guard import LLMResponseGuard


class BaseChatAgent:
    """
    Agente de chat base genérico que puede ser reutilizado en cualquier dominio.
    
    Esta clase contiene toda la lógica core de conversación, manejo de herramientas,
    y procesamiento de mensajes, pero es independiente de cualquier dominio específico.
    """
    
    def __init__(self, 
                 model: str,
                 tools_fetcher: Callable[[Optional[str]], List[Dict[str, Any]]],
                 handlers_generator: Callable[[List[Dict[str, Any]]], Dict[str, Any]],
                 agent_id: Optional[str] = None,
                 force_tool_usage: Optional[bool] = None,
                 logger_config: Optional[Dict[str, Any]] = None,
                 conversation_context: Optional[GenericConversationContext] = None):
        """
        Inicializa el agente base.
        
        Args:
            model: Nombre del modelo LLM a usar
            tools_fetcher: Función que obtiene herramientas para un agente específico
            handlers_generator: Función que genera handlers para las herramientas
            agent_id: ID del agente (opcional)
            force_tool_usage: Si forzar el uso de herramientas
            logger_config: Configuración del logger (opcional)
            conversation_context: Contexto de conversación específico (opcional)
        """
        self.client = Groq()
        self.model = model
        self.agent_id = agent_id
        
        # Configurar logging si se proporciona
        if logger_config:
            logging.basicConfig(**logger_config)
        
        # Obtener herramientas usando la función proporcionada
        self.tools = tools_fetcher(agent_id)
        logging.info(f"Loaded {len(self.tools)} tools for agent: {agent_id or 'default'}")
        
        # Generar handlers usando la función proporcionada
        self.handlers = handlers_generator(self.tools)
        
        self.force_tool_usage = force_tool_usage or False
        self.messages = []
        # Usar el contexto específico si se proporciona, sino usar el genérico
        self.context = conversation_context or GenericConversationContext()
        self.response_guard = LLMResponseGuard()
        self.tool_executor = ToolExecutor(self.handlers)
        self.inline_function_handler = InlineFunctionHandler(self.handlers)

    def _trim_history(self, max_pairs: int = 3) -> None:
        """
        Mantiene sólo los últimos `max_pairs` de mensajes de usuario y respuestas,
        siempre incluyendo el primer prompt de sistema.
        """
        if not self.messages:
            return
        system = self.messages[0]
        rest = self.messages[1:]
        # Recortar a los últimos max_pairs*2 mensajes
        trimmed = rest[-(max_pairs * 2):] if rest else []
        self.messages = [system] + trimmed

    def set_system_prompt(self, prompt: str):
        """Establece el prompt del sistema."""
        self.messages = [{"role": "system", "content": prompt}]

    def _handle_greetings(self, message: str) -> Optional[str]:
        """
        Devuelve una respuesta para saludos o despedidas, o None si no aplica.
        """
        clean = message.strip().lower()
        greetings = ['hola', 'buenos días', 'buenos dias', 'buenas tardes', 'buenas noches']
        farewells = ['adiós', 'adios', 'hasta luego', 'chao', 'chau']
        if clean in greetings:
            return "¡Hola! Solo escribe tu pregunta para que pueda ayudarte."
        if clean in farewells:
            return "¡Hasta luego! Si necesitas algo más, vuelve cuando quieras."
        return None

    def handle_message_with_context(self, user_message: str) -> str:
        """
        Procesa un mensaje de usuario manteniendo el contexto de la conversación.
        
        Args:
            user_message: El mensaje del usuario
            
        Returns:
            str: La respuesta del sistema, que puede ser un mensaje de error de validación
                 o la respuesta del LLM
        """
        # Manejo de saludos y despedidas
        greeting = self._handle_greetings(user_message)
        if greeting:
            return greeting
        
        try:
            self.context.update(user_message)
            logging.debug(f"Context after update: {self.context.as_dict()}")

            # Validar el contexto para campos requeridos
            validation_result = self.context.validate_context()
            if validation_result:
                logging.warning(f"Missing context fields: {validation_result}")
                # Devuelve el primer mensaje de error encontrado
                for field, message in validation_result.items():
                    return message

            # Construir el mensaje del usuario con contexto referencial si es necesario
            enhanced_message = user_message
            if self.context.get('is_referential'):
                referential_prompt = self.context.get_referential_prompt()
                if referential_prompt:
                    enhanced_message = f"{referential_prompt}\n\n**Consulta del usuario:** {user_message}"
                    logging.info(f"Enhanced message with referential context: {enhanced_message}")

            self.messages.append({"role": "user", "content": enhanced_message})
            logging.info(f"User message: {user_message}")
            logging.info("Sending initial request to LLM with tools...")

            resp = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,  # type: ignore[arg-type]
                tools=self.tools,  # type: ignore[arg-type]
                tool_choice="auto"
            )
            msg = resp.choices[0].message
            logging.info(f"Received response: {msg}")

            executed_calls = set()
            retry_limit = 5
            retry_count = 0

            # Procesar tool_calls y luego solicitar respuesta de texto puro
            tool_call_executed = False
            
            while hasattr(msg, "tool_calls") and msg.tool_calls and retry_count < retry_limit:
                new_calls = self.tool_executor.prepare_tool_calls(msg.tool_calls, executed_calls)
                if not new_calls:
                    break

                for call, args in new_calls:
                    fn_name = call.function.name
                    try:
                        result = self.handlers[fn_name](**args)
                        logging.info(f"Raw tool response for {fn_name}: {result}")
                        markdown_result = format_tool_response(fn_name, result)
                        tool_call_executed = True
                    except Exception as e:
                        logging.error(f"Error ejecutando {fn_name}: {e}")
                        markdown_result = f"Error ejecutando {fn_name}: {str(e)}"

                    if tool_call_executed:
                        final_content = markdown_result.strip()
                        self.messages.append({"role": "assistant", "content": final_content})
                        logging.info("Final response prepared (tool_call only, markdown returned).")
                        logging.info(f"Final Markdown content: {final_content}")
                        self._trim_history()
                        return final_content

                retry_count += 1
                logging.info(f"Sending retry {retry_count}/{retry_limit} for pure text completion...")
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,  # type: ignore[arg-type]
                    tools=self.tools,  # type: ignore[arg-type]
                    tool_choice="none"
                )
                msg = resp.choices[0].message
                logging.info(f"Received response: {msg}")

            if retry_count >= retry_limit:
                logging.error("Límite de reintentos superado.")
                raise RuntimeError("Límite de reintentos superado.")

            if msg.content:
                content_str = msg.content.strip()
                inline_result = self.inline_function_handler.handle_inline_function(content_str)
                if inline_result:
                    self.messages.append({"role": "assistant", "content": inline_result})
                    self._trim_history()
                    return inline_result

            # Enforce tool usage if configured
            if self.force_tool_usage and not tool_call_executed:
                raise RuntimeError("Tool usage was enforced but no tool was executed.")

            final_content = msg.content or ""
            self.messages.append({"role": "assistant", "content": final_content})
            logging.info(f"Final response prepared: {final_content}")
            self._trim_history()

            # Validar si la respuesta es válida según el guardián
            error = self.response_guard.validate(user_message, final_content, tool_call_executed)
            if error:
                logging.warning(f"Respuesta rechazada por LLMResponseGuard: {error}")
                return error
                
            return final_content
            
        except Exception as e:
            logging.error(f"Error inesperado procesando el mensaje: {e}", exc_info=True)
            return "Lo siento, ocurrió un error interno al procesar tu solicitud. Por favor, inténtalo de nuevo más tarde."
