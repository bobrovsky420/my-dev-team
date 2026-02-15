from crewai import Agent, Task

def create_tasks(project_description: str, agents: dict[str, Agent]) -> list[Task]:
    """
    Create a list of tasks for the crew based on the project description
    """
    return [
        Task(
            name="Write detailed requirements and specifications",
            agent=agents['pm'],
            description=(
                "Based on the project description below, write detailed requirements and specifications for the project.\n\n"
                "==================================================\n\n"
                f"{project_description}"
            ),
            expected_output="A structured markdown document with features, logic steps, and edge cases to handle."
        ),
        Task(
            name="Develop solution",
            agent=agents['developer'],
            description="Implement a solution based on the technical specification.",
            expected_output="A code block containing the developed solution, including unit tests."
        ),
        Task(
            name="Provide code review",
            agent=agents['reviewer'],
            description="Review the developed solution, identify any issues or improvements, and refine the solution accordingly.",
            expected_output="A final review report confirming the code is production-ready."
        )
    ]
