from app.agent.multi_agent_router import MultiAgentRouter

def main():
    router = MultiAgentRouter(model="llama-3.3-70b-versatile")
    print("Inicio del CLI multi-agente. 'exit' para salir.")
    while True:
        msg = input("Usuario: ")
        if msg.lower() in ["exit", "quit"]:
            break
        resp = router.handle_message(msg)
        print(f"Agente: {resp}\n")

if __name__ == "__main__":
    main()