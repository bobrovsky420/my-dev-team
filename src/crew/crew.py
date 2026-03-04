from functools import cached_property
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from project import ProjectState
from extensions import CrewExtension
from managers import BaseManager

class VirtualCrew:
    role = 'Virtual Crew'
    name: str = None

    def __init__(self, agents: dict, developers: dict, manager: BaseManager, extensions: list[CrewExtension] = None):
        self.logger = logging.getLogger(self.name or self.role)
        self.extensions = extensions or []
        self.agents = agents | developers
        self.developers = developers
        self.manager = manager
        self.app = self._build_graph()

    @cached_property
    def _memory(self):
        return MemorySaver()

    def _build_graph(self):
        def add_node(node_name, *, agent_func = None, conditional_router = True, end_key = None):
            workflow.add_node(node_name, agent_func or self.agents[node_name].process)
            if conditional_router:
                workflow.add_conditional_edges(node_name, self.manager.router)
            if end_key:
                workflow.add_edge(node_name, end_key)
        workflow = StateGraph(ProjectState)
        workflow.add_conditional_edges(START, self.manager.router)
        add_node('officer', agent_func=self.manager.queue_manager)
        add_node('human', agent_func=self._dummy_human_node)
        for agent in self.agents:
            if agent not in ['reporter']:
                add_node(agent)
        add_node('reporter', conditional_router=False, end_key=END)
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
