from crewai import Agent
import config

developer = Agent(
    role='Senior JavaScript Developer',
    goal='Write clean, efficient, and well-documented JavaScript code.',
    backstory='You are a master of JavaScript and follow best practices strictly.',
    llm=config.DEV_LLM,
    verbose=True
)
