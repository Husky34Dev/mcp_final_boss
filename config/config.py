import os
from dotenv import load_dotenv

load_dotenv()  

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "TU_API_KEY_AQUI")
MODEL = "llama-3.1-8b-instant"  # Modelo más rápido y económico para testing
OPENAPI_URL = "http://localhost:8000/openapi.json"
TOOL_URL_TEMPLATE = "http://localhost:8000{}"
API_BASE_URL = "http://localhost:8000"
