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
                    "Eres un asistente de soporte interno para operadores de una compa\u00f1\u00eda de servicios. "
                    "Tu funci\u00f3n es proporcionar respuestas claras y profesionales sobre informaci\u00f3n de abonados. "
                    "Usa las herramientas cuando sea necesario. Puedes usar el DNI guardado previamente si no se menciona uno nuevo."
                )
            }
        ]

    def handle_message(self, user_input: str) -> str:
        logger.info(f"Mensaje recibido: {user_input}")
        dni = extract_dni(user_input)
        if dni:
            self.context["dni"] = dni
        elif "dni" in self.context and any(p in user_input.lower() for p in ["este abonado", "el usuario", "sus", "su"]):
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
            return f"❌ Error en Groq: {str(e)}"

        msg = response.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        if tool_calls:
            self.messages.append(msg)
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
                    result = r.json()
                    self.messages.append({
                        "tool_call_id": call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                except Exception as e:
                    self.messages.append({
                        "tool_call_id": call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps({"error": str(e)}, ensure_ascii=False)
                    })

            final = self.client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                max_tokens=4096,
            )
            self.messages.append(final.choices[0].message)
            return final.choices[0].message.content.strip()
        else:
            self.messages.append(msg)
            return msg.content.strip()
