# Arquitectura Modular del Framework de Agentes

## Separación Framework vs Configuración de Dominio

La nueva arquitectura separa claramente el **framework genérico reutilizable** de la **configuración específica del dominio**:

### 🔧 Framework Genérico (`app/framework/`)

**Completamente reutilizable en cualquier dominio:**

```
app/framework/
├── base_chat_agent.py          # ⭐ Agente base genérico (corazón del framework)
├── agent_framework.py          # Framework de configuración de agentes
├── openapi_cache.py            # Sistema de cache de herramientas
├── conversation_context.py     # Manejo genérico de contexto conversacional
├── context_manager.py          # Gestor genérico de contexto
├── formatter.py                # ⭐ Sistema genérico de formateo de respuestas
├── tool_executor.py            # ⭐ Ejecutor genérico de herramientas
└── inline_function_handler.py  # ⭐ Handler genérico de funciones inline
```

#### `BaseChatAgent` - El Corazón del Framework

```python
from app.framework.base_chat_agent import BaseChatAgent

# Agente completamente genérico
agent = BaseChatAgent(
    model="llama3-8b-8192",
    tools_fetcher=my_domain_tools_fetcher,
    handlers_generator=my_domain_handlers_generator,
    agent_id="my_agent"
)
```

**Características:**
- ✅ **Sin dependencias específicas del dominio**
- ✅ **Manejo completo de conversaciones**
- ✅ **Ejecución de herramientas genérica**
- ✅ **Sistema de retry y validación**
- ✅ **Cache de mensajes**
- ✅ **Soporte para funciones inline**

### 🎯 Configuración Específica (`app/config/`)

**Específico del dominio de telecomunicaciones:**

```
app/config/
├── domain_adapter.py       # ⭐ Adaptador del dominio
├── agents_config.json      # Configuración de agentes específicos
├── config.py              # Configuración general
└── context_config.py       # Configuración de contexto
```

#### `TelecomDomainAdapter` - Interfaz de Dominio

```python
from app.config.domain_adapter import TELECOM_DOMAIN_ADAPTER

# Acceso a toda la configuración del dominio
adapter = TELECOM_DOMAIN_ADAPTER
tools = adapter.get_tools_for_agent("factura")
handlers = adapter.generate_handlers(tools)
framework = adapter.get_agent_framework()
```

### 🚀 Implementación del Dominio (`app/agents/`)

**Uso específico del framework para telecomunicaciones:**

```
app/agents/
├── shared_chat_agent.py    # ⭐ Agente específico de telecom
└── multi_agent_router.py   # Router multi-agente del dominio
```

## Flujo de Creación de Agentes

### 1. **Para el Dominio Actual (Telecomunicaciones)**

```python
# Uso directo del agente del dominio
from app.agents.shared_chat_agent import SharedChatAgent

agent = SharedChatAgent(
    model="llama3-8b-8192",
    agent_id="factura"  # Configuración automática del dominio
)

response = agent.handle_message_with_context("¿Cuál es mi factura?")
```

### 2. **Para un Nuevo Dominio (ej: E-commerce)**

```python
# 1. Crear adaptador de dominio
class EcommerceDomainAdapter:
    def get_tools_for_agent(self, agent_id):
        # Lógica específica de e-commerce
        return ecommerce_tools
    
    def generate_handlers(self, tools):
        # Handlers específicos de e-commerce
        return ecommerce_handlers

# 2. Crear agente específico
class EcommerceAgent(BaseChatAgent):
    def __init__(self, model, agent_id=None):
        adapter = EcommerceDomainAdapter()
        super().__init__(
            model=model,
            tools_fetcher=adapter.get_tools_for_agent,
            handlers_generator=adapter.generate_handlers,
            agent_id=agent_id
        )
```

### 3. **Uso del Framework Base Directamente**

```python
from app.framework.base_chat_agent import BaseChatAgent

# Para casos simples o prototipado rápido
def simple_tools_fetcher(agent_id=None):
    return [{"type": "function", "function": {"name": "get_time"}}]

def simple_handlers_generator(tools):
    return {"get_time": lambda: "12:00 PM"}

agent = BaseChatAgent(
    model="llama3-8b-8192", 
    tools_fetcher=simple_tools_fetcher,
    handlers_generator=simple_handlers_generator
)
```

## Ventajas de la Nueva Arquitectura

### ✅ **Para Desarrolladores del Framework**
- Código core completamente genérico
- Sin dependencias externas específicas
- Fácil testing y mantenimiento
- Reutilizable en cualquier proyecto

### ✅ **Para Desarrolladores de Aplicaciones**
- Configuración simple con adaptadores de dominio
- No necesitan tocar el código del framework
- Personalización completa del comportamiento
- Migración sencilla entre dominios

