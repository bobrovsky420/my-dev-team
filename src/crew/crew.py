import logging
from functools import cached_property
from langgraph.checkpoint.memory import MemorySaver

class VirtualCrew:
    role = 'Virtual Crew'
    name: str = None

    def __init__(self, manager, agents: dict = None, developers: dict = None, extensions: list = None):
        self.logger = logging.getLogger(self.name or self.role)
        self.manager = manager
        self.agents = agents or {}
        self.developers = developers or {}
        self.extensions = extensions or []
        self.app = self.manager.build_graph(
            agents=self.agents,
            developers=self.developers,
            memory=self._memory,
            human_interrupter=self._dummy_human_node
        )

    @cached_property
    def _memory(self):
        return MemorySaver()

    def _dummy_human_node(self, state: dict) -> dict:
        self.logger.info("Human input received. Resuming workflow...")
        return {'clarification_question': ''}

    def execute(self, thread_id: str, initial_state: dict = None) -> dict:
        config = {'configurable': {'thread_id': thread_id}}
        if initial_state:
            self.logger.info("Starting workflow...")
            for ext in self.extensions:
                ext.on_start(thread_id, initial_state)
        else:
            self.logger.info("Resuming workflow from memory...")
        while True:
            input_data = initial_state if 'initial_state' in locals() and initial_state else None
            for full_state in self.app.stream(input_data, config, stream_mode='values'):
                for ext in self.extensions:
                    ext.on_step(thread_id, full_state)
            if initial_state:
                initial_state = None
            state_snapshot = self.app.get_state(config)
            if not state_snapshot.next:
                break
            next_node = state_snapshot.next[0]
            self.logger.info("Workflow paused. Waiting on: %s", next_node)
            update_provided = False
            for ext in self.extensions:
                update = ext.on_pause(thread_id, state_snapshot.values, next_node)
                if update:
                    self.app.update_state(config, update)
                    update_provided = True
            if not update_provided:
                break
        final_state = self.app.get_state(config).values
        for ext in self.extensions:
            ext.on_finish(thread_id, final_state)
        return final_state
