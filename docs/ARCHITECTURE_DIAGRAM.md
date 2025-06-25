# Arquitectura: Framework vs Configuración Específica

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          🏗️ FRAMEWORK REUTILIZABLE                              │
│                         (Independiente del dominio)                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │ OpenAPICache    │    │ AgentFramework  │    │ SharedChatAgent │             │
│  │                 │    │                 │    │                 │             │
│  │ • fetch_tools() │    │ • load_config() │    │ • configurable  │             │
│  │ • filter_tools()│    │ • route_agent() │    │ • tool_executor │             │
│  │ • cache_system  │    │ • get_prompts() │    │ • context_mgmt  │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│                                  │                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │ ToolExecutor    │    │ ContextManager  │    │ ResponseGuard   │             │
│  │                 │    │                 │    │                 │             │
│  │ • execute()     │    │ • track_state() │    │ • validate()    │             │
│  │ • handle_errors │    │ • persist_data()│    │ • sanitize()    │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ usa
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     ⚙️ CONFIGURACIÓN ESPECÍFICA DEL DOMINIO                     │
│                         (Telecomunicaciones/Facturas)                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │ agents_config   │    │ domain_adapter  │    │ context_config  │             │
│  │                 │    │                 │    │                 │             │
│  │ • "factura"     │    │ • call_api()    │    │ • DNI validation│             │
│  │ • "incidencia"  │    │ • clean_schema()│    │ • query_types   │             │
│  │ • "abonado"     │    │ • OPENAPI_URL   │    │ • field_rules   │             │
│  │ • tools mapping │    │ • API_BASE_URL  │    │ • error_msgs    │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                                    │
│  │ MultiAgentRouter│    │ API Endpoints   │                                    │
│  │                 │    │                 │                                    │
│  │ • routing logic │    │ • /datos_abonado│                                    │
│  │ • agent_cache   │    │ • /facturas     │                                    │
│  │ • context flow  │    │ • /incidencias  │                                    │
│  └─────────────────┘    └─────────────────┘                                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Para Reutilizar en Otro Dominio (ej. Ventas)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          🏗️ FRAMEWORK REUTILIZABLE                              │
│                           (SE COPIA TAL CUAL)                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  [Exactamente el mismo código del framework]                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ usa
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ⚙️ NUEVA CONFIGURACIÓN ESPECÍFICA                       │
│                              (Ventas/Productos)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │ agents_config   │    │ sales_adapter   │    │ sales_context   │             │
│  │                 │    │                 │    │                 │             │
│  │ • "productos"   │    │ • call_sales()  │    │ • price validation│           │
│  │ • "cotizaciones"│    │ • clean_price() │    │ • product_types │             │
│  │ • "clientes"    │    │ • SALES_API_URL │    │ • currency_rules│             │
│  │ • tools mapping │    │ • API_TOKEN     │    │ • discount_msgs │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                                    │
│  │ SalesRouter     │    │ Sales Endpoints │                                    │
│  │                 │    │                 │                                    │
│  │ • sales logic   │    │ • /productos    │                                    │
│  │ • product_cache │    │ • /cotizaciones │                                    │
│  │ • quote flow    │    │ • /clientes     │                                    │
│  └─────────────────┘    └─────────────────┘                                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 📝 Guía Rápida de Separación

### ✅ ES FRAMEWORK (Reutilizable) SI:
- Maneja cache de herramientas OpenAPI ✓
- Ejecuta herramientas genéricamente ✓  
- Gestiona contexto conversacional ✓
- Enruta entre agentes ✓
- Valida respuestas ✓
- **No menciona**: facturas, DNI, telecomunicaciones

### ⚙️ ES CONFIGURACIÓN (Específico) SI:
- Define agentes como "factura", "incidencia" ✓
- Contiene URLs específicas de APIs ✓
- Tiene lógica de validación de DNI ✓
- Maneja tipos de consulta específicos ✓
- Contiene prompts del dominio ✓
- **Menciona**: facturas, telecomunicaciones, DNI

### 🎯 REGLA SIMPLE:
**Si cambio de "telecomunicaciones" a "ventas" y necesito modificarlo → Es configuración específica**  
**Si funciona igual en ambos dominios → Es framework reutilizable**
