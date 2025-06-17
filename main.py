# main.py

from app.agent.chat_agent import MultiAgentRouter

router = MultiAgentRouter()

while True:
    mensaje = input("🧑 > ")
    if mensaje.lower() in ["salir", "exit", "quit"]:
        break
    respuesta = router.handle_message(mensaje)
    print("🤖 >", respuesta)
