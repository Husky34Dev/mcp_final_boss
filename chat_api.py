# app/chat_api.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.agent.chat_agent import MultiAgentRouter  # usamos el router multiagente

app = FastAPI()

# Creamos el router multiagente con rol que queramos admin, facturacion, incidencias o soporte
# importar el rol desde la base de datos
agent = MultiAgentRouter(role="admin")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restringir en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    reply = agent.handle_message(request.message)
    return {"reply": reply}
