from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.agent.chat_agent import ChatAgent

app = FastAPI()

# Agente Groq
agent = ChatAgent()

# Permitir llamadas desde cualquier origen 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #restringir esto a servidores en los que confiamos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo para la entrada
class ChatRequest(BaseModel):
    message: str

# Modelo para la salida
class ChatResponse(BaseModel):
    reply: str

# Endpoint principal
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    reply = agent.handle_message(request.message)
    return {"reply": reply}
