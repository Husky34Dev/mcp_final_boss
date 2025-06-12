import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "TU_API_KEY_AQUI")
MODEL = "llama3-70b-8192"
OPENAPI_URL = "http://localhost:8000/openapi.json"
TOOL_URL_TEMPLATE = "http://localhost:8000{}"
