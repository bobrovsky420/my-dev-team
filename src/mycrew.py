import logging
from crewai import Crew, Process
import agents
import config
import human.mailpit as mail

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class MyCrew:
    def __init__(self):
        self.agents = agents.load_agents()
        self.is_running = False

    def create_crew(self, project_description: str) -> Crew:
        """
        Create a crew with defined agents and a main task based on the project description
        """
        main_task = agents.load_main_task(project_description)
        return Crew(
            agents=self.agents,
            tasks=[main_task],
            process=Process.hierarchical,
            manager_llm=config.REASONING_LLM,
            verbose=True
        )

    def run(self):
        self.is_running = True
        while self.is_running:
            logging.info("Manager checking local inbox...")
            original_msg = mail.check_new_project()
            mail.delete_message(original_msg['ID'])
            logging.info(f"Processing: {original_msg['Subject']}")
            project_description = original_msg['Text']
            crew = self.create_crew(project_description)
            result = crew.kickoff()
            mail.send_update(str(result), original_msg)
            logging.info("Cycle complete. Waiting for next email.")
            del crew

    def shutdown(self):
        logging.info("Shutdown command received. Closing office...")
        self.is_running = False

if __name__ == '__main__':
    crew = MyCrew()
    crew.run()
