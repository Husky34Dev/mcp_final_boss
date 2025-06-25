"""
Agente base genérico y reutilizable.
Basado en base_chat_agent.py pero con imports limpios y sin dependencias rotas.
"""
import json
import logging
import re
from typing import Optional, Dict, Any, List, Callable
from groq import Groq
from datetime import datetime

# Configurar logging exhaustivo para el agente
class AgentFlowLogger:
    """Logger especializado para auditar todo el flujo del agente."""
    
    def __init__(self, log_file='agent_flow.log'):
        self.logger = logging.getLogger('AGENT_FLOW')
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicar handlers si ya existen
        if not self.logger.handlers:
            # Handler para archivo con formato detallado
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Handler para consola con formato simple
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def log_message_received(self, user_message: str, context_before: dict):
        """Registra cuando se recibe un mensaje del usuario."""
        self.logger.info("=" * 80)
        self.logger.info(f"📨 MENSAJE RECIBIDO: {user_message}")
        self.logger.info(f"📋 CONTEXTO ANTES: {json.dumps(context_before, ensure_ascii=False, indent=2)}")
    
    def log_context_update(self, context_after: dict, is_referential: bool):
        """Registra la actualización del contexto."""
        self.logger.info(f"🔄 CONTEXTO DESPUÉS: {json.dumps(context_after, ensure_ascii=False, indent=2)}")
        self.logger.info(f"🔍 ES REFERENCIAL: {is_referential}")
    
    def log_llm_request(self, messages: list, tools: list):
        """Registra la solicitud al LLM."""
        self.logger.info(f"🤖 SOLICITUD LLM:")
        self.logger.info(f"   - Mensajes: {len(messages)} (último: {messages[-1]['content'][:100]}...)")
        self.logger.info(f"   - Herramientas disponibles: {[t.get('function', {}).get('name', 'unknown') for t in tools]}")
    
    def log_tool_calls(self, tool_calls):
        """Registra las tool calls generadas por el LLM."""
        if tool_calls:
            self.logger.info(f"🔧 TOOL CALLS GENERADOS ({len(tool_calls)}):")
            for i, call in enumerate(tool_calls, 1):
                try:
                    args = json.loads(call.function.arguments)
                    self.logger.info(f"   {i}. {call.function.name}({json.dumps(args, ensure_ascii=False)})")
                except:
                    self.logger.info(f"   {i}. {call.function.name}(argumentos no parseables)")
        else:
            self.logger.info("🔧 SIN TOOL CALLS")
    
    def log_tool_execution(self, tool_name: str, args: dict, result: str, error: Optional[str] = None):
        """Registra la ejecución de una herramienta."""
        if error:
            self.logger.error(f"❌ ERROR EN {tool_name}: {error}")
        else:
            self.logger.info(f"✅ EJECUTADO {tool_name}:")
            self.logger.info(f"   - Argumentos: {json.dumps(args, ensure_ascii=False)}")
            self.logger.info(f"   - Resultado: {result[:200]}{'...' if len(result) > 200 else ''}")
    
    def log_final_response(self, response: str, tool_executed: bool):
        """Registra la respuesta final."""
        self.logger.info(f"📤 RESPUESTA FINAL ({'con herramienta' if tool_executed else 'sin herramienta'}):")
        self.logger.info(f"   {response[:300]}{'...' if len(response) > 300 else ''}")
        self.logger.info("=" * 80)

# Instancia global del logger
flow_logger = AgentFlowLogger()


