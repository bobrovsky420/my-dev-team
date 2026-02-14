import logging
from crewai import Task, Crew, Process
from agents import pm, developer, reviewer
import config
import human.mailpit as mail

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class MyCrew:
    def __init__(self):
        self.agents = [pm, developer, reviewer]
        self.is_running = False

    def create_crew(self, project_description):
        main_task = Task(
            description=f"Analyze and implement this project: {project_description}",
            expected_output="Final production-ready code blocks and review report."
        )
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
            original_msg = mail.check_inbox()
            logging.info(f"Processing: {original_msg['Subject']}")
            project_description = original_msg['Text']
            crew = self.create_crew(project_description)
            result = crew.kickoff()
            mail.send_update(str(result), original_msg)
            logging.info("Cycle complete. Waiting for next email.")
            del crew

    def shutdown(self, msg):
        logging.info("Shutdown command received. Closing office...")
        self.is_running = False

if __name__ == '__main__':
    crew = MyCrew()
    crew.run()
