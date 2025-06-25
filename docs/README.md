# Documentación del Proyecto

## 📚 Índice de Documentación

### 🏗️ Arquitectura y Diseño
- **[MODULAR_ARCHITECTURE.md](MODULAR_ARCHITECTURE.md)** - 🆕 **Nueva arquitectura modular framework vs dominio**
- **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** - Diagrama visual de la arquitectura framework vs configuración específica
- **[FRAMEWORK_VS_CONFIG_GUIDE.md](FRAMEWORK_VS_CONFIG_GUIDE.md)** - Guía completa sobre cuándo modificar framework vs configuración
- **[STRUCTURE_SIMPLIFICATION.md](STRUCTURE_SIMPLIFICATION.md)** - Simplificación de la estructura de carpetas de agentes

### 🔄 Reutilización
- **[FRAMEWORK_REUSE_EXAMPLE.md](FRAMEWORK_REUSE_EXAMPLE.md)** - Ejemplo práctico de cómo reutilizar el framework en un proyecto de ventas
- **[SEPARATION_SUMMARY.md](SEPARATION_SUMMARY.md)** - Resumen ejecutivo de la separación completada

### 🚀 Performance y Optimizaciones
- **[PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md)** - Documentación detallada de todas las optimizaciones implementadas
- **[CACHE_OPTIMIZATION_SUMMARY.md](CACHE_OPTIMIZATION_SUMMARY.md)** - Resumen específico de las optimizaciones de cache

### 📈 Refactoring
- **[REFACTORING_BEFORE_AFTER.md](REFACTORING_BEFORE_AFTER.md)** - Comparación completa del antes vs después de la refactorización

## 🎯 Guía de Lectura Recomendada

### Para Desarrolladores Nuevos en el Proyecto:
1. **README.md** (directorio raíz) - Visión general del proyecto
2. **ARCHITECTURE_DIAGRAM.md** - Entender la arquitectura
3. **STRUCTURE_SIMPLIFICATION.md** - Estructura actual simplificada
4. **FRAMEWORK_VS_CONFIG_GUIDE.md** - Aprender qué modificar y cuándo

### Para Reutilizar el Framework:
1. **FRAMEWORK_REUSE_EXAMPLE.md** - Ejemplo práctico paso a paso
2. **SEPARATION_SUMMARY.md** - Entender qué copiar vs qué crear

### Para Mantenimiento y Optimización:
1. **PERFORMANCE_OPTIMIZATIONS.md** - Entender las optimizaciones actuales
2. **CACHE_OPTIMIZATION_SUMMARY.md** - Detalles del sistema de cache
3. **REFACTORING_BEFORE_AFTER.md** - Historia de los cambios

## 🔧 Enlaces Rápidos

### Framework (Reutilizable)
```
app/framework/openapi_cache.py      # Cache genérico de OpenAPI
app/framework/agent_framework.py    # Framework de agentes
app/agents/shared_chat_agent.py     # Agente configurable
app/utils/                          # Utilidades genéricas
```

### Configuración Específica (Telecomunicaciones)
```
app/config/agents_config.json       # Definición de agentes
app/config/domain_adapter.py        # Adaptador del dominio
app/config/config.py                # URLs y configuración
app/agent/multi_agent_router.py     # Router específico
```

### Testing y Desarrollo
```
test_cache_performance.py           # Test de rendimiento
chat_api.py                         # API principal
main.py                             # CLI
```

## 📊 Métricas del Proyecto

- **Framework**: 4 módulos reutilizables
- **Configuración específica**: 6 archivos de dominio
- **Performance**: 5x-40x mejora en velocidad
- **Cache**: 1 carga OpenAPI vs N por agente
- **Agentes**: 4 especializados (factura, incidencia, abonado, default)

## 🎉 Estado del Proyecto

✅ **Arquitectura modular** completada  
✅ **Framework reutilizable** separado  
✅ **Optimizaciones de cache** implementadas  
✅ **Documentación completa** organizada  
✅ **Testing** incluido  
✅ **Código limpio** y reestructurado  

El proyecto está listo para **producción** y **reutilización** en otros dominios.
