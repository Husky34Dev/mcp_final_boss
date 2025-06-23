import json
import logging
import re
from groq import Groq
from ..utils.handlers_and_tools import fetch_tools, generate_handlers
from app.utils.formatter import format_tool_response
from app.utils.conversation_context import ConversationContext
from app.utils.llm_response_guard import LLMResponseGuard

# Configuración del logger para SharedChatAgent
logging.basicConfig(
    filename="chat_agent.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class SharedChatAgent:
    def __init__(self, model: str, force_tool_usage: bool = False):
        self.client = Groq()
        self.model = model
        self.tools = fetch_tools()
        self.handlers = generate_handlers(self.tools)
        self.messages = []
        self.context = ConversationContext()  # Contexto conversacional
        self.response_guard = LLMResponseGuard()  # Validador de respuestas
        # Propiedad para forzar el uso de herramientas
        self.force_tool_usage = False

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
        self.messages = [{"role": "system", "content": prompt}]
        # self.context.clear()  # No limpiar contexto al cambiar de sistema, para mantener memoria referencial

    def handle_message_with_context(self, user_message: str) -> str:
        """
        Procesa un mensaje de usuario manteniendo el contexto de la conversación.
        
        Args:
            user_message: El mensaje del usuario
            
        Returns:
            str: La respuesta del sistema, que puede ser un mensaje de error de validación
                 o la respuesta del LLM
        """
        # Respuestas genéricas para saludos y despedidas
        clean_msg = user_message.strip().lower()
        if clean_msg in ['hola', 'buenos días', 'buenos dias', 'buenas tardes', 'buenas noches']:
            return "¡Hola! Solo escribe tu pregunta para que pueda ayudarte con facturas, datos del abonado o incidencias."
        if clean_msg in ['adiós', 'adios', 'hasta luego', 'chao', 'chau']:
            return "¡Hasta luego! Si necesitas algo más, vuelve cuando quieras."
        # Continúa con el flujo normal
        try:
            self.context.update(user_message)  # Actualiza el contexto con el mensaje
            logging.debug(f"Context after update: {self.context.as_dict()}")

            # Validar el contexto para campos requeridos
            validation_result = self.context.validate_context()
            if validation_result:
                logging.warning(f"Missing context fields: {validation_result}")
                # Devuelve el primer mensaje de error encontrado
                for field, message in validation_result.items():
                    return message

            # Si la consulta es referencial y hay un DNI en el contexto, inyecta el bloque generado
            if self.context.get('is_referential') and self.context.get('dni'):
                referential_prompt = self.context.get_referential_prompt()
                self.messages.append({"role": "system", "content": referential_prompt})
                logging.debug(f"Referential prompt injected: {referential_prompt}")

            self.messages.append({"role": "user", "content": user_message})
            logging.info(f"User message: {user_message}")
            logging.info("Sending initial request to LLM with tool_choice='auto'...")

            resp = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,  # type: ignore[arg-type]
                tools=self.tools,
                tool_choice="auto"
            )
            msg = resp.choices[0].message
            logging.info(f"Received response: {msg}")

            executed_calls = set()
            retry_limit = 5
            retry_count = 0

            # Procesar tool_calls y luego solicitar respuesta de texto puro
            tool_call_executed = False
            # Solo iterar tool_calls si existe y es lista no vacía
            while hasattr(msg, "tool_calls") and msg.tool_calls and retry_count < retry_limit:
                new_calls = []
                for call in msg.tool_calls:
                    fn_name = call.function.name
                    args = json.loads(call.function.arguments)

                    # Validar si args es None antes de usarlo
                    if args is None or not isinstance(args, dict):
                        logging.error(f"Invalid arguments for function {fn_name}: {args}. Skipping execution.")
                        continue

                    sig = (fn_name, tuple(sorted(args.items())))
                    if sig in executed_calls:
                        logging.info(f"Detección de llamada repetida: {fn_name} {args}. Rompiendo bucle.")
                        new_calls = []
                        break
                    executed_calls.add(sig)
                    new_calls.append((call, args))

                if not new_calls:
                    break

                markdown_result = ""  # Inicializar resultado markdown
                # Ejecuta cada nueva llamada y añade al historial
                for call, args in new_calls:
                    logging.info(f"Executing tool: {call.function.name} with args: {args}")
                    try:
                        result = self.handlers[call.function.name](**args)
                        logging.info(f"Raw tool response for {call.function.name}: {result}")
                        formatted_result = format_tool_response(call.function.name, result)
                        markdown_result = formatted_result  # Devuelve el markdown puro
                        payload = json.dumps(result, ensure_ascii=False)
                        tool_call_executed = True
                    except Exception as e:
                        logging.error(f"Error ejecutando {call.function.name}: {e}")
                        markdown_result = f"Error ejecutando {call.function.name}: {str(e)}"
                        payload = json.dumps({"error": str(e)}, ensure_ascii=False)

                    self.messages.append({
                        "role": "tool",
                        "name": call.function.name,
                        "content": payload,
                        "tool_call_id": call.id
                    })

                # Si ejecutamos una tool, devolvemos el markdown directamente y no pedimos integración al LLM
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
                    tools=self.tools,
                    tool_choice="none"
                )
                msg = resp.choices[0].message
                logging.info(f"Received response: {msg}")

            if retry_count >= retry_limit:
                logging.error("Límite de reintentos superado.")
                raise RuntimeError("Límite de reintentos superado.")

            # Manejar inline function 
            if msg.content:
                content_str = msg.content.strip()
                inline = re.match(r'<function=(\w+)>(\{.*\})\[/function\]', content_str)
                if not inline:
                    inline = re.match(r'<(\w+)>(\{.*\})</\1>', content_str)
                if inline:
                    fn_name, args_json = inline.group(1), inline.group(2)
                    try:
                        args = json.loads(args_json)
                        result = self.handlers[fn_name](**args)
                        formatted_result = format_tool_response(fn_name, result).strip()
                        self.messages.append({"role": "tool", "name": fn_name, "content": json.dumps(result, ensure_ascii=False)})
                        self.messages.append({"role": "assistant", "content": formatted_result})
                        self._trim_history()
                        return formatted_result
                    except Exception as e:
                        logging.error(f"Error executing inline function {fn_name}: {e}")
            # Now enforce tool usage if configured
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
            # Mensaje elegante para el usuario
            return "Lo siento, ocurrió un error interno al procesar tu solicitud. Por favor, inténtalo de nuevo más tarde."