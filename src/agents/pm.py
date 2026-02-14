from crewai import Agent
import config

pm = Agent(
    role='Product Manager',
    goal='Choose the best programming language and create specs.',
    backstory='You decide the tech stack based on project needs.',
    llm=config.REASONING_LLM
)