class BaseAgent:
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
                 conversation_context=None):
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
        # Usar el contexto específico si se proporciona
        self.context = conversation_context or self._create_default_context()
        
        # Importar utilidades desde el framework limpio
        from ..utils.response_guard import ResponseGuard
        from ..utils.function_handler import FunctionHandler
        from ..tools.configurable_formatter import format_tool_response
        
        self.response_guard = ResponseGuard()
        self.function_handler = FunctionHandler(self.handlers)

    def _create_default_context(self):
        """Crea un contexto por defecto simple."""
        from .context import SimpleContext
        return SimpleContext()

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

    def handle_message(self, user_message: str) -> str:
        """
        Procesa un mensaje de usuario manteniendo el contexto de la conversación.
        
        Args:
            user_message: El mensaje del usuario
            
        Returns:
            str: La respuesta del sistema
        """
        # Capturar contexto antes de procesar
        context_before = self.context.as_dict().copy()
        
        # Registrar mensaje recibido
        flow_logger.log_message_received(user_message, context_before)
        
        # Respuestas genéricas para saludos y despedidas
        clean_msg = user_message.strip().lower()
        if clean_msg in ['hola', 'buenos días', 'buenos dias', 'buenas tardes', 'buenas noches']:
            response = "¡Hola! Solo escribe tu pregunta para que pueda ayudarte."
            flow_logger.log_final_response(response, False)
            return response
        if clean_msg in ['adiós', 'adios', 'hasta luego', 'chao', 'chau']:
            response = "¡Hasta luego! Si necesitas algo más, vuelve cuando quieras."
            flow_logger.log_final_response(response, False)
            return response
        
        try:
            # Actualizar contexto
            self.context.update(user_message)
            context_after = self.context.as_dict().copy()
            is_referential = self.context.get('is_referential', False)
            
            # Registrar actualización de contexto
            flow_logger.log_context_update(context_after, is_referential)
            
            logging.debug(f"Context after update: {context_after}")

            # Validar el contexto para campos requeridos
            validation_result = self.context.validate_context()
            if validation_result:
                logging.warning(f"Missing context fields: {validation_result}")
                # Si force_tool_usage está activo y faltan campos requeridos, devolver mensaje de error
                if self.force_tool_usage:
                    # Devuelve el primer mensaje de error encontrado
                    for field, message in validation_result.items():
                        flow_logger.log_final_response(message, False)
                        return message

            # Construir el mensaje del usuario con contexto referencial si es necesario
            enhanced_message = user_message
            if self.context.get('is_referential'):
                referential_prompt = self.context.get_referential_prompt()
                if referential_prompt:
                    enhanced_message = f"{referential_prompt}\\n\\n**Consulta del usuario:** {user_message}"
                    logging.info(f"Enhanced message with referential context: {enhanced_message}")

            self.messages.append({"role": "user", "content": enhanced_message})
            logging.info(f"User message: {user_message}")
            
            # Registrar solicitud al LLM
            flow_logger.log_llm_request(self.messages, self.tools)
            
            logging.info("Sending initial request to LLM with tools...")

            resp = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,  # type: ignore[arg-type]
                tools=self.tools,  # type: ignore[arg-type]
                tool_choice="auto"
            )
            msg = resp.choices[0].message
            logging.info(f"Received response: {msg}")
            
            # Registrar tool calls si existen
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                # NUEVO: Forzar uso del contexto antes de registrar
                msg.tool_calls = self._force_context_arguments(msg.tool_calls)
                flow_logger.log_tool_calls(msg.tool_calls)
            else:
                flow_logger.log_tool_calls(None)

            executed_calls = set()
            retry_limit = 5
            retry_count = 0

            # Procesar tool_calls
            tool_call_executed = False
            
            while hasattr(msg, "tool_calls") and msg.tool_calls and retry_count < retry_limit:
                new_calls = self._prepare_tool_calls(msg.tool_calls, executed_calls)
                if not new_calls:
                    break

                for call, args in new_calls:
                    fn_name = call.function.name
                    try:
                        # Usar los argumentos tal como los genera el LLM
                        result = self.handlers[fn_name](**args)
                        logging.info(f"Raw tool response for {fn_name}: {result}")
                        from ..tools.configurable_formatter import format_tool_response
                        markdown_result = format_tool_response(fn_name, result)
                        tool_call_executed = True
                        
                        # Registrar ejecución exitosa
                        flow_logger.log_tool_execution(fn_name, args, markdown_result)
                        
                    except Exception as e:
                        logging.error(f"Error ejecutando {fn_name}: {e}")
                        markdown_result = f"Error ejecutando {fn_name}: {str(e)}"
                        
                        # Registrar error en ejecución
                        flow_logger.log_tool_execution(fn_name, args, "", str(e))

                    if tool_call_executed:
                        final_content = markdown_result.strip()
                        self.messages.append({"role": "assistant", "content": final_content})
                        logging.info("Final response prepared (tool_call only, markdown returned).")
                        self._trim_history()
                        
                        # Registrar respuesta final
                        flow_logger.log_final_response(final_content, True)
                        
                        return final_content

                retry_count += 1

            if retry_count >= retry_limit:
                logging.error("Límite de reintentos superado.")
                raise RuntimeError("Límite de reintentos superado.")

            # Manejar respuesta de texto
            if msg.content:
                content_str = msg.content.strip()
                
                # NUEVO: Detectar si el LLM está simulando tool calls en lugar de usarlas realmente
                if self._is_simulating_tool_calls(content_str) and self.force_tool_usage:
                    logging.warning("🚨 LLM está simulando tool calls - Forzando respuesta con validación de contexto")
                    
                    # En lugar de retry, forzar una respuesta de error que mencione los datos requeridos
                    context_data = self.context.as_dict()
                    dni_contexto = context_data.get('dni')
                    
                    if dni_contexto and context_data.get('is_referential'):
                        error_msg = f"No pude procesar tu consulta correctamente. El DNI en contexto es {dni_contexto}. Por favor, reformula tu pregunta."
                        flow_logger.log_final_response(error_msg, False)
                        return error_msg
                
                # Procesar funciones inline normales
                inline_result = self.function_handler.handle_inline_function(content_str)
                if inline_result:
                    self.messages.append({"role": "assistant", "content": inline_result})
                    self._trim_history()
                    
                    # Registrar respuesta con función inline
                    flow_logger.log_final_response(inline_result, True)
                    
                    return inline_result

            # Validar DNI antes de ejecutar herramientas (solo si está configurado force_tool_usage)
            if self.force_tool_usage and 'dni' in self.context.as_dict():
                dni = self.context.get('dni')
                # Regex corregido para DNI español: 8 dígitos seguidos de una letra
                if not re.match(r'^\d{8}[A-Za-z]$', dni):
                    logging.warning(f"Partial or invalid DNI detected: {dni}")
                    # No forzar error si el DNI no es válido, dejar que el LLM maneje la situación

            # Forzar uso de herramientas si está configurado
            if self.force_tool_usage and not tool_call_executed:
                # Verificar si hay campos faltantes antes de forzar error
                validation_result = self.context.validate_context()
                if validation_result:
                    # Si faltan campos requeridos, devolver mensaje de error en lugar de RuntimeError
                    for field, message in validation_result.items():
                        logging.warning(f"Cannot force tool usage due to missing field: {field}")
                        flow_logger.log_final_response(message, False)
                        return message
                else:
                    # Solo forzar error si no hay problemas de validación
                    logging.warning("Tool usage was enforced but no tool was executed")
                    # En lugar de error, permitir que el LLM responda sin herramientas
                    # raise RuntimeError("Tool usage was enforced but no tool was executed.")

            final_content = msg.content or ""
            self.messages.append({"role": "assistant", "content": final_content})
            logging.info(f"Final response prepared: {final_content}")
            self._trim_history()

            # Validar si la respuesta es válida según el guardián
            error = self.response_guard.validate(user_message, final_content, tool_call_executed)
            if error:
                logging.warning(f"Respuesta rechazada por ResponseGuard: {error}")
                flow_logger.log_final_response(error, False)
                return error
            
            # Registrar respuesta final sin herramientas
            flow_logger.log_final_response(final_content, tool_call_executed)
                
            return final_content
            
        except Exception as e:
            logging.error(f"Error inesperado procesando el mensaje: {e}", exc_info=True)
            error_response = "Lo siento, ocurrió un error interno al procesar tu solicitud. Por favor, inténtalo de nuevo más tarde."
            flow_logger.log_final_response(f"ERROR: {str(e)}", False)
            return error_response

    def _prepare_tool_calls(self, tool_calls, executed_calls):
        """Prepara llamadas a herramientas evitando duplicados."""
        new_calls = []
        for call in tool_calls:
            call_id = call.id
            if call_id in executed_calls:
                continue
            
            executed_calls.add(call_id)
            
            try:
                args = json.loads(call.function.arguments)
                new_calls.append((call, args))
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing tool call arguments: {e}")
                continue
                
        return new_calls

    def _force_context_arguments(self, tool_calls):
        """
        Pre-procesa los tool_calls para forzar el uso del contexto cuando está disponible.
        Esto evita que el LLM invente argumentos cuando ya tenemos el contexto.
        """
        if not tool_calls:
            return tool_calls
            
        # Obtener contexto actual
        context_data = self.context.as_dict()
        dni_contexto = context_data.get('dni')
        is_referential = context_data.get('is_referential', False)
        
        if not dni_contexto or not is_referential:
            # Si no hay DNI en contexto o no es referencial, no modificar
            return tool_calls
            
        # Pre-procesar cada tool_call
        for call in tool_calls:
            try:
                args = json.loads(call.function.arguments)
                original_args = args.copy()
                
                # Si la herramienta necesita DNI y tenemos uno en contexto
                if 'dni' in args and dni_contexto:
                    if args['dni'] != dni_contexto:
                        logging.warning(f"🔧 CONTEXTO FORZADO: Cambiando DNI de '{args['dni']}' a '{dni_contexto}'")
                        args['dni'] = dni_contexto
                        # Actualizar los argumentos del tool_call
                        call.function.arguments = json.dumps(args, ensure_ascii=False)
                        
                        # Log para auditoría
                        flow_logger.logger.info(f"🔧 ARGUMENTOS CORREGIDOS:")
                        flow_logger.logger.info(f"   - Original: {original_args}")
                        flow_logger.logger.info(f"   - Corregido: {args}")
                        
            except (json.JSONDecodeError, AttributeError) as e:
                logging.error(f"Error al procesar argumentos del tool_call: {e}")
                continue
                
        return tool_calls

    def _is_simulating_tool_calls(self, content: str) -> bool:
        """
        Detecta si el LLM está simulando tool calls en lugar de usarlos realmente.
        """
        # Patrones que indican simulación de funciones
        simulation_patterns = [
            r'<function=',  # <function=nombre_funcion>
            r'function\s*=',  # function = nombre
            r'```.*function.*```',  # bloques de código con función
            r'\{.*"function".*\}',  # JSON con función simulada
        ]
        
        for pattern in simulation_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                return True
                
        return False
