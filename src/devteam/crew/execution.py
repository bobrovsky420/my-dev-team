from logging import Logger
from typing import Any
from .event_emitter import EventEmitter
from .final_result import FinalResult

class Execution(EventEmitter):
    """Mixin to manage asynchronous execution."""

    app: Any # type: ignore
    logger: Logger

    async def inject_feedback(self, thread_id: str, feedback: str, feedback_source: str = 'reviewer') -> dict:
        """Inject feedback before resuming a thread."""
        config = {'configurable': {'thread_id': thread_id}}
        node_mapping = {
            'pm': 'planning',
            'architect': 'planning',
            'reviewer': 'development',
            'qa': 'development'
        }
        state_update = {}
        if feedback_source == 'reviewer':
            state_update['review_feedback'] = f"CRITICAL HUMAN FEEDBACK: {feedback}"
            state_update['current_phase'] = 'development'
        elif feedback_source == 'qa':
            state_update['test_results'] = f"CRITICAL HUMAN FEEDBACK: {feedback}"
            state_update['current_phase'] = 'development'
        elif feedback_source == 'pm':
            state_update['specs'] = f"CRITICAL HUMAN FEEDBACK: {feedback}"
            state_update['current_phase'] = 'planning'
        else:
            state_update['communication_log'] = [f"**[Human]**: {feedback}"]
        target_state = await self.app.aget_state(config)
        safe_config = target_state.config.copy()
        if 'configurable' not in safe_config:
            safe_config['configurable'] = {}
        if 'checkpoint_ns' not in safe_config['configurable']:
            safe_config['configurable']['checkpoint_ns'] = ""
        await self.app.aupdate_state(
            safe_config,
            state_update,
            as_node=node_mapping.get(feedback_source, 'development')
        )
        return state_update

    async def execute(self, thread_id: str, *, requirements: str = None, feedback: str = None, feedback_source: str = 'reviewer', checkpoint_id: str = None) -> FinalResult:
        config = {'configurable': {'thread_id': thread_id}}
        if checkpoint_id:
            config['configurable']['checkpoint_id'] = checkpoint_id
            self.logger.debug("Rewinding time to checkpoint: %s", checkpoint_id)
        abort_requested = False
        if feedback:
            state_update = await self.inject_feedback(thread_id, feedback, feedback_source)
            self.emit_event('resume', thread_id, state_update=state_update)
            initial_state = None
        elif requirements:
            initial_state = {
                'requirements': requirements,
                'current_phase': 'planning',
            }
            self.emit_event('start', thread_id, initial_state=initial_state)
        else:
            initial_state = None
            self.emit_event('resume', thread_id, state_update=initial_state)

        while True:
            async for event in self.app.astream(initial_state, config, stream_mode='updates', subgraphs=True):
                if isinstance(event, tuple) and len(event) == 2:
                    _, state_update = event
                else:
                    state_update = event
                state_object = await self.app.aget_state(config)
                full_state = state_object.values
                self.emit_event('step', thread_id, state_update=state_update, full_state=full_state)
                if full_state.get('error') is True:
                    traceback_str = full_state.get('error_message', 'Unknown Error')
                    self.logger.error("Workflow halted due to error:\n%s\n\nFix the issue and resume using: devteam --resume %s", traceback_str, thread_id)
                    abort_requested = True
                    break
                if full_state.get('abort_requested'):
                    abort_requested = True
                    self.logger.debug("Abort requested during execution. Ending workflow.")
                    break
            if abort_requested:
                break
            if initial_state:
                initial_state = None
            state_snapshot = await self.app.aget_state(config)
            if not state_snapshot.next:
                break
            next_node = state_snapshot.next[0]
            self.logger.debug("Workflow paused. Waiting on: %s", next_node)
            if update := self.emit_event('pause', thread_id, current_state=state_snapshot.values, next_node=next_node):
                await self.app.aupdate_state(config, update)
                if update.get('abort_requested'):
                    abort_requested = True
                    self.logger.debug("Abort requested. Ending workflow.")
                    break
            else:
                break

        final_state = await self.app.aget_state(config)
        final_state = final_state.values
        if abort_requested:
            final_state['abort_requested'] = True
        else:
            final_state['current_phase'] = 'complete'
        self.emit_event('finish', thread_id, final_state=final_state)
        final_state['thread_id'] = thread_id
        return FinalResult(**final_state)
