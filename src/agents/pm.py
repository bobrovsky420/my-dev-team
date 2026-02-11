from crewai import Agent
import config

pm = Agent(
    role='Product Manager',
    goal='Convert high-level ideas into detailed technical requirements.',
    backstory='You are an expert at defining MVP features and spotting logic gaps.',
    llm=config.PM_LLM,
    verbose=True
)
