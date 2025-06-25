# Ejemplo: Cómo Reutilizar el Framework en un Proyecto de Ventas

## 📁 Estructura para Proyecto de Ventas

```
proyecto_ventas/
├── app/
│   ├── framework/                  # ✅ COPIADO del framework
│   │   ├── openapi_cache.py        # Sistema de cache genérico  
│   │   ├── agent_framework.py      # Framework de agentes
│   │   └── conversation_context.py # Contexto conversacional
│   ├── agents/                     # ✅ COPIADO del framework
│   │   └── shared_chat_agent.py    # Agente configurable
│   ├── config/                     # ⚙️ ESPECÍFICO del dominio ventas
│   │   ├── agents_config.json      # Configuración de agentes de ventas
│   │   ├── config.py               # URLs de API de ventas
│   │   └── sales_adapter.py        # Adaptador específico de ventas
│   └── utils/                      # ✅ COPIADO del framework
│       ├── tool_executor.py        # Utilidades genéricas
│       └── formatter.py            
└── main.py                         # ⚙️ ESPECÍFICO del dominio
```

## ⚙️ Configuración para Ventas

### 1. Configuración de Agentes (`config/agents_config.json`)
```json
{
  "agents": {
    "productos": {
      "name": "ProductosAgent",
      "description": "Agente especializado en búsqueda de productos",
      "tools": [
        "buscar_productos",
        "obtener_detalles_producto", 
        "verificar_stock",
        "obtener_precios"
      ],
      "system_prompt": "Eres un asistente de ventas especializado en productos. Ayuda a los clientes a encontrar el producto perfecto para sus necesidades.",
      "can_handle_keywords": ["producto", "buscar", "precio", "stock"],
      "force_tool_usage": true
    },
    "cotizaciones": {
      "name": "CotizacionesAgent", 
      "description": "Agente para generar cotizaciones y presupuestos",
      "tools": [
        "crear_cotizacion",
        "calcular_descuentos",
        "obtener_cotizacion",
        "enviar_cotizacion"
      ],
      "system_prompt": "Eres un agente de cotizaciones. Generas presupuestos precisos y competitivos para los clientes.",
      "can_handle_keywords": ["cotización", "presupuesto", "precio", "descuento"],
      "force_tool_usage": true
    },
    "clientes": {
      "name": "ClientesAgent",
      "description": "Agente para gestión de información de clientes", 
      "tools": [
        "buscar_cliente",
        "crear_cliente",
        "actualizar_cliente",
        "historial_compras"
      ],
      "system_prompt": "Eres un agente de atención al cliente. Gestionas información y historial de clientes.",
      "can_handle_keywords": ["cliente", "historial", "información", "datos"],
      "force_tool_usage": false
    }
  },
  "routing": {
    "default_agent": "productos",
    "query_type_to_agent": {
      "product_search": "productos",
      "quote_request": "cotizaciones", 
      "customer_info": "clientes"
    }
  }
}
```

### 2. Configuración del Dominio (`config/config.py`)
```python
# Configuración específica para el proyecto de ventas
OPENAPI_URL = "https://api-ventas.miempresa.com/openapi.json"
API_BASE_URL = "https://api-ventas.miempresa.com"
MODEL = "llama-3.1-70b-versatile"

# Configuración específica de ventas
DEFAULT_CURRENCY = "USD"
MAX_DISCOUNT_PERCENT = 20
QUOTE_VALIDITY_DAYS = 30
```

### 3. Adaptador de Ventas (`config/sales_adapter.py`)
```python
"""
Adaptador específico para el dominio de ventas.
Integra el framework genérico con la configuración de ventas.
"""
import httpx
from typing import Optional, List, Dict, Any
from app.config.config import OPENAPI_URL, API_BASE_URL
from app.framework.agent_framework import AgentFramework
from app.framework.openapi_cache import GLOBAL_TOOLS_CACHE
import logging

# Framework de agentes específico para ventas
SALES_AGENT_FRAMEWORK = AgentFramework("app/config/agents_config.json")

def call_sales_api(endpoint: str, method: str, payload: dict):
    """Llamadas HTTP específicas para la API de ventas"""
    url = API_BASE_URL.rstrip('/') + endpoint
    headers = {
        "Authorization": f"Bearer {get_sales_api_token()}",
        "Content-Type": "application/json"
    }
    response = httpx.request(method, url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def clean_sales_schema(schema: dict) -> dict:
    """Limpieza específica para schemas de ventas"""
    # Lógica específica para APIs de ventas
    # Por ejemplo: convertir precios, validar monedas, etc.
    return schema

def fetch_sales_tools():
    """Carga herramientas específicas de ventas"""
    return GLOBAL_TOOLS_CACHE.fetch_tools(
        openapi_url=OPENAPI_URL,
        schema_cleaner_func=clean_sales_schema
    )

def fetch_tools_for_sales_agent(agent_id: Optional[str] = None):
    """Obtiene herramientas para agentes de ventas específicos"""
    if agent_id is None:
        return fetch_sales_tools()
    
    fetch_sales_tools()  # Asegurar que estén cargadas
    allowed_tools = SALES_AGENT_FRAMEWORK.get_tools_for_agent(agent_id)
    return GLOBAL_TOOLS_CACHE.get_filtered_tools(agent_id, allowed_tools)

def generate_sales_handlers(tools: List[Dict[str, Any]]):
    """Genera handlers específicos para ventas"""
    return GLOBAL_TOOLS_CACHE.generate_handlers(tools, call_sales_api)
```

