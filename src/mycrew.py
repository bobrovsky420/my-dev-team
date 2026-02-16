import logging
import re
from crewai import Crew, Process
from agents import agents, manager
from mail import mailpit as mail

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
            original_msg = mail.check_new_project()
            logging.info(f"Processing: {original_msg['Subject']}")
            project_description = original_msg['Text']
            crew = self.create_crew()
            result = str(crew.kickoff(inputs={'project_description': project_description}))
            if result_body := re.search(r'```markdown(.+)```', result, re.IGNORECASE | re.DOTALL):
                result = result_body.group(1)
            mail.send_update(result)
            logging.info("Cycle complete. Waiting for next email.")
            del crew

    def shutdown(self):
        logging.info("Shutdown command received. Closing office...")
        self.is_running = False

if __name__ == '__main__':
    crew = MyCrew()
    crew.run()
