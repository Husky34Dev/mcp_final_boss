# chat_core.py
import json
import httpx
import logging
from groq import Groq
from config import GROQ_API_KEY, MODEL, TOOL_URL_TEMPLATE
from app.tools.tools import fetch_tools
from app.utils.utils import extract_dni

logger = logging.getLogger("chat_agent")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("chat_agent.log", encoding="utf-8")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

class ChatAgent:
    def __init__(self, tools=None, context=None):
        self.client = Groq(api_key=GROQ_API_KEY)
        all_tools = fetch_tools()
        self.context = context if context is not None else {}

        selected = tools if tools else [tool["name"] for tool in all_tools]
        self.active_tools = [t for t in all_tools if t["name"] in selected]
        self.tool_names = [tool["name"] for tool in self.active_tools]

        self.groq_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            } for tool in self.active_tools
        ]

        self.messages = [
            {
                "role": "system",
                "content": (
                    "Eres un asistente de soporte interno para operadores de una compañía de servicios. "
                    "Tu función es proporcionar respuestas claras y profesionales sobre información de abonados. "
                    "Usa las herramientas cuando sea necesario. "
                    "Si encuentras referencias como 'este abonado', 'ese abonado', 'sus facturas', etc., "
                    "usa el último DNI guardado en el contexto."
                )
            }
        ]

    def _should_log_message(self, message: str) -> bool:
        # No logear mensajes internos del sistema o prompts de selección de agente
        return not any([
            "elige qué agente debería manejarlo" in message,
            "Responde solo con el nombre exacto del agente" in message
        ])

    def handle_message_with_context(self, user_input: str) -> tuple[str, dict | None]:
        if self._should_log_message(user_input):
            logger.info(f"Mensaje recibido: {user_input}")

        # Extraer DNI del mensaje o usar el del contexto si hay referencias
        dni = extract_dni(user_input)
        if dni:
            self.context["dni"] = dni
        elif "dni" in self.context and any(ref in user_input.lower() for ref in ["este abonado", "ese abonado", "sus", "su"]):
            # Añadir el DNI al mensaje para que las herramientas lo usen
            if not any(ref in user_input for ref in [str(self.context["dni"])]):
                user_input += f" (DNI: {self.context['dni']})"

        self.messages.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=self.groq_tools,
                tool_choice="auto",
                max_tokens=4096,
            )
        except Exception as e:
            return f"❌ Error en Groq: {str(e)}", None

        msg = response.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        if tool_calls:
            self.messages.append(msg)
            tool_response = None
            for call in tool_calls:
                tool_name = call.function.name
                try:
                    args = json.loads(call.function.arguments)
                except:
                    continue

                if tool_name == "datos_abonado" and not args.get("dni"):
                    if "dni" in self.context:
                        args["dni"] = self.context["dni"]
                    else:
                        continue

                tool = next((t for t in self.active_tools if t["name"] == tool_name), None)
                if not tool:
                    continue

                try:
                    r = httpx.post(TOOL_URL_TEMPLATE.format(tool["endpoint"]), json=args)
                    r.raise_for_status()
                    tool_response = r.json()  # Guardamos el resultado
                    self.messages.append({
                        "tool_call_id": call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(tool_response, ensure_ascii=False)
                    })
                except Exception as e:
                    error_response = {"error": str(e)}
                    self.messages.append({
                        "tool_call_id": call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(error_response, ensure_ascii=False)
                    })

            final = self.client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                max_tokens=4096,
            )
            self.messages.append(final.choices[0].message)
            return final.choices[0].message.content, tool_response
        else:
            self.messages.append(msg)
            return msg.content, None

    def handle_message(self, user_input: str) -> str:
        response, _ = self.handle_message_with_context(user_input)
        return response