### ✅ **Para Reutilización**
- Framework como librería independiente
- Cada dominio en su propio módulo
- Configuración por archivos JSON
- Interfaz consistente entre dominios

## Archivos Clave Modificados

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `app/framework/base_chat_agent.py` | **Framework** | 🆕 Agente base genérico |
| `app/agents/shared_chat_agent.py` | **Dominio** | ♻️ Ahora hereda del base |
| `app/config/domain_adapter.py` | **Dominio** | ♻️ Añadido `TelecomDomainAdapter` |
| `app/agents/multi_agent_router.py` | **Dominio** | ♻️ Usa el adaptador de dominio |

## Ejemplo de Migración a Otro Dominio

```python
# Para crear un sistema de soporte técnico:
class SupportDomainAdapter:
    def get_tools_for_agent(self, agent_id):
        if agent_id == "hardware":
            return hardware_diagnostic_tools
        elif agent_id == "software": 
            return software_diagnostic_tools
        return all_support_tools
    
    def generate_handlers(self, tools):
        return create_support_handlers(tools, api_client=support_api)

class SupportAgent(BaseChatAgent):
    def __init__(self, model, agent_id=None):
        adapter = SupportDomainAdapter()
        super().__init__(
            model=model,
            tools_fetcher=adapter.get_tools_for_agent,
            handlers_generator=adapter.generate_handlers,
            agent_id=agent_id
        )
        
        self._domain_greeting = "¡Hola! Soy tu asistente de soporte técnico."
```

## 🔧 **Framework Genérico Reorganizado** (`app/framework/`)

**Ahora todos los componentes del framework están organizados lógicamente:**

```
app/framework/
├── base_chat_agent.py          # ⭐ Agente base genérico (corazón del framework)
├── agent_framework.py          # Framework de configuración de agentes
├── openapi_cache.py            # Sistema de cache de herramientas
├── conversation_context.py     # Manejo genérico de contexto conversacional
├── context_manager.py          # Gestor genérico de contexto
├── formatter.py                # ⭐ Sistema genérico de formateo de respuestas
├── tool_executor.py            # ⭐ Ejecutor genérico de herramientas
└── inline_function_handler.py  # ⭐ Handler genérico de funciones inline
```

### 🎯 **Utils Específicos del Dominio** (`app/utils/`)

**Solo quedan los utils específicos de telecomunicaciones:**

```
app/utils/
├── conversation_context.py     # Contexto específico de telecom (hereda del genérico)
├── formatter.py               # Formateadores específicos de telecom (usa framework genérico)
├── llm_response_guard.py      # Guard específico de telecom (usa context_config)
└── utils.py                   # Utilidades específicas del dominio
```

### ✅ **Ventajas de la Reorganización:**

1. **🔄 Framework Completamente Autocontenido**
   - Todos los componentes core en `app/framework/`
   - Sin dependencias cruzadas hacia `app/utils/`
   - Fácil extracción como librería independiente

2. **🎯 Separación Clara de Responsabilidades**
   - Framework: Lógica genérica reutilizable
   - Utils: Funcionalidad específica del dominio
   - Config: Configuración y adaptadores del dominio

3. **📦 Reutilización Simplificada**
   ```python
   # Para usar el framework en otro dominio, solo copiar app/framework/
   from my_project.framework.base_chat_agent import BaseChatAgent
   ```

4. **🧪 Testing Aislado**
   - Framework se puede testear independientemente
   - Utils del dominio se testean por separado
   - No hay dependencias circulares

### 🔄 **Cambios Realizados:**

| Módulo | Antes | Después | Tipo |
|--------|-------|---------|------|
| `tool_executor.py` | `app/utils/` | `app/framework/` | **Framework Core** |
| `inline_function_handler.py` | `app/utils/` | `app/framework/` | **Framework Core** |
| `formatter.py` | Solo utils | Framework + Domain | **Híbrido Mejorado** |
| `conversation_context.py` | Duplicado | Generic + Domain | **Jerarquía Clara** |

### 🚀 **Uso del Nuevo Sistema:**

#### Framework Genérico:
```python
from app.framework.base_chat_agent import BaseChatAgent
from app.framework.formatter import GLOBAL_FORMATTER

# Registrar formateadores personalizados
GLOBAL_FORMATTER.register_formatter("my_tool", my_custom_formatter)

agent = BaseChatAgent(
    model="llama3-8b-8192",
    tools_fetcher=my_tools_function,
    handlers_generator=my_handlers_function
)
```

#### Dominio Específico (Telecom):
```python
from app.agents.shared_chat_agent import SharedChatAgent

# Los formateadores de telecom ya están registrados automáticamente
agent = SharedChatAgent(
    model="llama3-8b-8192", 
    agent_id="factura"
)
```

Esta arquitectura permite que el framework sea **completamente genérico** mientras que cada aplicación puede tener su **configuración específica** sin modificar el código core.
