from app.agent.chat_agent import ChatAgent

def cli_loop():
    agent = ChatAgent()
    print("🟢 Agente Groq iniciado (modo consola). Escribe 'salir' para terminar.\n")

    while True:
        user_input = input("🧑 > ").strip()
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("👋 Hasta luego.")
            break

        respuesta = agent.handle_message(user_input)
        print("🤖 >", respuesta)

if __name__ == "__main__":
    cli_loop()
