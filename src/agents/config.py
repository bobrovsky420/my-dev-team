from crewai import LLM

GPU_CONFIG = {
    'num_ctx': 8192,
    'temperature': 0.7,
    'num_gpu': 1
}

BASE_URL = 'http://localhost:11434'

MANAGER_LLM = LLM(model='ollama/gemma3:4b', base_url=BASE_URL, config=GPU_CONFIG)
PM_LLM = LLM(model='ollama/deepseek-r1:7b', base_url=BASE_URL, config=GPU_CONFIG)
DEV_LLM = LLM(model='ollama/qwen2.5-coder:7b', base_url=BASE_URL, config=GPU_CONFIG)
QA_LLM = LLM(model='ollama/gemma3:4b', base_url=BASE_URL, config=GPU_CONFIG)
