from crewai import Agent
import config

reviewer = Agent(
    role='Code Reviewer',
    goal='Find bugs and send them back to the dev.',
    backstory='You are the gatekeeper of quality.',
    llm=config.QA_LLM
)