### 4. Aplicación Principal (`main.py`)
```python
"""
Aplicación principal para el sistema de ventas.
Usa el framework genérico con configuración específica de ventas.
"""
from app.framework.agent_framework import AgentFramework
from app.agents.shared_chat_agent import SharedChatAgent  
from app.config.sales_adapter import SALES_AGENT_FRAMEWORK, fetch_tools_for_sales_agent

class SalesRouter:
    def __init__(self):
        self.framework = SALES_AGENT_FRAMEWORK
        self._agent_cache = {}
    
    def _get_sales_agent(self, agent_id: str):
        if agent_id not in self._agent_cache:
            agent = SharedChatAgent(model="llama-3.1-70b-versatile", agent_id=agent_id)
            # Configurar con herramientas específicas de ventas
            agent.tools = fetch_tools_for_sales_agent(agent_id)
            agent.set_system_prompt(self.framework.get_system_prompt(agent_id))
            self._agent_cache[agent_id] = agent
        return self._agent_cache[agent_id]
    
    def handle_sales_query(self, message: str) -> str:
        # Detectar tipo de consulta de ventas
        agent_id = self.framework.get_agent_for_message(message)
        
        # Obtener agente específico
        agent = self._get_sales_agent(agent_id) 
        
        # Procesar consulta
        return agent.handle_message_with_context(message)

def main():
    router = SalesRouter()
    
    print("🛒 Sistema de Ventas Inteligente iniciado")
    while True:
        query = input("Cliente: ")
        if query.lower() in ['exit', 'salir']:
            break
        
        response = router.handle_sales_query(query)
        print(f"Vendedor: {response}\n")

if __name__ == "__main__":
    main()
```

## 🔄 Comparación: Telecomunicaciones vs Ventas

| Aspecto | Telecomunicaciones | Ventas |
|---------|-------------------|---------|
| **Framework** | ✅ Mismo (`agent_framework.py`) | ✅ Mismo (`agent_framework.py`) |
| **Cache** | ✅ Mismo (`openapi_cache.py`) | ✅ Mismo (`openapi_cache.py`) |
| **Agente Base** | ✅ Mismo (`shared_chat_agent.py`) | ✅ Mismo (`shared_chat_agent.py`) |
| **Configuración** | `agents_config.json` (facturas) | `agents_config.json` (productos) |
| **API URL** | `localhost:8000` | `api-ventas.miempresa.com` |
| **Adaptador** | `domain_adapter.py` | `sales_adapter.py` |
| **Agentes** | factura, incidencia, abonado | productos, cotizaciones, clientes |
| **Herramientas** | facturas, incidencias, abonados | productos, cotizaciones, clientes |

## 📋 Pasos para Migrar a Otro Dominio

### 1. ✅ Copiar Framework (Sin cambios)
```bash
cp -r framework/ nuevo_proyecto/app/
cp -r utils/ nuevo_proyecto/app/  
cp agents/shared_chat_agent.py nuevo_proyecto/app/agents/
```

### 2. ⚙️ Crear Nueva Configuración
- Escribir `agents_config.json` para el nuevo dominio
- Configurar URLs en `config.py`
- Crear adaptador específico (`domain_adapter.py`)

### 3. 🚀 Usar Framework
```python
# El framework es genérico, solo cambia la configuración
from app.framework.agent_framework import AgentFramework
from app.agents.shared_chat_agent import SharedChatAgent

# Instanciar con nueva configuración
framework = AgentFramework("config/agents_config.json")
agent = SharedChatAgent(agent_id="productos")  # En lugar de "factura"
```

## 🎯 Resultado

**Una vez separado**:
- ✅ **Framework reutilizable** en múltiples proyectos
- ✅ **Configuración específica** por dominio  
- ✅ **Sin duplicación** de código
- ✅ **Fácil mantenimiento** del framework central
- ✅ **Personalización completa** por proyecto
