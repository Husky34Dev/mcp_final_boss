# main.py o donde uses el router

from app.agent.chat_agent import MultiAgentRouter

router = MultiAgentRouter(role="admin")  # Definir el rol

while True:
    entrada = input("🧑 > ")
    respuesta = router.handle_message(entrada)
    print("🤖 >", respuesta)
