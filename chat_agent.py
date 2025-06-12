import json
import httpx
from groq import Groq
from config import GROQ_API_KEY, MODEL, TOOL_URL_TEMPLATE
from tools import fetch_tools
from utils import extract_dni

class ChatAgent:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.tools = fetch_tools()
        self.messages = [{
            "role": "system",
            "content": (
                "Eres un asistente de atención al cliente para una compañía de servicios. "
                "Tu tarea es responder en español de forma clara y directa, ayudando al usuario a consultar información de abonados "
                "como dirección, pagos, deudas y facturas. Utiliza las herramientas disponibles si lo crees necesario. "
                "Si el usuario pide **todas las facturas** o **historial de facturas**, llama a la herramienta `todas_las_facturas`. "
                "Si pide solo las **facturas pendientes**, usa `facturas_pendientes`. "
                "No expliques qué herramienta usas, simplemente responde con la información. "
                "Evita repeticiones y mantén un tono profesional."
            )
        }]

        self.groq_tools = [{
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
        } for tool in self.tools]

    def handle_message(self, user_input: str) -> str:
        dni = extract_dni(user_input)
        if dni:
            user_input += f" (DNI detectado: {dni})"
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
