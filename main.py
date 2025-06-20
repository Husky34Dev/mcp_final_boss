from app.agent.multi_agent_router import MultiAgentRouter
from app.config.config import MODEL

def main():
    router = MultiAgentRouter(model=MODEL)
    print("Inicio del CLI multi-agente. 'exit' para salir.")
    while True:
        msg = input("Usuario: ")
        if msg.lower() in ["exit", "quit"]:
            break
        resp = router.handle_message(msg)
        print(f"Agente: {resp}\n")

if __name__ == "__main__":
    main()