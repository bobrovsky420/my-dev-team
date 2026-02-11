from crewai import Agent
import config

developer = Agent(
    role='Senior Python Developer',
    goal='Write clean, efficient, and well-documented Python code.',
    backstory='You are a master of Python 3.12+ and follow PEP8 strictly.',
    llm=config.DEV_LLM,
    verbose=True
)
