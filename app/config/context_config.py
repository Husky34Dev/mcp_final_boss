# Se reemplaza el gestor antiguo por el manager genérico basado en JSON
from app.framework.context_manager import FrameworkContextManager

# Ruta al JSON de configuración
CONFIG_PATH = "c:\\projects\\mcp_groq\\app\\config\\query_config.json"

# Instancia global del gestor de contexto
context_config = FrameworkContextManager(CONFIG_PATH)
