from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

app = FastAPI()

# Tool endpoint con operation_id claro
@app.post("/print_message", operation_id="print_message")
async def print_message(message: str):
    print(f"Mensaje recibido por MCP: {message}")
    return {"status": "ok", "echo": message}


# Opcional: endpoint raíz de prueba
@app.get("/")
async def root():
    return {"message": "Hello from FastAPI-MCP server!"}
mcp = FastApiMCP(app)
# Monta el MCP
mcp.mount()