from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

LOCAL_TEST_MODELS = {
    'coder': 'ollama/qwen2.5-coder:7b',
    'reasoning': 'ollama/qwen3:8b',
    'text': 'ollama/gemma3:4b'
}

GROQ_TEST_MODELS = {
    'coder': 'groq/compound',
    'reasoning': 'groq/compound',
    'text': 'groq/compound'
}

TEST_MODELS = LOCAL_TEST_MODELS

def get_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Returns a configured LLM instance."""
    if model_name.startswith('test/'):
        model_name = TEST_MODELS[model_name[5:]]
    if model_name.startswith('ollama/'):
        return ChatOllama(model=model_name[7:], temperature=temperature, format="json")
    if model_name.startswith('groq/'):
        actual_model = model_name if model_name == 'groq/compound' else model_name[5:]
        llm = ChatGroq(model=actual_model, temperature=temperature, max_retries=2)
        return llm.bind(response_format={'type': 'json_object'})
    raise ValueError(f"Unsupported model: {model_name}")
