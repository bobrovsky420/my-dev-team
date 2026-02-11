from crewai import Task, Crew, Process
from agents import pm, developer, reviewer

project_description = "AI Dev Crew system to build Python apps based on descriptions."

task1 = Task(
    description=f"Create a technical specification for: {project_description}",
    agent=pm,
    expected_output="A structured markdown document."
)

task2 = Task(
    description="Implement the Python script based on the PM's specification.",
    agent=developer,
    expected_output="A single .py file."
)

task3 = Task(
    description="Review the developer's code. Provide a Pass/Fail report.",
    agent=reviewer,
    expected_output="A review report and final code."
)

dev_team = Crew(
    agents=[pm, developer, reviewer],
    tasks=[task1, task2, task3],
    process=Process.sequential,
    verbose=True
)

if __name__ == '__main__':
    result = dev_team.kickoff()
    print(result)
