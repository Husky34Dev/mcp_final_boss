# Separación Framework vs Configuración Específica

## 🏗️ FRAMEWORK REUTILIZABLE (Independiente del dominio)

### Componentes del Framework

#### 1. **Core Framework** (`app/framework/`)
- `agent_framework.py` - Framework genérico de agentes
- `context_manager.py` - Gestión de contexto conversacional  
- `conversation_context.py` - Estado conversacional

#### 2. **Utilities Genéricas** (`app/utils/`)
- `tool_executor.py` - Ejecutor genérico de herramientas
- `llm_response_guard.py` - Validador de respuestas
- `inline_function_handler.py` - Manejo de funciones inline
- `formatter.py` - Formateo de respuestas
- `conversation_context.py` - Contexto conversacional

#### 3. **Cache System** (en `handlers_and_tools.py`)
```python
# FRAMEWORK GENÉRICO - Reutilizable
_TOOLS_CACHE: Optional[List[Dict[str, Any]]] = None
_FILTERED_TOOLS_CACHE: Dict[str, List[Dict[str, Any]]] = {}  
_HANDLERS_CACHE: Dict[str, Any] = {}

def fetch_tools()  # Genérico para cualquier OpenAPI
def fetch_tools_for_agent()  # Filtrado genérico
def generate_handlers()  # Creación genérica de handlers
def clear_tools_cache()  # Gestión de cache
```

#### 4. **Shared Agent** (`app/agent/agents/shared_chat_agent.py`)
```python
# FRAMEWORK - Agente configurable genérico
class SharedChatAgent:
    def __init__(self, model: str, agent_id: Optional[str] = None):
        # Configurable para cualquier dominio
        self.tools = fetch_tools_for_agent(agent_id)
        self.handlers = generate_handlers(self.tools)
```

---

## ⚙️ CONFIGURACIÓN ESPECÍFICA (Telecomunicaciones/Facturas)

### Componentes Específicos del Dominio

#### 1. **Configuración de Agentes** (`app/config/agents_config.json`)
```json
{
  "agents": {
    "factura": {
      "name": "FacturaAgent",
      "tools": ["todas_las_facturas", "facturas_pendientes"],
      "system_prompt": "Eres un agente especializado en facturas...",
      "can_handle_keywords": ["factura", "facturas", "pago"]
    }
  }
}
```

#### 2. **Configuración de API** (`app/config/config.py`)
```python
# ESPECÍFICO - URLs y configuración del dominio
OPENAPI_URL = "http://localhost:8000/openapi.json"  
API_BASE_URL = "http://localhost:8000"
MODEL = "llama-3.1-70b-versatile"
```

#### 3. **Configuración de Contexto** (`app/config/context_config.py`)
```python
# ESPECÍFICO - Validaciones del dominio de telecomunicaciones
class ContextConfig:
    def detect_query_type(self, message: str) -> str:
        # Lógica específica para facturas/incidencias/abonados
```

#### 4. **Router Específico** (`app/agent/multi_agent_router.py`)
```python
# ESPECÍFICO - Integra framework con configuración del dominio
from app.config.domain_adapter import AGENT_FRAMEWORK
from app.config.context_config import context_config

class MultiAgentRouter:
    def __init__(self):
        self.agent_framework = AGENT_FRAMEWORK  # Framework genérico
        # Lógica específica del dominio
```

#### 5. **API Específica** (`app/api/server.py`)
```python
# ESPECÍFICO - Endpoints del dominio de telecomunicaciones
@app.post("/datos_abonado")
@app.post("/todas_las_facturas") 
@app.post("/crear_incidencia")
```

---

## 📋 CUÁNDO USAR QUÉ

### 🔧 Modifica el FRAMEWORK cuando:
- Quieres agregar nueva funcionalidad a todos los proyectos
- Mejoras el sistema de cache
- Optimizas el manejo de herramientas OpenAPI
- Añades nuevas capacidades conversacionales
- Mejoras el sistema de contexto

### ⚙️ Modifica la CONFIGURACIÓN cuando:
- Cambias agentes específicos (facturas → ventas)
- Modificas prompts del dominio
- Agregas/quitas herramientas de un agente
- Cambias palabras clave de routing
- Ajustas validaciones del contexto

---

## 🚀 CÓMO REUTILIZAR EN OTROS PROYECTOS

### Paso 1: Copiar Framework
```bash
# Copiar componentes reutilizables
cp -r app/framework/ nuevo_proyecto/app/
cp -r app/utils/ nuevo_proyecto/app/
cp app/agent/agents/shared_chat_agent.py nuevo_proyecto/app/agent/agents/
cp app/agent/utils/handlers_and_tools.py nuevo_proyecto/app/agent/utils/
```

### Paso 2: Crear Nueva Configuración
```json
// nuevo_proyecto/app/config/agents_config.json
{
  "agents": {
    "ventas": {
      "name": "VentasAgent", 
      "tools": ["buscar_productos", "crear_cotizacion"],
      "system_prompt": "Eres un agente de ventas...",
      "can_handle_keywords": ["producto", "precio", "comprar"]
    }
  }
}
```

### Paso 3: Configurar URLs específicas
```python
# nuevo_proyecto/app/config/config.py
OPENAPI_URL = "http://mi-api-ventas.com/openapi.json"
API_BASE_URL = "http://mi-api-ventas.com"
```

### Paso 4: Usar el Framework
```python
# nuevo_proyecto/main.py
from app.framework.agent_framework import AgentFramework
from app.agents.shared_chat_agent import SharedChatAgent

# El framework es genérico, solo cambia la configuración
framework = AgentFramework("app/config/agents_config.json")
agent = SharedChatAgent(agent_id="ventas")
```

---

## 📁 ESTRUCTURA RECOMENDADA PARA REUTILIZACIÓN

```
mi_framework_agentes/           # Framework reutilizable
├── framework/
│   ├── agent_framework.py      # ✅ Framework core
│   ├── context_manager.py      # ✅ Gestión de contexto
│   └── conversation_context.py # ✅ Estado conversacional
├── utils/
│   ├── tool_executor.py        # ✅ Ejecutor genérico
│   ├── llm_response_guard.py   # ✅ Validador
│   ├── formatter.py            # ✅ Formateo
│   └── cache_system.py         # ✅ Sistema de cache
└── agents/
    └── shared_chat_agent.py    # ✅ Agente configurable

proyecto_telecomunicaciones/    # Implementación específica
├── config/
│   ├── agents_config.json      # ⚙️ Agentes específicos
│   ├── config.py               # ⚙️ URLs del dominio
│   └── context_config.py       # ⚙️ Validaciones específicas
├── api/
│   └── server.py               # ⚙️ Endpoints específicos
└── main.py                     # ⚙️ Integración específica
```

---

## 🎯 RESUMEN DE SEPARACIÓN

| Componente | Tipo | Cuándo Modificar | Reutilizable |
|------------|------|------------------|--------------|
| `agent_framework.py` | Framework | Nuevas capacidades generales | ✅ Sí |
| `shared_chat_agent.py` | Framework | Mejoras al agente base | ✅ Sí |
| `cache_system.py` | Framework | Optimizaciones de cache | ✅ Sí |
| `agents_config.json` | Configuración | Cambios de dominio | ❌ No |
| `context_config.py` | Configuración | Validaciones específicas | ❌ No |
| `multi_agent_router.py` | Configuración | Lógica de routing específica | ❌ No |

**Regla simple**: Si es específico de "facturas/telecomunicaciones" → Configuración. Si puede usarse en "ventas/medicina/educación" → Framework.
