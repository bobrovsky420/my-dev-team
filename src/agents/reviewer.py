from crewai import Agent
import config

reviewer = Agent(
    role='Code Reviewer',
    goal='Audit code for bugs, security risks, and optimization opportunities.',
    backstory='You have a sharp eye for edge cases and never let sloppy code pass.',
    llm=config.QA_LLM,
    verbose=True
)
