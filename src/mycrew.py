from dotenv import load_dotenv
import logging
import time
from crewai import Crew, Process
from agents import agents, manager
from mail import mailpit as mail

load_dotenv()

LOG_FILE = 'mycrew.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

class MyCrew:
    def __init__(self):
        self.agents = agents.load_agents()
        self.is_running = False

    @staticmethod
    def _task_callback(task_output):
        """
        Forces the system to wait after every task to avoid Groq Rate Limits
        """
        timeout = 30
        logging.warning("Task finished. Cooling down for %i sec to respect Groq Free Tier limits...", timeout)
        time.sleep(timeout)

    def create_crew(self) -> Crew:
        return Crew(
            agents=list(self.agents.values()),
            tasks=manager.create_tasks(self.agents),
            process=Process.sequential,
#            task_callback=self._task_callback,
            verbose=True
        )

    def run(self):
        self.is_running = True
        while self.is_running:
            logging.info("Manager checking local inbox...")
            project = mail.check_new_project()
            logging.info(f"Processing: {project.title}")
            crew = self.create_crew()
            result = crew.kickoff(inputs={'project_description': project.description})
            if result.pydantic:
                final_output = (
                    f"# {result.pydantic.title}\n\n"
                    f"## Description\n{result.pydantic.description}\n\n"
                    f"## Requirements\n{result.pydantic.requirements}\n\n"
                    f"## Constraints\n{result.pydantic.constraints}\n\n"
                    f"## Edge Cases\n{result.pydantic.edge_cases}\n\n"
                    f"## Additional Notes\n{result.pydantic.additional_notes}"
                )
            else:
                final_output = result.raw
            mail.send_update(final_output)
            logging.info("Cycle complete. Waiting for next email.")
            del crew
            exit(0)

    def shutdown(self):
        logging.info("Shutdown command received. Closing office...")
        self.is_running = False

if __name__ == '__main__':
    crew = MyCrew()
    crew.run()
