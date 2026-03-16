from importlib import resources
import yaml

def build_agents_from_config(config_name: str) -> dict:
    # pylint: disable=import-outside-toplevel
    import devteam.agents as agents_module
    import devteam.tools as tools_module
    config_path = resources.files('devteam.config.crews').joinpath(config_name)
    crew_config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    agents = {}
    for node_name, details in crew_config.get('agents', {}).items():
        class_name = details['class']
        config_file = details['config']
        AgentClass = getattr(agents_module, class_name, None)
        if not AgentClass:
            raise ValueError(f"Configuration Error: '{class_name}' is not a valid class in devteam.agents")
        print(f"Instantiating '{node_name}' as {class_name} with configuration file '{config_file}'...")
        agents[node_name] = AgentClass.from_config(node_name, config_file)
        if sandbox_class := details.get('sandbox', None):
            ToolsClass = getattr(tools_module, sandbox_class, None)
            if not ToolsClass:
                raise ValueError(f"Configuration Error: '{class_name}' is not a valid class in devteam.tools")
            print(f"    Adding {sandbox_class} tool to '{node_name}'...")
            agents[node_name] = agents[node_name].with_sandbox(ToolsClass())
    return agents
