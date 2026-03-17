import logging
import yaml
from ..settings import get_config_dir

logger = logging.getLogger("Crew Factory")

def load_crew_config(config_name: str) -> dict:
    config_path = get_config_dir() / 'crews' / config_name
    return yaml.safe_load(config_path.read_text(encoding='utf-8'))

def build_agents_from_config(config_name: str) -> dict:
    """Agents factory"""
    # pylint: disable=import-outside-toplevel,cyclic-import
    import devteam.agents as agents_module
    import devteam.tools as tools_module
    crew_config = load_crew_config(config_name)
    agents = {}
    for node_name, details in crew_config.get('agents', {}).items():
        class_name = details['class']
        config_file = details['config']
        AgentClass = getattr(agents_module, class_name, None)
        if not AgentClass:
            raise ValueError(f"Configuration Error: '{class_name}' is not a valid class in devteam.agents")
        logger.debug("Instantiating '%s' as %s with configuration file '%s'...", node_name, class_name, config_file)
        agents[node_name] = AgentClass.from_config(node_name, config_file)
        if sandbox_class := details.get('sandbox', None):
            ToolsClass = getattr(tools_module, sandbox_class, None)
            if not ToolsClass:
                raise ValueError(f"Configuration Error: '{sandbox_class}' is not a valid class in devteam.tools")
            logger.debug("Adding %s tool to '%s'...", sandbox_class, node_name)
            agents[node_name] = agents[node_name].with_sandbox(ToolsClass())
    return agents
