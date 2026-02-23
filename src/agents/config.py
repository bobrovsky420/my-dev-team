from langchain_ollama import ChatOllama

def get_llm(model_name: str = "qwen3:8b", temperature: float = 0.2):
    """Returns a configured local Ollama instance."""
    return ChatOllama(model=model_name, temperature=temperature)
