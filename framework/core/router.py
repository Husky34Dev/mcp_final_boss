"""
Router simple para sistemas multi-agente configurables por JSON.
"""
import json
import logging
from typing import Dict, Any, Callable, Optional
from .agent import BaseAgent
from .context import ConfigurableContext


class SimpleRouter:
    """
    Router simple que dirige mensajes a agentes configurados.
    Todo viene de configuración JSON - sin lógica hardcodeada.
    """
    
    def __init__(self, 
                 model: str,
                 agents_config_path: str,
                 context_config_path: str,
                 tools_fetcher: Callable,
                 handlers_generator: Callable):
        """
        Inicializa el router.
        
        Args:
            model: Modelo LLM a usar
            agents_config_path: Ruta al archivo de configuración de agentes
            context_config_path: Ruta al archivo de configuración de contexto
            tools_fetcher: Función para obtener herramientas
            handlers_generator: Función para generar handlers
        """
        
        self.model = model
        self.context_config_path = context_config_path
        self.tools_fetcher = tools_fetcher
        self.handlers_generator = handlers_generator
        self.logger = logging.getLogger(__name__)
        
        # Cargar configuración de agentes
        try:
            with open(agents_config_path, 'r', encoding='utf-8') as f:
                agents_config = json.load(f)
        except FileNotFoundError:
            self.logger.error(f"No se encontró archivo de configuración: {agents_config_path}")
            agents_config = self._get_default_config()
        
        # Crear contexto compartido para todos los agentes
        self.shared_context = ConfigurableContext(context_config_path)
        
        # Crear agentes 
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_configs: Dict[str, Dict[str, Any]] = {}
        for agent_id, agent_config in agents_config.get('agents', {}).items():
            self.agents[agent_id] = self._create_agent(agent_id, agent_config)
            self.agent_configs[agent_id] = agent_config
        
        # Configuración de routing
        self.routing_config = agents_config.get('routing', {})
        self.default_agent = self.routing_config.get('default_agent', 'default')
        
        self.logger.info(f"Router inicializado con {len(self.agents)} agentes")
    
    def _create_agent(self, agent_id: str, agent_config: Dict[str, Any]) -> BaseAgent:
        """Crea un agente individual."""
        
        # Función para obtener herramientas específicas de este agente
        def agent_tools_fetcher(aid: Optional[str]) -> list:
            tool_names = agent_config.get('tools', [])
            if not tool_names:
                return []
            return self.tools_fetcher(tool_names)
        
        agent = BaseAgent(
            model=self.model,
            tools_fetcher=agent_tools_fetcher,
            handlers_generator=self.handlers_generator,
            agent_id=agent_id,
            force_tool_usage=agent_config.get('force_tool_usage', False),
            conversation_context=self.shared_context
        )
        
        # Establecer prompt del sistema si está definido
        system_prompt = agent_config.get('system_prompt', '')
        if system_prompt:
            agent.set_system_prompt(system_prompt)
        
        return agent
    
    def route_message(self, message: str) -> str:
        """
        Dirige un mensaje al agente apropiado.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            str: Respuesta del agente apropiado
        """
        try:
            # Actualizar contexto compartido
            self.shared_context.update(message)
            
            # Determinar qué agente debe manejar el mensaje
            agent_id = self._select_agent(message)
            
            # Obtener el agente seleccionado
            agent = self.agents.get(agent_id)
            if not agent:
                self.logger.warning(f"Agente {agent_id} no encontrado, usando default")
                agent = self.agents.get(self.default_agent)
                if not agent:
                    return "Error: No hay agentes disponibles para procesar la consulta."
            
            self.logger.info(f"Dirigiendo mensaje al agente: {agent_id}")
            
            # Procesar mensaje con el agente seleccionado
            return agent.handle_message(message)
            
        except Exception as e:
            self.logger.error(f"Error en routing: {e}", exc_info=True)
            return "Lo siento, ocurrió un error al procesar tu consulta. Por favor, inténtalo de nuevo."
    
    def _select_agent(self, message: str) -> str:
        """
        Selecciona el agente apropiado basado en el mensaje y la configuración.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            str: ID del agente seleccionado
        """
        # Obtener tipo de query del contexto
        query_type = self.shared_context.get('query_type', 'generic')
        
        # Buscar en configuración de routing
        query_to_agent = self.routing_config.get('query_type_to_agent', {})
        
        # Si hay mapeo directo
        if query_type in query_to_agent:
            return query_to_agent[query_type]
        
        # Fallback: buscar por keywords en los agentes
        message_lower = message.lower()
        for agent_id, agent in self.agents.items():
            if agent_id == self.default_agent:
                continue  # Saltar el agente default en esta búsqueda
                
            agent_config = self.agent_configs.get(agent_id, {})
            keywords = agent_config.get('can_handle_keywords', [])
            if any(keyword in message_lower for keyword in keywords):
                return agent_id
        
        # Si es referencial y hay fallback configurado
        if (self.shared_context.get('is_referential') and 
            self.routing_config.get('referential_fallback', False)):
            # Mantener el último agente usado (podría implementarse)
            pass
        
        # Default fallback
        return self.default_agent
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto si no existe archivo."""
        return {
            "agents": {
                "default": {
                    "name": "DefaultAgent",
                    "description": "Agente por defecto",
                    "tools": [],
                    "system_prompt": "Eres un asistente útil.",
                    "can_handle_keywords": [],
                    "force_tool_usage": False
                }
            },
            "routing": {
                "query_type_to_agent": {},
                "default_agent": "default",
                "referential_fallback": False
            }
        }
