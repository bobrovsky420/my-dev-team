import logging
from functools import cached_property
from pathlib import Path
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END
from devteam.extensions import CrewExtension, WorkspaceSaver, GitCommitter
from devteam.utils import LLMFactory, RateLimiter
from .final_result import FinalResult

class VirtualCrew:
    role = 'Virtual Crew'
    name: str = None

    def __init__(self,
                 project_folder: Path,
                 manager,
                 agents: dict,
                 llm_factory: LLMFactory,
                 *,
                 extensions: list[CrewExtension] = None,
                 rate_limiter: RateLimiter = None,
                 checkpointer = None,
                 workspace_saver: CrewExtension = None,
                 git_committer: CrewExtension = None):
        self.logger = logging.getLogger(self.name or self.role)
        self.project_folder = project_folder
        self.manager = manager
        self.agents = agents or {}
        self.workspace_saver = workspace_saver or WorkspaceSaver(workspace_dir=project_folder)
        self.git_committer = git_committer or GitCommitter(workspace_dir=project_folder / 'workspace')
        self.extensions = extensions or []
        for agent in self.agents.values():
            agent.llm_factory = llm_factory
            if rate_limiter:
                agent.rate_limiter = rate_limiter
        self.app = self.manager.build_graph(agents=self.agents, memory=checkpointer or MemorySaver())

    @cached_property
    def system_hooks(self) -> list[CrewExtension]:
        return [
            self.workspace_saver,
            self.git_committer
        ]

    @cached_property
    def all_extensions(self) -> list[CrewExtension]:
        return self.system_hooks + self.extensions

    async def get_history(self, thread_id: str) -> list[dict]:
        config = {'configurable': {'thread_id': thread_id}}
        all_checkpoints = []
        seen_c_ids = set()
        async for state_snapshot in self.app.aget_state_history(config):
            c_id = state_snapshot.config['configurable']['checkpoint_id']
            if c_id not in seen_c_ids:
                all_checkpoints.append({
                    'time': state_snapshot.created_at,
                    'ns': 'root',
                    'c_id': c_id,
                    'node': state_snapshot.next[0] if state_snapshot.next else END
                })
                seen_c_ids.add(c_id)
            full_state = await self.app.aget_state(state_snapshot.config, subgraphs=True)
            for task in full_state.tasks:
                if task.state and hasattr(task.state, 'config'):
                    sub_ns = task.state.config['configurable'].get('checkpoint_ns')
                    if sub_ns:
                        sub_config = {
                            'configurable': {
                                'thread_id': thread_id,
                                'checkpoint_ns': sub_ns
                            }
                        }
                        async for sub_snapshot in self.app.aget_state_history(sub_config):
                            sub_c_id = sub_snapshot.config['configurable']['checkpoint_id']
                            if sub_c_id not in seen_c_ids:
                                all_checkpoints.append({
                                    'time': sub_snapshot.created_at,
                                    'ns': sub_ns,
                                    'c_id': sub_c_id,
                                    'node': sub_snapshot.next[0] if sub_snapshot.next else END
                                })
                                seen_c_ids.add(sub_c_id)
        all_checkpoints.sort(key=lambda x: x['time'], reverse=True)
        return all_checkpoints

    async def execute(self, thread_id: str, *, requirements: str = None, feedback: str = None, feedback_source: str = 'reviewer', checkpoint_id: str = None) -> FinalResult:
        config = {'configurable': {'thread_id': thread_id}}
        if checkpoint_id:
            config['configurable']['checkpoint_id'] = checkpoint_id
            self.logger.debug("Rewinding time to checkpoint: %s", checkpoint_id)
        abort_requested = False
        if feedback:
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
            for ext in self.all_extensions:
                ext.on_resume(thread_id, state_update)
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
            config = {'configurable': {'thread_id': thread_id}}
            initial_state = None
        elif requirements:
            initial_state = {
                'requirements': requirements,
                'current_phase': 'planning',
            }
            for ext in self.all_extensions:
                ext.on_start(thread_id, initial_state)
        else:
            initial_state = None
            for ext in self.all_extensions:
                ext.on_resume(thread_id, initial_state)

        while True:
            async for event in self.app.astream(initial_state, config, stream_mode='updates', subgraphs=True):
                if isinstance(event, tuple) and len(event) == 2:
                    namespace, state_update = event
                else:
                    state_update = event
                state_object = await self.app.aget_state(config)
                full_state = state_object.values
                for ext in self.all_extensions:
                    ext.on_step(thread_id, state_update=state_update, full_state=full_state)
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
            update_provided = False
            for ext in self.all_extensions:
                update = ext.on_pause(thread_id, state_snapshot.values, next_node)
                if update:
                    await self.app.aupdate_state(config, update)
                    update_provided = True
                    if update.get('abort_requested'):
                        abort_requested = True
                        break
            if abort_requested:
                self.logger.debug("Abort requested. Ending workflow.")
                break
            if not update_provided:
                break
        final_state = await self.app.aget_state(config)
        final_state = final_state.values
        if abort_requested:
            final_state['abort_requested'] = True
        else:
            final_state['current_phase'] = 'complete'
        for ext in self.all_extensions:
            ext.on_finish(thread_id, final_state)
        final_state['thread_id'] = thread_id
        return FinalResult(**final_state)
