import os
import json
import re
import httpx
import jsonref
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "TU_API_KEY_AQUI")
MODEL = "llama3-70b-8192"
OPENAPI_URL = "http://localhost:8000/openapi.json"
TOOL_URL_TEMPLATE = "http://localhost:8000{}"

client = Groq(api_key=GROQ_API_KEY)

def extract_dni(texto):
    match = re.search(r"\b\d{8}[A-Z]\b", texto, re.IGNORECASE)
    return match.group(0) if match else None

def clean_schema(schema):
    try:
        return json.loads(json.dumps(schema))
    except TypeError:
        if isinstance(schema, dict):
            return {k: clean_schema(v) for k, v in schema.items()}
        elif isinstance(schema, list):
            return [clean_schema(i) for i in schema]
        else:
            return str(schema)

def fetch_tools():
    r = httpx.get(OPENAPI_URL)
    r.raise_for_status()
    spec = jsonref.JsonRef.replace_refs(r.json())

    tools = []
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            if "operationId" not in op:
                continue
            schema = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
            tools.append({
                "name": op["operationId"],
                "description": op.get("description", f"Herramienta para {op['operationId']}"),
                "input_schema": clean_schema(schema),
                "endpoint": path
            })
    return tools

def agent_loop():
    tools = fetch_tools()
    print(f"🛠️  Herramientas disponibles: {[t['name'] for t in tools]}")

    groq_tools = [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
        }
        for tool in tools
    ]

    messages = [
        {
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
        }
    ]

    while True:
        user_input = input("🧑 > ").strip()
        dni = extract_dni(user_input)
        if dni:
            user_input += f" (DNI detectado: {dni})"
        messages.append({"role": "user", "content": user_input})

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=groq_tools,
                tool_choice="auto",
                max_tokens=4096,
            )
        except Exception as e:
            print("❌ Error en Groq:", e)
            continue

        msg = response.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        if tool_calls:
            messages.append(msg)
            for call in tool_calls:
                tool_name = call.function.name
                try:
                    args = json.loads(call.function.arguments)
                    # ==== DEBUG START ====
                    print(f"🔧 Tool llamada: {tool_name}")
                    print(f"📦 Argumentos generados:", json.dumps(args, indent=2, ensure_ascii=False))
                    # ==== DEBUG END ====
                except Exception as e:
                    print(f"❌ Error parseando argumentos: {e}")
                    continue

                tool = next((t for t in tools if t["name"] == tool_name), None)
                if not tool:
                    print(f"⚠️ Herramienta no encontrada: {tool_name}")
                    continue

                try:
                    r = httpx.post(TOOL_URL_TEMPLATE.format(tool["endpoint"]), json=args)
                    r.raise_for_status()
                    result = r.json()
                    # ==== DEBUG START ====
                    print(f"📥 Respuesta de {tool_name}:", json.dumps(result, indent=2, ensure_ascii=False))
                    # ==== DEBUG END ====
                    messages.append({
                        "tool_call_id": call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                except Exception as e:
                    print(f"❌ Error ejecutando {tool_name}:", e)
                    continue

            try:
                final = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_tokens=4096,
                )
                print("🤖 >", final.choices[0].message.content.strip())
                messages.append(final.choices[0].message)
            except Exception as e:
                print("❌ Error final post-tool:", e)
        else:
            print("🤖 >", msg.content.strip())
            messages.append(msg)

if __name__ == "__main__":
    print("🟢 Agente Groq iniciado.")
    agent_loop()
