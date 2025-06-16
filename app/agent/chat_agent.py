import json
import httpx
from groq import Groq
from config import GROQ_API_KEY, MODEL, TOOL_URL_TEMPLATE
from app.tools.tools import fetch_tools
from app.utils.utils import extract_dni
import logging

# Configuración del logger
logging.basicConfig(
    filename="chat_agent.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class ChatAgent:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.tools = fetch_tools()
        self.messages = [
            {
            "role": "system",
            "content": (
                "Eres un asistente de soporte interno para operadores de una compañía de servicios. "
                "Tu función es proporcionar respuestas claras, concisas y profesionales sobre información de abonados: dirección, pagos, deudas, facturas e incidencias.\n\n"
                "Utiliza las herramientas disponibles cuando sea necesario. Sigue estas reglas:\n"
                "- Si se solicita **el historial o todas las facturas**, usa `todas_las_facturas`.\n"
                "- Si se piden **facturas pendientes**, usa `facturas_pendientes`.\n"
                "- Si se proporciona un **DNI**, puedes usar herramientas como `datos_abonado`, `deuda_total`, `facturas_pendientes`, etc.\n"
                "- Para **crear una incidencia**, usa `crear_incidencia` con `dni`, `ubicacion`, `descripcion` y `estado`.\n"
                "- Si se mencionan **incidencias en una ciudad o zona**, usa `incidencias_por_ubicacion`.\n"
                "- Si se solicitan **incidencias de un abonado por DNI**, usa `incidencias_por_dni`.\n\n"
                "No expliques qué herramienta estás usando. Responde únicamente con la información requerida, de forma precisa y sin repeticiones. "
                "Mantén siempre el idioma español."
            )
            }
        ]


        self.groq_tools = [{
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
        } for tool in self.tools]

    def handle_message(self, user_input: str) -> str:
        logging.info(f"Mensaje recibido: {user_input}")
        dni = extract_dni(user_input)
        if dni:
            user_input += f" (DNI detectado: {dni})"
        self.messages.append({"role": "user", "content": user_input})

        try:
            logging.info(f"Parámetros enviados a Groq: {self.messages}")
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=self.groq_tools,
                tool_choice="auto",
                max_tokens=4096,
            )
        except Exception as e:
            return f"❌ Error en Groq: {str(e)}"

        msg = response.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        if tool_calls:
            self.messages.append(msg)
            failed_tools = set()
            calls_this_turn = 0

            for call in tool_calls:
                if calls_this_turn >= 4:
                    break

                tool_name = call.function.name
                if tool_name in failed_tools:
                    continue

                try:
                    args = json.loads(call.function.arguments)
                except Exception:
                    failed_tools.add(tool_name)
                    continue

                if tool_name == "datos_abonado":
                    if not args.get("dni") and not args.get("poliza"):
                        failed_tools.add(tool_name)
                        continue
                    if "poliza" in args and args["poliza"] == "":
                        del args["poliza"]

                tool = next((t for t in self.tools if t["name"] == tool_name), None)
                if not tool:
                    failed_tools.add(tool_name)
                    continue

                try:
                    r = httpx.post(TOOL_URL_TEMPLATE.format(tool["endpoint"]), json=args)
                    r.raise_for_status()
                    result = r.json()
                    self.messages.append({
                        "tool_call_id": call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                    calls_this_turn += 1
                except Exception as e:
                    failed_tools.add(tool_name)
                    self.messages.append({
                        "tool_call_id": call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps({"error": str(e)}, ensure_ascii=False)
                    })

            try:
                final = self.client.chat.completions.create(
                    model=MODEL,
                    messages=self.messages,
                    max_tokens=4096,
                )
                self.messages.append(final.choices[0].message)
                return final.choices[0].message.content.strip()
            except Exception as e:
                return f"❌ Error final tras herramientas: {str(e)}"
        else:
            self.messages.append(msg)
            return msg.content.strip()
