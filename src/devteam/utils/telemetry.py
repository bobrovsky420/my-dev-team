import logging
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from litellm import cost_per_token

class TelemetryTracker(BaseCallbackHandler):
    """Tracks token usage and estimates costs across all agent LLM calls"""

    # Cost per 1 million tokens (Prompt / Completion)
    PRICING = {
        'groq/qwen/qwen3-32b': (0.29, 0.59),
        'groq/groq/compound': (0.15, 0.60)
    }

    def __init__(self):
        self.logger = logging.getLogger('Telemetry')
        self.total_requests = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_cost = 0.0

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Fires automatically every time an LLM finishes generating text"""
        self.total_requests += 1
        model_provider, model_name, input_tokens, output_tokens = self._extract_metadata(response)
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_cost += self._calculate_cost(model_provider, model_name, input_tokens, output_tokens)
        self.logger.info("Accumulated: %i %i %.6f", self.input_tokens, self.output_tokens, self.total_cost)

    def _extract_metadata(self, response) -> tuple:
        input_tokens = 0
        output_tokens = 0
        for generation in (x for row in response.generations for x in row):
            model_provider = generation.message.response_metadata.get('model_provider', 'unknown')
            model_name = generation.message.response_metadata.get('model_name', 'unknown')
            input_tokens += generation.message.usage_metadata.get('input_tokens', 0)
            output_tokens += generation.message.usage_metadata.get('output_tokens', 0)
        self.logger.info("Generation: %s/%s %i %i", model_provider, model_name, input_tokens, output_tokens)
        return model_provider, model_name, input_tokens, output_tokens

    def _calculate_cost(self, model_provider: str, model_name: str, input_tokens: int, output_tokens: int):
        """Calculates the cost based on the specific model used"""
        if model_provider == 'ollama':
            return 0
        try:
            if model_name == 'groq/compound': model_name = 'openai/gpt-oss-120b'
            p_cost, c_cost = cost_per_token(
                model=f'{model_provider}/{model_name}',
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens
            )
            return p_cost + c_cost
        except Exception as e:
            self.logger.error("%s", e)
            return 0

    def print_receipt(self):
        """Prints a receipt"""
        print("\n" + "="*40)
        print("📊 TELEMETRY & COST REPORT")
        print("="*40)
        print(f"Total API Requests:  {self.total_requests}")
        print(f"Prompt Tokens:       {self.input_tokens:,}")
        print(f"Completion Tokens:   {self.output_tokens:,}")
        print(f"Total Tokens:        {self.input_tokens + self.output_tokens:,}")
        print("-" * 40)
        print(f"Estimated Cost:      ${self.total_cost:.4f}")
        print("="*40 + "\n")
