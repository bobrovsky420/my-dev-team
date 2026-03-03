from functools import cached_property
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from project import ProjectState
from extensions import CrewExtension
from .manager import CrewManager

class VirtualCrew:
    role = 'Virtual Crew'
    name: str = None

    def __init__(self, agents: dict, developers: dict, extensions: list[CrewExtension] = None):
        self.logger = logging.getLogger(self.name or self.role)
        self.extensions = extensions or []
        self.agents = agents
        self.developers = developers
        self.manager = CrewManager(developers=list(self.developers.keys()))
        self.app = self._build_graph()

    @cached_property
    def _memory(self):
        return MemorySaver()

    def _build_graph(self):
        def add_node(node_name, *, agent_func = None, conditional_router = True):
            workflow.add_node(node_name, agent_func or self.agents[node_name].process)
            if conditional_router:
                workflow.add_conditional_edges(node_name, self.manager.router)
        workflow = StateGraph(ProjectState)
        add_node('officer', agent_func=self.manager.queue_manager)
        add_node('pm')
        add_node('architect')
        for dev in self.developers:
            add_node(dev, agent_func=self.developers[dev].process)
        add_node('judge')
        add_node('reviewer')
        add_node('qa')
        add_node('final_qa', agent_func=self.agents['qa'].process)
        add_node('human', agent_func=self._dummy_human_node)
        add_node('reporter', conditional_router=False)
        workflow.add_conditional_edges(START, self.manager.router)
        workflow.add_edge('reporter', END)
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
