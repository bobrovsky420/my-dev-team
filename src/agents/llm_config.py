from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

def get_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Returns a configured LLM instance."""
    if model_name.startswith('ollama/'):
        return ChatOllama(model=model_name[7:], temperature=temperature, format="json")
    elif model_name.startswith('groq/'):
        actual_model = model_name if model_name == 'groq/compound' else model_name[5:]
        llm = ChatGroq(model=actual_model, temperature=temperature, max_retries=2)
        return llm.bind(response_format={'type': 'json_object'})
    raise ValueError(f"Unsupported model: {model_name}")
