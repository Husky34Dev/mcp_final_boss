import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "TU_API_KEY_AQUI")
MODEL = "llama-3.1-8b-instant"
OPENAPI_URL = "http://localhost:8000/openapi.json"
TOOL_URL_TEMPLATE = "http://localhost:8000{}"
API_BASE_URL = "http://localhost:8000"
