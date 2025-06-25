# Framework Multi-Agente Configurable

Un framework simple y limpio para crear sistemas multi-agente configurables por JSON.

## Estructura

```
framework_clean/
├── core/
│   ├── agent.py       # Agente base reutilizable
│   ├── context.py     # Manejo de contexto configurable
│   └── router.py      # Router simple para dirigir mensajes
├── tools/
│   ├── formatter.py   # Formateador de respuestas
│   └── openapi_cache.py # Cache para herramientas OpenAPI
├── utils/
│   ├── response_guard.py # Validador de respuestas
│   └── function_handler.py # Manejador de funciones inline
└── example_usage.py   # Ejemplo de uso
```

## Características

- **100% Configurable por JSON**: No hay lógica hardcodeada
- **Reutilizable**: Independiente del dominio específico
- **Simple**: Arquitectura limpia y fácil de entender
- **Extensible**: Fácil de extender con nuevas funcionalidades

## Uso Básico

1. **Crear configuración de agentes** (`agents_config.json`):
```json
{
  "agents": {
    "factura": {
      "name": "FacturaAgent",
      "tools": ["obtener_facturas", "calcular_deuda"],
      "system_prompt": "Eres un experto en facturas...",
      "can_handle_keywords": ["factura", "pago", "deuda"],
      "force_tool_usage": true
    }
  },
  "routing": {
    "query_type_to_agent": {
      "factura": "factura"
    },
    "default_agent": "default"
  }
}
```

2. **Crear configuración de contexto** (`context_config.json`):
```json
{
  "query_types": {
    "factura": ["factura", "pago", "deuda"],
    "abonado": ["datos", "cliente"]
  },
  "field_definitions": {
    "dni": {
      "patterns": ["\\\\b([0-9]{8}[A-Za-z])\\\\b"]
    }
  }
}
```

3. **Inicializar el router**:
```python
from framework_clean import SimpleRouter

router = SimpleRouter(
    model="llama-3.1-8b-instant",
    agents_config_path="agents_config.json",
    context_config_path="context_config.json", 
    tools_fetcher=my_tools_function,
    handlers_generator=my_handlers_function
)

response = router.route_message("¿Cuáles son mis facturas?")
```

## Ventajas del Framework Limpio

### Antes (framework original):
- ❌ Imports rotos (agent_framework, context_manager, tool_executor)
- ❌ Archivos duplicados (formatter.py en dos lugares)
- ❌ Dependencias circulares
- ❌ Código experimental mezclado con producción
- ❌ Configuraciones redundantes
- ❌ Difícil de entender y mantener

### Después (framework_clean):
- ✅ Imports limpio y funcionales
- ✅ Un solo archivo por funcionalidad
- ✅ Dependencias claras y simples
- ✅ Solo código de producción
- ✅ Configuración centralizada
- ✅ Fácil de entender y extender

## Migración

Para migrar del framework anterior al nuevo:

1. Reemplaza imports:
```python
# Antes
from framework.agents.simple_router import SimpleRouter
from framework.base_chat_agent import BaseChatAgent

# Después  
from framework_clean import SimpleRouter
from framework_clean.core import BaseAgent
```

2. Las configuraciones JSON se mantienen igual
3. El API público es compatible

## Componentes

### BaseAgent
El agente base que maneja conversaciones con LLMs y herramientas.

### ConfigurableContext  
Contexto completamente configurable por JSON que extrae entidades, detecta tipos de query y maneja referencias.

### SimpleRouter
Router que dirige mensajes a agentes especializados basado en configuración.

### Tools
- **OpenAPIToolsCache**: Cache para herramientas desde especificaciones OpenAPI
- **BaseToolFormatter**: Formateador extensible para respuestas

### Utils
- **ResponseGuard**: Valida calidad de respuestas LLM
- **FunctionHandler**: Maneja funciones inline en respuestas

Este framework limpio reemplaza completamente al anterior eliminando toda la complejidad innecesaria.
