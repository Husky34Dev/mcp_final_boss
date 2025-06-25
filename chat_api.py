"""
API de Chat Multi-Agente usando el framework limpio.

Este archivo expone un endpoint `/chat` que:
- Usa el framework multi-agente configurado en my_app
- Funciona con la interfaz web existente (index.html)
- Conecta con el servidor de datos (api/server.py)
- Devuelve respuestas en el formato esperado por el frontend
"""
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any

# Importar la función principal del chat desde la configuración limpia
from my_app import handle_chat_message, preload_all_tools

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Chat Multi-Agente API",
    description="API para chat inteligente con agentes especializados",
    version="1.0.0"
)

# Configurar CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción usar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos (solo el index.html)
try:
    app.mount("/static", StaticFiles(directory="."), name="static")
except Exception as e:
    logger.warning(f"No se pudieron servir archivos estáticos: {e}")


# Modelos Pydantic para las requests
class ChatRequest(BaseModel):
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "message": "¿Cuáles son mis facturas pendientes?"
            }
        }


class ChatResponse(BaseModel):
    reply: str
    
    class Config:
        schema_extra = {
            "example": {
                "reply": "Aquí tienes tus facturas pendientes..."
            }
        }


@app.on_event("startup")
async def startup_event():
    """Evento de inicio para precargar herramientas."""
    logger.info("Iniciando Chat API...")
    try:
        # Precargar herramientas en cache para mejorar rendimiento
        preload_all_tools()
        logger.info("Herramientas precargadas exitosamente")
    except Exception as e:
        logger.warning(f"Error al precargar herramientas: {e}")
        logger.info("La aplicación continuará, las herramientas se cargarán bajo demanda")


@app.get("/")
async def serve_chat_interface():
    """Servir la interfaz web de chat."""
    try:
        return FileResponse("index.html")
    except Exception as e:
        logger.error(f"Error sirviendo index.html: {e}")
        raise HTTPException(status_code=404, detail="Interfaz de chat no encontrada")


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Endpoint principal para el chat multi-agente.
    
    Procesa mensajes del usuario y devuelve respuestas inteligentes
    usando el sistema de agentes especializados.
    """
    try:
        logger.info(f"Mensaje recibido: {request.message[:100]}...")
        
        # Procesar mensaje usando el framework multi-agente
        response = handle_chat_message(request.message)
        
        logger.info(f"Respuesta generada: {response[:100]}...")
        
        return ChatResponse(reply=response)
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno del servidor: {str(e)}"
        )


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Endpoint de salud para monitoreo."""
    return {"status": "healthy", "service": "chat-api"}


@app.get("/info")
async def get_api_info() -> Dict[str, Any]:
    """Información sobre la API y el sistema."""
    try:
        from my_app import get_router
        router = get_router()
        
        return {
            "title": "Chat Multi-Agente API",
            "version": "1.0.0",
            "framework": "framework multi-agente limpio",
            "agents_available": list(router.agents.keys()) if router.agents else [],
            "default_agent": getattr(router, 'default_agent', 'unknown'),
            "status": "operational"
        }
    except Exception as e:
        logger.error(f"Error obteniendo información: {e}")
        return {
            "title": "Chat Multi-Agente API",
            "version": "1.0.0",
            "status": "operational",
            "error": str(e)
        }


if __name__ == "__main__":
    logger.info("Iniciando servidor de Chat API...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # Puerto diferente al servidor de datos (8000)
        log_level="info"
    )
