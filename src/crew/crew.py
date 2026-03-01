from functools import cached_property
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents import ProductManager, SeniorDeveloper, CodeJudge, CodeReviewer, QAEngineer, CrewManager
from project import ProjectState
from .extension import CrewExtension

class VirtualCrew:
    role: str = 'Virtual Crew'

    def __init__(self, extensions: list[CrewExtension] = None):
        self.logger = logging.getLogger(self.role)
        self.extensions = extensions or []
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
        return workflow.compile(
            checkpointer=self._memory,
            interrupt_before=['human']
        )

    def _human_node(self, state: ProjectState) -> dict:
        """Dummy node that acts as a breakpoint for human input."""
        # The actual input() prompt happens in the execution loop.
        # This node just clears the question so we don't get stuck in a loop.
        return {'clarification_question': ''}

    def execute_project(self, requirements: str, thread_id: str):
        config = {'configurable': {'thread_id': thread_id}}

        self.logger.info("Starting Project Requirements:\n%s", requirements)

        initial_state = {
            'requirements': requirements,
            'clarification_question': '',
            'human_answer': '',
            'specs': '',
            'code_drafts': [],
            'code': '',
            'winner_index': 0,
            'review_feedback': '',
            'test_results': '',
            'revision_count': 0,
            'next_agent': '',
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
