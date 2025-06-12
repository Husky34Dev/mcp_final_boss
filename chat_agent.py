import json
import httpx
from groq import Groq
from config import GROQ_API_KEY, MODEL, TOOL_URL_TEMPLATE
from tools import fetch_tools
from utils import extract_dni

client = Groq(api_key=GROQ_API_KEY)

def agent_loop():
    tools = fetch_tools()
    print(f"🛠️  Herramientas disponibles: {[t['name'] for t in tools]}")

    groq_tools = [{
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["input_schema"]
        }
    } for tool in tools]

    messages = [{
        "role": "system",
        "content": (
            "Eres un asistente de atención al cliente..."
        )
    }]

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
            failed_tools = set()
            calls_this_turn = 0

            for call in tool_calls:
                if calls_this_turn >= 4:
                    print("⚠️ Límite de llamadas por turno alcanzado.")
                    break

                tool_name = call.function.name
                if tool_name in failed_tools:
                    continue

                try:
                    args = json.loads(call.function.arguments)
                except Exception as e:
                    failed_tools.add(tool_name)
                    continue

                if tool_name == "datos_abonado":
                    if not args.get("dni") and not args.get("poliza"):
                        failed_tools.add(tool_name)
                        continue
                    if "poliza" in args and args["poliza"] == "":
                        del args["poliza"]

                tool = next((t for t in tools if t["name"] == tool_name), None)
                if not tool:
                    failed_tools.add(tool_name)
                    continue

                try:
                    r = httpx.post(TOOL_URL_TEMPLATE.format(tool["endpoint"]), json=args)
                    r.raise_for_status()
                    result = r.json()
                    messages.append({
                        "tool_call_id": call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                    calls_this_turn += 1
                except Exception as e:
                    failed_tools.add(tool_name)
                    messages.append({
                        "tool_call_id": call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps({"error": str(e)}, ensure_ascii=False)
                    })

            try:
                final = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_tokens=4096,
                )
                print("🤖 >", final.choices[0].message.content.strip())
                messages.append(final.choices[0].message)
            except Exception as e:
                print("❌ Error final:", e)
        else:
            print("🤖 >", msg.content.strip())
            messages.append(msg)
