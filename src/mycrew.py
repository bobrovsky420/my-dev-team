import human.mailpit as mail

original_msg = mail.check_inbox()
project_description = original_msg['Text']

from crewai import Task, Crew, Process
from agents import pm, developer, reviewer

task1 = Task(
    description=f"Create a technical specification for:\n{project_description}",
    agent=pm,
    expected_output="A structured markdown document."
)

task2 = Task(
    description="Implement the JavaScript application based on the PM's specification.",
    agent=developer,
    expected_output="A single .js file."
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

result = dev_team.kickoff()

mail.send_update(str(result), original_msg)
