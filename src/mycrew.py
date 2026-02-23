from functools import cached_property
import logging
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents import ProductManager, SeniorDeveloper, CodeReviewer, QAEngineer, CrewManager
from project import ProjectState

load_dotenv()

LOG_FILE = 'mycrew.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

class VirtualCrew:
    def __init__(self):
        self._init_agents()
        self.app = self._build_graph()

    def _init_agents(self):
        """Instantiates all agent nodes with the assigned LLM."""
        self.pm = ProductManager()
        self.dev = SeniorDeveloper()
        self.reviewer = CodeReviewer()
        self.qa = QAEngineer()
        self.manager = CrewManager()

    def _router(self, state: ProjectState) -> str:
        """Determines the next step in the workflow based on the Manager's output."""
        next_agent = state.get('next_agent')
        if next_agent == 'FINISH':
            return END
        return next_agent

    @cached_property
    def _memory(self):
        """Initializes a shared memory store for the crew."""
        return MemorySaver()

    def _build_graph(self):
        """Constructs the nodes and edges of the LangGraph state machine."""
        workflow = StateGraph(ProjectState)
        workflow.add_node('manager', self.manager.process)
        workflow.add_node('pm', self.pm.process)
        workflow.add_node('developer', self.dev.process)
        workflow.add_node('reviewer', self.reviewer.process)
        workflow.add_node('qa', self.qa.process)
        workflow.set_entry_point('manager')
        workflow.add_edge('pm', 'manager')
        workflow.add_edge('developer', 'manager')
        workflow.add_edge('reviewer', 'manager')
        workflow.add_edge('qa', 'manager')
        workflow.add_conditional_edges(
            'manager',
            self._router,
            {
                'pm': 'pm',
                'developer': 'developer',
                'reviewer': 'reviewer',
                'qa': 'qa',
                END: END
            }
        )
        return workflow.compile(checkpointer=self._memory)

    def execute_project(self, requirements: str, thread_id: str):
        """Runs the crew against a set of requirements."""
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

        print(f"Starting Project Requirements: {requirements}\n")

        for output in self.app.stream(initial_state, config):
            pass

        final_state = self.app.get_state(config).values
        final_code = final_state.get('code', "No code generated")

        return final_code

if __name__ == '__main__':
    project_requirements = (
        "Build a Python CLI application that accepts a URL, scrapes the text content "
        "from the webpage, and saves it to a local text file. It should handle exceptions gracefully."
    )
    crew = VirtualCrew()
    final_code = crew.execute_project(requirements=project_requirements, thread_id='web_scraper_v1')

    print("\n\n" + "="*50)
    print("PROJECT COMPLETED")
    print("="*50)
    print("FINAL CODE:\n")
    print(final_code)
