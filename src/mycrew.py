from functools import cached_property
import logging
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents import ProductManager, SeniorDeveloper, CodeJudge, CodeReviewer, QAEngineer, CrewManager
from project import ProjectState

load_dotenv()

LOG_FILE = 'mycrew.log'

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s [%(name)s]: %(message)s',
    handlers=[
        file_handler,
        console_handler
    ]
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

class VirtualCrew:
    role: str = 'Virtual Crew'

    def __init__(self):
        self.logger = logging.getLogger(self.role)
        self.agents = self._init_agents()
        self.agents['manager'].developers = self._developers
        self.app = self._build_graph()

    def _init_agents(self):
        return {
            'pm': ProductManager.from_config('agents/pm.yml'),
            'dev 1': SeniorDeveloper.from_config('agents/developer_1.yml'),
            'dev 2': SeniorDeveloper.from_config('agents/developer_2.yml'),
            'judge': CodeJudge.from_config('agents/judge.yml'),
            'reviewer': CodeReviewer.from_config('agents/reviewer.yml'),
            'qa': QAEngineer.from_config('agents/qa.yml'),
            'manager': CrewManager.from_config('agents/manager.yml')
        }

    @cached_property
    def _developers(self):
        return ['dev 1', 'dev 2']

    @cached_property
    def _memory(self):
        return MemorySaver()

    def _build_graph(self):
        workflow = StateGraph(ProjectState)
        workflow.add_node('manager', self.agents['manager'].router)
        workflow.add_node('pm', self.agents['pm'].process)
        for dev in self._developers:
            workflow.add_node(dev, self.agents[dev].process)
        workflow.add_node('judge', self.agents['judge'].process)
        workflow.add_node('reviewer', self.agents['reviewer'].process)
        workflow.add_node('qa', self.agents['qa'].process)
        workflow.add_node('human', self._human_node)
        workflow.add_node('report', self.agents['manager'].process)
        workflow.set_entry_point('manager')
        workflow.add_conditional_edges('manager', lambda state: state['next_agent'])
        workflow.add_edge('pm', 'manager')
        for dev in self._developers:
            workflow.add_edge(dev, 'manager')
        workflow.add_edge('judge', 'manager')
        workflow.add_edge('reviewer', 'manager')
        workflow.add_edge('qa', 'manager')
        workflow.add_edge('human', 'manager')
        workflow.add_edge('report', END)
        return workflow.compile(checkpointer=self._memory, interrupt_before=['human'])

    def _human_node(self, state: ProjectState) -> dict:
        """Dummy node that acts as a breakpoint for human input."""
        # The actual input() prompt happens in the execution loop.
        # This node just clears the question so we don't get stuck in a loop.
        return {'clarification_question': ''}

    def execute_project(self, requirements: str, thread_id: str):
        initial_state = {
            'requirements': requirements,
            'specs': '',
            'code': '',
            'review_feedback': '',
            'test_results': '',
            'revision_count': 0,
            'next_agent': '',
            'project_status': 'started'
        }

        config = {'configurable': {'thread_id': thread_id}}

        self.logger.info("Starting Project Requirements:\n%s", requirements)

        while True:
            for output in self.app.stream(initial_state if 'initial_state' in locals() else None, config):
                pass

            # Remove initial_state so we don't overwrite memory on resumption
            if 'initial_state' in locals():
                del initial_state

            state_snapshot = self.app.get_state(config)

            if not state_snapshot.next:
                break

            if state_snapshot.next[0] == 'human':
                question = state_snapshot.values.get('clarification_question')
                print(f"\n[Product Manager Needs Clarification]: {question}")
                user_answer = input("Your response: ")
                self.app.update_state(config, {'human_answer': user_answer})
                self.logger.info("Resuming workflow...")

        final_state = self.app.get_state(config).values
        final_report = final_state.get('final_report', "No report generated.")

        return final_report

if __name__ == '__main__':
    project_requirements = (
        "Build a Python CLI application that accepts a URL, scrapes the text content "
        "from the webpage, and saves it to a local text file. It should handle exceptions gracefully."
    )
    crew = VirtualCrew()
    final_report = crew.execute_project(requirements=project_requirements, thread_id='my_project')

    print("\n\n" + "="*50)
    print("PROJECT COMPLETED - FINAL REPORT")
    print("="*50)
    print(final_report)
