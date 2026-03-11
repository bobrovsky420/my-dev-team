from langchain_core.language_models.chat_models import BaseChatModel

MODEL_MAP = {
    'groq': {
        'reasoning': 'groq/compound',
        'code-generator': 'groq/compound',
        'code-analyzer': 'groq/compound',
        'fast-utility': 'groq/compound'
    },
    'ollama': {
        'reasoning': 'qwen3:8b',
        'code-generator': 'qwen2.5-coder:7b',
        'code-analyzer': 'qwen2.5-coder:7b',
        'fast-utility': 'gemma3:4b'
    },
    'openai': {
        'reasoning': 'o1-preview',
        'code-generator': 'gpt-4o',
        'code-analyzer': 'gpt-4o',
        'fast-utility': 'gpt-4o-mini'
    }
}

class LLMFactory:
    def __init__(self, provider: str):
        self.provider = provider.lower()
        if self.provider not in MODEL_MAP:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def create(self, category: str, temperature: float) -> BaseChatModel:
        """Returns a configured LLM instance."""
        model_name = MODEL_MAP[self.provider].get(category, MODEL_MAP[self.provider]['reasoning'])
        match self.provider:
            case 'ollama':
                from langchain_ollama import ChatOllama
                return ChatOllama(model=model_name, temperature=temperature, format='json')
            case 'groq':
                from langchain_groq import ChatGroq
                llm = ChatGroq(model=model_name, temperature=temperature, max_retries=2)
                return llm.bind(response_format={'type': 'json_object'})
            case 'openai':
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(model=model_name, temperature=temperature)
