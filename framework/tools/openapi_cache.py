"""
Sistema de cache genérico para herramientas OpenAPI.
Este módulo es independiente del dominio y puede reutilizarse en cualquier proyecto.
"""
import httpx
import jsonref
import logging
from typing import Optional, List, Dict, Any


class OpenAPIToolsCache:
    """
    Cache genérico para herramientas OpenAPI que puede reutilizarse en cualquier proyecto.
    Independiente del dominio específico (facturas, ventas, etc.)
    """
    
    def __init__(self):
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._filtered_tools_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._handlers_cache: Dict[str, Any] = {}
        self._tools_loading = False
    
    def fetch_tools(self, openapi_url: str, schema_cleaner_func=None) -> List[Dict[str, Any]]:
        """
        Descarga y cachea herramientas desde una especificación OpenAPI.
        
        Args:
            openapi_url: URL de la especificación OpenAPI
            schema_cleaner_func: Función opcional para limpiar schemas (específica del dominio)
        
        Returns:
            Lista de herramientas en formato compatible con LLMs
        """
        # Si ya tenemos las herramientas en cache, devolverlas
        if self._tools_cache is not None:
            logging.debug(f"Using cached tools: {len(self._tools_cache)} tools")
            return self._tools_cache
        
        # Evitar cargas concurrentes
        if self._tools_loading:
            logging.warning("Tools are already being loaded, waiting...")
            import time
            while self._tools_loading and self._tools_cache is None:
                time.sleep(0.1)
            return self._tools_cache if self._tools_cache is not None else []
        
        # Primera carga: descargar desde OpenAPI
        self._tools_loading = True
        logging.info("Loading tools from OpenAPI (first time)...")
        
        try:
            r = httpx.get(openapi_url, timeout=10.0)
            r.raise_for_status()
            spec = jsonref.JsonRef.replace_refs(r.json())

            tools = []
            paths = spec.get("paths", {}) if isinstance(spec, dict) else {}
            
            for path, methods in paths.items():
                if not isinstance(methods, dict):
                    continue
                    
                for method, op in methods.items():
                    if not isinstance(op, dict):
                        continue
                        
                    operation_id = op.get("operationId")
                    if not operation_id:
                        continue
                        
                    schema = (
                        op.get("requestBody", {})
                          .get("content", {})
                          .get("application/json", {})
                          .get("schema", {})
                    )
                    
                    # Aplicar limpieza de schema si se proporciona (específico del dominio)
                    if schema_cleaner_func:
                        parameters = schema_cleaner_func(schema)
                    else:
                        parameters = schema
                    
                    description = op.get("description")
                    if not description:
                        description = f"Esta herramienta realiza la operación '{operation_id}' en el endpoint '{path}' usando el método '{method.upper()}.'"
                    
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": operation_id,
                            "description": description,
                            "parameters": parameters
                        },
                        "endpoint": path,
                        "method": method.upper()
                    })
            
            # Guardar en cache
            self._tools_cache = tools
            logging.info(f"Loaded and cached {len(tools)} tools from OpenAPI")
            return tools
            
        except Exception as e:
            logging.error(f"Error loading tools from OpenAPI: {e}")
            # Si hay error, devolver lista vacía para evitar fallos
            self._tools_cache = []
            return self._tools_cache
            
        finally:
            self._tools_loading = False
    
    def get_filtered_tools(self, agent_id: str, allowed_tools: List[str]) -> List[Dict[str, Any]]:
        """
        Obtiene herramientas filtradas para un agente específico.
        
        Args:
            agent_id: ID del agente
            allowed_tools: Lista de nombres de herramientas permitidas para este agente
        
        Returns:
            Lista de herramientas filtradas
        """
        # Verificar si ya tenemos las herramientas filtradas en cache
        if agent_id in self._filtered_tools_cache:
            logging.debug(f"Using cached filtered tools for agent: {agent_id}")
            return self._filtered_tools_cache[agent_id]
        
        # Primera vez para este agente: filtrar y cachear
        if self._tools_cache is None:
            raise ValueError("Tools not loaded. Call fetch_tools() first.")
        
        filtered_tools = []
        for tool in self._tools_cache:
            tool_name = tool['function']['name']
            if tool_name in allowed_tools:
                filtered_tools.append(tool)
        
        # Guardar en cache específico para este agente
        self._filtered_tools_cache[agent_id] = filtered_tools
        logging.info(f"Filtered and cached {len(filtered_tools)} tools for agent: {agent_id}")
        
        return filtered_tools
    
    def generate_handlers(self, tools: List[Dict[str, Any]], api_caller_func) -> Dict[str, Any]:
        """
        Genera handlers HTTP para las herramientas.
        
        Args:
            tools: Lista de herramientas
            api_caller_func: Función para hacer llamadas HTTP (específica del dominio)
        
        Returns:
            Diccionario de handlers
        """
        # Crear una clave de cache basada en los nombres de las herramientas
        tool_names = sorted([tool["function"]["name"] for tool in tools])
        cache_key = f"handlers_{'_'.join(tool_names)}"
        
        # Verificar si ya tenemos estos handlers en cache
        if cache_key in self._handlers_cache:
            logging.debug(f"Using cached handlers for {len(tools)} tools")
            return self._handlers_cache[cache_key]
        
        # Generar handlers por primera vez
        handlers = {}
        for tool in tools:
            name = tool["function"]["name"]
            endpoint = tool["endpoint"]
            method = tool["method"]
            
            def make_handler(ep, mtd):
                def handler(**kwargs):
                    return api_caller_func(ep, mtd, kwargs)
                return handler
            
            handlers[name] = make_handler(endpoint, method)
        
        # Guardar en cache
        self._handlers_cache[cache_key] = handlers
        logging.info(f"Generated and cached handlers for {len(tools)} tools")
        
        return handlers
    
    def clear_cache(self):
        """Limpia todo el cache"""
        self._tools_cache = None
        self._tools_loading = False
        self._filtered_tools_cache.clear()
        self._handlers_cache.clear()
        logging.info("Tools cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        return {
            "tools_cached": self._tools_cache is not None,
            "tools_count": len(self._tools_cache) if self._tools_cache else 0,
            "filtered_tools_cache_entries": len(self._filtered_tools_cache),
            "handlers_cache_entries": len(self._handlers_cache),
            "tools_loading": self._tools_loading,
            "cached_agents": list(self._filtered_tools_cache.keys()) if self._filtered_tools_cache else []
        }


# Instancia global del sistema de cache (puede reutilizarse en cualquier proyecto)
GLOBAL_TOOLS_CACHE = OpenAPIToolsCache()
