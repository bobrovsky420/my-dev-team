from functools import cached_property
import logging
from langgraph.checkpoint.memory import MemorySaver
from extensions import CrewExtension
from managers import BaseManager

class VirtualCrew:
    role = 'Virtual Crew'
    name: str = None

    def __init__(self, agents: dict, developers: dict, manager: BaseManager, extensions: list[CrewExtension] = None):
        self.logger = logging.getLogger(self.name or self.role)
        self.extensions = extensions or []
        self.app = manager.build_graph(
            agents=agents,
            developers=developers,
            memory=self._memory,
            human_interrupter=self._dummy_human_node
        )

    @cached_property
    def _memory(self):
        return MemorySaver()

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
        return final_state.get('final_report', 'No report generated.')
