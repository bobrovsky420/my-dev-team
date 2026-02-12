from crewai import Task, Crew, Process
from agents import pm, developer, reviewer

project_description = """
Develop a JavaScript bookmarklet that will be running on top of GitLab.
The bookmarklet will do:
    1) Clone predefined GitLab project to the user's namespace:
        - User should provide the new desired project name
    2) Create a new personal token with API access.
    3) Setup CI/CD variables:
        - GROUP_PRIVATE_TOKEN: the personal token created in step 2.
        - DQ_MAIL_LIST: user's e-mail address.
"""

task1 = Task(
    description=f"Create a technical specification for: {project_description}",
    agent=pm,
    expected_output="A structured markdown document."
)

task2 = Task(
    description="Implement the JavaScript bookmarklet based on the PM's specification.",
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

if __name__ == '__main__':
    result = dev_team.kickoff()
    print(result)
