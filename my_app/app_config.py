"""
Configuración principal de la aplicación multi-agente.

Este archivo conecta el framework multi-agente con la configuración específica
de telecomunicaciones, incluyendo:
- Configuración de agentes especializados (factura, incidencia, abonado)
- Integración con OpenAPI para herramientas dinámicas
- Limpieza de schemas para compatibilidad con Groq
- Routing inteligente de mensajes
- Formateo automático de respuestas a markdown
"""
import httpx
import os
from framework.core.router import SimpleRouter
from config.config import OPENAPI_URL, API_BASE_URL, MODEL
from framework.tools import GLOBAL_TOOLS_CACHE, GLOBAL_FORMATTER, UnifiedFormatter


def call_my_api(endpoint: str, method: str, payload: dict) -> dict:
    """Función para llamar a mi API específica."""
    url = API_BASE_URL.rstrip('/') + endpoint
    response = httpx.request(method, url, json=payload)
    response.raise_for_status()
    return response.json()


def clean_schema_for_groq(schema):
    """Limpia esquemas OpenAPI para que sean compatibles con Groq"""
    if isinstance(schema, dict):
        cleaned = {}
        for key, value in schema.items():
            if key == 'anyOf':
                # Convertir anyOf a un tipo simple
                # Si tiene string y null, usar string opcional
                types = [item.get('type') for item in value if isinstance(item, dict)]
                if 'string' in types:
                    cleaned['type'] = 'string'
                elif types:
                    cleaned['type'] = types[0]
            else:
                cleaned[key] = clean_schema_for_groq(value)
        return cleaned
    elif isinstance(schema, list):
        return [clean_schema_for_groq(item) for item in schema]
    else:
        return schema


def get_tools_for_agent(tools_list: list) -> list:
    """Obtiene herramientas desde la cache global y las limpia para Groq."""
    all_tools = GLOBAL_TOOLS_CACHE.fetch_tools(OPENAPI_URL)
    
    # Filtrar solo las herramientas solicitadas
    filtered_tools = []
    for tool in all_tools:
        if tool.get('function', {}).get('name') in tools_list:
            # Limpiar herramienta para Groq (remover campos no estándar)
            clean_function = tool["function"].copy()
            
            # Limpiar parámetros para ser compatibles con Groq
            if 'parameters' in clean_function:
                clean_function['parameters'] = clean_schema_for_groq(clean_function['parameters'])
            
            clean_tool = {
                "type": tool["type"],
                "function": clean_function
            }
            filtered_tools.append(clean_tool)
    
    return filtered_tools


def generate_handlers(tools: list) -> dict:
    """Genera handlers para las herramientas usando la cache global."""
    # Obtener las herramientas originales (con endpoint y method)
    all_tools = GLOBAL_TOOLS_CACHE.fetch_tools(OPENAPI_URL)
    
    handlers = {}
    for tool in tools:
        func_name = tool.get('function', {}).get('name')
        if func_name:
            # Buscar la herramienta original para obtener endpoint y method
            original_tool = None
            for orig_tool in all_tools:
                if orig_tool.get('function', {}).get('name') == func_name:
                    original_tool = orig_tool
                    break
            
            if original_tool:
                endpoint = original_tool.get('endpoint')
                method = original_tool.get('method')
                
                def make_handler(ep, mtd):
                    return lambda **kwargs: call_my_api(ep, mtd, kwargs)
                
                handlers[func_name] = make_handler(endpoint, method)
    
    return handlers


# Crear router principal del sistema multi-agente
ROUTER = SimpleRouter(
    model=MODEL,
    agents_config_path="my_app/agents_config.json",
    context_config_path="my_app/context_config.json",
    tools_fetcher=get_tools_for_agent,
    handlers_generator=generate_handlers
)


# Configurar el formateador global con la configuración JSON
def setup_formatters():
    """Configura los formatters usando la configuración JSON."""
    formatters_config_path = os.path.join("my_app", "formatters_config.json")
    if os.path.exists(formatters_config_path):
        # Configurar el formateador global con el archivo JSON
        GLOBAL_FORMATTER.config_path = formatters_config_path
        GLOBAL_FORMATTER.formatters_config = GLOBAL_FORMATTER._load_config()
        
        # Obtener todos los formatters configurados y registrarlos manualmente también
        all_formatters = GLOBAL_FORMATTER.get_all_formatters()
        print(f"✅ Configurados {len(all_formatters)} formatters personalizados")
    else:
        print("⚠️ No se encontró archivo de configuración de formatters")


# Inicializar formatters al cargar el módulo
setup_formatters()


# Función principal para el chat API
def handle_chat_message(message: str) -> str:
    """Función principal para manejar mensajes de chat."""
    return ROUTER.route_message(message)


# Funciones de acceso para testing
def get_context_manager():
    """Retorna el context manager del agente por defecto."""
    default_agent_id = ROUTER.default_agent
    if default_agent_id in ROUTER.agents:
        return ROUTER.agents[default_agent_id].context
    return None


def get_router():
    """Retorna el router configurado."""
    return ROUTER


# Función para precargar herramientas
def preload_all_tools():
    """Precarga todas las herramientas en cache."""
    GLOBAL_TOOLS_CACHE.fetch_tools(OPENAPI_URL)
