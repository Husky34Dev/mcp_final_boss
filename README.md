# Framework Multi-Agente Profesional

Sistema inteligente de agentes conversacionales con arquitectura modular y framework completamente reutilizable.

## 🏗️ Arquitectura

Este proyecto incluye un framework multi-agente genérico y una implementación específica para telecomunicaciones.

### Framework Core (`framework/`)
```
framework/
├── core/
│   ├── agent.py          # Agente base reutilizable
│   ├── context.py        # Contexto configurable por JSON
│   └── router.py         # Router multi-agente
├── tools/
│   ├── formatter.py      # Formateador de respuestas
│   └── openapi_cache.py  # Cache para herramientas OpenAPI
└── utils/
    ├── response_guard.py # Validador de respuestas LLM
    └── function_handler.py # Manejador de funciones inline
```

### Implementación Específica (`my_app/`, `config/`, `api/`)
- **Configuración JSON**: Agentes y contexto completamente configurables
- **API específica**: Endpoints para telecomunicaciones
- **Configuración de dominio**: Adaptación a necesidades específicas

## 🚀 Características

- ✅ **Framework 100% Reutilizable**: Independiente del dominio específico
- ✅ **Configuración por JSON**: Sin lógica hardcodeada
- ✅ **4 Agentes Especializados**: factura, incidencia, abonado, default
- ✅ **Cache Global Optimizado**: Sin llamadas redundantes a OpenAPI
- ✅ **Contexto Persistente**: Mantiene referencias entre conversaciones
- ✅ **Arquitectura Limpia**: Separación clara entre framework y aplicación

## 🔧 Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd mcp_groq

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export GROQ_API_KEY="tu_api_key_aqui"
```

## 📋 Uso Rápido

### 1. Usar el Framework en tu Proyecto

```python
from framework import SimpleRouter

# Crear router con tu configuración
router = SimpleRouter(
    model="llama-3.1-8b-instant",
    agents_config_path="mi_config/agentes.json",
    context_config_path="mi_config/contexto.json",
    tools_fetcher=mi_funcion_herramientas,
    handlers_generator=mi_funcion_handlers
)

# Procesar mensajes
response = router.route_message("¿Cuáles son mis facturas?")
print(response)
```

### 2. Ejecutar la Implementación de Telecomunicaciones

```bash
# Ejecutar aplicación de ejemplo
python my_app/app_config.py

# O ejecutar API server
python api/server.py
```

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus APIs keys
```

## 🏃‍♂️ Uso

### API REST
```bash
# Iniciar servidor
python -m uvicorn chat_api:app --reload

# Endpoints disponibles:
# POST /chat - Conversación con agentes
# GET /cache/stats - Estadísticas del cache
# POST /cache/clear - Limpiar cache
```

### CLI
```bash
# Interfaz de línea de comandos
python main.py
```

### Interfaz Web
```bash
# Abrir en navegador
http://localhost:8000
# o usar el archivo index.html
```

## 📋 Ejemplos de Uso

```bash
# Consultas de facturas
"¿Cuáles son las facturas del DNI 12345678A?"
"Estado de pagos pendientes"

# Incidencias
"Incidencias en Madrid"
"Crear incidencia por corte de servicio"

# Datos de abonado
"Datos del abonado 12345678A"
"¿Existe el cliente con DNI 87654321B?"

# Consultas referenciales
"DNI 12345678A" -> "sus facturas" -> "incidencias"
```

## ⚙️ Configuración

### Agentes (`app/config/agents_config.json`)
```json
{
  "agents": {
    "factura": {
      "tools": ["todas_las_facturas", "facturas_pendientes"],
      "system_prompt": "Eres un agente especializado en facturas...",
      "can_handle_keywords": ["factura", "pago", "deuda"]
    }
  }
}
```

### APIs (`app/config/config.py`)
```python
OPENAPI_URL = "http://localhost:8000/openapi.json"
API_BASE_URL = "http://localhost:8000"
MODEL = "llama-3.1-70b-versatile"
```

## 🔄 Reutilización en Otros Dominios

### 1. Copiar Framework
```bash
cp -r app/framework/ nuevo_proyecto/
cp -r app/agents/ nuevo_proyecto/
cp -r app/utils/ nuevo_proyecto/
```

### 2. Crear Nueva Configuración
```json
{
  "agents": {
    "ventas": {
      "tools": ["buscar_productos", "crear_cotizacion"],
      "system_prompt": "Eres un asistente de ventas...",
      "can_handle_keywords": ["producto", "precio"]
    }
  }
}
```

### 3. Adaptar Dominio
```python
# config/sales_adapter.py
from app.framework.openapi_cache import GLOBAL_TOOLS_CACHE

def fetch_sales_tools():
    return GLOBAL_TOOLS_CACHE.fetch_tools("https://api-ventas.com/openapi.json")
```

## 📊 Performance

- **Primera consulta**: 0.2-0.4s (con precarga)
- **Cambio de agente**: 0.05-0.1s (cache)
- **Consultas posteriores**: 0.1-0.3s
- **Llamadas HTTP OpenAPI**: 1 total (vs N por agente)

## 🧪 Testing

```bash
# Test de rendimiento del cache
python test_cache_performance.py

# Estadísticas en tiempo real
curl http://localhost:8000/cache/stats
```

## 📁 Estructura del Proyecto

```
mcp_groq/
├── app/
│   ├── framework/              # 🏗️ Framework reutilizable
│   │   ├── openapi_cache.py    # Cache genérico
│   │   ├── agent_framework.py  # Framework de agentes
│   │   └── conversation_context.py
│   ├── config/                 # ⚙️ Configuración específica
│   │   ├── agents_config.json  # Definición de agentes
│   │   ├── domain_adapter.py   # Adaptador del dominio
│   │   └── config.py          # URLs y configuración
│   ├── agents/
│   │   └── shared_chat_agent.py # Agente configurable
│   ├── agent/
│   │   └── multi_agent_router.py # Router específico
│   ├── api/
│   │   └── server.py          # API de telecomunicaciones
│   └── utils/                 # Utilidades genéricas
├── docs/                      # 📚 Documentación
├── chat_api.py               # API principal
├── main.py                   # CLI
├── index.html               # Interfaz web
└── test_cache_performance.py # Testing
```

## 📚 Documentación

- **`docs/ARCHITECTURE_DIAGRAM.md`** - Diagrama de arquitectura
- **`docs/FRAMEWORK_VS_CONFIG_GUIDE.md`** - Guía framework vs configuración
- **`docs/FRAMEWORK_REUSE_EXAMPLE.md`** - Ejemplo de reutilización
- **`docs/PERFORMANCE_OPTIMIZATIONS.md`** - Optimizaciones implementadas
- **`docs/CACHE_OPTIMIZATION_SUMMARY.md`** - Resumen de optimizaciones
- **`docs/REFACTORING_BEFORE_AFTER.md`** - Antes vs después
- **`docs/SEPARATION_SUMMARY.md`** - Resumen de separación

## 🤝 Contribuir

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para detalles.
