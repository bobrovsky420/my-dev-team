import logging
from functools import cached_property
from langgraph.checkpoint.memory import MemorySaver
from ..utils import LLMFactory, RateLimiter
from .final_result import FinalResult

class VirtualCrew:
    role = 'Virtual Crew'
    name: str = None

    def __init__(self, manager, agents: dict, llm_factory: LLMFactory, extensions: list = None, rate_limiter: RateLimiter = None, checkpointer = None):
        self.logger = logging.getLogger(self.name or self.role)
        self.manager = manager
        self.agents = agents or {}
        self.extensions = extensions or []
        for agent in self.agents.values():
            agent.llm_factory = llm_factory
            if rate_limiter:
                agent.rate_limiter = rate_limiter
        self.app = self.manager.build_graph(agents=self.agents, memory=checkpointer or self.memory)

    @cached_property
    def memory(self):
        return MemorySaver()

    async def execute(self, thread_id: str, *, requirements: str = None, feedback: str = None, feedback_source: str = 'reviewer') -> FinalResult:
        config = {'configurable': {'thread_id': thread_id}}
        abort_requested = False
        if feedback:
            node_mapping = {
                'pm': 'planning',
                'architect': 'planning',
                'reviewer': 'development',
                'qa': 'development'
            }
            self.logger.info("Injecting Human Feedback as '%s'...", feedback_source)
            state_update = {}
            if feedback_source == 'reviewer':
                state_update['review_feedback'] = f"CRITICAL HUMAN FEEDBACK: {feedback}"
            elif feedback_source == 'qa':
                state_update['test_results'] = f"CRITICAL HUMAN FEEDBACK: {feedback}"
            elif feedback_source == 'pm':
                state_update['specs'] = f"CRITICAL HUMAN FEEDBACK: {feedback}"
            else:
                state_update['communication_log'] = [f"**[Human]**: {feedback}"]
            await self.app.aupdate_state(config, state_update, as_node=node_mapping.get(feedback_source, 'development'))
            initial_state = None
        elif requirements:
            initial_state = {
                'requirements': requirements
            }
            self.logger.info("Starting new workflow...")
            for ext in self.extensions:
                ext.on_start(thread_id, initial_state)
        else:
            initial_state = None
            self.logger.info("Resuming workflow from memory...")
        while True:
            async for event in self.app.astream(initial_state, config, stream_mode='updates', subgraphs=True):
                if isinstance(event, tuple) and len(event) == 2:
                    namespace, state_update = event
                else:
                    state_update = event
                state_object = await self.app.aget_state(config)
                full_state = state_object.values
                for ext in self.extensions:
                    ext.on_step(thread_id, state_update=state_update, full_state=full_state)
                if full_state.get('abort_requested'):
                    abort_requested = True
                    self.logger.info("Abort requested during execution. Ending workflow.")
                    break
            if abort_requested:
                break
            if initial_state:
                initial_state = None
            state_snapshot = await self.app.aget_state(config)
            if not state_snapshot.next:
                break
            next_node = state_snapshot.next[0]
            self.logger.info("Workflow paused. Waiting on: %s", next_node)
            update_provided = False
            for ext in self.extensions:
                update = ext.on_pause(thread_id, state_snapshot.values, next_node)
                if update:
                    await self.app.aupdate_state(config, update)
                    update_provided = True
                    if update.get('abort_requested'):
                        abort_requested = True
                        break
            if abort_requested:
                self.logger.info("Abort requested. Ending workflow.")
                break
            if not update_provided:
                break
        final_state = await self.app.aget_state(config)
        final_state = final_state.values
        if abort_requested:
            final_state['abort_requested'] = True
        for ext in self.extensions:
            ext.on_finish(thread_id, final_state)
        final_state['thread_id'] = thread_id
        return FinalResult(**final_state)
