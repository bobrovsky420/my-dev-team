from crewai import Agent
import config

developer = Agent(
    role='Senior Developer',
    goal='Write the code in the language chosen by the PM.',
    backstory='You implement the PMs specs perfectly.',
    max_iter=3,
    llm=config.DEV_LLM
)
