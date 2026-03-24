import logging
import yaml
import devteam.agents as agents_module
from devteam.settings import get_config_dir
import devteam.tools as tools_module

class AgentsFactory:
    def __init__(self, config_dir = None):
        self.logger = logging.getLogger('Agents Factory')
        self.config_dir = config_dir or get_config_dir()

    def _load_crew_config(self, config_name: str) -> dict:
        config_path = self.config_dir / 'crews' / config_name
        return yaml.safe_load(config_path.read_text(encoding='utf-8'))

    def create_agents(self, config_name: str) -> dict:
        crew_config = self._load_crew_config(config_name)
        agents = {}
        for node_name, details in crew_config.get('agents', {}).items():
            class_name = details['class']
            config_file = details['config']
            AgentClass = getattr(agents_module, class_name, None) # pylint: disable=invalid-name
            if not AgentClass:
                raise ValueError(f"Configuration Error: '{class_name}' is not a valid class in devteam.agents")
            self.logger.debug("Instantiating '%s' as %s with configuration file '%s'...", node_name, class_name, config_file)
            agent = AgentClass.from_config(node_name, config_file)
            if sandbox_class := details.get('sandbox', None):
                ToolsClass = getattr(tools_module, sandbox_class, None) # pylint: disable=invalid-name
                if not ToolsClass:
                    raise ValueError(f"Configuration Error: '{sandbox_class}' is not a valid class in devteam.tools")
                self.logger.debug("Adding %s tool to '%s'...", sandbox_class, node_name)
                agent = agent.with_sandbox(ToolsClass())
            agents[node_name] = agent
        return agents
