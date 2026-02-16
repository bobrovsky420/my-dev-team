import logging
from crewai import Crew, Process
from agents import agents, config, manager
from human import mailpit as mail

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class MyCrew:
    def __init__(self):
        self.agents = agents.load_agents()
        self.is_running = False

    def create_crew(self, project_description: str) -> Crew:
        """
        Create a crew with hierarchical processing.
        The manager dynamically delegates work to team members.
        """
        return Crew(
            agents=list(self.agents.values()),
            tasks=[manager.create_main_task(project_description)],
            manager_llm=config.MANAGER_LLM,
            process=Process.hierarchical,
            verbose=True
        )

    def run(self):
        self.is_running = True
        while self.is_running:
            logging.info("Manager checking local inbox...")
            original_msg = mail.check_new_project()
            logging.info(f"Processing: {original_msg['Subject']}")
            project_description = original_msg['Text']
            crew = self.create_crew(project_description)
            result = crew.kickoff()
            mail.send_update(str(result))
            logging.info("Cycle complete. Waiting for next email.")
            del crew

    def shutdown(self):
        logging.info("Shutdown command received. Closing office...")
        self.is_running = False

if __name__ == '__main__':
    crew = MyCrew()
    crew.run()
