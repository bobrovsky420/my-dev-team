from dotenv import load_dotenv
import logging
from crewai import Crew, Process
from agents import agents, manager
from mail import mailpit as mail

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class MyCrew:
    def __init__(self):
        self.agents = agents.load_agents()
        self.is_running = False

    def create_crew(self) -> Crew:
        return Crew(
            agents=list(self.agents.values()),
            tasks=manager.create_tasks(self.agents),
            process=Process.sequential,
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
                final_output = result.pydantic.content
            else:
                final_output = result.raw
            mail.send_update(final_output)
            logging.info("Cycle complete. Waiting for next email.")
            del crew

    def shutdown(self):
        logging.info("Shutdown command received. Closing office...")
        self.is_running = False

if __name__ == '__main__':
    crew = MyCrew()
    crew.run()
