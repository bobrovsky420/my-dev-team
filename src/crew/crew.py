from functools import cached_property
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents import ProductManager, SystemArchitect, SeniorDeveloper, CodeJudge, CodeReviewer, QAEngineer, CrewManager
from project import ProjectState
from extensions import CrewExtension

class VirtualCrew:
    role: str = 'Virtual Crew'

    def __init__(self, extensions: list[CrewExtension] = None):
        self.logger = logging.getLogger(self.role)
        self.extensions = extensions or []
        self.agents = self._init_agents()
        self.developers = self._init_developers()
        self.agents['manager'].developers = self.developers
        self.app = self._build_graph()

    def _init_agents(self):
        return {
            'pm': ProductManager.from_config('agents/pm.yml'),
            'architect': SystemArchitect.from_config('agents/architect.yml'),
            'judge': CodeJudge.from_config('agents/judge.yml'),
            'reviewer': CodeReviewer.from_config('agents/reviewer.yml'),
            'qa': QAEngineer.from_config('agents/qa.yml'),
            'manager': CrewManager.from_config('agents/manager.yml')
        }

    def _init_developers(self):
        name = 'dev'
        devs = SeniorDeveloper.from_config('agents/developer.yml')
        if isinstance(devs, list):
            return {f'{name}_{i+1}': dev for i, dev in enumerate(devs)}
        return {name: devs}

    @cached_property
    def _memory(self):
        return MemorySaver()

    def _build_graph(self):
        workflow = StateGraph(ProjectState)
        workflow.add_node('manager', self.agents['manager'].router)
        workflow.add_node('officer', self.agents['manager'].queue_manager)
        workflow.add_node('pm', self.agents['pm'].process)
        workflow.add_node('architect', self.agents['architect'].process)
        for dev in self.developers:
            workflow.add_node(dev, self.developers[dev].process)
        workflow.add_node('judge', self.agents['judge'].process)
        workflow.add_node('reviewer', self.agents['reviewer'].process)
        workflow.add_node('qa', self.agents['qa'].process)
        workflow.add_node('final_qa', self.agents['qa'].process)
        workflow.add_node('human', self._dummy_human_node)
        workflow.add_node('report', self.agents['manager'].process)
        workflow.set_entry_point('manager')
        workflow.add_conditional_edges('manager', lambda state: state['next_agent'])
        workflow.add_edge('officer', 'manager')
        workflow.add_edge('pm', 'manager')
        workflow.add_edge('architect', 'manager')
        for dev in self.developers:
            workflow.add_edge(dev, 'manager')
        workflow.add_edge('judge', 'manager')
        workflow.add_edge('reviewer', 'manager')
        workflow.add_edge('qa', 'manager')
        workflow.add_edge('final_qa', 'manager')
        workflow.add_edge('human', 'manager')
        workflow.add_edge('report', END)
        return workflow.compile(
            checkpointer=self._memory,
            interrupt_before=['human']
        )

    def _dummy_human_node(self, state: dict) -> dict:
        """Passthrough node for Human-in-the-Loop interruptions."""
        self.logger.info("Human input received. Routing back to workflow...")
        return {'clarification_question': ''}

    def execute_project(self, requirements: str, thread_id: str):
        config = {'configurable': {'thread_id': thread_id}}

        self.logger.info("Starting Project Requirements:\n%s", requirements)

        initial_state = {
            'requirements': requirements,
            'clarification_question': '',
            'human_answer': '',
            'specs': '',
            'pending_tasks': [],
            'current_task': '',
            'completed_tasks': [],
            'code_drafts': [],
            'code': '',
            'task_phase': 'drafting',
            'winner_index': 0,
            'review_feedback': '',
            'test_results': '',
            'revision_count': 0,
            'project_status': 'started',
            'final_report': '',
            'communication_log': []
        }
        for ext in self.extensions:
            ext.on_start(thread_id, initial_state)
        while True:
            for full_state in self.app.stream(initial_state if 'initial_state' in locals() else None, config, stream_mode='values'):
                for ext in self.extensions:
                    ext.on_step(thread_id, full_state)
            if 'initial_state' in locals(): # Remove initial_state so we don't overwrite memory on resumption
                del initial_state
            state_snapshot = self.app.get_state(config)
            if not state_snapshot.next:
                break
            next_node = state_snapshot.next[0]
            for ext in self.extensions:
                update = ext.on_pause(thread_id, state_snapshot.values, next_node)
                if update:
                    self.app.update_state(config, update)
        final_state = self.app.get_state(config).values
        for ext in self.extensions:
            ext.on_finish(thread_id, final_state)
        return final_state.get('final_report', "No report generated.")
