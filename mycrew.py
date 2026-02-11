from crewai import Agent, Task, Crew, Process, LLM

gpu_config = {
    "num_ctx": 8192,
    "temperature": 0.7,
    "num_gpu": 1
}

dev_llm = LLM(model="ollama/qwen2.5-coder:7b", base_url="http://localhost:11434", config=gpu_config)
reasoning_llm = LLM(model="ollama/deepseek-r1:7b", base_url="http://localhost:11434", config=gpu_config)
qa_llm = LLM(model="ollama/gemma3:4b", base_url="http://localhost:11434", config=gpu_config)

pm = Agent(
    role='Product Manager',
    goal='Convert high-level ideas into detailed technical requirements.',
    backstory='You are an expert at defining MVP features and spotting logic gaps in project plans.',
    llm=reasoning_llm,
    verbose=True
)

developer = Agent(
    role='Senior Python Developer',
    goal='Write clean, efficient, and well-documented Python code.',
    backstory='You are a master of Python 3.12+ and follow PEP8 strictly.',
    llm=dev_llm,
    verbose=True
)

reviewer = Agent(
    role='Code Reviewer',
    goal='Audit code for bugs, security risks, and optimization opportunities.',
    backstory='You have a sharp eye for edge cases and never let a sloppy line of code pass.',
    llm=qa_llm,
    verbose=True
)

project_description = """
Project
=======
AI Dev Crew

Objective
=========
Build a Python `crewai` multi-agent system which will create a Python application based on the provided projects description.

Required Team
=============
1. Product Manager (PM): Create a technical specification based on the project description.
2. Developer: Implement the code according to the PM's specification.
3. Reviewer: Audit the code for quality and correctness.
"""

task1 = Task(
    description=f"Create a technical specification for: {project_description}",
    agent=pm,
    expected_output="A structured markdown document with features, logic steps, and edge cases to handle."
)

task2 = Task(
    description="Implement the Python script based on the PM's specification.",
    agent=developer,
    expected_output="A single .py file containing the full implementation."
)

task3 = Task(
    description="Review the developer's code. Provide a 'Pass' or 'Fail' report with specific feedback.",
    agent=reviewer,
    expected_output="A review report followed by the final, refined code block."
)

dev_team = Crew(
    agents=[pm, developer, reviewer],
    tasks=[task1, task2, task3],
    process=Process.sequential,
    verbose=True
)

result = dev_team.kickoff()
